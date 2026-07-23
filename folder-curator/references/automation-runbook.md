---
pipeline-status: new
---
# Automation runbook — the hands-off curation pipeline

Wire the hands-off path: a file lands in a curated directory → it's announced on Bloodbank →
drained one-at-a-time to n8n → curated by the `folder-curator` CLI → the outcome is emitted
back on Bloodbank. Envelope/subject/schema rules belong to `bloodbank-integration`; node
boundaries to `delonet-n8n-architecture`; this file is the curator-specific wiring.

## Topology

Atomic nodes, one reversible responsibility each; the bus provides backpressure so the
workflow is never overloaded and files drain in order.

```
[file lands in a curated dir]  (e.g. client_dropbox/ — via the inbound Drive pull → drive-sync.md)
        │  announce: bb-emit curator.file.received   (one per file not in .curator/ledger.json)
        ▼
  bloodbank.evt.v1.curator.file.received   ── retained by BLOODBANK_EVENTS (JetStream, evt.v1.>)
        │
[curator-drain]  nats-py durable · manual_ack · max_ack_pending=1     (assets/curator-drain.py)
        │  POST envelope → n8n webhook; ACK only on HTTP 2xx  (exactly one in flight)
        ▼
[n8n: "Folder Curator Intake"]   (https://n8n.delo.sh · PM2 :5678 · availableInMCP)
  Webhook ─▶ Exec: folder-curator plan ─▶ Exec: folder-curator apply ─▶ Respond(plan JSON)
        │                                          │
        │                                   ┌──────┴───────┬─────────────────┐
        │                              route │   keep/low-conf │      (apply error)
        ▼                                    ▼                 ▼                ▼
  emit curator.file.routed                       emit curator.file.flagged   emit curator.file.failed
        └──────────────────────── bloodbank ──────────────────────────────────┘
                                     → event-toaster → ntfy + every other consumer
```

Invariant: the workflow routes files **out** of the watched dir into their category home
(`threads/`, `workshop/`) or leaves low-confidence items in the review queue. It never writes
into a subdir of the watch root, and it is **bus-fed** (webhook), not `localFileTrigger`-fed —
`apply` rewrites review-queue items in place, which would re-fire a file trigger forever.

## 1. Schema-first events — DONE

The `curator` domain is registered and the four event schemas exist and validate. What landed:

- **Domain** `curator` added to `docs/event-naming.md` §6 **and** the runtime allowlist
  `services/agent-hooks/core/validate.py` (`ALLOWED_DOMAINS`). Action `routed` added to §8.1
  and `EVENT_ACTIONS`. Entity `file` broadened to pair with `curator`.
- **Schemas** under `bloodbank/schemas/bloodbank/v1/curator/`:
  `file.received.v1.json`, `file.routed.v1.json`, `file.flagged.v1.json`, `file.failed.v1.json`
  (each `allOf`-extends `_common/cloudevent_base.v1.json`; `type`/`kind`/`domain` consts pinned).
- **Verified:** `mise run validate:schemas` (tree), `mise run smoketest:schema-contract-consistency`
  (every declared type passes the runtime validator), `mise run smoketest:bloodbank-naming`.
- **Retention:** `BLOODBANK_EVENTS` already filters `bloodbank.evt.v1.>` — curator events are
  retained with **no `compose/nats/streams.json` change**.

The event set and their `data` (model payloads on the schema files, not this sketch):

| Type (`bloodbank.v1.` +) | When | Key `data` |
|---|---|---|
| `curator.file.received` | a file appeared in a curated dir (announce) | `file_path`, `file_hash_sha256`, `curated_dir` |
| `curator.file.routed`   | file classified + placed (after `apply`) | `file_path`, `destination`, `category`, `kind`, `confidence` |
| `curator.file.flagged`  | parked for review (0 or >1 category match; or a quarantined secret) | `file_path`, `reason`, `confidence`, `purpose` |
| `curator.file.failed`   | a curation step failed (error branch) | `file_path`, `stage`, `error` |

Subject = type with `evt` inserted: `bloodbank.evt.v1.curator.file.<action>`. `ordering_key`
= `file:<sha256(file_path)>` so re-detections of one artifact share a bucket.

## 2. Announce producer

The inbound Drive pull is the only producer of `curator.file.received`. After each `rclone
copy`, `sync-jim-dropbox-from-drive.sh` emits one `received` per file whose content-hash is
not already in `.curator/ledger.json`, via `~/.local/bin/bb-emit`. Full script + ledger-diff →
[drive-sync.md](./drive-sync.md). Keep `ordering_key`/`correlationid` derived from the file's
sha256 so the lifecycle (`received → routed`/`flagged`/`failed`) for one file stitches together.

## 3. Orderly draining (backpressure) — `assets/curator-drain.py`

A small host-side JetStream **durable** consumer drains ONE event at a time and POSTs it to the
n8n webhook, ack-ing only on HTTP 2xx (`manual_ack`, `max_ack_pending=1`, subject
`...curator.file.received` only — never the workflow's own outputs, which would loop). This is
the "fed by the bus, can't be overloaded, drains in order" mechanism. The daemon ships at
`assets/curator-drain.py` (PEP-723 uv, nats-py). Deploy:

```bash
# from the skill root:
ln -sfn "$(realpath assets/curator-drain.py)" ~/.local/bin/curator-drain
cat > ~/.config/systemd/user/curator-drain.service <<'UNIT'
[Unit]
Description=Bloodbank -> n8n folder-curator drain (one-in-flight backpressure)
Wants=network-online.target
After=network-online.target
[Service]
Type=simple
Environment=CURATOR_WEBHOOK=http://127.0.0.1:5678/webhook/folder-curator-intake
ExecStart=%h/.local/bin/curator-drain
Restart=always
RestartSec=5
Nice=10
[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload && systemctl --user enable --now curator-drain.service
```

Do not enable it until the n8n workflow exists and its webhook path is confirmed.

## 4. n8n workflow — "Folder Curator Intake"

Built **inactive** via n8n-mcp `create_workflow_from_code` (`settings.availableInMCP: true`),
webhook path `folder-curator-intake`. Atomic nodes:

1. **Webhook** — receives the `curator.file.received` envelope; a Set/Code node derives
   `clientRoot` (`data.curated_dir`) and `filePath` (`data.file_path`).
2. **Execute Command — plan:** `/home/delorenj/.local/bin/folder-curator --client-root "<clientRoot>" plan "<filePath>"`; parse the JSON.
3. **Execute Command — apply:** same with `apply` (idempotent via the content-hash ledger — safe on webhook redelivery).
4. **Branch** on `action`/`confidence` → emit `curator.file.routed` (route) / `curator.file.flagged` (keep, low-confidence, or quarantined secret) via `Execute Command` piping `data` into `bb-emit`.
5. **Error branch** off the apply node → `curator.file.failed` (stage + message).
6. **Respond to Webhook** with the plan JSON — so the same endpoint fulfils the synchronous "file path in → destination out" contract.

Use the **absolute** CLI path in Execute Command (n8n's PATH excludes `~/.local/bin`). Cutover
(activate + point the drain at it) is a deliberate later step; don't refactor a live daily
workflow in place. Tags/long descriptions need a direct `PUT /api/v1/workflows/{id}` (the MCP
tool drops them).

## 5. The custom node — `n8n-nodes-folder-curator` (service-client)

Per delonet-n8n-architecture's escalation ladder, the Execute-Command-CLI rung is transitional.
The promoted node runs its logic **in-process in `execute()`** — but the engine is a non-trivial
Python program, so reimplementing it in TypeScript would fork the source of truth and invite
drift. Instead this uses the skill's sanctioned **service-client** pattern (the same one
`n8n-nodes-transcribe` uses for the faster-whisper Python pipeline): the engine is exposed over
HTTP by `folder-curator serve`, and the node is a thin in-process HTTP client
(`this.helpers.httpRequest`) — it never shells out, and there is exactly ONE engine.

- **Service:** `folder-curator serve --host 127.0.0.1 --port 8787` — `POST /plan`, `POST /apply`
  with `{"file","client_root"}`, `GET /health`. Runs as systemd `curator-serve.service`.
- **Node package:** `/home/delorenj/code/n8n-nodes-folder-curator/`, cloned from the
  `n8n-nodes-hermes` scaffold; node `Folder Curator` with `operation` (plan/apply), `filePath`,
  `clientRoot`, `serviceUrl` (default `http://127.0.0.1:8787`). Installed into `~/.n8n/nodes`;
  restart n8n with `PM2_HOME=/home/delorenj/.pm2` + the node-dir `pm2` (the mise shim is broken).
- **Cutover:** swap the workflow's two `Execute Command` nodes (plan, apply) for the Folder
  Curator node (operation plan, then apply). The Execute-Command rung stays a valid fallback.

## 6. Gotchas

- **Bus-fed, not file-triggered.** A `localFileTrigger` on the watched dir would re-fire on
  `apply`'s in-place edits. The drain is the trigger; the ledger dedup is the redelivery backstop.
- **MCP refuses the workflow** unless `settings.availableInMCP: true`.
- **Tags / >255-char descriptions** are dropped via the MCP tool — use the direct REST API.
- **n8n "up" check:** `curl -sf localhost:5678/healthz`, not PM2 status (PM2 shows `online` even
  when the HTTP server has died).
- **bb-emit for pipeline events only via NATS-direct** — never the HTTP `/publish` path
  (v2/RabbitMQ; the v3 toaster and JetStream consumers never see it).
