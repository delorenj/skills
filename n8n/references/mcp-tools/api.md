# MCP Tool API Reference

Tool-by-tool reference for the n8n-mcp MCP server, grouped by category. Each entry documents the call shape, parameters, return shape, and a worked example.

> Note on nodeType: search/validate tools use the SHORT prefix (`nodes-base.slack`, `nodes-langchain.agent`). Workflow tools use the FULL prefix (`n8n-nodes-base.slack`, `@n8n/n8n-nodes-langchain.agent`). `search_nodes` returns both fields (`nodeType` and `workflowNodeType`) so you can pass the right one to the right tool. See [gotchas.md](./gotchas.md) for the failure mode.

---

## Search and Discovery

### search_nodes

Find nodes by keyword. Always your first call when you do not already know the exact nodeType.

**Latency**: under 20 ms.

**Parameters**:

| Name | Type | Required | Default | Notes |
|---|---|---|---|---|
| `query` | string | yes | | Keywords ("slack", "http request", "webhook trigger") |
| `mode` | string | no | `"OR"` | `OR` (any word matches), `AND` (all words), `FUZZY` (typo-tolerant) |
| `limit` | number | no | 20 | Max results |
| `source` | string | no | `"all"` | `all`, `core`, `community`, `verified` |
| `includeExamples` | boolean | no | false | Include template-derived example configs |

**Returns**:

```javascript
{
  query: "slack",
  results: [
    {
      nodeType: "nodes-base.slack",          // For search/validate tools
      workflowNodeType: "n8n-nodes-base.slack", // For workflow tools
      displayName: "Slack",
      description: "Consume Slack API",
      category: "output",
      relevance: "high"
    }
  ]
}
```

**Example**:

```javascript
search_nodes({ query: "slack" })
search_nodes({ query: "http request", mode: "AND" })
search_nodes({ query: "slak", mode: "FUZZY" })   // typo-tolerant
search_nodes({ query: "webhook", source: "core" })
```

### get_node

Unified node-info tool. Returns schema, docs, version history, or property search results depending on `mode` and `detail`.

**Latency**: under 10 ms (standard detail), under 100 ms (full detail).

**Parameters (mode = "info", the default)**:

| Name | Type | Required | Default | Notes |
|---|---|---|---|---|
| `nodeType` | string | yes | | SHORT prefix, e.g. `nodes-base.slack` |
| `detail` | string | no | `"standard"` | `minimal` (~200 tokens), `standard` (~1-2K, RECOMMENDED), `full` (~3-8K, use sparingly) |
| `includeExamples` | boolean | no | false | Adds 200-400 tokens per example. Works in `mode: "info"`, `detail: "standard"` |
| `includeTypeInfo` | boolean | no | false | Adds type structure metadata (validation rules, JS types). 80-120 tokens per property |

**Other modes** (override default `mode: "info"`):

| Mode | Extra Params | Purpose |
|---|---|---|
| `docs` | none | Returns human-readable markdown documentation (usage, auth, patterns, best practices) |
| `search_properties` | `propertyQuery` (required), `maxPropertyResults` (default 20) | Find specific properties matching a keyword like "auth", "header", "body" |
| `versions` | none | List version history with breaking-change flags |
| `compare` | `fromVersion` (required), `toVersion` (optional, defaults to latest) | Property-level diff between two versions |
| `breaking` | `fromVersion` (required) | Only the breaking changes |
| `migrations` | `fromVersion` (required) | Changes that can be auto-migrated |

**Examples**:

```javascript
// Standard (recommended for 95% of cases)
get_node({ nodeType: "nodes-base.slack" })

// With real-world example configs
get_node({ nodeType: "nodes-base.slack", includeExamples: true })

// Quick metadata only
get_node({ nodeType: "nodes-base.slack", detail: "minimal" })

// Full schema (debugging only)
get_node({ nodeType: "nodes-base.httpRequest", detail: "full" })

// Readable docs
get_node({ nodeType: "nodes-base.slack", mode: "docs" })

// Find a specific property
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "auth"
})

// Check versions
get_node({ nodeType: "nodes-base.executeWorkflow", mode: "versions" })

// Breaking changes from a known version
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "breaking",
  fromVersion: "3.0"
})
```

### get_suggested_nodes

Returns curated node recommendations for a workflow technique. Useful as a "show me the canonical nodes for X" call after you have a high-level concept but not a specific service.

```javascript
get_suggested_nodes({ categories: ["webhook_processing", "rate_limited_api"] })
```

### get_sdk_reference

Returns the n8n Workflow SDK reference, used when programmatically building workflow code that you will pass to `create_workflow_from_code` or related tools. Request specific sections (`guidelines`, `design`) when you need targeted guidance.

```javascript
get_sdk_reference()
get_sdk_reference({ sections: ["guidelines", "design"] })
```

---

## Validation

### validate_node

Unified node-config validator. Two modes (`full` default, `minimal`), four profiles (`minimal`, `runtime`, `ai-friendly`, `strict`).

**Latency**: 50-100 ms.

**Parameters**:

| Name | Type | Required | Default | Notes |
|---|---|---|---|---|
| `nodeType` | string | yes | | SHORT prefix |
| `config` | object | yes | | The node parameters to validate. Pass `{}` to see all required fields |
| `mode` | string | no | `"full"` | `full` (comprehensive), `minimal` (required-fields only, under 50 ms) |
| `profile` | string | no | `"runtime"` | `minimal`, `runtime` (RECOMMENDED), `ai-friendly`, `strict` |

**Returns**:

```javascript
{
  nodeType: "nodes-base.slack",
  workflowNodeType: "n8n-nodes-base.slack",
  displayName: "Slack",
  valid: false,
  errors: [
    { type: "missing_required", property: "name", message: "Channel name is required", fix: "Provide a channel name (lowercase, no spaces, 1-80 characters)" }
  ],
  warnings: [
    { type: "best_practice", property: "errorHandling", message: "Slack API can have rate limits", suggestion: "Add onError: 'continueRegularOutput' with retryOnFail" }
  ],
  suggestions: [],
  summary: { hasErrors: true, errorCount: 1, warningCount: 1, suggestionCount: 0 }
}
```

**Error types**: `missing_required`, `invalid_value`, `type_mismatch`, `best_practice` (warning), `suggestion`.

**Profile selection**:

| Profile | Use When |
|---|---|
| `minimal` | Quick checks during early editing. Most permissive |
| `runtime` | Pre-deployment validation. Balanced. The recommended default |
| `ai-friendly` | AI-generated configs. Reduces false positives by ~60% |
| `strict` | Production deployment. Most thorough |

**Examples**:

```javascript
// See all required fields
validate_node({ nodeType: "nodes-base.slack", config: {}, mode: "minimal" })

// Full pre-deployment check
validate_node({
  nodeType: "nodes-base.slack",
  config: { resource: "channel", operation: "create", name: "general" },
  profile: "runtime"
})

// Production strict
validate_node({ nodeType: "nodes-base.webhook", config, profile: "strict" })
```

### validate_workflow

Validate a complete workflow object (not yet stored in n8n). Use this on locally-assembled workflow JSON before calling `n8n_create_workflow`.

**Latency**: 100-500 ms.

**Parameters**:

| Name | Type | Required | Default | Notes |
|---|---|---|---|---|
| `workflow` | object | yes | | `{ nodes: [...], connections: {...} }` |
| `options.validateNodes` | boolean | no | true | Validate each node config |
| `options.validateConnections` | boolean | no | true | Validate connection references |
| `options.validateExpressions` | boolean | no | true | Validate `={{ }}` expressions |
| `options.profile` | string | no | `"runtime"` | Profile passed to per-node validation |

**Returns**: Same shape as `validate_node`, but with errors aggregated per node plus workflow-level errors (broken connections, missing triggers, AI connection issues, etc.).

```javascript
validate_workflow({
  workflow: {
    nodes: [/* ... */],
    connections: {/* ... */}
  },
  options: {
    validateNodes: true,
    validateConnections: true,
    validateExpressions: true,
    profile: "runtime"
  }
})
```

### n8n_validate_workflow

Validate a workflow already stored in your n8n instance (by ID). Requires n8n API.

```javascript
n8n_validate_workflow({
  id: "wf-abc",
  options: {
    validateNodes: true,
    validateConnections: true,
    validateExpressions: true,
    profile: "runtime"
  }
})
```

### n8n_autofix_workflow

Preview or apply automatic fixes for common validation errors on a workflow stored in n8n.

**Parameters**:

| Name | Type | Required | Default | Notes |
|---|---|---|---|---|
| `id` | string | yes | | Workflow ID |
| `applyFixes` | boolean | no | false | `false` is preview-only, `true` applies |
| `confidenceThreshold` | string | no | `"medium"` | `high` (90%+), `medium` (70-89%), `low` (any) |

**Fix types** the tool can apply:

- `expression-format`: Add missing `=` prefix to expressions.
- `typeversion-correction`: Downgrade unsupported typeVersions.
- `error-output-config`: Remove conflicting onError settings.
- `node-type-correction`: Fix unknown node types via similarity matching (90%+ confidence).
- `webhook-missing-path`: Generate UUIDs for webhook nodes missing paths.
- `typeversion-upgrade`: Smart upgrade of nodes to latest version with auto-migration.
- `version-migration`: Provides guidance for breaking changes that need manual handling.

Check `postUpdateGuidance` in the response for any manual follow-up steps.

```javascript
// Preview
n8n_autofix_workflow({ id: "wf-abc", applyFixes: false, confidenceThreshold: "medium" })

// Apply
n8n_autofix_workflow({ id: "wf-abc", applyFixes: true })
```

---

## Workflow Management

### n8n_create_workflow

Create a new workflow from `nodes` and `connections`.

**Latency**: 100-500 ms.

**Parameters**:

| Name | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Workflow name |
| `nodes` | array | yes | Array of node objects (use FULL prefix `n8n-nodes-base.*` in `type`) |
| `connections` | object | yes | Connections object keyed by source node name |
| `settings` | object | no | Workflow settings |

**Workflows are created inactive**. Use `activateWorkflow` operation to enable. Auto-sanitization runs on create.

**Example**:

```javascript
n8n_create_workflow({
  name: "Webhook to Slack",
  nodes: [
    {
      id: "webhook-1",
      name: "Webhook",
      type: "n8n-nodes-base.webhook",  // FULL prefix
      typeVersion: 2,
      position: [250, 300],
      parameters: { path: "slack-notify", httpMethod: "POST" }
    },
    {
      id: "slack-1",
      name: "Slack",
      type: "n8n-nodes-base.slack",
      typeVersion: 2,
      position: [450, 300],
      parameters: {
        resource: "message",
        operation: "post",
        channel: "#general",
        text: "={{$json.body.message}}"
      }
    }
  ],
  connections: {
    "Webhook": { "main": [[{ node: "Slack", type: "main", index: 0 }]] }
  }
})
```

### create_workflow_from_code

Alternate creation path using SDK code (as opposed to the explicit nodes/connections shape). Pair with `get_sdk_reference` and `validate_workflow` first. Include a short `description` so users can find and recognize the workflow.

```javascript
create_workflow_from_code({
  code: /* SDK source string */,
  description: "Posts a Slack message every weekday at 9am with the daily standup link"
})
```

### n8n_update_partial_workflow

The single most-used n8n-mcp tool (over 38,000 uses in telemetry). Apply a list of typed operations to an existing workflow. 56-second average between successive edits, indicating iterative building.

**Latency**: 50-200 ms.

**Parameters**:

| Name | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Workflow ID |
| `intent` | string | no | Free-text description of what you are doing. IMPORTANT: include it. Better AI responses |
| `operations` | array | yes | List of typed operations (see below) |
| `continueOnError` | boolean | no | Best-effort mode: apply what works, skip what fails |
| `validateOnly` | boolean | no | Preview without applying |

**19 operation types**:

Node operations (7):

| Type | Purpose |
|---|---|
| `addNode` | Add a new node |
| `removeNode` | Remove a node by ID or name |
| `updateNode` | Update node properties using dot notation. Use `updates: {...}` (NOT `parameters: {...}`) |
| `patchNodeField` | Strict find/replace on a single string field (preferred for code, HTML, templates) |
| `moveNode` | Change position |
| `enableNode` | Enable a disabled node |
| `disableNode` | Disable an active node |

Connection operations (5):

| Type | Purpose |
|---|---|
| `addConnection` | Connect nodes. Supports smart params (`branch`, `case`) and `sourceOutput` for AI connections |
| `removeConnection` | Remove a connection. Supports `ignoreErrors` |
| `rewireConnection` | Atomically change a connection target |
| `cleanStaleConnections` | Auto-remove broken connections (references to non-existent nodes) |
| `replaceConnections` | Replace the entire connections object |

Metadata operations (4): `updateSettings`, `updateName`, `addTag`, `removeTag`.

Activation operations (2): `activateWorkflow`, `deactivateWorkflow`.

Project management (1): `transferWorkflow` (enterprise/cloud).

**Smart parameters** (use these instead of `sourceIndex`):

```javascript
// IF node
{ type: "addConnection", source: "IF", target: "True Handler", branch: "true" }
{ type: "addConnection", source: "IF", target: "False Handler", branch: "false" }

// Switch node
{ type: "addConnection", source: "Switch", target: "Handler A", case: 0 }
{ type: "addConnection", source: "Switch", target: "Handler B", case: 1 }
```

**AI connection types** (use `sourceOutput`):

`ai_languageModel`, `ai_tool`, `ai_memory`, `ai_outputParser`, `ai_embedding`, `ai_vectorStore`, `ai_document`, `ai_textSplitter`.

```javascript
{ type: "addConnection", source: "OpenAI Chat Model", target: "AI Agent", sourceOutput: "ai_languageModel" }
{ type: "addConnection", source: "HTTP Request Tool", target: "AI Agent", sourceOutput: "ai_tool" }
{ type: "addConnection", source: "Window Buffer Memory", target: "AI Agent", sourceOutput: "ai_memory" }
```

**Property removal**: set the property to `null` in `updates`.

```javascript
{
  type: "updateNode",
  nodeName: "HTTP Request",
  updates: {
    continueOnFail: null,           // Remove deprecated property
    onError: "continueErrorOutput"  // Add new property
  }
}
```

**Credential attachment** (nested by credential type, with `id` and `name`):

```javascript
{
  type: "updateNode",
  nodeName: "HTTP Request",
  updates: {
    credentials: {
      httpHeaderAuth: { id: "abc123", name: "My API Key" }
    }
  }
}
```

**`patchNodeField` (surgical string edit, strict mode)**:

Prefer `patchNodeField` over `updateNode` with `__patch_find_replace` for editing strings (code, HTML, email templates, JSON bodies). Strict behavior:

- Find string not found: operation fails (not a silent warning).
- Multiple matches without `replaceAll: true`: operation fails (ambiguity detected).
- Patches are applied sequentially. Order matters.

Parameters per patch:

| Name | Type | Required | Default | Notes |
|---|---|---|---|---|
| `find` | string | yes | | Literal string or regex |
| `replace` | string | yes | | Replacement |
| `replaceAll` | boolean | no | false | Replace all occurrences |
| `regex` | boolean | no | false | Treat `find` as regex (ReDoS-safe patterns only) |

Security limits: max 50 patches per operation, regex patterns capped at 500 chars, regex only on fields under 512 KB, rejects nested quantifiers and overlapping alternations, prototype pollution protection on field paths.

```javascript
n8n_update_partial_workflow({
  id: "wf-abc",
  intent: "Bump API page size",
  operations: [{
    type: "patchNodeField",
    nodeName: "Code",
    fieldPath: "parameters.jsCode",
    patches: [{ find: "const limit = 10;", replace: "const limit = 50;" }]
  }]
})

// Replace all occurrences (URL migration)
n8n_update_partial_workflow({
  id: "wf-abc",
  intent: "Migrate API domain",
  operations: [{
    type: "patchNodeField",
    nodeName: "Code",
    fieldPath: "parameters.jsCode",
    patches: [{ find: "api.old.com", replace: "api.new.com", replaceAll: true }]
  }]
})

// Regex
n8n_update_partial_workflow({
  id: "wf-abc",
  intent: "Normalize limit constant",
  operations: [{
    type: "patchNodeField",
    nodeName: "Code",
    fieldPath: "parameters.jsCode",
    patches: [{ find: "const\\s+limit\\s*=\\s*\\d+", replace: "const limit = 100", regex: true }]
  }]
})
```

**Activation** (use the activation operations, not a separate API call):

```javascript
n8n_update_partial_workflow({
  id: "wf-abc",
  intent: "Activate workflow for production",
  operations: [{ type: "activateWorkflow" }]
})
```

**Recovery operations**:

```javascript
// Remove broken connections
{ type: "cleanStaleConnections" }

// Atomically change target
{ type: "rewireConnection", source: "Webhook", from: "Old Handler", to: "New Handler" }
```

### n8n_update_full_workflow

Full workflow replacement (versus partial). Rare. Prefer `n8n_update_partial_workflow` for almost all edits.

### n8n_get_workflow

Retrieve a workflow. Pick a `mode` to control payload size.

| Mode | Returns |
|---|---|
| `full` (default) | Complete workflow JSON |
| `details` | Full + execution stats |
| `structure` | Nodes + connections only |
| `minimal` | id, name, active, tags |

```javascript
n8n_get_workflow({ id: "wf-abc" })
n8n_get_workflow({ id: "wf-abc", mode: "structure" })
n8n_get_workflow({ id: "wf-abc", mode: "minimal" })
```

### n8n_list_workflows

List workflows with filtering. Pair with `n8n_get_workflow` for details.

### n8n_delete_workflow

Permanently delete a workflow by ID.

### archive_workflow

Soft-delete (archive) a workflow.

### publish_workflow / unpublish_workflow

Workflow publishing controls.

### n8n_workflow_versions

Version control: list, get, rollback, delete, prune.

```javascript
// List versions
n8n_workflow_versions({ mode: "list", workflowId: "wf-abc", limit: 10 })

// Get a specific version
n8n_workflow_versions({ mode: "get", versionId: 123 })

// Rollback (validates by default before applying)
n8n_workflow_versions({
  mode: "rollback",
  workflowId: "wf-abc",
  versionId: 123,
  validateBefore: true
})

// Delete one version
n8n_workflow_versions({ mode: "delete", workflowId: "wf-abc", versionId: 123 })

// Delete all versions for a workflow
n8n_workflow_versions({ mode: "delete", workflowId: "wf-abc", deleteAll: true })

// Prune to most recent N
n8n_workflow_versions({ mode: "prune", workflowId: "wf-abc", maxVersions: 10 })
```

### n8n_test_workflow

Trigger a workflow execution for testing. Auto-detects trigger type.

```javascript
// Webhook trigger
n8n_test_workflow({
  workflowId: "wf-abc",
  triggerType: "webhook",   // optional, auto-detected
  httpMethod: "POST",
  data: { message: "Hello!" },
  waitForResponse: true,
  timeout: 120000
})

// Chat trigger
n8n_test_workflow({
  workflowId: "wf-abc",
  triggerType: "chat",
  message: "Hello, AI agent!",
  sessionId: "session-123"
})
```

### execute_workflow

Programmatically execute a workflow (less interactive than `n8n_test_workflow`).

---

## Templates

### search_templates

Search the curated template library (2,700+ workflows).

```javascript
// Keyword search (default)
search_templates({ query: "webhook slack", limit: 20 })

// By node types
search_templates({
  searchMode: "by_nodes",
  nodeTypes: ["n8n-nodes-base.httpRequest", "n8n-nodes-base.slack"]
})

// By task type
search_templates({ searchMode: "by_task", task: "webhook_processing" })

// By metadata
search_templates({
  searchMode: "by_metadata",
  complexity: "simple",
  maxSetupMinutes: 15
})
```

### get_template

Retrieve template content.

```javascript
get_template({ templateId: 2947, mode: "structure" })  // nodes+connections only
get_template({ templateId: 2947, mode: "full" })       // complete workflow JSON
```

### n8n_deploy_template

Deploy a template directly to your n8n instance.

**Latency**: 200-500 ms.

**Parameters**:

| Name | Type | Required | Default | Notes |
|---|---|---|---|---|
| `templateId` | number | yes | | Template ID from n8n.io or `search_templates` |
| `name` | string | no | | Custom workflow name (optional) |
| `autoFix` | boolean | no | true | Auto-fix common issues |
| `autoUpgradeVersions` | boolean | no | true | Upgrade node typeVersions |
| `stripCredentials` | boolean | no | true | Remove credential references from the template |

**Returns**: Workflow ID, `requiredCredentials`, `fixesApplied`.

```javascript
const result = n8n_deploy_template({
  templateId: 2947,
  name: "Production Slack Notifier"
})
// result.id, result.requiredCredentials, result.fixesApplied
```

---

## Workflow Generation

### n8n_generate_workflow

Natural-language to workflow with a two-step review checkpoint.

> Hosted-only. On self-hosted instances the response is `{ hosted_only: true, ... }` with a redirect message. For self-hosted, fall back to `n8n_deploy_template` (templates) or `n8n_create_workflow` (manual).

**Latency**: proposals ~2 s, fresh generation 5-15 s, deploy ~3 s.

**Parameters**:

| Name | Type | Required | Notes |
|---|---|---|---|
| `description` | string | yes | Natural-language description |
| `deploy_id` | string | no | UUID of a proposal from a prior call. Deploys that proposal |
| `skip_cache` | boolean | no | Skip the proposal cache; return a fresh preview (NOT deployed) |
| `confirm_deploy` | boolean | no | Deploy the most recent preview in this session |

**Two paths**:

Path A (default, recommended): proposals then deploy.

```javascript
// Step 1: get up to 5 proposals (NOT deployed)
n8n_generate_workflow({ description: "Slack daily standup reminder at 9am every weekday" })
// → { status: "proposals", proposals: [{ id, name, description, flow_summary, credentials_needed }, ...] }

// Step 2: deploy the proposal you want
n8n_generate_workflow({
  description: "Slack daily standup reminder at 9am every weekday",
  deploy_id: "uuid-1"
})
// → { status: "deployed", workflow_id, workflow_name, workflow_url, node_count, node_summary }
```

Path B: skip proposals, fresh preview, confirm.

```javascript
n8n_generate_workflow({
  description: "Webhook receives JSON, transforms it, POSTs to a REST API",
  skip_cache: true
})
// → { status: "preview", ... }

n8n_generate_workflow({
  description: "Webhook receives JSON, transforms it, POSTs to a REST API",
  confirm_deploy: true
})
// → { status: "deployed", ... }
```

**Caveats**:

- Hosted-only.
- Generated workflows deploy in inactive state. Configure credentials in n8n UI before activating.
- Proposals/preview live in per-MCP-session state; reconnecting loses them.
- Always run `n8n_validate_workflow({ id })` after deployment.

**Tool comparison**:

| Goal | Tool |
|---|---|
| Pick from a curated 2,700+ template library | `n8n_deploy_template` |
| Describe what you want in plain English (hosted only) | `n8n_generate_workflow` |
| Build node-by-node with full control | `n8n_create_workflow` |

---

## Data Tables

### n8n_manage_datatable

Unified CRUD on n8n data tables and rows. Supports filtering, pagination, dry-run.

**Latency**: 50-500 ms.

**Table actions**: `createTable`, `listTables`, `getTable`, `updateTable`, `deleteTable`.

**Row actions**: `getRows`, `insertRows`, `updateRows`, `upsertRows`, `deleteRows`.

**Filter conditions**: `eq`, `neq`, `like`, `ilike`, `gt`, `gte`, `lt`, `lte`.

**Examples**:

```javascript
// Create a table
n8n_manage_datatable({
  action: "createTable",
  name: "Contacts",
  columns: [
    { name: "email", type: "string" },
    { name: "score", type: "number" }
  ]
})

// Get rows with a filter
n8n_manage_datatable({
  action: "getRows",
  tableId: "dt-123",
  filter: { filters: [{ columnName: "status", condition: "eq", value: "active" }] },
  limit: 50
})

// Insert rows
n8n_manage_datatable({
  action: "insertRows",
  tableId: "dt-123",
  data: [{ email: "a@b.com", score: 10 }],
  returnType: "all"     // or "count" (default, smaller response)
})

// Bulk update with dry run preview
n8n_manage_datatable({
  action: "updateRows",
  tableId: "dt-123",
  filter: { filters: [{ columnName: "score", condition: "lt", value: 5 }] },
  data: { status: "inactive" },
  dryRun: true
})

// Upsert
n8n_manage_datatable({
  action: "upsertRows",
  tableId: "dt-123",
  filter: { filters: [{ columnName: "email", condition: "eq", value: "a@b.com" }] },
  data: { score: 15 },
  returnData: true
})
```

Best practices:

- Use `dryRun: true` before bulk updates or deletes.
- Define column types upfront (`string`, `number`, `boolean`, `date`).
- Use `returnType: "count"` for `insertRows` unless you need rows back.
- `deleteRows` requires a filter (cannot delete all rows without one).

Lower-level data-table tools are also exposed for direct manipulation: `create_data_table`, `add_data_table_column`, `add_data_table_rows`, `delete_data_table_column`, `rename_data_table`, `rename_data_table_column`, `search_data_tables`.

---

## Credentials

### n8n_manage_credentials

Unified credential CRUD plus schema discovery and reverse-lookup of which workflows use each credential.

**Latency**: 50-500 ms.

**Actions**: `list`, `get`, `create`, `update`, `delete`, `getSchema`.

**Optional flag**: `includeUsage` (boolean, default false). On `list` and `get`, attaches `usedIn: [{ id, name, active }]` and `usageCount` by reverse-scanning workflows.

**Examples**:

```javascript
// List
n8n_manage_credentials({ action: "list" })
// → [{ id, name, type, createdAt, updatedAt }, ...]

// Get (data field stripped for security)
n8n_manage_credentials({ action: "get", id: "123" })

// Discover required fields for a credential type
n8n_manage_credentials({ action: "getSchema", type: "httpHeaderAuth" })

// Create
n8n_manage_credentials({
  action: "create",
  name: "My Slack Token",
  type: "slackApi",
  data: { accessToken: "xoxb-..." }
})

// Update
n8n_manage_credentials({
  action: "update",
  id: "123",
  name: "Updated Name",
  data: { accessToken: "xoxb-new-..." },
  type: "slackApi"   // optional; required by some n8n versions
})

// Delete
n8n_manage_credentials({ action: "delete", id: "123" })

// List with workflow-usage info
n8n_manage_credentials({ action: "list", includeUsage: true })
// → each credential gains usedIn: [{id, name, active}] and usageCount: N
//   Response may include usageScanError if the scan failed

// Get one credential plus the workflows that reference it
n8n_manage_credentials({ action: "get", id: "123", includeUsage: true })
```

**When to use `includeUsage`**:

- Pre-delete safety check: confirm a credential is not referenced.
- Credential rotation impact analysis: list affected workflows before updating secrets.
- Remediation: locate workflows flagged by `n8n_audit_instance` for shared/over-privileged credentials.

**`includeUsage` caveats**:

- Triggers a full workflow scan client-side (no native n8n endpoint). Slower on large instances.
- Capped at 5000 workflows. Archived workflows are excluded by n8n.
- "No usages" does NOT prove a credential is unused. Verify before destructive actions.
- On scan failure the response degrades gracefully: base credentials returned with a `usageScanError` field.

**Security**:

- `get`, `create`, and `update` responses always strip the `data` field (defense-in-depth).
- `get` falls back to list+filter if direct GET returns 403/405.
- Credential request bodies are redacted from debug logs.

---

## Audit

### n8n_audit_instance

Combined security audit: n8n's built-in audit (`POST /audit`) plus a custom deep scan of all workflows.

**Latency**: 500-5000 ms.

**Parameters** (all optional):

| Name | Type | Default | Notes |
|---|---|---|---|
| `categories` | string[] | all | Subset of built-in: `credentials`, `database`, `nodes`, `instance`, `filesystem` |
| `includeCustomScan` | boolean | true | Run the custom deep scan |
| `customChecks` | string[] | all | Subset of `hardcoded_secrets`, `unauthenticated_webhooks`, `error_handling`, `data_retention` |
| `daysAbandonedWorkflow` | number | | Threshold for abandoned-workflow detection |

**Custom deep scan checks**:

| Check | What it Flags |
|---|---|
| `hardcoded_secrets` | 50+ regex patterns for API keys, tokens, passwords (OpenAI, AWS, Stripe, GitHub, Slack, etc.) plus PII (email, phone, credit card). Secrets are masked in output (first 6 + last 4 chars) |
| `unauthenticated_webhooks` | Webhook/form triggers without authentication |
| `error_handling` | Workflows with 3+ nodes and no error handling |
| `data_retention` | Workflows saving all execution data (success + failure) |

**Output**: Actionable markdown report with summary table (critical/high/medium/low counts), findings grouped by workflow, and a Remediation Playbook with three sections:

- **Auto-fixable**: Items you can fix with tool chains (e.g., add auth to webhooks).
- **Requires review**: Needs human judgment (e.g., PII detection).
- **Requires user action**: Manual intervention (e.g., rotate exposed keys).

**Remediation types**: `auto_fixable`, `review_recommended`, `user_input_needed`, `user_action_needed`.

**Examples**:

```javascript
// Full audit (default)
n8n_audit_instance()

// Built-in only
n8n_audit_instance({
  categories: ["credentials", "nodes"],
  includeCustomScan: false
})

// Custom scan, specific checks
n8n_audit_instance({
  customChecks: ["hardcoded_secrets", "unauthenticated_webhooks"]
})

// Custom abandoned threshold
n8n_audit_instance({ daysAbandonedWorkflow: 90 })
```

---

## Executions

### n8n_executions

Manage workflow executions: list, get details, delete.

```javascript
// Get details
n8n_executions({ action: "get", id: "exec-id", mode: "summary" })  // preview, summary, filtered, full, error

// Get error info for debugging
n8n_executions({
  action: "get",
  id: "exec-id",
  mode: "error",
  includeStackTrace: true
})

// List
n8n_executions({
  action: "list",
  workflowId: "wf-abc",
  status: "error",  // success, error, waiting
  limit: 100
})

// Delete
n8n_executions({ action: "delete", id: "exec-id" })
```

### get_execution

Lower-level fetch of a single execution record.

---

## Self-Help and Diagnostics

### tools_documentation

Inline tool documentation.

```javascript
// Overview of all tools
tools_documentation()

// Details for one tool
tools_documentation({ topic: "search_nodes", depth: "full" })

// Code node guides
tools_documentation({ topic: "javascript_code_node_guide", depth: "full" })
tools_documentation({ topic: "python_code_node_guide", depth: "full" })
```

### ai_agents_guide

Comprehensive guide to AI workflow patterns.

```javascript
ai_agents_guide()
// or
tools_documentation({ topic: "ai_agents_guide", depth: "full" })
```

### n8n_health_check

Verify the MCP server and its connection to n8n.

```javascript
// Quick check
n8n_health_check()

// Diagnostic (env vars, tool status, API connectivity)
n8n_health_check({ mode: "diagnostic" })
```

---

## Tool Availability Matrix

| Always Available (no n8n API) | Requires N8N_API_URL + N8N_API_KEY |
|---|---|
| `search_nodes`, `get_node`, `get_suggested_nodes` | `n8n_create_workflow`, `create_workflow_from_code` |
| `validate_node`, `validate_workflow` | `n8n_update_partial_workflow`, `n8n_update_full_workflow` |
| `search_templates`, `get_template` | `n8n_validate_workflow`, `n8n_autofix_workflow` |
| `tools_documentation`, `ai_agents_guide`, `get_sdk_reference` | `n8n_list_workflows`, `n8n_get_workflow`, `n8n_delete_workflow`, `archive_workflow` |
| `n8n_health_check` (basic) | `n8n_test_workflow`, `execute_workflow`, `n8n_executions` |
| | `n8n_deploy_template`, `n8n_workflow_versions` |
| | `n8n_manage_datatable`, `n8n_manage_credentials` |
| | `n8n_audit_instance` |
| | `n8n_generate_workflow` (hosted-only) |

If API tools are unavailable, drive workflows through templates plus local-only validation.

---

## Performance Reference

| Tool | Response Time | Payload Size |
|---|---|---|
| `search_nodes` | under 20 ms | small |
| `get_node` (standard) | under 10 ms | ~1-2 KB |
| `get_node` (full) | under 100 ms | 3-8 KB |
| `validate_node` (minimal) | under 50 ms | small |
| `validate_node` (full) | under 100 ms | medium |
| `validate_workflow` | 100-500 ms | medium |
| `n8n_manage_credentials` | 50-500 ms | small-medium |
| `n8n_audit_instance` | 500-5000 ms | large |
| `n8n_create_workflow` | 100-500 ms | medium |
| `n8n_update_partial_workflow` | 50-200 ms | small |
| `n8n_deploy_template` | 200-500 ms | medium |
| `n8n_generate_workflow` | 2-15 s (gen), ~3 s (deploy) | medium |

---

## See Also

- [patterns.md](./patterns.md): Named, named copy-paste patterns for combining these tools (search-then-validate, iterative editing, validation loop, recovery).
- [gotchas.md](./gotchas.md): Failure modes for each tool category (wrong nodeType prefix, wrong parameter names, credential attachment, profile choice).
- [configuration.md](./configuration.md): MCP server registration and environment variables that govern which tools are available.
- [../validation/](../validation/): Deeper coverage of validation response shapes, error types, and recovery beyond the call surface here.
- [../node-configuration/](../node-configuration/): What `get_node` reveals and what `validate_node` checks (discriminators, required fields, allowed values).
- [../workflow-patterns/](../workflow-patterns/): Architectural patterns for assembling nodes into working workflows.
