---
name: litellm-fallback-ladders
description: Build ordered provider ladders in LiteLLM router configs.
---

# litellm-fallback-ladders

Use when a consumer needs a strictly ordered chain of providers — e.g. "new provider first, then free pools, then metered, then subscription last resort" — expressed in a `litellm-config.yaml`. Covers the fallbacks-vs-multi-deployment law, env plumbing, and verification.

## The one law

**A ladder must be `router_settings.fallbacks` chains, never multiple deployments under one `model_name`.** Same-name deployments are load-balanced (simple-shuffle) across all of them: a "primary" listed first is NOT tried first — every rung fires at random. This fails silently: calls succeed, but on random providers, so a cost-isolation ladder quietly bills the expensive rung half the time. Ordered semantics live only in fallbacks.

## Recipe

1. Give each rung its own `model_name` (`hs-free-retain`, `hs-or-retain`, …) with a single deployment each. One model group per rung, role-suffixed so the chain reads as a ladder.
2. The consumer-facing names (`hindsight-retain`, …) are the primary group — rung 1's deployment.
3. Express the order once, in `router_settings.fallbacks`:

```yaml
router_settings:
  fallbacks:
    - hindsight-retain: [hs-free-retain, hs-or-retain, hs-auto-retain]
```

4. Keys: one env var per provider (`os.environ/NAME`); raw-key gitignored env file (0600) when the vault write path is unavailable — never commit raw keys to a tracked `.env.op`.

## Pitfalls

- **Compose interpolation reads `--env-file`/shell env, not service `env_file`.** A var defined only in a service-level `env_file:` still fails `required variable X is missing` at `up`. Pass it on the command line: `op run --env-file .env.op --env-file .env.ladder -- docker compose up -d` (op run accepts multiple `--env-file`).
- **Config edits do not hot-reload.** A bind-mounted config still needs `docker compose restart <svc>` before new groups appear; verify with `GET /model/info` — the new rung groups must be listed.
- **Verify which rung served, not just that the call returned 200.** Check the provider's own usage ledger (gateway logs table, provider dashboard) for absence/presence of rows in the window — an empty `choices[0].message.content` with a 200 usually means a fallback fired or a reasoning model burned the token budget (see below).
- **Reasoning models can return empty `content` at small `max_tokens`** — visible reasoning (`reasoning_content`) consumes the budget before prose. Probe with `max_tokens ≥ 256` before concluding a rung is broken.
- **Dormant rungs are fine.** A provider with exhausted credits stays in the chain as the rung that wakes on top-up — LiteLLM skips it on failure and falls to the next.
