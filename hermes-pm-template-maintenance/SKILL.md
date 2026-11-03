---
name: hermes-pm-template-maintenance
description: |
  RETIRED (2026-11-03). Do not select this skill in any set, pack or manifest, and do not load it: it only redirects to agent-fleet-operations (references/pm-template-maintenance.md), which is in the global selection. Use agent-fleet-operations for all Hermes fleet, template, profile, and runtime work. Kept only so frozen desk projections that still link it do not dangle; it will be deleted once they resync.
pipeline-status:
  - new
---

# Hermes PM Template Maintenance (retired)

**Retired 2026-11-03. Do not select it.** It was a compatibility shim for the
rename to **agent-fleet-operations** and duplicates that skill's
`references/pm-template-maintenance.md`. It has been removed from the tracked
Skillex sets; this directory survives only so selections that still name it (the
live global manifest, desks whose projection is frozen) do not dangle until they
are re-selected and resynced. Do not add material here.

## Redirect

- Update template to capture X → `agent-fleet-operations` `references/pm-template-maintenance.md`
- Fleet self-check → `agent-fleet-operations` `references/fleet-self-check.md`
- Hermes core/shared config/template update → `agent-fleet-operations` `references/hermes-fleet-updates.md`
- Project bootstrap / repo-local agent provisioning → `33god-projects`
