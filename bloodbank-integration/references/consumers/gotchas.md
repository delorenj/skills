# Consumers — gotchas

Each gotcha: **Symptom**, **Cause**, **Fix**, **Prevention**.

## 1. "JetStream durable consumer skips messages it should have replayed"

**Symptom.** Restart the consumer; messages published while it was offline never arrive.

**Cause.** Either (a) the subject isn't covered by a stream in `compose/v3/nats/streams.json` (so JetStream wasn't storing them in the first place), or (b) the durable was created with `deliver_policy="new"` (only future messages).

**Fix.** Confirm the stream covers the subject (`nats stream ls` from a nats-box). Recreate the durable with `deliver_policy="all"` if you genuinely want backfill.

**Prevention.** When adding a new event_type, add (or extend) a stream definition in `streams.json` in the same PR.

## 2. "Core subscribe drops messages under load"

**Symptom.** Bursts of events arrive but the consumer processes only some.

**Cause.** Core subscribe is fire-and-forget; the handler is slower than the producer rate, and NATS has no retention to replay from.

**Fix.** Convert to a JetStream durable consumer. Core subscribe is only for the catch-all/observability pattern where dropped messages are acceptable.

**Prevention.** Decide durability up front: if the consumer's job is operationally meaningful, use JetStream.

## 3. "Dapr subscriber gets every message twice"

**Symptom.** The consumer logs the same event two or more times.

**Cause.** Most often a duplicate route in `SUBSCRIPTIONS` (same topic, two routes), or a stale sidecar mounting an old subscription list alongside a fresh one.

**Fix.** Audit `/dapr/subscribe` for duplicate `(pubsubname, topic)` pairs. Restart the sidecar after changing the subscription list.

**Prevention.** Diff the subscriptions list on startup against expected; fail the boot if there are duplicates.

## 4. "Toaster sees the event but my JetStream durable doesn't"

**Symptom.** `bloodbank-event-toaster` logs `toasted: foo.bar.baz` but your durable consumer on the same subject is silent.

**Cause.** Toaster uses **core** subscribe (sees every message on the broker); JetStream durables only see messages **retained by a stream**. The subject isn't in any stream.

**Fix.** Add the subject to the appropriate stream in `compose/v3/nats/streams.json` and re-apply (`nats-init` runs at compose-up time).

**Prevention.** Treat the toaster as a "did it hit the broker" check, not a "is it retained" check.

## 5. "FastStream consumer binds but never gets messages"

**Symptom.** No exceptions on startup, queue is declared, but messages from `/publish` never arrive.

**Cause.** Wrong routing key pattern. `bloodbank.events.v1` is a **topic** exchange — patterns use `*` (one token) and `#` (zero+ tokens), not regex.

**Fix.** For "all agent events": `routing_key="agent.#"`. For exactly `agent.session.started`: `routing_key="agent.session.started"`. For "all session.* events from any domain": `routing_key="*.session.*"`.

**Prevention.** Match what you see in `event_producers/http.py` — the routing key is the envelope's `event_type` field verbatim.

## 6. "Consumer crashes on schema-validation error"

**Symptom.** A new field was added upstream; consumer crashes parsing it against an older holyfields version.

**Cause.** Producer regenerated and published with a newer schema; consumer's pinned holyfields version doesn't know about the field. With `additionalProperties: false`, Pydantic rejects.

**Fix.** Update the consumer's holyfields dependency to a version that includes the new field. Restart.

**Prevention.** Schemas in `_common/cloudevent_base.v1.json` and per-event schemas should keep `additionalProperties: false` only at the envelope level (where 33GOD knows the field set). At the `data` level, consider permitting unknowns or use Pydantic `model_config = ConfigDict(extra="ignore")` in consumers.

## 7. "ntfy stream stops mid-day"

**Symptom.** You stop seeing toasts on `https://ntfy.delo.sh/bloodbank`.

**Cause.** The toaster container is down or the ntfy server is unreachable. The toaster is best-effort by design.

**Fix.** `docker logs bloodbank-event-toaster --tail 50`. Common: container restarted and lost its NATS subscription handle — usually self-heals via `max_reconnect_attempts=-1`.

**Prevention.** Don't depend on the toaster for anything operational; it's intentionally not durable.
