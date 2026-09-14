---
name: cloudflare-focused-hub
description: Hub skill for any Cloudflare Workers platform task. Triages the request and routes to one or more specialized skills covering CLI/config (wrangler), Worker code authoring & review (workers-best-practices), stateful coordination (durable-objects), and AI agents on Workers (agents-sdk). Load when the user mentions Cloudflare, Workers, Pages, Wrangler, Durable Objects, KV, R2, D1, Vectorize, Hyperdrive, Queues, Workflows, Workers AI, the Agents SDK, MCP servers on Workers, or any deploy/dev/binding/observability task targeting Cloudflare's edge.
---

# Cloudflare Platform Hub

Router for the four Cloudflare-focused skills. Load only the child skills the task actually needs — not all four.

All child skills bias **retrieval over pre-trained knowledge**. APIs, config fields, and CLI flags drift; fetch current docs before authoring or reviewing.

## Triage

Identify the task's primary surface, then load the matching skill(s).

| Task signal | Load |
|---|---|
| `wrangler …` command, `wrangler.jsonc` config, KV/R2/D1/Vectorize/Hyperdrive/Queues/Workflows CLI, secrets, deploys, environments, `wrangler types` | **wrangler** → `../cloudflare-wrangler/SKILL.md` |
| Writing or reviewing Worker source, handler signatures, streaming, `waitUntil`, floating promises, global state, bindings, observability config, security patterns | **workers-best-practices** → `../cloudflare-workers-best-practices/SKILL.md` |
| Stateful coordination (chat rooms, multiplayer, booking), RPC methods, SQLite-backed storage, alarms, WebSocket hibernation, `getByName`, sharding | **durable-objects** → `../cloudflare-durable-objects/SKILL.md` |
| AI agents, `Agent` class, `@callable`, `useAgent`/`useAgentChat`, scheduled tasks, AgentWorkflow, MCP server/client, chat agents, durable execution, voice/browser tools | **agents-sdk** → `../cloudflare-agents-sdk/SKILL.md` |

## Common combinations

Most non-trivial tasks load 2–3 skills. Load the primary skill first, then layer.

| Scenario | Load (in order) |
|---|---|
| New Worker from scratch | wrangler → workers-best-practices |
| Reviewing a Worker PR | workers-best-practices (+ durable-objects if DOs touched, + agents-sdk if agents touched) |
| Building a chat room / multiplayer app | durable-objects → workers-best-practices → wrangler |
| Building an AI agent (chat, MCP server, scheduled) | agents-sdk → wrangler (durable-objects only if customizing the underlying DO) |
| Wiring KV/R2/D1/Vectorize/Hyperdrive bindings | wrangler → workers-best-practices |
| Setting up CI / staging / production envs | wrangler |
| Debugging deploy/auth/types/startup-time errors | wrangler |

## Cross-cutting rules (apply regardless of skill)

These show up in every child skill — internalize once at the hub level:

- **`wrangler.jsonc` is canon.** Prefer JSONC over TOML; newer features are JSON-only.
- **`compatibility_date` recent + `nodejs_compat` flag.** Most libraries assume both.
- **`wrangler types` after every config change.** Never hand-write the `Env` interface.
- **Secrets via `wrangler secret put` (interactive) or `secret bulk` from file.** Never echo, log, hardcode, or pass as CLI args. `.dev.vars` for local only and never committed.
- **Bindings beat REST.** In-process KV/R2/D1/Queues are always preferred over the Cloudflare REST API.
- **Service bindings beat public HTTP** for Worker-to-Worker calls.
- **Hyperdrive for any external Postgres/MySQL.**
- **`extends`, not `implements`** on `DurableObject`, `WorkerEntrypoint`, `Workflow`, `Agent` — `implements` loses `this.ctx` / `this.env`.
- **Don't destructure `ctx`** (`const { waitUntil } = ctx` throws "Illegal invocation").

## Discovery hints

If unsure which skill applies, look for these in the user's message or the code:

- `import { DurableObject } from "cloudflare:workers"` → durable-objects
- `import { Agent, …  } from "agents"` or `from "agents/react"` → agents-sdk
- `import { McpAgent }` or MCP server/transport mentions → agents-sdk
- `wrangler …` in shell, or any `wrangler.jsonc` field discussion → wrangler
- Any review of a `.ts`/`.js` file under a Workers project, with no DO/Agent imports → workers-best-practices

## Out of scope here

- Generic frontend frameworks deployed to Pages — load **wrangler** for `wrangler pages …`, otherwise framework-specific skills.
- Workflows authored *outside* the Agents SDK — see [Rules of Workflows](https://developers.cloudflare.com/workflows/build/rules-of-workflows/); no dedicated child skill yet.
- Cloudflare Access/Zero Trust, Magic Transit, Stream — not covered by this set.
