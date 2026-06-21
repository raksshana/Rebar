"""
Baseline test: run one tier-2 and one tier-3 episode for each model directly,
without HUD. Prints grader breakdown per (model, tier).

Usage:
    python tests/test_baseline.py [--tiers 2 3] [--models claude gemini gpt]
"""
import argparse
import builtins
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.orchestration import orchestrate
from generator.difficulty_dial import obfuscate_dest_schema, translate_dest_data
from generator.data_generation import generate_source_data, make_gemini_model
from agent.wrapper import AnthropicClient, OpenAIClient, _extract_code, _exec_script
from agent.prompt import build_script_prompt


# ---------------------------------------------------------------------------
# Thin Gemini wrapper matching AnthropicClient's interface
# ---------------------------------------------------------------------------

class GeminiClient:
    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None):
        from google import genai
        self.model = model
        self._client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY"])

    def generate_text(self, prompt: str) -> str:
        response = self._client.models.generate_content(model=self.model, contents=prompt)
        return response.text


def _call_model(client, prompt: str) -> str:
    """Unified call regardless of client type."""
    if isinstance(client, AnthropicClient):
        return client.generate_text(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="",
        )
    if isinstance(client, OpenAIClient):
        return client.generate_text(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="",
        )
    return client.generate_text(prompt)


# ---------------------------------------------------------------------------
# Single episode runner
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


def run_episode(client, tier: int) -> dict:
    """Run one migration episode and return the full grader result dict."""
    task = orchestrate(tier)
    source_data = generate_source_data(task.source_schema, n=3, gemini_model=_get_gemini_data_client())

    dest_schema = task.dest_schema
    entity_map, field_maps = None, None
    if tier == 3:
        dest_schema, entity_map, field_maps = obfuscate_dest_schema(dest_schema)

    prompt = build_script_prompt(task.source_schema, dest_schema, source_data)
    raw_response = _call_model(client, prompt)

    code = _extract_code(raw_response)
    dest_store: dict = {}

    def write_dest(entity: str, records: list) -> dict:
        dest_store.setdefault(entity, []).extend(records)
        return {"written": len(records), "errors": []}

    exec_result = _exec_script(code, {
        "source_data": source_data,
        "write_dest": write_dest,
        "source_schema": task.source_schema,
        "dest_schema": dest_schema,
        "__builtins__": builtins,
    })

    if exec_result["error"]:
        print(f"    [exec error] {exec_result['stderr'].strip()}")

    real_dest = translate_dest_data(dest_store, entity_map, field_maps) if tier == 3 else dest_store
    return task.grader.grade(source_data, real_dest)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tiers", nargs="+", type=int, default=[2, 3])
    parser.add_argument("--models", nargs="+", default=["claude", "gemini", "gpt"],
                        help="Any subset of: claude gemini gpt")
    args = parser.parse_args()

    all_models = {
        "claude": ("claude-opus-4-8", lambda: AnthropicClient("claude-opus-4-8")),
        "gemini": ("gemini-2.5-flash",  lambda: GeminiClient("gemini-2.5-flash")),
        "gpt":    ("gpt-5.4",            lambda: OpenAIClient("gpt-5.4")),
    }

    models = {}
    for key in args.models:
        if key not in all_models:
            print(f"Unknown model key '{key}'. Choose from: {list(all_models)}")
            sys.exit(1)
        label, factory = all_models[key]
        try:
            models[label] = factory()
        except Exception as e:
            print(f"Could not initialise {key}: {e}")
            sys.exit(1)

    tiers = args.tiers

    results = {}
    for model_name, client in models.items():
        results[model_name] = {}
        for tier in tiers:
            print(f"\nRunning {model_name} tier {tier}...")
            try:
                result = run_episode(client, tier)
                results[model_name][tier] = result
                print(f"  coverage:               {result['coverage']:.3f}")
                print(f"  field_fidelity:         {result['field_fidelity']:.3f}")
                print(f"  relationship_integrity: {result['relationship_integrity']:.3f}")
                print(f"  type_correctness:       {result['type_correctness']:.3f}")
                if "structural" in result:
                    print(f"  structural:             {result['structural']:.3f}")
                print(f"  TOTAL:                  {result['total']:.1f} / 100")
            except Exception as e:
                print(f"  ERROR: {type(e).__name__}: {e}")
                results[model_name][tier] = None

    # Summary table
    print("\n" + "=" * 60)
    print(f"{'':28}" + "".join(f"  Tier {t}" for t in tiers))
    print("-" * 60)
    for model_name in models:
        row = f"{model_name:<28}"
        for tier in tiers:
            r = results[model_name].get(tier)
            row += f"  {r['total']:>5.1f}" if r else "    ERR"
        print(row)
    print("=" * 60)


if __name__ == "__main__":
    main()
