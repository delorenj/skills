---
name: automaticai-gateway-ops
description: Operate the AutomaticAI gateway — tokens, channels, catalog.
version: 1.0.0
author: grolf
license: MIT
metadata:
  hermes:
    tags: [gateway, llm-routing, devops]
    related_skills: [typesafe-ai, litellm-fallback-ladders]
---

# automaticai-gateway-ops

## When to Use

Use when a task requires mutating or debugging the AutomaticAI gateway at `api.automaticai.io` (Go new-api fork, remote `aai-gateway` host, Postgres `newapi-postgres` + redis `newapi-redis` reachable via `ssh aai-gateway docker exec …`): minting scoped tokens, adding provider channels, exposing new `automaticai/*` models, repointing the auto-router classifier, or diagnosing 403/400 on gateway models. Covers the catalog gate, cache/restart rules, and verification patterns.

## Admin session

- The admin API session token expires fast. Re-login with curl and a browser User-Agent — Cloudflare 403s the plain urllib UA: `curl -s -X POST https://api.automaticai.io/api/user/login -H 'Content-Type: application/json' -d '{"username":…,"password":…}'` (creds `op://DeLoSecrets/n6g3t4ljymbexmjm3x43pu6bc4/*`). Send admin calls with `New-Api-User: 1` and the browser UA.

## Minting a scoped token

1. `POST /api/token/` with `{name, group, model_limits_enabled, model_limits, unlimited_quota, expired_time:-1, user_id}`. **It returns success with an empty key** — the key never comes back over the API. Fetch it from the DB: `SELECT key FROM tokens WHERE name='<name>'` and prefix `sk-`.
2. Set `user_id` to a user whose group setup admits the token's group — a token minted under the root session but left with a mismatched owner 403s with `无权访问 <group> 分组`. Fleet tokens live under user 5 (delo-relay) with group `aai-personal`.
3. `model_limits` must list the auto family AND each free route explicitly — `automaticai/auto` grants the auto family, but `automaticai/free` alone does NOT grant the individual free routes; copy a working fleet token's limits when in doubt.
4. **Redis caches token rows.** After any DB edit to a token (limits, user_id, group), run `docker exec newapi-redis redis-cli FLUSHALL` (or restart `new-api`) before re-testing — the old row serves 403s long after the edit.

## Adding a provider channel

1. Insert the `channels` row directly (API create is validation-quirky): type 58 for custom OAuth-style upstreams, `base_url` without `/v1`, `models` as comma-separated `automaticai/<account>/<model>` names, `model_mapping` JSON route→upstream-model, `"group"` quoted (reserved word), `auto_ban` is bigint (use 1 not true).
2. Restart `new-api` — channel rows are cached too.
3. **The catalog gate is the real gate.** `Normalize()` validates EVERY `automaticai/*` model name against the catalog embedded in the Go binary (generated from `ops/routes.json` in `~/code/client-portal/gateway` by `brand/apply-gateway.py`). A DB channel with no routes.json entry serves 400 `unknown AutomaticAI model` forever. Exposing models fleet-wide = routes.json edit → apply-gateway.py → Go rebuild → deploy (`bash ops/compose.sh up -d new-api`).
4. Deploy env changes flow through `.env.op` (op:// refs) with a gitignored `.env.ingress`-style overlay for raw keys the vault can't take; `ops/compose.sh` chains both env files (multiple `op run --env-file` args are legal).

## Classifier options (hot)

`automaticai_auto.classifier_url` / `.classifier_model` are hot-reloaded NewAPI options — `PUT /api/option/` takes effect immediately, no restart. The classifier's API key comes from the `AAI_JEV_API_KEY` env var, which DOES need a container recreate. Classifier path (Jev/SystemOne) is governed by the typesafe-ai skill.

## Verifying

- Live call through the new token/route: `POST /v1/chat/completions` with `model: automaticai/auto/fast` etc.
- Ledger proof of who served: `SELECT model_name, to_timestamp(created_at) FROM logs WHERE token_name='<n>' ORDER BY created_at DESC LIMIT 5`.
- Auto-router internals: `GET /v1/automaticai/auto/state` (needs an allowed-group auto-scoped token).
