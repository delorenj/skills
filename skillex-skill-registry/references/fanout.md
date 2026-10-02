# Activation and discovery

Use Skillex as the sole writer of managed skill projections. Check the installed
sync help, preview the explicit scope, apply it, and verify a second preview.
Client `skills/` roots should resolve to the scope's `.agents/skills` directory.

Source topology passing does not prove consumer discovery. Inventory nested
imports, frontmatter names, broken links, and reserved system skills; query the
actual host's skill list after a reload when available. A missing skill can be
an omitted selection, a broken alias, disabled host configuration, or a parser
error. Fix the owner, not a generated copy.

Do not prune foreign directories as if they were managed links. Migrate useful
imports into the catalog and disable their old source before removing discovery.

## Hermes PMs

PMs do not support writable local overlays: Skillex-only ownership is mandatory.
Use a real per-profile `skills/` root with recorded canonical child links and
`skillex profile sync <name> --project <repo> --skillex-only`. Preview with
`--dry-run --json`; strictness persists on later ordinary sync. Foreign content
must first be preserved outside discovery roots. Whole-root aliases require an
explicit migration; migration alone retains foreign children and is not strict.

Require `.no-bundled-skills` and an empty PM `skills.external_dirs` list through
the owning locked config-delta renderer. Do not scan global archive/system roots
alongside a complete profile projection. Never rerun full provisioning to sync
skills: that can alter unrelated live state. Verify the actual pinned Hermes
scanner returns only selected catalog paths and the second sync preview is empty.

Strict roots tolerate Hermes bookkeeping only: `.usage.json`, `.usage.json.lock`,
`.curator_state`, `.curator_suppressed`, `.sync_state` (regular files) and the
curator's `.curator_backups/` tarball store (Skillex 0.1.3+). `.hub` and
`.archive` stay refused: they mean a hub install or a curator archival moved
skills in or out. `profile show` exit 6 is a pending sync (selection or
catalog change), not a failure; exit 3 is a strict refusal. Convert a legacy
desk with `~/code/skillex/scripts/hermes-skillex-cutover.py` (preview, then
`--apply`); it quarantines displaced content under
`~/.hermes/.skill-quarantine/<profile>/<stamp>/` with a journal.
