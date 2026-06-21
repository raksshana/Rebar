# Rebar

Project for HUD's Frontier RSI/RL Environments Hackathon @ Y Combinator by Raksshana and Vihari

Rebar is a benchmark and training environment for **schema migration**: given a source database and a target schema, an agent must write a script that transforms and loads the data correctly. We grade every record, not just whether the script runs.

## Why this project

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
│                        generator/                               │
│                                                                 │
│  schema_generation.py  →  difficulty_dial.py  →  orchestrate() │
│  Builds a random          Applies transforms      Ties together │
│  source schema            (rename, retype,        schema +      │
│  (entities, fields,       merge, split,           transforms +  │
│  nested blocks)           partition, etc.)        Grader        │
│                                                                 │
│  data_generation.py                                             │
│  Faker for structured fields (dates, enums, refs)              │
│  Gemini for richtext and unrecognized text fields              │
└───────────────────────────────┬─────────────────────────────────┘
                                │ GeneratedTask
                                │ (source_schema, dest_schema,
                                │  transformations, grader)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      migration_episode.py                       │
│                                                                 │
│  build_episode(seed, tier, n_records)                           │
│  Deterministic: same seed → identical schema + data every time  │
│  Tier 3: obfuscates dest entity/field names (EntityA, fa, fb…) │
│  before showing them to the model                               │
└───────────────────────────────┬─────────────────────────────────┘
                                │ prompt
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          model                                  │
│                                                                 │
│  Receives: source schema, dest schema, source data              │
│  Returns: a Python migration script                             │
│                                                                 │
│  Frontier baselines: Claude Opus/Sonnet, GPT-5.5, Gemini Flash  │
│  RL target: Kimi K2.5 (fine-tuned via Fireworks + HUD GRPO)    │
└───────────────────────────────┬─────────────────────────────────┘
                                │ script
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     agent/wrapper.py                            │
│                                                                 │
│  _extract_code()   strips ```python fences                      │
│  _exec_script()    exec() with write_dest() injected            │
│                    captures stdout/stderr, never raises          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ dest_store
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        grader/                                  │
│                                                                 │
│  Tier 3: translate_dest_data() reverses name obfuscation first  │
│                                                                 │
│  grader.grade(source_data, dest_data) scores five axes:         │
│  • coverage               (0–1)  did records reach the right   │
│                                  destination entity?            │
│  • field_fidelity         (0–1)  are field values correct?      │
│  • relationship_integrity (0–1)  do refs point to valid IDs?    │
│  • type_correctness       (0–1)  are Python types right?        │
│  • structural             (0–1)  were merges/splits/partitions  │
│                                  actually performed?            │
│                                                                 │
│  total = base × (0.20 + 0.80 × structural) × 100               │
│  structural acts as a multiplier — a model that copies fields   │
│  but skips structural transforms is capped at ~20/100           │
└───────────────────────────────┬─────────────────────────────────┘
                                │ reward (total / 100)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  harness/ + HUD platform                        │
│                                                                 │
│  harness/env.py    HUD Environment template — one episode       │
│  harness/train.py  GRPO training loop via HUD TrainingClient    │
│                    group_size rollouts per task, same seed →    │
│                    identical task for all rollouts in a group   │
│                                                                 │
│  Eval:     Taskset([tasks]).run(agent, runtime=LocalRuntime)    │
│  Training: TrainingClient.step(batch) → Fireworks fine-tune     │
└─────────────────────────────────────────────────────────────────┘
```

### Difficulty tiers

| Tier | What the model sees | Transforms applied |
|------|--------------------|--------------------|
| 2    | Real entity and field names | Renames, retypes, enum remaps, unmapped fields, flatten nested, computed fields, denormalize |
| 3    | Obfuscated names (EntityA, fa, fb…) | All of Tier 2 plus merges, splits, partitions, extract nested |

Tier 3 requires the model to reverse-engineer which source entity maps to which destination entity purely from structural clues — enum value sets, ref targets, field type patterns — with no name hints.
