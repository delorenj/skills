# Composition

How to write the two bodies. The lint enforces the mechanical half of this;
the rest is judgment, and this file is the judgment written down.

## The two registers

| | internal | external |
|---|---|---|
| Who reads it | the team, PMs, future agents in three weeks asking "when did that change" | the client, who makes decisions from it |
| Register | dense, chronological, complete | narrative, warm, earned confidence |
| Length | what the window needs, under 5000 chars | 120 to 250 words; longer stops being read |
| Names tickets | always, key and title | never |
| Lead | the headline numbers, then the timeline | the outcome the reader can see or feel |
| Ends with | what is still open | what you need from the client, or nothing |

Never write both in one pass. Internal first, complete; then external, chosen
from it.

## Before writing: find what the digest cannot know

The digest has facts and no judgment. Establish, from the digest, git and the
previous report's title:

- **Why did the closed tickets matter?** A key and a title are not an outcome.
  Read the commits (`git log`, `git show`) if the titles do not carry it.
- **What actually unblocked?** The best line in any update is usually "the last
  uncertain thing is now behind us", and no counter can tell you that.
- **What broke, and is it still broken?** The digest's failures and the
  sessions that ended badly; say which is which.
- **What is waiting on the client?** This belongs in the external update and
  is often the only part they act on.
- **What did the previous update promise?** Its title is in the digest. If it
  happened, say so; if it did not, say that.

A quiet window is a real answer and still gets an update: a short honest one.
A feed that goes silent reads as work having stopped, which is a worse message
than a quiet window honestly reported. What a quiet window does not get is
padding: no manufactured significance, no activity dressed up as progress.

## The internal body

Exhaustive and chronological. Order: headline metrics, then the timeline, then
the ticket movement, then what is still open, then assumptions you made because
nobody was there to ask.

```
# Invoice drafts land in the CRM; credential rotation started

## The day
| Sessions | 6 |
| Commits | 4 |
| Tickets closed | 1 |

## Timeline
09:40 a1b2c3d feat(relay): draft invoice reaches the CRM
13:02 pytest failed twice on the mirror suite; fixed in b2c3d4e
16:15 SMK-231 moved to In Progress

## Closed
- **SMK-214** Draft invoice reaches the CRM

## Still open
- SMK-231 needs the new credential in the vault before the mirror can pick it up

## Assumptions
- Treated the failed pytest run as transient; the retry passed.
```

Name people and agents for their work. Stale branches are news. So is "we do
not know what this one is for": say that plainly rather than inventing a
purpose from commit subjects.

## The external body

The one the user described as "spun like a salesman would, but not lies". The
distinction that makes it work:

> **Spin is choosing which true thing to lead with. It is never asserting
> something that is not so.**

Rules, in order of how badly breaking each one lands:

1. **Never claim something works that has not been observed working.** Not
   "the invoice path is done" but "a draft invoice landed on a real record
   this afternoon". The second is stronger anyway, because it is checkable.
2. **Lead with the outcome, not the activity.** The client does not buy tool
   calls or commits. They buy the thing the work makes true for them.
3. **Name the hard thing and say why it was hard.** This is where the
   confidence comes from. "Four separate reviews concluded those writes were
   impossible. They weren't" reads as competence; "we made great progress"
   reads as nothing.
4. **Convert internal vocabulary.** A ticket key becomes an outcome. A burndown
   becomes "the pieces are built". A retry-loop fix becomes "nothing can fail
   quietly overnight". A refactor becomes what the reader now experiences.
5. **Do not hide a problem; reframe it honestly.** A slipped date is "the
   honest last mile, and it's measured in days, not weeks". A real blocker the
   client must clear is stated plainly, because they are the only one who can
   clear it.
6. **End with what you need from the client**, or with nothing. Never end with
   filler.

Shape: a lead sentence carrying the win (bold it if it earns it), two or three
short paragraphs or bullet groups of substance under `##` headings, a closing
line about what is next or what is needed. Tickets with the client-visible
label (`surface: always` in the digest) are surfaced as momentum every time,
whatever else the window held.

The register is set by `~/code/james-brennan/workshop/2026-08-28-email-to-jim.md`.
Read it before writing the first one. It is the best example on this machine of
the voice: specific, warm, technically honest, quietly proud, never inflated.

## Tone

From `~/code/intelliforia/.claude/skills/team-update/references/voice-and-structure.md`,
which is the same voice for a different reader:

- Plain and direct. Short declaratives; let a long sentence land only after
  several short ones. Contractions are fine.
- Concrete over abstract: "one session's data leaking into another's note",
  not "a data integrity issue".
- Confident about facts, explicitly hedged about the unproven: "reviewed but
  not yet merged or clinically tested; all verification so far is at the code
  level". Copy that instinct.
- No hype. No "exciting", "robust", "seamless". If it is genuinely good, the
  facts show it.
- "You" is fine in a client update (it is a letter, not a page); "we" is fine
  too. Neither is an excuse for a sales voice.

| avoid | use |
|---|---|
| leverage, utilise | use |
| robust, seamless, exciting | (delete; state the fact) |
| refactored X into Y | what the reader now experiences |
| shadow DOM, reducer, symlink, worktree | the visible behaviour it produces |
| we've been working on | it shipped / it's being checked / it's blocked on |
| soon, shortly | a real state, or nothing |

## What the lint refuses, and why

For every audience: a missing `# title` line, a title outside 2 to 180
characters, a body over 5000 characters or empty, and unfilled placeholders
(`TODO`, `TKTK`, `XXX`, `<placeholder>`, `{{`, `lorem ipsum`). A warning for
anything shaped like an HTML tag (the portal renders it literally) and for a
must-surface ticket the text never mentions.

For the external audience, as errors: a ticket key (the project's identifier
and any `lint.extra_identifiers`), a commit sha, an absolute path, burndown
language, a tool-call count, a sprint number, "refactor" in any form, an agent
name, any `lint.banned_terms` entry, and the title of an internal-only ticket,
verbatim or as three of its distinctive words in order on one line. The last
one is the reason the external digest drops internal tickets entirely: the
agent cannot paraphrase what it never saw, and the lint catches what it
remembered from the internal body.

Fix the text, never the lint. If a rule is wrong for a project, `lint.banned_terms`
and `lint.extra_identifiers` are the two knobs; the rest is the contract.
