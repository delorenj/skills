---
name: civilwar-letterifier
description: Rewrite any text as a solemn, slightly absurd 19th-century Civil War field dispatch (Ken Burns documentary voice), then optionally turn it into a multimodal video — period narration via ElevenLabs, the letter in fancy script on aged parchment, a mournful music bed, and a slow Ken Burns pan/zoom of the letter being read. Use when the user types /civilwar, asks to "civil-war-ify" or "Ken Burns" some text, or asks for a documentary-style letter video.
license: Complete terms in LICENSE
---

# Civil War Letterifier

Two layers. Use only what the user asks for.

1. **Letterify (text → letter).** Rewrite the user's text as a mournful field dispatch. This is the default and is just prose — no tools needed.
2. **Letterify the multimodal extravaganza (letter → documentary clip).** Narrated, scored, written in script on parchment, with a Ken Burns drift over the page. Triggered when the user wants audio/video ("make the video", "with the voice and music", "the full Ken Burns thing").

---

## Layer 1 — The `/civilwar` command

When the user types `/civilwar <text>` (or asks to civil-war-ify / Ken-Burns something), rewrite that text as a solemn, slightly absurd Civil War-era letter or documentary narration.

**Inviolable rules:**
- Preserve the original meaning, names, facts, dates, numbers, requests, and logistics **exactly**. A blocked Jira ticket stays a blocked Jira ticket.
- **Do not invent facts.** Period-flavored metaphor is welcome; new commitments, dates, or details are not.
- Mournful field-dispatch register: read over banjo, fiddle, and candlelight. Address a recipient ("My dear colleagues"), sign off as an obedient, beleaguered servant.
- Keep professional messages still usable — the manager must learn the actual status.

### Modes

| Mode | Trigger | Length & tone |
|------|---------|---------------|
| **standard** | `/civilwar <text>` | Default. One sepia paragraph or two. Tasteful tragedy. |
| **field-note** | `/civilwar field-note <text>` | One or two sentences — short enough for Slack/SMS. |
| **full** | `/civilwar full <text>` | Maximum banjo, maximum plague. Open with a stage cue (`*faint fiddle over distant thunder*`). HR is concerned. |
| **executive** | `/civilwar executive <text>` | Grave dispatch from Antietam that still conveys the Jira ticket, the blocker, and the ask. Safe to send to a manager. |

See `references/letter-style-guide.md` for the full register, devices, and worked examples. Read it before writing if you want the voice exactly right.

### Quick example

`/civilwar full I can't make the meeting today because my stomach is wrecked and I need to lie down.`

> *faint fiddle over the low murmur of distant thunder*
>
> My dear colleagues,
>
> I regret to report that I shall be unable to attend our appointed council this day. A most grievous rebellion has commenced within my own constitution, and I have been compelled to retire from the field and take refuge upon the nearest horizontal surface.
>
> Pray proceed without me, and know that I remain, though diminished, devoted to the cause.
>
> Your obedient and intestinally besieged servant,
> J.

---

## Layer 2 — The multimodal extravaganza

Goal: a documentary clip where the letter, in elegant script on candlelit parchment, drifts slowly under the camera (Ken Burns) while a weathered period voice reads it over a mournful fiddle-and-banjo bed.

**Pipeline (all local; renders on the user's machine):**

```
user text
   │  Layer 1 (you write the prose)
   ▼
letter.json ──► scripts/build.mjs ──► out/letter.mp4
                   │  1. ElevenLabs narration  → remotion/public/narration.mp3
                   │  2. music bed (drop-in or auto-generated, optional)
                   │  2b. ambient bed (assets/sfx, always-on atmosphere)
                   │  3. props.json
                   └─ 4. Remotion render (parchment + script + Ken Burns + audio)
```

Three audio layers stack in the render: the **narration** (voice), the optional
**music bed**, and an always-on **ambient bed** (field atmosphere) underneath
both.

### Step 1 — Write the letter spec

Letterify the text (Layer 1), then save it as a small JSON file the renderer understands:

```json
{
  "letterText": "My dear colleagues,\n\nI regret to report that I shall be unable...\n\nPray proceed without me.",
  "dateLine":   "Camp near the Sofa, this 30th day of June",
  "signature":  "Your obedient & intestinally besieged servant, J.",
  "title":      "A Letter from the Front",
  "fontStyle":  "script"
}
```

- `\n\n` separates paragraphs. Keep it to what fits a slow read (roughly ≤ 200 words for a tight clip).
- `fontStyle`: `"script"` (Tangerine calligraphy — the default "fancy script") or `"dispatch"` (IM Fell English — a printed period typeface, better for longer text).

### Step 2 — Render

```bash
# Prereqs: Node 18+, ffmpeg, and ELEVENLABS_API_KEY in env or .env.local
export ELEVENLABS_API_KEY=sk_...

# Voice only:
node scripts/build.mjs --spec letter.json --voice Adam --out out/letter.mp4

# Auto-generate a mournful music bed:
node scripts/build.mjs --spec letter.json --voice Adam --auto-music --out out/letter.mp4

# Use a real period track you dropped in:
node scripts/build.mjs --spec letter.json --music assets/music/your-track.mp3 --out out/letter.mp4
```

First run installs the Remotion deps under `remotion/` automatically. The clip auto-lengths to the narration plus a title card and a fade-out.

### Voice

- Default stock voice: **`Adam`** (documentary narrator). `George` (warm British storyteller) also fits. Override with `--voice <name|id>` or `CIVILWAR_VOICE`.
- For the authentic weathered, solemn 19th-century reader, **design a custom voice** — see `references/voice-and-music.md`. Pass its voice id via `--voice`.

### Music

Pick one; defaults to voice-only if you skip it:
- `--music <file>` — a track you supply (recommended for the real thing). Drop files in `assets/music/`.
- `--auto-music` — synthesize an original mournful fiddle/banjo bed via ElevenLabs (no licensing worries, looped under the voice).

**Licensing matters:** the actual Ken Burns theme ("Ashokan Farewell") is copyrighted — do not bundle it. `references/voice-and-music.md` lists public-domain period tunes and royalty-free sources.

### Ambient bed

A separate, **always-on** atmosphere layer (crickets, wind, a distant camp) that
plays beneath the voice and music for the entire film — it is not an alternative
to the music bed; both stack. Drop an audio file in `assets/sfx/` (a file named
`ambient.*` is preferred; otherwise the first/random track is used) and it is
picked up automatically. Overrides:

- `--ambient <file>` — use a specific ambient track.
- `--ambient-volume <0..1>` — peak level of the bed (default `0.16`; it sits
  below the music's `0.22` so it never competes with the narration).

If `assets/sfx/` is empty and no `--ambient` is given, the layer is simply
skipped.

### Tuning the look

The composition lives in `remotion/src/CivilWarLetter.tsx`. Preview and tweak live with:

```bash
cd remotion && npm install && npm run studio
```

`references/composition-guide.md` documents every knob (parchment, sepia grade, candle flicker, pan distance, fonts, pads).

---

## Defaults this skill was built with
- Music: drop-in track if present, else auto-generated bed (so the pipeline always finishes).
- Ambient: always-on bed from `assets/sfx/` (skipped only if that folder is empty), layered under voice + music at `0.16`.
- Voice: stock `Adam` by default; custom-designed period voice recommended.
- Output: 1920×1080, 30fps, h264 MP4.
