# Module Setup

Standalone module self-registration for the 33GOD Integration (g) expansion
module. This file is loaded when:

- The user passes `setup`, `configure`, or `install` as an argument
- `{project-root}/_bmad/config.yaml` has no `g33` section yet

## Overview

Registers g33 into a project that ALREADY has BMAD installed. Writes:

- **`{project-root}/_bmad/config.yaml`** — `g33:` section (surgical; other
  sections and operator edits preserved byte-for-byte)
- **`{project-root}/_bmad/module-help.csv`** — g33 capability rows (anti-zombie)
- **`{project-root}/_bmad/custom/config.toml`** — `[modules.g33]` team TOML
  registration, active in the REAL upstream 4-layer runtime resolver
- **`{project-root}/_bmad/custom/bmad-build.toml`** and
  **`{project-root}/_bmad/custom/bmad-code-review.toml`** — sparse team
  overrides using only customize.toml-supported keys (activation steps,
  persistent facts)

## Check Existing Config

1. Read `./assets/module.yaml` (code `g33`, version 1.0.0).
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
operator-edited g33 content is preserved on rerun unless `--force` is passed.
All conflicts are detected before any mutation — a rejected conflict leaves
zero mutations.

## Verify

After install, verify the module is ACTIVE in the real upstream TOML resolver:

```bash
python3 {project-root}/_bmad/scripts/resolve_config.py --project-root {resolved-project-root} --key modules.g33
```

The output must show `code = "g33"`. Then display the `module_greeting` from
`./assets/module.yaml`.

## Manual install (alternative)

Copy this skill directory into the project's skill root, then run the same
`g33_install.py` command. For PJangler-driven provisioning, invoke
`scripts/g33_cli.py setup --project-root <root>` which delegates to the same
installer.
