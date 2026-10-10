# Reference-only packs

Inspect an existing current pack and the installed `pack --help` before authoring.
A pack can own a manifest, hooks, commands, provenance, and support material;
its skill membership references canonical catalog names.

A pack is additive and composable: selecting a pack with ten distinct new skills
adds ten individual symlinks to the existing canonical skill root. It does not
replace `.agents/skills/` with a symlink to the pack. Root replacement belongs
to a skill set, and sets are mutually exclusive. An installed command that
requires exclusive packs implements the wrong model; do not teach that behavior
as the pack contract.

Do not render copied skill payloads, reintroduce sealing/checksum inventories,
or restore obsolete versioned payload snapshots. Pin the catalog and composition
revisions for reproducibility. Validate source topology and preview a consumer's
compiled map before claiming the pack works.
