"""Minimal HUD diagnostic — runs one episode and prints the raw job object."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hud.eval import Taskset
from hud.runtime import LocalRuntime
from hud.agents import create_agent
from harness.env import migrate


async def main():
    agent = create_agent("claude-sonnet-4-6")
    task = migrate(tier=2)

    print(f"task type: {type(task)}")
    print(f"task: {task}")

    job = await Taskset([task]).run(agent, runtime=LocalRuntime("harness/env.py"))

    print(f"\njob type: {type(job)}")
    print(f"job: {job}")
    print(f"job.results type: {type(job.results)}")
    print(f"job.results: {job.results}")
    print(f"job.runs: {getattr(job, 'runs', 'ATTR NOT FOUND')}")


if __name__ == "__main__":
    asyncio.run(main())
