import asyncio
import os

from hud.eval import Taskset
from hud import LocalRuntime
from hud.agents import create_agent, OpenAIChatAgent
from hud.agents.types import OpenAIChatConfig

from harness.env import migrate

# Models routed through HUD's gateway
_GATEWAY_MODELS = {
    "claude-sonnet": "claude-sonnet-4-6",
    "gemini":        "gemini-3.5-flash",
}

_FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p1-70b-instruct"

TIERS = [2, 3]  # Tier 0/1 not yet implemented in generator


def _build_agents(fireworks_api_key: str | None = None) -> dict:
    agents = {name: create_agent(model_id) for name, model_id in _GATEWAY_MODELS.items()}
    if fireworks_api_key:
        agents["llama-70b"] = OpenAIChatAgent(OpenAIChatConfig(
            model=_FIREWORKS_MODEL,
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=fireworks_api_key,
        ))
    return agents


async def evaluate(
    tiers: list[int] = TIERS,
    n_per_cell: int = 10,
    fireworks_api_key: str | None = None,
) -> dict:
    """Run n_per_cell episodes per (model, tier) and return aggregated scores."""
    agents = _build_agents(fireworks_api_key)
    results = {}

    for label, agent in agents.items():
        results[label] = {}
        for tier in tiers:
            tasks = [migrate(tier=tier) for _ in range(n_per_cell)]
            job = await Taskset(tasks).run(agent, runtime=LocalRuntime("harness/env.py"))

            print(f"\n[debug] {label} tier={tier}: {len(job.runs)} runs")
            for i, run in enumerate(job.runs[:2]):  # show first 2
                print(f"  run[{i}] reward={run.reward} status={getattr(run, 'status', '?')} trace={getattr(run, 'trace', '?')}")

            scores = [
                run.reward * 100
                for run in job.runs
                if run.reward is not None
            ]

            if not scores:
                print(f"[warn] no scores returned for {label} tier={tier}")
                results[label][tier] = {"mean": 0.0, "min": 0.0, "max": 0.0, "n": 0}
                continue

            results[label][tier] = {
                "mean": round(sum(scores) / len(scores), 1),
                "min":  round(min(scores), 1),
                "max":  round(max(scores), 1),
                "n":    len(scores),
            }

    return results


def print_report(results: dict, tiers: list[int] = TIERS) -> None:
    labels = list(results.keys())
    col = 24
    print(f"\n{'':8}" + "".join(f"{l:>{col}}" for l in labels))
    print("-" * (8 + col * len(labels)))
    for tier in tiers:
        row = f"Tier {tier}  "
        for label in labels:
            s = results[label].get(tier)
            cell = f"{s['mean']} ({s['min']}–{s['max']})" if s and s["n"] > 0 else "-"
            row += f"{cell:>{col}}"
        print(row)
    print()


if __name__ == "__main__":
    results = asyncio.run(evaluate(
        fireworks_api_key=os.getenv("FIREWORKS_API_KEY"),
    ))
    print_report(results)
