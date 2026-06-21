# Migration mapping analysis:
# Source -> Destination entity mappings:
# User -> EntityK
# Environment -> EntityP
# Vendor -> EntityE
# Contract -> EntityQ
# Note -> EntityJ
# Audit -> EntityN (needs EntityD for actor ref)
# Notification -> EntityA/EntityB/EntityG/EntityI/EntityL/EntityO (pick one - EntityL fits best)
# Service -> EntityC
# ApiKey -> EntityH
# Runbook -> EntityM
# Runbook attachments -> EntityF

# User -> EntityK
# User: id, name, email, role, timezone, is_active, title, skills, department
# EntityK: id, fd(name), fb(email), fc(role), ff(timezone), fa(is_active), fg(skills), fe(department)
# Missing: title -> no direct match in EntityK... but EntityK has fd,fb,fc,ff,fa,fg,fe
# title field has no match - we'll store name->fd, email->fb, role->fc, timezone->ff, is_active->fa, skills->fg, department->fe
# title doesn't have a field - it gets dropped

entity_k_records = []
for rec in source_data.get("User", []):
    entity_k_records.append({
        "id": rec["id"],
        "fd": rec.get("name"),
        "fb": rec.get("email"),
        "fc": rec.get("role"),
        "ff": rec.get("timezone"),
        "fa": rec.get("is_active"),
        "fg": rec.get("skills"),
        "fe": rec.get("department"),
    })
write_dest("EntityK", entity_k_records)

# Environment -> EntityP
# Environment: id, name, type, is_active, tier, region, created_at, cloud_provider
# EntityP: id, fc(name?), fi(type), fh(is_active), ff(tier), fa(region?), fb(created_at), fg(cloud_provider), fe(?), fd(bool?)
# EntityP fields: fc(text), fi(enum dev/staging/prod/dr), fh(bool), ff(enum critical/standard/low), fa(text), fb(date), fg(enum aws/gcp/azure/on_prem/hybrid), fe(text), fd(bool)
# name->fa or fc, type->fi, is_active->fh, tier->ff, region->fa or fc, created_at->fb, cloud_provider->fg
# fa=text(region), fc=text(name), fi=type, fh=is_active, ff=tier, fb=created_at, fg=cloud_provider
# fe=text (no match left - extra text field), fd=bool (no match left)

entity_p_records = []
for rec in source_data.get("Environment", []):
    entity_p_records.append({
        "id": rec["id"],
        "fc": rec.get("name"),
        "fi": rec.get("type"),
        "fh": rec.get("is_active"),
        "ff": rec.get("tier"),
        "fa": rec.get("region"),
        "fb": rec.get("created_at"),
        "fg": rec.get("cloud_provider"),
        "fe": None,
        "fd": None,
    })
write_dest("EntityP", entity_p_records)

# Vendor -> EntityE
# Vendor: id, name, email, status, country, payment_terms, notes, website, contract_type, category, contacts
# EntityE: id, fd(name), ff(email?), fe(status), fc(country), fi(notes richtext), fa(website?), fj(contract_type), fg(category), fb(contacts nested ContactBlock), fh(payment_terms)
# fd=text(name), ff=text(email), fe=enum(status), fc=text(country), fi=richtext(notes), fa=text(website), fj=enum(contract_type), fg=enum(category), fb=nested contacts, fh=text(payment_terms)

entity_e_records = []
for rec in source_data.get("Vendor", []):
    entity_e_records.append({
        "id": rec["id"],
        "fd": rec.get("name"),
        "ff": rec.get("email"),
        "fe": rec.get("status"),
        "fc": rec.get("country"),
        "fi": rec.get("notes"),
        "fa": rec.get("website"),
        "fj": rec.get("contract_type"),
        "fg": rec.get("category"),
        "fb": rec.get("contacts"),
        "fh": rec.get("payment_terms"),
    })
write_dest("EntityE", entity_e_records)

# Contract -> EntityQ
# Contract: id, vendor_id(->Vendor/EntityE), owner_id(->User/EntityK), status, value, type, signed_at, auto_renew, payment_terms, end_date, start_date, notes
# EntityQ: id, fj(ref EntityE vendor_id), fb(ref EntityK owner_id), fd(status enum), fg(value number), fi(type enum), fc(signed_at date), fk(auto_renew bool), fh(payment_terms text), ff(end_date date), fa(start_date date), fe(notes richtext)

entity_q_records = []
for rec in source_data.get("Contract", []):
    entity_q_records.append({
        "id": rec["id"],
        "fj": rec.get("vendor_id"),
        "fb": rec.get("owner_id"),
        "fd": rec.get("status"),
        "fg": rec.get("value"),
        "fi": rec.get("type"),
        "fc": rec.get("signed_at"),
        "fk": rec.get("auto_renew"),
        "fh": rec.get("payment_terms"),
        "ff": rec.get("end_date"),
        "fa": rec.get("start_date"),
        "fe": rec.get("notes"),
    })
write_dest("EntityQ", entity_q_records)

# Note -> EntityJ
# Note: id, title, author_id(->User/EntityK), status, view_count, content, word_count, is_pinned, created_at, format, tags
# EntityJ: id, fg(ref EntityK author_id), fb(status enum), fa(view_count number), ff(content richtext), fh(word_count number), fd(is_pinned bool), fe(created_at date), fi(format enum), fc(tags multi_enum)
# title has no field in EntityJ... dropped

entity_j_records = []
for rec in source_data.get("Note", []):
    entity_j_records.append({
        "id": rec["id"],
        "fg": rec.get("author_id"),
        "fb": rec.get("status"),
        "fa": rec.get("view_count"),
        "ff": rec.get("content"),
        "fh": rec.get("word_count"),
        "fd": rec.get("is_pinned"),
        "fe": rec.get("created_at"),
        "fi": rec.get("format"),
        "fc": rec.get("tags"),
    })
write_dest("EntityJ", entity_j_records)

# Audit -> EntityN
# Audit: id, actor_id(->User/EntityK), action, entity_type, entity_id, severity, resource, ip_address, changes, outcome
# EntityN: id, fc(ref EntityD), fb(outcome enum), fa(severity enum), fe(action enum), ff(resource text), fd(entity_type/entity_id text)
# EntityN references EntityD - but actor_id refs User(EntityK). EntityD has ref to EntityK.
# We need to create EntityD records for actors, then reference them in EntityN
# EntityD: id, fa(ref EntityK), fd(text), fb(text), fc(richtext)
# We'll create EntityD records from Audit actor info
# EntityD: id=audit.id, fa=actor_id(EntityK ref), fd=entity_type, fb=entity_id, fc=changes(richtext)

entity_d_records = []
for rec in source_data.get("Audit", []):
    entity_d_records.append({
        "id": rec["id"],
        "fa": rec.get("actor_id"),
        "fd": rec.get("entity_type"),
        "fb": rec.get("ip_address"),
        "fc": rec.get("changes"),
    })
write_dest("EntityD", entity_d_records)

# EntityN: fc(ref EntityD = audit.id), fb(outcome), fa(severity), fe(action), ff(resource), fd(entity_id text)
entity_n_records = []
for rec in source_data.get("Audit", []):
    entity_n_records.append({
        "id": rec["id"],
        "fc": rec["id"],  # ref to EntityD which has same id
        "fb": rec.get("outcome"),
        "fa": rec.get("severity"),
        "fe": rec.get("action"),
        "ff": rec.get("resource"),
        "fd": rec.get("entity_id"),
    })
write_dest("EntityN", entity_n_records)

# Notification -> EntityL
# Notification: id, recipient_id(->User/EntityK), type, title, created_at, channel, is_read, body, link, priority, read_at, metrics
# EntityL: id, fb(ref EntityK recipient_id), fc(title text), fi(created_at date), fe(channel enum), fh(is_read bool), fd(body richtext), fg(link text), ff(priority enum), fj(read_at date), fa(metrics nested MetricBlock)
# type has no field in EntityL... dropped

entity_l_records = []
for rec in source_data.get("Notification", []):
    entity_l_records.append({
        "id": rec["id"],
        "fb": rec.get("recipient_id"),
        "fc": rec.get("title"),
        "fi": rec.get("created_at"),
        "fe": rec.get("channel"),
        "fh": rec.get("is_read"),
        "fd": rec.get("body"),
        "fg": rec.get("link"),
        "ff": rec.get("priority"),
        "fj": rec.get("read_at"),
        "fa": rec.get("metrics"),
    })
write_dest("EntityL", entity_l_records)

# Service -> EntityC
# Service: id, name, env_id(->Environment/EntityP), owner_id(->User/EntityK), tier, sla_minutes, repo_url, port, description, is_active, language, version
# EntityC: id, fi(name text), fh(ref EntityP env_id), fl(ref EntityK owner_id), fb(tier enum), fk(sla_minutes number), fa(repo_url text), fd(port number), fc(description richtext), ff(is_active bool), fg(language text), fe(version text), fj(text - extra)

entity_c_records = []
for rec in source_data.get("Service", []):
    entity_c_records.append({
        "id": rec["id"],
        "fi": rec.get("name"),
        "fh": rec.get("env_id"),
        "fl": rec.get("owner_id"),
        "fb": rec.get("tier"),
        "fk": rec.get("sla_minutes"),
        "fa": rec.get("repo_url"),
        "fd": rec.get("port"),
        "fc": rec.get("description"),
        "ff": rec.get("is_active"),
        "fg": rec.get("language"),
        "fe": rec.get("version"),
        "fj": None,
    })
write_dest("EntityC", entity_c_records)

# ApiKey -> EntityH
# ApiKey: id, name, service_id(->Service/EntityC), owner_id(->User/EntityK), status, scopes, description, last_used
# EntityH: id, fb(name text), fg(ref EntityC service_id), fd(ref EntityK owner_id), fa(status enum), fe(scopes multi_enum), ff(description text), fc(last_used date)

entity_h_records = []
for rec in source_data.get("ApiKey", []):
    entity_h_records.append({
        "id": rec["id"],
        "fb": rec.get("name"),
        "fg": rec.get("service_id"),
        "fd": rec.get("owner_id"),
        "fa": rec.get("status"),
        "fe": rec.get("scopes"),
        "ff": rec.get("description"),
        "fc": rec.get("last_used"),
    })
write_dest("EntityH", entity_h_records)

# Runbook -> EntityM
# Runbook: id, title, author_id(->User/EntityK), status, type, description, tags, is_approved, severity_level, next_review_due, attachments
# EntityM: id, fd(title text), fi(ref EntityK author_id), fg(status enum), fh(type enum), fb(description richtext), fe(tags multi_enum), fc(is_approved bool), ff(severity_level enum), fa(next_review_due date)
# attachments -> EntityF (separate entity)

entity_m_records = []
entity_f_records = []

for rec in source_data.get("Runbook", []):
    entity_m_records.append({
        "id": rec["id"],
        "fd": rec.get("title"),
        "fi": rec.get("author_id"),
        "fg": rec.get("status"),
        "fh": rec.get("type"),
        "fb": rec.get("description"),
        "fe": rec.get("tags"),
        "fc": rec.get("is_approved"),
        "ff": rec.get("severity_level"),
        "fa": rec.get("next_review_due"),
    })
    # Attachments -> EntityF
    # EntityF: id, fa(ref EntityM runbook_id), fe(filename text), fd(url text), fb(file_type enum), ff(size_kb number), fc(uploaded_at date)
    for idx, att in enumerate(rec.get("attachments", [])):
        att_id = int(str(rec["id"]) + str(idx + 1))
        entity_f_records.append({
            "id": att_id,
            "fa": rec["id"],
            "fe": att.get("filename"),
            "fd": att.get("url"),
            "fb": att.get("file_type"),
            "ff": att.get("size_kb"),
            "fc": att.get("uploaded_at"),
        })

write_dest("EntityM", entity_m_records)
write_dest("EntityF", entity_f_records)