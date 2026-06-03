---
name: drumjangler-project-bmad
description: Project-specific guardrails for Drumjangler BMAD work. Use when starting Drumjangler planning or development, reconciling MVP or Linear work, or when a request mentions BMAD in this repo.
---

# Drumjangler Project BMAD Guardrails

## Purpose

Keep Drumjangler aligned with the real BMad Method installation and the product north star: a drummer co-pilot teaching app, not only a stem-splitting utility.

## Required Orientation

1. Run `scripts/session-hooks/session-start.sh` at the start of meaningful planning or development work.
2. Confirm the formal BMAD install exists at `_bmad/`. If uncertain, run `npx --yes bmad-method@latest status`.
3. Fetch and read the Linear document named `Drumjangler Operating Ledger`: https://linear.app/delorenj/document/drumjangler-operating-ledger-1dc19818bd1f
4. Treat `_bmad/` plus the official `bmad-*` skills as the source of BMAD workflow. Do not invent alternate BMAD directories, commands, prompts, or document systems.
5. Use `bmad-help` when workflow routing is unclear. Then use the specific official BMAD skill it recommends, such as `bmad-prd`, `bmad-create-epics-and-stories`, `bmad-create-story`, `bmad-dev-story`, `bmad-quick-dev`, or `bmad-code-review`.
6. Read existing `_bmad-output/` artifacts before planning. The top-level files are legacy bootstrap artifacts; reconcile them into the installed `planning-artifacts/` and `implementation-artifacts/` layout as work proceeds.
7. Treat Linear ticket status as evidence to verify, not truth to trust. Reconcile tickets against the repo and app behavior before closing, reopening, or implementing.
8. Prioritize MVP work that advances the beta path: library/history, local watch/import, original/drums/drumless playback, token economics, purchase flow, and reliable split processing.
9. If BMAD artifacts are missing or stale, rerun the installer rather than hand-creating BMAD internals:

```bash
npx --yes bmad-method@latest install --modules bmm --tools codex,claude-code --output-folder _bmad-output
```

## Session End

Run `scripts/session-hooks/session-end.sh` before finalizing meaningful planning or development work.

Update the Linear `Drumjangler Operating Ledger` every meaningful session. If Now / Next / Later did not change, append a session note with:

```text
Horizon impact: none. Status quo preserved.
```

## Issue Closure Discipline

Follow `docs/operations/agent-operating-contract.md` for all issue-state changes.

- Start issue work with `scripts/agent/issue-start.sh <ISSUE_ID>`.
- Inspect evidence with `scripts/agent/issue-evidence.sh <ISSUE_ID>`.
- Do not close or recommend closing Linear issues unless `scripts/agent/issue-close-gate.sh <ISSUE_ID>` passes.
- If the gate fails, keep the issue open and record the missing evidence.
- Workflow scripts emit BloodBank-style local events; the event contract lives at `docs/operations/bloodbank-events.md`.

## Output Discipline

- Planning artifacts belong under `_bmad-output/planning-artifacts/`.
- Implementation artifacts, stories, reviews, sprint status, and retrospectives belong under `_bmad-output/implementation-artifacts/`.
- Durable product or engineering knowledge belongs under `docs/`.
- Keep changes tied to repo evidence, Linear evidence, or BMAD workflow outputs.
- The detailed BMAD + Linear hook contract lives at `docs/operations/bmad-linear-operating-model.md`.
- The multi-agent operating contract lives at `docs/operations/agent-operating-contract.md`.
- The BloodBank workflow event contract lives at `docs/operations/bloodbank-events.md`.
