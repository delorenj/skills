---
name: delonet-daily-report
description: Operate the merged DeLoNET Daily Report — one deterministic pipeline that writes the daily developer journal from the Candystore audit trail and git history, plus Hermes fleet health, nightly PR maintenance from pr-crusher state, and a report-delivery self-check that catches its own missed runs. Deterministic local collectors emit schema-validated SectionArtifacts with honest complete/partial/stale/failed status, a manifest enumerated from config (never from disk), one bounded LLM narration pass, and atomic immutable archive generations behind a current.json pointer. Use for reportctl, `reportctl verify`, daily journal or daily report work, section/collector configuration, coverage and freshness, stale or missing sections, archive publication, and diagnosing a report that silently did not run. Replaces the retired candystore-daily-journal skill. Do not use for Hermes fleet provisioning, Bloodbank schema changes, external news reporting, or general cron administration.
---

# DeLoNET Daily Report

One report, one cron job, one narrator pass. Deterministic collectors read real
local sources; the framework refuses to describe a run as better than it was.

**This skill replaces `candystore-daily-journal`**, which is retired into it as
the `dev_activity` collector.

## The rule that outranks everything else

> Never report success you did not achieve.

Both systems this merge replaces failed the same way on 2026-08-18: a Hermes cron
job logged "completed successfully" over a command that exited 2, and the journal's
own event hardcoded `outcome.status="complete"` with all four sections `"complete"`
on every run, regardless of what happened.

Every status in this package is derived from a file that was actually read:

| Rule | Where it lives |
|---|---|
| A section's `status` describes the **collection**, never the news it found | `collectors/*.py`, most visibly `collectors/report_delivery.py` |
| `complete` when every enabled section completed; `failed` when none did, or when a **required** section did not run at all (`failed` / `missing` / `stale` / `invalid`); `partial` otherwise | `reportctl_archive.derive_status` |
| A non-complete section must carry a `reason` | `validate_section_artifact` |
| Coverage is enumerated from config, never from disk | `artifact_health`, `validate_run_manifest` |
| A crashing collector degrades the report, never vanishes from it | `collectors.base.run_collector` |
| Truncation is always recorded in `caveats` | `collectors.base.enforce_byte_cap` |
| A required section may not be disabled, and one must exist | `reportctl_config.validate_config` |
| The published artifact is checked, not the scheduler's own account of itself | `reportctl verify` |

`reportctl verify --date YYYY-MM-DD` exits non-zero when no valid report is
published for that date. That single command is what would have caught the silent
failure, and it is the acceptance gate for the whole pipeline.

### Status is about the collection, not about the news

The rule above has a corollary that is easy to get backwards, and getting it
backwards latched this pipeline into a failure it could not leave.

| A section reports | when |
|---|---|
| `complete` | it read every source it needed and produced a trustworthy answer — **including** when that answer is "three days are missing and here they are" |
| `partial` | some source could not be read, so the answer is incomplete |
| `failed` | it could not do its job at all |

`report-delivery` finding a missed run is therefore a **complete** collection
reporting bad news. The bad news goes in `summary` (`report-delivery: DELIVERY
FAILED -- 6 of 6 due day(s) … have no valid published report (6 missing).`), in
`metrics.delivery_health` (`ok` / `degraded` / `failed` / `unknown`), in
`caveats` (as `DELIVERY FAILED: …`, placed first so the "Risks and Watchlist"
section renders it), and in `detail` — never in `status`.

That matters because `derive_status` fails a run when a **required** section did
not run, and `report-delivery` is required. Putting the verdict in `status` made
one missed day fail the run; a failed run publishes a generation `verify` refuses;
a refused generation is what tomorrow's `report-delivery` scan calls `invalid` —
so the gap regenerated itself and the pipeline could never return to green. A
report whose whole job is to say something is wrong cannot be suppressed as a
failure for saying it.

The teeth are unchanged: a required collector that could not read its sources
still returns `failed`, still fails the run, and still exits 3.

## Sections and collectors

Sections are declared in config; each names a module under `scripts/collectors/`.

| Section | Collector | Required | Reads |
|---|---|---|---|
| `dev-activity` | `dev_activity` | yes | Candystore `/events` + `/summary/heatmap`, `git log` per configured project root |
| `fleet-health` | `fleet_health` | no | `~/.hermes/agents-registry.yaml`, `systemctl --user list-timers hermes-*`, each profile's `cron/jobs.json` — verifies the artifact, not `last_status` |
| `pr-maintenance` | `pr_maintenance` | no | `~/.local/state/pr-crusher/repos/*/summary.json` and `runs/tick-*/summary.json` |
| `report-delivery` | `report_delivery` | yes | this skill's own `archive/*/current.json` for the last N days plus Candystore `reporting.report.completed` events |

Every collector module exposes:

```python
def collect(section: dict, date: str, config: dict) -> SectionResult
```

`run.py` calls it positionally; collectors that also accept the keyword form
(`date=`, `config=`) work either way.

It returns a `SectionResult`; it does not decide the run's fate. A source it
could not read is `status="partial"` or `"failed"` with a reason naming the
source — never an exception and never a fake `complete`. A source it read
successfully is `complete`, whatever it found there.

## Bounding collector output: a field allowlist, not a secret scanner

The retired `reportctl_security.py` regex denylist is gone. It took the pipeline
down on 2026-07-25 on false positives, and a denylist can also miss a token shape
nobody has seen yet. Its replacement is stricter in both directions:

- `collectors.base.allowlist(obj, allowed_keys)` returns a copy holding **only**
  the named keys, recursively. Anything a collector attaches that is not named
  simply does not exist by the time the narrator sees it.
- A hard byte cap (default 256 000) bounds the serialized result. Overflow
  truncates the `detail` array and states the truncation in `caveats` —
  "showing 30 of 43", never silently.
- The committed mirror is additionally covered by the global `pre-commit` guard
  in `~/.config/git/hooks/`.

## Commands

```text
reportctl --config PATH validate            # config schema v2
reportctl --config PATH paths   --date D    # artifact and archive locations
reportctl --config PATH status  --date D    # section, manifest, and publish state
reportctl --config PATH collect --date D [--section ID ...]
reportctl --config PATH run     --date D [--section ID ...] [--no-narrate] [--no-emit] [--no-mirror]
reportctl --config PATH verify  --date D [--require-complete]
reportctl --config PATH archive --report R.json --markdown R.md [--manifest M.json]
```

`run` is the whole pipeline: collect, manifest, narrate, publish, mirror, emit.
`--section` limits **collection only** — every enabled section is still
enumerated in the manifest, so one left uncollected is reported `missing`
rather than dropped.

`--date` defaults to **yesterday**: the report is always about a day that has finished.

Exit codes are part of the contract:

| Code | Meaning |
|---|---|
| 0 | the command did what it says it did |
| 2 | configuration, contract, or I/O error |
| 3 | the run or the published artifact did not meet its acceptance check |

`collect` exits 3 when any selected section did not complete. `run` exits 3 when
the derived status is `failed` — no section completed, or a **required** section
did not run — and 2 when the publish itself failed; `complete` and `partial`
both exit 0, because a report that admits a gap is a successful report. `verify`
exits 3 when the artifact is absent, invalid, or records a run whose status is
`failed`; add `--require-complete` to also fail on a published report that
honestly admits a degraded section.

A run that reports six undelivered days exits **0**. That is the report working,
not the report failing, and the exit code has to say so or nobody ever reads the
document that names the six days. What exits non-zero is a run that did not
happen and a collector that could not read its sources.

`python3 -m collectors.report_delivery` follows the same split: its exit code
answers "could the check run" (0 when both sources were read), and the delivery
verdict goes to **stderr** plus `metrics.delivery_health` on stdout.

## What one run does

1. **Collect** — every enabled section through `run_collector`, so a collector
   that raises becomes a `failed` artifact and the run continues.
2. **Manifest** — expected sections enumerated **from config**, each resolved by
   reading its file back: `complete` / `partial` / `missing` / `invalid` /
   `stale` / `failed`. A section that failed to write is caught here.
3. **Narrate** — one LLM call (see below), or the deterministic render.
4. **Publish** — `archive_report` stages a generation, fsyncs, renames, then
   swaps `current.json`; the publish is then re-read and verified. The report
   pair is mirrored to `~/code/33GOD/_bmad-output/daily-journals/<date>/`
   (override with `DDR_MIRROR_DIR`), and one Bloodbank event is emitted.

## The narrator

One call, one provider, no fan-out. `narrator.provider` and `narrator.model`
from config are passed to the local Hermes CLI:

```bash
hermes -z <PROMPT> --ignore-rules -t todo --provider <provider> -m <model> \
    --usage-file <tmp>
```

`-t todo` is a containment, not a preference. `-z` auto-bypasses approvals and
the default toolset includes `terminal`, `file`, `code_execution`, `delegation`
and every configured MCP server — measured on this host, the default invocation
answered a "run `id -un`" prompt with `TOOLRESULT=delorenj`. The payload carries
text this pipeline did not write (commit subjects, PR titles, decision notes
from other repositories), so the narrator must not hold a shell. With
`-t todo` the same prompt answers `SHELL_UNAVAILABLE` and the only tool exposed
is the in-session task list. `-t ''` silently falls back to the full default set,
and an unknown toolset makes hermes refuse to start — which surfaces as a
narrator failure and the deterministic render, so this fails closed.
`DDR_NARRATOR_TOOLSETS` overrides it.

`hermes -z/--oneshot` prints only the final response text, which is what makes
it usable from a script. The binary is resolved from `~/.local/bin/hermes`, then
the hermes-agent venv, and only then `PATH` — `PATH` on this host picks up
per-agent launcher wrappers that rewrite `HERMES_HOME`, and the narrator must
not depend on who invoked the run. `DDR_NARRATOR_CMD` overrides the lookup and
`DDR_NARRATOR_TIMEOUT` the 300 s timeout.

Three things the narrator cannot do:

- **Change a status.** Statuses are derived in `run.py` from files that were
  read. Every narrated collector section is published with the authoritative
  status line ahead of the prose, and `coverage-freshness` is never narrated at
  all — it is rendered from the manifest.
- **See unbounded input.** The payload is field-allowlisted through
  `collectors.base.allowlist` and capped at 256 000 bytes; overflow drops detail
  lines and says so *inside the payload*, so the model knows its view is partial.
- **Report its own success.** The exit code is only one claim; the
  `--usage-file` report is read as a second one, and an exit of 0 with
  `failed: true` is treated as a failure. If the usage report names a different
  model than the one configured, the report says so.

Any narrator failure — disabled, missing CLI, timeout, non-zero exit, output
that does not parse, a section body omitted — falls back to the deterministic
render from `assets/report-template.md` and degrades the report to `partial`
with a caveat naming the failure. A narrator outage never blocks publication.

## The Bloodbank event

One event per run to the local Dapr sidecar (`DAPR_HTTP_PORT`, default 3504),
written to `<artifact_dir>/<date>/report-event.json` whether or not it is
published:

- `bloodbank.reporting.report.completed` when the report was published, with
  `outcome.sections` copied from the manifest and `outcome.status` equal to the
  status of the report that was actually published — never more.
  The schema makes `outcome.status` a function of the sections map: `partial`
  is only valid when something is degraded. So a run whose sections all
  completed but whose narrator died (published as `partial`) names the degraded
  narration as its own component, `report-narration`, rather than rounding the
  envelope up to `complete`.
- `bloodbank.reporting.report.failed` when nothing completed or the publish
  failed. A failed run never emits a `completed` event.
- `delivery` is derived from the mirror: `delivered` only when the copy landed.

The predecessor hardcoded `outcome.status="complete"` with four `"complete"`
sections on every run. `scripts/tests/test_run_pipeline.py::EventTests` locks
the replacement in.

The cron subcommands (`plan`, `reconcile`, `health`) and `topic` are gone. There
is one job now, and `verify` is how its correctness is established.

## Contract versions

They move independently. Read the JSON Schemas in `assets/contracts/` as normative.

| Contract | Version | Note |
|---|---|---|
| config | **2** | `topics` replaced by collector-backed `sections`; adds `narrator`, `project_roots` |
| SectionArtifact | **2** | `findings`/`sources` optional (local sources have no URLs); adds `metrics`, `detail`; `reason` required unless `status` is `complete` |
| RunManifest | 1 | unchanged |
| DailyReport | 1 | unchanged |

## Setup

1. Copy `assets/example-config.v2.json` outside the skill (canonically
   `~/.config/delonet-daily-report/report.json`) and adjust `project_roots` and
   section `options`.
2. `scripts/reportctl --config PATH validate`.
3. `scripts/reportctl --config PATH run --date YYYY-MM-DD`.
4. `scripts/reportctl --config PATH verify --date YYYY-MM-DD` — this is the gate.

This package never writes `~/.config` or `~/.hermes` itself. Operators choose
paths and apply changes explicitly.

## Route by intent

```text
├─ Components, paths, filesystem contract → references/architecture.md
├─ Compose, validate, and publish a report → references/report-composition.md
└─ A report that lied, went stale, or vanished → references/safety-gotchas.md
```

## Out of scope

- **External news or feed reading** — a different product. Diluting the journal
  with it is how both predecessor systems ended up half-built.
- **Hermes installation, profiles, or fleet provisioning:** use `33god-agent-fleet-operations`.
- **Bloodbank event schemas or publishers:** use `bloodbank-integration`.
- **Re-enabling pr-crusher's Bloodbank publisher** — a clean follow-up; for now
  its state is read directly from disk.
- **General-purpose cron administration:** use Hermes cron documentation directly.
