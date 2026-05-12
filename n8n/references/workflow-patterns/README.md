# Workflow Patterns

Proven architectural patterns for n8n workflows. Six core patterns cover 90% of real-world workflow use cases: webhook processing, HTTP API integration, database operations, AI agent workflows, scheduled tasks, and batch processing. Use this reference when designing a new workflow, choosing a topology, or evaluating whether an existing workflow follows a sound pattern. Each pattern entry documents structure, components, common variants, complete examples, and integration-specific gotchas.

## When to Use

| Need | Pattern |
|------|---------|
| Receive HTTP requests from external systems | [webhook-processing.md](./webhook-processing.md) |
| Fetch and consume data from third-party REST APIs | [http-api-integration.md](./http-api-integration.md) |
| Read, write, sync, or maintain database records | [database-operations.md](./database-operations.md) |
| Build conversational AI with tools and memory | [ai-agent-workflow.md](./ai-agent-workflow.md) |
| Run recurring automation on a cron or interval | [scheduled-tasks.md](./scheduled-tasks.md) |
| Process large datasets in chunks (e.g., N categories x M paginated items) | [patterns.md](./patterns.md) (Batch Processing) |
| Look up which pattern fits a specific task type | [api.md](./api.md) |
| Diagnose a failing or misbehaving workflow | [gotchas.md](./gotchas.md) |
| Configure triggers, credentials, timezones, or environment | [configuration.md](./configuration.md) |

## Quick Start

1. Identify the **trigger** type your workflow needs: webhook (event), schedule (time), manual (testing), or another node trigger.
2. Look up the canonical pattern in [api.md](./api.md) using the task-to-pattern mapping table.
3. Read the alongside file for that pattern (e.g., [webhook-processing.md](./webhook-processing.md)) for full structure, variants, and a complete example.
4. Scan [gotchas.md](./gotchas.md) for pitfalls specific to your pattern before building.
5. Configure triggers and credentials per [configuration.md](./configuration.md).
6. Validate with `validate_workflow` (see [../validation/](../validation/)).

## Reading Order

| Task | Files to Read |
|------|---------------|
| First-time pattern selection | README.md, [api.md](./api.md), then the chosen alongside file |
| Build a webhook-driven integration | [webhook-processing.md](./webhook-processing.md), [gotchas.md](./gotchas.md), [configuration.md](./configuration.md) |
| Build an API-fetching workflow | [http-api-integration.md](./http-api-integration.md), [patterns.md](./patterns.md) (rate-limiting / pagination), [gotchas.md](./gotchas.md) |
| Build a database sync or ETL workflow | [database-operations.md](./database-operations.md), [patterns.md](./patterns.md) (batch processing), [gotchas.md](./gotchas.md) |
| Build an AI agent | [ai-agent-workflow.md](./ai-agent-workflow.md), [gotchas.md](./gotchas.md), then [../mcp-tools/](../mcp-tools/) |
| Build a scheduled job | [scheduled-tasks.md](./scheduled-tasks.md), [configuration.md](./configuration.md), [gotchas.md](./gotchas.md) |
| Process very large datasets | [patterns.md](./patterns.md) (Batch Processing, Nested Loops), [gotchas.md](./gotchas.md) |
| Debug a misbehaving workflow | [gotchas.md](./gotchas.md), then the relevant alongside file |
| Plan an end-to-end deployment | All files in order: README.md, api.md, alongside files, patterns.md, gotchas.md, configuration.md |

## In This Reference

- [api.md](./api.md): Pattern-selection API. Maps every common task scenario to its canonical pattern. Treat as a decision table.
- [patterns.md](./patterns.md): Index of the 5 alongside pattern files plus cross-cutting patterns (batch processing, retries, error handling, idempotency) that apply to all six patterns.
- [gotchas.md](./gotchas.md): Four-part gotchas for design failure modes, anti-patterns, and integration-specific traps (Google Sheets, Google Drive, webhook data access, etc.).
- [configuration.md](./configuration.md): Trigger configuration (cron, interval, webhook URLs), credentials, timezones, workflow settings, environment variables.
- [webhook-processing.md](./webhook-processing.md): Most-common pattern. HTTP endpoint trigger, validation, response modes, authentication, security.
- [http-api-integration.md](./http-api-integration.md): REST API consumption. Authentication methods, pagination strategies, rate limiting, retries.
- [database-operations.md](./database-operations.md): Read/write/sync/ETL with Postgres, MySQL, MongoDB. Transactions, batch writes, security.
- [ai-agent-workflow.md](./ai-agent-workflow.md): AI agents with tools and memory. 8 AI connection types, prompt engineering, prompt injection defenses.
- [scheduled-tasks.md](./scheduled-tasks.md): Cron, interval, and days-and-hours schedules. Timezones, DST, execution locks, monitoring.

## The Six Core Patterns

1. **Webhook Processing** (most common): Receive HTTP request, validate, transform, act, respond. See [webhook-processing.md](./webhook-processing.md).
2. **HTTP API Integration**: Trigger, HTTP Request, transform, action, error handler. See [http-api-integration.md](./http-api-integration.md).
3. **Database Operations**: Schedule or event, query, transform, write, verify. See [database-operations.md](./database-operations.md).
4. **AI Agent Workflow**: Trigger, AI Agent (model + tools + memory), output. See [ai-agent-workflow.md](./ai-agent-workflow.md).
5. **Scheduled Tasks**: Schedule, fetch, process, deliver, log. See [scheduled-tasks.md](./scheduled-tasks.md).
6. **Batch Processing**: Prepare, SplitInBatches, process per batch, accumulate, aggregate. See [patterns.md](./patterns.md).

## See Also

- [../mcp-tools/](../mcp-tools/): Discovery and creation tools (search_nodes, get_node_types, create_workflow_from_code).
- [../validation/](../validation/): Workflow validation before deploy.
- [../expressions/](../expressions/): Expression syntax for transformation nodes (e.g., `{{$json.body.field}}`).
- [../node-configuration/](../node-configuration/): Node-specific parameter reference.
- [../code-javascript/](../code-javascript/): Code node patterns for cross-iteration data, accumulator state, and complex transforms.
- [../code-python/](../code-python/): Python Code node patterns.
