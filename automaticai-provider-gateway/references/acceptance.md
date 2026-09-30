# Acceptance and diagnosis

Read current `ops/ACCEPTANCE-unified-provider.md` and the consumer's installed
state. Use a current scoped token; a previous short-lived acceptance token may
have expired. Do not print its resolved value or redirect it to a file.

## Choose the appropriate proof

For a consumer configuration change, probe its selected account through its
actual installed CLI/SDK/service. Cover streaming and tool continuation when
that consumer uses them. Prove a spawned worker or helper path separately when
it has its own configuration source.

For relay changes, an added account or broad route changes, use the live harness:

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
streaming with usage, and multiple function calls followed by their outputs and
the final reply. It does not replace native Claude/Codex acceptance or the
consumer's feature-specific test.

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
| Claude native `context_management` / 400 | Required beta defaults must be appended to native feature headers, never replace the caller's entire `anthropic-beta` |
| SDK succeeds, CLI fails | Native protocol, helper models, CLI auth precedence, beta headers and installed settings schema |
| Config correct, traffic still direct | Actual process environment, launcher/profile/generator precedence, stale installed service or alternate helper path |
| Tool continuation fails | Complete assistant/reasoning/tool history and preserved call IDs; converted Responses cannot rely on upstream response storage |
| New channel temporarily absent | Routing-cache readiness; bounded retry before diagnosing the configuration |
| Immediately after recreation / edge 404 | Traefik readiness can lag roughly 30 seconds; bound retries and recheck health |
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
