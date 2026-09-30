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
