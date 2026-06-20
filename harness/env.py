import builtins

from hud import Environment

from agent.wrapper import _extract_code, _exec_script
from agent.prompt import build_script_prompt
from generator.schema_generation import get_schema
from generator.schema import validate_schema
from generator.difficulty_dial import apply_difficulty, obfuscate_dest_schema, translate_dest_data
from generator.data_generation import generate_source_data, make_gemini_model

env = Environment(name="rebar-migration")

# Gemini model — initialized once on first episode, None if key not set
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


def _generate_episode(tier: int) -> tuple:
    """Generate one migration episode. Retries until schema is valid (max 10 attempts)."""
    source_schema = None
    for _ in range(10):
        candidate = get_schema(tier)
        if not validate_schema(candidate):   # empty list = valid
            source_schema = candidate
            break
    if source_schema is None:
        source_schema = get_schema(tier)     # use last attempt if all failed validation

    dest_schema, transformations = apply_difficulty(source_schema, tier)
    source_data = generate_source_data(source_schema, n=3, gemini_model=_get_gemini())
    return source_schema, dest_schema, transformations, source_data


# ── Stub grader (replace with Grader(...).grade(...) once grader module is ready) ──

def _stub_grade(source_data: dict, dest_store: dict) -> float:
    """Coverage-only grade — replace with real Grader."""
    total, hits = 0, 0
    for entity, records in source_data.items():
        dest_ids = {r.get("id") for r in dest_store.get(entity, [])}
        for rec in records:
            total += 1
            if rec["id"] in dest_ids:
                hits += 1
    return (hits / total * 100.0) if total else 0.0


# ── HUD environment template ───────────────────────────────────────────────

@env.template()
async def migrate(tier: int = 2):
    source_schema, dest_schema, transformations, source_data = _generate_episode(tier)

    # Tier 3: obfuscate dest schema before showing it to the model
    entity_map, field_maps = None, None
    if tier == 3:
        dest_schema, entity_map, field_maps = obfuscate_dest_schema(dest_schema)

    prompt = build_script_prompt(source_schema, dest_schema, source_data)
    raw_response = yield prompt

    code = _extract_code(raw_response)
    dest_store: dict = {}

    def write_dest(entity: str, records: list) -> dict:
        dest_store.setdefault(entity, []).extend(records)
        return {"written": len(records), "errors": []}

    _exec_script(code, {
        "source_data": source_data,
        "write_dest": write_dest,
        "source_schema": source_schema,
        "dest_schema": dest_schema,
        "__builtins__": builtins,
    })

    # Tier 3: reverse obfuscation so grader sees real names
    real_dest = translate_dest_data(dest_store, entity_map, field_maps) if tier == 3 else dest_store

    score = _stub_grade(source_data, real_dest)
    yield score / 100.0
