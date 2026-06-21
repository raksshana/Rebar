import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hud import Environment

from migration_episode import build_episode
from agent.wrapper import _extract_code, _exec_script, _RESTRICTED_BUILTINS
from generator.difficulty_dial import translate_dest_data

env = Environment(name="rebar-migration")


@env.template()
async def migrate(seed: int, tier: int = 3, n_records: int = 3):
    # Same (seed, tier, n_records) → identical task every time.
    # All group_size GRPO repetitions of this task must pass the same seed.
    episode = build_episode(seed=seed, tier=tier, n_records=n_records)

    raw_response = yield episode.prompt

    code = _extract_code(raw_response)
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

    if exec_result["error"]:
        print("[exec_error] " + exec_result["stderr"].strip())

    if tier == 3:
        real_dest = translate_dest_data(dest_store, episode.entity_map, episode.field_maps)
    else:
        real_dest = dest_store

    grade = episode.task.grader.grade(episode.source_data, real_dest)
    print(
        f"[grader] seed={seed} "
        f"exec_error={exec_result['error']} "
        f"entities={list(dest_store.keys())} "
        f"grade={grade['total']:.1f}"
    )
    yield grade["total"] / 100.0
