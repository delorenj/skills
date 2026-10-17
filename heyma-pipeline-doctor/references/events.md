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

**The bus works. Delivery has never been the problem; the problem has been
that nothing a human reads was subscribed to Wax failures.**

`passes.py` emits a proper `task.failed` event on every pass failure, and those
events were published successfully and archived in Candystore throughout the
five-day title-slug outage. Nobody was watching.

What exists now, and what still doesn't:

- **`bloodbank.audio.task.exhausted` is the deliberate notification path.** A
  pass that exhausts its attempt budget fires it once per (item, slug,
  version), and ntfy-router routes it like any other non-muted event. A
  transient failure that heals on the sweep never pages; a dead one does.
- **`notify_stage_failure`** puts a dead sub-stage on the desktop directly.
- The measured noise problem stands as context (2026-09):
  `bloodbank-event-toaster` forwards **every** `bloodbank.evt.>` envelope to
  `ntfy.delo.sh/bloodbank` at priority 5 — **20,327 toasts in 24 h, 95.9 % of
  them `agent.tool.*`**. A signal placed in that topic is destroyed by the
  noise, which is why the exhaustion signal is its own event type.

So when triaging "why wasn't I told":

1. Was the failure *exhausting* (final attempt) or did it heal on a later
   sweep? Only exhaustion is designed to page.
2. Confirm the event was emitted — `SELECT * FROM outbox WHERE subject LIKE '%task%'`.
3. Confirm it published — `published_at IS NOT NULL`.
4. If both are true, the gap is the **alert leg** (routing/muting), not the bus.

Narrowing the toaster's `SUBJECT_FILTER` touches shared infra at
`~/code/33GOD/bloodbank` and affects other consumers — treat it as a separate
change, not part of a Wax fix.

## Subjects and ordering — read before concluding "wrong order"

`bloodbank.evt.audio.*` in capture/flow order: `session.started` →
(`session.ended` | `session.failed` | `session.canceled`) → `file.recorded` →
`file.sent` → `transcription.started` → … then the enrichment layer:

- **Per-pass command events**: each executed pass mints a deterministic
  command id `uuid5(WAX_NS, "ep:<item>:<slug>:<attempt>")`, issues
  `bloodbank.cmd.audio.task.start` (mirrored as `task.requested`), then
  `task.started` and `task.completed|failed|skipped`, correlated on that id.
  A `dependency_failed` gate or a `when`/`skip_when` skip issues **none** of
  these — no command ran.
- **Pass events publish early by design.** A completed pass's declared events
  (e.g. `ticketable`'s `intake.detected` per ticket) are enqueued as soon as
  that pass's own `requires` subgraph completes — they may legitimately appear
  in the outbox *before* `transcription.completed`, correlated on the pass's
  command id until a completion event id exists. A wedged sibling no longer
  withholds them.
- **`transcription.completed` is plan-gated**: one envelope per plan, written
  only when every planned pass is `completed`/`skipped`, with every pass result
  attached. Ids are `uuid5(WAX_NS, "completion:<item>:<plan_id>")`; pass-event
  ids are `uuid5(WAX_NS, "ep-event:<item>:<slug>:<type>:<key>")`, so re-plans
  and backfills never duplicate.
- **`bloodbank.audio.task.exhausted`** is the dead-letter signal: a pass that
  fails its final permitted attempt fires it exactly once per
  (item, slug, version). If you are asking "why wasn't I told", look for this
  event first.

Plus `status.updated` on every edge and `heartbeat.recorded` every 60 s.

A manual `wax ep run` re-run gets a fresh `attempt` in its command id — that
determinism is why attempts increment instead of replaying.
