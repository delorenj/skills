---
name: excavate
description: Dig through git history, docs, tickets, PRs, and session breadcrumbs to reconstruct a lost feature's context and persist it to project Hindsight memory.
---

# Excavate

## Outcome

A successful dig ends with **Hindsight memories written** that let future sessions recall:

1. **What** the feature was — functionality, user-visible behavior, API shape
2. **Why** it existed — the problem it solved, the user journey it served
3. **Where** it lived — files, modules, components, routes, models
4. **How** it was built — architecture decisions, integration points, dependencies
5. **When** it was introduced and lost — commit SHAs, epoch markers, epic/story refs
6. **Big-picture placement** — how it fit the larger product plan, adjacent systems
7. **Reintegration hints** — what's changed in the current architecture that affects restoration

Plus one entry in the archeology meta-bank capturing the **loss pattern** (what, when, how it was lost, mitigation idea).

No markdown report artifact. The memory is the deliverable.

## Dig Sites

Breadcrumbs scatter across many sources. Dig in parallel where possible. Non-obvious sites worth probing:

**Git forensics:**
- `git log --all --oneline --grep=<term>` — feature mentions across all branches
- `git log --diff-filter=D --summary` — file deletions (squashed victims often show here)
- `git log --follow <file>` — history of a specific file even through renames
- `git show <sha>` — full diff for a suspect commit
- `git blame <file>` — last-touched attribution
- `git log --merges --grep=<term>` — merge commits often carry PR titles
- `git log -S "<code-string>"` — when exact code disappeared

**Documentation:**
- `{project-root}/docs/` and subdirectories (check `INDEX.md` for TOC)
- `{project-root}/docs/session-reports/` — session-level context, often the only trace of in-flight work
- `{project-root}/_bmad/` — BMAD stories, epics, planning docs, sprint status
- Domain `GOD.md` files — check CLAUDE.md for the file-to-GOD mapping
- README.md at every level

**Tickets & PRs:**
- Plane board (URL in CLAUDE.md if present) — the ticket reference is usually in branch name or commit message
- `gh pr list --state all --search <keyword>` — search all PRs by keyword
- `gh pr view <num> --comments` — PR body + review comments (review comments often contain the context that didn't make it into code)
- Linked issues in PR bodies
- `gh api repos/<owner>/<repo>/pulls/<num>/comments` — line-level review comments

**Session history:**
- `hindsight memory recall $BANK "<keyword>"` — prior session knowledge
- `hindsight memory recall ${BANK}-archeology "<keyword>"` — prior digs on same feature
- Cross-bank recall if the feature might span projects

## Epoch Bounding (The Scalpel)

Narrow the time window before digging wide. Techniques:

- **File existence transitions** — when did `<file>` first appear? When was it last modified? When did it disappear? Three SHAs bound the epoch.
- **Epic/story markers** — commit messages often reference tickets. Find the epic surrounding the loss.
- **Merge commits** — `git log --merges --first-parent` on the main branch gives a coarse timeline of what shipped when.
- **Branch point** — the divergence between staging and main often bookends a release window.

Announce the epoch before digging: "The trail begins at `<sha>` and ends at `<sha>`. Narrowing."

## Persistence (Exact Commands)

Bank names resolve on activation. Use them exactly:

**Write restored feature context to project bank:**
```bash
hindsight memory retain "$BANK" "<restored context describing what/why/where/how>" --context architecture
```

Multiple memories are fine — one per dimension if the context is large. Prefer focused, well-titled memories over one massive dump.

**Write loss pattern to archeology bank:**
```bash
hindsight memory retain "$ARCHEOLOGY_BANK" "Feature: <name>. Lost during <epoch>. Mechanism: <squash|rebase|refactor|amnesia|other>. Signal that would have prevented loss: <what should have flagged this>." --context session-summary
```

**Always also update sidecar `chronology.md`** with a one-line dig record: date, feature, outcome (recovered/partial/cold).

## Autonomy & Writes

Full trust. Proceed without confirmation mid-dig. Narrate every write as it happens ("Writing restored sidecar context to `intelliforia` bank..."). If the dig calls for opening a Plane ticket or leaving a PR comment, do it and announce.

## Failure Modes

If the trail runs truly cold:

- Name the dead ends explicitly: "No commits between X and Y reference the sidecar. No PRs match. No session reports catalog it."
- Record the cold trail itself as a loss pattern — absence of breadcrumbs is its own signal that process failed.
- Suggest external context the user might hold: local notes, Obsidian vault entries, chat logs, screen recordings.

## Narration Register

Temple of Doom, not cron job. Examples of tone:

- Opening: "Now then. What was lost?"
- First hit: "The first breadcrumb. Commit `9edc6304`, 2026-04-18. 'checkpoint: auto-commit'. Buried in a checkpoint, of course."
- Squash confrontation: "The bastards squashed it. But the PR body remembers what the commit history forgot. Pulling `#594`."
- Recovery: "Found it. `extension/src/stores/userJourneyStore.ts`, alive through `877fc588`, ripped out by `#594` without replacement. The aggregation is gone. The localStorage flush is gone. The intent is in the PR body."
- Close: "Restored. Memory persisted to `intelliforia` bank. The loss pattern is catalogued. The project remembers again."
