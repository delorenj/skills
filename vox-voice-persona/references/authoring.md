# Authoring a persona

Bundled files: `voxxy persona path` (`~/code/voxxy/plugins/voice-persona/personas/<id>.md`). The id is the file stem.

```markdown
---
name: Peter Griffin        # display name used in the prompt (default: file stem)
voices: [peter]            # fallback voice->persona mapping when voxxy has no record
temperature: 0.8           # sampling temperature (default 0.7)
description: one line
---
# Character bible (free-form)   <- body goes to the model verbatim
## Rules for rewriting          <- name the facts that must survive
## Examples                     <- 2-3 honest before/after pairs, "after" keeps every fact
```

Only `name`, `voices`, `temperature`, `description` are read; other keys are documentation.

Fastest path: let the CLI write the first draft, then edit it.

```bash
voxxy persona generate brian-griffin -c "Brian Griffin from Family Guy" --voice brian --dry-run   # read it
voxxy persona generate brian-griffin -c "Brian Griffin from Family Guy" --voice brian             # write + associate
```

It web-searches the character, follows the structure above, validates through the plugin loader, refuses to
overwrite without `--force`, and with `--voice` sets `voices: [brian]` and associates the voice if it exists on the server.
`voxxy voice clone "<who>"` runs the same generator as its last step. Always read a generated persona: check the
rules forbid dropping facts, the tics are budgeted (not one per sentence), and the examples keep every number.

Steps for a new character (by hand):

1. `cp personas/peter-griffin.md personas/<new-id>.md`; rewrite bible, tics, catchphrase budget, profanity level (prose).
2. Rules must say numbers, names, paths, commands, warnings and action items are never dropped or altered; keep the tone
   out of errors/warnings. Convey accents by word choice, not phonetic spelling (the TTS voice supplies the sound).
3. `voxxy persona list` (it appears), `voxxy persona rewrite <new-id> "text with 42 numbers"` to test.
4. Associate: `voxxy voice persona <voice> <new-id>` (no frontmatter `voices:` needed). Add `voices:` only if it should be
   the default when voxxy has no record.
5. Edit the persona file => parsed personas are cached by (path, mtime); no restart for the file. Hermes loads the plugin
   code at gateway start, so a changed `__init__.py` needs a (batched, `hermes-gateway-restart --reason`) restart.
6. Tests: `cd ~/code/voxxy && mise x -- uv run pytest plugins/voice-persona/tests -q`. Commit and push the persona.

Private/profile-only persona: put `PERSONA.md` in the profile `HERMES_HOME` and set `tts.persona.file: PERSONA.md`
(wins over everything, including the voxxy record).

Changing `PROMPT_VERSION` or the prompt is a plugin code change: bump the version so logs show which prompt produced a rewrite.
