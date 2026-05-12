# MCP Tool Gotchas

Recurring failure modes for n8n-mcp tool calls. Each entry follows the four-part structure: Symptom, Why, Bad, Good. Use these to triage error responses and to pre-empt mistakes when generating tool calls.

---

## nodeType Format Errors

### Wrong Prefix for Search and Validate Tools

**Symptom**: `search_nodes`, `get_node`, or `validate_node` returns "Node not found" or returns nothing despite a valid-looking nodeType.

**Why**: Search and validate tools expect the SHORT prefix (`nodes-base.*`, `nodes-langchain.*`). The FULL prefix (`n8n-nodes-base.*`) is used by workflow tools (`n8n_create_workflow`, `n8n_update_partial_workflow`) and is not interchangeable.

**Bad**:

```javascript
get_node({ nodeType: "slack" })                    // missing prefix
get_node({ nodeType: "n8n-nodes-base.slack" })     // wrong (FULL) prefix
validate_node({ nodeType: "n8n-nodes-base.httpRequest", config })  // wrong prefix
```

**Good**:

```javascript
get_node({ nodeType: "nodes-base.slack" })
validate_node({ nodeType: "nodes-base.httpRequest", config, profile: "runtime" })
get_node({ nodeType: "nodes-langchain.agent" })    // AI langchain nodes use nodes-langchain.*
```

### Wrong Prefix for Workflow Tools

**Symptom**: `n8n_create_workflow` or `n8n_update_partial_workflow` accepts the call but the resulting node is invalid in n8n, or the API rejects unknown node type.

**Why**: Workflow tools store the node `type` field as written. n8n expects the FULL prefix at runtime.

**Bad**:

```javascript
n8n_create_workflow({
  nodes: [{ type: "nodes-base.slack", ... }]    // missing n8n- prefix
})
```

**Good**:

```javascript
n8n_create_workflow({
  nodes: [{ type: "n8n-nodes-base.slack", ... }]
})

// Langchain nodes
n8n_create_workflow({
  nodes: [{ type: "@n8n/n8n-nodes-langchain.agent", ... }]
})
```

### Forgetting Both Formats Exist

**Symptom**: You hand-write one nodeType, then reuse the wrong one across tool families.

**Why**: It is easy to forget which family expects which prefix.

**Bad**:

```javascript
// You searched and got nodes-base.slack, then pasted it into create
n8n_create_workflow({ nodes: [{ type: "nodes-base.slack", ... }] })  // wrong
```

**Good**:

```javascript
// search_nodes returns BOTH formats. Use the right one for the right tool
const result = search_nodes({ query: "slack" })
const node = result.results[0]

// For get_node, validate_node, validate_workflow
get_node({ nodeType: node.nodeType })            // "nodes-base.slack"

// For n8n_create_workflow, n8n_update_partial_workflow
n8n_create_workflow({ nodes: [{ type: node.workflowNodeType, ... }] })  // "n8n-nodes-base.slack"
```

---

## Parameter Structure Errors

### `parameters` vs `updates` in `updateNode`

**Symptom**: `n8n_update_partial_workflow` returns success but the node parameters did not change. Or the call rejects the operation.

**Why**: The `updateNode` operation uses the key `updates`, not `parameters`. This is the single most-frequently-encountered partial-update bug.

**Bad**:

```javascript
n8n_update_partial_workflow({
  id: "wf-123",
  operations: [{
    type: "updateNode",
    nodeName: "HTTP Request",
    parameters: { url: "https://api.example.com" }   // wrong key
  }]
})
```

**Good**:

```javascript
n8n_update_partial_workflow({
  id: "wf-123",
  intent: "Update HTTP Request URL",
  operations: [{
    type: "updateNode",
    nodeName: "HTTP Request",
    updates: { url: "https://api.example.com" }     // correct key
  }]
})
```

### Flat Credentials Object

**Symptom**: Credentials do not attach to the node. The workflow runs and fails with "no credentials configured" or "credential not found".

**Why**: Credentials must nest by credential TYPE, with `id` and `name`. A flat string or flat object will not bind correctly.

**Bad**:

```javascript
// Flat string
updates: { credentials: "myApiKey" }

// Flat object
updates: { credentials: { id: "abc123", name: "My API Key" } }
```

**Good**:

```javascript
updates: {
  credentials: {
    httpHeaderAuth: {        // credential TYPE goes here
      id: "abc123",
      name: "My API Key"
    }
  }
}

// Slack example
updates: {
  credentials: {
    slackApi: { id: "xyz789", name: "Production Slack" }
  }
}
```

Use `n8n_manage_credentials({ action: "getSchema", type: "..." })` to confirm the credential type name.

### Property Removal Without `null`

**Symptom**: Trying to remove a property leaves it set to its previous value, or you write a workaround (set to empty string) that breaks the node.

**Why**: To remove a property cleanly, set it to `null` in `updates`. Auto-sanitization understands this.

**Bad**:

```javascript
// Setting to empty string is not removal
updates: { onError: "" }

// Trying to omit it does nothing
updates: { /* onError just absent */ }
```

**Good**:

```javascript
updates: {
  continueOnFail: null,           // remove deprecated property
  onError: "continueErrorOutput"  // set new property in the same call
}
```

### Connection Operation Without Smart Params

**Symptom**: Connections to IF/Switch outputs point to the wrong branch. Hours later you discover the True/False handlers are swapped.

**Why**: `sourceIndex` is fragile (which output is index 0 again?). Smart parameters (`branch`, `case`) are clearer and survive node renames.

**Bad**:

```javascript
// Hard to verify by reading
operations: [{
  type: "addConnection",
  source: "IF",
  target: "Handler",
  sourceIndex: 0    // is 0 true or false?
}]
```

**Good**:

```javascript
operations: [
  { type: "addConnection", source: "IF", target: "True Handler", branch: "true" },
  { type: "addConnection", source: "IF", target: "False Handler", branch: "false" }
]

// Switch
operations: [
  { type: "addConnection", source: "Switch", target: "Handler A", case: 0 },
  { type: "addConnection", source: "Switch", target: "Handler B", case: 1 }
]
```

### AI Connection Without `sourceOutput`

**Symptom**: AI agent runs without its language model, memory, or tools attached. Side-inputs appear disconnected in the n8n UI.

**Why**: AI side-inputs need the typed output. There are 8: `ai_languageModel`, `ai_tool`, `ai_memory`, `ai_outputParser`, `ai_embedding`, `ai_vectorStore`, `ai_document`, `ai_textSplitter`.

**Bad**:

```javascript
// No sourceOutput, defaults to "main" which is wrong
{ type: "addConnection", source: "OpenAI Chat Model", target: "AI Agent" }
```

**Good**:

```javascript
{ type: "addConnection", source: "OpenAI Chat Model", target: "AI Agent", sourceOutput: "ai_languageModel" }
{ type: "addConnection", source: "Window Buffer Memory", target: "AI Agent", sourceOutput: "ai_memory" }
{ type: "addConnection", source: "HTTP Request Tool", target: "AI Agent", sourceOutput: "ai_tool" }
```

---

## Tool Selection Errors

### Defaulting to `detail: "full"`

**Symptom**: Token bills for `get_node` calls inflate noticeably. Slower agent loops.

**Why**: `detail: "full"` returns 3-8K tokens of complete schema. The default `standard` returns 1-2K and covers 95% of cases. `minimal` is even smaller.

**Bad**:

```javascript
get_node({ nodeType: "nodes-base.httpRequest", detail: "full" })   // 3-8K tokens
```

**Good**:

```javascript
// Default (standard), 1-2K tokens, covers 95% of cases
get_node({ nodeType: "nodes-base.httpRequest" })

// Just need metadata
get_node({ nodeType: "nodes-base.httpRequest", detail: "minimal" })  // ~200 tokens

// Just need one property
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "auth"
})

// Just want readable docs
get_node({ nodeType: "nodes-base.httpRequest", mode: "docs" })
```

Use `detail: "full"` only when debugging complex configuration or exploring advanced features.

### Skipping the Validation Profile

**Symptom**: Validation either floods you with false positives or misses real errors.

**Why**: The default profile in some contexts is too permissive. Explicitly specify `profile: "runtime"` for balanced pre-deployment validation.

**Bad**:

```javascript
validate_node({ nodeType, config })       // unspecified profile
```

**Good**:

```javascript
validate_node({ nodeType, config, profile: "runtime" })       // balanced default
validate_node({ nodeType, config, profile: "strict" })        // production
validate_node({ nodeType, config, profile: "ai-friendly" })   // AI-generated config
validate_node({ nodeType, config: {}, mode: "minimal" })      // just see required fields
```

### Trying One-Shot Workflow Construction

**Symptom**: Large `n8n_create_workflow` calls have hard-to-trace errors. Auto-sanitization warnings pile up. The workflow is broken in ways you cannot easily diagnose.

**Why**: Real workflows are built iteratively, 56 s average between edits (telemetry from 31,464 occurrences). Each partial update gets its own validation feedback. One-shot creation moves the entire error budget into a single failure mode.

**Bad**:

```javascript
n8n_create_workflow({
  name: "Complex AI Workflow",
  nodes: [/* 15 nodes assembled in one shot */],
  connections: { /* 25 connections */ }
})
// Validation finds 10 errors. Which one caused which?
```

**Good**:

```javascript
// Create a small skeleton
const wf = n8n_create_workflow({
  name: "Complex AI Workflow",
  nodes: [/* 2-3 trigger nodes */],
  connections: { /* minimal */ }
})

// Validate, then add nodes one logical chunk at a time
n8n_validate_workflow({ id: wf.id })

n8n_update_partial_workflow({
  id: wf.id,
  intent: "Add AI agent and LLM",
  operations: [
    { type: "addNode", node: {/* AI Agent */} },
    { type: "addNode", node: {/* OpenAI Chat Model */} },
    { type: "addConnection", source: "OpenAI Chat Model", target: "AI Agent", sourceOutput: "ai_languageModel" }
  ]
})

n8n_validate_workflow({ id: wf.id })
// ... and so on
```

### Omitting `intent` on Partial Updates

**Symptom**: Tool responses are less helpful. Downstream AI summaries are vague.

**Why**: The `intent` field gives the tool (and any consuming AI) context for the change. Free-text. Always include it.

**Bad**:

```javascript
n8n_update_partial_workflow({
  id,
  operations: [{ type: "addNode", node: {...} }]
  // no intent
})
```

**Good**:

```javascript
n8n_update_partial_workflow({
  id,
  intent: "Add error handling for API rate limits",
  operations: [{ type: "addNode", node: {...} }]
})
```

### Using `updateNode` for String Edits

**Symptom**: You replace an entire Code node's `jsCode` to change one line and accidentally clobber unrelated edits. Or the change silently does not apply because `__patch_find_replace` did not find the target.

**Why**: `patchNodeField` is strict (errors on miss, errors on multiple matches without `replaceAll`). `updateNode` with `__patch_find_replace` is tolerant (warns but continues). For string edits, prefer `patchNodeField`.

**Bad**:

```javascript
// Tolerant - silent failure on miss
operations: [{
  type: "updateNode",
  nodeName: "Code",
  updates: {
    "parameters.jsCode": {
      __patch_find_replace: { find: "const limit = 10;", replace: "const limit = 50;" }
    }
  }
}]

// Or worse: replace the entire field
operations: [{
  type: "updateNode",
  nodeName: "Code",
  updates: { "parameters.jsCode": "/* entire reconstructed file */" }
}]
```

**Good**:

```javascript
operations: [{
  type: "patchNodeField",
  nodeName: "Code",
  fieldPath: "parameters.jsCode",
  patches: [{ find: "const limit = 10;", replace: "const limit = 50;" }]
}]
```

### `patchNodeField` Ambiguity

**Symptom**: `patchNodeField` operation fails with "multiple matches found".

**Why**: By design, `patchNodeField` refuses ambiguous replacements. Either narrow the `find` string with more surrounding context, or set `replaceAll: true` if every occurrence should change.

**Bad**:

```javascript
// "0" appears in many places in the code; ambiguous
patches: [{ find: "0", replace: "10" }]
```

**Good**:

```javascript
// Narrow with surrounding context
patches: [{ find: "const limit = 0;", replace: "const limit = 10;" }]

// Or explicitly replace all
patches: [{ find: "api.old.com", replace: "api.new.com", replaceAll: true }]
```

### `patchNodeField` Miss

**Symptom**: `patchNodeField` operation fails with "find string not found".

**Why**: Strict mode errors on miss (this is the safety net you wanted). Inspect the actual field content to find the right `find` string, then retry.

**Bad**:

```javascript
// You guessed the string. It is not in the file
patches: [{ find: "const PAGE_SIZE = 10;", replace: "const PAGE_SIZE = 50;" }]
```

**Good**:

```javascript
// 1. Get the current content
const wf = n8n_get_workflow({ id: "wf-abc" })
const codeNode = wf.nodes.find(n => n.name === "Code")
console.log(codeNode.parameters.jsCode)

// 2. Use the exact string you see
patches: [{ find: "const limit = 10;", replace: "const limit = 50;" }]
```

---

## Auto-Sanitization Surprises

### Hand-Setting `singleValue` on Binary Operators

**Symptom**: Validation warns about operator structure, or your manual `singleValue` is removed on the next update.

**Why**: Auto-sanitization runs on ALL nodes on every workflow update. It removes `singleValue` from binary operators (`equals`, `contains`, `greaterThan`, etc.) and adds it to unary operators (`isEmpty`, `isNotEmpty`, `true`, `false`). Do not fight it.

**Bad**:

```javascript
// Manually setting singleValue: true on equals
{
  type: "boolean",
  operation: "equals",       // binary
  singleValue: true          // wrong, will be auto-stripped
}
```

**Good**:

```javascript
// Binary operators
{ type: "boolean", operation: "equals" }
{ type: "string", operation: "contains" }

// Unary operators
{ type: "string", operation: "isEmpty", singleValue: true }
{ type: "string", operation: "isNotEmpty", singleValue: true }
```

Trust auto-sanitization. If you see operator structure warnings, save the workflow and they will clear on the next update.

### Expecting Auto-Sanitization to Fix Connections

**Symptom**: You delete a node and the workflow still has stale connection references. Auto-sanitization does not remove them.

**Why**: Auto-sanitization only fixes operator structures and IF/Switch metadata. It cannot fix:

- Broken connections (references to non-existent nodes).
- Branch count mismatches (3 Switch rules but 2 outputs).
- Paradoxical corrupt states.

**Bad**: Wait for auto-sanitization to clean up.

**Good**:

```javascript
n8n_update_partial_workflow({
  id,
  intent: "Clean up stale connections after node deletion",
  operations: [{ type: "cleanStaleConnections" }]
})

// Or rewire atomically
operations: [{
  type: "rewireConnection",
  source: "Webhook",
  from: "Old Handler",
  to: "New Handler"
}]

// Or run autofix
n8n_autofix_workflow({ id, applyFixes: true })
```

---

## Hosted vs Self-Hosted

### Calling `n8n_generate_workflow` on Self-Hosted

**Symptom**: Tool returns `{ hosted_only: true, ... }` with a redirect message instead of a workflow.

**Why**: `n8n_generate_workflow` is hosted-only. Self-hosted instances do not run the underlying generation pipeline.

**Bad**:

```javascript
// On self-hosted
n8n_generate_workflow({ description: "..." })
// → { hosted_only: true, ... }
```

**Good**:

```javascript
// On self-hosted, fall back
n8n_deploy_template({ templateId: 2947 })    // curated templates

// Or build manually
n8n_create_workflow({ name, nodes, connections })
```

### Forgetting Proposals Are Not Deployed

**Symptom**: User asked for a workflow but nothing exists in n8n. You returned the proposals and stopped.

**Why**: `n8n_generate_workflow` is a two-step flow. Step 1 returns proposals or a preview (NOT deployed). Step 2 deploys, with `deploy_id` (proposal) or `confirm_deploy: true` (preview).

**Bad**:

```javascript
// Step 1
const proposals = n8n_generate_workflow({ description: "..." })
// → status: "proposals". You stop here. Nothing was deployed.
```

**Good**:

```javascript
const proposals = n8n_generate_workflow({ description: "..." })
// User picks proposal "uuid-1"

n8n_generate_workflow({ description: "...", deploy_id: "uuid-1" })
// → status: "deployed"

// Validate immediately
n8n_validate_workflow({ id: deployed.workflow_id })
```

### Activation Confusion After Generation or Template Deploy

**Symptom**: Workflow is created but does not run on triggers. User is confused.

**Why**: Workflows deployed via `n8n_generate_workflow` or `n8n_deploy_template` are created INACTIVE. Configure credentials in the n8n UI (or via `n8n_manage_credentials`), then activate.

**Bad**:

```javascript
n8n_deploy_template({ templateId: 2947 })
// Workflow exists but is inactive. User wonders why it does not fire
```

**Good**:

```javascript
const result = n8n_deploy_template({ templateId: 2947 })

// Configure credentials
n8n_manage_credentials({ action: "create", name: "...", type: "slackApi", data: {...} })

// Validate
n8n_validate_workflow({ id: result.id })

// Activate
n8n_update_partial_workflow({
  id: result.id,
  intent: "Activate workflow",
  operations: [{ type: "activateWorkflow" }]
})
```

---

## Credential Errors

### Treating "No Usages" as "Safe to Delete"

**Symptom**: You delete a credential and a workflow breaks at runtime.

**Why**: `includeUsage: true` scans active workflows up to 5000 entries. Archived workflows are excluded by n8n's API. A "no usages" result does NOT prove the credential is unused.

**Bad**:

```javascript
const cred = n8n_manage_credentials({ action: "get", id: "123", includeUsage: true })
if (cred.usageCount === 0) {
  n8n_manage_credentials({ action: "delete", id: "123" })  // unsafe!
}
```

**Good**:

```javascript
const cred = n8n_manage_credentials({ action: "get", id: "123", includeUsage: true })

if (cred.usageScanError) {
  // Scan failed; do not delete
  throw new Error("Cannot verify usage; aborting destructive action")
}

if (cred.usageCount === 0) {
  // Additional manual verification (check archives, ask owner, etc.)
  // Then, if confirmed safe:
  n8n_manage_credentials({ action: "delete", id: "123" })
}
```

### Trying to Update a Credential Without `type`

**Symptom**: `update` action fails with a vague error about the credential type on some n8n versions.

**Why**: Some n8n versions require `type` on update. Pass it defensively.

**Bad**:

```javascript
n8n_manage_credentials({
  action: "update",
  id: "123",
  name: "New Name",
  data: { accessToken: "..." }
  // missing type
})
```

**Good**:

```javascript
n8n_manage_credentials({
  action: "update",
  id: "123",
  name: "New Name",
  data: { accessToken: "..." },
  type: "slackApi"   // pass it defensively
})
```

### Expecting `data` Back in Responses

**Symptom**: You expect to read back the secret you just stored. The `data` field is missing in `get`, `create`, and `update` responses.

**Why**: All three actions strip the `data` field from responses (defense-in-depth). Secrets are never returned by the MCP tool, even to the caller that just supplied them.

**Bad**:

```javascript
const cred = n8n_manage_credentials({ action: "create", name, type, data })
console.log(cred.data.accessToken)   // undefined
```

**Good**: Treat `data` as write-only. Re-supply on update when needed. Store secrets in your own secrets manager, not by reading them back from n8n-mcp.

---

## Data Table Errors

### `deleteRows` Without a Filter

**Symptom**: `deleteRows` action rejected.

**Why**: By design. `deleteRows` requires a filter (cannot delete all rows without one). This is a guardrail.

**Bad**:

```javascript
n8n_manage_datatable({ action: "deleteRows", tableId: "dt-123" })  // rejected
```

**Good**:

```javascript
n8n_manage_datatable({
  action: "deleteRows",
  tableId: "dt-123",
  filter: { filters: [{ columnName: "status", condition: "eq", value: "archived" }] }
})

// Or use dryRun first
n8n_manage_datatable({
  action: "deleteRows",
  tableId: "dt-123",
  filter: { filters: [{ columnName: "status", condition: "eq", value: "archived" }] },
  dryRun: true
})
```

### Bulk Update Without `dryRun`

**Symptom**: You wrote a wrong filter and bulk-updated 10,000 rows you did not mean to touch.

**Why**: `dryRun: true` previews the affected row count without applying changes. Use it before any bulk update or delete.

**Bad**:

```javascript
n8n_manage_datatable({
  action: "updateRows",
  tableId: "dt-123",
  filter: { filters: [...] },
  data: { status: "inactive" }
})
```

**Good**:

```javascript
// Preview
const preview = n8n_manage_datatable({
  action: "updateRows",
  tableId: "dt-123",
  filter: { filters: [...] },
  data: { status: "inactive" },
  dryRun: true
})
// Confirm the count, then apply
n8n_manage_datatable({ /* same call without dryRun */ })
```

---

## False Positives in Validation

### Treating Every Warning as a Blocker

**Symptom**: Validation warnings accumulate and you cannot tell which to fix.

**Why**: Warnings are best-practice nudges, not blockers. Roughly 40% are acceptable false positives in specific use cases. Errors block execution; warnings are advisory.

**Bad**: Refuse to ship until all warnings clear.

**Good**: Fix errors first. Triage warnings by use case. If warnings dominate (especially in AI-generated configs), switch to the `ai-friendly` profile.

```javascript
validate_node({ nodeType, config, profile: "ai-friendly" })  // ~60% fewer false positives
```

### Trying to Fix Auto-Sanitizable Warnings Manually

**Symptom**: You manually flip `singleValue` on operators based on validation warnings. Next update reverts the change. You go in circles.

**Why**: Auto-sanitization fixes these on the next workflow update. Trust it.

**Bad**:

```javascript
// Validation warns "binary operator should not have singleValue"
// You add a partial update to "fix" it manually
// Next update auto-sanitization undoes it
// Repeat
```

**Good**: Ignore the warning. The next `n8n_update_partial_workflow` call sanitizes it for free.

---

## API Availability Errors

### Calling API-Required Tools Without Credentials

**Symptom**: Workflow management tools return "API not configured" or similar.

**Why**: Tools that talk to your n8n instance need `N8N_API_URL` and `N8N_API_KEY` in the MCP server's environment.

**Bad**: Attempting `n8n_create_workflow` without configuring the env vars.

**Good**:

```javascript
// First, verify
n8n_health_check({ mode: "diagnostic" })
// → status, env vars, tool status, API connectivity

// If API tools are unavailable, fall back to local-only flow:
// search_nodes, get_node, validate_node, validate_workflow, search_templates, get_template
```

See [configuration.md](./configuration.md) for the env-var setup.

---

## See Also

- [api.md](./api.md): Parameter shapes and call signatures. Most gotchas here trace back to a parameter shape on a specific tool.
- [patterns.md](./patterns.md): The "good" shapes assembled into named patterns. Use patterns to avoid the gotchas preemptively.
- [configuration.md](./configuration.md): Environment variables that control tool availability (the source of "API not configured" gotchas).
- [../validation/](../validation/): Deeper coverage of validation error types and false positives.
- [../node-configuration/](../node-configuration/): Required fields and allowed values that drive the `missing_required` and `invalid_value` errors gotchas here are designed to avoid.
