"""
Hand-calculated unit tests for the MigrateGym grader.

Each case fixes a tiny schema + transform log + source/dest data and asserts the
exact score, so the scoring formula and the structural multiplier are pinned
down independently of the randomized end-to-end validation harness.

Run:  python3 tests/test_grader.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grader.grader import Grader  # noqa: E402


def approx(a, b, eps=1e-6):
    return abs(a - b) < eps


def case_rename_perfect():
    """Tier-0 style rename, perfect migration → 100, no structural key."""
    schema = {"entities": {"User": {"fields": {
        "id": {"kind": "id"}, "name": {"kind": "text"}, "age": {"kind": "number"}}}}}
    transforms = [{"type": "rename", "entity": "User", "from": "name", "to": "full_name"}]
    source = {"User": [{"id": 1, "name": "a", "age": 5}, {"id": 2, "name": "b", "age": 6}]}
    dest = {"User": [{"id": 1, "full_name": "a", "age": 5},
                     {"id": 2, "full_name": "b", "age": 6}]}
    res = Grader(schema, transforms).grade(source, dest)
    assert approx(res["total"], 100.0), res
    assert "structural" not in res, res
    print("  rename_perfect: total=100, no structural multiplier  OK")


def case_wrong_value():
    """One wrong field value → field_fidelity 5/6, total 95 (no structural)."""
    schema = {"entities": {"User": {"fields": {
        "id": {"kind": "id"}, "name": {"kind": "text"}, "age": {"kind": "number"}}}}}
    transforms = [{"type": "rename", "entity": "User", "from": "name", "to": "full_name"}]
    source = {"User": [{"id": 1, "name": "a", "age": 5}, {"id": 2, "name": "b", "age": 6}]}
    dest = {"User": [{"id": 1, "full_name": "WRONG", "age": 5},
                     {"id": 2, "full_name": "b", "age": 6}]}
    res = Grader(schema, transforms).grade(source, dest)
    assert approx(res["field_fidelity"], 5 / 6), res
    assert approx(res["total"], 95.0), res
    print("  wrong_value: field_fidelity=5/6, total=95  OK")


def case_ref_exact_value():
    """Relationship integrity demands the exact source ref value (no 'pick first')."""
    schema = {"entities": {
        "Org": {"fields": {"id": {"kind": "id"}, "name": {"kind": "text"}}},
        "User": {"fields": {"id": {"kind": "id"},
                            "org_id": {"kind": "ref", "target": "Org", "cardinality": "one"}}},
    }}
    transforms = []  # no transforms — pure relationship check
    source = {
        "Org": [{"id": 1, "name": "x"}, {"id": 2, "name": "y"}],
        "User": [{"id": 1, "org_id": 1}, {"id": 2, "org_id": 2}],
    }
    # Model wrote org_id=1 for everyone — valid id, but wrong for record 2.
    dest = {
        "Org": [{"id": 1, "name": "x"}, {"id": 2, "name": "y"}],
        "User": [{"id": 1, "org_id": 1}, {"id": 2, "org_id": 1}],
    }
    res = Grader(schema, transforms).grade(source, dest)
    assert approx(res["relationship_integrity"], 0.5), res
    assert "structural" not in res, res
    print("  ref_exact_value: relationship_integrity=0.5 (pick-first blocked)  OK")


def case_structural_perfect():
    """Unmapped transform performed correctly → structural 1.0, total 100."""
    schema = {"entities": {"User": {"fields": {
        "id": {"kind": "id"}, "name": {"kind": "text"}, "secret": {"kind": "text"}}}}}
    transforms = [{"type": "unmapped", "entity": "User", "field": "secret"}]
    source = {"User": [{"id": 1, "name": "a", "secret": "x"},
                       {"id": 2, "name": "b", "secret": "y"}]}
    dest = {"User": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]}
    res = Grader(schema, transforms).grade(source, dest)
    assert approx(res["structural"], 1.0), res
    assert approx(res["total"], 100.0), res
    print("  structural_perfect: structural=1.0, total=100  OK")


def case_structural_ignored():
    """Unmapped field left in dest → structural 0.0; multiplier crushes total."""
    schema = {"entities": {"User": {"fields": {
        "id": {"kind": "id"}, "name": {"kind": "text"}, "secret": {"kind": "text"}}}}}
    transforms = [{"type": "unmapped", "entity": "User", "field": "secret"}]
    source = {"User": [{"id": 1, "name": "a", "secret": "x"},
                       {"id": 2, "name": "b", "secret": "y"}]}
    # Verbatim copy — secret left in.
    dest = {"User": [{"id": 1, "name": "a", "secret": "x"},
                     {"id": 2, "name": "b", "secret": "y"}]}
    res = Grader(schema, transforms).grade(source, dest)
    assert approx(res["structural"], 0.0), res
    # base = .2·1 + .3·(4/6) + .3·1 + .2·1 = 0.9 ; multiplier = 0.2 ; total = 18
    assert approx(res["field_fidelity"], 4 / 6), res
    assert approx(res["total"], 18.0), res
    print("  structural_ignored: structural=0.0, total=18 (multiplier floor)  OK")


def case_empty_dest():
    """Empty destination scores low."""
    schema = {"entities": {"User": {"fields": {
        "id": {"kind": "id"}, "name": {"kind": "text"}, "secret": {"kind": "text"}}}}}
    transforms = [{"type": "unmapped", "entity": "User", "field": "secret"}]
    source = {"User": [{"id": 1, "name": "a", "secret": "x"}]}
    res = Grader(schema, transforms).grade(source, {})
    assert res["total"] < 15, res
    print(f"  empty_dest: total={res['total']:.2f} (<15)  OK")


def case_partition_correct():
    """Perfect partition: each record in exactly the right bucket → 100."""
    schema = {"entities": {"Issue": {"fields": {
        "id":     {"kind": "id"},
        "status": {"kind": "enum", "values": ["bug", "feature"]},
        "title":  {"kind": "text"},
    }}}}
    transforms = [{"type": "partition", "entity": "Issue", "on_field": "status",
                   "mapping": {"bug": "BugIssue", "feature": "FeatureIssue"}}]
    source = {"Issue": [
        {"id": 1, "status": "bug",     "title": "crash"},
        {"id": 2, "status": "feature", "title": "dark mode"},
        {"id": 3, "status": "bug",     "title": "freeze"},
    ]}
    dest = {
        "BugIssue":     [{"id": 1, "title": "crash"}, {"id": 3, "title": "freeze"}],
        "FeatureIssue": [{"id": 2, "title": "dark mode"}],
    }
    res = Grader(schema, transforms).grade(source, dest)
    assert approx(res["coverage"],   1.0), res
    assert approx(res["structural"], 1.0), res
    assert approx(res["total"],    100.0), res
    print("  partition_correct: coverage=1.0, structural=1.0, total=100  OK")


def case_partition_shotgun():
    """Shotgun: every record in every bucket — coverage and structural penalised.

    The exploit: copy all records to all partition sub-entities.
    Before the fix this scored ~100 (full recall, presence-only structural check).
    After the fix coverage drops to 0.5 and structural to 0.5.
    """
    schema = {"entities": {"Issue": {"fields": {
        "id":     {"kind": "id"},
        "status": {"kind": "enum", "values": ["bug", "feature"]},
        "title":  {"kind": "text"},
    }}}}
    transforms = [{"type": "partition", "entity": "Issue", "on_field": "status",
                   "mapping": {"bug": "BugIssue", "feature": "FeatureIssue"}}]
    source = {"Issue": [
        {"id": 1, "status": "bug",     "title": "crash"},
        {"id": 2, "status": "feature", "title": "dark mode"},
        {"id": 3, "status": "bug",     "title": "freeze"},
    ]}
    all_recs = [{"id": 1, "title": "crash"}, {"id": 2, "title": "dark mode"},
                {"id": 3, "title": "freeze"}]
    dest = {"BugIssue": list(all_recs), "FeatureIssue": list(all_recs)}
    res = Grader(schema, transforms).grade(source, dest)
    # coverage: 3 recall hits / (3 recall + 3 false positives) = 0.5
    assert approx(res["coverage"], 0.5), res
    # structural: Jaccard(Bug)=2/3, Jaccard(Feat)=1/3 → avg=0.5
    assert approx(res["structural"], 0.5), res
    assert res["total"] < 60.0, res
    print(f"  partition_shotgun: cov={res['coverage']:.3f} struct={res['structural']:.3f} total={res['total']:.1f}  OK")


def case_extra_records_penalised():
    """Extra dest records (IDs not in source) incur a precision penalty on coverage."""
    schema = {"entities": {"User": {"fields": {
        "id":   {"kind": "id"},
        "name": {"kind": "text"},
    }}}}
    transforms = []
    source = {"User": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]}
    # Correct records plus one fabricated extra.
    dest = {"User": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"},
                     {"id": 99, "name": "fake"}]}
    res = Grader(schema, transforms).grade(source, dest)
    # 2 recall hits, 1 false positive → coverage = 2/3
    assert approx(res["coverage"], 2 / 3), res
    assert res["total"] < 100.0, res
    print(f"  extra_records_penalised: coverage={res['coverage']:.3f} total={res['total']:.1f}  OK")


if __name__ == "__main__":
    print("Grader unit tests")
    case_rename_perfect()
    case_wrong_value()
    case_ref_exact_value()
    case_structural_perfect()
    case_structural_ignored()
    case_empty_dest()
    case_partition_correct()
    case_partition_shotgun()
    case_extra_records_penalised()
    print("All grader unit tests passed.")
