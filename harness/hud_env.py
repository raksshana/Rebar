"""
HUD environment entry point for the rebar-migration task.

run_rollout(task_row, model_response_text) -> float
  Rebuilds the episode deterministically from the task row's seed, executes
  the model's migration script against it, and returns the grader's total
  reward in [0, 1].
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migration_episode import build_episode
from generator.difficulty_dial import translate_dest_data
from agent.wrapper import _extract_code, _exec_script, _RESTRICTED_BUILTINS


def run_rollout(
    task_row: dict,
    model_response_text: str,
    detail: dict | None = None,
) -> float:
    """
    Grade a single model rollout against the episode defined by task_row.

    task_row must have an "args" key with seed, tier, and n_records.
    Returns reward in [0, 1]. If detail is provided (a mutable dict), it is
    populated with exec_error (bool) and exec_stderr (str) for diagnostics.
    """
    args = task_row["args"]
    episode = build_episode(
        seed=args["seed"],
        tier=args["tier"],
        n_records=args["n_records"],
    )

    code = _extract_code(model_response_text)

    dest_store: dict = {}

    def write_dest(entity: str, records: list) -> dict:
        dest_store.setdefault(entity, []).extend(records)
        return {"written": len(records), "errors": []}

    exec_result = _exec_script(code, {
        "source_data": episode.source_data,
        "write_dest": write_dest,
        "source_schema": episode.task.source_schema,
        "dest_schema": episode.shown_dest_schema,
        "__builtins__": _RESTRICTED_BUILTINS,
    })

    if detail is not None:
        detail["exec_error"] = exec_result["error"]
        detail["exec_stderr"] = exec_result["stderr"]

    if args["tier"] == 3:
        real_dest = translate_dest_data(dest_store, episode.entity_map, episode.field_maps)
    else:
        real_dest = dest_store

    grade = episode.task.grader.grade(episode.source_data, real_dest)
    return grade["total"] / 100.0
