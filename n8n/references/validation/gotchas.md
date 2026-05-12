# Validation Gotchas

Every documented error type and false-positive symptom. Each entry uses the four-part structure: quoted symptom, Cause, Solution, bad/good code pair.

---

## Error: Must-Fix

### "missing_required"

> `{ "type": "missing_required", "property": "channel", "message": "Channel name is required" }`

**Cause:** A required field for the current node type, resource, or operation is not present in the configuration. Often happens when copying configs between operations that have different requirements, or when configuring a fresh node without consulting `get_node`. Most common validation error (about 45 percent of error volume).

**Solution:** Use `get_node({ nodeType })` to enumerate required fields, then add the missing field with an appropriate value. Some required fields are conditional (e.g. `body` is required only when `sendBody: true`), so re-read the error message for context.

```javascript
// BAD: missing required channel
{
  "resource": "message",
  "operation": "post"
  // missing: channel
}

// GOOD
{
  "resource": "message",
  "operation": "post",
  "channel": "#general"
}
```

Conditional required fields:

```javascript
// BAD: sendBody is true but body is missing
{
  "method": "POST",
  "url": "https://api.example.com/create",
  "sendBody": true
  // missing: body (required when sendBody=true)
}

// GOOD
{
  "method": "POST",
  "url": "https://api.example.com/create",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": { "name": "John", "email": "john@example.com" }
  }
}
```

For required-field discovery, see [../node-configuration/](../node-configuration/).

---

### "invalid_value"

> `{ "type": "invalid_value", "property": "operation", "message": "Operation must be one of: post, update, delete, get", "current": "send" }`

**Cause:** The value provided does not match the allowed options for that field. Typically a typo, a guess at an enum value, or wrong case (enums are case-sensitive). Second most common error (about 28 percent of error volume).

**Solution:** Read the error message's `allowed` array for valid options, or call `get_node` to see the enum. Match case exactly: `message` not `Message`, `post` not `send`.

```javascript
// BAD: "send" is not a valid Slack operation
{
  "resource": "message",
  "operation": "send"
}

// GOOD
{
  "resource": "message",
  "operation": "post"
}
```

Case sensitivity:

```javascript
// BAD: capital M
{
  "resource": "Message",
  "operation": "post"
}

// GOOD: lowercase
{
  "resource": "message",
  "operation": "post"
}
```

Invalid HTTP method:

```javascript
// BAD
{ "method": "FETCH", "url": "https://api.example.com" }

// GOOD
{ "method": "GET", "url": "https://api.example.com" }
```

Invalid channel format:

```javascript
// BAD: wrong format
{ "channel": "General" }

// GOOD: starts with # and lowercase
{ "channel": "#general" }
```

---

### "type_mismatch"

> `{ "type": "type_mismatch", "property": "limit", "message": "Expected number, got string", "current": "100" }`

**Cause:** The value is the wrong primitive type (string instead of number, number instead of string, boolean serialized as string, object instead of array). Often comes from hardcoded JSON or from upstream nodes that stringify numbers.

**Solution:** Match the expected type exactly. Use `100` (number) not `"100"` (string), `true` (boolean) not `"true"` (string), arrays for list fields not objects.

```javascript
// BAD: string instead of number
{
  "operation": "executeQuery",
  "query": "SELECT * FROM users",
  "limit": "100"
}

// GOOD
{
  "operation": "executeQuery",
  "query": "SELECT * FROM users",
  "limit": 100
}
```

Boolean as string:

```javascript
// BAD
{
  "method": "GET",
  "url": "https://api.example.com",
  "sendHeaders": "true"
}

// GOOD
{
  "method": "GET",
  "url": "https://api.example.com",
  "sendHeaders": true
}
```

Object instead of array:

```javascript
// BAD
{
  "name": "New Channel",
  "tags": { "tag": "important" }
}

// GOOD
{
  "name": "New Channel",
  "tags": ["important", "alerts"]
}
```

Number passed where channel name (string) expected:

```javascript
// BAD: channel ID as number
{
  "resource": "message",
  "operation": "post",
  "channel": 12345
}

// GOOD: channel name as string
{
  "resource": "message",
  "operation": "post",
  "channel": "#general"
}
```

---

### "invalid_expression"

> `{ "type": "invalid_expression", "property": "text", "message": "Expressions must be wrapped in {{}}", "current": "$json.name" }`

**Cause:** An n8n expression has syntax errors, missing delimiters, typos in references, invalid JavaScript, or references a property that does not exist on the upstream data. Webhook bodies are a common trap: the data lives under `.body`, not at the top level of `$json`.

**Solution:** Wrap expressions in `={{ }}`. Verify referenced node names exactly (n8n is case-sensitive and whitespace-sensitive). Use safe navigation (`?.`) when the data shape is uncertain. For webhook payloads, prefix with `.body`. See [../expressions/](../expressions/) for the full expression grammar.

Missing delimiters:

```javascript
// BAD: no {{ }} wrap
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",
  "text": "$json.name"
}

// GOOD
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",
  "text": "={{$json.name}}"
}
```

Invalid node reference (typo):

```javascript
// BAD: "HTTP Requets" has a typo
{
  "field": "data",
  "value": "={{$node['HTTP Requets'].json.data}}"
}

// GOOD
{
  "field": "data",
  "value": "={{$node['HTTP Request'].json.data}}"
}
```

Property access on possibly-undefined chain:

```javascript
// BAD: throws if data or user is undefined
{ "text": "={{$json.data.user.name}}" }

// GOOD: safe navigation with fallback
{ "text": "={{$json.data?.user?.name || 'Unknown'}}" }
```

Webhook data trap (very common):

```javascript
// BAD: webhook data lives under .body, not at the root
{ "field": "email", "value": "={{$json.email}}" }

// GOOD
{ "field": "email", "value": "={{$json.body.email}}" }
```

---

### "invalid_reference"

> `{ "type": "invalid_reference", "property": "expression", "message": "Node 'Transform Data' does not exist in workflow" }`

**Cause:** An expression or connection references a node by a name that does not exist in the workflow. Causes: node was renamed, node was deleted, the workflow was copied from another workflow with different names, or there is a typo.

**Solution:** Update the reference to match the current node name. If the offender is a workflow-level connection (not an expression), use `n8n_update_partial_workflow` with `cleanStaleConnections` to remove orphaned connection entries automatically.

Deleted node reference:

```javascript
// BAD: 'Transform Data' was deleted
{ "value": "={{$node['Transform Data'].json.result}}" }

// GOOD: update to existing node
{ "value": "={{$node['Set'].json.result}}" }
```

Renamed node not updated:

```javascript
// BAD: old name
{ "value": "={{$node['Get Weather'].json.temperature}}" }

// GOOD: current name
{ "value": "={{$node['Weather API'].json.temperature}}" }
```

Stale connection (workflow-level), fix by cleanup operation:

```javascript
// BAD: connection references node 'Slack1' which does not exist
// (no source code fix, this is in connections, not parameters)

// GOOD: clean stale connections
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{ type: "cleanStaleConnections" }]
});
```

---

### "patchNodeField: find string not found"

> `patchNodeField: find string not found in field "parameters.jsCode"`

**Cause:** The `find` value in a `patchNodeField` operation does not exist in the target field. Either the content was already changed by a previous operation, the find string has a typo, or whitespace/line endings differ.

**Solution:** Use `n8n_get_workflow` to inspect the current field value and confirm the exact string. Whitespace and line endings matter. If you are unsure, use `regex: true` with `\s+` for flexible whitespace matching.

```javascript
// BAD: stale find string after the field was already updated
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "patchNodeField",
    node: "Code",
    field: "parameters.jsCode",
    find: "return items;",   // already changed
    replace: "return items.filter(i => i.active);"
  }]
});

// GOOD: verify current value first, or use regex with flexible whitespace
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "patchNodeField",
    node: "Code",
    field: "parameters.jsCode",
    find: "return\\s+items;",
    replace: "return items.filter(i => i.active);",
    regex: true
  }]
});
```

---

### "patchNodeField: ambiguous match (multiple occurrences)"

> `patchNodeField: find string matches 3 times in field "parameters.jsCode", set replaceAll: true to replace all, or use a more specific find string`

**Cause:** The find string appears more than once in the field. Without `replaceAll: true`, this is treated as ambiguous and rejected. The strict-by-default behavior prevents accidentally replacing the wrong occurrence.

**Solution:** Either set `replaceAll: true` if you genuinely want all occurrences replaced, or make your find string more specific (include more surrounding context) to match only the intended location.

```javascript
// BAD: 'count' appears 3 times in the code, unclear which to replace
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "patchNodeField",
    node: "Code",
    field: "parameters.jsCode",
    find: "count",
    replace: "total"
  }]
});

// GOOD: more specific find string targets the one location intended
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "patchNodeField",
    node: "Code",
    field: "parameters.jsCode",
    find: "const count = items.length;",
    replace: "const total = items.length;"
  }]
});

// ALSO GOOD: replaceAll if you truly want all three
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "patchNodeField",
    node: "Code",
    field: "parameters.jsCode",
    find: "count",
    replace: "total",
    replaceAll: true
  }]
});
```

---

### "patchNodeField: invalid or unsafe regex pattern"

> `patchNodeField: invalid or unsafe regex pattern`

**Cause:** When `regex: true`, the pattern is validated for correctness and ReDoS safety. Nested quantifiers like `(a+)+` and overlapping alternations like `(\w|\d)+` are rejected because they can cause catastrophic backtracking.

**Solution:** Simplify the regex pattern. Avoid nested quantifiers and overlapping character classes. If you need to match flexibly, use specific character classes rather than alternations of overlapping classes.

```javascript
// BAD: nested quantifier, ReDoS risk
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "patchNodeField",
    node: "Code",
    field: "parameters.jsCode",
    find: "(\\s+)+;",   // nested quantifier
    replace: ";",
    regex: true
  }]
});

// GOOD: flat quantifier, safe
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "patchNodeField",
    node: "Code",
    field: "parameters.jsCode",
    find: "\\s+;",
    replace: ";",
    regex: true
  }]
});
```

---

## Error: Workflow-Level

### "Broken Connection"

> `Connection from 'Transform' to 'NonExistent' - target node not found`

**Cause:** A connection entry points to a node name that no longer exists in the workflow. The target node was deleted or renamed and the connection was not updated.

**Solution:** Either remove the stale connection (use `cleanStaleConnections`) or create/rename the target node to match the connection.

```javascript
// BAD: connection points to 'NonExistent' which is not in nodes[]
{
  "nodes": [{ "name": "Transform", ... }],
  "connections": {
    "Transform": { "main": [[{ "node": "NonExistent" }]] }
  }
}

// GOOD: clean stale connections
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{ type: "cleanStaleConnections" }]
});
```

---

### "Circular Dependency"

> `Circular dependency detected: Node A -> Node B -> Node A`

**Cause:** Connections form a loop. n8n workflows are directed acyclic graphs. A cycle prevents execution from terminating.

**Solution:** Restructure the workflow to remove the loop. For iteration, use a Loop Over Items node or a `splitInBatches` pattern instead of self-referencing connections.

```javascript
// BAD: A -> B -> A
{
  "connections": {
    "A": { "main": [[{ "node": "B" }]] },
    "B": { "main": [[{ "node": "A" }]] }
  }
}

// GOOD: linear flow with proper iteration node
{
  "connections": {
    "A": { "main": [[{ "node": "Loop Over Items" }]] },
    "Loop Over Items": { "main": [[{ "node": "B" }]] }
  }
}
```

---

### "Multiple Start Nodes"

> `Multiple trigger nodes found, only one will execute`

**Cause:** The workflow has more than one trigger node. While n8n allows this, only one will fire per execution, which is rarely the intent.

**Solution:** Remove extra triggers, or split into separate workflows that each have a single trigger.

```javascript
// BAD: two trigger nodes
{
  "nodes": [
    { "type": "n8n-nodes-base.webhook", ... },
    { "type": "n8n-nodes-base.scheduleTrigger", ... }
  ]
}

// GOOD: split into two workflows, each with one trigger
```

---

### "Disconnected Node"

> `Node 'Transform' is not connected to workflow flow`

**Cause:** A node exists in the workflow but has no incoming connections and is not a trigger. It will never execute.

**Solution:** Connect the node to the flow, or remove it if it is unused.

```javascript
// BAD: 'Transform' has no incoming connections
{
  "nodes": [
    { "name": "Webhook", "type": "n8n-nodes-base.webhook" },
    { "name": "Transform", "type": "n8n-nodes-base.set" },
    { "name": "Slack", "type": "n8n-nodes-base.slack" }
  ],
  "connections": {
    "Webhook": { "main": [[{ "node": "Slack" }]] }
    // Transform never runs
  }
}

// GOOD: wire Transform into the flow
{
  "connections": {
    "Webhook": { "main": [[{ "node": "Transform" }]] },
    "Transform": { "main": [[{ "node": "Slack" }]] }
  }
}
```

---

## Warning: Should-Fix

### "best_practice: missing error handling"

> `{ "type": "best_practice", "property": "onError", "message": "Slack API can have rate limits", "suggestion": "Add onError: 'continueRegularOutput'" }`

**Cause:** The node has no `continueOnFail`, `retryOnFail`, or `onError` configuration. External API calls and database writes can fail transiently. Without error handling, the entire workflow execution dies on the first failure.

**Solution:** For production workflows, add `continueOnFail: true`, `retryOnFail: true`, and a `maxTries` value. For dev/test workflows or non-critical notifications, this warning may be a false positive (see "Symptom: missing error handling warning on dev workflow" below).

```javascript
// BAD (for production): no error handling
{
  "resource": "message",
  "operation": "post",
  "channel": "#alerts"
}

// GOOD (for production)
{
  "resource": "message",
  "operation": "post",
  "channel": "#alerts",
  "continueOnFail": true,
  "retryOnFail": true,
  "maxTries": 3
}
```

---

### "deprecated: old typeVersion"

> `{ "type": "deprecated", "property": "typeVersion", "message": "typeVersion 1 is deprecated for Slack node, use version 2", "current": 1, "recommended": 2 }`

**Cause:** The node is pinned to an old `typeVersion` that has been superseded. Old versions still work but may stop working in future n8n releases.

**Solution:** Upgrade to the recommended `typeVersion`. Note that parameter shapes can differ between versions, so re-validate after upgrading. You can use `n8n_autofix_workflow` with `fixTypes: ["typeversion-upgrade"]` for automatic migration.

```javascript
// BAD
{ "type": "n8n-nodes-base.slack", "typeVersion": 1 }

// GOOD
{ "type": "n8n-nodes-base.slack", "typeVersion": 2 }
```

---

### "performance: unbounded query"

> `{ "type": "performance", "property": "query", "message": "SELECT without LIMIT can return massive datasets", "suggestion": "Add LIMIT clause or use pagination" }`

**Cause:** A SQL query has no `LIMIT` clause. On a large production table, this can return millions of rows, exhausting memory and locking up the workflow.

**Solution:** Add `LIMIT` for one-shot queries on large tables, or use cursor-style pagination for sweeps. False positive on small known-bounded tables or aggregations (see "Symptom: unbounded query warning on small dataset" below).

```sql
-- BAD: production users table could have millions of rows
SELECT * FROM users WHERE active = true

-- GOOD: bounded
SELECT * FROM users WHERE active = true LIMIT 1000

-- BETTER: cursor pagination
SELECT * FROM users WHERE id > {{$json.lastId}} ORDER BY id LIMIT 1000
```

---

## Auto-Fixed (Trust the System)

### "operator_structure"

> `{ "type": "operator_structure", "message": "Binary operator has singleValue: true" }` (or the inverse for unary)

**Cause:** IF/Switch boolean operator metadata is wrong. Binary operators (`equals`, `notEquals`, etc.) should not have `singleValue`. Unary operators (`isEmpty`, `isNotEmpty`, `true`, `false`) require `singleValue: true`.

**Solution:** Do nothing. Auto-sanitization fixes this on every workflow save (`n8n_create_workflow`, `n8n_update_partial_workflow`). Manually fixing it wastes time and often gets it wrong.

```javascript
// BAD: do not manually set singleValue
{
  "type": "boolean",
  "operation": "equals",
  "singleValue": true   // wrong, but you do not need to fix it
}

// GOOD: just let auto-sanitization run
{
  "type": "boolean",
  "operation": "equals"
  // auto-sanitization removes singleValue on save if present, adds it for unary ops
}
```

---

## False Positives (Symptoms, Not Errors)

Roughly 40 percent of warnings are acceptable in specific use cases. The `ai-friendly` profile reduces false positives by about 60 percent. Below are the most common warning symptoms that are often safe to ignore, with reasoning. If you accept a warning, document why.

### Symptom: missing error handling warning on dev/test or non-critical workflow

> `{ "type": "best_practice", "message": "No error handling configured" }`

**Cause:** The warning fires on every node without `continueOnFail`/`retryOnFail`, regardless of whether the workflow is production-critical. For dev/test workflows, optional notifications, or manual-trigger flows, error handling is often noise.

**Solution:** Safe to ignore when: testing (you want to see failures), non-critical notifications (failure has no business impact), or manual-trigger workflows (a human is watching). Always fix when: production automation, customer-facing operations, payment processing, anything handling critical data.

```javascript
// BAD (looks dangerous, is fine for context): test workflow
{
  "name": "Test Slack Integration",
  "nodes": [{
    "type": "n8n-nodes-base.slack",
    "parameters": { "resource": "message", "operation": "post", "channel": "#test" }
    // warning: no error handling
    // ACCEPTED: test workflow, want to see failures
  }]
}

// GOOD (production): error handling added
{
  "name": "Process Customer Orders",
  "nodes": [{
    "type": "n8n-nodes-base.postgres",
    "parameters": {
      "query": "INSERT INTO orders...",
      "continueOnFail": true,
      "retryOnFail": true,
      "maxTries": 3,
      "waitBetweenTries": 1000
    }
  }]
}
```

---

### Symptom: no retry logic warning on idempotent or internal call

> `{ "type": "best_practice", "message": "External API calls should retry on failure" }`

**Cause:** The warning treats all external calls equally. Some APIs (Stripe, AWS SDK) have built-in retry. GET requests are idempotent and easy to retry manually. Internal/localhost services are highly reliable.

**Solution:** Safe to ignore when: API has built-in retry (Stripe SDK retries automatically), operation is idempotent (GET requests), or the target is internal (`localhost`, internal microservice). Always fix when: flaky external APIs, non-idempotent operations (POST that could create duplicates on retry without idempotency keys).

```javascript
// BAD (looks risky, is fine): Stripe has built-in retry
{
  "type": "n8n-nodes-base.stripe",
  "parameters": { "resource": "charge", "operation": "create" }
  // ACCEPTED: Stripe SDK retries automatically
}

// GOOD: flaky external API gets explicit retry
{
  "url": "https://unreliable-api.com/data",
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 2000
}
```

---

### Symptom: missing rate limiting warning on low-volume workflow

> `{ "type": "best_practice", "message": "API may have rate limits" }`

**Cause:** The warning fires on any HTTP call to a known rate-limited service, even when the workflow's call volume is far below any limit.

**Solution:** Safe to ignore when: internal APIs (no limits), low-volume workflows (once per day), or APIs with server-side rate limiting and 429-aware retry. Always fix when: high-volume loops against public APIs (GitHub, Twitter), batch operations against rate-limited services.

```javascript
// BAD (looks risky, is fine): once-per-day workflow
{
  "trigger": { "type": "n8n-nodes-base.cron", "parameters": { "mode": "everyDay", "hour": 9 } },
  "nodes": [{
    "type": "n8n-nodes-base.httpRequest",
    "parameters": { "url": "https://api.example.com/daily-report" }
    // ACCEPTED: once per day, no rate limit concerns
  }]
}

// GOOD: high-volume loop adds batching
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "https://api.github.com/...",
    "options": {
      "batching": {
        "batch": { "batchSize": 10, "batchInterval": 1000 }
      }
    }
  }
}
```

---

### Symptom: unbounded query warning on small dataset

> `{ "type": "performance", "message": "SELECT without LIMIT can return massive datasets" }`

**Cause:** The warning fires on every `SELECT` without `LIMIT`, even when the queried table is known to be small (config tables, lookup tables, test fixtures) or the query is an aggregation that returns a single row.

**Solution:** Safe to ignore when: querying small known-bounded tables (config with about 10 rows), aggregation queries (`COUNT`, `SUM`, `AVG`), or dev/test environments with small datasets. Always fix when: production queries on tables that can grow unbounded.

```sql
-- BAD (looks dangerous, is fine): config table with ~10 rows
SELECT * FROM app_config
-- ACCEPTED: known small table

-- ALSO FINE: aggregation returns one row
SELECT COUNT(*) as total FROM users WHERE active = true

-- GOOD (for production user table): add LIMIT
SELECT * FROM users LIMIT 1000
```

---

### Symptom: missing input validation warning on trusted webhook

> `{ "type": "best_practice", "message": "Webhook doesn't validate input data" }`

**Cause:** The warning fires on any webhook node without an explicit validation IF. Internal webhooks called only from your own backend, or cryptographically signed webhooks (Stripe, GitHub), already have authenticity guarantees.

**Solution:** Safe to ignore when: internal webhooks (your backend already validates), trusted sources with cryptographic signatures (Stripe webhook signature, GitHub HMAC). Always fix when: public webhooks that accept user-submitted data.

```javascript
// BAD (looks risky, is fine): internal webhook
{
  "type": "n8n-nodes-base.webhook",
  "parameters": { "path": "internal-trigger" }
  // ACCEPTED: your backend already validates
}

// GOOD: public webhook adds validation
{
  "nodes": [
    { "name": "Webhook", "type": "n8n-nodes-base.webhook" },
    {
      "name": "Validate Input",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "boolean": [
            { "value1": "={{$json.body.email}}", "operation": "isNotEmpty" },
            { "value1": "={{$json.body.email}}", "operation": "regex", "value2": "^[^@]+@[^@]+\\.[^@]+$" }
          ]
        }
      }
    }
  ]
}
```

---

### Symptom: hardcoded credentials warning on truly public API

> `{ "type": "security", "message": "Credentials should not be hardcoded" }`

**Cause:** The warning fires on any literal `Authorization` header. For genuinely public APIs (`https://api.ipify.org`) or clearly-marked demo workflows, there are no real credentials at risk.

**Solution:** Safe to ignore when: public APIs that need no auth, demo/example workflows with obvious placeholder tokens. Always fix when: any real API key, password, or token is present. Migrate to the n8n credentials system immediately.

```javascript
// BAD (looks like a leak, is fine): genuinely public API
{
  "url": "https://api.ipify.org"
  // ACCEPTED: no credentials present
}

// GOOD: real credentials live in the credentials system, not in the workflow
{
  "authentication": "headerAuth",
  "credentials": {
    "headerAuth": { "id": "credential-id", "name": "My API Key" }
  }
}
```

---

### Symptom: IF node metadata warning (known issue #304)

> `{ "type": "metadata_incomplete", "message": "IF node missing conditions.options metadata", "node": "IF" }`

**Cause:** False positive for IF v2.2+. Auto-sanitization adds the required metadata on save, but validation runs before sanitization, so the warning surfaces even though the saved workflow will be correct.

**Solution:** Ignore. The metadata is added automatically on save.

```javascript
// BAD: do not manually add conditions.options metadata
{
  "type": "n8n-nodes-base.if",
  "typeVersion": 2.2,
  "parameters": {
    "conditions": {
      "options": { /* manually constructed */ },
      "boolean": [...]
    }
  }
}

// GOOD: just configure the conditions, let auto-sanitization handle the metadata
{
  "type": "n8n-nodes-base.if",
  "typeVersion": 2.2,
  "parameters": {
    "conditions": {
      "boolean": [{ "value1": "={{$json.active}}", "operation": "equals", "value2": true }]
    }
  }
}
```

---

### Symptom: Switch branch count warning with fallback (known issue #306)

> `{ "type": "configuration_mismatch", "message": "Switch has 3 rules but 4 output connections", "node": "Switch" }`

**Cause:** False positive when using "fallback" mode. The fallback creates an extra output that is not represented in the rules count, so validation flags a mismatch that is actually intentional.

**Solution:** Ignore if you are intentionally using fallback mode. The extra output is the fallback branch.

```javascript
// BAD: removing the fallback connection just to silence the warning
{
  "type": "n8n-nodes-base.switch",
  "parameters": { "rules": [...], "fallbackOutput": "none" }
}

// GOOD: keep the fallback if you want it, accept the warning
{
  "type": "n8n-nodes-base.switch",
  "parameters": {
    "rules": [...],
    "fallbackOutput": "extra"   // ACCEPTED: warning is a false positive
  }
}
```

---

### Symptom: credentials cannot be validated in test mode (known issue #338)

> `{ "type": "credentials_invalid", "message": "Cannot validate credentials without execution context" }`

**Cause:** False positive during static validation. Credentials are validated at runtime, not at build time, so the validator cannot test them.

**Solution:** Ignore. Credentials are tested when the workflow actually runs. If credentials are wrong, you will see a real error at execution time.

```javascript
// BAD: remove credentials configuration just to silence the warning
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": { "url": "..." }
  // authentication removed
}

// GOOD: keep credentials, accept the warning
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": { "url": "...", "authentication": "headerAuth" },
  "credentials": { "headerAuth": { "id": "abc", "name": "My Key" } }
}
```

---

## Decision Framework: Should I Fix This Warning?

1. Is it a SECURITY warning? Yes -> always fix. No -> continue.
2. Is this a production workflow? No -> probably acceptable. Yes -> continue.
3. Does it handle critical data? Yes -> fix the warning. No -> continue.
4. Is there a known workaround or known-issue marker? Yes -> acceptable if documented. No -> fix the warning.

## Summary

### Always Fix

- Security warnings (real credentials, SQL injection risks)
- Production workflow errors of any type
- Hardcoded real credentials

### Usually Fix

- Error handling on production nodes
- Retry logic for flaky external APIs
- Input validation on public webhooks
- Rate limiting in high-volume loops

### Often Acceptable

- Error handling in dev/test workflows
- Retry logic for idempotent or internal calls
- Rate limiting on low-volume workflows
- Query LIMIT on small known datasets

### Always Acceptable

- Known n8n issues (#304 IF metadata, #306 Switch fallback, #338 credentials in test mode)
- Auto-sanitization warnings (operator structure)

## See Also

- [api.md](./api.md): Tool signatures that surface these errors.
- [patterns.md](./patterns.md): How to run the validation loop, recovery strategies, and progressive validation.
- [configuration.md](./configuration.md): Profile selection to reduce false-positive noise.
- [../expressions/](../expressions/): Expression syntax reference for `invalid_expression` fixes.
- [../node-configuration/](../node-configuration/): Required-field discovery for `missing_required` and `invalid_value`.
