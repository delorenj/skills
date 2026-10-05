---
name: g33-33god-integration
description: Routes 33GOD ecosystem work and turns evidence into BMAD handoffs. Use when the user says 'setup g33', 'install 33GOD Integration', 'route 33GOD work', '33GOD preflight', or 'evidence to handoff'.
---

# 33GOD Integration (g33)

## Overview

Expansion module for installed BMAD. g33 is a consult/routing/evidence surface
that informs existing 33GOD workflows. It is NOT an employee, orchestrator,
lifecycle engine, or scheduler, and it never seizes lifecycle state.

Three capabilities plus module setup:

| Code | Capability | What it does |
| --- | --- | --- |
| PF | preflight | Validate project bindings, tool/skill availability, and Krebs enrollment |
| ER | ecosystem-route | Route a work request to owner components with contract entrypoints |
| EH | evidence-to-handoff | Turn an evidence bundle into a BMAD implementation handoff |
| SU | configure | Install or reconfigure this module (safe, idempotent) |

## On Activation

1. Read `./assets/module.yaml` for module metadata (code, version) and variable defaults.
2. If `{project-root}/_bmad/config.yaml` has no `g33` section, or the user passed `setup`/`configure`/`install`, load `./assets/module-setup.md` and complete registration first.
3. Route to the requested capability below.

## Capabilities

All commands resolve `{project-root}` to the actual absolute project root before
invocation. `--json` emits machine-readable output and exits 0 on findings
(exit nonzero only for usage/IO errors).

### Preflight (PF)

```bash
python3 {skill-root}/scripts/g33_cli.py preflight --project-root {project-root} --json
```

Reports PASS/FAIL/WARN per check: `.project.json` ticket binding, Krebs
execution enrollment via the canonical policyVersion-2 executionReadiness
adapter (managed must be fully ready — FAIL on any gap; invalid mode is FAIL
never downgraded to legacy; shadow may be incrementally enrolled as WARN but
never certifies managed readiness; absent/legacy is a WARN), tool availability
(`px`, `node`, `uv`, `python3` via PATH), and the effective module config from
`_bmad/custom/config.toml` (consumed, not ornamental).

### Ecosystem Route (ER)

```bash
python3 {skill-root}/scripts/g33_cli.py route --project-root {project-root} --request "<what the work is>" --json
```

Classifies the request against `./assets/ecosystem-map.toml` and returns owning
components with contract entrypoints (repo-relative paths and CLI commands —
never machine-absolute paths). Consumes the project's installed
`[modules.g33]` answers: `ecosystem_root` flows into the output and
`doctrine_pointer` overrides the bundled default (`momo/PILLARS.md`, pillars
1-4) for citations. Also cites the Bloodbank event-naming contract. Never
invents events, claims nonexistent handoffs, or calls services.

### Evidence-to-Handoff (EH)

```bash
python3 {skill-root}/scripts/g33_cli.py evidence --project-root {project-root} --bundle <evidence.json> --out <handoff.md> --json
```

Reads an evidence bundle (JSON: `acceptance_criteria`, `worker_claims`,
`diff_path`, `test_proof_path`, optional `review_notes`, `implementer`,
`reviewer`, separate `installed_evidence_path` / `deployed_evidence_path` receipts;
see README for their schema) and writes a handoff document that separates implemented / tested /
installed / deployed / outstanding. Recorded evidence is read and hashed; supported textual diff hunks/counts
and complete supported count/pytest summary lines with per-command exits are validated.
Prose/expected-output notes cannot certify test results; foreign YAML namespaces
are refused by parsed key identity and section-scoped ownership. Worker claims need explicit
`claim_evidence` links to known acceptance criteria and parsed changed paths.
Missing/invalid/unmapped/failing evidence stays claimed-unverified or NOT CLEAN.
Installed/deployed receipt text remains claimed-unverified even with valid schema;
receipt commands are never executed. See README for the complete bundle schema. The reviewer != implementer attestation is
VALIDATED from distinct declared identities in the bundle (or explicitly NOT
VALIDATED). Decision compass cites pillars by number from the doctrine path
recorded in the owner map or the project's doctrine_pointer override.

## Guards

- Never assume Krebs enrollment. Validate it from `.project.json` when mode is
  managed|shadow; otherwise route to the legacy adapter.
- Never assume every board is Krebs-enrolled.
- No new event types — event identity follows the Bloodbank contract
  (`bloodbank.<domain>.<entity>.<action>`, `bloodbank/docs/event-naming.md`).
- Plane webhook (via n8n) owns task facts; this module never writes them.
- No secrets are read or printed; CLI output scrubs secret-named values.
- Point to doctrine (PILLARS.md); do not copy it.
- The module informs existing workflows (Momo orchestration, BMAD artifacts,
  Pilot boards); it does not schedule, hire, or auto-merge.

## Outcome

User receives either a routing/preflight/evidence result or a completed module
registration. Summarize findings with evidence paths; never overstate
installed/deployed state (see `modules.g33` in `{project-root}/_bmad/custom/config.toml`).

## Upstream BMAD update boundary

**update-preservation: unavailable.** The observe/plan/apply v1 bridge does not
supply pre-update capture/protection, post-update restore/reconcile/verify, or
failure recovery for an upstream BMAD installer. It must not authorize a safe
upstream update. The owning updater must refuse updates before mutation until
it supplies that contract, including native installed BMAD projection bytes,
operator-edited help/SKILL.md, customizations, g33 declarations and foreign
mappings. Retained g33 trees and declarations remain protected after opt-out.
This module's additive rerun applies only to its own contained write targets.

Write containment uses the real project root: a supplied project-root symlink
is allowed as an alias for that real directory; every existing descendant
write component and leaf must be a regular directory/file, never a symlink
(including dangling links and links that point back inside the project).
Read-only reference activation symlinks in `.agents/skills` remain allowed.
Outputs are staged then replaced atomically. A caught apply failure rolls back
published files and created directories; rollback failure is returned explicitly.
Abrupt process termination or machine failure is not a supported update/recovery
protocol and requires operator inspection before another apply.
