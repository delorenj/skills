# Troubleshooting

- **Reversed set/pack semantics:** older code, docs, and memory claim packs are
  exclusive root replacements and sets are additive. The user explicitly
  corrected this on 2026-10-10: sets replace roots and are mutually exclusive;
  packs add member symlinks to existing roots and compose. A passing test for
  reversed behavior is evidence of implementation drift, not product intent.

- **Source checks pass; clients disagree:** inspect actual roots, nested imports,
  disabled entries, and frontmatter name collisions. Catalog health is separate.
- **Removed skill returns:** a selection or another installer still owns it.
  Change that owner; deleting generated output is temporary.
- **Command absent:** inspect PATH and installed help. Python and Node CLIs may
  differ. Report the command actually exercised, not a repository version alone.
- **Pack checksum passes but topology fails:** copied definitions violate the
  reference-only contract. Promote one definition and replace copies with refs.
- **System skill appears twice:** preserve `.system` ownership and remove the
  extra catalog selection; qualify genuinely distinct imported workflows.
- **Sync reports foreign content:** classify its writer and preserve it until
  deliberately migrated. Never weaken topology validation to hide the conflict.
- **Profile sync reports `E_PROFILE_SOURCE_CHANGED` but source is unchanged:** check
  registry resolution before assuming a real edit. Re-run the preview, then retry with an
  explicit `--registry-root` pointing at the registry checkout. Do not restore or delete the
  source skill or hand-edit projections.
