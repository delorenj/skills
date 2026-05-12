---
name: n8n
description: Comprehensive n8n workflow automation skill covering workflow architecture patterns (webhook, HTTP API, database, AI agent, scheduled tasks, batch processing), node configuration (operation-aware setup, displayOptions, property dependencies, patchNodeField), expressions ({{}} syntax, $json/$node/$input/$helpers/DateTime), Code nodes (JavaScript and Python with sandbox limits, $helpers.httpRequest, SplitInBatches, pairedItem), n8n-mcp MCP tool usage (search_nodes, get_node_essentials, validate_node_operation, validate_workflow, n8n_create_workflow, n8n_update_partial_workflow), and validation (validate_node, validate_workflow, profiles strict/runtime/ai-friendly/minimal, error catalog, false positives). Use for any n8n development task: building workflows, configuring nodes, writing expressions or Code nodes, validating configurations, debugging failures, deploying to n8n instances, or managing n8n via MCP. Biases towards retrieval via n8n-mcp tools over pre-trained knowledge because n8n's node catalog and parameter schemas change frequently and pre-trained knowledge of nodeType strings, required fields, and displayOptions is unreliable.
references:
  - workflow-patterns
  - node-configuration
  - expressions
  - mcp-tools
  - validation
---

# n8n Platform Skill

Consolidated reference-hub for building and operating n8n workflows. Use the decision trees below to identify the topic, then load the detailed references.

Your knowledge of n8n node types, parameter schemas, and validation rules may be outdated. **Prefer retrieval over pre-training**: every node configuration must be confirmed against `n8n-mcp` tools before use. Hand-written nodeType strings, parameter shapes, or displayOptions are unreliable. The references in this skill are starting points, not source of truth.

## Retrieval Sources

Fetch current information before citing node types, parameter schemas, or operation requirements.

| Source | How to retrieve | Use for |
|--------|-----------------|---------|
| n8n-mcp MCP server | `search_nodes`, `get_node_essentials`, `get_node_info`, `list_nodes`, `list_ai_tools` | Node types, parameter shapes, operation requirements |
| n8n-mcp validation | `validate_node_operation`, `validate_node_minimal`, `validate_workflow`, `validate_workflow_connections`, `validate_workflow_expressions` | Pre-deploy and pre-save validation |
| n8n REST API via n8n-mcp | `n8n_create_workflow`, `n8n_update_partial_workflow`, `n8n_get_workflow`, `n8n_list_executions`, `n8n_trigger_webhook_workflow` | Workflow management on running n8n instances |
| n8n docs | `https://docs.n8n.io/` | Concepts, latest features, version-specific changes |
| n8n changelog | `https://docs.n8n.io/release-notes/` | Recent feature additions, deprecations |

When a reference file and n8n-mcp disagree, **trust n8n-mcp**. The references here capture patterns and gotchas; the schemas live in n8n-mcp.

## Quick Decision Trees

### "I need to build a workflow"

```
Need to build a workflow?
├─ Receive external event (HTTP) → references/workflow-patterns/webhook-processing.md
├─ Call external API on a schedule or trigger → references/workflow-patterns/http-api-integration.md
├─ Query or write to a database → references/workflow-patterns/database-operations.md
├─ Build an LLM-driven agent (chat, tools, memory) → references/workflow-patterns/ai-agent-workflow.md
├─ Cron/scheduled job → references/workflow-patterns/scheduled-tasks.md
└─ Choosing between patterns or composing them → references/workflow-patterns/
```

### "I need to write code inside a node"

```
Need to write code?
├─ Expression in a node field (single-line `{{ }}`) → references/expressions/
│  ├─ Access data from previous node → references/expressions/api.md ($json, $node)
│  ├─ Transform with helpers (dates, strings) → references/expressions/patterns.md
│  └─ Debug expression errors → references/expressions/gotchas.md
├─ Code node block (multi-line logic) → references/code-javascript/ (default)
│  └─ Python specifically requested → references/code-python/
│     (Note: JavaScript covers 95% of use cases; prefer it unless Python stdlib is required)
└─ Custom node TypeScript package → out of scope; see n8n docs for community node authoring
```

### "I need to configure a node"

```
Need to configure a node?
├─ First time setting up the node type → references/node-configuration/README.md + node-configuration/patterns.md (per-node patterns)
├─ Adding required parameters per operation → references/node-configuration/api.md (operation-aware setup, displayOptions)
├─ Surgical edit (one field) on an existing node → references/node-configuration/patterns.md (patchNodeField)
├─ Property dependencies (field A controls field B visibility) → references/node-configuration/configuration.md (dependency chains)
└─ Debugging configuration errors → references/node-configuration/gotchas.md
```

### "I need to validate something"

```
Need to validate?
├─ Single node config before saving → validate_node_operation (see references/validation/api.md, references/mcp-tools/api.md)
├─ Entire workflow before deploying → validate_workflow + validate_workflow_connections + validate_workflow_expressions
├─ Interpret a validation error → references/validation/gotchas.md
├─ Profile selection (strict / runtime / ai-friendly / minimal) → references/validation/configuration.md
└─ Recover from validation failure → references/validation/patterns.md
```

### "I need to use n8n-mcp tools"

```
Need to call an n8n-mcp tool?
├─ Find the right node by capability → references/mcp-tools/patterns.md (search strategies)
├─ Get tool reference for a specific function → references/mcp-tools/api.md
├─ Build, update, or trigger a workflow on a running n8n instance → references/mcp-tools/api.md (Workflow Management)
├─ Manage data tables, credentials, executions → references/mcp-tools/api.md (by category)
├─ Register the MCP server in your harness → references/mcp-tools/configuration.md
└─ Troubleshoot tool errors → references/mcp-tools/gotchas.md
```

## Topic Index

| Topic | Reference |
|-------|-----------|
| Workflow architecture patterns (webhook, HTTP API, database, AI agent, scheduled) | `references/workflow-patterns/` |
| Node configuration (operation-aware setup, dependencies, surgical edits) | `references/node-configuration/` |
| Expression syntax (`{{}}`, variables, helpers, DateTime) | `references/expressions/` |
| Code node: JavaScript | `references/code-javascript/` |
| Code node: Python (beta) | `references/code-python/` |
| n8n-mcp MCP tool usage and patterns | `references/mcp-tools/` |
| Workflow and node validation (profiles, error catalog, false positives) | `references/validation/` |

## Cross-Cutting Rules

These apply across every n8n task regardless of topic:

- **n8n-mcp is canon for schemas.** Never hand-write nodeType strings, required fields, or displayOptions. Always derive from `search_nodes`, `get_node_essentials`, or `get_node_info`.
- **Validate before save.** `validate_node_operation` after every configuration change. `validate_workflow` before deploy.
- **Operations dictate required fields.** A node's required parameter set depends on which operation is selected. Always pass `operation` to `get_node_essentials` to see only the relevant fields.
- **Use `patchNodeField` for surgical edits.** Full-node updates risk overwriting unrelated config. Use diff-based updates for single-field changes.
- **Expressions in `{{ }}`, code in Code node.** Single expressions belong inline in node parameters; multi-line logic belongs in Code nodes.
- **JavaScript for 95% of Code node use cases.** Python is beta with limited stdlib; choose Python only when its stdlib is required (regex, hashlib, statistics).
- **Credentials never inline.** Reference credentials by ID (`credentials: { httpHeaderAuth: { id: "..." } }`); never inline tokens or keys in node parameters.
- **Workflows save inactive by default.** Verify with manual execution or `n8n_trigger_webhook_workflow` before activating.
- **`compatibility_date`, `nodejs_compat`, and `runners` settings change Code node behavior.** Check the harness's n8n version when sandbox errors appear.

## Discovery Hints

If the task signal is ambiguous, match against these code-level signals:

- `{{ $json.field }}` or `={{ ... }}` in node parameter → expressions
- `return items.map(item => ...)` or `$input.all()` in user-supplied code → code-javascript
- `_input.all()` or `_json` with underscore prefix → code-python
- `wrangler`-style CLI mention → NOT n8n (this is Cloudflare; load the cloudflare skill)
- `search_nodes`, `get_node_*`, `validate_*`, `n8n_create_workflow` → mcp-tools (and the relevant downstream topic)
- `nodes-base.httpRequest`, `nodes-langchain.agent`, or any `nodes-base.*` / `nodes-langchain.*` reference → node-configuration
- `displayOptions`, `show:`, `hide:` in node spec → node-configuration

## Out of Scope

This skill covers n8n workflow authoring, node configuration, and operation via n8n-mcp. It does NOT cover:

- **Self-hosting n8n** (Docker setup, server configuration, database backends). See `https://docs.n8n.io/hosting/`.
- **Custom node development** (TypeScript node packages, `n8n-nodes-*` community packages). Separate skill or n8n docs at `https://docs.n8n.io/integrations/creating-nodes/`.
- **n8n core source code, internal APIs, or contributions** to the n8n repo.
- **Workflow file format reverse-engineering.** Use n8n-mcp tools and the n8n REST API instead of editing JSON files by hand.
- **Generic JavaScript or Python language tutorials.** This skill assumes language fluency; it covers only the n8n-specific runtime environment and helpers.
- **Workflow scheduling outside n8n** (system cron, Airflow, etc.). Use n8n's Schedule Trigger; do not orchestrate n8n from external schedulers when avoidable.
- **Credential storage and rotation policies at the organizational level.** This skill covers credential references in node config; credential lifecycle is a separate concern.

For each excluded category, locate the appropriate documentation rather than treating it as an n8n skill problem.
