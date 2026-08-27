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
  board id, URL, and state);
- the `agents` map populated by later provisioning.

There is no separate `.plane.json`, no role-suffixed PM board, and no board
identity inferred from a summary line. Read `.project.json` itself.

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

PJangler renders `agents/hermes/pm/`, binds it to the board already recorded in
`.project.json`, adds one agent entry to `.project.json`, and reconciles the
matching fleet registry record. It must not create a second board or duplicate
an existing agent entry.

## 3. Profile and local runtime contract

The deployment creates a real named profile such as
`~/.hermes/profiles/<repo>-pm/`. It is not a symlink to repo-local runtime.

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

Run the relevant read-only `pj audit` and profile-renderer `check`, then rerun
`pj hermes-agent --yes`. The rerun must be convergent: no duplicate identity,
new tracked runtime, retired units, credential-less crash loop, shared-gateway
change, or unexplained stable-file drift.

Required runtime skills must resolve to regular
`~/.agents/skills/<canonical-name>/SKILL.md` files before deployment is marked
complete. Repair Skillex projection when one is absent; never create a
placeholder merely to silence validation.

## Template resolution

PJangler normally uses its vendored, version-locked Hermes template. The
`PJANGLER_HERMES_TEMPLATE` override is for explicitly scoped template
development only. Template source changes, submodule bumps, and fleet backfills
belong to their respective repositories and boards, not the target project.
