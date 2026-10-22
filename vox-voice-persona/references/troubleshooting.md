# Troubleshooting

Hermes logs: `~/.hermes/logs/agent.log` (and `~/.hermes/profiles/<p>/logs/`). Grep `voice-persona:`.

| Log line / symptom | Meaning / fix |
| --- | --- |
| `voice-persona: <id> rewrite accepted (N -> M chars, prompt voice-persona/3)` | working |
| `rejected ... rewrite (<reason>, prompt ...); speaking original text` | validator said no: empty, > `max_ratio`, < `min_ratio`, or digits dropped. Try `voxxy persona rewrite ... --json` to see the reason; tune persona rules or ratios |
| `rewrite exceeded Ns; speaking original text` | LLM too slow. Pin `auxiliary.tts_persona` to `automaticai/personal/glm-5.3-flash`, or raise `tts.persona.timeout_seconds` (core bound: `tts.transform_timeout_seconds` 45) |
| `rewrite failed (...)` | auxiliary client error (provider/key/model); check `auxiliary.tts_persona` |
| agent never rewrites | `plugins.enabled` lacks `voice-persona`, symlink missing in `<profile>/plugins`, `tts.persona.enabled` not true, gateway not restarted since enabling, or streaming TTS path (bypasses personas) |
| rewrites in the wrong voice | resolution order: profile `file`/`name` beat the voxxy record; check `voxxy voice persona VOICE` for the effective source |
| voxxy record ignored | `auto_from_voice: false`, provider is not `vox`, no voice set, or lookup failed (falls back to frontmatter) - 60s cache, wait or change profile |
| voxxy lookup 401/403 | the plugin sends `tts.vox.api_key` or env `VOX_API_KEY` as Bearer and X-API-Key, same as `plugins/tts/vox`. Fix the key for the gateway process |
| persona set but silent | persona file missing for that slug (logged once). `voxxy persona list`; ids are file stems |
| `voxxy persona rewrite`: no key / 401 | set `VOXXY_PERSONA_API_KEY` or `persona_api_key_ref` (op:// ref) in `~/.config/voxxy/config.toml`; token must be a gateway consumer token, never an OpenRouter management key |
| `voxxy persona rewrite`: project root not found | set `project_root` in `~/.config/voxxy/config.toml` or run inside `~/code/voxxy` |
| `PUT .../persona` 404/405 on the server | core image is older than migration 003: apply `migrations/003_voice_persona.sql` and rebuild + recreate `vox` |
| `speak` synthesis fails after a good rewrite | TTS, not persona: ElevenLabs fallback quota (`quota_exceeded`) hits longer rewritten text first; check `docker logs vox` |

Deploy recap for the server side (app code is baked into the image):
`mise run migrate` (or the psql command in `migrations/003_voice_persona.sql`), then
`op run --env-file .env.template -- docker compose -f compose.yml build vox` and
`... docker compose -f compose.yml -f compose.engines.yml up -d --no-deps vox`; confirm `https://vox.delo.sh/healthz`
and that `GET /voices` has a `persona` field.
