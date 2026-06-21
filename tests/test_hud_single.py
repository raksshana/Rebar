"""HUD diagnostic — smoke test for the migrate template via Taskset."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hud import LocalRuntime
from hud.eval import Taskset
from hud.agents import create_agent


async def test_migrate_hud():
    print("\n=== Test: migrate template via HUD ===")
    from harness.env import migrate

    agent = create_agent("claude-sonnet-4-6")
    task = migrate(tier=3)
    print(f"task: {task}")
    job = await Taskset("rebar-migrate", [task]).run(
        agent, runtime=LocalRuntime("harness/env.py")
    )
    print(f"job.runs: {job.runs}")
    for run in job.runs:
        print(f"  reward={run.reward}")


if __name__ == "__main__":
    asyncio.run(test_migrate_hud())
