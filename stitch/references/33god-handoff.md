# 33GOD UX ideation handoff

## Ownership and entry

The existing pipeline is product brief/spec → `bmad-ux` Discovery → optional
Stitch Design handoff → `bmad-ux` Update/Finalize → architecture/stories/build.
Stitch owns generated reference artifacts only. BMAD's `.memlog.md` records UX
decisions; DESIGN.md owns appearance and EXPERIENCE.md owns behavior. Both spines
win over generated screens. No new event subject, scheduler, ticket lifecycle,
or employee orchestration layer is needed.

Before calling Stitch, assemble the captured Discovery prompt: product goal and
source references, named journey, screen/surface list, device and breakpoints,
content and important states, UI-system/brand constraints, and open questions.
Do not upload the full repository or private documents by default. Confirm what
will leave the machine and the project ID. If generation is not authorized or
authentication is unavailable, return the prompt and pending action; keep the
existing manual Stitch handoff available without claiming a CLI generation.

## Artifacts

Inside the BMAD run's `{doc_workspace}` use:

```text
.working/stitch/<screen-id>/<unique-export>/   # one new empty dir per download
.working/stitch/handoff.md                    # run-specific decision record
```

For standalone ideation, agree on an output directory first, and use the same
relative layout. Do not derive the run workspace from the shell's current dir.
The CLI does not automatically author these decision records or both BMAD spines.

The handoff record contains:

- Product/source references, date, CLI version, project ID, and Canvas URLs
  resolved with `stitch url`, not constructed by hand. For the manual fallback,
  use user-supplied Canvas links and artifact paths; mark unavailable CLI version,
  IDs or CLI-resolved links explicitly unavailable rather than inventing them.
- Submitted prompts, device, constraints and whether DESIGN.md was uploaded.
  Credentials never belong in a prompt or record.
- Every candidate screen ID and local export path; which direction was selected,
  by whom, and why. If no choice was made, say **selection pending**.
- Covered surfaces/states versus unmocked, untested or assumed states, including
  responsive behavior, empty/error/loading states, keyboard/focus and contrast.
- Open questions and the exact next action: resume BMAD UX Update/Finalize with
  this record and its referenced exports. Generated HTML is not build-ready code.

Log chosen decisions and artifact references through BMAD's existing memlog
writer (`_bmad/scripts/memlog.py append`) when the workspace has been initialized;
never hand-edit the memlog. Stitch must not invent a memlog when BMAD is absent.

## Return to BMAD

BMAD UX reconciles the handoff and exports against captured decisions, lifts
accepted visual tokens/layout into DESIGN.md and behavioral decisions into
EXPERIENCE.md, surfaces conflicts/open questions, and promotes keepers using its
existing Finalize process. Keep original Stitch exports in place as provenance;
promote copies of chosen mockups, then update handoff.md with the promoted paths
and append a promotion event through the memlog writer. Do not break references
to original exports. Rejected alternatives remain identifiable rather than
silently becoming requirements. Mock coverage is not an accessibility test.
Only after contracts are reconciled does implementation continue through the
existing architecture/story/build route.

No generation during installation, no implicit project rebinding, and no fleet
profile sync: distribution is a canonical Skillex selection, not a new service.
