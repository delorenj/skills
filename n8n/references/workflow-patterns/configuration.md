# Workflow Configuration

Setup concerns shared by all six patterns: triggers, credentials, timezones, workflow settings, environment variables, and activation.

## Trigger Configuration

### Webhook Trigger

```javascript
{
  path: "form-submit",          // URL path: https://n8n.example.com/webhook/form-submit
  httpMethod: "POST",           // GET, POST, PUT, DELETE
  responseMode: "onReceived",   // "onReceived" | "lastNode" | "streaming"
  responseData: "allEntries"    // "allEntries" | "firstEntryJson"
}
```

- **`path`**: pick a descriptive, kebab-case path. Use environment variables to differentiate dev / prod: `={{$env.WEBHOOK_PATH_PREFIX}}/form-submit`.
- **`responseMode`**: see decision in [api.md](./api.md). Use `lastNode` when caller needs the workflow result; `onReceived` for fire-and-forget; `streaming` for chat trigger.
- **URL**: production webhook URL is `https://<host>/webhook/<path>`; test URL is `https://<host>/webhook-test/<path>` (active only while editor's "Listen for Test Event" is on).

### Schedule Trigger: Interval Mode

For simple recurring jobs.

```javascript
// Every 15 minutes
{ mode: "interval", interval: 15, unit: "minutes" }

// Every 2 hours
{ mode: "interval", interval: 2, unit: "hours" }

// Every day
{ mode: "interval", interval: 1, unit: "days" }
```

### Schedule Trigger: Days & Hours Mode

For specific weekdays at a specific clock time.

```javascript
// Weekdays at 9 AM
{
  mode: "daysAndHours",
  days: ["monday", "tuesday", "wednesday", "thursday", "friday"],
  hour: 9,
  minute: 0
}

// Every Monday at 6 PM
{
  mode: "daysAndHours",
  days: ["monday"],
  hour: 18,
  minute: 0
}
```

### Schedule Trigger: Cron Mode

For complex schedules. Cron format is `minute hour day month weekday`.

```javascript
// Every weekday at 9 AM
{ mode: "cron", expression: "0 9 * * 1-5" }

// First day of every month at midnight
{ mode: "cron", expression: "0 0 1 * *" }

// Every 15 minutes during business hours, weekdays
{ mode: "cron", expression: "*/15 9-17 * * 1-5" }
```

Cron special characters:

- `*` = any value
- `*/15` = every 15 units
- `1-5` = range (Monday-Friday)
- `1,15` = enumerated values

Common cron expressions:

| Expression | Meaning |
|------------|---------|
| `0 */6 * * *` | Every 6 hours |
| `0 9,17 * * *` | 9 AM and 5 PM daily |
| `0 0 * * 0` | Every Sunday at midnight |
| `*/30 * * * *` | Every 30 minutes |
| `0 0 1,15 * *` | 1st and 15th of each month |

### Manual Trigger

Used during development to substitute for a webhook or schedule. Replace with the real trigger before deploy.

### AI Chat Trigger

Use for AI Agent Workflows that need a chat UI. Set `responseMode: "streaming"` for incremental output (and remove the AI Agent's main output connections; see [gotchas.md](./gotchas.md)).

## Timezone Configuration

Always set the workflow timezone explicitly. The default is the n8n host's timezone, which is implicit and often UTC.

```javascript
// Workflow settings
{
  timezone: "America/New_York"
}
```

Common values:

| Zone | Region |
|------|--------|
| `America/New_York` | US Eastern (handles EDT/EST) |
| `America/Chicago` | US Central |
| `America/Denver` | US Mountain |
| `America/Los_Angeles` | US Pacific |
| `Europe/London` | GMT/BST |
| `Europe/Paris` | CET/CEST |
| `Asia/Tokyo` | JST |
| `Australia/Sydney` | AEDT |
| `UTC` | Universal Time |

Daylight saving: setting an IANA timezone (not UTC) makes schedules DST-aware. A workflow set to 9 AM `America/New_York` runs at 9 AM local both in EST and EDT.

## Credentials

All authentication goes through the credentials system, never inline in node parameters.

| Credential Type | Use Case |
|------------------|----------|
| `httpHeaderAuth` | Bearer tokens and API-key-in-header |
| `httpQueryAuth` | API-key-in-query-string |
| `httpBasicAuth` | Basic auth (username + password) |
| `oAuth2Api` | OAuth2 flows |
| `googleApi` | Google Workspace (Sheets, Drive, Gmail) |
| Service-specific (`slackOAuth2Api`, `postgres`, etc.) | Service nodes use their own typed credentials |

Reference a credential from a node:

```javascript
{
  authentication: "predefinedCredentialType",
  nodeCredentialType: "httpHeaderAuth"
}
```

For OAuth2 setup, the credential needs:

- Authorization URL
- Token URL
- Client ID
- Client Secret
- Scopes

For databases, the credential carries host, database name, user, password, and connection pool settings:

```javascript
{
  host: "db.example.com",
  database: "mydb",
  user: "user",
  password: "pass",
  // Connection pool
  min: 2,
  max: 10,
  idleTimeoutMillis: 30000
}
```

## Environment Variables

Reference environment variables anywhere with `={{$env.VAR_NAME}}`. Use them for:

- API base URLs: `={{$env.API_BASE_URL}}/users`
- Webhook path prefixes: `={{$env.WEBHOOK_PATH_PREFIX}}/form-submit`
- Feature flags
- Per-environment toggles (dev / staging / prod)

Set environment variables on the n8n host (Docker env vars, Kubernetes secrets, or `.env`). They are not the same as n8n credentials and should not store secrets that you can put in credentials instead.

## Workflow Settings

Open the workflow in the n8n UI and configure Settings:

| Setting | Recommendation |
|---------|----------------|
| Execution Order | **v1** (connection-based). v0 is legacy and order-dependent on visual layout. |
| Timezone | Set explicitly per the table above. |
| Error Workflow | Wire to a dedicated error-handling workflow for alerts. |
| Save Manual Executions | On during development; off in production to save disk. |
| Save Successful Production Executions | On for the first weeks of a new workflow, then re-evaluate. |
| Save Failed Production Executions | Always on. |
| Timeout | Set a sensible upper bound; default is unlimited. |

## Per-Node Settings

Common per-node settings that affect pattern behavior:

| Setting | Effect |
|---------|--------|
| `continueOnFail: true` | Node failure does not halt the workflow; downstream nodes can branch on `$json.error`. |
| `executeOnce: true` | Node runs once even if upstream has multiple items. |
| `retryOnFail` / `maxTries` / `waitBetweenTries` | Built-in retry with backoff (alternative to manual retry pattern). |
| `notesInFlow: true` | Show node notes inline in the editor for documentation. |
| `alwaysOutputData: true` | Emit an empty item rather than nothing on no-op. |

## Activation

Activation is **manual** in the n8n UI. The MCP server and most API calls cannot activate workflows. After creating or updating, open the workflow in the editor and toggle the active switch.

Verify activation by:

1. Editor shows the green active indicator.
2. Webhook production URL responds (`/webhook/<path>`, not `/webhook-test/<path>`).
3. Schedule trigger shows its next run time.
4. Executions list begins receiving entries on the configured trigger.

## Monitoring & Logging

Recommended companion infrastructure:

- A `workflow_executions` table for custom execution logs (see [scheduled-tasks.md](./scheduled-tasks.md) for schema).
- A summary scheduled workflow (daily / weekly) that emails or Slacks success / failure counts.
- An Error Trigger workflow that fans out to Slack + PagerDuty + log table.

## Security Settings

- **Always HTTPS** for webhook URLs in production.
- **IP whitelist** in workflow settings for internal-only webhooks.
- **Read-only DB users** for AI agent tools (see [ai-agent-workflow.md](./ai-agent-workflow.md)).
- **Least-privilege credentials**: scope OAuth2 to exactly the operations the workflow needs.

## See Also

- [api.md](./api.md) for the decision tables that determine which trigger and pattern to use.
- [gotchas.md](./gotchas.md) for activation, timezone, and credential failure modes.
- [scheduled-tasks.md](./scheduled-tasks.md) for additional cron and execution-lock details.
- [webhook-processing.md](./webhook-processing.md) for response-mode trade-offs and webhook security.
