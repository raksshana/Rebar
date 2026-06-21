# User -> EntityK
users = []
for r in source_data["User"]:
    users.append({
        "id": r["id"],
        "fd": r["name"],
        "fb": r["email"],
        "fc": r["role"],
        "ff": r["timezone"],
        "fa": r["is_active"],
        "fg": r["skills"],
        "fe": r["department"],
    })
write_dest("EntityK", users)

# Environment -> EntityP
envs = []
for r in source_data["Environment"]:
    envs.append({
        "id": r["id"],
        "fc": r["name"],
        "fi": r["type"],
        "fh": r["is_active"],
        "ff": r["tier"],
        "fa": r["region"],
        "fb": r["created_at"],
        "fg": r["cloud_provider"],
        "fe": None,
        "fd": None,
    })
write_dest("EntityP", envs)

# Vendor -> EntityE
vendors = []
for r in source_data["Vendor"]:
    vendors.append({
        "id": r["id"],
        "fd": r["name"],
        "fa": r["email"],
        "fe": r["status"],
        "fc": r["country"],
        "ff": r["payment_terms"],
        "fi": r["notes"],
        "fh": r["website"],
        "fj": r["contract_type"],
        "fg": r["category"],
        "fb": [
            {
                "name": c.get("name"),
                "email": c.get("email"),
                "phone": c.get("phone"),
                "role": c.get("role"),
                "is_primary": c.get("is_primary"),
            }
            for c in r.get("contacts", [])
        ],
    })
write_dest("EntityE", vendors)

# Contract -> EntityQ
contracts = []
for r in source_data["Contract"]:
    contracts.append({
        "id": r["id"],
        "fj": r["vendor_id"],
        "fb": r["owner_id"],
        "fd": r["status"],
        "fg": r["value"],
        "fi": r["type"],
        "fa": r["signed_at"],
        "fk": r["auto_renew"],
        "ff": r["end_date"],
        "fc": r["start_date"],
        "fh": r["payment_terms"],
        "fe": r["notes"],
    })
write_dest("EntityQ", contracts)

# Note -> EntityJ
notes = []
for r in source_data["Note"]:
    notes.append({
        "id": r["id"],
        "fg": r["author_id"],
        "fb": r["status"],
        "fa": r["view_count"],
        "ff": r["content"],
        "fh": r["word_count"],
        "fd": r["is_pinned"],
        "fe": r["created_at"],
        "fi": r["format"],
        "fc": r["tags"],
    })
write_dest("EntityJ", notes)

# Audit -> EntityN
audits = []
for r in source_data["Audit"]:
    audits.append({
        "id": r["id"],
        "fc": r["actor_id"],
        "fb": r["outcome"],
        "fa": r["severity"],
        "fe": r["action"],
        "ff": r["entity_type"],
        "fd": r["entity_id"],
    })
write_dest("EntityN", audits)

# Notification -> EntityA
notifications = []
for r in source_data["Notification"]:
    notifications.append({
        "id": r["id"],
        "fi": r["recipient_id"],
        "fd": r["title"],
        "fb": r["created_at"],
        "fh": r["channel"],
        "fc": r["is_read"],
        "fe": r["body"],
        "fg": r["link"],
        "fa": r["priority"],
        "ff": r["read_at"],
        "fj": [
            {
                "name": m.get("name"),
                "value": m.get("value"),
                "unit": m.get("unit"),
                "target": m.get("target"),
                "period": m.get("period"),
            }
            for m in r.get("metrics", [])
        ],
    })
write_dest("EntityA", notifications)

# Service -> EntityC
services = []
for r in source_data["Service"]:
    services.append({
        "id": r["id"],
        "fi": r["name"],
        "fh": r["env_id"],
        "fl": r["owner_id"],
        "fb": r["tier"],
        "fk": r["sla_minutes"],
        "fa": r["repo_url"],
        "fd": r["port"],
        "fc": r["description"],
        "ff": r["is_active"],
        "fg": r["language"],
        "fe": r["version"],
        "fj": None,
    })
write_dest("EntityC", services)

# ApiKey -> EntityH
apikeys = []
for r in source_data["ApiKey"]:
    apikeys.append({
        "id": r["id"],
        "fb": r["name"],
        "fg": r["service_id"],
        "fd": r["owner_id"],
        "fa": r["status"],
        "fe": r["scopes"],
        "ff": r["description"],
        "fc": r["last_used"],
    })
write_dest("EntityH", apikeys)

# Runbook -> EntityM, attachments -> EntityF
runbooks = []
attachments = []
attach_id = 1
for r in source_data["Runbook"]:
    runbooks.append({
        "id": r["id"],
        "fd": r["title"],
        "fi": r["author_id"],
        "fg": r["status"],
        "fh": r["type"],
        "fb": r["description"],
        "fe": r["tags"],
        "fc": r["is_approved"],
        "ff": r["severity_level"],
        "fa": r["next_review_due"],
    })
    for a in r.get("attachments", []):
        attachments.append({
            "id": attach_id,
            "fa": r["id"],
            "fe": a.get("filename"),
            "fd": a.get("url"),
            "fb": a.get("file_type"),
            "ff": a.get("size_kb"),
            "fc": a.get("uploaded_at"),
        })
        attach_id += 1
write_dest("EntityM", runbooks)
write_dest("EntityF", attachments)