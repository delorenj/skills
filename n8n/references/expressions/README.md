# n8n Expressions

Expressions are how n8n passes data between nodes. Any node field that supports dynamic content uses the double-curly-brace syntax (`{{ }}`) to reference upstream data, transform values, format dates, or compute conditional output. n8n evaluates the contents of `{{ }}` at execution time against an expression context that exposes the current item (`$json`), other nodes (`$node["Name"]`), input helpers (`$input`, `$item`), runtime metadata (`$workflow`, `$execution`), the current timestamp (`$now`, `$today`), environment variables (`$env`), and Luxon DateTime utilities. Anything outside `{{ }}` is treated as literal text, which means a missing brace is the single most common source of broken workflows.

## When to Use

| Situation | Use Expressions? | Notes |
|-----------|------------------|-------|
| Dynamic value in a node field (URL, body, header) | Yes | Wrap in `{{ }}` |
| Concatenating literal text with a value | Yes | Adjacent text auto-joins, e.g. `Hello {{$json.name}}!` |
| Setting an entire field from an expression in JSON mode | Yes, with `=` prefix | e.g. `"email": "={{$json.body.email}}"` |
| Code node body (JavaScript or Python) | No | Use direct access like `$json.field` (see [../code-javascript/](../code-javascript/)) |
| Webhook path | No | Paths must be static, use URL parameters (`:userId`) |
| Credential fields (API keys, secrets) | No | Use the n8n credential system |
| Static configuration (timeouts, retry counts) | No | Plain values only |

## Quick Start

Reference a field from the current item:

```
{{$json.email}}
```

Reference a field from another node by name (case-sensitive, quoted if it contains spaces):

```
{{$node["HTTP Request"].json.data}}
```

Reference webhook payload data (always nested under `.body`):

```
{{$json.body.name}}
```

Format the current timestamp:

```
{{$now.toFormat('yyyy-MM-dd')}}
```

Combine literal text with expressions in a single field:

```
Hello {{$json.body.name}}, your order {{$json.body.order_id}} is confirmed.
```

## Reading Order

| Task | Files to Read |
|------|---------------|
| Look up the syntax for a specific variable or helper | [api.md](./api.md) |
| Build a working expression for a specific use case (mapping, dates, arrays, conditionals) | [patterns.md](./patterns.md) |
| Diagnose an expression that returns `undefined`, literal text, or a syntax error | [gotchas.md](./gotchas.md) |
| Understand setup or installation requirements for expressions | [configuration.md](./configuration.md) |
| Get oriented on the whole topic before diving deeper | This README, then [patterns.md](./patterns.md) |

## In This Reference

- [README.md](./README.md), this file, overview and routing.
- [api.md](./api.md), variable and helper reference for `$json`, `$node`, `$input`, `$item`, `$itemIndex`, `$now`, `$today`, `$env`, `$workflow`, `$execution`, `$helpers`, and DateTime methods.
- [patterns.md](./patterns.md), named copy-paste expression patterns organized by use case (data mapping, type conversion, dates, strings, arrays, conditionals, multi-node flows).
- [gotchas.md](./gotchas.md), four-part entries (symptom, cause, solution, bad/good pair) for the 15 most common expression mistakes.
- [configuration.md](./configuration.md), note on setup (expressions require none).

## See Also

- [../code-javascript/](../code-javascript/), for writing JavaScript inside Code nodes where the `{{ }}` syntax does NOT apply and you use direct variable access instead.
- [../code-python/](../code-python/), for the Python equivalent inside Code nodes.
- [../node-configuration/](../node-configuration/), for understanding which node fields accept expressions and which require static values.
- [../workflow-patterns/](../workflow-patterns/), for end-to-end workflow examples that show expressions used in context across multiple nodes.
- [../validation/](../validation/), for using n8n-mcp tools to validate expressions before execution.
