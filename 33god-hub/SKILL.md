---
name: 33god-hub
description: Unified entrypoint for the private 33GOD productized development environment. Use when work spans Plane/n8n ingress, Bloodbank events or commands, Candystore, Holocene, PJangler, Flume, Hermes Fleet, Skillex, Hindsight, Pipeline MCP Hub, Candybar, HeyMa, Stitch UX ideation and BMAD handoffs, hooks, changelogs, backfills, or local/cloud platform composition, especially when tracing a message end-to-end.
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
| Durable event history, sessions, cross-CLI handoffs (`candystore context latest`) | Candystore |
| Dashboard, live status, tool health | Holocene |
| Project bootstrap, CommonProject, project registry | PJangler |
| Hiring, onboarding and reviewing agents; the org chart | Flume |
| PM planning, delegation and reviewed closeout | Momo shared skill |
| Managed ticket attempts, leases, questions, evidence and recovery | Krebs execution authority |
| Authenticated Plane CLI and provider operations | Pilot (`px`) |
| Long-running agents, profiles, fleet defaults | Hermes Fleet |
| Skill packs and agent capability distribution | Skillex |
| Recall/retain/journal memory hooks | Hindsight |
| Compact MCP tool gateway | Pipeline MCP Hub |
| Recurring/scheduled work (cron, timers, nightly jobs, poll loops) | Candybar (the single clock; never cron or a new `.timer`) via the `candybar` skill |
| Metrics, logs and operator observability | Monitoring stack + Prometheus/Loki/Grafana |
| Audio and document enrichment pipelines; voice/transcription interface | HeyMa / Wax (the `heyma` hub); TTS via Vox |

## Platform skills

The control plane authors these; each is also available standalone. Load the
matching one rather than re-deriving its decisions here.

| Load when | Skill |
|---|---|
| Resuming project work, switching agent CLIs, or finding recent requests, outcomes, decisions, and unfinished work in the event trail | [candystore-context](../candystore-context/SKILL.md) |
| Adding or renaming a Plane label, choosing between a label and a state, wiring automation that writes to a board, scaffolding or reconciling a project board | `board-taxonomy` |
| Landing a change forward across the component repos | `merge-forward` |
| Publishing or composing skill packs | `skillex-skill-registry` |
| UX ideation from captured intent, Stitch screen/variant exploration, and a selected design handoff into BMAD UX | [stitch](../stitch/SKILL.md); `bmad-ux` owns Discovery and final DESIGN.md / EXPERIENCE.md |
| Anything HeyMa/Wax: provenance, CLI, folder bindings, passes, calls, n8n EP graphs, the read-only Holocene Wax tab | the `heyma` hub (`~/HeyMa/skills/heyma/SKILL.md`; `skillex skill show heyma`) |
| Wax recording, diarization, archive or execution incident | the `heyma` hub's doctor sub-skill (`~/HeyMa/skills/heyma/subskills/doctor/SUBSKILL.md`) |
| Implementing a reusable text/frontmatter enrichment pass | the `heyma` hub's create-enrichment-pass sub-skill (`~/HeyMa/skills/heyma/subskills/create-enrichment-pass/SUBSKILL.md`) |
| Designing or changing metrics, logs, traces, dashboards or cross-system observability | `monitoring-stack` |
| Simplifying repository ignores or reconciling already-tracked paths against the effective global ignore | `gitignore-maintenance` |

## Portability / external deployment

When packaging 33GOD parts for deployment outside the home lab (e.g. a
`docker compose up` install on someone else's machine):

- Ground the inventory in RUNTIME evidence, not the repo tree alone — sweep
  `docker ps`, `systemctl --user list-units --state=running`, the Bloodbank
  compose services, cron jobs, and the event catalog (`docs/event-naming.md`).
  Repos under 33GOD/ are only a subset of what actually runs; systemd user
  units (hook-hub, n8n binary, Wax, Vinyl, curator, pdf2md, hermes-gateway)
  and host-level stacks carry much of the system.
- Split into dependency-ordered, non-overlapping groups where each group is one
  Compose bundle: bus first (NATS/Dapr/Apicurio/Candystore — zero deps), then
  integration plane (n8n + custom nodes + workflows), fleet runtime,
  observability, project tooling (PJangler + Skillex + CommonProject move
  together), voice (Wax+Vinyl+transcription+TTS; n8n and Bloodbank are prereqs),
  enrichment/memory, orchestration apps.
- LLM-touching services ship with their base_url as CONFIG, never wired to the
  home gateway — the recipient points them at any OpenAI-compatible endpoint.
  The personal gateway, desktop operator layer (zellij/crank/deckard), and
  household stacks are deliberately not shipped.
- Deliver the plan as a live checkoff artifact (see `html-artifact-delivery`):
  one checkbox per component + per group, dependency gating that shows
  "blocked by" until upstream components are checked, and localStorage
  persistence — the operator works through it one group at a time.

## Event and command spine

- **Observability has one backbone.** Immutable facts belong in
  Bloodbank/Candystore, numeric series in Prometheus, logs in Loki and traces in
  Tempo. Grafana and Holocene are consumers, not competing systems of record.
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
- **Identity is declared, not guessed.** `.project.json` → PJangler supplies
  board-to-repo identity; the org chart Flume writes into the shared Hermes
  registry supplies agent-to-profile routing. `pj project identity --apply` is
  the one cross-store write that joins them.

Managed ticket execution uses `px` → `bb call` → Krebs → Pilot's internal
provider adapter. A command receipt follows durable intent and provider readback;
publication alone is not success. Momo supplies the PM playbook under the actual
host's actor identity. Hermes and interactive hosts supervise runs; they do not
own a second ticket state machine. Root PM delegates component work to that
board's owning PM. Read `krebs/docs/execution-contract.md` and the rollout ledger
before changing managed execution or enabling a board. An installed skill is not
evidence that native actor enrollment or runtime cutover has passed.

Load [references/event-journey.md](references/event-journey.md) before changing
any producer, consumer, webhook, subject, projection, or command route.

## Operating procedure

When resuming work, use an existing startup handoff or run
`candystore context latest --project <registered-project-slug>` for recent
event-backed context. Check current source and service state before acting on it.

1. Read `33god-platform/components.yaml`.
2. Load the matching `components/<id>.yaml`.
3. If a change affects more than one component, add a pipeline changelog entry.
4. If old repos/configs can drift, add or update a backfill check.
5. Route implementation details to the component skill or repo AGENTS.md.

Repository hygiene crosses two owners: PJangler/CommonProject emit only the
portable repo contract, while Skillex distributes `gitignore-maintenance` for
effective-ignore and Git-index reconciliation. `.agents/` is the canonical
agent-config tree; client roots are local projections governed by the
operator's global ignore. Never copy `core.excludesFile` into a repository.

## Commands

```bash
cd ~/code/33GOD/33god-platform
python3 scripts/platform.py validate
python3 scripts/platform.py components list
python3 scripts/platform.py backfills check
```
