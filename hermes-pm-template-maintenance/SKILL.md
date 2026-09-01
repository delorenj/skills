---
name: hermes-pm-template-maintenance
description: |
  DEPRECATED compatibility shim. Use agent-fleet-operations for all Hermes fleet, template, profile, and runtime work. This shim exists only so existing references resolve during migration; do not add new material here.
pipeline-status:
  - new
---

# Hermes PM Template Maintenance (deprecated)

This skill has been renamed/wrapped as **agent-fleet-operations**. Route all Hermes fleet, template, profile, runtime, and PM backfill work there.

## Redirect

- Update template to capture X → `agent-fleet-operations` `references/pm-template-maintenance.md`
- Fleet self-check → `agent-fleet-operations` `references/fleet-self-check.md`
- Hermes core/shared config/template update → `agent-fleet-operations` `references/hermes-fleet-updates.md`
- Project bootstrap / repo-local agent provisioning → `33god-projects`
