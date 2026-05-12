# Producers — gotchas

Each gotcha: **Symptom**, **Cause**, **Fix**, **Prevention**.

## 1. "I published but `event-toaster` never logged it"

**Symptom.** A `curl … /publish` returns 200, but `docker logs bloodbank-event-toaster` shows nothing for your event.

**Cause.** `/publish` lands on the v2 RabbitMQ exchange. `event-toaster` subscribes to v3 NATS `event.>` only. The two buses are not bridged.

**Fix.** Republish through NATS — either the stdlib pattern (`bloodbank/services/copilot-hooks/copilot_hook_publish.py`) or nats-py.

**Prevention.** Default to NATS for new producers. Reserve HTTP `/publish` for webhook receivers that genuinely need v2.

## 2. "My NATS publish goes through but downstream consumers don't react"

**Symptom.** Toaster logs `toasted: myservice.thing.happened` (so NATS got it), but the specific consumer that filters on `type == "myservice.thing.happened"` never fires.

**Cause.** Envelope `type` field doesn't match the NATS subject. The subject was `event.myservice.thing.happened` but the envelope's `type` is `"myservice.thing.HAPPENED"` or `"my-service.thing.happened"` etc.

**Fix.** Make subject and `type` mathematically derivable: subject = `event.` + type. Always.

**Prevention.** Derive both from a single constant in your code. Never type either by hand at the call site.

## 3. "Dapr publish returns 204 but no NATS message"

**Symptom.** `POST /v1.0/publish/bloodbank-v3-pubsub/<topic>` returns 204 No Content; subject is silent on NATS.

**Cause.** Dapr can succeed when the pubsub component is misconfigured (typo in `metadata.url`, wrong component name). Dapr's success means "I queued the publish locally," not "the broker accepted it."

**Fix.** Check the daprd sidecar logs (`docker logs <svc>-daprd`) for `error publishing to topic`. Confirm the component name in `compose/v3/components/` matches the path segment after `/publish/`.

**Prevention.** Wire an integration smoke test that publishes once and reads back via NATS in CI. The `bloodbank-event-toaster` ntfy stream is a fast manual smoke check.

## 4. "Hook hangs the agent for ~5 seconds"

**Symptom.** Claude Code or Copilot CLI feels sluggish after wiring up a publish hook. Each tool call has a visible delay.

**Cause.** Publish path is making a DNS lookup, TLS handshake, HTTPS POST, etc. on a hot path. Or NATS is unreachable and the 5-second timeout fires on every hook.

**Fix.** Use the stdlib NATS publisher to localhost on a TCP connection — sub-50ms total. If you must use HTTP, run a tiny on-host proxy and POST to `127.0.0.1`.

**Prevention.** Time it before deploying: `time printf '{"x":1}' | python3 publisher.py preToolUse` should be < 50ms.

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
