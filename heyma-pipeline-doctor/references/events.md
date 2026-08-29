# Events / Bloodbank — playbook

Symptoms that land here: the outbox is growing; nothing appears in Candystore;
no notification arrived for something that failed.

## The chain

```
ledger write + outbox insert   (same transaction)
        ▼
waxd drains every 10 s → natsclient → JetStream PubAck → outbox.published_at set
        ▼
nats://127.0.0.1:4222 → Candystore 127.0.0.1:8683 (archives bloodbank.evt.>)
```

Publishing is **fail-open**: a dead bus never stops a recording or a
transcription. Events simply queue.

## Triage

```bash
# is the bus up?
python3 -c "import socket;print(socket.create_connection(('127.0.0.1',4222),timeout=4).recv(64)[:40])"

# is the outbox draining? a transient non-zero backlog is normal (10 s cycle) —
# only rows older than ~10 min mean the drain itself stopped.
sqlite3 -readonly "file:$HOME/HeyMa/var/wax.db?mode=ro" \
  "SELECT subject, created_at FROM outbox WHERE published_at IS NULL ORDER BY created_at LIMIT 10;"

bin/wax events            # CLI view
docker ps | grep -i nats
```

## The alerting gap — the important part

**The bus works. The problem has never been delivery; it is that nothing a human
reads is subscribed to Wax failures.**

`passes.py` emits a proper `task.failed` event on every pass failure, and those
events were published successfully and archived in Candystore throughout the
five-day title-slug outage. Nobody was watching.

The one channel that does fire is `bloodbank-event-toaster`, which forwards
**every** `bloodbank.evt.>` envelope to `ntfy.delo.sh/bloodbank` at priority 5.
Measured: **20,327 toasts in 24 h, 95.9 % of them `agent.tool.*`, and 10 (0.05 %)
audio failures.** A signal placed in that topic is destroyed by the noise.

So when triaging "why wasn't I told":

1. Confirm the event was emitted — `SELECT * FROM outbox WHERE subject LIKE '%task%'`.
2. Confirm it published — `published_at IS NOT NULL`.
3. If both are true, the gap is the **alert leg**, not the bus. Wax needs its own
   ntfy topic with first-failure-per-(slug, reason_code) debouncing, kept fail-open
   so an alert failure can never break a recording.

Narrowing the toaster's `SUBJECT_FILTER` touches shared infra at
`~/code/33GOD/bloodbank` and affects other consumers — treat it as a separate
change, not part of a Wax fix.

## Subjects

`bloodbank.evt.audio.*` in flow order: `session.started` →
(`session.ended` | `session.failed` | `session.canceled`) → `file.recorded` →
`file.sent` → `transcription.started` →
(`transcription.completed` | `transcription.failed`) →
`task.requested` + `task.started` → (`task.completed` | `task.failed`) per pass.
Plus `status.updated` on every edge and `heartbeat.recorded` every 60 s.

`command_id` / `idempotency_key` are `uuid5(WAX_NS, f"ep:{item_id}:{slug}:{attempt}")`
— deterministic, which is why a manual re-run must pass an incremented `attempt`
rather than replaying attempt 1.
