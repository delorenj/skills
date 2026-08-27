# Hermes Fleet — Voice / TTS Management

Session-specific detail for changing the default TTS voice on the self-hosted Voxxy service.

## Fast path

Use the bundled script from the skill directory:

```bash
scripts/set_voice.sh <voice-slug>
```

Example: `scripts/set_voice.sh carlin`

The script:
1. Verifies the voice exists at `https://vox.delo.sh/voices/<slug>`.
2. Reads `tts.provider` from the active Hermes profile.
3. For provider `voxxy` or `vox`, sets both `tts.vox.voice` and `tts.voice`.
4. Reminds the user to restart Hermes or run `/reset`.

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
- TTS config is cached per Hermes session. Restart or `/reset` is required for changes to take effect.
- This workflow configures Voxxy only. It does not switch providers.
