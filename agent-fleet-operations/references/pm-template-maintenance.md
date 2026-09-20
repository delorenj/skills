---
pipeline-status:
  - new
---

# PM Template Maintenance

Use this when the operator says variants of:
- "update the template to capture X"
- "make this default for all PM agents"
- "propagate this to existing/future PMs"
- "do a Hermes workforce self-check for this repo"
- "all MCP servers failed in this repo but not in other CLIs"

Do not use this lane for a plain Hermes core update or shared default config
change. For those, use [hermes-fleet-updates.md](hermes-fleet-updates.md) and
avoid template/backfill work unless the runtime contract actually changed.

## Command Contract

Interpret:
- Input: `update template to capture <X>`
- Output:
  1) template changes applied
  2) current-employee backfill applied
  3) verification evidence (files + key lines)

## Self-check lane

When the request is investigative rather than prescriptive, run the self-check
lane before proposing fixes.

Trigger examples:
- "self-check the Hermes workforce for this repo"
- "these MCP servers fail here but not in other CLIs"
- "understand the intended architecture first, then explain drift"

Required outputs:
1. baseline architecture from `.project.json`, generated base-plus-delta desks,
   shared `~/.hermes/config.yaml`, and template/SSOT references
2. live reproduction (`hermes mcp list`, role wrappers, systemd status, gateway
   logs)
3. server-by-server ownership split (repo-local vs shared fleet/template vs
   external service)
4. ordered remediation plan
5. ticket routing by owning board

Detailed checklist and acceptance criteria:
- [fleet-self-check.md](fleet-self-check.md)
- Any deploy/backfill transaction: [pm-deployment.md](pm-deployment.md) and its
  machine-readable [pm-deployment-contract.json](pm-deployment-contract.json)

## Defaults

- Workforce CLI: `flume` (`~/.local/bin/flume` →
  `~/code/33GOD/flume/packages/flume-hr/dist/index.js`)
- Canonical global skill root: `/home/delorenj/.agents/skills`
- Runtime skill core: pinned by `[fleet] symlinked_runtime_skills` in
  `~/.config/hermes-agent-template/config.toml`; template options may only add
  skills, never drop a pinned member
- Self-check reference: this skill's
  `references/fleet-self-check.md`
- Org chart source of truth: `/home/delorenj/.hermes/agents-registry.yaml`
- Handbook: `/home/delorenj/code/33GOD/flume/contracts/handbook.yaml`
  (`flume handbook validate`)
- Template repo: `/home/delorenj/code/33GOD/hermes-agent-template`, vendored as a
  flume submodule at `~/code/33GOD/flume/templates/hermes-agent`; push the
  template repo, then bump the submodule pointer
- Ticket-provider adapters: canonical in
  `~/code/33GOD/krebs/adapters/tp/{plane,linear,trello}.sh`, vendored into
  `template/.scripts/providers/`
- Canonical service model: per agent only `hermes-<agent>-gateway.service`;
  Bloodbank command ingress is the single fleet-shared
  `hermes-fleet-bloodbank-gateway.service`. Per-agent heartbeat timers,
  consumers, and checkpoint timers are retired —
  `flume remediate hermes.registry-parity` converges registry drift and
  re-running `70-systemd.sh` deletes leftover heartbeat units
- Provisioning/board model (how agents bind to the repo's one board via
  `.project.json`): see the `33god-projects` skill
- Shared Hermes install: `~/.hermes/hermes-agent`, reached by generated agents
  through `~/.hermes/fleet.env`
- Shared config base: `~/.hermes/config.yaml`; each real named desk owns an
  override-only `config.delta.yaml` and a generated `config.yaml`

## Procedure

1. Classify `<X>`
- Hermes core update only: update `~/.hermes/hermes-agent`, restart long-running
  services, and stop here
- shared config/default model only: write `HERMES_HOME="$HOME/.hermes" hermes
  config set ...`, render/check named desks, and stop here
- rule/behavior prompt change
- script/bootstrap behavior
- reusable skill content
- PM orchestration workflow
- self-check / runtime drift investigation

2. Update template source of truth
- only do this for future-employee provisioning or PM behavior changes
- `template/SOUL.md.jinja` for PM behavior rules
- `template/.scripts/10-hermes-profile.sh` for desk/bootstrap defaults
- create/patch skills in global root (`/home/delorenj/.agents/skills/...`)

3. Backfill current employees
- Do this only when they must converge immediately or the runtime contract
  changed; do not backfill for a simple shared model/default update.
- Update each real named desk's `config.delta.yaml` only for local overrides,
  then render its generated `config.yaml`.
- Confirm desk state:
  - a legacy profile symlink aborts the transaction before mutation
  - `~/.hermes/profiles/<repo>-pm/` is a real directory
  - `config.delta.yaml` is a real override-only file and `config.yaml` carries
    the renderer marker and passes drift checks
  - `profile.yaml` contains identity metadata only and
    `hindsight/config.json` explicitly pins the agent bank
- Sync local fallback skill copy (if applicable):
  - `runtime/skills/software-development/subagent-driven-development/SKILL.md`
- Confirm launch/runtime integration:
  - repo-local runtime is ignored/untracked local state, not the desk or a
    nested repository
  - `git check-ignore` succeeds for runtime and `git ls-files` returns no
    runtime paths
  - systemd units set `HERMES_HOME` to the named desk path

4. Verify
- Confirm target lines exist in template files
- Confirm the desk delta contains only intentional local overrides and generated
  config matches base-plus-delta
- Confirm `hermes -p <repo>-pm config get model.default` resolves from the
  shared default when no local override exists
- Confirm skill content includes requested `<X>` behavior
- `flume audit` for the eight employee rules; `flume review --agent <repo>-pm`
  for the nine observation domains
- Observe `Result`, `ExecMainStatus`, and `NRestarts` through a bounded
  stabilization window
- Confirm unchanged reruns leave the registry byte-identical and preserve
  `provisioned_at` plus extension metadata

5. Report
- What changed
- Which employees were backfilled
- Any follow-up (restart gateway/session)
- For self-checks: which fixes belong to the repo board vs the Hermes Agent PM
  board vs service-specific boards

## Safety rules

- Never invent event naming contracts; follow repo specs.
- Keep one canonical source for each workflow/skill to prevent drift.
- Run repository and global Git hooks for normal commits, releases, and pushes;
  never bypass them.
- If existing agent scripts differ, patch them to template parity —
  `flume audit --rules hermes.pm-scaffold` lists exactly which files are stale or
  missing, and `flume remediate hermes.pm-scaffold` converges them.
- Do not copy `.env`, `auth.json`, sessions, memories, gateway state, or other
  runtime-local state between desks. Generated base-plus-delta config is
  maintenance machinery, not a reason to share local state.
- Do not run plain `uv sync` during Hermes core updates unless you have checked
  dependency changes and preserved any installed optional extras.
- For presence/work-state streams, use canonical 4-token Bloodbank event types
  (e.g. `bloodbank.system.heartbeat.received`,
  `bloodbank.agent.invocation.started|completed|failed`) rather than legacy short
  names. Their NATS subjects add the kind marker:
  `bloodbank.evt.system.heartbeat.received`. No version token belongs in either.
- Pass secret values only by pipe, anonymous FD, or process memory. Never put
  them in curl argv or unrelated child environments; a failed transient
  1Password validation preserves the last valid reference/marker for recovery.
- Tracked backup cleanup needs correct globs, scoped untracking, a committed and
  pushed removal verified against the remote tree, and preservation of
  unrelated dirty runtime state. See [pm-deployment.md](pm-deployment.md).

## Experiential findings (important)

- Existing employees' `.scripts/10-hermes-profile.sh` files can diverge from the
  template and may be missing canonical-skill sync blocks; inspect before
  changing and converge through the current generator rather than patching old
  symlink/native-inheritance assumptions.
- Use `/home/delorenj/.agents/skills` as the deployed global activation root;
  writable source definitions live once in Skillex `all-skills/`.
- Backfill must validate canonical skill projections and the desk delta/
  generated config pair; it must not create placeholder skills or silently mark
  a missing projection complete.
- Runtime `SOUL.md` may need direct backfill if you want behavior immediately
  without re-onboarding.
- Under generated desk config, do not backfill shared model/provider defaults
  into deltas; update `~/.hermes/config.yaml` once, render, and verify desks.

## Meta-agent scaffold pattern

If the operator wants a dedicated template-governor behavior, add to PM SOUL:
- Trigger phrase: `update template to capture <X>`
- Required steps: classify -> patch template -> backfill -> verify -> report
- Success criteria: future employees inherit + current ones converge.
