# API Reference: Configuration-Relevant MCP Calls

The configuration loop uses a small set of MCP calls: `get_node_essentials`, `get_node_info` (both surfaced through the unified `get_node` interface), `patchNodeField` (via `n8n_update_partial_workflow`), and `update_full_workflow` for whole-node replacement. This file documents each call, the property dependency model, and the `displayOptions` semantics that govern when fields appear, hide, or become required.

---

## get_node (Unified Entry Point)

The `get_node` MCP tool is the primary discovery surface for configuration. It exposes three modes plus two detail levels.

### Standard Detail (Default, Use This First)

```javascript
get_node({
  nodeType: "nodes-base.slack"
});
// detail: "standard" is the default, no need to set explicitly
```

**Returns** (approximately 1-2K tokens):
- Required fields
- Common options
- Operation list
- Metadata

**Use for**: 95% of configuration needs. This is the first call you make for any node.

Equivalent to the `get_node_essentials` call in older surface naming: lean schema with the fields most likely to be required for the most common operations.

### Full Detail (Use Sparingly)

```javascript
get_node({
  nodeType: "nodes-base.slack",
  detail: "full"
});
```

**Returns** (approximately 3-8K tokens):
- Complete schema
- All properties (including those gated by `displayOptions`)
- All nested options

**Warning**: Large response. Use only when standard detail is insufficient, for example when you must inspect the full `displayOptions` graph for a deeply nested field.

Equivalent to the `get_node_info` call in older surface naming: full property definitions for a node.

### search_properties Mode (Find a Specific Field)

```javascript
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "auth"
});
```

**Use for**: Finding authentication, headers, body fields, or any property when you know a keyword but not the full path. Returns matching property paths with descriptions, including their `displayOptions` rules.

### Common Mistakes

- Jumping straight to `detail: "full"` instead of starting with standard. Wastes tokens, slows iteration.
- Skipping `get_node` entirely and guessing field names. Almost always produces invalid configurations.
- Using `search_properties` for a brand-new node when you have not yet read the standard summary.

---

## validate_node (The Other Half of the Loop)

Every configuration call should be paired with validation. This is not a configuration tool per se, but it is the feedback signal that drives the loop.

```javascript
validate_node({
  nodeType: "nodes-base.httpRequest",
  config,
  profile: "runtime"
});
```

Validation returns dependency hints in error messages, for example "body required when sendBody=true". Treat those messages as the authoritative source of truth about which fields are required for the current operation and dependency state.

See [../validation/](../validation/) for full error taxonomy.

---

## patchNodeField (Surgical Field Edits)

When you need to edit a specific string inside a node field rather than replace the entire field, use `patchNodeField` inside `n8n_update_partial_workflow`. This is especially useful for:

- Editing code inside Code nodes without re-transmitting the full code block.
- Updating URLs or text in large HTML email templates.
- Fixing typos in JSON bodies or long text fields.

```javascript
// Instead of replacing the entire jsCode field:
n8n_update_partial_workflow({
  id: "wf-123",
  operations: [{
    type: "patchNodeField",
    nodeName: "Code",
    fieldPath: "parameters.jsCode",
    patches: [{find: "const limit = 10;", replace: "const limit = 50;"}]
  }]
})
```

### Strictness Guarantees

`patchNodeField` is strict by design:

- It errors if the `find` string is not found.
- It errors if `find` matches multiple times, unless `replaceAll: true`.

This prevents accidental silent failures during configuration updates. The strictness is a feature, not a bug, it forces you to be explicit about which match you intend to change. See [../mcp-tools/](../mcp-tools/) for full syntax and worked examples.

---

## update_full_workflow (Whole-Node Replacement)

When the patch is broader than a string-level edit (changing operation, replacing a body block, restructuring an `assignments` array), replace the whole node. The workflow-level call is `update_full_workflow` (or the older `n8n_update_partial_workflow` with node-level operations).

**Decision rule**:

- Single substring change in a long string field, use `patchNodeField`.
- Structural changes, multiple fields, or short fields, replace the node parameters wholesale.

Validate before deploying, in both cases.

```javascript
// Whole-node replacement pattern
const config = {/* full parameters */};
const result = validate_node({nodeType: "...", config, profile: "runtime"});
if (result.valid) {
  // Deploy via update_full_workflow / n8n_update_partial_workflow node-op
}
```

---

## Property Dependency Model

Field visibility and requiredness in n8n are governed by `displayOptions` rules attached to each property.

### What Are Property Dependencies?

**Definition**: Rules that control when fields are visible or required based on other field values.

**Mechanism**: `displayOptions` in the node schema.

**Purpose**:
- Show relevant fields only.
- Hide irrelevant fields.
- Simplify the configuration UX.
- Prevent invalid configurations.

### displayOptions Structure

**Basic format**:

```javascript
{
  "name": "fieldName",
  "type": "string",
  "displayOptions": {
    "show": {
      "otherField": ["value1", "value2"]
    }
  }
}
```

**Translation**: Show `fieldName` when `otherField` equals "value1" OR "value2".

### show vs hide

**show** (most common): field appears when condition matches.

```javascript
{
  "name": "body",
  "displayOptions": {
    "show": {
      "sendBody": [true]
    }
  }
}
// Meaning: show "body" when sendBody = true
```

**hide** (less common): field disappears when condition matches.

```javascript
{
  "name": "advanced",
  "displayOptions": {
    "hide": {
      "simpleMode": [true]
    }
  }
}
// Meaning: hide "advanced" when simpleMode = true
```

### AND Logic (Multiple Keys in show)

```javascript
{
  "name": "body",
  "displayOptions": {
    "show": {
      "sendBody": [true],
      "method": ["POST", "PUT", "PATCH"]
    }
  }
}
// Show "body" when sendBody = true AND method IN (POST, PUT, PATCH).
```

All keys must match (AND logic across keys).

### OR Logic (Multiple Values in One Key)

```javascript
{
  "name": "someField",
  "displayOptions": {
    "show": {
      "method": ["POST", "PUT", "PATCH"]
    }
  }
}
// Show when method = POST OR PUT OR PATCH.
```

Any value matches (OR logic within a single key).

---

## Common Dependency Shapes

### Boolean Toggle

A boolean flag gates a single dependent field.

```javascript
{
  "name": "sendBody",
  "type": "boolean",
  "default": false
}

{
  "name": "body",
  "displayOptions": {
    "show": {
      "sendBody": [true]
    }
  }
}
```

Flow: user toggles `sendBody`, the `body` field appears or hides.

### Resource/Operation Cascade

Different operations show different field sets.

```javascript
// Operation: post
{
  "name": "channel",
  "displayOptions": {
    "show": {
      "resource": ["message"],
      "operation": ["post"]
    }
  }
}

// Operation: update
{
  "name": "messageId",
  "displayOptions": {
    "show": {
      "resource": ["message"],
      "operation": ["update"]
    }
  }
}
```

Flow: pick `resource = message`, then `operation = post` shows `channel`. Switching to `operation = update` hides `channel` and shows `messageId`.

### Type-Specific Configuration

Different types within a single block need different fields.

```javascript
// String operations that need value2
{
  "name": "value2",
  "displayOptions": {
    "show": {
      "conditions.string.0.operation": ["equals", "notEquals", "contains"]
    }
  }
}

// Unary operations hide value2
{
  "displayOptions": {
    "hide": {
      "conditions.string.0.operation": ["isEmpty", "isNotEmpty"]
    }
  }
}
```

### Method-Specific Fields

HTTP methods unlock different option sets.

```javascript
// Query parameters available for all methods
{
  "name": "queryParameters",
  "displayOptions": {
    "show": {
      "sendQuery": [true]
    }
  }
}

// Body available only for body-bearing methods
{
  "name": "body",
  "displayOptions": {
    "show": {
      "sendBody": [true],
      "method": ["POST", "PUT", "PATCH", "DELETE"]
    }
  }
}
```

---

## Finding Property Dependencies

### Search by Keyword

```javascript
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "body"
});
// Returns properties matching "body" with their displayOptions rules.
```

### Inspect the Full Schema

```javascript
get_node({
  nodeType: "nodes-base.httpRequest",
  detail: "full"
});
// Returns the complete schema, every property's displayOptions are visible.
```

### When to Use Each

**Use `search_properties` when**:
- Validation fails with "missing field" but the field is not in your config.
- A field appears or disappears unexpectedly between operations.
- You need to understand what controls a specific field's visibility.
- You are building dynamic configuration tooling.

**Use `detail: "full"` when**:
- You need the entire dependency graph for a node.
- You are debugging a multi-step dependency chain.

**Do not use either when**:
- Standard `get_node` already showed you the required fields.
- The field requirements are obvious from the operation you chose.

---

## Worked Example: HTTP Request POST With JSON

Each step exposes the next required field via `displayOptions`.

**Step 1**: Set method.

```javascript
{
  "method": "POST"
  // sendBody becomes visible
}
```

**Step 2**: Enable body.

```javascript
{
  "method": "POST",
  "sendBody": true
  // body field becomes visible AND required
}
```

**Step 3**: Configure body contentType.

```javascript
{
  "method": "POST",
  "sendBody": true,
  "body": {
    "contentType": "json"
    // content field becomes visible AND required
  }
}
```

**Step 4**: Add content.

```javascript
{
  "method": "POST",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {
      "name": "John",
      "email": "john@example.com"
    }
  }
}
// Valid configuration.
```

**Dependency chain**:

```
method=POST
  → sendBody visible
    → sendBody=true
      → body visible + required
        → body.contentType=json
          → body.content visible + required
```

---

## Worked Example: IF Node Operator Dependencies

Binary vs unary operators expose different value fields.

**Binary operator** (`equals`):

```javascript
{
  "conditions": {
    "string": [
      {
        "operation": "equals"
        // value1 required, value2 required, singleValue should NOT be set
      }
    ]
  }
}
```

**Unary operator** (`isEmpty`):

```javascript
{
  "conditions": {
    "string": [
      {
        "operation": "isEmpty"
        // value1 required, value2 hidden, singleValue should be true (auto-added)
      }
    ]
  }
}
```

**Dependency table**:

| Operator | value1 | value2 | singleValue |
|---|---|---|---|
| equals | Required | Required | false |
| notEquals | Required | Required | false |
| contains | Required | Required | false |
| isEmpty | Required | Hidden | true |
| isNotEmpty | Required | Hidden | true |

---

## Worked Example: Slack Operation Matrix

Each operation requires a different subset of fields. This is the canonical operation-aware configuration case.

```javascript
// post message
{
  "resource": "message",
  "operation": "post"
  // Shows: channel (required), text (required), attachments, blocks
}

// update message
{
  "resource": "message",
  "operation": "update"
  // Shows: messageId (required), text (required), channel (optional)
}

// delete message
{
  "resource": "message",
  "operation": "delete"
  // Shows: messageId (required), channel (required)
  // Hides: text, attachments, blocks
}

// get message
{
  "resource": "message",
  "operation": "get"
  // Shows: messageId (required), channel (required)
  // Hides: text, attachments, blocks
}
```

**Field visibility matrix**:

| Field | post | update | delete | get |
|---|---|---|---|---|
| channel | Required | Optional | Required | Required |
| text | Required | Required | Hidden | Hidden |
| messageId | Hidden | Required | Required | Required |
| attachments | Optional | Optional | Hidden | Hidden |
| blocks | Optional | Optional | Hidden | Hidden |

---

## Nested Dependencies

Some dependencies live inside object properties. The parent value determines the structure expected for children.

```javascript
{
  "body": {
    "contentType": "json",
    // content expects a JSON object
    "content": {
      "key": "value"
    }
  }
}

{
  "body": {
    "contentType": "form-data",
    // content expects a form fields array
    "content": [
      {
        "name": "field1",
        "value": "value1"
      }
    ]
  }
}
```

**Strategy**: configure parent first, then children. The parent value defines the child structure.

```javascript
// Step 1: set parent
{
  "body": {
    "contentType": "json"
  }
}

// Step 2: add children in parent-determined format
{
  "body": {
    "contentType": "json",
    "content": {
      "key": "value"
    }
  }
}
```

---

## Auto-Sanitization

Some structural quirks are fixed automatically by n8n. Others are not.

**Auto-sanitization fixes operator structure** (IF and Switch nodes). For example, the `singleValue` flag on unary operators:

```javascript
// You configure (missing singleValue)
{
  "type": "boolean",
  "operation": "isEmpty"
}

// Auto-sanitization adds it
{
  "type": "boolean",
  "operation": "isEmpty",
  "singleValue": true
}
```

**Auto-sanitization does NOT fix missing required fields**. You still must add them yourself.

```javascript
// You configure (missing channel)
{
  "resource": "message",
  "operation": "post",
  "text": "Hello"
}

// Auto-sanitization does NOT add channel.
// Validation will fail.
```

Trust auto-sanitization for operator metadata. Do not trust it for business-required fields like channel, messageId, or table.

---

## See Also

- [README.md](./README.md): Configuration philosophy and reading order.
- [patterns.md](./patterns.md): Per-node-type patterns that consume these API calls.
- [gotchas.md](./gotchas.md): Failure modes specific to displayOptions, missing fields, and dependency cycles.
- [configuration.md](./configuration.md): Node dependencies, credentials, version pinning.
- [../mcp-tools/](../mcp-tools/): Full MCP tool surface beyond the configuration calls listed here.
- [../validation/](../validation/): Validation error taxonomy and the validation half of the configure-validate loop.
