# The artifact

## Layout

```
.recaps/
  index.html                      the hub — reverse-chronological rail, rewritten each run
  entries/
    2026-09-03-1412-<slug>.json   machine record, one file per run, WRITE-ONCE
  2026-09-03-1412-<slug>.html     the page, write-once
```

**One file per entry; the index is derived, never merged.** A single shared index that every run
rewrites guarantees conflicts the moment two agents work one repo in a day — and it makes the window
anchor a race, where both runs chain from the same point and the second silently starts after work it
never saw. `HHMM` in the name is required: same-day repeats are normal.

Entries link back to `./index.html` only. A run adds two files and rewrites one.

### The entry record

```json
{
  "id": "2026-09-03-1412-fleet-systemd-health",
  "generated_at": 1756900320,
  "window": { "start": 1756814400, "end": 1756900320, "basis": "entries", "confidence": "high" },
  "head_sha": "a106d6e...",
  "host": "big-chungus",
  "sessions": ["e5a5df55-..."],
  "capability_headline": "Fleet health is now observable per agent",
  "counts": { "capabilities": 1, "commits": 8, "repos": 2 },
  "path": "2026-09-03-1412-fleet-systemd-health.html"
}
```

Timestamps are **epoch seconds**. `basis` records which window rung fired so the next run knows how much
to trust the anchor. `host` and `head_sha` let the next run refuse a foreign anchor.

**Idempotency:** re-running for the same resolved window **replaces** its entry — it does not append.
Key on the window, or the directory fills with near-duplicates on the first retry.

**The hub row carries the capability headline**, not just the title, so a month of recaps answers "what
can I do now" without opening anything. After ~20 entries, roll older ones into a collapsed year band.

## Committing

Write always. **Commit only** when `.recaps/` already exists (the user opted in once) or the user asks.
Several repos here are forks and vendored clones; writing a "what you can do now" page into someone
else's tree and committing it is wrong by default. Honour a `.recaps/.gitignore` containing `*`.
`--private` redirects to `~/.local/state/recaps/<repo>/`.

## Self-contained, and it must open from `file://`

- **Inline everything.** No CDN, no web fonts, system font stack. Ship the CSS inline from
  `assets/recap.css`.
- **Never `fetch()`.** It is blocked on `file://` and it fails *silently* — a hub that fetches its own
  index renders empty on disk. Embed data as a JSON island.
- **Escape `<` as `<` inside embedded JSON**, and HTML-escape every quoted commit subject and
  ticket title. A commit message containing `</script>` ends the page.
- Put the JSON island **above** the code that reads it.
- All paths relative.

## Theme

Three blocks. The dark palette is written twice — that is not a mistake, it is what makes an explicit
toggle win in both directions.

```css
:root { color-scheme: light dark; /* complete LIGHT palette */ }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { /* dark */ } }
:root[data-theme="dark"] { /* dark again */ }
```

`background: var(--bg)` on **both** `html` and `body`. In `<head>`, before the stylesheet:

```html
<script>try{var t=localStorage.getItem('recap-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}</script>
```

The `try/catch` is mandatory even though `localStorage` works on `file://`.

## Pills

**NEW · CHANGED · CAVEAT · BROKE**

`CHANGED` is the one that earns its place: *something you already do now behaves differently* is the
fact a human most needs and a commit log never states.

## Filtering

Prefer the CSS-only `:has()` radio filter over JS chips. Keep the radios focusable —
`position:absolute; opacity:0`, never `display:none`.

## Choosing the shape — the page varies, the hub does not

The hub is always a reverse-chronological rail; navigation must be predictable. For the entry, compute:

- **C** = capabilities
- **T** = distinct surfaces touched
- **S** = does order carry meaning (a migration, a staged rollout, a debugging arc)
- **Q** = does one quantity vary across ≥5 comparable buckets

| condition | shape |
|---|---|
| C = 0 | a short honest note and the remaining bands. **Never padding.** |
| C ≤ 2, T = 1 | a plain list |
| 3 ≤ C ≤ 8 | capability cards |
| C ≥ 3 and T ≥ 3 | a table, one row per surface |
| S | a timeline as the spine, capabilities hanging off it |
| Q | add **exactly one** inline SVG chart, its question in the title |

They compose. A chart earns its place only when the reader would otherwise hold five or more numbers in
their head, and **the numbers always also appear as text**. Inline SVG only — no chart library, nothing
to load. **Banned: donuts, progress rings, decorative sparklines, anything 3-D.**

## Related skills — reference, do not duplicate

- Visual polish beyond the shipped stylesheet: `~/.agents/skills/impeccable/SKILL.md`
- Prose register for a non-engineer reader:
  `~/code/intelliforia-mobile/.agents/skills/team-update/references/voice-and-structure.md` — the
  strongest model for this voice. Its card formula and status-pill discipline transfer directly; its
  personas and video sections do not.
- A periodic project update to a declared audience is a **different job**: `activity-report`.
