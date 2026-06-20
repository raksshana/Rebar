"""
Validation harness for the MigrateGym grader.

Builds, for randomly generated Tier 2 / Tier 3 tasks:
  * synthetic source data (valid refs, enums, nested blocks),
  * a *known-correct* destination by forward-applying the transform log
    (an independent re-derivation of `apply_transforms_to_data`),

then asserts the grader's core invariants:
  * a perfect migration scores 100,
  * an empty destination scores low,
  * a verbatim copy scores below perfect.

Run:  python3 tests/test_grader_validation.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.orchestration import orchestrate          # noqa: E402
from grader.rewards import _coerce, _compute_value        # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic source data
# ---------------------------------------------------------------------------

def _gen_scalar(kind, fdef, seed):
    if kind in ("text", "richtext"):
        return f"val_{seed}"
    if kind == "number":
        return random.randint(1, 1000)
    if kind == "bool":
        return random.choice([True, False])
    if kind == "date":
        return f"20{random.randint(10, 23):02d}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
    if kind == "enum":
        return random.choice(fdef["values"])
    if kind == "multi_enum":
        vals = fdef["values"]
        k = random.randint(1, min(2, len(vals)))
        return random.sample(vals, k)
    return f"val_{seed}"


def _gen_nested_item(block_def, seed):
    item = {}
    for fname, fdef in block_def["fields"].items():
        item[fname] = _gen_scalar(fdef["kind"], fdef, f"{seed}_{fname}")
    return item


def generate_source_data(schema, n=4):
    """Generate `n` records per entity with valid refs / enums / nested blocks."""
    blocks = schema.get("nested_blocks", {})
    data = {ename: [] for ename in schema["entities"]}
    counter = 0
    for ename, edef in schema["entities"].items():
        for i in range(1, n + 1):
            rec = {}
            for fname, fdef in edef["fields"].items():
                kind = fdef["kind"]
                counter += 1
                if kind == "id":
                    rec[fname] = i
                elif kind == "ref":
                    rec[fname] = random.randint(1, n)  # target ids are 1..n
                elif kind == "nested":
                    block_def = blocks[fdef["of"]]
                    rec[fname] = [
                        _gen_nested_item(block_def, counter * 10 + j)
                        for j in range(random.randint(1, 3))
                    ]
                else:
                    rec[fname] = _gen_scalar(kind, fdef, counter)
            data[ename].append(rec)
    return data


# ---------------------------------------------------------------------------
# Forward transform application — the "answer key" builder
# ---------------------------------------------------------------------------

def _pre_rename(transformations, entity, current_name):
    for t in transformations:
        if t["type"] == "rename" and t["entity"] == entity and t["to"] == current_name:
            return t["from"]
    return current_name


def apply_transforms_to_data(source_data, transformations):
    """Replay the transform log forward over source data, producing the exact
    destination data a perfect model would write. Independent of the grader's
    own replay logic so it actually tests it."""
    import copy
    data = copy.deepcopy(source_data)
    src_orig = source_data  # original, for denormalize joins

    for t in transformations:
        tp = t["type"]

        if tp == "rename":
            for rec in data.get(t["entity"], []):
                if t["from"] in rec:
                    rec[t["to"]] = rec.pop(t["from"])

        elif tp == "retype":
            for rec in data.get(t["entity"], []):
                if t["field"] in rec:
                    rec[t["field"]] = _coerce(rec[t["field"]], t["to"])

        elif tp == "enum_remap":
            for rec in data.get(t["entity"], []):
                f = t["field"]
                if f in rec:
                    rec[f] = t["mapping"].get(rec[f], rec[f])

        elif tp == "unmapped":
            for rec in data.get(t["entity"], []):
                rec.pop(t["field"], None)

        elif tp == "flatten_nested":
            for rec in data.get(t["entity"], []):
                val = rec.pop(t["field"], None)
                rec[t["into"]] = len(val) if isinstance(val, list) else 0

        elif tp == "split":
            orig, detail = t["from"], t["into"][1]
            link_field, moved = t["link_field"], t["moved_fields"]
            detail_recs = []
            for idx, rec in enumerate(data.get(orig, []), start=1):
                drec = {"id": idx, link_field: rec["id"]}
                for mf in moved:
                    if mf in rec:  # don't fabricate null columns for absent fields
                        drec[mf] = rec.pop(mf)
                detail_recs.append(drec)
            data[detail] = detail_recs

        elif tp == "merge":
            parent, child = t["from"]
            merged_name, link = t["into"], t["dropped_link_field"]
            by_parent = {}
            for c in data.get(child, []):
                by_parent.setdefault(c.get(link), []).append(c)
            merged = []
            for p in data.get(parent, []):
                m = dict(p)
                kids = by_parent.get(p["id"], [])
                if kids:
                    kid = kids[0]
                    for f, v in kid.items():
                        if f == link or f == "id":
                            continue
                        dest_f = f if f not in m else f"{child.lower()}_{f}"
                        m[dest_f] = v
                merged.append(m)
            data[merged_name] = merged
            data.pop(parent, None)
            data.pop(child, None)

        elif tp == "extract_nested":
            ent, field = t["entity"], t["field"]
            new_entity, link_field = t["new_entity"], t["link_field"]
            new_recs = []
            idc = 1
            for rec in data.get(ent, []):
                items = rec.pop(field, []) or []
                for item in items:
                    nr = {"id": idc, link_field: rec["id"]}
                    nr.update(item)
                    new_recs.append(nr)
                    idc += 1
            data[new_entity] = new_recs

        elif tp == "partition":
            ent, on_field = t["entity"], t["on_field"]
            subs = {sub: [] for sub in t["mapping"].values()}
            for rec in data.get(ent, []):
                sub = t["mapping"].get(rec.get(on_field))
                if sub is None:
                    continue
                r = dict(rec)
                r.pop(on_field, None)
                subs[sub].append(r)
            for sub, recs in subs.items():
                data[sub] = recs
            data.pop(ent, None)

        elif tp == "denormalize":
            ent, from_entity = t["entity"], t["from_entity"]
            via_src = _pre_rename(transformations, ent, t["via_field"])
            from_by_id = {r["id"]: r for r in src_orig.get(from_entity, [])}
            orig_by_id = {r["id"]: r for r in src_orig.get(ent, [])}
            for rec in data.get(ent, []):
                osrc = orig_by_id.get(rec.get("id"))
                ref_val = osrc.get(via_src) if osrc else None
                referenced = from_by_id.get(ref_val)
                for item in t["inlined"]:
                    rec[item["dest_field"]] = (
                        referenced.get(item["source_field"]) if referenced else None
                    )

        elif tp == "computed":
            for rec in data.get(t["entity"], []):
                rec[t["dest_field"]] = _compute_value(t, rec)

    return data


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def verbatim_copy(source_data):
    import copy
    return copy.deepcopy(source_data)


def run_tier(tier, trials=40):
    perfects, empties, verbatims = [], [], []
    for _ in range(trials):
        task = orchestrate(tier)
        source_schema, transformations = task.source_schema, task.transformations
        source_data = generate_source_data(source_schema)
        perfect = apply_transforms_to_data(source_data, transformations)

        # The grader comes pre-loaded with the answer key from the generator.
        grader = task.grader

        p = grader.grade(source_data, perfect)["total"]
        e = grader.grade(source_data, {})["total"]
        v = grader.grade(source_data, verbatim_copy(source_data))["total"]
        perfects.append(p)
        empties.append(e)
        verbatims.append(v)

        if p < 99.999:
            # Surface a failing case in full for debugging.
            res = grader.grade(source_data, perfect)
            raise AssertionError(
                f"Tier {tier}: perfect migration scored {p:.4f} (expected 100)\n"
                f"  axes={res}\n"
                f"  transforms={[t['type'] for t in transformations]}"
            )
        if e > 25:
            raise AssertionError(f"Tier {tier}: empty dest scored {e:.2f} (expected low)")
        if v >= p:
            raise AssertionError(f"Tier {tier}: verbatim {v:.2f} >= perfect {p:.2f}")

    def stats(xs):
        return f"min={min(xs):.2f} max={max(xs):.2f} mean={sum(xs)/len(xs):.2f}"

    print(f"Tier {tier}  ({trials} trials)")
    print(f"  perfect : {stats(perfects)}")
    print(f"  empty   : {stats(empties)}")
    print(f"  verbatim: {stats(verbatims)}")
    print("  OK\n")


if __name__ == "__main__":
    random.seed(7)
    run_tier(2, trials=60)
    run_tier(3, trials=60)
    print("All grader validation checks passed.")
