# Workflow Patterns Gotchas

Each entry follows a four-part structure: quoted symptom or error name, `**Cause:**`, `**Solution:**`, then a `❌ BAD` / `✅ GOOD` code pair.

## Webhook Data Access

### "My expression `{{$json.email}}` returns empty or undefined"

**Cause:** Data from the Webhook node is nested under `$json.body`, not at the top level. The top level holds `headers`, `params`, `query`, and `body` keys.

**Solution:** Access webhook body fields via `$json.body.<field>`.

```javascript
// ❌ BAD: returns undefined
{{$json.email}}

// ✅ GOOD: data is under .body
{{$json.body.email}}
```

### "I added a Respond to Webhook node but the webhook returns instantly anyway"

**Cause:** The Webhook node's `responseMode` is still `onReceived` (the default), which sends a 200 immediately and ignores the Respond to Webhook node.

**Solution:** Set `responseMode: "lastNode"` on the Webhook node, then place the Respond to Webhook node at the end of the flow.

```javascript
// ❌ BAD: Respond to Webhook is ignored
{ responseMode: "onReceived" }

// ✅ GOOD: workflow awaits Respond to Webhook
{ responseMode: "lastNode" }
```

### "The webhook accepts requests from anyone on the internet"

**Cause:** No authentication layer was added. A raw n8n webhook URL is publicly callable by default.

**Solution:** Add token-in-query, header-based auth, signature verification, or IP whitelist before any sensitive processing.

```javascript
// ❌ BAD: no validation, anyone can POST
Webhook → Postgres (INSERT)

// ✅ GOOD: validate signature first
Webhook → Code (HMAC verify) → IF (valid) → Postgres
```

## Multiple Items and Execution

### "My node processed every input item when I only wanted one"

**Cause:** n8n nodes execute once per input item by default. Multiple upstream items cause multiple executions.

**Solution:** Use "Execute Once" mode on the node, or select a specific item with `{{$json[0].field}}`, or aggregate items upstream with a Code node.

```javascript
// ❌ BAD: runs N times for N input items
HTTP Request (sendBody: true, body uses {{$json.id}})

// ✅ GOOD: explicit first-item access or Execute Once mode
{{$json[0].id}}   // or set executeOnce: true on the node
```

### "Nodes are firing in an order I didn't expect"

**Cause:** The workflow is using the legacy v0 execution order (top-to-bottom by position), not the v1 connection-based ordering.

**Solution:** Open workflow settings and set Execution Order to v1 (connection-based). This is the recommended default for all new workflows.

```javascript
// ❌ BAD: relies on visual node positioning
{ executionOrder: "v0" }

// ✅ GOOD: deterministic, follows connections
{ executionOrder: "v1" }
```

### "My expression renders as the literal string `{{...}}` in output"

**Cause:** The field is in fixed-string mode rather than expression mode.

**Solution:** Toggle the field to expression mode, ensure leading `=` for parameter strings (`"={{...}}"`), and use `{{}}` around the expression.

```javascript
// ❌ BAD: literal output
"name": "{{$json.body.name}}"

// ✅ GOOD: evaluated
"name": "={{$json.body.name}}"
```

## Credentials

### "API calls fail with 401 / 403 even though my key is correct"

**Cause:** Credentials were configured as raw header values in node parameters, or the wrong credential type was selected. n8n's credentials system requires explicit auth type binding.

**Solution:** Use the Credentials section of the node, choose the matching auth type (`httpHeaderAuth`, `oAuth2Api`, etc.), and reference the credential, not the raw secret.

```javascript
// ❌ BAD: secret exposed in parameters
headerParameters: { "Authorization": "Bearer sk-abc123xyz" }

// ✅ GOOD: bound via credentials system
{ authentication: "predefinedCredentialType", nodeCredentialType: "httpHeaderAuth" }
```

## SplitInBatches Wiring

### "After my SplitInBatches loop, `$('NodeInsideLoop').all()` only returns the last batch"

**Cause:** Per-iteration node data is overwritten each batch. n8n exposes only the most recent iteration's items at the end of the loop.

**Solution:** Use `$getWorkflowStaticData('global')` inside the loop to push each batch into a persistent accumulator, then read it after the loop completes.

```javascript
// ❌ BAD: only sees last batch
const all = $('Inside Loop').all();

// ✅ GOOD: persistent accumulator
const sd = $getWorkflowStaticData('global');
sd.acc ??= [];
sd.acc.push(...$input.all().map(i => i.json));
```

### "My nested SplitInBatches loop terminates after one outer iteration"

**Cause:** The inner loop's `done[0]` output was connected to the aggregate instead of looping back to the outer loop input.

**Solution:** Wire `inner_done[0] → outer loop input`. Wire `outer_done[0] → Limit 1 → Aggregate`.

```
❌ BAD wiring:
  Outer → Inner → ... → Inner done[0] → Aggregate
  (outer loop never sees the next iteration)

✅ GOOD wiring:
  Outer → Inner → ... → Inner done[0] → (back to Outer input)
                        Outer done[0] → Limit 1 → Aggregate
```

## Webhook Edge Cases

### "Workflow times out on a large webhook payload"

**Cause:** Webhook timeout defaults to 120 seconds. Synchronous processing of a large payload (image, large array) exceeds that.

**Solution:** Switch to an async queue pattern: webhook writes to Redis or a queue table, returns 200 immediately, and a separate scheduled workflow drains the queue.

```javascript
// ❌ BAD: synchronous heavy work, timeout risk
Webhook → Heavy Process → Respond

// ✅ GOOD: queue + drain
Webhook → Redis LPUSH → Respond (200 instant)
Schedule (every 1 min) → Redis BRPOP → Heavy Process
```

## HTTP API Integration

### "Workflow stops the moment any API call errors"

**Cause:** Default node behavior throws on non-2xx responses, halting the workflow.

**Solution:** Set `continueOnFail: true` on the HTTP Request node, then route on `{{$json.error}}` with an IF node.

```javascript
// ❌ BAD: API down = full workflow halt
HTTP Request → Process

// ✅ GOOD: handle failure path
HTTP Request (continueOnFail: true) → IF ($json.error) → Recovery
```

### "API base URL is hardcoded across many nodes"

**Cause:** The URL was typed directly into each HTTP Request node, so dev/staging/prod cannot diverge without manual edits.

**Solution:** Use an environment variable: `={{$env.API_BASE_URL}}/users`.

```javascript
// ❌ BAD: hardcoded
url: "https://api.example.com/prod/users"

// ✅ GOOD: env-var driven
url: "={{$env.API_BASE_URL}}/users"
```

### "I synchronously processed 10,000 items and the workflow ran out of memory"

**Cause:** The whole dataset is held in memory while every downstream node runs.

**Solution:** Use SplitInBatches to chunk processing.

```
❌ BAD:
  HTTP Request (10000 items) → Process All

✅ GOOD:
  HTTP Request → SplitInBatches (100) → Process → loop
```

## Database Operations

### "My query is vulnerable to SQL injection"

**Cause:** User-supplied data was concatenated into the SQL string instead of bound as a parameter.

**Solution:** Use parameterized queries with `$1`, `$2`, etc. (Postgres) or `?` (MySQL) and pass values through the `parameters` array.

```javascript
// ❌ BAD: SQL injection risk
{ query: "SELECT * FROM users WHERE email = '={{$json.email}}'" }

// ✅ GOOD: parameterized
{ query: "SELECT * FROM users WHERE email = $1", parameters: ["={{$json.email}}"] }
```

### "A SELECT * returned millions of rows and crashed the workflow"

**Cause:** The query has no LIMIT, no WHERE clause filter, or no pagination.

**Solution:** Always include `LIMIT` plus a watermark filter (`WHERE updated_at > $1`) or cursor (`WHERE id > $1 ORDER BY id LIMIT 1000`).

```sql
-- ❌ BAD: unbounded
SELECT * FROM large_table

-- ✅ GOOD: bounded with watermark
SELECT * FROM large_table
WHERE updated_at > $1
ORDER BY updated_at ASC
LIMIT 1000
```

### "Two-table write left an orphaned record after the second insert failed"

**Cause:** The two INSERTs were not wrapped in a transaction, so failure of the second leaves the first committed.

**Solution:** Use BEGIN / COMMIT / ROLLBACK or an atomic UPSERT pattern, and add an Error Trigger that performs compensating deletes.

```
❌ BAD:
  INSERT into orders
  INSERT into order_items   (fails → orphan)

✅ GOOD:
  BEGIN
    INSERT into orders
    INSERT into order_items
  COMMIT (or ROLLBACK on error)
```

### "UPDATE silently succeeded but no rows actually changed"

**Cause:** The WHERE clause matched nothing and n8n did not flag it as an error. `rowsAffected` was 0.

**Solution:** Add an IF check on `{{$json.rowsAffected}} === 0` and alert.

```javascript
// ❌ BAD: silent zero-row update
Postgres UPDATE → next step

// ✅ GOOD: verify update applied
Postgres UPDATE → IF ($json.rowsAffected === 0) → Alert
```

## AI Agent Workflow

### "I connected my tool to the AI Agent but it's never called"

**Cause:** The tool was connected to the AI Agent's main port instead of the `ai_tool` port. Tools must use the dedicated connection type.

**Solution:** Connect via the `ai_tool` connection type. Visually this is the small AI-specific port, not the main data port.

```
❌ BAD: HTTP Request → AI Agent  (main port)

✅ GOOD: HTTP Request --[ai_tool]--> AI Agent
```

### "The AI never picks the right tool"

**Cause:** Tool descriptions are vague ("Get data", "Search for things"), so the model cannot decide when to call them.

**Solution:** Write specific, action-oriented descriptions that name inputs and outputs.

```javascript
// ❌ BAD
description: "Search for things"

// ✅ GOOD
description: "Search GitHub issues by keyword and repository. Returns top 5 matching issues with titles and URLs."
```

### "An AI tool fetched a webpage and the agent then deleted records"

**Cause:** Indirect prompt injection. Any tool that pulls third-party text (HTTP, web search, Wikipedia, MCP filesystem) can return attacker-controlled instructions that the agent executes.

**Solution:** Never pair untrusted-input tools with destructive-output tools without a guardrail. Use read-only DB users, restrict scopes, gate destructive actions behind human approval (Send and Wait), and add explicit system-prompt rules.

```
❌ BAD:
  AI Agent with: HTTP Request (web) + Postgres (full write)

✅ GOOD:
  AI Agent with: HTTP Request (web) + Postgres (read-only)
  Destructive actions go through Send and Wait approval
```

### "My chatbot has no memory of the previous turn"

**Cause:** No memory node connected via `ai_memory`.

**Solution:** Add Window Buffer Memory (recommended) with a `sessionKey` keyed on `user_id` or `session_id`.

```javascript
// ❌ BAD: every turn is standalone

// ✅ GOOD
{ memoryType: "windowBufferMemory", sessionKey: "={{$json.body.session_id}}", contextWindowLength: 10 }
```

### "A tool returned 10MB of data and the next agent call failed on token limit"

**Cause:** Unbounded tool output (full-table SELECT, full-page HTML) consumed the context window.

**Solution:** Cap tool outputs (LIMIT in SQL, truncate text, return summarized JSON).

```javascript
// ❌ BAD
{ query: "SELECT * FROM table" }

// ✅ GOOD
{ query: "SELECT id, title FROM table LIMIT 10" }
```

### "Streaming chat shows no incremental output"

**Cause:** The AI Agent has a main output connection downstream, which forces non-streaming mode.

**Solution:** When the Chat Trigger uses `responseMode: "streaming"`, the AI Agent must have NO main output connections; the response streams back through the Chat Trigger automatically.

```
❌ BAD: AI Agent → Code → Respond (kills streaming)

✅ GOOD: AI Agent (no main outputs; streaming flows back via Chat Trigger)
```

## Scheduled Tasks

### "Scheduled job ran at the wrong wall-clock time"

**Cause:** Workflow timezone is not set, so the schedule runs in UTC (or in the host's timezone).

**Solution:** Set `timezone` explicitly in workflow settings (e.g., `"America/New_York"`). This also handles daylight saving correctly.

```javascript
// ❌ BAD: schedule says "9 AM" but in which timezone?
{ mode: "daysAndHours", hour: 9 }

// ✅ GOOD: timezone-aware
{ timezone: "America/New_York", mode: "daysAndHours", hour: 9 }
```

### "Two executions of the same scheduled workflow are running at once"

**Cause:** Schedule interval is shorter than the job runtime, so a new instance starts before the previous finishes.

**Solution:** Add a Redis-backed execution lock at the start of the workflow; skip if already locked.

```
❌ BAD:
  Schedule (every 5 min) → Job (takes 10 min)   (overlapping runs)

✅ GOOD:
  Schedule → Redis (SET lock NX EX 1800) → IF acquired → Job → Redis DEL lock
```

### "Dates in queries are hardcoded and stop working tomorrow"

**Cause:** A literal date string was embedded in the SQL.

**Solution:** Use SQL date arithmetic (`CURRENT_DATE - INTERVAL '1 day'`) or n8n expressions (`$now.minus({days: 1})`).

```sql
-- ❌ BAD
SELECT * FROM orders WHERE date = '2024-01-15'

-- ✅ GOOD
SELECT * FROM orders WHERE date = CURRENT_DATE - INTERVAL '1 day'
```

### "Workflow looks correct in the editor but never runs on schedule"

**Cause:** Workflow was created via the n8n API or MCP but not activated. The MCP and API cannot activate workflows; activation is manual in the UI.

**Solution:** Open the workflow in the n8n UI and toggle the active switch. (Or use the `activateWorkflow` operation if your tooling supports it.)

```
❌ BAD: created via MCP, assumed active

✅ GOOD: manual UI activation, then verify in Executions list
```

## Integration-Specific Gotchas

### Google Sheets: "Appending broke my formula column"

**Cause:** The Google Sheets node's `append` operation rewrites the formula range, breaking formulas in sheets with computed columns.

**Solution:** Use the Google Sheets API `values.update` (PUT) via an HTTP Request node with a `googleApi` credential, never the append node on formula-bearing sheets.

```javascript
// ❌ BAD: append breaks formulas
Google Sheets (append)

// ✅ GOOD: PUT via HTTP Request with googleApi cred
HTTP Request (PUT spreadsheets/{id}/values/{range})
```

### Google Sheets: "My ADD() formula started returning #VALUE!"

**Cause:** The cell was written as a string ("4.98") instead of a number (4.98). Google Sheets formulas error on string operands.

**Solution:** Coerce to a number with `parseFloat()` in a Code node before writing.

```javascript
// ❌ BAD
{ amount: "={{$json.amount}}" }   // string

// ✅ GOOD
const n = parseFloat($json.amount);
return [{ json: { amount: n } }];
```

### Google Sheets: "I sent 10 items and the node ran 10 times"

**Cause:** Google Sheets nodes execute once per input item.

**Solution:** Aggregate all rows into a single item upstream (Code node returning one item with `rows: [...]`), then bulk-write.

```javascript
// ❌ BAD: 10 separate node executions
10 items → Google Sheets (append)

// ✅ GOOD: 1 execution, 10 rows written
Code (aggregate to 1 item) → Google Sheets (bulk)
```

### Google Sheets: "UNFORMATTED_VALUE returned numbers where I expected text like N/A"

**Cause:** The API returns the underlying numeric type for `UNFORMATTED_VALUE`; display-only text like "N/A" is not preserved.

**Solution:** Filter explicitly in a Code node, do not rely on display strings.

```javascript
// ❌ BAD: assumes "N/A" passes through
if (val === "N/A") skip();

// ✅ GOOD: numeric-aware filter
if (val === null || val === undefined || typeof val !== 'number') skip();
```

### Google Drive: "I uploaded a CSV but Drive shows a Google Doc"

**Cause:** `convertToGoogleDocument: true` was set, which creates a Google Doc (text document), not a Google Sheet or a downloadable CSV.

**Solution:** Omit `convertToGoogleDocument` entirely to keep the file as a raw CSV.

```javascript
// ❌ BAD: creates a Doc
{ convertToGoogleDocument: true }

// ✅ GOOD: stays a CSV
{ /* convertToGoogleDocument omitted */ }
```

### Google Drive: "My CSV download link opens a viewer instead of downloading"

**Cause:** The `/view` URL form opens the Drive viewer.

**Solution:** Use the export-download URL format: `https://drive.google.com/uc?id={fileId}&export=download`.

```javascript
// ❌ BAD
url: `https://drive.google.com/file/d/${id}/view`

// ✅ GOOD
url: `https://drive.google.com/uc?id=${id}&export=download`
```

## Data-Quality Gotchas

### "My monitor only catches price spikes, not crashes"

**Cause:** Threshold check uses `diff > threshold` instead of `Math.abs(diff) > threshold`.

**Solution:** Compare magnitude, not signed delta. A 90% crash is as important as a 90% spike.

```javascript
// ❌ BAD: only catches increases
if (diff > threshold) flag();

// ✅ GOOD: catches both directions
if (Math.abs(diff) > threshold) flag();
```

## See Also

- [api.md](./api.md) for choosing the right pattern up front.
- [patterns.md](./patterns.md) for the cross-cutting patterns that prevent many of these gotchas.
- [configuration.md](./configuration.md) for timezone, credentials, and trigger setup.
- The relevant alongside file for pattern-specific details.
