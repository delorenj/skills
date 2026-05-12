# Producers

How to publish an event onto the bloodbank bus. The recommended path is **NATS direct** with a holyfields-generated envelope; reach for an alternative only when the recommended path doesn't fit your runtime.

## Reading Order

| Task | Read |
|---|---|
| Pick the right producer path for your runtime | this README + the producer decision tree in `../../SKILL.md` |
| Copy-paste a working pattern (NATS direct, Dapr, HTTP, hookd_bridge) | `methods.md` |
| Hit a confusing failure (envelope never arrived, duplicate publish, etc.) | `gotchas.md` |

## Producer methods at a glance

| Method | When to use | Where it lands | Code reference |
|---|---|---|---|
| **NATS direct (nats-py)**       | Long-running Python service on host, has nats-py available | NATS subject `event.<type>` | _new code; see `methods.md`_ |
| **NATS direct (stdlib TCP)**    | Hook scripts, no deps allowed, fire-and-forget | NATS subject `event.<type>` | `bloodbank/services/copilot-hooks/copilot_hook_publish.py` |
| **Dapr pub/sub**                | 33GOD service container with a Dapr sidecar | Dapr `bloodbank-v3-pubsub` → NATS `event.<type>` | `bloodbank/services/heartbeat-tick/main.py` |
| **bloodbank HTTP `/publish`**   | External tool with HTTP only, generic event | RabbitMQ `bloodbank.events.v1` (v2 path; toaster won't see it) | `bloodbank/event_producers/http.py` |
| **bloodbank HTTP `/event`**     | Typed webhook (Plane, GitHub) where bloodbank derives the routing key | RabbitMQ `bloodbank.events.v1` (v2 path) | `bloodbank/event_producers/http.py` |
| **hookd_bridge `/hooks/agent`** | Issuing a COMMAND envelope (not an event) to a specific agent | RabbitMQ `command.<target>.<verb>` | `bloodbank/hookd_bridge/bridge.py` |

## The default

For new producers, default to **NATS direct** on subject `event.<type>` using a holyfields-generated envelope:

```python
import nats, json
from holyfields.generated.agent.session_started_v1 import AgentSessionStartedV1, AgentSessionStartedV1Data

env = AgentSessionStartedV1(
    specversion="1.0", id=str(uuid.uuid4()),
    source="urn:33god:service:my-service",
    type="agent.session.started",
    subject=f"agent/{session_id}",
    time=now_iso(), domain="agent",
    data=AgentSessionStartedV1Data(session_id=session_id, working_directory=cwd, started_at=now_iso()),
)
nc = await nats.connect("nats://nats:4222")    # use localhost:4222 from the host
await nc.publish("event.agent.session.started", env.model_dump_json().encode())
await nc.drain()
```

Verify it arrived: tail `bloodbank-event-toaster` logs or curl `https://ntfy.delo.sh/bloodbank/json?poll=1&since=30s`.

## When the default doesn't fit

Use `methods.md` to pick the alternative. The common reasons to deviate:

- You're a webhook receiver with no NATS reachability → HTTP `/event`.
- You're a Bash hook from an agent harness → stdlib NATS (see the copilot-hooks pattern).
- You need command semantics (TTL, FSM-guard, target_agent) → hookd_bridge.
- You already have a Dapr sidecar wired up → Dapr publish (one less broker to think about in your service code).
