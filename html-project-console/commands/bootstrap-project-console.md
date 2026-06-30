---
pipeline-status:
  - new
---
# Bootstrap Project Console

Use this command when a user wants to consolidate markdown planning artifacts into
one browser-renderable file.

## Steps

1. Copy `templates/project-console.html` to `<target>/project-console.html`.
2. Inventory current docs (plan, tasks, artifacts, changelog).
3. Populate `window.PROJECT_CONSOLE_DATA` from that inventory.
4. Add repo-specific links under `artifacts`.
5. Summarize what was migrated and what remains.
