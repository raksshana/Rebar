"""Tier 3 migration tasks for HUD eval and RL training."""

from harness.env import migrate

tasks = [
    migrate(tier=3).model_copy(update={"slug": f"rebar-t3-{i:02d}"})
    for i in range(1, 21)
]
