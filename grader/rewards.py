"""
Reward / scoring functions for MigrateGym.

The grader replays the transformation log (the generator's ground truth) against
the model-produced destination data and scores it on five axes:

    coverage                — did source records reach the correct dest entity?  (0–1)
    field_fidelity          — did the migrated field values come out correctly?  (0–1)
    relationship_integrity  — do ref values point to valid dest ids AND match
                              the source record's ref value exactly?             (0–1)
    type_correctness        — does every dest field hold the right Python type?  (0–1)
    structural              — were the structural transforms actually performed? (0–1)

Every helper here works purely off `source_schema`, the ordered `transformations`
list, `source_data` (real names) and `dest_data` (real names — obfuscation has
already been reversed by `translate_dest_data`). No generator imports required:
the grader is self-contained and replays the transforms itself.

Transform log formats consumed (see generator/difficulty_dial.py):

    rename          {entity, from, to}
    retype          {entity, field, from, to}
    enum_remap      {entity, field, mapping}
    unmapped        {entity, field}
    flatten_nested  {entity, field, block, into, strategy}
    split           {from, into:[orig, detail], moved_fields, link_field}
    merge           {from:[parent, child], into, dropped_link_field}
    extract_nested  {entity, field, block, new_entity, link_field}
    partition       {entity, on_field, mapping:{value: sub_entity}}
    denormalize     {entity, via_field, from_entity, inlined:[{source_field, dest_field}]}
    computed        {entity, operation, source_fields|source_field, dest_field, [separator|value]}
"""

import re

# Structural transforms — their presence flips the grader into multiplier mode.
_STRUCTURAL_KINDS = {
    "merge", "split", "flatten_nested", "unmapped",
    "denormalize", "partition", "computed", "extract_nested",
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


# ---------------------------------------------------------------------------
# Low-level value helpers
# ---------------------------------------------------------------------------

def _coerce(value, to_kind):
    """Mirror the retype coercion the model is expected to perform.

    Coercion pairs (generator _COERCIONS):
        text<->richtext, date->text  (identity on the string)
        number->text                 (str)
        number->bool                 (truthiness)
        bool->number                 (0/1)
    """
    if value is None:
        return None
    if to_kind in ("text", "richtext"):
        return str(value)
    if to_kind == "bool":
        return bool(value)
    if to_kind == "number":
        if isinstance(value, bool):
            return int(value)
        return value
    return value


def _values_equal(a, b):
    """Tolerant equality used across every value comparison."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-9
    return a == b


def _compute_value(t, record):
    """Expected value for a `computed` transform, read from a (post-T1) record."""
    op = t["operation"]
    if op == "concat":
        a, b = t["source_fields"]
        sep = t.get("separator", " ")
        return f"{record.get(a, '')}{sep}{record.get(b, '')}"
    if op == "multiply":
        a, b = t["source_fields"]
        va, vb = record.get(a), record.get(b)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            return va * vb
        return None
    if op == "sum_fields":
        a, b = t["source_fields"]
        va, vb = record.get(a), record.get(b)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            return va + vb
        return None
    if op == "bool_from_enum":
        return record.get(t["source_field"]) == t["value"]
    return None


def _is_valid_kind(value, kind):
    """Type-check table — does `value` have the right Python type for `kind`?"""
    if kind is None:
        return True
    if kind == "id":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind in ("text", "richtext", "enum"):
        return isinstance(value, str)
    if kind == "date":
        return isinstance(value, str) and bool(_DATE_RE.match(value))
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "bool":
        return isinstance(value, bool)
    if kind == "multi_enum":
        return isinstance(value, (list, str))
    if kind == "ref":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "nested":
        return True  # never type-checked (handled by extract/flatten)
    return True


# ---------------------------------------------------------------------------
# Transform-replay context — classifies entities by their dest fate
# ---------------------------------------------------------------------------

class _Context:
    """Pre-computed lookups shared by every axis.

    Classifies each source entity by what happened to it in the destination:
    stayed put, was split, merged (as parent / child), partitioned, or had a
    nested block extracted.
    """

    def __init__(self, source_schema, transformations):
        self.source_schema = source_schema
        self.transformations = transformations

        self.merge_ts = [t for t in transformations if t["type"] == "merge"]
        self.split_ts = [t for t in transformations if t["type"] == "split"]
        self.partition_ts = [t for t in transformations if t["type"] == "partition"]
        self.extract_ts = [t for t in transformations if t["type"] == "extract_nested"]

        # parent -> merged entity name; set of child entities
        self.merge_parents = {t["from"][0]: t["into"] for t in self.merge_ts}
        self.merge_children = {t["from"][1] for t in self.merge_ts}

        # entity -> its partition transform
        self.partition_by_entity = {t["entity"]: t for t in self.partition_ts}
        self.partitioned = set(self.partition_by_entity)

        # entities that no longer exist under their own name in dest
        self.removed = set(self.merge_parents) | self.merge_children | self.partitioned

        # field-rename map: (entity, source_field) -> dest_field
        self.rename_map = {}
        for t in transformations:
            if t["type"] == "rename":
                self.rename_map[(t["entity"], t["from"])] = t["to"]

    # -- name resolution ----------------------------------------------------

    def dest_field_name(self, entity, source_field):
        """Resolve a source field name to its (possibly renamed) dest name."""
        return self.rename_map.get((entity, source_field), source_field)

    # -- routing ------------------------------------------------------------

    def route_partition(self, entity, src_record):
        """Sub-entity a source record routes to (or None)."""
        t = self.partition_by_entity[entity]
        expected = apply_transforms_to_record(src_record, entity, self.transformations)
        value = expected.get(t["on_field"])
        return t["mapping"].get(value)

    def target_dest_ids(self, target_entity, dest_data):
        """Valid dest id set for a ref whose source target is `target_entity`."""
        if target_entity in self.merge_parents:
            return _id_set(dest_data.get(self.merge_parents[target_entity], []))
        if target_entity in self.partitioned:
            t = self.partition_by_entity[target_entity]
            ids = set()
            for sub in t["mapping"].values():
                ids |= _id_set(dest_data.get(sub, []))
            return ids
        return _id_set(dest_data.get(target_entity, []))

    def locate_dest_record(self, entity, src_record, dest_index):
        """The dest record a surviving/merged/partitioned source record maps to."""
        sid = src_record.get("id")
        if entity in self.merge_parents:
            return dest_index.get(self.merge_parents[entity], {}).get(sid)
        if entity in self.partitioned:
            sub = self.route_partition(entity, src_record)
            if sub is None:
                return None
            return dest_index.get(sub, {}).get(sid)
        return dest_index.get(entity, {}).get(sid)


# ---------------------------------------------------------------------------
# Record-level transform replay
# ---------------------------------------------------------------------------

def apply_transforms_to_record(record, entity, transformations, apply_split_drop=True):
    """Replay per-entity field transforms to compute the expected dest record
    for the destination row that *keeps the entity's name*.

    Handles: rename, retype, enum_remap, unmapped, flatten_nested, split
    (drops moved fields), computed. Structural relocations (merge / partition /
    extract / denormalize) are scored separately and are intentionally not
    applied here.

    `apply_split_drop=False` keeps split-moved fields in place (with all other
    field transforms still applied) — used to recover the expected values for
    those fields in the detail entity.
    """
    expected = dict(record)
    for t in transformations:
        tp = t["type"]
        if tp == "rename" and t["entity"] == entity:
            if t["from"] in expected:
                expected[t["to"]] = expected.pop(t["from"])
        elif tp == "retype" and t["entity"] == entity:
            if t["field"] in expected:
                expected[t["field"]] = _coerce(expected[t["field"]], t["to"])
        elif tp == "enum_remap" and t["entity"] == entity:
            f = t["field"]
            if f in expected:
                expected[f] = t["mapping"].get(expected[f], expected[f])
        elif tp == "unmapped" and t["entity"] == entity:
            expected.pop(t["field"], None)
        elif tp == "flatten_nested" and t["entity"] == entity:
            val = expected.pop(t["field"], None)
            expected[t["into"]] = len(val) if isinstance(val, list) else 0
        elif tp == "split" and t["from"] == entity and apply_split_drop:
            for mf in t["moved_fields"]:
                expected.pop(mf, None)
        elif tp == "computed" and t["entity"] == entity:
            expected[t["dest_field"]] = _compute_value(t, expected)
    return expected


# ---------------------------------------------------------------------------
# Tiny collection helpers
# ---------------------------------------------------------------------------

def _id_set(records):
    return {r["id"] for r in records if isinstance(r, dict) and "id" in r}


def _index_by_id(records):
    return {r["id"]: r for r in records if isinstance(r, dict) and "id" in r}


def _build_dest_index(dest_data):
    return {ent: _index_by_id(recs) for ent, recs in dest_data.items()}


def _safe_ratio(hits, total, empty=1.0):
    return empty if total == 0 else hits / total


def _via_source_name(ctx, via_entity, via_field):
    """Source-side name of a (possibly renamed) ref field used by a JOIN."""
    for (ent, src_field), dest_field in ctx.rename_map.items():
        if ent == via_entity and dest_field == via_field:
            return src_field
    return via_field


def _relocated_present(entity, ctx, dest_data):
    """True if `entity` was consumed by a later merge/partition AND its
    destination actually holds records. Used to grant field-absence checks
    vacuous credit (the relocation is verified by the merge/partition check),
    while still scoring 0 for an entity that is merely missing from dest."""
    for mt in ctx.merge_ts:
        if entity in mt["from"] and dest_data.get(mt["into"]):
            return True
    if entity in ctx.partition_by_entity:
        subs = ctx.partition_by_entity[entity]["mapping"].values()
        if any(dest_data.get(sub) for sub in subs):
            return True
    return False


def _records_for_entity(entity, transformations, dest_data):
    """Where an entity's records ended up — handles later merge/partition.
    Returns None when the entity vanished without a tracked destination
    (callers grant vacuous credit in that case)."""
    if entity in dest_data:
        return dest_data[entity]
    for t in transformations:
        if t["type"] == "merge" and entity in t["from"]:
            return dest_data.get(t["into"], [])
        if t["type"] == "partition" and t["entity"] == entity:
            recs = []
            for sub in t["mapping"].values():
                recs.extend(dest_data.get(sub, []))
            return recs
    return None


# ---------------------------------------------------------------------------
# Axis 1 — Coverage
# ---------------------------------------------------------------------------

def score_coverage(source_schema, transformations, source_data, dest_data, ctx=None):
    """Fraction of source records that reached the correct dest entity (id-based,
    with count-based handling for structural relocations)."""
    if ctx is None:
        ctx = _Context(source_schema, transformations)
    total = 0
    hits = 0

    # Base loop — entities that keep their own name in dest.
    for ename in source_schema["entities"]:
        if ename in ctx.removed:
            continue
        src_recs = source_data.get(ename, [])
        src_ids = _id_set(src_recs)
        dest_ids = _id_set(dest_data.get(ename, []))
        # Recall: did each source record appear in dest?
        for src in src_recs:
            total += 1
            if src.get("id") in dest_ids:
                hits += 1
        # Precision: dest records whose IDs have no matching source are false positives.
        for did in dest_ids:
            if did not in src_ids:
                total += 1

    # Merge — parent records should land in the merged entity (count-based).
    for t in ctx.merge_ts:
        parent = t["from"][0]
        expected = len(source_data.get(parent, []))
        actual = len(dest_data.get(t["into"], []))
        total += expected
        hits += min(actual, expected)

    # Split — each source record yields one detail record (count-based). The
    # detail entity may itself have been merged away later; follow it.
    for t in ctx.split_ts:
        orig = t["from"]
        expected = len(source_data.get(orig, []))
        detail_recs = _records_for_entity(t["into"][1], transformations, dest_data) or []
        total += expected
        hits += min(len(detail_recs), expected)

    # Extract nested — expected count = total nested items across source records.
    for t in ctx.extract_ts:
        ent, field = t["entity"], t["field"]
        expected = sum(
            len(src.get(field, []) or [])
            for src in source_data.get(ent, [])
        )
        actual = len(dest_data.get(t["new_entity"], []))
        total += expected
        hits += min(actual, expected)

    # Partition — each source record routes to exactly one sub-entity.
    # Recall:    source record appeared in its correct bucket.
    # Precision: records placed in the wrong bucket are false positives.
    for ent, t in ctx.partition_by_entity.items():
        sub_ids = {sub: _id_set(dest_data.get(sub, [])) for sub in t["mapping"].values()}

        # Build the correct-assignment map once so the FP loop is O(n).
        correct_sub_for = {}
        for src in source_data.get(ent, []):
            sub = ctx.route_partition(ent, src)
            if sub is not None:
                correct_sub_for[src.get("id")] = sub

        # Recall
        for src in source_data.get(ent, []):
            total += 1
            sub = ctx.route_partition(ent, src)
            if sub is not None and src.get("id") in sub_ids.get(sub, set()):
                hits += 1

        # Precision: penalise every dest record that is in the wrong bucket
        # (or whose ID does not exist in the source at all).
        for sub in t["mapping"].values():
            for aid in sub_ids.get(sub, set()):
                if correct_sub_for.get(aid) != sub:
                    total += 1  # false positive

    return _safe_ratio(hits, total)


# ---------------------------------------------------------------------------
# Axis 2 — Field Fidelity
# ---------------------------------------------------------------------------

def score_field_fidelity(source_schema, transformations, source_data, dest_data, ctx=None):
    """Did the migrated field values come out correctly?"""
    if ctx is None:
        ctx = _Context(source_schema, transformations)
    dest_index = _build_dest_index(dest_data)
    total = 0
    hits = 0

    # Fields a given entity should NOT carry into dest (unmapped).
    unmapped_by_entity = {}
    for t in transformations:
        if t["type"] == "unmapped":
            unmapped_by_entity.setdefault(t["entity"], set()).add(t["field"])

    # --- Base loop: entities that keep their name --------------------------
    for ename in source_schema["entities"]:
        if ename in ctx.removed:
            continue
        dest_by_id = dest_index.get(ename, {})
        for src in source_data.get(ename, []):
            expected = apply_transforms_to_record(src, ename, transformations)
            drec = dest_by_id.get(src.get("id"))
            if drec is None:
                total += 1  # missing-record penalty
                continue
            for f, ev in expected.items():
                if f in drec:
                    total += 1
                    if _values_equal(drec[f], ev):
                        hits += 1
            # Penalise unmapped fields that were left in the dest record.
            for uf in unmapped_by_entity.get(ename, ()):  # post-rename names
                if uf in drec:
                    total += 1  # present but should be absent → miss

    # --- Split: moved fields must show up in the detail entity -------------
    dest_kinds = _build_dest_field_kinds(source_schema, transformations)
    for t in ctx.split_ts:
        orig, detail = t["from"], t["into"][1]
        link_field = t["link_field"]
        # Only check moved fields that still exist on the detail entity — a
        # later unmapped may have dropped some of them.
        detail_fields = dest_kinds.get(detail, {})
        moved = [mf for mf in t["moved_fields"] if mf in detail_fields]
        detail_by_link = {}
        for r in dest_data.get(detail, []):
            detail_by_link[r.get(link_field)] = r
        for src in source_data.get(orig, []):
            post = apply_transforms_to_record(
                src, orig, transformations, apply_split_drop=False)
            drec = detail_by_link.get(src.get("id"))
            for mf in moved:
                total += 1
                if drec is not None and mf in drec and _values_equal(drec[mf], post.get(mf)):
                    hits += 1

    # --- Merge: parent fields must show up in the merged entity ------------
    for t in ctx.merge_ts:
        parent, merged = t["from"][0], t["into"]
        merged_by_id = dest_index.get(merged, {})
        for src in source_data.get(parent, []):
            expected = apply_transforms_to_record(src, parent, transformations)
            drec = merged_by_id.get(src.get("id"))
            if drec is None:
                total += 1
                continue
            for f, ev in expected.items():
                if f in drec:
                    total += 1
                    if _values_equal(drec[f], ev):
                        hits += 1

    # --- Partition: each record's fields must show up in the right sub -----
    for ent, t in ctx.partition_by_entity.items():
        on_field = t["on_field"]
        for src in source_data.get(ent, []):
            sub = ctx.route_partition(ent, src)
            if sub is None:
                continue
            expected = apply_transforms_to_record(src, ent, transformations)
            expected.pop(on_field, None)  # discriminator dropped from sub-entities
            drec = dest_index.get(sub, {}).get(src.get("id"))
            if drec is None:
                total += 1
                continue
            for f, ev in expected.items():
                if f in drec:
                    total += 1
                    if _values_equal(drec[f], ev):
                        hits += 1

    # --- Extract nested: each extracted record matches a source item -------
    for t in ctx.extract_ts:
        ent, field = t["entity"], t["field"]
        new_entity, link_field = t["new_entity"], t["link_field"]
        block = t["block"]
        block_fields = list(
            source_schema.get("nested_blocks", {}).get(block, {}).get("fields", {})
        )
        dest_by_parent = {}
        for r in dest_data.get(new_entity, []):
            dest_by_parent.setdefault(r.get(link_field), []).append(r)
        for src in source_data.get(ent, []):
            items = src.get(field, []) or []
            drecs = dest_by_parent.get(src.get("id"), [])
            for i, item in enumerate(items):
                drec = drecs[i] if i < len(drecs) else None
                for bf in block_fields:
                    total += 1
                    if drec is not None and _values_equal(drec.get(bf), item.get(bf)):
                        hits += 1
            extra = len(drecs) - len(items)
            if extra > 0:
                total += extra  # over-extraction penalty

    # --- Denormalize: inlined fields require a JOIN against the ref target --
    for t in (x for x in transformations if x["type"] == "denormalize"):
        ent, from_entity = t["entity"], t["from_entity"]
        via_src = _via_source_name(ctx, ent, t["via_field"])
        from_by_id = _index_by_id(source_data.get(from_entity, []))
        dest_by_id = dest_index.get(ent, {})
        for src in source_data.get(ent, []):
            drec = dest_by_id.get(src.get("id"))
            if drec is None:
                continue  # absence already penalised in base loop
            ref_val = src.get(via_src)
            referenced = from_by_id.get(ref_val)
            for item in t["inlined"]:
                total += 1
                expected = referenced.get(item["source_field"]) if referenced else None
                if _values_equal(drec.get(item["dest_field"]), expected):
                    hits += 1

    return _safe_ratio(hits, total)


# ---------------------------------------------------------------------------
# Axis 3 — Relationship Integrity
# ---------------------------------------------------------------------------

def score_relationship_integrity(source_schema, transformations, source_data, dest_data, ctx=None):
    """Every dest ref must point to a valid dest id AND equal the source
    record's ref value (closes the 'pick first' exploit)."""
    if ctx is None:
        ctx = _Context(source_schema, transformations)
    dest_index = _build_dest_index(dest_data)
    total = 0
    hits = 0

    for ename, edef in source_schema["entities"].items():
        if ename in ctx.merge_children:
            continue  # child ids not preserved; refs dropped
        ref_fields = [
            (fname, fdef) for fname, fdef in edef["fields"].items()
            if fdef.get("kind") == "ref"
        ]
        if not ref_fields:
            continue
        for src in source_data.get(ename, []):
            drec = ctx.locate_dest_record(ename, src, dest_index)
            if drec is None:
                total += len(ref_fields)  # record never made it → integrity miss
                continue
            for fname, fdef in ref_fields:
                dest_field = ctx.dest_field_name(ename, fname)
                if dest_field not in drec:
                    total += 1  # ref missing from dest record
                    continue
                total += 1
                valid_ids = ctx.target_dest_ids(fdef["target"], dest_data)
                src_val = src.get(fname)
                if _values_equal(drec[dest_field], src_val) and drec[dest_field] in valid_ids:
                    hits += 1

    # Extract-nested link field — must point to a valid parent id.
    for t in ctx.extract_ts:
        parent_ids = ctx.target_dest_ids(t["entity"], dest_data)
        for r in dest_data.get(t["new_entity"], []):
            total += 1
            if r.get(t["link_field"]) in parent_ids:
                hits += 1

    # Split detail link field — must point to a valid parent id.
    for t in ctx.split_ts:
        parent_ids = ctx.target_dest_ids(t["from"], dest_data)
        for r in dest_data.get(t["into"][1], []):
            total += 1
            if r.get(t["link_field"]) in parent_ids:
                hits += 1

    return _safe_ratio(hits, total)


# ---------------------------------------------------------------------------
# Axis 4 — Type Correctness
# ---------------------------------------------------------------------------

def _build_dest_field_kinds(source_schema, transformations):
    """Expected {dest_entity: {field: kind}} after replaying every transform."""
    kinds = {
        ename: {f: fdef["kind"] for f, fdef in edef["fields"].items()}
        for ename, edef in source_schema["entities"].items()
    }
    blocks = source_schema.get("nested_blocks", {})

    for t in transformations:
        tp = t["type"]
        if tp == "rename":
            km = kinds.get(t["entity"], {})
            if t["from"] in km:
                km[t["to"]] = km.pop(t["from"])
        elif tp == "retype":
            km = kinds.get(t["entity"], {})
            if t["field"] in km:
                km[t["field"]] = t["to"]
        elif tp == "unmapped":
            kinds.get(t["entity"], {}).pop(t["field"], None)
        elif tp == "flatten_nested":
            km = kinds.get(t["entity"], {})
            km.pop(t["field"], None)
            km[t["into"]] = "number"
        elif tp == "split":
            orig, detail = t["from"], t["into"][1]
            km = kinds.get(orig, {})
            detail_kinds = {"id": "id", t["link_field"]: "ref"}
            for mf in t["moved_fields"]:
                if mf in km:
                    detail_kinds[mf] = km.pop(mf)
            kinds[detail] = detail_kinds
        elif tp == "merge":
            parent, child = t["from"]
            merged = dict(kinds.get(parent, {}))
            for f, k in kinds.get(child, {}).items():
                if f == t["dropped_link_field"] or k == "id":
                    continue
                dest_f = f if f not in merged else f"{child.lower()}_{f}"
                merged[dest_f] = k
            kinds.pop(parent, None)
            kinds.pop(child, None)
            kinds[t["into"]] = merged
        elif tp == "extract_nested":
            kinds.get(t["entity"], {}).pop(t["field"], None)
            new_kinds = {"id": "id", t["link_field"]: "ref"}
            for bf, bdef in blocks.get(t["block"], {}).get("fields", {}).items():
                new_kinds[bf] = bdef["kind"]
            kinds[t["new_entity"]] = new_kinds
        elif tp == "denormalize":
            km = kinds.get(t["entity"], {})
            src_fields = source_schema["entities"].get(t["from_entity"], {}).get("fields", {})
            for item in t["inlined"]:
                sf = src_fields.get(item["source_field"], {})
                km[item["dest_field"]] = sf.get("kind", "text")
        elif tp == "computed":
            km = kinds.get(t["entity"], {})
            op = t["operation"]
            km[t["dest_field"]] = (
                "text" if op == "concat"
                else "bool" if op == "bool_from_enum"
                else "number"
            )
        elif tp == "partition":
            km = kinds.get(t["entity"], {})
            base = {f: k for f, k in km.items() if f != t["on_field"]}
            for sub in t["mapping"].values():
                kinds[sub] = dict(base)
            kinds.pop(t["entity"], None)

    return kinds


def score_type_correctness(source_schema, transformations, source_data, dest_data, ctx=None):
    """For every field present in a dest record, is its Python type valid?"""
    dest_kinds = _build_dest_field_kinds(source_schema, transformations)
    total = 0
    hits = 0
    for ename, kind_map in dest_kinds.items():
        for rec in dest_data.get(ename, []):
            if not isinstance(rec, dict):
                continue
            for f, kind in kind_map.items():
                if kind == "nested":
                    continue
                if f in rec:
                    total += 1
                    if _is_valid_kind(rec[f], kind):
                        hits += 1
    return _safe_ratio(hits, total)


# ---------------------------------------------------------------------------
# Axis 5 — Structural (multiplier)
# ---------------------------------------------------------------------------

def score_structural(source_schema, transformations, source_data, dest_data, ctx=None):
    """Were the structural transforms actually performed?

    Returns (score, has_structural). has_structural is False only when there
    are no structural transforms (Tier 0/1) → multiplier collapses to 1.0.
    """
    if ctx is None:
        ctx = _Context(source_schema, transformations)
    dest_kinds = _build_dest_field_kinds(source_schema, transformations)
    total = 0.0
    got = 0.0
    has_structural = False

    for t in transformations:
        tp = t["type"]
        if tp not in _STRUCTURAL_KINDS:
            continue
        has_structural = True

        if tp == "merge":
            # parent records land in the merged entity; vacuous if no parents.
            total += 1
            expected = len(source_data.get(t["from"][0], []))
            got += 1.0 if (expected == 0 or dest_data.get(t["into"])) else 0.0

        elif tp == "split":
            # detail entity gets one row per source record (it may itself have
            # been merged away later — follow it).
            total += 1
            expected = len(source_data.get(t["from"], []))
            detail_recs = _records_for_entity(t["into"][1], transformations, dest_data)
            got += 1.0 if (expected == 0 or detail_recs) else 0.0

        elif tp == "extract_nested":
            # new entity gets one row per nested item; vacuous if there were none.
            total += 1
            expected = sum(
                len(src.get(t["field"], []) or [])
                for src in source_data.get(t["entity"], [])
            )
            got += 1.0 if (expected == 0 or dest_data.get(t["new_entity"])) else 0.0

        elif tp == "partition":
            # Each sub-entity must contain exactly the records routed to it.
            # Score per sub using Jaccard(expected_ids, actual_ids) so that
            # shotgun output (all records in every bucket) and round-robin
            # (wrong records in right-shaped buckets) both score well below 1.
            expected_by_sub = {sub: set() for sub in t["mapping"].values()}
            for src in source_data.get(t["entity"], []):
                sub = ctx.route_partition(t["entity"], src)
                if sub in expected_by_sub:
                    expected_by_sub[sub].add(src.get("id"))
            for sub in t["mapping"].values():
                total += 1
                expected_ids = expected_by_sub[sub]
                actual_ids = _id_set(dest_data.get(sub, []))
                if not expected_ids:
                    # Legitimately empty bucket — credit only when not spuriously
                    # populated (empty is easy; wrong records would score 0).
                    got += 1.0 if not actual_ids else 0.0
                else:
                    # Jaccard: |expected ∩ actual| / |expected ∪ actual|
                    correct = len(expected_ids & actual_ids)
                    union_size = len(expected_ids | actual_ids)
                    got += correct / union_size if union_size > 0 else 1.0

        elif tp == "flatten_nested":
            total += 1
            ent = t["entity"]
            if ent in dest_data:
                parent_recs = dest_data[ent]
                if not parent_recs:
                    got += 0.0
                else:
                    # Find where the count field is expected to live in the final
                    # dest schema — it may stay on the parent, be relocated by a
                    # later split, or be dropped entirely by a later unmapped.
                    host = None
                    if t["into"] in dest_kinds.get(ent, {}):
                        host = ent
                    else:
                        for s in ctx.split_ts:
                            if s["from"] == ent and t["into"] in s.get("moved_fields", []):
                                if t["into"] in dest_kinds.get(s["into"][1], {}):
                                    host = s["into"][1]
                                break
                    if host is None:
                        present = 1.0  # count field dropped later — not expected
                    else:
                        host_recs = dest_data.get(host, [])
                        present = (
                            sum(1 for r in host_recs if t["into"] in r) / len(host_recs)
                            if host_recs else 0.0
                        )
                    absent = sum(1 for r in parent_recs if t["field"] not in r) / len(parent_recs)
                    got += (present + absent) / 2
            elif _relocated_present(ent, ctx, dest_data):
                got += 1.0  # merged/partitioned away — relocation check covers it
            else:
                got += 0.0  # missing from dest

        elif tp == "unmapped":
            total += 1
            ent = t["entity"]
            if ent in dest_data:
                recs = dest_data[ent]
                got += (sum(1 for r in recs if t["field"] not in r) / len(recs)) if recs else 0.0
            elif _relocated_present(ent, ctx, dest_data):
                got += 1.0  # merged/partitioned away — collisions make absence unverifiable
            else:
                got += 0.0  # missing from dest

        elif tp == "denormalize":
            recs = dest_data.get(t["entity"], [])
            for item in t["inlined"]:
                total += 1
                if recs:
                    got += sum(1 for r in recs if item["dest_field"] in r) / len(recs)

        elif tp == "computed":
            recs = dest_data.get(t["entity"], [])
            total += 1
            if recs:
                src_by_id = _index_by_id(source_data.get(t["entity"], []))
                ok = 0
                counted = 0
                for drec in recs:
                    src = src_by_id.get(drec.get("id"))
                    if src is None:
                        continue
                    counted += 1
                    expected = apply_transforms_to_record(
                        src, t["entity"], transformations
                    ).get(t["dest_field"])
                    if t["dest_field"] in drec and _values_equal(drec[t["dest_field"]], expected):
                        ok += 1
                got += (ok / counted) if counted else 0.0

    score = 1.0 if total == 0 else got / total
    return score, has_structural
