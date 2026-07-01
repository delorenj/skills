# Civil War Letterifier 🎻🕯️

Rewrite any text as a solemn, slightly absurd 19th-century Civil War field
dispatch — then turn it into a Ken Burns documentary clip: a weathered period
voice reading the letter, written in fancy script on candlelit parchment, over a
mournful fiddle-and-banjo bed, with a slow pan/zoom down the page.

## SlowBurns CLI (one command, end to end)

```bash
slowburns something.txt          # → ./out/slowburns-<timestamp>-something.mp4
```

One command: rewrites the text as a Civil War dispatch (burns-speak), narrates
it in the period voice, lays a mournful music bed **and** an always-on field
ambience bed underneath, and renders the letter on parchment with a slow Ken
Burns drift. The output gets a unique, time-ordered name in `./out`, with the
letter text saved alongside as `*.letter.txt`.

Defaults (just `slowburns file.txt`): **letterify on, music on, ambient on.**
Music and ambience are synthesized once and cached in `assets/` for reuse.

```bash
slowburns memo.txt --mode full          # maximum melodrama
slowburns --text "Standup moved to 4pm" # inline text
slowburns memo.txt --raw                # input is already period prose
slowburns memo.txt --no-music --no-ambient
slowburns --help
```

Install the `slowburns` command with `npm link` (no deps to install — the
scripts use bare `node`); the Remotion render deps auto-install on first run.

### Keys

- **`ELEVENLABS_API_KEY`** — narration + synthesized music/ambience beds.
- **`SLOWBURNS_OPENROUTER_API_KEY`** — the letterify step, via
  [OpenRouter](https://openrouter.ai) (falls back to `OPENROUTER_API_KEY`).
  Default model `anthropic/claude-sonnet-5`; override with `--model <slug>` or
  `$SLOWBURNS_MODEL`. The value may be a literal key **or** a 1Password reference
  (`op://DeLoSecrets/OpenRouter/SLOWBURNS_OPENROUTER_API_KEY`), resolved at
  runtime via `op read` — so no plaintext key need live on disk.

Put both in a project `.env.local` (gitignored) or the environment. The letter's
sign-off is written by the model (cohesive with the content); set the name with
`--signer` (default `J.`).

## Two layers

**1. Letterify (just prose).** Type `/civilwar <text>` and get the letter back.
Modes: `field-note` (short), `full` (maximum banjo), `executive` (manager-safe).

**2. The multimodal extravaganza (the video).** Driven by the `slowburns` CLI
above, or directly:

```bash
export ELEVENLABS_API_KEY=sk_...        # Node 18+, ffmpeg required
node scripts/build.mjs --file note.txt --auto-music --out out/letter.mp4
```

That narrates the letter, builds/loads a music + ambient bed, and renders an MP4
sized to the narration.

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
