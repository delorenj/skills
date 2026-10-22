---
name: vox-voice-persona
description: Explain and operate the Hermes Voice Personality ("voice-persona") plugin for voxxy, and how a persona is associated with a voice at the voxxy level. Use when the user asks to make a voice talk like a character, "give peter/carlin/brule a personality", associate a persona with a voice, set or clear a voice's persona, write or edit a persona file, enable persona TTS enrichment for a Hermes agent/profile, dry-run an in-character rewrite, use `voxxy persona`, `voxxy voice persona`, or `voxxy speak --persona`, or debug "why does my agent not talk in character" / rejected rewrites / persona timeouts.
metadata:
  pipeline-status:
  - new
---

# vox-voice-persona

The voice-persona plugin rewrites the text that is about to be spoken **as a character would say it**
(Peter Griffin, George Carlin, Dr. Steve Brule, or any persona file) without losing a fact. One LLM
call, whole response at once, fail-open: on any problem the original text is spoken.

- Plugin + bundled personas: `~/code/voxxy/plugins/voice-persona/` (`README.md`, `__init__.py`, `personas/*.md`)
- Voice -> persona association lives on the voxxy server (`voices.persona`, `https://vox.delo.sh`)
- CLI: `voxxy persona ...`, `voxxy voice persona ...`, `voxxy speak --persona ...` (needs the `voxxy` CLI; see [vox-tts](../vox-tts/SKILL.md))

## Where it sits

```
response -> prepare_spoken_text -> transform_tts_text [voice-persona] -> prepare_spoken_text -> chunk -> TTS provider
```

Hermes fires the `transform_tts_text` hook inside `text_to_speech_tool`. The plugin is provider-agnostic
(vox, elevenlabs, edge...). The voxxy CLI loads the same module by file path, so
`voxxy persona rewrite` behaves exactly like the hook (same prompt, sanitizer and validator).

## Associate a persona with a voice (voxxy level)

```bash
voxxy voice persona peter peter-griffin   # associate
voxxy voice persona peter                 # show stored + effective persona and its source
voxxy voice persona peter none            # explicitly NO persona (also blocks the frontmatter fallback)
voxxy voice persona peter --clear         # unset (NULL): frontmatter `voices:` fallback applies again
voxxy voice list                          # Persona column
voxxy voice info peter                    # persona + effective (voxxy | frontmatter | none)
```

API: `PUT https://vox.delo.sh/voices/{name}/persona` with JSON `{"persona": "<slug>" | "none" | null}`
(API-key auth like every mutating endpoint). 404 unknown voice, 422 bad slug (`^[A-Za-z0-9][A-Za-z0-9_.-]*$`).
`GET /voices` and the MCP `list_voices_tool` return `persona`. Re-uploading a voice clip keeps its persona.
The server stores only the slug; it never reads persona files, so a slug with no file just resolves to nothing
(the CLI warns when setting a slug that is not bundled).

`voices.persona` semantics: `NULL` = unset, `none` = explicitly no persona, anything else = id of
`personas/<id>.md`.

### Resolution order (Hermes plugin)

1. profile `tts.persona.file`
2. profile `tts.persona.name`
3. **voxxy voice record** (`GET {base}/voices/{voice}`) - only when `auto_from_voice` is true (default), a voice is set,
   and the provider is `vox` or unspecified. `none` stops here with no persona.
4. persona-file frontmatter `voices: [peter]` (bundled: peter -> peter-griffin, carlin -> george-carlin, brule -> steve-brule)

Any voxxy lookup failure (network, 404, bad JSON, bad slug) logs once and falls through to 4. A voxxy slug whose
file is missing yields no persona (logged once), not a fallback. Results are cached in memory 60s per (base, voice),
so a change reaches a running gateway within about a minute with no restart.

## Enable it for a Hermes profile

1. Plugin symlink in the profile (per-profile, not global):
   `ln -s /home/delorenj/code/voxxy/plugins/voice-persona ~/.hermes/profiles/<profile>/plugins/voice-persona`
2. Enable + configure via the profile's `config.delta.yaml` (config.yaml is generated from base + delta; see
   `agent-fleet-operations` / `flume`):
   ```yaml
   plugins: {enabled: [voice-persona]}   # or list_patches.plugins.enabled add: [voice-persona]
   tts:
     persona:
       enabled: true        # master switch, default false = no-op
       # name: peter-griffin   # optional pin; beats the voxxy record
       # file: PERSONA.md      # optional profile-local persona; beats name
       # timeout_seconds: 40   # hard bound on the rewrite
       # voxxy_timeout_seconds: 3
       # auto_from_voice: true
   ```
   With only `enabled: true` and `tts.provider: vox`, `tts.vox.voice: peter`, the agent speaks as Peter via the
   voxxy record. Live examples: peter-griffin (peter), infra-pm (brule), context-director + milkshake-pm (carlin).
3. Optional - pin a fast non-reasoning model for the pass (the default `auto` route is a slow reasoning model, ~20s):
   ```yaml
   auxiliary:
     tts_persona:
       provider: automaticai
       model: automaticai/personal/glm-5.3-flash
       timeout: 40
   ```
4. Apply: **never** restart the gateway with raw systemctl/`hermes gateway restart`. Use
   `hermes-gateway-restart --reason "<why>"` (waits for idle, coalesces, ~6 min outage for everyone). Batch edits and
   ask for one restart after the last. Voxxy-side association changes need **no** restart.

## CLI usage

```bash
voxxy persona list [--json]                 # bundled personas, temperature, which voices map (voxxy | frontmatter)
voxxy persona show ID [--raw]               # render the persona file
voxxy persona path                          # ~/code/voxxy/plugins/voice-persona/personas
voxxy persona rewrite ID "text"             # dry run, no audio; text may come from stdin
voxxy persona rewrite --voice peter "Build 17 passed."   # use the voice's effective persona
voxxy persona rewrite peter-griffin "..." --json         # {original, rewrite, accepted, reason, persona, model, prompt_version, elapsed_s}
voxxy speak -v peter --persona auto "deploy done"        # rewrite, then synthesize (env VOX_PERSONA)
voxxy speak -v carlin --persona george-carlin "..."   # an explicit persona id
```

`speak --persona` is OFF by default (scripts must not gain LLM latency). `auto` = the voice's effective persona.
Works with all speak modes (`--out`, `--raw`, `--sink`, `--via` rewrites locally before piping to the remote).
Fail-open: a failed rewrite speaks the original and prints a dim warning on stderr. `persona rewrite` exits 1 with the
reason when validation rejects; 4 for an unknown id or a voice with no persona.

CLI LLM settings (independent of Hermes): env `VOXXY_PERSONA_BASE_URL` > `~/.config/voxxy/config.toml`
`persona_base_url` > `https://api.automaticai.io/v1`; model `VOXXY_PERSONA_MODEL` > `persona_model` >
`automaticai/personal/glm-5.3-flash`; key `VOXXY_PERSONA_API_KEY` > `persona_api_key_ref` (an `op://` reference
resolved with `op read` at call time; a raw key there is refused); `VOXXY_PERSONA_TIMEOUT` (default 40s).
The CLI uses a dedicated gateway consumer token `voxxy-cli-persona`, scoped to the glm-5.3-flash route.

More: [CLI reference](references/cli.md), [authoring a persona](references/authoring.md),
[troubleshooting](references/troubleshooting.md).

## Limits

- Whole-file TTS only. The sentence-level streaming TTS path (`gateway/run_turn.py`, `tools/tts_streaming.py`) bypasses personas.
- Adds one LLM call of latency (seconds; bounded by `timeout_seconds`, core also bounds the hook with `tts.transform_timeout_seconds`, default 45).
- Digit guard: a rewrite is rejected if it drops more than 15% of the digit runs in the source; also rejected when empty,
  longer than `max_ratio` (1.8) or shorter than `min_ratio` (0.5). Spelled-out numbers and names are not verifiable.
- Longer spoken text costs more TTS credits (ElevenLabs fallback has a hard quota; a rewrite is longer than the original).
