# Pattern-Selection API

This file is the decision API for workflow-patterns: given a task type or scenario, it returns the canonical pattern to use. There is no formal SDK surface here. Use the tables below the way you would use method signatures: scan the "input scenario" column, then read the chosen pattern's alongside file.

## Primary Decision Table

| Task / Scenario (Input) | Canonical Pattern (Output) | Alongside File |
|-------------------------|----------------------------|----------------|
| External service POSTs data to you | Webhook Processing | [webhook-processing.md](./webhook-processing.md) |
| Form submission needs handling | Webhook Processing | [webhook-processing.md](./webhook-processing.md) |
| Slack slash command or Discord bot | Webhook Processing | [webhook-processing.md](./webhook-processing.md) |
| Stripe / PayPal payment notification | Webhook Processing (with signature verification) | [webhook-processing.md](./webhook-processing.md) |
| GitHub / GitLab webhook | Webhook Processing | [webhook-processing.md](./webhook-processing.md) |
| IoT device pushing readings | Webhook Processing | [webhook-processing.md](./webhook-processing.md) |
| Fetch data from a third-party REST API | HTTP API Integration | [http-api-integration.md](./http-api-integration.md) |
| Synchronize with a third-party service on a timer | HTTP API Integration + Scheduled Tasks | [http-api-integration.md](./http-api-integration.md), [scheduled-tasks.md](./scheduled-tasks.md) |
| Build a CRM-to-CRM bridge | HTTP API Integration | [http-api-integration.md](./http-api-integration.md) |
| Enrich records via a third-party API (Clearbit, etc.) | HTTP API Integration | [http-api-integration.md](./http-api-integration.md) |
| Sync between two databases (e.g., Postgres to MySQL) | Database Operations | [database-operations.md](./database-operations.md) |
| Run an ETL pipeline | Database Operations | [database-operations.md](./database-operations.md) |
| Periodic database maintenance / cleanup | Database Operations + Scheduled Tasks | [database-operations.md](./database-operations.md), [scheduled-tasks.md](./scheduled-tasks.md) |
| Archive old records | Database Operations + Scheduled Tasks | [database-operations.md](./database-operations.md), [scheduled-tasks.md](./scheduled-tasks.md) |
| Real-time write from webhook into a DB | Webhook Processing + Database Operations | [webhook-processing.md](./webhook-processing.md), [database-operations.md](./database-operations.md) |
| Conversational AI / customer support chat | AI Agent Workflow | [ai-agent-workflow.md](./ai-agent-workflow.md) |
| AI assistant that calls APIs or queries databases | AI Agent Workflow | [ai-agent-workflow.md](./ai-agent-workflow.md) |
| Document Q&A over a knowledge base | AI Agent Workflow (with RAG) | [ai-agent-workflow.md](./ai-agent-workflow.md) |
| AI-powered email routing / triage | AI Agent Workflow | [ai-agent-workflow.md](./ai-agent-workflow.md) |
| SQL analyst chatbot | AI Agent Workflow (with read-only DB tool) | [ai-agent-workflow.md](./ai-agent-workflow.md) |
| Daily / weekly report generation | Scheduled Tasks | [scheduled-tasks.md](./scheduled-tasks.md) |
| Cron-driven data pull | Scheduled Tasks | [scheduled-tasks.md](./scheduled-tasks.md) |
| Health check / uptime monitor | Scheduled Tasks (with HTTP API check) | [scheduled-tasks.md](./scheduled-tasks.md) |
| Automated backup | Scheduled Tasks | [scheduled-tasks.md](./scheduled-tasks.md) |
| Content publishing on a calendar | Scheduled Tasks | [scheduled-tasks.md](./scheduled-tasks.md) |
| Dataset larger than API batch limit | Batch Processing (SplitInBatches) | [patterns.md](./patterns.md) |
| N categories x M paginated items per category | Batch Processing (Nested Loops) | [patterns.md](./patterns.md) |
| Cursor / date-window pagination over an API | Batch Processing (id_from pagination) | [patterns.md](./patterns.md), [http-api-integration.md](./http-api-integration.md) |
| Need to accumulate results across loop iterations | Batch Processing (workflowStaticData accumulator) | [patterns.md](./patterns.md), [../code-javascript/](../code-javascript/) |

## Trigger Selection

| Stimulus | Trigger Node | Pattern |
|----------|--------------|---------|
| External HTTP push | Webhook | Webhook Processing |
| Calendar time | Schedule Trigger | Scheduled Tasks |
| Manual run for testing | Manual Trigger | Any pattern (development) |
| User chat message | Chat Trigger or Webhook | AI Agent Workflow |
| Email arrival | Email Trigger (IMAP) | Webhook-like / AI Agent |
| File change | Local File Trigger | Database Operations / Scheduled-like |
| Polling for changes | Polling Trigger | Scheduled Tasks |

## Data-Source Selection

| Where the data lives | Source Node |
|----------------------|-------------|
| REST API | HTTP Request |
| Relational DB | Postgres, MySQL, Microsoft SQL, SQLite |
| Document DB | MongoDB |
| Key-value store | Redis |
| Spreadsheet | Google Sheets, Microsoft Excel |
| Service-specific | Slack, Gmail, Notion, Airtable, etc. |
| Custom logic | Code (JavaScript / Python) |

## Transformation Selection

| Need | Node |
|------|------|
| Field map / rename | Set |
| Complex logic / loops / accumulators | Code |
| Two-way conditional routing | IF |
| Multi-way conditional routing | Switch |
| Combine two data streams | Merge |
| Aggregate items into one item | Aggregate or Code |
| Split one item into many | Split Out |
| Iterate over a large dataset | SplitInBatches |

## Output / Action Selection

| Destination | Node |
|-------------|------|
| External REST API | HTTP Request |
| Database write | Postgres / MySQL / MongoDB / etc. |
| Team chat | Slack / Discord / Microsoft Teams |
| Email | Send Email / Gmail |
| File | Write Binary File / Google Drive / S3 |
| Spreadsheet append | Google Sheets / Excel |
| Webhook response (synchronous) | Respond to Webhook |

## Error-Handling Selection

| Need | Mechanism |
|------|-----------|
| Catch any workflow failure | Error Trigger workflow (separate workflow) |
| Continue past a single node failure | `continueOnFail: true` on the node |
| Stop with a custom message | Stop and Error node |
| Conditional check on error presence | IF on `{{$json.error}}` |
| Retry with backoff | Wait + IF + loopback (or `retryOnFail` per node) |
| Fallback to alternative service | continueOnFail then IF, branch to secondary HTTP Request |

## Response-Mode Selection (Webhook Only)

| Scenario | `responseMode` |
|----------|----------------|
| Fire-and-forget, long-running processing | `onReceived` (instant 200) |
| Caller needs the workflow's result back | `lastNode` (then add Respond to Webhook node) |
| Streaming chat response | `streaming` (no main output on AI Agent) |

## Schedule Mode Selection

| Need | `mode` |
|------|--------|
| Every X minutes / hours / days | `interval` |
| Specific days at a specific clock time | `daysAndHours` |
| Anything more complex | `cron` (e.g., `0 9 * * 1-5`) |

## Memory Selection (AI Agent Only)

| Conversation profile | Memory type |
|----------------------|-------------|
| Short, bounded session | Window Buffer Memory (recommended) |
| Need every message indefinitely | Buffer Memory |
| Very long conversation, token-sensitive | Summary Memory |
| Per-user vs per-session | Set `sessionKey` to `user_id` or `session_id` accordingly |

## Pattern Composition

Patterns combine. Common multi-pattern compositions:

| Composition | Use Case |
|-------------|----------|
| Webhook Processing + Database Operations | Real-time write from event |
| Webhook Processing + AI Agent Workflow | Chatbot endpoint |
| Scheduled Tasks + HTTP API Integration | Periodic API sync |
| Scheduled Tasks + Database Operations | ETL / maintenance |
| Scheduled Tasks + Batch Processing | Backfill or bulk processing job |
| HTTP API Integration + Batch Processing | Paginated dataset fetch |
| AI Agent Workflow + Database Operations (read-only) | SQL analyst agent |
| AI Agent Workflow + HTTP API Integration (as ai_tool) | AI with API access |

## See Also

- [patterns.md](./patterns.md) for cross-cutting patterns that apply across multiple canonical patterns.
- [gotchas.md](./gotchas.md) for failure modes that bite during pattern selection.
- [../validation/](../validation/) to validate the resulting workflow.
