# Consumer methods — recipes

## 1. NATS core subscribe (recommended for most consumers)

**Requires.** `nats-py`; NATS reachable.

**Pattern.**

```python
import asyncio, json, nats
from nats.aio.msg import Msg

async def main():
    nc = await nats.connect("nats://nats:4222", name="my-consumer", max_reconnect_attempts=-1)

    async def on_msg(msg: Msg):
        envelope = json.loads(msg.data.decode("utf-8", errors="replace"))
        # work...

    await nc.subscribe("event.agent.tool.invoked", cb=on_msg)
    await asyncio.Event().wait()

asyncio.run(main())
```

**Properties.** No durability — if your service is down when an event fires, the event is missed. No ack — if your handler raises, the message is gone. Fan-in works (multiple instances of the same consumer all get every message).

**Reference.** `bloodbank/services/event-toaster/main.py` — wildcard `event.>` fan-in.

## 2. NATS JetStream durable consumer

**Requires.** The target stream exists (defined in `bloodbank/compose/v3/nats/streams.json`); `nats-py` with `js` API.

**Pattern.**

```python
import asyncio, json, nats

async def main():
    nc = await nats.connect("nats://nats:4222")
    js = nc.jetstream()

    async def on_msg(msg):
        envelope = json.loads(msg.data.decode("utf-8"))
        # work...
        await msg.ack()

    await js.subscribe(
        subject="event.agent.session.started",
        durable="my-consumer-durable",
        cb=on_msg,
        manual_ack=True,
    )
    await asyncio.Event().wait()

asyncio.run(main())
```

**Properties.** Durable — JetStream tracks last-acked sequence per `durable` name. Offline consumers catch up on reconnect. Required for "must not miss" semantics.

**Caution.** A subject must be covered by a stream definition (`streams.json`) for JetStream to retain it. Subjects outside any stream are ephemeral even with a durable consumer.

## 3. Dapr subscriber

**Requires.** Service container has a daprd sidecar. Service exposes an HTTP endpoint that Dapr can call.

**Pattern.** Reference: `bloodbank/services/claude-events-recorder/main.py`.

```python
# /dapr/subscribe — Dapr calls this once at sidecar startup
SUBSCRIPTIONS = [
    {"pubsubname": "bloodbank-v3-pubsub", "topic": "event.agent.session.started",
     "route": "/events/session_started"},
    {"pubsubname": "bloodbank-v3-pubsub", "topic": "event.agent.tool.invoked",
     "route": "/events/tool_invoked"},
]

# Then handle POST /events/session_started — Dapr delivers each matching event
# as a CloudEvents JSON body. Return 200 for ack, 500 to nack/retry.
```

**Properties.** Dapr handles connection, retries, and acks via HTTP status codes. Decouples your service from the broker.

## 4. FastStream RabbitMQ consumer (v2 / legacy)

**Requires.** RabbitMQ at `amqp://...:5673`; exchange `bloodbank.events.v1` (declared by the bloodbank service on startup).

**Pattern.**

```python
from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, ExchangeType, RabbitQueue

broker = RabbitBroker("amqp://delorenj:$RABBITMQ_PASS@localhost:5673/")
app = FastStream(broker)

events_x = RabbitExchange("bloodbank.events.v1", type=ExchangeType.TOPIC, durable=True)
queue    = RabbitQueue("my-consumer.agent_events", routing_key="agent.#", durable=True)

@broker.subscriber(queue, events_x)
async def handle(envelope: dict):
    # work...
    return  # ack is implicit on successful return
```

**Properties.** Topic-pattern matching with `*` (one token) and `#` (zero+ tokens). Durable queue retains messages while consumer is offline.

**Caution.** v2 RabbitMQ events are not bridged to v3 NATS. Producers on `/publish` land here; producers on NATS direct or Dapr do NOT.

## 5. ntfy.delo.sh/bloodbank (read-only catch-all)

Nothing to deploy. Open `https://ntfy.delo.sh/bloodbank` in the ntfy mobile/desktop app or fetch the JSON stream:

```bash
curl -s "https://ntfy.delo.sh/bloodbank/json?poll=1&since=5m"
```

Every event the toaster sees on `event.>` shows up here. Use it for human eyes / smoke tests, not for code-level consumption.
