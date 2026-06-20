import random
import copy

# ---------------------------------------------------------------------------
# Nested block catalogue — 12 block types, each with 3–6 fields
# ---------------------------------------------------------------------------

_NESTED_BLOCKS = {
    "LineItemBlock": {
        "fields": {
            "product_name": {"kind": "text"},
            "sku":          {"kind": "text"},
            "qty":          {"kind": "number"},
            "unit_price":   {"kind": "number"},
            "discount":     {"kind": "number"},
            "total":        {"kind": "number"},
        }
    },
    "CommentBlock": {
        "fields": {
            "body":      {"kind": "richtext"},
            "author":    {"kind": "text"},
            "posted_at": {"kind": "date"},
            "upvotes":   {"kind": "number"},
            "is_pinned": {"kind": "bool"},
        }
    },
    "TagBlock": {
        "fields": {
            "label":    {"kind": "text"},
            "color":    {"kind": "text"},
            "category": {"kind": "text"},
        }
    },
    "AddressBlock": {
        "fields": {
            "street":  {"kind": "text"},
            "city":    {"kind": "text"},
            "state":   {"kind": "text"},
            "country": {"kind": "text"},
            "zip":     {"kind": "text"},
            "type":    {"kind": "enum", "values": ["billing", "shipping", "office"]},
        }
    },
    "ReviewBlock": {
        "fields": {
            "rating":     {"kind": "number"},
            "title":      {"kind": "text"},
            "body":       {"kind": "richtext"},
            "reviewer":   {"kind": "text"},
            "verified":   {"kind": "bool"},
            "created_at": {"kind": "date"},
        }
    },
    "AttachmentBlock": {
        "fields": {
            "filename":    {"kind": "text"},
            "url":         {"kind": "text"},
            "file_type":   {"kind": "enum", "values": ["pdf", "image", "doc", "video", "archive"]},
            "size_kb":     {"kind": "number"},
            "uploaded_at": {"kind": "date"},
        }
    },
    "ChecklistBlock": {
        "fields": {
            "item":     {"kind": "text"},
            "checked":  {"kind": "bool"},
            "due_date": {"kind": "date"},
            "assignee": {"kind": "text"},
        }
    },
    "MetricBlock": {
        "fields": {
            "name":   {"kind": "text"},
            "value":  {"kind": "number"},
            "unit":   {"kind": "text"},
            "target": {"kind": "number"},
            "period": {"kind": "enum", "values": ["daily", "weekly", "monthly", "quarterly"]},
        }
    },
    "ContactBlock": {
        "fields": {
            "name":       {"kind": "text"},
            "email":      {"kind": "text"},
            "phone":      {"kind": "text"},
            "role":       {"kind": "text"},
            "is_primary": {"kind": "bool"},
        }
    },
    "StepBlock": {
        "fields": {
            "title":       {"kind": "text"},
            "description": {"kind": "richtext"},
            "order":       {"kind": "number"},
            "status":      {"kind": "enum", "values": ["pending", "in_progress", "done", "skipped"]},
            "duration_m":  {"kind": "number"},
        }
    },
    "LogBlock": {
        "fields": {
            "message":   {"kind": "text"},
            "level":     {"kind": "enum", "values": ["debug", "info", "warn", "error"]},
            "timestamp": {"kind": "date"},
            "service":   {"kind": "text"},
        }
    },
    "CustomFieldBlock": {
        "fields": {
            "key":        {"kind": "text"},
            "value":      {"kind": "text"},
            "field_type": {"kind": "enum", "values": ["text", "number", "date", "bool", "select"]},
        }
    },
}

_NESTED_FIELD_NAMES = {
    "LineItemBlock":   "line_items",
    "CommentBlock":    "comments",
    "TagBlock":        "tags",
    "AddressBlock":    "addresses",
    "ReviewBlock":     "reviews",
    "AttachmentBlock": "attachments",
    "ChecklistBlock":  "checklist",
    "MetricBlock":     "metrics",
    "ContactBlock":    "contacts",
    "StepBlock":       "steps",
    "LogBlock":        "logs",
    "CustomFieldBlock":"custom_fields",
}

# ---------------------------------------------------------------------------
# Entity catalogue — 59 entity types across 4 layers
#
# deps   — entity names whose id fields must be in the schema before this
#           entity can be added (corresponds exactly to ref fields in base_fields)
# base_fields   — always included; defines the entity's identity and core refs
# optional_pool — scalar fields only (no refs); randomly sampled to vary schemas
# ---------------------------------------------------------------------------

_ENTITY_CATALOG = {

    # ================================================================
    # LAYER 0 — Root entities (no deps, no ref fields)
    # ================================================================

    "User": {
        "deps": [],
        "base_fields": {
            "id":    {"kind": "id"},
            "name":  {"kind": "text"},
            "email": {"kind": "text"},
            "role":  {"kind": "enum", "values": ["admin", "member", "viewer", "guest"]},
        },
        "optional_pool": {
            "phone":      {"kind": "text"},
            "title":      {"kind": "text"},
            "department": {"kind": "enum", "values": ["engineering", "product", "design", "sales", "ops", "support", "legal", "finance"]},
            "created_at": {"kind": "date"},
            "is_active":  {"kind": "bool"},
            "timezone":   {"kind": "text"},
            "bio":        {"kind": "richtext"},
            "skills":     {"kind": "multi_enum", "values": ["backend", "frontend", "data", "ml", "design", "ops", "security"]},
        },
    },

    "Organization": {
        "deps": [],
        "base_fields": {
            "id":     {"kind": "id"},
            "name":   {"kind": "text"},
            "domain": {"kind": "text"},
        },
        "optional_pool": {
            "industry":       {"kind": "enum", "values": ["tech", "finance", "healthcare", "education", "retail", "logistics", "media", "government"]},
            "size":           {"kind": "enum", "values": ["startup", "smb", "mid_market", "enterprise"]},
            "plan":           {"kind": "enum", "values": ["free", "starter", "pro", "enterprise"]},
            "founded_at":     {"kind": "date"},
            "is_active":      {"kind": "bool"},
            "country":        {"kind": "text"},
            "website":        {"kind": "text"},
            "description":    {"kind": "richtext"},
            "employee_count": {"kind": "number"},
        },
    },

    "Customer": {
        "deps": [],
        "base_fields": {
            "id":     {"kind": "id"},
            "name":   {"kind": "text"},
            "email":  {"kind": "text"},
            "status": {"kind": "enum", "values": ["lead", "prospect", "active", "churned", "suspended"]},
        },
        "optional_pool": {
            "phone":      {"kind": "text"},
            "company":    {"kind": "text"},
            "tier":       {"kind": "enum", "values": ["free", "basic", "pro", "enterprise"]},
            "country":    {"kind": "text"},
            "mrr":        {"kind": "number"},
            "created_at": {"kind": "date"},
            "is_verified":{"kind": "bool"},
            "notes":      {"kind": "richtext"},
            "source":     {"kind": "enum", "values": ["organic", "referral", "paid", "partner", "event"]},
        },
    },

    "Vendor": {
        "deps": [],
        "base_fields": {
            "id":    {"kind": "id"},
            "name":  {"kind": "text"},
            "email": {"kind": "text"},
        },
        "optional_pool": {
            "website":       {"kind": "text"},
            "status":        {"kind": "enum", "values": ["active", "inactive", "pending", "blocked"]},
            "contract_type": {"kind": "enum", "values": ["msa", "sow", "nda", "subscription", "purchase_order"]},
            "rating":        {"kind": "number"},
            "country":       {"kind": "text"},
            "category":      {"kind": "enum", "values": ["software", "hardware", "services", "consulting", "cloud", "logistics"]},
            "notes":         {"kind": "richtext"},
            "payment_terms": {"kind": "text"},
        },
    },

    "Product": {
        "deps": [],
        "base_fields": {
            "id":    {"kind": "id"},
            "name":  {"kind": "text"},
            "sku":   {"kind": "text"},
            "price": {"kind": "number"},
        },
        "optional_pool": {
            "cost":        {"kind": "number"},
            "category":    {"kind": "enum", "values": ["software", "hardware", "service", "subscription", "physical"]},
            "status":      {"kind": "enum", "values": ["active", "deprecated", "draft", "discontinued"]},
            "description": {"kind": "richtext"},
            "in_stock":    {"kind": "bool"},
            "weight":      {"kind": "number"},
            "unit":        {"kind": "text"},
            "tags":        {"kind": "multi_enum", "values": ["new", "sale", "featured", "limited", "digital", "physical"]},
        },
    },

    "Environment": {
        "deps": [],
        "base_fields": {
            "id":   {"kind": "id"},
            "name": {"kind": "text"},
            "type": {"kind": "enum", "values": ["dev", "staging", "prod", "dr"]},
        },
        "optional_pool": {
            "region":             {"kind": "text"},
            "cloud_provider":     {"kind": "enum", "values": ["aws", "gcp", "azure", "on_prem", "hybrid"]},
            "is_active":          {"kind": "bool"},
            "created_at":         {"kind": "date"},
            "description":        {"kind": "richtext"},
            "tier":               {"kind": "enum", "values": ["critical", "standard", "low"]},
            "maintenance_window": {"kind": "text"},
        },
    },

    "Tag": {
        "deps": [],
        "base_fields": {
            "id":   {"kind": "id"},
            "name": {"kind": "text"},
            "slug": {"kind": "text"},
        },
        "optional_pool": {
            "color":       {"kind": "text"},
            "description": {"kind": "text"},
            "category":    {"kind": "text"},
            "is_active":   {"kind": "bool"},
            "usage_count": {"kind": "number"},
        },
    },

    "Location": {
        "deps": [],
        "base_fields": {
            "id":   {"kind": "id"},
            "name": {"kind": "text"},
            "type": {"kind": "enum", "values": ["office", "warehouse", "remote", "datacenter", "store"]},
        },
        "optional_pool": {
            "address":      {"kind": "text"},
            "city":         {"kind": "text"},
            "country":      {"kind": "text"},
            "timezone":     {"kind": "text"},
            "is_active":    {"kind": "bool"},
            "capacity":     {"kind": "number"},
            "manager_name": {"kind": "text"},
        },
    },

    "Currency": {
        "deps": [],
        "base_fields": {
            "id":     {"kind": "id"},
            "code":   {"kind": "text"},
            "symbol": {"kind": "text"},
        },
        "optional_pool": {
            "name":           {"kind": "text"},
            "exchange_rate":  {"kind": "number"},
            "is_default":     {"kind": "bool"},
            "updated_at":     {"kind": "date"},
            "decimal_places": {"kind": "number"},
        },
    },

    # ================================================================
    # LAYER 1 — All deps are roots
    # ================================================================

    "Project": {
        "deps": ["User"],
        "base_fields": {
            "id":       {"kind": "id"},
            "name":     {"kind": "text"},
            "owner_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":   {"kind": "enum", "values": ["draft", "active", "on_hold", "completed", "cancelled"]},
        },
        "optional_pool": {
            "priority":   {"kind": "enum", "values": ["low", "medium", "high", "critical"]},
            "start_date": {"kind": "date"},
            "end_date":   {"kind": "date"},
            "budget":     {"kind": "number"},
            "description":{"kind": "richtext"},
            "is_public":  {"kind": "bool"},
            "phase":      {"kind": "enum", "values": ["planning", "design", "development", "testing", "launch"]},
            "tags":       {"kind": "multi_enum", "values": ["internal", "external", "client", "research", "infrastructure"]},
        },
    },

    "Team": {
        "deps": ["Organization"],
        "base_fields": {
            "id":     {"kind": "id"},
            "name":   {"kind": "text"},
            "org_id": {"kind": "ref", "target": "Organization", "cardinality": "one"},
            "type":   {"kind": "enum", "values": ["engineering", "product", "design", "sales", "ops", "support"]},
        },
        "optional_pool": {
            "description":  {"kind": "richtext"},
            "size":         {"kind": "number"},
            "slack_channel":{"kind": "text"},
            "created_at":   {"kind": "date"},
            "is_active":    {"kind": "bool"},
            "focus_area":   {"kind": "text"},
        },
    },

    "Department": {
        "deps": ["Organization"],
        "base_fields": {
            "id":     {"kind": "id"},
            "name":   {"kind": "text"},
            "org_id": {"kind": "ref", "target": "Organization", "cardinality": "one"},
        },
        "optional_pool": {
            "budget":      {"kind": "number"},
            "headcount":   {"kind": "number"},
            "cost_center": {"kind": "text"},
            "is_active":   {"kind": "bool"},
            "location":    {"kind": "text"},
            "description": {"kind": "richtext"},
        },
    },

    "Workspace": {
        "deps": ["Organization"],
        "base_fields": {
            "id":     {"kind": "id"},
            "name":   {"kind": "text"},
            "org_id": {"kind": "ref", "target": "Organization", "cardinality": "one"},
            "plan":   {"kind": "enum", "values": ["free", "team", "business", "enterprise"]},
        },
        "optional_pool": {
            "created_at":       {"kind": "date"},
            "member_count":     {"kind": "number"},
            "is_public":        {"kind": "bool"},
            "slug":             {"kind": "text"},
            "description":      {"kind": "richtext"},
            "storage_used_mb":  {"kind": "number"},
        },
    },

    "Article": {
        "deps": ["User"],
        "base_fields": {
            "id":        {"kind": "id"},
            "title":     {"kind": "text"},
            "author_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":    {"kind": "enum", "values": ["draft", "review", "published", "archived"]},
        },
        "optional_pool": {
            "published_at": {"kind": "date"},
            "word_count":   {"kind": "number"},
            "content":      {"kind": "richtext"},
            "read_time":    {"kind": "number"},
            "featured":     {"kind": "bool"},
            "category":     {"kind": "enum", "values": ["engineering", "product", "design", "business", "news"]},
            "tags":         {"kind": "multi_enum", "values": ["tutorial", "announcement", "deep_dive", "opinion", "case_study"]},
        },
    },

    "Course": {
        "deps": ["User"],
        "base_fields": {
            "id":            {"kind": "id"},
            "title":         {"kind": "text"},
            "instructor_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":        {"kind": "enum", "values": ["draft", "published", "archived", "upcoming"]},
        },
        "optional_pool": {
            "level":       {"kind": "enum", "values": ["beginner", "intermediate", "advanced"]},
            "price":       {"kind": "number"},
            "duration_h":  {"kind": "number"},
            "description": {"kind": "richtext"},
            "category":    {"kind": "enum", "values": ["programming", "design", "business", "data", "ops"]},
            "max_students":{"kind": "number"},
            "is_published":{"kind": "bool"},
        },
    },

    "Service": {
        "deps": ["Environment", "User"],
        "base_fields": {
            "id":       {"kind": "id"},
            "name":     {"kind": "text"},
            "env_id":   {"kind": "ref", "target": "Environment", "cardinality": "one"},
            "owner_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "tier":     {"kind": "enum", "values": ["critical", "standard", "low"]},
        },
        "optional_pool": {
            "repo_url":    {"kind": "text"},
            "version":     {"kind": "text"},
            "is_active":   {"kind": "bool"},
            "sla_minutes": {"kind": "number"},
            "description": {"kind": "richtext"},
            "language":    {"kind": "text"},
            "port":        {"kind": "number"},
        },
    },

    "Order": {
        "deps": ["Customer"],
        "base_fields": {
            "id":          {"kind": "id"},
            "customer_id": {"kind": "ref", "target": "Customer", "cardinality": "one"},
            "total":       {"kind": "number"},
            "status":      {"kind": "enum", "values": ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded"]},
        },
        "optional_pool": {
            "tax":            {"kind": "number"},
            "discount":       {"kind": "number"},
            "placed_at":      {"kind": "date"},
            "shipped_at":     {"kind": "date"},
            "payment_method": {"kind": "enum", "values": ["card", "bank_transfer", "paypal", "crypto", "invoice"]},
            "notes":          {"kind": "richtext"},
            "currency":       {"kind": "text"},
            "items_count":    {"kind": "number"},
        },
    },

    "Subscription": {
        "deps": ["Customer", "Product"],
        "base_fields": {
            "id":          {"kind": "id"},
            "customer_id": {"kind": "ref", "target": "Customer", "cardinality": "one"},
            "product_id":  {"kind": "ref", "target": "Product", "cardinality": "one"},
            "plan":        {"kind": "enum", "values": ["monthly", "quarterly", "annual"]},
            "status":      {"kind": "enum", "values": ["active", "cancelled", "past_due", "trialing", "paused"]},
        },
        "optional_pool": {
            "started_at":    {"kind": "date"},
            "next_billing":  {"kind": "date"},
            "amount":        {"kind": "number"},
            "is_trial":      {"kind": "bool"},
            "trial_ends_at": {"kind": "date"},
            "cancelled_at":  {"kind": "date"},
            "seats":         {"kind": "number"},
        },
    },

    "Contract": {
        "deps": ["Vendor", "User"],
        "base_fields": {
            "id":        {"kind": "id"},
            "vendor_id": {"kind": "ref", "target": "Vendor", "cardinality": "one"},
            "owner_id":  {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":    {"kind": "enum", "values": ["draft", "active", "expired", "terminated", "under_review"]},
            "value":     {"kind": "number"},
        },
        "optional_pool": {
            "start_date":    {"kind": "date"},
            "end_date":      {"kind": "date"},
            "type":          {"kind": "enum", "values": ["msa", "sow", "nda", "license", "support"]},
            "auto_renew":    {"kind": "bool"},
            "notes":         {"kind": "richtext"},
            "payment_terms": {"kind": "text"},
            "signed_at":     {"kind": "date"},
        },
    },

    "Account": {
        "deps": ["User"],
        "base_fields": {
            "id":       {"kind": "id"},
            "name":     {"kind": "text"},
            "owner_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "type":     {"kind": "enum", "values": ["prospect", "customer", "partner", "reseller"]},
            "status":   {"kind": "enum", "values": ["active", "inactive", "prospect"]},
        },
        "optional_pool": {
            "industry":       {"kind": "enum", "values": ["tech", "finance", "healthcare", "retail", "education", "logistics"]},
            "annual_revenue": {"kind": "number"},
            "employee_count": {"kind": "number"},
            "website":        {"kind": "text"},
            "created_at":     {"kind": "date"},
            "tier":           {"kind": "enum", "values": ["strategic", "major", "standard", "small"]},
        },
    },

    "Note": {
        "deps": ["User"],
        "base_fields": {
            "id":        {"kind": "id"},
            "title":     {"kind": "text"},
            "author_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":    {"kind": "enum", "values": ["draft", "published", "archived", "pinned"]},
        },
        "optional_pool": {
            "content":    {"kind": "richtext"},
            "created_at": {"kind": "date"},
            "word_count": {"kind": "number"},
            "is_pinned":  {"kind": "bool"},
            "tags":       {"kind": "multi_enum", "values": ["personal", "work", "reference", "todo", "idea"]},
            "format":     {"kind": "enum", "values": ["markdown", "rich_text", "plain"]},
            "view_count": {"kind": "number"},
        },
    },

    "Page": {
        "deps": ["User"],
        "base_fields": {
            "id":        {"kind": "id"},
            "title":     {"kind": "text"},
            "author_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":    {"kind": "enum", "values": ["draft", "published", "archived"]},
        },
        "optional_pool": {
            "published_at": {"kind": "date"},
            "content":      {"kind": "richtext"},
            "template":     {"kind": "enum", "values": ["blank", "dashboard", "doc", "kanban", "calendar", "gallery"]},
            "is_locked":    {"kind": "bool"},
            "view_count":   {"kind": "number"},
            "word_count":   {"kind": "number"},
            "icon":         {"kind": "text"},
        },
    },

    "Runbook": {
        "deps": ["User"],
        "base_fields": {
            "id":        {"kind": "id"},
            "title":     {"kind": "text"},
            "author_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":    {"kind": "enum", "values": ["draft", "approved", "deprecated"]},
            "type":      {"kind": "enum", "values": ["incident", "deployment", "maintenance", "onboarding", "offboarding"]},
        },
        "optional_pool": {
            "severity_level":  {"kind": "enum", "values": ["sev1", "sev2", "sev3"]},
            "version":         {"kind": "text"},
            "last_reviewed":   {"kind": "date"},
            "description":     {"kind": "richtext"},
            "is_approved":     {"kind": "bool"},
            "tags":            {"kind": "multi_enum", "values": ["security", "ops", "platform", "database", "network"]},
            "next_review_due": {"kind": "date"},
        },
    },

    "Policy": {
        "deps": ["User"],
        "base_fields": {
            "id":       {"kind": "id"},
            "name":     {"kind": "text"},
            "owner_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":   {"kind": "enum", "values": ["draft", "active", "deprecated", "under_review"]},
            "version":  {"kind": "text"},
        },
        "optional_pool": {
            "type":           {"kind": "enum", "values": ["security", "privacy", "hr", "compliance", "engineering"]},
            "effective_date": {"kind": "date"},
            "review_date":    {"kind": "date"},
            "description":    {"kind": "richtext"},
            "is_mandatory":   {"kind": "bool"},
            "scope":          {"kind": "multi_enum", "values": ["global", "regional", "team", "product", "customer_facing"]},
        },
    },

    "Asset": {
        "deps": ["User"],
        "base_fields": {
            "id":       {"kind": "id"},
            "name":     {"kind": "text"},
            "owner_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "type":     {"kind": "enum", "values": ["hardware", "software", "license", "vehicle", "equipment"]},
            "status":   {"kind": "enum", "values": ["active", "decommissioned", "maintenance", "lost", "reserved"]},
        },
        "optional_pool": {
            "value":            {"kind": "number"},
            "purchased_at":     {"kind": "date"},
            "location":         {"kind": "text"},
            "serial_number":    {"kind": "text"},
            "warranty_expires": {"kind": "date"},
            "condition":        {"kind": "enum", "values": ["new", "good", "fair", "poor"]},
        },
    },

    "Report": {
        "deps": ["User"],
        "base_fields": {
            "id":        {"kind": "id"},
            "title":     {"kind": "text"},
            "author_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "type":      {"kind": "enum", "values": ["analytics", "financial", "operational", "compliance", "custom"]},
            "status":    {"kind": "enum", "values": ["draft", "published", "scheduled", "archived"]},
        },
        "optional_pool": {
            "created_at":  {"kind": "date"},
            "schedule":    {"kind": "enum", "values": ["daily", "weekly", "monthly", "quarterly", "on_demand"]},
            "is_public":   {"kind": "bool"},
            "format":      {"kind": "enum", "values": ["pdf", "csv", "html", "json"]},
            "description": {"kind": "richtext"},
            "last_run":    {"kind": "date"},
        },
    },

    "Review": {
        "deps": ["Product", "User"],
        "base_fields": {
            "id":         {"kind": "id"},
            "product_id": {"kind": "ref", "target": "Product", "cardinality": "one"},
            "author_id":  {"kind": "ref", "target": "User", "cardinality": "one"},
            "rating":     {"kind": "number"},
            "status":     {"kind": "enum", "values": ["pending", "approved", "rejected", "hidden"]},
        },
        "optional_pool": {
            "title":         {"kind": "text"},
            "body":          {"kind": "richtext"},
            "created_at":    {"kind": "date"},
            "is_verified":   {"kind": "bool"},
            "helpful_votes": {"kind": "number"},
            "response":      {"kind": "richtext"},
        },
    },

    "Server": {
        "deps": ["Environment"],
        "base_fields": {
            "id":       {"kind": "id"},
            "hostname": {"kind": "text"},
            "env_id":   {"kind": "ref", "target": "Environment", "cardinality": "one"},
            "status":   {"kind": "enum", "values": ["running", "stopped", "maintenance", "terminated"]},
            "role":     {"kind": "enum", "values": ["web", "api", "worker", "database", "cache", "proxy"]},
        },
        "optional_pool": {
            "ip_address": {"kind": "text"},
            "os":         {"kind": "text"},
            "cpu_cores":  {"kind": "number"},
            "memory_gb":  {"kind": "number"},
            "is_active":  {"kind": "bool"},
            "rack":       {"kind": "text"},
            "disk_gb":    {"kind": "number"},
        },
    },

    "Cluster": {
        "deps": ["Environment"],
        "base_fields": {
            "id":     {"kind": "id"},
            "name":   {"kind": "text"},
            "env_id": {"kind": "ref", "target": "Environment", "cardinality": "one"},
            "status": {"kind": "enum", "values": ["running", "degraded", "stopped", "provisioning"]},
        },
        "optional_pool": {
            "provider":           {"kind": "enum", "values": ["gke", "eks", "aks", "on_prem"]},
            "region":             {"kind": "text"},
            "node_count":         {"kind": "number"},
            "is_active":          {"kind": "bool"},
            "max_nodes":          {"kind": "number"},
            "kubernetes_version": {"kind": "text"},
        },
    },

    "Ticket": {
        "deps": ["User"],
        "base_fields": {
            "id":          {"kind": "id"},
            "title":       {"kind": "text"},
            "reporter_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":      {"kind": "enum", "values": ["open", "in_progress", "on_hold", "resolved", "closed"]},
            "priority":    {"kind": "enum", "values": ["low", "medium", "high", "urgent", "critical"]},
            "type":        {"kind": "enum", "values": ["bug", "feature_request", "support", "billing", "security"]},
        },
        "optional_pool": {
            "created_at":       {"kind": "date"},
            "resolved_at":      {"kind": "date"},
            "sla_breach":       {"kind": "bool"},
            "description":      {"kind": "richtext"},
            "severity":         {"kind": "enum", "values": ["sev1", "sev2", "sev3", "sev4"]},
            "assignee_name":    {"kind": "text"},
            "satisfaction_score":{"kind": "number"},
            "category":         {"kind": "text"},
        },
    },

    "Audit": {
        "deps": ["User"],
        "base_fields": {
            "id":          {"kind": "id"},
            "actor_id":    {"kind": "ref", "target": "User", "cardinality": "one"},
            "action":      {"kind": "enum", "values": ["create", "read", "update", "delete", "login", "logout", "export", "import"]},
            "entity_type": {"kind": "text"},
            "entity_id":   {"kind": "text"},
        },
        "optional_pool": {
            "created_at": {"kind": "date"},
            "ip_address": {"kind": "text"},
            "changes":    {"kind": "richtext"},
            "severity":   {"kind": "enum", "values": ["low", "medium", "high", "critical"]},
            "resource":   {"kind": "text"},
            "outcome":    {"kind": "enum", "values": ["success", "failure", "blocked"]},
        },
    },

    "Session": {
        "deps": ["User"],
        "base_fields": {
            "id":        {"kind": "id"},
            "user_id":   {"kind": "ref", "target": "User", "cardinality": "one"},
            "started_at":{"kind": "date"},
            "is_active": {"kind": "bool"},
        },
        "optional_pool": {
            "device_type": {"kind": "enum", "values": ["desktop", "mobile", "tablet", "api"]},
            "ip_address":  {"kind": "text"},
            "ended_at":    {"kind": "date"},
            "duration_s":  {"kind": "number"},
            "user_agent":  {"kind": "text"},
            "location":    {"kind": "text"},
            "mfa_used":    {"kind": "bool"},
        },
    },

    "Notification": {
        "deps": ["User"],
        "base_fields": {
            "id":           {"kind": "id"},
            "recipient_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "type":         {"kind": "enum", "values": ["email", "push", "sms", "in_app", "slack", "webhook"]},
            "title":        {"kind": "text"},
        },
        "optional_pool": {
            "body":      {"kind": "richtext"},
            "is_read":   {"kind": "bool"},
            "created_at":{"kind": "date"},
            "priority":  {"kind": "enum", "values": ["low", "normal", "high", "urgent"]},
            "link":      {"kind": "text"},
            "read_at":   {"kind": "date"},
            "channel":   {"kind": "enum", "values": ["email", "push", "sms", "in_app"]},
        },
    },

    # ================================================================
    # LAYER 2 — At least one dep is a Layer-1 entity
    # ================================================================

    "Task": {
        "deps": ["Project", "User"],
        "base_fields": {
            "id":          {"kind": "id"},
            "title":       {"kind": "text"},
            "project_id":  {"kind": "ref", "target": "Project", "cardinality": "one"},
            "assignee_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":      {"kind": "enum", "values": ["todo", "in_progress", "in_review", "done", "cancelled"]},
        },
        "optional_pool": {
            "priority":    {"kind": "enum", "values": ["low", "medium", "high", "critical"]},
            "due_date":    {"kind": "date"},
            "points":      {"kind": "number"},
            "description": {"kind": "richtext"},
            "is_blocked":  {"kind": "bool"},
            "type":        {"kind": "enum", "values": ["feature", "bug", "chore", "spike", "epic"]},
            "created_at":  {"kind": "date"},
            "tags":        {"kind": "multi_enum", "values": ["frontend", "backend", "infra", "design", "data"]},
        },
    },

    "Issue": {
        "deps": ["Project", "User"],
        "base_fields": {
            "id":          {"kind": "id"},
            "title":       {"kind": "text"},
            "project_id":  {"kind": "ref", "target": "Project", "cardinality": "one"},
            "reporter_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "assignee_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":      {"kind": "enum", "values": ["open", "in_progress", "in_review", "resolved", "closed"]},
            "type":        {"kind": "enum", "values": ["bug", "feature", "task", "epic", "chore"]},
        },
        "optional_pool": {
            "priority":      {"kind": "enum", "values": ["p0", "p1", "p2", "p3"]},
            "severity":      {"kind": "enum", "values": ["low", "medium", "high", "critical"]},
            "created_at":    {"kind": "date"},
            "resolved_at":   {"kind": "date"},
            "description":   {"kind": "richtext"},
            "is_regression": {"kind": "bool"},
            "points":        {"kind": "number"},
            "labels":        {"kind": "multi_enum", "values": ["frontend", "backend", "payments", "auth", "infra", "mobile"]},
        },
    },

    "Sprint": {
        "deps": ["Project"],
        "base_fields": {
            "id":         {"kind": "id"},
            "name":       {"kind": "text"},
            "project_id": {"kind": "ref", "target": "Project", "cardinality": "one"},
            "status":     {"kind": "enum", "values": ["planning", "active", "completed", "cancelled"]},
        },
        "optional_pool": {
            "start_date":       {"kind": "date"},
            "end_date":         {"kind": "date"},
            "velocity":         {"kind": "number"},
            "goal":             {"kind": "richtext"},
            "is_completed":     {"kind": "bool"},
            "capacity":         {"kind": "number"},
            "actual_velocity":  {"kind": "number"},
        },
    },

    "Milestone": {
        "deps": ["Project"],
        "base_fields": {
            "id":         {"kind": "id"},
            "name":       {"kind": "text"},
            "project_id": {"kind": "ref", "target": "Project", "cardinality": "one"},
            "status":     {"kind": "enum", "values": ["pending", "in_progress", "completed", "delayed", "cancelled"]},
        },
        "optional_pool": {
            "due_date":    {"kind": "date"},
            "description": {"kind": "richtext"},
            "is_completed":{"kind": "bool"},
            "progress":    {"kind": "number"},
            "priority":    {"kind": "enum", "values": ["low", "medium", "high", "critical"]},
            "owner_name":  {"kind": "text"},
        },
    },

    "Label": {
        "deps": ["Project"],
        "base_fields": {
            "id":         {"kind": "id"},
            "name":       {"kind": "text"},
            "project_id": {"kind": "ref", "target": "Project", "cardinality": "one"},
            "color":      {"kind": "text"},
        },
        "optional_pool": {
            "description": {"kind": "text"},
            "is_active":   {"kind": "bool"},
            "category":    {"kind": "enum", "values": ["type", "status", "priority", "team", "feature"]},
        },
    },

    "Feature": {
        "deps": ["Project", "User"],
        "base_fields": {
            "id":         {"kind": "id"},
            "name":       {"kind": "text"},
            "project_id": {"kind": "ref", "target": "Project", "cardinality": "one"},
            "owner_id":   {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":     {"kind": "enum", "values": ["ideation", "planned", "in_progress", "launched", "cancelled"]},
            "type":       {"kind": "enum", "values": ["enhancement", "new_feature", "improvement", "deprecation"]},
        },
        "optional_pool": {
            "priority":        {"kind": "enum", "values": ["low", "medium", "high", "critical"]},
            "description":     {"kind": "richtext"},
            "target_date":     {"kind": "date"},
            "is_breaking":     {"kind": "bool"},
            "tags":            {"kind": "multi_enum", "values": ["frontend", "backend", "api", "mobile", "platform"]},
            "impact_estimate": {"kind": "enum", "values": ["low", "medium", "high", "transformational"]},
        },
    },

    "Release": {
        "deps": ["Project"],
        "base_fields": {
            "id":         {"kind": "id"},
            "version":    {"kind": "text"},
            "project_id": {"kind": "ref", "target": "Project", "cardinality": "one"},
            "status":     {"kind": "enum", "values": ["planned", "in_progress", "released", "cancelled"]},
            "type":       {"kind": "enum", "values": ["major", "minor", "patch", "hotfix"]},
        },
        "optional_pool": {
            "released_at":   {"kind": "date"},
            "notes":         {"kind": "richtext"},
            "is_hotfix":     {"kind": "bool"},
            "changelog":     {"kind": "richtext"},
            "environment":   {"kind": "enum", "values": ["staging", "prod"]},
            "reviewer_name": {"kind": "text"},
        },
    },

    "Workflow": {
        "deps": ["Project", "User"],
        "base_fields": {
            "id":         {"kind": "id"},
            "name":       {"kind": "text"},
            "project_id": {"kind": "ref", "target": "Project", "cardinality": "one"},
            "creator_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":     {"kind": "enum", "values": ["active", "inactive", "draft", "archived"]},
            "trigger":    {"kind": "enum", "values": ["manual", "schedule", "event", "webhook"]},
        },
        "optional_pool": {
            "step_count":  {"kind": "number"},
            "last_run":    {"kind": "date"},
            "is_active":   {"kind": "bool"},
            "description": {"kind": "richtext"},
            "run_count":   {"kind": "number"},
            "schedule":    {"kind": "text"},
        },
    },

    "Employee": {
        "deps": ["Department", "User"],
        "base_fields": {
            "id":      {"kind": "id"},
            "user_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "dept_id": {"kind": "ref", "target": "Department", "cardinality": "one"},
        },
        "optional_pool": {
            "title":           {"kind": "text"},
            "level":           {"kind": "enum", "values": ["junior", "mid", "senior", "lead", "manager", "director"]},
            "salary":          {"kind": "number"},
            "hired_at":        {"kind": "date"},
            "is_active":       {"kind": "bool"},
            "employment_type": {"kind": "enum", "values": ["full_time", "part_time", "contractor", "intern"]},
            "manager_name":    {"kind": "text"},
        },
    },

    "TeamMember": {
        "deps": ["Team", "User"],
        "base_fields": {
            "id":      {"kind": "id"},
            "team_id": {"kind": "ref", "target": "Team", "cardinality": "one"},
            "user_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "role":    {"kind": "enum", "values": ["member", "lead", "admin", "observer"]},
        },
        "optional_pool": {
            "joined_at":       {"kind": "date"},
            "is_lead":         {"kind": "bool"},
            "title":           {"kind": "text"},
            "allocation_pct":  {"kind": "number"},
        },
    },

    "Channel": {
        "deps": ["Workspace", "User"],
        "base_fields": {
            "id":           {"kind": "id"},
            "name":         {"kind": "text"},
            "workspace_id": {"kind": "ref", "target": "Workspace", "cardinality": "one"},
            "creator_id":   {"kind": "ref", "target": "User", "cardinality": "one"},
            "type":         {"kind": "enum", "values": ["public", "private", "dm", "announcement"]},
        },
        "optional_pool": {
            "topic":        {"kind": "text"},
            "is_archived":  {"kind": "bool"},
            "member_count": {"kind": "number"},
            "purpose":      {"kind": "text"},
            "created_at":   {"kind": "date"},
            "last_active":  {"kind": "date"},
        },
    },

    "Deployment": {
        "deps": ["Service", "User"],
        "base_fields": {
            "id":          {"kind": "id"},
            "service_id":  {"kind": "ref", "target": "Service", "cardinality": "one"},
            "deployed_by": {"kind": "ref", "target": "User", "cardinality": "one"},
            "version":     {"kind": "text"},
            "status":      {"kind": "enum", "values": ["pending", "running", "success", "failed", "rolled_back"]},
        },
        "optional_pool": {
            "deployed_at":   {"kind": "date"},
            "duration_s":    {"kind": "number"},
            "environment":   {"kind": "enum", "values": ["dev", "staging", "prod"]},
            "is_rollback":   {"kind": "bool"},
            "notes":         {"kind": "richtext"},
            "commit_sha":    {"kind": "text"},
            "artifact_url":  {"kind": "text"},
        },
    },

    "Alert": {
        "deps": ["Service"],
        "base_fields": {
            "id":         {"kind": "id"},
            "service_id": {"kind": "ref", "target": "Service", "cardinality": "one"},
            "severity":   {"kind": "enum", "values": ["low", "medium", "high", "critical"]},
            "message":    {"kind": "text"},
            "status":     {"kind": "enum", "values": ["open", "acknowledged", "resolved", "suppressed"]},
        },
        "optional_pool": {
            "metric":        {"kind": "text"},
            "triggered_at":  {"kind": "date"},
            "is_resolved":   {"kind": "bool"},
            "resolved_at":   {"kind": "date"},
            "threshold":     {"kind": "number"},
            "runbook_url":   {"kind": "text"},
            "assignee_name": {"kind": "text"},
        },
    },

    "Pipeline": {
        "deps": ["Service"],
        "base_fields": {
            "id":         {"kind": "id"},
            "name":       {"kind": "text"},
            "service_id": {"kind": "ref", "target": "Service", "cardinality": "one"},
            "status":     {"kind": "enum", "values": ["pending", "running", "success", "failed", "cancelled"]},
            "trigger":    {"kind": "enum", "values": ["push", "pr", "schedule", "manual", "webhook"]},
        },
        "optional_pool": {
            "duration_s":   {"kind": "number"},
            "ran_at":       {"kind": "date"},
            "commit_sha":   {"kind": "text"},
            "is_successful":{"kind": "bool"},
            "branch":       {"kind": "text"},
            "environment":  {"kind": "enum", "values": ["dev", "staging", "prod"]},
            "stage":        {"kind": "enum", "values": ["build", "test", "deploy", "notify"]},
        },
    },

    "Webhook": {
        "deps": ["Service"],
        "base_fields": {
            "id":         {"kind": "id"},
            "service_id": {"kind": "ref", "target": "Service", "cardinality": "one"},
            "url":        {"kind": "text"},
            "is_active":  {"kind": "bool"},
        },
        "optional_pool": {
            "events":         {"kind": "multi_enum", "values": ["push", "pull_request", "deploy", "alert", "comment", "create", "delete"]},
            "created_at":     {"kind": "date"},
            "retry_count":    {"kind": "number"},
            "last_triggered": {"kind": "date"},
            "timeout_ms":     {"kind": "number"},
            "secret_hash":    {"kind": "text"},
        },
    },

    "ApiKey": {
        "deps": ["Service", "User"],
        "base_fields": {
            "id":         {"kind": "id"},
            "name":       {"kind": "text"},
            "service_id": {"kind": "ref", "target": "Service", "cardinality": "one"},
            "owner_id":   {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":     {"kind": "enum", "values": ["active", "revoked", "expired"]},
        },
        "optional_pool": {
            "created_at": {"kind": "date"},
            "expires_at": {"kind": "date"},
            "last_used":  {"kind": "date"},
            "scopes":     {"kind": "multi_enum", "values": ["read", "write", "admin", "webhook", "export"]},
            "description":{"kind": "text"},
        },
    },

    "OrderItem": {
        "deps": ["Order", "Product"],
        "base_fields": {
            "id":         {"kind": "id"},
            "order_id":   {"kind": "ref", "target": "Order", "cardinality": "one"},
            "product_id": {"kind": "ref", "target": "Product", "cardinality": "one"},
            "qty":        {"kind": "number"},
            "unit_price": {"kind": "number"},
        },
        "optional_pool": {
            "discount": {"kind": "number"},
            "total":    {"kind": "number"},
            "status":   {"kind": "enum", "values": ["pending", "fulfilled", "cancelled", "returned"]},
            "notes":    {"kind": "text"},
            "weight":   {"kind": "number"},
        },
    },

    "Invoice": {
        "deps": ["Order"],
        "base_fields": {
            "id":       {"kind": "id"},
            "order_id": {"kind": "ref", "target": "Order", "cardinality": "one"},
            "amount":   {"kind": "number"},
            "status":   {"kind": "enum", "values": ["draft", "sent", "paid", "overdue", "cancelled", "voided"]},
        },
        "optional_pool": {
            "tax":            {"kind": "number"},
            "issued_at":      {"kind": "date"},
            "due_date":       {"kind": "date"},
            "paid_at":        {"kind": "date"},
            "notes":          {"kind": "richtext"},
            "payment_method": {"kind": "text"},
            "currency":       {"kind": "text"},
        },
    },

    "Payment": {
        "deps": ["Order"],
        "base_fields": {
            "id":       {"kind": "id"},
            "order_id": {"kind": "ref", "target": "Order", "cardinality": "one"},
            "amount":   {"kind": "number"},
            "status":   {"kind": "enum", "values": ["pending", "completed", "failed", "refunded", "disputed"]},
            "method":   {"kind": "enum", "values": ["card", "bank_transfer", "paypal", "crypto", "wallet"]},
        },
        "optional_pool": {
            "processed_at":  {"kind": "date"},
            "transaction_id":{"kind": "text"},
            "gateway":       {"kind": "enum", "values": ["stripe", "adyen", "braintree", "paypal", "internal"]},
            "is_refund":     {"kind": "bool"},
            "failure_reason":{"kind": "text"},
            "currency":      {"kind": "text"},
        },
    },

    "Shipment": {
        "deps": ["Order"],
        "base_fields": {
            "id":       {"kind": "id"},
            "order_id": {"kind": "ref", "target": "Order", "cardinality": "one"},
            "status":   {"kind": "enum", "values": ["pending", "picked", "packed", "shipped", "in_transit", "delivered", "returned", "failed"]},
        },
        "optional_pool": {
            "carrier":            {"kind": "text"},
            "tracking_number":    {"kind": "text"},
            "shipped_at":         {"kind": "date"},
            "estimated_delivery": {"kind": "date"},
            "weight":             {"kind": "number"},
            "cost":               {"kind": "number"},
            "origin_city":        {"kind": "text"},
            "dest_city":          {"kind": "text"},
        },
    },

    "Enrollment": {
        "deps": ["Course", "User"],
        "base_fields": {
            "id":         {"kind": "id"},
            "course_id":  {"kind": "ref", "target": "Course", "cardinality": "one"},
            "student_id": {"kind": "ref", "target": "User", "cardinality": "one"},
            "status":     {"kind": "enum", "values": ["active", "completed", "dropped", "pending"]},
        },
        "optional_pool": {
            "enrolled_at":        {"kind": "date"},
            "progress":           {"kind": "number"},
            "is_completed":       {"kind": "bool"},
            "score":              {"kind": "number"},
            "completion_date":    {"kind": "date"},
            "certificate_issued": {"kind": "bool"},
        },
    },

    "Comment": {
        "deps": ["Article", "User"],
        "base_fields": {
            "id":         {"kind": "id"},
            "body":       {"kind": "richtext"},
            "article_id": {"kind": "ref", "target": "Article", "cardinality": "one"},
            "author_id":  {"kind": "ref", "target": "User", "cardinality": "one"},
        },
        "optional_pool": {
            "created_at": {"kind": "date"},
            "is_approved":{"kind": "bool"},
            "upvotes":    {"kind": "number"},
            "is_flagged": {"kind": "bool"},
            "reply_count":{"kind": "number"},
            "status":     {"kind": "enum", "values": ["pending", "approved", "rejected"]},
        },
    },

    "Opportunity": {
        "deps": ["Account", "User"],
        "base_fields": {
            "id":         {"kind": "id"},
            "name":       {"kind": "text"},
            "account_id": {"kind": "ref", "target": "Account", "cardinality": "one"},
            "owner_id":   {"kind": "ref", "target": "User", "cardinality": "one"},
            "stage":      {"kind": "enum", "values": ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]},
            "value":      {"kind": "number"},
        },
        "optional_pool": {
            "close_date":  {"kind": "date"},
            "probability": {"kind": "number"},
            "is_won":      {"kind": "bool"},
            "notes":       {"kind": "richtext"},
            "type":        {"kind": "enum", "values": ["new_business", "expansion", "renewal", "upsell"]},
            "source":      {"kind": "enum", "values": ["inbound", "outbound", "referral", "partner"]},
        },
    },

    "Document": {
        "deps": ["Workspace", "User"],
        "base_fields": {
            "id":           {"kind": "id"},
            "title":        {"kind": "text"},
            "workspace_id": {"kind": "ref", "target": "Workspace", "cardinality": "one"},
            "author_id":    {"kind": "ref", "target": "User", "cardinality": "one"},
            "type":         {"kind": "enum", "values": ["policy", "runbook", "spec", "design_doc", "adr", "meeting_notes", "onboarding"]},
            "status":       {"kind": "enum", "values": ["draft", "review", "approved", "published", "archived"]},
        },
        "optional_pool": {
            "version":       {"kind": "number"},
            "created_at":    {"kind": "date"},
            "content":       {"kind": "richtext"},
            "is_template":   {"kind": "bool"},
            "is_public":     {"kind": "bool"},
            "word_count":    {"kind": "number"},
            "last_reviewed": {"kind": "date"},
        },
    },

    # ================================================================
    # LAYER 3 — Deps include at least one Layer-2 entity
    # ================================================================

    "Incident": {
        "deps": ["Alert", "Environment"],
        "base_fields": {
            "id":           {"kind": "id"},
            "alert_id":     {"kind": "ref", "target": "Alert", "cardinality": "one"},
            "env_id":       {"kind": "ref", "target": "Environment", "cardinality": "one"},
            "title":        {"kind": "text"},
            "status":       {"kind": "enum", "values": ["open", "investigating", "mitigated", "resolved", "postmortem"]},
            "severity":     {"kind": "enum", "values": ["sev1", "sev2", "sev3", "sev4"]},
        },
        "optional_pool": {
            "opened_at":      {"kind": "date"},
            "resolved_at":    {"kind": "date"},
            "impact_score":   {"kind": "number"},
            "postmortem":     {"kind": "richtext"},
            "root_cause":     {"kind": "text"},
            "affected_users": {"kind": "number"},
            "downtime_min":   {"kind": "number"},
        },
    },

    "Grade": {
        "deps": ["Enrollment"],
        "base_fields": {
            "id":            {"kind": "id"},
            "enrollment_id": {"kind": "ref", "target": "Enrollment", "cardinality": "one"},
            "score":         {"kind": "number"},
            "max_score":     {"kind": "number"},
        },
        "optional_pool": {
            "graded_at":    {"kind": "date"},
            "feedback":     {"kind": "richtext"},
            "is_passing":   {"kind": "bool"},
            "letter_grade": {"kind": "text"},
            "grader_name":  {"kind": "text"},
        },
    },
}


# ---------------------------------------------------------------------------
# Schema builder — shared by both tiers
# ---------------------------------------------------------------------------

def _build_schema(target_range, blocks_range, field_density):
    """
    target_range   — (min, max) entity count
    blocks_range   — (min, max) nested block count
    field_density  — "medium" (Tier 2) or "high" (Tier 3)
    """
    target = random.randint(*target_range)

    # Always seed with User — it's the most-connected root and ensures
    # a rich candidate pool in every schema.
    roots = [n for n, s in _ENTITY_CATALOG.items() if not s["deps"]]
    other_roots = [r for r in roots if r != "User"]
    n_extra = min(random.randint(1, 2), len(other_roots))
    placed = {"User"} | set(random.sample(other_roots, n_extra))

    # Greedy expansion: repeatedly add a candidate whose deps are all placed.
    # Tier 3 biases toward multi-dep entities to create denser cross-connections.
    while len(placed) < target:
        candidates = [
            name for name, spec in _ENTITY_CATALOG.items()
            if name not in placed
            and all(dep in placed for dep in spec["deps"])
        ]
        if not candidates:
            break

        if field_density == "high":
            multi = [c for c in candidates if len(_ENTITY_CATALOG[c]["deps"]) >= 2]
            if multi and random.random() < 0.70:
                placed.add(random.choice(multi))
                continue

        placed.add(random.choice(candidates))

    # Build entity field dicts, sampling optional fields by density.
    entities = {}
    for name in placed:
        spec = _ENTITY_CATALOG[name]
        fields = copy.deepcopy(spec["base_fields"])
        pool = spec.get("optional_pool", {})
        if pool:
            if field_density == "high":
                lo = max(1, len(pool) * 2 // 3)
            else:
                lo = 1
            n_opt = random.randint(lo, len(pool))
            for fname in random.sample(list(pool.keys()), n_opt):
                fields[fname] = copy.deepcopy(pool[fname])
        entities[name] = {"fields": fields}

    # Attach nested blocks — one block per entity, prefer unused entities.
    n_blocks = random.randint(*blocks_range)
    block_names = random.sample(list(_NESTED_BLOCKS.keys()), min(n_blocks, len(_NESTED_BLOCKS)))
    nested_blocks = {bn: copy.deepcopy(_NESTED_BLOCKS[bn]) for bn in block_names}

    entity_list = list(entities.keys())
    used: set = set()
    for block_name in block_names:
        available = [e for e in entity_list if e not in used]
        if not available:
            available = entity_list
        host = random.choice(available)
        used.add(host)
        field_name = _NESTED_FIELD_NAMES.get(block_name, block_name.lower().replace("block", "") + "s")
        entities[host]["fields"][field_name] = {"kind": "nested", "of": block_name}

    return {"entities": entities, "nested_blocks": nested_blocks}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_schema(tier):
    """Return a fresh source schema dict for the given difficulty tier.

    Tier 2 — 6–10 entities, greedy dense ref web, 2–3 nested blocks.
    Tier 3 — 8–12 entities, same pool with denser cross-connections,
              more optional fields included, 3–4 nested blocks.
    """
    if tier == 2:
        return _build_schema(
            target_range=(6, 10),
            blocks_range=(2, 3),
            field_density="medium",
        )
    if tier == 3:
        return _build_schema(
            target_range=(8, 12),
            blocks_range=(3, 4),
            field_density="high",
        )
    raise NotImplementedError(f"get_schema: tier {tier} is not implemented")
