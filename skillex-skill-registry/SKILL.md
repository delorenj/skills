---
name: skillex-skill-registry
description: Operate the Skillex catalog, reference-only sets and packs, skill manifests, and activation roots. Use for importing, selecting, syncing, or diagnosing installed skills. Content review belongs to skill-maintenance; hook dialect generation belongs to agent-config-fanout.
---

# Skillex registry

The writable definition is `~/code/skillex/all-skills/<name>/`. Sets and packs
select that definition; one `.agents/skills` root per scope exposes it; client
`skills` directories alias that root. Do not copy skill payloads into packs or
client directories. Host-owned `.system` skills remain installer-owned.

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
