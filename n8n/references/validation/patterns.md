# Validation Patterns

Copy-paste-ready patterns for using validation effectively. Each is a named, reusable approach.

## Pattern: The Validation Loop

The canonical configure, validate, fix, revalidate cycle. Telemetry shows 7,841 occurrences of this pattern with an average of 23 seconds reading errors and 58 seconds fixing per cycle, typically 2 to 3 iterations to reach valid state.

### Flow

```
1. Configure node
   ↓
2. validate_node (read errors)
   ↓
3. Fix one error category at a time
   ↓
4. validate_node again
   ↓
5. Repeat until valid (usually 2 to 3 iterations)
```

### Good Example

```javascript
// Iteration 1: start with what you know
let config = {
  resource: "channel",
  operation: "create"
};

let result = validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "runtime"
});
// Error: Missing "name"

// Iteration 2: add the field the error pointed to
config.name = "general";

result = validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "runtime"
});
// Error: Missing "text"

// Iteration 3
config.text = "Hello!";

result = validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "runtime"
});
// Valid
```

### Bad Example: One-Shot Validation

```javascript
// Bad: assume validation passed because no exception was thrown
const result = validate_node({ nodeType, config, profile: "runtime" });
deploy(config);   // result.valid was never checked
```

Always inspect `result.valid` and `result.errors` before treating a config as good.

## Pattern: Progressive Validation

Build the config in layers, validating after each addition. Prevents the "twenty errors at once" overwhelm.

### Good Example

```javascript
// Step 1: minimal valid config
let config = {
  resource: "message",
  operation: "post",
  channel: "#general",
  text: "Hello"
};
validate_node({ nodeType: "nodes-base.slack", config, profile: "runtime" });
// Valid

// Step 2: add attachments
config.attachments = [...];
validate_node({ nodeType: "nodes-base.slack", config, profile: "runtime" });
// Valid

// Step 3: add blocks
config.blocks = [...];
validate_node({ nodeType: "nodes-base.slack", config, profile: "runtime" });
// Valid
```

### Bad Example: Everything At Once

```javascript
// Bad: configure all 14 fields, validate, get 8 errors, panic
let config = {
  resource: "message", operation: "post", channel: "#general", text: "Hello",
  attachments: [...], blocks: [...], threadTs: "...", iconEmoji: "...",
  iconUrl: "...", linkNames: true, mrkdwn: true, unfurlLinks: false,
  unfurlMedia: false, asUser: true
};
validate_node({ nodeType: "nodes-base.slack", config, profile: "runtime" });
// 8 errors, unclear which field caused which
```

## Pattern: Error Triage

Sort the result by severity and act in order.

```javascript
const result = validate_node({ nodeType, config, profile: "runtime" });

// 1. Errors first: must fix
result.errors.forEach(error => {
  console.log(`MUST FIX: ${error.property} - ${error.message}`);
  console.log(`Fix: ${error.fix}`);
});

// 2. Warnings second: should fix (some may be false positives)
result.warnings.forEach(warning => {
  console.log(`SHOULD FIX: ${warning.property} - ${warning.message}`);
});

// 3. Suggestions last: optional
result.suggestions.forEach(s => {
  console.log(`OPTIONAL: ${s.message}`);
});
```

## Pattern: Edit Then Revalidate

After every meaningful change to a node or workflow, revalidate. Do not stack edits.

### Good Example

```javascript
// Make one change
config.channel = "#alerts";
let result = validate_node({ nodeType, config, profile: "runtime" });
if (!result.valid) {
  // fix the error this change introduced before moving on
}

// Make next change only after the previous validates
config.text = "={{$json.body.message}}";
result = validate_node({ nodeType, config, profile: "runtime" });
```

### Bad Example: Stacking Edits

```javascript
// Bad: make seven changes, then validate, then guess which one broke it
config.channel = "#alerts";
config.text = "={{$json.body.message}}";
config.threadTs = "={{$json.body.thread_ts}}";
config.attachments = [...];
config.blocks = [...];
config.iconEmoji = ":robot:";
config.linkNames = true;

const result = validate_node({ nodeType, config, profile: "runtime" });
// 3 errors, which change caused which?
```

## Pattern: Use get_node Before You Configure

Avoid guessing required fields and allowed enum values.

```javascript
// Before configuring, learn what is required
const info = get_node({ nodeType: "nodes-base.slack" });

info.properties.forEach(prop => {
  if (prop.required) {
    console.log(`Required: ${prop.name} (${prop.type})`);
  }
});

// Now build config with knowledge in hand
const config = {
  resource: "message",
  operation: "post",
  channel: "#general",
  text: "Hello"
};
```

For node configuration discovery patterns in depth, see [../node-configuration/](../node-configuration/).

## Pattern: Validation Profile by Lifecycle Stage

Match the profile to your stage. See [configuration.md](./configuration.md) for the full profile reference.

```javascript
// Development: keep noise down
validate_node({ nodeType, config, profile: "ai-friendly" });

// Pre-production: balanced check
validate_node({ nodeType, config, profile: "runtime" });

// Production deployment: see everything
validate_node({ nodeType, config, profile: "strict" });
```

## Pattern: Trust Auto-Sanitization for Operator Structure

Auto-sanitization runs on every workflow save (`n8n_create_workflow`, `n8n_update_partial_workflow`, etc.). It fixes IF/Switch operator structure issues without your intervention.

### What Auto-Sanitization Fixes

**Binary operators** (compare two values): `equals`, `notEquals`, `contains`, `notContains`, `greaterThan`, `lessThan`, `startsWith`, `endsWith`.

Auto-sanitization removes `singleValue` if present:

```javascript
// Before (you write this):
{
  "type": "boolean",
  "operation": "equals",
  "singleValue": true   // wrong for binary operator
}

// After (auto-sanitization on save):
{
  "type": "boolean",
  "operation": "equals"
  // singleValue removed
}
```

**Unary operators** (check single value): `isEmpty`, `isNotEmpty`, `true`, `false`.

Auto-sanitization adds `singleValue: true` if missing:

```javascript
// Before:
{
  "type": "boolean",
  "operation": "isEmpty"
  // missing singleValue
}

// After:
{
  "type": "boolean",
  "operation": "isEmpty",
  "singleValue": true   // added
}
```

**IF/Switch metadata**: Auto-sanitization adds the full `conditions.options` metadata for IF v2.2+ and Switch v3.2+.

### What Auto-Sanitization Does NOT Fix

| Problem | Tool to Use Instead |
|---|---|
| Broken connections (references to non-existent nodes) | `n8n_update_partial_workflow` with `cleanStaleConnections` |
| Branch count mismatches (3 Switch rules, 2 outputs) | Manually add missing connections or remove extra rules |
| Paradoxical corrupt states (API returns corrupt data, rejects updates) | May require manual database intervention |

### Good Example

```javascript
// Just configure naturally and let auto-sanitization handle it
const ifNode = {
  type: "n8n-nodes-base.if",
  parameters: {
    conditions: {
      boolean: [{
        value1: "={{$json.active}}",
        operation: "isEmpty"
        // do NOT set singleValue manually
      }]
    }
  }
};

// Auto-sanitization will add singleValue: true on save
```

### Bad Example

```javascript
// Bad: manually try to fix operator structure (often gets it wrong)
const ifNode = {
  parameters: {
    conditions: {
      boolean: [{
        value1: "={{$json.active}}",
        operation: "isEmpty",
        singleValue: false   // wrong, but you spent time computing it
      }]
    }
  }
};
```

## Pattern: Recovery Strategy 1: Start Fresh

When a node configuration is severely broken, do not try to patch your way out.

```javascript
// 1. Note required fields from get_node
const info = get_node({ nodeType: "nodes-base.slack" });

// 2. Build minimal valid configuration
let config = {
  resource: "message",
  operation: "post",
  channel: "#general",
  text: "Hello"
};
validate_node({ nodeType: "nodes-base.slack", config, profile: "runtime" });
// Valid

// 3. Add features incrementally, validating after each
config.attachments = [...];
validate_node({ nodeType: "nodes-base.slack", config, profile: "runtime" });
```

## Pattern: Recovery Strategy 2: Binary Search

When a workflow validates but executes incorrectly.

```
1. Remove half the nodes
2. Validate and test
3. If works: problem is in removed nodes
4. If fails: problem is in remaining nodes
5. Repeat until problem isolated
```

## Pattern: Recovery Strategy 3: Clean Stale Connections

When you get `invalid_reference` errors at the workflow level (connections point to deleted or renamed nodes).

```javascript
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "cleanStaleConnections"
  }]
});
```

## Pattern: Recovery Strategy 4: Auto-Fix Preview, Then Apply

When you have many fixable issues across a workflow.

```javascript
// 1. Preview fixes (does not mutate)
const preview = n8n_autofix_workflow({
  id: "workflow-id",
  applyFixes: false,
  confidenceThreshold: "medium"
});

// 2. Review the preview output

// 3. Apply only high-confidence fixes
n8n_autofix_workflow({
  id: "workflow-id",
  applyFixes: true,
  confidenceThreshold: "high"
});

// 4. For complex migrations, check postUpdateGuidance in the response
//    for step-by-step manual follow-up instructions
```

### Targeting Specific Fix Types

```javascript
n8n_autofix_workflow({
  id: "workflow-id",
  fixTypes: ["expression-format", "typeversion-upgrade"],
  applyFixes: true
});
```

## Pattern: Document Accepted Warnings

When you choose to accept a warning as a false positive, document why. See [gotchas.md](./gotchas.md) for the false-positive catalog.

```javascript
// workflows/customer-notifications.json
{
  "nodes": [{
    "name": "Send Slack Notification",
    "type": "n8n-nodes-base.slack",
    "parameters": {
      "channel": "#notifications"
      // ACCEPTED WARNING: No error handling
      // Reason: Non-critical notification, failures are acceptable
      // Reviewed: 2025-10-20
      // Reviewer: Engineering Team
    }
  }]
}
```

## Best Practices Checklist

### Do

- Validate after every significant change.
- Read error messages completely (they contain the fix).
- Fix errors iteratively, one category at a time.
- Use `runtime` profile for pre-deployment.
- Check `valid` field before treating a config as good.
- Trust auto-sanitization for operator issues.
- Use `get_node` when unclear about requirements.
- Document false positives you accept.

### Do Not

- Skip validation before activation.
- Try to fix all errors at once.
- Ignore error messages.
- Use `strict` profile during development (too noisy).
- Assume validation passed without checking `valid`.
- Manually fix auto-sanitization issues.
- Deploy with unresolved errors.
- Ignore all warnings (some are important, especially security).

## See Also

- [api.md](./api.md): Tool signatures referenced throughout these patterns.
- [gotchas.md](./gotchas.md): Specific error types each pattern handles.
- [configuration.md](./configuration.md): Profile selection for each lifecycle stage.
- [../mcp-tools/](../mcp-tools/): Where these tools live in the broader MCP catalog.
- [../workflow-patterns/](../workflow-patterns/): Workflow structure patterns that `validate_workflow` enforces.
