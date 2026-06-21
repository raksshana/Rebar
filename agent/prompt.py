from __future__ import annotations
import json


def build_script_prompt(
    source_schema: dict,
    dest_schema: dict,
    source_data: dict,
) -> str:
    return (
        "You are a data migration expert. Write a Python script that reads records "
        "from the source and writes migrated records to the destination.\n\n"
        "Pre-injected variables available in your script:\n"
        "- `source_data` — dict mapping entity name -> list of record dicts\n"
        "- `write_dest(entity_name, records)` — call this to write migrated records\n"
        "- `source_schema`, `dest_schema` — the schemas below as Python dicts\n\n"
        "## Source Schema\n"
        "```json\n"
        f"{json.dumps(source_schema, indent=2)}\n"
        "```\n\n"
        "## Destination Schema\n"
        "```json\n"
        f"{json.dumps(dest_schema, indent=2)}\n"
        "```\n\n"
        "## Source Data\n"
        "```json\n"
        f"{json.dumps(source_data, indent=2)}\n"
        "```\n\n"
        "Rules:\n"
        "- Write only top-level executable statements — no function or class definitions\n"
        "- Migrate ALL records from ALL source entities to the correct destination entity\n"
        "- Call `write_dest(entity_name, [record, ...])` to emit each batch of records\n"
        "- Each destination record must be a dict with fields matching the destination schema\n"
        "- `source_data` and `write_dest` are already available — do not redefine them\n"
        "- Standard library imports (e.g. `import re`) are allowed\n\n"
        "Output ONLY a single ```python ... ``` code block. "
        "No explanation, no prose, no text before or after the block."
    )
