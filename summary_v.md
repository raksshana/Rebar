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
