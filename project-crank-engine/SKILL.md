---
name: project-crank-engine
description: Set up aggressive recurring project execution loops (“Crank Engines”) using cron + agent turns, with a strict finish contract. Use when the user asks to keep cranking on a project/sprint (e.g. “set up an aggressive crank engine”, “keep pushing until sprint is done”, “run status every X minutes”), and needs configurable project, recipients, focus scope, quantifiable completion criteria, screenshot evidence, and manager-go/no-go enforcement.
---

# Project Crank Engine

Create repeatable project execution loops that:
1. dispatch focused work/status prompts,
2. run at a user-selected crank intensity (light → aggressive),
3. enforce a measurable finish definition,
4. require visual proof (screenshot) when possible,
5. keep running until completion is truly met.

## Required Inputs

Collect these before creating/updating a crank job:
- `project`: repo/product name (e.g. SVGMe)
- `agentId`: target agent (e.g. `svgme`)
- `pace`: `light` | `balanced` | `aggressive` | custom interval
- `goal`: explicit sprint objective
- `scope`: what to crank on now (epic/story/ticket range)
- `recipient`: where updates are delivered (channel + to + account)
- `finish_contract`: quantifiable done criteria (must be measurable)

If any are missing, ask once in a compact checklist.

## Pace Slider (Preset Profiles)

Use these defaults unless the user overrides cadence directly:

- **light**: every 30 min, status-first updates, corrective push only for stale/no-progress cycles
- **balanced**: every 15 min, execution + status, corrective push on missed cycle goals
- **aggressive**: every 8–10 min, execution-heavy, immediate corrective "back in the oven" on any unmet cycle target

If user says “aggressive crank engine,” map to aggressive preset.
If user says “light crank engine” or “check every half hour,” map to light preset.

## Finish Contract (Non-Negotiable)

Never accept vague “done.” Require all of:
- **Ticket metric:** e.g. `N/N sprint stories in Done`
- **Code metric:** PR merged count / branch state / test pass signal
- **Evidence artifact:** screenshot (preferred) + command evidence

Minimum evidence set per completion claim:
1. board metric (counts),
2. one screenshot of board/PR state,
3. final command-backed repo state summary.

If criteria fail, decision is **NOT DONE** → send corrective prompt and keep crank job active.

## Prompt Template

Use `references/prompt-templates.md`.
For custom prompts, keep this structure:
1. Mission now
2. Evidence checklist
3. Quantifiable finish contract
4. Decision rule (`DONE` vs `NOT DONE`)
5. Next action if `NOT DONE`

Optional helper:
- `scripts/render_crank_prompt.py` renders a standardized prompt from parameters.

## Cron Creation Pattern

Default to isolated agent turn jobs.

- `sessionTarget`: `isolated`
- `payload.kind`: `agentTurn`
- `schedule.kind`: `every`
- `delivery.mode`: `announce`

Set interval from pace preset unless user provides explicit cadence.

## Post-Create Verification (Required)

After creating/updating crank job:
1. Confirm job exists and is enabled.
2. Confirm `delivery` route is valid (real channel/to/account values, not labels).
3. Force a run once when safe.
4. Verify run history shows `delivered` (not just `status: ok`).

If `not-delivered`, fix routing immediately.

## Manager Decision Loop

On each crank update:
- evaluate against finish contract,
- if incomplete: send “back in the oven” corrective direction and continue,
- if complete: announce completion with evidence summary and offer to disable/remove job.

Do not disable active crank jobs without explicit user approval (unless user asked “run until done, then stop”).

## Decision Authority (Critical)

Default behavior is **execute-forward**, not ask-forward.

- Crank worker should continue shipping the next concrete slice unless blocked.
- Manager (Cack) assumes provisional go-ahead for normal sequencing decisions.
- Escalate only for real blockers or high-impact tradeoffs (security/risk/scope).
- Do not spam user with repetitive status-only updates lacking progress delta.

Required status format each cycle:
1) **Progress delta since last cycle** (what shipped)
2) **Current measurable gap to finish contract**
3) **Next action already started**
4) **Escalation needed?** (yes/no + exact decision if yes)

## Quick Example Trigger

User: “Set up an aggressive Crank Engine on project X to finish the sprint.”

Execution behavior:
- create `every 10m` crank job,
- require measurable sprint finish contract,
- require screenshot evidence,
- keep looping until manager confirms pass.
