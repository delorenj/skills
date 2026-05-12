# Expression Patterns

Copy-paste expression recipes organized by use case. Each pattern shows the data shape it operates on, the expression to use, and the expected output.

## Data mapping

### Map a webhook field into a downstream node

Webhook node receives:

```json
{
  "headers": {"content-type": "application/json"},
  "params": {},
  "query": {},
  "body": {
    "name": "John Doe",
    "email": "john@example.com",
    "company": "Acme Corp",
    "message": "Interested in your product"
  }
}
```

In a downstream Slack node text field:

```
New form submission!

Name: {{$json.body.name}}
Email: {{$json.body.email}}
Company: {{$json.body.company}}
Message: {{$json.body.message}}
```

Output:

```
New form submission!

Name: John Doe
Email: john@example.com
Company: Acme Corp
Message: Interested in your product
```

Good: reference user data through `.body`. Bad: `{{$json.name}}` returns `undefined` because the field lives at `body.name`.

### Reference data from an earlier node by name

Inside an Email node, reference fields from both Webhook and HTTP Request:

```
Subject: Order {{$node["Webhook"].json.body.order_id}} Confirmed

Body:
Dear {{$node["HTTP Request"].json.order.customer}},

Your order {{$node["Webhook"].json.body.order_id}} has been confirmed!

Total: ${{$node["HTTP Request"].json.order.total}}
Items: {{$node["HTTP Request"].json.order.items.join(', ')}}
```

Good: quoted node names match exactly, including capitalization. Bad: `$node[HTTP Request]` (missing quotes) or `$node["http request"]` (wrong case) both fail.

### Pass dynamic values into an HTTP Request URL

Webhook receives `{ "body": { "order_id": "ORD-12345" } }`. In the HTTP Request URL field:

```
https://api.example.com/orders/{{$json.body.order_id}}
```

Resolves to: `https://api.example.com/orders/ORD-12345`.

### Chain multi-node calls with location lookup

Based on n8n template #2947 (Weather to Slack), structure is Webhook to OpenStreetMap to Weather API to Slack.

Webhook receives `{ "body": { "text": "London" } }`.

OpenStreetMap URL:

```
https://nominatim.openstreetmap.org/search?q={{$json.body.text}}&format=json
```

Weather API URL:

```
https://api.weather.gov/points/{{$node["OpenStreetMap"].json[0].lat}},{{$node["OpenStreetMap"].json[0].lon}}
```

Final Slack message:

```
Weather for {{$json.body.text}}:

Temperature: {{$node["Weather API"].json.properties.temperature.value}}°C
Conditions: {{$node["Weather API"].json.properties.shortForecast}}
```

## Database insertion

### Insert with current timestamp into Postgres

HTTP Request returns:

```json
{
  "data": {
    "users": [
      {"id": 123, "name": "Alice Smith", "email": "alice@example.com", "role": "admin"}
    ]
  }
}
```

Postgres node INSERT statement:

```sql
INSERT INTO users (user_id, name, email, role, synced_at)
VALUES (
  {{$json.data.users[0].id}},
  '{{$json.data.users[0].name}}',
  '{{$json.data.users[0].email}}',
  '{{$json.data.users[0].role}}',
  '{{$now.toFormat('yyyy-MM-dd HH:mm:ss')}}'
)
```

## Date and time

Current execution time is `2025-10-20 14:30:45`.

### ISO format

```javascript
{{$now.toISO()}}
```

Output: `2025-10-20T14:30:45.000Z`

### Custom date format

```javascript
{{$now.toFormat('yyyy-MM-dd')}}
```

Output: `2025-10-20`

### Time only

```javascript
{{$now.toFormat('HH:mm:ss')}}
```

Output: `14:30:45`

### Full readable date

```javascript
{{$now.toFormat('MMMM dd, yyyy')}}
```

Output: `October 20, 2025`

### Future date (date math, add)

```javascript
{{$now.plus({days: 7}).toFormat('yyyy-MM-dd')}}
```

Output: `2025-10-27`

### Past date (date math, subtract)

```javascript
{{$now.minus({hours: 24}).toFormat('yyyy-MM-dd HH:mm')}}
```

Output: `2025-10-19 14:30`

### Parse a fixed date string

```javascript
{{DateTime.fromISO('2025-12-25').toFormat('MMMM dd, yyyy')}}
```

Output: `December 25, 2025`

## Arrays

Data:

```json
{
  "users": [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
    {"name": "Charlie", "email": "charlie@example.com"}
  ]
}
```

### First element

```javascript
{{$json.users[0].name}}
```

Output: `Alice`

### Last element

```javascript
{{$json.users[$json.users.length - 1].name}}
```

Output: `Charlie`

### Map to single field, join

```javascript
{{$json.users.map(u => u.email).join(', ')}}
```

Output: `alice@example.com, bob@example.com, charlie@example.com`

### Array length

```javascript
{{$json.users.length}}
```

Output: `3`

Good: bracket notation `[0]` for indices. Bad: `$json.users.0.name` is invalid JavaScript.

## Conditionals

Data:

```json
{
  "order": {"status": "completed", "total": 150}
}
```

### Ternary operator

```javascript
{{$json.order.status === 'completed' ? 'Order Complete' : 'Pending...'}}
```

Output: `Order Complete`

### Default value with `||`

```javascript
{{$json.order.notes || 'No notes provided'}}
```

Output: `No notes provided` (if `notes` is missing or falsy).

### Multiple conditions

```javascript
{{$json.order.total > 100 ? 'Premium Customer' : 'Standard Customer'}}
```

Output: `Premium Customer`

## String manipulation

Data:

```json
{
  "user": {
    "email": "JOHN@EXAMPLE.COM",
    "message": "  Hello World  "
  }
}
```

### Lowercase

```javascript
{{$json.user.email.toLowerCase()}}
```

Output: `john@example.com`

### Uppercase

```javascript
{{$json.user.message.toUpperCase()}}
```

Output: `  HELLO WORLD  `

### Trim whitespace

```javascript
{{$json.user.message.trim()}}
```

Output: `Hello World`

### Substring

```javascript
{{$json.user.email.substring(0, 4)}}
```

Output: `JOHN`

### Replace substring

```javascript
{{$json.user.message.replace('World', 'n8n')}}
```

Output: `  Hello n8n  `

### Split and re-join

```javascript
{{$json.tags.split(',').join(', ')}}
```

## Type conversion and number ops

### Math on numeric fields

```javascript
{{$json.price * 1.1}}          // add 10%
{{$json.quantity + 5}}
{{$json.price.toFixed(2)}}     // format to 2 decimals
```

### Concatenate text with values (automatic)

```
Hello {{$json.name}}!
```

Good: adjacent literal text and expressions auto-concatenate. Bad: backtick template literals (`` `Hello ${$json.name}!` ``) do not work in expression fields.

## Fields with spaces or special characters

Data:

```json
{
  "user data": {
    "first name": "Jane",
    "last name": "Doe",
    "phone number": "+1234567890"
  }
}
```

### Bracket notation for each segment

```javascript
{{$json['user data']['first name']}}
```

Output: `Jane`

### Combine bracket-notation fields with literal text

```javascript
{{$json['user data']['first name']}} {{$json['user data']['last name']}}
```

Output: `Jane Doe`

### Special characters and diacritics

Bracket notation is mandatory for keys containing currency symbols, slashes, or non-ASCII characters:

```javascript
{{$json['Gross Price w/o shipment']}}
{{$json['Cena brutto zł']}}
```

## Environment variables

With `API_KEY=secret123` set on the n8n host:

### In an HTTP Request header

```
Authorization: Bearer {{$env.API_KEY}}
```

Resolves to: `Authorization: Bearer secret123`.

### In a URL query parameter

```
https://api.example.com/data?key={{$env.API_KEY}}
```

If `$env` access is blocked on your instance, see the alternatives listed in [api.md](./api.md).

## Code node (direct access, no `{{ }}`)

When you need to transform data in a Code node, drop the braces and use the variables directly.

Input from Webhook:

```json
{
  "body": {
    "items": ["apple", "banana", "cherry"]
  }
}
```

Code node body:

```javascript
const items = $json.body.items;
const uppercased = items.map(item => item.toUpperCase());

return [{
  json: {
    original: items,
    transformed: uppercased,
    count: items.length
  }
}];
```

Output:

```json
{
  "original": ["apple", "banana", "cherry"],
  "transformed": ["APPLE", "BANANA", "CHERRY"],
  "count": 3
}
```

Good: direct `$json.body.items` access. Bad: `'{{$json.body.items}}'` returns the literal string `"{{$json.body.items}}"`. See [../code-javascript/](../code-javascript/) for the full Code node API.

## JSON-mode field assignment with the `=` prefix

When a field is set in JSON mode and you want its entire value to be the expression result, prefix the value with `=`:

```json
{
  "name": "={{$json.body.name}}",
  "email": "={{$json.body.email}}"
}
```

In a plain text field, omit the `=`:

```
Hello {{$json.body.name}}!
```

## Summary of high-frequency patterns

- Webhook data: `{{$json.body.field}}`
- Other node data: `{{$node["Name"].json.field}}`
- Timestamps: `{{$now.toFormat('yyyy-MM-dd')}}`
- Array access: `{{$json.array[0].field}}`
- Default value: `{{$json.field || 'default'}}`
- Conditional: `{{$json.x === 'y' ? 'a' : 'b'}}`

## See Also

- [api.md](./api.md), full reference for every variable and method used above.
- [gotchas.md](./gotchas.md), what to do when these patterns return `undefined` or syntax errors.
- [configuration.md](./configuration.md), setup notes (none needed).
- [../code-javascript/](../code-javascript/), Code node patterns where these expressions are written without `{{ }}`.
- [../workflow-patterns/](../workflow-patterns/), full multi-node workflow examples that combine these patterns end-to-end.
