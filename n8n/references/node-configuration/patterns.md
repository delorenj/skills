# Patterns: Copy-Paste-Ready Node Configurations

Named patterns for configuring n8n nodes. Covers the four cross-cutting patterns first (progressive disclosure, operation-aware setup, property dependency chains, surgical edits vs full updates), then per-node patterns organized by category. All snippets are runnable starting points, adapt to your data shape and validate before deploying.

---

## Cross-Cutting Patterns

These four meta-patterns apply across every node type. Master these first, then specialize.

### Pattern: Progressive Disclosure of Fields

Start with the smallest possible configuration. Let validation tell you what to add next.

```javascript
// Step 1: minimal
const config = {
  "method": "POST",
  "url": "https://api.example.com/create",
  "authentication": "none"
};

// Step 2: validate
validate_node({nodeType: "nodes-base.httpRequest", config, profile: "runtime"});
// Error: "sendBody required for POST"

// Step 3: add field, validate again
config.sendBody = true;
validate_node({...});
// Error: "body required when sendBody=true"

// Step 4: complete it
config.body = {
  contentType: "json",
  content: {name: "={{$json.name}}", email: "={{$json.email}}"}
};
validate_node({...});
// Valid
```

Average 2-3 iterations to a valid configuration. Do not try to enumerate every option in your head, the validator already has that knowledge.

### Pattern: Operation-Aware Setup

Before changing the `operation` field on a resource/operation node, re-discover the new requirements. Field sets are not transferable across operations.

```javascript
// Working: post message
const post = {
  "resource": "message",
  "operation": "post",
  "channel": "#general",
  "text": "Hello"
};

// To switch to update, do NOT just change operation in place.
// Step 1: re-check requirements for the new operation
get_node({nodeType: "nodes-base.slack"});
// Step 2: build the new config from scratch
const update = {
  "resource": "message",
  "operation": "update",
  "messageId": "1234567890",  // Required for update, NOT for post
  "text": "Updated"
  // channel optional, can be inferred
};
```

### Pattern: Property Dependency Chains

Configure parent fields first, then children. Each parent value gates which children are visible and required.

```javascript
// HTTP Request POST with JSON body
// Layer 1: method gates sendBody
{"method": "POST"}

// Layer 2: sendBody gates body
{"method": "POST", "sendBody": true}

// Layer 3: contentType inside body gates content shape
{
  "method": "POST",
  "sendBody": true,
  "body": {"contentType": "json"}
}

// Layer 4: content matches contentType shape
{
  "method": "POST",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {"name": "John", "email": "john@example.com"}
  }
}
```

If you set children before parents, you may write valid-looking values that the schema strips on save because their parent gate is wrong.

### Pattern: Surgical Edits vs Full Updates

Choose the right update granularity:

- **Surgical edit (patchNodeField)**: a single substring change inside a long string field (Code, HTML template, JSON body, long URL).
- **Full node update**: structural changes, multiple fields, or short fields where the patch context is bigger than the field itself.

```javascript
// Surgical edit
n8n_update_partial_workflow({
  id: "wf-123",
  operations: [{
    type: "patchNodeField",
    nodeName: "Code",
    fieldPath: "parameters.jsCode",
    patches: [{find: "const limit = 10;", replace: "const limit = 50;"}]
  }]
});

// Full node update (structural change)
// Build full parameters object, validate, then replace the node.
```

`patchNodeField` errors on zero matches or multiple matches (unless `replaceAll: true`). Use this strictness to your advantage, it forces explicit intent.

---

## HTTP and API Nodes

### Pattern: HTTP Request GET

Minimal:

```javascript
{
  "method": "GET",
  "url": "https://api.example.com/users",
  "authentication": "none"
}
```

With query parameters:

```javascript
{
  "method": "GET",
  "url": "https://api.example.com/users",
  "authentication": "none",
  "sendQuery": true,
  "queryParameters": {
    "parameters": [
      {"name": "limit", "value": "100"},
      {"name": "offset", "value": "={{$json.offset}}"}
    ]
  }
}
```

With authentication:

```javascript
{
  "method": "GET",
  "url": "https://api.example.com/users",
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "httpHeaderAuth"
}
```

### Pattern: HTTP Request POST With JSON

Minimal:

```javascript
{
  "method": "POST",
  "url": "https://api.example.com/users",
  "authentication": "none",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
}
```

With expressions:

```javascript
{
  "method": "POST",
  "url": "https://api.example.com/users",
  "authentication": "none",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {
      "name": "={{$json.name}}",
      "email": "={{$json.email}}",
      "metadata": {
        "source": "n8n",
        "timestamp": "={{$now.toISO()}}"
      }
    }
  }
}
```

**Gotcha**: remember `sendBody: true` for POST/PUT/PATCH. Without it, validation will complain and the body will not be sent.

### Pattern: HTTP Request PUT or PATCH

Same shape as POST, just change `method`:

```javascript
{
  "method": "PUT",
  "url": "https://api.example.com/users/123",
  "authentication": "none",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {"name": "Updated Name"}
  }
}
```

### Pattern: HTTP Request DELETE

Minimal (no body):

```javascript
{
  "method": "DELETE",
  "url": "https://api.example.com/users/123",
  "authentication": "none"
}
```

With body (some APIs allow it):

```javascript
{
  "method": "DELETE",
  "url": "https://api.example.com/users",
  "authentication": "none",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {"ids": ["123", "456"]}
  }
}
```

### Pattern: Webhook Receiver

Minimal:

```javascript
{
  "path": "my-webhook",
  "httpMethod": "POST",
  "responseMode": "onReceived"
}
```

**Gotcha**: webhook data is under `$json.body`, not `$json`.

```javascript
// Wrong
{"text": "={{$json.email}}"}

// Correct
{"text": "={{$json.body.email}}"}
```

With header auth:

```javascript
{
  "path": "secure-webhook",
  "httpMethod": "POST",
  "responseMode": "onReceived",
  "authentication": "headerAuth",
  "options": {
    "responseCode": 200,
    "responseData": "{\n  \"success\": true\n}"
  }
}
```

Returning data from the last node:

```javascript
{
  "path": "my-webhook",
  "httpMethod": "POST",
  "responseMode": "lastNode",
  "options": {
    "responseCode": 201,
    "responseHeaders": {
      "entries": [
        {"name": "Content-Type", "value": "application/json"}
      ]
    }
  }
}
```

---

## Communication Nodes

### Pattern: Slack Post Message

Minimal:

```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",
  "text": "Hello from n8n!"
}
```

With dynamic content:

```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "={{$json.channel}}",
  "text": "New user: {{$json.name}} ({{$json.email}})"
}
```

With attachments:

```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "#alerts",
  "text": "Error Alert",
  "attachments": [
    {
      "color": "#ff0000",
      "fields": [
        {"title": "Error Type", "value": "={{$json.errorType}}"},
        {"title": "Timestamp", "value": "={{$now.toLocaleString()}}"}
      ]
    }
  ]
}
```

**Gotcha**: channel must start with `#` for public channels or be a channel ID.

### Pattern: Slack Update Message

```javascript
{
  "resource": "message",
  "operation": "update",
  "messageId": "1234567890.123456",
  "text": "Updated message content"
}
```

`messageId` is required, `channel` is optional (can be inferred).

### Pattern: Slack Create Channel

```javascript
{
  "resource": "channel",
  "operation": "create",
  "name": "new-project-channel",
  "isPrivate": false
}
```

**Gotcha**: channel name must be lowercase, no spaces, 1-80 chars.

### Pattern: Gmail Send Email

Minimal:

```javascript
{
  "resource": "message",
  "operation": "send",
  "to": "user@example.com",
  "subject": "Hello from n8n",
  "message": "This is the email body"
}
```

Dynamic with options:

```javascript
{
  "resource": "message",
  "operation": "send",
  "to": "={{$json.email}}",
  "subject": "Order Confirmation #{{$json.orderId}}",
  "message": "Dear {{$json.name}},\n\nYour order has been confirmed.\n\nThank you!",
  "options": {
    "ccList": "admin@example.com",
    "replyTo": "support@example.com"
  }
}
```

### Pattern: Gmail Get Email

Minimal:

```javascript
{
  "resource": "message",
  "operation": "getAll",
  "returnAll": false,
  "limit": 10
}
```

With filters:

```javascript
{
  "resource": "message",
  "operation": "getAll",
  "returnAll": false,
  "limit": 50,
  "filters": {
    "q": "is:unread from:important@example.com",
    "labelIds": ["INBOX"]
  }
}
```

---

## Database Nodes

### Pattern: Postgres Execute Query (SELECT)

Minimal:

```javascript
{
  "operation": "executeQuery",
  "query": "SELECT * FROM users WHERE active = true LIMIT 100"
}
```

With parameters (SQL injection prevention):

```javascript
{
  "operation": "executeQuery",
  "query": "SELECT * FROM users WHERE email = $1 AND active = $2",
  "additionalFields": {
    "mode": "list",
    "queryParameters": "user@example.com,true"
  }
}
```

**Gotcha**: always use parameterized queries for user input.

```javascript
// BAD, SQL injection risk
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

### Pattern: Postgres Insert

```javascript
{
  "operation": "insert",
  "table": "users",
  "columns": "name,email,created_at",
  "additionalFields": {
    "mode": "list",
    "queryParameters": "John Doe,john@example.com,NOW()"
  }
}
```

With expressions:

```javascript
{
  "operation": "insert",
  "table": "users",
  "columns": "name,email,metadata",
  "additionalFields": {
    "mode": "list",
    "queryParameters": "={{$json.name}},={{$json.email}},{{JSON.stringify($json)}}"
  }
}
```

### Pattern: Postgres Update

```javascript
{
  "operation": "update",
  "table": "users",
  "updateKey": "id",
  "columns": "name,email",
  "additionalFields": {
    "mode": "list",
    "queryParameters": "={{$json.id}},Updated Name,newemail@example.com"
  }
}
```

---

## Data Transformation Nodes

### Pattern: Set With Fixed Values

```javascript
{
  "mode": "manual",
  "duplicateItem": false,
  "assignments": {
    "assignments": [
      {"name": "status", "value": "active", "type": "string"},
      {"name": "count", "value": 100, "type": "number"}
    ]
  }
}
```

### Pattern: Set From Input Data

```javascript
{
  "mode": "manual",
  "duplicateItem": false,
  "assignments": {
    "assignments": [
      {
        "name": "fullName",
        "value": "={{$json.firstName}} {{$json.lastName}}",
        "type": "string"
      },
      {
        "name": "email",
        "value": "={{$json.email.toLowerCase()}}",
        "type": "string"
      },
      {
        "name": "timestamp",
        "value": "={{$now.toISO()}}",
        "type": "string"
      }
    ]
  }
}
```

**Gotcha**: use the correct `type` for each field.

```javascript
// Wrong, value coerced to string "25"
{"name": "age", "value": "25", "type": "string"}

// Correct, value is number 25
{"name": "age", "value": 25, "type": "number"}
```

### Pattern: Code Node Simple Transformation

```javascript
{
  "mode": "runOnceForAllItems",
  "jsCode": "return $input.all().map(item => ({\n  json: {\n    name: item.json.name.toUpperCase(),\n    email: item.json.email\n  }\n}));"
}
```

### Pattern: Code Node Per-Item Processing

```javascript
{
  "mode": "runOnceForEachItem",
  "jsCode": "// Process each item\nconst data = $input.item.json;\n\nreturn {\n  json: {\n    fullName: `${data.firstName} ${data.lastName}`,\n    email: data.email.toLowerCase(),\n    timestamp: new Date().toISOString()\n  }\n};"
}
```

**Gotcha**: inside Code nodes, use `$input.item.json` or `$input.all()`. Expressions (`{{...}}`) do not interpolate inside `jsCode`.

```javascript
// Wrong, the expression is a literal string here
{"jsCode": "const name = '={{$json.name}}';"}

// Correct
{"jsCode": "const name = $input.item.json.name;"}
```

See [../code-javascript/](../code-javascript/) for further Code-node specifics.

---

## Conditional Nodes

### Pattern: IF String Equals (Binary)

```javascript
{
  "conditions": {
    "string": [
      {
        "value1": "={{$json.status}}",
        "operation": "equals",
        "value2": "active"
      }
    ]
  }
}
```

### Pattern: IF String Contains (Binary)

```javascript
{
  "conditions": {
    "string": [
      {
        "value1": "={{$json.email}}",
        "operation": "contains",
        "value2": "@example.com"
      }
    ]
  }
}
```

### Pattern: IF isEmpty (Unary)

```javascript
{
  "conditions": {
    "string": [
      {
        "value1": "={{$json.email}}",
        "operation": "isEmpty"
        // No value2, singleValue: true added by auto-sanitization
      }
    ]
  }
}
```

**Gotcha**: unary operators (`isEmpty`, `isNotEmpty`) do not need `value2`. Auto-sanitization adds `singleValue: true` for you.

### Pattern: IF Number Greater Than

```javascript
{
  "conditions": {
    "number": [
      {
        "value1": "={{$json.age}}",
        "operation": "larger",
        "value2": 18
      }
    ]
  }
}
```

### Pattern: IF Boolean Is True

```javascript
{
  "conditions": {
    "boolean": [
      {
        "value1": "={{$json.isActive}}",
        "operation": "true"
      }
    ]
  }
}
```

### Pattern: IF Multiple Conditions (AND)

```javascript
{
  "conditions": {
    "string": [
      {
        "value1": "={{$json.status}}",
        "operation": "equals",
        "value2": "active"
      }
    ],
    "number": [
      {
        "value1": "={{$json.age}}",
        "operation": "larger",
        "value2": 18
      }
    ]
  },
  "combineOperation": "all"
}
```

### Pattern: IF Multiple Conditions (OR)

```javascript
{
  "conditions": {
    "string": [
      {"value1": "={{$json.status}}", "operation": "equals", "value2": "active"},
      {"value1": "={{$json.status}}", "operation": "equals", "value2": "pending"}
    ]
  },
  "combineOperation": "any"
}
```

### Pattern: Switch Multi-Way Routing

```javascript
{
  "mode": "rules",
  "rules": {
    "rules": [
      {
        "conditions": {
          "string": [
            {"value1": "={{$json.status}}", "operation": "equals", "value2": "active"}
          ]
        }
      },
      {
        "conditions": {
          "string": [
            {"value1": "={{$json.status}}", "operation": "equals", "value2": "pending"}
          ]
        }
      }
    ]
  },
  "fallbackOutput": "extra"
}
```

**Gotcha**: number of rules must match the number of outputs on the node.

---

## AI Nodes

### Pattern: OpenAI Chat Completion

Minimal:

```javascript
{
  "resource": "chat",
  "operation": "complete",
  "messages": {
    "values": [
      {"role": "user", "content": "={{$json.prompt}}"}
    ]
  }
}
```

With system prompt and options:

```javascript
{
  "resource": "chat",
  "operation": "complete",
  "messages": {
    "values": [
      {
        "role": "system",
        "content": "You are a helpful assistant specialized in customer support."
      },
      {
        "role": "user",
        "content": "={{$json.userMessage}}"
      }
    ]
  },
  "options": {
    "temperature": 0.7,
    "maxTokens": 500
  }
}
```

---

## Schedule Nodes

### Pattern: Schedule Trigger Daily At Time

```javascript
{
  "rule": {
    "interval": [
      {"field": "hours", "hoursInterval": 24}
    ],
    "hour": 9,
    "minute": 0,
    "timezone": "America/New_York"
  }
}
```

**Gotcha**: always set timezone explicitly.

```javascript
// Bad, uses server timezone
{"rule": {"interval": [...]}}

// Good, explicit timezone
{"rule": {"interval": [...], "timezone": "America/New_York"}}
```

### Pattern: Schedule Trigger Every N Minutes

```javascript
{
  "rule": {
    "interval": [
      {"field": "minutes", "minutesInterval": 15}
    ]
  }
}
```

### Pattern: Schedule Trigger Cron Expression

```javascript
{
  "mode": "cron",
  "cronExpression": "0 */2 * * *",
  "timezone": "America/New_York"
}
```

---

## Special-Case Nodes

### Pattern: SplitInBatches v3

```javascript
{
  "batchSize": 100,
  "options": {}
}
```

**Output wiring**:

- `main[0]` (done) connects to downstream processing. Insert a Limit 1 before downstream nodes to avoid duplicates.
- `main[1]` (each batch) connects to the loop body, which loops back to SplitInBatches input.

See [../workflow-patterns/](../workflow-patterns/) for detailed loop and nested loop patterns.

### Pattern: Google Sheets Bulk Write

Per-item execution: every input item triggers a separate API call. For 100 items into a Google Sheets "Append Row", that is 100 API calls.

For bulk writes, aggregate items in a Code node first and use a single HTTP Request with the Sheets API:

```javascript
// Step 1: Code node aggregates items
{
  "mode": "runOnceForAllItems",
  "jsCode": "const rows = $input.all().map(i => [i.json.name, i.json.email]);\nreturn [{json: {values: rows}}];"
}

// Step 2: HTTP Request to Sheets API values.update (PUT)
{
  "method": "PUT",
  "url": "https://sheets.googleapis.com/v4/spreadsheets/SHEET_ID/values/A1?valueInputOption=USER_ENTERED",
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "googleApi",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {"values": "={{$json.values}}"}
  }
}
```

**Gotcha**: never use `append` on sheets with formula columns. It overwrites the formulas. Use HTTP Request with `values.update` (PUT) and a `googleApi` credential instead.

---

## Anti-Patterns to Avoid

### Anti-Pattern: Over-Configuring Upfront

```javascript
// Bad, every possible field set "just in case"
{
  "method": "GET",
  "url": "...",
  "sendQuery": false,
  "sendHeaders": false,
  "sendBody": false,
  "timeout": 10000,
  "ignoreResponseCode": false
}

// Good, start minimal
{
  "method": "GET",
  "url": "...",
  "authentication": "none"
}
// Add fields only when needed.
```

### Anti-Pattern: Skip Validation

```javascript
// Bad
const config = {/* ... */};
n8n_update_partial_workflow({/* ... */});

// Good
const config = {/* ... */};
const result = validate_node({/* ... */});
if (result.valid) {
  n8n_update_partial_workflow({/* ... */});
}
```

### Anti-Pattern: Ignore Operation Context

```javascript
// Bad, changing operation but reusing the same fields
{
  "resource": "message",
  "operation": "update",
  "channel": "#general",
  "text": "..."
  // Missing: messageId (required for update)
}

// Good, re-check requirements when changing operation
get_node({nodeType: "nodes-base.slack"});
{
  "resource": "message",
  "operation": "update",
  "messageId": "1234567890",
  "text": "..."
}
```

### Anti-Pattern: Manually Fix Auto-Sanitization

```javascript
// Bad, hand-managing singleValue for an IF unary operator
{
  "operation": "isEmpty",
  "singleValue": true  // The system will add this for you
}

// Good, let auto-sanitization handle it
{
  "operation": "isEmpty"
  // Save and the system adds singleValue: true.
}
```

---

## Summary Table

| Category | Most Common | Key Gotcha |
|---|---|---|
| HTTP / API | GET, POST JSON | Remember `sendBody: true` |
| Webhooks | POST receiver | Data is under `$json.body` |
| Communication | Slack post | Channel format (`#name`) |
| Database | SELECT with params | Use parameterized queries |
| Transform | Set assignments | Correct `type` per field |
| Conditional | IF string equals | Unary vs binary operators |
| AI | OpenAI chat | System plus user messages |
| Schedule | Daily at time | Set timezone explicitly |

Configuration approach across all patterns:

1. Use the pattern as a starting point.
2. Adapt to your use case.
3. Validate.
4. Iterate based on errors.
5. Deploy when valid.

---

## See Also

- [README.md](./README.md): Reading order and configuration philosophy.
- [api.md](./api.md): The MCP calls and `displayOptions` model behind every pattern here.
- [gotchas.md](./gotchas.md): Common failure modes for each pattern category.
- [configuration.md](./configuration.md): Credentials, dependencies, and environment requirements that the patterns assume.
- [../workflow-patterns/](../workflow-patterns/): Higher-level workflow patterns that combine these node configurations.
- [../code-javascript/](../code-javascript/) and [../code-python/](../code-python/): Code-node language specifics.
- [../expressions/](../expressions/): Expression syntax for all `={{ ... }}` fields used in these patterns.
