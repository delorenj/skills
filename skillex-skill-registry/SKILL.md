---
name: skillex-skill-registry
description: Operate the Skillex catalog, reference-only sets and packs, skill manifests, and activation roots. Use for importing, selecting, syncing, or diagnosing installed skills. Content review belongs to skill-maintenance; hook dialect generation belongs to agent-config-fanout.
---

# Skillex registry

- `github.com/delorenj/skills` is the canonical source for Skillex skills.
- The skills are tracked as submodule `all-skills` inside the Skillex repository.

## Core model — user-confirmed 2026-10-10

- **Skill root:** a directory where an agent looks for skills, almost always
  named `skills/`.
- **Global skill root:** a directory an agent automatically loads skills from
  regardless of project scope.
- **Canonical skill root:** Skillex's SSOT discovery root: `~/.agents/skills/`
  globally and `<project>/.agents/skills/` per project. Client roots alias it.
- **Skill set replaces a root.** Selecting a set in the manifest replaces the
  canonical root with a symlink to the set's skill root. Sets are mutually
  exclusive; they are not additive bundles.
- **Skill pack populates a root.** Selecting a pack adds its members as individual
  skill symlinks to the existing root. Ten distinct additional members mean ten
  additional links, not a whole-root alias. Packs are composable.

**Sets select the root; packs add skills to it.** These operations are not synonyms
and are not determined by global versus project scope.

The writable definition catalog is `~/code/skillex/all-skills/<name>/`; do not
confuse definition ownership with the canonical skill root. Sets and packs
reference these definitions, never copied payloads. Host-owned `.system` skills
remain installer-owned.

Existing CLI/schema behavior and recalled claims that packs are exclusive or
replace roots are implementation drift, not product authority. Preview before
sync; stop if the plan contradicts this model. Do not invent collision,
inheritance, or shared-set mutation policy from these basic definitions.

Hermes PMs are **Skillex-only**, with a real per-profile `skills/` projection,
not a whole-root alias to the default Hermes catalog. `skillex profile sync
<name> --project <repo> --skillex-only` establishes persistent strict ownership
and bundled opt-out. Preview first with `--dry-run --json`; a foreign child is
an explicit preservation/migration decision, never implicit adoption or deletion.
Clear PM `skills.external_dirs` through the owning locked delta/config renderer:
external archives or bundled roots defeat exclusive selection. Keep local
archives outside every discovery root. Normal sync must honor the strict policy
on later runs; dropping the flag does not permit overlays.

Strict desks resync themselves. A desk's receipt records the `all-skills` HEAD, so
every catalog commit leaves each one `sync pending` (`skillex profile show` exit 6);
the user units `skillex-hermes-resync.path` (HEAD moved) and `.timer` (every 15
minutes) run `scripts/hermes-skillex-resync.py` in the Skillex repo, which
strict-syncs the pending ones and re-checks them. Give it about 20 seconds after a
commit and look with `scripts/install-hermes-resync.sh status`; the log is
`~/.local/state/skillex/hermes-resync.jsonl` plus `hermes-resync.last.json`. A desk
it reports `refused` (exit 3) holds foreign or unowned content and is left
untouched: never hand-edit it, quarantine through `scripts/hermes-skillex-cutover.py`
(preview, then `--apply`). Contract: `docs/implementation/hermes-skillex-resync.md`.

## PM authoring and activation

- Create/edit the canonical `all-skills/<name>/SKILL.md`, not `$HERMES_HOME/skills`.
- Use `skillex vendor sync` for declared upstream sources or `skillex skill import`
  for an accepted import; inspect the installed command's help for arguments.
- Change a `.agents/skills.json` selection or `skillex set add <set> <names...>` /
  `skillex pack add <ref> <names...>`, then preview and sync the affected scope.
- For a PM, use `skillex profile show <name> --project <repo> --json` and the
  strict profile sync command above. Whole-root aliases need `skillex migrate
  --profile <name> --project <repo>` preview/apply first; migration preserves
  foreign children, so it is not by itself a Skillex-only cutover.
- Never use Hermes hub install, local `skill_manage create`, fallback copies,
  or shell symlinks as PM activation writers. Read tools remain useful; writable
  bodies belong only in the canonical catalog. Promote a captured procedure
  there and select it explicitly.

## No skill-operation mise tasks — user policy 2026-10-10

Assume every existing mise task that manages skills is wrong. Remove it; do not
repin it, repair the wrapper, or create a replacement mise task. Invoke `skillex`
directly. This includes sync/provision/activation/migration wrappers and their
skill-task dependencies, watchers, and enter-hook invocations. Preserve unrelated
build/test/env tasks and runtime/tool installation. Fix the generating template
at its owner when encountered so retired tasks cannot return.

Use `skillex integrations retire-mise --project <repo>` to preview and repeat with
`--apply` to remove supported task forms; `--file <config>` targets one explicit
source, `-g` targets global mise configs. If the installed version lacks the
command, upgrade the CLI rather than hand-editing a consumer as a one-off remedy.
A refused mixed/unsupported config is not clean; extend the command and retest.
Follow the currently authorized pilot/rollout boundary, not an unbounded sweep.

## Operate

1. Identify the canonical source, selection manifest, activation root, and writer.
   Read the repository's accepted topology ADR and current manifest schema.
2. Inspect `command -v skillex` and the installed command's `--help`. Python and
   Node implementations coexist on this host; a repository build is not proof
   of what PATH runs. Never infer support from a version string or old incident.
3. Edit canonical content or reference-only membership. For accepted upstream
   imports, use the declared vendor source and resolved commit; preserve its
   provenance and local patches. `vendor status` is an offline pin check.
4. Preview the affected scope with `skillex sync --scope global --dry-run --json`
   (or the installed equivalent for a project). Inspect adds, removals, foreign
   entries, and errors before applying. Foreign entries need an ownership decision.
5. Apply the same scope, inspect resolved paths and actual client discovery, then
   repeat the preview: the second run should plan no managed changes.
6. Validate source topology separately from consumer topology. Commit and push
   the catalog first, then compositions and the parent catalog revision.

Do not republish host-provided system skills as top-level catalog selections.
Disable or migrate a competing import through its owning configuration; deleting
one generated copy alone does not stop regeneration. Preserve unrelated skills.

## References

- [Ownership and topology](references/topology.md)
- [Manifests and selection](references/manifest.md)
- [Reference-only packs](references/pack-authoring.md)
- [Activation and discovery](references/fanout.md)
- [PJangler integration](references/pjangler-integration.md)
- [Troubleshooting](references/gotchas.md)
