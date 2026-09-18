---
name: kapture
description: "The canonical browser tool on this machine. Kapture drives real Chrome tabs through a DevTools extension and a shared server on 127.0.0.1:61822, reachable by plain curl with no MCP wiring. Use for anything that happens inside a web page here: opening a URL, reading a live page, filling a form, clicking through a flow, verifying a UI change, reading console errors or network traffic, scraping, and debugging a running app. Prefer it over the mcp__claude-in-chrome__* tools. Triggers: kapture, browse to, open this page, click that button, fill the form, screenshot the page, read the browser console, check the network tab, scrape this site, does the UI work. Do NOT use for the authenticated Chromium profile on the Mac (ego-browser), an isolated hidden desktop the user must not see (agent-workspace-linux), or native desktop windows and OS dialogs (computer-use)."
---

# kapture — the browser on this machine

Three layers: a Chrome extension (currently 1.2.1), a server on `127.0.0.1:61822`, and
every client that talks to it. Source is at `~/code/kapture`; the server is published as
`kapture-mcp` on npm. It is not a headless browser — it drives Chrome windows on the
user's actual desktop, and other agents are on the same server at the same time.

**The upstream README in a stale checkout will lie to you.** `~/code/kapture` on this box
sits at v2.1.1; current is 2.6.1, which added `type`, `insertText`, `clear`, `scroll`,
`dialog`, `watch_console`, the `network_*` trio, `evaluate` and `compose` — 34 tools, not
the 18 the old README lists. Read current source with
`git -C ~/code/kapture show origin/master:server/src/tools.yaml`, never the working tree.

## The one fact that governs everything

**You do not need the user to click anything.** `POST /tabs` opens a tab that connects
itself and returns its `tabId` in about half a second. Agent-owned work always starts
there — never open with "please click the Kapture icon."

```bash
T=$(curl -s -X POST http://127.0.0.1:61822/tabs -d '{}' | jq -r .tabId)
curl -s -X POST "http://127.0.0.1:61822/tab/$T/navigate" -d '{"url":"https://example.com"}'
```

`new_tab` always lands on the Kapture how-to page, so navigate straight after. The only
thing the user must do by hand is **adopt a tab they already have open** — click the
Kapture toolbar icon, flip the toggle, badge turns green ✓. Ask for that only when the
task needs *that specific* tab: their session, their scroll position, their app state.

## curl, not MCP

Do not wire the Kapture MCP server into Claude Code. Its 34 tool schemas are ~24 KB of
JSON — 7-8k tokens resident on **every turn of every session**, for a capability most
sessions never use. The HTTP API costs nothing until called, needs no config, and already
works: the origin policy admits any request with no `Origin` header specifically so
scripts and curl can drive it (`server/src/origin-policy.ts`).

| Verb | Path | Covers |
|---|---|---|
| GET | `/tabs`, `/tab/{id}` | which tabs are alive |
| GET | `/tab/{id}/elements?selector=`, `/dom`, `/console`, `/elementsFromPoint`, `/screenshot/view` | everything you read |
| POST | `/tab/{id}/{command}` | navigate, click, fill, type, insertText, clear, select, keypress, scroll, focus, blur, back, forward, reload, show, dialog, compose, evaluate, network_monitor, network_requests, network_body |
| POST | `/tabs` · DELETE `/tab/{id}` | open · close |

Reads are GET only — `POST /tab/{id}/screenshot` is a 404. Full map and per-tool
parameters: [references/http-api.md](./references/http-api.md).

## Preflight

`/tabs` is not proof of life. A tab whose page has lost its content script still appears
there with a *fresh* `lastPing` and fails every command. Probe, don't trust the list:

```bash
bash ~/.agents/skills/kapture/scripts/kapture-doctor.sh
```

It reports one line per tab — `LIVE`, `ZOMBIE`, or the server being down — and tells you
what to do about each.

## The loop that works

Locate, act, verify — and put all three in one `compose` call when you can. Each line is
`<tool>?<url-encoded-query>`; act-lines run in order and stop at the first failure, and
the **final** line may be a read, so the verification rides back in the same response.

```bash
curl -s -X POST "http://127.0.0.1:61822/tab/$T/compose" -d '{"script":
"type?selector=textarea%5Bname%3Dq%5D&text=kapture%20mcp
wait?t=300
keypress?key=Enter&selector=textarea%5Bname%3Dq%5D
wait?t=3000
elements?selector=h2&visible=true"}'
```

That is one round trip for what would be five MCP calls. Encode `&` as `%26` or it splits
the pair; a leading `#` makes the line a comment. Max 100 steps. The whole script is
validated before anything runs, so a bad script has no side effects — but a script that
fails at step 4 has already done steps 1-3. It is not transactional.

## Reading is where the tokens go

- **`elements` returns no text.** It gives `tagName`, `id`, `className`, a unique
  `selector`, `bounds`, `visible`, `focused`, `scrollParent` — geometry and identity, for
  locating things. No match is `"elements": []` with `success: true`, not an error.
- **`dom` is the only way to read content**, it returns the outerHTML of the **first**
  match, and it has no truncation of any kind. Scope it (`dom?selector=main`) and check
  `domSize` first — every successful response hands you `domSize`, `url`, `title`,
  `viewportDimensions` and `scrollPosition` for free. A live OpenRouter tab measured
  `domSize: 496486`. An unscoped `dom` on that is half a megabyte into context.
- **Screenshot to show the user, not to inform yourself.** It captures the viewport only
  unless you pass a selector, and its pixels are device pixels:
  `image_px = css_px × devicePixelRatio × scale`. At the default `scale: 0.3` on this
  2× display that is 0.6 — divide a screenshot coordinate by 0.6 before feeding it to a
  coordinate click. `GET /tab/{id}/screenshot/view` returns raw bytes, so write it to a
  file and Read it.
- **Querying mutates the page.** Kapture stamps `id="kapture-N"` on every unnamed element
  it touches. Those ids are real and usable, but they are yours, not the site's — never
  assert on them, and re-read after a navigation because the numbering restarts.
- `visible=true` means visible **and inside the current viewport**, so an element below
  the fold reports `visible: false`. It also fails outright on the GET endpoint (the query
  parser coerces the string to a boolean); pass it inside a `compose` script, or omit it
  and read each element's own `visible` flag.

## Choosing an input tool

| Situation | Tool |
|---|---|
| plain `<input>`/`<textarea>`, and the page is not picky | `fill` — sets `.value`, fires synthetic events, then blurs |
| React/Vue controlled input, autocomplete, input mask, contenteditable | `type` — real per-character CDP key events |
| a large block of text, or an editor like Google Docs | `insertText` — one commit, no per-key events |
| replacing existing content | `clear` first — `type` types at the cursor, it does not replace |
| native `<select>` | `select`, matching the option's **value**, never its text |
| a custom dropdown | click the trigger, then click the option |
| submitting | `keypress?key=Enter` — Enter now carries `\r` and triggers real form submission |

`:contains()` is not CSS and Kapture rejects it by name. Use xpath for text:
`//button[contains(., "Save")]`.

## When it breaks

| Symptom | What it means | Move |
|---|---|---|
| `Could not establish connection. Receiving end does not exist.` | zombie tab: socket alive, page has no content script | **Abandon the tabId.** Verified on this box: `reload` times out and `show` fails; neither revives it. Open a fresh tab, or ask the user to reload theirs. Background-only commands (`network_*`) still answer. |
| `Command timeout: <cmd>` after 5s | the extension did not answer in time | **Not "it did not happen."** The late result is discarded. Re-read state *before* retrying anything that mutates, or you double-submit. |
| `DIALOG_OPEN`, or a result with `success: true` **and** a `dialog` field | an alert/confirm/prompt is blocking the tab | `POST /tab/{id}/dialog {"accept":true}` (`text` for a prompt), then retry. Every other command fails fast until you do. |
| `EVAL_NOT_ALLOWED`, or no `evaluate` in the tool list | the per-tab JS toggle is off; the tool is hidden until some tab enables it | There is no programmatic grant. Use the purpose-built tools; they cover nearly everything. Ask the user only if nothing else can do it. |
| `ELEMENT_NOT_FOUND` on something you can see | not yet rendered, or inside an iframe | `wait?t=` in a compose script; for an iframe, selectors can never reach it — screenshot, then coordinate-click. |
| `NAVIGATION_BLOCKED` | non-http(s) URL | `chrome://`, `file://`, `about:blank` are unreachable, and a tab sitting on one cannot be driven at all. |
| an input result carrying `warning:` | the tab is hidden; the event may not have landed | `show` it and retry, or verify the effect before moving on. |

**Never restart or kill the Kapture server.** If `/tabs` answers, the server is healthy and
the problem is the tab. Starting a second one refuses and exits, and its "⚠️ Port 61822 is
already in use" banner with a `kill -9` suggestion fires even when the thing on the port is
its own healthy self — acting on it would drop every connected client and tab. Only start
one when curl gets connection-refused. Full taxonomy:
[references/failure-modes.md](./references/failure-modes.md).

## You are not alone in this browser

One server per machine, shared by every client — Gemini, antigravity and Claude sessions
are frequently all attached at once (`GET /clients` lists them). Nothing arbitrates. Another
agent can navigate or close the tab you are working in, so re-check `url` and `title` from
the response you just got rather than trusting a tabId you captured minutes ago. Network
monitoring is the only refcounted resource; pass a distinct `clientId` from curl, or your
`enabled:false` turns it off for everyone.

Etiquette on a human's live browser: work in a tab you opened, close it when you are done,
and do not navigate a tab the user is reading out from under them. `show` only to hand
something back to them deliberately.

## Routing: when it is not kapture

| The task | Use |
|---|---|
| needs the authenticated Chromium profile on the MacBook | `ego-browser` |
| must stay out of the visible browser — unattended, destructive, parallel, focus-stealing | `agent-workspace-linux` |
| is a native or Electron window, an OS dialog, a file picker, the browser's own chrome | `computer-use` |
| is the browser embedded inside the Orca app | `orca-cli` |
| needs a surface kapture lacks (GIF capture, file upload into a page) or Kapture is not installed at all | `mcp__claude-in-chrome__*` — and say out loud that you fell back |

Everything else in a web page on this machine is kapture's. Setup, MCP wiring per CLI, and
what to tell the user when the extension is missing:
[references/setup.md](./references/setup.md).

## Scope

This skill owns pages in Chrome on this host. It does not do stealth, fingerprint spoofing,
or captcha solving — a challenge is a handoff, not a puzzle. Anything that moves money or
changes account control stops and asks first, even when the session is already logged in.
