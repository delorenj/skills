# Voice / TTS Management

Session-specific detail for changing the default TTS voice on the self-hosted Voxxy service.

`tts.provider` must be the registry key `vox`, never the service name `voxxy` —
an unregistered provider makes Hermes fall back to a built-in with no error.
`flume audit --rules hermes.fleet-config` fails a fleet base that sets anything
else.

## Fast path

Use the bundled script from the skill directory:

```bash
scripts/set_voice.sh <voice-slug>
```

Example: `scripts/set_voice.sh carlin`

The script:
1. Verifies the voice exists at `https://vox.delo.sh/voices/<slug>`.
2. Reads `tts.provider` from the active Hermes profile.
3. Sets both `tts.vox.voice` and `tts.voice` when that provider is `vox` (the
   legacy spelling `voxxy` is still accepted so the script can be used to fix a
   profile that has it, but the value itself must be corrected to `vox`).
4. Reminds you to `/reset` the session, or to batch a host restart into one
   `hermes-gateway-restart --reason "..."`.

## Manual fallback

```bash
# Verify the voice exists
curl -s https://vox.delo.sh/voices/<slug>

# Set in the active profile (ignore the "unrecognized key" warning)
hermes config set --force tts.vox.voice <slug>
hermes config set --force tts.voice <slug>
```

## Common pitfalls

- Voice names are slugs (`carlin`, `rick`, `morty`, `damian`, `david`), not display names.
- `tts.vox.voice` and `tts.voice` are custom Voxxy keys. Hermes core may warn they are unrecognized; use `--force` and save them anyway.
- TTS config is cached per Hermes session. `/reset` (per session) or a restart is required for changes to take effect. Chat turns run in the one host gateway, `hermes-gateway.service`: cycle just that profile on the control socket (`unserve-profile` then `serve-profile` on `~/.hermes/gateway.sock`), or batch the change with others and run ONE `hermes-gateway-restart --reason "tts voice change"`. Never a raw `systemctl` restart; there is no per-agent gateway unit.
- This workflow configures Voxxy only. It does not switch providers.
- Changing a voice on a named desk means editing its `config.delta.yaml` and
  rendering, not hand-editing the generated `config.yaml`. The delta writer takes
  the same per-profile lock as every other writer — see
  [config-mutation-safety.md](config-mutation-safety.md).
