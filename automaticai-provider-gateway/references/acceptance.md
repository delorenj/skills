# Acceptance and diagnosis

Read current `ops/ACCEPTANCE-unified-provider.md` and the consumer's installed
state. Use a current scoped token; a previous short-lived acceptance token may
have expired. Do not print its resolved value or redirect it to a file.

## Bound the verification

Match proof to the requested change, not every capability the gateway exposes.
For a repair, default to one exact failing-payload reproduction, focused offline
regressions, and one affected-route continuation or existing real-client receipt.
Reuse evidence already collected in this session. The user's report that they
are actively using the route is relevant evidence, not an invitation to keep
spending their allowance on synthetic certification. If they say stop, stop
probes and reviewers; report what is deployed and any unverified scope briefly.

A full account matrix is appropriate for an explicitly requested onboarding or
fleet acceptance exercise. If broader checks uncover unrelated model behavior,
record it separately; do not turn a repaired deployment into an endless effort
to make every model produce the same synthetic answer. Do not keep replaying a
request after allowance exhaustion or a provider filter stop. Keep failures
visible without switching accounts or weakening assertions.

Before a long-stream probe, identify the regression it protects. One completed
quiet turn with the required data gap and bounded byte gaps is enough; do not
repeat a matrix merely because a cheaper or shorter turn completed too quickly.
A capped `response.incomplete` can show transport survival but is not completed
inference. Stop at the declared budget and report an inconclusive gate honestly.

## Choose the appropriate proof

For a consumer configuration change, use its selected account through its
actual installed CLI/SDK/service only when existing relevant traffic does not
already settle the question. Cover streaming and tool continuation when
that consumer uses them. Prove a spawned worker or helper path separately only
when its distinct configuration is part of the requested change.

For a requested broader relay/account acceptance run, use the live harness:

```sh
python3 ops/verify-unified-provider.py \
  --token-ref op://DeLoSecrets/yeurk5dpqkaarspvsn3cjtmkki/default \
  --output /tmp/aai-live-acceptance.json
```

Prefer a named acceptance token for repeated operations; substitute its reference
in that command. `--models` limits the probe to explicit canonical routes.
`--wait-ready` allows bounded discovery readiness after recreation. The report
contains only non-secret metadata. Keep it in runtime storage.

The harness covers both Chat and Responses, canonical/alias prefixes, terminal
streaming with usage, string and content-array tool outputs, interrupted parallel
histories, and result-only continuation with no fabricated final user turn. It
does not replace a feature-specific wire fixture. An existing native-client
receipt can avoid another synthetic native CLI run.

## Protocol-history lessons

- Trace the converter actually selected by the managed route. A fixed
  Responses-to-Chat path does not protect direct Responses-to-Claude conversion.
- Responses `function_call_output.output` can be a block array. Translate
  `input_text` and `output_text` to native Claude `text` inside `tool_result`;
  preserve whitespace, block order, call IDs and input immutability. String-only
  probes missed the October 6, 2026 `input_text` discriminator failure.
- Translate OpenAI-shaped media, but deep-preserve already-native Claude blocks
  (`text`, `image`, `document`, `search_result`, `browser_state`, `tool_reference`).
  Do not rebuild them with a reduced DTO that drops titles, context, citations,
  cache controls or native text/file/content sources. Media belongs inside its
  tool result, not stringified into the text tokenizer.
- Claude requires the complete tool-result batch in the next user message after
  assistant tool uses. Safe text-only instruction/commentary interleaving needs
  normalization; missing, duplicate or ambiguous results must fail, not be invented.
- Test history ending at the last tool output. Deferring progress text to the end
  can create an assistant prefill that Claude refuses. Preserve terminal progress
  on the existing assistant tool-call turn before the complete result group;
  leave explicit-final-user and Chat ordering unchanged. Do not make the fixture
  pass by appending a user prompt the real client never sends.
- Assert complete marshalled wire JSON through the public converter and bridge,
  not only helper outputs or a substring containing an ID. Cover array outputs,
  parallel batches, native metadata and no-final-user history offline first.

## Interpret probe outcomes

Treat HTTP status, terminal state, text compliance and ledger settlement as
separate dimensions. Responses JSON/SSE must finish as `completed`; a 200 with
`incomplete`/`content_filter` is not a converter-validation 400 and must not pass
just because its text happens to match. A completed answer with no visible text
also fails answer acceptance, without proving an account or credential defect.

Make deterministic prompts explicit: for `OK`, request two uppercase letters
without punctuation or quotes. The ambiguous `Reply exactly OK.` often returned
`OK.` on older models. Fix that fixture ambiguity, not the strict assertion.
Retain filter/empty-answer limitations rather than repeatedly rebuilding the
relay to chase provider output variation.

## Read back the ledger and control plane

Confirm all of these against actual usage, not the expected configuration:

- Canonical route, `automaticai_account`, native `upstream_model_name` and channel.
- `automaticai_requested_effort`, `automaticai_effective_effort`, whether effort
  defaulted, and recorded outgoing `reasoning_effort`.
- Subscription model ratio/quota zero, or selected metered rates with group ratio 1.
- Enabled role-1 consumer, intended group, unexpired key and permitted model set.
- Exact managed channel owner/mapping and current access credential synchronization.
- If deployed: installed image ID, health and public status version, plus real relay.

Transport success is insufficient: NewAPI management envelopes must also have
`success=true`. A successful `/api/status` checks in-memory settings; it cannot
prove database, Redis, quota, provider or billing behavior.

## Failure isolation and renewal

For account-onboarding or routing changes, check that bad/expired credentials,
rate limits, denied token scope and disconnected grants stay on the explicit
account. Verify another intended account remains healthy; no paid or team
substitution is allowed.

Controlled expiry tests must preserve the real vault grant, restore the correct
managed state and re-probe afterward. A controlled snapshot proves gateway expiry
handling, not that a real provider session naturally expired during the test.
Do not inject invalid credentials or recreate a service during an ordinary
consumer-only migration when existing account-isolation acceptance suffices.

Force gateway-owned renewal without an interactive CLI sharing the grant, then
probe. Stop any CLI that shares it; never import mutable CLI auth as a durable
gateway session. After
container recreation, verify access-only credential synchronization and the
oneshot's exit status. A partially successful all-account renewal remains
partially successful until every required account is connected.

## Known diagnosis traps

| Symptom | Inspect before changing anything |
| --- | --- |
| Unknown alias / 400 | Current catalog spelling, conflicting effort fields, generic `ultracode`, actual protocol |
| 401 / 403 | Consumer-token expiry/scope, credential precedence, selected-account access synchronization |
| Known route / 503 | Missing dedicated grant or disabled owned channel; do not fall back |
| Claude subscription / generic 429 | Native client comparison, minimum supported client version and required Agent SDK preamble; a 429 alone does not prove quota exhaustion |
| 429 `insufficient_quota` (r2 and later) | An upstream account out of money or plan allowance (OpenRouter workspace/key budget, 402 credits, Kimi weekly window, z.ai 1113/1308/1310). Only the final client response is rewritten: the error log keeps the upstream status (`status_code=403`, 402 or 400), retry and channel auto-disable see it too, and no channel is disabled. `Retry-After` appears only when the reset is derivable (OpenRouter daily budget: next 00:00 UTC). Read the ledger row, not the client status, and never switch accounts to get around it |
| Claude native `context_management` / 400 | Required beta defaults must be appended to native feature headers, never replace the caller's entire `anthropic-beta` |
| SDK succeeds, CLI fails | Native protocol, helper models, CLI auth precedence, beta headers and installed settings schema |
| Config correct, traffic still direct | Actual process environment, launcher/profile/generator precedence, stale installed service or alternate helper path |
| Tool continuation fails | Complete assistant/reasoning/tool history and preserved call IDs; converted Responses cannot rely on upstream response storage |
| Claude `tool_result.content` rejects `input_text` | Wrong nested wire format in the selected converter; normalize array blocks rather than repairing credentials |
| Claude says tool results must immediately follow tool use | Parallel results were separated by commentary/instructions; preserve the whole batch and normalize safe interleaving |
| Claude refuses assistant prefill after results | Deferred commentary became the final assistant message; test continuation ending at the actual last result, without adding a user turn |
| HTTP 200 but no expected answer | Inspect Responses terminal status, `incomplete_details`, native stop reason and returned text separately; provider `content_filter` and punctuation are not auth failures |
| New channel temporarily absent | Routing-cache readiness; bounded retry before diagnosing the configuration |
| Immediately after recreation / JSON 503 with `Retry-After` | Caddy answers 503 until `new-api` is healthy (roughly 30 seconds); bound retries and recheck health |
| Timer enabled, grant unhealthy | Real oneshot exit status, manager vault access, identity/expiry and pending-refresh marker |

Transient readiness retries must be bounded. Do not retry authentication failures,
denied scope, rate limits or incomplete-refresh rotation indefinitely. Account
selection, preserved provider errors and zero-charge failures are part of the
contract, not problems to hide with another route.

## Baseline and remaining gate

The 2026-09-30 snapshot passed 48/48 API/stream/tool checks across six connected
routes, all four effort levels on those routes, token authorization checks,
native Claude Code on both subscription accounts and independent forced Claude
renewals. The exact evidence and image live in the deployment acceptance file.

That initial snapshot's OpenAI connection gate was completed later the same day.
Astra/Sol/Sol 6.1 passed 24 API/stream/parallel-tool checks and 24 effort/ledger
checks after forced dedicated renewal and recreation. Bare installed Codex and
its native hook verified completed gateway receipts with the child's own UUID.
The all-account renewal oneshot succeeded. Current evidence is in
`ops/SESSION-ROUTING-PROOF.md` and the updated deployment acceptance record.

DELO-1 remains the hardening epic with controlled OpenAI failure/isolation
acceptance still named separately; DELO-2 (`aai-auto`) remains Backlog and blocked
by it. Re-read board state before changing tickets and keep these gates honest.
