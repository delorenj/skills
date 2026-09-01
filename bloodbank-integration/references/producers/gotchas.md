# Producers — gotchas

Each gotcha: **Symptom**, **Cause**, **Fix**, **Prevention**.

## 1. "I published but `event-toaster` never logged it"

**Symptom.** A `curl … /publish` returns 200, but `docker logs bloodbank-event-toaster` shows nothing for your event.

**Cause.** `/publish` lands on the v2 RabbitMQ exchange. `event-toaster` subscribes to v3 NATS `bloodbank.evt.>` only. The two buses are not bridged.

**Fix.** Republish through NATS — either the canonical stdlib hook publisher (`bloodbank/services/agent-hooks/publish.py`) or nats-py.

**Prevention.** Default to NATS for new producers. Reserve HTTP `/publish` for webhook receivers that genuinely need v2.

## 2. "My NATS publish goes through but downstream consumers don't react"

**Symptom.** Toaster logs `toasted: myservice.thing.happened` (so NATS got it), but the specific consumer that filters on `type == "myservice.thing.happened"` never fires.

**Cause.** Envelope `type` field doesn't match the NATS subject. The subject was `bloodbank.evt.system.heartbeat.received` but the envelope's `type` is `"bloodbank.system.heartbeat.RECEIVED"` or `"system.heartbeat.received"` etc.

**Fix.** Make subject and `type` mathematically derivable: insert `evt` after the `bloodbank` segment (`bloodbank.x.y.z` -> `bloodbank.evt.x.y.z`). Always.

**Prevention.** Derive both from a single constant in your code. Never type either by hand at the call site.

## 3. "Dapr publish returns 204 but no NATS message"

**Symptom.** `POST /v1.0/publish/bloodbank-pubsub/<topic>` returns 204 No Content; subject is silent on NATS.

**Cause.** Dapr can succeed when the pubsub component is misconfigured (typo in `metadata.url`, wrong component name). Dapr's success means "I queued the publish locally," not "the broker accepted it."

**Fix.** Check the daprd sidecar logs (`docker logs <svc>-daprd`) for `error publishing to topic`. Confirm the component name in `compose/v3/components/` matches the path segment after `/publish/`.

**Prevention.** Wire an integration smoke test that publishes once and reads back via NATS in CI. The `bloodbank-event-toaster` ntfy stream is a fast manual smoke check.

## 4. "Hook hangs the agent for ~5 seconds"

**Symptom.** Claude Code or Copilot CLI feels sluggish after wiring up a publish hook. Each tool call has a visible delay.

**Cause.** Publish path is making a DNS lookup, TLS handshake, HTTPS POST, etc. on a hot path. Or NATS is unreachable and the 5-second timeout fires on every hook.

**Fix.** Use the stdlib NATS publisher to localhost on a TCP connection — sub-50ms total. If you must use HTTP, run a tiny on-host proxy and POST to `127.0.0.1`.

**Prevention.** Time it before deploying: `time printf '{"x":1}' | python3 ~/code/33GOD/bloodbank/services/agent-hooks/publish.py --client claude --hook post_tool` should be < 50ms.

## 5. "Hook script killed Copilot when the broker was down"

**Symptom.** During a NATS outage, the agent harness errors out on every tool use because the hook script returns non-zero.

**Cause.** The publisher is failing strict and propagating its non-zero exit to the harness, which treats it as a hook veto.

**Fix.** Make the publisher fail open — exit 0 on connect/publish errors, log to stderr. Gate strict mode behind an env var (`BLOODBANK_HOOK_STRICT=1`) for debugging only.

**Prevention.** Validate the fail-open behavior in the publisher's tests by pointing it at `127.0.0.1:1` (closed port) and asserting exit 0.

## 6. "Two services publish the same event_type and I get duplicate downstream effects"

**Symptom.** A consumer that increments a counter is double-incrementing per real-world event.

**Cause.** Two producers think they own the same event. Common when migrating from v2 to v3 and both paths are live simultaneously.

**Fix.** Identify the canonical owner. Deactivate the duplicate by either (a) removing its publish call, or (b) renaming its `type` to a producer-specific variant during migration.

**Prevention.** One event_type = one producer service. Encode the owning service in the envelope's `source` (`urn:33god:service:<owner>`) and have consumers reject foreign sources during cutover.

## 7. "`bb.py emit` exists but does nothing"

**Symptom.** `python3 bloodbank/cli/bb.py emit ...` prints usage and exits; there is no documented way to hand-craft an event.

**Cause.** `emit` is intentionally a stub in the current wave. Per the module docstring, operator emission is only valid through a Dapr sidecar per ADR-0001; the CLI is not the production publish path.

**Fix.** If you are on the host and the Candystore / platform stack is up, publish directly to the local candystore Dapr sidecar. Construct a valid CloudEvents envelope, validate it with `bb.py verify-envelope --file <envelope.json>`, then POST it:

```python
import json, urllib.request

with open("envelope.json") as f:
    envelope = json.load(f)

req = urllib.request.Request(
    "http://127.0.0.1:3504/v1.0/publish/bloodbank-pubsub/bloodbank.evt.<domain>.<entity>.<action>",
    data=json.dumps(envelope).encode("utf-8"),
    headers={"Content-Type": "application/cloudevents+json"},
    method="POST",
)
urllib.request.urlopen(req, timeout=5)   # 204 = accepted
```

Verify ingestion by querying Candystore: `GET http://127.0.0.1:8683/events?type=<type>&limit=10`.

**Prevention.** Treat `bb.py emit` as a scaffold placeholder. For recurring operator emission, add a small wrapper script that validates the envelope and posts to the sidecar, rather than relying on the stub subcommand.

## Plane HMAC fails even though the configured secret is correct

**Symptom.** The active n8n Plane workflow rejects `X-Plane-Signature`, often
after a Code/Set node or webhook-node option changed.

**Cause.** Plane signs the exact request bytes. HMAC verification was attempted
over parsed/re-serialized JSON, or the n8n Webhook node did not preserve the raw
body. Equivalent JSON is not byte-identical JSON.

**Fix.** Enable raw-body handling on the Webhook node and pass those bytes to the
custom Plane → Bloodbank node. Select the secret by payload `webhook_id`; do not
guess by workspace name. Resolve the selected `op://` reference only at runtime.

**Prevention.** Keep HMAC verification as the first provenance step. Test a known
webhook, an unknown `webhook_id`, a bad signature, and a payload whose parsed
object would serialize differently.

## Plane events arrive twice or on the wrong transport

**Symptom.** A single Plane action produces duplicate facts, or `/event` returns
200 while NATS/Candystore remains silent.

**Cause.** A legacy port-8477 bridge, second n8n workflow, or Bloodbank HTTP
`/event` path is still active. `/event` lands on RabbitMQ v2; it is not bridged to
the canonical NATS event stream.

**Fix.** Keep exactly one active Plane workflow and one Plane webhook per
workspace, all targeting `https://n8n.delo.sh/webhook/plane`. Disable the legacy
relay and query Candystore for the deterministic event ID before retrying.

**Prevention.** Treat n8n as the sole Plane provenance boundary and derive a
deterministic ID from provider action, board, entity, source time, and state or
comment identity.
