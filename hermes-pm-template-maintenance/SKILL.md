---
name: hermes-pm-template-maintenance
description: Standard workflow for PM agents to capture new governance rules/workflows/skills into the hermes PM template and propagate to existing agents.
---

# Hermes PM Template Maintenance

Use this when the operator says variants of:
- "update the template to capture X"
- "make this default for all PM agents"
- "propagate this to existing/future PM agents"

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

## Defaults

- Canonical global skill root: `/home/delorenj/.agents/skills`
- PM workflow skill path: `/home/delorenj/.agents/skills/subagent-driven-development/SKILL.md`
- Fleet registry source of truth: `/home/delorenj/.hermes/agents-registry.yaml`
- Template repo: `/home/delorenj/code/hermes-agent-template` (also vendored as a pjangler submodule at `~/code/pjangler/templates/hermes-agent`; push the template repo, then bump the submodule pointer)
- Provisioning/board model (how agents bind to the repo's one board via `.project.json`): see the `33god-projects` skill
- Shared Hermes install: `~/.hermes/hermes-agent`, reached by generated agents
  through `~/.hermes/fleet.env`
- Shared inherited config: `~/.hermes/config.yaml`; PM/scrum-master runtime
  `config.yaml` files must stay override-only

## Procedure

1. Classify `<X>`
- Hermes core update only: update `~/.hermes/hermes-agent`, restart long-running
  services, and stop here
- shared config/default model only: write `HERMES_HOME="$HOME/.hermes" hermes
  config set ...`, verify inherited profiles, and stop here
- rule/behavior prompt change
- script/bootstrap behavior
- reusable skill content
- PM orchestration workflow

2. Update template source of truth
- only do this for future-agent provisioning or PM behavior changes
- `template/SOUL.md.jinja` for PM behavior rules
- `template/.scripts/10-hermes-profile.sh` for profile/bootstrap defaults
- create/patch skills in global root (`/home/delorenj/.agents/skills/...`)

3. Backfill existing PM agents
- Do this only when existing agents must converge immediately or the runtime
  contract changed; do not backfill for a simple shared model/default update.
- Update each PM runtime config only for local overrides:
  - `skills.external_dirs.0 = /home/delorenj/.agents/skills`
- Confirm inherited profile metadata:
  - `runtime/profile.yaml` has `config.inherit_from: default`
  - `runtime/profile.yaml` has `config.save_mode: delta`
- Sync local fallback skill copy (if applicable):
  - `runtime/skills/software-development/subagent-driven-development/SKILL.md`
- Confirm launch/runtime integration:
  - `~/.hermes/profiles/<repo>-pm` points at `agents/hermes/pm/runtime/`
  - systemd units set `HERMES_HOME` to the named profile path

4. Verify
- Confirm target lines exist in template files
- Confirm runtime config contains only intentional local overrides
- Confirm `hermes -p <repo>-pm config get model.default` resolves from the
  shared default when no local override exists
- Confirm skill content includes requested `<X>` behavior

5. Report
- What changed
- Which agents were backfilled
- Any follow-up (restart gateway/session)

## Safety rules

- Never invent event naming contracts; follow repo specs.
- Keep one canonical source for each workflow/skill to prevent drift.
- If existing agent scripts differ, patch them to template parity.
- Do not copy `.env`, `auth.json`, sessions, memories, gateway state, or other
  runtime-local state between profiles. Only `config.yaml` participates in
  inherited config.
- Do not run plain `uv sync` during Hermes core updates unless you have checked
  dependency changes and preserved any installed optional extras.
- For presence/work-state streams, use Bloodbank v1 event names (e.g. `bloodbank.v1.system.heartbeat.received`, `bloodbank.v1.agent.invocation.started|completed|failed`) rather than legacy short names.

## Experiential findings (important)

- Existing PM agent `.scripts/10-hermes-profile.sh` files can diverge from template and may be missing canonical-skill sync blocks; do not assume old_string patch matches — inspect file first, then inject block after `terminal.cwd` config.
- Use `/home/delorenj/.agents/skills` as canonical root (not `/home/delorenj/code/skillex/all-skills`) for deployed PM fleet inheritance.
- Backfill must update both:
  1) runtime `config.yaml` (`skills.external_dirs.0`)
  2) local fallback skill copy under runtime skills path.
- Runtime `SOUL.md` may need direct backfill if you want behavior immediately without reprovisioning.
- Under inherited profile config, do not backfill shared model/provider defaults
  into runtime `config.yaml`; update `~/.hermes/config.yaml` once and verify
  inherited profiles resolve it.

## Meta-agent scaffold pattern

If operator wants a dedicated template-governor behavior, add to PM SOUL:
- Trigger phrase: `update template to capture <X>`
- Required steps: classify -> patch template -> backfill -> verify -> report
- Success criteria: future agents inherit + existing agents converge.
