# Component Map

The canonical component list lives in `33god-platform/components.yaml` and
`33god-platform/components/*.yaml`.

Use those manifests over stale prose docs when deciding ownership, health
commands, compose profiles, and changelog topics.

Plane and n8n are integration boundaries, not active component-registry owners.
Plane owns signed provider actions; the Bloodbank-owned n8n custom node owns
authentication and normalization; Bloodbank owns the resulting contract and
transport. Record cross-boundary changes in the pipeline changelog even when no
new component manifest is added.
