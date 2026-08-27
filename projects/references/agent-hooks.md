---
pipeline-status:
  - new
---
# Agent Hooks: Hindsight Memory + Bloodbank Events

Every Hermes agent provisioned into a 33god repo is wired for two cross-cutting capabilities
by default: **Hindsight** (persistent memory) and **Bloodbank** (the NATS event bus). Both are
part of provisioning, not bolted on later.

> This file covers the **harness/global** layer (how an agent gets Hindsight recall/retain +
> Bloodbank emit/consume). For the **per-dev, committed fan-out** that ships these same hooks —
> plus skills — to every teammate and every agent CLI (Claude/Codex/Hermes/Kimi) from a repo
> SSOT, see [project-scoped-hooks.md](project-scoped-hooks.md).

## Hindsight memory (recall + retain)

Hindsight is the shared team memory at `https://api.hs.delo.sh` (config `~/.hindsight/config`).
It is wired at the **harness** layer, not per-repo code. The machine-global
hook scripts live together under `~/.agents/hooks/hindsight/`; live agent configs
should point there, not to per-agent or `.old` script folders:

- **Recall (passive):** a `UserPromptSubmit` hook recalls relevant memories before each prompt;
  results arrive in `<hindsight-memory>` tags. Bank resolution:
  `BANK=$(basename "$(git rev-parse --show-toplevel)")`, falling back to `general`
  (`infra` for homelab, exact bank `33GOD` for the platform).
- **Retain (active):** `hindsight memory retain $BANK "<learning>" --context <category>`
  (categories: architecture, conventions, debugging, deployment, dependencies, preferences,
  session-summary, code-edit).
- **Recall on demand:** `hindsight memory recall $BANK "<question>" --budget mid`.

The Hermes runtime scaffold seeds `runtime/memories/{MEMORY.md,USER.md}` as the agent's local
memory surface. For the full API, bank-routing architecture, and reflection, use the
`hindsight` skill — this hub only states that agents are memory-wired by default.

The named Hermes profile `~/.hermes/profiles/<repo>-<role>/` is a real
directory. Its `config.yaml` is generated from the shared fleet base plus the
profile's real `config.delta.yaml`; its Hindsight config explicitly pins the
agent's identity-memory bank. Repo-local runtime is ignored local state and may
receive explicit owned-state links, but it is not the profile directory or a
nested Git repository.

## Bloodbank events (emit + consume)

Bloodbank is the NATS event bus (`BLOODBANK_NATS_HOST`/`PORT`, default `127.0.0.1:4222`;
compose at `~/code/33GOD/bloodbank`). Each agent is both a consumer and a producer.
Machine-global agent lifecycle hooks are normalized through one publisher:

```bash
python3 ~/.agents/hooks/bloodbank/publish.py --client <claude|codex|copilot|hermes> --hook <native-event>
```

Client-specific payload prep belongs in Bloodbank's adapter package
(`services/agent-hooks/clients/<client>.py`), not in separate per-agent publisher
trees. Legacy `claude/publish.py`, `codex/publish.py`, `copilot/publish.py`, and
`hermes/publish.py` are compatibility wrappers only.

**Binding (in `agents/hermes/<role>/role.yaml`):**
```yaml
bloodbank:
  subscribe:
    - "bloodbank.evt.v1.repo.<repo>.>"          # all events for this repo
    - "bloodbank.cmd.v1.agent.invocation.start" # one command contract; target is in data
  producer: "hermes-agent:<agent_id>"
```

**Consume:** there is intentionally **no per-agent consumer**. Command ingress
is the single fleet-shared `hermes-fleet-bloodbank-gateway.service`, which
subscribes once to `bloodbank.cmd.v1.agent.invocation.start` and routes
`data.target_agent_id` → the agent's Hermes profile via the fleet registry.
`60-bloodbank.sh` is a compatibility checkpoint only — it installs no files or
services. A `bloodbank-consumer.py` or `hermes-<agent>-consumer.service`
sighting is drift (`pj migrate hermes.registry-parity` removes it).

**Emit:** agents publish through the envelope helper. The PM's sentinel pass
emits via `.scripts/sentinel/bin/emit-event.py`; producer identity is
`hermes-agent:<agent_id>`.

**Subject scheme:**
- `bloodbank.evt.v1.repo.<repo>.>` — repo-scoped events.
- `bloodbank.cmd.v1.agent.invocation.start` — the single command subject; the
  target agent travels in `data.target_agent_id`, never in the subject.

### Plane facts use a separate ingress boundary

Agent hooks do not publish Plane ticket lifecycle facts. Plane sends signed
webhooks for both self-hosted workspaces to the one active n8n workflow at
`https://n8n.delo.sh/webhook/plane`. That workflow verifies raw-body HMAC,
normalizes the provider action, resolves `board_id` through the shared fleet
registry, and publishes `bloodbank.evt.v1.repo.task.*`.

PJangler owns the identity dependency in that journey: repo-root
`.project.json.ticket_provider` is reconciled into
`~/.hermes/agents-registry.yaml`, which the n8n node reads on every execution.
Never guess a repo from the Plane workspace; `automaticai` is just another
workspace tenant slug on the same self-hosted `plane.delo.sh` instance.

The complete event/command trace lives in the `bloodbank-integration` skill at
`references/event-journey.md`.

Skipping (e.g. local-only provisioning): `SKIP_BLOODBANK=1` makes `60-bloodbank.sh` a no-op.

## Wiring checklist when adding/repairing an agent

1. Repo-root `.project.json` has the canonical `project_slug`,
   `ticket_provider.{type,workspace,identifier,board_id,state}`, and agent entry.
2. The shared fleet registry record has the correct `profile_name` and explicit
   `bloodbank.{enabled,gateway_scope,target_agent_id}`. There is no per-agent
   consumer file or service.
3. `hermes-fleet-bloodbank-gateway.service` is the only command consumer; a live
   dispatch additionally requires the target's current `enabled: true` policy.
4. The live CLI hook config calls `~/.agents/hooks/bloodbank/publish.py --client <agent> --hook ...`;
   run `cd ~/code/33GOD/bloodbank && mise run health:hooks:check` after repair.
5. Hindsight: the harness `UserPromptSubmit` recall hook is active and the bank resolves to the
   repo (verify with `hindsight memory recall $BANK "smoke" --budget low`).
6. Memory surface present: `runtime/memories/MEMORY.md` + `USER.md`.
