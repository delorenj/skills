---
name: kapture
description: "The canonical browser tool on this machine. Kapture drives real Chrome tabs through a DevTools extension and a server on 127.0.0.1:61822, reachable by plain curl with no MCP wiring. Use for anything inside a web page here — in a tab it opens itself, or one the user already has open: opening a URL, reading a live page, filling a form, clicking through a flow, verifying a UI change, reading the console or network traffic, scraping, debugging a running app. Prefer it over the mcp__claude-in-chrome__* tools. Triggers: kapture, browse to, open this page, click that button, fill the form, screenshot the page, read the browser console, scrape this site. Do NOT use for the authenticated Chromium profile on the Mac (ego-browser); work that must stay out of the user's live browser — unattended runs, long loops, parallel sessions, anything destructive or focus-stealing (agent-workspace-linux); the browser inside the Orca app (orca-cli); or native windows, browser chrome and OS dialogs (computer-use)."
---

# kapture — the browser on this machine

Three layers: a Chrome extension (currently 1.2.1), a server on `127.0.0.1:61822`, and every
client that talks to it. Source is at `~/code/kapture`; the server ships as `kapture-mcp` on
npm. It is not a headless browser — it drives Chrome windows on the user's actual desktop, and
other agents are on the same server at the same time.

**The upstream README in a stale checkout will lie to you.** `~/code/kapture` sits at v2.1.1;
current is 2.6.1 — 32 tools (31 advertised, since `evaluate` is hidden until a tab enables it)
against the 21 that checkout defines and the 10 its README lists. Read current source with
`git -C ~/code/kapture show origin/master:server/src/tools.yaml`, never the working tree.

## The first move: adopt a tab, or open one

**You never need the user to click anything — and you may not need a new tab at all.** Decide
in one call:

```bash
K=http://127.0.0.1:61822                                  # used by every example below
bash ~/.agents/skills/kapture/scripts/kapture-doctor.sh   # LIVE / ZOMBIE / server down, per tab
```

`/tabs` alone is not proof of life — a tab that has lost its content script still appears there
with a *fresh* `lastPing` and fails every command, so the doctor probes each one.

If the task names something already open ("the app I have open", "this form") and a tab matches
by URL or title, **use that tabId** — a connected tab is already yours to read. Two matches or
none, ask, quoting the titles. Otherwise open your own; it self-connects in about half a second:

```bash
T=$(curl -s -m20 -X POST "$K/tabs" -d '{"browser":"chrome"}' | jq -r .tabId)
curl -s -X POST "$K/tab/$T/navigate" -d '{"url":"https://example.com"}'
```

Name the browser — with an empty body the server runs `xdg-open`, and a non-Chromium default
silently fails after 15s. `new_tab` lands on the Kapture how-to page, so navigate after. Close
what you opened; never close theirs.

The one thing a human must do by hand is **adopt a tab missing from `/tabs`**: click the Kapture
toolbar icon, flip the toggle, badge turns green ✓. Ask only when the task needs that tab.

## curl, not MCP

Do not wire the Kapture MCP server into Claude Code. Its 32 tool schemas are ~25 KB of JSON —
7-8k tokens resident on **every turn of every session**, for a capability most sessions never
use. The HTTP API costs nothing until called, needs no config, and already works: the origin
policy admits any request with no `Origin` header specifically so scripts can drive it.

Every read is a GET and every action a `POST /tab/{id}/{command}`; a read verb posted is a 404,
`POST /tab/{id}/screenshot` included. **Never use `curl -f` on a read** — a failed *command* on a
GET comes back 200 with an `error` body. Routes and every tool's parameters:
[references/http-api.md](./references/http-api.md).

## The loop that works

Locate, act, verify — all three in one `compose` call when you can. Each line is
`<tool>?<url-encoded-query>`; act-lines run in order and stop at the first failure, and the
**final** line may be a read, so the verification rides back in the same response.

A compose script is multi-line, but JSON strings cannot hold a raw newline — hand curl a
literal block and you get `{"error":"Invalid JSON body"}`. Let `jq` do the escaping:

```bash
jq -Rs '{script:.}' <<'EOF' | curl -s -X POST "$K/tab/$T/compose" --data-binary @-
type?selector=textarea%5Bname%3Dq%5D&text=kapture%20mcp
wait?t=300
keypress?key=Enter&selector=textarea%5Bname%3Dq%5D
wait?t=3000
elements?selector=h2&visible=true
EOF
```

That is one round trip for what would be five MCP calls. Encode `&` as `%26` or it splits the
pair; `%0A` is for a newline *inside a value*, not between steps. Max 100 steps. The whole
script is validated before anything runs, so a bad script has no side effects — but one that
fails at step 4 has already done steps 1-3. It is not transactional.

**Settling.** There is no wait-for-selector, and `navigate` returns as soon as the content
script answers — for an SPA, well before the app has rendered. Poll `elements` until it appears
and give up after ~10s; inside a compose script the only tool is `wait?t=<ms>`, so put the fixed
wait there and the real poll outside.

## Reading is where the tokens go

**There is no get-text tool**, and `dom` returns only the **first** match, so never loop it.
`elements` gives you every match at once — no text, but `href`, `src`, `value`, `name` and a
`<select>`'s `options` when present, which covers most extraction. For text, take one tightly
scoped `dom` and parse the `html` **locally**; check `domSize` first, since it rides free on
every response and a live OpenRouter tab measured `496486`.

**Screenshot to show the user, not to inform yourself** — and never trust a documented default.
The advertised `scale: 0.3` never applies: every optional param is built `.default(x).optional()`,
so an absent key stays undefined and the extension's own `scale = 0.5` wins. Measured here, an
unparameterised capture is 1:1 with CSS pixels, so a screenshot coordinate is already a click
coordinate. Compute the factor from the response rather than assuming one.

Poll loops, extraction commands and the pixel math:
[references/recipes.md](./references/recipes.md).

**Console is Chrome's per-page buffer, not Kapture's, and every navigation wipes it.** An empty
`logs` array means "nothing since this document loaded", never "no errors ever". Filter with
`?limit=20&level=error` (newest first). **Network capture has no history**: `network_monitor
{"enabled":true,"clientId":"..."}` first, *then* trigger the traffic.

**Querying mutates the page.** Kapture stamps `id="kapture-N"` on every unnamed element it
touches — usable, but yours, not the site's. Never assert on them.

## Typing into things

`fill` sets `.value` and is ignored by React/Vue, masks, autocomplete and contenteditable — all
of which need `type`, which sends real keys. `clear` first if you are replacing. `select` matches
an option's **value**, never its text. Submit with `keypress?key=Enter`. The full decision table
is in [references/recipes.md](./references/recipes.md).

`:contains()` is not CSS and Kapture rejects it by name. Use xpath for text:
`//button[contains(., "Save")]`.

## When it breaks

| Symptom | What it means | Move |
|---|---|---|
| `Could not establish connection. Receiving end does not exist.` | zombie tab: socket alive, page has no content script | **Abandon the tabId.** Verified here: `reload` times out, `show` fails, neither revives it. Open a fresh tab. `network_*` still answers. |
| `Command timeout: <cmd>` after 5s | the extension did not answer in time | **Not "it did not happen."** The late result is discarded — re-read state before retrying anything that mutates, or you double-submit. |
| `DIALOG_OPEN`, or `success: true` **with** a `dialog` field | an alert/confirm/prompt is blocking the tab | `POST /tab/{id}/dialog {"accept":true}` (`text` for a prompt), then retry. Everything else fails fast until you do. |
| `EVAL_NOT_ALLOWED`, or no `evaluate` in the list | the per-tab JS toggle is off, and the tool is hidden until some tab enables it | No programmatic grant exists. Use the purpose-built tools; ask the user only as a last resort. |
| `ELEMENT_NOT_FOUND` on something you can see | not rendered yet, or inside an iframe | Poll (see Settling); selectors never reach an iframe — screenshot, then coordinate-click. |
| a result carrying `warning:` | the tab is hidden; the event may not have landed | `show` it and retry, or verify the effect before moving on. |

**Never restart or kill the Kapture server.** If `/tabs` answers, the server is healthy and the
problem is the tab. Starting a second one refuses and exits, and its "Port 61822 is already in
use" banner suggests a `kill -9` even when the process on the port is its own healthy self —
acting on it drops every connected client and tab. Full taxonomy:
[references/failure-modes.md](./references/failure-modes.md).

One server per machine, shared by every client — Gemini, antigravity and Claude sessions are
often all attached at once (`GET /clients`), and nothing arbitrates. Another agent can navigate
or close the tab you are working in, so trust the `url` and `title` on the response you just
got over a tabId captured minutes ago.

## Routing: when it is not kapture

| The task | Use |
|---|---|
| needs the authenticated Chromium profile on the MacBook | `ego-browser` |
| must stay out of the live browser — unattended, long-running, parallel, destructive, focus-stealing | `agent-workspace-linux` |
| is a native or Electron window, an OS dialog, a file picker, the browser's own chrome | `computer-use` |
| is the browser embedded inside the Orca app | `orca-cli` |
| needs something kapture lacks (GIF capture, file upload into a page), or curl gets connection-refused | `mcp__claude-in-chrome__*` — and say out loud that you fell back |

A public page that needs no session needs no browser at all — fetch it. Everything else in a web
page on this machine is kapture's, authenticated or not. Setup, MCP wiring per CLI, and what to
tell the user when the extension is missing: [references/setup.md](./references/setup.md).

## Scope

This skill owns pages in Chrome on this host. No stealth, no fingerprint spoofing, no captcha
solving — a challenge is a handoff, not a puzzle. Anything that moves money or changes account
control stops and asks first, even when the session is already logged in.
