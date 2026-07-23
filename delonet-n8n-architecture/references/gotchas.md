# n8n instance facts + gotchas

Read this before editing a workflow programmatically or wiring file triggers /
archive steps / credentials. Each entry: **Symptom → Cause → Fix → Prevention.**

## Instance facts

- **Service:** n8n is PM2-managed (`pm2 restart n8n` / `pm2 logs n8n`), running the
  mise-installed node binary on port `5678`, cwd `~/.n8n`. Custom nodes live in
  `~/.n8n/nodes`; restart to load a newly-installed node.
- **Ingest paths:** `~/audio/inbox` (Syncthing `receiveonly`, versioned — never let
  a local writer add files here) and `~/audio/ingest` (plain local). Both watched by
  the transcribe workflow.

## localFileTrigger re-fires forever

- **Symptom:** a workflow triggers in an infinite loop; the same file reprocesses endlessly.
- **Cause:** the archive/move target is a **subdirectory of the watched folder**, so
  writing the archived copy fires the `add` trigger again.
- **Fix:** archive off-filesystem (S3) or to a **sibling outside the watch root**
  (e.g. `~/audio/processed/`, next to `~/audio/inbox/`, not inside it).
- **Prevention:** treat "archive destination ∉ watch root" as an invariant when
  designing any file-triggered workflow.

## n8n MCP tools refuse the workflow

- **Symptom:** `update_workflow` / `get_workflow_details` error: *"Workflow is not
  available in MCP. Enable MCP access in workflow settings."*
- **Cause:** `settings.availableInMCP` is false/absent.
- **Fix:** `GET /api/v1/workflows/{id}`, set `settings.availableInMCP: true`, `PUT`
  it back.
- **Prevention:** set `availableInMCP: true` in `settings` on every workflow meant
  to be MCP-managed.

## Tags / long descriptions silently dropped via MCP

- **Symptom:** tags don't stick; workflow description truncates.
- **Cause:** the MCP `update_workflow` tool caps `description` at 255 chars and
  ignores tags entirely; the list endpoint omits `description`.
- **Fix:** use the direct API — `PUT /api/v1/workflows/{id}` with the envelope
  `{name, nodes, connections, settings}` (NOT the full GET document); manage tags
  and rich descriptions there.
- **Prevention:** for richer-than-trivial metadata, script against the REST API,
  not the MCP tool.

## AWS/S3-typed credential rejected

- **Symptom:** saving an AWS-typed credential with a custom endpoint (for
  `s3.delo.sh`) fails validation.
- **Cause:** when `customEndpoints=true`, the schema requires **all** endpoint
  fields present — `rekognitionEndpoint, lambdaEndpoint, snsEndpoint, sesEndpoint,
  sqsEndpoint, s3Endpoint, ssmEndpoint` — even if empty.
- **Fix:** supply every `*Endpoint` field (empty string is accepted) alongside
  `s3Endpoint`.
- **Prevention:** prefer `n8n-nodes-minio` (or a custom `n8n-nodes-delo-minio`) for
  delo S3 — it sidesteps the AWS cred schema entirely.

## PM2 says "online" but n8n is dead

- **Symptom:** PM2 shows n8n `online` for hours, but the UI/API is unreachable (no
  TCP listener on 5678).
- **Cause:** the HTTP server crashed silently while the Node event loop survived on
  background workers; PM2 only checks `kill -0 PID`, not port binding.
- **Fix:** `pm2 restart n8n`; confirm with `curl -sf localhost:5678/healthz` or a
  port check, not PM2 status alone.
- **Prevention:** health-check the **port**, not the process, when judging n8n up.

## A node's hardcoded repo path breaks after a move

- **Symptom:** every run of a script-backed node fails after a repo is relocated.
- **Cause:** an absolute repo path baked into the node/script (HeyMa moved
  `code/33GOD/HeyMa` → `code/HeyMa` and silently broke transcription for two weeks).
- **Fix:** self-locate — derive the repo dir from the script's own realpath, or pass
  it as a node parameter/env var.
- **Prevention:** never hardcode a repo path in a node or the scripts it calls; the
  `bin/transcribe` self-locating pattern is the reference.

## Activating/deactivating a workflow from the CLI

- **Symptom:** `n8n update:workflow --id=X --active=true` prints "Please use:
  publish:workflow" and does nothing; or a flag flips in the DB but the running
  instance still fires the old triggers.
- **Cause:** in n8n 2.x, `update:workflow --active` is deprecated for activation
  (deactivation still works); activation is `publish:workflow`. And CLI writes hit the
  sqlite DB, but the running server caches active workflows + trigger registrations.
- **Fix:** `n8n unpublish:workflow --id=<old>` + `n8n publish:workflow --id=<new>`,
  then restart n8n so triggers reload. Verify with the API (`active` field), not the
  CLI's optimistic message.
- **Prevention:** treat activation as DB-write + restart; confirm via API afterward.

## `pm2` from a fresh shell can't see/restart n8n

- **Symptom:** `pm2 restart n8n` → rc 127 (command not found) or rc 1 / empty app
  list, even though n8n is running.
- **Cause:** n8n is managed by the PM2 **God Daemon under `PM2_HOME=/home/delorenj/.pm2`**;
  a non-interactive shell has `PM2_HOME` unset (points elsewhere), and the mise `pm2`
  shim errors ("Set a global default version") because no global node is pinned.
- **Fix:** invoke the real binary with the daemon's home:
  `PATH=/home/delorenj/.local/share/mise/installs/node/24.6.0/bin:$PATH
  PM2_HOME=/home/delorenj/.pm2 pm2 restart n8n`.
- **Prevention:** in any deploy hook that restarts n8n, set `PM2_HOME` and use the
  node-dir `pm2`, not the mise shim.
