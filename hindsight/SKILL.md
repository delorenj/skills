---
name: hindsight
description: Recall and retain project context through Hindsight. Use for relevant project history or explicit memory work. Runtime hook and plugin maintenance is a separate, scoped operation.
---
# Hindsight memory

Use the installed CLI and `~/.hindsight/config`. The service endpoint is
`https://api.hs.delo.sh`; use current hostname routing rather than a pinned IP.
Current source and live evidence outrank recalled facts.

## Resolve the bank

Run from the task's working directory:

```bash
BANK=$(bash ~/.agents/skills/hindsight/scripts/hs-bank-id.sh)
hindsight memory recall "$BANK" "<relevant project question>"
```

The helper calls `~/.agents/hooks/lib/hindsight-bank.sh`. The shared resolver
honors the main checkout's `.hindsight/bank`, then `HINDSIGHT_BANK`, origin name,
main checkout basename, and CWD basename outside Git. Do not recreate that logic
with `--show-toplevel` or a `general` fallback. It must stay worktree-safe.

Other relevant banks include `infra`, `docker`, and `33GOD` (exact case).
Do not use retired `33god`, `33god-core`, or `33god-infra` names. Use
`hindsight bank list` for the actual inventory; PJangler lists projects.

## Scope and operations

Hooks may supply context already. Recall manually when useful context is missing.
Retain only within the session's memory permissions and avoid duplicate capture.
Never retain credentials. Do not treat a memory request as authorization to
reconfigure hooks, schedulers, other clients, or retention policy.

A retain that fails with 403 / "operation not allowed" / `PermissionDeniedError`
is not auth: Hindsight's fact-extraction and consolidation LLM calls (OpenRouter
behind `hindsight-litellm`) hit the org monthly budget or the key's daily limit.
A failed retain stores nothing. `hindsight operation list <bank>` shows the real
error; once budget returns, `hindsight operation retry <bank> <operation-id>`.
Pass `--doc-id` on CLI retains: two in the same second share an auto id and the
second replaces the first.

- [CLI operations](references/cli-operations.md): retain, recall, reflect, models,
  directives, documents, and bank management; confirm installed help if it differs.
- [Multi-bank routing](references/multi-bank-routing.md): project versus identity
  context, when the task actually needs multiple banks.
- [Runtime integrations](references/runtime-integrations.md): OpenClaw, Hermes,
  and Claude integration maintenance, only for the named runtime in scope.

This package owns memory procedures. Global instructions should link here rather
than copy the bank algorithm or integration-specific requirements.
