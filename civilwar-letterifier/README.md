# Civil War Letterifier 🎻🕯️

Rewrite any text as a solemn, slightly absurd 19th-century Civil War field
dispatch — then turn it into a Ken Burns documentary clip: a weathered period
voice reading the letter, written in fancy script on candlelit parchment, over a
mournful fiddle-and-banjo bed, with a slow pan/zoom down the page.

## Two layers

**1. Letterify (just prose).** Type `/civilwar <text>` and get the letter back.
Modes: `field-note` (short), `full` (maximum banjo), `executive` (manager-safe).

**2. The multimodal extravaganza (the video).**

```bash
export ELEVENLABS_API_KEY=sk_...        # Node 18+, ffmpeg required
node scripts/build.mjs --spec letter.json --voice Adam --auto-music --out out/letter.mp4
```

That narrates the letter, builds/loads a music bed, and renders an MP4 sized to
the narration.

## Layout

```
civilwar-letterifier/
├── SKILL.md                  # the skill (read this first)
├── references/
│   ├── letter-style-guide.md # the field-dispatch voice + modes + examples
│   ├── voice-and-music.md    # stock vs custom voice; music + licensing
│   └── composition-guide.md  # every visual knob
├── scripts/
│   ├── build.mjs             # orchestrator: narrate → music → props → render
│   ├── narrate.mjs           # ElevenLabs TTS (single continuous read)
│   └── make-music.mjs        # optional auto-generated ambient bed
├── assets/
│   ├── example-letter.json   # sample spec
│   └── music/                # drop period tracks here
└── remotion/                 # the Remotion project (Ken Burns composition)
    └── src/CivilWarLetter.tsx
```

## Credits / building blocks

Builds on this repo's `elevenlabs-remotion`, `elevenlabs-voices`, and `remotion`
skills.
