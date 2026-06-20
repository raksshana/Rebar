"""
Difficulty dial for MigrateGym.

apply_difficulty(source_schema, tier) -> (dest_schema, transformations)

Tier 2: structural transforms (split / merge / flatten_nested / unmapped)
Tier 3: T1 noise + full structural stack + name obfuscation helpers
"""

import copy
import random

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RENAME_SUFFIXES = ["_new", "_updated", "_v2"]

_MERGE_SUFFIXES = ["Record", "Node", "Object", "Unit", "Bundle", "Entry", "Item"]

_EXTRACT_SUFFIXES = ["Entry", "Item", "Row", "Record"]

_COERCIONS = {
    "text":     ["richtext"],
    "richtext": ["text"],
    "number":   ["text", "bool"],
    "date":     ["text"],
    "bool":     ["number"],
}

# Synonym pools for partition sub-entity naming.
# Keys are pre-T1 enum values; values are shuffled per call.
_ENUM_SYNONYMS = {
    # lifecycle / status
    "draft":        ["Pending", "Provisional", "Tentative", "Working"],
    "active":       ["Running", "Live", "Current", "Enabled"],
    "inactive":     ["Idle", "Dormant", "Offline", "Suspended"],
    "pending":      ["Queued", "Awaiting", "Staged", "Held"],
    "open":         ["Raised", "Unresolved", "Outstanding", "Flagged"],
    "closed":       ["Concluded", "Settled", "Finalized", "Resolved"],
    "in_progress":  ["Running", "Executing", "Underway", "Processing"],
    "resolved":     ["Addressed", "Fixed", "Cleared", "Handled"],
    "cancelled":    ["Voided", "Withdrawn", "Aborted", "Dropped"],
    "completed":    ["Delivered", "Finished", "Fulfilled", "Done"],
    "done":         ["Finished", "Complete", "Closed", "Delivered"],
    "todo":         ["Queued", "Upcoming", "Staged", "Deferred"],
    "success":      ["Passed", "Delivered", "Accepted", "Healthy"],
    "failed":       ["Errored", "Broken", "Rejected", "Faulted"],
    "archived":     ["Stored", "Frozen", "Retired", "Historical"],
    "published":    ["Live", "Released", "Visible", "Available"],
    "on_hold":      ["Paused", "Blocked", "Deferred", "Suspended"],
    "review":       ["Evaluating", "Assessing", "Vetting", "Checking"],
    "in_review":    ["Evaluating", "Assessing", "Vetting", "Reviewing"],
    "approved":     ["Cleared", "Accepted", "Validated", "Authorized"],
    "deprecated":   ["Retired", "Legacy", "Sunset", "Obsolete"],
    "under_review": ["Evaluating", "Assessing", "Vetting", "Checking"],
    "planning":     ["Drafting", "Scoping", "Preparing", "Designing"],
    "on_hold":      ["Paused", "Blocked", "Deferred", "Suspended"],
    # priority
    "low":          ["Routine", "Deferred", "Normal", "Standard"],
    "medium":       ["Moderate", "Regular", "Scheduled", "Normal"],
    "high":         ["Elevated", "Urgent", "Accelerated", "Priority"],
    "critical":     ["Severe", "Blocking", "Immediate", "Essential"],
    "urgent":       ["Immediate", "Emergency", "Rush", "Express"],
    "p0":           ["Blocker", "Emergency", "Critical", "Severe"],
    "p1":           ["Major", "Urgent", "High", "Elevated"],
    "p2":           ["Moderate", "Normal", "Medium", "Scheduled"],
    "p3":           ["Minor", "Low", "Routine", "Deferred"],
    # issue / task type
    "bug":          ["Defect", "Fault", "Anomaly", "Regression"],
    "feature":      ["Enhancement", "Capability", "Addition", "Improvement"],
    "task":         ["Action", "WorkItem", "Operation", "Item"],
    "epic":         ["Initiative", "Theme", "Goal", "Stream"],
    "chore":        ["Maintenance", "Cleanup", "Upkeep", "Routine"],
    "spike":        ["Investigation", "Research", "Exploration", "Discovery"],
    "enhancement":  ["Improvement", "Upgrade", "Extension", "Boost"],
    # release type
    "major":        ["Breaking", "Principal", "Primary", "Core"],
    "minor":        ["Incremental", "Supplemental", "Small", "Patch"],
    "patch":        ["Fix", "Correction", "Update", "Repair"],
    "hotfix":       ["Emergency", "Urgent", "Critical", "Immediate"],
    # environment
    "dev":          ["Development", "Local", "Sandbox", "Experimental"],
    "staging":      ["PreProd", "Validation", "Integration", "Canary"],
    "prod":         ["Production", "Live", "Released", "Deployed"],
    "dr":           ["Recovery", "Failover", "Backup", "Redundant"],
    # roles
    "admin":        ["Superuser", "Manager", "Owner", "Principal"],
    "member":       ["Participant", "Contributor", "Regular", "Standard"],
    "viewer":       ["Observer", "Reader", "Readonly", "Watcher"],
    "guest":        ["External", "Visitor", "Temporary", "Limited"],
    "lead":         ["Principal", "Senior", "Head", "Primary"],
    "owner":        ["Principal", "Custodian", "Steward", "Manager"],
    # severity
    "sev1":         ["Critical", "Emergency", "P0", "Blocker"],
    "sev2":         ["Major", "Urgent", "P1", "High"],
    "sev3":         ["Moderate", "Normal", "P2", "Medium"],
    "sev4":         ["Minor", "Low", "P3", "Routine"],
    # order / payment
    "confirmed":    ["Accepted", "Validated", "Cleared", "Authorized"],
    "processing":   ["Handling", "Working", "Executing", "Active"],
    "shipped":      ["Dispatched", "Sent", "Fulfilled", "InTransit"],
    "delivered":    ["Received", "Complete", "Fulfilled", "Handed"],
    "refunded":     ["Returned", "Reversed", "Credited", "Reimbursed"],
    "disputed":     ["Contested", "Challenged", "Flagged", "Queried"],
    "past_due":     ["Overdue", "Late", "Delinquent", "Lapsed"],
    "trialing":     ["Testing", "Evaluating", "Piloting", "Sampling"],
    "paused":       ["Suspended", "Halted", "Stopped", "Frozen"],
    # service / cluster
    "running":      ["Operational", "Active", "Live", "Serving"],
    "stopped":      ["Halted", "Offline", "Down", "Terminated"],
    "maintenance":  ["Servicing", "Updating", "Upgrading", "Patching"],
    "terminated":   ["Deleted", "Destroyed", "Deprovisioned", "Removed"],
    "degraded":     ["Impaired", "Partial", "Reduced", "Limited"],
    "provisioning": ["Creating", "Initializing", "Starting", "Deploying"],
    "rolled_back":  ["Reverted", "Restored", "Undone", "Reset"],
    # deployment
    "acknowledged": ["Noted", "Seen", "Received", "Registered"],
    "suppressed":   ["Muted", "Silenced", "Ignored", "Filtered"],
    # subscription
    "trialing":     ["Evaluating", "Piloting", "Testing", "Sampling"],
    # document / content
    "postmortem":   ["Analysis", "Retrospective", "Review", "Inquiry"],
    "investigating":["Analyzing", "Diagnosing", "Assessing", "Probing"],
    "mitigated":    ["Contained", "Reduced", "Controlled", "Bounded"],
    # employee
    "full_time":    ["Permanent", "Regular", "Staff", "Salaried"],
    "part_time":    ["Parttime", "Fractional", "Casual", "Flex"],
    "contractor":   ["Freelance", "Consulting", "External", "Independent"],
    "intern":       ["Trainee", "Apprentice", "Junior", "Provisional"],
}

_COMPUTED_DEST_FIELDS = {
    "concat":         ["full_title", "composite_ref", "heading_text", "display_label", "short_name"],
    "multiply":       ["estimated_cost", "weighted_value", "derived_metric", "total_amount", "net_price"],
    "sum_fields":     ["grand_total", "net_value", "running_total", "aggregate_score", "combined_count"],
    "bool_from_enum": ["flagged", "needs_attention", "in_flight", "watchlisted", "is_escalated"],
}


# ---------------------------------------------------------------------------
# Label generators (safe past 26 items)
# ---------------------------------------------------------------------------

def _entity_label(i):
    if i < 26:
        return f"Entity{chr(65 + i)}"
    return f"Entity{chr(65 + i // 26 - 1)}{chr(65 + i % 26)}"


def _field_label(i):
    if i < 26:
        return f"f{chr(97 + i)}"
    return f"f{chr(97 + i // 26 - 1)}{chr(97 + i % 26)}"


# ---------------------------------------------------------------------------
# Small lookup helpers
# ---------------------------------------------------------------------------

def _pre_rename_name(transforms, entity, current_name):
    """Resolve a post-T1 field name back to its original source name."""
    for t in transforms:
        if t["type"] == "rename" and t["entity"] == entity and t["to"] == current_name:
            return t["from"]
    return current_name


def _get_pre_remap_value(transforms, entity, field, current_value):
    """Resolve a post-T1 enum value back to its original value for synonym lookup."""
    for t in transforms:
        if t["type"] == "enum_remap" and t["entity"] == entity and t["field"] == field:
            for orig, remapped in t["mapping"].items():
                if remapped == current_value:
                    return orig
    return current_value


def _pick_dest_field(op, existing_fields):
    pool = _COMPUTED_DEST_FIELDS[op]
    available = [f for f in pool if f not in existing_fields]
    if available:
        return random.choice(available)
    base = random.choice(pool)
    i = 2
    while f"{base}_{i}" in existing_fields:
        i += 1
    return f"{base}_{i}"


# ---------------------------------------------------------------------------
# T1 noise (rename / retype / enum_remap)
# Used as a fallback inside Tier 2 and as step 1 of Tier 3.
# ---------------------------------------------------------------------------

def _apply_tier1(dest, transforms):
    entities = dest["entities"]

    # 1. Rename 1–2 non-id, non-nested fields (ref fields are eligible)
    rename_candidates = [
        (ename, fname)
        for ename, entity in entities.items()
        for fname, fdef in entity["fields"].items()
        if fdef["kind"] not in ("id", "nested")
    ]
    random.shuffle(rename_candidates)
    n_renames = min(random.randint(1, 2), len(rename_candidates))
    for ename, fname in rename_candidates[:n_renames]:
        suffix = random.choice(_RENAME_SUFFIXES)
        new_name = fname + suffix
        entities[ename]["fields"][new_name] = entities[ename]["fields"].pop(fname)
        transforms.append({"type": "rename", "entity": ename, "from": fname, "to": new_name})

    # 2. Retype 1–2 coercible fields (using current names — may be post-rename)
    retype_candidates = [
        (ename, fname, fdef["kind"])
        for ename, entity in entities.items()
        for fname, fdef in entity["fields"].items()
        if fdef["kind"] in _COERCIONS
    ]
    random.shuffle(retype_candidates)
    n_retypes = min(random.randint(1, 2), len(retype_candidates))
    for ename, fname, kind in retype_candidates[:n_retypes]:
        new_kind = random.choice(_COERCIONS[kind])
        entities[ename]["fields"][fname] = {"kind": new_kind}
        transforms.append({"type": "retype", "entity": ename, "field": fname,
                            "from": kind, "to": new_kind})

    # 3. Enum remap — 60% chance, one enum field, all values suffixed
    if random.random() < 0.60:
        enum_candidates = [
            (ename, fname, fdef)
            for ename, entity in entities.items()
            for fname, fdef in entity["fields"].items()
            if fdef["kind"] == "enum" and fdef.get("values")
        ]
        if enum_candidates:
            ename, fname, fdef = random.choice(enum_candidates)
            suffix = random.choice(["_v2", "_new", "_updated"])
            mapping = {v: v + suffix for v in fdef["values"]}
            entities[ename]["fields"][fname] = {"kind": "enum", "values": list(mapping.values())}
            transforms.append({"type": "enum_remap", "entity": ename,
                                "field": fname, "mapping": mapping})


# ---------------------------------------------------------------------------
# Structural transforms — each returns the transform dict on success or None
# ---------------------------------------------------------------------------

def _try_unmapped(dest, transforms):
    """Drop 1–2 scalar fields from dest so the model must leave them absent."""
    entities = dest["entities"]
    candidates = [
        (ename, fname)
        for ename, entity in entities.items()
        for fname, fdef in entity["fields"].items()
        if fdef["kind"] not in ("id", "ref", "nested")
    ]
    if not candidates:
        return None
    random.shuffle(candidates)
    n_drop = random.randint(1, min(2, len(candidates)))
    results = []
    for ename, fname in candidates[:n_drop]:
        del entities[ename]["fields"][fname]
        t = {"type": "unmapped", "entity": ename, "field": fname}
        transforms.append(t)
        results.append(t)
    return results if results else None


def _try_flatten_nested(dest, transforms):
    """Replace a nested field with a count scalar."""
    entities = dest["entities"]
    candidates = [
        (ename, fname, fdef)
        for ename, entity in entities.items()
        for fname, fdef in entity["fields"].items()
        if fdef["kind"] == "nested"
    ]
    if not candidates:
        return None
    ename, fname, fdef = random.choice(candidates)
    block_name = fdef["of"]
    count_field = f"{fname}_count"
    del entities[ename]["fields"][fname]
    entities[ename]["fields"][count_field] = {"kind": "number"}
    t = {"type": "flatten_nested", "entity": ename, "field": fname,
         "block": block_name, "into": count_field, "strategy": "count"}
    transforms.append(t)
    return t


def _try_split(dest, transforms, exclude=None):
    """
    Pick entity with ≥4 fields; move a random subset of scalars to a new
    {EntityName}Detail entity with a back-ref FK.
    """
    if exclude is None:
        exclude = set()
    entities = dest["entities"]

    eligible = [
        ename for ename, entity in entities.items()
        if ename not in exclude
        and f"{ename}Detail" not in entities
        and len(entity["fields"]) >= 4
        and sum(1 for fd in entity["fields"].values()
                if fd["kind"] not in ("id", "ref", "nested")) >= 2
    ]
    if not eligible:
        return None

    ename = random.choice(eligible)
    entity = entities[ename]
    moveable = [
        fname for fname, fdef in entity["fields"].items()
        if fdef["kind"] not in ("id", "ref", "nested")
    ]
    # Move at least 1, keep at least 1 scalar in original
    max_move = max(1, len(moveable) - 1)
    n_move = random.randint(1, max_move)
    moved_fields = random.sample(moveable, n_move)

    detail_name = f"{ename}Detail"
    link_field = f"{ename.lower()}_id"

    detail_fields = {
        "id": {"kind": "id"},
        link_field: {"kind": "ref", "target": ename, "cardinality": "one"},
    }
    for fname in moved_fields:
        detail_fields[fname] = copy.deepcopy(entity["fields"].pop(fname))

    entities[detail_name] = {"fields": detail_fields}

    t = {"type": "split", "from": ename, "into": [ename, detail_name],
         "moved_fields": moved_fields, "link_field": link_field}
    transforms.append(t)
    return t


def _try_merge(dest, transforms, exclude=None):
    """
    Find a child entity with exactly 1 ref to a parent; absorb both into a
    new {ParentName}{Suffix} entity. Conflicting child field names get a
    {childname_} prefix. Child's id field is dropped (not preserved in merge).

    Only merges when the parent has no other incoming refs in the schema —
    this prevents dangling refs in other entities after the parent is deleted.
    """
    if exclude is None:
        exclude = set()
    entities = dest["entities"]

    # Build a map of how many entities reference each entity (incoming ref count)
    incoming_ref_count: dict = {}
    for ename, entity in entities.items():
        for fdef in entity["fields"].values():
            if fdef.get("kind") == "ref" and fdef.get("target") in entities:
                target = fdef["target"]
                incoming_ref_count[target] = incoming_ref_count.get(target, 0) + 1

    child_candidates = []
    for ename, entity in entities.items():
        if ename in exclude:
            continue
        ref_fields = [
            (fname, fdef) for fname, fdef in entity["fields"].items()
            if fdef["kind"] == "ref"
        ]
        if len(ref_fields) == 1:
            parent_name = ref_fields[0][1]["target"]
            if parent_name in entities and parent_name not in exclude:
                # Valid only if:
                # 1. Child is the sole entity referencing the parent (deleting parent
                #    won't orphan anyone else)
                # 2. Nothing else references the child (deleting child won't orphan anyone)
                if (incoming_ref_count.get(parent_name, 0) == 1
                        and incoming_ref_count.get(ename, 0) == 0):
                    child_candidates.append((ename, ref_fields[0][0], parent_name))

    if not child_candidates:
        return None

    child_name, link_field, parent_name = random.choice(child_candidates)

    # Avoid collision with existing entity names
    used_names = set(entities.keys())
    suffix = random.choice(_MERGE_SUFFIXES)
    merged_name = f"{parent_name}{suffix}"
    attempts = 0
    while merged_name in used_names and attempts < 20:
        suffix = random.choice(_MERGE_SUFFIXES)
        merged_name = f"{parent_name}{suffix}"
        attempts += 1

    parent_fields = entities[parent_name]["fields"]
    child_fields = entities[child_name]["fields"]

    merged_fields = copy.deepcopy(parent_fields)
    for fname, fdef in child_fields.items():
        if fname == link_field:
            continue  # drop the FK to parent — it is now implicit
        if fdef["kind"] == "id":
            continue  # child ids are not preserved in merge
        dest_fname = fname if fname not in merged_fields else f"{child_name.lower()}_{fname}"
        merged_fields[dest_fname] = copy.deepcopy(fdef)

    del entities[parent_name]
    del entities[child_name]
    entities[merged_name] = {"fields": merged_fields}

    t = {"type": "merge", "from": [parent_name, child_name],
         "into": merged_name, "dropped_link_field": link_field}
    transforms.append(t)
    return t


def _try_extract_nested(dest, transforms):
    """
    Normalise a nested block into a proper child entity.
    New entity name = block name minus 'Block' + random suffix (Entry/Item/Row/Record).
    The parent entity name is deliberately excluded from the new entity name.
    """
    entities = dest["entities"]
    nested_blocks = dest.get("nested_blocks", {})

    candidates = [
        (ename, fname, fdef)
        for ename, entity in entities.items()
        for fname, fdef in entity["fields"].items()
        if fdef["kind"] == "nested" and fdef["of"] in nested_blocks
    ]
    if not candidates:
        return None

    ename, fname, fdef = random.choice(candidates)
    block_name = fdef["of"]
    block_def = nested_blocks[block_name]

    base = block_name.replace("Block", "")
    suffix = random.choice(_EXTRACT_SUFFIXES)
    new_entity_name = f"{base}{suffix}"
    # Avoid collision; also avoid using parent entity name in the new name
    attempts = 0
    while new_entity_name in entities and attempts < 20:
        suffix = random.choice(_EXTRACT_SUFFIXES)
        new_entity_name = f"{base}{suffix}"
        attempts += 1

    link_field = f"{ename.lower()}_id"
    new_fields = {
        "id": {"kind": "id"},
        link_field: {"kind": "ref", "target": ename, "cardinality": "one"},
    }
    new_fields.update(copy.deepcopy(block_def["fields"]))

    del entities[ename]["fields"][fname]
    entities[new_entity_name] = {"fields": new_fields}

    t = {"type": "extract_nested", "entity": ename, "field": fname,
         "block": block_name, "new_entity": new_entity_name, "link_field": link_field}
    transforms.append(t)
    return t


def _try_partition(dest, transforms, exclude=None):
    """
    Split entity into N sub-entities by an enum discriminator.
    Sub-entity names use synonym obfuscation: {Synonym}{EntityName}.
    Handles enum values that were remapped by T1 by resolving back to originals.

    Only partitions entities with no incoming refs from other dest entities —
    partition deletes the entity, which would otherwise leave dangling refs.
    """
    if exclude is None:
        exclude = set()
    entities = dest["entities"]

    # Entities that are targets of ref fields in other dest entities
    referenced_entities = {
        fdef["target"]
        for entity in entities.values()
        for fdef in entity["fields"].values()
        if fdef.get("kind") == "ref" and fdef.get("target") in entities
    }

    # Need enum fields with ≥2 values on non-excluded, non-referenced entities
    candidates = [
        (ename, fname, fdef)
        for ename, entity in entities.items()
        if ename not in exclude
        and ename not in referenced_entities  # deleting this entity won't orphan refs
        for fname, fdef in entity["fields"].items()
        if fdef["kind"] == "enum" and len(fdef.get("values", [])) >= 2
    ]
    if not candidates:
        return None

    ename, disc_field, disc_fdef = random.choice(candidates)
    values = disc_fdef["values"]
    used_sub_names = set(entities.keys())

    mapping = {}
    for val in values:
        base_val = _get_pre_remap_value(transforms, ename, disc_field, val)
        synonyms = list(_ENUM_SYNONYMS.get(base_val, []))
        if synonyms:
            random.shuffle(synonyms)
            syn = synonyms[0]
        else:
            # Fallback: title-case the original value
            syn = base_val.replace("_", " ").title().replace(" ", "")
        sub_name = f"{syn}{ename}"
        # Avoid collision
        tag = 0
        while sub_name in used_sub_names or sub_name in mapping.values():
            tag += 1
            sub_name = f"{syn}{tag}{ename}"
        mapping[val] = sub_name
        used_sub_names.add(sub_name)

    # Build sub-entity schemas — all fields except the discriminator
    base_fields = {
        fname: copy.deepcopy(fdef)
        for fname, fdef in entities[ename]["fields"].items()
        if fname != disc_field
    }
    for sub_name in mapping.values():
        entities[sub_name] = {"fields": copy.deepcopy(base_fields)}

    del entities[ename]

    t = {"type": "partition", "entity": ename,
         "on_field": disc_field, "mapping": mapping}
    transforms.append(t)
    return t


def _try_denormalize(dest, transforms, allowed=None):
    """
    Inline 1–2 scalar fields from a ref target into the referencing entity.
    source_field is always the pre-rename (source) name.
    Restricted to entities in `allowed` (T1-surviving entities).
    """
    if allowed is None:
        allowed = set(dest["entities"].keys())
    entities = dest["entities"]

    # Ref fields in allowed entities whose target still exists in dest
    candidates = [
        (ename, fname, fdef)
        for ename in allowed
        if ename in entities
        for fname, fdef in entities[ename]["fields"].items()
        if fdef["kind"] == "ref" and fdef["target"] in entities
    ]
    if not candidates:
        return None

    ename, via_field, via_fdef = random.choice(candidates)
    from_entity = via_fdef["target"]

    scalar_candidates = [
        (fname, fdef)
        for fname, fdef in entities[from_entity]["fields"].items()
        if fdef["kind"] not in ("id", "ref", "nested")
    ]
    if not scalar_candidates:
        return None

    random.shuffle(scalar_candidates)
    n_inline = random.randint(1, min(2, len(scalar_candidates)))

    inlined = []
    for fname, fdef in scalar_candidates[:n_inline]:
        # Store the pre-rename name so the grader can look it up in source_data
        source_field = _pre_rename_name(transforms, from_entity, fname)
        dest_field = f"{from_entity.lower()}_{source_field}_inline"
        entities[ename]["fields"][dest_field] = copy.deepcopy(fdef)
        inlined.append({"source_field": source_field, "dest_field": dest_field})

    t = {"type": "denormalize", "entity": ename, "via_field": via_field,
         "from_entity": from_entity, "inlined": inlined}
    transforms.append(t)
    return t


def _try_computed(dest, transforms, allowed=None, denorm_dest_fields=None):
    """
    Add a derived field with an opaque business-logic name.
    Operations: concat, multiply, sum_fields, bool_from_enum.
    Denormalized dest fields are excluded as source candidates.
    """
    if allowed is None:
        allowed = set(dest["entities"].keys())
    if denorm_dest_fields is None:
        denorm_dest_fields = set()
    entities = dest["entities"]

    ops = ["concat", "multiply", "sum_fields", "bool_from_enum"]
    random.shuffle(ops)

    for ename in (e for e in allowed if e in entities):
        entity_fields = entities[ename]["fields"]
        for op in ops:
            if op == "concat":
                text_fields = [
                    f for f, fd in entity_fields.items()
                    if fd["kind"] in ("text", "richtext")
                    and (ename, f) not in denorm_dest_fields
                ]
                if len(text_fields) >= 2:
                    src = random.sample(text_fields, 2)
                    sep = random.choice([" ", " - ", ", ", " | "])
                    dest_field = _pick_dest_field(op, entity_fields)
                    entity_fields[dest_field] = {"kind": "text"}
                    t = {"type": "computed", "entity": ename, "operation": op,
                         "source_fields": src, "dest_field": dest_field, "separator": sep}
                    transforms.append(t)
                    return t

            elif op == "multiply":
                num_fields = [
                    f for f, fd in entity_fields.items()
                    if fd["kind"] == "number"
                    and (ename, f) not in denorm_dest_fields
                ]
                if len(num_fields) >= 2:
                    src = random.sample(num_fields, 2)
                    dest_field = _pick_dest_field(op, entity_fields)
                    entity_fields[dest_field] = {"kind": "number"}
                    t = {"type": "computed", "entity": ename, "operation": op,
                         "source_fields": src, "dest_field": dest_field}
                    transforms.append(t)
                    return t

            elif op == "sum_fields":
                num_fields = [
                    f for f, fd in entity_fields.items()
                    if fd["kind"] == "number"
                    and (ename, f) not in denorm_dest_fields
                ]
                if len(num_fields) >= 2:
                    src = random.sample(num_fields, 2)
                    dest_field = _pick_dest_field(op, entity_fields)
                    entity_fields[dest_field] = {"kind": "number"}
                    t = {"type": "computed", "entity": ename, "operation": op,
                         "source_fields": src, "dest_field": dest_field}
                    transforms.append(t)
                    return t

            elif op == "bool_from_enum":
                enum_fields = [
                    (f, fd) for f, fd in entity_fields.items()
                    if fd["kind"] == "enum" and fd.get("values")
                    and (ename, f) not in denorm_dest_fields
                ]
                if enum_fields:
                    fname, fdef = random.choice(enum_fields)
                    value = random.choice(fdef["values"])
                    dest_field = _pick_dest_field(op, entity_fields)
                    entity_fields[dest_field] = {"kind": "bool"}
                    t = {"type": "computed", "entity": ename, "operation": op,
                         "source_field": fname, "value": value, "dest_field": dest_field}
                    transforms.append(t)
                    return t

    return None


# ---------------------------------------------------------------------------
# Tier orchestrators
# ---------------------------------------------------------------------------

def _apply_tier2(dest, transforms):
    """
    Try 2 ops from a shuffled pool {split, merge, flatten_nested, unmapped}.
    Fall back to T1 if 0 structural ops succeed.
    """
    pool = [_try_split, _try_merge, _try_flatten_nested, _try_unmapped]
    random.shuffle(pool)
    succeeded = sum(1 for op in pool[:2] if op(dest, transforms) is not None)
    if succeeded == 0:
        _apply_tier1(dest, transforms)
    return dest, transforms


def _apply_tier3(dest, transforms):
    """
    Full Tier-3 transform stack in the order mandated by summary.md:
    1. T1 noise
    2. unmapped
    3. extract_nested
    4. split         (excl. extract-created / extract-parents)
    5. merge ×2      (excl. split/extract-created / extract-parents)
    6. partition     (excl. merge/split/extract-created / extract-parents)
    7. denormalize   (T1-surviving entities only)
    8. computed ×1–2 (T1-surviving entities only; runs LAST)
    """
    # Step 1 — T1 noise
    _apply_tier1(dest, transforms)

    # Step 2 — unmapped
    _try_unmapped(dest, transforms)

    # Snapshot of surviving entities before structural transforms
    t1_surviving = set(dest["entities"].keys())

    # Step 3 — extract_nested
    extract_created: set = set()
    extract_parents: set = set()
    t = _try_extract_nested(dest, transforms)
    if t:
        extract_created.add(t["new_entity"])
        extract_parents.add(t["entity"])

    # Step 4 — split (excl. extract-created and extract-parents)
    split_created: set = set()
    split_exclude = extract_created | extract_parents
    t = _try_split(dest, transforms, exclude=split_exclude)
    if t:
        split_created.add(t["into"][1])  # the Detail entity

    # Step 5 — merge ×2 (excl. split/extract-created / extract-parents)
    merge_created: set = set()
    merge_exclude = split_created | extract_created | extract_parents
    for _ in range(2):
        t = _try_merge(dest, transforms, exclude=merge_exclude)
        if t:
            merge_created.add(t["into"])
            merge_exclude.add(t["into"])  # don't re-merge something just created

    # Step 6 — partition (excl. merge/split/extract-created / extract-parents)
    part_exclude = merge_created | split_created | extract_created | extract_parents
    _try_partition(dest, transforms, exclude=part_exclude)

    # Step 7 — denormalize (T1-surviving entities that still exist in dest)
    denoorm_allowed = t1_surviving & set(dest["entities"].keys())
    _try_denormalize(dest, transforms, allowed=denoorm_allowed)

    # Step 8 — computed ×1–2 (T1-surviving; excl. denorm inline fields)
    computed_allowed = t1_surviving & set(dest["entities"].keys())
    denorm_dest_fields = {
        (t["entity"], item["dest_field"])
        for t in transforms
        if t["type"] == "denormalize"
        for item in t["inlined"]
    }
    for _ in range(random.randint(1, 2)):
        _try_computed(dest, transforms,
                      allowed=computed_allowed,
                      denorm_dest_fields=denorm_dest_fields)

    return dest, transforms


# ---------------------------------------------------------------------------
# Name obfuscation — Tier 3 only
# ---------------------------------------------------------------------------

def obfuscate_dest_schema(dest_schema):
    """
    Replace all entity and field names with opaque identifiers.
    Returns (obf_schema, entity_map, field_maps).

    entity_map:  {"User": "EntityA", ...}
    field_maps:  {"User": {"name": "fa", "email": "fb", ..., "id": "id"}, ...}

    ref.target values are rewritten to the obfuscated entity name.
    id always stays id.
    """
    entities = dest_schema["entities"]
    entity_names = list(entities.keys())
    random.shuffle(entity_names)
    entity_map = {name: _entity_label(i) for i, name in enumerate(entity_names)}

    field_maps = {}
    for real_name in entity_names:
        non_id = [f for f in entities[real_name]["fields"] if f != "id"]
        random.shuffle(non_id)
        fmap = {fname: _field_label(i) for i, fname in enumerate(non_id)}
        fmap["id"] = "id"
        field_maps[real_name] = fmap

    obf_entities = {}
    for real_name, obf_name in entity_map.items():
        fmap = field_maps[real_name]
        obf_fields = {}
        for fname, fdef in entities[real_name]["fields"].items():
            obf_fname = fmap.get(fname, fname)
            obf_fdef = copy.deepcopy(fdef)
            if obf_fdef.get("kind") == "ref":
                obf_fdef["target"] = entity_map.get(obf_fdef["target"], obf_fdef["target"])
            obf_fields[obf_fname] = obf_fdef
        obf_entities[obf_name] = {"fields": obf_fields}

    obf_schema = {"entities": obf_entities}
    if dest_schema.get("nested_blocks"):
        obf_schema["nested_blocks"] = copy.deepcopy(dest_schema["nested_blocks"])

    return obf_schema, entity_map, field_maps


def translate_dest_data(dest_data, entity_map, field_maps):
    """
    Reverse obfuscation on LLM-written records so the grader sees real names.
    dest_data:  {"EntityA": [{"id": 1, "fa": "foo", ...}], ...}
    Returns:    {"User": [{"id": 1, "name": "foo", ...}], ...}
    """
    rev_entity = {v: k for k, v in entity_map.items()}
    rev_fields = {
        entity_map[real]: {obf: real_f for real_f, obf in fmap.items()}
        for real, fmap in field_maps.items()
    }

    real_data = {}
    for obf_entity, records in dest_data.items():
        real_entity = rev_entity.get(obf_entity, obf_entity)
        fmap = rev_fields.get(obf_entity, {})
        real_data[real_entity] = [
            {fmap.get(f, f): v for f, v in record.items()}
            for record in records
        ]
    return real_data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_difficulty(source_schema, tier):
    """
    Return (dest_schema, transformations) for the given tier.

    dest_schema is a deep-copy of source_schema with all transforms applied.
    transformations is the ordered list of transform dicts (ground truth for grader).
    Tier 3 dest_schema has real names; call obfuscate_dest_schema() before
    showing it to the LLM.
    """
    dest = copy.deepcopy(source_schema)
    transforms = []

    if tier == 2:
        return _apply_tier2(dest, transforms)
    if tier == 3:
        return _apply_tier3(dest, transforms)

    raise NotImplementedError(f"apply_difficulty: tier {tier} is not implemented")
