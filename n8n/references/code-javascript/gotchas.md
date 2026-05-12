# Code Node JavaScript: Gotchas

The most common Code-node errors, their causes, and their fixes, in the four-part structure: symptom, cause, solution, bad/good code pair. Frequencies cited where known come from n8n validation telemetry.

For the API surface these errors are about, see [api.md](./api.md). For correct patterns, see [patterns.md](./patterns.md).

---

## Error #1: Empty Code or Missing Return Statement

> "Code cannot be empty" or "Code must return data"

**Cause**: The Code node has no `return` statement, or one branch of the code reaches the end without returning. n8n flags this as the most common Code-node failure (about 38% of all validation failures).

**Solution**: Ensure every code path produces a `return` of an array of `{json}`-wrapped objects, including the empty-input case (`return [];`).

```javascript
// BAD: code executes but never returns
const items = $input.all();
for (const item of items) {
  console.log(item.json.name);
}
// forgot to return

// BAD: only one branch returns
const items = $input.all();
if (items.length === 0) {
  return [];
}
const processed = items.map(item => ({ json: item.json }));
// forgot to return processed

// GOOD: every path returns
const items = $input.all();
if (items.length === 0) return [];
return items.map(item => ({ json: { ...item.json, processed: true } }));
```

---

## Error #2: Expression Syntax Confusion

> "Unexpected token" / "Expression syntax is not valid in Code nodes" / literal strings like `{{ $json.field }}` appearing in output

**Cause**: n8n has two distinct syntaxes. Expression syntax `{{ ... }}` is for **other nodes** (Set, IF, HTTP Request URL fields, etc.). **Inside a Code node, you write plain JavaScript.** Using `{{ }}` inside a Code node either fails to parse or is treated as a literal string. This accounts for about 8% of validation failures.

**Solution**: Drop the `{{ }}` braces. Use direct variable access (`$json.field`, `$input.first().json.field`) and JavaScript template literals (backticks) for interpolation.

```javascript
// BAD: n8n expression syntax inside Code node
const userName = "{{ $json.name }}";          // literal string, not the value
const value    = "{{ $now.toFormat('yyyy-MM-dd') }}";

// GOOD: plain JavaScript
const userName = $json.name;
const value    = DateTime.now().toFormat('yyyy-MM-dd');

// GOOD: template literal for interpolation
const greeting = `Hello, ${$json.name}! Your email is ${$json.email}`;
```

Quick conversion guide:

| Other-node expression | Code-node JavaScript |
|-----------------------|----------------------|
| `{{ $json.field }}` | `$json.field` |
| `{{ $now }}` | `new Date().toISOString()` or `DateTime.now()` |
| `{{ $node['HTTP Request'].json.data }}` | `$node["HTTP Request"].json.data` |
| `` `{{ $json.firstName }} {{ $json.lastName }}` `` | `` `${$json.firstName} ${$json.lastName}` `` |

---

## Error #3: Incorrect Return Wrapper Format

> "Return value must be an array of objects" / "Each item must have a json property"

**Cause**: The Code node enforces a strict output shape: an **array** of objects, each with a **`json` property**. Returning a bare object, an array of raw objects, a plain string, or a `{data: ...}` wrapper instead of `{json: ...}` all break this contract. About 5% of validation failures.

**Solution**: Always return `[{ json: {...} }]` or `[]`. Use `.map(item => ({ json: ... }))` when transforming arrays.

```javascript
// BAD: object instead of array
return { json: { result: 'success' } };

// BAD: array without json wrapper
return [{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }];

// BAD: plain value
return 'processed';

// BAD: wrong wrapper key
return [{ data: { result: 'success' } }];

// GOOD: single result
return [{ json: { result: 'success', timestamp: new Date().toISOString() } }];

// GOOD: multiple results
return [
  { json: { id: 1, name: 'Alice' } },
  { json: { id: 2, name: 'Bob' } }
];

// GOOD: transformed array
return $input.all().map(item => ({
  json: { id: item.json.id, name: item.json.name, processed: true }
}));

// GOOD: empty result
return [];
```

Return-format checklist:

- Result is an array `[...]`
- Each element has a `json` property
- Structure matches `[{ json: {...} }]` (or `[{ json: {...} }, { json: {...} }]`)
- No `{ json: {...} }` without the surrounding array
- No `[{...}]` without the `json` key

---

## Error #4: Unmatched Expression Brackets

> "Unmatched expression brackets" on save / parsing error / code looks correct but fails validation

**Cause**: Quote and bracket imbalance, usually triggered by single quotes inside single-quoted strings, unescaped backslashes, or multi-line strings built with the wrong quote style. About 6% of validation failures.

**Solution**: Prefer template literals (backticks) for multi-line and quote-heavy strings. Escape backslashes (`\\`) and embedded quotes (`\'` / `\"`) when sticking with normal string literals.

```javascript
// BAD: single quote inside single-quoted string
const message = 'It's a nice day';

// BAD: HTML with double quotes inside double-quoted multi-line
const html = "
  <div class="container">
    <p>Hello</p>
  </div>
";

// GOOD: alternate quote style
const message1 = "It's a nice day";

// GOOD: escape
const message2 = 'It\'s a nice day';

// GOOD: template literals handle multi-line and embedded quotes
const html = `
  <div class="${className}">
    <h1>${title}</h1>
    <p>${content}</p>
  </div>
`;

// GOOD: escape backslashes for Windows paths
const path = "C:\\Users\\Documents\\file.txt";
```

Escaping reference:

| Character | Inside same-quote string | Example |
|-----------|--------------------------|---------|
| Single quote in single-quoted | `\'` | `'It\'s working'` |
| Double quote in double-quoted | `\"` | `"She said \"hello\""` |
| Backslash | `\\` | `"C:\\path"` |
| Newline | `\n` | `"Line 1\nLine 2"` |
| Tab | `\t` | `"Col1\tCol2"` |

---

## Error #5: Missing Null Checks / Undefined Access

> "Cannot read property 'X' of undefined" / "Cannot read property 'X' of null"

**Cause**: Direct nested-property access without verifying the path exists, or array index access without a length check. Especially common with webhook payloads (where the path is `$json.body.*`, not `$json.*`) and with optional API response fields.

**Solution**: Use optional chaining (`?.`), nullish coalescing (`??`), guard clauses, or try/catch. For arrays, prefer `$input.first()` (built-in empty-safety) over `$input.all()[0]`.

```javascript
// BAD: crashes if user is missing
const email = item.json.user.email;

// BAD: assumes array is non-empty
const firstId = $input.all()[0].json.id;

// BAD: webhook nesting forgotten (very common)
const name = $json.name;  // undefined; data is under .body

// GOOD: optional chaining
const email = item.json?.user?.email ?? 'no-email@example.com';

// GOOD: guard clause
const items = $input.all();
if (items.length === 0) return [];
const firstId = items[0].json.id;

// GOOD: $input.first() handles empty input safely
const data = $input.first().json;

// GOOD: explicit webhook nesting
const name = $json.body?.name ?? 'Unknown';

// GOOD: try/catch around risky operations
try {
  const email = item.json.user.email.toLowerCase();
  return [{ json: { email } }];
} catch (error) {
  return [{ json: { error: 'Invalid user data', details: error.message } }];
}
```

Webhook safety in particular:

```javascript
// BAD
const name  = $json.body.user.name;
const email = $json.body.user.email;

// SAFE: step-by-step defaults
const body  = $json.body || {};
const user  = body.user || {};
const name  = user.name  || 'Unknown';
const email = user.email || 'no-email';

// BETTER: optional chaining
const name2  = $json.body?.user?.name  ?? 'Unknown';
const email2 = $json.body?.user?.email ?? 'no-email';
```

---

## Error #6: UnsupportedFunctionError (Auth Helpers Blocked)

> `UnsupportedFunctionError: The function "helpers.httpRequestWithAuthentication" is not supported in the Code Node`

**Cause**: Since n8n v2.0, Code nodes run inside the `JsTaskRunnerSandbox` task runner, which deliberately blocks `$helpers.httpRequestWithAuthentication` and `$helpers.requestWithAuthenticationPaginated`. The legacy vm2 sandbox used to bind them; that's why older tutorials and forum posts show the helpers "working." n8n's source comment: *"these rely on checking the credentials from the current node type (Code Node), and Code Node doesn't have credentials."* The deny-list is compiled-in, so **no env var re-enables it**.

**Solution**: Don't authenticate from inside the Code node. Use an **HTTP Request node** with a credential attached (the canonical pattern), or build a **sub-workflow** where a child HTTP Request node holds the credential. If the token genuinely arrives as runtime data, you can use `$helpers.httpRequest` with a manual `Authorization` header.

```javascript
// BAD: blocked in the task runner sandbox
const data = await $helpers.httpRequestWithAuthentication.call(
  this,
  'baseLinkerApi',
  { url: 'https://api.example.com/things', method: 'POST' }
);

// GOOD (Option A): replace Code node with HTTP Request node
//   - Credential attached natively
//   - Expressions in URL/body/headers
//   - Pagination supported

// GOOD (Option B): sub-workflow delegation
//   Parent Code node prepares the payload
return $input.all().map(i => ({
  json: {
    url:    'https://api.example.com/things',
    method: 'POST',
    body:   { sku: i.json.sku }
  }
}));
//   then Execute Workflow → child with Execute Workflow Trigger
//   → HTTP Request node using ={{ $json.url }}, ={{ $json.body }},
//   with the credential attached.

// GOOD (Option C): token as runtime data (from an upstream credential-aware node)
const token = $('Get Token').first().json.access_token;
const data = await $helpers.httpRequest({
  url: 'https://api.example.com/data',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

Decision guide:

| Need | Use |
|------|-----|
| Single authenticated API call | HTTP Request node directly |
| Many API calls plus pre/post processing | Sub-workflow pattern (Option B) |
| Token already in the data flow | Manual `$helpers.httpRequest()` with header |
| `httpRequestWithAuthentication` from Code node | Does not work; pick A, B, or C |

---

## Error #7: `$env` is not defined

> `ReferenceError: $env is not defined` / works on dev instance, throws in production

**Cause**: `$env` access is gated by the **`N8N_BLOCK_ENV_ACCESS_IN_NODE`** environment variable. When set to `true` (an increasingly common production hardening), `$env` is removed from the Code node sandbox entirely. The Code node has no way to detect whether the flag is set.

**Solution**: Treat secrets as a **credential concern**, not a Code-node concern. Route them through HTTP Request node credentials or the External Secrets integration (`$secrets`) if your edition supports it. Use a **Set** node at the top of the workflow for non-secret configuration constants.

```javascript
// BAD: throws if N8N_BLOCK_ENV_ACCESS_IN_NODE=true
const apiKey = $env.API_KEY;

// GOOD: token arrives as data from an upstream credential-aware node
const apiKey = $('Set Secret').first().json.apiKey;

// BEST: never see the secret in code at all
// Have an HTTP Request node with the credential attached do the call server-side.
```

Why it matters: letting Code nodes read arbitrary env vars is a privilege escalation surface. Any user with workflow-edit access could exfiltrate `DB_PASSWORD`, `N8N_ENCRYPTION_KEY`, and so on. Don't fight the restriction; route secrets through credentials.

---

## Error #8: Cannot find module 'crypto' (or any other built-in)

> `Error: Cannot find module 'crypto'` when calling `require('crypto')`

**Cause**: `require()` for Node.js built-in modules is gated by the **`N8N_RUNNERS_ALLOWED_BUILT_IN_MODULES`** env var (or the legacy `NODE_FUNCTION_ALLOW_BUILTIN`). On default installs neither is set, so `require()` throws. `Buffer` and `URL` are exposed as globals and always work.

**Solution**: Avoid `require()` in portable skills. For hashing or crypto needs, either do the work in an external service the workflow calls, or get the instance's `N8N_RUNNERS_ALLOWED_BUILT_IN_MODULES` set to `*` or a comma-list including `crypto`.

```javascript
// BAD: only works on instances with the allowlist configured
const crypto = require('crypto');
const hash = crypto.createHash('sha256').update('text').digest('hex');

// GOOD: use globals where possible
const encoded = Buffer.from('Hello World').toString('base64');
const decoded = Buffer.from(encoded, 'base64').toString();

// GOOD: when hashing is essential, do it in an upstream HTTP Request node
//   that calls a service you control, instead of inside the Code node.
```

External npm packages (`axios`, `lodash`, `moment`, etc.) are also unavailable by default. Replacements:

| External package | n8n built-in alternative |
|------------------|--------------------------|
| `axios` / `request` | `$helpers.httpRequest()` |
| `lodash` | native `Array` / `Object` methods |
| `moment` | `DateTime` (Luxon) |

---

## Error Frequency and Quick Reference

| Error Message | Likely Cause | Fix |
|---------------|--------------|-----|
| "Code cannot be empty" | Empty code field | Add meaningful code (Error #1) |
| "Code must return data" | Missing return statement | Add `return [...]` (Error #1) |
| "Return value must be an array" | Returning object instead of array | Wrap in `[...]` (Error #3) |
| "Each item must have json property" | Missing `json` wrapper | Use `{ json: {...} }` (Error #3) |
| "Unexpected token" | Expression syntax `{{ }}` in code | Remove `{{ }}`, use JavaScript (Error #2) |
| "Cannot read property X of undefined" | Missing null check | Use optional chaining `?.` (Error #5) |
| "Cannot read property X of null" | Null value access | Add guard clause or default (Error #5) |
| "Unmatched expression brackets" | Quote/bracket imbalance | Check string escaping (Error #4) |
| "UnsupportedFunctionError ... httpRequestWithAuthentication" | Auth helper blocked in task runner | HTTP Request node + credential, or sub-workflow (Error #6) |
| "$env is not defined" | `N8N_BLOCK_ENV_ACCESS_IN_NODE=true` | Route secrets through credentials (Error #7) |
| "Cannot find module 'crypto'" | `require()` allowlist not set | Move logic out of Code node, or set `N8N_RUNNERS_ALLOWED_BUILT_IN_MODULES` (Error #8) |

---

## Debugging Tips

### 1. Use `console.log()`

```javascript
const items = $input.all();
console.log('Items count:', items.length);
console.log('First item:', items[0]);
// Check the browser DevTools console (F12) or n8n server logs
```

### 2. Return intermediate results to inspect them

```javascript
const items = $input.all();
const processed = items.map(item => ({ json: item.json }));
return processed;  // wire to a No-Op node to see the shape
```

### 3. Try-catch around suspect operations

```javascript
try {
  const result = riskyOperation();
  return [{ json: { result } }];
} catch (error) {
  return [{ json: { error: error.message, stack: error.stack } }];
}
```

### 4. Validate input structure

```javascript
const items = $input.all();
console.log('Input structure:', JSON.stringify(items[0], null, 2));
```

---

## Pre-Deployment Checklist

**Code structure**

- Code field is not empty
- A `return` statement exists
- Every code path returns data

**Return format**

- Returns an array: `[...]`
- Each item has a `json` property: `{ json: {...} }`
- Format is `[{ json: {...} }]`

**Syntax**

- No `{{ }}` expression syntax (Code node uses plain JavaScript)
- Template literals use backticks: `` `${variable}` ``
- All quotes and brackets balanced
- Strings properly escaped

**Data safety**

- Null checks (`?.`) for optional nested properties
- Array length checks before index access (or use `$input.first()`)
- Webhook data accessed via `.body`
- Try/catch around risky operations
- Default values for missing data

**Sandbox / credentials**

- No `$helpers.httpRequestWithAuthentication` (blocked)
- No `$env` for secrets (gated by `N8N_BLOCK_ENV_ACCESS_IN_NODE`)
- No `require()` of built-ins unless the instance allowlist is known
- Auth flows through HTTP Request node + credential or a sub-workflow

**Testing**

- Test with empty input
- Test with missing fields
- Test with unexpected data types
- Check the browser console for runtime errors

---

## See Also

- [README.md](./README.md), [api.md](./api.md), [patterns.md](./patterns.md), [configuration.md](./configuration.md) (this topic)
- [../code-python/](../code-python/) for the Python flavor (different sandbox rules)
- [../expressions/](../expressions/) for the correct use of `{{ }}` expression syntax in **other** nodes
- [../node-configuration/](../node-configuration/) for the HTTP Request node, the canonical replacement for in-Code auth
- [../validation/](../validation/) for validating Code-node configuration via the n8n MCP / validate API
- [../workflow-patterns/](../workflow-patterns/) for SplitInBatches semantics, sub-workflow delegation, and workflow-level error handling
