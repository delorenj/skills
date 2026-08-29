---
name: heyma-pipeline-doctor
description: "Diagnose and repair the HeyMa audio pipeline (Wax): recording, ingest, transcription, diarization, enrichment passes, S3/MinIO archive, Bloodbank events, the tray, and the wax CLI. Use whenever a recording did not become a finished transcript, transcripts keep bare timestamp filenames instead of summary slugs, speakers are not labelled, the tray looks fine but nothing is happening, waxd seems wedged, audio is missing, or any wax command misbehaves. Also use before changing anything in components/wax so you start from a known state. Triggers: pipeline broken, transcription not running, no diarization, no speaker labels, enrichment pass failed, title-slug failed, filenames not renamed, wax status, waxd, tray green but broken, silent failure, transcript missing, audio not archived, MinIO/S3 archive, outbox stuck, wax doctor. Do NOT use for authoring a NEW enrichment pass (use create-enrichment-pass), for Bloodbank schema/event-contract work (use bloodbank-integration), or for non-HeyMa repos."
---

# HeyMa Pipeline Doctor

The pipeline is **Wax** — one daemon (`waxd`) that owns the microphone, the inbox,
the SQLite ledger, transcription, the enrichment passes, the S3 archive, the event
outbox, and the tray. It lives at `components/wax/`.

> Repo-root `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` described a retired n8n
> pipeline for months after it was replaced. If anything you read contradicts what
> the code does, trust the code and say so. The design doc of record is
> `components/wax/docs/WAX-DESIGN.md`.

## The one thing to know before you start

**Wax fails silently by construction.** Every value-producing sub-stage degrades by
returning an empty value rather than raising: a broken diarizer returns `[]` and
the transcript honestly records `diarized: false`; a broken enrichment pass is
recorded `failed` in the ledger and the item is still marked `complete` 215 ms
later. Historically none of that reached the tray, `wax status`, or the journal.

So: **never conclude "it's fine" from a green tray or a quiet journal.** Ask the
ledger. That is what the doctor script does.

## Step 1 — always run this first

```bash
.agents/skills/heyma-pipeline-doctor/scripts/doctor.sh
```

~40 s, read-only, safe during a recording. It prints a layered board:

```
  ✔ pass    ✘ fail    ▲ warn (degraded, not stopped)    ○ skipped
```

Useful flags: `--quick` (skip S3 round-trips and the test suite, ~8 s),
`--layer <name>`, `--only <check-id>`, `--json`, `--verbose`.

The layers run in **dependency order**, and a failure in an early layer marks the
dependent ones `○` instead of reporting a cascade of derived failures as causes.
**Fix the first failing layer, then re-run.** Do not fix the bottom of the board.

If `wax doctor` exists in the CLI, it complements this: it reports *resolved
configuration* (every env var, its value, and its source) from inside the
component. Run it when the board says a dependency is missing but you cannot see
why — the answer is usually that a var resolved somewhere you did not expect.

## Step 2 — read exactly one playbook

Load the reference for the **first** failing layer. Do not read them all.

| Board layer | Playbook |
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

Two more, worth their tokens:

- `references/architecture.md` — the map of moving parts and how a recording flows
  through them. Read when you need to reason about a failure the board does not
  name.
- `references/incident-log.md` — **read this early.** Every outage this pipeline
  has had, with its signature and its actual root cause. This system breaks in
  repeating shapes; pattern-matching here has repeatedly been faster than
  reasoning from first principles.

## Step 3 — fix, verify, land

1. Apply the smallest fix the playbook names.
2. Re-run `doctor.sh --layer <that layer>`. The check that was red must go green.
3. If you changed anything under `components/wax/src`, restart the daemon:
   `systemctl --user restart waxd.service` — the daemon does **not** hot-reload.
4. Re-run the full `doctor.sh`. Confirm you did not push the failure downstream.
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
- **Resolve paths from the running daemon, never from a doc.** `/proc/<pid>/fd`
  says which ledger is actually open; `/proc/<pid>/environ` says which root is
  actually in effect. A stale `~/audio/var/state.json` once cost an investigation
  an hour by looking exactly like a live status mirror.
- **Do not judge the ledger by `wax.db`'s mtime.** WAL mode leaves it untouched
  for hours while every write lands in `wax.db-wal`.
- **Never write a credential into a file.** Keys resolve at call time from
  `op://DeLoSecrets/...` references. Committing an `op://` path is correct;
  committing a value never is.

## When the board is all green and the user still has a problem

Then the failure is in something the board does not yet check — which means the
board has a gap, and closing it is part of the fix. Add the check to
`scripts/doctor.sh` in the right layer, with a `fail_means` message that names the
next step, and add the incident to `references/incident-log.md`. A troubleshooting
skill that does not learn is just documentation.
