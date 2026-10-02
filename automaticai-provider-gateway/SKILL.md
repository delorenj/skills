---
name: automaticai-provider-gateway
description: "Operate AutomaticAI at api.automaticai.io: account-specific model
  routes, consumer tokens, dedicated OAuth grants, normalized effort, client
  configuration, NewAPI deployment, and authenticated acceptance. Use when
  configuring or debugging this gateway; consumer discovery and permanent
  direct-provider remediation belong to
  automaticai-provider-gateway-lazy-migration-strategy."
---

# AutomaticAI provider gateway

Operate the user's unified inference provider at `api.automaticai.io`. Preserve
the requested model, account and billing path while exposing OpenAI Chat
Completions and Responses, plus native Claude Messages for the two Claude
subscription routes.

## Start with current source

The deployment source is `~/docker/stacks/ai/newapi` in the Docker repository;
the pristine upstream checkout is `~/code/newapi`. Read the deployment's
`AGENTS.md`, then:

- `ops/routes.json`: authoritative route, account, upstream and credential map.
- `ops/UNIFIED-PROVIDER.md`: operational commands and checked-in client examples.
- `ops/ACCEPTANCE-unified-provider.md`: dated live evidence and remaining gates.
- `ops/ROADMAP.md`: provider hardening before the future adaptive router.

Read current files and runtime state before relying on this skill's snapshot.
Catalog membership, discovery, account connection and proven live traffic are
separate facts. A known route can be disconnected; a displayed model is not
proof of a successful request.

## Contract

1. Use `https://api.automaticai.io/v1` for OpenAI clients. Use the origin
   `https://api.automaticai.io` for Claude Code's `ANTHROPIC_BASE_URL`.
2. Use canonical `automaticai/<account>/<model>` names. `aai/` is an equivalent
   request prefix with identical permissions; discovery publishes canonical names.
3. Choose the intended account explicitly: personal Claude, Intelliforia team,
   personal Kimi, personal OpenAI, or deliberately paid OpenRouter. Never recover
   from a disconnected, expired, rate-limited or unauthorized route by switching
   accounts or sending subscription traffic to a paid provider.
4. Mint a scoped gateway token per consumer and keep it in 1Password. Resolve
   references into process environment; never write or print a resolved key.
5. Normalize effort to `medium`, `high`, `xhigh`, `max`. Claude and Astra/Sol
   default to `xhigh`. Enable Claude `ultracode` in its client harness; do not send
   it as a gateway API field. Astra/Sol have no ultra setting.
6. Give each dedicated OAuth grant exactly one refresh owner. The gateway
   renewal service owns its dedicated grants; interactive CLI grants remain
   separate. NewAPI gets access credentials only.
7. Prove the actual authenticated request, account and ledger after a change.
   Public status, a successful build, an enabled timer and a green webhook are
   insufficient acceptance evidence.

See [route and effort contract](references/route-contract.md) for all initial
routes, identities, native mappings and unavailable-route behavior.

## Workflow

### Inspect and choose

Resolve the real consumer's endpoint, API style, model, account, token scope,
helper models and fallback chain. Read `/v1/models` using that consumer's token
without printing it. For OAuth accounts, use:

```sh
cd ~/docker/stacks/ai/newapi
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
[prompt/session receipt proof](references/prompt-proof.md). A successful separate
probe cannot prove the executing parent used the gateway. At minimum prove:

- The installed process reads the intended source and gateway token.
- Its selected route succeeds through the API style it actually uses.
- Streaming terminates; its tool history works when tools are part of the job.
- Usage records the intended account, native model, requested/effective effort
  and subscription or metered charge.
- A repeated dry-run or configuration regeneration does not undo the change.

Run the broad gateway harness when modifying relay behavior or onboarding an
account; use the affected route and real consumer for a configuration-only change.
Save secret-free evidence in runtime storage, never in Git.

### Per-model optimization

Each upstream provider has official limits, caching semantics, and streaming
quirks that the branded overlay and client configs must honor. Never treat
"traffic flows" as integration-complete without checking these:

- **Claude prompt caching**: verify `cache_creation_tokens` then `cache_tokens`
  are non-zero in gateway logs. The branded overlay injects `cache_control`
  breakpoints on the last system block and penultimate message. If both are
  zero, caching is silently broken and 140k-token requests will take 86+ s.
- **Claude max_tokens**: NewAPI's `claude.default_max_tokens` option controls
  the cap when clients omit it. With thinking at 80% budget, 8192 leaves only
  ~1.6k output tokens. Current setting: `{"default":32768,"claude-opus-5-5":65536}`.
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
- **Effort-to-thinking budgets**: verify `xhigh` and `max` efforts actually
  reach the upstream thinking configuration. Check gateway logs for
  `automaticai_effective_effort` matching the requested value.

When adding a new model or provider, read its official API docs for max output
tokens, prompt caching syntax, recommended effort mapping, and SSE event shapes
before wiring the route. Then verify each of the above empirically.

### Land and report

Commit and push the task's source changes into each owning repository's main
branch, including submodule pins when changed. Preserve unrelated work. Run
`git unpushed`, resolve task-created findings, and distinguish unrelated findings
from this task. Final readable documents also belong in the AutomaticAI vault at
`~/code/DeLoDocs/Projects/AutomaticAI/`; verify copied bytes.

Report what now works, the route/account used, verification and any remaining
concrete blocker. Do not describe Astra/Sol, renewal or the whole provider fleet
as complete until their live gates pass.

## Future routing epic

The FireRouter-inspired `aai-auto` route is future work. Harden and accept the
explicit upstream models and OAuth connections first. Initial adaptive routing
is opt-in for personal agents, uses proven routes, preserves a selected account
and model through a turn's tool/cache/context sequence, exposes its decision and
settlement, and retains explicit-route escape hatches. Never migrate traffic to
`aai-auto` before it exists and passes that gate.
