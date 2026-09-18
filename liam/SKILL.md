---
name: liam
description: "Work on liam, delorenj's hard fork of Kapture — browser automation for agents that drives real Chrome tabs from a CLI or plain HTTP, with MCP demoted to an opt-in adapter. Source at ~/code/liam, published as @delorenj/liam, extension id nikmjmdooglaejpjjjpnffpcockkboaj. Use when building, installing, debugging or extending liam itself: adding a tool to tools.yaml, touching the extension, cutting a release, or wiring its Bloodbank/ssbnk/Hindsight integration. Triggers: liam, the liam fork, liam server, liam extension, @delorenj/liam, fork of kapture. Do NOT use to actually drive a browser for a task — that is the kapture skill until liam's extension is loaded and its CLI ships; and do NOT use for upstream Kapture's own behaviour, which the kapture skill documents."
---

# liam — the Kapture fork

> *"I am a particular set of skills."*

A hard fork of [williamkapke/kapture](https://github.com/williamkapke/kapture) (MIT, dormant
since 2026-07-06). Source at `~/code/liam`, public at
[delorenj/liam](https://github.com/delorenj/liam). `origin` is the fork, `upstream` is William's
— kept for cherry-picking, not for merge discipline.

**This skill is about working on liam. It is not how you drive a browser.** For that, use
`kapture` — which is still the live tool on this machine, because liam's extension has to be
loaded by hand and the two servers cannot share port 61822.

## Why the fork exists

Three things a skill could document but not fix:

1. **MCP is a context tax.** 32 tool schemas ≈ 25 KB ≈ 7-8k tokens resident on every turn of
   every session, for a capability most sessions never use. Here HTTP and the CLI are the
   product; MCP becomes `liam mcp`, an opt-in adapter over a protocol-neutral core.
2. **There is no way to read text.** Upstream gives you an element's geometry or a
   half-megabyte of `outerHTML`, and nothing in between.
3. **Nothing reports to the platform.** Five browser drivers exist on this box and none emit a
   Bloodbank event, deposit an artifact, or remember anything about a site.

## What is already done

Phase 1 landed: renamed, re-keyed, upstream couplings cut, **62/62 unit tests green**.

- **Own extension id** `nikmjmdooglaejpjjjpnffpcockkboaj`, from a new RSA keypair. This is not
  cosmetic — Chrome refuses two extensions with the same id, and upstream's is installed in four
  profiles here. The private key is in 1Password (`Liam Chrome Extension Signing Key`), never in
  the repo. If you regenerate it, the id changes and `server/src/origin-policy.ts` must change
  with it or **every connection 403s silently** behind an infinite reconnect backoff.
- **`new_tab` no longer needs the internet.** It opened
  `williamkapke.github.io/kapture/how-to.html` and waited 15s for that page to self-connect; it
  now opens this server's own `/welcome`, which self-connects by the same CustomEvent. The
  page's CSS and images are vendored into `server/static/assets` and served by an `/assets`
  route.
- **One source of truth for the port** in `server/src/config.ts`. Upstream declared `PORT` in
  `index.ts`, hardcoded 61822 again in `bridge.ts`, and hardcoded the derived origins a third
  time in `origin-policy.ts` — so `KAPTURE_PORT` moved the server and left the bridge and the
  allow-list behind. `LIAM_PORT` moves all of it.
- Page-facing contracts renamed in lockstep: `liam-message`, `liam-loaded`, `liam-connect`,
  `liam-connected`, `liam://` resource URIs, `liam-N` element ids.

## Installing it (the human step)

```bash
cd ~/code/liam/server && npm install && npm run build
node dist/index.js          # binds 127.0.0.1:61822
```

**Stop the Kapture server first** — one process owns 61822, and starting a second prints a
banner suggesting `kill -9` that you should not act on blindly.

Then the part no agent can do: `chrome://extensions` → Developer mode → **Load unpacked** →
`~/code/liam/extension`. The `key` in the manifest pins the id, so it stays stable across
reloads and coexists with the Web Store Kapture. Connect a tab with the toolbar toggle, or open
<http://127.0.0.1:61822/welcome>.

## Working on it

The tool surface is a **declarative registry**: `server/src/tools.yaml` (32 tools, types,
defaults, ranges), from which `yaml-loader.ts` generates the Zod validation schema and the MCP
JSON Schema in one loop. The whole fork thesis is that the CLI becomes a third face on that same
registry.

Adding a tool costs 2-3 files — `tools.yaml`, plus `extension/page-helpers.js` (page/DOM work)
or `extension/modules/background-*.js` and its entry in `background-commands.js` (CDP/tabs
work). But **eligibility is duplicated across five hardcoded lists** that `tools.yaml` knows
nothing about, so a new tool silently works over MCP and silently 404s over HTTP:
`HTTP_TAB_COMMANDS` (`index.ts`), `ELIGIBLE_COMPOSE_TOOLS` and `TERMINAL_COMPOSE_TOOLS`
(`compose.ts`), the URI table (`resource-handler.ts`), and `DIALOG_EXEMPT_COMMANDS`
(`extension/modules/tab-manager.js`). Collapsing those into the registry is the next
architectural task.

```bash
cd ~/code/liam/server && npm test    # 62 tests, node --test via tsx
```

Two traps the suite already encodes. `tools-schema.test.ts` guards a real regression: re-adding
a top-level `oneOf` to an advertised schema 400s every Anthropic request while every behavioural
test stays green. And `index.integration.test.ts` must import `origin-policy` **dynamically** —
it transitively pulls in `config.ts`, which reads `LIAM_PORT` at module load, and a static import
hoists above the test's env assignment, silently binding the real 61822 instead of the test's
61999.

## Known upstream bug, inherited

**No `default:` in `tools.yaml` is ever applied.** `yaml-loader.ts` builds each optional property
`.default(x).optional()`, and zod's optional wrapper resolves an absent key to `undefined`
without consulting the inner default — so whatever the receiving function falls back to is what
you actually get. Measured: `screenshot.scale` is 0.5, not the advertised 0.3; `navigate.timeout`
is 5000, not 30000. Fixing this is Phase 2, and it needs a test asserting a declared default
actually reaches the extension.

## Roadmap

Neutral core (drop the MCP content-block envelope from the internal calling convention) →
generated CLI → `text`/`extract` and a settle primitive → Bloodbank events on
`bloodbank.agent.tool.*` with screenshots to ssbnk → per-site learnings persisted through
Hindsight. The full plan, with the verification gates, is in the session plan file.

## Scope

Building liam. Driving a browser is `kapture` today and will be `liam` once its extension is
loaded and the CLI ships — at which point this skill and that one merge and the sets swap over.
