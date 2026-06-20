"""
Orchestration entry point for MigrateGym (Tier 3 focus; Tier 2 still supported).

orchestrate(tier) ties the generator pieces together and hands the grader its
answer key:
  1. generate a valid source schema       (schema_generation.get_schema)
  2. generate the transformation mapping   (difficulty_dial.apply_difficulty)
  3. apply it to produce the dest schema   (same call — mapping drives dest)
  4. wire the answer key into a Grader      (Grader(source_schema, transformations))

Returns a GeneratedTask namedtuple:
  - source_schema  : dict, the generated source (validated)
  - transformations: list[dict], the ordered source->dest mapping / answer key
  - dest_schema    : dict, the source with all transforms applied (real names;
                     call obfuscate_dest_schema() before showing it to the model)
  - grader         : Grader, pre-loaded with (source_schema, transformations) —
                     the generator's mapping IS the grader's answer key. Score a
                     migration with `task.grader.grade(source_data, dest_data)`.

The transformations list IS the answer key the grader replays. apply_difficulty
produces it together with dest_schema in one call (the mapping decision drives
each dest mutation), so orchestrate just guarantees a valid source first and then
binds the mapping to the grader.
"""

from collections import namedtuple

try:
    from .schema_generation import get_schema
    from .difficulty_dial import apply_difficulty
    from .schema import validate_schema
except ImportError:  # allow running as a flat script, not only as a package
    from schema_generation import get_schema
    from difficulty_dial import apply_difficulty
    from schema import validate_schema

# The grader lives in a sibling top-level package; support both package and
# flat-script execution.
try:
    from grader.grader import Grader
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from grader.grader import Grader


_MAX_SCHEMA_ATTEMPTS = 50


GeneratedTask = namedtuple(
    "GeneratedTask",
    ["source_schema", "transformations", "dest_schema", "grader"],
)


def orchestrate(tier=3):
    """
    Run the full generator pipeline for the given difficulty tier and bind the
    resulting mapping to a grader as its answer key.

    Tier 3 is the focus; Tier 2 is still supported.

    Returns:
        GeneratedTask(source_schema, transformations, dest_schema, grader)
    """
    if tier not in (2, 3):
        raise NotImplementedError(f"orchestrate: tier {tier} is not implemented")

    # 1. Generate a source schema, retrying until validate_schema passes.
    source_schema = None
    for _ in range(_MAX_SCHEMA_ATTEMPTS):
        candidate = get_schema(tier)
        problems = validate_schema(candidate)
        if not problems:
            source_schema = candidate
            break
    if source_schema is None:
        raise RuntimeError(
            f"orchestrate: could not generate a valid tier-{tier} source schema "
            f"in {_MAX_SCHEMA_ATTEMPTS} attempts"
        )

    # 2 + 3. Generate the transformation mapping and apply it to produce the
    # destination schema (apply_difficulty returns both together).
    dest_schema, transformations = apply_difficulty(source_schema, tier)

    # 4. Hand the answer key (source schema + transform mapping) to the grader.
    grader = Grader(source_schema, transformations)

    return GeneratedTask(source_schema, transformations, dest_schema, grader)
