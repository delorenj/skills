# n8n Code Node (Python, Beta)

The Code node lets you write Python directly inside an n8n workflow. The Python runtime is currently in beta, runs in a sandboxed interpreter, and exposes data through underscore-prefixed globals (`_input`, `_json`, `_node`) plus a small number of helpers (`_now`, `_today`, `_jmespath`). The most important fact about Python in n8n is what it does NOT have: there are no external libraries, no pip packages, no `requests`, no `pandas`, no `numpy`. You get the Python standard library and nothing else. Because of that limitation, plus the fact that JavaScript has full access to n8n helper functions (`$helpers.httpRequest`, Luxon DateTime, etc.), the official guidance from this reference is unambiguous.

## JavaScript First: Use Python for Roughly 5 Percent of Cases

For roughly 95 percent of Code node use cases, JavaScript is the better choice. Python is appropriate only when one of the following is true:

- You need a Python-specific standard library function (regex behavior, `hashlib`, `statistics`, `decimal`, `fractions`) that is awkward to replicate in JavaScript.
- You are significantly more comfortable with Python syntax and the workflow is internal or one-off.
- A data transformation maps unusually well to Python list and dict comprehensions.

Pick JavaScript when you need any of the following:

- HTTP requests from inside the Code node (`$helpers.httpRequest`).
- Advanced date/time work (Luxon DateTime, time zones, durations).
- Access to the wider n8n helper surface (`$helpers`, `$workflow`, `$execution`, `$getWorkflowStaticData`, etc.).
- Cross-iteration accumulation in SplitInBatches loops (the static-data helper may not be available in Python Beta mode).

See [../code-javascript/](../code-javascript/) for the recommended path.

## When to Use Python vs JavaScript vs Other Nodes

| Situation | Choice | Notes |
|-----------|--------|-------|
| Default Code node language | JavaScript | 95 percent of cases. Full helper surface. |
| You need `statistics.mean`, `statistics.stdev`, `statistics.median`, etc. | Python | Built-in statistics module. |
| You need `hashlib` (MD5, SHA-256) | Either, but Python is idiomatic | JavaScript also has `crypto` via helpers in some setups. |
| You need an HTTP request from inside the Code node | JavaScript | `$helpers.httpRequest()`. Python has no `requests`. |
| You need DataFrame-style work | JavaScript or upstream nodes | No `pandas` or `numpy` available. |
| You need to parse HTML | HTTP Request node + HTML Extract node | No `bs4`/`lxml`. |
| You need a database driver | n8n database nodes (Postgres, MySQL, MongoDB) | No `psycopg2`/`pymongo`/`sqlalchemy`. |
| Simple field mapping | Set node | Skip Code entirely. |
| Basic filtering | Filter node | Skip Code entirely. |
| Simple conditionals | IF or Switch node | Skip Code entirely. |
| Single API call only | HTTP Request node | Skip Code entirely. |

## Quick Start Template

The minimum viable Python Code node, running in "Run Once for All Items" mode (the default and recommended mode):

```python
from datetime import datetime

# Read all items from the previous node
items = _input.all()

# Transform each one
processed = []
for item in items:
    processed.append({
        "json": {
            **item["json"],
            "processed": True,
            "timestamp": datetime.now().isoformat()
        }
    })

# Return a list of {"json": {...}} objects
return processed
```

Five rules that prevent almost every Python Code node bug:

1. Consider JavaScript first. Use Python only when it pays for itself.
2. Read input through `_input.all()`, `_input.first()`, or `_input.item` (in Each Item mode).
3. Return `[{"json": {...}}, ...]`, always a list, always with the `"json"` wrapper.
4. Webhook payloads live under `_json["body"]`, not directly on `_json`.
5. Only the Python standard library is available. No `requests`, no `pandas`, no `numpy`.

## Decision Tree: Should I Use Python Here?

```
Does the task need an HTTP request, a database driver, pandas, numpy, or BeautifulSoup?
├─ YES -> Do NOT use Python. Use a dedicated n8n node upstream, then optionally
│         post-process in a Code node. If you still need code, use JavaScript.
│
└─ NO  -> Is the task simple field mapping, filtering, or a conditional?
    ├─ YES -> Use Set / Filter / IF / Switch instead of any Code node.
    │
    └─ NO  -> Does it specifically benefit from Python's standard library
              (statistics, hashlib, regex idioms) AND you would not lose anything
              by giving up the n8n helper surface?
        ├─ YES -> Python is reasonable. Proceed.
        └─ NO  -> Use JavaScript. See ../code-javascript/.
```

## Reading Order

| Task | Files to Read |
|------|---------------|
| Get oriented and decide whether Python is the right tool | This README |
| Look up `_input`, `_json`, `_node`, helpers, or a standard library module | [api.md](./api.md) |
| Build a working snippet for a real use case (aggregation, regex, CRM normalization, top-N, lookups) | [patterns.md](./patterns.md) |
| Diagnose `ModuleNotFoundError`, `KeyError`, `IndexError`, empty output, or wrong return format | [gotchas.md](./gotchas.md) |
| Choose between Python (Beta) and Python (Native), pick the right mode, understand beta caveats | [configuration.md](./configuration.md) |

## In This Reference

- [README.md](./README.md), this file, overview and routing with the JavaScript-first recommendation.
- [api.md](./api.md), `_input`, `_json`, `_node`, helper symbols (`_now`, `_today`, `_jmespath`), and a per-module standard library reference with examples for `json`, `datetime`, `re`, `base64`, `hashlib`, `urllib.parse`, `math`, `random`, `statistics`, and `collections`.
- [patterns.md](./patterns.md), ten named copy-paste-ready patterns for Python-specific use cases (multi-source aggregation, regex filtering, markdown parsing, JSON diff, CRM normalization, release notes, array reshaping, dictionary lookup, top-N, string aggregation), plus comparative snippets against JavaScript.
- [gotchas.md](./gotchas.md), four-part entries (symptom, cause, solution, bad/good) for the seven most common Python failure modes: `ModuleNotFoundError`, missing return, `KeyError`, `IndexError`, wrong return format, `_input.item` in the wrong mode, and webhook body nesting.
- [configuration.md](./configuration.md), Code node parameters for Python: beta status, Python (Beta) vs Python (Native), mode selection ("Run Once for All Items" vs "Run Once for Each Item"), and known limitations.

## See Also

- [../code-javascript/](../code-javascript/), the recommended Code node language for 95 percent of cases, including full n8n helper surface and Luxon DateTime.
- [../expressions/](../expressions/), for the `{{ }}` expression syntax used in non-Code nodes. Inside Code nodes you do not use `{{ }}`; you access data directly via `_input`/`_json`/`_node`.
- [../node-configuration/](../node-configuration/), for understanding Code node parameter dependencies (mode + language).
- [../mcp-tools/](../mcp-tools/), for finding and validating Code nodes via n8n-mcp: `search_nodes({query: "code"})`, `get_node_types(["nodes-base.code"])`, `validate_workflow(...)`.
- [../workflow-patterns/](../workflow-patterns/), for end-to-end workflows that show Code nodes in transformation steps, including when to swap Python for JavaScript.
- [../validation/](../validation/), for validating Code node configuration with n8n-mcp before deploy.
