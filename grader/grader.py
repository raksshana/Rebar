"""
Grader entry point for MigrateGym.

    grader = Grader(source_schema, transformations)
    result = grader.grade(source_data, dest_data)

`source_data` is keyed by real source-entity name; `dest_data` is keyed by real
dest-entity name (Tier 3 obfuscation must already be reversed via
`translate_dest_data` before grading). `result` is::

    {
      "coverage":               0.0–1.0,
      "field_fidelity":         0.0–1.0,
      "relationship_integrity": 0.0–1.0,
      "type_correctness":       0.0–1.0,
      "structural":             0.0–1.0,   # only when structural transforms exist
      "total":                  0.0–100.0,
    }

Final score formula
-------------------
    base  = coverage·0.20 + field_fidelity·0.30
          + relationship_integrity·0.30 + type_correctness·0.20

No structural transforms (Tier 0/1)::
    total = base · 100

Structural transforms present (Tier 2/3)::
    total = base · (ALPHA + (1 - ALPHA)·structural) · 100      ALPHA = 0.20

The multiplier makes structural correctness a prerequisite: a model that copies
unchanged fields but performs no structural work is capped at ~ALPHA·base.
"""

try:
    from .rewards import (
        _Context,
        score_coverage,
        score_field_fidelity,
        score_relationship_integrity,
        score_type_correctness,
        score_structural,
    )
except ImportError:  # allow running as a flat script, not only as a package
    from rewards import (
        _Context,
        score_coverage,
        score_field_fidelity,
        score_relationship_integrity,
        score_type_correctness,
        score_structural,
    )


# Axis weights (must sum to 1.0).
W_COVERAGE = 0.20
W_FIELD_FIDELITY = 0.30
W_RELATIONSHIP_INTEGRITY = 0.30
W_TYPE_CORRECTNESS = 0.20

# Structural-multiplier floor: with structural=0 a model keeps at most ALPHA·base.
ALPHA = 0.20


class Grader:
    """Scores a migration against the generator's ground-truth transform log."""

    def __init__(self, source_schema, transformations):
        self.source_schema = source_schema
        self.transformations = transformations or []

    def grade(self, source_data, dest_data):
        """Grade `dest_data` against `source_data`. Returns the score dict."""
        source_data = source_data or {}
        dest_data = dest_data or {}
        ctx = _Context(self.source_schema, self.transformations)

        coverage = score_coverage(
            self.source_schema, self.transformations, source_data, dest_data, ctx)
        field_fidelity = score_field_fidelity(
            self.source_schema, self.transformations, source_data, dest_data, ctx)
        relationship_integrity = score_relationship_integrity(
            self.source_schema, self.transformations, source_data, dest_data, ctx)
        type_correctness = score_type_correctness(
            self.source_schema, self.transformations, source_data, dest_data, ctx)
        structural, has_structural = score_structural(
            self.source_schema, self.transformations, source_data, dest_data, ctx)

        base = (
            coverage * W_COVERAGE
            + field_fidelity * W_FIELD_FIDELITY
            + relationship_integrity * W_RELATIONSHIP_INTEGRITY
            + type_correctness * W_TYPE_CORRECTNESS
        )

        if has_structural:
            multiplier = ALPHA + (1.0 - ALPHA) * structural
        else:
            multiplier = 1.0

        result = {
            "coverage": coverage,
            "field_fidelity": field_fidelity,
            "relationship_integrity": relationship_integrity,
            "type_correctness": type_correctness,
            "total": base * multiplier * 100.0,
        }
        if has_structural:
            result["structural"] = structural
        return result
