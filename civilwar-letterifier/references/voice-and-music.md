# Voice & Music

## Voice

### Custom Period Voice

**Civil War Veteran Narrator** — a 19th-century American male reading a somber
letter by candlelight.

ElevenLabs Voice ID: HvjKMFO0rjuPaM2f997g

### For More Custom period Voices

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
carries most of the character — emphasize _weathered, slow, mournful, dignified_.

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

**Licensing — read this.** The signature Ken Burns _Civil War_ theme is
**"Ashokan Farewell" by Jay Ungar (1982) — still under copyright.** Do **not**
bundle or publish it. Period _compositions_ below are public domain, but any
specific _recording/arrangement_ may not be — verify the recording's license.

Public-domain era tunes (find a freely-licensed recording, or record your own
solo fiddle/banjo):

- _When Johnny Comes Marching Home_ (1863)
- _The Battle Cry of Freedom_ (1862)
- _Aura Lea_ (1861)
- _Hard Times Come Again No More_ — Stephen Foster (1854)
- _Lorena_ (1856)
- _Shenandoah_ (traditional)

Royalty-free / freely-licensed sources for solo-fiddle laments:

- Free Music Archive (filter CC / public domain) — freemusicarchive.org
- Internet Archive audio (verify each item's rights) — archive.org
- YouTube Audio Library (free use)
- Musopen — public-domain recordings — musopen.org

A solo, sparse fiddle or fingerpicked banjo at low volume reads best; busy
arrangements fight the narration.
