---
pipeline-status:
  - new
---
# Project creation via PJangler

PJangler owns project identity and Hermes PM deployment. Use its installed `pj`
entry point rather than invoking Copier, template scripts, or systemd directly.

## 1. Bootstrap the repository

CommonProject establishes the repository skeleton, its one ticket board, and
the canonical repo-root `.project.json`. From the supported project bootstrap
surface:

```bash
mise run init-project
# or the repository's supported non-interactive init task
```

The resulting `.project.json` owns:

- `project_name`, `project_slug`, description, and absolute `repo_path`;
- the single `ticket_provider` binding (provider, workspace, identifier,
  board id, and state);
- the `agents` map populated by later provisioning.

There is no separate `.plane.json`, no role-suffixed PM board, and no board
identity inferred from a summary line. A valid Plane binding has `state:
linked` and a live-resolved identifier/board id. Never persist
`ticket_provider.board_url`; construct a URL transiently when presenting it.

Read and parse the raw manifest before mutation. Malformed JSON aborts with the
manifest and all other state byte-unchanged. Hold one project lock across
read/validation, the live Plane check-or-create, and atomic manifest
replacement so concurrent deploys cannot create or publish split identity.

## 2. Deploy the unified PM

The official non-interactive deployment is:

```bash
cd <repo>
pj hermes-agent --yes
```

The PM is the only supported role for the standard project deployment. The
retired scrum-master's ticket-sentinel duties run inside the PM heartbeat, so
there is no paired agent or second provisioning prompt.

Before running it, seal the target repository (including nested repositories),
`.project.json`, matching registry/profile state, target systemd units, and the
fleet-shared gateway. Preserve dirty work exactly; do not reset, clean, stash,
rewrite, or convert repo-local runtime into a tracked submodule. The detailed
before/after and rerun contract is in **agent-fleet-operations**
`references/pm-deployment.md`.

The seal always includes content hashes for every dirty and untracked path and
HEAD/index/status plus dirty/untracked hashes for every nested Git repository;
it is not optional just because a working tree was already known to be dirty.

PJangler renders `agents/hermes/pm/`, binds it to the board already recorded in
`.project.json`, adds one agent entry to `.project.json`, and reconciles the
matching fleet registry record. It must not create a second board or duplicate
an existing agent entry. The linked Plane identifier and board id are checked
live before the atomic manifest write.

## 3. Profile and local runtime contract

The deployment creates a real named profile such as
`~/.hermes/profiles/<repo>-pm/`. It is not a symlink to repo-local runtime.
If that path is a legacy symlink, abort before any write; migration is a
separate explicitly scoped action.

- `<profile>/config.yaml` is generated from the fleet base
  `~/.hermes/config.yaml` plus `<profile>/config.delta.yaml`.
- `config.delta.yaml` is the small, real, hand-edited override source (usually
  just the project working directory). Hermes does not natively interpret
  `config.inherit_from` metadata.
- `profile.yaml` describes identity/role; it does not implement config
  inheritance.
- `hindsight/config.json` explicitly pins the profile's identity-memory bank.
- `agents/hermes/pm/runtime/` is ignored, untracked local state. It is not a
  profile, submodule, or nested repository; only explicit owned-state links may
  connect it to the named profile.

Prove both halves of runtime exclusion:

```bash
git check-ignore -q -- agents/hermes/pm/runtime/
git ls-files -- agents/hermes/pm/runtime/  # stdout must be empty
```

Never hand-edit generated `config.yaml`. Change the delta and use the canonical
profile renderer. Never place literal credentials in shared or profile `.env`;
use the fleet's `secrets.onepassword.env` mappings to `op://DeLoSecrets/...`
references. Secret migration is a separate approval-gated operation.

## 4. Services and reconciliation

The standard per-agent service surfaces are:

1. `hermes-<agent-id>-gateway.service` for chat ingress;
2. `hermes-<agent-id>-heartbeat.timer` and its oneshot service for sentinel and
   reconciliation work.

They have separate health semantics. If a channel credential was supplied, the
gateway should be enabled and active without restart churn. If no channel
credential was supplied, chat ingress must be explicitly deferred and the
gateway left disabled and inactive; missing credentials must never create a
crash loop. The heartbeat timer remains independently enabled/healthy, while
its oneshot service can be inactive between successful ticks.

Deferred means the profile delta explicitly sets
`platforms.telegram.enabled: false` and `platforms.slack.enabled: false`, even
when the fleet base enables a channel. Only verified ownership of the PM's
dedicated channel credential may set its platform true.

Bloodbank command ingress belongs to the existing fleet-shared
`hermes-fleet-bloodbank-gateway.service`. A repo deploy must leave that shared
unit/config/state untouched. It creates no per-agent consumer, checkpoint
timer, or filesystem inbox.

## 5. Verify direct state and rerun

Do not accept the deployer's summary or a green aggregate audit as complete
proof. Directly compare:

- `.project.json` and the one matching `~/.hermes/agents-registry.yaml` row;
- the real profile directory, generated config, real delta, metadata, and
  Hindsight pin;
- exact unit-file/enabled/active/failed/restart state for gateway and heartbeat;
- pre/post target and nested-repository status;
- pre/post shared gateway identity and state.

Observe services through a bounded stabilization window. Check `Result`,
`ExecMainStatus`, restart-count stability, and the latest heartbeat service
result; a single `is-active` sample cannot establish success.

Run the relevant read-only `pj audit` and profile-renderer `check`, then rerun
`pj hermes-agent --yes`. The rerun must be convergent: no duplicate identity,
new tracked runtime, retired units, credential-less crash loop, shared-gateway
change, or unexplained stable-file drift.

The registry itself must be byte-identical on an unchanged rerun, preserving
the original `provisioned_at` and extension/unknown metadata rather than
reconstructing the row.

The immutable required core is `33god-projects`, `delonet-conventions`,
`delonet-dotenv`, `hermes-pm-template-maintenance`, `hindsight`, and
`subagent-driven-development`. Each must resolve to a regular
`~/.agents/skills/<canonical-name>/SKILL.md` before deployment is marked
complete. Configuration may add optional skills but never subtract the core.
Repair Skillex projection when one is absent; never create a placeholder merely
to silence validation.

## Template resolution

PJangler normally uses its vendored, version-locked Hermes template. The
`PJANGLER_HERMES_TEMPLATE` override is for explicitly scoped template
development only. Template source changes, submodule bumps, and fleet backfills
belong to their respective repositories and boards, not the target project.
