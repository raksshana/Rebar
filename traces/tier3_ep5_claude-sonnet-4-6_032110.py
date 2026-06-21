# Migration mapping analysis:
# Source -> Destination:
# Environment -> EntityC
# Currency -> EntityG + EntityH (Currency has no direct match; best fit split or EntityG for date-based)
# User -> EntityD
# Project -> EntityM
# Service -> EntityA
# Task -> EntityE
# Workflow -> EntityB (or EntityF or EntityI or EntityL)
# Feature -> EntityK

# Let's analyze field by field:

# Environment -> EntityC
# Environment: id, name, type(enum dev/staging/prod/dr), cloud_provider(enum), created_at(date), is_active(bool), description(richtext), checklist(nested)
# EntityC: id, fg(text), fd(enum dev/staging/prod/dr), fe(enum aws/gcp/azure/on_prem/hybrid), fa(date), fb(bool), fc(richtext), ff(bool)
# Mapping: name->fg, type->fd, cloud_provider->fe, created_at->fa, is_active->fb, description->fc
# ff(bool) has no source match -> None
# checklist is dropped (EntityC has no nested field)

entity_c_records = []
for rec in source_data.get("Environment", []):
    entity_c_records.append({
        "id": rec["id"],
        "fg": rec.get("name"),
        "fd": rec.get("type"),
        "fe": rec.get("cloud_provider"),
        "fa": rec.get("created_at"),
        "fb": rec.get("is_active"),
        "fc": rec.get("description"),
        "ff": None,
    })
write_dest("EntityC", entity_c_records)

# Currency -> EntityG + EntityH
# EntityG: id, fa(date)
# EntityH: id, fa(ref EntityG), fd(text), fb(text), ff(number), fe(text), fc(number)
# Currency: id, code(text), symbol(text), name(text), exchange_rate(number), updated_at(date), is_default(bool)
# EntityG gets: id, fa=updated_at
# EntityH gets: id, fa=currency_id(ref EntityG), fd=code, fb=name, ff=exchange_rate, fe=symbol, fc=None (is_default bool->no number field)
# is_default(bool) doesn't fit EntityH fields well; drop it or ignore
# Actually EntityH.fc is number, EntityH.ff is number
# exchange_rate->ff, is_default has no target -> drop
# fc(number) no source match -> None

entity_g_records = []
entity_h_records = []
for rec in source_data.get("Currency", []):
    entity_g_records.append({
        "id": rec["id"],
        "fa": rec.get("updated_at"),
    })
    entity_h_records.append({
        "id": rec["id"],
        "fa": rec["id"],  # ref to EntityG same id
        "fd": rec.get("code"),
        "fb": rec.get("name"),
        "ff": rec.get("exchange_rate"),
        "fe": rec.get("symbol"),
        "fc": None,
    })
write_dest("EntityG", entity_g_records)
write_dest("EntityH", entity_h_records)

# User -> EntityD
# User: id, name(text), email(text), role(enum admin/member/viewer/guest), created_at(date), phone(text), title(text), skills(multi_enum), bio(richtext), department(enum), timezone(text), line_items(nested LineItemBlock)
# EntityD: id, fa(text), fk(text), fh(enum admin/member/viewer/guest), ff(date), fb(text), fj(text), fe(multi_enum backend/frontend/data/ml/design/ops/security), fc(richtext), fd(enum engineering/product/design/sales/ops/support/legal/finance), fi(text), fg(nested LineItemBlock)
# Mapping: name->fa, email->fk, role->fh, created_at->ff, phone->fb, title->fj, skills->fe, bio->fc, department->fd, timezone->fi, line_items->fg

entity_d_records = []
for rec in source_data.get("User", []):
    entity_d_records.append({
        "id": rec["id"],
        "fa": rec.get("name"),
        "fk": rec.get("email"),
        "fh": rec.get("role"),
        "ff": rec.get("created_at"),
        "fb": rec.get("phone"),
        "fj": rec.get("title"),
        "fe": rec.get("skills"),
        "fc": rec.get("bio"),
        "fd": rec.get("department"),
        "fi": rec.get("timezone"),
        "fg": rec.get("line_items"),
    })
write_dest("EntityD", entity_d_records)

# Project -> EntityM
# Project: id, name(text), owner_id(ref User), status(enum draft/active/on_hold/completed/cancelled), is_public(bool), priority(enum low/medium/high/critical), end_date(date), description(richtext), start_date(date), budget(number), custom_fields(nested CustomFieldBlock)
# EntityM: id, fe(text), ff(ref EntityD), fb(enum draft/active/on_hold/completed/cancelled), fg(enum low/medium/high/critical), fi(date), fh(richtext), fa(date), fc(number), fd(nested CustomFieldBlock)
# Mapping: name->fe, owner_id->ff(ref EntityD), status->fb, priority->fg, end_date->fi, description->fh, start_date->fa, budget->fc, custom_fields->fd
# is_public(bool) -> no bool field in EntityM -> drop

entity_m_records = []
for rec in source_data.get("Project", []):
    entity_m_records.append({
        "id": rec["id"],
        "fe": rec.get("name"),
        "ff": rec.get("owner_id"),
        "fb": rec.get("status"),
        "fg": rec.get("priority"),
        "fi": rec.get("end_date"),
        "fh": rec.get("description"),
        "fa": rec.get("start_date"),
        "fc": rec.get("budget"),
        "fd": rec.get("custom_fields"),
    })
write_dest("EntityM", entity_m_records)

# Service -> EntityA
# Service: id, name(text), env_id(ref Environment->EntityC), owner_id(ref User->EntityD), tier(enum critical/standard/low), sla_minutes(number), language(text), port(number), version(text), repo_url(text), description(richtext), addresses(nested AddressBlock)
# EntityA: id, fb(text), fe(ref EntityC), fg(ref EntityD), fc(enum critical/standard/low), ff(number), fj(text), fa(number), fh(text), fi(text), fl(richtext), fd(nested AddressBlock), fk(text)
# Mapping: name->fb, env_id->fe, owner_id->fg, tier->fc, sla_minutes->ff, language->fj, port->fa, version->fh, repo_url->fi, description->fl, addresses->fd
# fk(text) -> no source match -> None

entity_a_records = []
for rec in source_data.get("Service", []):
    entity_a_records.append({
        "id": rec["id"],
        "fb": rec.get("name"),
        "fe": rec.get("env_id"),
        "fg": rec.get("owner_id"),
        "fc": rec.get("tier"),
        "ff": rec.get("sla_minutes"),
        "fj": rec.get("language"),
        "fa": rec.get("port"),
        "fh": rec.get("version"),
        "fi": rec.get("repo_url"),
        "fl": rec.get("description"),
        "fd": rec.get("addresses"),
        "fk": None,
    })
write_dest("EntityA", entity_a_records)

# Task -> EntityE
# Task: id, title(text), project_id(ref Project->EntityM), assignee_id(ref User->EntityD), status(enum todo/in_progress/in_review/done/cancelled), due_date(date), is_blocked(bool), type(enum feature/bug/chore/spike/epic), description(richtext), tags(multi_enum frontend/backend/infra/design/data), created_at(date), priority(enum low/medium/high/critical), points(number)
# EntityE: id, fc(text), fi(ref EntityM), fe(ref EntityD), fd(enum todo/in_progress/in_review/done/cancelled), fb(date), ff(bool), fa(enum feature/bug/chore/spike/epic), fj(multi_enum frontend/backend/infra/design/data), fg(date), fk(enum low/medium/high/critical), fh(number)
# Mapping: title->fc, project_id->fi, assignee_id->fe, status->fd, due_date->fb, is_blocked->ff, type->fa, tags->fj, created_at->fg, priority->fk, points->fh
# description(richtext) -> no richtext field in EntityE -> drop

entity_e_records = []
for rec in source_data.get("Task", []):
    entity_e_records.append({
        "id": rec["id"],
        "fc": rec.get("title"),
        "fi": rec.get("project_id"),
        "fe": rec.get("assignee_id"),
        "fd": rec.get("status"),
        "fb": rec.get("due_date"),
        "ff": rec.get("is_blocked"),
        "fa": rec.get("type"),
        "fj": rec.get("tags"),
        "fg": rec.get("created_at"),
        "fk": rec.get("priority"),
        "fh": rec.get("points"),
    })
write_dest("EntityE", entity_e_records)

# Workflow -> best match analysis:
# Workflow: id, name(text), project_id(ref Project->EntityM), creator_id(ref User->EntityD), status(enum active/inactive/draft/archived), trigger(enum manual/schedule/event/webhook), last_run(date), is_active(bool), step_count(number), schedule(text), description(richtext), run_count(number)
# 
# EntityB: id, fg(text), fa(ref EntityM), fh(enum active/inactive/draft/archived), fb(date), fd(bool), fe(number), fi(text), fj(richtext), fc(number), ff(ref EntityD)
# Mapping: name->fg, project_id->fa, status->fh, last_run->fb, is_active->fd, step_count->fe, schedule->fi, description->fj, run_count->fc, creator_id->ff
# trigger(enum) -> no enum field for trigger values in EntityB -> drop
# EntityB matches very well!

entity_b_records = []
for rec in source_data.get("Workflow", []):
    entity_b_records.append({
        "id": rec["id"],
        "fg": rec.get("name"),
        "fa": rec.get("project_id"),
        "fh": rec.get("status"),
        "fb": rec.get("last_run"),
        "fd": rec.get("is_active"),
        "fe": rec.get("step_count"),
        "fi": rec.get("schedule"),
        "fj": rec.get("description"),
        "fc": rec.get("run_count"),
        "ff": rec.get("creator_id"),
    })
write_dest("EntityB", entity_b_records)

# Feature -> EntityK
# Feature: id, name(text), project_id(ref Project->EntityM), owner_id(ref User->EntityD), status(enum ideation/planned/in_progress/launched/cancelled), type(enum enhancement/new_feature/improvement/deprecation), description(richtext), priority(enum low/medium/high/critical), impact_estimate(enum low/medium/high/transformational), is_breaking(bool), tags(multi_enum frontend/backend/api/mobile/platform)
# EntityK: id, ff(text), fg(ref EntityM), fd(ref EntityD), fh(enum ideation/planned/in_progress/launched/cancelled), fc(enum enhancement/new_feature/improvement/deprecation), fa(richtext), fb(enum low/medium/high/critical), fi(enum low/medium/high/transformational), fe(bool), fj(multi_enum frontend/backend/api/mobile/platform)
# Mapping: name->ff, project_id->fg, owner_id->fd, status->fh, type->fc, description->fa, priority->fb, impact_estimate->fi, is_breaking->fe, tags->fj

entity_k_records = []
for rec in source_data.get("Feature", []):
    entity_k_records.append({
        "id": rec["id"],
        "ff": rec.get("name"),
        "fg": rec.get("project_id"),
        "fd": rec.get("owner_id"),
        "fh": rec.get("status"),
        "fc": rec.get("type"),
        "fa": rec.get("description"),
        "fb": rec.get("priority"),
        "fi": rec.get("impact_estimate"),
        "fe": rec.get("is_breaking"),
        "fj": rec.get("tags"),
    })
write_dest("EntityK", entity_k_records)

# Handle remaining destination entities that have no direct source match:
# EntityF, EntityI, EntityJ, EntityL -> emit empty lists
write_dest("EntityF", [])
write_dest("EntityI", [])
write_dest("EntityJ", [])
write_dest("EntityL", [])