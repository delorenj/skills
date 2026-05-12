# Code Node JavaScript: API Reference

Complete symbol-by-symbol reference for the API surface available inside an n8n Code node when the language is set to JavaScript. Organized by symbol, each with shape, semantics, and examples.

For task-oriented recipes, see [patterns.md](./patterns.md). For error symptoms and fixes, see [gotchas.md](./gotchas.md). For the node parameters that govern these behaviors, see [configuration.md](./configuration.md).

---

## Sandbox Restrictions (Read First)

Since n8n v2.0, Code nodes execute inside the `JsTaskRunnerSandbox` task runner. The legacy vm2 sandbox is being removed. Several APIs are deliberately blocked or gated by env vars. Knowing what's blocked saves hours of "why does this throw on activation but not in the editor preview."

### What's always safe

`$input.*`, `$json`, `$node[...]`, `$helpers.httpRequest()` (no auth), `$jmespath()`, `$getWorkflowStaticData()`, `DateTime` (Luxon), and all standard JavaScript globals (`Math`, `JSON`, `Object`, `Array`, `console`, `Buffer`, `URL`, `URLSearchParams`).

### What's blocked unconditionally

```javascript
// BLOCKED, throws UnsupportedFunctionError
await $helpers.httpRequestWithAuthentication.call(this, 'credType', { ... });
await $helpers.requestWithAuthenticationPaginated.call(this, { ... }, 'credType');
```

n8n's source comment: *"these rely on checking the credentials from the current node type (Code Node), and Code Node doesn't have credentials."* The deny-list is compiled-in (`packages/@n8n/task-runner/src/runner-types.ts`); there is no env var to re-enable them. See [gotchas.md](./gotchas.md) Error #6 for the workaround.

### What's conditionally blocked

- `$env.*`, blocked when `N8N_BLOCK_ENV_ACCESS_IN_NODE=true` (common production hardening). See [gotchas.md](./gotchas.md) Error #7.
- `require('crypto')`, `require('fs')`, etc., blocked unless `N8N_RUNNERS_ALLOWED_BUILT_IN_MODULES` (or legacy `NODE_FUNCTION_ALLOW_BUILTIN`) is set to `*` or includes the module.
- External npm packages, blocked unless `N8N_RUNNERS_ALLOWED_EXTERNAL_MODULES` is set **and** the package is installed in the runner image. Effectively rare.

---

## `$input`: Primary Data Source

The canonical way to read items coming into the Code node from the previous node. Always prefer `$input.*` over the legacy `$json` global because it is explicit about scope.

### `$input.all()`

Returns an array of all input items from the previous node. Each item is shaped `{ json: {...}, binary?: {...}, pairedItem?: {...} }`.

```javascript
const allItems = $input.all();
// allItems = [
//   { json: { id: 1, name: "Alice" } },
//   { json: { id: 2, name: "Bob" } }
// ]

console.log(`Received ${allItems.length} items`);
return allItems;
```

When to use:

- Aggregation (sum, count, average)
- Filtering / mapping / sorting across the whole dataset
- Deduplication
- Comparison across items
- Building aggregated reports

Examples by intent:

```javascript
// Filter active items
const active = $input.all().filter(i => i.json.status === 'active');
return active;
```

```javascript
// Reshape every item
const transformed = $input.all().map(item => ({
  json: {
    id: item.json.id,
    fullName: `${item.json.firstName} ${item.json.lastName}`,
    email: item.json.email,
    processedAt: new Date().toISOString()
  }
}));
return transformed;
```

```javascript
// Aggregate
const items = $input.all();
const total = items.reduce((sum, i) => sum + (i.json.amount || 0), 0);
return [{
  json: { total, count: items.length, average: total / items.length }
}];
```

```javascript
// Top N
const topFive = $input.all()
  .sort((a, b) => (b.json.score || 0) - (a.json.score || 0))
  .slice(0, 5);
return topFive.map(i => ({ json: i.json }));
```

```javascript
// Group by category
const grouped = {};
for (const item of $input.all()) {
  const cat = item.json.category || 'Uncategorized';
  (grouped[cat] ||= []).push(item.json);
}
return Object.entries(grouped).map(([category, items]) => ({
  json: { category, items, count: items.length }
}));
```

```javascript
// Deduplicate by id
const seen = new Set();
const unique = [];
for (const item of $input.all()) {
  if (!seen.has(item.json.id)) {
    seen.add(item.json.id);
    unique.push(item);
  }
}
return unique;
```

### `$input.first()`

Returns just the first input item. Built-in safety: does not throw on empty input (the equivalent of `$input.all()[0]` does).

```javascript
const data = $input.first().json;
return [{ json: data }];
```

When to use:

- Previous node returns a single object (typical API response shape)
- Configuration / metadata access
- Initial / first data point
- Form submissions or single-event webhooks

Examples:

```javascript
// Process single API response
const response = $input.first().json;
return [{
  json: {
    userId: response.data.user.id,
    userName: response.data.user.name,
    status: response.status,
    fetchedAt: new Date().toISOString()
  }
}];
```

```javascript
// Reshape a single object
const data = $input.first().json;
return [{
  json: {
    id: data.id,
    contact: { email: data.email, phone: data.phone },
    address: { street: data.street, city: data.city, zip: data.zip }
  }
}];
```

```javascript
// Validate single item
const item = $input.first().json;
const isValid = item.email && item.email.includes('@');
return [{ json: { ...item, valid: isValid, validatedAt: new Date().toISOString() } }];
```

```javascript
// Extract nested data
const response = $input.first().json;
const users = response.data?.users || [];
return users.map(user => ({
  json: {
    id: user.id,
    name: user.profile?.name || 'Unknown',
    email: user.contact?.email || 'no-email'
  }
}));
```

### `$input.item`

The currently iterated item. **Only available in "Run Once for Each Item" mode** (see [configuration.md](./configuration.md)). In "All Items" mode this is `undefined`.

```javascript
// Each Item mode only
const item = $input.item;
return [{
  json: {
    ...item.json,
    processed: true,
    processedAt: new Date().toISOString()
  }
}];
```

When to use:

- Per-item independent API calls
- Per-item validation with different error handling
- Item-specific transformations driven by item properties

Per-item validation example:

```javascript
const data = $input.item.json;
const errors = [];
if (!data.email) errors.push('Email required');
if (!data.name) errors.push('Name required');
if (data.age && data.age < 18) errors.push('Must be 18+');

return [{
  json: {
    ...data,
    valid: errors.length === 0,
    errors: errors.length > 0 ? errors : undefined
  }
}];
```

Conditional processing example:

```javascript
const data = $input.item.json;
if (data.type === 'premium') {
  return [{ json: { ...data, discount: 0.20, tier: 'premium' } }];
}
return [{ json: { ...data, discount: 0.05, tier: 'standard' } }];
```

---

## `$json`: Current Item Shorthand

Shorthand for "the json of the current item." In Each Item mode, this is the current iteration; in All Items mode the meaning is ambiguous (effectively the first item). **Prefer the explicit `$input.first().json` or `$input.item.json` form.**

```javascript
// Works but ambiguous
const value = $json.field;

// Prefer
const value = $input.first().json.field;
```

### Critical: Webhook payloads are nested under `$json.body`

This is the single most common Code-node mistake. The Webhook node wraps **all** incoming data under `body`.

Webhook output structure:

```javascript
{
  headers: { 'content-type': 'application/json', 'user-agent': '...' /* ... */ },
  params: {},
  query: {},
  body: {
    // YOUR DATA IS HERE
    name: 'Alice',
    email: 'alice@example.com',
    message: 'Hello!'
  },
  method: 'POST',
  url: '...'
}
```

Wrong vs right:

```javascript
// WRONG: undefined
const name = $json.name;
const email = $json.email;

// CORRECT
const name = $json.body.name;
const email = $json.body.email;

// CORRECT: extract body once
const webhook = $json.body;
const name = webhook.name;
```

Full webhook example:

```javascript
const webhook = $input.first().json;

return [{
  json: {
    userName: webhook.body.name,
    userEmail: webhook.body.email,
    message: webhook.body.message,

    contentType: webhook.headers['content-type'],
    authenticated: !!webhook.query.api_key,

    method: webhook.method,
    url: webhook.url,

    receivedAt: new Date().toISOString()
  }
}];
```

Common webhook scenarios:

```javascript
// Form submission (POST body)
const formData = $json.body;

// Query parameters (?key=value)
const apiKey = $json.query.api_key;

// HTTP headers
const auth = $json.headers['authorization'];
const sig  = $json.headers['x-signature'];
```

---

## `$node["NodeName"]`: Reference Other Nodes by Name

Read the output of any named upstream node, not just the immediate previous one.

### Correct call syntax

```javascript
// WRONG: .json directly on the node reference
const data = $('HTTP Request').json;

// CORRECT: call .first() then .json
const data = $('HTTP Request').first().json;

// CORRECT: get all items
const allData = $('HTTP Request').all();

// CORRECT: bracket-name form (legacy but still supported)
const webhookData = $node["Webhook"].json;
```

> The `$node["Name"]` form (legacy property access) and `$("Name")` form (modern function form) both work; the modern form is more consistent because it requires `.first()` / `.all()` like `$input`.

### When to use

- Need data from a specific node further upstream than the immediate predecessor
- Combining outputs from multiple branches
- Comparing two snapshots from different nodes

### Examples

```javascript
// Combine multiple sources
const webhook  = $node["Webhook"].json;
const database = $node["Postgres"].json;
const api      = $node["HTTP Request"].json;

return [{
  json: {
    combined: {
      webhook: webhook.body,
      dbRecords: database.length,
      apiResponse: api.status
    },
    processedAt: new Date().toISOString()
  }
}];
```

```javascript
// Compare two snapshots
const oldData = $node["Get Old Data"].json;
const newData = $node["Get New Data"].json;

const changes = {
  added:    newData.filter(n => !oldData.find(o => o.id === n.id)),
  removed:  oldData.filter(o => !newData.find(n => n.id === o.id)),
  modified: newData.filter(n => {
    const old = oldData.find(o => o.id === n.id);
    return old && JSON.stringify(old) !== JSON.stringify(n);
  })
};

return [{
  json: {
    changes,
    summary: {
      added: changes.added.length,
      removed: changes.removed.length,
      modified: changes.modified.length
    }
  }
}];
```

```javascript
// Use whichever branch executed
const ifTrue  = $node["IF True"].json;
const ifFalse = $node["IF False"].json;
const result  = ifTrue || ifFalse || {};
return [{ json: result }];
```

---

## `$helpers`: n8n Helper Object

A small bag of n8n-supplied helpers. Most of it is blocked in the task runner sandbox; one method is genuinely useful.

### `$helpers.httpRequest(options)`

Issue an HTTP request without using the HTTP Request node. **No credential attachment** is possible here; this is for unauthenticated calls, or for cases where the token genuinely arrives as runtime data.

Full option signature:

```javascript
const response = await $helpers.httpRequest({
  method: 'POST',                   // GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
  url: 'https://api.example.com/users',
  headers: {
    'Authorization': 'Bearer token123',
    'Content-Type': 'application/json',
    'User-Agent': 'n8n-workflow'
  },
  body: {
    name: 'John Doe',
    email: 'john@example.com'
  },
  qs: {                              // Query-string parameters
    page: 1,
    limit: 10
  },
  timeout: 10000,                    // Milliseconds; default no timeout
  json: true,                        // Auto-parse JSON response (default true)
  simple: false,                     // Don't throw on 4xx/5xx (default true)
  resolveWithFullResponse: false     // Return only body (default false)
});
```

GET (simple):

```javascript
const users = await $helpers.httpRequest({
  method: 'GET',
  url: 'https://api.example.com/users'
});
return [{ json: { users } }];
```

GET (with query string):

```javascript
const results = await $helpers.httpRequest({
  method: 'GET',
  url: 'https://api.example.com/search',
  qs: { q: 'javascript', page: 1, per_page: 50 }
});
return [{ json: results }];
```

POST (with JSON body):

> For authenticated APIs, prefer an HTTP Request node with a credential attached. Embedding a token in a Code node only works when (a) the token arrives as runtime data from an upstream node, or (b) `$env` access is enabled (see Error #7 in [gotchas.md](./gotchas.md)).

```javascript
const apiToken = $input.first().json.apiToken;  // from a credential-aware upstream node

const newUser = await $helpers.httpRequest({
  method: 'POST',
  url: 'https://api.example.com/users',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiToken}`
  },
  body: {
    name: $json.body.name,
    email: $json.body.email,
    role: 'user'
  }
});
return [{ json: newUser }];
```

PATCH / PUT:

```javascript
const updated = await $helpers.httpRequest({
  method: 'PATCH',
  url: `https://api.example.com/users/${userId}`,
  body: { name: 'Updated Name', status: 'active' }
});
return [{ json: updated }];
```

DELETE:

```javascript
await $helpers.httpRequest({
  method: 'DELETE',
  url: `https://api.example.com/users/${userId}`,
  headers: { 'Authorization': `Bearer ${apiToken}` }
});
return [{ json: { deleted: true, userId } }];
```

Authentication patterns (when the token genuinely flows as data):

```javascript
// Bearer token from a previous node
const response = await $helpers.httpRequest({
  url: 'https://api.example.com/data',
  headers: { 'Authorization': `Bearer ${$input.first().json.token}` }
});
```

```javascript
// API key header from a previous node
const response = await $helpers.httpRequest({
  url: 'https://api.example.com/data',
  headers: { 'X-API-Key': $input.first().json.apiKey }
});
```

```javascript
// Manual Basic Auth
const credentials = Buffer.from(`${username}:${password}`).toString('base64');
const response = await $helpers.httpRequest({
  url: 'https://api.example.com/data',
  headers: { 'Authorization': `Basic ${credentials}` }
});
```

Graceful error handling:

```javascript
try {
  const response = await $helpers.httpRequest({
    method: 'GET',
    url: 'https://api.example.com/users',
    simple: false   // do not throw on 4xx/5xx
  });

  if (response.statusCode >= 200 && response.statusCode < 300) {
    return [{ json: { success: true, data: response.body } }];
  }
  return [{
    json: {
      success: false,
      status: response.statusCode,
      error: response.body
    }
  }];
} catch (error) {
  return [{ json: { success: false, error: error.message } }];
}
```

Full response (headers, status code):

```javascript
const response = await $helpers.httpRequest({
  url: 'https://api.example.com/data',
  resolveWithFullResponse: true
});

return [{
  json: {
    statusCode: response.statusCode,
    headers: response.headers,
    body: response.body,
    rateLimit: response.headers['x-ratelimit-remaining']
  }
}];
```

### `$helpers.httpRequestWithAuthentication` (BLOCKED)

```javascript
// BLOCKED, throws UnsupportedFunctionError
await $helpers.httpRequestWithAuthentication.call(this, 'credType', { ... });
```

No env var re-enables this in the task runner. Use an HTTP Request node with credential, or the sub-workflow delegation pattern. See [gotchas.md](./gotchas.md) Error #6.

### `$helpers.requestWithAuthenticationPaginated` (BLOCKED)

Same story as `httpRequestWithAuthentication`.

---

## `DateTime`: Luxon Date/Time

`DateTime` is the Luxon library, exposed as a global. Use it for any non-trivial date / time work; avoid `Date` for arithmetic.

### Current date/time

```javascript
const now = DateTime.now();
const nowTokyo = DateTime.now().setZone('Asia/Tokyo');
const today = DateTime.now().startOf('day');

return [{
  json: {
    iso: now.toISO(),               // "2025-01-20T15:30:00.000Z"
    formatted: now.toFormat('yyyy-MM-dd HH:mm:ss'),
    unix: now.toSeconds(),
    millis: now.toMillis()
  }
}];
```

### Formatting

```javascript
const now = DateTime.now();

return [{
  json: {
    isoFormat:  now.toISO(),                          // "2025-01-20T15:30:00.000Z"
    sqlFormat:  now.toSQL(),                          // "2025-01-20 15:30:00.000"
    httpFormat: now.toHTTP(),                         // "Mon, 20 Jan 2025 15:30:00 GMT"

    dateOnly:   now.toFormat('yyyy-MM-dd'),           // "2025-01-20"
    timeOnly:   now.toFormat('HH:mm:ss'),             // "15:30:00"
    readable:   now.toFormat('MMMM dd, yyyy'),        // "January 20, 2025"
    compact:    now.toFormat('yyyyMMdd'),             // "20250120"
    withDay:    now.toFormat('EEEE, MMMM dd, yyyy'),  // "Monday, January 20, 2025"
    custom:     now.toFormat('dd/MM/yy HH:mm')        // "20/01/25 15:30"
  }
}];
```

### Parsing

```javascript
const dt1 = DateTime.fromISO('2025-01-20T15:30:00');
const dt2 = DateTime.fromFormat('01/20/2025', 'MM/dd/yyyy');
const dt3 = DateTime.fromSQL('2025-01-20 15:30:00');
const dt4 = DateTime.fromSeconds(1737384600);
const dt5 = DateTime.fromMillis(1737384600000);

return [{ json: { parsed: dt1.toISO() } }];
```

### Arithmetic

```javascript
const now = DateTime.now();

return [{
  json: {
    tomorrow:   now.plus({ days: 1 }).toISO(),
    nextWeek:   now.plus({ weeks: 1 }).toISO(),
    nextMonth:  now.plus({ months: 1 }).toISO(),
    inTwoHours: now.plus({ hours: 2 }).toISO(),

    yesterday:   now.minus({ days: 1 }).toISO(),
    lastWeek:    now.minus({ weeks: 1 }).toISO(),
    lastMonth:   now.minus({ months: 1 }).toISO(),
    twoHoursAgo: now.minus({ hours: 2 }).toISO(),

    in90Days:  now.plus({ days: 90 }).toFormat('yyyy-MM-dd'),
    in6Months: now.plus({ months: 6 }).toFormat('yyyy-MM-dd')
  }
}];
```

### Comparisons and differences

```javascript
const now = DateTime.now();
const target = DateTime.fromISO('2025-12-31');

return [{
  json: {
    isFuture: target > now,
    isPast:   target < now,
    isEqual:  target.equals(now),

    daysUntil:   target.diff(now, 'days').days,
    hoursUntil:  target.diff(now, 'hours').hours,
    monthsUntil: target.diff(now, 'months').months,

    detailedDiff: target.diff(now, ['months', 'days', 'hours']).toObject()
  }
}];
```

### Timezones

```javascript
const now = DateTime.now();

return [{
  json: {
    local:    now.toISO(),

    tokyo:    now.setZone('Asia/Tokyo').toISO(),
    newYork:  now.setZone('America/New_York').toISO(),
    london:   now.setZone('Europe/London').toISO(),
    utc:      now.toUTC().toISO(),

    timezone:        now.zoneName,            // "America/Los_Angeles"
    offset:          now.offset,              // minutes
    offsetFormatted: now.toFormat('ZZ')       // "+08:00"
  }
}];
```

### Start / end of period

```javascript
const now = DateTime.now();

return [{
  json: {
    startOfDay:   now.startOf('day').toISO(),
    endOfDay:     now.endOf('day').toISO(),
    startOfWeek:  now.startOf('week').toISO(),
    endOfWeek:    now.endOf('week').toISO(),
    startOfMonth: now.startOf('month').toISO(),
    endOfMonth:   now.endOf('month').toISO(),
    startOfYear:  now.startOf('year').toISO(),
    endOfYear:    now.endOf('year').toISO()
  }
}];
```

### Weekday / month / year info

```javascript
const now = DateTime.now();

return [{
  json: {
    weekday:      now.weekday,        // 1 = Monday, 7 = Sunday
    weekdayShort: now.weekdayShort,   // "Mon"
    weekdayLong:  now.weekdayLong,    // "Monday"
    isWeekend:    now.weekday > 5,

    month:      now.month,            // 1-12
    monthShort: now.monthShort,       // "Jan"
    monthLong:  now.monthLong,        // "January"

    year:        now.year,
    quarter:     now.quarter,         // 1-4
    daysInMonth: now.daysInMonth      // 28-31
  }
}];
```

---

## `$jmespath(data, expression)`: JSON Querying

Query and transform JSON structures using JMESPath syntax. Useful when the data is deeply nested and a chain of `.map().filter()` would obscure intent.

### Basic queries

```javascript
const data = $input.first().json;

const names      = $jmespath(data, 'users[*].name');
const adults     = $jmespath(data, 'users[?age >= `18`]');
const firstUser  = $jmespath(data, 'users[0]');

return [{ json: { names, adults, firstUser } }];
```

### Advanced

```javascript
const data = $input.first().json;

// Sort, reverse, slice
const top5       = $jmespath(data, 'users | sort_by(@, &score) | reverse(@) | [0:5]');

// Nested field extraction
const emails     = $jmespath(data, 'users[*].contact.email');

// Multi-field projection
const simplified = $jmespath(data, 'users[*].{name: name, email: contact.email}');

// Conditional filter
const premium    = $jmespath(data, 'users[?subscription.tier == `premium`]');

return [{ json: { top5, emails, simplified, premium } }];
```

### Common patterns

```javascript
// Filter and project
const filtered = $jmespath(data, 'products[?price > `100`].{name: name, price: price}');

// Aggregate functions
const totalPrice = $jmespath(data, 'sum(products[*].price)');
const maxPrice   = $jmespath(data, 'max(products[*].price)');
const numProducts = $jmespath(data, 'length(products)');

// Nested filtering
const inStock    = $jmespath(data, 'categories[*].products[?inStock == `true`]');
```

---

## `$getWorkflowStaticData(scope)`: Persistent Storage

Read/write a JSON object that persists across workflow executions. Two scopes:

- `'global'`: persists across all executions of the workflow
- `'node'`: persists only for the current node

Critical use case: accumulating data across iterations of a SplitInBatches loop (see [patterns.md](./patterns.md)).

### Basic usage

```javascript
const staticData = $getWorkflowStaticData('global');

if (!staticData.counter) {
  staticData.counter = 0;
}

staticData.counter++;

return [{ json: { executionCount: staticData.counter } }];
```

### Use case: rate limiting

```javascript
const staticData = $getWorkflowStaticData('global');
const now = Date.now();

if (!staticData.lastRun) {
  staticData.lastRun = now;
  staticData.runCount = 1;
} else {
  const timeSinceLastRun = now - staticData.lastRun;
  if (timeSinceLastRun < 60000) {
    return [{ json: { error: 'Rate limit: wait 1 minute between runs' } }];
  }
  staticData.lastRun = now;
  staticData.runCount++;
}

return [{ json: { allowed: true, totalRuns: staticData.runCount } }];
```

### Use case: track last-processed id

```javascript
const staticData = $getWorkflowStaticData('global');
const current = $input.all();

const lastId = staticData.lastProcessedId || 0;
const newItems = current.filter(i => i.json.id > lastId);

if (newItems.length > 0) {
  staticData.lastProcessedId = Math.max(...newItems.map(i => i.json.id));
}

return newItems;
```

### Use case: accumulate results across executions

```javascript
const staticData = $getWorkflowStaticData('global');

if (!staticData.accumulated) {
  staticData.accumulated = [];
}

const current = $input.all().map(i => i.json);
staticData.accumulated.push(...current);

return [{
  json: {
    currentBatch: current.length,
    totalAccumulated: staticData.accumulated.length,
    allData: staticData.accumulated
  }
}];
```

---

## `$env`: Environment Variables (Conditionally Blocked)

Read environment variables exposed to the n8n process. **Gated by `N8N_BLOCK_ENV_ACCESS_IN_NODE`**. When set to `true` (common production hardening) any reference throws `ReferenceError: $env is not defined`. Since you cannot tell from inside the Code node, **do not rely on `$env` for portable skills.** Treat secrets as a credential concern (HTTP Request node with credential attached).

```javascript
// Throws if N8N_BLOCK_ENV_ACCESS_IN_NODE=true
const apiKey = $env.API_KEY;
```

See [gotchas.md](./gotchas.md) Error #7 for safe alternatives.

---

## Standard JavaScript Globals

All standard JavaScript built-ins are available with no allowlist.

### `Math`

```javascript
return [{
  json: {
    rounded: Math.round(3.7),       // 4
    floor:   Math.floor(3.7),       // 3
    ceil:    Math.ceil(3.2),        // 4

    max:     Math.max(1, 5, 3, 9, 2),  // 9
    min:     Math.min(1, 5, 3, 9, 2),  // 1

    random:    Math.random(),                  // 0-1
    randomInt: Math.floor(Math.random() * 100),

    abs:  Math.abs(-5),    // 5
    sqrt: Math.sqrt(16),   // 4
    pow:  Math.pow(2, 3)   // 8
  }
}];
```

### `JSON`

```javascript
const parsed      = JSON.parse('{"name": "John", "age": 30}');
const stringified = JSON.stringify({ name: 'John', age: 30 });
const pretty      = JSON.stringify({ name: 'John', age: 30 }, null, 2);

return [{ json: { parsed, stringified, pretty } }];
```

### `console`

Debug output goes to the browser DevTools console (F12) of whoever is viewing the workflow editor, or to the n8n server logs in production.

```javascript
console.log('Processing items:', $input.all().length);
console.log('First item:', $input.first().json);
console.error('Error message');
console.warn('Warning message');
console.info('Info message');

return [{ json: { processed: true } }];
```

### `Object`

```javascript
const obj = { name: 'John', age: 30, city: 'NYC' };

return [{
  json: {
    keys:    Object.keys(obj),       // ["name", "age", "city"]
    values:  Object.values(obj),     // ["John", 30, "NYC"]
    entries: Object.entries(obj),    // [["name", "John"], ...]

    hasName: 'name' in obj,

    merged:  Object.assign({}, obj, { country: 'USA' })
  }
}];
```

### `Array`

```javascript
const arr = [1, 2, 3, 4, 5];

return [{
  json: {
    mapped:   arr.map(x => x * 2),         // [2, 4, 6, 8, 10]
    filtered: arr.filter(x => x > 2),      // [3, 4, 5]
    reduced:  arr.reduce((s, x) => s + x, 0), // 15
    some:     arr.some(x => x > 3),        // true
    every:    arr.every(x => x > 0),       // true
    find:     arr.find(x => x > 3),        // 4
    includes: arr.includes(3),             // true
    joined:   arr.join(', ')               // "1, 2, 3, 4, 5"
  }
}];
```

---

## Node.js Modules

### `Buffer` (global, always available)

```javascript
// Base64 encode
const encoded = Buffer.from('Hello World').toString('base64');

// Base64 decode
const decoded = Buffer.from(encoded, 'base64').toString();

// Hex
const hex = Buffer.from('Hello').toString('hex');

return [{ json: { encoded, decoded, hex } }];
```

### `URL` / `URLSearchParams` (globals, always available)

```javascript
const url = new URL('https://example.com/path?param1=value1&param2=value2');

const params = new URLSearchParams({
  search: 'query',
  page: 1,
  limit: 10
});

return [{
  json: {
    host:         url.host,
    pathname:     url.pathname,
    search:       url.search,
    queryString:  params.toString()  // "search=query&page=1&limit=10"
  }
}];
```

### `require('crypto')` and other built-ins (GATED)

`require('crypto')` only works when `N8N_RUNNERS_ALLOWED_BUILT_IN_MODULES` (or legacy `NODE_FUNCTION_ALLOW_BUILTIN`) is set to `*` or a comma-list including `crypto`. On default installs `require()` throws `Cannot find module 'crypto'`.

```javascript
// Works only when the runner allowlist includes 'crypto'
const crypto = require('crypto');

const sha256 = crypto.createHash('sha256').update('my secret text').digest('hex');
const md5    = crypto.createHash('md5').update('my text').digest('hex');
const random = crypto.randomBytes(16).toString('hex');

return [{ json: { sha256, md5, random } }];
```

If you cannot guarantee the allowlist, move hashing/crypto out of the Code node, or compute it in an upstream service.

### External npm packages

Blocked unless `N8N_RUNNERS_ALLOWED_EXTERNAL_MODULES` lists the package **and** it is installed in the runner image. Effectively rare. Do not rely on:

- `axios` (use `$helpers.httpRequest`)
- `lodash` (use native array methods)
- `moment` (use `DateTime`/Luxon)
- `request` (deprecated upstream anyway)

---

## What's NOT Available

Authentication helpers, unconditionally:

- `$helpers.httpRequestWithAuthentication`
- `$helpers.requestWithAuthenticationPaginated`

Conditionally blocked:

- `$env.*`, when `N8N_BLOCK_ENV_ACCESS_IN_NODE=true`
- `require('crypto' | 'fs' | ...)`, unless `N8N_RUNNERS_ALLOWED_BUILT_IN_MODULES` includes them

External npm packages (rare; only when both allowlisted **and** installed):

- `axios`, `lodash`, `moment`, `request`, and so on

Workarounds:

| Need | Workaround |
|------|------------|
| HTTP with credential auth | HTTP Request node with credential attached, or sub-workflow pattern |
| Secrets | Arrive as data from an upstream HTTP Request / credential-aware node |
| Hashing/crypto | Do it in an external service the workflow calls, or update the instance allowlist |
| Date/time library | Use the built-in `DateTime` (Luxon) |
| HTTP library | Use built-in `$helpers.httpRequest` |
| Utility library (lodash) | Use native `Array` / `Object` methods |

---

## Symbol Cheat Sheet

| Symbol | Type | Use For |
|--------|------|---------|
| `$input.all()` | array | All input items, aggregation |
| `$input.first()` | object | First input item (safe on empty input) |
| `$input.item` | object | Current item (Each Item mode only) |
| `$json` | object | Shorthand for current item json (prefer explicit `$input` form) |
| `$json.body` | object | Webhook payload nesting (critical) |
| `$node["Name"].json` / `$("Name").first().json` | object | Output of a named upstream node |
| `$helpers.httpRequest(opts)` | function | Make HTTP request (no auth) |
| `$helpers.httpRequestWithAuthentication` | function | BLOCKED in sandbox |
| `$jmespath(data, expr)` | function | JMESPath query against JSON |
| `$getWorkflowStaticData(scope)` | function | Persistent storage (`'global'` or `'node'`) |
| `$env.VAR` | object | Env var access, gated by `N8N_BLOCK_ENV_ACCESS_IN_NODE` |
| `DateTime` | global | Luxon date/time |
| `Math`, `JSON`, `Object`, `Array`, `console` | global | Standard JavaScript |
| `Buffer`, `URL`, `URLSearchParams` | global | Always available |
| `require('crypto')` | function | Gated by `N8N_RUNNERS_ALLOWED_BUILT_IN_MODULES` |

---

## See Also

- [README.md](./README.md), [patterns.md](./patterns.md), [gotchas.md](./gotchas.md), [configuration.md](./configuration.md) (this topic)
- [../code-python/](../code-python/) for the Python flavor (different API surface)
- [../expressions/](../expressions/) for `{{ }}` expression syntax in other nodes
- [../node-configuration/](../node-configuration/) for HTTP Request node and credentials (the canonical alternative to in-Code auth)
- [../workflow-patterns/](../workflow-patterns/) for sub-workflow / SplitInBatches patterns that pair with this API
- Luxon docs (powers `DateTime`): https://moment.github.io/luxon/
- JMESPath docs (powers `$jmespath`): https://jmespath.org/
- n8n built-in reference: https://docs.n8n.io/code-examples/methods-variables-reference/
