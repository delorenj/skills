# Consumer recipes and durable cutover

Gateway operational detail belongs to `$automaticai-provider-gateway`, especially
its route contract, client integration and acceptance references. These recipes
identify the consumer owner to change. Read the installed framework's current
schema and repository instructions before editing; do not assume a generic key
works in every CLI.

## Resolve intent before rewriting

Record the active model, account, API style, explicit effort, context requirement,
tools and billing expectation. Use existing route/profile/credential metadata to
resolve intent. A bare `claude-opus-5.5` does not establish personal versus team;
ask for the missing account preference if current ownership cannot establish it.
Prepare all independent work while that decision is pending.

Mapping examples from the initial catalog:

| Existing intent | Gateway target |
| --- | --- |
| Personal Claude subscription | `automaticai/personal/claude-opus-5.5` |
| Intelliforia / tri-devs team Claude | `automaticai/intelliforia/claude-opus-5.5` |
| Deliberately paid OpenRouter Claude | `automaticai/openrouter/claude-opus-5.5` |
| Personal Kimi K3, 1M context | `automaticai/personal/kimi-k3` |
| Personal Kimi K3 256K | `automaticai/personal/kimi-k3s` |
| Personal Kimi Coding legacy alias | `automaticai/personal/kimi-2.8`, with native alias/version caveat |
| Personal OpenAI Astra / Sol | Their corresponding `automaticai/personal/astra` / `sol`, only after grant acceptance |

Do not reduce model quality, change a model family, collapse team into personal,
change context capacity or change billing merely to make the route available.
An unavailable exact mapping remains a blocker until added and accepted, or
until the user explicitly chooses another supported route.

## SDKs, wrappers and worker factories

Update the maintained client constructor/config to
`https://api.automaticai.io/v1`, a canonical permitted model and a named consumer
token reference. Inject the resolved token in process environment. Ensure both
Chat and Responses clients use the same custom provider where both are used.

Inspect separate constructors and factory defaults for planner, helper, critic,
summarizer, retry/fallback and spawned agents. Pass the gateway provider config
through worker creation instead of letting a child fall back to native OAuth.
Remove direct-provider credential precedence from that launch scope. Preserve
provider OAuth/control-plane ownership elsewhere.

Full tool history and call IDs must survive protocol conversion. For Responses
consumers relying on `previous_response_id`, assess and implement complete
stateless history where required; do not silently drop history to make a basic
request pass. Probe actual tool/stream paths after the source change.

## Claude Code and team wrappers

Modify the wrapper/profile source used by the installed command. Resolve the
named gateway token into `ANTHROPIC_AUTH_TOKEN` and set
`ANTHROPIC_BASE_URL=https://api.automaticai.io`. Clear inherited direct OAuth/API
auth precedence in that wrapper, preserving interactive grants outside its scope.

Set the chosen account-specific route for the main model and **all** default
Opus/Sonnet/Haiku helper models. Enable `xhigh` and the installed Claude harness's
supported ultracode/workflow settings using the checked-in gateway example.
Keep `ultracode` out of generic API bodies. Verify native `/v1/messages`
streaming with the real installed Claude command and read the same account's
ledger. The gateway owns required OAuth preamble/beta adaptation.

For tri-devs, every helper must select Intelliforia. A successful personal
request is not acceptance for a team wrapper. Client-estimated API price is not
the gateway's actual subscription quota charge.

## Codex and personal OpenAI

Use the canonical owner `~/.agents/providers/automaticai/` and its idempotent
source installer/launcher. Codex 0.159.2 supports command-backed 1Password auth;
this owner avoids mixing it with native-login auth or env-key/static-bearer auth.
Select the gateway Responses provider and exact catalog model, preserving an
explicit normalized effort. Astra/Sol default to xhigh, with no ultra. Native
gpt-6.1-sol maps to automaticai/personal/sol-6.1; the older sol route is gpt-6-sol.
Read [session-start verification](session-start-verification.md) for native
hook startup, per-prompt challenges, actual session receipts and recursion guards.

If OpenAI is disconnected, commit/push any usable preparation without activating
a broken live default. Finish the dedicated user sign-in with the gateway
operations runbook, reconcile, and complete native-client/live acceptance before
cutover. An unrelated interactive login or platform API key does not prove this
subscription route. Record the exact activation step and owner in the open
handoff so a restart or future session does not mistake preparation for completion.

## Hermes / Flume profiles and generated agents

Use `$agent-fleet-operations` to establish the current template, role delta,
profile renderer, credential launcher and service unit. Treat generated runtime
profiles as projections. Change the owning role/template provider configuration
and regeneration mechanism, then regenerate and install using its supported
commands. Do not patch only a file under a live `~/.hermes/profiles` directory.

Include background models and the profile's spawned-worker defaults. If a shared
template controls many agents, coordinate one owner task and preserve per-agent
account overrides. Inspect what the actual launcher injects, not merely the
renderer output. Restart only the affected consumer when ready and test through
its real gateway/invocation path. A source commit without installed-process
proof remains an incomplete migration.

Generic multi-CLI fan-out is owned by `$agent-config-fanout`; its source inputs,
mapping decisions and repeat-check must retain unrelated dialect settings.
Reference-only skill activation is owned by `$skillex-skill-registry`.

## Compose, service inference, hooks and automation

Update the service's tracked provider/client config and `.env.op` reference.
For a user service, update its tracked unit or credential launcher; environment
files must contain references, never raw keys. Reinstall/reload the affected unit
or recreate only the affected Compose service, keeping unrelated services alive.

For jobs/hooks, exercise the actual operation that makes the LLM call. A Hindsight
read-health check cannot prove its retain/summarization inference path. A job
schema test cannot prove its deployed worker uses the gateway. For n8n, prove
deployed node/provider parity after publishing via the owning workflow mechanism.
Do not send unrelated Slack/email messages as migration probes.

Inspect local proxy wrappers before removing them. They may be retained if their
LLM egress is AutomaticAI and the consumer account is preserved. Keep native
transport, tool and OAuth-control behavior separate from inference routing.

## Cutover sequence

1. **Baseline:** note repo branch/upstream/WIP, source owner, installed runtime
   and secret-free routing evidence. Do not reset or stage unrelated work.
2. **Availability:** inspect catalog permissions and dedicated account status.
   Verify the exact route/capability before changing a live default.
3. **Token:** mint/adopt the named scoped gateway token; save only its reference
   to the maintained source and resolve in the launcher.
4. **Source:** update the authoritative provider and every affected role/helper
   path. Remove direct fallback and auth precedence in that consumer scope.
5. **Projection:** regenerate/sync/install with the owning mechanism. Inspect
   actual runtime fields and variable presence without exposing credentials.
6. **Probe:** make a fresh installed-consumer request, including streaming/tool
   features used by its real workload. Inspect account/model/effort/charge in
   gateway usage. Do not settle for an HTTP status or mock URL assertion.
7. **Persistence:** rerun generation/check and restart/relaunch as applicable.
   It must preserve the result with no managed drift. Run the focused regression
   check on the source that previously introduced the direct path.
8. **Land:** commit explicit task paths, push/integrate main in every owning repo,
   update parent submodule pins, and run `git unpushed`. Preserve unrelated WIP.
9. **Close:** report the accepted consumer/account or its concrete remaining
   blocker. A pending passkey/capability handoff remains open.

## Regression checks

Choose a check tied to the actual failure seam: factory test that children
inherit provider configuration; renderer test for main/helper account parity;
launcher test that gateway auth wins; or a configuration guard checking owned
active model/endpoint fields. Keep it secret-free and run it in the source's
normal validation path. A hard-coded assertion mirroring a copied URL without
exercising that seam is insufficient.

Do not scan the whole home directory each turn or create an independent second
configuration registry. The lazy rule triggers when active work encounters a
bypass; the permanent owner fix prevents that same path returning.
