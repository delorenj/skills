# Hooks — gotchas

Each gotcha: **Symptom**, **Cause**, **Fix**, **Prevention**.

## 1. "Hooks fire but nothing reaches NATS"

**Symptom.** Manually piping a payload to the publisher exits 0, but no toast appears and no NATS subscription sees it.

**Cause.** Publisher is failing open on a connection error — the script swallowed the failure to protect the harness.

**Fix.** Re-run with `BLOODBANK_HOOK_STRICT=1` to surface the real error: `BLOODBANK_HOOK_STRICT=1 BLOODBANK_HOOK_VERBOSE=1 echo '{}' | python3 publisher.py sessionStart`. Likely: NATS container not running, wrong host/port, firewall.

**Prevention.** Add a strict-mode CI smoke test that talks to a known-good NATS.

## 2. "Hook works manually but not from inside the harness"

**Symptom.** Direct invocation publishes correctly; running the harness produces nothing.

**Cause.** Usually one of: (a) the harness can't find the hook config (wrong filename / dir), (b) the hook config's `bash` field uses a relative path that's invalid in the harness's cwd, (c) the hook is silently timing out.

**Fix.** Check the harness's logs for hook execution. Most CLIs log "hook timed out" or "hook command not found" at DEBUG. Use absolute paths in `bash`/`command` fields. Add `BLOODBANK_HOOK_VERBOSE=1` to confirm the publisher ran.

**Prevention.** Always absolute-path the publisher in the hook config. Never `cd` then `python`.

## 3. "Hook script slows down the agent"

**Symptom.** Visible lag after each tool call when hooks are enabled.

**Cause.** Publish path is slow — DNS, TLS, HTTPS, or a missing NATS forcing the timeout to fire on every call.

**Fix.** Profile: `time printf '{"x":1}' | python3 publisher.py preToolUse` should be < 50ms. If higher, switch from HTTP to NATS direct on `127.0.0.1`, or lower `BLOODBANK_NATS_TIMEOUT`.

**Prevention.** Default to stdlib NATS TCP on localhost. Never put the publish path through DNS or TLS for hot-path hooks.

## 4. "preToolUse fires but postToolUse doesn't, or vice versa"

**Symptom.** Half the tool-use lifecycle shows up; the other half is missing.

**Cause.** The harness's `*ToolUse` events are split across separate hook entries. Adding `preToolUse` to a config doesn't add `postToolUse`.

**Fix.** List every hook explicitly in the config file. See `services/copilot-hooks/hooks.json` for the 7-hook reference shape.

**Prevention.** Lint the hook config by enumerating expected vs present keys. A script in CI is fine.

## 5. "Hookd daemon silently exits"

**Symptom.** Claude Code events stop arriving; nothing in `event-toaster`.

**Cause.** The Rust daemon panicked or the Unix socket got rmed.

**Fix.** Restart from `~/code/33GOD/hookd/` with `cargo run`. Check journalctl / systemd unit if you've set one up. Look at `hookd/src/main.rs` for the recent panic site.

**Prevention.** Run the daemon under a supervisor (systemd-user-unit, runit, etc.) so it auto-restarts.

## 6. "I get duplicate session.started events on every Claude Code session"

**Symptom.** `event.agent.session.started` arrives twice per real session.

**Cause.** Claude Code can emit both `SessionStart` and `Stop` → `SessionStart` (when restarted). Combined with hookd's enrichment that adds a session_id, you may see two with different IDs.

**Fix.** Consumers should dedupe on the envelope `id` (UUID) or treat `session_id` changes as a legitimate new session.

**Prevention.** Document this in your consumer; don't try to fix it on the producer side.
