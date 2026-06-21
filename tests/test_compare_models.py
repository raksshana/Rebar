"""
Compare models on identical schemas.

Generates N episodes once, then runs every model on the same
(schema, source_data) so scores are directly comparable.

Usage:
    python tests/test_compare_models.py
    python tests/test_compare_models.py --tiers 3 --n 3
"""
import argparse
import builtins
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.orchestration import orchestrate
from generator.difficulty_dial import obfuscate_dest_schema, translate_dest_data
from generator.data_generation import generate_source_data, make_gemini_model
from agent.wrapper import AnthropicClient, OpenAIClient, FireworksClient, _extract_code, _exec_script
from agent.prompt import build_script_prompt


# ---------------------------------------------------------------------------
# Shared Gemini data client
# ---------------------------------------------------------------------------

_gemini_data_client = None

def _get_gemini_data_client():
    global _gemini_data_client
    if _gemini_data_client is None:
        try:
            _gemini_data_client = make_gemini_model()
        except Exception:
            pass
    return _gemini_data_client


# ---------------------------------------------------------------------------
# Episode generation (schema + data, no model call yet)
# ---------------------------------------------------------------------------

def generate_episodes(tiers: list[int], n: int) -> list[dict]:
    """Generate n episodes per tier. Returns list of episode dicts."""
    episodes = []
    for tier in tiers:
        for i in range(n):
            print(f"  Generating tier {tier} episode {i + 1}/{n}...")
            task = orchestrate(tier)
            source_data = generate_source_data(
                task.source_schema, n=3, gemini_model=_get_gemini_data_client()
            )

            dest_schema = task.dest_schema
            entity_map, field_maps = None, None
            if tier == 3:
                dest_schema, entity_map, field_maps = obfuscate_dest_schema(dest_schema)

            prompt = build_script_prompt(task.source_schema, dest_schema, source_data)

            episodes.append({
                "tier": tier,
                "index": i + 1,
                "task": task,
                "source_data": source_data,
                "dest_schema": dest_schema,
                "entity_map": entity_map,
                "field_maps": field_maps,
                "prompt": prompt,
            })
    return episodes


# ---------------------------------------------------------------------------
# Run one model on a pre-generated episode
# ---------------------------------------------------------------------------

def run_on_episode(client: AnthropicClient, episode: dict, verbose: bool = False) -> dict:
    raw_response = client.generate_text(
        messages=[{"role": "user", "content": episode["prompt"]}],
        system_prompt="",
    )

    code = _extract_code(raw_response)
    dest_store: dict = {}

    def write_dest(entity: str, records: list) -> dict:
        dest_store.setdefault(entity, []).extend(records)
        return {"written": len(records), "errors": []}

    exec_result = _exec_script(code, {
        "source_data": episode["source_data"],
        "write_dest": write_dest,
        "source_schema": episode["task"].source_schema,
        "dest_schema": episode["dest_schema"],
        "__builtins__": builtins,
    })

    if exec_result["error"]:
        print(f"      [exec error] {exec_result['stderr'].strip()}")

    if verbose:
        print(f"      --- generated code ---")
        for line in code.splitlines():
            print(f"      {line}")
        if exec_result["stdout"].strip():
            print(f"      --- stdout ---")
            print(f"      {exec_result['stdout'].strip()}")
        if exec_result["stderr"].strip():
            print(f"      --- stderr ---")
            print(f"      {exec_result['stderr'].strip()}")
        print(f"      --- dest_store entities: {list(dest_store.keys())} ---")

    real_dest = (
        translate_dest_data(dest_store, episode["entity_map"], episode["field_maps"])
        if episode["tier"] == 3 else dest_store
    )
    return episode["task"].grader.grade(episode["source_data"], real_dest)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tiers", nargs="+", type=int, default=[2, 3])
    parser.add_argument("--n", type=int, default=5, help="Episodes per tier")
    parser.add_argument("--verbose", action="store_true", help="Print generated code for each episode")
    args = parser.parse_args()

    _fw = lambda m: FireworksClient(f"accounts/fireworks/models/{m}")

    class GeminiClient:
        def __init__(self):
            from google import genai
            self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        def generate_text(self, messages, system_prompt=""):
            prompt = messages[0]["content"]
            return self._client.models.generate_content(model="gemini-2.5-flash", contents=prompt).text

    _account = "vihari5tejo-c218bcay"
    _dep = lambda dep_id: FireworksClient(f"accounts/{_account}/deployments/{dep_id}")

    models = {
        "kimi-k2p5": _dep("metnvyc4"),
        "kimi-k2p6": _dep("dpj8h9ep"),
    }

    print(f"Generating {args.n} episode(s) per tier {args.tiers}...")
    episodes = generate_episodes(args.tiers, args.n)
    print(f"Generated {len(episodes)} episodes total.\n")

    # results[model][tier] = list of total scores
    results: dict[str, dict[int, list[float]]] = {m: {t: [] for t in args.tiers} for m in models}

    for ep_idx, episode in enumerate(episodes):
        tier = episode["tier"]
        print(f"Episode {ep_idx + 1} (tier {tier}):")
        for model_name, client in models.items():
            print(f"  Running {model_name}...")
            try:
                result = run_on_episode(client, episode, verbose=args.verbose)
                results[model_name][tier].append(result["total"])
                print(f"    coverage={result['coverage']:.2f}  "
                      f"field_fidelity={result['field_fidelity']:.2f}  "
                      f"structural={result.get('structural', 1.0):.2f}  "
                      f"total={result['total']:.1f}")
            except Exception as e:
                print(f"    ERROR: {type(e).__name__}: {e}")
                results[model_name][tier].append(0.0)
        print()

    # Summary table
    col = 20
    print("=" * (12 + col * len(models)))
    print(f"{'':12}" + "".join(f"{m:>{col}}" for m in models))
    print("-" * (12 + col * len(models)))
    for tier in args.tiers:
        scores_per_model = {m: results[m][tier] for m in models}
        row = f"Tier {tier:<7}"
        for m in models:
            s = scores_per_model[m]
            avg = sum(s) / len(s) if s else 0.0
            row += f"{avg:>{col}.1f}"
        print(row)

        # Per-episode breakdown
        for i in range(args.n):
            row = f"  ep {i + 1:<8}"
            for m in models:
                s = results[m][tier]
                val = s[i] if i < len(s) else 0.0
                row += f"{val:>{col}.1f}"
            print(row)
        print()
    print("=" * (12 + col * len(models)))


if __name__ == "__main__":
    main()
