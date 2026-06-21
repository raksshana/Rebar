# User -> EntityG
recs = []
for r in source_data["User"]:
    recs.append({
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
write_dest("EntityG", recs)

# Vendor -> EntityC
recs = []
for r in source_data["Vendor"]:
    recs.append({
        "id": r["id"],
        "fa": r.get("name"),
        "ff": r.get("email"),
        "fb": r.get("notes"),
        "fe": r.get("rating"),
        "fh": r.get("category"),
        "fd": r.get("notes"),
        "fi": r.get("payment_terms"),
        "fc": r.get("status"),
        "fg": [
            {
                "label": b.get("label"),
                "color": b.get("color"),
                "category": b.get("category"),
            } for b in r.get("tags", [])
        ],
    })
write_dest("EntityC", recs)

# Contract -> EntityK
recs = []
for r in source_data["Contract"]:
    recs.append({
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
write_dest("EntityK", recs)

# Page -> EntityL
recs = []
for r in source_data["Page"]:
    recs.append({
        "id": r["id"],
        "fi": r.get("title"),
        "fe": r.get("author_id"),
        "ff": r.get("status"),
        "fa": r.get("is_locked"),
        "fd": r.get("view_count"),
        "fc": r.get("template"),
        "fh": r.get("published_at"),
        "fg": r.get("word_count"),
        "fb": [
            {
                "message": b.get("message"),
                "level": b.get("level"),
                "timestamp": b.get("timestamp"),
                "service": b.get("service"),
            } for b in r.get("logs", [])
        ],
    })
write_dest("EntityL", recs)

# Audit -> EntityM
recs = []
for r in source_data["Audit"]:
    recs.append({
        "id": r["id"],
        "fc": r.get("actor_id"),
        "fj": r.get("action"),
        "fa": r.get("entity_type"),
        "fe": r.get("entity_id"),
        "fg": r.get("outcome"),
        "fb": r.get("changes"),
        "fi": r.get("created_at"),
        "ff": r.get("resource"),
        "fd": [],
        "fh": r.get("ip_address"),
    })
write_dest("EntityM", recs)

# Location -> EntityB
recs = []
for r in source_data["Location"]:
    recs.append({
        "id": r["id"],
        "fe": r.get("name"),
        "ff": r.get("type"),
        "fb": r.get("manager_name"),
        "fd": r.get("country"),
        "fc": r.get("is_active"),
        "fg": r.get("capacity"),
        "fi": r.get("address"),
        "fa": r.get("timezone"),
        "fh": r.get("city"),
    })
write_dest("EntityB", recs)

# Organization -> EntityH
recs = []
for r in source_data["Organization"]:
    recs.append({
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
write_dest("EntityH", recs)

# Customer -> EntityF
recs = []
for r in source_data["Customer"]:
    recs.append({
        "id": r["id"],
        "fh": r.get("name"),
        "ff": r.get("email"),
        "fc": r.get("company"),
        "fb": r.get("mrr"),
        "fe": r.get("source"),
        "fa": r.get("country"),
        "fi": r.get("is_verified"),
        "fg": r.get("tier"),
        "fd": [
            {
                "title": b.get("title"),
                "description": b.get("description"),
                "order": b.get("order"),
                "status": b.get("status"),
                "duration_m": b.get("duration_m"),
            } for b in r.get("steps", [])
        ],
    })
write_dest("EntityF", recs)

# Runbook -> EntityO
recs = []
for r in source_data["Runbook"]:
    recs.append({
        "id": r["id"],
        "fi": r.get("title"),
        "ff": r.get("author_id"),
        "fd": r.get("status"),
        "fe": r.get("type"),
        "fb": r.get("version"),
        "fc": r.get("next_review_due"),
        "fa": r.get("last_reviewed"),
        "fh": r.get("is_approved"),
        "fg": r.get("tags"),
    })
write_dest("EntityO", recs)

# Tag -> EntityE
recs = []
for r in source_data["Tag"]:
    recs.append({
        "id": r["id"],
        "fa": r.get("name"),
        "fe": r.get("slug"),
        "fc": r.get("usage_count"),
        "fb": r.get("description"),
        "fd": r.get("color"),
        "ff": r.get("description"),
    })
write_dest("EntityE", recs)