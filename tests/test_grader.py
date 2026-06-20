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


if __name__ == "__main__":
    print("Grader unit tests")
    case_rename_perfect()
    case_wrong_value()
    case_ref_exact_value()
    case_structural_perfect()
    case_structural_ignored()
    case_empty_dest()
    print("All grader unit tests passed.")
