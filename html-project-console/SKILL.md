---
name: html-project-console
description: >
  Scaffold and maintain a single-file HTML project console that replaces scattered
  markdown status docs with one browser-renderable control center for planning,
  progress tracking, artifacts, and human feedback.
---

# html-project-console

## Purpose

Use this skill when the user wants a **browser-native project cockpit** instead of
many markdown files. It creates a predictable `project-console.html` that the
agent can keep updating over time.

## What this skill scaffolds

1. `templates/project-console.html` — a no-build, single-file SPA starter.
2. `commands/bootstrap-project-console.md` — reusable prompt to instantiate the
   file into any target project path.
3. `references/design-principles.md` — shared UX and content model rules.

## Workflow

1. Copy `templates/project-console.html` to the chosen project location as
   `project-console.html`.
2. Fill the `window.PROJECT_CONSOLE_DATA` JSON object with:
   - vision
   - plan
   - todo
   - changelog
   - artifacts
   - feedback
3. Keep updates append-only where possible (`changelog`, `decisions`) for
   traceability.
4. Regenerate only the data object unless user asks for layout changes.

## Guardrails

- Keep it dependency-free (plain HTML/CSS/JS only).
- Keep all data local in the file by default.
- Preserve section IDs for stable automation targets.
- Prefer progressive enhancement over framework complexity.

## Extension ideas

- Add a `<dialog>`-based feedback form that writes JSON snippet for copy/paste.
- Add side-by-side colored diffs for latest changed files.
- Add Mermaid rendering fallback if available.
