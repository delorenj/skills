# Module Setup

Standalone module self-registration for the 33GOD Integration (g33) expansion
module. This file is loaded when:

- The user passes `setup`, `configure`, or `install` as an argument
- `{project-root}/_bmad/config.yaml` has no `g33` section yet

## Overview

Registers g33 into a project that ALREADY has BMAD installed. Writes:

- **`{project-root}/_bmad/config.yaml`** — `g33:` section (surgical; other
  sections and operator edits preserved byte-for-byte)
- **`{project-root}/_bmad/_config/bmad-help.csv`** — active g33 capability rows
  (anti-zombie; YAML-only layouts use legacy `module-help.csv` and stay inactive)
- **`{project-root}/_bmad/custom/config.toml`** — `[modules.g33]` team TOML
  registration, active in the REAL upstream 4-layer runtime resolver
- **`{project-root}/_bmad/custom/bmad-*.toml`** — build, code-review, prd, spec
  and architecture overrides only for actually installed skill surfaces; sparse team
  overrides using only customize.toml-supported keys (activation steps,
  persistent facts)

## Python prerequisite

Use Python >=3.11 with PyYAML>=6.0 (declared in `../requirements.txt` and the
installer's PEP 723 metadata). The interpreter used by manual commands or the
bridge must have that dependency; `uv run` can consume script metadata. Missing
PyYAML produces an actionable preflight refusal and zero writes. The module does
not install dependencies into the operator's environment or fall back to partial
YAML validation.

## Check Existing Config

1. Read `./assets/module.yaml` (code `g33`, version 1.1.0).
2. If `{project-root}/_bmad/config.yaml` already has a `g33` section, this is a
   reconfiguration/update.
3. Run a dry run first and show the plan:

```bash
python3 ./scripts/g33_install.py --project-root {resolved-project-root} --dry-run
```

Resolve `{project-root}` to the actual absolute project root in every path
argument — these are filesystem paths, not config values.

## Collect Configuration

Defaults come from `./assets/module.yaml`:

- `ecosystem_root` (default `.`) — repo-relative ecosystem monorepo pointer for
  doctrine citations only; never an absolute home path
- `g33_output_folder` (default `{project-root}/_bmad-output/implementation-artifacts`) —
  where evidence-to-handoff documents go

If the user provides inline values (e.g. `output folder is docs/handoffs`), map
them to these keys; otherwise defaults are used. A JSON answers file can be
supplied via `--answers`.

## Apply

```bash
python3 ./scripts/g33_install.py --project-root {resolved-project-root}
```

The installer is idempotent: a rerun with no operator edits changes nothing;
operator-edited g33 content is preserved on rerun. `--force` re-emits managed
values while preserving unknown keys, comments and operator array entries.
All conflicts are detected before any mutation — a rejected conflict leaves
zero mutations.

## Verify

After install, verify the module is ACTIVE in the real upstream TOML resolver:

```bash
python3 {project-root}/_bmad/scripts/resolve_config.py --project-root {resolved-project-root} --key modules.g33
```

The JSON output must show `modules.g33.code` equal to `g33`.
A supported active layout contains `_bmad/config.toml`, the real configuration
and customization resolvers, and an installed BMAD customization surface.
BMAD 6.12.0 YAML-only registration is inactive; the bridge reports `unavailable`.
Use the real `resolve_customization.py` with an installed skill to verify its
g33 activation steps and persistent facts. Then display the `module_greeting` from
`./assets/module.yaml`.

## Manual install (alternative)

Select `g33-33god-integration` through the canonical Skillex registry in the
project's `.agents/skills.json`, then run
`skillex --registry-root <registry-root> sync --project <project-root> --json`.
The activated skill is a reference symlink to the canonical body; do not copy
its source into a reference-only pack. Run the canonical module's
`g33_install.py` command after activation. For PJangler-driven provisioning, invoke
`scripts/g33_cli.py setup --project-root <root>` which delegates to the same
installer.

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

The installer and bridge observe share parsed YAML namespace ownership. Quoted,
escaped and explicit/block `g33` keys are equivalent to the canonical key. An
existing section requires a whole managed comment at its direct mapping-member
indentation; marker-like scalar content, nested/sibling comments and header
comments confer no ownership. Foreign or indirect/flow namespaces refuse before
writes. Plain/force edits preserve legitimate managed key spelling and operator
nested content/comments; observe reads the installer ownership result.
