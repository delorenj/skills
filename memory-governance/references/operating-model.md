# Memory Operating Model

## Clocks and what they control

- **Heartbeat clock (agent runtime):** triage/dispatch loop and proactive checks.
- **Cron clock (scheduler):** exact-time reminders or isolated scheduled tasks.
- **QMD update clock (memory backend):** memory index refresh; independent from heartbeat and cron.

## Decision table

| Need | Use |
|---|---|
| Run continuous "what should I do now" loop | Heartbeat |
| Trigger at exact time (9:00am) | Cron |
| Keep memory index fresh | QMD update interval |
| Long-term memory curation | Dream cycle + promotion review |

## Memory write tiers

1. `memory/YYYY-MM-DD.md` = raw operational journal
2. `MEMORY.md` = curated durable context

Promote only durable items:
- stable preferences
- durable decisions/rules
- recurring workflows
- major lessons

## Dream cycle role

Nightly dream cycle should:
1. review latest daily logs
2. prune stale/noisy context
3. promote durable context into `MEMORY.md`
4. produce a short human-readable summary for the vault
