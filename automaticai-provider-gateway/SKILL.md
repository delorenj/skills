---
name: automaticai-provider-gateway
description: "Operate AutomaticAI at api.automaticai.io: account-specific model
  routes, consumer tokens, dedicated OAuth grants, normalized effort, client
  configuration, NewAPI deployment to its AWS Lightsail VM, outages, backups,
  alerts and cost, and authenticated acceptance. Use when configuring,
  deploying, debugging or restoring this gateway; consumer discovery and
  permanent direct-provider remediation belong to
  automaticai-provider-gateway-lazy-migration-strategy."
---

# AutomaticAI provider gateway

Operate the user's unified inference provider at `api.automaticai.io`. Preserve
the requested model, account and billing path while exposing OpenAI Chat
Completions and Responses, plus native Claude Messages for catalog routes that
support it.

## Start with current source

The canonical source is `~/code/client-portal/gateway`; the former
`~/docker/stacks/ai/newapi` is only a compatibility symlink. Read `gateway/AGENTS.md`
and `gateway/README.md`. `SOURCE.json` pins upstream; `brand/prepare-source.sh`
exports it from the external cache and applies the tracked fork. Do not use
`~/code/newapi` as build authority: its checkout can be an older release. Then read:

- `ops/routes.json`: authoritative route, account, upstream and credential map.
- `ops/UNIFIED-PROVIDER.md`: operational commands and checked-in client examples.
- `ops/ACCEPTANCE-unified-provider.md`: dated live evidence and remaining gates.
- `ops/ROADMAP.md`: provider hardening before the future adaptive router.

## Where it runs

The gateway runs on the AWS Lightsail VM `aai-gateway`, not on big-chungus
(`gateway/TARGET` says `cloud`). Deploy only through `./ops/compose.sh`, read
the VM with `docker --context aai-cloud ...` or `ssh aai-gateway`, and never
`docker context use`. Health, recovery, alerts, cost and backups are in
[hosting](references/hosting.md) and the runbook `gateway/ops/CLOUD.md`.

Read current files and runtime state before relying on this skill's snapshot.
Catalog membership, discovery, account connection and proven live traffic are
separate facts. A known route can be disconnected; a displayed model is not
proof of a successful request.

## Contract

1. Use `https://api.automaticai.io/v1` for OpenAI clients. Use the origin
   `https://api.automaticai.io` for Claude Code's `ANTHROPIC_BASE_URL`.
2. Explicit routes use canonical `automaticai/<account>/<model>` names; opt-in
   adaptive routes use the `automaticai/auto` family described below. `aai/` is an
   equivalent request prefix with identical permissions; discovery is canonical.
3. For explicit routes, choose the intended account: personal Claude,
   Intelliforia team, personal Kimi, personal OpenAI, or deliberately paid
   OpenRouter. Never recover from a failed explicit route by silently switching
   accounts or billing paths. User-authorized auto routes may choose within their
   token-permitted subscription/free pool, never a hidden paid fallback.
4. Mint a scoped gateway token per consumer and keep it in 1Password. Resolve
   references into process environment; never write or print a resolved key.
5. Normalize effort to `medium`, `high`, `xhigh`, `max`. Claude and Astra/Sol
   default to `xhigh`. Enable Claude `ultracode` in its client harness; do not send
   it as a gateway API field. Astra/Sol have no ultra setting.
6. Give each dedicated OAuth grant exactly one refresh owner. The gateway
   renewal service owns its dedicated grants; interactive CLI grants remain
   separate. NewAPI gets access credentials only.
7. Use task-scoped authenticated traffic and ledger evidence after a change.
   Existing relevant usage, including the user's working session, can satisfy
   that evidence; do not keep generating proof after the user says it works or
   asks to stop. Public status alone does not prove inference or billing.

See [route and effort contract](references/route-contract.md) for all initial
routes, identities, native mappings and unavailable-route behavior.

## Usage and allowance observability

Settled requests are exported as `bloodbank.evt.llm.usage.recorded`; provider
allowance windows as `bloodbank.evt.llm.allowance.observed`. Their authoritative
schemas live in the Bloodbank repo. Subscription gauges use provider-reported
utilization and reset metadata; gateway token totals split the used portion and
expose unexplained use as outside-gateway usage. `input_tokens` is normalized as
uncached input plus cache reads plus cache writes.

The NewAPI ledger remains the request-level source. Prefer a read-only,
durable-cursor exporter over synchronous publication from the relay hot path.
Use deterministic event IDs and ordering keys so replay and backfill are
idempotent. Grafana and Holocene consume Prometheus/Candystore projections;
Grafana is not an intermediary API. Never place prompts, prompt hashes, proof
markers or credentials in these events. Load `$monitoring-stack` for store,
cardinality and dashboard decisions.

## Workflow

### Inspect and choose

Resolve the real consumer's endpoint, API style, model, account, token scope,
helper models and fallback chain. Read `/v1/models` using that consumer's token
without printing it. For OAuth accounts, run from
`~/code/client-portal/gateway`:

```sh
python3 ops/oauth-connections.py status all
python3 ops/reconcile-routes.py --dry-run
```

Reconciliation's dry-run inspects planned managed-account changes. It is not
permission to mutate unrelated clients or evidence that a relay works.

If the task discovers direct agent-provider inference, invoke
`$automaticai-provider-gateway-lazy-migration-strategy` immediately. That skill
owns detection, delegated remediation, durable consumer-source fixes and landing;
this skill owns the gateway operations used by the remediation worker.

### Connect, provision or repair

Use [operations](references/operations.md) for the exact OAuth, token, route
reconciliation and deployment procedures. Preview supported changes before
applying them; read their management state back afterward. Preserve legacy
channels, other consumers and unrelated Git work.

Use [client integration](references/client-integration.md) for endpoint shape,
credential precedence, Chat/Responses history, Claude helper models and Codex
provider configuration. The checked-in deployment examples are the command owner;
adapt their token reference and account rather than copying credentials.

### Accept the change

Use [acceptance and diagnosis](references/acceptance.md) and
[prompt/session receipt proof](references/prompt-proof.md) for the evidence
needed by the task. A separate probe cannot prove the executing parent's
routing. Fresh synthetic proof is unnecessary when existing evidence settles:

- The installed process reads the intended source and gateway token.
- Its selected route succeeds through the API style it actually uses.
- Streaming terminates; its tool history works when tools are part of the job.
- Usage records the intended account, native model, requested/effective effort
  and subscription or metered charge.
- A repeated dry-run or configuration regeneration does not undo the change.

Choose a bounded verification budget before running probes: reproduce the failing
wire shape, test the repair offline, then one affected-route/client continuation
and relevant ledger readback if fresh live evidence is needed. Broad account or
fleet certification is separate from a narrow deployment fix. Consult
[acceptance](references/acceptance.md) for when to run a broader harness and when
to stop. Save secret-free evidence in runtime storage, never in Git.

### Per-model optimization

Each upstream provider has limits, caching semantics, and streaming quirks that
the branded overlay and client configs must honor. Check the aspects affected by
the task; ordinary working traffic is not a claim of full integration acceptance:

- **Claude prompt caching**: look for `cache_creation_tokens` then `cache_tokens`
  on suitable existing ledger rows. The branded overlay injects `cache_control`
  breakpoints on the last system block and penultimate message. A tiny prompt can
  legitimately show zero cache tokens; do not diagnose failure from that alone.
- **Claude max_tokens**: NewAPI's `claude.default_max_tokens` option controls
  the cap when clients omit it. With thinking at 80% budget, 8192 leaves only
  ~1.6k output tokens. Read the live option map; historical defaults are not proof
  of the current cap.
- **Cloudflare idle timeout**: the current deployment investigation identifies
  an approximately 125 s edge read/idle timeout on quiet Claude Responses streams,
  not a universal 100 s time-to-first-byte failure. Prompt caching reduces cold
  latency; `automaticai_stream.heartbeat_seconds` (default 15, clamped to 25)
  keeps response-phase SSE traffic alive once upstream has answered. Never enable
  `general_setting.ping_interval_enabled`: its pre-header ping commits HTTP 200
  before the upstream status is known and hides provider errors. Use the current
  `AGENTS.md` and `ops/UNIFIED-PROVIDER.md` for deployment-specific evidence.
- **Codex stream retries**: preserve same-model retries (`stream_max_retries ≥ 5`)
  and the current documented `stream_idle_timeout_ms=1200000`. SSE comment
  heartbeats do not reset Codex's event-level timer. Zero retries turns any
  transient SSE drop into a permanent cutoff.
- **Responses tool mapping**: upstream `RequestFunctionDeclarations` only
  accepts `type=function`. The branded patch also accepts `type=custom` with a
  default string-input schema. `type=namespace` (MCP tools) still needs mapping.
- **Responses tool-result conversion**: content-array outputs need block-level
  translation (`input_text`/`output_text` to Claude `text`), not raw forwarding.
  Test result-only continuations and interrupted parallel batches; native Claude
  blocks and their citation/cache metadata must survive unchanged. See
  [protocol-history lessons](references/acceptance.md#protocol-history-lessons).
- **Effort-to-thinking budgets**: verify `xhigh` and `max` efforts actually
  reach the upstream thinking configuration. Check gateway logs for
  `automaticai_effective_effort` matching the requested value.

When adding a new model or provider, read its official API docs for max output
tokens, prompt caching syntax, recommended effort mapping, and SSE event shapes
before wiring the route. Then verify each of the above empirically.

### Land and report

Follow the session's version-control authorization in each owning repository;
changing or deploying a file does not itself authorize committing or pushing it.
Preserve unrelated work and report source publication state separately from the
running image. Keep runtime evidence out of Git; update existing runbooks when
requested rather than creating or copying extra documents by default.

Report what now works, the route/account used, verification and any remaining
concrete blocker. Do not describe Astra/Sol, renewal or the whole provider fleet
as complete until their live gates pass.

## Opt-in adaptive routing

`automaticai/auto` is live for allowed personal tokens. Read the current gateway
`ops/AUTO-ROUTER.md` for policy, acceptance and client recipes; do not use the old
`aai-auto` spelling. Explicit account/model routes remain the escape hatch.
Auto is a deliberate opt-in exception to explicit account selection: it chooses
only token-permitted subscription routes, then proven OpenRouter `:free` routes;
there is no paid fallback. A turn and its tool loop stay pinned. State and
feedback are available through `tokies auto` and `tokies auto feedback`.

For Claude Code, `/model automaticai/auto` changes one session. The durable
launcher recipe uses main/Opus `automaticai/auto/orchestrator`, Sonnet and
`CLAUDE_CODE_SUBAGENT_MODEL` `automaticai/auto/subagent`, Haiku
`automaticai/auto/fast`, and `CLAUDE_CODE_MAX_CONTEXT_TOKENS=800000`. Native
subagent markers still override an inherited orchestrator slot. Never map the
Fable advisor to auto. Preserve the existing gateway token and credential owner.
Before enabling auto for another consumer, verify its discovery parser accepts
rows with `automaticai.auto = true`; do not infer client readiness from successful
wire API probes or broaden unrelated consumers' scopes.

### Auto router for Hermes fleet agents

Hermes profiles inherit the auto routes through the fleet base config
(`~/.hermes/config.yaml`). To wire a new consumer:

1. **Mint a scoped token**: `python3 ops/gateway-tokens.py mint <consumer> --auto`
   from `~/code/client-portal/gateway`. The `--auto` flag adds the four auto
   names plus the policy's free routes. Verify with `gateway-tokens.py status <consumer>`.
2. **Add auto routes to `providers.<name>.models`** in the consumer's Hermes
   config so `/model` and delegation can resolve them. Use `hermes config set`
   (never hand-edit; the tool refuses direct writes to `config.yaml`).
3. **Add `model.aliases`** for ergonomic `/model auto`, `/model auto-orch`,
   `/model auto-sub`, `/model auto-fast` shortcuts.
4. **Point `secrets.onepassword.env.<KEY_ENV>`** at the minted consumer token's
   `op://` reference. Profiles override `AUTOMATICAI_GATEWAY_KEY` in their
   `config.delta.yaml` for per-member tracking.
5. **Set `delegation.model: automaticai/auto/subagent`** so spawned workers
   route adaptively instead of pinning a single model.
6. **Verify with live probes**: `curl -H "Authorization: Bearer $key"` against
   `/v1/models` (auto rows carry `automaticai.auto: true`) and
   `/v1/chat/completions` with `model: automaticai/auto/fast` (should route to
   a free tier model) and `model: automaticai/auto/orchestrator` (should route
   to a frontier subscription model). Check the response `model` field to confirm
   the router's target.

The auto router classifies each request (role, context, tools) and picks the
best available model. Delegated workers on `auto/subagent` start at the strong
tier and ratchet up/down based on success/failure. Fast aux calls (titles,
summaries) route to `auto/fast` (free tier first). Orchestrator calls route to
`auto/orchestrator` (frontier tier). The router never falls back to metered
billing; exhausted subscription pools fall through to free routes.
