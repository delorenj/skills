# Webhook Processing Pattern

Cross-refs: see [patterns.md](./patterns.md) for cross-cutting batch and retry patterns; see [gotchas.md](./gotchas.md) for webhook-specific traps (data under `$json.body`, response mode confusion, authentication).

**Use Case**: Receive HTTP requests from external systems and process them instantly.

## Pattern Structure

```
Webhook → [Validate] → [Transform] → [Action] → [Response/Notify]
```

**Key Characteristic**: Instant event-driven processing.

## Use Cases

- Form submissions, contact forms, lead capture.
- Payment notifications (Stripe, PayPal) with signature verification.
- Chat platform integrations (Slack slash commands, Discord interactions, Microsoft Teams).
- Source-control webhooks (GitHub, GitLab) for CI/CD and notifications.
- IoT device telemetry with threshold-based alerts.
- Generic third-party integrations that push events.

## Core Components

### 1. Webhook Node (Trigger)

Purpose: create an HTTP endpoint to receive data.

```javascript
{
  path: "form-submit",        // URL path: https://n8n.example.com/webhook/form-submit
  httpMethod: "POST",         // GET, POST, PUT, DELETE
  responseMode: "onReceived", // or "lastNode" for custom response
  responseData: "allEntries"  // or "firstEntryJson"
}
```

Critical: data is nested under `$json.body`. See [gotchas.md](./gotchas.md).

```javascript
// ❌ BAD
{{$json.email}}
// ✅ GOOD
{{$json.body.email}}
```

### 2. Validation (Optional but Recommended)

Purpose: verify incoming data before processing.

Options:

- **IF node**: check required fields exist.
- **Code node**: custom validation logic.
- **Stop and Error**: fail gracefully with a message.

Example IF condition:

```javascript
{{$json.body.email}} is not empty AND {{$json.body.name}} is not empty
```

### 3. Transformation

Purpose: map webhook data to the desired format.

Typical nodes: Set, Code.

Set node example:

```javascript
{
  "user_email": "={{$json.body.email}}",
  "user_name":  "={{$json.body.name}}",
  "timestamp":  "={{$now}}"
}
```

### 4. Action

Purpose: do something with the data.

Common actions:

- Store in a database (Postgres, MySQL, MongoDB).
- Send notification (Slack, Email, Discord).
- Call another API (HTTP Request).
- Update an external system (CRM, support ticket).

### 5. Response (if `responseMode: "lastNode"`)

Purpose: send a custom HTTP response.

Webhook Response (Respond to Webhook) node:

```javascript
{
  statusCode: 200,
  headers: { "Content-Type": "application/json" },
  body: { "status": "success", "message": "Form received" }
}
```

## Webhook Data Structure

```json
{
  "headers": {
    "content-type": "application/json",
    "user-agent": "...",
    "x-custom-header": "..."
  },
  "params": {
    "id": "123"
  },
  "query": {
    "token": "abc"
  },
  "body": {
    "name": "John",
    "email": "john@example.com"
  }
}
```

Accessing parts:

```javascript
// Headers
{{$json.headers['content-type']}}
{{$json.headers['x-api-key']}}

// URL path parameters (path like /webhook/form/:id)
{{$json.params.id}}

// Query string
{{$json.query.token}}
{{$json.query.page}}

// Body (most common)
{{$json.body.email}}
{{$json.body.user.name}}
{{$json.body.items[0].price}}
```

## Variants

### Variant: Form Submissions

```
1. Webhook (path: "contact-form", POST)
2. IF (check email and message not empty)
3. Postgres (insert into contacts table)
4. Email (send confirmation to user)
5. Slack (notify team in #leads)
6. Respond to Webhook ({"status": "success"})
```

Data access:

```javascript
Name:    {{$json.body.name}}
Email:   {{$json.body.email}}
Message: {{$json.body.message}}
```

### Variant: Payment Webhooks (Stripe, PayPal)

Signature verification is mandatory.

```javascript
// Code node, Stripe signature verification
const crypto = require('crypto');
const signature = $input.item.headers['stripe-signature'];
const secret = $credentials.stripeWebhookSecret;

const expectedSig = crypto
  .createHmac('sha256', secret)
  .update($input.item.body)
  .digest('hex');

if (signature !== expectedSig) {
  throw new Error('Invalid webhook signature');
}

return $input.item.body;
```

### Variant: Chat Platform (Slack slash command)

```
1. Webhook (path: "slack-command", POST)
2. Code (parse Slack payload: $json.body.text, $json.body.user_id)
3. HTTP Request (fetch data from API)
4. Set (format Slack message)
5. Respond to Webhook (immediate Slack response)
```

Slack data access:

```javascript
Command:    {{$json.body.command}}
Text:       {{$json.body.text}}
User ID:    {{$json.body.user_id}}
Channel ID: {{$json.body.channel_id}}
```

### Variant: GitHub Webhook

```
1. Webhook (path: "github", POST)
2. IF ($json.body.action equals "opened")
3. Set (extract PR title, author, url)
4. Slack (notify #dev-team)
5. Respond to Webhook (200 OK)
```

GitHub data access:

```javascript
Event Type: {{$json.headers['x-github-event']}}
Action:     {{$json.body.action}}
PR Title:   {{$json.body.pull_request.title}}
Author:     {{$json.body.pull_request.user.login}}
URL:        {{$json.body.pull_request.html_url}}
```

### Variant: IoT Device

```
1. Webhook (path: "sensor-data", POST)
2. Set (extract sensor readings)
3. Postgres (insert into sensor_readings)
4. IF (temperature > 80)
5. Email (alert admin)
```

## Authentication and Security

### Query Parameter Token (simple, less secure)

```javascript
// IF node
{{$json.query.token}} equals "your-secret-token"
```

### Header-Based Auth (better)

```javascript
// IF node
{{$json.headers['x-api-key']}} equals "your-api-key"
```

### Signature Verification (best, for Stripe, GitHub, etc.)

```javascript
// Code node
const crypto = require('crypto');
const signature = $input.item.headers['x-signature'];
const secret = $credentials.webhookSecret;

const calculatedSig = crypto
  .createHmac('sha256', secret)
  .update(JSON.stringify($input.item.body))
  .digest('hex');

if (signature !== `sha256=${calculatedSig}`) {
  throw new Error('Invalid signature');
}

return $input.item.body;
```

### IP Whitelist

Restrict access by IP in workflow settings. Useful for internal-only callers.

## Response Modes

### `onReceived` (Default)

Behavior: immediate 200 OK, workflow continues in background.

Use when:

- Long-running workflows.
- Response does not depend on workflow result.
- Fire-and-forget processing.

```javascript
{ responseMode: "onReceived", responseCode: 200 }
```

### `lastNode` (Custom Response)

Behavior: wait for workflow completion, send custom response.

Use when:

- Caller needs the workflow's result.
- Synchronous processing required.
- Form submissions with a confirmation payload.

```javascript
{ responseMode: "lastNode" }
```

Then add a Respond to Webhook node:

```javascript
{
  statusCode: 200,
  headers: { "Content-Type": "application/json" },
  body: { "id": "={{$json.record_id}}", "status": "success" }
}
```

## Error Handling

### Pattern 1: Error Trigger Workflow

```
Main Flow:  Webhook → [nodes...] → Success Response
Error Flow: Error Trigger → Log Error → Slack Alert → Error Response
```

Error response example (if `responseMode: "lastNode"`):

```javascript
{
  statusCode: 500,
  body: { "status": "error", "message": "Processing failed" }
}
```

### Pattern 2: Validation Early Exit

```
Webhook → IF (validate) → [True: Process]
                        → [False: Error Response]
```

False-branch response:

```javascript
{
  statusCode: 400,
  body: { "status": "error", "message": "Invalid data: missing email" }
}
```

### Pattern 3: Continue On Fail

Per-node setting for non-critical actions.

```
Webhook → Database (critical) → Slack (continueOnFail: true)
```

## Testing Webhooks

### Manual Trigger Substitution

Replace Webhook with Manual Trigger during development. Pass test data via a Set node.

### curl

```bash
curl -X POST https://n8n.example.com/webhook/form-submit \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'
```

### Postman / Insomnia

- Create a request collection.
- Test multiple payload shapes.
- Verify response codes and bodies.

### webhook.site

- Use webhook.site to inspect what an upstream service is actually sending before pointing it at n8n.

## Performance Considerations

### Large Payloads

- Default webhook timeout: 120 seconds.
- For large or slow processing, switch to an async queue pattern:

```
Webhook → Queue (Redis/DB) → Respond (immediate)

Separate workflow:
Schedule → Check Queue → Process
```

### High Volume

- Use "Execute Once" mode when processing all items as a batch.
- Add rate limiting.
- Monitor execution times.
- Scale the n8n instance if needed.

### Retries

- Webhook callers typically do not retry automatically.
- Implement retry logic on the caller side.
- Or use a queue pattern for guaranteed processing.

## Complete Worked Example: Stripe Payment Webhook

```
1. Webhook
   - path: "stripe-payment"
   - httpMethod: POST
   - responseMode: lastNode

2. Code (verify Stripe signature)
   - HMAC-SHA256 with $credentials.stripeWebhookSecret
   - Throws on mismatch

3. IF ({{$json.body.type}} equals "checkout.session.completed")
   - True branch continues
   - False branch → Respond to Webhook (200 "ignored event type")

4. Postgres (UPSERT into payments)
   - ON CONFLICT (stripe_session_id) DO UPDATE
   - Captures: amount, customer_email, status, processed_at

5. Send Email (receipt to customer)
   - To: {{$json.body.data.object.customer_details.email}}
   - Subject: Payment received
   - Template-rendered HTML body

6. Slack (#sales channel)
   - "New payment: ${{$json.body.data.object.amount_total / 100}}"

7. Respond to Webhook
   - 200 OK
   - { "received": true }

Error workflow:
  Error Trigger
    → Slack (#alerts)
    → Postgres (insert into webhook_errors)
```

## Workflow Checklist

**Setup**
- Choose a descriptive webhook path.
- Configure the HTTP method (POST most common).
- Choose the response mode (`onReceived` vs `lastNode`).
- Test the webhook URL before connecting upstream services.

**Security**
- Add authentication (token, signature, IP whitelist).
- Validate incoming data.
- Sanitize user input if storing or displaying it.
- Use HTTPS always.

**Data Handling**
- Remember data is under `$json.body`.
- Handle missing fields gracefully.
- Transform data to the desired format.
- Log important data for debugging.

**Error Handling**
- Add an Error Trigger workflow.
- Validate required fields.
- Return appropriate error responses.
- Alert the team on failures.

**Testing**
- Test with curl or Postman.
- Test error scenarios (missing fields, bad signatures).
- Verify response format.
- Monitor first production executions.

## See Also

- [patterns.md](./patterns.md) for retries, idempotency, and queue-based async processing.
- [gotchas.md](./gotchas.md) for response-mode confusion and the `$json.body` trap.
- [configuration.md](./configuration.md) for response modes, paths, and credentials.
- [http-api-integration.md](./http-api-integration.md) for making HTTP requests in response.
- [database-operations.md](./database-operations.md) for writing webhook payloads to a DB.
- [../expressions/](../expressions/) for accessing webhook data correctly.
