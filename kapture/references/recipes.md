# Recipes

The worked versions of the three things the body only states as rules: waiting for a page to
settle, getting data off it, and converting screenshot pixels. `K=http://127.0.0.1:61822`
and `T` is a live tabId throughout.

## Settling

There is no wait-for-selector tool. `navigate` returns as soon as the content script answers —
for an SPA that is well before the app has rendered — and its advertised `timeout: 30000` never
applies anyway (see the dead-defaults note in [http-api.md](./http-api.md)), so the server also
gives up at 5000ms. Poll rather than guess:

```bash
SEL='.result'
for i in $(seq 20); do
  n=$(curl -s --get --data-urlencode "selector=$SEL" "$K/tab/$T/elements" | jq '.elements|length')
  [ "$n" -gt 0 ] && break
  sleep 0.5
done
[ "$n" -gt 0 ] || echo "gave up waiting for $SEL"
```

Inside a `compose` script the only tool is `wait?t=<ms>`, so put a generous fixed wait there and
the real poll outside. **Give up after ~10s**: screenshot the tab, say what you were waiting
for, and hand it back. A missing element after ten seconds is a finding about the page, not a
reason to keep polling.

To watch what a page logs *while* it settles, end a compose script with `watch_console`:

```bash
jq -Rs '{script:.}' <<'EOF' | curl -s -X POST "$K/tab/$T/compose" --data-binary @-
click?selector=%23submit
watch_console?timeout=5000
EOF
```

That is the only way to reach `watch_console` over HTTP — it has no route of its own.

## Getting data off a page

`dom` returns only the **first** match. `dom?selector=.result` hands you result #1 and there is
no way to ask for #2, so never loop it.

**Attributes and structure — one call, every match:**

```bash
curl -s --get --data-urlencode "selector=.result a" "$K/tab/$T/elements" \
  | jq -r '.elements[] | "\(.href)"'
```

`elements` returns no text, but per element it gives `tagName`, `id`, `className`, a unique
`selector`, `bounds`, `visible`, `focused`, `position`, `scrollParent` — plus `href`, `src`,
`value` and `name` when the element has them, and a full `options` array
(index/value/text/selected/disabled) on a `<select>`. So every link on a page is one call, and
confirming a `fill` landed is one call, no screenshot needed.

**Text — one scoped `dom`, parsed locally:**

```bash
curl -s --get --data-urlencode "selector=.results" "$K/tab/$T/dom" \
  | jq -r .html > /tmp/page.html
# then parse /tmp/page.html with a real parser; do not read it into context
```

Check the budget first — `domSize` rides free on every successful response, along with `url`,
`title`, `viewportDimensions` and `scrollPosition`:

```bash
curl -s "$K/tab/$T" | jq '.domSize'
```

A live OpenRouter tab measured `domSize: 496486`. An unscoped `dom` there is half a megabyte.

**Inside an iframe:** nothing selector-based reaches it — the content script is declared
`all_frames: false`, so `dom` returns the top document only, `elementsFromPoint` returns the
`<iframe>` element itself, and `evaluate` is top-frame too. The only way in is a coordinate
`click`/`hover`, which dispatches CDP input that hit-tests at the browser level.

## Screenshot pixels

The advertised `scale: 0.3` **never applies**. `yaml-loader.ts` builds every optional parameter
as `.default(x).optional()`, and zod's optional wrapper resolves an absent key to `undefined`
without consulting the inner default — so the extension's own signature fallback wins
(`scale = 0.5`, `quality = 0.5`). This is true of *every* documented default in `tools.yaml`;
it happens to agree with the extension for `console_logs.limit` (100),
`network_requests.limit` (50), `network_body.maxBytes` (65536) and `keypress.delay` (50), and
disagree for `screenshot` and `navigate`.

Measured on this machine (viewport 1701×756 CSS px, devicePixelRatio 2):

| request | image |
|---|---|
| `/screenshot/view` (no params) | 1701×756 |
| `?scale=0.3` | 1021×454 |
| `?scale=0.5` | 1701×756 |
| `?scale=1` | 3401×1511 |

So `image_px = css_px × dpr × scale`, and at the *effective* default the image is 1:1 with CSS
pixels — a screenshot coordinate is already a coordinate `click` wants. Rather than trusting any
default, compute the factor from the response you already have:

```
factor = image_width / viewportDimensions.width
css_x  = image_x / factor
```

`/screenshot/view` returns raw image bytes with the right Content-Type; write it to a file and
Read it. `/screenshot` returns JSON with base64 in `data` instead. Element captures
(`?selector=`) render beyond the viewport, so an element below the fold is capturable without
scrolling to it; a zero-size element returns `SCREENSHOT_ERROR`.

## Choosing an input tool

| Situation | Tool |
|---|---|
| plain `<input>`/`<textarea>`, page is not picky | `fill` — sets `.value`, fires synthetic events, blurs |
| React/Vue controlled input, autocomplete, mask, contenteditable | `type` — real per-character CDP key events |
| a large block, or an editor like Google Docs | `insertText` — one IME-style commit, no per-key events |
| replacing existing content | `clear` first — `type` types at the cursor, it does not replace |
| native `<select>` | `select`, matching the option's **value**, never its text |
| a custom dropdown | click the trigger, then click the option |
| submitting | `keypress?key=Enter` — Enter carries `\r` and triggers real form submission |

`fill` refuses anything that is not input/textarea/contenteditable with `INVALID_ELEMENT`, and
`select` refuses a non-`<select>` tag. For a `<select>`, `elements` returns the full `options`
array (index/value/text/selected/disabled) so you can read the values before choosing one.
