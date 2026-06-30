# Composition Guide — `remotion/src/CivilWarLetter.tsx`

The clip is one Remotion composition. Preview it live:

```bash
cd remotion && npm install && npm run studio   # opens Remotion Studio
```

In the Studio you can edit `props.json` (or the `defaultProps` in `Root.tsx`)
and scrub frames. `node scripts/build.mjs` regenerates `props.json` and renders.

## Layers (back → front)
1. **Parchment** — warm radial gradient + fractal-noise paper grain (multiplied).
2. **The letter** — `dateLine` (right-aligned italic), the body in the chosen
   font, and the `signature` in large script. Sits in a centered column.
3. **Ken Burns drift** — the letter column pans downward while the whole frame
   slowly zooms (`scale` 1.03 → 1.12). The pan distance is computed from the
   *measured* letter height (via `delayRender` + `useLayoutEffect`), so the last
   line always lands on screen no matter how the text wraps. Short letters just
   drift; long ones scroll like a documentary.
4. **Candlelight** — a warm radial glow whose opacity flickers via three detuned
   sines (never periodic).
5. **Archival grade + vignette** — `sepia/contrast/brightness/saturate` over the
   scene, plus a burnt-edge vignette on top.
6. **Title card** (during `introPad`) and **fade-to-black** (during `outroPad`).
7. **Audio** — narration starts after the title card; music loops underneath,
   ducked to ~0.22 and fading in/out.

## Timing
`Root.tsx`'s `calculateMetadata` reads the narration duration with
`getAudioDurationInSeconds` and sets:

```
durationInFrames = ceil((introPad + narration + outroPad) * fps)
```

So you never set a length by hand — record the voice, and the video fits it.

## Knobs (props, set in `letter.json` / `build.mjs` flags)
| Prop | Effect | Default |
|------|--------|---------|
| `fontStyle` | `script` (Tangerine) or `dispatch` (IM Fell English) | `script` |
| `accentColor` | ink for date line + signature | `#5a2a16` |
| `introPad` | seconds of title card before narration | `3.5` |
| `outroPad` | seconds of hold + fade after narration | `4` |
| `title` | title-card text | "A Letter from the Front" |

## In-code constants worth tuning
In `CivilWarLetter.tsx`:
- `scale` range — zoom intensity.
- `topMargin` / `bottomMargin` — where text rests; affects pan distance.
- `flicker` coefficients — candle liveliness.
- body `fontSize` (76 script / 46 dispatch) and `lineHeight`.
- `letterColumnWidth` — text measure / wrap width.
- music `volume` interpolation — duck level and fade lengths.

## Fonts
Loaded via `@remotion/google-fonts` (Tangerine, IM Fell English) — no binaries,
fetched at build. To use a real scanned handwriting font, drop a `.woff2` in
`remotion/public/` and load it with `@remotion/fonts` (`loadFont`) instead; see
the repo's `remotion/references/fonts.md`.

## Aspect ratio
Default 1920×1080. For vertical (Reels/TikTok) set `width: 1080, height: 1920`
in `Root.tsx` and reduce `letterColumnWidth` to ~`width * 0.82`.
