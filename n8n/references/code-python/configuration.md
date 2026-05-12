# Configuration: Python Code Node

How to configure the Code node when you want to run Python. Covers language selection (and the beta caveat), the two Python sub-modes (Beta vs Native), the execution mode (All Items vs Each Item), and known limitations relative to JavaScript.

For when to use Python at all, see [README.md](./README.md). For the symbol reference once you have picked the right configuration, see [api.md](./api.md).

---

## Beta Status: Read This First

Python in the n8n Code node is currently in beta. Practical implications:

- The runtime, helpers, and sandbox behavior can change between n8n versions without the kind of backward-compatibility guarantees you get from JavaScript.
- Some helpers that exist in JavaScript (`$getWorkflowStaticData`, advanced `$helpers` methods) are missing or inconsistent in Python Beta. See [gotchas.md](./gotchas.md) entry 10.
- External library support is not on the roadmap in any near-term sense. Only the Python standard library is available.
- For production workflows where stability matters, prefer JavaScript. Use Python for internal/experimental work and tasks that are unambiguously easier in Python.

Recommendation: JavaScript for roughly 95 percent of cases. Use Python only when it pays for itself (Python-specific standard library, regex idioms, statistics work, strong personal preference). See [README.md](./README.md) for the full decision tree.

---

## Step 1: Select the Code Node

In the n8n UI, add a Code node. To find it programmatically with n8n-mcp:

```
search_nodes({query: "code"})
get_node_types(["nodes-base.code"])
```

The Code node ID is `nodes-base.code` (sometimes shown as `n8n-nodes-base.code`).

---

## Step 2: Select the Language

The Code node has a Language parameter with three relevant choices:

| Language | Status | When to Pick |
|----------|--------|--------------|
| JavaScript | Stable | The default and recommended choice. 95 percent of cases. |
| Python (Beta) | Beta | Recommended Python mode. Full data-access helpers (`_input`, `_json`, `_node`) and shortcut symbols (`_now`, `_today`, `_jmespath`). |
| Python (Native) (Beta) | Beta | Stripped-down Python with only `_items` and `_item`. No helpers. Use only when you specifically need pure Python without n8n's helper layer. |

### Python (Beta) vs Python (Native)

The two Python modes differ in what is exposed inside the code body.

| Concern | Python (Beta) | Python (Native) |
|---------|---------------|-----------------|
| Read all items | `_input.all()` | `_items` |
| Read first item | `_input.first()` | `_items[0]` |
| Read current item (Each Item mode) | `_input.item` | `_item` |
| Current JSON | `_json` | `_item["json"]` |
| Reference another node | `_node["Name"]` | not available |
| Current time | `_now` | use `datetime.now()` |
| Today | `_today` | use `datetime.now().date()` |
| JMESPath query | `_jmespath(expr, data)` | not available |
| Standard library | full | full |

Recommendation: pick Python (Beta). It exposes more, costs nothing, and is the documented happy path. Pick Python (Native) only if you have a specific reason to avoid the helper layer (e.g., portable Python code that you want to test outside n8n).

---

## Step 3: Select the Execution Mode

The Mode parameter controls how often the code body runs per workflow execution.

### Mode A: Run Once for All Items (default, recommended)

The code body executes exactly once per workflow run, regardless of how many input items the previous node produced. You read all items via `_input.all()`, process them in a single function body, and return a list.

Use for:
- Aggregations (sum, count, average, top-N).
- Filtering and transforming a batch.
- Group-by, deduplication, joins between sources.
- Any task where the output is a function of the entire input set.

Performance: faster for multiple items because the interpreter starts up once.

Data access symbols available:
- `_input.all()` (primary)
- `_input.first()` (convenience for "just the first one")
- `_json` (refers to the first item, but be explicit instead)
- `_node["Name"]` (reference other nodes)

Symbols that misbehave in this mode:
- `_input.item` is `None`. Accessing it raises `AttributeError` on subscript. See [gotchas.md](./gotchas.md) entry 6.

Example skeleton:

```python
from datetime import datetime

all_items = _input.all()

processed = []
for item in all_items:
    processed.append({
        "json": {
            **item["json"],
            "processed_at": datetime.now().isoformat()
        }
    })

return processed
```

### Mode B: Run Once for Each Item

The code body executes once per input item. n8n collects the per-iteration returns into a single output list. You read the current item via `_input.item`.

Use for:
- Per-item validation where each item has independent logic.
- Conditional shaping that varies item-by-item.
- Cases where you want item-level retries or error isolation at the n8n level.

Performance: slower for large datasets because the interpreter restarts per item. Avoid for batch work.

Data access symbols available:
- `_input.item` (primary, current item only)
- `_input.all()` (still works, returns the full upstream list)
- `_input.first()` (still works)
- `_node["Name"]` (still works)

Example skeleton:

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

### Mode Decision Cheat Sheet

| Question | Answer |
|----------|--------|
| Are you aggregating across items? | All Items |
| Are you filtering or sorting a list? | All Items |
| Are you grouping or deduplicating? | All Items |
| Does each item need independent processing with no cross-item dependencies? | Each Item |
| Are you doing a per-item API enrichment (in JS only, since Python has no HTTP)? | Each Item |
| In doubt? | All Items |

Roughly 95 percent of Code nodes should be in All Items mode. Each Item mode is a specialty choice.

---

## Step 4: Configure Error Handling

The Code node respects the standard n8n error-handling parameters at the node level:

- Continue On Fail: if true, errors do not stop the workflow. The Code node emits an error item instead. Useful when one bad payload should not kill a batch run.
- Retry On Fail: retries the Code node body N times before failing. Less useful for Python Code (errors are usually deterministic), but available.
- Always Output Data: if true, the node always emits at least one item, even when the code returns `[]` or fails. Useful for downstream nodes that need at least one trigger.

For tightly coupled flows where a Python Code node failure should halt processing, leave Continue On Fail off. For best-effort batch processing where one bad record should not kill the run, turn it on and inspect the error item downstream.

---

## Step 5: Test the Configuration

Once configured, validate before deploy:

1. Pin sample input data on the Code node to test in isolation.
2. Run with a typical payload.
3. Run with an empty input. Confirm the code returns `[]` or a sensible empty marker rather than raising.
4. Run with a payload missing optional fields. Confirm `.get()` defaults kick in.
5. If the source is a webhook, confirm the code accesses payload under `["body"]`.
6. Validate via n8n-mcp:

```
validate_workflow({...full workflow code...})
```

See [../validation/](../validation/) for the full validation surface.

---

## Known Limitations Relative to JavaScript

A non-exhaustive list of things Python Code nodes cannot do, all of which JavaScript Code nodes can:

| Capability | JavaScript | Python (Beta) |
|------------|------------|---------------|
| HTTP request from inside the node | `$helpers.httpRequest()` | not available |
| Workflow static data (cross-execution state) | `$getWorkflowStaticData('global')` | not reliably available |
| Advanced date/time (Luxon DateTime, time zones, duration arithmetic) | full Luxon API | manual `datetime` + `timedelta` |
| External libraries | possible via n8n environment for some setups | strictly none |
| Binary helpers | full `$helpers.prepareBinaryData` and friends | limited |
| Workflow metadata helpers | `$workflow`, `$execution` | partial |

If your Code node needs any of the above, configure it as JavaScript instead. See [../code-javascript/](../code-javascript/).

---

## Configuration Cheat Sheet

The shortest path to a working Python Code node:

1. Add a Code node.
2. Language: Python (Beta).
3. Mode: Run Once for All Items.
4. Body:

```python
from datetime import datetime

items = _input.all()
processed = []
for item in items:
    processed.append({
        "json": {
            **item["json"],
            "processed_at": datetime.now().isoformat()
        }
    })

return processed
```

5. Continue On Fail: off (unless you have a reason).
6. Validate via n8n-mcp.
7. Deploy.

---

## See Also

- [README.md](./README.md), the JavaScript-first recommendation and decision tree. Read this before settling on Python.
- [api.md](./api.md), the symbol reference, including the table comparing Python (Beta) and Python (Native).
- [patterns.md](./patterns.md), worked examples in both All Items and Each Item modes.
- [gotchas.md](./gotchas.md), failure modes including `_input.item` in the wrong mode and SplitInBatches cross-iteration state.
- [../code-javascript/](../code-javascript/), the recommended alternative for any limitation listed above.
- [../node-configuration/](../node-configuration/), general Code node parameter dependencies (Language drives the body format; Mode drives data-access symbols).
- [../mcp-tools/](../mcp-tools/), `get_node_types(["nodes-base.code"])` to introspect the Code node parameter schema.
- [../validation/](../validation/), `validate_workflow` flow for Code nodes before deploy.
