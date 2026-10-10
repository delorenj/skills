# Ownership

`all-skills/` contains real skill directories. `sets/` and `packs/` contain
references, never another writable SKILL.md. The accepted contract is
`~/code/skillex/docs/architecture/ADR-0001-reference-only-skill-topology.md`.

The canonical skill root is `~/.agents/skills/` globally or
`<project>/.agents/skills/` locally. A **set replaces** that root with a symlink
to the set's skill root; sets are mutually exclusive. A **pack populates** the
existing root with individual member symlinks; packs are composable. This is an
operation distinction, not a global-versus-project distinction.

`all-skills/` is the definition catalog, not the canonical discovery root. Client
roots alias the scope's canonical root. Installer-owned `.system` is a reserved
exception in the consumer tree, not a second catalog to overwrite.

The user's 2026-10-10 definitions supersede any older ADR wording that treats
sets and packs as interchangeable compositions or makes packs root replacements.

Pin the catalog revision and pack composition revision. Imported sources also
record the upstream revision in `.source.yaml`; consult the declared vendor
source before refreshing. A checksum-valid copied pack is still the wrong topology.
