---
name: recap
description: >-
  Produce a comprehensive, bounded post-run report after a long agent session — many hours, many
  tickets, or thousands of lines — and write it as a self-contained HTML artifact into `.recaps/` in
  the repo. Answers the question a commit list cannot: what can I do now that I could not before, what
  needs me, and what should I not trust. Use when the user says "recap", "what did you just do",
  "session report", "post-task report", "summarize this session", "what changed", "I can't follow the
  scrollback", or at the end of any run too long to reconstruct by reading the tail of the console.
  Prefer running it from a FRESH session against the finished one. Do NOT use for a periodic project
  update to an audience (activity-report), a customer changelog, or a PR description (pr-creator).
metadata:
  version: "1.0.0"
---

# recap

After a fourteen-hour run the console tail is useless. Scrolling it is worse. This produces one page
that a human can read in ninety seconds and an engineer can act on, bounded by a window it resolves
rather than guesses.

## The one rule

**If a section could be written by reading `git log`, it is not the section anyone wanted.**

The user's complaint, verbatim in spirit: *"eight commit SHAs and 'story 1.8 is closed' is concise and
comprehensive, and nowhere at all does it let me know what I can do now that I couldn't before. I'm a
human — I can't remember the story numbers for the thirty projects I'm working on."*

So a recap leads with **capabilities in the user's own vocabulary, each with the literal thing to run**,
and treats commits as evidence in a footnote. `pjangler fleet status --domain systemd now reports five
observations per agent where it used to say unsupported` is a recap sentence. `Story 1.8 closed` is not.

## Run it out of band

**Preferred: a fresh session recapping a finished one.** `recap --session <id>` or `recap --since <t>`.

Two reasons, and the first is the important one. An agent recapping itself reports what it *intended*;
its own transcript corroborates its intentions; nothing contradicts it. That is precisely how "8 commits,
everything landed" gets written by an agent that believes it. Independent evidence — running the command,
diffing the API — is the only antidote. Second, this fires when context is nearly exhausted, and a wide
harvest is unaffordable there.

In-session is a convenience, not the design point. When running in-session, lean harder on probes and
lighter on your own memory.

## The five passes

Run them in order. **Harvest wide, render narrow** — most of what you gather appears nowhere.

### 1. Resolve the window — never guess it

A sha is an anchor you convert to an instant. It is never the window.

Full chain, its ordering, and the four ways it silently lies: **[references/window.md](references/window.md)**.
Read it before writing any range. The short version: chain from `.recaps/entries/`, else the session
transcript, else the reflog, else ask — and **validate every rung's output, never its error message**
(`git rev-parse "HEAD@{5000.hours.ago}"` exits 0 and hands you a sha from three months earlier).

### 2. Probe the boundary — this is the engine

**[references/probe.md](references/probe.md)**

The "before" half of *what you can do now that you couldn't* is the valuable half and the hard half, and
it is mechanically derivable: check out the base, ask the software what it could do, ask HEAD the same
question, diff the answers. `--help` at base vs HEAD. Exported symbols. Routes. Config keys and required
env vars. Test names. Migrations.

This is the primary capability source **because prose is not portable**. Measured across 60 repos on this
machine: 0 have a justfile, 1 has a Makefile, ~15 have mise tasks, ~4 have a user-authored CHANGELOG, and
median commit-body size clears 500 bytes in 3 of 10 sampled repos — two of which are the repos this skill
was designed in. Mining prose an agent already wrote is circular and is empty exactly where it is needed.

### 3. Harvest what the diff cannot show

**[references/harvest.md](references/harvest.md)**

Tiered by portability, minimum-viable first. Board moves, other repos, orphaned work, decisions and
rejections, and live-system measurements. Run the universal tier always; probe for the rest.

### 4. Compose against the schema

A **capability** requires all four of:

| field | rule |
|---|---|
| headline | in the user's vocabulary, naming the effect — not the ticket, not the module |
| invocation | the literal runnable thing: a command, a URL, a flag, an import |
| before | one sentence, from a probe or from evidence. **Hard cap: one sentence.** |
| evidence | ≤3 shas/paths/tickets; the rest goes in the card's `<details>` |

**No derivable `before` and no runnable invocation means it is not a capability.** Demote it to the
engineer band. That single rule is what stops "story 1.8 closed" from wearing a card.

**Verify before you headline.** Run the invocation in its safest read-only form — `--help`, `--version`,
an explicitly read-only task. A "you can now run X" that errors when pasted is worse than silence. Mark
anything you could not verify as unverified, and never headline it.

**C=0 is the normal, comfortable outcome.** Most long runs produce proof, cleanup, refactoring and
knowledge — not new user-facing capability. Say so plainly in one line. If every recap you write has
four to six capability cards, you are inflating, and the user will stop trusting this faster than he
stopped trusting the commit summary.

### 5. Render and record

**[references/artifact.md](references/artifact.md)** — `.recaps/` layout, the self-contained HTML rules,
and the decision rule for what shape the page takes.

## What the page must contain

Ordered as the reader reads: top-down, stopping whenever they like.

1. **What you can do now** — capability cards, or one honest line saying there is none.
2. **What needs you** — where to resume and what wants a human. Uncommitted work, in-window stashes,
   branches ahead of upstream, failing tests, open questions the run recorded, tickets left mid-flight.
   *After a long run this is the second question every operator asks, and it is the highest value per
   line on the page.*
3. **What broke, and what not to trust** — regressions, newly skipped tests, disabled CI steps, removed
   assertions, TODO/FIXME added in-window, anything reverted or abandoned. **Never skip this because the
   news is good.** A page with no caveats reads as marketing.
4. **If you depend on this** — mandatory, and it renders **even when C=0**: schema migrations, new
   required env vars, changed defaults, dropped behaviour, breaking dependency bumps. These are the
   engineer's most urgent facts and they have no capability to hang off, so a capability-first structure
   drops them silently unless this band is compulsory.
5. **What was learned about the live system** — a number the run measured against the real thing belongs
   here even when no code changed, with the command to reproduce it beside it. "1 of 28 gateways healthy;
   20 agents with no verified channel ownership" is knowledge the user did not have this morning and
   cannot get from a diff. This is a first-class band, not a footnote.
6. **Decisions and rejections** — judgment calls that changed the outcome, and things deliberately *not*
   done, each with its reason. A declined refactor, a rejected review finding, a chosen trade-off. None
   of it appears in a diff, and it is the part of a long run that is impossible to reconstruct later.
7. **Health at HEAD** — one line. `tests: passing / not run / failing (as of T)`. A recap that claims
   capabilities without this is asserting into the dark, and it is what makes a CAVEAT pill mean anything.
8. **Evidence** — commits, repos, tickets, artifacts.
9. **Provenance** — **one line**: window, which rung resolved it, confidence.

Bands with nothing in them are omitted, except 3, 4 and 7, which always render.

## Budget, enforced by counting

The temptation after a long run is to show the work. Resist it mechanically.

- **Capability layer ≤200 words.** This is where inflation happens, so this is the tight one. Count it.
- **Whole surface ≤600 words** — about two minutes. Count it and cut; do not collapse to get under.
- **≤7 capability cards**; the rest collapses into *also changed*.

  *Calibrated by dogfooding, not guessed.* The first draft of this skill said 400 words for the whole
  surface. Recapping a 27-hour, 2-repo session with a regression and a live finding came to 759, and
  after cutting every sentence that could go it settled at 563 — with nothing left to remove that was
  not a mandatory band. A budget that forces you to delete "what needs you" is the wrong budget. If a
  recap is over 600, the usual cause is a session that was really two; check the idle-gap split before
  cutting content.
- **One chart maximum**, and only past the gate in artifact.md.
- `<details>` only *inside* a card. No orphan collapsed sections, never nested. Forty collapsed blocks
  reads as "I could not decide what mattered".
- Provenance gets one line, not a methodology section.

## House rules

1. **Plain English.** If a sentence needs the reader to know what a reducer is, name the visible effect
   instead.
2. **Every claim carries evidence** — a sha, a path, a ticket, a command — and unverifiable claims are
   dropped or explicitly labelled. A wrong "shipped" is worse than an omission.
3. **Never address the reader as "you" in prose.** The page reports; it does not instruct. (The band
   *titles* use "you" deliberately — they are the user's question, not an instruction.)
4. **No hype.** No "seamless", "robust", "exciting". If it is good, the facts show it.
5. **Be honest about what is unfinished, unproven or abandoned**, and prefer the narrow window with a
   note over the wide one that re-reports work already read.
6. **Never invent a purpose** for a commit or branch you do not understand. "Unclear what this is for"
   is a legitimate and useful sentence.

## Where it lands

`.recaps/` in the repo where the window was resolved. Cross-repo work appears as a band with links
rather than as a second recap. If that repo is a submodule, say so in the provenance line — a `.recaps/`
inside a submodule is nearly invisible.

**Do not commit it by default.** Write the file always; commit only when the repo already has a
`.recaps/` entry (the user opted in once) or the user asks. Several repos here are forks and vendored
clones, and writing a "what you can do now" page into someone else's tree and committing it is wrong by
default. `--private` writes to `~/.local/state/recaps/<repo>/` instead.
