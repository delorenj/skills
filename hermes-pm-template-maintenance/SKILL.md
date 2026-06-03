---
name: hermes-pm-template-maintenance
description: Standard workflow for PM agents to capture new governance rules/workflows/skills into the hermes PM template and propagate to existing agents.
version: 1.0.0
pipeline-status:
  - new
---

# Hermes PM Template Maintenance

Use this when the operator says variants of:
- "update the template to capture X"
- "make this default for all PM agents"
- "propagate this to existing/future PM agents"

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
- Template repo: `/home/delorenj/code/hermes-agent-template`

## Procedure

1. Classify `<X>`
- rule/behavior prompt change
- script/bootstrap behavior
- reusable skill content
- PM orchestration workflow

2. Update template source of truth
- `template/SOUL.md.jinja` for PM behavior rules
- `template/.scripts/10-hermes-profile.sh` for profile/bootstrap defaults
- create/patch skills in global root (`/home/delorenj/.agents/skills/...`)

3. Backfill existing PM agents
- Update each PM runtime config:
  - `skills.external_dirs.0 = /home/delorenj/.agents/skills`
- Sync local fallback skill copy (if applicable):
  - `runtime/skills/software-development/subagent-driven-development/SKILL.md`

4. Verify
- Confirm target lines exist in template files
- Confirm runtime config points to `/home/delorenj/.agents/skills`
- Confirm skill content includes requested `<X>` behavior

5. Report
- What changed
- Which agents were backfilled
- Any follow-up (restart gateway/session)

## Safety rules

- Never invent event naming contracts; follow repo specs.
- Keep one canonical source for each workflow/skill to prevent drift.
- If existing agent scripts differ, patch them to template parity.
- For presence/work-state streams, use Bloodbank v1 event names (e.g. `bloodbank.v1.system.heartbeat.received`, `bloodbank.v1.agent.invocation.started|completed|failed`) rather than legacy short names.

## Experiential findings (important)

- Existing PM agent `.scripts/10-hermes-profile.sh` files can diverge from template and may be missing canonical-skill sync blocks; do not assume old_string patch matches — inspect file first, then inject block after `terminal.cwd` config.
- Use `/home/delorenj/.agents/skills` as canonical root (not `/home/delorenj/code/skillex/all-skills`) for deployed PM fleet inheritance.
- Backfill must update both:
  1) runtime `config.yaml` (`skills.external_dirs.0`)
  2) local fallback skill copy under runtime skills path.
- Runtime `SOUL.md` may need direct backfill if you want behavior immediately without reprovisioning.

## Meta-agent scaffold pattern

If operator wants a dedicated template-governor behavior, add to PM SOUL:
- Trigger phrase: `update template to capture <X>`
- Required steps: classify -> patch template -> backfill -> verify -> report
- Success criteria: future agents inherit + existing agents converge.
