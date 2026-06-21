"""
HUD online RL training loop for Rebar.

Usage:
    python -m harness.train --model rebar-rl --tier 3 --rounds 20 --group 8

Prereqs:
    hud models fork moonshot-ai/kimi-k2.7-code --name rebar-rl
"""
import argparse
import asyncio

from hud import LocalRuntime
from hud.eval import Taskset, Job
from hud.agents import create_agent
from hud.training import TrainingClient

from harness.env import migrate


async def train(
    model_name: str,
    tier: int = 3,
    rounds: int = 20,
    group_size: int = 8,
    learning_rate: float = 1e-5,
):
    """
    Online RL loop:
      for each round:
        1. run group_size episodes with current model weights
        2. pass runs to TrainingClient.step() to update weights
        3. print mean reward
    """
    agent = create_agent(
        model_name,
        completion_kwargs={"extra_body": {"return_token_ids": True}},
    )
    trainer = TrainingClient(model_name)
    runtime = LocalRuntime("harness/env.py")

    session = await Job.start(model_name, group=group_size)

    print(f"Starting training: model={model_name} tier={tier} rounds={rounds} group={group_size}")
    print(f"Job ID: {session.id}\n")

    for round_num in range(1, rounds + 1):
        start_idx = len(session.runs)

        tasks = [migrate(tier=tier) for _ in range(group_size)]
        await Taskset(f"rebar-train-r{round_num}", tasks).run(
            agent,
            runtime=runtime,
            job=session,
        )

        batch = session.runs[start_idx:]
        rewards = [r.reward for r in batch if r.reward is not None]
        mean_reward = sum(rewards) / len(rewards) if rewards else 0.0

        print(f"Round {round_num:>3}/{rounds} — mean reward: {mean_reward:.3f}  ({len(rewards)} runs)")

        if rewards:
            await trainer.step(batch, learning_rate=learning_rate, group_size=group_size)

    print("\nTraining complete.")
    print(f"Run: hud models checkpoints {model_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Forked model name, e.g. rebar-rl")
    parser.add_argument("--tier", type=int, default=3)
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--group", type=int, default=8, help="Episodes per round (GRPO group size)")
    parser.add_argument("--lr", type=float, default=1e-5)
    args = parser.parse_args()

    asyncio.run(train(
        model_name=args.model,
        tier=args.tier,
        rounds=args.rounds,
        group_size=args.group,
        learning_rate=args.lr,
    ))
