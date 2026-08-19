---
name: project-notebook
description: Operate PJangler Project Notebook as bounded, Git-grounded project memory. Use when an agent needs to inspect notebook status, read or update the stable Overview, manage scoped notes, search project knowledge, audit or migrate a binding, recover capture receipts, or install/check the canonical global Project Notebook hooks without changing foreign hooks.
---

# Project Notebook

Treat Git and the repository's Project Manifest as authoritative. Treat the
remote notebook as scoped, derivative context that PJangler owns and can audit.

## Work through PJangler

1. Resolve the repository explicitly when the current directory is ambiguous.
2. Inspect `pj notebook status [repo]` before assuming a healthy binding.
3. Use `--json` when another tool will consume the result. Check `ok`, symbolic
   error code, and `next_actions`; do not infer success from prose.
4. Keep reads and mutations project-scoped. Never call the notebook service
   directly or accept a result whose membership in the resolved binding is not
   proven.
5. Use `pj notebook audit [repo]` to diagnose Drift. Use
   `pj notebook migrate [repo]` for an owned repair plan, adding `--apply` for
   local changes and `--live` only when remote repair is intended.
6. Preserve repository files as the source of truth. Never overwrite Git
   content from notebook content.

## Use the public command surface

Use these command families rather than internal hook or worker entrypoints:

- `pj notebook status|create|overview|audit|migrate`
- `pj notebook list notes`, `get note`, `add note`, `update note`, `delete note`
- `pj notebook search notes`
- `pj notebook capture list|retry`

Direct note mutation authorizes only that selected operation. `create` and live
migration require `--live`; note deletion requires confirmation or `--yes`.
Never delete the stable Overview note.

For complete command forms, policy precedence, hook projection, and safe
configuration, read [configuration.md](references/configuration.md). For
capture pressure, Drift, snapshots, uninstall, and failure recovery, read
[recovery.md](references/recovery.md).

## Handle session context safely

- Let the global wrappers scope themselves at runtime. Global installation does
  not enable a repository.
- Use true `SessionStart` and `SessionEnd` only. Never substitute `Stop` for a
  session boundary.
- Keep hook payloads and user content out of argv and logs.
- Treat hook failures as bounded, actionable, fail-open diagnostics.
- Treat `PROJECT NOTEBOOK OVERVIEW DRIFT` as stale context. Run the exact audit
  or migration action reported before relying on the stored Overview.
- Treat retention pressure as an admission diagnostic, not a receipt state.
  Never delete or compact an unresolved receipt to make room.

## Protect credentials and foreign configuration

Resolve endpoint and authentication through PJangler runtime configuration;
never store them in a repository Manifest, note, hook command, or skill file.
Use `scripts/project-hooks.py` for global Claude projection. Its owner marker is
exactly `project-notebook.v1`; do not hand-edit live settings or remove
Bloodbank, Hindsight, Git checkpoint, notification, CommonProject, or other
foreign hooks.
