# Claude Code → Bloodbank v3 Event Publishing

Use this when adding new event types that Claude Code itself should emit
to the v3 event bus, or when extending the existing `agent.*` payloads.

## Trigger phrases

- "Claude Code should publish ..."
- "add a new agent.* event"
- "hook event for ..."
- "tell bloodbank when Claude Code does X"

## Architecture (load this fully before editing)

```
Claude Code hook (PostToolUse / Stop / SessionStart / Notification / ...)
    → .claude/hooks/bloodbank-publisher.sh <event-type>   (stdin: hook JSON)
        → builds CloudEvents 1.0 envelope (cloudevent_base.v1.json)
        → POST http://localhost:3503/v1.0/publish/bloodbank-v3-pubsub/event.agent.<type>
            → daprd-heartbeat sidecar (host:3503 → container:3500)
                → NATS JetStream stream BLOODBANK_V3_EVENTS
                    → subject event.agent.<entity>.<action>
```

Key invariants:

- Publish target is a Dapr sidecar, not the v2 RabbitMQ HTTP API.
- `daprd-claude-events` (host:3503) is the canonical publish target.
  The producer (Claude Code on the host) and consumer
  (claude-events-recorder) are wired through the same sidecar.
- Hook MUST be best-effort: silent no-op + size-rotated error log when
  the sidecar is unreachable. Never fail the hook (Claude Code surfaces
  stderr as an error).
- claude-flow is BANNED. Strip any `npx claude-flow@alpha hooks ...`
  entries from `.claude/settings.json` on sight.

## Files in scope

- `~/code/33GOD/.claude/settings.json` — hook registration + env
- `~/code/33GOD/.claude/hooks/bloodbank-publisher.sh` — the publisher
- `~/code/33GOD/.claude/hooks/README.md` — operator-facing docs
- `~/code/33GOD/holyfields/schemas/agent/<entity>.<action>.v1.json` — schema (when authoring v3 versions)
- `~/code/33GOD/bloodbank/compose/v3/docker-compose.yml` — publish target sidecar

## Recipe: add a new agent event

### 1) Choose the contract

| Decision | Rule |
|---|---|
| CloudEvents `type` | `agent.<entity>.<action>` (past-tense action) |
| NATS subject | `event.<type>` → `event.agent.<entity>.<action>` |
| `subject` field | `agent/<session_id>[/<entity>/<id>]` |
| `domain` field | `agent` (constant for this family) |
| `producer` / `service` | `claude-code` |
| `source` URN | `urn:33god:agent:claude-code` |

### 2) Author the schema (optional for first pass)

The current publisher emits inline-built envelopes. Schemas under
`holyfields/schemas/agent/` are still v2-shaped (extend
`base_event.v1.json`). Authoring a v3 schema (extends
`_common/cloudevent_base.v1.json`) is best done as a separate PR.

If authoring now: copy `holyfields/schemas/system/heartbeat.tick.v1.json`
as a template. Lock `type` and `domain` via `const`. Seal the `data`
block with `additionalProperties: false`. Add tests under
`holyfields/tests/test_<event>.py` mirroring `test_heartbeat_tick.py`.

### 3) Add the handler in the publisher

Edit `.claude/hooks/bloodbank-publisher.sh`. Pattern:

```bash
handle_<entity>_<action>() {
    local input="$1"
    local session_data; session_data=$(load_session)
    local session_id;   session_id=$(echo "$session_data" | jq -r '.session_id')

    # Extract whatever you need from $input (the hook stdin JSON).
    local data
    data=$(jq -cn \
        --arg session_id "$session_id" \
        --arg foo "$(echo "$input" | jq -r '.foo // ""')" \
        '{ session_id: $session_id, foo: $foo }')

    local envelope
    envelope=$(build_envelope \
        "agent.<entity>.<action>" \
        "agent/$session_id" \
        "$data" \
        "$session_id")
    publish "event.agent.<entity>.<action>" "$envelope"
}
```

Wire into the `case` statement in `main()`:

```bash
<event-type>) handle_<entity>_<action> "$input" ;;
```

### 4) Register the hook

Edit `.claude/settings.json` under `hooks.<HookName>`:

```json
{
  "hooks": {
    "<HookName>": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "cat | .claude/hooks/bloodbank-publisher.sh <event-type>",
            "description": "Publish ..."
          }
        ]
      }
    ]
  }
}
```

Available Claude Code hook events: `SessionStart`, `UserPromptSubmit`,
`PreToolUse`, `PostToolUse`, `Stop`, `Notification`, `PreCompact`,
`SessionEnd`. Pick the one whose semantics match the event you're
emitting.

### 5) Verify end-to-end

Bring up the publish target if it's not already running:

```bash
docker compose --project-name bloodbank-v3 \
  --profile claude-events \
  -f bloodbank/compose/v3/docker-compose.yml \
  up -d nats nats-init dapr-placement claude-events-recorder daprd-claude-events

until curl -sf --max-time 2 http://localhost:3503/v1.0/healthz >/dev/null; do sleep 2; done
```

Fire the hook manually with a representative payload, then read it
back from JetStream:

```bash
echo '{...representative hook stdin...}' | \
  BLOODBANK_DEBUG=true .claude/hooks/bloodbank-publisher.sh <event-type>
# expect: published ok (http=204)

docker run --rm --network bloodbank-v3-network natsio/nats-box:0.14.5 \
  nats --server nats://nats:4222 stream subjects BLOODBANK_V3_EVENTS

docker run --rm -i --network bloodbank-v3-network natsio/nats-box:0.14.5 \
  nats --server nats://nats:4222 sub 'event.agent.<entity>.<action>' \
  --count=1 --last-per-subject --raw
```

Confirm the envelope shape matches `cloudevent_base.v1.json`: all of
`specversion`, `id`, `source`, `type`, `subject`, `time`,
`datacontenttype`, `correlationid`, `producer`, `service`, `domain`,
`schemaref`, `traceparent`, `data`.

### 6) Verify sidecar-down path

Bring v3 down and re-fire. Hook MUST exit 0. Check the error log:

```bash
docker compose --project-name bloodbank-v3 -f bloodbank/compose/v3/docker-compose.yml down
echo '{...}' | .claude/hooks/bloodbank-publisher.sh <event-type>; echo "exit=$?"
tail -3 .claude/sessions/publish-errors.log
```

Expected: `exit=0`, error log captures `http=000` line, no stderr noise.

## Recipe: extend an existing payload

1. Edit the matching `handle_*` function in
   `.claude/hooks/bloodbank-publisher.sh` to add new `data` fields.
2. If a v3 schema exists, add the field there with appropriate type +
   `required` membership. If only the v2 schema exists, add the field
   to your TODO list for the schema-migration PR.
3. Re-run the verify step (5) and confirm the new field appears in
   the envelope.

## Common pitfalls

- **Hook fails Claude Code session**: you wrote to stderr or returned
  non-zero. The publisher MUST exit 0. Use `log_error_once()` to
  append to the rotated log file instead of stderr.
- **HTTP 404 from Dapr**: pubsub component name typo. Confirm
  `BLOODBANK_PUBSUB` env is `bloodbank-v3-pubsub` and matches
  `compose/v3/components/pubsub.yaml`.
- **HTTP 500 from Dapr**: NATS-side error. Check
  `docker logs bloodbank-v3-daprd-claude-events` for the actual reason
  (most often: stream not yet created, or subject doesn't match
  `BLOODBANK_V3_EVENTS` subjects pattern `event.>`).
- **Envelope rejected by downstream consumer**: missing 33GOD
  extensions. The publisher's `build_envelope()` populates them all;
  if you bypass it, ensure `correlationid`, `producer`, `service`,
  `domain`, `schemaref` are present.

## Out of scope (for now)

- Strict schema validation **at publish time** (the publisher emits
  inline-built envelopes). The Holyfields CI gate validates schemas and
  the heartbeat round-trip; agent.* schema gating shipped under V3-110
  but is not invoked from the publisher itself.

## Reference

- Publisher: `~/code/33GOD/.claude/hooks/bloodbank-publisher.sh`
- README: `~/code/33GOD/.claude/hooks/README.md`
- Envelope schema: `~/code/33GOD/holyfields/schemas/_common/cloudevent_base.v1.json`
- Pattern reference (other producer): `~/code/33GOD/bloodbank/services/heartbeat-tick/main.py`
- ADR: `~/code/33GOD/docs/architecture/ADR-0001-v3-platform-pivot.md` (amended by ADR-0002)
