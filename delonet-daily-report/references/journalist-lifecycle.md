# Journalist lifecycle

Use this reference to manage topic jobs and reconcile them against canonical
Hermes state.

## Reading order

Choose the path that matches the scheduler operation you need to perform.

| Task | Read |
|---|---|
| Add/update/remove a topic | This file |
| Reconcile cron | This file → `safety-gotchas.md` |
| Understand job prompts | This file → `investigator-workflow.md` |

## Owned jobs

Limit lifecycle operations to the following jobs owned by this skill.

- Create one `ddr:journal:<id>` Hermes cron job for every configured topic.
- Pause jobs for disabled topics; resume them when enabled.
- Keep exactly one `ddr:daily` aggregator, paused when `daily.enabled` is false.
- Fix `ddr:daily` at `0 7 * * *` in `America/New_York`; reportctl rejects other zones or aggregator schedules because Hermes has no per-job timezone flag.
- Remove managed jobs for deleted topics. Never mutate names outside `ddr:journal:` and `ddr:daily`.

## Topic commands

Use `reportctl topic` commands to mutate configuration atomically.

```bash
scripts/reportctl --config /path/report.json topic add ai-agents "AI Agents" \
  --prompt "Material agent platform releases and research" \
  --source https://example.org/releases --schedule "15 6 * * *"
scripts/reportctl --config /path/report.json topic update ai-agents --schedule "30 6 * * *"
scripts/reportctl --config /path/report.json topic pause ai-agents
scripts/reportctl --config /path/report.json topic resume ai-agents
scripts/reportctl --config /path/report.json topic remove ai-agents
```

Every mutation validates the full config and uses atomic replacement. Duplicate IDs fail without changing the file.

## Reconciliation

Reconciliation brackets the initial canonical jobs read with fingerprints before
it plans or executes any action.

Use `plan` first. With no `--jobs`, plan/status/health read canonical
`$HERMES_HOME/cron/jobs.json` directly; they never scrape human CLI output.
Explicit snapshots remain available for offline read-only planning. `reconcile
--apply` rejects snapshots, takes a profile-scoped lock, fingerprints before and
after its initial canonical read, and aborts before planning or mutation when
those fingerprints differ. It then uses optimistic fingerprints plus ID/name
checks around every mutation.

The stable plan orders duplicate removals, stale removals, creates, edits,
pauses, and resumes by job name and ID. Managed jobs attach
`delonet-daily-report` with `--skill`; apply preflight requires that skill under
the active `$HERMES_HOME/skills`. The active profile’s `config.yaml` must
authoritatively match the configured timezone and required
`inference.provider`/`inference.model`; a conflicting `HERMES_TIMEZONE` fails
preflight. Hermes snapshots those profile defaults when a public cron create
command runs. Snapshot drift triggers a remove-first recreate. Every create uses
a far-future one-shot staging schedule, pauses the returned ID immediately,
verifies ID/name ownership and snapshots, edits desired fields while paused,
and resumes only after a final post-check when configuration enables the job.
Failures trigger verified pause/remove compensation so no unsafe replacement
remains. The controller never edits `jobs.json` directly and never passes
unsupported provider or model flags.
Health flags null or mismatched snapshots. It also converts observable
`next_run_at` through `zoneinfo` and requires the exact next future 07:00 Eastern
occurrence, including DST transitions. Stale and later-day values fail health.

Journalist prompts name the reporting window, sources, three investigator roles, exact section path, and contract. Aggregator prompts validate every expected section, mark stale/missing manifest entries, and archive JSON plus Markdown.
