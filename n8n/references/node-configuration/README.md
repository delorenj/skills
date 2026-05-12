# Node Configuration

Operation-aware node configuration guidance for n8n. This reference covers property dependencies, required field discovery, get_node detail-level selection, displayOptions semantics, and surgical edits via patchNodeField. Use it whenever you set up node parameters, debug "missing required field" validation errors, or decide between a full node replacement and a targeted field patch.

---

## Configuration Philosophy

**Progressive disclosure**: Start minimal, add complexity as needed.

Configuration best practices:
- `get_node` with `detail: "standard"` is the most-used discovery pattern.
- 56 seconds is the average between configuration edits, configuration is iterative.
- Standard detail covers 95% of use cases with a 1-2K token response.

**Key insight**: Most configurations need only standard detail, not full schema.

**Four guiding principles**:
- **Operation-aware**: Different operations mean different required fields.
- **Progressive disclosure**: Start minimal, add fields only when validation demands.
- **Dependency-aware**: Understand the field visibility rules controlled by `displayOptions`.
- **Validation-driven**: Let validation errors guide each iteration.

---

## When To Use This Reference

| Situation | Read |
|---|---|
| Starting a new node configuration | [patterns.md](./patterns.md), then [api.md](./api.md) |
| Choosing between standard, full, and search_properties detail | [api.md](./api.md) |
| Validation says a field is required but you cannot see it | [gotchas.md](./gotchas.md) and [api.md](./api.md) |
| Field disappears after changing operation | [gotchas.md](./gotchas.md) |
| Editing a single string inside a Code or HTML field | [api.md](./api.md) (patchNodeField) |
| Resolving dependencies, version pinning, or credentials | [configuration.md](./configuration.md) |
| Picking a pattern for HTTP, Slack, Postgres, IF, Switch, OpenAI, Schedule | [patterns.md](./patterns.md) |
| Debugging "field doesn't save" after deploy | [gotchas.md](./gotchas.md) |

---

## Quick Start

Minimal HTTP Request POST with JSON body (the canonical worked example):

```javascript
// Step 1: Discover the node at standard detail (default level)
const info = get_node({
  nodeType: "nodes-base.httpRequest"
});

// Step 2: Configure minimally
const config = {
  "method": "POST",
  "url": "https://api.example.com/create",
  "authentication": "none",
  "sendBody": true,                     // Required for POST body
  "body": {                             // Required when sendBody=true
    "contentType": "json",
    "content": {
      "name": "={{$json.name}}",
      "email": "={{$json.email}}"
    }
  }
};

// Step 3: Validate before deploy
validate_node({
  nodeType: "nodes-base.httpRequest",
  config,
  profile: "runtime"
});
```

The same pattern applies to every node: discover with `get_node`, configure minimally, validate, iterate.

---

## Standard Configuration Workflow

```
1. Identify node type and operation
   ↓
2. Use get_node (standard detail is default)
   ↓
3. Configure required fields
   ↓
4. Validate configuration
   ↓
5. If field unclear, get_node({mode: "search_properties"})
   ↓
6. Add optional fields as needed
   ↓
7. Validate again
   ↓
8. Deploy
```

Average iteration count is 2-3 validate-fix cycles before a configuration is accepted.

---

## get_node Detail-Level Decision Tree

```
┌─────────────────────────────────┐
│ Starting new node config?       │
├─────────────────────────────────┤
│ YES, use get_node (standard)    │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ Standard has what you need?     │
├─────────────────────────────────┤
│ YES, configure with it          │
│ NO,  continue                   │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ Looking for a specific field?   │
├─────────────────────────────────┤
│ YES, search_properties mode     │
│ NO,  continue                   │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ Still need more details?        │
├─────────────────────────────────┤
│ YES, get_node({detail: "full"}) │
└─────────────────────────────────┘
```

---

## Reading Order

| Task | Files to Read |
|---|---|
| First time configuring any node | [README.md](./README.md), then [api.md](./api.md), then [patterns.md](./patterns.md) |
| Building a specific node type fast | [patterns.md](./patterns.md) |
| Diagnosing a confusing validation error | [gotchas.md](./gotchas.md), then [api.md](./api.md) |
| Designing a configuration with property dependencies | [api.md](./api.md), then [patterns.md](./patterns.md) |
| Updating an existing node surgically | [api.md](./api.md) (patchNodeField section) |
| Pinning versions, planning credentials, or auditing dependencies | [configuration.md](./configuration.md) |
| Onboarding to the topic end-to-end | [README.md](./README.md), [api.md](./api.md), [patterns.md](./patterns.md), [gotchas.md](./gotchas.md), [configuration.md](./configuration.md) |

---

## In This Reference

- **[api.md](./api.md)**: `get_node_essentials`, `get_node_info`, `patchNodeField`, `update_full_workflow`, property dependency rules, displayOptions semantics.
- **[patterns.md](./patterns.md)**: Named, copy-paste patterns for HTTP, Webhook, Slack, Gmail, Postgres, Set, Code, IF, Switch, OpenAI, Schedule Trigger, and the four cross-cutting node-configuration patterns.
- **[gotchas.md](./gotchas.md)**: displayOptions traps, missing required fields per operation, dependency cycles, and other common configuration mistakes in four-part structure.
- **[configuration.md](./configuration.md)**: Node dependencies, version pinning, credentials structure, node-level environment requirements.

---

## See Also

- [../mcp-tools/](../mcp-tools/): Full surface area of the n8n MCP discovery tools.
- [../validation/](../validation/): Interpreting validation errors that drive the configuration loop.
- [../expressions/](../expressions/): Expression syntax for fields that accept `={{ ... }}`.
- [../workflow-patterns/](../workflow-patterns/): Higher-level workflow patterns that consume the node configurations described here.
- [../code-javascript/](../code-javascript/) and [../code-python/](../code-python/): Code-node specifics that complement [patterns.md](./patterns.md).
