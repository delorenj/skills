# Patterns: Python Code Node

Copy-paste-ready Python patterns for n8n Code nodes. Each pattern has a stated use case, a complete snippet, and the key techniques it demonstrates. All snippets assume Python (Beta) mode and the default "Run Once for All Items" mode unless otherwise noted.

Before reaching for any of these, confirm Python is actually the right choice for the task (see [README.md](./README.md)). For symbol-level reference, see [api.md](./api.md). For failure modes, see [gotchas.md](./gotchas.md).

---

## Pattern Index

| Pattern | When to Use |
|---------|-------------|
| [1. Process All Items](#pattern-1-process-all-items-with-_inputall) | Default batch processing |
| [2. Process First Item](#pattern-2-process-first-item-with-_inputfirst) | Single-object API response, single webhook |
| [3. Process Each Item](#pattern-3-process-each-item-with-_inputitem) | Per-item logic in Each Item mode |
| [4. Reference Another Node](#pattern-4-reference-another-node-with-_node) | Combining outputs from named nodes |
| [5. Read a Webhook Payload](#pattern-5-read-a-webhook-payload) | Anything coming from a Webhook trigger |
| [6. Multi-Source Data Aggregation](#pattern-6-multi-source-data-aggregation) | Combining data from multiple upstream sources |
| [7. Regex-Based Filtering](#pattern-7-regex-based-filtering) | Tagging or filtering by keyword patterns |
| [8. Markdown to Structured Data](#pattern-8-markdown-to-structured-data) | Parsing markdown checklists or notes |
| [9. JSON Object Diff](#pattern-9-json-object-diff) | Detecting added, removed, and modified fields |
| [10. CRM Data Normalization](#pattern-10-crm-data-normalization) | Merging contacts from different shapes |
| [11. Release Notes Categorization](#pattern-11-release-notes-categorization) | Parsing release notes into features/fixes/breaking |
| [12. Array Reshape and Field Extraction](#pattern-12-array-reshape-and-field-extraction) | Flattening nested objects |
| [13. Dictionary Lookup Table](#pattern-13-dictionary-lookup-table) | Fast O(1) ID-based lookups |
| [14. Top-N by Score](#pattern-14-top-n-by-score) | Top performers, top sellers |
| [15. String Aggregation](#pattern-15-string-aggregation) | Building a formatted text summary |
| [16. Statistical Aggregation](#pattern-16-statistical-aggregation) | mean, median, stdev across input items |
| [17. Group-By](#pattern-17-group-by-with-defaultdict) | Bucketing items by a key |
| [18. Deduplicate by Key](#pattern-18-deduplicate-by-key) | Remove duplicates by id, email, etc. |
| [19. Hash-Based Unique ID](#pattern-19-hash-based-unique-id) | Stable derived IDs from input fields |
| [20. Safe Nested Access](#pattern-20-safe-nested-access) | Deep `.get()` chains that never raise |

---

## Pattern 1: Process All Items with `_input.all()`

The default mode for Python Code nodes. Use this for batch operations, aggregations, filtering, sorting.

```python
all_items = _input.all()

# Filter only active items
active_items = [
    item for item in all_items
    if item["json"].get("status") == "active"
]

return active_items
```

Transform shape:

```python
from datetime import datetime

all_items = _input.all()
transformed = []
for item in all_items:
    transformed.append({
        "json": {
            "id": item["json"].get("id"),
            "full_name": f"{item['json'].get('first_name', '')} {item['json'].get('last_name', '')}",
            "email": item["json"].get("email"),
            "processed_at": datetime.now().isoformat()
        }
    })

return transformed
```

Key techniques: list comprehension for filtering, dict unpacking for transformation, `.get()` with defaults.

---

## Pattern 2: Process First Item with `_input.first()`

Use when the previous node produces a single object (most API responses, single-record webhooks).

```python
from datetime import datetime

response = _input.first()["json"]

return [{
    "json": {
        "user_id": response.get("data", {}).get("user", {}).get("id"),
        "user_name": response.get("data", {}).get("user", {}).get("name"),
        "status": response.get("status"),
        "fetched_at": datetime.now().isoformat()
    }
}]
```

Restructure a single object into a nested shape:

```python
data = _input.first()["json"]

return [{
    "json": {
        "id": data.get("id"),
        "contact": {
            "email": data.get("email"),
            "phone": data.get("phone")
        },
        "address": {
            "street": data.get("street"),
            "city": data.get("city"),
            "zip": data.get("zip")
        }
    }
}]
```

Key techniques: chained `.get({}, {})` for safe nested access, restructuring a flat object into nested groups.

---

## Pattern 3: Process Each Item with `_input.item`

Only valid in "Run Once for Each Item" mode (see [configuration.md](./configuration.md)). The code body runs once per input item; n8n collects the returns.

```python
from datetime import datetime

item = _input.item

return [{
    "json": {
        **item["json"],
        "processed": True,
        "processed_at": datetime.now().isoformat()
    }
}]
```

Per-item validation:

```python
item = _input.item
data = item["json"]

errors = []
if not data.get("email"):
    errors.append("Email required")
if not data.get("name"):
    errors.append("Name required")
if data.get("age") and data["age"] < 18:
    errors.append("Must be 18+")

return [{
    "json": {
        **data,
        "valid": len(errors) == 0,
        "errors": errors if errors else None
    }
}]
```

Conditional branch:

```python
item = _input.item
data = item["json"]

if data.get("type") == "premium":
    return [{"json": {**data, "discount": 0.20, "tier": "premium"}}]
else:
    return [{"json": {**data, "discount": 0.05, "tier": "standard"}}]
```

---

## Pattern 4: Reference Another Node with `_node`

Combine outputs from named nodes. Note the `.first()` form, which is more reliable than direct subscripting (see [gotchas.md](./gotchas.md)).

```python
from datetime import datetime

webhook = _node["Webhook"]["json"]
api = _node["HTTP Request"]["json"]
db = _node["Postgres"]["json"]

return [{
    "json": {
        "combined": {
            "webhook": webhook.get("body", {}),
            "db_records": len(db) if isinstance(db, list) else 1,
            "api_status": api.get("status")
        },
        "processed_at": datetime.now().isoformat()
    }
}]
```

Compare across nodes:

```python
old = _node["Get Old Data"]["json"]
new = _node["Get New Data"]["json"]

old_ids = [o.get("id") for o in old]
new_ids = [n.get("id") for n in new]

changes = {
    "added": [n for n in new if n.get("id") not in old_ids],
    "removed": [o for o in old if o.get("id") not in new_ids]
}

return [{
    "json": {
        "changes": changes,
        "summary": {
            "added": len(changes["added"]),
            "removed": len(changes["removed"])
        }
    }
}]
```

Reliable shape:

```python
# Safer than _node["HTTP Request"]["json"]
data = _node["HTTP Request"].first()["json"]
```

---

## Pattern 5: Read a Webhook Payload

The single most common Python Code node mistake is forgetting that webhook payloads are nested under `body`. See [gotchas.md](./gotchas.md) entry 7.

```python
from datetime import datetime

webhook_output = _input.first()["json"]
payload = webhook_output.get("body", {})

content_type = webhook_output.get("headers", {}).get("content-type")
api_key = webhook_output.get("query", {}).get("api_key")

return [{
    "json": {
        "user_name": payload.get("name"),
        "user_email": payload.get("email"),
        "message": payload.get("message"),
        "received_at": datetime.now().isoformat(),
        "content_type": content_type,
        "authenticated": bool(api_key)
    }
}]
```

Full surface:

```python
webhook = _input.first()["json"]

return [{
    "json": {
        "form_data": webhook.get("body", {}),
        "query_params": webhook.get("query", {}),
        "user_agent": webhook.get("headers", {}).get("user-agent"),
        "content_type": webhook.get("headers", {}).get("content-type"),
        "method": webhook.get("method"),
        "url": webhook.get("url")
    }
}]
```

---

## Pattern 6: Multi-Source Data Aggregation

Combine items from multiple upstream sources (different APIs, different webhooks, different databases) into a single normalized list.

```python
from datetime import datetime

all_items = _input.all()
processed_articles = []

for item in all_items:
    source_name = item["json"].get("name", "Unknown")
    source_data = item["json"]

    # Hacker News shape
    if source_name == "Hacker News" and source_data.get("hits"):
        for hit in source_data["hits"]:
            processed_articles.append({
                "title": hit.get("title", "No title"),
                "url": hit.get("url", ""),
                "summary": hit.get("story_text") or "No summary",
                "source": "Hacker News",
                "score": hit.get("points", 0),
                "fetched_at": datetime.now().isoformat()
            })

    # Reddit shape
    elif source_name == "Reddit" and source_data.get("data"):
        for post in source_data["data"].get("children", []):
            post_data = post.get("data", {})
            processed_articles.append({
                "title": post_data.get("title", "No title"),
                "url": post_data.get("url", ""),
                "summary": post_data.get("selftext", "")[:200],
                "source": "Reddit",
                "score": post_data.get("score", 0),
                "fetched_at": datetime.now().isoformat()
            })

processed_articles.sort(key=lambda x: x["score"], reverse=True)

return [{"json": article} for article in processed_articles]
```

Key techniques: branching by source identifier, normalizing different shapes to a single schema, sorting by a common field.

---

## Pattern 7: Regex-Based Filtering

Filter and tag items by keyword pattern. This is one of the cases where Python's regex idioms are arguably nicer than JavaScript's.

```python
import re

all_items = _input.all()
priority_tickets = []

high_priority_pattern = re.compile(
    r'\b(urgent|critical|emergency|asap|down|outage|broken)\b',
    re.IGNORECASE
)

for item in all_items:
    ticket = item["json"]
    combined = f"{ticket.get('subject', '')} {ticket.get('description', '')}"
    matches = high_priority_pattern.findall(combined)

    priority_tickets.append({
        "json": {
            **ticket,
            "priority": "high" if matches else "normal",
            "matched_keywords": list(set(matches)),
            "keyword_count": len(matches)
        }
    })

priority_tickets.sort(key=lambda x: x["json"]["keyword_count"], reverse=True)
return priority_tickets
```

Key techniques: `re.compile` for reusable patterns, `re.IGNORECASE`, concatenated text fields, sort by match count.

---

## Pattern 8: Markdown to Structured Data

Parse a markdown checklist into a structured task list.

```python
import re

markdown_text = _input.first()["json"]["body"].get("markdown", "")

tasks = []
for line in markdown_text.split("\n"):
    m = re.match(r'^\s*-\s*\[([ x])\]\s*(.+)$', line, re.IGNORECASE)
    if not m:
        continue

    checked = m.group(1).lower() == 'x'
    task_text = m.group(2).strip()

    priority_match = re.search(r'\[(P\d|HIGH|MEDIUM|LOW)\]', task_text, re.IGNORECASE)
    priority = priority_match.group(1).upper() if priority_match else "NORMAL"

    clean_text = re.sub(r'\[(P\d|HIGH|MEDIUM|LOW)\]', '', task_text, flags=re.IGNORECASE).strip()

    tasks.append({
        "text": clean_text,
        "completed": checked,
        "priority": priority,
        "original_line": line.strip()
    })

return [{
    "json": {
        "tasks": tasks,
        "total": len(tasks),
        "completed": sum(1 for t in tasks if t["completed"]),
        "pending": sum(1 for t in tasks if not t["completed"])
    }
}]
```

Key techniques: line-by-line parsing, layered regex extraction (checkbox -> priority tag -> clean text), summary statistics in a single return.

---

## Pattern 9: JSON Object Diff

Compare two JSON objects and categorize the differences.

```python
all_items = _input.all()
old_data = all_items[0]["json"] if len(all_items) > 0 else {}
new_data = all_items[1]["json"] if len(all_items) > 1 else {}

changes = {"added": {}, "removed": {}, "modified": {}, "unchanged": {}}

for key in set(old_data.keys()) | set(new_data.keys()):
    old_value = old_data.get(key)
    new_value = new_data.get(key)

    if key not in old_data:
        changes["added"][key] = new_value
    elif key not in new_data:
        changes["removed"][key] = old_value
    elif old_value != new_value:
        changes["modified"][key] = {"old": old_value, "new": new_value}
    else:
        changes["unchanged"][key] = old_value

return [{
    "json": {
        "changes": changes,
        "summary": {
            "added_count": len(changes["added"]),
            "removed_count": len(changes["removed"]),
            "modified_count": len(changes["modified"]),
            "unchanged_count": len(changes["unchanged"]),
            "has_changes": (
                len(changes["added"]) > 0
                or len(changes["removed"]) > 0
                or len(changes["modified"]) > 0
            )
        }
    }
}]
```

Key techniques: set union for key coverage, categorical bucketing, summary booleans.

---

## Pattern 10: CRM Data Normalization

Normalize contact records from different CRM systems into a single shape.

```python
import re
from datetime import datetime

all_items = _input.all()
normalized = []

for item in all_items:
    raw = item["json"]
    source = raw.get("source", "unknown")

    email = raw.get("email", "").lower().strip()
    phone = re.sub(r'\D', '', raw.get("phone", ""))

    if "full_name" in raw:
        parts = raw["full_name"].split(" ", 1)
        first_name = parts[0] if len(parts) > 0 else ""
        last_name = parts[1] if len(parts) > 1 else ""
    else:
        first_name = raw.get("first_name", "")
        last_name = raw.get("last_name", "")

    status_raw = raw.get("status", "").lower()
    status = "active" if status_raw in ("active", "enabled", "true", "1") else "inactive"

    normalized.append({
        "json": {
            "id": raw.get("id", ""),
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "full_name": f"{first_name} {last_name}".strip(),
            "email": email,
            "phone": phone,
            "status": status,
            "source": source,
            "normalized_at": datetime.now().isoformat(),
            "original_data": raw
        }
    })

return normalized
```

Key techniques: regex to strip non-digits from phone numbers, fallback name parsing, status whitelist, preservation of original data alongside the normalized form.

---

## Pattern 11: Release Notes Categorization

Parse release notes and bucket lines by keyword.

```python
import re

release_notes = _input.first()["json"]["body"].get("notes", "")

categories = {"features": [], "fixes": [], "breaking": [], "other": []}

for line in release_notes.split("\n"):
    line = line.strip()
    if not line or line.startswith("#"):
        continue

    clean = re.sub(r'^[\*\-\+]\s*', '', line)

    if re.search(r'\b(feature|add|new)\b', clean, re.IGNORECASE):
        categories["features"].append(clean)
    elif re.search(r'\b(fix|bug|patch|resolve)\b', clean, re.IGNORECASE):
        categories["fixes"].append(clean)
    elif re.search(r'\b(breaking|deprecated|remove)\b', clean, re.IGNORECASE):
        categories["breaking"].append(clean)
    else:
        categories["other"].append(clean)

return [{
    "json": {
        "categories": categories,
        "summary": {
            "features": len(categories["features"]),
            "fixes": len(categories["fixes"]),
            "breaking": len(categories["breaking"]),
            "other": len(categories["other"]),
            "total": sum(len(v) for v in categories.values())
        }
    }
}]
```

Key techniques: skip headers and blanks, strip bullet markers, fall-through keyword buckets.

---

## Pattern 12: Array Reshape and Field Extraction

Flatten nested objects into a flat shape for downstream consumers.

```python
all_items = _input.all()
transformed = []

for item in all_items:
    user = item["json"]
    profile = user.get("profile", {})
    settings = user.get("settings", {})

    transformed.append({
        "json": {
            "user_id": user.get("id"),
            "email": user.get("email"),
            "name": profile.get("name", "Unknown"),
            "avatar": profile.get("avatar_url"),
            "bio": profile.get("bio", "")[:100],
            "notifications_enabled": settings.get("notifications", True),
            "theme": settings.get("theme", "light"),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login_at")
        }
    })

return transformed
```

Key techniques: layered `.get()` extraction, slicing for truncation, flattening profile + settings into top-level fields.

---

## Pattern 13: Dictionary Lookup Table

Build an in-memory lookup table for fast O(1) access by ID.

```python
all_items = _input.all()

users_by_id = {}
for item in all_items:
    user = item["json"]
    uid = user.get("id")
    if uid:
        users_by_id[uid] = {
            "name": user.get("name"),
            "email": user.get("email"),
            "status": user.get("status")
        }

# Use the lookup
lookup_ids = [1, 3, 5]
looked_up = []
for uid in lookup_ids:
    if uid in users_by_id:
        looked_up.append({"json": {"id": uid, **users_by_id[uid], "found": True}})
    else:
        looked_up.append({"json": {"id": uid, "found": False}})

return looked_up
```

Key techniques: index by primary key, present/absent marker via boolean.

---

## Pattern 14: Top-N by Score

Get the top N items by some numeric field, with rank attached.

```python
all_items = _input.all()

products = [
    {
        "id": item["json"].get("id"),
        "name": item["json"].get("name"),
        "sales": item["json"].get("sales", 0),
        "revenue": item["json"].get("revenue", 0.0),
        "category": item["json"].get("category")
    }
    for item in all_items
]

products.sort(key=lambda p: p["sales"], reverse=True)
top_10 = products[:10]

return [
    {"json": {**product, "rank": index + 1}}
    for index, product in enumerate(top_10)
]
```

Key techniques: sort key via lambda, slice for top N, `enumerate` to add ranks.

---

## Pattern 15: String Aggregation

Build a single formatted text summary from many items.

```python
all_items = _input.all()
messages = []

for item in all_items:
    data = item["json"]
    user = data.get("user", "Unknown")
    message = data.get("message", "")
    timestamp = data.get("timestamp", "")
    messages.append(f"[{timestamp}] {user}: {message}")

summary = "\n".join(messages)
total_length = sum(len(msg) for msg in messages)
average_length = total_length / len(messages) if messages else 0

return [{
    "json": {
        "summary": summary,
        "message_count": len(messages),
        "total_characters": total_length,
        "average_length": round(average_length, 2)
    }
}]
```

Key techniques: f-string templating, `"\n".join`, guarded average against empty list.

---

## Pattern 16: Statistical Aggregation

The headline Python use case. `mean`, `median`, `stdev`, `variance` in one snippet.

```python
import statistics

all_items = _input.all()
amounts = [item["json"].get("amount", 0) for item in all_items]

if not amounts:
    return [{"json": {"error": "No data"}}]

return [{
    "json": {
        "count": len(amounts),
        "total": sum(amounts),
        "average": statistics.mean(amounts),
        "median": statistics.median(amounts),
        "stdev": statistics.stdev(amounts) if len(amounts) > 1 else 0,
        "variance": statistics.variance(amounts) if len(amounts) > 1 else 0,
        "min": min(amounts),
        "max": max(amounts),
        "range": max(amounts) - min(amounts)
    }
}]
```

Key techniques: empty-list guard, `stdev`/`variance` guarded against n=1.

---

## Pattern 17: Group-By with `defaultdict`

Bucket items by a key without manual key-exists checks.

```python
from collections import defaultdict

all_items = _input.all()
grouped = defaultdict(list)

for item in all_items:
    category = item["json"].get("category", "Uncategorized")
    grouped[category].append(item["json"])

return [
    {"json": {"category": cat, "items": items, "count": len(items)}}
    for cat, items in grouped.items()
]
```

Key techniques: `defaultdict(list)` removes the "if key not in dict" boilerplate.

---

## Pattern 18: Deduplicate by Key

Remove duplicates while preserving order.

```python
all_items = _input.all()
seen = set()
unique = []

for item in all_items:
    item_id = item["json"].get("id")
    if item_id and item_id not in seen:
        seen.add(item_id)
        unique.append(item)

return unique
```

Key techniques: `set` for O(1) membership, order preservation via list.

---

## Pattern 19: Hash-Based Unique ID

Derive a stable ID from input fields using `hashlib`.

```python
import hashlib
from datetime import datetime

seed = f"{datetime.now().isoformat()}-{_json.get('user_id', 'unknown')}"
unique_id = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]

return [{
    "json": {
        "id": unique_id,
        "generated_at": datetime.now().isoformat()
    }
}]
```

Key techniques: deterministic seed string, truncated hex digest for a short ID.

---

## Pattern 20: Safe Nested Access

For dictionaries with optional nested structures.

```python
value = (
    _input.first()["json"]
    .get("level1", {})
    .get("level2", {})
    .get("level3", "default")
)
```

Combined with list/dict comprehension and filtering:

```python
items = _input.all()

result = [
    {
        "json": {
            "id": item["json"]["id"],
            "name": item["json"]["name"].upper()
        }
    }
    for item in items
    if item["json"].get("active") and item["json"].get("verified")
]

return result
```

---

## Python vs JavaScript: Side-by-Side

Reference table for translating between languages.

### Data access

```python
# Python
all_items = _input.all()
first_item = _input.first()
current = _input.item
webhook_data = _json["body"]
```

```javascript
// JavaScript
const allItems = $input.all();
const firstItem = $input.first();
const current = $input.item;
const webhookData = $json.body;
```

### Safe property access

```python
# Python
name = user["name"]            # may raise KeyError
name = user.get("name", "?")   # safe with default
```

```javascript
// JavaScript
const name = user.name;          // may be undefined
const name = user.name ?? "?";   // safe with default
```

### Filtering an array

```python
# Python
filtered = [item for item in items if item["active"]]
```

```javascript
// JavaScript
const filtered = items.filter((item) => item.active);
```

### Sorting

```python
# Python
items.sort(key=lambda x: x["score"], reverse=True)
```

```javascript
// JavaScript
items.sort((a, b) => b.score - a.score);
```

---

## Best Practices Cross-Cutting All Patterns

1. Always use `.get()` for dict access, with a sensible default. Saves you from `KeyError`. See [gotchas.md](./gotchas.md) entry 3.
2. Handle empty lists explicitly. `if not items: return []` before any `[0]` access. See [gotchas.md](./gotchas.md) entry 4.
3. Prefer list comprehensions over manual `append` loops when the body is a simple expression.
4. Return `[{"json": {...}}]`, always. Empty result is `[]`, not `None`. See [gotchas.md](./gotchas.md) entry 5.
5. Use standard library only. If you find yourself wanting `requests` or `pandas`, switch to JavaScript or use a dedicated n8n node. See [gotchas.md](./gotchas.md) entry 1.
6. Debug with `print()`. Output shows in the browser console (F12) and in execution logs.

---

## See Also

- [README.md](./README.md), the JavaScript-first recommendation, decision tree, and quick start.
- [api.md](./api.md), the symbol-by-symbol reference for everything used in these patterns.
- [gotchas.md](./gotchas.md), the failure modes that these patterns are designed to avoid.
- [configuration.md](./configuration.md), mode selection (which patterns require "Each Item" mode vs "All Items" mode).
- [../code-javascript/](../code-javascript/), for the JavaScript equivalents of these patterns. Recommended for 95 percent of cases.
- [../expressions/](../expressions/), if you can do it inline with `{{ }}` and avoid the Code node entirely.
- [../workflow-patterns/](../workflow-patterns/), for end-to-end workflows that use Code nodes in context.
