# Expression API Reference

Every n8n expression is evaluated against a runtime context that exposes a fixed set of variables and helpers. This file documents each one: what it returns, when to use it, and the methods it supports.

All examples below are written as they appear inside a node field, so they include the surrounding `{{ }}`. Inside Code nodes, drop the braces and use the variables directly (see [../code-javascript/](../code-javascript/)).

## `$json`, current item

Returns the JSON object for the current item being processed by the node.

```javascript
{{$json.fieldName}}
{{$json['field with spaces']}}
{{$json.nested.property}}
{{$json.items[0].name}}
```

For webhook payloads, the user-sent data lives under `.body`, not at the root:

```javascript
{{$json.body.email}}
{{$json.body.user.name}}
```

The root of a Webhook node's `$json` contains:

```javascript
{
  "headers": {...},
  "params": {...},
  "query": {...},
  "body": {...}   // user data lives here
}
```

## `$node["Name"]`, reference another node

Access data from any previous node in the workflow by name.

```javascript
{{$node["Set"].json.value}}
{{$node["HTTP Request"].json.data}}
{{$node["Respond to Webhook"].json.message}}
{{$node["Webhook"].json.body.email}}
```

Rules:

- Node names must be in double quotes inside the brackets.
- Node names are case-sensitive and must match the workflow exactly.
- Always include `.json` (or `.binary` for binary data) before the property path.

## `$input`, the input data API

Used primarily in Code nodes but also available in expressions for accessing the current item or all items.

```javascript
{{$input.item.json.email}}
{{$input.all().length}}
```

Common methods:

- `$input.item`, the current single item.
- `$input.all()`, an array of all incoming items.
- `$input.first()`, the first incoming item.
- `$input.last()`, the last incoming item.

## `$item(index)`, access a specific item by index

Returns the item at the given index from the current node's input.

```javascript
{{$item(0).$node["HTTP Request"].json.data}}
```

Use when iterating across multiple items and you need to pin to a specific position.

## `$itemIndex`, current item index

The zero-based index of the item currently being processed.

```javascript
Item number {{$itemIndex + 1}} of {{$input.all().length}}
```

## `$now`, current DateTime (Luxon)

A Luxon `DateTime` object representing the moment of execution.

```javascript
{{$now}}
{{$now.toFormat('yyyy-MM-dd')}}
{{$now.toFormat('HH:mm:ss')}}
{{$now.toFormat('yyyy-MM-dd HH:mm')}}
{{$now.toISO()}}
{{$now.plus({days: 7})}}
{{$now.minus({hours: 24}).toISO()}}
```

Available methods (Luxon DateTime):

- `.toFormat('pattern')`, format using tokens like `yyyy`, `MM`, `dd`, `HH`, `mm`, `ss`, `MMMM`.
- `.toISO()`, ISO 8601 string with timezone.
- `.toLocal()`, convert to local timezone.
- `.plus({units: n})`, add duration. Units: `years`, `months`, `weeks`, `days`, `hours`, `minutes`, `seconds`.
- `.minus({units: n})`, subtract duration. Same units as `.plus()`.
- `.set({units: n})`, set specific components (year, month, day, hour, etc.).

## `$today`, start of current day (Luxon)

A Luxon `DateTime` set to 00:00:00 of the current day. Same methods as `$now`.

```javascript
{{$today.toFormat('yyyy-MM-dd')}}
{{$today.plus({days: 1})}}
```

## `DateTime`, Luxon DateTime constructor

The Luxon `DateTime` class is exposed for parsing and constructing dates.

```javascript
{{DateTime.fromISO('2025-12-25').toFormat('MMMM dd, yyyy')}}
{{DateTime.fromFormat('25/12/2025', 'dd/MM/yyyy').toISO()}}
{{DateTime.now().toFormat('yyyy-MM-dd')}}
```

## `$env`, environment variables

Access environment variables set on the n8n instance.

```javascript
{{$env.API_KEY}}
{{$env.DATABASE_URL}}
```

Warning: some n8n instances run with `N8N_BLOCK_ENV_ACCESS_IN_NODE` enabled, which blocks `$env` access entirely. If `$env` returns an error, alternatives are:

- Store the value in a credential and reference the credential.
- Use a Set node with the value entered manually.
- Pass the value through webhook query parameters.

## `$workflow`, workflow metadata

Information about the currently executing workflow.

```javascript
{{$workflow.id}}
{{$workflow.name}}
{{$workflow.active}}
```

## `$execution`, execution metadata

Information about the current execution.

```javascript
{{$execution.id}}
{{$execution.mode}}        // 'manual', 'trigger', 'webhook', etc.
{{$execution.resumeUrl}}   // for wait nodes
```

## `$helpers`, utility helpers

A collection of utility functions for common operations such as HTTP requests, file handling, and item construction. Used primarily in Code nodes, but also available in expressions.

```javascript
{{$helpers.httpRequest({...})}}
```

See [../code-javascript/](../code-javascript/) for the full helpers catalog when writing inside Code nodes.

## Built-in JavaScript methods

n8n expressions execute as JavaScript inside `{{ }}`, so standard prototype methods are available on the resolved values.

### Strings

- `.toLowerCase()`, `.toUpperCase()`
- `.trim()`, `.trimStart()`, `.trimEnd()`
- `.replace(search, replacement)`
- `.substring(start, end)`, `.slice(start, end)`
- `.split(separator)`
- `.includes(value)`, `.startsWith(value)`, `.endsWith(value)`

### Arrays

- `.length`
- `.map(fn)`, `.filter(fn)`, `.find(fn)`, `.some(fn)`, `.every(fn)`
- `.join(separator)`
- `.slice(start, end)`
- `.sort()`, `.reverse()`
- `.includes(value)`

### Numbers

- `.toFixed(digits)`
- `.toString()`
- Math operators: `+`, `-`, `*`, `/`, `%`

### Logical

- Ternary: `condition ? a : b`
- Default value: `value || fallback`
- Nullish coalescing: `value ?? fallback`

## Validation rules at a glance

1. Wrap every expression in `{{ }}`.
2. Use bracket notation (`['field name']`) for property names containing spaces, diacritics, or special characters.
3. Quote node names inside `$node[...]` and match the case exactly.
4. Never nest `{{ }}` inside another `{{ }}`.
5. Always include `.json` after `$node["Name"]` before the property path.

## See Also

- [patterns.md](./patterns.md), real-world expression patterns grouped by use case.
- [gotchas.md](./gotchas.md), what goes wrong with `$json`, `$node`, dates, and arrays, and how to fix each one.
- [configuration.md](./configuration.md), expressions require no setup.
- [../code-javascript/](../code-javascript/), for using these same variables inside Code nodes without the `{{ }}` wrapper.
