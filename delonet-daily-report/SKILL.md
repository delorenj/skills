---
name: delonet-daily-report
description: Operate the DeLoNET Daily Report pipeline; configure tracked news topics and sources, batch three ephemeral investigator roles, reconcile durable Hermes cron journalists named ddr:journal:{id} and the ddr:daily aggregator, validate SectionArtifact/RunManifest/DailyReport JSON contracts, compose freshness-aware briefs and a daily company rollup, archive reports, and diagnose scheduler health. Use for reportctl, daily intelligence reports, requests like "add X to my daily report", topic add/update/pause/resume/remove, stale or duplicate sections, source policy, journalist lifecycle, cron reconciliation, and report safety. Do not use for Hermes fleet provisioning, Bloodbank changes, general news writing, or arbitrary cron administration.
---

# DeLoNET Daily Report

Route daily-report work to the smallest necessary reference set, then use `scripts/reportctl` for deterministic state changes and reconciliation.

## Operating principles

- Keep configuration as the source of truth; treat Hermes cron as reconciled runtime state.
- Pin `inference.provider` and `inference.model` to the authoritative active Hermes profile; recreate jobs whose native snapshots drift.
- Use three ephemeral investigator roles per topic run when subagents are available; never make investigators durable.
- Make journalists durable only as `ddr:journal:<id>` jobs and keep exactly one `ddr:daily` aggregator.
- Preserve evidence lineage, timestamps, and freshness state through every contract boundary.
- Plan first. Apply cron changes only after reviewing the stable reconciliation plan.

## Route by intent

```text
Need to change the system?
├─ Understand components, paths, or contracts → references/architecture.md
├─ Add or assess feeds, sites, APIs, or trust rules → references/sources.md
├─ Run multi-agent research for one topic → references/investigator-workflow.md
├─ Add/update/pause/resume/remove topics or reconcile cron → references/journalist-lifecycle.md
├─ Build, validate, or archive a daily report → references/report-composition.md
└─ Diagnose duplicates, stale sections, leaked secrets, or unsafe output → references/safety-gotchas.md
```

## Common combinations

| Scenario | Read in order |
|---|---|
| Bootstrap or redesign the pipeline | `references/architecture.md` → `references/journalist-lifecycle.md` |
| Add a topic with credible sources | `references/sources.md` → `references/journalist-lifecycle.md` |
| Execute a journalist run | `references/investigator-workflow.md` → `references/report-composition.md` |
| Debug a bad daily brief | `references/safety-gotchas.md` → `references/report-composition.md` |
| Recover scheduler drift | `references/journalist-lifecycle.md` → `references/safety-gotchas.md` |

## Controller workflow

1. Copy `assets/example-config.json` outside the skill and customize it.
2. Run `scripts/reportctl --config PATH validate`.
3. Mutate topics with `topic add|update|pause|resume|remove`; writes are atomic.
4. Run `scripts/reportctl --config PATH plan --jobs SNAPSHOT.json` for offline planning, or omit `--jobs` to read canonical `$HERMES_HOME/cron/jobs.json`.
5. Review commands, then run `scripts/reportctl --config PATH reconcile --apply`. Never use `--apply` casually.
6. Archive validated output with `archive --report REPORT.json --markdown REPORT.md`; writes are atomic.
7. Run `status`, `health`, and `paths --date YYYY-MM-DD` to inspect coverage and archive locations.

## Cross-cutting rules

- **Never embed credentials.** Store only public source URLs and environment-variable names; redact secret-like values from status and plans.
- **Reject silent data loss.** Mark missing, invalid, or old section artifacts stale; do not omit them without a manifest entry.
- **Use stable identifiers.** Topic IDs are lowercase kebab-case and permanently determine job names and section paths.
- **Keep aggregation separate.** Journalists emit `SectionArtifact`; only `ddr:daily` emits `RunManifest` and `DailyReport`.
- **Batch investigators.** Spawn the primary-source researcher, change tracker, and skeptic concurrently in one request when delegation exists; collect results, then terminate them.

## Out of scope

This skill covers one report pipeline and its owned cron jobs. It does not cover:

- **Hermes installation, profiles, or fleet provisioning:** use `agent-fleet-operations`.
- **Bloodbank event schemas or publishers:** use `bloodbank-integration`; make no Bloodbank edits.
- **General-purpose cron administration:** use Hermes cron documentation directly.
- **n8n workflow design:** use `delonet-n8n-architecture`.
- **Live configuration installation:** operators choose paths and explicitly apply changes; this package never writes `~/.config` or `~/.hermes` during setup or tests.
