# Validation API

Tool signatures, parameter shapes, and return types for the n8n validation surface.

## Tool Overview

| Tool | Scope | Mutates? |
|---|---|---|
| `validate_node` | Single node configuration | No |
| `validate_workflow` | Entire workflow (nodes + connections + expressions) | No |
| `n8n_autofix_workflow` | Workflow-level auto-repair (preview or apply) | Optional |
| `n8n_update_partial_workflow` (with `cleanStaleConnections`) | Targeted cleanup of broken references | Yes |
| `n8n_audit_instance` | Instance-wide security and best-practice scan | No |

For where these tools sit in the larger MCP surface, see [../mcp-tools/](../mcp-tools/).

## validate_node

Validate a single node configuration against its type definition.

### Signature

```javascript
validate_node({
  nodeType: string,        // e.g. "nodes-base.slack"
  config: object,          // the parameters object you would put in the node
  profile: string          // "minimal" | "runtime" | "ai-friendly" | "strict"
})
```

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `nodeType` | string | Yes | Fully qualified node type ID (e.g. `nodes-base.slack`, `nodes-base.httpRequest`). |
| `config` | object | Yes | The node's `parameters` object, including `resource`, `operation`, `mode`, and all configured fields. |
| `profile` | string | No (default `runtime`) | Validation strictness. See [configuration.md](./configuration.md). |

### Example

```javascript
const result = validate_node({
  nodeType: "nodes-base.slack",
  config: {
    resource: "message",
    operation: "post",
    channel: "#general",
    text: "Hello"
  },
  profile: "runtime"
});
```

## validate_workflow

Validate an entire workflow, including node configurations, connections, expressions, and flow structure.

### Signature

```javascript
validate_workflow({
  workflow: {
    nodes: Array<NodeObject>,
    connections: object
  },
  options: {
    validateNodes: boolean,        // default true
    validateConnections: boolean,  // default true
    validateExpressions: boolean,  // default true
    profile: string                // "minimal" | "runtime" | "ai-friendly" | "strict"
  }
})
```

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `workflow.nodes` | array | Yes | Array of node objects (full structure including `name`, `type`, `typeVersion`, `parameters`). |
| `workflow.connections` | object | Yes | The connections map (source node name to output array to target list). |
| `options.validateNodes` | boolean | No | Run per-node validation. |
| `options.validateConnections` | boolean | No | Check that all connection endpoints exist. |
| `options.validateExpressions` | boolean | No | Parse and resolve all `={{ }}` expressions across the workflow. |
| `options.profile` | string | No | Same profile system as `validate_node`. |

### What It Checks

1. **Node configurations**: Each node valid against its type (delegates to `validate_node` per node).
2. **Connections**: No broken references, no orphaned target nodes.
3. **Expressions**: Syntax valid, all `$node['Name']` references resolve.
4. **Flow**: No circular dependencies, no multiple unintended start nodes, no disconnected nodes.

### Example

```javascript
const result = validate_workflow({
  workflow: {
    nodes: [...],
    connections: {...}
  },
  options: {
    validateNodes: true,
    validateConnections: true,
    validateExpressions: true,
    profile: "runtime"
  }
});
```

## Validation Result Structure

Both `validate_node` and `validate_workflow` return the same shape:

```javascript
{
  "valid": false,
  "errors": [
    {
      "type": "missing_required",       // see gotchas.md for full list
      "property": "channel",            // dotted path within the node
      "message": "Channel name is required",
      "fix": "Provide a channel name (lowercase, no spaces)",
      "node": "Slack",                  // workflow-level results only
      "path": "parameters.channel"      // workflow-level results only
    }
  ],
  "warnings": [
    {
      "type": "best_practice",
      "property": "errorHandling",
      "message": "Slack API can have rate limits",
      "suggestion": "Add onError: 'continueRegularOutput'"
    }
  ],
  "suggestions": [
    {
      "type": "optimization",
      "message": "Consider using batch operations for multiple messages"
    }
  ],
  "summary": {
    "hasErrors": true,
    "errorCount": 1,
    "warningCount": 1,
    "suggestionCount": 1
  }
}
```

### Field Reference

| Field | Type | Meaning |
|---|---|---|
| `valid` | boolean | `true` only if `errors` is empty. Warnings and suggestions do not affect this. |
| `errors[]` | array | Must-fix items. Workflow will not run while any are present. |
| `errors[].type` | string | Error category. See [gotchas.md](./gotchas.md). |
| `errors[].property` | string | The offending parameter (dotted path). |
| `errors[].message` | string | Human-readable description. |
| `errors[].fix` | string | Suggested remediation. Usually has the literal fix. |
| `warnings[]` | array | Should-fix items. Do not block execution. |
| `warnings[].type` | string | One of `best_practice`, `deprecated`, `performance`, `security`. |
| `warnings[].suggestion` | string | Recommended change. |
| `suggestions[]` | array | Optional improvements (optimization, alternative). |
| `summary` | object | Counts for quick branching. |

### Reading the Result

```javascript
// 1. Check valid
if (result.valid) {
  // ready to deploy
} else {
  // has errors, must fix
}

// 2. Fix errors first
result.errors.forEach(error => {
  console.log(`Error in ${error.property}: ${error.message}`);
  console.log(`Fix: ${error.fix}`);
});

// 3. Review warnings (some may be false positives, see gotchas.md)
result.warnings.forEach(warning => {
  console.log(`Warning: ${warning.message}`);
  console.log(`Suggestion: ${warning.suggestion}`);
});

// 4. Consider suggestions
result.suggestions.forEach(s => console.log(`Optional: ${s.message}`));
```

## n8n_autofix_workflow

Workflow-level auto-repair. Can preview or apply fixes.

### Signature

```javascript
n8n_autofix_workflow({
  id: string,                        // workflow ID
  applyFixes: boolean,               // default false (preview-only)
  confidenceThreshold: string,       // "high" | "medium" | "low"
  fixTypes: Array<string>            // optional, restrict to specific fix kinds
})
```

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | The workflow ID. |
| `applyFixes` | boolean | No (default `false`) | If `false`, returns a preview without mutating the workflow. If `true`, applies the fixes. |
| `confidenceThreshold` | string | No (default `medium`) | Only fixes at or above this confidence are applied. `high` = 90 percent+, `medium` = 70 to 89 percent, `low` = under 70 percent. |
| `fixTypes` | string[] | No | Whitelist of fix types to consider. |

### Supported Fix Types

| `fixTypes` value | What it does |
|---|---|
| `expression-format` | Adds missing `=` prefix to expressions (`{{ $json.x }}` becomes `={{ $json.x }}`). |
| `typeversion-correction` | Downgrades nodes with unsupported `typeVersion`. |
| `error-output-config` | Removes conflicting `onError` settings. |
| `node-type-correction` | Fixes unknown node types via 90 percent+ similarity matching. |
| `webhook-missing-path` | Generates UUIDs for webhook nodes missing a `path`. |
| `typeversion-upgrade` | Smart upgrades to latest node versions with auto-migration. |
| `version-migration` | Guidance for complex breaking changes requiring manual steps. |

### Confidence Semantics

| Level | Range | Recommended Action |
|---|---|---|
| `high` | 90 percent and up | Safe to auto-apply. |
| `medium` | 70 to 89 percent | Review before applying. |
| `low` | under 70 percent | Manual review required. |

### Examples

```javascript
// Preview all fixes (does not mutate)
n8n_autofix_workflow({ id: "workflow-id" });

// Apply only high-confidence fixes
n8n_autofix_workflow({
  id: "workflow-id",
  applyFixes: true,
  confidenceThreshold: "high"
});

// Target specific fix types
n8n_autofix_workflow({
  id: "workflow-id",
  fixTypes: ["expression-format", "typeversion-upgrade"],
  applyFixes: true
});
```

### Post-Update Guidance

For version upgrades, check the `postUpdateGuidance` field in the response for step-by-step migration instructions when the upgrade requires manual follow-up.

## n8n_update_partial_workflow (cleanStaleConnections)

Used for targeted cleanup that auto-sanitization cannot perform. Most relevant validation use is `cleanStaleConnections`.

### Signature (validation-relevant subset)

```javascript
n8n_update_partial_workflow({
  id: string,
  operations: Array<Operation>
})
```

### cleanStaleConnections Operation

```javascript
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "cleanStaleConnections"
  }]
});
```

Removes connection entries that reference nodes no longer present in the workflow. Resolves `invalid_reference` errors at the workflow level.

### patchNodeField Operation

The `patchNodeField` operation is strict by design and emits validation errors when something is wrong. See the `patchNodeField` entries in [gotchas.md](./gotchas.md) for error symptoms and fixes.

```javascript
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "patchNodeField",
    node: "Code",
    field: "parameters.jsCode",
    find: "old string",
    replace: "new string",
    replaceAll: false,    // default
    regex: false          // default
  }]
});
```

## n8n_audit_instance

Proactive, instance-wide validation for things `validate_node` and `validate_workflow` cannot see (hardcoded secrets, unauthenticated webhooks, missing error handling across workflows, data retention).

```javascript
n8n_audit_instance();
```

Use this in addition to per-node and per-workflow validation, not as a replacement.

## Auto-Sanitization (Implicit)

Auto-sanitization runs automatically on `n8n_create_workflow`, `n8n_update_partial_workflow`, and any workflow save. There is no separate tool call. It fixes IF/Switch operator structure (`singleValue` add/remove) and `conditions.options` metadata for IF v2.2+ and Switch v3.2+. See [patterns.md](./patterns.md) for what it does and does not fix.

## See Also

- [patterns.md](./patterns.md): How to compose these tools into a validation loop.
- [gotchas.md](./gotchas.md): Specific errors each tool can return and how to fix them.
- [configuration.md](./configuration.md): Profile selection and trade-offs.
- [../mcp-tools/](../mcp-tools/): Broader MCP tool catalog including discovery and creation tools.
