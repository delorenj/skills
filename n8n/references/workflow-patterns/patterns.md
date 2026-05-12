# Patterns Index and Cross-Cutting Patterns

This file is an index of the five canonical alongside-file patterns plus cross-cutting patterns (batch processing, error handling, retries, idempotency, dataflow topologies) that apply across all six core patterns.

## The Five Canonical Patterns (Alongside Files)

| Pattern | Structure | Alongside File |
|---------|-----------|----------------|
| **Webhook Processing** | Webhook, Validate, Transform, Action, Respond/Notify | [webhook-processing.md](./webhook-processing.md) |
| **HTTP API Integration** | Trigger, HTTP Request, Transform, Action, Error Handler | [http-api-integration.md](./http-api-integration.md) |
| **Database Operations** | Trigger, Query/Read, Transform, Write/Update, Verify/Log | [database-operations.md](./database-operations.md) |
| **AI Agent Workflow** | Trigger, AI Agent (Model + Tools + Memory), Process Response, Output | [ai-agent-workflow.md](./ai-agent-workflow.md) |
| **Scheduled Tasks** | Schedule Trigger, Fetch Data, Process, Deliver, Log/Notify | [scheduled-tasks.md](./scheduled-tasks.md) |

The sixth core pattern, **Batch Processing**, is documented inline below because it composes with all of the others rather than living on its own.

## Cross-Cutting Pattern: Batch Processing

### SplitInBatches Loop

The SplitInBatches node splits a large dataset into smaller chunks for processing. Understanding its outputs is critical:

- `main[0]` = **done**, fires ONCE after all batches complete
- `main[1]` = **each batch**, fires per batch (this is the loop body)

```
Prepare Items
  → SplitInBatches
    → [main[1]: Process Batch] (loops back automatically)
    → [main[0]: Done] → Limit 1 → Aggregate
```

Always add a **Limit 1** node after the done output.

### Cross-Iteration Data Accumulation

After the loop, `$('Node Inside Loop').all()` returns ONLY the last batch's items. To accumulate across all iterations, use `$getWorkflowStaticData('global')` in a Code node inside the loop body. See [../code-javascript/](../code-javascript/) for the complete accumulator pattern.

```javascript
// ✅ GOOD: inside loop body Code node
const staticData = $getWorkflowStaticData('global');
if (!staticData.accumulated) staticData.accumulated = [];
staticData.accumulated.push(...$input.all().map(i => i.json));
return $input.all();
```

After the loop completes on `main[0]`, a downstream Code node reads `$getWorkflowStaticData('global').accumulated` for the full dataset.

### Nested Loops (N x M)

When processing N categories x M items per category and an API has a per-call batch limit:

```
Define Categories (N items)
  → Outer Loop (SplitInBatches, batchSize=1)
    → Prepare category data
    → Inner Loop (SplitInBatches, batchSize=1000)
      → API Call
      → Verify
      → (loops back to Inner Loop main[1])
    → Inner done[0] → Rate Limit Delay → back to Outer Loop input
  → Outer done[0] → Limit 1 → Final Aggregate
```

**Wiring rule**: the inner `done[0]` must connect back to the OUTER loop input, not to the aggregate. The outer `done[0]` feeds the final aggregate. See [gotchas.md](./gotchas.md) for the common wiring failure mode.

### API Pagination via id_from + Date Windowing

For APIs without multi-ID filtering, use `id_from` + date windowing for efficient pagination:

```
Schedule → Set Date Window → Fetch Page → Process
  → IF has_more?
    → [true] Update id_from → Fetch Page (loop)
    → [false] → Aggregate → Output
```

### Dry-Run / Verification Tolerance

When testing with API write nodes disabled (dry runs), downstream verification nodes receive the request body instead of the response. Make verification tolerant:

```javascript
// In the verification Code node
const body = $input.first().json;
const looksLikeRequest = body.method && body.parameters && !body.status;
if (looksLikeRequest) {
  return [{ json: { status: 'SKIPPED', message: 'Upstream disabled for testing' }}];
}
// Normal response verification below...
```

## Cross-Cutting Pattern: Data Flow Topologies

### Linear Flow

```
Trigger → Transform → Action → End
```

Use when the workflow has a single path.

### Branching Flow

```
Trigger → IF → [True Path]
             → [False Path]
```

Use when actions depend on conditions.

### Parallel Processing

```
Trigger → [Branch 1] → Merge
       → [Branch 2] →
```

Use when independent operations can run simultaneously. Use the Merge node to wait for all branches before continuing.

### Loop Pattern

```
Trigger → SplitInBatches → Process → (loops back until done)
```

Use when processing large datasets in chunks.

### Error Handler Pattern

```
Main Flow → [Success Path]
         → [Error Trigger → Error Handler]
```

Use when a separate workflow should handle errors for clarity and reuse.

## Cross-Cutting Pattern: Error Handling

Three layered strategies, used in combination:

1. **Per-node `continueOnFail: true`**: prevents one failed node from stopping the workflow. Pair with a downstream IF check.
2. **Error Trigger workflow**: a separate workflow listening for failures of the main workflow. Use for alerting, logging, and recovery.
3. **Explicit IF gates**: validate data shape, check `{{$json.statusCode}}` or `{{$json.error}}`, and route to recovery.

```
HTTP Request (continueOnFail: true)
  → IF ({{$json.error}} is empty)
    → [Success: process]
    → [Error: log, retry, or alert]
```

## Cross-Cutting Pattern: Retry with Exponential Backoff

```javascript
// Code node
const maxRetries = 3;
let retryCount = $json.retryCount || 0;

if ($json.error && retryCount < maxRetries) {
  const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
  return [{ json: { ...$json, retryCount: retryCount + 1, waitTime: delay } }];
}
```

Pair with a Wait node configured by `waitTime`, then loop back to the failing operation.

## Cross-Cutting Pattern: Idempotency

Multiple-execution safety, critical for webhooks (which can be redelivered) and scheduled jobs (which can overlap):

1. **Use UPSERT instead of INSERT** where possible (`ON CONFLICT DO UPDATE`).
2. **Track last-sync watermark**: query records `WHERE updated_at > $1` and store `$1` after the run.
3. **Deduplicate by external ID**: store the webhook's event ID in a `processed_events` table; skip if seen.
4. **Execution locks**: Redis SET with TTL prevents overlapping scheduled runs (see [scheduled-tasks.md](./scheduled-tasks.md)).

## Cross-Cutting Pattern: Bidirectional Threshold Checking

When comparing values (prices, quantities, metrics), always check both directions:

```javascript
// ❌ BAD: only catches increases
if (diff > threshold) { flag(); }

// ✅ GOOD: catches spikes AND crashes, both are data-quality signals
if (Math.abs(diff) > threshold) { flag(); }
```

## Cross-Cutting Pattern: Rate Limiting

Three strategies, scale up as needed:

1. **Wait Between Requests**: simple `Wait` node between API calls.
2. **Exponential Backoff on 429**: see retry pattern above.
3. **Respect Rate Limit Headers**: read `x-ratelimit-remaining` and `x-ratelimit-reset` headers, then wait dynamically.

```javascript
// Code node
const headers = $input.first().json.headers;
const remaining = parseInt(headers['x-ratelimit-remaining'] || '999');
const resetTime = parseInt(headers['x-ratelimit-reset'] || '0');

if (remaining < 10) {
  const now = Math.floor(Date.now() / 1000);
  return [{ json: { shouldWait: true, waitSeconds: Math.max(resetTime - now, 0) } }];
}
return [{ json: { shouldWait: false } }];
```

## Cross-Cutting Pattern: Authentication

Always via the n8n credentials system, never hardcoded in node parameters. The five common forms:

| Form | Credential Type |
|------|-----------------|
| None (public APIs) | `none` |
| Bearer token | `httpHeaderAuth` with `Authorization: Bearer ...` |
| API key in header | `httpHeaderAuth` |
| API key in query | `httpQueryAuth` |
| Basic auth | `httpBasicAuth` |
| OAuth2 | `oAuth2Api` |

Detailed examples live in [http-api-integration.md](./http-api-integration.md).

## Cross-Cutting Pattern: Webhook Data Access

Data from the Webhook node is nested under `$json.body`. This is the single most-encountered gotcha in webhook workflows. See [gotchas.md](./gotchas.md) for the four-part entry.

```javascript
{{$json.body.email}}   // ✅ GOOD
{{$json.email}}        // ❌ BAD, returns undefined
```

Also available:

- `{{$json.headers['x-custom-header']}}` for headers
- `{{$json.params.id}}` for URL path params (e.g., `/webhook/form/:id`)
- `{{$json.query.token}}` for URL query string params

## Workflow Creation Checklist

Apply this checklist to every workflow regardless of pattern:

**Planning Phase**
- Identify the pattern (use [api.md](./api.md))
- List required nodes (use `search_nodes`)
- Map the data flow (input, transform, output)
- Plan the error handling strategy

**Implementation Phase**
- Create workflow with appropriate trigger
- Add data source nodes
- Configure authentication via credentials
- Add transformation nodes (Set, Code, IF)
- Add output / action nodes
- Configure error handling

**Validation Phase**
- Validate each node (`validate_node`)
- Validate the complete workflow (`validate_workflow`)
- Test with sample data
- Handle edge cases (empty data, errors)

**Deployment Phase**
- Review workflow settings (execution order, timeout, error handling)
- Activate the workflow in the n8n UI (manual activation; API and MCP cannot activate)
- Monitor first executions
- Document the workflow purpose and data flow

## Best Practices

### Do

- Start with the simplest pattern that solves the problem.
- Plan the workflow structure before building.
- Use error handling on every workflow.
- Test with sample data before activation.
- Use descriptive node names.
- Document complex workflows in the notes field.
- Monitor executions after deployment.

### Don't

- Build the whole workflow in one shot; iterate.
- Skip validation before activation.
- Ignore error scenarios.
- Use complex patterns when simple ones suffice.
- Hardcode credentials in node parameters.
- Forget to handle empty-data cases.
- Mix multiple patterns without clear boundaries.
- Deploy without testing.

## See Also

- [api.md](./api.md) for the pattern-selection decision tables.
- [gotchas.md](./gotchas.md) for failure modes specific to each pattern and cross-cutting integration traps.
- [configuration.md](./configuration.md) for trigger and credential setup.
- [../code-javascript/](../code-javascript/) for accumulator patterns and complex Code node logic.
- [../validation/](../validation/) for pre-deploy validation.
