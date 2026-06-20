import builtins

from hud import Environment

from agent.wrapper import _extract_code, _exec_script
from agent.prompt import build_script_prompt

env = Environment(name="rebar-migration")


# ── Stubs ──────────────────────────────────────────────────────────────────
# Swap these three functions out once the real modules are ready:
#   _stub_orchestrate  → generator.orchestration.orchestrate(tier)
#   _stub_generate_data → generator.data_generation.generate_source_data(schema)
#   _stub_grade        → grader.grader.Grader(source_schema, transforms).grade(source_data, dest)

def _stub_orchestrate(tier: int) -> tuple:
    source_schema = {
        "entities": {
            "User": {
                "fields": {
                    "id":    {"kind": "id"},
                    "name":  {"kind": "text"},
                    "score": {"kind": "number"},
                }
            }
        },
        "nested_blocks": {}
    }
    dest_schema = {
        "entities": {
            "User": {
                "fields": {
                    "id":      {"kind": "id"},
                    "name_v2": {"kind": "text"},
                    "score":   {"kind": "number"},
                }
            }
        },
        "nested_blocks": {}
    }
    transformations = [
        {"type": "rename", "entity": "User", "from": "name", "to": "name_v2"}
    ]
    return source_schema, dest_schema, transformations


def _stub_generate_data(source_schema: dict, n: int = 3) -> dict:
    return {
        "User": [
            {"id": i, "name": f"User{i}", "score": i * 10}
            for i in range(1, n + 1)
        ]
    }


def _stub_grade(source_data: dict, dest_store: dict, transformations: list) -> float:
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
async def migrate(tier: int = 0):
    source_schema, dest_schema, transformations = _stub_orchestrate(tier)
    source_data = _stub_generate_data(source_schema)

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

    score = _stub_grade(source_data, dest_store, transformations)
    yield score / 100.0
