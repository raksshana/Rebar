import json
import random
import re

from faker import Faker

fake = Faker()


# ── Faker text dispatch ────────────────────────────────────────────────────
# Ordered list of (substring, generator) pairs.
# A field name matches the first pattern found as a substring of its lowercased name
# (after stripping rename suffixes like _v2, _new, _updated).

_TEXT_PATTERNS: list[tuple[str, callable]] = [
    ("email",      lambda: fake.email()),
    ("first_name", lambda: fake.first_name()),
    ("last_name",  lambda: fake.last_name()),
    ("name",       lambda: fake.name()),
    ("phone",      lambda: fake.phone_number()),
    ("street",     lambda: fake.street_address()),
    ("address",    lambda: fake.address()),
    ("city",       lambda: fake.city()),
    ("country",    lambda: fake.country()),
    ("region",     lambda: fake.state()),
    ("zip",        lambda: fake.zipcode()),
    ("url",        lambda: fake.url()),
    ("username",   lambda: fake.user_name()),
    ("hostname",   lambda: fake.hostname()),
    ("ip",         lambda: fake.ipv4()),
    ("company",    lambda: fake.company()),
    ("timezone",   lambda: fake.timezone()),
    ("locale",     lambda: fake.locale()),
    ("currency",   lambda: fake.currency_code()),
    ("color",      lambda: fake.color_name()),
    ("slug",       lambda: fake.slug()),
    ("version",    lambda: fake.numerify("#.#.#")),
    ("uuid",       lambda: str(fake.uuid4())),
    ("token",      lambda: fake.sha256()[:32]),
    ("key",        lambda: fake.bothify("key-????-####")),
    ("code",       lambda: fake.bothify("??-####")),
    ("tag",        lambda: fake.word()),
    ("label",      lambda: fake.word().capitalize()),
    ("title",      lambda: fake.catch_phrase()),
]

_RENAME_SUFFIXES = ("_v2", "_new", "_updated", "_renamed")


def _faker_text(field_name: str) -> str | None:
    """Return a Faker string for a recognized field name, or None if Faker can't handle it."""
    clean = field_name.lower()
    for suffix in _RENAME_SUFFIXES:
        clean = clean.removesuffix(suffix)
    for pattern, fn in _TEXT_PATTERNS:
        if pattern in clean:
            return fn()
    return None


def _faker_value(field_name: str, field_def: dict, id_pools: dict):
    """Generate a single value using Faker. Returns None for LLM-delegated fields."""
    match field_def["kind"]:
        case "number":
            return random.randint(1, 1000)
        case "bool":
            return random.choice([True, False])
        case "date":
            return fake.date()
        case "enum":
            return random.choice(field_def["values"])
        case "multi_enum":
            vals = field_def["values"]
            return random.sample(vals, k=random.randint(1, len(vals)))
        case "ref":
            pool = id_pools.get(field_def["target"], [1])
            return random.choice(pool)
        case "text":
            return _faker_text(field_name)  # None if unrecognized → LLM
        case _:
            return None  # richtext, nested → LLM or special handling


# ── LLM (Gemini) generation ───────────────────────────────────────────────

def _llm_batch(context_label: str, llm_fields: dict, n: int, gemini_model) -> list[dict]:
    """
    Ask Gemini to generate n records for the given fields.
    context_label: e.g. "Product" or "Product.ReviewBlock"
    llm_fields: {field_name: field_def}
    """
    field_lines = "\n".join(
        f'  - "{name}" ({defn["kind"]})' for name, defn in llm_fields.items()
    )
    prompt = (
        f'Generate {n} realistic database records for a "{context_label}" entity.\n'
        f"Fields to fill:\n{field_lines}\n\n"
        f"Rules:\n"
        f'- Values must make semantic sense for a "{context_label}" record\n'
        f'- "richtext" fields: 1–3 realistic sentences\n'
        f'- "text" fields: concise, 1–5 words\n'
        f"- Values should vary across the {n} records\n"
        f"- Return ONLY a raw JSON array of {n} objects with exactly the listed field names\n"
        f"- No explanation, no markdown fences — just the JSON array"
    )
    response = gemini_model.generate_content(prompt)
    text = response.text.strip()
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    try:
        records = json.loads(match.group(0) if match else text)
        return records[:n]
    except (json.JSONDecodeError, AttributeError):
        return [{name: f"{name}_{i + 1}" for name in llm_fields} for i in range(n)]


def _stub_llm(llm_fields: dict, records: list[dict]) -> None:
    """Fallback when no Gemini model: write placeholder strings."""
    for record in records:
        for field_name in llm_fields:
            record[field_name] = f"{field_name}_{record.get('id', 0)}"


# ── Topological sort ──────────────────────────────────────────────────────

def _topo_sort(entities: dict) -> list[str]:
    """Return entity names ordered so ref targets always come before their dependents."""
    deps = {
        name: {
            f["target"]
            for f in entity["fields"].values()
            if f["kind"] == "ref" and f["target"] in entities
        }
        for name, entity in entities.items()
    }
    order: list[str] = []
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        visited.add(name)
        for dep in deps[name]:
            visit(dep)
        order.append(name)

    for name in entities:
        visit(name)
    return order


# ── Nested block generation ───────────────────────────────────────────────

def _generate_block_items(
    entity_name: str,
    block_name: str,
    block_def: dict,
    id_pools: dict,
    gemini_model,
) -> list[dict]:
    """Generate 1–3 items for a nested block field on a single record."""
    n = random.randint(1, 3)
    block_fields = {
        name: defn
        for name, defn in block_def.get("fields", {}).items()
        if defn["kind"] not in ("id", "nested")
    }

    faker_fields = {
        name: defn for name, defn in block_fields.items()
        if not (defn["kind"] == "richtext" or
                (defn["kind"] == "text" and _faker_text(name) is None))
    }
    llm_fields = {name: defn for name, defn in block_fields.items() if name not in faker_fields}

    items: list[dict] = [{} for _ in range(n)]
    for field_name, field_def in faker_fields.items():
        for item in items:
            val = _faker_value(field_name, field_def, id_pools)
            if val is not None:
                item[field_name] = val

    if llm_fields:
        context = f"{entity_name}.{block_name}"
        if gemini_model:
            llm_data = _llm_batch(context, llm_fields, n, gemini_model)
            for i, item in enumerate(items):
                row = llm_data[i] if i < len(llm_data) else {}
                for field_name in llm_fields:
                    item[field_name] = row.get(field_name, f"{field_name}_{i + 1}")
        else:
            for i, item in enumerate(items):
                for field_name in llm_fields:
                    item[field_name] = f"{field_name}_{i + 1}"

    return items


# ── Entity record generation ──────────────────────────────────────────────

def _generate_entity_records(
    entity_name: str,
    fields: dict,
    nested_blocks: dict,
    n: int,
    id_pools: dict,
    gemini_model,
) -> list[dict]:
    # Partition fields into three buckets
    faker_fields: dict = {}
    llm_fields: dict = {}
    nested_fields: dict = {}

    for field_name, field_def in fields.items():
        kind = field_def["kind"]
        if kind == "id":
            continue
        elif kind == "nested":
            nested_fields[field_name] = field_def
        elif kind == "richtext" or (kind == "text" and _faker_text(field_name) is None):
            llm_fields[field_name] = field_def
        else:
            faker_fields[field_name] = field_def

    # Faker pass
    records: list[dict] = [{"id": i + 1} for i in range(n)]
    for field_name, field_def in faker_fields.items():
        for record in records:
            val = _faker_value(field_name, field_def, id_pools)
            if val is not None:
                record[field_name] = val

    # LLM pass — one batched call per entity
    if llm_fields:
        if gemini_model:
            llm_data = _llm_batch(entity_name, llm_fields, n, gemini_model)
            for i, record in enumerate(records):
                row = llm_data[i] if i < len(llm_data) else {}
                for field_name in llm_fields:
                    record[field_name] = row.get(field_name, f"{field_name}_{record['id']}")
        else:
            _stub_llm(llm_fields, records)

    # Nested pass — 1–3 block items per record
    for field_name, field_def in nested_fields.items():
        block_name = field_def["of"]
        block_def = nested_blocks.get(block_name, {"fields": {}})
        for record in records:
            record[field_name] = _generate_block_items(
                entity_name, block_name, block_def, id_pools, gemini_model
            )

    return records


# ── Public API ────────────────────────────────────────────────────────────

def make_gemini_model(api_key: str | None = None):
    """Build a Gemini GenerativeModel. Reads GEMINI_API_KEY from env if api_key not given."""
    import os
    import google.generativeai as genai
    genai.configure(api_key=api_key or os.environ["GEMINI_API_KEY"])
    return genai.GenerativeModel("gemini-1.5-flash")


def generate_source_data(
    source_schema: dict,
    n: int = 3,
    gemini_model=None,
) -> dict:
    """
    Generate n source records per entity in the schema.

    source_schema : canonical schema dict with "entities" and "nested_blocks"
    n             : number of records to generate per entity
    gemini_model  : google.generativeai.GenerativeModel, or None for faker-only fallback

    Returns dict[entity_name -> list[record_dict]]
    """
    entities = source_schema["entities"]
    nested_blocks = source_schema.get("nested_blocks", {})
    id_pools: dict[str, list[int]] = {}
    result: dict[str, list[dict]] = {}

    for entity_name in _topo_sort(entities):
        records = _generate_entity_records(
            entity_name,
            entities[entity_name]["fields"],
            nested_blocks,
            n,
            id_pools,
            gemini_model,
        )
        result[entity_name] = records
        id_pools[entity_name] = [r["id"] for r in records]

    return result
