# Design System: SlowBurns (slowburns.app)

## 1. Visual Theme & Atmosphere

SlowBurns is a candlelit field office at dusk rendered as a web surface: the page is a physical object resting on a desk, not a screen. The canvas is the exact parchment of the product's own video, so opening the app and watching a finished dispatch feel like one continuous sheet of paper. It should read the way the first ninety seconds of a serious PBS / Ken Burns documentary look and sound - reverent, unhurried, dryly self-serious - while the subject matter (a two-o'clock dentist appointment, a blocked ticket, ten minutes of traffic) supplies all of the humor. The joke lives entirely in the solemnity of the treatment; the visuals never wink.

Density is deliberately uneven. Macro-whitespace opens up between sections (py-24 to py-40) so the eye rests, then sudden intimate density arrives inside the dispatch card, where ruled ledger lines, copperplate script, a pressed date, and a wax seal cluster like real correspondence. Variance comes from the tension between crisp, upright, editorial UI chrome and the warm, slanted human hand of the letter itself. Only one thing is perpetually alive in the page chrome: the candlelight - a soft radial glow in the upper-right corner that breathes, casting a living flicker across the paper exactly as a flame would light a letter on camera. The page begins in warm parchment light and settles, at the footer, into the deep near-black vignette the film lives inside.

- **Density:** 4 / 10 - Daily-App-Balanced trending airy; one lit object per zone.
- **Variance:** 8 / 10 - Offset, asymmetric, never centered; the dispatch card even sits at a slight rake.
- **Motion:** 5 / 10 - Fluid but weighted; nothing slides fast. Ink sets, wax presses, candlelight breathes.

## 2. Color Palette & Roles

The palette IS the video composition mapped onto a page. The parchment canvas walks the brand's exact radial gradient so site and film are cut from one sheet; the ink and accent-ink are held verbatim; candlelight appears only as luminance; and the near-black anchors the deepest shadow and the footer, honoring the no-pure-black rule.

**Canvas & surfaces (the paper)**
- **Field Parchment** (#f4e8c9) - Primary canvas, radial center-light; the brightest reading surface.
- **Aged Parchment** (#ecdcb0) - Gradient mid-tone and inner-card core fill.
- **Foxed Wheat** (#dcc488) - Gradient outer step, panel grounds sitting away from the light.
- **Foxed Edge** (#cbae6e) - Hairline bezels, double-bezel shells, section rules, ruled ledger lines, vignette edge, and brass catalog-plate frames.

**Ink (text family - warm, never pure black)**
- **Iron-Gall Ink** (#2b1a0c) - Primary body and UI text; the letter's body voice.
- **Signature Ink** (#5a2a16) - Deep-sepia text ink for dates, signatures, and drop-caps ONLY. This is a text color, not a UI accent; it is the same hue as the accent below, used as ink.

**The single chromatic accent (one, and only one)**
- **Wax Seal Oxblood** (#5a2a16) - THE single accent (HSB ~18 deg, 76%, 35%; saturation < 80%). Taken verbatim from the brand's "Accent ink (date, signature)." Reserved for: the wax seal, the one primary CTA per view, and one hairline emphasis rule per section. Its vitality comes from relief and candlelight specular, never from a brighter hue. There is no second accent anywhere.

**Candlelight (luminance only - never a fill, never an accent)**
- **Candlelight** (#ffc470) - Ambient corner glow and inset specular highlights on seal, glass, and card top-edges.
- **Ember Glow** (#ffaa46) - The warmer inner core of the light pool and the seal's specular hot-spot. Used only as radial luminance; never as a flat fill, rim, or box-shadow color on components.

**The dark (vignette & footer)**
- **Vignette Umber** (#140a02) - Deepest shadow, deboss wells, film-vignette corners, and the footer "parlor plinth" ground.
- **Deep Char** (#0b0805) - The absolute floor, reserved for the very center of deboss wells and the darkest vignette corners.
- **Warm Bone** (#e7d6b0) - Primary text ON the dark footer plinth; a softened parchment-family tint (not a chromatic accent) held at AA contrast against Vignette Umber.

## 3. Typography Rules

Three tiers of chrome plus one restricted "hand." Hierarchy is weight- and optical-size-driven, never color-driven. No system fonts, no generic serifs.

- **Display - Fraunces** (variable serif). The engraved documentary title card. Run at high optical size (opsz ~144), SOFT 0 / WONK 0 so it reads museum-grade and engraved, not trendy-quirky. Weight-driven hierarchy: connective words at ~340, the load-bearing nouns at ~600-900, within one line. Tight leading (~0.98), generous eyebrow tracking. Old-style (text) figures for dates and signatures. Always left-aligned, never centered. Headlines scale via clamp(); the emphasized clause gains weight, not color.
- **Body / reading - Newsreader** (optical serif by Production Type - a distinctive modern editorial face, explicitly NOT a generic Times/Georgia/Garamond/Palatino). All running deck copy, paragraphs, museum captions, and helper text. 18-20px, ~1.6 leading, max 65 characters per line. Iron-Gall Ink (#2b1a0c) on parchment; Warm Bone (#e7d6b0) on the dark footer. Warm, journal-grade, period-adjacent.
- **Mono / instrument-of-record - Space Mono**. Telegraphic metadata only: catalog numbers, dispatch timestamps, coordinates, word counts, field-input hints ("DISPATCH - DRAFT", "DISPATCHED 04:12"), and the eyebrow kickers. Uppercase, tracked +0.08em, in Signature Ink or Iron-Gall. Quiet, mechanical, the field telegraph.
- **The hand - Pinyon Script** (period copperplate). RESTRICTED EXCLUSIVELY to the rendered dispatch letter body inside the parchment card. It must never touch nav, buttons, labels, or any UI, or it becomes a wedding invitation.

Fallback stacks (last-resort load only, never the design intent): Fraunces -> serif; Newsreader -> serif; Space Mono -> monospace; Pinyon Script -> cursive. Generic serifs are banned as an intended choice.

## 4. Component Stylings

- **Primary button (magnetic):** Wax Seal Oxblood (#5a2a16) fill, Space Mono or Newsreader label in Field Parchment, slight period radius (~6px - never a pill). Magnetic physics with a nested "button-in-button" trailing seal-circle that eases behind the cursor. On :active it letterpresses INWARD - inset shadow deepens toward Vignette Umber, translate-y 1px - and releases on the settle curve. No outer glow, ever. **Exactly one Oxblood primary CTA per view. When a persistent/sticky nav is present, its call-to-action uses the ghost/secondary treatment - the single Oxblood primary fill is never shown twice in one viewport (nor duplicated against a section's own accent, e.g. the Letterify seal).**
- **Secondary button:** Ghost - 1px Foxed Edge (#cbae6e) hairline outline, Iron-Gall text, transparent fill. Used for the persistent nav call-to-action and quiet links (e.g., "watch a dispatch").
- **The Wax Seal (signature component):** The seal is SlowBurns' signifier and the single act of the whole experience - pressing it turns a mundane message into a dispatch. It exists in three strictly separated registers, and nowhere else:
  1. **The one pressable relief seal** - the Letterify submit control ("press the seal to dispatch"). This is the ONLY interactive, fully-rendered wax seal, and the only seal that ever moves: an irregular SVG edge, a dual cast shadow, an inset Candlelight specular where the flame catches the top, and a debossed "SB" monogram. At rest it lifts on hover (shadow grows, as if peelable); on press it stamps (scale 0.96, shadow tightens, specular sharpens) as the Oxblood wax radial-mask-reveals into a debossed well. It marks the single moment a mundane message becomes a dispatch.
  2. **Depicted seals** - product imagery, always already pressed and never interactive: the finished dispatch on the hero card, the parchment dispatches in the Vitrine examples, and the small type-height seal that stands in for the final period of the hero headline (an instance of inline image-typography). These depict a sealed letter; they are not controls and do not animate.
  3. **The flat brand mark** - in the header wordmark and the footer colophon only, a small FLAT debossed "SB" monogram glyph, never the relief object.
  There is never a loose or decorative seal. Only register 1 animates.
- **Double-bezel cards:** Outer hairline shell in Foxed Edge (#cbae6e) + inner core in Aged Parchment (#ecdcb0) with a Candlelight inset highlight along the top edge, concentric radii. The hero dispatch card is rotated ~-1.5deg (a letter laid on a desk) with faint Foxed-Edge ruled ledger lines; it un-rotates to 0deg on mobile.
- **The Vitrine (cataloged artifact):** Every photograph and every "before" screenshot is presented behind museum glass - a darkened vignette pulling toward Vignette Umber at the corners, faint foxing flecks at two edges, one soft specular that sweeps diagonally across the glass as the section scrolls into view (a docent's lamp passing over the case), then settles. Each is capped by a hairline Foxed-Edge brass plate carrying a Space Mono catalog number. All photography is real (picsum.photos) and sepia-duotoned in CSS - never a broken link, never clip-art.
- **Inputs (the letterify composer):** The textarea is styled as ruled ledger paper - label above in Space Mono, faint Foxed-Edge horizontal rules, Iron-Gall ink text. Focus state = Foxed-Edge border deepens + a soft Candlelight inset rim (luminance, not a colored glow ring). Error text below in Signature Ink. No floating labels.
- **Loaders:** No circular spinners. Text renders with a ruled-line shimmer; the video render uses a "developing print" skeleton - a low-contrast sepia block that resolves upward to full tone, matching the final card's dimensions.
- **Empty states:** Composed, not "no data" - an empty dispatch card with a single faint ruled line ("awaiting your word") and the seal at rest, indicating the one gesture that fills it.

## 5. Layout Principles

- CSS Grid first; contain everything in a max-width ~1400px centered field. No flexbox percentage/calc() math.
- Macro whitespace: section vertical rhythm py-24 to py-40, reducing proportionally via clamp(3rem, 8vw, 6rem) on mobile.
- **Header:** a thin parchment bar. Left: the "SlowBurns" wordmark in Fraunces beside the small flat "SB" monogram brand glyph (register 3, never a relief seal). Center-right: Space Mono nav links. Far right: the nav call-to-action rendered as a GHOST/secondary button (Foxed-Edge hairline outline) - the Oxblood primary fill is reserved for the hero, never duplicated here.
- **Hero:** asymmetric two-zone split, min-h-[100dvh]. LEFT column holds the type; RIGHT column holds the actual product (the rendered dispatch card, already sealed). Never centered. Clean, non-overlapping spatial zones - text never sits on top of the card or the tintype.
- **How it works:** a 2-column zig-zag, alternating type and Vitrine artifact down three steps. NEVER a row of three equal cards.
- **Examples / before -> after:** an asymmetric editorial grid or a horizontal catalog rail (one large feature dispatch beside two smaller), each item a Vitrine pairing the plain original with the parchment dispatch. Never a 3-equal-column card row.
- **Footer:** a full-bleed Vignette Umber (#140a02) "parlor plinth" - the page's warm parchment darkens into the film's deep vignette; Warm Bone text, a single small flat "SB" monogram mark (register 3, never a relief seal), Space Mono colophon.
- Deep vignette treatment on the hero and section edges as a film frame - subtle, corners only.
- Responsive: single-column collapse below 768px, no exceptions and no horizontal scroll. Inline hero image-typography stacks below the headline on mobile; the dispatch card un-rotates. All interactive targets >= 44px. Body text >= 1rem. Full-height sections use min-h-[100dvh], never h-screen.

## 6. Motion & Interaction

- **Global easing:** cubic-bezier(0.32,0.72,0,1) on everything. Nothing linear; nothing fast.
- **Scroll reveal (ink drying / print developing):** elements rise 16-24px while a 6px blur resolves to 0, staggered ~80-90ms per element; Vitrine images additionally fade from low-contrast sepia to full tone.
- **Signature perpetual micro-motion - the candlelight (the ONE ambient page-chrome motion):** a low-saturation radial light pool anchored upper-right breathes on a long ~9-12s ease, opacity drifting 0.9<->1.0 with the center nudging 4-6px, casting a living flicker across the paper. It is ambient luminance, never a UI rim-light or colored box-shadow.
- **Hero dispatch card - the seal is already pressed:** the hero card depicts a finished, sealed letter; its wax seal is statically depicted and does NOT stamp. On load the card arrives via the standard ink-drying reveal (rise + blur-resolve), not a separate seal animation. The single active stamp/press gesture in the entire experience belongs solely to the Letterify submit seal.
- **Hero dispatch card - Ken Burns preview (product imagery, not page chrome):** the card runs a true, imperceptible pan/zoom, scale 1.00 -> 1.06 over ~24s with a few pixels of drift - a muted live preview of the video product. It is the only perpetual motion besides the candlelight, and it is exempt from the "one ambient motion" rule precisely because it IS the product demonstrating itself, not decorative chrome.
- **Buttons:** letterpress deboss inward on :active; primary carries magnetic physics with the trailing nested seal-circle.
- **The Letterify seal (the one stamp):** at rest it lifts on hover; on press it stamps (scale 0.96, specular sharpens) as the Oxblood wax radial-mask-reveals into a debossed well. This is the only seal that animates anywhere.
- **Vitrine glass:** a slow specular sweep (docent's lamp) on scroll-into-view and again on hover.
- **Discipline & performance:** animate transform and opacity only - never top/left/width/height. Paper-grain / film-noise lives on a single fixed, pointer-events-none pseudo-element at ~0.03 opacity. No bouncing chevrons, no "scroll to explore," no marquees. The restraint is the point.

## 7. Anti-Patterns (Banned)

- No emojis anywhere.
- No Inter, Roboto, Arial, Open Sans, Helvetica, or any system font.
- No generic serifs (Times New Roman, Georgia, Garamond, Palatino). Distinctive serifs only (here: Fraunces for display, Newsreader for body - both distinctive modern editorial faces, never generic).
- No pure black (#000000) - use Vignette Umber (#140a02) or Deep Char (#0b0805).
- More than one accent color is banned. Wax Seal Oxblood (#5a2a16) is the ONLY chromatic accent; candlelight is luminance, not a second accent. Accent saturation stays < 80%.
- No neon, no AI-purple, no blue glows, no outer-glow shadows, no oversaturated accents, no gradient text on headers.
- No centered hero. No 3-equal-column card rows. No overlapping elements - every element in its own clean spatial zone.
- No two primary CTAs in one view. Exactly one Oxblood primary fill per viewport; a persistent nav's call-to-action is always the ghost/secondary treatment.
- No fabricated stats, metrics, uptime, response times, or "by the numbers" dashboards. Use [placeholder] labels if real data is absent.
- No "LABEL // YEAR" formatting. No generic placeholder names (John Doe, Acme, Nexus). No fake round numbers.
- No AI copy cliches (Elevate, Seamless, Unleash, Next-Gen). Copy is dry, reverent, documentary - a PBS narrator who does not know the letter is about a dentist appointment. No winking in the chrome.
- No filler UI text ("Scroll to explore," "Swipe down"), no scroll arrows, no bouncing chevrons.
- No broken image links - real photography via picsum.photos or inline SVG only.
- Product-specific costume-party bans: Pinyon Script is confined to the letter body only (never nav/buttons). The wax seal obeys the three-register doctrine - exactly ONE pressable relief seal that animates (the Letterify submit); all other seals are either statically-depicted product imagery (hero card, Vitrine examples, the inline headline period) or a small FLAT "SB" monogram brand glyph (header and footer). No loose or decorative seals. Grain held at ~0.03 - no torn-paper PNGs, no burnt edges, no heavy foxing, no treasure-map distressing. No western / "WANTED" slab display faces. No orange-teal or sepia-Instagram wash over everything. The seal must read as pressed physical wax (deboss + specular + cast shadow), never flat clip-art.
