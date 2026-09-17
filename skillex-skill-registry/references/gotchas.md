# Troubleshooting

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
