# Producer methods — recipes

Each section is a self-contained recipe with the runtime requirements, env vars, and a runnable code snippet.

## 1. NATS direct via nats-py (recommended for services)

**Requires.** `nats-py` in your service's dependencies; NATS reachable at `nats://nats:4222` (inside `bloodbank-network`) or `nats://127.0.0.1:4222` (from host).

**Pattern.**

```python
import asyncio, json, uuid
from datetime import datetime, timezone
import nats

async def emit():
    nc = await nats.connect("nats://nats:4222", name="my-service")
    envelope = {
        "specversion": "1.0",
        "id": str(uuid.uuid4()),
        "source": "urn:33god:service:my-service",
        "type": "myservice.thing.happened",
        "subject": "thing/abc123",
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "datacontenttype": "application/json",
        "domain": "myservice",
        "data": {"thing_id": "abc123", "detail": "..."},
    }
    await nc.publish("event.myservice.thing.happened", json.dumps(envelope).encode("utf-8"))
    await nc.drain()

asyncio.run(emit())
```

**Verify.** `docker logs bloodbank-event-toaster --tail 5` should show `toasted: myservice.thing.happened`.

## 2. NATS direct via stdlib TCP (recommended for shell hooks)

**Requires.** Python ≥ 3.10 only — no `nats-py`, no virtualenv. Use this when a Bash hook must publish without dragging in dependencies.

**Pattern.** See the working implementation:

- `bloodbank/services/copilot-hooks/copilot_hook_publish.py` (full file, ≈ 80 SLoC)

The hot path is ~6 lines:

```python
with socket.create_connection(("127.0.0.1", 4222), timeout=3) as s:
    f = s.makefile("rwb", buffering=0); f.readline()                           # eat INFO
    f.write(b'CONNECT {"verbose":false,"name":"hook","lang":"py-stdlib"}\r\n')
    f.write(f"PUB {subject} {len(body)}\r\n".encode() + body + b"\r\n")
    f.write(b"PING\r\n"); f.flush()
    while not f.readline().startswith(b"PONG"): pass                            # drain
```

**When to use.** Copilot CLI hooks, ad-hoc one-shot scripts, anywhere a `requirements.txt` would be overkill.

## 3. Dapr pub/sub (when you have a sidecar)

**Requires.** Service container with a daprd sidecar configured against `bloodbank-v3-pubsub`. Dapr resolves the underlying NATS connection from the component config in `bloodbank/compose/v3/components/`.

**Pattern.** Reference implementation: `bloodbank/services/heartbeat-tick/main.py`.

```python
import json, urllib.request

DAPR_HTTP = "http://daprd-mysvc:3500"
PUBSUB = "bloodbank-v3-pubsub"
TOPIC = "event.myservice.thing.happened"   # Dapr topic == NATS subject

req = urllib.request.Request(
    f"{DAPR_HTTP}/v1.0/publish/{PUBSUB}/{TOPIC}",
    data=json.dumps(envelope).encode("utf-8"),
    headers={"Content-Type": "application/cloudevents+json"},
    method="POST",
)
urllib.request.urlopen(req, timeout=5).read()
```

**Why over NATS direct.** Dapr handles reconnect, retries, the CloudEvents wrapper, and decouples your code from the broker choice. If the bus ever moves off NATS, only the Dapr component config changes.

## 4. bloodbank HTTP `/publish` (RabbitMQ path)

**Requires.** bloodbank's FastAPI service reachable at `http://bloodbank:8000` (in network) or `https://bloodbank.delo.sh` (external). RabbitMQ at `amqp://...:5673`.

**Important.** This publishes to the **v2 RabbitMQ exchange** (`bloodbank.events.v1`). The v3 NATS catch-all (`event-toaster`) does **not** see RabbitMQ-only events. Use this only when:

- you genuinely need v2 fan-out (e.g., a consumer wired through FastStream)
- you have HTTP only and no path to NATS

```bash
curl -X POST https://bloodbank.delo.sh/publish \
  -H "Content-Type: application/json" \
  -d '{"event_type": "myservice.thing.happened", "payload": {"thing_id": "abc"}}'
```

## 5. bloodbank HTTP `/event` (typed webhook ingress)

For webhooks where bloodbank derives the routing key from headers/body (Plane, GitHub-style). See `bloodbank/event_producers/http.py:195` for the full handler.

```bash
curl -X POST 'https://bloodbank.delo.sh/event?secret=$PLANE_WEBHOOK_SECRET' \
  -H 'x-plane-event: issue.created' \
  -H 'content-type: application/json' \
  -d '{...plane payload...}'
```

Same v2 RabbitMQ caveat as `/publish`.

## 6. hookd_bridge `/hooks/agent` (command envelopes)

For issuing a directive at a specific agent, not announcing a fact. The bridge wraps your text in a CommandEnvelope and publishes on `command.<target>.<verb>`.

```bash
curl -X POST http://localhost:18790/hooks/agent \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[Command] action=run_drift_check from=ops priority=normal",
    "sessionKey": "agent:lenoon:main"
  }'
```

Use only when you actually need command semantics. Most integrations want event semantics — stay in `event.*`.
