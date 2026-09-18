# Failure modes

Every error Kapture can hand you, what actually caused it, and the move. Codes come from
`server/src/browser-command-handler.ts` and `extension/modules/*.js` at 2.6.1 / 1.2.1.

## The four that will actually happen

### Zombie tab — `Could not establish connection. Receiving end does not exist.`

The extension's service worker still holds an open WebSocket, so `GET /tabs` lists the tab
with a **fresh `lastPing`** and nothing about the listing looks wrong. The page underneath
has no Kapture content script. Causes: the extension was reloaded or updated while the tab
was open (Chrome does not re-inject into already-open tabs), the tab was navigated to a
`chrome://`, Web Store or other-extension page, or Chrome discarded the tab.

Verified on this machine, against a real zombie:

- `reload` → `Command timeout: reload`, and the tab is still dead ten seconds later.
- `show` → fails with the same connection error (it focuses first, then dies decorating
  its response, which needs the content script).
- `POST network_requests` → `{"success": true, ...}`. Background-only commands survive.

**So there is no in-band fix. Abandon the tabId.** Open a fresh one with `POST /tabs`, or
ask the user to reload the tab in Chrome and re-flip the toggle. `DELETE /tab/{id}` clears
the misleading registry entry.

This is why a preflight has to probe each tab with a real content-script round trip
(`elements?selector=title`) rather than trusting `/tabs` or `tab_detail`, both of which
answer from server-side state — exactly the state a zombie lies about.

### `Command timeout: <command>.` (default 5000 ms)

The message suggests a blocking dialog, and sometimes it is right. The part that matters:
**a timeout does not mean the command did not run.** The server deletes its pending entry
and rejects; the extension keeps going, and its late answer is dropped with
`No pending command found for response`.

Re-read state before retrying anything that mutates, or you will double-submit the form.

Per-tool budgets: everything is 5000 ms unless the tool takes a `timeout`. `navigate`
advertises 30000 but the extension's own wait for the content script is a hardcoded 5000,
so a slow page fails at ~5s regardless — let it fail, then poll `tab_detail`/`elements`
until the URL settles. `reload` races the server's 5000 against the extension's 5000,
which is why it surfaces as a timeout rather than a navigation error.

### `DIALOG_OPEN`, and the silent variant

An `alert`/`confirm`/`prompt`/`onbeforeunload` freezes the tab. Every command except
`dialog`, `show` and `close` fails fast rather than hanging.

The variant that catches people: the command that *triggered* the dialog returns
`success: true` **with a `dialog` field** and a warning, because Kapture races the command
against the dialog opening rather than letting it hang. Treat `success: true` + `dialog`
as **not finished**.

```bash
curl -s -X POST "$K/tab/$T/dialog" -d '{"accept":true}'          # OK / Leave
curl -s -X POST "$K/tab/$T/dialog" -d '{"accept":false}'         # Cancel / Stay
curl -s -X POST "$K/tab/$T/dialog" -d '{"accept":true,"text":"hi"}'  # prompt() value
```

Then retry — never retry the original command first, it will just re-fail. `NO_DIALOG`
means Kapture never saw one (it opened before any CDP session existed); do not loop, and
if one is visibly on screen the user has to dismiss it. Requires extension 1.2.0+.

### `EVAL_NOT_ALLOWED`

`evaluate` is off per tab until the user flips "Allow JavaScript Execution" in the Kapture
toolbar popup. There is **no programmatic way to grant it**. Two consequences worth
knowing: the tool is hidden from the MCP tool list entirely until some connected tab has
it enabled (so its absence is not a bug), and the grant is in-memory — any WebSocket close
revokes it, though a page reload or navigation does not, because the socket lives in the
service worker.

Use the purpose-built tools; between `elements`, `dom`, `type`, `scroll` and `compose`
they cover nearly everything. Ask the user only when nothing else can do the job.

## Targeting errors

| Code | Cause | Move |
|---|---|---|
| `ELEMENT_NOT_FOUND` | no match — Kapture always takes the **first** match | `elements` with the default `visible=all` to see what is really there; `wait?t=` in a compose script if it has not rendered; if it is in an iframe, selectors can never reach it |
| `SELECTOR_OR_XPATH_REQUIRED` | no target, or a mixed mode | exactly one of `selector`, `xpath`, or `x`+`y` |
| `INVALID_SELECTOR` / `INVALID_XPATH` | syntax error | `:contains()` is intercepted by name with its own message — it is not CSS. Use `//button[contains(., "Save")]` |
| `INVALID_ELEMENT` | `fill` on a non-input, or `select` on a non-`<select>` | `type`/`insertText` for rich editors; click-the-trigger-then-the-option for custom dropdowns |
| `OPTION_NOT_FOUND` | `select` matches the option's **value**, not its text | `elements` on the select returns a full `options` array with index/value/text/selected/disabled |
| `CLICK_FAILED` / "Element disappeared before the click completed" | the element was removed mid-command on a re-rendering SPA | re-query, or coordinate-click (coordinate mode skips element tracking entirely) |

## Everything else

| Code | Cause | Move |
|---|---|---|
| `Tab <id> not found` | stale or never-connected id. The only error mapped to HTTP 404 | `GET /tabs`; with none connected, `list_tabs` adds a hint pointing at `new_tab` |
| `NAVIGATION_BLOCKED` | non-http(s) URL | `chrome://`, `file://`, `about:blank`, `data:` are refused, and such a page cannot host a content script, so it cannot be driven at all |
| `NAVIGATION_FAILED` | "Timeout waiting for content script" (5000 ms, hardcoded), "Navigation did not complete in time" (back/forward, 4000 ms), or "Tab closed during navigation" | for back/forward re-check the URL before assuming failure — it often landed |
| `EXTENSION_OUTDATED` | version gates: `watch_console` needs a reported version; `network_*` needs 1.1.0; coordinate `click`/`hover` and `dialog` need 1.2.0 | the gate is on the coordinate *mode*, not the tool — selector targeting still works. Otherwise ask the user to update the extension |
| `SCREENSHOT_ERROR` | element has no rendered size (`display:none`, collapsed), or the debugger could not attach | check `bounds`/`visible` via `elements` first |
| `NOT_MONITORING` | `network_body` with monitoring off | `network_monitor {"enabled":true}`, **re-trigger the traffic** (there is no history), then `network_requests`, then `network_body` |
| `MONITOR_START_ERROR` / `CONSOLE_LOG_ERROR` | a competing debugger owns the tab (often the user's own DevTools), or they dismissed the "Kapture is debugging this browser" infobar | retry once; then close DevTools on that tab |
| `EVAL_ERROR` | the evaluated JS threw | it runs in the page's **main world** — page globals exist, `chrome.*` does not |
| `UNKNOWN_COMMAND` | server/extension version skew | update the extension |
| HTTP 403 `Origin not allowed` | a browser Origin not on the allow-list | curl sends none, which is always allowed. The one exception is `/assistants*`, which *requires* a browser origin by design |

## Things that are not errors but will mislead you

- **`elements` with no match returns `success: true` and `"elements": []`.** Only the
  action tools raise `ELEMENT_NOT_FOUND`.
- **An input result carrying `warning:`** means the tab is hidden and the event may not
  have been delivered. Input still works on background tabs (Kapture enables CDP focus
  emulation for the duration), but check the effect or `show` the tab and retry.
- **Reading mutates.** `getUniqueSelector` assigns `id="kapture-N"` to unnamed elements,
  clicks inject a `#kapture-cursor` div for a second, and the content script adds
  `kapture-loaded` / `kapture-connected` classes to `<body>`. Never assert on element ids
  after a Kapture query, and never report a Kapture-stamped id as if the site authored it.
- **Selectors never reach iframes.** The content script is declared `all_frames: false`,
  so `dom` returns the top document only, an iframe appears as an empty tag,
  `elementsFromPoint` returns the `<iframe>` itself, and `evaluate` is top-frame too. The
  only way in is coordinate `click`/`hover`, which dispatches CDP input that hit-tests at
  the browser level.
- **`close` returns before the tab is gone** — the removal is deferred so the ack is
  delivered first. `{"closed": true}` means scheduled; the tab may linger in `/tabs` for a
  moment.
- **Console has no Kapture-side storage.** Both console tools replay Chrome's own per-page
  buffer, which resets on navigation. Anything logged before the current document is gone —
  for startup logs, start `watch_console` around the navigation. Every arg comes back as a
  string; circular refs become `[Circular]`.
