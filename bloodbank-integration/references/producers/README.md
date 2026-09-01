# Producers

How to publish an event onto the bloodbank bus. The recommended path is **NATS direct** with a Bloodbank schemas-generated envelope; reach for an alternative only when the recommended path doesn't fit your runtime.

## Reading Order

| Task | Read |
|---|---|
| Pick the right producer path for your runtime | this README + the producer decision tree in `../../SKILL.md` |
| Copy-paste a working pattern (NATS direct, Dapr, HTTP, hookd_bridge) | `methods.md` |
| Hit a confusing failure (envelope never arrived, duplicate publish, etc.) | `gotchas.md` |

## Producer methods at a glance

| Method | When to use | Where it lands | Code reference |
|---|---|---|---|
| **NATS direct (nats-py)**       | Long-running Python service on host, has nats-py available | NATS subject `bloodbank.evt.<domain>.<entity>.<action>` | _new code; see `methods.md`_ |
| **NATS direct (stdlib TCP)**    | Hook scripts, no deps allowed, fire-and-forget | NATS subject `bloodbank.evt.<...>` | `bloodbank/services/agent-hooks/core/nats_publish.py` |
| **Dapr pub/sub**                | 33GOD service container with a Dapr sidecar | Dapr `bloodbank-pubsub` → NATS `bloodbank.evt.<...>` | `bloodbank/services/heartbeat-tick/main.py` |
| **bloodbank HTTP `/publish`**   | External tool with HTTP only, generic event | RabbitMQ `bloodbank.events.v1` (v2 path; toaster won't see it) | `bloodbank/event_producers/http.py` |
| **n8n Plane ingress**           | Signed Plane webhook from either self-hosted workspace | HMAC + normalization → NATS `bloodbank.evt.repo.*` | `bloodbank/integrations/n8n-nodes-bloodbank` |
| **bloodbank HTTP `/event`**     | Legacy typed HTTP producer that explicitly needs v2 | RabbitMQ `bloodbank.events.v1` (v2 path) | `bloodbank/event_producers/http.py` |
| **hookd_bridge `/hooks/agent`** | Issuing a COMMAND envelope (not an event) to a specific agent | command subject `bloodbank.cmd.agent.invocation.start` | `bloodbank/hookd_bridge/bridge.py` |

## The default

For new producers, default to **NATS direct** on the envelope's `subject` using a Bloodbank schemas-generated envelope:

```python
import nats, json
# symbol names come from your codegen run over schemas/bloodbank/agent/session.started.json
from bloodbank.generated.agent.session_started import AgentSessionStarted, AgentSessionStartedData

env = AgentSessionStarted(
    specversion="1.0", id=str(uuid.uuid4()),
    source="urn:33god:service:my-service",
    type="bloodbank.agent.session.started",
    subject="bloodbank.evt.agent.session.started",
    time=now_iso(), domain="agent",
    data=AgentSessionStartedData(session_id=session_id, working_directory=cwd, started_at=now_iso()),
)
nc = await nats.connect("nats://nats:4222")    # use localhost:4222 from the host
await nc.publish(env.subject, env.model_dump_json().encode())
await nc.drain()
```

Verify it arrived: tail `bloodbank-event-toaster` logs or curl `https://ntfy.delo.sh/bloodbank/json?poll=1&since=30s`.

## When the default doesn't fit

Use `methods.md` to pick the alternative. The common reasons to deviate:

- You're receiving Plane → use the one HTTPS n8n ingress; do not add `/event`, a second workflow, or a port-8477 relay.
- You're another webhook receiver with no NATS reachability → build an authenticated normalization adapter; treat HTTP `/event` as a legacy v2 exception.
- You're a Bash hook from an agent harness → canonical `services/agent-hooks/publish.py` + client adapter.
- You need command semantics (TTL, FSM-guard, target_agent) → hookd_bridge.
- You already have a Dapr sidecar wired up → Dapr publish (one less broker to think about in your service code).
