# Model Traces: Claude Sonnet 4.6 vs Claude Opus 4.8

These are the actual migration scripts each model generated across 5 identical Tier 3 episodes.
Same prompt, same schema, same source data — only the model differs.

**Final scores (averaged over 5 episodes):**

| Model | Total |
|---|---|
| Claude Sonnet 4.6 | 60.0 |
| Claude Opus 4.8 | 52.4 |

---

## What Tier 3 requires

Each episode gives the model:
- A source schema with readable entity/field names
- A destination schema with obfuscated names (EntityA, EntityB…, fa, fb…)
- Source data records

The model must infer the mapping from structural clues alone (field types, enum value sets, ref targets) and write a Python script that calls `write_dest(entity_name, records)`.

The grader scores on five axes. The most important is **structural** — a multiplier:

```
total = base × (0.20 + 0.80 × structural) × 100
```

Models that skip structural transforms (merges, splits, extract_nested, partitions) are capped at roughly 20/100 regardless of field-level accuracy. Every structural miss compounds the penalty across all other axes.

---

## Per-episode comparison

| Episode | What Opus misses | What Sonnet does |
|---|---|---|
| ep1 | Audit→EntityD bridge (split) | Creates EntityD records from Audit actor info, links via `fc` ref |
| ep2 | Org.metrics→EntityD (extract_nested) | Iterates metrics into flat EntityD rows with auto-incremented IDs |
| ep3 | Review.line_items→EntityF; Deployment→EntityL | Both extract_nested and derived split done correctly |
| ep4 | Environment.comments→EntityE; Customer→4 entities | Extracts nested comments with ID counter; routes Customer to all 4 dest entities |
| ep5 | Workflow routed to EntityI instead of EntityB | Correct entity match via field signature analysis |

---

## The smoking gun: Episode 2

The clearest single example. Both models receive the same Organization entity with a `metrics` nested block field.

**Opus ep2** — maps Organization to EntityK with metrics inlined:
```python
write_dest("EntityK", [{
    "id": r["id"],
    "fa": r.get("name"),
    "fb": r.get("metrics"),   # nested block passed through as-is
    ...
}])
# EntityD never written
```

**Sonnet ep2** — identifies metrics as an extract_nested transform:
```python
metric_id_counter = 1
entity_d_records = []
for r in source_data.get("Organization", []):
    for metric in r.get("metrics", []):
        entity_d_records.append({
            "id": metric_id_counter,
            "fb": r["id"],          # foreign key back to Organization
            "fa": metric.get("name"),
            "fc": metric.get("value"),
            ...
        })
        metric_id_counter += 1
write_dest("EntityD", entity_d_records)
```

This loop — iterating a nested block into a separate entity with a link field — is exactly what the grader's `extract_nested` structural check looks for. Opus never writes to EntityD at all in episode 2.

---

## Why the gap is real, not a grading artifact

1. **Pattern is consistent across all 5 episodes.** Sonnet attempts more structural transforms in every single episode. This is not a sampling fluke.

2. **Opus applies the right structural pattern to the wrong field in ep3.** It iterates `ApiKey.reviews` (not a nested block in the source schema) instead of `Review.line_items` (the actual nested block). The coding pattern is structurally identical — Opus understands extract_nested — but it misidentifies the source. The grader correctly gives zero structural credit because the ground truth log records the transform as `{source: "Review", field: "line_items", dest: "EntityF"}`.

3. **The structural multiplier amplifies every miss.** If Opus gets `structural = 0.53` vs Sonnet's `0.58`, the downstream effect on total is large because structural multiplies the base score across all five axes simultaneously.

4. **One legitimate caveat:** In ep2 and ep4 Sonnet writes Customer records to 4 destination entities simultaneously. If the ground truth routes to only one, those extra writes create false-positive coverage penalties. Despite this potential penalty, Sonnet still scores higher — meaning the structural multiplier gain outweighs the coverage cost.

---

## Files

Each file is named `tier3_ep{N}_{model}_032110.py`. Episodes 1–5 use identical schemas and source data across both models (same random seed per episode, generated at 03:21:10).
