---
name: heyma-pipeline-doctor
description: "Diagnose and repair Wax incidents in audio or document execution: stalled recordings, missing transcripts or speaker labels, failed EPs, archive/outbox errors, stale worker heartbeat or a misleading green tray. Use when waxd or a Wax command misbehaves, and establish a baseline before changing its runner. The legacy doctor board covers audio, not document-binding health. Normal pipeline discovery, bindings, compiles/imports, n8n graph authoring and Holocene belong to wax-pipeline; new portable EP implementation belongs to create-enrichment-pass; event schemas belong to bloodbank-integration."
---

# HeyMa Pipeline Doctor

The pipeline is **Wax** — one daemon (`waxd`) that owns the microphone, the inbox,
the SQLite ledger, transcription, the enrichment passes, the S3 archive, the event
outbox, the document bindings, and the tray. It lives at `components/wax/`.

**This skill owns incidents**: something is wrong and you need to find, fix, and
land it. Neighbouring skills own the rest:

- **`wax-pipeline`** — operating the pipelines: catalog reads, pipeline
  compile/import, document runs and folder bindings, n8n Wax graph authoring,
  the read-only Holocene surface. Its `references/documents.md` and
  `references/pipelines-and-n8n.md` are the detailed operations guides.
- **`create-enrichment-pass`** — authoring a new enrichment pass from scratch.

> Docs drift; code is truth. The current documents of record are
> `components/wax/docs/WAX-DESIGN.md` (architecture),
> `components/wax/docs/ENRICHMENT-PASSES.md` (pass, event and document
> contract), and `components/wax/docs/CONTROL-SURFACE.md` (the released
> pipelines and CLI-first operation). If anything you read contradicts the
> code, trust the code and say so.

## The one thing to know before you start

**Wax's failure mode is degradation, not crashing — and completion is
plan-gated.**

The dated gotcha that shaped this system: in the 2026-08-12 and 2026-08-15
outages (see `references/incident-log.md`), value-producing sub-stages degraded
by returning empty values instead of raising — a broken diarizer returned `[]`
and the transcript honestly recorded `diarized: false`; a broken enrichment
pass was recorded `failed` while the item still parked `complete` — and none of
it reached the tray, `wax status`, or the journal. Both ran at 100% failure for
days behind a green tray. That design shape is why "green is not evidence"
is still the standing rule here.

Today the pipeline gates completion on the plan:

- `transcription.completed` is written **only when every planned pass** is
  `completed` or `skipped` at the plan's version; a failed pass leaves the item
  `enrichment_pending` until it succeeds on retry.
- Pass failures carry a `reason_code` in the ledger and in the note's
  `wax.passes.<slug>` block; a pass that exhausts its attempt budget emits the
  **`bloodbank.audio.task.exhausted`** dead-letter event instead of failing
  silently.
- A malformed registry entry (bad `requires`/`after`/`when`, a missing or
  disabled dependency) **quarantines** just that pass and its dependents —
  loudly, in `wax ep list` and `wax doctor` — rather than degrading the fleet.
- The worker sweeps failed passes on a timer (`WAX_SWEEP_INTERVAL_S`, default
  900 s); retries are not manual-only.

What still degrades quietly, and why you are here: sub-stage *values* can still
collapse to empty (`diarized: false` is an honest record of a failed diarizer),
and `wax status`'s summary can read calm while a value-producing stage is dead.
So: **never conclude "it's fine" from a green tray or a quiet journal.** Ask
the ledger and the doctor.

## Step 1 — CLI first

```bash
mise x -- ./bin/wax doctor          # resolved config + one probe per thing that can rot
mise x -- ./bin/wax status          # both state machines, queue, pass + diarization health
mise x -- ./bin/wax catalog --json  # pipelines, drift, bindings, worker freshness
```

(from the repo root; installed `wax` and `mise run wax:doctor` work too)

`wax doctor` is the component's own probe set — registry quarantine, the title
provider's key and model, pass-event schemas, the pjangler registry, diarization
device policy plus a **real Sortformer CUDA forward pass**, the daemon's
transcriber pin, state-mirror age, outbox staleness. Its rules are narrow and
absolute: it may never report health it has not just verified, and it never
prints a resolved secret (it prints *which* field answered, never what it
said). `wax catalog --json` is the same safe projection Holocene reads —
frozen graphs, drift, bindings, recent runs, worker heartbeat.

Then, for the deeper layered board:

```bash
.agents/skills/heyma-pipeline-doctor/scripts/doctor.sh
```

~40 s, read-only, safe during a recording. It prints:

```
  ✔ pass    ✘ fail    ▲ warn (degraded, not stopped)    ○ skipped
```

Useful flags: `--quick` (skip S3 round-trips and the test suite, ~8 s),
`--layer <name>`, `--only <check-id>`, `--json`, `--verbose`.

The layers run in **dependency order**, and a failure in an early layer marks
the dependent ones `○` instead of reporting a cascade of derived failures as
causes. **Fix the first failing layer, then re-run.** Do not fix the bottom of
the board.

**Coverage caveat — the board is not end-to-end proof.** It checks the *audio*
pipeline: capture, inbox, transcription, diarization, archive, events, desktop,
deploy. It does **not** cover document pipelines (folder bindings, document
receipts, scan cadence) or pipeline compilation. For those, read
`wax catalog --json` and `wax documents list` (see `wax-pipeline`). A green
board plus a broken document flow is expected behaviour of the board, not
evidence the document flow is fine.

If the board and `wax doctor` disagree, the CLI is authoritative — it runs
inside the component against the daemon's resolved environment, which the
board can only approximate from `/proc`.

## Step 2 — read exactly one playbook

Load the reference for the **first** failing layer. Do not read them all.

| Problem | Playbook |
|---|---|
| Daemon, Paths & ledger, Deploy, Repo hygiene | `references/control-plane.md` |
| Capture | `references/capture-ingest.md` |
| Queue & inbox | `references/capture-ingest.md` |
| Stage outcomes — titles/slugs | `references/enrichment.md` |
| Stage outcomes — diarization | `references/transcription.md` |
| Enrichment dependencies | `references/enrichment.md` |
| Transcription dependencies | `references/transcription.md` |
| Archive | `references/archive.md` |
| Events | `references/events.md` |
| Pipelines, documents, n8n graph (not an incident) | `wax-pipeline` skill |

Two more, worth their tokens:

- `references/architecture.md` — the map of moving parts and how a recording
  (and, now, a document) flows through them. Read when you need to reason
  about a failure the board does not name.
- `references/incident-log.md` — **read this early.** Every outage this
  pipeline has had, with its signature and its actual root cause. This system
  breaks in repeating shapes; pattern-matching here has repeatedly been faster
  than reasoning from first principles.

## Step 3 — fix, verify, land

1. Apply the smallest fix the playbook names.
2. Re-run the layer that was red: `doctor.sh --layer <that layer>` and/or the
   matching `wax doctor` probe. The check that was red must go green.
3. If you changed anything under `components/wax/src` (the Python runner),
   restart the daemon: `systemctl --user restart waxd.service` — the daemon
   does **not** hot-reload Python. Live-registry YAML is re-read on each call;
   compiled graphs need explicit import/compile to adopt config changes, and
   existing minted plans stay frozen. A plain restart preserves the encoder scope.
4. Re-run the full `doctor.sh`. Confirm you did not push the failure
   downstream.
5. Commit and push. Never leave a repaired pipeline uncommitted.

## Rules that keep you from making it worse

- **The audio is the irreplaceable artifact and is never deleted.** Not by you,
  not by a script, not "temporarily". If a check reports unbacked audio, that is
  the only real emergency on the board — stop and resolve it first.
- **Read-only until you know the cause.** Every check in the script is read-only
  on purpose. Do not `wax reconcile --rebuild`, do not restart, do not move files
  to "see if it clears" — the state on disk *is* the evidence.
- **`~/audio/` is retired.** The live root is the repo (`WAX_ROOT`, default
  `~/HeyMa`), so `inbox/`, `stream/`, `var/`, `archive/` are all inside it.
  Anything under `~/audio/` is a leftover and lies convincingly.
- **Resolve paths from the running daemon, never from a doc or your own PATH.**
  `/proc/<pid>/fd` says which ledger is actually open; `/proc/<pid>/environ`
  says which root and `WAX_TRANSCRIBE` pin are actually in effect. A stale
  `~/audio/var/state.json` once cost an investigation an hour by looking
  exactly like a live status mirror; a PATH-resolved `transcribe` copy made the
  board cry "two checkouts" at a correctly pinned daemon.
- **Do not judge the ledger by `wax.db`'s mtime.** WAL mode leaves it untouched
  for hours while every write lands in `wax.db-wal`.
- **Never write a credential into a file, and never print a resolved one.**
  Keys resolve at call time from `op://DeLoSecrets/...` references; `wax doctor`
  masks credential-named values. Committing an `op://` path is correct;
  committing a value never is.

## When everything is green and the user still has a problem

Then the failure is in something the checks do not yet cover — which means the
coverage has a gap, and closing it is part of the fix. Add the check to
`scripts/doctor.sh` in the right layer (or a probe to `wax doctor` in the
component), with a `fail_means` message that names the next step, and add the
incident to `references/incident-log.md`. A troubleshooting skill that does not
learn is just documentation.
