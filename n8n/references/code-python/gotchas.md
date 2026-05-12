# Gotchas: Python Code Node

Failure modes specific to Python in n8n Code nodes. Each entry follows a four-part structure: symptom, cause, solution, and a bad/good code pair. Read this file end-to-end before deploying a Python Code node, and consult it first when an existing one breaks.

Top failure modes, ordered by frequency:

1. `ModuleNotFoundError` from importing an external library (Python-specific, most critical)
2. Empty output or missing `return` statement
3. `KeyError` from direct dict access without `.get()`
4. `IndexError` from `[0]` on an empty list
5. Incorrect return format (`None`, plain dict, wrong wrapper)
6. `AttributeError` from `_input.item` in the wrong mode
7. Webhook payload nested under `body`, accessed directly instead

---

## Gotcha 1: `ModuleNotFoundError` (the Python-specific one)

### Symptom

```
ModuleNotFoundError: No module named 'requests'
```

Variants: `pandas`, `numpy`, `bs4`, `pymongo`, `psycopg2`, `selenium`, `openpyxl`, anything outside the Python standard library.

### Cause

n8n's Python sandbox ships only the Python standard library. There is no `pip install` at runtime, and there is no way to add packages from inside a Code node. Python in n8n is a stripped-down execution environment, not a full Python interpreter with the PyPI ecosystem.

### Solution

Pick one of three recovery paths, in order of preference:

1. Switch to JavaScript and use `$helpers.httpRequest()` (the recommended path for 95 percent of cases). See [../code-javascript/](../code-javascript/).
2. Put a dedicated n8n node upstream of the Code node (HTTP Request, Postgres, MongoDB, HTML Extract, Spreadsheet File) and process its output in Python.
3. If the need is HTTP-only and modest, use `urllib.request` from the standard library. No retries, no convenience methods, no auth handling, but it works for simple GETs.

Replacement table:

| Need | NOT available | Use instead |
|------|---------------|-------------|
| HTTP requests | `requests` | HTTP Request node, or JavaScript with `$helpers.httpRequest()`, or `urllib.request.urlopen` |
| Data analysis | `pandas` | List comprehensions, `statistics`, group-by with `collections.defaultdict` |
| Numerical computing | `numpy` | `math`, `statistics`, plain lists |
| Database driver | `psycopg2`, `pymongo`, `sqlalchemy` | n8n Postgres / MySQL / MongoDB nodes |
| HTML parsing | `bs4`, `lxml` | HTML Extract node, or JavaScript with regex |
| Excel | `openpyxl`, `xlsxwriter` | Spreadsheet File node |
| Image processing | `pillow` | External API or dedicated node |

### Bad / Good

```python
# BAD: External library, will crash
import requests
response = requests.get("https://api.example.com/data")
return [{"json": response.json()}]
```

```python
# GOOD (option 1, recommended): Put HTTP Request node before Code node
response = _input.first()["json"]
return [{
    "json": {
        "status": response.get("status"),
        "data": response.get("body"),
        "processed": True
    }
}]
```

```python
# GOOD (option 2, no upstream node needed but austere): urllib
from urllib.request import urlopen
import json

with urlopen("https://api.example.com/data") as response:
    data = json.loads(response.read())

return [{"json": data}]
```

```javascript
// BEST (option 3, switch to JavaScript)
const response = await $helpers.httpRequest({
  method: 'GET',
  url: 'https://api.example.com/data'
});
return [{json: response}];
```

---

## Gotcha 2: Empty Code or Missing `return`

### Symptom

The node outputs nothing, or the workflow errors with "No data was returned" or similar. Downstream nodes see no items.

### Cause

The Code node body either has no `return` statement at all, or the return is inside a conditional branch that did not execute on this run. n8n requires every code path to terminate in a `return` of the correct shape.

### Solution

Audit every branch of the function. Add an unconditional terminal `return` at the bottom. If you have early returns inside `if` blocks, make sure the fallthrough case also returns something (often `return []` or `return [{"json": {"error": "..."}}]`).

### Bad / Good

```python
# BAD: No return
items = _input.all()
processed = [item for item in items if item["json"].get("active")]
# Forgot to return!
```

```python
# BAD: Return only in one branch
items = _input.all()
if items:
    return [{"json": {"count": len(items)}}]
# Implicit None return if items is empty -> wrong shape
```

```python
# GOOD: Unconditional terminal return
items = _input.all()
if not items:
    return [{"json": {"error": "No items"}}]

processed = [item for item in items if item["json"].get("active")]
return processed if processed else [{"json": {"message": "No active items"}}]
```

---

## Gotcha 3: `KeyError` on Dict Access

### Symptom

```
KeyError: 'name'
```

Surfaces on a line like `item["json"]["name"]` or `_json["body"]["email"]`.

### Cause

Direct bracket access on a Python dict raises `KeyError` when the key is missing. Webhook payloads, partial API responses, and items with optional fields all guarantee this happens eventually.

### Solution

Use `.get(key, default)` for every dict access where the key might be absent. For nested dicts, chain `.get(key, {})` so each intermediate level produces an empty dict that the next `.get()` can safely operate on.

### Bad / Good

```python
# BAD: Direct access, will KeyError on missing field
item = _input.first()["json"]
name = item["name"]
email = item["email"]
age = item["age"]

return [{"json": {"name": name, "email": email, "age": age}}]
```

```python
# GOOD: .get() with defaults
item = _input.first()["json"]
name = item.get("name", "Unknown")
email = item.get("email", "no-email@example.com")
age = item.get("age", 0)

return [{"json": {"name": name, "email": email, "age": age}}]
```

```python
# GOOD: Chained .get() for nested access
webhook = _input.first()["json"]
name = (
    webhook
    .get("body", {})
    .get("user", {})
    .get("name", "Unknown")
)
return [{"json": {"name": name}}]
```

---

## Gotcha 4: `IndexError` on List Access

### Symptom

```
IndexError: list index out of range
```

Triggered by `_input.all()[0]`, `items[1]`, or any unguarded indexing on a list that turns out to be empty or shorter than expected.

### Cause

The previous node returned zero items, or fewer items than the code assumed. `_input.all()` is a normal Python list, so indexing past its bounds raises just like any other list.

### Solution

Either guard with `len(...)` before indexing, or use the built-in safe accessors. `_input.first()` returns `None` instead of raising when there is no first item. Slicing (`list[:n]`) never raises, it just returns a shorter list.

### Bad / Good

```python
# BAD: Assumes two items exist
all_items = _input.all()
first = all_items[0]
second = all_items[1]
```

```python
# GOOD: Guard with length check
all_items = _input.all()
if len(all_items) >= 2:
    first = all_items[0]["json"]
    second = all_items[1]["json"]
    return [{"json": {"first": first, "second": second}}]

return [{"json": {"error": f"Expected 2+ items, got {len(all_items)}"}}]
```

```python
# GOOD: Use _input.first() instead of [0]
first = _input.first()
if first is not None:
    return [{"json": first["json"]}]

return []
```

```python
# GOOD: Slicing never raises
first_five = _input.all()[:5]
return [{"json": item["json"]} for item in first_five]
```

---

## Gotcha 5: Incorrect Return Format

### Symptom

Workflow execution fails with a type-related error, or downstream nodes see no items, or you see "Input data is not a valid object" complaints. Sometimes the error message is opaque.

### Cause

n8n expects every Code node to return a list of dicts, each with a `"json"` key whose value is itself a dict. Anything else fails the contract: returning a plain dict, returning a list of dicts without the `"json"` wrapper, returning `None`, returning a string, returning a single non-list item.

### Solution

The shape contract is rigid. Memorize it:

- One result: `return [{"json": {...}}]`
- Multiple results: `return [{"json": {...}}, {"json": {...}}]`
- No results: `return []`
- Never `None`, never a bare dict, never a list missing the `"json"` wrapper.

### Bad / Good

```python
# BAD: Plain dict
return {"name": "Alice", "age": 30}

# BAD: List of dicts without "json" wrapper
return [{"name": "Alice"}, {"name": "Bob"}]

# BAD: None
return None

# BAD: String
return "success"

# BAD: Single item, not in a list
return {"json": {"name": "Alice"}}
```

```python
# GOOD: Single result, wrapped in list
return [{"json": {"name": "Alice", "age": 30}}]

# GOOD: Multiple results
return [
    {"json": {"name": "Alice"}},
    {"json": {"name": "Bob"}}
]

# GOOD: Empty result (valid)
return []

# GOOD: Aggregation result, single summary item
all_items = _input.all()
total = sum(item["json"].get("amount", 0) for item in all_items)
return [{"json": {"total": total, "count": len(all_items)}}]

# GOOD: Transformed list comprehension
return [
    {"json": {"id": item["json"]["id"], "processed": True}}
    for item in _input.all()
]
```

---

## Gotcha 6: `_input.item` in the Wrong Mode (`AttributeError`)

### Symptom

```
AttributeError: 'NoneType' object has no attribute '__getitem__'
```

Or accessing `_input.item["json"]` produces `None`-related errors.

### Cause

`_input.item` is only populated when the node is configured in "Run Once for Each Item" mode. In the default "Run Once for All Items" mode, `_input.item` is `None`, and any subsequent subscripting fails.

### Solution

Match your data-access method to your mode. In All Items mode, use `_input.all()` or `_input.first()`. In Each Item mode, use `_input.item`. If you cannot guarantee the mode, defensively check for `None`. See [configuration.md](./configuration.md) for mode selection.

### Bad / Good

```python
# BAD: Using _input.item in All Items mode
current = _input.item       # None in All Items mode
data = current["json"]      # AttributeError
```

```python
# GOOD: Match access pattern to mode
# In "Run Once for All Items" mode:
all_items = _input.all()
first_data = all_items[0]["json"] if all_items else {}

# In "Run Once for Each Item" mode:
current = _input.item
data = current["json"]
```

```python
# GOOD: Defensive code that works in both modes
current = _input.item
if current is not None:
    return [{"json": current["json"]}]

# Fall back to All Items mode
all_items = _input.all()
return all_items if all_items else [{"json": {"message": "No data"}}]
```

---

## Gotcha 7: Webhook Payload Nested Under `body`

### Symptom

`KeyError` on what looked like a top-level field of the webhook payload. The webhook clearly sent `{"name": "Alice", "email": "..."}`, but accessing `_json["name"]` raises.

### Cause

The Webhook node wraps every incoming request in a fixed envelope: `headers`, `params`, `query`, `body`, `method`, `url`. The actual request payload (POST body, form data, JSON body) lives under the `body` key. Accessing `_json["name"]` looks for `name` at the envelope level, where it does not exist.

### Solution

Always go through `body` to reach the payload. Use `.get("body", {})` for safety in case the envelope structure changes or the Code node runs from a non-webhook source.

### Bad / Good

```python
# BAD: Direct access, KeyError
webhook = _input.first()["json"]
name = webhook["name"]
email = webhook["email"]
```

```python
# GOOD: Access via "body"
webhook = _input.first()["json"]
body = webhook.get("body", {})
name = body.get("name", "Unknown")
email = body.get("email", "no-email")

return [{"json": {"name": name, "email": email}}]
```

```python
# GOOD: Full webhook surface
webhook = _input.first()["json"]
return [{
    "json": {
        "form_data": webhook.get("body", {}),
        "query_params": webhook.get("query", {}),
        "user_agent": webhook.get("headers", {}).get("user-agent"),
        "method": webhook.get("method"),
        "url": webhook.get("url")
    }
}]
```

---

## Gotcha 8: `StatisticsError` on Single-Element Lists

### Symptom

```
statistics.StatisticsError: stdev requires at least two data points
```

### Cause

`statistics.stdev` and `statistics.variance` require at least two values. With zero or one input value, they raise rather than return `0`.

### Solution

Guard with a length check.

### Bad / Good

```python
# BAD: No guard
import statistics
values = [item["json"].get("value", 0) for item in _input.all()]
sd = statistics.stdev(values)  # raises if len(values) < 2
```

```python
# GOOD: Length-guarded
import statistics
values = [item["json"].get("value", 0) for item in _input.all()]
sd = statistics.stdev(values) if len(values) > 1 else 0
```

---

## Gotcha 9: `_node["Name"]["json"]` Returns Surprising Shape

### Symptom

You reference another node by name and the resulting `["json"]` is not what you expected, sometimes a list, sometimes a dict, sometimes `None`.

### Cause

Direct subscript access on `_node["Name"]` does not always normalize multi-item outputs. If the referenced node emitted multiple items, the shape is implementation-defined and not always documented.

### Solution

Use `.first()` to force a stable shape, or `.all()` if you need the full list.

### Bad / Good

```python
# BAD: Direct subscript
data = _node["HTTP Request"]["json"]
```

```python
# GOOD: Explicit .first()
data = _node["HTTP Request"].first()["json"]
```

---

## Gotcha 10: Cross-Iteration State (SplitInBatches)

### Symptom

You try to accumulate state across iterations of a SplitInBatches loop in Python using `$getWorkflowStaticData('global')`, and the helper is either not available or behaves inconsistently.

### Cause

`$getWorkflowStaticData('global')` is a JavaScript helper. In Python (Beta), it is not reliably available. Even where there is partial support, behavior across batch iterations is not guaranteed.

### Solution

Use a JavaScript Code node for the accumulation step, and keep Python only for per-iteration transformations. Alternatively, restructure the workflow to avoid cross-iteration state (collect first, then process the full set in one All Items pass).

Related: The SplitInBatches node has two outputs. `main[0]` (done) fires once after all batches complete; `main[1]` (each batch) fires for every batch and is the loop body. Always add a Limit 1 node after the done output to suppress duplicate downstream fires.

### Bad / Good

```python
# BAD: Trying to accumulate in Python with the workflow static data helper
# (helper not reliably available in Python Beta)
data = $getWorkflowStaticData('global')  # not real Python
```

```javascript
// GOOD: Use a JavaScript Code node for the accumulation
const data = $getWorkflowStaticData('global');
data.runningTotal = (data.runningTotal || 0) + $json.amount;
return [{json: {runningTotal: data.runningTotal}}];
```

---

## Error-Code Quick Fix Table

| Error | Quick Fix |
|-------|-----------|
| `ModuleNotFoundError` | Use JavaScript or upstream n8n node. Stdlib only. |
| `KeyError: 'field'` | Change `data["field"]` to `data.get("field", default)`. |
| `IndexError: list index out of range` | Guard with `if len(items) > 0` or use `_input.first()` or slice. |
| Empty output | Add unconditional `return [{"json": {...}}]` at the bottom. |
| `AttributeError: 'NoneType'` on `_input.item` | Check the node mode (Each Item vs All Items). |
| "Input data is not a valid object" | Wrap result: `return [{"json": result}]`. |
| `KeyError: 'name'` on webhook | Access via `_json.get("body", {})`. |
| `statistics.StatisticsError` | Length-guard before `stdev`/`variance`. |
| `_node[...]["json"]` surprises | Use `_node[...].first()["json"]`. |
| `$getWorkflowStaticData` not working | Move accumulation to JavaScript Code node. |

---

## Testing Checklist Before Deploy

Before saving a Python Code node, verify:

- [ ] Considered JavaScript first. Using Python only when it pays for itself.
- [ ] Code is not empty. Has meaningful logic.
- [ ] Every code path ends in `return`. No implicit `None` returns.
- [ ] Return shape is `[{"json": {...}}, ...]`. Never bare dict, never `None`.
- [ ] Data access matches the configured mode (`_input.all()` / `_input.first()` for All Items; `_input.item` for Each Item).
- [ ] No external imports. Standard library only.
- [ ] Every dict access uses `.get(key, default)`. No direct `[key]` on user-supplied data.
- [ ] List indexing is either guarded by `len(...)` or replaced by `_input.first()` / slicing.
- [ ] Webhook data accessed via `["body"]`.
- [ ] `_node["..."]` access uses `.first()`.
- [ ] `statistics.stdev` / `variance` guarded for n < 2.
- [ ] Test with empty input. Test with missing fields. Test in both modes if relevant.

---

## See Also

- [README.md](./README.md), the JavaScript-first recommendation and decision tree (avoiding gotcha 1 starts here).
- [api.md](./api.md), the symbol reference. Knowing what is available is half of avoiding gotchas.
- [patterns.md](./patterns.md), patterns that were written specifically to avoid these failure modes.
- [configuration.md](./configuration.md), mode selection (avoids gotcha 6).
- [../code-javascript/](../code-javascript/), the recommended alternative for almost everything that triggers gotcha 1.
- [../validation/](../validation/), validate Code node configuration with n8n-mcp before running.
- [../workflow-patterns/](../workflow-patterns/), for SplitInBatches loop construction (avoids gotcha 10).
