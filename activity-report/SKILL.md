---
name: activity-report
description: Produce a periodic project update for one pjangler project and one declared audience (internal or external), from Candystore, git, the ticket board and Hindsight, rendered as plain text, markdown and a self-contained HTML artifact, and emitted as one bloodbank.project.activity.recorded event. Use for "daily update", "client update", "internal update", "what did we ship", "periodic update", "activity report", "portal update", the nightly 03:00 run, a catch-up for a skipped window, or re-writing an update that lint refused. Do NOT use for the Surface operations payload (apps/surface, no free text), for roadmap checkpoints, for deploys, or for Bloodbank schema work (bloodbank-integration).
metadata:
  version: "0.1.3"
---

# activity-report

One project, one window, one declared audience, one event. The pipeline collects
what observably happened (Candystore sessions, git, the ticket board, Hindsight),
an agent writes one plain-text update in the portal grammar, the lint refuses
anything that must not reach that audience, and the result is rendered, emitted as
`bloodbank.project.activity.recorded`, verified in Candystore, and (when the
project has one) written to the client portal.

## Prerequisite: declare the audience

Every command that touches text takes `--audience internal|external` and none
defaults it. The audience decides who may read the result, what the lint refuses,
whether the portal row is client-visible, and whether the event carries sources
and tickets. If the request does not say who reads it, ask before writing a word.

| | internal | external |
|---|---|---|
| Who reads it | the team, PMs, future agents | the client |
| Portal row | `visible_to_client = 0` | `visible_to_client = 1` |
| Register | dense, chronological, complete | narrative, warm, earned confidence |
| Length | up to 5000 chars | 120 to 250 words |
| Names tickets | always, by key and title | never |
| Event carries | `sources` and `tickets` | neither |

## Running it

```
activity-report run --project <slug> [--audience A]... [--dry-run] [--since T] [--until T] [--force]
```

`run` execs `scripts/run.sh`, which for each configured audience (internal first)
runs the stages below. Every stage is also a subcommand you can run by hand on the
same files; `runtime/activity-report/<slug>/<label>-<audience>.*` holds them,
where `<label>` is the window end in the project zone as `YYYY-MM-DDTHHMM`.

| stage | subcommand | what it proves |
|---|---|---|
| collect | `collect --audience A --run-id R --out D` | the digest: the whole window, nothing else |
| compose | headless `claude --print` with the template in `templates/` | one `raw.txt`, linted green |
| lint | `lint --audience A RAW --digest D [--lint-json J]` | nothing forbidden for this audience |
| render | `render --audience A RAW --digest D --md M --html H` | markdown and one self-contained html |
| assemble | `assemble --audience A --digest D --raw RAW --md M --html H --out E [--model M] [--dry-run]` | the event data, contract-checked locally |
| emit | `emit E --out J [--dry-run]` | `bb-emit --check`, then `--strict` publish |
| verify | `verify --run-id R [--audience A]` | the projection has the event |
| portal | `portal E [--dry-run]` | the row exists with the right visibility |
| retain | `retain --audience A RAW --digest D` | the report's facts are in the project's memory: `units=<n>` read back, empty extractions retried; internal only by default |

`--dry-run` (or `ACTIVITY_REPORT_DRY=1`) still emits the event, flagged
`generator.dry_run: true`, so a parallel night is visible in Candystore; it skips
verify, the portal row, retain and the durable html copy. `emit --dry-run` by
itself runs `bb-emit --check` and publishes nothing.

Exit codes, per audience and overall (the worst wins): `0` done, `2` config,
source or compose failure, `3` refused (lint, contract or verify), `4` nothing
to do (a window shorter than `window.min_minutes`; counts as done overall),
`5` another run holds the project lock. Logs:
`~/.local/state/activity-report/<slug>/<label>-<audience>.log`.

## Composing: the six steps

You are the compose stage when a runner hands you a digest, or when someone asks
for an update by hand. Either way:

1. **Declare the audience** and read the digest for it. Never re-collect; the
   digest is the whole window and what is not in it did not observably happen.
   For external, also read this run's internal `raw.txt`: it is the complete
   account you are choosing from.
2. **Find what the digest cannot know.** What was the point of the work, not
   just the commits? What did the previous update promise, and did it happen?
   What would the reader ask first? What is unresolved that they will hear
   about anyway? `git log`/`git show`/`git diff` answer the first; the previous
   report title in the digest answers the second.
3. **Choose what to lead with.** Spin is choosing which true thing to lead with.
   It is never asserting something that is not so. `references/composition.md`
   has the six rules in order of damage and the register for each audience.
4. **Write exactly one file**, `raw.txt`, in the format below. External is 120
   to 250 words; internal is as long as the window needs, under the cap.
5. **Run the lint and fix until green**:
   `activity-report lint --audience A RAW --digest D` (external adds
   `--lint-json J`). Exit 3 means it found something; the findings name the
   line and the rule. Rewrite, do not argue.
6. **Stop.** The runner renders, assembles, emits, verifies and publishes.
   By hand, run those stages yourself in that order, and never skip verify.

## raw.txt

Line 1 is `# <title>`: plain text, 2 to 180 characters, specific to the window.
Everything after it is the body in the portal grammar, at most 5000 characters:

```
## Heading             a section
- item                 a bullet (also `* item`)
| Metric | value |     a two-column metric row; a section of only these renders as tiles
HH:MM text             a timeline entry
anything else          a paragraph
```

`**bold**` is the only inline form. Anything else (HTML, links, nested lists,
tables wider than two columns) renders literally in the portal. Full grammar and
how each block renders: `references/portal-grammar.md`.

## Non-negotiables

- The external body never contains a ticket key, a commit sha, an absolute path,
  a tool-call count, burndown language, a sprint number, an agent name, the word
  "refactor", or the title of an internal-only ticket (verbatim or paraphrased).
  The lint refuses all of these; the Bloodbank validator refuses the first three
  again at emit.
- Never claim anything the digest does not show. Never invent significance for a
  quiet window; a quiet window gets a short, honest quiet update.
- Never widen the 5000-character body cap or the 180-character title cap. They
  are the portal's; a row past them cannot be edited in the admin console.
- One event per (project, window, audience). One portal row per (project,
  window end, visibility); a re-run overwrites its row, it never adds one.
- Never write both audiences in one pass: internal first, then external from it.
- The compose stage's tool grant is files, the lint and read-only git. Never
  widen it; an unattended agent that needs more should fail loudly.
- Verify independently of what the emitter or the agent believes. Success is
  the event in the projection and the row with the intended visibility.

## Per-project setup

1. Add an `activity_report` block to the repo's `.project.json`. Every key and
   its default is explained in `assets/example.project-block.json`; the block
   is optional and an absent one means the defaults.
2. `activity-report init` in the repo: installs the `~/.local/bin/activity-report`
   shim and checks the config and the runtime dir's gitignore.
3. `activity-report ensure-labels --confirm` once per board: creates the
   `xp:external` / `xp:internal` exposure labels. A ticket with the external
   label is always surfaced to the client; one with the internal label is never
   named to the client; unlabeled tickets are the agent's judgment call.
4. `activity-report install-timer --project <slug>` (or
   `scripts/install-timer.sh`): the nightly systemd user timer at
   `schedule.at` in the project zone. `timer-status` shows the last run and the
   next one. `references/scheduling.md` has the cutover order.

## Where to look

| you want | read |
|---|---|
| the client register, the internal register, the six rules, the exemplar | `references/composition.md` |
| the body grammar, how each block renders, the portal row and its id | `references/portal-grammar.md` |
| the timer units, the drop-in, dry parallel nights, the james-brennan cutover, intelliforia | `references/scheduling.md` |
| module signatures, file layout, the digest and event shapes, the mapping table | `references/internals.md` |
| what collect reads and how (Candystore, git, board, Hindsight, tokens) | `references/data-sources.md` |
| the event's `data` schema, vendored for reading | `assets/schemas/event-data.schema.json` |
| the config block, every key explained | `assets/example.project-block.json` |

## Related skills

- `bloodbank-integration`: the event contract itself (schema, validator,
  fixtures). Changes to the event shape go there, not here.
- `project-lifecycle`: where a project's board, labels and repos come from.
- The project's own invariants skill (for james-brennan,
  `.agents/skills/project-invariants`): read it before any deploy, data or
  cleanup decision the update might tempt you into. This skill writes updates;
  it never acts on the project.
