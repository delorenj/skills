# The HTTP API and the full tool surface

Read this when you need a parameter you do not remember, or you are deciding whether a
tool is reachable over HTTP at all. Everything here is from `origin/master` at
kapture-mcp 2.6.1 / extension 1.2.1. Regenerate the tool list with:

```bash
git -C ~/code/kapture show origin/master:server/src/tools.yaml
```

## Endpoints

Base is `http://127.0.0.1:61822`. A request with no `Origin` header is always allowed
(`server/src/origin-policy.ts`), which is why curl works with no configuration.

| Method | Path | Notes |
|---|---|---|
| GET | `/tabs` | every registered tab, with `lastPing`, `domSize`, dimensions, `scrollPosition`, `pageVisibility` |
| GET | `/clients` | connected MCP clients — who else is sharing this browser |
| GET | `/tab/{id}` | one tab's detail |
| GET | `/tab/{id}/elements?selector=` or `?xpath=` | `[&visible=true\|false\|all]` — **the `visible` param is broken here**, see below |
| GET | `/tab/{id}/dom[?selector=]` | outerHTML of body, or of the first match |
| GET | `/tab/{id}/console[?limit=&level=&before=]` | newest first |
| GET | `/tab/{id}/elementsFromPoint?x=&y=` | |
| GET | `/tab/{id}/screenshot` | JSON with base64 in `data` |
| GET | `/tab/{id}/screenshot/view` | **raw image bytes** — pipe to a file and Read it |
| POST | `/tabs` | = `new_tab`. Body `{}` or `{"browser":"chrome\|edge\|brave\|opera\|vivaldi"}` |
| POST | `/tab/{id}/{command}` | JSON body of that tool's params, minus `tabId` |
| DELETE | `/tab/{id}` | = `close` |

`POST /tab/{id}/{command}` accepts exactly these: `navigate`, `back`, `forward`, `reload`,
`show`, `click`, `hover`, `focus`, `blur`, `fill`, `select`, `keypress`, `scroll`, `type`,
`insertText`, `clear`, `evaluate`, `compose`, `network_monitor`, `network_requests`,
`network_body`, `dialog`. Anything else is a 404 — notably `screenshot`, `dom`,
`elements`, `elementsFromPoint` and `console_logs`, which are GET resources instead.

`watch_console` has **no** HTTP route at all. Reach it as the final line of a `compose`
script, or poll `/console`.

Status codes are coarse: only a message containing "not found" becomes 404, schema
failures are 400, and everything else — including a compose parse error — is 500. Parse
the JSON body; do not branch on the status.

## Every tool, by job

Required args are in **bold**. Every tab-scoped tool takes `tabId` (supplied by the URL
over HTTP). Every selector-taking tool accepts `selector` **or** `xpath`, never both, and
acts on the **first** match only, echoing back the unique selector it actually used.

### Find and manage tabs
| Tool | Args |
|---|---|
| `list_tabs` | — |
| `tab_detail` | — |
| `new_tab` | `browser` (chrome, edge, brave, opera, vivaldi) |
| `close` | — |
| `show` | — brings the tab to the front and focuses its window |

### Move
| Tool | Args |
|---|---|
| `navigate` | **`url`** (http/https only), `timeout` (default 30000 — but the extension's internal wait is a hardcoded 5000, so this only buys the server patience) |
| `back` / `forward` / `reload` | — |
| `scroll` | selector alone = scrollIntoView centred · `x`/`y` alone = absolute document scroll (a missing axis keeps the current offset) · selector **plus** coords = scroll *inside* that element, returning `elementScroll` |

### Read
| Tool | Args |
|---|---|
| `elements` | selector/xpath, `visible` (`"true"`/`"false"`/`"all"`, default `all`) |
| `dom` | selector/xpath (first match; omit for `body`) |
| `elementsFromPoint` | **`x`**, **`y`** — returns the `<iframe>` element, never its contents |
| `screenshot` | selector/xpath, `scale` 0.1–1.0 (default 0.3), `format` webp/jpeg/png (default webp), `quality` 0.1–1.0 (default 0.85) |
| `console_logs` | `limit` (default 100), `level`, `before` (timestamp, for paging). Returns `{logs, hasMore, totalCount}`, **newest first** |
| `watch_console` | **`timeout`** 1000–60000 — collects live for that window, returns **chronological** |

### Act
| Tool | Args |
|---|---|
| `click` / `hover` | selector/xpath **or** `x`+`y` (CSS pixels, viewport-relative) |
| `focus` / `blur` | selector/xpath |
| `fill` | **`value`** + selector/xpath — sets `.value`, fires synthetic input/change, blurs. Rejects anything but input/textarea/contenteditable |
| `type` | **`text`**, optional selector/xpath, `delay` 0–5000 per char, `timeout` up to 120000 — real CDP keystrokes, types at the cursor |
| `insertText` | **`text`**, optional selector/xpath — one IME-style commit |
| `clear` | optional selector/xpath — Ctrl/Cmd+A then Backspace via real key events |
| `select` | **`value`** + selector/xpath — native `<select>` only, matches the option's **value** attribute |
| `keypress` | **`key`** (`"Enter"`, `"Control+a"`, `"Shift+Tab"`, F1–F12, arrows…), optional selector/xpath, `delay` (>500 auto-repeats), `timeout` 1000–70000 |
| `dialog` | **`accept`** bool, `text` for a `prompt()`. Extension 1.2.0+ |

### Network
Capture has **no history** — enable before the traffic you want.

| Tool | Args |
|---|---|
| `network_monitor` | **`enabled`** bool, `clientId` (**pass one from HTTP**), `force` |
| `network_requests` | `limit` (default 50), `since` (the prior call's `cursor`) |
| `network_body` | **`requestId`**, `maxBytes` (default 65536) — returns `requestBody` and `body`; streaming/evicted bodies come back as `bodyError` |

Every HTTP caller that omits `clientId` collapses into one shared identity `"http"`, so
one curl's `enabled:false` stops monitoring for every other curl.

### Escape hatches
| Tool | Args |
|---|---|
| `evaluate` | **`code`**, `timeout` 1000–60000. Gated per tab; hidden from the MCP tool list until some tab allows it. Main world, top frame only, result must be JSON-serializable, promises are awaited |
| `compose` | **`script`** — see below |

## compose

One command per line, `<tool>?<query-string>`, keys are that tool's own parameter names.
A `tabId` key on a line is discarded. Blank lines and lines starting with `#` are comments.

- **Anywhere:** navigate, back, forward, reload, click, hover, focus, blur, fill, type,
  insertText, clear, select, keypress, scroll — plus `wait?t=<ms>` (0–60000).
- **Final line only:** screenshot, dom, elements, elementsFromPoint, console_logs,
  watch_console. This is the act-then-verify pattern.
- **Never:** evaluate, new_tab, close, show, list_tabs, tab_detail, dialog, the
  `network_*` trio, or compose itself.
- Max 100 steps. No cap on script length or total runtime; each line uses its own tool's
  timeout.

Encoding: `%20` or `+` for a space, `%26` for `&` (it splits the pair otherwise), `%0A`
for a newline inside a value. A `#` inside a *value* is fine; only a leading `#` comments
the line.

Validation is all-or-nothing — every bad line is reported together and nothing executes:

```
Invalid compose script:
Line 1: 'elements' returns data and may only be the final command
Line 3: 'evaluate' is not an eligible compose command
Line 4: wait requires t=<milliseconds> in 0-60000
```

Execution is **not** transactional. It stops at the first failure; earlier steps have
already happened. The response is an ordered array of `{command, ...that tool's result}`,
one per executed step, with the error on the last entry. A `wait` yields
`{command:"wait", success:true, waited:N}`. If the script ends in a screenshot, the image
arrives as `dataUrl` on the last array element over HTTP (as a separate image content
block over MCP).

## The `visible` coercion bug

```
GET /tab/{id}/elements?selector=h1&visible=true
  -> {"error":"...Expected 'true' | 'false' | 'all', received boolean"}
```

The GET resource parser turns the string `"true"` into a real boolean, and the schema
wants the string. Workarounds, both verified:

```bash
# omit it (defaults to "all") and read each element's own `visible` flag
curl -s --get --data-urlencode "selector=h1" "$K/tab/$T/elements"
# or route it through compose, where the value survives as a string
curl -s -X POST "$K/tab/$T/compose" -d '{"script":"elements?selector=h1&visible=true"}'
```

Remember what it means: `visible: true` requires the element to be rendered **and inside
the current viewport**. Something below the fold is `false`. Scroll to it first, or read
`bounds` yourself.

## Schema enforcement is uneven

`type: number` parameters are range-checked (`scale=0.05` is rejected). `type: integer`
parameters fall through to `z.any()` — `console_logs?limit=9999` and even `limit=abc` are
accepted despite the documented 1–500 range. Do not rely on the documented bounds for
integer params.
