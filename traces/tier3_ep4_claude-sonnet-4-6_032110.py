# Migration script: source -> destination

# Mapping analysis:
# User -> EntityC (id, name->fb, created_at->fa) [used as ref target]
# User -> EntityD (id, fc=owner ref EntityC, fa=name, fd=skills, fe=email, fb=title, fg=timezone, ff=role, fh=is_active)
# Account -> EntityN (id, fc=name, fg=owner_id ref EntityC, fd=type, fe=status, fh=website, fi=created_at, fj=annual_revenue, fb=tier, fa=industry, ff=created_at... wait)
# Let me re-analyze carefully

# Source -> Dest entity mapping:
# User -> EntityC: id, fb=name, fa=created_at
# User -> EntityD: id, fc=owner_id(ref EntityC), fa=name, fd=skills(multi_enum), fe=email, fb=title, fg=timezone, ff=role, fh=is_active
# Account -> EntityN: id, fc=name, fg=owner_id(ref EntityC), fd=type, fe=status, fh=website, fi=created_at, fj=annual_revenue, fb=tier, fa=industry, ff=created_at(duplicate - check dest)
# Opportunity -> EntityA: id, fi=name, fc=account_id(ref EntityN), fa=owner_id(ref EntityC), fj=stage, fd=value, fg=close_date, ff=source, fh=type, fb=probability, fe=is_won
# Article -> EntityO: id, fb=title, fi=author_id(ref EntityC), fj=status, fe=content(richtext), fc=word_count, fd=read_time, ff=published_at, fg=tags, fh=category, fa=addresses(nested AddressBlock)
# Comment -> EntityL: id, fd=body(richtext), ff=article_id(ref EntityO), fa=author_id(ref EntityC), fc=is_flagged, fb=reply_count, fg=status, fe=is_approved
# Environment -> EntityF: id, fb=name, fa=type, fe=maintenance_window, ff=region, fg=description(richtext), fd=tier(mapped _v2), fh=has_comments(bool - need to derive), fc=bool
# Service -> EntityJ: id, fi=name, fc=env_id(ref EntityF), fg=owner_id(ref EntityC), ff=tier, fd=version, fe=description(richtext), fk=is_active, fh=language, fj=repo_url, fa=sla_minutes, fb=port(text)
# Location -> EntityH: id, fb=name, fe=type, fa=country, fd=address, ff=capacity, fg=manager_name, fi=city, fh=timezone, fc=is_active
# Deployment -> EntityM: id, ff=service_id(ref EntityJ), fe=deployed_by(ref EntityC), fg=version, fi=status, fd=artifact_url, fb=environment, fa=notes(richtext), fh=is_rollback, fc=contacts(nested ContactBlock)
# Customer -> EntityB: id, fj=name, fg=email, ff=status, fh=source, fa=company, fi=mrr, fe=tier(text), fb=is_verified, fd=country, fc=created_at, fk=attachments
# Customer -> EntityG: id, fh=name, fe=email, fc=status, fd=source, fa=company, fk=mrr, fi=tier(text), fb=is_verified, ff=country, fj=created_at, fg=attachments
# Customer -> EntityI: id, fa=name, fc=email, ff=status, fk=source, fe=company, fb=mrr, fd=tier(text), fj=is_verified, fh=country, fg=created_at, fi=attachments
# Customer -> EntityK: id, ff=name, fb=email, fg=status, fa=source, fc=company, fe=mrr, fj=tier(text), fd=is_verified, fk=country, fh=created_at, fi=attachments

# Tier mapping for Environment (EntityF.fd): critical->critical_v2, standard->standard_v2, low->low_v2
tier_v2_map = {
    "critical": "critical_v2",
    "standard": "standard_v2",
    "low": "low_v2"
}

# --- EntityC: from User (id, name->fb, created_at->fa) ---
entity_c_records = []
for u in source_data.get("User", []):
    entity_c_records.append({
        "id": u["id"],
        "fb": u.get("name"),
        "fa": u.get("created_at"),
    })
write_dest("EntityC", entity_c_records)

# --- EntityD: from User ---
entity_d_records = []
for u in source_data.get("User", []):
    entity_d_records.append({
        "id": u["id"],
        "fc": u.get("id"),          # ref to EntityC (same id as User)
        "fa": u.get("name"),
        "fd": u.get("skills", []),
        "fe": u.get("email"),
        "fb": u.get("title"),
        "fg": u.get("timezone"),
        "ff": u.get("role"),
        "fh": u.get("is_active"),
    })
write_dest("EntityD", entity_d_records)

# --- EntityN: from Account ---
# EntityN fields: id, fc=name, fg=owner_id(ref EntityC), fd=type, fe=status, fh=website, fi=created_at, fj=annual_revenue, fb=tier, fa=industry, ff=created_at
# ff and fi both map to created_at - use created_at for fi, and for ff also created_at (duplicate date fields)
entity_n_records = []
for a in source_data.get("Account", []):
    entity_n_records.append({
        "id": a["id"],
        "fc": a.get("name"),
        "fg": a.get("owner_id"),
        "fd": a.get("type"),
        "fe": a.get("status"),
        "fh": a.get("website"),
        "fi": a.get("created_at"),
        "fj": a.get("annual_revenue"),
        "fb": a.get("tier"),
        "fa": a.get("industry"),
        "ff": a.get("created_at"),  # second date field, mapping from same source
    })
write_dest("EntityN", entity_n_records)

# --- EntityA: from Opportunity ---
entity_a_records = []
for o in source_data.get("Opportunity", []):
    entity_a_records.append({
        "id": o["id"],
        "fi": o.get("name"),
        "fc": o.get("account_id"),   # ref to EntityN
        "fa": o.get("owner_id"),     # ref to EntityC
        "fj": o.get("stage"),
        "fd": o.get("value"),
        "fg": o.get("close_date"),
        "ff": o.get("source"),
        "fh": o.get("type"),
        "fb": o.get("probability"),
        "fe": o.get("is_won"),
    })
write_dest("EntityA", entity_a_records)

# --- EntityO: from Article ---
entity_o_records = []
for a in source_data.get("Article", []):
    entity_o_records.append({
        "id": a["id"],
        "fb": a.get("title"),
        "fi": a.get("author_id"),    # ref to EntityC
        "fj": a.get("status"),
        "fe": a.get("content"),
        "fc": a.get("word_count"),
        "fd": a.get("read_time"),
        "ff": a.get("published_at"),
        "fg": a.get("tags", []),
        "fh": a.get("category"),
        "fa": a.get("addresses", []),
    })
write_dest("EntityO", entity_o_records)

# --- EntityL: from Comment ---
entity_l_records = []
for c in source_data.get("Comment", []):
    entity_l_records.append({
        "id": c["id"],
        "fd": c.get("body"),
        "ff": c.get("article_id"),   # ref to EntityO
        "fa": c.get("author_id"),    # ref to EntityC
        "fc": c.get("is_flagged"),
        "fb": c.get("reply_count"),
        "fg": c.get("status"),
        "fe": c.get("is_approved"),
    })
write_dest("EntityL", entity_l_records)

# --- EntityF: from Environment ---
# fd: tier mapped to _v2 variant
# fh and fc are both bool - fh: has comments (len > 0), fc: derived from maintenance_window presence
entity_f_records = []
for e in source_data.get("Environment", []):
    entity_f_records.append({
        "id": e["id"],
        "fb": e.get("name"),
        "fa": e.get("type"),
        "fe": e.get("maintenance_window"),
        "ff": e.get("region"),
        "fg": e.get("description"),
        "fd": tier_v2_map.get(e.get("tier"), e.get("tier")),
        "fh": len(e.get("comments", [])) > 0,
        "fc": e.get("maintenance_window") is not None,
    })
write_dest("EntityF", entity_f_records)

# --- EntityJ: from Service ---
# fb=port as text, fa=sla_minutes(number), fj=repo_url(text), fh=language(text)
entity_j_records = []
for s in source_data.get("Service", []):
    entity_j_records.append({
        "id": s["id"],
        "fi": s.get("name"),
        "fc": s.get("env_id"),       # ref to EntityF
        "fg": s.get("owner_id"),     # ref to EntityC
        "ff": s.get("tier"),
        "fd": s.get("version"),
        "fe": s.get("description"),
        "fk": s.get("is_active"),
        "fh": s.get("language"),
        "fj": s.get("repo_url"),
        "fa": s.get("sla_minutes"),
        "fb": str(s["port"]) if s.get("port") is not None else None,
    })
write_dest("EntityJ", entity_j_records)

# --- EntityH: from Location ---
entity_h_records = []
for loc in source_data.get("Location", []):
    entity_h_records.append({
        "id": loc["id"],
        "fb": loc.get("name"),
        "fe": loc.get("type"),
        "fa": loc.get("country"),
        "fd": loc.get("address"),
        "ff": loc.get("capacity"),
        "fg": loc.get("manager_name"),
        "fi": loc.get("city"),
        "fh": loc.get("timezone"),
        "fc": loc.get("is_active"),
    })
write_dest("EntityH", entity_h_records)

# --- EntityM: from Deployment ---
entity_m_records = []
for d in source_data.get("Deployment", []):
    entity_m_records.append({
        "id": d["id"],
        "ff": d.get("service_id"),   # ref to EntityJ
        "fe": d.get("deployed_by"),  # ref to EntityC
        "fg": d.get("version"),
        "fi": d.get("status"),
        "fd": d.get("artifact_url"),
        "fb": d.get("environment"),
        "fa": d.get("notes"),
        "fh": d.get("is_rollback"),
        "fc": d.get("contacts", []),
    })
write_dest("EntityM", entity_m_records)

# --- EntityB: from Customer ---
# fe=tier as text (since dest has text field for tier in EntityB)
entity_b_records = []
for c in source_data.get("Customer", []):
    entity_b_records.append({
        "id": c["id"],
        "fj": c.get("name"),
        "fg": c.get("email"),
        "ff": c.get("status"),
        "fh": c.get("source"),
        "fa": c.get("company"),
        "fi": c.get("mrr"),
        "fe": c.get("tier"),         # text in dest EntityB
        "fb": c.get("is_verified"),
        "fd": c.get("country"),
        "fc": c.get("created_at"),
        "fk": c.get("attachments", []),
    })
write_dest("EntityB", entity_b_records)

# --- EntityG: from Customer ---
entity_g_records = []
for c in source_data.get("Customer", []):
    entity_g_records.append({
        "id": c["id"],
        "fh": c.get("name"),
        "fe": c.get("email"),
        "fc": c.get("status"),
        "fd": c.get("source"),
        "fa": c.get("company"),
        "fk": c.get("mrr"),
        "fi": c.get("tier"),         # text in dest EntityG
        "fb": c.get("is_verified"),
        "ff": c.get("country"),
        "fj": c.get("created_at"),
        "fg": c.get("attachments", []),
    })
write_dest("EntityG", entity_g_records)

# --- EntityI: from Customer ---
entity_i_records = []
for c in source_data.get("Customer", []):
    entity_i_records.append({
        "id": c["id"],
        "fa": c.get("name"),
        "fc": c.get("email"),
        "ff": c.get("status"),
        "fk": c.get("source"),
        "fe": c.get("company"),
        "fb": c.get("mrr"),
        "fd": c.get("tier"),         # text in dest EntityI
        "fj": c.get("is_verified"),
        "fh": c.get("country"),
        "fg": c.get("created_at"),
        "fi": c.get("attachments", []),
    })
write_dest("EntityI", entity_i_records)

# --- EntityK: from Customer ---
entity_k_records = []
for c in source_data.get("Customer", []):
    entity_k_records.append({
        "id": c["id"],
        "ff": c.get("name"),
        "fb": c.get("email"),
        "fg": c.get("status"),
        "fa": c.get("source"),
        "fc": c.get("company"),
        "fe": c.get("mrr"),
        "fj": c.get("tier"),         # text in dest EntityK
        "fd": c.get("is_verified"),
        "fk": c.get("country"),
        "fh": c.get("created_at"),
        "fi": c.get("attachments", []),
    })
write_dest("EntityK", entity_k_records)

# --- EntityE: from Environment comments (nested CommentBlock -> EntityE) ---
# EntityE: id, fe=ref EntityF, fd=richtext, fa=text, fb=date, ff=number, fc=bool
# Map Environment comments to EntityE records
# fe -> env id (ref EntityF), fd -> body (richtext), fa -> author (text), fb -> posted_at (date), ff -> upvotes (number), fc -> is_pinned (bool)
entity_e_records = []
comment_id_counter = 1
for e in source_data.get("Environment", []):
    for comment in e.get("comments", []):
        entity_e_records.append({
            "id": comment_id_counter,
            "fe": e["id"],               # ref to EntityF (the environment)
            "fd": comment.get("body"),
            "fa": comment.get("author"),
            "fb": comment.get("posted_at"),
            "ff": comment.get("upvotes"),
            "fc": comment.get("is_pinned"),
        })
        comment_id_counter += 1
write_dest("EntityE", entity_e_records)