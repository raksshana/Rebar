"""

Compare five Claude models on the exact same migration task.



Fairness guarantees:

  1. Each tier's task is generated exactly once.

  2. Source data is generated exactly once.

  3. Destination-schema obfuscation is performed exactly once.

  4. The migration prompt is built exactly once.

  5. Every model receives the exact same prompt string.

  6. Every generated script executes against a fresh deep copy of the same

     source data and schemas, preventing one model from mutating another

     model's inputs.



Models compared:

  - Claude Opus 4.8

  - Claude Opus 4.6

  - Claude Opus 4.1

  - Claude Sonnet 4.5

  - Claude Sonnet 4.6



Diagnostics:

  - Shared prompt SHA-256 fingerprint

  - Execution stdout and stderr

  - Metric-by-metric comparison table

  - All five generated scripts printed side by side

  - Final score summary across tiers



Usage:

    python tests/test_claude_compare.py

    python tests/test_claude_compare.py --tiers 1 2 3

    python tests/test_claude_compare.py --tiers 3 --n-records 5

    python tests/test_claude_compare.py --no-scripts

    python tests/test_claude_compare.py --script-column-width 36

"""



import argparse

import copy

import hashlib

import os

import sys

import textwrap

from typing import Any



sys.path.insert(

    0,

    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),

)



from generator.orchestration import orchestrate

from generator.difficulty_dial import (

    obfuscate_dest_schema,

    translate_dest_data,

)

from generator.data_generation import generate_source_data

from agent.wrapper import AnthropicClient, _extract_code, _exec_script, _RESTRICTED_BUILTINS

from agent.prompt import build_script_prompt





# Full pinned IDs are used for pre-4.6 models so the benchmark does not

# silently move to a different snapshot later.

MODELS = [

    (

        "Opus 4.8",

        "claude-opus-4-8",

        lambda: AnthropicClient("claude-opus-4-8"),

    ),

    (

        "Opus 4.6",

        "claude-opus-4-6",

        lambda: AnthropicClient("claude-opus-4-6"),

    ),

    (

        "Opus 4.1",

        "claude-opus-4-1-20250805",

        lambda: AnthropicClient("claude-opus-4-1-20250805"),

    ),

    (

        "Sonnet 4.5",

        "claude-sonnet-4-5-20250929",

        lambda: AnthropicClient("claude-sonnet-4-5-20250929"),

    ),

    (

        "Sonnet 4.6",

        "claude-sonnet-4-6",

        lambda: AnthropicClient("claude-sonnet-4-6"),

    ),

]



DIVIDER = "=" * 110

THIN_DIVIDER = "-" * 110



BASE_METRICS = [

    "coverage",

    "field_fidelity",

    "relationship_integrity",

    "type_correctness",

]





def _call_model(client: AnthropicClient, prompt: str) -> str:

    """Send the identical migration prompt to one model."""

    return client.generate_text(

        messages=[

            {

                "role": "user",

                "content": prompt,

            }

        ],

        system_prompt="",

    )





def _prompt_fingerprint(prompt: str) -> str:

    """Return a short SHA-256 fingerprint for verifying prompt identity."""

    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]





def _print_exec_result(model_name: str, exec_result: dict[str, Any]) -> None:

    """Print useful execution diagnostics for one generated migration."""

    if exec_result["error"]:

        print(f"\n    !! EXECUTION ERROR [{model_name}]")



        stderr = exec_result.get("stderr", "").strip()

        stdout = exec_result.get("stdout", "").strip()



        if stderr:

            print("       stderr:")

            print(textwrap.indent(stderr, "         "))



        if stdout:

            print("       stdout:")

            print(textwrap.indent(stdout[:1000], "         "))



        if not stderr and not stdout:

            print("       No stderr or stdout was captured.")



    else:

        stdout = exec_result.get("stdout", "").strip()



        if stdout:

            print(f"\n    [stdout: {model_name}]")

            print(textwrap.indent(stdout[:1000], "      "))





def run_episode(

    client: AnthropicClient,

    task: Any,

    shared_prompt: str,

    source_data_snapshot: dict,

    source_schema_snapshot: dict,

    dest_schema_snapshot: dict,

    tier: int,

    entity_map: dict | None = None,

    field_maps: dict | None = None,

    model_name: str = "",

    model_id: str = "",

) -> dict[str, Any]:

    """

    Run one model against a prebuilt task and the exact shared prompt.



    Deep copies are used in the execution namespace because a model-generated

    script could modify source_data or one of the schema dictionaries.

    """



    raw_response = _call_model(client, shared_prompt)

    code = _extract_code(raw_response)



    # Every model gets independent copies with identical initial values.

    episode_source_data = copy.deepcopy(source_data_snapshot)

    episode_source_schema = copy.deepcopy(source_schema_snapshot)

    episode_dest_schema = copy.deepcopy(dest_schema_snapshot)



    dest_store: dict[str, list] = {}



    def write_dest(entity: str, records: list) -> dict:

        """

        Collect records written by the model-generated migration script.

        """

        if entity not in dest_store:

            dest_store[entity] = []



        dest_store[entity].extend(copy.deepcopy(records))



        return {

            "written": len(records),

            "errors": [],

        }



    exec_result = _exec_script(

        code,

        {

            "source_data": episode_source_data,

            "write_dest": write_dest,

            "source_schema": episode_source_schema,

            "dest_schema": episode_dest_schema,

            "__builtins__": _RESTRICTED_BUILTINS,

        },

    )



    _print_exec_result(model_name, exec_result)



    if tier == 3:

        real_dest = translate_dest_data(

            copy.deepcopy(dest_store),

            copy.deepcopy(entity_map),

            copy.deepcopy(field_maps),

        )

    else:

        real_dest = copy.deepcopy(dest_store)



    # Grade against an untouched copy of the original source records.

    result = task.grader.grade(

        copy.deepcopy(source_data_snapshot),

        real_dest,

    )



    result["_model_name"] = model_name

    result["_model_id"] = model_id

    result["_raw_response"] = raw_response

    result["_code"] = code

    result["_exec_error"] = exec_result["error"]

    result["_stderr"] = exec_result.get("stderr", "")

    result["_stdout"] = exec_result.get("stdout", "")

    result["_dest_store"] = dest_store



    return result





def _format_metric_value(

    result: dict[str, Any] | None,

    metric: str,

) -> str:

    """Format one score-table cell."""

    if result is None:

        return "MODEL ERROR"



    if metric == "execution":

        return "ERROR" if result["_exec_error"] else "OK"



    if metric not in result:

        return "—"



    value = result[metric]



    if metric == "total":

        return f"{value:.1f}"



    return f"{value:.3f}"





def _print_score_table(

    tier: int,

    tier_results: dict[str, dict[str, Any] | None],

) -> None:

    """Print metrics as rows and models as columns."""

    model_names = [display_name for display_name, _, _ in MODELS]



    metrics = list(BASE_METRICS)



    if any(

        result is not None and "structural" in result

        for result in tier_results.values()

    ):

        metrics.append("structural")



    metrics.extend(["total", "execution"])



    metric_width = 25

    column_width = 17



    print(f"\n{DIVIDER}")

    print(f"TIER {tier} — SIDE-BY-SIDE SCORE COMPARISON")

    print(DIVIDER)



    header = f"{'Metric':<{metric_width}}"

    for model_name in model_names:

        header += f"{model_name:>{column_width}}"



    print(header)

    print(THIN_DIVIDER)



    display_names = {

        "coverage": "Coverage",

        "field_fidelity": "Field fidelity",

        "relationship_integrity": "Relationship integrity",

        "type_correctness": "Type correctness",

        "structural": "Structural",

        "total": "TOTAL / 100",

        "execution": "Script execution",

    }



    for metric in metrics:

        row = f"{display_names[metric]:<{metric_width}}"



        for model_name in model_names:

            result = tier_results.get(model_name)

            value = _format_metric_value(result, metric)

            row += f"{value:>{column_width}}"



        print(row)



    print(DIVIDER)





def _wrap_code_for_column(code: str, width: int) -> list[str]:

    """

    Wrap code into a fixed-width column while preserving indentation as much

    as possible.

    """

    if not code.strip():

        return ["<no code extracted>"]



    output: list[str] = []

    prefix_width = 5

    content_width = max(8, width - prefix_width)



    for line_number, original_line in enumerate(code.splitlines(), start=1):

        expanded_line = original_line.expandtabs(4)



        chunks = textwrap.wrap(

            expanded_line,

            width=content_width,

            replace_whitespace=False,

            drop_whitespace=False,

            break_long_words=True,

            break_on_hyphens=False,

        )



        if not chunks:

            chunks = [""]



        output.append(f"{line_number:>3}  {chunks[0]}")



        for continuation in chunks[1:]:

            output.append(f"{'':>{prefix_width}}{continuation}")



    return output





def _print_scripts_side_by_side(

    tier: int,

    tier_results: dict[str, dict[str, Any] | None],

    column_width: int,

) -> None:

    """Print all five extracted migration scripts in parallel columns."""

    model_names = [display_name for display_name, _, _ in MODELS]



    columns: list[list[str]] = []



    for model_name in model_names:

        result = tier_results.get(model_name)



        if result is None:

            code = "<model request failed>"

        else:

            code = result.get("_code", "") or "<no code extracted>"



        columns.append(_wrap_code_for_column(code, column_width))



    max_rows = max(len(column) for column in columns)

    separator = " | "

    horizontal_rule = "-+-".join("-" * column_width for _ in columns)



    print(f"\n{DIVIDER}")

    print(f"TIER {tier} — ALL GENERATED SCRIPTS SIDE BY SIDE")

    print(DIVIDER)



    header_cells = [

        model_name[:column_width].center(column_width)

        for model_name in model_names

    ]

    print(separator.join(header_cells))

    print(horizontal_rule)



    for row_index in range(max_rows):

        cells = []



        for column in columns:

            if row_index < len(column):

                cell = column[row_index]

            else:

                cell = ""



            cells.append(cell[:column_width].ljust(column_width))



        print(separator.join(cells))



    print(horizontal_rule)





def _print_model_details(

    tier_results: dict[str, dict[str, Any] | None],

) -> None:

    """Print model IDs, code length, and error details."""

    print("\nMODEL DETAILS")

    print(THIN_DIVIDER)



    for display_name, model_id, _ in MODELS:

        result = tier_results.get(display_name)



        if result is None:

            print(f"  {display_name:<14} {model_id:<38} MODEL CALL FAILED")

            continue



        line_count = len(result.get("_code", "").splitlines())

        status = "EXEC ERROR" if result["_exec_error"] else "OK"



        print(

            f"  {display_name:<14} "

            f"{model_id:<38} "

            f"{line_count:>4} code lines  "

            f"{status}"

        )





def _print_ranking(

    tier: int,

    tier_results: dict[str, dict[str, Any] | None],

) -> None:

    """Rank successful model runs by total grader score."""

    valid_results = [

        (model_name, result)

        for model_name, result in tier_results.items()

        if result is not None

    ]



    valid_results.sort(

        key=lambda item: item[1]["total"],

        reverse=True,

    )



    print(f"\nTIER {tier} RANKING")

    print(THIN_DIVIDER)



    for rank, (model_name, result) in enumerate(valid_results, start=1):

        error_suffix = " [EXEC ERROR]" if result["_exec_error"] else ""



        print(

            f"  {rank}. {model_name:<14} "

            f"{result['total']:>6.1f} / 100"

            f"{error_suffix}"

        )





def _print_final_summary(

    all_results: dict[str, dict[int, dict[str, Any] | None]],

    tiers: list[int],

) -> None:

    """Print model totals for every requested tier."""

    model_width = 18

    tier_width = 12



    print(f"\n{DIVIDER}")

    print("FINAL SUMMARY")

    print(DIVIDER)



    header = f"{'Model':<{model_width}}"



    for tier in tiers:

        header += f"{f'Tier {tier}':>{tier_width}}"



    header += f"{'Average':>{tier_width}}"

    header += f"{'Exec errors':>15}"



    print(header)

    print(THIN_DIVIDER)



    for model_name, _, _ in MODELS:

        row = f"{model_name:<{model_width}}"

        scores: list[float] = []

        error_count = 0



        for tier in tiers:

            result = all_results.get(model_name, {}).get(tier)



            if result is None:

                row += f"{'ERR':>{tier_width}}"

                error_count += 1

                continue



            row += f"{result['total']:>{tier_width}.1f}"

            scores.append(result["total"])



            if result["_exec_error"]:

                error_count += 1



        average = sum(scores) / len(scores) if scores else 0.0



        row += f"{average:>{tier_width}.1f}"

        row += f"{f'{error_count}/{len(tiers)}':>15}"



        print(row)



    print(DIVIDER)





def _grade_dest_store(
    task: Any,
    source_data_snapshot: dict,
    dest_store: dict,
    tier: int,
    entity_map: dict | None,
    field_maps: dict | None,
) -> dict:
    """Re-grade an (optionally modified) dest_store, handling tier-3 translation."""
    candidate = (
        translate_dest_data(
            copy.deepcopy(dest_store),
            copy.deepcopy(entity_map),
            copy.deepcopy(field_maps),
        )
        if tier == 3
        else copy.deepcopy(dest_store)
    )
    return task.grader.grade(copy.deepcopy(source_data_snapshot), candidate)


def _print_output_summary(
    model_name: str,
    dest_store: dict,
    source_data: dict,
) -> None:
    """Print record counts per dest entity and flag suspicious patterns.

    Shotgun signal: a partition sub-entity contains as many records as the
    entire source dataset (because the model wrote every source record into
    every sub-entity instead of routing each record to exactly one).
    """
    total_src = sum(len(r) for r in source_data.values())

    print(f"    {'Entity':<22} {'Recs':>5}  {'UniqIDs':>7}  {'Dups':>5}  Notes")
    print(f"    {'─' * 60}")

    for entity, records in sorted(dest_store.items()):
        if not isinstance(records, list):
            continue
        ids = [r.get("id") for r in records if isinstance(r, dict)]
        n_unique = len(set(ids))
        n_dups = len(ids) - n_unique
        notes: list[str] = []
        if n_dups:
            notes.append(f"!! {n_dups} dup IDs")
        # If a dest entity that is NOT a source entity has the same record
        # count as ALL source records combined, it almost certainly received
        # a verbatim dump of every source record (shotgun).
        if entity not in source_data and len(records) == total_src and total_src > 0:
            notes.append("?? matches total-source count — possible shotgun")
        print(
            f"    {entity:<22} {len(records):>5}  {n_unique:>7}  {n_dups:>5}"
            + (f"  {', '.join(notes)}" if notes else "")
        )

    print()


def _print_partition_ablation(
    task: Any,
    source_data_snapshot: dict,
    tier_results: dict,
    tier: int,
    entity_map: dict | None,
    field_maps: dict | None,
) -> None:
    """Ablation audit: grade each model's output with partition sub-entities
    individually removed or individually kept.

    How to read the output
    ──────────────────────
    Large negative delta on removal   → records were unique to that bucket
                                        → correct partitioning
    Near-zero delta on removal        → same records exist in every other bucket
                                        → shotgun exploit
    """
    partition_ts = [t for t in task.transformations if t["type"] == "partition"]
    if not partition_ts:
        return

    all_subs: list[str] = []
    for t in partition_ts:
        all_subs.extend(t["mapping"].values())
    if not all_subs:
        return

    model_names = [name for name, _, _ in MODELS]
    col = 13

    print(f"\n{DIVIDER}")
    print("PARTITION ABLATION AUDIT")
    print("  Large -delta on removal  =  records were unique there  =  CORRECT partition")
    print("  Near-zero delta          =  records duplicated elsewhere  =  SHOTGUN exploit")
    print(DIVIDER)

    header = f"  {'Condition':<32}" + "".join(f"  {n[:col]:>{col}}" for n in model_names)
    print(header)
    print("  " + "─" * (32 + (col + 2) * len(model_names)))

    def _row(label: str, store_fn) -> str:
        line = f"  {label:<32}"
        for name in model_names:
            r = tier_results.get(name)
            if r is None:
                line += f"  {'ERR':>{col}}"
                continue
            try:
                score = _grade_dest_store(
                    task,
                    source_data_snapshot,
                    store_fn(r["_dest_store"]),
                    tier,
                    entity_map,
                    field_maps,
                )["total"]
                line += f"  {score:>{col}.1f}"
            except Exception:
                line += f"  {'ERR':>{col}}"
        return line

    # Baseline
    print(_row("Full output", lambda s: s))
    print()

    # Remove one sub at a time
    for removed in all_subs:
        def _rm(s, rem=removed):
            c = copy.deepcopy(s)
            c.pop(rem, None)
            return c
        print(_row(f"Without {removed}", _rm))

    print()

    # Keep only one sub at a time
    for kept in all_subs:
        def _keep(s, k=kept):
            c = copy.deepcopy(s)
            for sub in all_subs:
                if sub != k:
                    c.pop(sub, None)
            return c
        print(_row(f"Only {kept}", _keep))

    # Remove all partition subs
    def _rm_all(s):
        c = copy.deepcopy(s)
        for sub in all_subs:
            c.pop(sub, None)
        return c
    print()
    print(_row("No partition subs", _rm_all))
    print(DIVIDER)


def main() -> None:

    parser = argparse.ArgumentParser(

        description=(

            "Run one identical migration benchmark across five Claude models."

        )

    )



    parser.add_argument(

        "--tiers",

        nargs="+",

        type=int,

        default=[3],

        choices=[0, 1, 2, 3],

        help="Difficulty tiers to benchmark. Default: 3",

    )



    parser.add_argument(

        "--n-records",

        type=int,

        default=3,

        help="Number of source records generated per entity. Default: 3",

    )



    parser.add_argument(

        "--no-scripts",

        action="store_true",

        help="Do not print the five generated scripts side by side.",

    )



    parser.add_argument(

        "--no-audit",

        action="store_true",

        help="Skip the reward-hacking audit (output summary + partition ablation).",

    )



    parser.add_argument(

        "--script-column-width",

        type=int,

        default=32,

        help=(

            "Width of each model's script column. "

            "Five columns are printed. Default: 32"

        ),

    )



    args = parser.parse_args()



    if args.n_records < 1:

        parser.error("--n-records must be at least 1")



    if args.script_column_width < 16:

        parser.error("--script-column-width must be at least 16")



    print(DIVIDER)

    print("INITIALISING CLAUDE CLIENTS")

    print(DIVIDER)



    clients: list[tuple[str, str, AnthropicClient]] = []



    # Initialise every client before generating tasks so configuration

    # problems are caught before benchmark execution begins.

    for display_name, model_id, factory in MODELS:

        try:

            client = factory()

            clients.append((display_name, model_id, client))

            print(f"  OK  {display_name:<14} {model_id}")

        except Exception as exc:

            print(

                f"  FAILED  {display_name} ({model_id}): "

                f"{type(exc).__name__}: {exc}"

            )

            sys.exit(1)



    all_results: dict[str, dict[int, dict[str, Any] | None]] = {

        display_name: {}

        for display_name, _, _ in MODELS

    }



    for tier in args.tiers:

        print(f"\n{DIVIDER}")

        print(f"TIER {tier} — GENERATING ONE SHARED MIGRATION")

        print(DIVIDER)



        # Generate the benchmark exactly once for this tier.

        task = orchestrate(tier)



        source_data = generate_source_data(

            task.source_schema,

            n=args.n_records,

            gemini_model=None,

        )



        dest_schema = task.dest_schema

        entity_map = None

        field_maps = None



        # Obfuscate exactly once, then share the resulting schema and maps.

        if tier == 3:

            dest_schema, entity_map, field_maps = obfuscate_dest_schema(

                dest_schema

            )



        # Freeze pristine snapshots before executing any generated scripts.

        source_data_snapshot = copy.deepcopy(source_data)

        source_schema_snapshot = copy.deepcopy(task.source_schema)

        dest_schema_snapshot = copy.deepcopy(dest_schema)

        entity_map_snapshot = copy.deepcopy(entity_map)

        field_maps_snapshot = copy.deepcopy(field_maps)



        # Most important fairness property: build the prompt one time.

        shared_prompt = build_script_prompt(

            source_schema_snapshot,

            dest_schema_snapshot,

            source_data_snapshot,

        )



        fingerprint = _prompt_fingerprint(shared_prompt)



        print(

            "  Source entities : "

            f"{list(source_schema_snapshot['entities'].keys())}"

        )

        print(

            "  Transformations : "

            f"{[transform['type'] for transform in task.transformations]}"

        )

        print(f"  Source records  : {args.n_records} per entity")

        print(f"  Prompt length   : {len(shared_prompt):,} characters")

        print(f"  Prompt SHA-256  : {fingerprint}")

        print("  Same prompt     : YES — reused verbatim for every model")



        tier_results: dict[str, dict[str, Any] | None] = {}



        for display_name, model_id, client in clients:

            print(f"\n  Running {display_name}...")

            print(f"    Model ID: {model_id}")

            print(f"    Prompt fingerprint: {fingerprint}")



            try:

                result = run_episode(

                    client=client,

                    task=task,

                    shared_prompt=shared_prompt,

                    source_data_snapshot=source_data_snapshot,

                    source_schema_snapshot=source_schema_snapshot,

                    dest_schema_snapshot=dest_schema_snapshot,

                    tier=tier,

                    entity_map=entity_map_snapshot,

                    field_maps=field_maps_snapshot,

                    model_name=display_name,

                    model_id=model_id,

                )



                tier_results[display_name] = result

                all_results[display_name][tier] = result



                error_flag = (

                    " [EXEC ERROR]"

                    if result["_exec_error"]

                    else ""

                )



                print(

                    f"    Finished: "

                    f"{result['total']:.1f} / 100"

                    f"{error_flag}"

                )



                if not args.no_audit:

                    _print_output_summary(

                        display_name,

                        result["_dest_store"],

                        source_data_snapshot,

                    )



            except Exception as exc:

                print(

                    f"    MODEL ERROR: "

                    f"{type(exc).__name__}: {exc}"

                )



                tier_results[display_name] = None

                all_results[display_name][tier] = None



        _print_score_table(tier, tier_results)

        _print_model_details(tier_results)

        _print_ranking(tier, tier_results)



        if not args.no_audit:

            _print_partition_ablation(

                task=task,

                source_data_snapshot=source_data_snapshot,

                tier_results=tier_results,

                tier=tier,

                entity_map=entity_map_snapshot,

                field_maps=field_maps_snapshot,

            )



        if not args.no_scripts:

            _print_scripts_side_by_side(

                tier=tier,

                tier_results=tier_results,

                column_width=args.script_column_width,

            )



    _print_final_summary(all_results, args.tiers)





if __name__ == "__main__":

    main()
