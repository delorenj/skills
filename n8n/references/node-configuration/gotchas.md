# Gotchas: Common Configuration Failures

Each entry uses the four-part structure: **Symptom**, **Cause**, **Fix**, **Prevention**. Failures are grouped by category: displayOptions traps, missing required fields per operation, dependency cycles, and miscellaneous configuration mistakes.

---

## displayOptions Traps

### Field Required But Not Visible

**Symptom**: Validation returns `{ "type": "missing_required", "property": "body", "message": "body is required" }` but you do not see a `body` field in your configuration. There is nowhere to put the value the validator is asking for.

**Cause**: The `body` field has a `displayOptions.show` rule that hides it until a gating field is set. For HTTP Request, `body` only shows when `sendBody: true` AND `method` is POST/PUT/PATCH/DELETE. Validation evaluates against the full schema, including hidden fields, so the requirement surfaces even though the field is gated.

**Fix**:

```javascript
// Discover the gating field
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "body"
});
// Returns body's displayOptions: shows when sendBody=true.

// Add the gating field
{
  "method": "POST",
  "sendBody": true,   // Now body is visible AND required
  "body": {/* ... */}
}
```

**Prevention**: When validation complains about a field you cannot see, immediately run `get_node` in `search_properties` mode for the missing field name. Read the `displayOptions.show` keys, those are the fields you need to set first.

### Field Disappears After Changing Operation

**Symptom**: You had a working Slack configuration with `operation: "post"`, you changed it to `operation: "update"`, and now validation says `messageId is required`. The `channel` and `text` you carefully set are still in the config but the node refuses to validate.

**Cause**: Different operations expose different field sets via `displayOptions`. The cascading `resource` plus `operation` keys gate which fields are required. `post` requires `channel` and `text`. `update` requires `messageId` and `text`. Reusing a `post` configuration as the starting point for `update` leaves you with the wrong required fields.

**Fix**:

```javascript
// Re-check requirements for the new operation
get_node({nodeType: "nodes-base.slack"});

// Build the update configuration from scratch
{
  "resource": "message",
  "operation": "update",
  "messageId": "1234567890",  // Required for update
  "text": "Updated",
  "channel": "#general"       // Optional for update, can be inferred
}
```

**Prevention**: Treat operation changes as a re-discovery moment, never a field rename. Add a checklist habit: change operation, run `get_node`, rebuild required fields.

### Field Validates But Does Not Save

**Symptom**: You configure `body` on a GET request. Validation passes. You deploy. After save, `body` is gone from the saved node.

**Cause**: The schema accepted the field shape, but `displayOptions` strips fields not visible for the current configuration. `body` is hidden when `method = GET`, so it is dropped at save time regardless of what you put in it. Validation does not always reject incompatible-but-well-formed values, but persistence enforces visibility.

**Fix**:

```javascript
// Inspect the dependencies before configuring
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "body"
});
// Confirms body only persists for POST/PUT/PATCH/DELETE.

// Use a method that supports body
{
  "method": "POST",
  "sendBody": true,
  "body": {/* ... */}
}
```

**Prevention**: Respect dependencies from the start. Configure parent gates before children. If a method does not support a feature, do not configure that feature on that method.

### AND vs OR Confusion in displayOptions

**Symptom**: You see a `displayOptions.show` block with multiple keys and assume any one of them triggers visibility. The field never appears even when one condition matches.

**Cause**: Multiple keys inside a single `show` block are AND-ed together. Multiple values inside one key are OR-ed. Mixing these up causes you to set only one of several required gates.

**Fix**: Read the rule carefully:

```javascript
{
  "displayOptions": {
    "show": {
      "sendBody": [true],                 // Condition 1
      "method": ["POST", "PUT", "PATCH"]  // Condition 2 (any of these)
    }
  }
}
// Field shows when (sendBody = true) AND (method IN POST/PUT/PATCH).
```

**Prevention**: Mentally translate every `displayOptions` block into a Boolean expression before acting on it. AND across keys, OR within values. Document the expected dependency chain when designing a non-trivial configuration.

---

## Missing Required Fields Per Operation

### Slack post Without channel

**Symptom**: Validation error `channel is required for resource=message operation=post`.

**Cause**: `post` requires both `channel` and `text`. They are gated only by `resource=message` AND `operation=post`, no other prerequisite. If you copy a config from a different operation or forget the channel, the field is missing.

**Fix**:

```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",  // Required
  "text": "Hello"         // Required
}
```

**Prevention**: Keep a small per-operation cheat-sheet for the Slack node. The patterns file in this reference has the matrix.

### Slack update Without messageId

**Symptom**: Validation error `messageId is required for resource=message operation=update`. Your `channel` and `text` are there but the validator demands `messageId`.

**Cause**: `update` requires `messageId` (the timestamp ID of the prior message). `channel` is optional for `update` but required for `post`, so reusing a `post` configuration leaves `messageId` missing.

**Fix**:

```javascript
{
  "resource": "message",
  "operation": "update",
  "messageId": "1234567890.123456",
  "text": "Updated"
}
```

**Prevention**: Pipe the original message's response into the update node so `messageId` flows naturally. Use `={{$json.ts}}` if posting and updating in the same workflow.

### HTTP Request POST Without sendBody

**Symptom**: Validation error `sendBody required for POST`. Your `body` is configured but the validator still complains.

**Cause**: `sendBody` is a separate boolean gate that controls whether the body block is included in the request at all. Setting `body` without setting `sendBody: true` leaves the body invisible.

**Fix**:

```javascript
{
  "method": "POST",
  "url": "...",
  "sendBody": true,   // Required gate
  "body": {/* ... */}
}
```

**Prevention**: Memorize the HTTP Request pattern: every body-bearing method needs `sendBody: true`. Same applies to `sendQuery` for query parameters and `sendHeaders` for custom headers.

### Postgres insert Without table or columns

**Symptom**: Validation error `table is required` or `columns is required`.

**Cause**: `insert`, `update`, and `delete` operations all require `table`. `insert` additionally requires `columns`. The default schema does not provide a sensible fallback.

**Fix**:

```javascript
{
  "operation": "insert",
  "table": "users",
  "columns": "name,email,created_at",
  "additionalFields": {
    "mode": "list",
    "queryParameters": "John,john@example.com,NOW()"
  }
}
```

**Prevention**: For any database operation, identify the table first, then the columns, then the values. Build in that order.

### Webhook Without path

**Symptom**: Validation error `path is required` even though you set `httpMethod` and `responseMode`.

**Cause**: `path` is the unique URL slug that identifies this webhook on the n8n server. There is no default, n8n cannot guess what URL the external caller expects.

**Fix**:

```javascript
{
  "path": "my-webhook",
  "httpMethod": "POST",
  "responseMode": "onReceived"
}
```

**Prevention**: Treat `path` as the first field you set on any Webhook node, before method or response mode.

---

## Dependency Cycles

### contentType Set Before sendBody

**Symptom**: You set `body.contentType: "json"` and `body.content: {...}`. The node validates clean but the request is never sent with a body. The receiving API gets an empty payload.

**Cause**: `body.contentType` and `body.content` are only meaningful when `sendBody: true`. Without `sendBody`, the body block is structurally valid but never serialized into the actual HTTP request. There is no validation failure because the schema permits the field shape, the runtime simply ignores the block.

**Fix**:

```javascript
{
  "method": "POST",
  "sendBody": true,   // Set the gate first
  "body": {
    "contentType": "json",
    "content": {/* ... */}
  }
}
```

**Prevention**: Configure parent gates before children, always. Build the dependency chain top-down: `method` → `sendBody` → `body.contentType` → `body.content`.

### content Shape Mismatch With contentType

**Symptom**: You changed `body.contentType` from `json` to `form-data` and your previously-working `body.content` (a JSON object) is now serialized incorrectly or rejected by the API.

**Cause**: The expected shape of `body.content` is determined by `body.contentType`. For `json`, content is a JSON object. For `form-data`, content is an array of `{name, value}` form fields. The child structure is gated by the parent value.

**Fix**:

```javascript
// For contentType: "json"
{
  "body": {
    "contentType": "json",
    "content": {"key": "value"}
  }
}

// For contentType: "form-data"
{
  "body": {
    "contentType": "form-data",
    "content": [
      {"name": "field1", "value": "value1"}
    ]
  }
}
```

**Prevention**: When changing `contentType`, also rebuild `content`. Run `get_node` with `search_properties` for `content` to confirm the expected shape under the new `contentType`.

### IF Operator Switch Leaves Stale value2

**Symptom**: You change an IF condition from `operation: "equals"` (binary) to `operation: "isEmpty"` (unary). The `value2` field you previously set is still there in the saved config. Sometimes the condition evaluates oddly.

**Cause**: Switching from a binary to a unary operator does not strip `value2`. Auto-sanitization adds `singleValue: true` for unary operators but does not remove leftover fields. Stale `value2` can survive and confuse runtime evaluation.

**Fix**: Remove `value2` when switching to a unary operator.

```javascript
// After switch
{
  "value1": "={{$json.email}}",
  "operation": "isEmpty"
  // singleValue: true auto-added, value2 should NOT be here
}
```

**Prevention**: When switching operator type (binary to unary or vice versa), rebuild the condition object from scratch rather than mutating in place. Or validate after the switch, the validator will hint if `value2` is unexpectedly present.

---

## Other Common Configuration Mistakes

### Webhook Body Access via Wrong Path

**Symptom**: Downstream nodes evaluate `={{$json.email}}` and get `undefined`. The webhook clearly received the payload (you can see it in the execution data).

**Cause**: Webhook puts the request body under `$json.body`, not `$json` directly. Other webhook metadata (`headers`, `query`, `params`) is at the top level of `$json`.

**Fix**:

```javascript
// Wrong
{"text": "={{$json.email}}"}

// Correct
{"text": "={{$json.body.email}}"}
```

**Prevention**: Always inspect the webhook's actual output shape in n8n's execution view before writing downstream expressions. Treat `$json.body` as the default reach for webhook payloads.

### Slack Channel Without #

**Symptom**: Slack post succeeds at validation but fails at runtime with `channel_not_found`.

**Cause**: Public channels must be referenced as `#channel-name` or by their Slack channel ID. A bare `channel-name` without `#` is treated as a literal name lookup and may not resolve.

**Fix**:

```javascript
// Wrong
{"channel": "general"}

// Correct (public channel by name)
{"channel": "#general"}

// Correct (any channel by ID)
{"channel": "C0123456789"}
```

**Prevention**: Standardize on channel IDs from the Slack API for programmatic posting. They are stable and unambiguous.

### Set Node Wrong Type

**Symptom**: Downstream nodes treat your numeric value as a string. Math operations break or produce concatenated strings.

**Cause**: The `type` field on each assignment coerces the value. Setting `type: "string"` with `value: "25"` produces the string `"25"`, not the number `25`.

**Fix**:

```javascript
// Wrong
{"name": "age", "value": "25", "type": "string"}

// Correct
{"name": "age", "value": 25, "type": "number"}
```

**Prevention**: For every Set assignment, deliberately choose the type that matches the downstream consumer's expectations. Use `number` for numeric IDs, ages, counts. Use `boolean` for flags.

### Code Node Using Expression Syntax

**Symptom**: Your Code node returns literal strings like `"={{$json.name}}"` instead of the actual data values.

**Cause**: Expressions (`={{ ... }}`) only interpolate inside parameter fields, not inside `jsCode`. JavaScript code runs in its own context with `$input`, `$json`, and `$node` as JavaScript variables, not as expression markers.

**Fix**:

```javascript
// Wrong, expression inside jsCode is a literal string
{"jsCode": "const name = '={{$json.name}}';"}

// Correct, use the JS API
{"jsCode": "const name = $input.item.json.name;"}
```

**Prevention**: Remember the two worlds: parameter fields use expressions, Code nodes use JavaScript. See [../code-javascript/](../code-javascript/) for the full API.

### Postgres SQL Injection From Direct Expression

**Symptom**: User-supplied input passes through to your SQL query unsanitized. Either you get SQL errors on quotes/apostrophes, or worse, you have a security incident.

**Cause**: Inlining `={{$json.email}}` directly into a query string concatenates user input into SQL. There is no escaping.

**Fix**:

```javascript
// BAD, SQL injection
{"query": "SELECT * FROM users WHERE email = '{{$json.email}}'"}

// GOOD, parameterized
{
  "query": "SELECT * FROM users WHERE email = $1",
  "additionalFields": {
    "mode": "list",
    "queryParameters": "={{$json.email}}"
  }
}
```

**Prevention**: Treat any user-controlled value as untrusted. Never concatenate it into a SQL string. Use `$1`, `$2`, ... placeholders with `queryParameters`.

### Schedule Trigger Missing Timezone

**Symptom**: Your schedule fires at the right hour according to the server, but your team in another timezone sees it firing at unexpected times.

**Cause**: Without an explicit `timezone`, schedule triggers use the n8n server's system timezone. This may not match your team's expectation, especially in distributed deployments or container hosts that default to UTC.

**Fix**:

```javascript
{
  "rule": {
    "interval": [/* ... */],
    "timezone": "America/New_York"
  }
}
```

**Prevention**: Always set `timezone` explicitly on every schedule trigger. Treat it as a required field even though the schema marks it optional.

### Switch Rule/Output Count Mismatch

**Symptom**: One of your Switch outputs always receives 0 items, or the fallback fires for cases that should match a rule.

**Cause**: The number of rules in the Switch configuration must match the number of output connections from the node. Mismatched counts route items to outputs that do not exist (silently dropped) or leave unused rules.

**Fix**: Ensure the count of `rules.rules[]` equals the visible output count on the node, plus configure `fallbackOutput` for the catch-all.

**Prevention**: When adding or removing a Switch rule, also adjust the node's output connections in the same change.

### Google Sheets append on Formula Sheets

**Symptom**: After an `append` operation, your formula columns are overwritten with literal values. The formulas that computed `Total = Quantity * Price` are now just numbers, and they stop updating on later edits.

**Cause**: The Google Sheets `append` operation writes values to all columns in the appended row, replacing any formulas present. n8n's append does not preserve formula cells.

**Fix**: Use HTTP Request with the Sheets API `values.update` (PUT) and a `googleApi` credential, scoped to only the data columns:

```javascript
{
  "method": "PUT",
  "url": "https://sheets.googleapis.com/v4/spreadsheets/SHEET_ID/values/A2:C2?valueInputOption=USER_ENTERED",
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "googleApi",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {"values": [["John", "Doe", "john@example.com"]]}
  }
}
```

**Prevention**: Audit any sheet you write to for formula columns. If formulas exist, switch to the HTTP Request pattern. See [patterns.md](./patterns.md) "Google Sheets Bulk Write".

### Google Sheets Per-Item API Explosion

**Symptom**: Your workflow with 100 items takes minutes to run and you hit Google API rate limits.

**Cause**: Google Sheets nodes execute once per input item. 100 items mean 100 API calls. This is fine for small batches but quickly becomes a bottleneck.

**Fix**: Aggregate items in a Code node first, then write in bulk with HTTP Request:

```javascript
// Code node, runOnceForAllItems
{
  "jsCode": "const rows = $input.all().map(i => [i.json.name, i.json.email]);\nreturn [{json: {values: rows}}];"
}
// Then a single HTTP Request to values.update
```

**Prevention**: Whenever you write more than ~20 items to Google Sheets in a workflow, switch to bulk HTTP Request immediately.

### Manually Adding singleValue for Unary Operators

**Symptom**: You hand-set `singleValue: true` on an IF unary condition. Sometimes it works, sometimes auto-sanitization rewrites it and you fight against the system.

**Cause**: Auto-sanitization adds `singleValue: true` for unary operators automatically. Manually setting it creates configuration noise and can race against the auto-sanitizer.

**Fix**: Let auto-sanitization handle it.

```javascript
// Don't manage singleValue yourself
{
  "value1": "={{$json.email}}",
  "operation": "isEmpty"
  // System adds singleValue: true on save
}
```

**Prevention**: Trust auto-sanitization for operator structure (singleValue, IF/Switch metadata). Focus your attention on business-required fields instead.

---

## See Also

- [README.md](./README.md): Configuration philosophy.
- [api.md](./api.md): `displayOptions` semantics and how to discover dependencies.
- [patterns.md](./patterns.md): Correct configurations that avoid these gotchas.
- [configuration.md](./configuration.md): Credentials and environment requirements.
- [../validation/](../validation/): Validation error taxonomy that surfaces these symptoms.
- [../expressions/](../expressions/): Expression syntax issues that overlap with several gotchas here.
