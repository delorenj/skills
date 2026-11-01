# Stitch as a Design handoff producer

When the user chooses Stitch in Design handoff mode, load the canonical `stitch`
skill and follow [its handoff contract](../../stitch/references/33god-handoff.md).
Assemble the producer prompt from captured Discovery, not a newly invented brand.

The CLI can generate screens/variants and export HTML/screenshots on the user's
behalf **after** they approve external generation and the target project/content.
Use `{doc_workspace}/.working/stitch/<screen-id>/<unique-export>/` (new empty
folder per download) and `.working/stitch/handoff.md`. Let the user choose a
direction; record selection pending if they have not. Never treat an installed
CLI, configured key, or dry-run response as proof of remote generation.

If CLI/auth is unavailable or remote execution is not approved, retain the manual
path: give the assembled prompt to the user for Stitch Canvas and have them save
outputs in the run workspace. Report the boundary; do not claim a generated result.

Resume Update/Finalize to reconcile the record and exports against `.memlog.md`.
DESIGN.md and EXPERIENCE.md remain the peer authorities and win on conflict with
mocks/imports. Stitch outputs are visual references, not complete UX contracts or
production code. Keep all normal BMAD discovery, coverage, validation opt-in and
promotion rules intact; do not bypass them merely because a screen was generated.
