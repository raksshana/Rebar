"""
Compare four models on identical tasks (same schema + source data per tier).
Source data is generated with Faker only — no Gemini data call.

Diagnostics built in:
  1. Raw scripts printed for every model (suppress with --no-scripts)
  2. Exec errors shown with full stderr
  3. After each tier, side-by-side script diff for the most-divergent pair

Usage:
    python tests/test_compare.py [--tiers 2 3] [--no-scripts]
"""
import argparse
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.orchestration import orchestrate
from generator.difficulty_dial import obfuscate_dest_schema, translate_dest_data
from generator.data_generation import generate_source_data
from agent.wrapper import AnthropicClient, OpenAIClient, _extract_code, _exec_script, _RESTRICTED_BUILTINS
from agent.prompt import build_script_prompt


MODELS = [
    ("claude-opus-4-8",   lambda: AnthropicClient("claude-opus-4-8")),
    ("claude-sonnet-4-6", lambda: AnthropicClient("claude-sonnet-4-6")),
    ("gpt-5.4",           lambda: OpenAIClient("gpt-5.4")),
    ("gpt-4o",            lambda: OpenAIClient("gpt-4o")),
]

DIVIDER = "=" * 70


def _call_model(client, prompt: str) -> str:
    return client.generate_text(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="",
    )


def _print_script(model_name: str, raw_response: str, extracted_code: str) -> None:
    print(f"\n{'─'*70}")
    print(f"  SCRIPT: {model_name}")
    print(f"{'─'*70}")
    print("[raw response truncated to first 300 chars if long]")
    if len(raw_response) > 300:
        preamble = raw_response[:300].rstrip()
        print(preamble)
        print(f"... [{len(raw_response) - 300} more chars before code block]")
    else:
        print(raw_response)
    print(f"\n[extracted code — {len(extracted_code.splitlines())} lines]")
    print(extracted_code)
    print(f"{'─'*70}")


def _print_exec_result(model_name: str, exec_result: dict) -> None:
    if exec_result["error"]:
        print(f"\n  !! EXEC ERROR [{model_name}]")
        print(f"     stderr: {exec_result['stderr'].strip()}")
        if exec_result["stdout"].strip():
            print(f"     stdout: {exec_result['stdout'].strip()[:400]}")
    else:
        if exec_result["stdout"].strip():
            print(f"  [stdout] {exec_result['stdout'].strip()[:200]}")


def _side_by_side(name_a: str, code_a: str, name_b: str, code_b: str) -> None:
    """Print two scripts sequentially with a clear comparison header."""
    print(f"\n{DIVIDER}")
    print("SCRIPT COMPARISON  (most-divergent pair this tier)")
    print(DIVIDER)
    for name, code in [(name_a, code_a), (name_b, code_b)]:
        print(f"\n>>> {name}  ({len(code.splitlines())} lines)\n")
        print(code)
    print(DIVIDER)


def run_episode(client, task, source_data, dest_schema, tier: int,
                entity_map=None, field_maps=None, print_scripts: bool = True,
                model_name: str = "") -> dict:
    """Run one migration episode for a single model on a pre-built task."""
    prompt = build_script_prompt(task.source_schema, dest_schema, source_data)
    raw_response = _call_model(client, prompt)
    code = _extract_code(raw_response)

    if print_scripts:
        _print_script(model_name, raw_response, code)

    dest_store: dict = {}

    def write_dest(entity: str, records: list) -> dict:
        dest_store.setdefault(entity, []).extend(records)
        return {"written": len(records), "errors": []}

    exec_result = _exec_script(code, {
        "source_data": source_data,
        "write_dest": write_dest,
        "source_schema": task.source_schema,
        "dest_schema": dest_schema,
        "__builtins__": _RESTRICTED_BUILTINS,
    })

    _print_exec_result(model_name, exec_result)

    real_dest = translate_dest_data(dest_store, entity_map, field_maps) if tier == 3 else dest_store
    result = task.grader.grade(source_data, real_dest)
    result["_code"] = code
    result["_exec_error"] = exec_result["error"]
    result["_stderr"] = exec_result["stderr"]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tiers", nargs="+", type=int, default=[3])
    parser.add_argument("--no-scripts", action="store_true",
                        help="Suppress per-model script dump")
    args = parser.parse_args()
    print_scripts = not args.no_scripts

    # Build all clients up front so a missing API key fails fast.
    clients = []
    for name, factory in MODELS:
        try:
            clients.append((name, factory()))
        except Exception as e:
            print(f"Could not initialise {name}: {e}")
            sys.exit(1)

    all_results = {}  # {model_name: {tier: result_dict}}

    for tier in args.tiers:
        print(f"\n{DIVIDER}")
        print(f"TIER {tier}  —  generating shared task + source data (faker only)")
        print(DIVIDER)
        task = orchestrate(tier)
        source_data = generate_source_data(task.source_schema, n=3, gemini_model=None)

        dest_schema = task.dest_schema
        entity_map, field_maps = None, None
        if tier == 3:
            dest_schema, entity_map, field_maps = obfuscate_dest_schema(dest_schema)

        print(f"  Entities  : {list(task.source_schema['entities'].keys())}")
        print(f"  Transforms: {[t['type'] for t in task.transformations]}")

        for model_name, client in clients:
            print(f"\n  Running {model_name}...")
            try:
                result = run_episode(
                    client, task, source_data, dest_schema, tier,
                    entity_map=entity_map, field_maps=field_maps,
                    print_scripts=print_scripts, model_name=model_name,
                )
                all_results.setdefault(model_name, {})[tier] = result
                err_flag = "  [EXEC ERROR]" if result["_exec_error"] else ""
                print(f"    coverage:               {result['coverage']:.3f}")
                print(f"    field_fidelity:         {result['field_fidelity']:.3f}")
                print(f"    relationship_integrity: {result['relationship_integrity']:.3f}")
                print(f"    type_correctness:       {result['type_correctness']:.3f}")
                if "structural" in result:
                    print(f"    structural:             {result['structural']:.3f}")
                print(f"    TOTAL:                  {result['total']:.1f} / 100{err_flag}")
            except Exception as e:
                print(f"    ERROR: {type(e).__name__}: {e}")
                all_results.setdefault(model_name, {})[tier] = None

        # Diagnostic 3: side-by-side scripts for the most-divergent pair
        tier_scores = [
            (name, all_results.get(name, {}).get(tier))
            for name, _ in clients
        ]
        valid = [(name, r) for name, r in tier_scores if r is not None]
        if len(valid) >= 2:
            best  = max(valid, key=lambda x: x[1]["total"])
            worst = min(valid, key=lambda x: x[1]["total"])
            gap = best[1]["total"] - worst[1]["total"]
            if gap >= 5:
                print(f"\n  Most-divergent pair: {best[0]} ({best[1]['total']:.1f}) "
                      f"vs {worst[0]} ({worst[1]['total']:.1f})  [gap={gap:.1f}]")
                _side_by_side(
                    best[0],  best[1]["_code"],
                    worst[0], worst[1]["_code"],
                )

    # Summary table
    tiers = args.tiers
    print(f"\n{DIVIDER}")
    print("SUMMARY")
    print(f"{'Model':<24}" + "".join(f"  Tier {t}" for t in tiers)
          + "  Errors")
    print("-" * 70)
    for model_name, _ in clients:
        row = f"{model_name:<24}"
        errors = 0
        for tier in tiers:
            r = all_results.get(model_name, {}).get(tier)
            if r:
                row += f"  {r['total']:>6.1f}"
                if r["_exec_error"]:
                    errors += 1
            else:
                row += "     ERR"
                errors += 1
        row += f"  {errors}/{len(tiers)} exec errors"
        print(row)
    print(DIVIDER)


if __name__ == "__main__":
    main()
