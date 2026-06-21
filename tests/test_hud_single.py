"""HUD diagnostic — tests minimal template and manual template execution."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hud import Environment, LocalRuntime
from hud.eval import Taskset
from hud.agents import create_agent


# ── Test 1: minimal env with no external imports ───────────────────────────

_minimal_env = Environment(name="rebar-test-minimal")

@_minimal_env.template()
async def simple_task():
    answer = yield "What is 2+2? Reply with just the number."
    yield 1.0 if answer and "4" in answer else 0.0


# ── Test 2: minimal env via HUD Taskset ───────────────────────────────────

async def test_minimal_hud():
    print("\n=== Test: minimal Taskset (name, [task]) ===")
    agent = create_agent("claude-sonnet-4-6")
    task = simple_task()
    print(f"task: {task}")
    job = await Taskset("rebar-test", [task]).run(agent)
    print(f"job.runs: {job.runs}")
    print(f"job.results: {job.results}")
    for run in job.runs:
        print(f"  reward={run.reward}")


# ── Test 3: real migrate template ─────────────────────────────────────────

async def test_migrate_hud():
    print("\n=== Test: migrate template via HUD ===")
    from harness.env import migrate
    agent = create_agent("claude-sonnet-4-6")
    task = migrate(tier=3)
    print(f"task: {task}")
    job = await Taskset("rebar-migrate", [task]).run(agent, runtime=LocalRuntime("harness/env.py"))
    print(f"job.runs: {job.runs}")
    for run in job.runs:
        print(f"  reward={run.reward}")


async def main():
    await test_minimal_hud()
    await test_migrate_hud()


if __name__ == "__main__":
    asyncio.run(main())
