---
name: hindsight-memory-routing
description: Domain-first Hindsight memory architecture for multi-agent orgs. Use when designing bank strategy, wiring primary/secondary recall banks, or configuring per-agent memory routing and auto-capture hooks.
---

# Hindsight Memory Routing (Domain-First + Role Overlay)

Use this skill when you need high-signal long-term memory across many agents/projects.

## Core Strategy

**Primary bank = domain/product** (source of truth)

- Example: `wean`, `chorescore`, `33god-core`, `33god-infra`

**Secondary bank(s) = role/hierarchy overlay**

- Example: `exec-office` for leadership decisions

**Global fallback bank**

- Example: `33GOD` for org-wide context

Avoid agent-only banks as canonical memory (they drift when agents switch projects).

## Routing Pattern

For each agent/session:

1. Resolve **writeBank** (where new memories are retained)
2. Resolve **recallBanks[]** (ordered primary→secondary→fallback)
3. On prompt build, recall from each bank and merge results
4. On run end/reset/tool-error, retain high-signal facts into writeBank

## Recommended 33GOD Map

- `main` → write: `exec-office`, recall: `exec-office`, `33GOD`, `33god-core`, `33god-infra`
- `eng` → write: `33god-core`, recall: `33god-core`, `33god-infra`, `exec-office`, `33GOD`
- `infra` → write: `33god-infra`, recall: `33god-infra`, `33god-core`, `exec-office`, `33GOD`
- `mobile` → write: `chorescore`, recall: `chorescore`, `wean`, `exec-office`, `33GOD`
- `wean` → write: `wean`, recall: `wean`, `chorescore`, `exec-office`, `33GOD`
- `overworld` → write: `overworld`, recall: `overworld`, `exec-office`, `33GOD`

## Create/Verify Banks

```bash
hindsight create-bank exec-office
hindsight create-bank 33god-core
hindsight create-bank 33god-infra
hindsight create-bank chorescore
hindsight create-bank wean
hindsight create-bank overworld
hindsight list-banks
```

## Capture Policy (high signal only)

Retain automatically for:

- explicit memory intent ("remember", "don’t forget", preferences)
- post-run user facts/decisions
- high-level architectural patterns
- pre-reset session summaries
- non-standard system paths/configs
- tool errors (debugging context)

Do **not** retain:

- cron/noise/system spam
- tiny one-word messages
- slash commands

## Validation Checklist

1. Recall test:

```bash
hindsight recall wean "current blockers"
```

1. Retain test:

```bash
hindsight retain wean debugging "Detox build fails on duplicate META-INF/LICENSE.md"
```

1. Re-recall test:

```bash
hindsight recall wean "detox build blocker"
```

1. Confirm prompt injection shows merged bank lines (when hooks enabled).

## Failure Modes

- **Cross-project pollution**: writeBank too broad (fix routing)
- **Recall noise**: too many recallBanks/topK too high (tighten)
- **Missed intent**: memory-intent regex too strict (expand)
- **Latency spike**: recalling too many banks per prompt (cap at 3-4)
