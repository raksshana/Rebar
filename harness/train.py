"""
HUD online RL training loop for Rebar.

Usage:
    python -m harness.train --model rebar-rl --tier 3 --rounds 20 --group 8 --tasks-per-round 4

Prereqs:
    hud models fork moonshotai/Kimi-K2.5 --name rebar-kimi-k25
"""
import argparse
import asyncio

from hud import LocalRuntime, TrainingClient
from hud.eval import Taskset, Job
from hud.agents import create_agent

from harness.env import migrate


async def train(
    model_name: str,
    tier: int = 3,
    rounds: int = 20,
    group_size: int = 8,
    tasks_per_round: int = 4,
    learning_rate: float = 1e-5,
    max_tokens: int = 10000,
    base_seed: int = 42000,
):
    agent = create_agent(
        model_name,
        completion_kwargs={
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "extra_body": {"return_token_ids": True},
        },
    )
    trainer = TrainingClient(model_name)
    runtime = LocalRuntime("harness/env.py")

    session = await Job.start(model_name, group=group_size)

    print(
        f"Training model={model_name} tier={tier} rounds={rounds} "
        f"group={group_size} tasks_per_round={tasks_per_round} max_tokens={max_tokens}"
    )
    print(f"Job ID: {session.id}\n")

    for round_num in range(1, rounds + 1):
        start_idx = len(session.runs)

        # Each task gets a unique deterministic seed so all group_size GRPO
        # repetitions of that task see the identical schema and source data.
        tasks = []
        for task_index in range(tasks_per_round):
            seed = base_seed + round_num * 1000 + task_index
            tasks.append(
                migrate(seed=seed, tier=tier, n_records=3).model_copy(
                    update={"slug": f"rebar-r{round_num:03d}-task{task_index:02d}-seed{seed}"}
                )
            )

        await Taskset(f"rebar-train-r{round_num}", tasks).run(
            agent,
            runtime=runtime,
            job=session,
        )

        batch = session.runs[start_idx:]
        rewards = [r.reward for r in batch if r.reward is not None]
        mean_reward = sum(rewards) / len(rewards) if rewards else 0.0
        min_r = min(rewards) if rewards else 0.0
        max_r = max(rewards) if rewards else 0.0

        print(
            f"Round {round_num:>3}/{rounds} — "
            f"mean={mean_reward:.3f}  min={min_r:.3f}  max={max_r:.3f}  "
            f"runs={len(rewards)}"
        )

        if rewards:
            await trainer.step(batch, learning_rate=learning_rate, group_size=group_size)

    print("\nTraining complete.")
    print(f"Run: hud models checkpoints {model_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--tier", type=int, default=3)
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--group", type=int, default=8, help="GRPO group size (repetitions per task)")
    parser.add_argument("--tasks-per-round", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--max-tokens", type=int, default=10000)
    parser.add_argument("--base-seed", type=int, default=42000)
    args = parser.parse_args()

    asyncio.run(train(
        model_name=args.model,
        tier=args.tier,
        rounds=args.rounds,
        group_size=args.group,
        tasks_per_round=args.tasks_per_round,
        learning_rate=args.lr,
        max_tokens=args.max_tokens,
        base_seed=args.base_seed,
    ))
