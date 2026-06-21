# Environment -> EntityI
recs = []
for r in source_data.get("Environment", []):
    recs.append({
        "id": r.get("id"),
        "fg": r.get("name"),
        "fc": r.get("type"),
        "fi": r.get("created_at"),
        "fh": r.get("maintenance_window"),
        "fe": r.get("region"),
        "fb": r.get("is_active"),
        "ff": r.get("description"),
        "fd": None,
        "fa": None,
    })
write_dest("EntityI", recs)

# User -> EntityG
recs = []
for r in source_data.get("User", []):
    atts = []
    for a in r.get("attachments", []) or []:
        atts.append({
            "filename": a.get("filename"),
            "url": a.get("url"),
            "file_type": a.get("file_type"),
            "size_kb": a.get("size_kb"),
            "uploaded_at": a.get("uploaded_at"),
        })
    recs.append({
        "id": r.get("id"),
        "fe": r.get("name"),
        "fa": r.get("email"),
        "fb": r.get("role"),
        "ff": r.get("phone"),
        "fg": r.get("timezone"),
        "fh": r.get("is_active"),
        "fi": r.get("skills"),
        "fd": r.get("title"),
        "fc": atts,
    })
write_dest("EntityG", recs)

# Page -> EntityD
recs = []
for r in source_data.get("Page", []):
    recs.append({
        "id": r.get("id"),
        "fc": r.get("title"),
        "fb": r.get("author_id"),
        "fa": r.get("status"),
        "fg": r.get("template"),
        "ff": r.get("view_count"),
        "fd": r.get("word_count"),
        "fe": r.get("icon"),
    })
write_dest("EntityD", recs)

# Currency -> EntityK
recs = []
for r in source_data.get("Currency", []):
    recs.append({
        "id": r.get("id"),
        "fb": r.get("code"),
        "fe": r.get("symbol"),
        "ff": r.get("exchange_rate"),
        "fd": r.get("is_default"),
        "fa": r.get("name"),
        "fc": r.get("decimal_places"),
    })
write_dest("EntityK", recs)

# Product -> EntityM
recs = []
for r in source_data.get("Product", []):
    recs.append({
        "id": r.get("id"),
        "fa": r.get("name"),
        "fb": r.get("sku"),
        "fe": r.get("price"),
        "fd": r.get("tags"),
        "ff": r.get("in_stock"),
        "fg": r.get("cost"),
        "fc": r.get("status"),
        "fi": r.get("weight"),
        "fh": r.get("description"),
    })
write_dest("EntityM", recs)

# Service -> EntityE
recs = []
for r in source_data.get("Service", []):
    recs.append({
        "id": r.get("id"),
        "fd": r.get("name"),
        "fh": r.get("env_id"),
        "fe": r.get("owner_id"),
        "fb": r.get("tier"),
        "fg": r.get("version"),
        "ff": r.get("language"),
        "fi": r.get("is_active"),
        "fa": r.get("description"),
        "fc": None,
    })
write_dest("EntityE", recs)

# Review -> EntityA
recs = []
for r in source_data.get("Review", []):
    recs.append({
        "id": r.get("id"),
        "fh": r.get("product_id"),
        "fa": r.get("author_id"),
        "fe": r.get("rating"),
        "fb": r.get("status"),
        "fc": r.get("created_at"),
        "ff": r.get("response"),
        "fg": r.get("is_verified"),
        "fd": r.get("body"),
    })
write_dest("EntityA", recs)

# ApiKey -> EntityH
recs = []
for r in source_data.get("ApiKey", []):
    reviews = []
    for rb in r.get("reviews", []) or []:
        reviews.append({
            "rating": rb.get("rating"),
            "title": rb.get("title"),
            "body": rb.get("body"),
            "reviewer": rb.get("reviewer"),
            "verified": rb.get("verified"),
            "created_at": rb.get("created_at"),
        })
    recs.append({
        "id": r.get("id"),
        "fa": r.get("name"),
        "fb": r.get("service_id"),
        "fe": r.get("owner_id"),
        "ff": r.get("last_used"),
        "fd": r.get("description"),
        "fc": r.get("created_at"),
        "fg": reviews,
    })
write_dest("EntityH", recs)

# Deployment -> EntityC
status_map = {
    "pending": "pending_v2",
    "running": "running_v2",
    "success": "success_v2",
    "failed": "failed_v2",
    "rolled_back": "rolled_back_v2",
}
recs = []
for r in source_data.get("Deployment", []):
    recs.append({
        "id": r.get("id"),
        "fh": r.get("service_id"),
        "fc": r.get("deployed_by"),
        "fa": r.get("version"),
        "fd": status_map.get(r.get("status")),
        "fg": r.get("deployed_at"),
        "fb": r.get("commit_sha"),
        "ff": r.get("artifact_url"),
        "fe": None,
    })
write_dest("EntityC", recs)