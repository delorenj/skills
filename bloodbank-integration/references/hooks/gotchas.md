# Hooks — gotchas

Each gotcha: **Symptom**, **Cause**, **Fix**, **Prevention**.

## 1. "Hooks fire but nothing reaches NATS"

**Symptom.** Manually piping a payload to the publisher exits 0, but no toast appears and no NATS subscription sees it.

**Cause.** Publisher is failing open on a connection error — the script swallowed the failure to protect the harness.

**Fix.** Re-run with `BLOODBANK_HOOK_STRICT=1` to surface the real error, using the canonical publisher:
`printf '{}' | BLOODBANK_HOOK_STRICT=1 BLOODBANK_HOOK_VERBOSE=1 python3 ~/.agents/hooks/bloodbank/publish.py --client copilot --hook sessionStart`. Likely: NATS container not running, wrong host/port, firewall.

**Prevention.** Add a strict-mode CI smoke test that talks to a known-good NATS.

## 2. "Hook works manually but not from inside the harness"

**Symptom.** Direct invocation publishes correctly; running the harness produces nothing.

**Cause.** Usually one of: (a) the harness can't find the hook config (wrong filename / dir), (b) the hook config's `bash` field uses a relative path that's invalid in the harness's cwd, (c) the hook is silently timing out.

**Fix.** Check the harness's logs for hook execution. Most CLIs log "hook timed out" or "hook command not found" at DEBUG. Use absolute paths in `bash`/`command` fields. Add `BLOODBANK_HOOK_VERBOSE=1` to confirm the publisher ran.

**Prevention.** Always absolute-path the publisher in the hook config. Never `cd` then `python`.

## 3. "Hook script slows down the agent"

**Symptom.** Visible lag after each tool call when hooks are enabled.

**Cause.** Publish path is slow — DNS, TLS, HTTPS, or a missing NATS forcing the timeout to fire on every call.

**Fix.** Profile: `time printf '{"x":1}' | python3 ~/.agents/hooks/bloodbank/publish.py --client copilot --hook preToolUse` should be < 50ms. If higher, verify the local NATS path on `127.0.0.1`, or lower `BLOODBANK_NATS_TIMEOUT`.

**Prevention.** Default to stdlib NATS TCP on localhost. Never put the publish path through DNS or TLS for hot-path hooks.

## 4. "preToolUse fires but postToolUse doesn't, or vice versa"

**Symptom.** Half the tool-use lifecycle shows up; the other half is missing.

**Cause.** The harness's `*ToolUse` events are split across separate hook entries. Adding `preToolUse` to a config doesn't add `postToolUse`.

**Fix.** List every hook explicitly in `hooks.master.json` and regenerate. See `services/agent-hooks/copilot/hooks.json` for the generated 7-hook reference shape.

**Prevention.** Lint the hook config by enumerating expected vs present keys. A script in CI is fine.

## 5. "Health check says Bloodbank commands are foreign or missing"

**Symptom.** `health/hook_healthcheck.py --check` reports Bloodbank commands as `foreign`, or says `~/.agents/hooks/bloodbank/publish.py` is missing/non-executable even though configs look right.

**Cause.** The deployed command shape changed but the classifier/marker logic did not, or the canonical hook mount was not installed. The health checker must understand `--client ... --hook ...` and match `bloodbank/publish.py`, not just old `<agent>/publish.py` paths.

**Fix.** Run `cd ~/code/33GOD/bloodbank && python3 services/agent-hooks/sync.py --install`, confirm `readlink -f ~/.agents/hooks/bloodbank`, and rerun `BLOODBANK_ENABLED=false python3 services/agent-hooks/health/hook_healthcheck.py --check`.

**Prevention.** Keep installer markers specific: canonical `bloodbank/publish.py` plus explicit legacy markers (`claude/publish.py`, `codex/publish.py`, etc.) for migration.

## 6. "I get duplicate session.started events on every Claude Code session"

**Symptom.** `bloodbank.evt.agent.session.started` arrives twice per real session.

**Cause.** Claude Code can emit both `SessionStart` and a later restart/start path. The adapter self-roots each new session chain, so different session IDs may represent real new sessions.

**Fix.** Consumers should dedupe on the envelope `id` (UUID) or treat `session_id` changes as a legitimate new session.

**Prevention.** Document this in your consumer; don't try to fix it on the producer side.
