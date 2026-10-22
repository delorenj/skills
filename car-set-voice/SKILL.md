---
name: car-set-voice
description: "Use when the driver (or an operator) wants the in-car desk to
  speak a tile's replies in another vox voice: sets the per-agent car reply
  voice, persisted across restarts, car only (the agent's Telegram/Hermes voice
  is untouched)."
metadata:
  tool:
    contract: tool.json
    entrypoint: scripts/set_voice.py
    effect: writes-desk-prefs
    consumers: [car-desk]
---

# car-set-voice

Sets the voice the Holocene car desk (the voice-memo watcher, `services/inbox-watcher` in the holocene repo, HOLOC-23)
speaks one tile's replies in. One tile is one agent (`holocene-pm`, `flume-pm`, ...). The setting is per agent, survives
restarts, and applies from the next reply, with no restart. It is car only: the agent's Telegram / Hermes TTS voice
(`tts.voice` in its profile delta) is not touched.

## Who calls it

- **The car desk** (consumer `car-desk`): the watcher loads `tool.json` from its Skillex scope
  (`~/.local/state/holocene-auto/car-desk-scope/.agents/skills/`), offers it to the fast model as the `car_set_voice`
  tool, validates the model's arguments against the schema and runs the entrypoint (no shell, 3 s timeout). The phrases
  "use walken voice", "switch the voice to Morgan Freeman", "reset the voice" run it with no LLM call. The driver hears
  the result in the new voice ("Switched Holocene PM to Walken.").
- **An operator or another agent**: run the script directly, or the watcher's own verb
  `mise -C ~/code/33GOD/holocene run memo:voice <agent> <voice>`.

## Run it

```bash
scripts/set_voice.py --json --agent holocene-pm --voice walken      # by name
scripts/set_voice.py --json --agent holocene-pm --voice "walken two" # walken2
scripts/set_voice.py --json --agent holocene-pm --voice "Morgan Freeman"
scripts/set_voice.py --json --agent holocene-pm --voice default     # back to MEMO_VOX_VOICE (rick)
scripts/set_voice.py --json --list                                  # the valid voices
```

Valid voices are what `voxxy -q voice list --json` lists (12 on 2026-10-22: brule carlin damian david dumply marge morgan
morty peter rick walken walken2). A name, a display name, a display name's unique first or last word (`freeman`), or a
name with its digits spoken (`walken two`) all resolve. Anything else is refused (exit 3) and nothing is written.

## Contract

- `tool.json`: an OpenAI function object, `car_set_voice(voice: string)`.
- stdout: one JSON object, `{"ok": true, "agent", "voice", "display_name", "spoken", "cleared"}` or
  `{"ok": false, "error", "valid"?}`.
- Exit codes: 0 done, 2 bad arguments, 3 refused (unknown voice), 1 failed (the writer or vox's list could not be reached).
- Effect: the script writes through the watcher's own verb, `memo_trace.py voice <agent> <voice> --json --by <by>`, which
  sets `tiles.<agent>.voice` in `~/.local/state/holocene-auto/inbox-watcher/converse.json` under an fcntl lock (the
  watcher writes the same file). It never edits that file itself and holds no key.
- Environment: `HOLOCENE_MEMO_TRACE` (path of `memo_trace.py`, default
  `~/code/33GOD/holocene/services/inbox-watcher/memo_trace.py`); `MEMO_VOX_URL` when set names the vox whose
  `GET /voices` is the list (the watcher's tests); `MEMO_STATE_DIR` is passed through to the verb.

## What the watcher does with it

It locks the voice per reply at the first render (chunks and retries never switch), and if vox ever answers "voice not
found" for it, falls back to the default voice at once (no 30-minute TTS retry) and reports `voice` (used) and
`voice_requested` on the `voiced` / `replied` facts. `mise run memo:converse status` and the heartbeat show each tile's
voice.
