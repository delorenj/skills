---
name: 33god-hub
description: Unified entrypoint for the private 33GOD productized development environment. Use when work spans Plane/n8n ingress, Bloodbank events or commands, Candystore, Holocene, PJangler, Hermes Fleet, Skillex, Hindsight, Pipeline MCP Hub, Candybar, HeyMa, hooks, changelogs, backfills, or local/cloud platform composition, especially when tracing a message end-to-end.
---

# 33GOD Hub

Start here for platform work. This skill routes by product component and
cross-component contract, not by whichever repo happens to be open.

## Product rule

33GOD is one private development environment made from multiple repos. Component
repos own implementation; the platform control plane owns composition,
changelog, skill routing, and backfill coordination.

## Component map

| Need | Component |
|---|---|
| Signed Plane webhook ingress and provider normalization | n8n integration boundary + Bloodbank custom node |
| Event schemas, NATS/Dapr, agent lifecycle events | Bloodbank |
| Durable event history, sessions, event summaries | Candystore |
| Dashboard, live status, tool health | Holocene |
| Project/agent provisioning, project registry | PJangler |
| Long-running agents, profiles, fleet defaults | Hermes Fleet |
| Skill packs and agent capability distribution | Skillex |
| Recall/retain/journal memory hooks | Hindsight |
| Compact MCP tool gateway | Pipeline MCP Hub |
| Topology/event visualization | Candybar |
| Voice/transcription/TTS interface | HeyMa |

## Platform skills

The control plane authors these; each is also available standalone. Load the
matching one rather than re-deriving its decisions here.

| Load when | Skill |
|---|---|
| Adding or renaming a Plane label, choosing between a label and a state, wiring automation that writes to a board, scaffolding or reconciling a project board | `board-taxonomy` |
| Landing a change forward across the component repos | `merge-forward` |
| Publishing or composing skill packs | `skillex-skill-registry` |

## Event and command spine

- **Events are facts.** Producers publish `bloodbank.evt.*`; the
  `BLOODBANK_EVENTS` stream retains them, Candystore projects them durably, and
  Holocene/toaster consume read-side views.
- **Commands are intent.** Producers publish `bloodbank.cmd.*`; a targeted
  consumer acts, then emits lifecycle events. The command itself is not the
  durable audit record.
- **Plane uses one authenticated boundary.** Both self-hosted workspaces target
  `https://n8n.delo.sh/webhook/plane`; raw-body HMAC and `webhook_id` select the
  per-webhook 1Password secret before provider-neutral publication. The
  `automaticai` workspace is a tenant slug, not another infrastructure owner.
- **Identity is declared, not guessed.** `.project.json` → PJangler → the shared
  Hermes registry supplies board-to-repo and agent-to-profile routing.

Load [references/event-journey.md](references/event-journey.md) before changing
any producer, consumer, webhook, subject, projection, or command route.

## Operating procedure

1. Read `33god-platform/components.yaml`.
2. Load the matching `components/<id>.yaml`.
3. If a change affects more than one component, add a pipeline changelog entry.
4. If old repos/configs can drift, add or update a backfill check.
5. Route implementation details to the component skill or repo AGENTS.md.

## Commands

```bash
cd ~/code/33GOD/33god-platform
python3 scripts/platform.py validate
python3 scripts/platform.py components list
python3 scripts/platform.py backfills check
```
