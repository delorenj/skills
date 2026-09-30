# Detect a bypass and identify its owner

## What counts

The policy covers LLM inference made by interactive agents, their spawned
workers, long-running gateways, automation jobs, memory/summarization hooks,
evaluators and service-side agent SDKs. Inspect each role with a distinct model
selector. A migrated primary does not excuse a direct helper or retry path.

A compliant path is either a direct consumer call to AutomaticAI or an
intentional local wrapper whose final inference hop is demonstrably AutomaticAI.
The authenticated gateway request must still retain the exact intended account,
model and token scope. A localhost, LiteLLM or OpenAI-compatible URL alone is
insufficient evidence: follow that wrapper's routing until the inference egress
is known.

A bypass includes:

- Explicit provider API endpoints (Anthropic, OpenAI platform/subscription,
  Kimi/Moonshot, OpenRouter, Gemini or Copilot) used for agent inference.
- A native provider selected without a custom gateway base URL, including SDK
  defaults and CLI OAuth modes.
- Legacy proxy routing that sends to a vendor directly instead of AutomaticAI.
- Helper, summarizer, planner, spawned-worker or error-recovery models left on a
  direct provider while the primary uses AutomaticAI.
- Inherited credentials or wrapper precedence that override an apparently
  correct gateway configuration.

Do **not** classify these as agent-inference bypasses:

- AutomaticAI's upstream adaptors and egress: a proxy must reach its providers.
- Provider sign-in, refresh/token exchange, catalog discovery and key management
  performed by the gateway's dedicated control-plane owner.
- 1Password, MCP/service APIs, browser/voice transports or other non-inference calls.
- Historical docs, archived examples, mocks, inactive profiles and provider
  implementation code that the inspected runtime does not execute.

Unsupported inference endpoints such as embeddings/reranking still need a
supported gateway capability to satisfy a universal routing policy. Record the
gap and delegate capability assessment; they cannot be repaired by changing
their URL to a Chat endpoint. Models absent from the current catalog likewise
need a real route and upstream acceptance, not a guessed mapping.

## Focused inspection

1. Establish what is actually launched: command/wrapper, working directory,
   selected profile, executable version, service unit and generator/template.
2. Check existing `AGENTS.md`, `.project.json`, provider config, `.env.op`,
   launchers and role-specific model settings. Reach for CodeGraph first when
   the repo has an index; otherwise use targeted `rg` searches and reads.
3. Trace precedence: command arguments, per-profile settings, environment,
   wrapper exports, native OAuth/session state and framework defaults. Inspect
   secret **names and presence** without rendering values.
4. Follow helper/fallback/worker settings and local wrapper egress. Confirm that
   candidate files are active before flagging a vendor reference.
5. Resolve the maintained source and runtime projection. Delegate immediately
   once the active bypass is established; the worker can complete deeper tracing.

Example search within known text configuration owners:

```sh
rg -l -i \
  'api\.(openai|anthropic|moonshot)\.|openrouter\.ai|model_provider|base_url|reasoning_effort|ANTHROPIC_BASE_URL' \
  .agents ops config src
```

Use only paths that exist in the inspected repo. `-l` returns filenames, avoiding
accidental disclosure of credentials stored on matching lines. After identifying
a file, read relevant routing fields with redaction; never dump auth files,
`.env`, process environments or arbitrary secret-bearing YAML wholesale.
Filename searches are candidates, not a verdict. Absence of an explicit URL
does not exclude a native SDK default.

## Durable source ownership

| Runtime you encounter | Find and fix |
| --- | --- |
| Generated CLI config under `.claude/`, `.codex/`, `.kimi/` or equivalent | Committed `.agents/` provider input / fan-out source and its launcher |
| Hermes profile or PM service | Owning repo role config, template delta, credential launcher and tracked unit; use the current `agent-fleet-operations` contract |
| Wrapper installed in a user bin directory | Its maintained source repo and installation path, then install the source change |
| Compose service | Tracked Compose/config plus `.env.op` references, then recreate only the affected service |
| SDK/job/worker code | Client factory, role-model config and spawn defaults used by the actual process |
| n8n/remote deployed workflow | Workflow source/export and deploy mechanism plus the actual deployed node configuration |
| Native per-user configuration that is truly hand-maintained | Its established tracked owner; do not invent a competing generator or commit runtime/auth files |

If the generator is unknown, keep tracing until it is found. A hot edit to the
runtime projection can be a temporary diagnostic, but does not satisfy the
permanent fix. Use `agent-config-fanout` for shared dialect generation and
`skillex-skill-registry` only for skill selection/activation; this migration
skill does not become another fan-out writer.

## Fork and deduplicate

Use the harness's real worker API (`collaboration.spawn_agent` where available,
or the installed equivalent). Do not invent a tool name. Assign explicit
ownership and tell workers that they are not alone and must preserve others'
changes. The worker's task includes gateway verification and landing, not merely
diagnosis. Use [the task template](../assets/remediation-task.md).

Deduplication key: the canonical configuration owner (repository/common Git dir
plus maintained config path), consumer or profile identity, and intended
account. Related helpers generated by the same owner belong to the same task.
One template change affecting many projections needs one template owner and a
bounded rollout plan, not many agents racing over its files.

Check active workers/finding records. Join an existing task when it already owns
that key, adding new evidence or helper paths. Do not spawn recursively for each
tool call, failed provider request or child inheriting the old bootstrap settings.
The assigned remediation worker handles its own finding inline.

Use a task-specific source lock or current project coordination mechanism when
necessary. Do not add a new daemon, runtime database or global fleet scheduler
just to implement lazy migration. The policy is encounter → worker → permanent
source fix → actual runtime acceptance → main/push.

## Running agent and blocker boundaries

An already-running agent's backend may be fixed for that conversation. The
worker changes the source used by subsequent invocations and tests a fresh
process. It must not kill its parent, restart itself recursively, or claim the
current in-flight turn was rerouted. Clearly report the next-launch boundary.

If the intended account is disconnected, fork immediately for source preparation
and account assessment. Continue independent work and leave cutover pending.
User passkey verification, missing capabilities or unavailable runtimes require
a concrete handoff: consumer/owner, exact missing prerequisite, prepared change,
next command and acceptance needed. Keep it in the existing project tracker or
source document; do not close it as completed or leave an abandoned branch.

Honor explicit current-user instructions such as read-only audit or pausing a
migration. The policy does not grant permission to bypass provider protections,
enable paid fallback, publish private messages or mutate unrelated work.
