# Voice & Music

## Voice

### The narrator (hardcoded — not parameterized)

There is exactly **one** narrator: the custom **"Civil War Veteran"** voice — a
19th-century American male reading a somber letter by candlelight.

ElevenLabs Voice ID: **`HvjKMFO0rjuPaM2f997g`**

It is hardcoded as `VOICE_ID` in `scripts/narrate.mjs`. There is no `--voice`
flag and no `CIVILWAR_VOICE` env var — the voice is deliberately fixed so every
dispatch sounds like the same weathered reader.

### Changing the narrator

To swap narrators, design a new voice and replace that one `VOICE_ID` constant in
`scripts/narrate.mjs`. This repo's **`elevenlabs-voices`** skill has the tool:

```bash
python3 ../elevenlabs-voices/scripts/voice-design.py \
  --gender male --age old --accent american --accent-strength 1.1 \
  --description "A weathered, solemn American man in his sixties reading a wartime letter by candlelight; slow, gravelly, mournful, dignified, unhurried, with the cadence of a 19th-century field dispatch." \
  --style storytelling --save "CivilWarNarrator"
```

It prints a `voice_id`; paste it into `VOICE_ID`. Tips: keep `--age old`,
`--accent american`, strength ~1.0–1.2. The description carries most of the
character — emphasize _weathered, slow, mournful, dignified_.

### Cartesia capacity fallback (configuration gate)

Cartesia is not a second narrator or a load-balancing path. It is a single,
capacity-only backup when ElevenLabs has returned a definitive quota, concurrency,
or availability failure. The live adapter calls the current official
`POST https://api.cartesia.ai/tts/bytes` endpoint with `Authorization: Bearer`,
`Cartesia-Version: 2026-08-14`, `model_id: sonic-3.6`, a stock voice ID, and an
MP3 request (`container: mp3`, `encoding: mp3`, 44.1 kHz, 128 kbps). It requests
`locale: en-US`, `volume: 1`, and a measured slow `speed: 0.85`; the intent is a
solemn, unhurried documentary read without cloning or custom-voice training.

The bounded stock candidate is **Jameson**, because Cartesia's current official
voice guidance names it among stable English male voices; this is a candidate
name, not a verified ID. Set `CARTESIA_VOICE_ID` only after a standard runtime key
can inspect the official Voice Library and a mock-safe validation confirms the
chosen stock voice supports this model and output. Do not invent or hard-code an
unverified ID. Live validation is currently blocked: no usable standard Cartesia
runtime key is available, and the legacy admin/unrecognized key must never be used
for TTS, provisioned, persisted, or tested with paid synthesis.

Use only a standard `CARTESIA_API_KEY` (`sk_car_...`); the adapter rejects
`sk_car_admin_...`. Supply it through an `op://DeLoSecrets/...` reference resolved
at invocation time, never a plaintext secret or dotenv file. The receipt contains
only provider/model/voice/fallback class and a safe request ID, never transcript,
response body, headers, or credentials.

Official references (checked 2026-08-31):

- https://docs.cartesia.ai/api-reference/tts/bytes
- https://docs.cartesia.ai/use-the-api/api-conventions
- https://docs.cartesia.ai/build-with-cartesia/capability-guides/choosing-a-voice

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

## Ambient bed

The composition layers a third, **always-on** track — field atmosphere — beneath
both the narration and the (optional) music. Unlike music it is not gated behind
a flag: any audio file in `assets/sfx/` is picked up automatically and plays for
the whole film, looped, fading in at the open and out under the closing fade.

- Drop a file in `assets/sfx/`. A track named `ambient.*` is preferred; otherwise
  the first (or a random) audio file is used.
- Override the file with `--ambient <file>` and the level with
  `--ambient-volume <0..1>` (default `0.16`, just under the music's `0.22`).
- Empty folder + no `--ambient` → the layer is skipped and the render still
  finishes (voice, plus music if selected).

What reads well: low, continuous, non-melodic texture — distant crickets, night
wind, a faint crackling fire, a far-off camp. Keep it quiet and unbusy so it
deepens the scene without pulling against the voice. Anything with a recognizable
tune belongs in the music bed, not here.

**Licensing:** the same rules as music apply — use field-recording / ambience
that you own or that is public-domain / CC-cleared; verify the specific
recording's license before publishing.
