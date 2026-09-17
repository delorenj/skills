# Implementation and verification

## One owner per change

Map entrypoint -> real source -> selecting composition -> activation root ->
client alias. Include host-provided and synced/remote imports without assuming
Skillex owns them. For this installation, all-skills owns catalog bytes; sets and
packs are reference-only. Use the installed registry CLI help and preview before
mutating, rather than copying a historical command sequence.

A requested ~/code/skillex/skill path can alias the canonical skill-maintenance
package. Do not write through unknown/generated symlinks until ownership is known.

## Repair sequence

1. Reconcile overlapping WIP and the latest report against live state.
2. Fix credential, scope, and delivery contradictions in the owning procedures.
3. Update callers and referenced recipes; an entrypoint fix with a contradictory
   reference can reintroduce the defect on the next detailed task.
4. Narrow triggers and remove generic opt-in workflows from default compositions.
5. Package or explicitly locate required dependencies. Preserve installer-owned
   system packages rather than projecting a duplicate catalog copy beside them.
6. Resolve synced duplicates through their owner. If preserving an import outside
   discovery, verify byte preservation and retain an ownership receipt. Do not
   symlink a writer-owned destination to canonical files that writer can overwrite.
7. Preview global sync, inspect every operation, apply, then preview again.
   Reconcile only the scope requested; foreign content is not permission to delete.

## Verification

- Validate metadata and real links. Recheck reported false positives manually.
- Test changed executable helpers with meaningful fixtures, including failure
  behavior and absence of credential values in stdout/stderr.
- Check source topology, then real client discovery. Confirm duplicate names and
  removed defaults are absent or disabled under the consuming client's own rules.
- Confirm a second sync produces no new mutations. Do not describe a foreign-entry
  warning as a clean activation result.
- Keep a finding-by-finding closeout. Record exactly what was tested and what
  still depends on future integration or another host.
- Commit/push source changes before advancing parent pins; verify upstream state.
  Do not absorb unrelated WIP to make a global status report green.

## Tool limits

The inventory script checks literal Markdown file links outside fenced examples.
It cannot determine whether a command works, a skill is selected by a model,
a secret-shaped value is real, or two policies are semantically contradictory.
It intentionally does not execute skill instructions, inspect credentials, or
mutate discovery. Those are separate, scoped actions supported by concrete evidence.

## Host-recreated imports

A host may recreate `skills/synced` immediately after it is archived. Treat
physical inventory and enabled discovery as different checks. For Codex, record
explicit retired entrypoint paths in a version-1 JSON policy with a
`disabled_paths` array. Preview `scripts/configure-codex-skills.py --policy <file>`;
add `--apply` only for authorized installation changes. It uses the installed
`skills/config/write` API without reading or exposing unrelated configuration.

Run the same helper with `--verify --cwd <scope>` to query `skills/list`
with `forceReload` in a fresh app-server session. Recreated
known paths must be disabled; retained canonical names must be enabled. The
policy is path-specific: new bucket IDs require reconciliation. Other CLIs do
not necessarily honor Codex exclusions. Never label a shared physical root
collision-free solely because one host suppresses entries. Archive preservation
receipts belong outside source control; the exclusion declaration is source.
