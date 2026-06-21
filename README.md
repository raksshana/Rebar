# Rebar

Built by Raksshana and Vihari for HUD's Frontier RL Environments Hackathon @ Y Combinator.

Data migrations fail silently and cost millions. Rebar is an RL training stack that teaches models to migrate data between mismatched schemas autonomously — generating verifiable tasks, grading every record, and closing the gap where frontier LLMs still break down.

## Why it matters

Organizations are always migrating data. Legacy databases get replaced by modern warehouses. Acquisitions fold one company's CRM into another's. Teams outgrow spreadsheets and move to Postgres, Snowflake, or Databricks. The natural end state is an **AI agent** that reads both schemas, writes the transformation code, runs it, and verifies the output—fully autonomously, at any scale.

At small scale, that already looks plausible. A frontier LLM can draft a migration script from a source schema and a target spec, execute it, and pass a spot-check on a few rows. The task looks like code generation, and models are good at that. **Full autonomy at real-world scale is a different problem.** The hard part is rarely "copy table A to table B." It is inferring what the data *means*, preserving relationships and invariants across incompatible systems, handling edge cases in messy source data, and proving correctness across millions or billions of records—without a human in the loop to catch mistakes.

That gap shows up in production migrations and in evals: frontier models score well on toy mappings but fall apart as complexity increases. Practitioner reports point to the same failure modes:

| What shows up in real migrations | Why agents struggle |
| --- | --- |
| Multiple vendors (Salesforce, Databricks, Foundry) with no single source of truth | **Schema heterogeneity** — the same entity is modeled differently across systems; the agent must reconcile conflicting representations without explicit documentation |
| $100M reconciliation gaps after Redshift → Snowflake; SQL logic that "worked" in the old warehouse | **Business logic embedded in queries** — transformation is not just reshaping columns; computed meaning lives in ad-hoc SQL the agent never sees |
| Auto-incremented IDs in the new system with no traceability back to Salesforce | **ID remapping** — new primary keys are generated and every foreign-key reference must be rewritten consistently across tables |
| 32-layer dependency graph, ~1B records, strict ordering (migrate X before Y) | **Ordering constraints at scale** — topological dependencies plus volume; one wrong step corrupts downstream tables with no easy rollback |
| Excel exports with duplicate rows, broken links, and inconsistent date formats | **Data quality** — nulls, format drift, orphan references, and duplicates that only surface when the agent's script runs on the full dataset |

These are exactly the skills Rebar is built to measure and improve. An agent must **read a source schema, read a target schema, write transformation code, and pass record-level verification**—with difficulty that scales from simple renames to obfuscated, multi-table structural changes. The goal is to find where frontier models fail today, and train them to close the gap toward reliable autonomous migration.

## System architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Generator                                │
│                                                                 │
│  Builds a random source schema, applies difficulty transforms   │
│  (rename, retype, merge, split, partition, etc.) to produce a  │
│  destination schema + ground-truth transformation log.          │
│  Faker fills structured fields; Gemini fills richtext.          │
│  Tier 3: dest entity and field names are obfuscated             │
│  (EntityA, fa, fb…) before being shown to the model.           │
└───────────────────────────────┬─────────────────────────────────┘
                                │ source schema, dest schema,
                                │ source data, transformation log
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Model                                  │
│                                                                 │
│  Receives source schema, dest schema, and source data.          │
│  Returns a Python script that calls write_dest() to emit        │
│  migrated records.                                              │
└───────────────────────────────┬─────────────────────────────────┘
                                │ migration script
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Grader                                 │
│                                                                 │
│  Executes the script, then scores the output on five axes:      │
│  • coverage               did records reach the right entity?   │
│  • field_fidelity         are field values correct?             │
│  • relationship_integrity do refs point to valid IDs?           │
│  • type_correctness       are Python types right?               │
│  • structural             were merges/splits/partitions done?   │
│                                                                 │
│  total = base × (0.20 + 0.80 × structural) × 100               │
│  A model that copies fields but skips structural transforms     │
│  is capped at ~20/100.                                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ reward (0–1)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       HUD Training Loop                         │
│                                                                 │
│  Online RL: the model trains continuously as episodes run.      │
│  GRPO groups identical tasks (same seed) so rollouts within a  │
│  group are directly comparable. HUD handles the training loop.  │
└─────────────────────────────────────────────────────────────────┘
```

### Transforms applied

Entity and field names are obfuscated (EntityA, fa, fb…). The model must reverse-engineer the mapping purely from structural clues — enum value sets, ref targets, field type patterns — with no name hints.

Transforms: renames, retypes, enum remaps, unmapped fields, flatten nested, computed fields, denormalize, merges, splits, partitions, extract nested.
