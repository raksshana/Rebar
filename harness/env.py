import sys
import os

# Ensure project root is on sys.path when HUD runs this file in a child process
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hud import Environment

from agent.wrapper import _extract_code, _exec_script, _RESTRICTED_BUILTINS
from agent.prompt import build_script_prompt
from generator.orchestration import orchestrate
from generator.difficulty_dial import obfuscate_dest_schema, translate_dest_data
from generator.data_generation import generate_source_data, make_gemini_model

env = Environment(name="rebar-migration")

# Gemini client — initialized once on first episode, None if key not set
_gemini = None
_gemini_tried = False


def _get_gemini():
    global _gemini, _gemini_tried
    if not _gemini_tried:
        _gemini_tried = True
        try:
            _gemini = make_gemini_model()
        except Exception:
            _gemini = None
    return _gemini


# ── HUD environment template ───────────────────────────────────────────────

@env.template()
async def migrate(tier: int = 2):
    task = orchestrate(tier)
    source_data = generate_source_data(task.source_schema, n=3, gemini_model=_get_gemini())

    dest_schema = task.dest_schema
    entity_map, field_maps = None, None
    if tier == 3:
        dest_schema, entity_map, field_maps = obfuscate_dest_schema(dest_schema)

    prompt = build_script_prompt(task.source_schema, dest_schema, source_data)
    raw_response = yield prompt

    code = _extract_code(raw_response)
    dest_store: dict = {}

    def write_dest(entity: str, records: list) -> dict:
        dest_store.setdefault(entity, []).extend(records)
        return {"written": len(records), "errors": []}

    _exec_script(code, {
        "source_data": source_data,
        "write_dest": write_dest,
        "source_schema": task.source_schema,
        "dest_schema": dest_schema,
        "__builtins__": _RESTRICTED_BUILTINS,
    })

    real_dest = translate_dest_data(dest_store, entity_map, field_maps) if tier == 3 else dest_store

    result = task.grader.grade(source_data, real_dest)
    print(f"[grader] {result}")
    yield result["total"] / 100.0
