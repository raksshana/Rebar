# Migration mapping (derived by matching field signatures between source and destination schemas)

# User -> EntityG
# User: id, name, email, role, bio, title, is_active, created_at, skills, department
# EntityG: id, fa(name/text), fc(email/text), fh(role/enum), ff(title/text), fd(is_active/bool), fb(created_at/date), fg(skills/multi_enum), fe(department/enum)
# Note: bio (richtext) has no match in EntityG, dropped

migrated_entity_g = []
for r in source_data.get("User", []):
    migrated_entity_g.append({
        "id": r["id"],
        "fa": r.get("name"),
        "fc": r.get("email"),
        "fh": r.get("role"),
        "ff": r.get("title"),
        "fd": r.get("is_active"),
        "fb": r.get("created_at"),
        "fg": r.get("skills"),
        "fe": r.get("department"),
    })
write_dest("EntityG", migrated_entity_g)

# Organization -> EntityH
# Organization: id, name, domain, website, employee_count, plan, industry, founded_at, size, description, metrics(nested MetricBlock)
# EntityH: id, fa(name/text), fh(domain/text), fi(website/text), fg(employee_count/number), fc(plan/enum), ff(industry/enum), fe(founded_at/date), fb(size/enum), fd(description/richtext)
# metrics nested block not present in EntityH, dropped

migrated_entity_h = []
for r in source_data.get("Organization", []):
    migrated_entity_h.append({
        "id": r["id"],
        "fa": r.get("name"),
        "fh": r.get("domain"),
        "fi": r.get("website"),
        "fg": r.get("employee_count"),
        "fc": r.get("plan"),
        "ff": r.get("industry"),
        "fe": r.get("founded_at"),
        "fb": r.get("size"),
        "fd": r.get("description"),
    })
write_dest("EntityH", migrated_entity_h)

# Location -> EntityB
# Location: id, name, type, manager_name, country, address, is_active, capacity, timezone, city
# EntityB: id, fe(name/text), ff(type/enum), fb(manager_name/text), fd(country/text), fc(is_active/bool), fg(capacity/number), fi(timezone/text), fa(address/text), fh(city/text)

migrated_entity_b = []
for r in source_data.get("Location", []):
    migrated_entity_b.append({
        "id": r["id"],
        "fe": r.get("name"),
        "ff": r.get("type"),
        "fb": r.get("manager_name"),
        "fd": r.get("country"),
        "fc": r.get("is_active"),
        "fg": r.get("capacity"),
        "fi": r.get("timezone"),
        "fa": r.get("address"),
        "fh": r.get("city"),
    })
write_dest("EntityB", migrated_entity_b)

# Vendor -> EntityC
# Vendor: id, name, email, country, rating, category, notes, payment_terms, status, tags(nested TagBlock)
# EntityC: id, fb(notes/richtext), fa(name/text), ff(email/text), fe(rating/number), fh(category/enum), fd(payment_terms/richtext->text stored as richtext), fi(country/text), fc(status/enum), fg(tags/nested TagBlock)

migrated_entity_c = []
for r in source_data.get("Vendor", []):
    migrated_entity_c.append({
        "id": r["id"],
        "fb": r.get("notes"),
        "fa": r.get("name"),
        "ff": r.get("email"),
        "fe": r.get("rating"),
        "fh": r.get("category"),
        "fd": r.get("payment_terms"),
        "fi": r.get("country"),
        "fc": r.get("status"),
        "fg": r.get("tags", []),
    })
write_dest("EntityC", migrated_entity_c)

# Contract -> EntityK
# Contract: id, vendor_id(->Vendor/EntityC), owner_id(->User/EntityG), status, value, end_date, signed_at, payment_terms, start_date, notes, auto_renew, type
# EntityK: id, fb(vendor_id -> ref EntityC), fd(owner_id -> ref EntityG), fa(status/enum), fh(value/number), fc(end_date/date), fe(signed_at/date), fg(start_date/date), fi(notes/richtext), ff(auto_renew/bool), fj(type/enum)
# payment_terms not in EntityK, dropped

migrated_entity_k = []
for r in source_data.get("Contract", []):
    migrated_entity_k.append({
        "id": r["id"],
        "fb": r.get("vendor_id"),
        "fd": r.get("owner_id"),
        "fa": r.get("status"),
        "fh": r.get("value"),
        "fc": r.get("end_date"),
        "fe": r.get("signed_at"),
        "fg": r.get("start_date"),
        "fi": r.get("notes"),
        "ff": r.get("auto_renew"),
        "fj": r.get("type"),
    })
write_dest("EntityK", migrated_entity_k)

# Page -> EntityL
# Page: id, title, author_id(->User/EntityG), status, is_locked, view_count, template, published_at, word_count, logs(nested LogBlock)
# EntityL: id, fi(title/text), fe(author_id -> ref EntityG), ff(status/enum), fa(is_locked/bool), fd(view_count/number), fc(template/enum), fh(published_at/date), fg(word_count/number), fb(logs/nested LogBlock)

migrated_entity_l = []
for r in source_data.get("Page", []):
    migrated_entity_l.append({
        "id": r["id"],
        "fi": r.get("title"),
        "fe": r.get("author_id"),
        "ff": r.get("status"),
        "fa": r.get("is_locked"),
        "fd": r.get("view_count"),
        "fc": r.get("template"),
        "fh": r.get("published_at"),
        "fg": r.get("word_count"),
        "fb": r.get("logs", []),
    })
write_dest("EntityL", migrated_entity_l)

# Audit -> EntityM
# Audit: id, actor_id(->User/EntityG), action, entity_type, entity_id, changes, outcome, resource, created_at, ip_address
# EntityM: id, fc(actor_id -> ref EntityG), fj(action/enum), fa(entity_type/text), fe(entity_id/text), fg(outcome/enum), fb(resource/text? or changes?), fi(created_at/date), ff(ip_address/text)
# Mapping: fc=actor_id, fj=action, fa=entity_type, fe=entity_id, fg=outcome, fb=resource, fi=created_at, ff=ip_address
# fd(multi_enum skills) - no match in Audit, set to empty list
# fh(text) - changes maps here as text

migrated_entity_m = []
for r in source_data.get("Audit", []):
    migrated_entity_m.append({
        "id": r["id"],
        "fc": r.get("actor_id"),
        "fj": r.get("action"),
        "fa": r.get("entity_type"),
        "fe": r.get("entity_id"),
        "fg": r.get("outcome"),
        "fb": r.get("resource"),
        "fi": r.get("created_at"),
        "ff": r.get("ip_address"),
        "fh": r.get("changes"),
        "fd": [],
    })
write_dest("EntityM", migrated_entity_m)

# Runbook -> EntityO
# Runbook: id, title, author_id(->User/EntityG), status, type, version, next_review_due, last_reviewed, is_approved, tags(multi_enum)
# EntityO: id, fi(title/text), ff(author_id -> ref EntityG), fd(status/enum), fe(type/enum), fb(version/text), fc(next_review_due/date), fa(last_reviewed/date), fh(is_approved/bool), fg(tags/multi_enum)

migrated_entity_o = []
for r in source_data.get("Runbook", []):
    migrated_entity_o.append({
        "id": r["id"],
        "fi": r.get("title"),
        "ff": r.get("author_id"),
        "fd": r.get("status"),
        "fe": r.get("type"),
        "fb": r.get("version"),
        "fc": r.get("next_review_due"),
        "fa": r.get("last_reviewed"),
        "fh": r.get("is_approved"),
        "fg": r.get("tags", []),
    })
write_dest("EntityO", migrated_entity_o)

# Customer -> EntityF
# Customer: id, name, email, status, company, mrr, source, country, is_verified, tier, steps(nested StepBlock)
# EntityF: id, fh(name/text), ff(email/text), fc(company/text), fb(mrr/number), fe(source/enum), fa(country/text), fi(is_verified/bool), fg(tier/enum), fd(steps/nested StepBlock)
# status not present in EntityF, dropped

migrated_entity_f = []
for r in source_data.get("Customer", []):
    migrated_entity_f.append({
        "id": r["id"],
        "fh": r.get("name"),
        "ff": r.get("email"),
        "fc": r.get("company"),
        "fb": r.get("mrr"),
        "fe": r.get("source"),
        "fa": r.get("country"),
        "fi": r.get("is_verified"),
        "fg": r.get("tier"),
        "fd": r.get("steps", []),
    })
write_dest("EntityF", migrated_entity_f)

# Tag -> EntityE
# Tag: id, name, slug, usage_count, description, color
# EntityE: id, fa(name/text), fe(slug/text), fc(usage_count/number), fb(description/text), fd(color/text), ff(text - no source match, set None)

migrated_entity_e = []
for r in source_data.get("Tag", []):
    migrated_entity_e.append({
        "id": r["id"],
        "fa": r.get("name"),
        "fe": r.get("slug"),
        "fc": r.get("usage_count"),
        "fb": r.get("description"),
        "fd": r.get("color"),
        "ff": None,
    })
write_dest("EntityE", migrated_entity_e)

# EntityA: id, fa(ref EntityG), fb(richtext)
# No direct source entity maps cleanly to EntityA's structure (just a ref to EntityG + richtext).
# We can use User bio + id to populate EntityA (one EntityA per User, fa=user.id, fb=user.bio)
migrated_entity_a = []
for r in source_data.get("User", []):
    migrated_entity_a.append({
        "id": r["id"],
        "fa": r.get("id"),
        "fb": r.get("bio"),
    })
write_dest("EntityA", migrated_entity_a)

# EntityD: id, fb(ref EntityH/Organization), fe(text), ff(number), fc(text), fa(number), fd(period/enum)
# Organization metrics (MetricBlock) can populate EntityD: one record per metric
# fb = org.id (ref EntityH), fa=metric.value, ff=metric.target, fe=metric.name, fc=metric.unit, fd=metric.period
metric_id_counter = 1
migrated_entity_d = []
for r in source_data.get("Organization", []):
    for metric in r.get("metrics", []):
        migrated_entity_d.append({
            "id": metric_id_counter,
            "fb": r["id"],
            "fe": metric.get("name"),
            "ff": metric.get("target"),
            "fc": metric.get("unit"),
            "fa": metric.get("value"),
            "fd": metric.get("period"),
        })
        metric_id_counter += 1
write_dest("EntityD", migrated_entity_d)

# EntityI: id, fa(name/text), ff(email/text), fe(company/text), fg(mrr/number), fc(source/enum), fi(country/text), fb(is_verified/bool), fd(tier/enum), fh(steps/nested StepBlock)
# This matches Customer again - migrate Customer to EntityI as well (duplicate/secondary mapping)
migrated_entity_i = []
for r in source_data.get("Customer", []):
    migrated_entity_i.append({
        "id": r["id"],
        "fa": r.get("name"),
        "ff": r.get("email"),
        "fe": r.get("company"),
        "fg": r.get("mrr"),
        "fc": r.get("source"),
        "fi": r.get("country"),
        "fb": r.get("is_verified"),
        "fd": r.get("tier"),
        "fh": r.get("steps", []),
    })
write_dest("EntityI", migrated_entity_i)

# EntityJ: id, ff(name/text), fh(email/text), fd(company/text), fc(mrr/number), fb(source/enum), fg(country/text), fi(is_verified/bool), fa(tier/enum), fe(steps/nested StepBlock)
# Another Customer-shaped entity
migrated_entity_j = []
for r in source_data.get("Customer", []):
    migrated_entity_j.append({
        "id": r["id"],
        "ff": r.get("name"),
        "fh": r.get("email"),
        "fd": r.get("company"),
        "fc": r.get("mrr"),
        "fb": r.get("source"),
        "fg": r.get("country"),
        "fi": r.get("is_verified"),
        "fa": r.get("tier"),
        "fe": r.get("steps", []),
    })
write_dest("EntityJ", migrated_entity_j)

# EntityN: id, fd(name/text), fc(email/text), fb(company/text), fe(mrr/number), fg(source/enum), ff(country/text), fh(is_verified/bool), fi(tier/enum), fa(steps/nested StepBlock)
# Another Customer-shaped entity
migrated_entity_n = []
for r in source_data.get("Customer", []):
    migrated_entity_n.append({
        "id": r["id"],
        "fd": r.get("name"),
        "fc": r.get("email"),
        "fb": r.get("company"),
        "fe": r.get("mrr"),
        "fg": r.get("source"),
        "ff": r.get("country"),
        "fh": r.get("is_verified"),
        "fi": r.get("tier"),
        "fa": r.get("steps", []),
    })
write_dest("EntityN", migrated_entity_n)

# EntityP: id, fc(name/text), fb(email/text), fg(company/text), fa(mrr/number), fi(source/enum), fh(country/text), ff(is_verified/bool), fd(tier/enum), fe(steps/nested StepBlock)
# Another Customer-shaped entity
migrated_entity_p = []
for r in source_data.get("Customer", []):
    migrated_entity_p.append({
        "id": r["id"],
        "fc": r.get("name"),
        "fb": r.get("email"),
        "fg": r.get("company"),
        "fa": r.get("mrr"),
        "fi": r.get("source"),
        "fh": r.get("country"),
        "ff": r.get("is_verified"),
        "fd": r.get("tier"),
        "fe": r.get("steps", []),
    })
write_dest("EntityP", migrated_entity_p)