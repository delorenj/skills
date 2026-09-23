---
name: agent-fleet-operations
description: |
  Operate and maintain the Hermes workforce with `flume`: hire/onboard an employee into a repo, the org chart in `~/.hermes/agents-registry.yaml`, the handbook (`contracts/handbook.yaml`), real named profiles with generated base-plus-delta config, ignored local runtime, the one gateway unit per agent, compliance audits and remediations, credential migration, transactional config recovery, and TTS defaults. Use for `flume hire|onboard|roster|org|record|review|audit|remediate|handbook`, `~/.hermes/*`, `hermes-agent-template`, PM deployment verification, generated profiles, gateway state, MCP drift, template propagation, or voice changes. Do NOT use for project bootstrap/identity requests (→ 33god-projects), Plane ticket operations (→ project-lifecycle), Bloodbank event schemas (→ bloodbank-integration), or generic config fan-out (→ agent-config-fanout).
---

# Hermes Workforce Operations

Route here for anything that touches a deployed Hermes agent, the agent template,
or the runtime provisioning contract — not the project that happens to employ one.

`flume` is the CLI. It hires, onboards and reviews employees; pjangler bootstraps
repos and keeps the project registry. The vocabulary is deliberate and the
mechanical mapping is exact:

| corporate | mechanical |
|---|---|
| employee | a deployed Hermes agent (`33god-pm`) |
| title | role (`pm`) |
| desk | `~/.hermes/profiles/<name>` |
| record | that agent's row in `~/.hermes/agents-registry.yaml` |
| org chart | the whole registry |
| job description | `agents/hermes/<title>/role.yaml` |
| handbook | `flume/contracts/handbook.yaml` |

```
flume hire <title>                 bring on a new employee for this repo (title defaults to pm)
flume onboard [title]              re-run the onboarding checklist (refuses a provisioned role dir; see below)
flume roster  (alias: flume org)   the org chart, and every disagreement between the two registries
flume record                       which build each employee actually runs, against the configured pin
flume review [--agent <id>]        performance review across all nine observation domains
flume handbook validate            authorities, classes, service model, retired modes
flume audit [repo] [--rules ids]   the eight employee invariants a repository is subject to
flume remediate <finding> [repo]   correct one finding
```

`roster`, `record`, `review` and `handbook validate` are strictly read-only, take
the same option surface (`--agent`, `--contract`, `--project-registry`,
`--agent-registry`, `--deadline-ms`, `--json`), and exit 0 even when the
workforce is in bad shape. Only a command failure, a blown `--deadline-ms`, or a
cancellation is nonzero — `flume review --exit-code` opts into projecting the
verdict onto the process exit (10 on notice, 11 unable to assess).

`flume onboard` is `runHire(force: false)`, and hire refuses any non-empty role
dir, so on an employee that is already deployed it stops at "Hermes target
directory is not empty" (every PM does this, 2026-09-23). To converge a deployed
employee, run its own marker-guarded steps from the role dir instead, then
`flume audit` + `flume review`:

```bash
cd <repo>/agents/hermes/pm
SKIP_TELEGRAM=1 bash .scripts/30-telegram.sh   # record the channel as deferred (or omit SKIP_* to wire a token; it prompts)
bash .scripts/70-systemd.sh                     # unit, heartbeat retired, gateway active|deferred from provisioning_status
bash .scripts/80-registry.sh                    # project the row
```

`80-registry.sh` re-dumps the WHOLE registry through `yaml.safe_dump`, which
requotes and re-indents every other row. When you need a one-row change,
simulate it first (`REGISTRY_FILE=<scratch copy> bash .scripts/80-registry.sh`),
back up `~/.hermes/agents-registry.yaml`, take `flock <registry>.lock` (other
agents write the same file), edit only that row, and re-parse to prove every
other row is unchanged.

The simulation is what the provisioner WOULD write, not what the contract
allows. Carry over only fields the handbook declares writable
(`contracts/handbook.yaml` `writable_fields`), then run `flume review --agent
<id>` and confirm the row raises no `registry-retired-key`. A role dir's
deployed scripts can lag the template: before template 5ee1909, 80-registry.sh
projected role.yaml `service_state` into `systemd.gateway_state` and
`systemd.heartbeat_state`, keys the handbook's `systemd_lifecycle` seam does
not declare (tonnybox-pm picked both up by a verbatim copy on 2026-09-23). Run
`flume remediate hermes.pm-scaffold <repo> --scripts-only` before you trust a
simulation or rerun the steps. Gateway and heartbeat state live in role.yaml
`service_state`; the registry row names the units only.

`flume remediate` keeps `migrate` as a frozen hidden alias. 74 copies of
`20-runtime-repo.sh` on this machine run
`<bin> migrate hermes.runtime-singleton <path> [--dry-run] --json`, so that argv
must keep working; write `remediate` in anything new.

`flume remediate hermes.pm-scaffold <repo>` does more than refresh scripts: it
also composes SOUL.md (tracked and runtime), rewrites the `hermes` wrapper and
`.gitignore`, seeds the runtime and adds missing registry rows. To land a
template change that only touched `.scripts/`, pass `--scripts-only`. It refreshes
the verbatim `.scripts/**` and the rendered `.scripts/sentinel.prompt.md` and
writes nothing else. Either mode still preserves a *locally-modified* script,
meaning bytes the template never shipped. Diff each one against its nearest
template version before you overwrite it by hand, and fold real behaviour into
the template as configuration (e.g. the extended ticket states are role.yaml
`ticket_provider:` keys) rather than keeping a per-repo fork. When you copy a
template file over one, copy its mode too: a 0644 `credential-launch.sh` kills
its gateway with `status=203/EXEC` on the next restart. A hand-written SOUL.md
(no composer marker, none of the rendered headings) is preserved and audits as
`soul-authored`; that is the intended steady state, not drift to clear.

`pj audit` still exists and owns the PROJECT rules (`mise.*`, `bmad.*`, `sot.*`,
`secrets.env-op`, `provenance.copier`, `skills.project-manifest`, `notebook.*`,
`momo-lifecycle-plane`, `board.schema`). It gained `--rules <comma,ids>` too.
`flume hire` uses it as a postcondition probe
(`pj audit --rules mise.config-root,sot.project-json --json`); a probe that
cannot reach `pj` reports **unable to assess** and does **not** fail the hire.
Flume never hard-depends on pjangler being installed.

## The canonical deployment standard (enforced)

One PM per repo, and exactly **one** per-agent systemd user unit:

- `hermes-<agent>-gateway.service` — chat-platform ingress (Telegram/Slack).

**Per-agent heartbeat timers are retired.** `hermes-<agent>-heartbeat.timer` and
its `.service` do not exist; `systemctl --user list-unit-files | grep -c heartbeat`
returns 0. Every agent used to get a one-minute oneshot whose reconciliation pass
was gated on a `role.yaml` flag that was true in exactly one repo, so ~20,000
no-op invocations a day is all it did. What took over its three apparent jobs:

- **liveness** — the gateway unit itself (`Restart=on-failure`);
- **scheduling** — Bloodbank;
- **persistence** — krebs leases.

`70-systemd.sh` now actively *removes* any heartbeat units it finds and records
`service_state.heartbeat: retired` in `role.yaml`, so re-running provisioning
converges a legacy host. `flume audit --rules systemd.sentinel` requires only the
gateway unit; demanding a timer failed every freshly provisioned agent.

Bloodbank command ingress is **fleet-shared**: `hermes-fleet-bloodbank-gateway.service`
(profile `fleet-bloodbank-gateway`, adapter `bloodbank/services/hermes-gateway`)
subscribes once to `bloodbank.cmd.agent.invocation.start` and routes
`data.target_agent_id` → Hermes profile via the registry's `profile_name`. There
is **no per-agent consumer unit, no checkpoint timer, no filesystem inbox** — any
of those is drift, not an alternative deployment style. Every registry row
advertises `bloodbank: {enabled, gateway_scope: fleet, target_agent_id: <id>}`,
and the registry's top-level `gateways.bloodbank` block records the shared
contract. Canonical command envelopes need an `actor` object and
`schemaref: bloodbank.agent.invocation.start.v1` or the gateway terminally
rejects them. Enforcement: `flume audit` / `flume remediate hermes.registry-parity`
detects and converges violations. Canon: `hermes-agent-template/docs/architecture.md`
§ "Bloodbank wiring". The retired scrum-master title's duties folded into the PM.

### Full command journey

```text
producer → bloodbank.cmd.agent.invocation.start
  → BLOODBANK_COMMANDS work-queue stream
  → fleet-shared durable pull consumer
  → validate envelope + prompt + actor + schema
  → authorize data.target_agent_id against the org chart
  → journal command state in mode-0600 SQLite
  → dispatch selected Hermes profile
  → emit conversation/invocation started + completed|failed events
  → BLOODBANK_EVENTS → Candystore → Holocene/toaster
```

Commands are short-lived intent and do not become Candystore rows directly.
The gateway's lifecycle **events** are the durable audit trail. A running gateway
does not prove a target is routable: eligibility requires `bloodbank.enabled`
absent or `true` (**no key means enabled**; only an explicit `false`
quarantines, and a present non-boolean is invalid, treated as disabled and
logged at ERROR), `gateway_scope: fleet`, matching `target_agent_id`, and a
nonblank `profile_name` in the current registry. The same rule holds in
`role.yaml`: `80-registry.sh` projects an absent key as `true`, and both it and
flume read the key with a YAML parser, so `enabled: "false"`, `enabled: ""`,
a bare `enabled:` and `True`/`yes` are all invalid (a blocked remediation), never
a quarantine or an enable. A past `completed` row in
the execution journal proves historical execution only.

## Reading a review verdict

`flume review` returns one of three verdicts. The JSON envelope and the ANSI
report both spell them mechanically; read them as the standing they mean:

| envelope `health.verdict` | standing | means |
|---|---|---|
| `healthy` | in good standing | every observation passed |
| `unhealthy` | on notice | an observation was read and it failed |
| `unproven` | unable to assess | the observation itself could not be trusted |

The third state is load-bearing. It fires when the run was incomplete, stale, or
carried an unjustified skip, and collapsing it into either of the other two is
how an aggregate report starts lying. `health.proven` is
`verdict === healthy && fleet_complete` — that, not the verdict alone, is what
lets you claim the whole workforce is clean. The nine observation domains are
`registry`, `project_binding`, `template_scaffold`, `profile`, `runtime`,
`systemd`, `live_process`, `bloodbank`, `release_provenance`; `--domain` scopes
to one. `--live` is an authorization, not a mode: it permits bounded read-only
host and network observation (the recipe-owned audit rules), never mutation,
process control, service changes, board changes, or Bloodbank activation.

## Operating Principles

- **Workforce truth lives in `~/.hermes/`.** `fleet.env`, `config.yaml`, and
  `agents-registry.yaml` are the shared sources; repo-local
  `agents/hermes/<title>/runtime/` contains only overrides and local state.
- **Profiles inherit the fleet base by GENERATION, not by a Hermes feature.**
  Hermes has **no** native profile config inheritance: `load_config()` merges only
  `DEFAULT_CONFIG` + `$HERMES_HOME/config.yaml` (plus a `/etc/hermes` managed
  overlay that *wins* at the leaf, so it cannot serve as an overridable base).
  `config.inherit_from: default` / `save_mode: delta` is read by **zero lines** of
  Hermes code — `profile.yaml` is metadata ABOUT a desk (description, role), never
  config. Inheritance is real only because `hermes-profile-config.py` renders it.
  Change the fleet default once, then `render --all`.
- **Template changes affect future employees; backfills affect current ones.** Do
  not backfill for a simple shared default or core update.
- **One board owns the shared workforce/template contract.** Fleet-wide fixes
  route to the Hermes Agent PM board, not the repo board.
- **Project identity is owned by `33god-projects` / pjangler.** This skill
  provisions against that identity; it does not create or rename projects.

## Triage Table

| You want to… | Read first | Then |
|---|---|---|
| Add an MCP server / hook / skill so **every** agent client gets it (incl. project-scoped) | [references/extension-points.md](references/extension-points.md) | the matching plane; MCP has no SSOT yet |
| Update Hermes core, shared config, or future-employee provisioning | [references/hermes-fleet-updates.md](references/hermes-fleet-updates.md) | the matching lane inside it |
| Change, backfill, validate, or recover profile config writers | [references/config-mutation-safety.md](references/config-mutation-safety.md) | inventory every writer and prove the real caller interleavings |
| Migrate a fleet credential or eradicate leaked history | [references/secret-migration.md](references/secret-migration.md) | separate containment from any approval-gated history rewrite |
| Run a workforce self-check or debug MCP failures that differ across repo-backed daemons | [references/fleet-self-check.md](references/fleet-self-check.md) | hermes-fleet-updates for remediation lanes |
| Trace or debug a Bloodbank command from producer through Hermes lifecycle events | this skill's full command journey | `bloodbank-integration` → `references/event-journey.md` for the transport contract |
| Capture a governance rule/workflow in the PM template and propagate to existing PMs | [references/pm-template-maintenance.md](references/pm-template-maintenance.md) | hermes-fleet-updates for backfill vs shared-config classification |
| Provision a new PM into a repo | → **33god-projects** `references/project-creation.md` | this skill only for runtime/template details |
| Assess, deploy, or rerun a PM without corrupting repo/fleet state | [references/pm-deployment.md](references/pm-deployment.md) | seal before-state, run `flume hire pm --yes`, then prove postconditions |

## Cross-Cutting Rules

- `~/.hermes/profiles/<repo>-<title>` must be a real named directory. Repo-local
  `agents/hermes/<title>/runtime/` is ignored local state, not the desk and not a
  nested Git repository; only explicit owned-state links may connect them. Reject
  a legacy profile symlink before any mutation rather than silently replacing or
  following it.
- **Never hand-edit `~/.hermes/profiles/<p>/config.yaml` — it is GENERATED.** Edit
  `config.delta.yaml` (override-only, usually 0–10 lines) then
  `hermes-profile-config.py render`. `check` is the drift gate. If Hermes itself
  wrote to a generated config (`/model`, onboarding), `absorb` folds it back
  before the next render, so an in-agent change is never silently lost. The
  generated file carries a render marker in its header; a `config.yaml` without
  one is a hand-forked copy and `hermes.runtime-singleton` fails it.
- Every initial seed, channel, voice, render, absorb, recovery, and backfill path
  that can rewrite `config.delta.yaml` or generated `config.yaml` uses the same
  symlink-safe, crash-releasing per-profile lock. Registry transactions acquire
  registry then profile, and acquire both before snapshotting any durable
  reference or identity they may later write. See
  [references/config-mutation-safety.md](references/config-mutation-safety.md).
- A `profile.yaml` `config:` block is inert — Hermes reads `profile.yaml` only for
  `description` / `role`. Do not add config there and do not trust one you find.
- Never duplicate fleet `mcp_servers` into a delta; the base owns them. A delta
  that redeclares a base LIST replaces it rather than extending it, which is what
  `hermes.delta-list-override` exists to catch.
- **`flume audit` enforces all of this.** The eight employee rules and what each
  one actually reads:

  | rule | scope | reads |
  |---|---|---|
  | `hermes.pm-scaffold` | project | `agents/hermes/<title>/` scripts and launcher match the pinned template |
  | `hermes.untracked-runtimes` | project | runtime is untracked + gitignored, no gitlink, no stale `.gitmodules` |
  | `systemd.sentinel` | host | gateway unit installed and matching each role's declared `service_state` |
  | `hermes.runtime-singleton` | project | real desk dir, shared links, Skillex projection, generated `config.yaml` + present `config.delta.yaml` + pinned memory bank |
  | `hermes.fleet-config` | host | fleet base: `tts.provider: vox`, a `hooks:` block with all four events calling the canonical publisher, `memory.provider` set, `memory` absent from `agent.disabled_toolsets` |
  | `hermes.delta-list-override` | host | no delta replaces a fleet-base list |
  | `hermes.profile-wiring` | host | launcher and unit `HERMES_HOME` point at the named desk; no dead `HERMES_OAUTH_FILE` |
  | `hermes.registry-parity` | host | registry ↔ `role.yaml` ↔ `.project.json` agree; `bloodbank` block present; no legacy `consumer_unit`/`checkpoint_timer` |

  `hermes.fleet-config` is deliberately **not** auto-fixable: those are fleet-wide
  operator decisions and a wrong guess changes every agent at once. When you
  change a fleet invariant, add it to a rule in the same pass, or the next drift
  is silent again.
- Identity-memory bank is pinned per desk in `<profile>/hindsight/config.json`.
  Do NOT rely on `bank_id_template: agent-{profile}` alone — `{profile}` resolves
  through `Path.resolve()` + a lowercase id regex, and silently yields the literal
  `custom` for symlinked profile dirs or uppercase names, merging agents' private
  memory. Re-run `memory-pin` after any profile rename.
- systemd units set `HERMES_HOME` to the named desk path, not the raw runtime path.
- Gateway health is per-agent and conditional. Without a per-agent channel
  credential, the gateway must be explicitly deferred, disabled, and inactive —
  never an enabled crash loop. The profile delta must set
  `platforms.telegram.enabled: false` and `platforms.slack.enabled: false` so a
  fleet-base enable cannot leak through; only verified credential ownership may
  flip one true.
- The deferred state has four parts, and `flume review` passes it:
  `telegram.provisioning_status: deferred` in role.yaml AND in the registry row,
  `platforms.telegram.enabled: false` in the delta, and the unit disabled +
  inactive. A gateway left running without a `verified` platform is a finding,
  not health: `undeclared` when the row names no status (voxxy-pm), and a
  contract violation when it says `disabled`/`deferred` (deckard-pm). Give the
  role's `telegram:` block all three keys (`provisioning_status`, `bot_username`,
  `bot_id`). Before template 7c3b6b5 the channel writer appended any key the
  block lacked to the LAST block in role.yaml (tonnybox-pm got
  `service_state.provisioning_status`).
- A disabled PM gateway is usually a dead bot, not a dead project. Test the
  vaulted token with getMe, feeding the URL on stdin
  (`printf 'url = "https://api.telegram.org/bot%s/getMe"\n' "$tok" | curl -s --config -`),
  and open `https://t.me/<handle>`. A 401, plus a t.me page with no bot title,
  means the bot was deleted. Only the operator can mint a new one (BotFather
  `/newbot`). Then run `bash .scripts/30-telegram.sh` (it prompts for the token
  and stages it in 1Password), followed by `70-systemd.sh` and `80-registry.sh`.
  Never re-enable the unit against the dead token. tonnybox-pm was parked this way
  on 2026-08-27, and pjangler also listed it in `DEAD_AGENT_IDS` because its role
  pointed at a hard-deleted board while `.project.json` still named the live
  one (PJAN-136). Check the Plane DB before you call a project dead.
- Service proof uses a bounded stabilization window over `Result`,
  `ExecMainStatus`, and `NRestarts`; one `is-active` sample is not success.
- The runtime skill core is pinned by `[fleet] symlinked_runtime_skills` in
  `~/.config/hermes-agent-template/config.toml` — that file, not this one, is the
  authority. Read it, then prove every member resolves to a real
  `~/.agents/skills/<name>/SKILL.md`. Configuration may add skills; it may never
  drop a pinned member, and a missing member is a hard failure, not a warning
  followed by a completion marker. Note that a pinned name is a *directory* under
  `~/.agents/skills/`, which is not always the skill's frontmatter `name:` —
  `33god-projects` ships in the `projects/` directory.
- `flume roster` / `record` / `review` / `audit` are aggregate claims. Verify their
  result against `.project.json`, the registry row, real profile files, and exact
  systemd enabled/active/restart state before declaring success.
- Never store literal credentials in `~/.hermes/.env`. Keep nonsecret toggles
  there if needed; store credentials in DeLoSecrets and map them with
  `secrets.onepassword.env` `op://` references. See
  [references/pm-deployment.md](references/pm-deployment.md) for the migration
  and process-verification boundary.
- A clean working tree or rewritten branch tip does not prove a leaked secret is
  gone. Eradication must cover live text/database/cache state, the Git index and
  reachable refs, local reflogs/unreachable objects, and fetched remote-reachable
  history without printing the value. Rotation, retirement, and private-remote
  history rewriting each require explicit authorization; see
  [references/secret-migration.md](references/secret-migration.md).
- Bloodbank lifecycle events emitted by hooks are 4-token types
  (`bloodbank.<domain>.<entity>.<action>`, e.g. `bloodbank.agent.invocation.started`)
  published on 5-token subjects (`bloodbank.evt.agent.invocation.started`). There is
  no version token in the name — the only version left is the schema revision in
  `dataschema` / `schemaref` (§13 of `bloodbank/docs/event-naming.md`).
- Bloodbank hook install is owned by Bloodbank's fan-out
  (`~/code/33GOD/bloodbank/services/agent-hooks/sync.py --install`). Generated
  Hermes configs should call
  `~/.agents/hooks/bloodbank/publish.py --client hermes --hook <event>`, not a
  Hermes-local publisher.
- Before a live command proof, audit the current target's Bloodbank registry
  eligibility. Never enable a target merely to make a smoke test pass; command
  dispatch invokes a real agent and requires explicit operational authority.

## Voice / TTS defaults

Hermes uses the self-hosted Voxxy service at `https://vox.delo.sh` for TTS. A
desk's voice is controlled by `tts.vox.voice` (and the fallback `tts.voice`).

> **`tts.provider` MUST be `vox`, never `voxxy`.** Voxxy is the *service* (with
> swappable server-side engines: voxcpm, vibevoice, elevenlabs); the Hermes
> plugin's registry key is `vox` (`provider.name == "vox"`, plugin key
> `tts/vox`). `voxxy` matches no registered provider, so Hermes silently falls
> back to a built-in — ElevenLabs when `ELEVENLABS_API_KEY` is set, otherwise
> Edge — and you hear a stranger's voice with no error. **This has regressed
> twice** (canon: `voxxy/docs/plans/hermes-voxxy-tts-plugin.md`);
> `flume audit --rules hermes.fleet-config` now fails a base that sets anything
> else. Diagnose by asking the service which engine answered, which isolates
> Hermes from Voxxy:
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

See [references/voice-management.md](references/voice-management.md) for the full
workflow, manual fallback, and common pitfalls.

## Out of Scope

- **Project bootstrap / repo-local agent requests** → `33god-projects`.
- **Plane ticket lifecycle** → `project-lifecycle`.
- **Bloodbank event schemas or naming contract** → `bloodbank-integration`.
- **Generic SSOT config fan-out engine mechanics** → `agent-config-fanout`.
