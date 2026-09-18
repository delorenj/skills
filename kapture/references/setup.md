# Setup, wiring, and server lifecycle

Read this when the preflight says the server is down, when no tab can be connected, or
when someone wants Kapture resident as MCP tools in a particular CLI.

## What the user does in the browser

The DevTools panel is **not** required any more. The background service worker owns every
WebSocket and executes every command (`README.md`: "DevTools does not need to be open").
Never ask the user to open F12 or to keep the Kapture panel focused — that advice is from
the 2.1.x era and is wrong for extension 1.2.x.

To adopt a tab they already have open, once per **tab**:

1. The page is open in Chrome.
2. Click the Kapture toolbar icon.
3. Flip the connection toggle on.
4. The badge shows a green ✓. (`↻` orange means retrying, blank means disconnected.)

Two shortcuts worth knowing:

- Any URL with `?kapture-connect=true` connects itself on load. Useful when you are asking
  the user to open a page for you anyway.
- A page you control can enroll itself:
  `window.dispatchEvent(new CustomEvent('kapture-message', {detail:{type:'connect'}}))`.
  This is exactly how Kapture's own landing page self-connects, and it means a local test
  harness can connect without any user action.

For agent-owned work you should not be asking at all — `POST /tabs` opens a tab that
connects itself in about half a second. The popup is only for adopting *their* tab.

`evaluate` has a **second**, separate toggle in the same popup ("Allow JavaScript
Execution"), disabled until the tab is connected, and it resets on any disconnect.

The browser must be Chromium-family: chrome, edge, brave, opera, vivaldi. No Firefox, no
Safari.

## Server lifecycle

The server binds `127.0.0.1:61822`. The port is effectively hardcoded — `KAPTURE_PORT`
moves the server but not the bridge and not the extension, so do not override it.

```bash
# is one up?  (a live HTTP answer beats a bound port)
curl -sf -m3 http://127.0.0.1:61822/tabs >/dev/null && echo up || echo down

# start one, detached
(setsid npx -y kapture-mcp@latest >/tmp/kapture.log 2>&1 &)
for i in $(seq 20); do curl -sf -m1 http://127.0.0.1:61822/tabs >/dev/null && break; sleep 0.5; done
```

**Never kill or restart it as a remediation step.** One server per machine is the design,
shared by every client; killing it drops every connected client and every connected tab.

Starting a second one is safe — it refuses to double-bind and exits — but read its output
carefully, because it is actively misleading:

```
┌───────────────────────────────────────────────┐
│ ⚠️ Port 61822 is already in use by "Kapture"  │
├───────────────────────────────────────────────┤
│    To stop the other instance, run:           │
│       kill -9 <pid>                           │
└───────────────────────────────────────────────┘
```

That banner fires whenever the listening process is not literally named `node` — and the
server sets its own process title to "Kapture MCP Server", so it *always* takes the scary
branch, even when the thing on the port is its own healthy self. It means "a Kapture
server is already up". Do not run the suggested `kill -9`.

Every `npx kapture-mcp bridge` you add just attaches to the one server: reuse if listening,
else spawn a detached child, else host in-process.

## MCP wiring per CLI

For **Claude Code, do not wire it.** 34 tool schemas is roughly 24 KB / 7-8k tokens
resident on every turn of every session, for a capability most sessions never touch. The
HTTP API costs nothing until called. Wire the MCP server only into a CLI or agent profile
whose whole job is browser work.

If you do wire Claude Code, the WebSocket form is better than the bridge — it skips the
`npx` → `sh` → `node` → bridge process chain, since the server is already running:

```bash
claude mcp add-json kapture '{"type":"ws","url":"ws://127.0.0.1:61822/mcp"}' -s user
# or the stdio bridge every other client uses:
claude mcp add kapture -s user -- npx -y kapture-mcp@latest bridge
```

Either way the running session does not hot-reload MCP config — it appears next session.

| CLI | Config file | Snippet |
|---|---|---|
| Gemini | `~/.gemini/settings.json` | `"kapture": {"command":"npx","args":["-y","kapture-mcp@latest","bridge"]}` |
| Codex | `~/.codex/config.toml` | `[mcp_servers.kapture]` / `command = "npx"` / `args = ["-y","kapture-mcp@latest","bridge"]` |
| OpenCode | `~/.config/opencode/opencode.json` | `"kapture": {"type":"local","command":["npx","-y","kapture-mcp@latest","bridge"],"enabled":true}` |
| Copilot | `~/.copilot/mcp-config.json` | `"kapture": {"type":"local","command":"npx","args":["-y","kapture-mcp@latest","bridge"],"tools":["*"]}` |
| Kimi Code | `~/.kimi-code/mcp.json` | `"kapture": {"type":"stdio","command":"npx","args":["-y","kapture-mcp@latest","bridge"]}` |
| Hermes fleet | `~/.hermes/config.yaml` under `mcp_servers:` | `kapture:` / `command: npx` / `args: [-y, kapture-mcp@latest, bridge]` — fans out to every profile, so only if fleet agents need a browser |

## The one-shot installer is human-only

Kapture ships a wizard that detects and configures assistants — it knows Claude Desktop,
Claude Code, VS Code, Cursor and Gemini, and writes the stdio bridge config into each.

You cannot drive it. `GET /assistants` and `POST /assistants/configure` require an exact
browser-set `Origin`, specifically so a no-Origin local caller cannot reach the endpoints
that write AI-client config files. The no-Origin allowance that makes the rest of the API
curl-friendly is deliberately withheld here.

So: tell the user to open <http://127.0.0.1:61822/welcome> and tick the boxes, or run
`npx kapture-mcp setup`. For Codex, OpenCode, Copilot, Kimi and Hermes the wizard does not
know them at all — hand-write the snippets above.

One detection quirk, in case its output looks wrong: Claude Code and Gemini have no
executable path to probe, so the wizard falls back to "does the config file's parent
directory exist" — which is `$HOME`. Both always report installed, regardless of reality.
The "configured" column is a real check.

## Reading current source

The checkout at `~/code/kapture` may be well behind npm. Compare before trusting it:

```bash
git -C ~/code/kapture fetch --all -q
git -C ~/code/kapture rev-list --count HEAD..origin/master   # how stale the tree is
npm view kapture-mcp version                                  # what is actually published
git -C ~/code/kapture show origin/master:server/src/tools.yaml
git -C ~/code/kapture show origin/master:README.md
```

The upstream default branch is `master`.
