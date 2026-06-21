# Environment -> EntityC
recs = []
for r in source_data.get("Environment", []):
    recs.append({
        "id": r.get("id"),
        "fg": r.get("name"),
        "fd": r.get("type"),
        "fe": r.get("cloud_provider"),
        "fa": r.get("created_at"),
        "fb": r.get("is_active"),
        "fc": r.get("description"),
        "ff": None,
    })
write_dest("EntityC", recs)

# Currency -> EntityH (fa->EntityG ref skipped, use text/number fields)
g_recs = []
h_recs = []
for r in source_data.get("Currency", []):
    g_id = r.get("id")
    g_recs.append({"id": g_id, "fa": r.get("updated_at")})
    h_recs.append({
        "id": r.get("id"),
        "fa": g_id,
        "fd": r.get("code"),
        "fb": r.get("name"),
        "ff": r.get("exchange_rate"),
        "fe": r.get("symbol"),
        "fc": None,
    })
write_dest("EntityG", g_recs)
write_dest("EntityH", h_recs)

# User -> EntityD
recs = []
for r in source_data.get("User", []):
    line_items = []
    for li in r.get("line_items", []) or []:
        line_items.append({
            "product_name": li.get("product_name"),
            "sku": li.get("sku"),
            "qty": li.get("qty"),
            "unit_price": li.get("unit_price"),
            "discount": li.get("discount"),
            "total": li.get("total"),
        })
    recs.append({
        "id": r.get("id"),
        "fa": r.get("name"),
        "fk": r.get("email"),
        "fh": r.get("role"),
        "ff": r.get("created_at"),
        "fb": r.get("phone"),
        "fj": r.get("title"),
        "fe": r.get("skills"),
        "fc": r.get("bio"),
        "fd": r.get("department"),
        "fi": r.get("timezone"),
        "fg": line_items,
    })
write_dest("EntityD", recs)

# Project -> EntityM
recs = []
for r in source_data.get("Project", []):
    custom_fields = []
    for cf in r.get("custom_fields", []) or []:
        custom_fields.append({
            "key": cf.get("key"),
            "value": cf.get("value"),
            "field_type": cf.get("field_type"),
        })
    recs.append({
        "id": r.get("id"),
        "fe": r.get("name"),
        "ff": r.get("owner_id"),
        "fb": r.get("status"),
        "fg": r.get("priority"),
        "fi": r.get("end_date"),
        "fh": r.get("description"),
        "fa": r.get("start_date"),
        "fc": r.get("budget"),
        "fd": custom_fields,
    })
write_dest("EntityM", recs)

# Service -> EntityA
recs = []
for r in source_data.get("Service", []):
    addresses = []
    for a in r.get("addresses", []) or []:
        addresses.append({
            "street": a.get("street"),
            "city": a.get("city"),
            "state": a.get("state"),
            "country": a.get("country"),
            "zip": a.get("zip"),
            "type": a.get("type"),
        })
    recs.append({
        "id": r.get("id"),
        "fb": r.get("name"),
        "fe": r.get("env_id"),
        "fg": r.get("owner_id"),
        "fc": r.get("tier"),
        "ff": r.get("sla_minutes"),
        "fj": r.get("language"),
        "fa": r.get("port"),
        "fh": r.get("version"),
        "fi": r.get("repo_url"),
        "fl": r.get("description"),
        "fd": addresses,
        "fk": None,
    })
write_dest("EntityA", recs)

# Task -> EntityE
recs = []
for r in source_data.get("Task", []):
    recs.append({
        "id": r.get("id"),
        "fc": r.get("title"),
        "fi": r.get("project_id"),
        "fe": r.get("assignee_id"),
        "fd": r.get("status"),
        "fb": r.get("due_date"),
        "ff": r.get("is_blocked"),
        "fa": r.get("type"),
        "fj": r.get("tags"),
        "fg": r.get("created_at"),
        "fk": r.get("priority"),
        "fh": r.get("points"),
    })
write_dest("EntityE", recs)

# Workflow -> EntityI
recs = []
for r in source_data.get("Workflow", []):
    recs.append({
        "id": r.get("id"),
        "fc": r.get("name"),
        "fe": r.get("project_id"),
        "fa": r.get("status"),
        "fh": r.get("last_run"),
        "fd": r.get("is_active"),
        "fg": r.get("step_count"),
        "ff": r.get("schedule"),
        "fi": r.get("description"),
        "fj": r.get("run_count"),
        "fb": r.get("creator_id"),
    })
write_dest("EntityI", recs)

# Feature -> EntityK
recs = []
for r in source_data.get("Feature", []):
    recs.append({
        "id": r.get("id"),
        "ff": r.get("name"),
        "fg": r.get("project_id"),
        "fd": r.get("owner_id"),
        "fh": r.get("status"),
        "fc": r.get("type"),
        "fa": r.get("description"),
        "fb": r.get("priority"),
        "fi": r.get("impact_estimate"),
        "fe": r.get("is_breaking"),
        "fj": r.get("tags"),
    })
write_dest("EntityK", recs)