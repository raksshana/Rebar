"""
Smoke test for the GRPO rollout-and-grade loop.

Loads 2 task rows from tasks/taskset_smoke.jsonl, generates 4 rollouts per
task using Claude Sonnet (stand-in for Qwen — see TODO), scores each via
run_rollout, and asserts that at least one task group has non-identical rewards
(the minimum GRPO signal check).

# TODO: swap _call_model to Qwen via Fireworks once FIREWORKS_API_KEY is wired
"""
from __future__ import annotations

import json
import os
import sys
import time

import anthropic

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
# Import hud_env directly to avoid harness/__init__.py pulling in the hud package
sys.path.insert(0, os.path.join(_ROOT, "harness"))

from migration_episode import build_episode
from hud_env import run_rollout

TASKSET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tasks", "taskset_smoke.jsonl",
)
N_ROLLOUTS = 4
TEMPERATURE = 0.7
MODEL = "claude-sonnet-4-6"  # TODO: swap to Qwen via Fireworks


def _call_model(prompt: str) -> str:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=8096,
        temperature=TEMPERATURE,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _load_tasks() -> list[dict]:
    with open(TASKSET_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def test_smoke():
    tasks = _load_tasks()
    assert tasks, "taskset_smoke.jsonl is empty"

    t_start = time.time()
    all_rewards: list[list[float]] = []
    passed = True
    failure_reason = ""

    for task_row in tasks:
        slug = task_row.get("slug", task_row["args"])
        args = task_row["args"]
        print(f"\n── {slug} (seed={args['seed']}, tier={args['tier']}) ──")

        episode = build_episode(
            seed=args["seed"],
            tier=args["tier"],
            n_records=args["n_records"],
        )

        rewards: list[float] = []
        for i in range(N_ROLLOUTS):
            response = _call_model(episode.prompt)
            detail: dict = {}
            reward = run_rollout(task_row, response, detail=detail)
            rewards.append(reward)

            err_flag = " [EXEC ERROR]" if detail.get("exec_error") else ""
            if detail.get("exec_stderr"):
                err_flag += f" stderr: {detail['exec_stderr'][:120].strip()}"
            print(f"  rollout {i+1}: reward={reward:.4f}{err_flag}")

        variance = (
            sum((r - sum(rewards) / len(rewards)) ** 2 for r in rewards) / len(rewards)
        )
        print(f"  variance: {variance:.6f}")
        all_rewards.append(rewards)

    elapsed = time.time() - t_start

    # GRPO health check: at least one group must have non-identical rewards
    any_varied = any(len(set(rewards)) > 1 for rewards in all_rewards)
    if not any_varied:
        passed = False
        failure_reason = (
            "all rollout groups returned identical rewards — "
            "GRPO would have no learning signal. "
            f"Try raising TEMPERATURE above {TEMPERATURE}."
        )

    print(f"\nwall-clock: {elapsed:.1f}s")
    if passed:
        print("SMOKE TEST PASSED")
    else:
        print(f"SMOKE TEST FAILED: {failure_reason}")

    assert passed, failure_reason


if __name__ == "__main__":
    test_smoke()
