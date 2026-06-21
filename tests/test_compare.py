"""
Compare models on identical migrations (same schema + source data per episode).
Source data is generated with Faker only — no Gemini data call.

Generated scripts are saved to scripts/tier{T}_ep{N}_{model}.py.
Terminal output shows only grades.

Usage:
    python tests/test_compare.py [--tiers 2 3] [--n 5]
"""
import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.orchestration import orchestrate
from generator.difficulty_dial import obfuscate_dest_schema, translate_dest_data
from generator.data_generation import generate_source_data
from agent.wrapper import AnthropicClient, OpenAIClient, _extract_code, _exec_script, _RESTRICTED_BUILTINS
from agent.prompt import build_script_prompt


class GeminiClient:
    def __init__(self, model: str = "gemini-2.5-flash"):
        from google import genai
        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self._model = model

    def generate_text(self, messages: list[dict], system_prompt: str = "") -> str:
        prompt = messages[0]["content"]
        return self._client.models.generate_content(model=self._model, contents=prompt).text


MODELS = [
    ("claude-opus-4-8",   lambda: AnthropicClient("claude-opus-4-8")),
    ("claude-sonnet-4-6", lambda: AnthropicClient("claude-sonnet-4-6")),
    ("gpt-5.5",           lambda: OpenAIClient("gpt-5.5")),
    ("gemini-2.5-flash",  lambda: GeminiClient()),
]

DIVIDER = "=" * 70
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


def _call_model(client, prompt: str) -> str:
    return client.generate_text(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="",
    )


def _save_script(tier: int, ep_idx: int, model_name: str, code: str, run_id: str) -> str:
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    safe_name = model_name.replace("/", "_").replace(".", "_")
    filename = f"tier{tier}_ep{ep_idx}_{safe_name}_{run_id}.py"
    path = os.path.join(SCRIPTS_DIR, filename)
    with open(path, "w") as f:
        f.write(code)
    return path


def run_episode(client, task, source_data, dest_schema, tier: int,
                entity_map=None, field_maps=None, model_name: str = "",
                ep_idx: int = 1, run_id: str = "") -> dict:
    """Run one migration episode for a single model on a pre-built task."""
    prompt = build_script_prompt(task.source_schema, dest_schema, source_data)
    raw_response = _call_model(client, prompt)
    code = _extract_code(raw_response)

    script_path = _save_script(tier, ep_idx, model_name, code, run_id)

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

    if exec_result["error"]:
        print(f"  !! EXEC ERROR [{model_name}] {exec_result['stderr'].strip()[:120]}")

    real_dest = translate_dest_data(dest_store, entity_map, field_maps) if tier == 3 else dest_store
    result = task.grader.grade(source_data, real_dest)
    result["_code"] = code
    result["_exec_error"] = exec_result["error"]
    result["_stderr"] = exec_result["stderr"]
    result["_script_path"] = script_path
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tiers", nargs="+", type=int, default=[3])
    parser.add_argument("--n", type=int, default=5, help="Migrations to generate per tier")
    args = parser.parse_args()
    run_id = datetime.now().strftime("%H%M%S")

    # Build all clients up front so a missing API key fails fast.
    clients = []
    for name, factory in MODELS:
        try:
            clients.append((name, factory()))
        except Exception as e:
            print(f"Could not initialise {name}: {e}")
            sys.exit(1)

    # results[model][tier] = list of scores (one per episode)
    all_scores = {name: {tier: [] for tier in args.tiers} for name, _ in clients}

    for tier in args.tiers:
        for ep_idx in range(args.n):
            print(f"\n{DIVIDER}")
            print(f"TIER {tier}  —  migration {ep_idx + 1}/{args.n}")
            print(DIVIDER)
            task = orchestrate(tier)
            source_data = generate_source_data(task.source_schema, n=3, gemini_model=None)

            dest_schema = task.dest_schema
            entity_map, field_maps = None, None
            if tier == 3:
                dest_schema, entity_map, field_maps = obfuscate_dest_schema(dest_schema)

            print(f"  Entities  : {list(task.source_schema['entities'].keys())}")
            print(f"  Transforms: {[t['type'] for t in task.transformations]}")

            col = 16
            header = f"  {'metric':<28}" + "".join(f"{n:>{col}}" for n, _ in clients)
            print(header)
            print("  " + "-" * (28 + col * len(clients)))

            ep_results = {}
            for model_name, client in clients:
                try:
                    result = run_episode(
                        client, task, source_data, dest_schema, tier,
                        entity_map=entity_map, field_maps=field_maps,
                        model_name=model_name, ep_idx=ep_idx + 1, run_id=run_id,
                    )
                    ep_results[model_name] = result
                    all_scores[model_name][tier].append(result["total"])
                except Exception as e:
                    print(f"    {model_name} ERROR: {type(e).__name__}: {e}")
                    ep_results[model_name] = None
                    all_scores[model_name][tier].append(0.0)

            for metric in ("coverage", "field_fidelity", "relationship_integrity", "type_correctness", "structural", "total"):
                row_vals = []
                for model_name, _ in clients:
                    r = ep_results.get(model_name)
                    if r and metric in r:
                        row_vals.append(f"{r[metric]:.2f}" if metric != "total" else f"{r[metric]:.1f}")
                    elif r and metric == "total":
                        row_vals.append("ERR")
                    else:
                        row_vals.append("-")
                if any(v not in ("-", "ERR") for v in row_vals):
                    print(f"  {metric:<28}" + "".join(f"{v:>{col}}" for v in row_vals))

    # Summary table
    print(f"\n{DIVIDER}")
    print(f"SUMMARY  ({args.n} migrations per tier)")
    col = 16
    print(f"  {'model':<24}" + "".join(f"  tier {t}" for t in args.tiers))
    print("  " + "-" * (24 + 8 * len(args.tiers)))
    for model_name, _ in clients:
        row = f"  {model_name:<24}"
        for tier in args.tiers:
            scores = all_scores[model_name][tier]
            avg = sum(scores) / len(scores) if scores else 0.0
            row += f"  {avg:>5.1f}"
        print(row)
    print(DIVIDER)


if __name__ == "__main__":
    main()
