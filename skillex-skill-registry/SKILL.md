---
name: skillex-skill-registry
description: Operate the Skillex catalog, reference-only sets and packs, skill manifests, and activation roots. Use for importing, selecting, syncing, or diagnosing installed skills. Content review belongs to skill-maintenance; hook dialect generation belongs to agent-config-fanout.
---

# Skillex registry

- `github.com/delorenj/skills` is the canonical source for Skillex skills.
- The skills are tracked as submodule `all-skills` inside the Skillex repository.

The writable definition is `~/code/skillex/all-skills/<name>/`. Sets and packs
select that definition; one `.agents/skills` root per scope exposes it; client
`skills` directories alias that root. Do not copy skill payloads into packs or
client directories. Host-owned `.system` skills remain installer-owned.

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
