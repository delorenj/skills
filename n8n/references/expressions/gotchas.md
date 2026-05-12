# Expression Gotchas

Complete catalog of expression errors. Each entry follows the same four-part structure: symptom, cause, solution, and a bad-versus-good code pair.

## 1. "Expression shows as literal text in the output"

**Cause:** The expression was written without the surrounding `{{ }}`, so n8n treated it as a plain string instead of evaluating it.

**Solution:** Wrap the entire expression in double curly braces.

```javascript
// Bad
$json.email

// Good
{{$json.email}}
```

## 2. "Undefined when accessing webhook data like `name` or `email`"

**Cause:** Webhook nodes nest the inbound payload under a `.body` property, alongside `headers`, `params`, and `query`. Reading from the root of `$json` skips past the actual user data.

**Solution:** Prefix every webhook field access with `.body`.

```javascript
// Bad
{{$json.name}}
{{$json.email}}
{{$json.message}}

// Good
{{$json.body.name}}
{{$json.body.email}}
{{$json.body.message}}
```

## 3. "Unexpected token" or undefined for a field name that contains a space

**Cause:** Dot notation breaks at the first space because JavaScript interprets the space as the end of the property name.

**Solution:** Use bracket notation with a quoted string for any key containing spaces.

```javascript
// Bad
{{$json.first name}}
{{$json.user data.email}}

// Good
{{$json['first name']}}
{{$json['user data'].email}}
```

## 4. "Cannot read property 'Request' of undefined" when referencing a node with spaces in its name

**Cause:** `$node.HTTP Request` is parsed as `$node.HTTP` followed by ` Request`, which is invalid. Node names with spaces must be bracket-quoted.

**Solution:** Use `$node["Node Name"]` with double quotes around the full name.

```javascript
// Bad
{{$node.HTTP Request.json.data}}
{{$node.Respond to Webhook.json}}

// Good
{{$node["HTTP Request"].json.data}}
{{$node["Respond to Webhook"].json}}
```

## 5. "Node returns undefined even though it has data"

**Cause:** Node names are case-sensitive. `"http request"` and `"HTTP Request"` resolve to different (or missing) nodes.

**Solution:** Match the node name exactly as it appears in the workflow editor.

```javascript
// Bad
{{$node["http request"].json.data}}
{{$node["Http Request"].json.data}}

// Good
{{$node["HTTP Request"].json.data}}
```

## 6. "Literal `{{value}}` appears in the rendered output"

**Cause:** The expression was wrapped in three (or more) braces on each side, so the outer pair is treated as literal characters and only the inner pair is evaluated.

**Solution:** Use exactly one pair of `{{ }}` around the expression.

```javascript
// Bad
{{{$json.field}}}

// Good
{{$json.field}}
```

## 7. "Syntax error or 'Cannot read property 0 of undefined' when indexing an array"

**Cause:** Array indices written with dot notation (`.0`, `.1`) are not valid JavaScript. The dot followed by a number is a parse error.

**Solution:** Use square brackets for array indices.

```javascript
// Bad
{{$json.items.0.name}}
{{$json.users.1.email}}

// Good
{{$json.items[0].name}}
{{$json.users[1].email}}
```

## 8. "Code node outputs the literal string `{{$json.email}}` instead of the value"

**Cause:** Code nodes execute JavaScript directly and do not evaluate `{{ }}` expressions. The braces are treated as plain text inside a string literal.

**Solution:** In Code nodes, drop the braces and use the variables directly. The Code node API also exposes `$input.item`, `$input.all()`, and friends.

```javascript
// Bad (inside a Code node)
const email = '{{$json.email}}';
const name = '={{$json.body.name}}';

// Good (inside a Code node)
const email = $json.email;
const name = $json.body.name;

// Or via the Code node API
const email = $input.item.json.email;
const allItems = $input.all();
```

See [../code-javascript/](../code-javascript/) for the full Code node API.

## 9. "Unexpected identifier" when using `$node` without quotes

**Cause:** Node names inside `$node[...]` must be quoted strings, not bare identifiers.

**Solution:** Wrap the node name in double quotes.

```javascript
// Bad
{{$node[HTTP Request].json.data}}

// Good
{{$node["HTTP Request"].json.data}}
```

## 10. "Undefined because the property path is wrong"

**Cause:** The expression points at a path that does not match the actual data shape. Common variants: forgetting to index into an array, or using a sibling property name (`user` versus `userData`).

**Solution:** Inspect the upstream node output in the expression editor and rebuild the path from the actual structure.

```javascript
// Bad
{{$json.data.items.name}}       // items is an array
{{$json.user.email}}            // the field is actually userData

// Good
{{$json.data.items[0].name}}
{{$json.userData.email}}
```

## 11. "Output shows a literal `=` prefix in plain text fields"

**Cause:** The `=` prefix is only meaningful in JSON-mode fields where it tells n8n to evaluate the entire value as an expression. In a plain text field, the `=` is rendered as a literal character.

**Solution:** Drop the `=` in text fields. Keep it in JSON mode where you want the whole property value to be an expression result.

```javascript
// Bad (in a text field)
Email: ={{$json.email}}

// Good (in a text field)
Email: {{$json.email}}

// Good (in JSON mode)
{
  "email": "={{$json.body.email}}"
}
```

## 12. "Webhook path does not change or fails validation when set to an expression"

**Cause:** Webhook paths must be static strings. They are registered at workflow activation time, not at each execution, so expressions cannot resolve dynamically.

**Solution:** Use a static path with URL parameters (`:paramName`) for dynamic segments. Read the parameter from `$json.params` at runtime.

```javascript
// Bad
path: "{{$json.user_id}}/webhook"
path: "users/={{$env.TENANT_ID}}"

// Good
path: "my-webhook"
path: "user-webhook/:userId"
```

## 13. "Node returns undefined when forgetting `.json` in `$node` reference"

**Cause:** All node output is stored under `.json` (or `.binary` for binary data). Skipping `.json` resolves to an undefined property on the node descriptor.

**Solution:** Include `.json` between the node name and the property path.

```javascript
// Bad
{{$node["HTTP Request"].data}}
{{$node["Webhook"].body.email}}

// Good
{{$node["HTTP Request"].json.data}}
{{$node["Webhook"].json.body.email}}
```

## 14. "Literal backticks or `+` symbols appear in the output"

**Cause:** JavaScript template literal syntax (`` `Hello ${value}` ``) and explicit string concatenation (`"Hello " + value`) are not recognized at the field level. n8n only evaluates the contents of `{{ }}`; everything else is literal text.

**Solution:** Place expressions inline inside `{{ }}`. Adjacent text and expressions are automatically concatenated.

```javascript
// Bad
`Hello ${$json.name}!`
"Hello " + $json.name + "!"

// Good
Hello {{$json.name}}!
```

## 15. "Literal `{{ }}` appears in the output"

**Cause:** The braces were written without any expression content between them, so there is nothing to evaluate, and n8n leaves them as text.

**Solution:** Fill in the expression, or remove the empty braces entirely.

```javascript
// Bad
{{}}
{{ }}

// Good
{{$json.field}}
```

## Quick reference table

| Error | Symptom | Fix |
|-------|---------|-----|
| No `{{ }}` | Literal text in output | Add `{{ }}` |
| Webhook data | `undefined` | Add `.body` |
| Space in field | Syntax error | Use `['field name']` |
| Space in node | `undefined` | Use `["Node Name"]` |
| Wrong case | `undefined` | Match exact case |
| Double `{{ }}` | Literal braces | Remove the extra pair |
| `.0` array | Syntax error | Use `[0]` |
| `{{ }}` in Code | Literal string | Remove `{{ }}` |
| No quotes in `$node` | Syntax error | Add double quotes |
| Wrong path | `undefined` | Check the actual data shape |
| `=` in text | Literal `=` | Remove `=` prefix |
| Dynamic webhook path | Path will not update | Use static path with `:param` |
| Missing `.json` | `undefined` | Add `.json` after node name |
| Template literals | Literal backticks | Use `{{ }}` |
| Empty `{{ }}` | Literal braces | Add expression content |

## Debugging checklist

When an expression does not behave as expected:

1. Confirm it is wrapped in `{{ }}`.
2. If reading from a Webhook node, prefix with `.body`.
3. If the field or node name contains a space, switch to bracket notation.
4. Verify the node name matches the workflow exactly (case-sensitive).
5. Verify the property path against the actual upstream data.
6. Open the expression editor and watch the live preview.
7. If you are inside a Code node, drop the `{{ }}` and use direct variable access.

## See Also

- [api.md](./api.md), the full list of variables and methods that should resolve in expression context.
- [patterns.md](./patterns.md), correct patterns to compare against the bad examples here.
- [configuration.md](./configuration.md), setup notes (none required).
- [../code-javascript/](../code-javascript/), for the Code node API used in the "no `{{ }}` in Code nodes" gotcha.
- [../validation/](../validation/), for using n8n-mcp validation tools to catch these errors before runtime.
