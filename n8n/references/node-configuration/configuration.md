# Configuration Environment: Dependencies, Credentials, Versions

Node-level configuration spans more than just parameter values. This reference covers:

- **Property dependency chains**: how to reason about the full chain of gated fields inside a single node.
- **Credentials structure**: how the `authentication`, `nodeCredentialType`, and credentialed-resource fields fit together.
- **Version pinning**: node-version semantics for nodes with breaking-change versions (SplitInBatches, IF, Switch).
- **Node-level environment requirements**: what each common node category assumes about the surrounding environment.

For per-property `displayOptions` semantics see [api.md](./api.md). For copy-paste configurations see [patterns.md](./patterns.md).

---

## Property Dependency Chains

A dependency chain is the ordered sequence of fields whose values gate the visibility and requiredness of later fields in the same node. Building configurations by walking the chain top-down avoids fighting the schema.

### Anatomy of a Dependency Chain

Each link in the chain has:

- **Gate field**: the field whose value controls the next field.
- **Gated field**: the field that becomes visible (and often required) when the gate matches.
- **Gate condition**: the `displayOptions.show` (or `hide`) rule.

The HTTP Request body chain has four links:

```
Link 1: method gates sendBody
        - Gate: method
        - Gated: sendBody (visible only for body-bearing methods)
        - Condition: method IN [POST, PUT, PATCH, DELETE]

Link 2: sendBody gates body
        - Gate: sendBody
        - Gated: body (visible and required)
        - Condition: sendBody = true

Link 3: body.contentType gates body.content shape
        - Gate: body.contentType
        - Gated: body.content (its expected structure)
        - Condition: contentType IN [json, form-data, raw, ...]

Link 4: body.content matches contentType
        - JSON object for contentType=json
        - Array of {name,value} for contentType=form-data
        - String for contentType=raw
```

### Dependency Chains for Common Nodes

#### HTTP Request

```
authentication
  └─ nodeCredentialType (when authentication=predefinedCredentialType)
method
  ├─ sendQuery
  │  └─ queryParameters
  ├─ sendHeaders
  │  └─ headerParameters
  └─ sendBody  (only for POST/PUT/PATCH/DELETE)
     └─ body
        └─ body.contentType
           └─ body.content  (shape determined by contentType)
```

#### Slack (resource=message)

```
resource=message
  ├─ operation=post
  │  ├─ channel (required)
  │  ├─ text (required)
  │  ├─ attachments (optional)
  │  └─ blocks (optional)
  ├─ operation=update
  │  ├─ messageId (required)
  │  ├─ text (required)
  │  └─ channel (optional)
  ├─ operation=delete
  │  ├─ messageId (required)
  │  └─ channel (required)
  └─ operation=get
     ├─ messageId (required)
     └─ channel (required)
```

#### Slack (resource=channel)

```
resource=channel
  └─ operation=create
     ├─ name (required, lowercase, 1-80 chars)
     └─ isPrivate (optional)
```

#### IF Node (string conditions)

```
conditions.string[i].operation
  ├─ Binary (equals, notEquals, contains, ...)
  │  ├─ value1 (required)
  │  ├─ value2 (required)
  │  └─ singleValue should NOT be set
  └─ Unary (isEmpty, isNotEmpty, ...)
     ├─ value1 (required)
     ├─ value2 (hidden)
     └─ singleValue = true (auto-added)
```

#### Postgres

```
operation
  ├─ executeQuery
  │  ├─ query (required)
  │  └─ additionalFields.queryParameters (recommended, for parameterized queries)
  ├─ insert
  │  ├─ table (required)
  │  ├─ columns (required)
  │  └─ additionalFields.queryParameters
  ├─ update
  │  ├─ table (required)
  │  ├─ updateKey (required)
  │  ├─ columns (required)
  │  └─ additionalFields.queryParameters
  └─ delete
     ├─ table (required)
     └─ additionalFields.queryParameters
```

### How to Walk a Chain When Configuring

1. Identify the root field (`method`, `resource`, `operation`, or similar discriminator).
2. Set it.
3. Discover what newly-visible fields are required, using `get_node` or validation errors.
4. Set those fields.
5. Repeat until validation passes.

This is the same flow described in [patterns.md](./patterns.md) under "Property Dependency Chains", and it is the only reliable way to navigate non-trivial dependency graphs.

### Auto-Sanitization Behavior in Dependency Chains

Some chain links are auto-fixed by n8n on save:

- **IF/Switch operator structure**: `singleValue: true` is added automatically for unary operators.
- **IF/Switch metadata**: rule and condition metadata is filled in.

Most are not:

- **Missing required business fields**: channel, messageId, table, columns. These you must set.
- **Stale fields after operator/operation switch**: leftover `value2` after switching to a unary operator is not removed.

Trust auto-sanitization for operator metadata only. Treat every other required field as your responsibility.

---

## Credentials Structure

n8n credential references inside a node configuration are themselves a small dependency chain. They are common across HTTP-style nodes (HTTP Request, Webhook) and integration nodes (Slack, Gmail, Google Sheets, Postgres).

### The authentication Field

`authentication` is the root credential discriminator. It selects how credentials are attached to the request.

Common values:

| `authentication` | Meaning | Additional fields required |
|---|---|---|
| `none` | No authentication | none |
| `predefinedCredentialType` | Use a stored credential of a named type | `nodeCredentialType` |
| `genericCredentialType` | Use a generic credential schema (basic auth, header auth, etc.) | `genericAuthType` |
| `headerAuth` (Webhook-only) | Authenticate the incoming webhook by header | header credential |

### Predefined Credential Types

When `authentication: "predefinedCredentialType"`, you must set `nodeCredentialType` to the name of a registered credential type:

```javascript
// HTTP Request with HTTP Header Auth
{
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "httpHeaderAuth"
}

// HTTP Request with Google API
{
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "googleApi"
}
```

The actual credential value (the secret) is stored in n8n's credentials store and referenced by ID separately from the node parameters. The node parameters only reference the credential type and the credential's ID slot.

Common `nodeCredentialType` values:

| `nodeCredentialType` | Use case |
|---|---|
| `httpHeaderAuth` | API token in a custom header |
| `httpBasicAuth` | Basic Auth |
| `httpQueryAuth` | API key in query string |
| `oAuth2Api` | OAuth2 |
| `googleApi` | Google service-account auth (Sheets, Drive, Gmail underlying) |

### Credentials for Service-Specific Nodes

Service-specific nodes (Slack, Gmail, Postgres) have their own credential types and do not use the generic `authentication` discriminator. They reference credentials directly via the node's `credentials` block at the workflow level, separate from the `parameters` object documented here.

For example, a Slack node's `parameters` does not include `authentication` or `nodeCredentialType`. Instead, the workflow JSON for the node carries:

```javascript
{
  "name": "Slack",
  "type": "n8n-nodes-base.slack",
  "parameters": {/* ... */},
  "credentials": {
    "slackApi": {"id": "5", "name": "Slack OAuth"}
  }
}
```

The credential ID and name resolve at runtime to the stored secret.

### When authentication=none Is Not Enough

Validation will sometimes pass with `authentication: "none"` because the schema permits it, but the target API requires authentication. The result is a runtime 401/403 rather than a validation failure.

Mitigation:

- For public APIs, `authentication: "none"` is fine.
- For private APIs, always set the appropriate `authentication` plus `nodeCredentialType` (or service-specific credential) before deploying.

### Credential Dependency Chain Summary

```
authentication
  ├─ "none" → no further fields
  ├─ "predefinedCredentialType"
  │   └─ nodeCredentialType
  │      └─ workflow-level credentials block (referenced by ID)
  └─ "genericCredentialType"
      └─ genericAuthType (basicAuth, headerAuth, queryAuth, oAuth2, ...)
         └─ workflow-level credentials block (referenced by ID)
```

---

## Version Pinning

Some n8n nodes have multiple versions with different schemas. The version is part of the node identifier in the workflow JSON and determines which schema applies.

### Why Versions Matter

- Field names and structures change between versions.
- Auto-sanitization rules differ.
- Output wiring differs (notably SplitInBatches).

Configuring against the wrong version produces validation errors that look like "unknown property" or "missing required field" when the field exists at a different name in the correct version.

### Common Versioned Nodes

#### SplitInBatches

Versions exist with different output wiring semantics. Version 3 has the now-standard two-output layout:

```javascript
// SplitInBatches v3
{
  "batchSize": 100,
  "options": {}
}
```

Output wiring (v3):

- `main[0]` (done): connect downstream processing here. Add a Limit 1 to avoid duplicate triggers if your downstream is sensitive to repeats.
- `main[1]` (each batch): connect this to the loop body, then loop the body back to SplitInBatches input.

When discovering this node, always confirm the version. Earlier versions had a single output and different parameter shapes.

#### IF Node

IF nodes have evolved condition syntax over versions. The patterns documented in this reference assume the contemporary multi-type structure (`conditions.string[]`, `conditions.number[]`, `conditions.boolean[]`).

When working with an older workflow, run `get_node` with `detail: "full"` to confirm the active version's condition schema before editing.

#### Switch Node

Switch nodes also have version-dependent rule schemas. Contemporary versions use the `mode: "rules"` plus `rules.rules[]` array shape shown in [patterns.md](./patterns.md). Older versions had a flatter structure.

### How to Discover the Version

`get_node` returns the canonical schema for the node type at its current version. If you need to inspect a specific version (because you are editing an older workflow), the workflow JSON carries a `typeVersion` field on each node. Match your discovery call to that version when possible, otherwise upgrade the node to the current version before editing.

### Pinning Strategy

For long-lived workflows:

- Note the `typeVersion` of each node in your design documentation.
- When upgrading n8n, audit nodes whose `typeVersion` is older than the latest available, plan the migration as a separate task from the upgrade itself.
- Do not silently bump versions during a configuration edit, treat the version bump as a discrete change with its own validation pass.

---

## Node-Level Environment Requirements

Each major node category assumes specific environment capabilities. Mismatches here surface as runtime errors that the validator cannot catch.

### HTTP Request and Webhook

**Assumed environment**:

- Outbound network access to the configured `url` (HTTP Request).
- Inbound reachability of the n8n server at the configured `path` (Webhook).
- TLS support for HTTPS URLs.
- Cert trust store covers the target API's certificate authority.

**Common mismatch**: Self-hosted n8n behind a proxy with no outbound access fails HTTP Request runtime with connection-refused or DNS-resolution errors. There is no validation signal.

### Slack and Gmail

**Assumed environment**:

- OAuth2 credentials configured at the n8n credentials level.
- For Slack: bot or user token with the required scopes (`chat:write`, `channels:read`, `groups:read`).
- For Gmail: OAuth2 access to the user's Gmail data.

**Common mismatch**: A workflow that posts to Slack validates clean but fails at runtime with `missing_scope` if the bot token lacks `chat:write` for the target channel type (public vs private).

### Postgres

**Assumed environment**:

- Postgres credential configured in n8n with host, port, database, user, password.
- Network reachability from n8n to the Postgres server.
- User has the required privileges for the operations (`SELECT`, `INSERT`, `UPDATE`, `DELETE`).

**Common mismatch**: Insert or update fails with permission-denied at runtime if the credentialed user lacks write privileges. The node validates because the parameters are well-formed.

### Google Sheets

**Assumed environment**:

- Either a Google OAuth2 credential or a Service Account credential.
- Sheet shared with the credentialed identity (especially for Service Account).
- The Sheets API enabled on the Google Cloud project.

**Common mismatch**: Service-account credentials work for the spreadsheet ID until someone changes the sharing, then the workflow fails with a 403.

**Per-item execution implication**: each input item triggers a separate API call. 100 items mean 100 calls. If you exceed Google's per-user-per-minute quota, you get 429s. Switch to the bulk pattern in [patterns.md](./patterns.md) "Google Sheets Bulk Write".

**Formula column safety**: never use `append` on sheets with formula columns. It overwrites formulas. Use HTTP Request with `values.update` (PUT) and a `googleApi` credential to write only the data columns. See [gotchas.md](./gotchas.md) "Google Sheets append on Formula Sheets".

### OpenAI and Other LLM Nodes

**Assumed environment**:

- API key credential configured.
- Sufficient quota and rate limit headroom for the workflow's call volume.
- Model name in the configuration is available on the connected account.

**Common mismatch**: A workflow validates with `model: "gpt-5"` but fails at runtime if the account does not have access to that model. Validation does not call the OpenAI API.

### Schedule Trigger

**Assumed environment**:

- n8n server running continuously to execute scheduled jobs.
- Timezone configuration matches operational expectations.
- For high-frequency schedules (every minute or faster), worker capacity to keep up.

**Common mismatch**: A schedule trigger configured without `timezone` runs on the server's system timezone, often UTC in containerized deployments. Set `timezone` explicitly. See [gotchas.md](./gotchas.md) "Schedule Trigger Missing Timezone".

### Code Node (JavaScript and Python)

**Assumed environment**:

- For JavaScript: Node.js runtime on the n8n server. Standard Node built-ins available, no npm install at runtime.
- For Python: Python runtime if Python execution is enabled in n8n config.
- No file-system access by default (sandboxed in most deployments).

**Common mismatch**: Code that uses npm packages will not run, n8n's Code node does not support arbitrary npm dependencies. For Python, the available stdlib is implementation-defined per deployment.

See [../code-javascript/](../code-javascript/) and [../code-python/](../code-python/) for the supported APIs.

---

## Putting It All Together

A fully-resilient node configuration accounts for four layers:

1. **Property dependency chain** within the node parameters (this file, top).
2. **Credentials chain** linking `authentication` to the credentials store (this file, middle).
3. **Version pinning** so the schema and the parameters match (this file, lower-middle).
4. **Environment requirements** so the runtime can actually execute the node (this file, bottom).

Validation catches layer 1 issues. Credential errors (layer 2) and version mismatches (layer 3) usually surface as validation errors that look like "missing required field". Environment mismatches (layer 4) only surface at runtime.

Plan each layer deliberately during configuration design. Discover, configure, validate, and confirm credentials and environment before deploying to production workflows.

---

## See Also

- [README.md](./README.md): Topic overview and reading order.
- [api.md](./api.md): The MCP calls and `displayOptions` semantics behind dependency chains.
- [patterns.md](./patterns.md): Per-node copy-paste configurations that consume the dependencies described here.
- [gotchas.md](./gotchas.md): Failures specific to credentials, versions, environment mismatches.
- [../mcp-tools/](../mcp-tools/): Full MCP discovery surface.
- [../validation/](../validation/): How validation interacts with credential and version errors.
- [../workflow-patterns/](../workflow-patterns/): Higher-level patterns that integrate multiple credentialed nodes.
