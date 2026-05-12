# Code Node JavaScript: Configuration

n8n Code node parameters that govern JavaScript execution: mode selection (Run Once for All Items vs Run Once for Each Item), language toggle (JavaScript vs Python), error-handling settings, and the sandbox environment variables that change what your code can do at runtime.

For the API that each mode exposes, see [api.md](./api.md). For the symptoms when the wrong mode is chosen, see [gotchas.md](./gotchas.md).

---

## Node Parameters

The Code node exposes four parameters that matter for JavaScript work:

| Parameter | Choices | Default | Effect |
|-----------|---------|---------|--------|
| **Mode** | Run Once for All Items, Run Once for Each Item | Run Once for All Items | Controls how often the code runs and which data-access symbols are valid |
| **Language** | JavaScript, Python (Beta) | JavaScript | Selects the script-language sandbox; this reference assumes JavaScript |
| **Code** | (textarea) | empty | The script body |
| **Continue On Fail** | Off, On | Off | If On, downstream execution continues even when this node throws |

Plus the workflow-level setting **Error Workflow**, which is the canonical way to surface Code-node failures (see [../workflow-patterns/](../workflow-patterns/) for error-handling patterns).

---

## Mode Selection

The Code node offers two execution modes. **This is the single most important configuration decision**: it changes which symbols are valid (`$input.all()` vs `$input.item`), how often the code runs, and the performance profile.

### Run Once for All Items (Recommended)

**Use this mode for the vast majority of cases (about 95%).**

- **How it works**: The code executes **exactly once** regardless of how many input items arrive
- **Data access**: `$input.all()` returns the full input array; `$input.first()` returns just the first
- **Best for**: aggregation, filtering, batch processing, transformation, anything that needs to look at multiple items together
- **Performance**: faster on large input arrays because there's only one VM invocation

```javascript
// Example: calculate total across all items in a single pass
const allItems = $input.all();
const total = allItems.reduce((sum, item) => sum + (item.json.amount || 0), 0);

return [{
  json: {
    total,
    count: allItems.length,
    average: total / allItems.length
  }
}];
```

**Choose this mode when you need to**:

- Compare items across the dataset
- Calculate totals, averages, or other statistics
- Sort or rank items
- Deduplicate
- Build an aggregated report
- Combine data from multiple items

### Run Once for Each Item

**Use this mode for specialized cases only.**

- **How it works**: The code executes **separately** for every input item; n8n invokes the sandbox once per item
- **Data access**: `$input.item` exposes the current item; `$input.all()` still works but is rarely needed
- **Best for**: item-specific logic with independent behavior, per-item validation with custom error handling, per-item HTTP calls
- **Performance**: slower on large datasets (multiple VM invocations); use only when behavior must differ per item

```javascript
// Example: per-item processing with a timestamp
const item = $input.item;

return [{
  json: {
    ...item.json,
    processed: true,
    processedAt: new Date().toISOString()
  }
}];
```

**Choose this mode when**:

- Each item needs an independent API call
- Per-item validation requires different error handling
- Item-specific transformations depend on item properties
- Business logic requires items be processed strictly separately

### Decision Shortcut

| Question | Answer |
|----------|--------|
| Do you need to look at multiple items? | All Items mode |
| Is each item completely independent **and** you need different behavior per item? | Each Item mode |
| Not sure? | All Items mode (you can always loop with `for`/`forEach` inside) |

### Symbol availability by mode

| Symbol | All Items mode | Each Item mode |
|--------|----------------|----------------|
| `$input.all()` | yes | yes (returns the current item wrapped in a 1-element array) |
| `$input.first()` | yes | yes |
| `$input.item` | undefined | **yes** (current item) |
| `$json` | shorthand for first item | shorthand for current item |
| `$node["Name"]` | yes | yes |
| `$helpers.*` | yes | yes |
| `DateTime`, `$jmespath`, `$getWorkflowStaticData` | yes | yes |

`$input.item` is the most common source of confusion: it is undefined in All Items mode. Reading `$input.item.json` in All Items mode throws "Cannot read property 'json' of undefined." See [gotchas.md](./gotchas.md) Error #5.

---

## Language Toggle: JavaScript vs Python

The language dropdown switches the sandbox between JavaScript (the `JsTaskRunnerSandbox` covered in this reference) and Python (beta in current versions; see [../code-python/](../code-python/)).

Choose **JavaScript** when:

- You want the richer built-in surface: `$helpers.httpRequest`, `DateTime`/Luxon, `$jmespath`
- The rest of your workflow uses `{{ }}` expressions (JavaScript syntax matches them, easing context switches)
- You need maximum stability (JavaScript is the primary surface; Python is beta)

Choose **Python** when:

- You need the Python ecosystem (numpy, pandas, etc., subject to instance allowlists)
- You're porting existing Python data-processing logic
- You're more comfortable with Python idioms for data work

Changing the language **does not** auto-translate code. The dropdown wipes the script body when you switch.

---

## Continue On Fail

When **Continue On Fail** is enabled, a thrown exception inside the Code node is caught by n8n: downstream nodes still receive an output item (typically with an `error` field describing what went wrong). When disabled (default), an exception halts the workflow execution.

```javascript
// With Continue On Fail enabled, a thrown error becomes:
// [{ json: { error: { message: "...", stack: "..." } } }]
// instead of halting the workflow.
```

Use Continue On Fail for:

- Batch processing where individual-item failures shouldn't kill the whole run
- Best-effort enrichment where missing data is acceptable
- Pipelines that have explicit error-handling branches downstream

Avoid Continue On Fail when:

- A failure should genuinely stop the workflow (financial transactions, irreversible side effects)
- You want the error to surface in the n8n executions log loudly
- You're still developing the workflow and want errors to be visible

The more idiomatic alternative for production workflows is to leave Continue On Fail off and wire the workflow's **Error Workflow** setting to a dedicated error-handling sub-workflow.

---

## Sandbox Environment Variables

The Code node runs inside the `JsTaskRunnerSandbox` (task runner), which is governed by several n8n environment variables. These are set on the n8n server, not in the node's UI. Knowing which are set tells you what your code can do.

### `N8N_BLOCK_ENV_ACCESS_IN_NODE`

- **Default**: false (varies by deployment; commonly `true` in hardened production)
- **Effect when true**: `$env` is removed from the Code node sandbox; any reference throws `ReferenceError: $env is not defined`
- **Why it exists**: prevents Code-node users from exfiltrating arbitrary environment variables (`DB_PASSWORD`, `N8N_ENCRYPTION_KEY`, etc.)
- **Implication for portable skills**: **do not rely on `$env`**. Route secrets through credentials. See [gotchas.md](./gotchas.md) Error #7.

### `N8N_RUNNERS_ALLOWED_BUILT_IN_MODULES`

- **Default**: unset (`require()` of any built-in throws)
- **Legacy alias**: `NODE_FUNCTION_ALLOW_BUILTIN`
- **Effect**: comma-separated list of Node.js built-in modules `require()` can load. Setting to `*` allows everything.
- **Common values**: `crypto`, `crypto,zlib`, `*`
- **Implication for portable skills**: assume the default. `Buffer` and `URL` are globals and always work; `require('crypto')` and similar do not. See [gotchas.md](./gotchas.md) Error #8.

### `N8N_RUNNERS_ALLOWED_EXTERNAL_MODULES`

- **Default**: unset (external npm modules unavailable)
- **Effect**: comma-separated list of external npm packages `require()` can load, **provided the package is installed in the runner image**. Both conditions are required.
- **Common values**: usually unset; `axios,lodash` on permissive instances
- **Implication for portable skills**: assume the default. Use `$helpers.httpRequest()` instead of `axios`, native array methods instead of `lodash`, `DateTime` (Luxon) instead of `moment`.

### What's compiled-in (no env var control)

`$helpers.httpRequestWithAuthentication` and `$helpers.requestWithAuthenticationPaginated` are blocked **unconditionally** in the task runner. The deny-list is in `packages/@n8n/task-runner/src/runner-types.ts`. No env var re-enables them. See [gotchas.md](./gotchas.md) Error #6 for workarounds.

---

## Version Notes

| n8n version | Sandbox | Notes |
|-------------|---------|-------|
| < 1.x | `vm2` | Original sandbox; `httpRequestWithAuthentication` *did* execute (but was semantically broken, since the Code node has no credential of its own) |
| 1.x | `vm2` | Same as above; many tutorials and forum posts from this era show patterns that no longer work |
| 2.0+ | `JsTaskRunnerSandbox` (task runner) | Auth helpers blocked, `$env` and `require()` gated by env vars, deny-list compiled-in |
| Latest | `JsTaskRunnerSandbox` | The vm2 fallback is being removed entirely; treat the task runner as the only sandbox |

**Migration footgun**: a workflow that used `$helpers.httpRequestWithAuthentication` against an n8n 1.x instance silently broke when the instance was upgraded to 2.0+. The workflow still saves and validates, but **throws on execution**. See [gotchas.md](./gotchas.md) Error #6.

---

## Pre-Save Configuration Checklist

Before saving a Code node configuration:

- [ ] **Mode** matches the work: All Items for aggregation/batch; Each Item only for genuinely per-item logic
- [ ] **Language** is JavaScript (or, deliberately, Python via [../code-python/](../code-python/))
- [ ] **Continue On Fail** matches risk tolerance (off for critical, on for best-effort)
- [ ] **Code** uses `$input.all()` (All Items) or `$input.item` (Each Item) consistent with the mode
- [ ] **Code** returns the correct shape: `[{ json: {...} }]`
- [ ] **Code** does not call blocked helpers (`httpRequestWithAuthentication`, gated `$env`)
- [ ] **Code** does not assume `require('crypto')` works unless the instance allowlist is known
- [ ] **Webhook-fed nodes** access data via `.body`
- [ ] **All code paths return** (no fall-through to undefined)

---

## See Also

- [README.md](./README.md), [api.md](./api.md), [patterns.md](./patterns.md), [gotchas.md](./gotchas.md) (this topic)
- [../code-python/](../code-python/) for the Python language option and its own sandbox rules
- [../expressions/](../expressions/) for the `{{ }}` expression syntax used in **other** nodes (not in Code)
- [../node-configuration/](../node-configuration/) for general n8n node parameter mechanics (the HTTP Request node, credentials, etc.)
- [../workflow-patterns/](../workflow-patterns/) for Error Workflow setup, SplitInBatches loops, and sub-workflow delegation
- [../validation/](../validation/) for validating Code-node configuration programmatically via the n8n MCP / validate API
- n8n docs: https://docs.n8n.io/code/code-node/
