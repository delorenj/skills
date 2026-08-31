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
   │  Layer 1 — YOU write the period prose (the only creative/agentic step)
   ▼
the note ──► scripts/build.mjs ──► out/letter.mp4
               │  1. ElevenLabs narration (Cartesia capacity fallback) → remotion/public/narration.mp3
               │  2. music bed (drop-in or auto-generated, optional)
               │  2b. ambient bed (assets/sfx, always-on atmosphere)
               │  3. props.json  (date auto-generated; signature/title fixed)
               └─ 4. Remotion render (parchment + script + Ken Burns + audio)
```

Three audio layers stack in the render: the **narration** (voice), the optional
**music bed**, and an always-on **ambient bed** (field atmosphere) underneath
both.

**The only thing you produce is the note text.** Everything else — narrator
voice, date line, signature, title, music, ambient, render — is deterministic
and handled by `build.mjs`. Don't write a date or signature; the script supplies
them (today's date as `"From the Encampment, this Nth day of <Month>"`, plus a
fixed signature and title).

### Step 1 — Write the note

Letterify the text (Layer 1). That period prose **is** the note — a salutation, a
body, and a closing line (no signature; the script appends one). Pass it straight
to the build as text, or save it to a `.txt` file. `\n\n` separates paragraphs;
keep it to a slow read (roughly ≤ 200 words for a tight clip).

### Step 2 — Render

```bash
# Prereqs: Node 18+, ffmpeg, and credentials in the process environment.
# Use op:// references resolved only at invocation; do not create a dotenv file.

# Pass the note inline (voice + music + ambient are all automatic):
node scripts/build.mjs --text "My dear colleagues, ...the period prose... Pray proceed without me." --out out/letter.mp4

# Or from a file:
node scripts/build.mjs --file note.txt --out out/letter.mp4

# Auto-generate a mournful music bed instead of using assets/music:
node scripts/build.mjs --file note.txt --auto-music

# Use a specific period track you dropped in:
node scripts/build.mjs --file note.txt --music assets/music/your-track.mp3

# Printed-dispatch typeface instead of script (config, not creative):
node scripts/build.mjs --file note.txt --font dispatch
```

First run installs the Remotion deps under `remotion/` automatically. The clip auto-lengths to the narration plus a title card and a fade-out. (`--spec letter.json` is still accepted for back-compat, but only its `letterText` is read.)

### Voice

The narrator is **hardcoded** — the custom **"Civil War Veteran"** voice
(`HvjKMFO0rjuPaM2f997g`), set as `VOICE_ID` in `scripts/narrate.mjs`. There is no
`--voice` flag and no env override: one note, one narrator. To change narrators,
design a new voice (see `references/voice-and-music.md`) and replace that single
constant.

### Capacity fallback

ElevenLabs remains the one-call primary narrator. Cartesia is considered exactly
once only after a definitive primary quota/capacity/availability result (allowlisted
provider code paired with an eligible provider-specific status and type). For
ElevenLabs, the current [error envelope](https://elevenlabs.io/docs/eleven-api/resources/errors)
must have `detail.type: rate_limit_error` plus `detail.code` of
`rate_limit_exceeded` or `concurrent_limit_exceeded` at HTTP 429, or
`detail.type: service_unavailable` plus `detail.code` of `service_unavailable`
or `maintenance` at HTTP 503. The documented legacy `detail.status` values
`too_many_concurrent_requests` and `system_busy` are accepted only at HTTP 429
and never override a present contradictory type. Cartesia retains its distinct,
top-level structured error schema and its own positive allowlist.

Bare, malformed, generic, auth/configuration/voice/model/input, or otherwise
unclassified responses — including generic 5xx responses — fail closed. It is
never a retry path and never follows another 4xx, malformed output, oversized or
invalid audio, or an ambiguous transport outcome. The adapter writes a temporary
MP3, validates it with `ffprobe`, then atomically publishes it with a sanitized
receipt sidecar.

Fallback is dark until both variables are present in the invocation environment:
`CARTESIA_API_KEY` (standard `sk_car_...`, never `sk_car_admin_...`) and an explicit
`CARTESIA_VOICE_ID`. See `references/voice-and-music.md` for the voice-selection
gate and source references. There is no persisted dotenv configuration.

### Bounded narration I/O and manual recovery

The narration adapter reads all values from the invocation environment and rejects
invalid values before any provider request. These bounded controls have safe
defaults and accept only whole numbers in the stated ranges:

- `SLOWBURNS_NARRATION_REQUEST_TIMEOUT_MS` — `30000` default, `1..120000`.
- `SLOWBURNS_NARRATION_BODY_TIMEOUT_MS` — `30000` default, `1..120000`.
- `SLOWBURNS_NARRATION_MAX_AUDIO_BYTES` — `67108864` default, `1024..134217728`.
- `SLOWBURNS_NARRATION_MAX_ERROR_BODY_BYTES` — `65536` default, `128..1048576`.
- `SLOWBURNS_NARRATION_FFPROBE_TIMEOUT_MS` — `5000` default, `1..30000`.
- `SLOWBURNS_NARRATION_FFPROBE_MAX_BUFFER_BYTES` — `65536` default,
  `1024..1048576`.

Every resolved output has one exclusive canonical claim at
`<output>.narration.lock`, independent of a caller-selected receipt path. The
lock contains only a hashed output identity, operation hash, owner PID/host,
timestamps, and a bounded phase history; it never contains a transcript, raw
path, provider message/body, request header, or credential. A response timeout,
body-read/size failure after a provider boundary, invalid successful audio, or
receipt-integrity failure retains the claim and blocks automatic regeneration.
On any non-normal streamed-body exit, the adapter best-effort cancels the
unread reader and aborts its request controller before classifying the error;
cleanup failures never replace that error or authorize a retry. Fully consumed
streams are not cancelled.
`SLOWBURNS_NARRATION_MAX_AUDIO_BYTES` applies to provider bodies, temporary
validation, and completed-artifact recovery. Recovery stats the final artifact
before `ffprobe` or a full SHA-256 read; an over-limit file is retained as
`receipt_integrity_artifact_too_large` with only its safe byte count, configured
limit, and hash identities in the lock. Its completed receipt is not repaired or
rewritten.

There is **no automatic stale-lock cleanup**. For a manual recovery, first inspect
the sanitized phase and receipt. The only possible manual-clear candidate is a
`claimed_pre_provider` lock unchanged for at least 10 minutes, after confirming
the recorded owner PID is dead on the recorded host and that no final artifact
exists. Any `*_request_started`, `*_headers_received`, `*_body_read_*`,
`*_audio_validation_*`, or receipt-integrity phase requires provider/request and
billing reconciliation (using only a safe request ID when present), artifact
inspection, and explicit operator removal after that investigation. Never delete
an ambiguous claim to make the CLI retry automatically.

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
- Voice: hardcoded custom "Civil War Veteran" (`HvjKMFO0rjuPaM2f997g` in `narrate.mjs`); not parameterized.
- Date line / signature / title: deterministic (date from today; signature + title fixed). The note text is the only creative input.
- Output: 1280×720, 60fps, browser-safe BT.709 h264 MP4. The composition
  retains a 1920×1080 design canvas and downsamples during rendering.
