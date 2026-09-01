# Consumers

How to receive events from the bloodbank bus. The recommended default for new consumers is **NATS core subscribe** on a specific subject (or a wildcard). Reach for JetStream durables, Dapr subscribers, FastStream, or the catch-all toaster only when their distinct capabilities are needed.

## Reading Order

| Task | Read |
|---|---|
| Pick the right consumer path | this README + the consumer decision tree in `../../SKILL.md` |
| Copy-paste a working pattern | `methods.md` |
| Hit a confusing failure (messages dropped, replay weirdness, ack issues) | `gotchas.md` |

## Consumer methods at a glance

| Method | Durable? | Use when | Code reference |
|---|---|---|---|
| **NATS core subscribe**          | No  | Fire-and-forget reactions, observability, wildcard fan-in | `bloodbank/services/event-toaster/main.py` |
| **NATS JetStream durable**       | Yes | Must not miss messages; need replay; consumer can be offline | `bloodbank/compose/v3/nats/streams.json` |
| **Dapr subscriber**              | Yes (Dapr handles ack) | Service already has a Dapr sidecar; want declarative subscriptions | `bloodbank/services/claude-events-recorder/main.py` |
| **FastStream RabbitMQ consumer** | Yes (AMQP ack) | v2 only; legacy consumer or RabbitMQ-only environment | `bloodbank/event_producers/consumer.py` |
| **ntfy.delo.sh/bloodbank**       | No  | You want desktop notifications, not code-level consumption | already running; subscribe in the ntfy app |

Canonical platform consumers are intentionally different: Candystore uses a
durable Dapr/JetStream subscription on `bloodbank.evt.>`; event-toaster uses a
non-durable core wildcard for human notification; the Hermes fleet gateway uses
a durable pull consumer on the **command** stream. Do not copy one consumer's
delivery semantics into another just because all three connect to NATS.

## The default

For new consumers, default to **NATS core subscribe** on the specific subject your service cares about:

```python
import asyncio, json, nats

async def main():
    nc = await nats.connect("nats://nats:4222", name="my-consumer")

    async def on_msg(msg):
        envelope = json.loads(msg.data.decode("utf-8"))
        # react...

    await nc.subscribe("bloodbank.evt.agent.tool.completed", cb=on_msg)
    await asyncio.Event().wait()   # run forever

asyncio.run(main())
```

Subject filters:

- `bloodbank.evt.agent.tool.completed` — exactly that event.
- `bloodbank.evt.agent.>` — all agent events.
- `bloodbank.evt.>` — wildcard fan-in (the catch-all pattern; see `event-toaster`).

## When to upgrade past core subscribe

| Need | Path |
|---|---|
| "Consumer can be offline and not miss anything" | JetStream durable consumer on the matching stream |
| "Replay events from a point in time / sequence" | JetStream durable with `deliver_policy` |
| "I already have a Dapr sidecar in this service" | Dapr subscriber via `/dapr/subscribe` routes |
| "I'm wiring a v2 RabbitMQ consumer that pre-dates the v3 migration" | FastStream + exchange `bloodbank.events.v1` |
| "I just want to see events on my phone" | Subscribe to topic `bloodbank` on `https://ntfy.delo.sh` |
| "I need a durable audit/read model" | Follow Candystore's Dapr `bloodbank.evt.>` projection |
| "I consume targeted agent commands" | Follow the fleet-shared Hermes JetStream pull consumer; never make one consumer per agent |

Recipes for each are in [methods.md](./methods.md).
