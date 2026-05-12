# MCP Tools

The n8n-mcp MCP server exposes a focused toolbox for building, validating, and operating n8n workflows from an agentic CLI. Tools are grouped into six categories: node discovery (search, schema, docs), configuration validation (per-node and per-workflow), workflow management (create, partial update, deploy, version, test), template library (2,700+ curated workflows), data tables and credentials (CRUD with schema discovery), and security audit (built-in plus custom deep scan). The two non-obvious things to internalize before calling anything: nodeType prefix varies by tool family (`nodes-base.*` for search and validate tools, `n8n-nodes-base.*` for workflow tools), and workflows are built iteratively (telemetry shows roughly 56 seconds between edits, not one-shot construction).

## When to Use

| Situation | What to Read |
|---|---|
| You need to find the right node for a task | [api.md](./api.md) (Search and Discovery), [patterns.md](./patterns.md) (Search Patterns) |
| You got a "Node not found" or wrong-prefix error | [gotchas.md](./gotchas.md) (nodeType Format) |
| You are planning a validate, fix, revalidate cycle | [patterns.md](./patterns.md) (Validation Loop) |
| You are building or editing a workflow | [api.md](./api.md) (Workflow Management), [patterns.md](./patterns.md) (Iterative Editing) |
| You want to deploy from a template or NL description | [api.md](./api.md) (Templates, Generation) |
| You want to know which tool flag to pass | [api.md](./api.md) |
| You hit a validation false positive or auto-sanitization surprise | [gotchas.md](./gotchas.md) |
| You are wiring n8n-mcp into Claude Code or another harness | [configuration.md](./configuration.md) |

## Quick Start

A typical n8n-mcp tool call sequence, from "I need a Slack notifier" to a live workflow:

```javascript
// 1. Find the node
search_nodes({ query: "slack" })
// → { results: [{ nodeType: "nodes-base.slack", workflowNodeType: "n8n-nodes-base.slack", ... }] }

// 2. Understand the node
get_node({ nodeType: "nodes-base.slack", includeExamples: true })
// → operations, properties, example configs

// 3. Validate a draft config
validate_node({
  nodeType: "nodes-base.slack",
  config: { resource: "message", operation: "post", channel: "#general", text: "Hello" },
  profile: "runtime"
})
// → { valid: true } or { valid: false, errors: [...] }

// 4. Build the workflow (use FULL prefix here!)
n8n_create_workflow({
  name: "Manual to Slack",
  nodes: [/* ... */],
  connections: { /* ... */ }
})

// 5. Validate the whole workflow
n8n_validate_workflow({ id: "wf-abc" })

// 6. Iterate (this is the common case, 56s avg between edits)
n8n_update_partial_workflow({
  id: "wf-abc",
  intent: "Add error handling for Slack rate limits",
  operations: [/* ... */]
})

// 7. Activate
n8n_update_partial_workflow({
  id: "wf-abc",
  intent: "Activate workflow",
  operations: [{ type: "activateWorkflow" }]
})
```

The golden rules:

1. Search before guessing. `search_nodes` is under 20 ms and prevents typos.
2. Use `get_node` at `detail: "standard"` (the default). Reserve `full` for debugging.
3. Use the `runtime` validation profile by default.
4. Build workflows iteratively with `n8n_update_partial_workflow`. Do not try one-shot construction.
5. Always pass `intent` on partial updates. It improves response quality.
6. Use the short prefix (`nodes-base.*`) for search and validate tools. Use the full prefix (`n8n-nodes-base.*`) for workflow tools.

## Reading Order

| Task | Files to Read |
|---|---|
| First-time tool selection | README.md, [api.md](./api.md) |
| Find and configure a single node | [patterns.md](./patterns.md) (Search Patterns), [api.md](./api.md) (Search and Discovery), [gotchas.md](./gotchas.md) (nodeType Format) |
| Build a validate, fix, revalidate loop | [patterns.md](./patterns.md) (Validation Loop), [api.md](./api.md) (Validation) |
| Build or iterate on a workflow | [api.md](./api.md) (Workflow Management), [patterns.md](./patterns.md) (Iterative Editing), [gotchas.md](./gotchas.md) (Parameter Names) |
| Deploy a template or generate from NL | [api.md](./api.md) (Templates, Generation), [patterns.md](./patterns.md) (Quick Start Strategies) |
| Manage credentials, data tables, executions | [api.md](./api.md) (Credentials, Data Tables, Executions) |
| Audit instance security | [api.md](./api.md) (Audit), [patterns.md](./patterns.md) (Remediation Loop) |
| Set up n8n-mcp in your harness | [configuration.md](./configuration.md) |
| Diagnose a tool error | [gotchas.md](./gotchas.md), [api.md](./api.md) |
| Full onboarding | README.md, [api.md](./api.md), [patterns.md](./patterns.md), [gotchas.md](./gotchas.md), [configuration.md](./configuration.md) |

## In This Reference

- **[api.md](./api.md)**: Tool-by-tool reference grouped by category (Search and Discovery, Validation, Workflow Management, Templates, Workflow Generation, Data Tables, Credentials, Audit, Executions, Self-Help). Each entry gives the call shape, parameters, return structure, and a worked example.
- **[patterns.md](./patterns.md)**: Named, copy-paste-ready patterns. Search strategies (keyword vs node-types vs task), mode selection, narrowing and broadening, validation loop, edit-then-revalidate, smart parameters, AI connection wiring, recovery, and the full lifecycle.
- **[gotchas.md](./gotchas.md)**: Four-part bad/good entries for the recurring failure modes. Wrong nodeType prefix, wrong parameter names (`parameters` vs `updates`), flat credentials object, default profile, `detail: "full"` overuse, ignored intent, missing smart params, auto-sanitization surprises.
- **[configuration.md](./configuration.md)**: How to register the n8n-mcp MCP server with Claude Code or another harness. Required environment variables (`N8N_API_URL`, `N8N_API_KEY`), tool availability by env config, and how to verify the install with `n8n_health_check`.

## Tool Categories at a Glance

| Category | Representative Tools | Latency |
|---|---|---|
| Search and Discovery | `search_nodes`, `get_node`, `get_suggested_nodes` | under 20 ms |
| Validation | `validate_node`, `validate_workflow`, `n8n_validate_workflow`, `n8n_autofix_workflow` | 50 to 500 ms |
| Workflow Management | `n8n_create_workflow`, `n8n_update_partial_workflow`, `n8n_get_workflow`, `n8n_list_workflows`, `n8n_delete_workflow`, `n8n_workflow_versions` | 50 to 500 ms |
| Templates | `search_templates`, `get_template`, `n8n_deploy_template` | 100 to 500 ms |
| Workflow Generation | `n8n_generate_workflow` (hosted-only) | 2 to 15 s |
| Data Tables | `n8n_manage_datatable` | 50 to 500 ms |
| Credentials | `n8n_manage_credentials` | 50 to 500 ms |
| Audit | `n8n_audit_instance` | 500 to 5000 ms |
| Executions | `n8n_executions`, `n8n_test_workflow` | 100 ms to many seconds |
| Self-Help | `tools_documentation`, `ai_agents_guide`, `n8n_health_check`, `get_sdk_reference` | under 50 ms |

The most-called tool in real telemetry is `n8n_update_partial_workflow` (over 38,000 uses), reflecting the iterative-editing reality.

## See Also

- [../validation/](../validation/): Deep dive on interpreting validation results, error types, profiles, and recovery. This MCP-tools reference covers the call surface; the validation reference covers the meaning of the responses.
- [../node-configuration/](../node-configuration/): Required fields, allowed values, and discriminators (`resource`, `operation`, `mode`) that `get_node` and `validate_node` operate on.
- [../workflow-patterns/](../workflow-patterns/): Architectural patterns for assembling nodes into working workflows once you have selected them with the MCP tools here.
- [../expressions/](../expressions/): Expression syntax for fields and the n8n SDK that `n8n_create_workflow` and `n8n_update_partial_workflow` write into.
