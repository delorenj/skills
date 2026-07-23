---
name: delonet-n8n-architecture
description: Architecture principles and the custom-node catalog for building n8n workflows on DeLoNET/33GOD. Use when creating, reviewing, or refactoring ANY n8n workflow for the pipeline — deciding node boundaries (atomic single-responsibility nodes vs a god-node executeCommand/localFileTrigger shell script), emitting pipeline lifecycle events to the bloodbank bus instead of ad-hoc ntfy, choosing community vs custom nodes, packaging custom nodes as n8n-nodes-* micro-packages (n8n-nodes-bloodbank, -transcribe, -vault, minio/s3.delo.sh, obsidian vault), rebuilding the inbox/transcribe pipeline, or applying n8n instance conventions (PM2 :5678, availableInMCP, archive-outside-watch-root, direct API PUT for tags/description). Do NOT use for whether-to-use-n8n-vs-bloodbank routing (delonet-workflow-router), the event schema/envelope contract itself (bloodbank-integration), or infra paths/containers/creds (delonet-conventions).
---

# DeLoNET n8n Architecture

How to build n8n workflows that are worth building on: atomic nodes with typed
contracts, lifecycle events on the bloodbank bus, safety invariants you can see
on the canvas, and reusable units that earn their place. n8n is meant to be a
visual hub for the internals — not a place to hide a shell script inside one node.

## Operating Principles

1. **One node, one reversible responsibility.** A single node that transcribes
   AND archives to S3 AND writes to the vault is a god-node. Split it. The tell:
   an `executeCommand` wrapping a script that quietly does three jobs, giving the
   canvas zero visibility into any of them.
2. **The bus is the completion signal.** Pipeline lifecycle events publish to
   bloodbank (`bloodbank.evt.v1.<domain>.<entity>.<action>`). Never wire ntfy /
   Slack / email directly for a pipeline event — the `bloodbank-event-toaster`
   already fans `bloodbank.evt.v1.>` out to `ntfy.delo.sh/bloodbank`, so emitting
   correctly gives you the notification **plus every other consumer** for free.
   A direct ntfy node bypasses the bus and throws all of that away.
3. **Schema-first events.** Only emit events already defined under
   `bloodbank/schemas/`. If the one you need is missing, author the schema first
   (→ `bloodbank-integration`), then emit. Never invent an ad-hoc payload.
4. **Safety invariants are topology, not buried logic.** "Back up before X",
   "never delete the source", "stash on failure" become visible error-branch /
   merge structure on the canvas so the guarantee is auditable — not 40 lines
   inside a bash function nobody opens.
5. **Reusable + parameterized beats bespoke.** Every atomic action that recurs
   across pipelines earns a reusable unit. Promote it up the escalation ladder
   as reuse grows.

## Quick Navigation

| Task | Read |
|---|---|
| Justify/apply the principles + the escalation ladder in depth | [references/principles.md](./references/principles.md) |
| Build, choose, or package a custom/community node | [references/node-catalog.md](./references/node-catalog.md) |
| Emit a bloodbank event from inside an n8n workflow | [references/bloodbank-emit.md](./references/bloodbank-emit.md) |
| n8n instance facts + hard-won failure modes | [references/gotchas.md](./references/gotchas.md) |
| Rebuild the transcribe/inbox pipeline (reference implementation) | [references/transcribe-rebuild.md](./references/transcribe-rebuild.md) |

## The Escalation Ladder

Pick the lowest rung that still gives a clean, typed boundary. Promote when a unit
reaches 2+ pipelines or needs credentials / schema validation / a real UI.

```
How reusable is this atomic action?
├─ One-off glue, this workflow only          → inline Code / Set / Execute Command
├─ Reused across 2+ workflows, no creds       → subworkflow (Execute Sub-workflow),
│                                                with an explicit typed input contract
└─ Reused broadly, OR needs credentials /
   schema validation / a first-class node UI  → custom node: n8n-nodes-<thing> micro-package
```

Never inline a multi-step responsibility just because `executeCommand` is fast to
write — that is exactly how god-nodes are born. Splitting first, promoting later,
is cheaper than untangling a monolith under fire.

## Cross-Cutting Rules

- **Custom nodes are per-node micro-packages, and self-contained.** One node = one
  npm package `n8n-nodes-<thing>`, cloned from the `n8n-nodes-hermes` scaffold,
  installed into `~/.n8n/nodes`. Its logic runs **in-process in `execute()`** — never
  shelling to a host script; build it **inside the repo that owns its contract**,
  generated on deploy. An `Execute Command` calling a host CLI is the transitional
  rung only. → node-catalog.
- **n8n has no Dapr sidecar.** It runs as a PM2 host process on `:5678`; NATS is on
  the host at `127.0.0.1:4222`. Emit **NATS-direct** (via the `bb-emit` CLI) to
  `bloodbank.evt.v1.<…>` — the bloodbank **HTTP ingress is v2/RabbitMQ and bypasses
  the v3 toaster**, and Dapr `/publish` is unavailable. → bloodbank-emit.
- **Never archive into a subdir of a watched folder.** `localFileTrigger` will
  re-fire forever. Archive off-filesystem (S3) or to a sibling outside the watch
  root. → gotchas.
- **MCP access is gated.** Set `settings.availableInMCP: true` or the n8n MCP
  tools refuse the workflow. Tags and >255-char descriptions are not settable via
  MCP — use direct API `PUT /api/v1/workflows/{id}` with the
  `{name, nodes, connections, settings}` envelope. → gotchas.
- **The source recording is irreplaceable; the transcript is derivable.** Back up
  the source FIRST, verify it landed, and never delete it. This invariant survives
  every refactor. → transcribe-rebuild.

## Out of Scope

- **Whether a job should be n8n at all** (vs a bloodbank consumer, a cron, an
  agent hook) → `delonet-workflow-router`.
- **The event envelope / schema / subject contract itself** (CloudEvents fields,
  naming convention, versioning) → `bloodbank-integration`.
- **Infra paths, container/service names, credentials, `s3.delo.sh` /
  `drive.delo.sh` endpoints** → `delonet-conventions`.
- **n8n node/workflow code syntax** (SDK parameter names, expression language) →
  the `n8n-*` MCP skills (`n8n-workflow-patterns`, `n8n-node-configuration`,
  `n8n-validation-expert`, …).
