---
name: agent-fleet-operations
description: |
  Operate and maintain the Hermes fleet: shared config/registry/install, PM template and deploy contract, real named profiles with generated base-plus-delta config, ignored local runtime, systemd units, fleet self-checks/backfills, credential migration, transactional config recovery, and TTS defaults. Use for Hermes fleet updates, `~/.hermes/*`, `hermes-agent-template`, PM deployment verification, generated profiles, gateway/heartbeat state, fleet audits, MCP drift, template propagation, or voice changes. Do NOT use for project bootstrap/identity requests (→ 33god-projects), Plane ticket operations (→ project-lifecycle), Bloodbank event schemas (→ bloodbank-integration), or generic config fan-out (→ agent-config-fanout).
---

# Hermes Fleet Operations

Route here for anything that touches the shared Hermes fleet, the agent template, or the runtime provisioning contract — not the project that happens to host an agent.

## The Canonical PM Deploy Standard (2026-08, enforced)

One PM per repo, and exactly TWO per-agent systemd user units:

1. `hermes-<agent>-gateway.service` — chat-platform ingress (Telegram/Slack).
2. `hermes-<agent>-heartbeat.timer` → `.service` — the fused sentinel/checkpoint
   tick (`.scripts/heartbeat.sh`).

Bloodbank command ingress is **fleet-shared**: `hermes-fleet-bloodbank-gateway.service`
(profile `fleet-bloodbank-gateway`, adapter `bloodbank/services/hermes-gateway`)
subscribes once to `bloodbank.cmd.v1.agent.invocation.start` and routes
`data.target_agent_id` → Hermes profile via the registry's `profile_name`.
There is **no per-agent consumer unit, no checkpoint timer, no filesystem
inbox** — any of those is drift, not an alternative deployment style. Every
registry entry advertises `bloodbank: {gateway_scope: fleet, target_agent_id: <id>}`.
Canonical command envelopes need an `actor` object and
`schemaref: bloodbank.v1.agent.invocation.start.v1` or the gateway terminally
rejects them. Enforcement: pjangler `pj audit` / `pj migrate hermes.registry-parity`
detects and converges violations. Canon: `hermes-agent-template/docs/architecture.md`
§ "Bloodbank wiring". The retired scrum-master role's duties folded into the PM
heartbeat (see Krebs lifecycle: `~/code/33GOD/krebs/spec/lifecycle.v1.yaml`).

### Full command journey

```text
producer → bloodbank.cmd.v1.agent.invocation.start
  → BLOODBANK_COMMANDS work-queue stream
  → fleet-shared durable pull consumer
  → validate envelope + prompt + actor + schema
  → authorize data.target_agent_id against the fleet registry
  → journal command state in mode-0600 SQLite
  → dispatch selected Hermes profile
  → emit conversation/invocation started + completed|failed events
  → BLOODBANK_EVENTS → Candystore → Holocene/toaster
```

Commands are short-lived intent and do not become Candystore rows directly.
The gateway's lifecycle **events** are the durable audit trail. A running gateway
does not prove a target is routable: eligibility is default-deny and requires
`bloodbank.enabled: true`, `gateway_scope: fleet`, matching
`target_agent_id`, and a nonblank `profile_name` in the current registry. A past
`completed` row in the execution journal proves historical execution only.

## Operating Principles

- **Fleet truth lives in `~/.hermes/`.** `fleet.env`, `config.yaml`, and `agents-registry.yaml` are the shared sources; repo-local `agents/hermes/<role>/runtime/` contains only overrides and local state.
- **Profiles inherit the fleet base by GENERATION, not by a Hermes feature.** Hermes has **no** native profile config inheritance: `load_config()` merges only `DEFAULT_CONFIG` + `$HERMES_HOME/config.yaml` (plus a `/etc/hermes` managed overlay that *wins* at the leaf, so it cannot serve as an overridable base). The `config.inherit_from: default` / `save_mode: delta` contract this skill used to assert is read by **zero lines** of Hermes code — `profile.yaml` is metadata ABOUT a profile (description, role), never config. Inheritance is real only because `hermes-profile-config.py` renders it. Change the fleet default once, then `render --all`.
- **Template changes affect future agents; backfills affect existing ones.** Do not backfill for a simple shared default or core update.
- **One board owns the shared fleet/template contract.** Fleet-wide fixes route to the Hermes Agent PM board, not the repo board.
- **Project identity is owned by `33god-projects` / PJangler.** This skill provisions against that identity; it does not create or rename projects.

## Triage Table

| You want to… | Read first | Then |
|---|---|---|
| Add an MCP server / hook / skill so **every** agent client gets it (incl. project-scoped) | [references/extension-points.md](references/extension-points.md) | the matching plane; MCP has no SSOT yet |
| Update Hermes core, shared config, or future-agent provisioning | [references/hermes-fleet-updates.md](references/hermes-fleet-updates.md) | the matching lane inside it |
| Change, backfill, validate, or recover profile config writers | [references/config-mutation-safety.md](references/config-mutation-safety.md) | inventory every writer and prove the real caller interleavings |
| Migrate a fleet credential or eradicate leaked history | [references/secret-migration.md](references/secret-migration.md) | separate containment from any approval-gated history rewrite |
| Run a fleet self-check or debug MCP failures that differ across repo-backed daemons | [references/fleet-self-check.md](references/fleet-self-check.md) | hermes-fleet-updates for remediation lanes |
| Trace or debug a Bloodbank command from producer through Hermes lifecycle events | this skill's full command journey | `bloodbank-integration` → `references/event-journey.md` for the transport contract |
| Capture a governance rule/workflow in the PM template and propagate to existing PM agents | [references/pm-template-maintenance.md](references/pm-template-maintenance.md) | hermes-fleet-updates for backfill vs shared-config classification |
| Provision a new PM agent into a repo | → **33god-projects** `references/project-creation.md` | this skill only for runtime/template details |
| Assess, deploy, or rerun a PM without corrupting repo/fleet state | [references/pm-deployment.md](references/pm-deployment.md) | seal before-state, run `pj hermes-agent --yes`, then prove postconditions |

## Cross-Cutting Rules

- `~/.hermes/profiles/<repo>-<role>` must be a real named directory. Repo-local
  `agents/hermes/<role>/runtime/` is ignored local state, not the profile and not
  a nested Git repository; only explicit owned-state links may connect them.
  Reject a legacy profile symlink before any mutation rather than silently
  replacing or following it.
- **Never hand-edit `~/.hermes/profiles/<p>/config.yaml` — it is GENERATED.** Edit
  `config.delta.yaml` (override-only, usually 0–10 lines) then
  `hermes-profile-config.py render`. `check` is the drift gate. If Hermes itself
  wrote to a generated config (`/model`, onboarding), `absorb` folds it back
  before the next render, so an in-agent change is never silently lost.
- Every initial seed, channel, voice, render, absorb, recovery, and backfill path
  that can rewrite `config.delta.yaml` or generated `config.yaml` uses the same
  symlink-safe, crash-releasing per-profile lock. Registry transactions acquire
  registry then profile, and acquire both before snapshotting any durable
  reference or identity they may later write. See
  [references/config-mutation-safety.md](references/config-mutation-safety.md).
- A `profile.yaml` `config:` block is inert — Hermes reads `profile.yaml` only for
  `description` / `role`. Do not add config there and do not trust one you find.
- Never duplicate fleet `mcp_servers` into a delta; the base owns them.
- **`pj audit` enforces all of this** — `hermes.runtime-singleton` (per-profile:
  generated `config.yaml` + present `config.delta.yaml` + pinned memory bank) and
  `hermes.fleet-config` (fleet base: `tts.provider: vox`, Bloodbank hooks block,
  `memory` absent from `disabled_toolsets`, non-empty `skills.external_dirs`).
  When you change a fleet invariant, add it to a parity rule in the same pass, or
  the next drift is silent again.
- Identity-memory bank is pinned per profile in `<profile>/hindsight/config.json`.
  Do NOT rely on `bank_id_template: agent-{profile}` alone — `{profile}` resolves
  through `Path.resolve()` + a lowercase id regex, and silently yields the literal
  `custom` for symlinked profile dirs or uppercase names, merging agents' private
  memory. Re-run `memory-pin` after any profile rename.
- systemd units set `HERMES_HOME` to the named profile path, not the raw runtime path.
- Gateway and heartbeat health are separate. Without a per-agent channel
  credential, the gateway must be explicitly deferred, disabled, and inactive
  while the heartbeat timer can remain enabled and healthy. The profile delta
  must set `platforms.telegram.enabled: false` and
  `platforms.slack.enabled: false` so a fleet-base enable cannot leak through;
  only verified credential ownership may flip one true.
- Service proof uses a bounded stabilization window over `Result`,
  `ExecMainStatus`, `NRestarts`, and the latest heartbeat service result; one
  `is-active` sample is not success.
- The immutable PM skill core is `33god-projects`, `delonet-conventions`,
  `delonet-dotenv`, `hermes-pm-template-maintenance`, `hindsight`, and
  `subagent-driven-development`. Configuration may add skills, never subtract
  or replace these six.
- Fleet summaries and `pj audit` are aggregate claims. Verify their result
  against `.project.json`, the registry row, real profile files, and exact
  systemd enabled/active/restart state before declaring success.
- Never store literal credentials in `~/.hermes/.env`. Keep nonsecret toggles
  there if needed; store credentials in DeLoSecrets and map them with
  `secrets.onepassword.env` `op://` references. See
  [references/pm-deployment.md](references/pm-deployment.md) for the migration
  and process-verification boundary.
- A clean working tree or rewritten branch tip does not prove a leaked secret is
  gone. Fleet secret eradication must cover live text/database/cache state, the
  Git index and reachable refs, local reflogs/unreachable objects, and fetched
  remote-reachable history without printing the value. Rotation, retirement,
  and private-remote history rewriting each require explicit authorization; see
  [references/secret-migration.md](references/secret-migration.md).
- For Bloodbank lifecycle events emitted by hooks, use v1 names (`bloodbank.v1.agent.*`).
- Bloodbank hook install is owned by Bloodbank's fan-out (`~/code/33GOD/bloodbank/services/agent-hooks/sync.py --install`). Generated Hermes configs should call `~/.agents/hooks/bloodbank/publish.py --client hermes --hook <event>`, not a Hermes-local publisher.
- Before a live command proof, audit the current target's Bloodbank registry
  eligibility. Never enable a target merely to make a smoke test pass; command
  dispatch invokes a real agent and requires explicit operational authority.

## Voice / TTS defaults

Hermes uses the self-hosted Voxxy service at `https://vox.delo.sh` for TTS. The active profile's voice is controlled by `tts.vox.voice` (and the fallback `tts.voice`).

> **`tts.provider` MUST be `vox`, never `voxxy`.** Voxxy is the *service* (with
> swappable server-side engines: voxcpm, vibevoice, elevenlabs); the Hermes
> plugin's registry key is `vox` (`provider.name == "vox"`, plugin key
> `tts/vox`). `voxxy` matches no registered provider, so Hermes silently falls
> back to a built-in — ElevenLabs when `ELEVENLABS_API_KEY` is set, otherwise
> Edge — and you hear a stranger's voice with no error. **This has regressed
> twice** (canon: `voxxy/docs/plans/hermes-voxxy-tts-plugin.md`). Diagnose by
> asking the service which engine answered, which isolates Hermes from Voxxy:
>
> ```bash
> curl -s -D- -o/dev/null -X POST https://vox.delo.sh/synthesize-url \
>   -H 'Content-Type: application/json' \
>   -d '{"text":"probe","voice":"carlin"}' | grep -i x-vox-engine
> ```
>
> `x-vox-engine: voxcpm` means Voxxy is healthy and the fault is Hermes-side
> (wrong provider key). Gateways cache config — `systemctl --user restart
> hermes-<agent>-gateway` after changing it.

To change the default voice instantly, run the bundled script with the voice slug:

```bash
scripts/set_voice.sh carlin
```

See [references/voice-management.md](references/voice-management.md) for the full workflow, manual fallback, and common pitfalls.

## Out of Scope

- **Project bootstrap / repo-local agent requests** → `33god-projects`.
- **Plane ticket lifecycle** → `project-lifecycle`.
- **Bloodbank event schemas or naming contract** → `bloodbank-integration`.
- **Generic SSOT config fan-out engine mechanics** → `agent-config-fanout`.
