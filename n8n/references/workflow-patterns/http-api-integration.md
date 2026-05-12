# HTTP API Integration Pattern

Cross-refs: see [patterns.md](./patterns.md) for batch processing, retries, and idempotency; see [gotchas.md](./gotchas.md) for credential, error-handling, and hardcoded-URL traps.

**Use Case**: Fetch data from REST APIs, transform it, and use it in workflows.

## Pattern Structure

```
Trigger → HTTP Request → [Transform] → [Action] → [Error Handler]
```

**Key Characteristic**: External data fetching with error handling.

## Use Cases

- Periodic data fetch from external services (GitHub, Jira, weather APIs, analytics).
- API-to-API bridges (CRM A to CRM B).
- Data enrichment (Clearbit, Hunter, FullContact).
- Health checks and uptime monitoring.
- Batch processing of paginated datasets.

## Core Components

### 1. Trigger

- **Schedule**: periodic fetching (most common).
- **Webhook**: triggered by an external event.
- **Manual**: on-demand execution.

### 2. HTTP Request Node

Purpose: call external REST APIs.

```javascript
{
  method: "GET",
  url: "https://api.example.com/users",
  authentication: "predefinedCredentialType",
  sendQuery: true,
  queryParameters: {
    "page": "={{$json.page}}",
    "limit": "100"
  },
  sendHeaders: true,
  headerParameters: {
    "Accept": "application/json",
    "X-API-Version": "v1"
  }
}
```

### 3. Response Processing

```
HTTP Request → Code (parse) → Set (map fields) → Action
```

### 4. Action

- Store in a database.
- Send to another API.
- Create notifications.
- Update a spreadsheet.

### 5. Error Handler

```
Error Trigger → Log Error → Notify Admin → Retry Logic (optional)
```

## Variants

### Variant: Data Fetching and Storage (GitHub issues)

```
1. Schedule (every hour)
2. HTTP Request
   - Method: GET
   - URL: https://api.github.com/repos/owner/repo/issues
   - Auth: Bearer Token
   - Query: state=open
3. Code (filter by labels)
4. Set (map to database schema)
5. Postgres (upsert issues)
```

```javascript
// Code node, filter issues
const issues = $input.all();
return issues
  .filter(item => item.json.labels.some(l => l.name === 'bug'))
  .map(item => ({
    json: {
      id: item.json.id,
      title: item.json.title,
      created_at: item.json.created_at
    }
  }));
```

### Variant: API to API (Jira to Slack)

```
1. Schedule (every 15 minutes)
2. HTTP Request (GET Jira tickets updated today)
3. IF (check if tickets exist)
4. Set (format for Slack)
5. HTTP Request (POST to Slack webhook)
```

### Variant: Data Enrichment

```
1. Postgres (SELECT new contacts)
2. Code (extract company domains)
3. HTTP Request (Clearbit enrichment per domain)
4. Set (combine contact + company data)
5. Postgres (UPDATE contacts)
```

### Variant: Monitoring and Alerting

```
1. Schedule (every 5 minutes)
2. HTTP Request (GET /health endpoint)
3. IF (status !== 200 OR response time > 2000ms)
4. Slack (alert #ops-team)
5. PagerDuty (create incident)
```

### Variant: Batch Processing

```
1. Manual Trigger
2. HTTP Request (GET /api/users?limit=1000)
3. Split In Batches (100 items per batch)
4. HTTP Request (POST /api/process for each batch)
5. Wait (2 seconds between batches; rate limiting)
6. Loop (back to step 4 until done)
```

## Authentication Methods

### None (Public APIs)

```javascript
{ authentication: "none" }
```

### Bearer Token (Most Common)

```javascript
{
  authentication: "predefinedCredentialType",
  nodeCredentialType: "httpHeaderAuth",
  headerAuth: {
    name: "Authorization",
    value: "Bearer YOUR_TOKEN"
  }
}
```

### API Key (Header)

```javascript
{
  sendHeaders: true,
  headerParameters: { "X-API-Key": "={{$credentials.apiKey}}" }
}
```

### API Key (Query)

```javascript
{
  sendQuery: true,
  queryParameters: { "api_key": "={{$credentials.apiKey}}" }
}
```

### Basic Auth

```javascript
{
  authentication: "predefinedCredentialType",
  nodeCredentialType: "httpBasicAuth"
}
```

### OAuth2

Credential needs: Authorization URL, Token URL, Client ID, Client Secret, Scopes.

```javascript
{
  authentication: "predefinedCredentialType",
  nodeCredentialType: "oAuth2Api"
}
```

## Handling API Responses

### Success Response (2xx)

```javascript
// Entire response
{{$json}}

// Specific fields
{{$json.data.id}}
{{$json.results[0].name}}
```

### Pagination: Offset-Based

```
1. Set (initialize: page=1, has_more=true)
2. HTTP Request (GET /api/items?page={{$json.page}})
3. Code (check if more pages)
4. IF (has_more === true)
   → Set (increment page) → Loop to step 2
```

```javascript
// Code node, check pagination
const items = $input.first().json;
const currentPage = $json.page || 1;
return [{
  json: {
    items: items.results,
    page: currentPage + 1,
    has_more: items.next !== null
  }
}];
```

### Pagination: Cursor-Based

```
1. HTTP Request (GET /api/items)
2. Code (extract next_cursor)
3. IF (next_cursor exists)
   → Set (cursor={{$json.next_cursor}}) → Loop to step 1
```

### Pagination: Link Header

```javascript
// Code node, parse Link header
const linkHeader = $input.first().json.headers['link'];
const hasNext = linkHeader && linkHeader.includes('rel="next"');
return [{
  json: {
    items: $input.first().json.body,
    has_next: hasNext,
    next_url: hasNext ? parseNextUrl(linkHeader) : null
  }
}];
```

### Error Responses (4xx, 5xx)

```javascript
{
  continueOnFail: true,
  ignoreResponseCode: true
}
```

Then branch on the error:

```
HTTP Request (continueOnFail: true)
  → IF (check error)
    → [Success Path]
    → [Error Path] → Log → Retry or Alert
```

IF condition:

```javascript
{{$json.error}} is empty
// OR
{{$json.statusCode}} < 400
```

## Rate Limiting

### Pattern 1: Wait Between Requests

```
Split In Batches (1 item per batch)
  → HTTP Request
  → Wait (1 second)
  → Loop
```

### Pattern 2: Exponential Backoff

```javascript
// Code node
const maxRetries = 3;
let retryCount = $json.retryCount || 0;

if ($json.error && retryCount < maxRetries) {
  const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
  return [{
    json: { ...$json, retryCount: retryCount + 1, waitTime: delay }
  }];
}
```

### Pattern 3: Respect Rate Limit Headers

```javascript
// Code node
const headers = $input.first().json.headers;
const remaining = parseInt(headers['x-ratelimit-remaining'] || '999');
const resetTime = parseInt(headers['x-ratelimit-reset'] || '0');

if (remaining < 10) {
  const now = Math.floor(Date.now() / 1000);
  const waitSeconds = resetTime - now;
  return [{ json: { shouldWait: true, waitSeconds: Math.max(waitSeconds, 0) } }];
}

return [{ json: { shouldWait: false } }];
```

## Request Configurations

### GET

```javascript
{
  method: "GET",
  url: "https://api.example.com/users",
  sendQuery: true,
  queryParameters: { "page": "1", "limit": "100", "filter": "active" }
}
```

### POST (JSON Body)

```javascript
{
  method: "POST",
  url: "https://api.example.com/users",
  sendBody: true,
  bodyParametersJson: JSON.stringify({
    name: "={{$json.name}}",
    email: "={{$json.email}}",
    role: "user"
  })
}
```

### POST (Form Data)

```javascript
{
  method: "POST",
  url: "https://api.example.com/upload",
  sendBody: true,
  bodyParametersUi: {
    parameter: [
      { name: "file", value: "={{$json.fileData}}" },
      { name: "filename", value: "={{$json.filename}}" }
    ]
  },
  sendHeaders: true,
  headerParameters: { "Content-Type": "multipart/form-data" }
}
```

### PUT / PATCH (Update)

```javascript
{
  method: "PATCH",
  url: "https://api.example.com/users/={{$json.userId}}",
  sendBody: true,
  bodyParametersJson: JSON.stringify({
    status: "active",
    last_updated: "={{$now}}"
  })
}
```

### DELETE

```javascript
{
  method: "DELETE",
  url: "https://api.example.com/users/={{$json.userId}}"
}
```

## Error Handling Patterns

### Retry on Failure

```
HTTP Request (continueOnFail: true)
  → IF (error occurred)
    → Wait (5 seconds)
    → HTTP Request (retry)
```

### Fallback API

```
HTTP Request (Primary, continueOnFail: true)
  → IF (failed)
    → HTTP Request (Fallback API)
```

### Error Trigger Workflow

```
Main: HTTP Request → Process Data

Error Workflow:
  Error Trigger
    → Set (extract error details)
    → Slack (alert team)
    → Database (log error)
```

### Circuit Breaker

```javascript
// Code node
const failures = $json.recentFailures || 0;
const threshold = 5;

if (failures >= threshold) {
  throw new Error('Circuit breaker open, too many failures');
}

return [{ json: { canProceed: true } }];
```

## Response Transformation

### Extract Nested Data

```javascript
// Code node
const response = $input.first().json;
return response.data.items.map(item => ({
  json: {
    id: item.id,
    name: item.attributes.name,
    email: item.attributes.contact.email
  }
}));
```

### Flatten Arrays

```javascript
// Code node, flatten nested array
const items = $input.all();
const flattened = items.flatMap(item =>
  item.json.results.map(result => ({
    json: { parent_id: item.json.id, ...result }
  }))
);
return flattened;
```

### Combine Multiple Responses

```
HTTP Request 1 (users)
  → Set (store users)
  → HTTP Request 2 (orders for each user)
  → Merge (combine users + orders)
```

## Testing and Debugging

1. **Test with Manual Trigger**. Replace Schedule with Manual Trigger for testing.
2. **Use Postman / Insomnia first**. Test the API outside n8n; understand response structure; verify auth.
3. **Log responses**. Add a Code node that logs `JSON.stringify($input.first().json, null, 2)`.
4. **Check execution data** in n8n UI: headers, body, status code, structure.
5. **Use binary response format** for file downloads:

```javascript
{
  method: "GET",
  url: "https://api.example.com/download/file.pdf",
  responseFormat: "file",
  outputPropertyName: "data"
}
```

## Performance Optimization

### Parallel Requests via SplitInBatches

```
Set (create array of IDs)
  → Split In Batches (10 items per batch)
  → HTTP Request (processes all 10 in parallel)
  → Loop
```

### Caching

```
IF (check cache exists)
  → [Cache Hit] → Use cached data
  → [Cache Miss] → HTTP Request → Store in cache
```

### Conditional Fetching

```
HTTP Request (GET with If-Modified-Since header)
  → IF (status === 304) → Use existing data
  → IF (status === 200) → Process new data
```

### Batch API Calls (if supported)

```javascript
{
  method: "POST",
  url: "https://api.example.com/batch",
  bodyParametersJson: JSON.stringify({
    requests: $json.items.map(item => ({
      method: "GET",
      url: `/users/${item.id}`
    }))
  })
}
```

## Complete Worked Example: Daily GitHub Issue Sync to Postgres

```
1. Schedule Trigger
   - mode: cron
   - expression: "0 6 * * *"     (daily at 6 AM)
   - timezone: America/New_York

2. Set (initialize pagination)
   - page: 1
   - since: ={{$now.minus({days: 1}).toISO()}}

3. HTTP Request
   - method: GET
   - url: https://api.github.com/repos/myorg/myrepo/issues
   - authentication: predefinedCredentialType / httpHeaderAuth (Bearer)
   - sendQuery: true
   - queryParameters:
       state: open
       since: ={{$json.since}}
       page: ={{$json.page}}
       per_page: 100
   - continueOnFail: true

4. IF ({{$json.error}} is empty)
   - True branch continues
   - False branch → Slack (#alerts) → end

5. Code (parse + check pagination)
   - Extract issues from response
   - Detect Link header rel="next"
   - Push to staticData accumulator

6. IF (more pages exist)
   - True → Set (page++) → loop to step 3
   - False → continue

7. Postgres (upsert)
   - operation: executeQuery
   - query: INSERT INTO issues ... ON CONFLICT (id) DO UPDATE SET ...
   - parameters: from accumulator

8. Slack (#dev-team)
   - "Synced {{$json.count}} GitHub issues at {{$now}}"

Error workflow:
  Error Trigger → Slack (#alerts) → Postgres (workflow_errors log)
```

## Workflow Checklist

**Planning**
- Test the API with Postman or curl first.
- Understand the response structure.
- Check rate limits.
- Review the authentication method.
- Plan error handling.

**Implementation**
- Use credentials, never hardcode.
- Configure the proper HTTP method.
- Set correct headers (`Content-Type`, `Accept`).
- Handle pagination if needed.
- Add query parameters properly.

**Error Handling**
- Set `continueOnFail: true` where appropriate.
- Check response status codes.
- Implement retry logic.
- Add an Error Trigger workflow.
- Alert on failures.

**Performance**
- Use batching for large datasets.
- Add rate limiting if needed.
- Consider caching.
- Test with production-like load.

**Security**
- HTTPS only.
- Secrets in credentials, not parameters.
- Validate API responses.
- Use environment variables for base URLs.

## See Also

- [patterns.md](./patterns.md) for batch processing, retries, rate limiting, idempotency.
- [gotchas.md](./gotchas.md) for hardcoded-URL, credential, and unbounded-response failures.
- [configuration.md](./configuration.md) for credential setup (OAuth2, Bearer, etc.).
- [webhook-processing.md](./webhook-processing.md) for receiving HTTP requests.
- [database-operations.md](./database-operations.md) for storing fetched API data.
- [scheduled-tasks.md](./scheduled-tasks.md) for periodic API sync triggers.
