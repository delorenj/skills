# Code Node: JavaScript

Expert guidance for writing JavaScript inside n8n Code nodes. Covers the API surface (`$input`, `$json`, `$node`, `$helpers`, DateTime), production-tested transformation patterns, the top runtime gotchas (sandbox restrictions, webhook body nesting, return-format requirements), and node configuration (mode selection, language toggle, version notes).

---

## Overview

The Code node runs JavaScript inside an n8n sandbox (the `JsTaskRunnerSandbox` since v2.0). It is the right tool when no single built-in node can express the transformation: aggregations, regex extractions, multi-step conditionals, structural reshaping, format conversion, or coordinating data from several upstream nodes. For single-field mapping or simple filtering, a Set / Filter / IF node is faster and cheaper.

Key constraints to internalize before writing code:

1. The node MUST return `[{ json: {...} }, ...]`, an array of `{ json }`-wrapped objects.
2. Webhook payloads live under `$json.body`, not `$json` directly.
3. `$helpers.httpRequestWithAuthentication` is **blocked** in the task runner sandbox. Use an HTTP Request node with a credential attached, or delegate to a sub-workflow.
4. `$env` is **conditionally blocked** by `N8N_BLOCK_ENV_ACCESS_IN_NODE=true` (common in production). Do not rely on it for portable code.
5. `require()` is gated by allowlists. `Buffer` and `URL` are globals and always available.

---

## When To Use the Code Node

Use the Code node when:

- Complex transformations requiring multiple steps
- Custom calculations or business logic
- Recursive operations
- API response parsing with non-trivial structure
- Multi-step conditionals that would otherwise require chaining many IF / Set nodes
- Data aggregation across items (sum, count, group, deduplicate)

Reach for a different node when:

| Need | Use Instead |
|------|-------------|
| Simple field mapping | **Set** node (see [../node-configuration/](../node-configuration/)) |
| Basic filtering | **Filter** node |
| Simple conditional branching | **IF** or **Switch** node |
| Authenticated HTTP calls | **HTTP Request** node with credential attached |
| Single-expression evaluation in another node | n8n expression syntax (see [../expressions/](../expressions/)) |

### JavaScript vs Python vs Node-Native Operations

| Task | Choose |
|------|--------|
| Aggregating items, regex, JSON reshaping, top-N filtering | Code node JavaScript (this reference) |
| Data-science work, pandas-style transforms, scipy / numpy logic | Code node Python (see [../code-python/](../code-python/)) |
| Single field rename / static value injection | **Set** node |
| Boolean condition routing | **IF** or **Switch** node |
| Iterating over arrays at workflow level | **SplitInBatches** + downstream nodes |
| HTTP call with OAuth / API-key credential | **HTTP Request** node, not the Code node |

JavaScript is the default choice for Code-node work: it is the n8n team's primary surface, has richer built-ins (`$helpers`, `DateTime`/Luxon, `$jmespath`), and matches the syntax used inside expressions. Pick Python only when you actually need the Python ecosystem.

---

## Quick Start: Code Node Template

```javascript
// Standard template for a Code node in "Run Once for All Items" mode
const items = $input.all();

const processed = items.map(item => ({
  json: {
    ...item.json,
    processed: true,
    timestamp: new Date().toISOString()
  }
}));

return processed;
```

Essential rules baked into this template:

1. Mode is **Run Once for All Items** (correct for ~95% of cases). See [configuration.md](./configuration.md).
2. Data access is via `$input.all()` (the canonical entry point). See [api.md](./api.md).
3. Return is `[{ json: {...} }, ...]`. See [gotchas.md](./gotchas.md) Error #3 for what happens otherwise.
4. If the upstream node is a Webhook, fields live under `item.json.body.*`, not `item.json.*`. See [gotchas.md](./gotchas.md) Error #5.

---

## In This Reference

| File | What's In It |
|------|--------------|
| [README.md](./README.md) | Overview, decision tables, quick start (you are here) |
| [api.md](./api.md) | The full API surface: `$input`, `$json`, `$node`, `$helpers`, DateTime, `$jmespath`, `$getWorkflowStaticData`, standard JS globals, Node.js modules |
| [patterns.md](./patterns.md) | Named, copy-paste-ready patterns: aggregation, regex extraction, markdown parsing, JSON comparison, CRM transforms, GitHub release processing, top-N ranking, Slack Block Kit, string aggregation, SplitInBatches loop accumulation, pairedItem |
| [gotchas.md](./gotchas.md) | The 7 most common errors in four-part (symptom / cause / solution / bad-good) form: missing return, expression syntax confusion, return wrapper, unmatched brackets, null access, blocked auth helpers, blocked `$env` |
| [configuration.md](./configuration.md) | Code node parameters: mode selection (All Items vs Each Item), language toggle (JavaScript vs Python), version notes, sandbox env vars |

---

## Reading Order

| Task | Files to Read |
|------|---------------|
| First-time author writing any Code node | [README.md](./README.md) → [configuration.md](./configuration.md) → [api.md](./api.md) (`$input` section) → [gotchas.md](./gotchas.md) |
| Picking the right data-access method (`$input.all` vs `$input.first` vs `$input.item`) | [configuration.md](./configuration.md) (mode) → [api.md](./api.md) (`$input` section) |
| Building an aggregation, transformation, or filter | [patterns.md](./patterns.md) → [api.md](./api.md) for any unfamiliar built-in |
| Webhook-triggered workflow | [gotchas.md](./gotchas.md) Error #5 (body nesting) → [api.md](./api.md) (`$input` / `$json` section) → [patterns.md](./patterns.md) (transformation pattern) |
| Making HTTP calls from a Code node | [api.md](./api.md) (`$helpers.httpRequest`) → [gotchas.md](./gotchas.md) Error #6 (auth helpers blocked) → [patterns.md](./patterns.md) (HTTP pattern) |
| Debugging a "Code cannot be empty" / "Return value must be an array" / "Cannot read property X of undefined" error | [gotchas.md](./gotchas.md) (relevant entry) |
| SplitInBatches loop that drops data across iterations | [patterns.md](./patterns.md) (cross-iteration accumulation) → [api.md](./api.md) (`$getWorkflowStaticData`) |
| Production hardening (env vars, sandbox, credentials) | [configuration.md](./configuration.md) (sandbox env vars) → [gotchas.md](./gotchas.md) Errors #6 and #7 |

---

## Top 5 Mistakes (Quick Hits)

Detailed in [gotchas.md](./gotchas.md), but worth seeing up front:

1. **Missing return statement** (38% of all Code-node failures). Always end with `return [{ json: ... }]`.
2. **Using `{{ }}` expression syntax inside a Code node.** Use plain JavaScript: `$json.field`, not `"{{ $json.field }}"`.
3. **Returning the wrong shape.** Must be `[{ json: {...} }]`, not `{ json: {...} }` or `[{...}]`.
4. **No null check on nested access.** Use `data?.user?.email ?? 'default'`.
5. **Accessing webhook data without `.body`.** It's `$json.body.email`, not `$json.email`.

---

## Pre-Deployment Checklist

Before saving any Code node, verify:

- Code field is not empty
- A `return` statement exists, and **every** code path reaches one
- Return shape is `[{ json: {...} }, ...]`
- Data access uses `$input.all()`, `$input.first()`, or `$input.item` (matching the mode)
- No `{{ }}` expression syntax inside the JavaScript
- Optional chaining (`?.`) or guard clauses protect nested access
- Webhook data accessed via `.body`
- Mode selection matches the work (All Items for almost everything)
- All code paths produce a consistent output shape

---

## See Also

- [api.md](./api.md), [patterns.md](./patterns.md), [gotchas.md](./gotchas.md), [configuration.md](./configuration.md) (this topic)
- [../code-python/](../code-python/) for the Python flavor of the same node
- [../expressions/](../expressions/) for `{{ }}` syntax used in other nodes (do not use inside the Code node)
- [../node-configuration/](../node-configuration/) for n8n node parameters in general (Set, IF, HTTP Request, etc.)
- [../workflow-patterns/](../workflow-patterns/) for higher-level patterns the Code node participates in (Webhook → Code → HTTP, SplitInBatches loops, error handling)
- [../validation/](../validation/) for validating a Code node's configuration via the n8n MCP / validate API
- n8n docs: Code Node Guide at https://docs.n8n.io/code/code-node/
- n8n docs: Built-in methods reference at https://docs.n8n.io/code-examples/methods-variables-reference/
- Luxon docs (powers `DateTime`): https://moment.github.io/luxon/
