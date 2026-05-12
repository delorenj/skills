# API Reference: Python Code Node

This file is the symbol-level reference for everything you can call from inside a Python Code node in n8n. It covers the data-access globals (`_input`, `_json`, `_node`), the helper symbols (`_now`, `_today`, `_jmespath`), the Python (Native) alternates (`_items`, `_item`), and every standard library module that has been confirmed to load. External libraries are not covered because none are available: see [gotchas.md](./gotchas.md) for `ModuleNotFoundError`.

For when to reach for each symbol, see [patterns.md](./patterns.md). For mode-related caveats (e.g. `_input.item` being `None` outside Each Item mode), see [configuration.md](./configuration.md).

---

## Data-Access Globals (Python Beta Mode)

n8n exposes data through underscore-prefixed globals. Python (Beta) is the recommended mode and gives you the full set below.

### Symbol comparison: JavaScript vs Python (Beta) vs Python (Native)

| JavaScript | Python (Beta) | Python (Native) |
|------------|---------------|-----------------|
| `$input.all()` | `_input.all()` | `_items` |
| `$input.first()` | `_input.first()` | `_items[0]` |
| `$input.item` | `_input.item` | `_item` |
| `$json` | `_json` | `_item["json"]` |
| `$node["Name"]` | `_node["Name"]` | not available |
| `$now` | `_now` | not available |
| `$today` | `_today` | not available |

### `_input.all()`

Returns a list of every item from the previous node. Each element is a dict shaped like `{"json": {...}, "binary": {...}}` (binary key only present if there is binary data). This is the most common entry point.

```python
all_items = _input.all()
# Example shape:
# [
#   {"json": {"id": 1, "name": "Alice"}},
#   {"json": {"id": 2, "name": "Bob"}}
# ]
print(f"Received {len(all_items)} items")
return all_items
```

Use it for: batch processing, aggregations, filtering, sorting, group-by, deduplication.

### `_input.first()`

Returns just the first item, same shape as a single element from `_input.all()`. Safer than `_input.all()[0]` because it does not raise `IndexError` on empty input (it returns `None` instead, see [gotchas.md](./gotchas.md)).

```python
first_item = _input.first()
data = first_item["json"]
return [{"json": data}]
```

Use it for: single-object API responses, single-record webhook payloads, "I just want the most recent thing."

### `_input.item`

Returns the current item, only meaningful when the node is configured in "Run Once for Each Item" mode. In "Run Once for All Items" mode this is `None`, and dereferencing it raises `AttributeError`.

```python
# Each Item mode only
current = _input.item
return [{
    "json": {
        **current["json"],
        "processed": True
    }
}]
```

Use it for: per-item logic where the node is intentionally fanned out, per-item validation, conditional branching that needs to live inside the Code node.

### `_json`

The raw JSON dict of the current item. In Each Item mode this is the current item's `json`. In All Items mode it usually refers to the first item's `json`. Prefer explicit access (`_input.first()["json"]["field"]` or `_input.all()[i]["json"]["field"]`) so that intent is unambiguous.

```python
# Less explicit
value = _json.get("field")

# More explicit, preferred
value = _input.first()["json"].get("field")
```

### `_node["NodeName"]`

References the output of another node by name. Names are case-sensitive and must match exactly, spaces and all.

```python
webhook_data = _node["Webhook"]["json"]
api_data = _node["HTTP Request"]["json"]
```

Important call-site shape: if a referenced node has multiple items, accessing `["json"]` directly may not give what you expect. Use `.first()` for clarity.

```python
# Risky depending on shape
data = _node["HTTP Request"]["json"]

# Reliable
data = _node["HTTP Request"].first()["json"]
```

### `_now`

A pre-resolved current `datetime` object. Equivalent to `datetime.now()` at the moment the node starts executing.

```python
now = _now
return [{"json": {"timestamp": now.isoformat()}}]
```

### `_today`

Today's date, midnight, as a `datetime` object.

### `_jmespath(expression, data)`

JMESPath query helper for navigating deeply nested JSON without writing chained `.get()` calls.

```python
data = _input.first()["json"]
names = _jmespath("body.users[*].name", data)
```

---

## Python (Native) Mode Symbols

If you choose Python (Native) mode in the node configuration (see [configuration.md](./configuration.md)), only these two symbols are available, and the helpers (`_now`, `_jmespath`) are gone.

### `_items`

The list of all input items. Direct analog of `_input.all()`.

```python
processed = []
for item in _items:
    processed.append({"json": {"id": item["json"].get("id"), "processed": True}})
return processed
```

### `_item`

The current item in Each Item mode. Analog of `_input.item`.

---

## Webhook Payload Shape

Webhook node output has a fixed structure. The actual request payload is nested under `body`. This is the single most common Python Code node mistake (see [gotchas.md](./gotchas.md)).

```python
# Webhook node output shape:
{
    "headers": {
        "content-type": "application/json",
        "user-agent": "..."
    },
    "params": {},        # URL path params
    "query": {},         # ?key=value
    "body": {            # YOUR PAYLOAD IS HERE
        "name": "Alice",
        "email": "alice@example.com"
    },
    "method": "POST",
    "url": "/webhook/..."
}
```

Access pattern:

```python
webhook = _input.first()["json"]
payload = webhook.get("body", {})
name = payload.get("name")
content_type = webhook.get("headers", {}).get("content-type")
api_key = webhook.get("query", {}).get("api_key")
```

---

## Return Format Contract

Every Python Code node must return a list of dicts, each shaped `{"json": {...}}`. Optional `binary` key for binary data. Anything else fails the n8n type contract.

```python
# Single result
return [{"json": {"field1": value1}}]

# Multiple results
return [
    {"json": {"id": 1}},
    {"json": {"id": 2}}
]

# Empty (valid)
return []
```

See [gotchas.md](./gotchas.md) for invalid return forms.

---

## Standard Library: Availability Map

n8n's Python sandbox ships only the Python standard library. No pip packages can be installed at runtime.

### Confirmed available, commonly useful

- `json`
- `datetime`, `time`
- `re`
- `base64`
- `hashlib`
- `urllib.parse`, `urllib.request`, `urllib.error`
- `math`
- `random`
- `statistics`
- `collections` (`defaultdict`, `Counter`, `namedtuple`)
- `itertools`
- `functools`
- `operator`
- `string`
- `textwrap`

### Confirmed available, occasionally useful

- `os.path` (path string operations only, filesystem mutation is sandboxed)
- `copy`
- `typing`
- `enum`
- `decimal`
- `fractions`

### NOT available (will raise `ModuleNotFoundError`)

- `requests` (use HTTP Request node, or JavaScript with `$helpers.httpRequest`)
- `pandas`, `numpy`, `scipy` (use list comprehensions, `statistics`, or upstream nodes)
- `beautifulsoup4` / `bs4`, `lxml` (use HTML Extract node)
- `selenium` (browser automation is not supported)
- `psycopg2`, `pymongo`, `sqlalchemy`, `pymysql` (use n8n database nodes)
- `flask`, `fastapi`, `django` (irrelevant inside a workflow)
- `pillow`, `openpyxl`, `xlsxwriter` (use Spreadsheet File node, external API)

See [gotchas.md](./gotchas.md) entry 1 for the recovery playbook when you discover something you need isn't available.

---

## Standard Library: Symbol-Level Reference

### `json`

The most common module. Parse and emit JSON.

```python
import json

# Parse JSON string to dict
data = json.loads('{"name": "Alice", "age": 30}')

# Emit dict to JSON string
output = json.dumps({"users": [{"id": 1}], "total": 1}, indent=2)

# Handle parse errors
try:
    parsed = json.loads(user_input)
    error = None
except json.JSONDecodeError as e:
    parsed = None
    error = str(e)
```

Pretty printing:

```python
pretty = json.dumps(data, indent=2, sort_keys=True)
```

### `datetime`

Date and time. There is no Luxon equivalent, so durations and time-zone math are more manual than in JavaScript.

```python
from datetime import datetime, timedelta

now = datetime.now()
tomorrow = now + timedelta(days=1)
one_hour_ago = now - timedelta(hours=1)
next_week = now + timedelta(weeks=1)

# Parsing ISO 8601
dt = datetime.fromisoformat("2025-01-15T14:30:00")
weekday = dt.strftime("%A")

# Formatting
iso = now.isoformat()
us_format = now.strftime("%m/%d/%Y")
eu_format = now.strftime("%d/%m/%Y")
long_format = now.strftime("%A, %B %d, %Y")
time_12h = now.strftime("%I:%M %p")
time_24h = now.strftime("%H:%M:%S")

# Comparison and difference
diff = datetime(2025, 1, 20) - datetime(2025, 1, 15)
diff.days             # 5
diff.total_seconds()  # 432000.0
```

### `re`

Regular expressions. Python's regex is often the reason someone chooses Python over JavaScript.

```python
import re

# Find one
m = re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)
email = m.group(0) if m else None

# Find all
hashtags = re.findall(r'#(\w+)', text)

# Substitution
cleaned = re.sub(r'\$', '', "Price: $99.99")
normalized = re.sub(r'\s+', ' ', cleaned)

# Anchored match for validation
is_valid_email = bool(re.match(r'^[\w.-]+@[\w.-]+\.\w+$', email))

# Split on multiple delimiters
parts = re.split(r'[,;|]', "apple,banana;orange|grape")
parts = [p.strip() for p in parts]

# Compiled, case-insensitive, reusable
priority_pattern = re.compile(r'\b(urgent|critical|emergency)\b', re.IGNORECASE)
matches = priority_pattern.findall(subject_line)
```

### `base64`

Encode and decode binary, Basic Auth construction.

```python
import base64

# Encode string -> base64 string
encoded = base64.b64encode("Hello, World!".encode("utf-8")).decode("utf-8")

# Decode base64 string -> string
decoded = base64.b64decode("SGVsbG8sIFdvcmxkIQ==").decode("utf-8")

# Basic Auth header
credentials = f"{username}:{password}"
auth_header = "Basic " + base64.b64encode(credentials.encode()).decode()
```

### `hashlib`

Checksums, password hashing, ID derivation.

```python
import hashlib

md5 = hashlib.md5("Hello, World!".encode()).hexdigest()
sha256 = hashlib.sha256(password.encode()).hexdigest()

# Truncated unique ID
seed = f"{datetime.now().isoformat()}-{user_id}"
short_id = hashlib.sha256(seed.encode()).hexdigest()[:16]
```

Note: `hashlib` is fine for checksums and ID derivation, but for credentialed password hashing you should be using the n8n credential system upstream, not rolling your own.

### `urllib.parse`

URL parsing, query string encoding/decoding, percent-encoding.

```python
from urllib.parse import urlparse, urlencode, parse_qs, quote, unquote

# Parse URL
p = urlparse("https://example.com/path?key=value&foo=bar#section")
p.scheme    # "https"
p.netloc    # "example.com"
p.path      # "/path"
p.query     # "key=value&foo=bar"
p.fragment  # "section"

# Build query string
qs = urlencode({"name": "Alice Smith", "email": "alice@example.com"})

# Parse query string (values are lists because keys can repeat)
params = parse_qs("name=Alice&tags=python&tags=n8n")
name = params.get("name", [""])[0]
tags = params.get("tags", [])

# Percent-encode / decode individual values
encoded = quote("Hello, World! ")
decoded = unquote(encoded)
```

`urllib.request.urlopen` exists and can make HTTP GETs without external libraries. It is intentionally austere: no retries, no JSON serialization, no convenient header handling. For real HTTP work, put an HTTP Request node before the Code node, or switch to JavaScript and use `$helpers.httpRequest`. See [gotchas.md](./gotchas.md) entry 1.

### `math`

Standard math.

```python
import math

math.ceil(16.7)        # 17
math.floor(16.7)       # 16
round(16.7)            # 17 (built-in, not math)
math.sqrt(16)          # 4.0
math.pow(2, 3)         # 8.0
math.fabs(-5.5)        # 5.5

# Trig (radians)
math.sin(math.radians(45))
math.cos(math.radians(45))
math.pi
math.e

# Logs
math.log10(100)        # 2.0
math.log(100)          # natural log
math.log2(100)
```

### `random`

Random selection, shuffling, sampling. Not cryptographically secure; use `secrets` (also standard library) for tokens.

```python
import random

random.random()                  # 0.0 to 1.0
random.randint(1, 100)           # inclusive
random.randrange(0, 100, 5)      # 0, 5, 10, ..., 95

random.choice(["red", "green", "blue"])
random.sample(range(1, 101), 10) # 10 unique values

items = [1, 2, 3, 4, 5]
random.shuffle(items)            # in place
```

### `statistics`

The reason a lot of people choose Python in the first place.

```python
import statistics

numbers = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

statistics.mean(numbers)         # 55.0
statistics.median(numbers)       # 55.0
statistics.mode([1, 2, 2, 3])    # 2
statistics.stdev(numbers)        # ~30.28
statistics.variance(numbers)     # ~916.67
```

Note: `stdev` and `variance` require at least 2 data points or they raise `StatisticsError`. Guard for that:

```python
sd = statistics.stdev(values) if len(values) > 1 else 0
```

### `collections`

The two members you will actually use are `defaultdict` and `Counter`.

```python
from collections import defaultdict, Counter

# Group-by without writing "if key not in d: d[key] = []"
grouped = defaultdict(list)
for item in items:
    grouped[item["category"]].append(item)

# Frequency counts
counts = Counter(tag for item in items for tag in item["tags"])
counts.most_common(5)  # top 5 most frequent
```

### `itertools` and `functools`

Pulled in occasionally for `itertools.chain`, `itertools.groupby` (requires pre-sorted input), `functools.reduce`. Not critical to memorize; reach for them only if you have a specific pattern.

---

## Helper Function Surface (Comparison)

| Concern | JavaScript | Python (Beta) | Python (Native) |
|---------|------------|---------------|-----------------|
| HTTP request | `$helpers.httpRequest()` | not available, use HTTP Request node | not available |
| Workflow static data | `$getWorkflowStaticData('global')` | not reliably available in Python Beta | not available |
| Current time | `$now` (Luxon DateTime) | `_now` (Python datetime) | use `datetime.now()` |
| Today | `$today` | `_today` | use `datetime.now().date()` |
| JMESPath | via library | `_jmespath(expr, data)` | not available |
| JSON parse | `JSON.parse()` | `json.loads()` | `json.loads()` |
| Regex | `/pattern/` | `re.findall`, `re.search` | `re.findall`, `re.search` |

If you need any helper not listed in the Python columns, that is a strong signal to use JavaScript. See [../code-javascript/](../code-javascript/).

---

## See Also

- [README.md](./README.md), the JavaScript-first recommendation and decision tree.
- [patterns.md](./patterns.md), named copy-paste patterns that use the symbols on this page.
- [gotchas.md](./gotchas.md), `ModuleNotFoundError`, `KeyError`, `IndexError`, mode mistakes, webhook nesting.
- [configuration.md](./configuration.md), mode selection (Python Beta vs Native, All Items vs Each Item) and beta caveats.
- [../code-javascript/](../code-javascript/), the symbol reference for the JavaScript equivalent.
- [../expressions/](../expressions/), the `{{ }}` symbol reference for non-Code nodes.
- [../mcp-tools/](../mcp-tools/), for `get_node_types(["nodes-base.code"])` to introspect Code node parameters.
