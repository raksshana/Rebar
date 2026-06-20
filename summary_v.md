Summary for Vihari's Code

---

## 2026-06-20

### Created `generator/__init__.py`
Empty package init file.

### Created `generator/schema.py`
`validate_schema(schema)` — checks: exactly one `id` per entity, all `ref.target` exist, all
`nested.of` exist, no name collisions between entities and blocks. Returns list of problem strings
(empty = valid).

### Created `generator/schema_generation.py` (v1 — fixed blueprints, replaced by v2)
Initial version: 25-entity catalog, 4 fixed Tier-3 blueprints. Replaced same session.

### Rewrote `generator/schema_generation.py` (v2 — large randomized pool)
`get_schema(tier)` — implemented for **Tier 2** and **Tier 3** only.

**Shared entity pool — 59 entity types across 4 layers:**
- Layer 0 (9 roots): User, Organization, Customer, Vendor, Product, Environment, Tag, Location, Currency
- Layer 1 (25 entities): all deps are roots — Project, Team, Department, Workspace, Article, Course,
  Service, Order, Subscription, Contract, Account, Note, Page, Runbook, Policy, Asset, Report,
  Review, Server, Cluster, Ticket, Audit, Session, Notification
- Layer 2 (23 entities): at least one dep is Layer-1 — Task, Issue, Sprint, Milestone, Label,
  Feature, Release, Workflow, Employee, TeamMember, Channel, Deployment, Alert, Pipeline, Webhook,
  ApiKey, OrderItem, Invoice, Payment, Shipment, Enrollment, Comment, Opportunity, Document
- Layer 3 (2 entities): Incident (deps: Alert+Environment), Grade (deps: Enrollment)

Each entity has a fixed canonical field set (semantically appropriate) plus an optional_pool of
scalar fields sampled to add variation. Refs are only in base_fields; optional_pool is scalars only.

**12 nested block types:** LineItemBlock, CommentBlock, TagBlock, AddressBlock, ReviewBlock,
AttachmentBlock, ChecklistBlock, MetricBlock, ContactBlock, StepBlock, LogBlock, CustomFieldBlock.
Each block has 3–6 richer fields than the previous version.

**Tier 2 — 6–10 entities, 2–3 blocks, medium field density:**
- Seeds with User + 1–2 random roots; greedy expansion picks uniformly from candidates.
- Optional fields: 1..N sampled from pool.
- Validated: 20/20 pass; 48–89 total fields per schema; 2–7 refs; 6–20 enums.

**Tier 3 — 8–12 entities, 3–4 blocks, high field density:**
- Same greedy algorithm but biases 70% toward multi-dep (≥2 refs) candidates for denser cross-connections.
- Optional fields: max(1, 2/3 of pool)..N sampled (more fields per entity).
- Validated: 20/20 pass; 78–133 total fields per schema; 6–16 refs; 11–28 enums.
- Entity combos vary widely across runs (project-tracking, devops, CRM, e-commerce, etc.).

### Created `generator/difficulty_dial.py`
`apply_difficulty(source_schema, tier)` → `(dest_schema, transformations)` — Tier 2 and Tier 3 only.

**T1 noise (`_apply_tier1`):** rename 1–2 non-id/non-nested fields; retype 1–2 coercible fields
(coercion table: text→richtext, richtext→text, number→text/bool, date→text, bool→number);
60%-chance enum_remap (all values of one enum field suffixed with _v2/_new/_updated).

**Tier 2 (`_apply_tier2`):** shuffle pool {split, merge, flatten_nested, unmapped}, try first 2.
Fall back to T1 if 0 structural ops succeed. Validated 50/50 PASS.

**Tier 3 (`_apply_tier3`):** ordered pipeline —
1. T1 noise, 2. unmapped, 3. extract_nested, 4. split, 5. merge×2, 6. partition, 7. denormalize,
8. computed×1–2. Entity exclusion sets prevent dangling refs at each step.
Validated 50/50 PASS. All 10 transform types fire across 50 samples.

**Structural transforms:**
- `_try_split`: picks entity with ≥4 fields; moves random subset of scalars to `{Name}Detail`
  with back-ref `{name_lower}_id` FK.
- `_try_merge`: child must have exactly 1 ref to parent; parent must have no other incoming refs;
  child must have no incoming refs. Child's `id` field dropped. Merges into `{Parent}{Suffix}`.
- `_try_flatten_nested`: replaces nested field with `{field}_count: number`.
- `_try_extract_nested`: moves nested block to new `{BlockBase}{Suffix}` child entity with FK.
- `_try_partition`: splits entity by enum discriminator into `{Synonym}{Entity}` sub-entities;
  restricted to entities with no incoming refs (prevents dangling refs on deletion).
  T1-remapped enum values resolved back to originals for synonym lookup.
- `_try_denormalize`: inlines 1–2 scalars from ref target; stores pre-rename source field name.
- `_try_computed`: adds opaque derived field (concat/multiply/sum_fields/bool_from_enum);
  denorm inline fields excluded as source candidates.

**Obfuscation (Tier 3):**
- `obfuscate_dest_schema(dest)` → `(obf_schema, entity_map, field_maps)`: EntityA/fa/fb labelling,
  shuffled order, `id` stays `id`, `ref.target` rewritten.
- `translate_dest_data(dest_data, entity_map, field_maps)`: reverses obfuscation for grader.
