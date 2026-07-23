#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["nats-py>=2.6"]
# ///
"""curator-drain — orderly, backpressured bridge from Bloodbank to the n8n Folder Curator workflow.

Subscribes as a JetStream DURABLE consumer to bloodbank.evt.v1.curator.file.received with
max_ack_pending=1, so exactly ONE file is in flight at a time: it POSTs each envelope to the
n8n webhook and ACKs only on HTTP 2xx. Under a burst it drains one-at-a-time (the bus is the
buffer, never the workflow); a failed POST is NAK'd for redelivery instead of being lost.
Deploy as a systemd --user unit (see references/automation-runbook.md).

Env:
  CURATOR_WEBHOOK   n8n webhook URL (required) — e.g. http://127.0.0.1:5678/webhook/folder-curator-intake
  NATS_URL          default nats://127.0.0.1:4222
  CURATOR_SUBJECT   default bloodbank.evt.v1.curator.file.received
  CURATOR_DURABLE   default curator-drain
"""
from __future__ import annotations

import asyncio
import os
import urllib.request

import nats
from nats.js.api import AckPolicy, ConsumerConfig

WEBHOOK = os.environ.get("CURATOR_WEBHOOK")
NATS_URL = os.environ.get("NATS_URL", "nats://127.0.0.1:4222")
SUBJECT = os.environ.get("CURATOR_SUBJECT", "bloodbank.evt.v1.curator.file.received")
DURABLE = os.environ.get("CURATOR_DURABLE", "curator-drain")


def _post(data: bytes) -> int:
    req = urllib.request.Request(
        WEBHOOK, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=180) as r:  # raises on connection error
        return r.status


async def main() -> None:
    if not WEBHOOK:
        raise SystemExit("CURATOR_WEBHOOK is required")
    nc = await nats.connect(NATS_URL, name=DURABLE, max_reconnect_attempts=-1)
    js = nc.jetstream()

    async def on_msg(msg) -> None:
        try:
            status = await asyncio.to_thread(_post, msg.data)
            if 200 <= status < 300:
                await msg.ack()  # only now is the next message delivered (max_ack_pending=1)
            else:
                await msg.nak(delay=30)
        except Exception:
            await msg.nak(delay=30)  # leave for redelivery; never ack a failed hand-off

    await js.subscribe(
        SUBJECT,
        durable=DURABLE,
        stream="BLOODBANK_EVENTS",
        cb=on_msg,
        manual_ack=True,
        config=ConsumerConfig(max_ack_pending=1, ack_policy=AckPolicy.EXPLICIT),
    )
    print(f"curator-drain: draining {SUBJECT} -> {WEBHOOK} (one in flight)", flush=True)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
