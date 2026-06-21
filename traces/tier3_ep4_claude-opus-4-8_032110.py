# EntityC: id, fb(text), fa(date) -> User minimal (ref target). Migrate Users to EntityC too? 
# EntityC is target of many refs (owner_id etc). EntityD is the full User.
# Map User -> EntityD (full) and also User -> EntityC (ref-target minimal).

# Environment -> EntityF
env_out = []
for r in source_data["Environment"]:
    tier_map = {"critical": "critical_v2", "standard": "standard_v2", "low": "low_v2"}
    env_out.append({
        "id": r["id"],
        "fb": r.get("name"),
        "fa": r.get("type"),
        "fe": r.get("maintenance_window"),
        "ff": r.get("region"),
        "fg": r.get("description"),
        "fd": tier_map.get(r.get("tier")),
        "fh": None,
        "fc": None,
    })
write_dest("EntityF", env_out)

# User -> EntityD (full)
user_d = []
for r in source_data["User"]:
    user_d.append({
        "id": r["id"],
        "fa": r.get("name"),
        "fc": r.get("email"),
        "fd": r.get("skills"),
        "fe": r.get("phone"),
        "fb": r.get("timezone"),
        "fg": r.get("title"),
        "ff": r.get("role"),
        "fh": r.get("is_active"),
    })
write_dest("EntityD", user_d)

# User -> EntityC (ref-target minimal: fb text=name, fa date=created_at)
user_c = []
for r in source_data["User"]:
    user_c.append({
        "id": r["id"],
        "fb": r.get("name"),
        "fa": r.get("created_at"),
    })
write_dest("EntityC", user_c)

# Account -> EntityN
acct_out = []
for r in source_data["Account"]:
    acct_out.append({
        "id": r["id"],
        "fc": r.get("name"),
        "fg": r.get("owner_id"),
        "fd": r.get("type"),
        "fe": r.get("status"),
        "fh": r.get("website"),
        "fi": r.get("created_at"),
        "fj": r.get("annual_revenue"),
        "fb": r.get("tier"),
        "fa": r.get("industry"),
        "ff": None,
    })
write_dest("EntityN", acct_out)

# Opportunity -> EntityA
opp_out = []
for r in source_data["Opportunity"]:
    opp_out.append({
        "id": r["id"],
        "fi": r.get("name"),
        "fc": r.get("account_id"),
        "fa": r.get("owner_id"),
        "fj": r.get("stage"),
        "fd": r.get("value"),
        "fg": r.get("close_date"),
        "ff": r.get("source"),
        "fh": r.get("type"),
        "fb": r.get("probability"),
        "fe": r.get("is_won"),
    })
write_dest("EntityA", opp_out)

# Article -> EntityO
art_out = []
for r in source_data["Article"]:
    art_out.append({
        "id": r["id"],
        "fb": r.get("title"),
        "fi": r.get("author_id"),
        "fj": r.get("status"),
        "fe": r.get("content"),
        "fc": r.get("word_count"),
        "fd": r.get("read_time"),
        "ff": r.get("published_at"),
        "fg": r.get("tags"),
        "fa": r.get("addresses"),
        "fh": r.get("category"),
    })
write_dest("EntityO", art_out)

# Comment -> EntityL
com_out = []
for r in source_data["Comment"]:
    com_out.append({
        "id": r["id"],
        "fd": r.get("body"),
        "ff": r.get("article_id"),
        "fa": r.get("author_id"),
        "fc": r.get("is_flagged"),
        "fb": r.get("reply_count"),
        "fg": r.get("status"),
        "fe": r.get("is_approved"),
    })
write_dest("EntityL", com_out)

# Service -> EntityJ
svc_out = []
for r in source_data["Service"]:
    svc_out.append({
        "id": r["id"],
        "fi": r.get("name"),
        "fc": r.get("env_id"),
        "fg": r.get("owner_id"),
        "ff": r.get("tier"),
        "fd": r.get("version"),
        "fe": r.get("description"),
        "fk": r.get("is_active"),
        "fh": r.get("language"),
        "fj": r.get("repo_url"),
        "fa": r.get("sla_minutes"),
        "fb": str(r.get("port")) if r.get("port") is not None else None,
    })
write_dest("EntityJ", svc_out)

# Location -> EntityH
loc_out = []
for r in source_data["Location"]:
    loc_out.append({
        "id": r["id"],
        "fb": r.get("name"),
        "fe": r.get("type"),
        "fa": r.get("country"),
        "fd": r.get("address"),
        "ff": r.get("capacity"),
        "fg": r.get("manager_name"),
        "fi": r.get("city"),
        "fh": r.get("timezone"),
        "fc": r.get("is_active"),
    })
write_dest("EntityH", loc_out)

# Deployment -> EntityM
dep_out = []
for r in source_data["Deployment"]:
    dep_out.append({
        "id": r["id"],
        "ff": r.get("service_id"),
        "fe": r.get("deployed_by"),
        "fg": r.get("version"),
        "fi": r.get("status"),
        "fd": r.get("artifact_url"),
        "fb": r.get("environment"),
        "fa": r.get("notes"),
        "fh": r.get("is_rollback"),
        "fc": r.get("contacts"),
    })
write_dest("EntityM", dep_out)

# Customer -> EntityB (has AttachmentBlock, status/source enums)
cust_out = []
for r in source_data["Customer"]:
    cust_out.append({
        "id": r["id"],
        "fj": r.get("name"),
        "fg": r.get("email"),
        "ff": r.get("status"),
        "fh": r.get("source"),
        "fa": r.get("company"),
        "fi": r.get("mrr"),
        "fe": r.get("tier"),
        "fb": r.get("is_verified"),
        "fd": r.get("phone"),
        "fc": r.get("created_at"),
        "fk": r.get("attachments"),
    })
write_dest("EntityB", cust_out)