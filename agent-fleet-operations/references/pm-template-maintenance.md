---
name: hermes-pm-template-maintenance
description: Standard workflow for PM agents to capture new governance rules/workflows/skills into the hermes PM template and propagate to existing agents.
pipeline-status:
  - new
---

# Hermes PM Template Maintenance

Use this when the operator says variants of:
- "update the template to capture X"
- "make this default for all PM agents"
- "propagate this to existing/future PM agents"
- "do a Hermes fleet self-check for this repo"
- "all MCP servers failed in this repo but not in other CLIs"

Do not use this skill for a plain Hermes core update or shared default config
change. For those, use the `33god-projects` skill's
`references/hermes-fleet-updates.md` workflow and avoid template/backfill work
unless the runtime contract actually changed.

## Command Contract

Interpret:
- Input: `update template to capture <X>`
- Output:
  1) template changes applied
  2) existing PM agent backfill applied
  3) verification evidence (files + key lines)

## Fleet self-check lane

When the request is investigative rather than prescriptive, run the fleet self-check lane before proposing fixes.

Trigger examples:
- "self-check the Hermes fleet for this repo"
- "these MCP servers fail here but not in other CLIs"
- "understand the intended architecture first, then explain drift"

Required outputs:
1. baseline architecture from `.project.json`, generated base-plus-delta profiles, shared `~/.hermes/config.yaml`, and template/SSOT references
2. live reproduction (`hermes mcp list`, role wrappers, systemd status, runtime logs)
3. server-by-server ownership split (repo-local vs shared fleet/template vs external service)
4. ordered remediation plan
5. ticket routing by owning board

Detailed checklist and acceptance criteria:
- `references/fleet-self-check.md`
- Any deploy/backfill transaction: `references/pm-deployment.md` and its
  machine-readable `references/pm-deployment-contract.json`

## Defaults

- Canonical global skill root: `/home/delorenj/.agents/skills`
- PM workflow skill path: `/home/delorenj/.agents/skills/subagent-driven-development/SKILL.md`
- Fleet self-check reference: `/home/delorenj/.agents/skills/hermes-pm-template-maintenance/references/fleet-self-check.md`
- Fleet registry source of truth: `/home/delorenj/.hermes/agents-registry.yaml`
- Template repo: `/home/delorenj/code/33GOD/hermes-agent-template` (also vendored as a pjangler submodule at `~/code/33GOD/pjangler/templates/hermes-agent`; push the template repo, then bump the submodule pointer)
- Canonical service model: per agent only `hermes-<agent>-gateway.service` + `hermes-<agent>-heartbeat.timer`; Bloodbank command ingress is the single fleet-shared `hermes-fleet-bloodbank-gateway.service` (no per-agent consumers/checkpoint timers — `pj migrate hermes.registry-parity` converges drift)
- Provisioning/board model (how agents bind to the repo's one board via `.project.json`): see the `33god-projects` skill
- Shared Hermes install: `~/.hermes/hermes-agent`, reached by generated agents
  through `~/.hermes/fleet.env`
- Shared config base: `~/.hermes/config.yaml`; each real named profile owns an
  override-only `config.delta.yaml` and a generated `config.yaml`
- Immutable PM skill core: `33god-projects`, `delonet-conventions`,
  `delonet-dotenv`, `hermes-pm-template-maintenance`, `hindsight`, and
  `subagent-driven-development`; template options may only add skills

## Procedure

1. Classify `<X>`
- Hermes core update only: update `~/.hermes/hermes-agent`, restart long-running
  services, and stop here
- shared config/default model only: write `HERMES_HOME="$HOME/.hermes" hermes
  config set ...`, render/check named profiles, and stop here
- rule/behavior prompt change
- script/bootstrap behavior
- reusable skill content
- PM orchestration workflow
- fleet self-check / runtime drift investigation

2. Update template source of truth
- only do this for future-agent provisioning or PM behavior changes
- `template/SOUL.md.jinja` for PM behavior rules
- `template/.scripts/10-hermes-profile.sh` for profile/bootstrap defaults
- create/patch skills in global root (`/home/delorenj/.agents/skills/...`)

3. Backfill existing PM agents
- Do this only when existing agents must converge immediately or the runtime
  contract changed; do not backfill for a simple shared model/default update.
- Update each real named profile's `config.delta.yaml` only for local overrides,
  then render its generated `config.yaml`.
- Confirm profile state:
  - a legacy profile symlink aborts the transaction before mutation
  - `~/.hermes/profiles/<repo>-pm/` is a real directory
  - `config.delta.yaml` is a real override-only file and `config.yaml` passes
    renderer drift checks
  - `profile.yaml` contains identity metadata only and
    `hindsight/config.json` explicitly pins the agent bank
- Sync local fallback skill copy (if applicable):
  - `runtime/skills/software-development/subagent-driven-development/SKILL.md`
- Confirm launch/runtime integration:
  - repo-local runtime is ignored/untracked local state, not the profile or a
    nested repository
  - `git check-ignore` succeeds for runtime and `git ls-files` returns no
    runtime paths
  - systemd units set `HERMES_HOME` to the named profile path

4. Verify
- Confirm target lines exist in template files
- Confirm profile delta contains only intentional local overrides and generated
  config matches base-plus-delta
- Confirm `hermes -p <repo>-pm config get model.default` resolves from the
  shared default when no local override exists
- Confirm skill content includes requested `<X>` behavior
- Observe `Result`, `ExecMainStatus`, `NRestarts`, and the latest heartbeat
  service result through a bounded stabilization window
- Confirm unchanged registry reruns are byte-identical and preserve
  `provisioned_at` plus extension metadata

5. Report
- What changed
- Which agents were backfilled
- Any follow-up (restart gateway/session)
- For self-checks: which fixes belong to repo board vs Hermes Agent PM vs service-specific boards

## Safety rules

- Never invent event naming contracts; follow repo specs.
- Keep one canonical source for each workflow/skill to prevent drift.
- Run repository and global Git hooks for normal commits, releases, and pushes;
  never bypass them.
- If existing agent scripts differ, patch them to template parity.
- Do not copy `.env`, `auth.json`, sessions, memories, gateway state, or other
  runtime-local state between profiles. Generated base-plus-delta config is
  maintenance machinery, not a reason to share local state.
- Do not run plain `uv sync` during Hermes core updates unless you have checked
  dependency changes and preserved any installed optional extras.
- For presence/work-state streams, use canonical 4-token Bloodbank event types (e.g. `bloodbank.system.heartbeat.received`, `bloodbank.agent.invocation.started|completed|failed`) rather than legacy short names. Their NATS subjects add the kind marker: `bloodbank.evt.system.heartbeat.received`. No version token belongs in either.
- Pass secret values only by pipe, anonymous FD, or process memory. Never put
  them in curl argv or unrelated child environments; a failed transient
  1Password validation preserves the last valid reference/marker for recovery.
- Tracked backup cleanup needs correct globs, scoped untracking, a committed and
  pushed removal verified against the remote tree, and preservation of
  unrelated dirty runtime state. See `references/pm-deployment.md` for details.

## Experiential findings (important)

- Existing PM agent `.scripts/10-hermes-profile.sh` files can diverge from the
  template and may be missing canonical-skill sync blocks; inspect before
  changing and converge through the current generator rather than patching old
  symlink/native-inheritance assumptions.
- Use `/home/delorenj/.agents/skills` as the deployed global activation root;
  writable source definitions live once in Skillex `all-skills/`.
- Backfill must validate canonical skill projections and the profile delta/
  generated config pair; it must not create placeholder skills or silently mark
  a missing projection complete.
- Runtime `SOUL.md` may need direct backfill if you want behavior immediately without reprovisioning.
- Under generated profile config, do not backfill shared model/provider defaults
  into deltas; update `~/.hermes/config.yaml` once, render, and verify profiles.

## Meta-agent scaffold pattern

If operator wants a dedicated template-governor behavior, add to PM SOUL:
- Trigger phrase: `update template to capture <X>`
- Required steps: classify -> patch template -> backfill -> verify -> report
- Success criteria: future agents inherit + existing agents converge.
