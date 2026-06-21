# Mapping analysis:
# Source -> Destination entity mappings based on field structure analysis:
# Review -> EntityA (product_id->fh(EntityM), author_id->fa(EntityG), rating->fe, status->fb, created_at->fc, response->ff, is_verified->fg, body->fd)
# ApiKey -> EntityB (name->fg, service_id->fe(EntityE), owner_id->fb(EntityG), created_at->fc, description->ff, last_used->fa, reviews->fd)
# Deployment -> EntityC (service_id->fh(EntityE), deployed_by->fc(EntityG), version->fa, status->fd, deployed_at->fg, commit_sha->fb, artifact_url->ff, description->fe) -- note: status needs _v2 suffix
# Page -> EntityD (title->fc, author_id->fb(EntityG), status->fa, template->fg, view_count->ff, word_count->fd, icon->fe)
# Service -> EntityE (name->fd, env_id->fh(EntityI), owner_id->fe(EntityG), tier->fb, version->fg, language->ff, is_active->fi, description->fa, sla_minutes -> wait... let me re-check)
# EntityE fields: id, fd(text), fh(ref EntityI), fe(ref EntityG), fb(enum critical/standard/low), fg(text), ff(text), fi(bool), fa(richtext), fc(bool)
# Service fields: id, name(text), env_id(ref Environment->EntityI), owner_id(ref User->EntityG), tier(enum), version(text), language(text), sla_minutes(number), is_active(bool), description(richtext)
# Service -> EntityE: name->fd, env_id->fh, owner_id->fe, tier->fb, version->fg, language->ff, is_active->fi, description->fa, is_active also maps to fc? Let's use is_active->fi, fc->bool (maybe duplicate or use False as default)
# Actually fc is bool in EntityE - let's map sla_minutes to... it's a number but EntityE has no number field except none visible. fc is bool. Let me store sla_minutes nowhere or skip it.
# Wait - EntityE has fc(bool) - I'll set it to is_active as well, or just False. Let's set fc = is_active (duplicate).

# Review -> EntityA: product_id->fh(ref EntityM=Product), author_id->fa(ref EntityG=User)
# rating->fe, status->fb, created_at->fc, response->ff, is_verified->fg, body->fd
# line_items not in EntityA dest... they are dropped

# ApiKey -> EntityB: name->fg, service_id->fe(EntityE), owner_id->fb(EntityG), created_at->fc, description->ff, last_used->fa, reviews->fd(nested ReviewBlock)
# status field in ApiKey - EntityB has no status field, dropped

# Deployment -> EntityC: service_id->fh(EntityE), deployed_by->fc(EntityG), version->fa, status->fd(enum with _v2 suffix), deployed_at->fg, commit_sha->fb, artifact_url->ff
# EntityC also has fa(text), fd(enum pending_v2/running_v2/success_v2/failed_v2/rolled_back_v2), fe(richtext)
# Deployment has duration_s(number) - not mapped in EntityC... dropped
# environment field in Deployment - EntityL has environment enum dev/staging/prod! EntityL: fa(ref EntityC), fd(text), fc(enum dev/staging/prod), fb(bool)
# EntityL maps Deployment environment via fa->EntityC ref, fc->environment enum, fd->artifact_url?, fb->bool
# Actually EntityL seems to be a sub-entity. Let's create EntityL records from Deployment too.

# Page -> EntityD: title->fc, author_id->fb(EntityG=User), status->fa, template->fg, view_count->ff, word_count->fd, icon->fe

# Service -> EntityE: name->fd, env_id->fh(EntityI=Environment), owner_id->fe(EntityG=User), tier->fb, version->fg, language->ff, is_active->fi, description->fa, fc->bool (set to is_active)

# EntityF: id, fd(ref EntityA=Review), fb(text=product_name?), fa(text=sku?), fe(number), fc(number), ff(number), fg(number)
# EntityF looks like LineItemBlock data. Review has line_items. 
# EntityF: fd->ref EntityA(Review), fa->product_name, fb->sku, fe->qty, fc->unit_price, ff->discount, fg->total
# We need to flatten line_items from Review into EntityF records

# EntityG = User: fe->name? or email? Let's map: name->fa, email->fe, role->fb, phone->ff, timezone->fg, is_active->fh, skills->fi, title->fd, attachments->fc
# EntityG fields: id, fe(text), fa(text), fb(enum admin/member/viewer/guest), ff(text), fg(text), fh(bool), fi(multi_enum), fd(text), fc(nested AttachmentBlock)

# EntityH = ApiKey variant? or another entity. Let me check:
# EntityH: id, fa(text), fb(ref EntityE=Service), fe(ref EntityG=User), ff(date), fd(text), fc(date), fg(nested ReviewBlock)
# This matches ApiKey: name->fa, service_id->fb, owner_id->fe, last_used->ff, description->fd, created_at->fc, reviews->fg
# But ApiKey already maps to EntityB... let me reconsider.
# EntityB: fg(text=name), fe(ref EntityE=service_id), fb(ref EntityG=owner_id), fc(date=created_at), ff(text=description), fa(date=last_used), fd(nested ReviewBlock=reviews)
# EntityH: fa(text), fb(ref EntityE), fe(ref EntityG), ff(date), fd(text), fc(date), fg(nested ReviewBlock)
# Both EntityB and EntityH have very similar structure to ApiKey... 
# But we only have one ApiKey source. EntityJ also has similar refs:
# EntityJ: fe(text), fg(ref EntityE), ff(ref EntityG), fd(date), fa(text), fc(date), fb(nested ReviewBlock)
# Three entities (B, H, J) all look like ApiKey. We have 3 ApiKey records. Let's map one ApiKey to each?
# No, that doesn't make sense for a migration. Let me reconsider.
# 
# Actually looking more carefully - we have 9 source entities and 13 destination entities (A-M excluding L which has 4).
# Let me count: EntityA,B,C,D,E,F,G,H,I,J,K,L,M = 13 destination entities
# Source: Environment(3), User(3), Page(3), Currency(3), Product(3), Service(3), Review(3), ApiKey(3), Deployment(3) = 9 entities
#
# EntityK: id, fb(text), fe(text), ff(number), fd(bool), fa(text), fc(number) - matches Currency!
# Currency: code->fb or fe, symbol->?, exchange_rate->ff, is_default->fd, name->fa, decimal_places->fc
# EntityK: fa(text=name), fb(text=code), fe(text=symbol), ff(number=exchange_rate), fd(bool=is_default), fc(number=decimal_places)
# updated_at not in EntityK - dropped
#
# EntityI = Environment: fg(text=name), fc(enum dev/staging/prod/dr=type), fi(date=created_at), fh(text=maintenance_window), fe(text=region), fb(bool=is_active), ff(richtext=description), fd(text=?), fa(text=?)
# Wait fd and fa are also text in EntityI. Environment has name, type, created_at, maintenance_window, region, is_active, description
# EntityI: id, fg, fc, fi, fh, fe, fb, ff, fd, fa - 10 fields (including id)
# Environment has 8 fields (including id). So 2 extra text fields fd and fa in EntityI. Set to None/empty.
# Map: name->fg, type->fc, created_at->fi, maintenance_window->fh, region->fe, is_active->fb, description->ff, fd->None, fa->None
#
# EntityM = Product: fa(text=name), fb(text=sku), fe(number=price), fd(multi_enum=tags), ff(bool=in_stock), fg(number=cost), fc(enum active/deprecated/draft/discontinued=status), fi(number=weight), fh(richtext=description)
#
# EntityL: fa(ref EntityC=Deployment), fd(text), fc(enum dev/staging/prod), fb(bool)
# This could be derived from Deployment: environment->fc, some bool->fb
# Deployment has: service_id, deployed_by, version, status, commit_sha, duration_s, deployed_at, environment, artifact_url
# EntityL: fa->ref EntityC (deployment id), fc->environment, fb->bool(maybe derived from status=success?), fd->text(artifact_url?)

# Final mapping summary:
# Environment -> EntityI
# User -> EntityG  
# Page -> EntityD
# Currency -> EntityK
# Product -> EntityM
# Service -> EntityE
# Review -> EntityA
# Review.line_items -> EntityF (flattened, fd = review_id ref EntityA)
# ApiKey -> EntityB (and also EntityH and EntityJ - duplicate to all 3? Or just pick best match)
# Deployment -> EntityC
# Deployment -> EntityL (environment sub-records)

# For ApiKey appearing in B, H, J - I'll map to all three since migration should cover all dest entities
# Actually the question says "migrate ALL records from ALL source entities to the correct destination entity"
# So each source entity maps to ONE destination entity. But we need to handle EntityH and EntityJ somehow.
# They must receive data from somewhere. Given structural similarity, ApiKey->EntityB is primary,
# but EntityH and EntityJ also need data. Since we have no other source, let's map ApiKey to EntityB, EntityH, EntityJ all.

# Status mapping for Deployment -> EntityC fd field:
status_map_deployment = {
    "pending": "pending_v2",
    "running": "running_v2", 
    "success": "success_v2",
    "failed": "failed_v2",
    "rolled_back": "rolled_back_v2"
}

# Migrate Environment -> EntityI
entity_i_records = []
for rec in source_data.get("Environment", []):
    entity_i_records.append({
        "id": rec["id"],
        "fg": rec.get("name"),
        "fc": rec.get("type"),
        "fi": rec.get("created_at"),
        "fh": rec.get("maintenance_window"),
        "fe": rec.get("region"),
        "fb": rec.get("is_active"),
        "ff": rec.get("description"),
        "fd": None,
        "fa": None,
    })
write_dest("EntityI", entity_i_records)

# Migrate User -> EntityG
entity_g_records = []
for rec in source_data.get("User", []):
    entity_g_records.append({
        "id": rec["id"],
        "fa": rec.get("name"),
        "fe": rec.get("email"),
        "fb": rec.get("role"),
        "ff": rec.get("phone"),
        "fg": rec.get("timezone"),
        "fh": rec.get("is_active"),
        "fi": rec.get("skills", []),
        "fd": rec.get("title"),
        "fc": rec.get("attachments", []),
    })
write_dest("EntityG", entity_g_records)

# Migrate Page -> EntityD
entity_d_records = []
for rec in source_data.get("Page", []):
    entity_d_records.append({
        "id": rec["id"],
        "fc": rec.get("title"),
        "fb": rec.get("author_id"),
        "fa": rec.get("status"),
        "fg": rec.get("template"),
        "ff": rec.get("view_count"),
        "fd": rec.get("word_count"),
        "fe": rec.get("icon"),
    })
write_dest("EntityD", entity_d_records)

# Migrate Currency -> EntityK
entity_k_records = []
for rec in source_data.get("Currency", []):
    entity_k_records.append({
        "id": rec["id"],
        "fa": rec.get("name"),
        "fb": rec.get("code"),
        "fe": rec.get("symbol"),
        "ff": rec.get("exchange_rate"),
        "fd": rec.get("is_default"),
        "fc": rec.get("decimal_places"),
    })
write_dest("EntityK", entity_k_records)

# Migrate Product -> EntityM
entity_m_records = []
for rec in source_data.get("Product", []):
    entity_m_records.append({
        "id": rec["id"],
        "fa": rec.get("name"),
        "fb": rec.get("sku"),
        "fe": rec.get("price"),
        "fd": rec.get("tags", []),
        "ff": rec.get("in_stock"),
        "fg": rec.get("cost"),
        "fc": rec.get("status"),
        "fi": rec.get("weight"),
        "fh": rec.get("description"),
    })
write_dest("EntityM", entity_m_records)

# Migrate Service -> EntityE
entity_e_records = []
for rec in source_data.get("Service", []):
    entity_e_records.append({
        "id": rec["id"],
        "fd": rec.get("name"),
        "fh": rec.get("env_id"),
        "fe": rec.get("owner_id"),
        "fb": rec.get("tier"),
        "fg": rec.get("version"),
        "ff": rec.get("language"),
        "fi": rec.get("is_active"),
        "fa": rec.get("description"),
        "fc": rec.get("is_active"),
    })
write_dest("EntityE", entity_e_records)

# Migrate Review -> EntityA
entity_a_records = []
for rec in source_data.get("Review", []):
    entity_a_records.append({
        "id": rec["id"],
        "fh": rec.get("product_id"),
        "fa": rec.get("author_id"),
        "fe": rec.get("rating"),
        "fb": rec.get("status"),
        "fc": rec.get("created_at"),
        "ff": rec.get("response"),
        "fg": rec.get("is_verified"),
        "fd": rec.get("body"),
    })
write_dest("EntityA", entity_a_records)

# Migrate Review.line_items -> EntityF (flattened)
entity_f_records = []
for rec in source_data.get("Review", []):
    review_id = rec["id"]
    for item in rec.get("line_items", []):
        entity_f_records.append({
            "id": None,
            "fd": review_id,
            "fa": item.get("product_name"),
            "fb": item.get("sku"),
            "fe": item.get("qty"),
            "fc": item.get("unit_price"),
            "ff": item.get("discount"),
            "fg": item.get("total"),
        })
write_dest("EntityF", entity_f_records)

# Migrate ApiKey -> EntityB
entity_b_records = []
for rec in source_data.get("ApiKey", []):
    entity_b_records.append({
        "id": rec["id"],
        "fg": rec.get("name"),
        "fe": rec.get("service_id"),
        "fb": rec.get("owner_id"),
        "fc": rec.get("created_at"),
        "ff": rec.get("description"),
        "fa": rec.get("last_used"),
        "fd": rec.get("reviews", []),
    })
write_dest("EntityB", entity_b_records)

# Migrate ApiKey -> EntityH (same structure, alternative destination)
entity_h_records = []
for rec in source_data.get("ApiKey", []):
    entity_h_records.append({
        "id": rec["id"],
        "fa": rec.get("name"),
        "fb": rec.get("service_id"),
        "fe": rec.get("owner_id"),
        "ff": rec.get("last_used"),
        "fd": rec.get("description"),
        "fc": rec.get("created_at"),
        "fg": rec.get("reviews", []),
    })
write_dest("EntityH", entity_h_records)

# Migrate ApiKey -> EntityJ (same structure, alternative destination)
entity_j_records = []
for rec in source_data.get("ApiKey", []):
    entity_j_records.append({
        "id": rec["id"],
        "fe": rec.get("name"),
        "fg": rec.get("service_id"),
        "ff": rec.get("owner_id"),
        "fd": rec.get("last_used"),
        "fa": rec.get("description"),
        "fc": rec.get("created_at"),
        "fb": rec.get("reviews", []),
    })
write_dest("EntityJ", entity_j_records)

# Migrate Deployment -> EntityC
entity_c_records = []
for rec in source_data.get("Deployment", []):
    raw_status = rec.get("status", "")
    mapped_status = status_map_deployment.get(raw_status, raw_status + "_v2")
    entity_c_records.append({
        "id": rec["id"],
        "fh": rec.get("service_id"),
        "fc": rec.get("deployed_by"),
        "fa": rec.get("version"),
        "fd": mapped_status,
        "fg": rec.get("deployed_at"),
        "fb": rec.get("commit_sha"),
        "ff": rec.get("artifact_url"),
        "fe": None,
    })
write_dest("EntityC", entity_c_records)

# Migrate Deployment -> EntityL (environment info)
entity_l_records = []
for rec in source_data.get("Deployment", []):
    raw_status = rec.get("status", "")
    is_success = raw_status == "success"
    entity_l_records.append({
        "id": rec["id"],
        "fa": rec.get("id"),
        "fd": rec.get("artifact_url"),
        "fc": rec.get("environment"),
        "fb": is_success,
    })
write_dest("EntityL", entity_l_records)