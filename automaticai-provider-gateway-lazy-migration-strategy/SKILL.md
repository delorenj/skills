---
name: automaticai-provider-gateway-lazy-migration-strategy
description: Apply the AutomaticAI routing policy whenever agent or
  agent-service LLM inference bypasses api.automaticai.io, including CLI
  defaults, helper models, profiles, hooks, SDKs, workers, and fallback chains.
  Immediately fork a remediation worker for each distinct configuration owner,
  fix the durable source, verify gateway runtime traffic, and land the change.
  Gateway account, OAuth, token, and relay operations belong to
  automaticai-provider-gateway.
---

# AutomaticAI lazy migration strategy

**Policy: all agent and agent-service LLM inference goes through AutomaticAI.**
When an active inference path bypasses the custom provider, immediately fork a
remediation worker and fix the source that controls that path. Discover and
migrate consumers as work encounters them; do not schedule a fleet-wide sweep
as a prerequisite to fixing the first finding.

This skill defines the consumer migration policy. Use
`$automaticai-provider-gateway` for account availability, model mapping, token
provisioning, OAuth, relay changes and gateway acceptance.

## Apply on encounter

Run a focused routing check when starting work on an agent consumer or changing
its model, SDK, launcher, profile, environment, fallback, template, deployment or
provider error handling. Include primary, helper, planner, critic, summarizer,
background memory and spawned-worker paths. Hooks and services making LLM calls
are consumers too.

Check effective configuration and active source ownership, rather than grepping
every vendor name on disk. Historical documents, tests, unused examples,
provider OAuth/control planes and the gateway's own upstream adaptors are not
direct-agent inference findings. Unsupported endpoints are tracked capability
blockers, not automatically valid migrations. Read
[detection and ownership](references/detection-and-ownership.md).

Read [session-start verification](references/session-start-verification.md)
for the installed Codex hook and deterministic actual-request receipt check.
Startup detects configured bypass before inference; post-request usage supplies
proof. Missing usage alone does not authorize declaring a bypass.

## Immediately delegate a real finding

1. Capture secret-free evidence: consumer, active API/endpoint/model, account
   intent, source owner, runtime entrypoint and each direct helper/fallback.
   A library's implicit native-provider default is a finding even if no vendor
   URL is written in the file.
2. Fork a real worker using the current harness's subagent facility. Give it
   explicit repository/file ownership and the
   [worker task template](assets/remediation-task.md). State that it is not alone
   and must preserve others' edits. Pass credential references, never raw keys.
3. Deduplicate by canonical configuration owner and consumer/account. Join or
   message an existing remediation worker instead of spawning one per call,
   generated file, failed retry or child agent. A remediation worker handles
   its assigned migration inline; it must not recursively fork itself for its
   own inherited bootstrap connection.
4. Continue independent parent work while the worker fixes the consumer. If the
   current task depends on that traffic, wait for its verified cutover before
   making dependent calls. Review its result and close the finding only when
   the acceptance checklist below is satisfied.

“Fork” means start a delegated agent now, not leave a Git branch or create a
ticket for later. If this harness genuinely has no delegation mechanism, perform
the same scoped remediation inline and record that limitation. Do not pretend a
fork happened. This policy authorizes migration work when applied; it does not
override a current user instruction to audit only, pause or preserve a route.

Do not kill or reconfigure the executing parent to replace its already-open
model connection. Fix its durable next-launch configuration, test a fresh
invocation and report when cutover takes effect. Avoid migration recursion and
self-restart loops. Forking does not make a disconnected account available.

## The permanent fix

The worker must:

1. Resolve the selected account and exact supported model from the live gateway
   catalog. Preserve explicit effort, capabilities and billing intent.
2. Mint/adopt a named consumer gateway token, scoped to primary and required
   helper routes. Persist only `op://` references and inject secrets in memory.
3. Change the authoritative provider configuration, template or launcher. For
   generated profiles, update the generator input and regenerate; for installed
   services, update their tracked unit/credential launcher and install it.
4. Remove direct-provider precedence from **that consumer's inference launch**.
   Configure helpers, fallback chains, retries and spawned-worker defaults to
   the intended gateway routes. Keep upstream credentials with their dedicated
   gateway OAuth/control-plane owners.
5. Regenerate/sync and restart or relaunch only the affected runtime. Verify a
   real request, then regenerate again to prove persistence and idempotence.
6. Add the smallest meaningful source regression check that prevents the
   discovered direct path from returning. Commit and push into the owning main
   branch, including templates, sibling owners and changed submodule pins.

Use [consumer recipes and cutover](references/consumer-recipes.md) for the
specific source/runtime seams. Shell exports, editing one generated profile,
changing only the main model, and passing only a mock URL assertion do not close
a permanent migration.

## Preserve account and capability intent

- Personal Claude stays personal; tri-devs/Intelliforia stays team. Bind Claude
  helper models to the selected subscription account.
- Paid OpenRouter stays an explicitly selected paid path. Never make it a hidden
  backup for a subscription failure or change existing paid intent implicitly.
- Personal Kimi uses the verified Coding-plan route and context requirement.
- Astra/Sol use the dedicated personal OpenAI grant, default `xhigh`, no ultra.
  If the grant is missing, prepare the source fix and keep live cutover pending;
  do not replace those models with Claude, Kimi or a platform API key.
- Unsupported models/features require adding and accepting a proper gateway
  route, or a concrete user decision. Do not invent a model alias or reclassify
  embeddings/reranking as Chat simply to remove a vendor hostname.

Current `aai/` aliases are valid. The adaptive `aai-auto` router is future work
after upstream/OAuth hardening; it is not an available migration target.

## Completion gate

Close a finding only when all applicable facts are proved:

- The source owner contains the correct gateway provider/URL, explicit route,
  normalized effort and token reference; no raw credential is written.
- Primary, helper, worker and fallback inference paths use the gateway; provider
  OAuth/control-plane traffic remains with its correct owner.
- The actual installed consumer succeeds with its intended API style, streaming
  and tool features; gateway usage proves account, native model and billing.
- Source regeneration/restart preserves the result, and its focused regression
  check catches reintroduction of the direct path.
- Task changes are committed, pushed and integrated into every owning main
  branch; `git unpushed` has no task-created findings. Report unrelated WIP
  separately without changing it.

A missing grant, required human passkey, unsupported capability or unreachable
runtime remains a named open blocker with an owner and exact next step. Complete
independent preparation, keep the handoff durable in the existing project
tracker/source, and report the boundary. Never mark a blocked cutover as migrated
or broaden spending/account selection to manufacture success.

Report the consumer, source owner, chosen route/account, runtime evidence,
commits and remaining blocker. Save readable final migration documents in their
source workspace and `~/code/DeLoDocs/Projects/AutomaticAI/`, verifying parity.

## Examples

- Encounter a Hermes helper calling OpenRouter directly: fork one worker for
  its role/template owner, select the gateway's explicit paid route only if that
  paid intent is established, patch and regenerate, then prove the helper request.
- Encounter a team Claude wrapper: fork immediately; bind main and all helpers
  to `automaticai/intelliforia/claude-opus-5.5`, remove launch auth conflicts and
  verify native Claude traffic plus the team ledger.
- Encounter Codex using personal OAuth while gateway Astra is disconnected:
  fork immediately for durable preparation, retain the sign-in blocker, and
  await user passkey verification before the actual gateway cutover.
- Encounter the gateway's `oauth-connections.py` contacting a provider token
  endpoint: that is required control-plane traffic; do not migrate it to itself.
