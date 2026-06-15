# BMAD HTML Workspace

## Purpose
Convert BMAD's fragmented Markdown outputs into a single, browser-renderable HTML workspace that acts like a lightweight project cockpit.

## When to use
- User asks for visual planning/status dashboards.
- Project has many docs (plans, tasks, PRDs, artifacts) and needs one canonical view.
- User wants lightweight interactivity (filters, checklists, notes, diff panels) without a backend.

## What this skill produces
1. `workspace.html` generated from a reusable template.
2. Embedded JSON state (`<script type="application/json">`) with project metadata, tasks, docs, and artifacts.
3. A stable section layout so every repo gets the same UX primitives.

## Workflow
1. **Inventory project context**
   - Read key planning + implementation docs.
   - Extract: goals, milestones, backlog, active tasks, open questions, artifacts.
2. **Map content to the app model**
   - Populate the schema from `references/app-model.md`.
3. **Render scaffold**
   - Copy `templates/workspace.template.html` to a project file (e.g. `_bmad-output/workspace.html`).
   - Fill `window.BMAD_STATE` JSON.
4. **Refresh loop**
   - On subsequent runs, only update JSON + changed sections.

## UX sections (default)
- Header (project name, phase, health)
- Plan timeline
- Active TODO board
- Docs/artifacts index
- Decision log
- Risks + blockers
- Code diff snapshot panel
- Feedback widget (simple form placeholder)

## Guardrails
- Keep it single-file by default (portable + commit-friendly).
- No external JS/CSS dependencies unless user asks.
- Treat this as read/write workspace state, not a replacement for source docs.
- Every panel must degrade gracefully if data is missing.

## Starter actions
- Use `templates/workspace.template.html` as initial scaffold.
- Follow `references/app-model.md` for JSON shape.
- Add repo-specific adapters later (optional scripts) to auto-sync from BMAD docs.
