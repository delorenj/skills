# Ownership

`all-skills/` contains real skill directories. `sets/` and `packs/` contain
references, never another writable SKILL.md. The accepted contract is
`~/code/skillex/docs/architecture/ADR-0001-reference-only-skill-topology.md`.

A scope's `.agents/skills` may alias a composition or contain managed canonical
symlinks. Client roots alias that scope root. Installer-owned `.system` is a
reserved exception in the consumer tree, not a second catalog to overwrite.

Pin the catalog revision and pack composition revision. Imported sources also
record the upstream revision in `.source.yaml`; consult the declared vendor
source before refreshing. A checksum-valid copied pack is still the wrong topology.
