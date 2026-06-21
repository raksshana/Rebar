"""

Compare Claude Sonnet 4.6 and GPT-5.4 on the exact same migration.



Fairness guarantees:

  1. The task is generated once per tier.

  2. Source data is generated once per tier.

  3. Destination-schema obfuscation is performed once.

  4. The prompt is built once and reused verbatim.

  5. Each generated script receives a fresh deep copy of the same inputs.



Usage:

    python3 tests/test_sonnet_gpt_compare.py

    python3 tests/test_sonnet_gpt_compare.py --tiers 2 3

    python3 tests/test_sonnet_gpt_compare.py --tiers 3 --n-records 5

    python3 tests/test_sonnet_gpt_compare.py --no-scripts

"""



import argparse

import builtins

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

from agent.wrapper import (

    AnthropicClient,

    OpenAIClient,

    _extract_code,

    _exec_script,

)

from agent.prompt import build_script_prompt





MODELS = [

    (

        "Sonnet 4.6",

        "claude-sonnet-4-6",

        lambda: AnthropicClient("claude-sonnet-4-6"),

    ),

    (

        "GPT-5.4",

        "gpt-5.4",

        lambda: OpenAIClient("gpt-5.4"),

    ),

]



DIVIDER = "=" * 100

THIN_DIVIDER = "-" * 100



METRICS = [

    "coverage",

    "field_fidelity",

    "relationship_integrity",

    "type_correctness",

]





def call_model(client: Any, prompt: str) -> str:

    """Send the shared prompt to one model."""

    return client.generate_text(

        messages=[

            {

                "role": "user",

                "content": prompt,

            }

        ],

        system_prompt="",

    )





def prompt_fingerprint(prompt: str) -> str:

    """Generate a short hash proving both models received the same prompt."""

    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]





def print_exec_result(

    model_name: str,

    exec_result: dict[str, Any],

) -> None:

    """Print stdout or detailed execution errors."""

    if exec_result["error"]:

        print(f"\n    !! EXEC ERROR [{model_name}]")



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

    client: Any,

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

    Run one model against the shared migration.



    Deep copies prevent one generated script from changing the inputs used by

    the other model.

    """

    raw_response = call_model(client, shared_prompt)

    code = _extract_code(raw_response)



    episode_source_data = copy.deepcopy(source_data_snapshot)

    episode_source_schema = copy.deepcopy(source_schema_snapshot)

    episode_dest_schema = copy.deepcopy(dest_schema_snapshot)



    dest_store: dict[str, list] = {}



    def write_dest(entity: str, records: list) -> dict:

        dest_store.setdefault(entity, []).extend(copy.deepcopy(records))



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

            "__builtins__": builtins,

        },

    )



    print_exec_result(model_name, exec_result)



    if tier == 3:

        real_dest = translate_dest_data(

            copy.deepcopy(dest_store),

            copy.deepcopy(entity_map),

            copy.deepcopy(field_maps),

        )

    else:

        real_dest = copy.deepcopy(dest_store)



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





def format_metric(

    result: dict[str, Any] | None,

    metric: str,

) -> str:

    if result is None:

        return "ERROR"



    if metric == "execution":

        return "ERROR" if result["_exec_error"] else "OK"



    if metric not in result:

        return "—"



    if metric == "total":

        return f"{result[metric]:.1f}"



    return f"{result[metric]:.3f}"





def print_score_table(

    tier: int,

    tier_results: dict[str, dict[str, Any] | None],

) -> None:

    """Print both models' scores side by side."""

    model_names = [name for name, _, _ in MODELS]



    metrics = list(METRICS)



    if any(

        result is not None and "structural" in result

        for result in tier_results.values()

    ):

        metrics.append("structural")



    metrics.extend(["total", "execution"])



    metric_labels = {

        "coverage": "Coverage",

        "field_fidelity": "Field fidelity",

        "relationship_integrity": "Relationship integrity",

        "type_correctness": "Type correctness",

        "structural": "Structural",

        "total": "TOTAL / 100",

        "execution": "Script execution",

    }



    metric_width = 30

    model_width = 25



    print(f"\n{DIVIDER}")

    print(f"TIER {tier} — SIDE-BY-SIDE RESULTS")

    print(DIVIDER)



    header = f"{'Metric':<{metric_width}}"



    for model_name in model_names:

        header += f"{model_name:>{model_width}}"



    print(header)

    print(THIN_DIVIDER)



    for metric in metrics:

        row = f"{metric_labels[metric]:<{metric_width}}"



        for model_name in model_names:

            value = format_metric(

                tier_results.get(model_name),

                metric,

            )

            row += f"{value:>{model_width}}"



        print(row)



    print(DIVIDER)





def print_script(

    model_name: str,

    result: dict[str, Any] | None,

) -> None:

    print(f"\n{'─' * 100}")

    print(f"SCRIPT: {model_name}")

    print(f"{'─' * 100}")



    if result is None:

        print("<model request failed>")

        return



    code = result.get("_code", "")



    print(

        f"Model ID: {result['_model_id']} | "

        f"Lines: {len(code.splitlines())}"

    )

    print()

    print(code or "<no code extracted>")





def print_scripts_side_by_side(

    tier_results: dict[str, dict[str, Any] | None],

    column_width: int,

) -> None:

    """

    Print both scripts in two terminal columns.



    Long lines are wrapped so the output remains readable.

    """

    model_names = [name for name, _, _ in MODELS]

    columns: list[list[str]] = []



    for model_name in model_names:

        result = tier_results.get(model_name)



        if result is None:

            code = "<model request failed>"

        else:

            code = result.get("_code", "") or "<no code extracted>"



        wrapped_lines: list[str] = []



        for line_number, line in enumerate(code.splitlines(), start=1):

            expanded = line.expandtabs(4)



            chunks = textwrap.wrap(

                expanded,

                width=max(10, column_width - 6),

                replace_whitespace=False,

                drop_whitespace=False,

                break_long_words=True,

                break_on_hyphens=False,

            )



            if not chunks:

                chunks = [""]



            wrapped_lines.append(f"{line_number:>4} {chunks[0]}")



            for chunk in chunks[1:]:

                wrapped_lines.append(f"{'':>5}{chunk}")



        columns.append(wrapped_lines or ["<no code extracted>"])



    max_rows = max(len(column) for column in columns)

    separator = " | "

    rule = "-+-".join("-" * column_width for _ in columns)



    print(f"\n{DIVIDER}")

    print("GENERATED SCRIPTS SIDE BY SIDE")

    print(DIVIDER)



    print(

        separator.join(

            name.center(column_width)

            for name in model_names

        )

    )

    print(rule)



    for row_index in range(max_rows):

        cells = []



        for column in columns:

            value = (

                column[row_index]

                if row_index < len(column)

                else ""

            )



            cells.append(value[:column_width].ljust(column_width))



        print(separator.join(cells))



    print(rule)





def print_ranking(

    tier: int,

    tier_results: dict[str, dict[str, Any] | None],

) -> None:

    valid = [

        (name, result)

        for name, result in tier_results.items()

        if result is not None

    ]



    valid.sort(

        key=lambda item: item[1]["total"],

        reverse=True,

    )



    print(f"\nTIER {tier} RANKING")

    print(THIN_DIVIDER)



    for rank, (name, result) in enumerate(valid, start=1):

        exec_flag = (

            " [EXEC ERROR]"

            if result["_exec_error"]

            else ""

        )



        print(

            f"  {rank}. {name:<15} "

            f"{result['total']:>6.1f} / 100"

            f"{exec_flag}"

        )



    if len(valid) == 2:

        gap = valid[0][1]["total"] - valid[1][1]["total"]



        print(

            f"\n  Score difference: "

            f"{valid[0][0]} leads by {gap:.1f} points"

        )





def print_output_summary(

    model_name: str,

    result: dict[str, Any] | None,

) -> None:

    """Print generated record counts and duplicate IDs."""

    if result is None:

        return



    dest_store = result["_dest_store"]



    print(f"\nDESTINATION OUTPUT: {model_name}")

    print(THIN_DIVIDER)



    for entity, records in sorted(dest_store.items()):

        ids = [record.get("id") for record in records]

        unique_ids = set(ids)

        duplicate_count = len(ids) - len(unique_ids)



        print(

            f"  {entity:<15} "

            f"records={len(records):<4} "

            f"unique_ids={len(unique_ids):<4} "

            f"duplicates={duplicate_count}"

        )





def print_final_summary(

    all_results: dict[str, dict[int, dict[str, Any] | None]],

    tiers: list[int],

) -> None:

    model_width = 20

    tier_width = 12



    print(f"\n{DIVIDER}")

    print("FINAL SUMMARY")

    print(DIVIDER)



    header = f"{'Model':<{model_width}}"



    for tier in tiers:

        header += f"{f'Tier {tier}':>{tier_width}}"



    header += f"{'Average':>{tier_width}}"

    header += f"{'Errors':>12}"



    print(header)

    print(THIN_DIVIDER)



    for model_name, _, _ in MODELS:

        row = f"{model_name:<{model_width}}"

        scores: list[float] = []

        errors = 0



        for tier in tiers:

            result = all_results.get(model_name, {}).get(tier)



            if result is None:

                row += f"{'ERR':>{tier_width}}"

                errors += 1

                continue



            row += f"{result['total']:>{tier_width}.1f}"

            scores.append(result["total"])



            if result["_exec_error"]:

                errors += 1



        average = (

            sum(scores) / len(scores)

            if scores

            else 0.0

        )



        row += f"{average:>{tier_width}.1f}"

        row += f"{f'{errors}/{len(tiers)}':>12}"



        print(row)



    print(DIVIDER)





def main() -> None:

    parser = argparse.ArgumentParser()



    parser.add_argument(

        "--tiers",

        nargs="+",

        type=int,

        default=[3],

        help="Difficulty tiers to run. Default: 3",

    )



    parser.add_argument(

        "--n-records",

        type=int,

        default=3,

        help="Source records generated per entity. Default: 3",

    )



    parser.add_argument(

        "--no-scripts",

        action="store_true",

        help="Do not print generated migration scripts.",

    )



    parser.add_argument(

        "--sequential-scripts",

        action="store_true",

        help=(

            "Print scripts sequentially instead of in two terminal columns."

        ),

    )



    parser.add_argument(

        "--script-column-width",

        type=int,

        default=55,

        help="Width of each script column. Default: 55",

    )



    parser.add_argument(

        "--output-summary",

        action="store_true",

        help="Show record and duplicate counts for every destination entity.",

    )



    args = parser.parse_args()



    if args.n_records < 1:

        parser.error("--n-records must be at least 1")



    print(DIVIDER)

    print("INITIALISING MODEL CLIENTS")

    print(DIVIDER)



    clients: list[tuple[str, str, Any]] = []



    for display_name, model_id, factory in MODELS:

        try:

            client = factory()

            clients.append((display_name, model_id, client))



            print(

                f"  OK  {display_name:<15} "

                f"{model_id}"

            )



        except Exception as exc:

            print(

                f"  FAILED  {display_name} ({model_id}): "

                f"{type(exc).__name__}: {exc}"

            )

            sys.exit(1)



    all_results: dict[

        str,

        dict[int, dict[str, Any] | None],

    ] = {

        display_name: {}

        for display_name, _, _ in MODELS

    }



    for tier in args.tiers:

        print(f"\n{DIVIDER}")

        print(f"TIER {tier} — GENERATING ONE SHARED MIGRATION")

        print(DIVIDER)



        task = orchestrate(tier)



        source_data = generate_source_data(

            task.source_schema,

            n=args.n_records,

            gemini_model=None,

        )



        dest_schema = task.dest_schema

        entity_map = None

        field_maps = None



        if tier == 3:

            dest_schema, entity_map, field_maps = (

                obfuscate_dest_schema(dest_schema)

            )



        source_data_snapshot = copy.deepcopy(source_data)

        source_schema_snapshot = copy.deepcopy(task.source_schema)

        dest_schema_snapshot = copy.deepcopy(dest_schema)

        entity_map_snapshot = copy.deepcopy(entity_map)

        field_maps_snapshot = copy.deepcopy(field_maps)



        # Build exactly one prompt for both models.

        shared_prompt = build_script_prompt(

            source_schema_snapshot,

            dest_schema_snapshot,

            source_data_snapshot,

        )



        fingerprint = prompt_fingerprint(shared_prompt)



        print(

            "  Source entities : "

            f"{list(source_schema_snapshot['entities'].keys())}"

        )

        print(

            "  Transformations : "

            f"{[t['type'] for t in task.transformations]}"

        )

        print(f"  Source records  : {args.n_records} per entity")

        print(f"  Prompt length   : {len(shared_prompt):,} characters")

        print(f"  Prompt SHA-256  : {fingerprint}")

        print("  Same prompt     : YES")



        tier_results: dict[

            str,

            dict[str, Any] | None,

        ] = {}



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



            except Exception as exc:

                print(

                    f"    MODEL ERROR: "

                    f"{type(exc).__name__}: {exc}"

                )



                tier_results[display_name] = None

                all_results[display_name][tier] = None



        print_score_table(tier, tier_results)

        print_ranking(tier, tier_results)



        if args.output_summary:

            for display_name, _, _ in MODELS:

                print_output_summary(

                    display_name,

                    tier_results.get(display_name),

                )



        if not args.no_scripts:

            if args.sequential_scripts:

                for display_name, _, _ in MODELS:

                    print_script(

                        display_name,

                        tier_results.get(display_name),

                    )

            else:

                print_scripts_side_by_side(

                    tier_results,

                    column_width=args.script_column_width,

                )



    print_final_summary(all_results, args.tiers)





if __name__ == "__main__":

    main()
