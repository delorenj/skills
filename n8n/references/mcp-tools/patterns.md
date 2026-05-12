# MCP Tool Patterns

Named, copy-paste-ready patterns for chaining n8n-mcp tools. Each pattern is structured: when to use, the call sequence, why it works, and variants. These distill the recurring shapes from real telemetry (search before guess, validate, fix, revalidate loop, iterative editing).

---

## Search Patterns

### Pattern: Search Then Get Details

The single most common discovery shape: keyword search, then standard-detail node info.

```javascript
// Step 1: search (under 20 ms)
const results = search_nodes({ query: "slack" })

// Step 2: pick a result and get details
const details = get_node({
  nodeType: results.results[0].nodeType,
  includeExamples: true
})
```

**Why it works**: `search_nodes` returns both prefixes, so you can pass `nodeType` (short) straight into `get_node`. `includeExamples: true` adds real template-derived configs that beat raw schema for learning.

**Telemetry**: ~18 s average between Step 1 and Step 2 (user reviewing results).

### Pattern: OR vs AND vs FUZZY Mode Selection

Pick the search mode based on what you know:

| You know | Mode | Why |
|---|---|---|
| The exact service name (one keyword) | `OR` (default) | Matches anything containing the word |
| Multiple constraints that must all hold ("http" AND "request") | `AND` | Narrows by all keywords |
| Vague memory or possible typo ("slak", "googl drive") | `FUZZY` | Typo-tolerant |

```javascript
search_nodes({ query: "slack" })                           // OR (default)
search_nodes({ query: "http request", mode: "AND" })       // both words required
search_nodes({ query: "slak", mode: "FUZZY" })             // typo-tolerant
```

### Pattern: Narrow by Source

Restrict to first-party nodes when community nodes confuse results:

```javascript
search_nodes({ query: "ai agent", source: "core" })        // built-in only
search_nodes({ query: "weather", source: "verified" })     // verified community nodes
```

### Pattern: Property Search Within a Node

When you know the node but need a specific field (often auth):

```javascript
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "auth",          // or "header", "body", "json", "url", "method", "credential"
  maxPropertyResults: 20
})
```

**Why it works**: Avoids loading the full schema (3-8K tokens) when you only need one property path.

### Pattern: Docs vs Schema

When you are learning a node for the first time, prefer `mode: "docs"` over higher detail levels:

```javascript
get_node({ nodeType: "nodes-base.slack", mode: "docs" })
```

Returns formatted markdown (usage examples, auth guide, common patterns, best practices). Better for humans (and humans-in-the-loop AI) than raw schema.

### Pattern: Version Compatibility Check

Before upgrading a workflow's node typeVersion, scan for breaking changes:

```javascript
// See all versions
get_node({ nodeType: "nodes-base.executeWorkflow", mode: "versions" })

// Only breaking changes from a known version
get_node({
  nodeType: "nodes-base.executeWorkflow",
  mode: "breaking",
  fromVersion: "1.0"
})

// Auto-migratable changes
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "migrations",
  fromVersion: "3.0"
})
```

### Pattern: Quick Metadata Sanity Check

When you just need "what does this node do?":

```javascript
get_node({ nodeType: "nodes-base.slack", detail: "minimal" })
// → ~200 tokens, nodeType, displayName, description, category
```

---

## Validation Patterns

### Pattern: Validation Loop (Configure, Validate, Fix, Revalidate)

The canonical iterative pattern. Telemetry shows 7,266 occurrences with average 23 s thinking about errors, 58 s fixing per cycle.

```javascript
// Iteration 1
let config = { resource: "channel", operation: "create" };

let result = validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "runtime"
})
// → { valid: false, errors: [{ property: "name", message: "Channel name is required" }] }

// Fix (~58 s)
config.name = "general"

// Iteration 2
result = validate_node({ nodeType: "nodes-base.slack", config, profile: "runtime" })
// → { valid: true }
```

**Why it works**: Each cycle narrows the error set. Use `errors[].fix` from the response as the immediate next change.

### Pattern: Progressive Validation by Profile

Tighten the profile as the workflow matures:

| Stage | Profile | Why |
|---|---|---|
| Early editing | `minimal` | Just check required fields |
| Pre-deployment | `runtime` | Balanced. Catches real errors |
| AI-generated configs | `ai-friendly` | Reduces false positives by ~60% |
| Production | `strict` | Maximum thoroughness |

```javascript
// Early: see required fields
validate_node({ nodeType: "nodes-base.slack", config: {}, mode: "minimal" })

// Pre-deployment
validate_node({ nodeType: "nodes-base.slack", config, profile: "runtime" })

// Production
validate_node({ nodeType: "nodes-base.slack", config, profile: "strict" })
```

### Pattern: Discover Required Fields Up Front

Before writing config from scratch, ask validate_node what is required:

```javascript
validate_node({ nodeType: "nodes-base.slack", config: {}, mode: "minimal" })
// → { valid: true, missingRequiredFields: [...] }
```

Use the result as a checklist.

### Pattern: Whole-Workflow Validation Before Create

Validate the assembled JSON before persisting it. Cheaper than create-then-validate.

```javascript
validate_workflow({
  workflow: { nodes, connections },
  options: {
    validateNodes: true,
    validateConnections: true,
    validateExpressions: true,
    profile: "runtime"
  }
})
```

### Pattern: Edit Then Revalidate

Most common post-edit shape (7,841 occurrences in telemetry):

```javascript
n8n_update_partial_workflow({ id, intent, operations: [...] })
// ~23 s thinking about what to validate
n8n_validate_workflow({ id })
```

### Pattern: Auto-Fix Then Revalidate

When validation reports the kind of error `n8n_autofix_workflow` can resolve, run preview first, then apply:

```javascript
// Preview
const preview = n8n_autofix_workflow({
  id: "wf-abc",
  applyFixes: false,
  confidenceThreshold: "medium"
})

// Apply
n8n_autofix_workflow({ id: "wf-abc", applyFixes: true })

// Revalidate
n8n_validate_workflow({ id: "wf-abc" })
```

Check `postUpdateGuidance` in the response for manual follow-up after version upgrades.

---

## Workflow Editing Patterns

### Pattern: Iterative Build (Not One-Shot)

Workflows are built across many partial updates (31,464 occurrences in telemetry, 56 s avg between edits). Resist the temptation to construct everything in one call.

```javascript
// Edit 1: add trigger
n8n_update_partial_workflow({
  id,
  intent: "Add webhook trigger",
  operations: [{ type: "addNode", node: { /* webhook */ } }]
})

// ~56 s thinking, planning next step

// Edit 2: add processor
n8n_update_partial_workflow({
  id,
  intent: "Add processor node",
  operations: [{ type: "addNode", node: { /* set */ } }]
})

// Edit 3: connect them
n8n_update_partial_workflow({
  id,
  intent: "Connect webhook to processor",
  operations: [{ type: "addConnection", source: "Webhook", target: "Set" }]
})

// Edit 4: validate
n8n_validate_workflow({ id })

// Edit 5: activate
n8n_update_partial_workflow({
  id,
  intent: "Activate workflow",
  operations: [{ type: "activateWorkflow" }]
})
```

**Why it works**: Each step is small enough to validate independently. Auto-sanitization runs on every update and cleans operator structures. Errors surface near the cause.

### Pattern: Always Pass `intent`

Include a free-text `intent` on every `n8n_update_partial_workflow` call. Better tool responses, better downstream AI reasoning.

```javascript
n8n_update_partial_workflow({
  id,
  intent: "Add error handling for API failures",  // describe WHY
  operations: [...]
})
```

### Pattern: Smart Parameters for Branches

Use `branch` and `case` instead of `sourceIndex` for IF and Switch nodes. They are clearer and survive node renames.

```javascript
// IF node
{ type: "addConnection", source: "IF", target: "True Handler", branch: "true" }
{ type: "addConnection", source: "IF", target: "False Handler", branch: "false" }

// Switch node
{ type: "addConnection", source: "Switch", target: "Handler A", case: 0 }
{ type: "addConnection", source: "Switch", target: "Handler B", case: 1 }
```

### Pattern: AI Connections with `sourceOutput`

For AI agent workflows, AI side-inputs use the 8 typed outputs.

```javascript
n8n_update_partial_workflow({
  id,
  intent: "Wire LLM, memory, and tool to AI Agent",
  operations: [
    { type: "addConnection", source: "OpenAI Chat Model", target: "AI Agent", sourceOutput: "ai_languageModel" },
    { type: "addConnection", source: "HTTP Request Tool", target: "AI Agent", sourceOutput: "ai_tool" },
    { type: "addConnection", source: "Window Buffer Memory", target: "AI Agent", sourceOutput: "ai_memory" }
  ]
})
```

Types: `ai_languageModel`, `ai_tool`, `ai_memory`, `ai_outputParser`, `ai_embedding`, `ai_vectorStore`, `ai_document`, `ai_textSplitter`.

### Pattern: Property Removal with `null`

Use `null` in `updates` to remove a property cleanly. Especially useful when migrating from deprecated property names.

```javascript
n8n_update_partial_workflow({
  id,
  intent: "Migrate HTTP error handling from deprecated continueOnFail",
  operations: [{
    type: "updateNode",
    nodeName: "HTTP Request",
    updates: {
      continueOnFail: null,
      onError: "continueErrorOutput"
    }
  }]
})
```

### Pattern: Credential Attachment (Nested Shape)

Credentials always nest by credential type with `id` and `name`:

```javascript
n8n_update_partial_workflow({
  id,
  intent: "Attach API key to HTTP Request",
  operations: [{
    type: "updateNode",
    nodeName: "HTTP Request",
    updates: {
      credentials: {
        httpHeaderAuth: { id: "abc123", name: "My API Key" }
      }
    }
  }]
})
```

See [gotchas.md](./gotchas.md) for the flat-object failure mode.

### Pattern: Surgical String Edits with `patchNodeField`

When you only need to change a substring (code, HTML, email template, JSON body), prefer `patchNodeField` over a full `updateNode`. Strict error handling catches mistakes early.

```javascript
// Basic
n8n_update_partial_workflow({
  id,
  intent: "Bump API page size",
  operations: [{
    type: "patchNodeField",
    nodeName: "Code",
    fieldPath: "parameters.jsCode",
    patches: [{ find: "const limit = 10;", replace: "const limit = 50;" }]
  }]
})

// Replace all
n8n_update_partial_workflow({
  id,
  intent: "Migrate API domain",
  operations: [{
    type: "patchNodeField",
    nodeName: "Code",
    fieldPath: "parameters.jsCode",
    patches: [{ find: "api.old.com", replace: "api.new.com", replaceAll: true }]
  }]
})

// Multiple sequential patches on a template
n8n_update_partial_workflow({
  id,
  intent: "Refresh email template footer",
  operations: [{
    type: "patchNodeField",
    nodeName: "Set Email",
    fieldPath: "parameters.assignments.assignments.6.value",
    patches: [
      { find: "© 2025", replace: "© 2026" },
      { find: "<p>Unsubscribe</p>", replace: "" }
    ]
  }]
})

// Regex (whitespace-insensitive)
operations: [{
  type: "patchNodeField",
  nodeName: "Code",
  fieldPath: "parameters.jsCode",
  patches: [{ find: "const\\s+limit\\s*=\\s*\\d+", replace: "const limit = 100", regex: true }]
}]
```

Behavior: errors on miss (not silent), errors on multiple matches without `replaceAll: true`. Use these errors as a safety net.

### Pattern: Preview Before Apply

Use `validateOnly: true` to preview an update without applying. Or `continueOnError: true` to apply only the operations that work.

```javascript
// Preview
n8n_update_partial_workflow({ id, operations, validateOnly: true })

// Best-effort apply
n8n_update_partial_workflow({ id, operations, continueOnError: true })
```

---

## Quick Start Strategies

### Pattern: Template-First Build

When the task matches a known template, deploy first, customize after:

```javascript
// 1. Find candidate templates
search_templates({ query: "webhook slack", limit: 5 })

// 2. Inspect one
get_template({ templateId: 2947, mode: "structure" })

// 3. Deploy with custom name
const result = n8n_deploy_template({
  templateId: 2947,
  name: "Production Slack Notifier"
})

// 4. Customize iteratively
n8n_update_partial_workflow({ id: result.id, intent: "...", operations: [...] })

// 5. Validate
n8n_validate_workflow({ id: result.id })
```

### Pattern: NL Generation (Hosted Only)

When the user describes the workflow in plain English and you are on hosted n8n:

```javascript
// Step 1: get proposals
n8n_generate_workflow({
  description: "When a new row is added to the 'leads' Postgres table, enrich it with Clearbit, then post a summary to the #sales Slack channel. Skip rows where 'company' is empty."
})
// → { status: "proposals", proposals: [...] }

// Step 2: deploy the proposal that fits
n8n_generate_workflow({ description: "...same...", deploy_id: "uuid-1" })
// → { status: "deployed", workflow_id: "abc" }

// Step 3: validate immediately (generator can miss things)
n8n_validate_workflow({ id: "abc" })

// Step 4: autofix if needed
n8n_autofix_workflow({ id: "abc", applyFixes: true })
```

**Description quality matters**: name services explicitly (Slack, Gmail, Postgres), specify the trigger cadence (cron, webhook, schedule), and describe branches and edge cases.

### Pattern: Manual Build (Self-Hosted, Full Control)

When you need precise control and no template fits:

```javascript
// 1. Search for each node
search_nodes({ query: "webhook" })
search_nodes({ query: "set" })
search_nodes({ query: "slack" })

// 2. Get details for each
get_node({ nodeType: "nodes-base.webhook" })
get_node({ nodeType: "nodes-base.set" })
get_node({ nodeType: "nodes-base.slack" })

// 3. Validate each config locally
validate_node({ nodeType: "nodes-base.webhook", config: {...}, profile: "runtime" })

// 4. Validate the assembled workflow JSON
validate_workflow({ workflow: { nodes, connections }, options: { profile: "runtime" } })

// 5. Create
const created = n8n_create_workflow({ name, nodes, connections })

// 6. Validate stored version
n8n_validate_workflow({ id: created.id })

// 7. Iterate
n8n_update_partial_workflow({ id: created.id, intent: "...", operations: [...] })
```

---

## Recovery Patterns

### Pattern: Clean Stale Connections

After renames or deletions, broken connection references can persist. Use `cleanStaleConnections`:

```javascript
n8n_update_partial_workflow({
  id,
  intent: "Remove broken connections after node deletion",
  operations: [{ type: "cleanStaleConnections" }]
})
```

### Pattern: Atomic Rewire

Change a target node atomically without disconnecting and reconnecting:

```javascript
n8n_update_partial_workflow({
  id,
  intent: "Replace deprecated handler",
  operations: [{
    type: "rewireConnection",
    source: "Webhook",
    from: "Old Handler",
    to: "New Handler"
  }]
})
```

### Pattern: Rollback via Versions

When a series of edits breaks the workflow, roll back instead of debugging forward:

```javascript
// Find the last good version
n8n_workflow_versions({ mode: "list", workflowId: "wf-abc", limit: 10 })

// Roll back (validates before applying by default)
n8n_workflow_versions({
  mode: "rollback",
  workflowId: "wf-abc",
  versionId: 122,
  validateBefore: true
})
```

---

## Credentials and Audit Patterns

### Pattern: Set Up Credentials for a New Integration

```javascript
// 1. Discover the schema
n8n_manage_credentials({ action: "getSchema", type: "slackApi" })

// 2. Create
n8n_manage_credentials({
  action: "create",
  name: "Production Slack",
  type: "slackApi",
  data: { accessToken: "xoxb-..." }
})

// 3. Verify
n8n_manage_credentials({ action: "list" })
```

### Pattern: Safely Delete or Rotate a Credential

Always check usage before destructive credential actions.

```javascript
// 1. See what depends on it
n8n_manage_credentials({ action: "get", id: "123", includeUsage: true })
// → usedIn: [{ id, name, active }, ...]

// 2a. Nothing depends on it: delete
n8n_manage_credentials({ action: "delete", id: "123" })

// 2b. Something does: rotate the secret instead
n8n_manage_credentials({
  action: "update",
  id: "123",
  data: { accessToken: "xoxb-new-..." }
})
```

`includeUsage` triggers a full client-side workflow scan (n8n has no native lookup). Slower on large instances and capped at 5000 workflows. A "no usages" result does not prove a credential is unused; archived workflows are excluded.

### Pattern: Audit-Then-Remediate Loop

```javascript
// 1. Audit
const report = n8n_audit_instance()

// 2. For each auto-fixable finding, apply the suggested tool chain
//    (e.g., add auth to webhooks, fix error handling)

// 3. For "user_input_needed", surface the choice
// 4. For "user_action_needed", emit a manual checklist (e.g., rotate exposed keys)

// 5. Re-audit
n8n_audit_instance()
```

### Pattern: Targeted Audit Subset

Scan for one issue type to keep the report focused:

```javascript
n8n_audit_instance({
  customChecks: ["hardcoded_secrets"],
  includeCustomScan: true
})

n8n_audit_instance({
  customChecks: ["unauthenticated_webhooks"]
})
```

---

## Execution and Testing Patterns

### Pattern: Trigger and Inspect

```javascript
// 1. Test the trigger
n8n_test_workflow({
  workflowId: "wf-abc",
  triggerType: "webhook",
  httpMethod: "POST",
  data: { message: "Hello!" },
  waitForResponse: true,
  timeout: 120000
})

// 2. Inspect execution details
n8n_executions({ action: "get", id: "exec-id", mode: "summary" })

// 3. If error, get full error context
n8n_executions({
  action: "get",
  id: "exec-id",
  mode: "error",
  includeStackTrace: true
})
```

### Pattern: Triage Failing Executions

```javascript
// List recent errors
n8n_executions({
  action: "list",
  workflowId: "wf-abc",
  status: "error",
  limit: 20
})

// Inspect each error
n8n_executions({ action: "get", id: "exec-id", mode: "error" })

// Optionally clean up old failures
n8n_executions({ action: "delete", id: "exec-id" })
```

---

## End-to-End Lifecycle

The canonical create-to-activate sequence:

```javascript
// 1. CREATE
const created = n8n_create_workflow({ name, nodes, connections })

// 2. VALIDATE
n8n_validate_workflow({ id: created.id })

// 3. EDIT (iterative, 56 s avg between edits)
n8n_update_partial_workflow({
  id: created.id,
  intent: "Add error handling",
  operations: [...]
})

// 4. REVALIDATE
n8n_validate_workflow({ id: created.id })

// 5. ACTIVATE
n8n_update_partial_workflow({
  id: created.id,
  intent: "Activate workflow for production",
  operations: [{ type: "activateWorkflow" }]
})

// 6. MONITOR
n8n_executions({ action: "list", workflowId: created.id })
n8n_executions({ action: "get", id: "exec-id" })
```

---

## Pattern Reference Card

| Goal | Pattern |
|---|---|
| Find an unknown node | [Search Then Get Details](#pattern-search-then-get-details) |
| Confirm a config is valid | [Validation Loop](#pattern-validation-loop-configure-validate-fix-revalidate) |
| Build a new workflow | [Iterative Build](#pattern-iterative-build-not-one-shot) |
| Edit a string inside a node | [Surgical String Edits with patchNodeField](#pattern-surgical-string-edits-with-patchnodefield) |
| Connect IF/Switch outputs | [Smart Parameters for Branches](#pattern-smart-parameters-for-branches) |
| Wire AI agent inputs | [AI Connections with sourceOutput](#pattern-ai-connections-with-sourceoutput) |
| Migrate deprecated properties | [Property Removal with null](#pattern-property-removal-with-null) |
| Recover from broken connections | [Clean Stale Connections](#pattern-clean-stale-connections) |
| Roll back a bad edit chain | [Rollback via Versions](#pattern-rollback-via-versions) |
| Set up credentials safely | [Set Up Credentials for a New Integration](#pattern-set-up-credentials-for-a-new-integration) |
| Rotate or delete a credential | [Safely Delete or Rotate a Credential](#pattern-safely-delete-or-rotate-a-credential) |
| Find hardcoded secrets | [Targeted Audit Subset](#pattern-targeted-audit-subset) |
| Trigger and debug a workflow | [Trigger and Inspect](#pattern-trigger-and-inspect) |

---

## See Also

- [api.md](./api.md): Tool-by-tool reference. Patterns here chain those tools; the API doc gives parameter shapes.
- [gotchas.md](./gotchas.md): The failure modes the patterns are designed to avoid.
- [configuration.md](./configuration.md): MCP server registration and environment that makes the API-requiring patterns work.
- [../validation/](../validation/): Deeper coverage of the validation responses these patterns consume.
- [../workflow-patterns/](../workflow-patterns/): Architectural patterns for workflow shapes (webhook processing, scheduled tasks, AI agent) once you have selected nodes.
