# Voice & Music

## Voice

### Stock voices (fastest)
ElevenLabs stock voices that fit the mournful-narrator brief:

| Voice | Why it works |
|-------|--------------|
| **Adam** | Dominant, documentary narration. Default. |
| **George** | Warm British storyteller; solemn and intimate. |
| **Arnold** | Deep and authoritative for graver dispatches. |

Use with `--voice Adam` (or set `CIVILWAR_VOICE`). The narrator delivery
(stability 0.45 / style 0.4) is tuned in `scripts/narrate.mjs` for a slow,
deliberate read — period letters should not sound rushed.

### Custom period voice (most authentic)
For a weathered, candle-lit 19th-century reader, design a voice once and reuse
its id. This repo's **`elevenlabs-voices`** skill has the tool:

```bash
python3 ../elevenlabs-voices/scripts/voice-design.py \
  --gender male --age old --accent american --accent-strength 1.1 \
  --description "A weathered, solemn American man in his sixties reading a wartime letter by candlelight; slow, gravelly, mournful, dignified, unhurried, with the cadence of a 19th-century field dispatch." \
  --style storytelling --save "CivilWarNarrator"
```

It prints a `voice_id`. Then:

```bash
node scripts/build.mjs --spec letter.json --voice <that_voice_id> --out out/letter.mp4
```

Tips: keep `--age old`, `--accent american`, strength ~1.0–1.2. The description
carries most of the character — emphasize *weathered, slow, mournful, dignified*.

## Music

The composition loops a short bed quietly under the narration and fades it in and
out. Two ways to get one:

### A. Auto-generate (no files, no licensing worries)
```bash
node scripts/build.mjs --spec letter.json --auto-music ...
```
`scripts/make-music.mjs` synthesizes an **original** fiddle/banjo bed via the
ElevenLabs Sound Generation API. It's not a recording of any copyrighted
arrangement, so it's safe to publish.

### B. Drop in a real track (best vibe)
Put a file in `assets/music/` and pass `--music assets/music/your-track.mp3`.

**Licensing — read this.** The signature Ken Burns *Civil War* theme is
**"Ashokan Farewell" by Jay Ungar (1982) — still under copyright.** Do **not**
bundle or publish it. Period *compositions* below are public domain, but any
specific *recording/arrangement* may not be — verify the recording's license.

Public-domain era tunes (find a freely-licensed recording, or record your own
solo fiddle/banjo):
- *When Johnny Comes Marching Home* (1863)
- *The Battle Cry of Freedom* (1862)
- *Aura Lea* (1861)
- *Hard Times Come Again No More* — Stephen Foster (1854)
- *Lorena* (1856)
- *Shenandoah* (traditional)

Royalty-free / freely-licensed sources for solo-fiddle laments:
- Free Music Archive (filter CC / public domain) — freemusicarchive.org
- Internet Archive audio (verify each item's rights) — archive.org
- YouTube Audio Library (free use)
- Musopen — public-domain recordings — musopen.org

A solo, sparse fiddle or fingerpicked banjo at low volume reads best; busy
arrangements fight the narration.
