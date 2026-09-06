# Making a tab impossible to miss

The user has ADHD and runs ~16–30 tabs. "An agent needs you" must be visible without
him going looking. A subtle `[!]` does not clear that bar. This is the design space,
with the dead ends marked so nobody re-explores them.

## What the `[!]` already is

Zellij's **native visual bell**. Not a plugin.

- Option `visual_bell`, **default true**. Doc text: *"Whether to show visual bell
  indicators (pane/tab frame flash and `[!]` suffix)"*.
- Triggered by the terminal BEL byte `0x07` written by any process in the pane. No OSC
  involved.
- Claude Code writes it itself — its `preferredNotifChannel` is unset, which resolves to
  `terminal_bell` on Alacritty.
- It already includes a **400 ms frame flash** the user has never noticed.

It surfaces as two fields on `TabInfo`, readable by any plugin **and** by
`zellij action list-tabs --json`:

```
has_bell_notification   # persistent
is_flashing_bell        # transient, 400 ms
```

**Nothing on this machine reads either one.** That is the untapped amplification hook:
the signal already exists and is already correct — it just has no loud consumer.

## The hard constraint

> A plugin that changes the tab **name** can never glow. The tab bar renders that name
> with one uniform style. To get loud you must own the **renderer**, not the string.

This is why `zellij-attention` can never satisfy the requirement: its only mutating
capability is `rename_tab`, so its ceiling is prepending `⏳` to a tab name. It also has
never actually loaded, so its emitter has been piping into the void.

Ruled out for the same reason: **zjstatus cannot flash one specific tab.** `tab_normal`
and `tab_active` are *global* formats applied to every tab of that class. There is no
per-tab-id conditional formatting and no external state injection into the `{tabs}`
widget. The only per-tab variable controllable from outside is `{name}`, and formatting
directives inside `{name}` are not re-rendered.

## What is possible

The tab bar is just a plugin pane (`zellij:tab-bar` in the layout), so a replacement can
render anything a terminal can — 24-bit colour included.

Animation is confirmed supported:

- `set_timeout(secs)` requires no permission and fires `Event::Timer`.
- Returning `true` from `update()` triggers a re-render.
- Timer → mutate state → return true → `render()` is a working loop at any framerate.
  zjstatus v0.24.0 shipped "timer-based idle refresh" on exactly this mechanism.

Two constraints learned the hard way:

1. **Prefer timer-driven colour cycling over SGR blink.** `slow_blink`/`fast_blink`
   depend on the host terminal honouring them; Alacritty's support is unreliable and
   many users disable it. A 4–8 fps hue cycle looks louder and works everywhere, and it
   gives gradients rather than binary on/off.
2. **Budget the framerate.** wasmi is an interpreter. With 30 tabs, animate only while
   something is actually alerting, and cancel the timer at idle.

Screen real estate matters too: the tab bar is one row, so a glow there is
width-constrained. A **sidebar** or floating pane gives far more room for genuinely loud
visuals — that is the zj-radar approach.

## The asset already on disk

`plugins/zellij_visual_notifications.wasm` is **the user's own plugin**, built January
2026 against zellij-tile 0.43.1 (which is fine — there is no version gate).

Config keys recovered from the binary:

```
enabled  debug  show_status_bar  show_border_colors  show_tab_badges
notification_timeout_ms  queue_max_size  theme
success_color  error_color  warning_color  info_color
animation_enabled  animation_style  animation_speed  animation_cycles
high_contrast  reduced_motion  ipc_socket_path
```

- `animation_style` ∈ `pulse` | `flash` | `breathe`
- Pipe names it listens for: `notification` | `clear` | `config_reload`
- Wire format: a `NotificationMessage` carrying
  `version type source pane_id tab_index priority timestamp ttl_ms command exit_code duration_ms`
- `type` values: `success completed failed failure warning information running working
  attention waiting input input_needed`
- Debug lines to confirm receipt: `Queueing notification: type=`,
  `No pane_id, notification queued but no visual state updated`

A config block for it exists in `layouts/agent-orchestrator.kdl`, which is not the
default layout — so it had never run in seven months.

### …and why it still cannot do this job — measured 2026-08-23

It was finally loaded and driven end to end. **It does not solve cross-tab attention,
and adding it to `load_plugins` is worse than useless.** Three findings, from its own
debug output:

1. **A `load_plugins` entry is a BACKGROUND plugin and gets no render surface.** Its log
   says `render() called: rows=0, cols=0`. It draws literally nothing. Listing it there
   *looks* like wiring while being a no-op — which is very likely why it sat "installed"
   for seven months.
2. **Even hosted in a real pane, its entire output is a one-line bar inside its own
   pane.** Captured verbatim with a notification queued:
   `🔔 \u{1b}[38;2;234;179;8m[❗!!:13*]\u{1b}[0m (+1 queued)` — i.e. the same subtle
   marker that is useless across 16–30 tabs.
3. **It has no tab-mutating call in its compiled symbols** — only
   `update_pane_visual_state`, `handle_notification_message`, `fg_escape`. It can never
   mark tab 7 while you are looking at tab 3, which is the whole requirement. (The
   `RenameTab` strings inside the `.wasm` come from the zellij-tile Action table that
   every plugin embeds, not from its own code.)

So it is a *pane* status bar, not a tab annunciator. If you ever want that bar, give it
a pane — see `layouts/agent-orchestrator.kdl`. Do not put it in `load_plugins`.

### What actually works cross-tab

The only stock-zellij mechanism that changes how **one** tab looks from **any other** tab
is the tab **name**. The painter uses `rename-tab-by-id`, which:

- mutates a tab by stable id **without stealing focus** — yanking focus off whatever the
  user is doing would be worse than no alert;
- still works when **no client is attached**, which matters because
  `go-to-tab-name` and `close-tab` are silent no-ops in that state.

### What paints it — one state machine, many surfaces

Superseded on 2026-09-05. The first version was a per-session daemon driven by
`~/.claude/settings.json` hooks, which meant it ran **its own state machine** — and,
being wired into one CLI's settings file, a codex pane could never light up at all no
matter what codex did.

Bloodbank already has the real thing: the **Agent State Machine** (`asm:*` in Redis,
`services/agent-hooks/core/asm.lua`). Every CLI's hooks propose signals into it, a
15s sweeper contributes the two facts the bus can never carry, and `asm.lua` arbitrates
under EVAL. The tab painter is now a **surface**: it reads `asm:*` and renames tabs.

**Do not build a second projector.** Two folds of one event stream are two answers to
one question, and they will disagree — that is exactly how the hook-era painter ended
up blind to codex while claiming to be agent-agnostic.

| ASM state | glyph | behaviour |
|---|---|---|
| `starting` `working` `tool_running` `delegating` | 🟢 | **blinks forever** |
| `awaiting_human` | 🔔 | steady; **clears on focus** |
| `failed` `stale` | 🔴 | steady |
| `idle` `unknown` `gone` | — | no marker |

The organising rule: **motion means busy, stillness means waiting on you.** Only the
active states blink — if everything blinked, nothing would read as urgent.

A tab holds several panes, so it shows the **worst** of them by precedence
(`awaiting_human` > red > active). One agent asking a question must not be hidden by its
neighbour merely working.

Three deliberate asymmetries, each of which looks like a bug until you know why:

- **`awaiting_human` clears when you navigate to the tab; `failed` does not.** Arriving
  *is* the acknowledgement for "answer me", but an unresolved failure should survive a
  glance and a move-on. The painter fires this as an `ack` **signal** through `asm.lua`
  rather than writing the state — a surface may propose, never decide.
- **Mid-turn traffic never clobbers `awaiting_human`.** A tool call firing must not erase
  the bell. But *starting new work* does clear it: being approved and carrying on is
  proof the human already unblocked you.
- **A discovered-but-silent agent is `unknown`, never `idle`.** Silence really does
  suggest rest — but that is an inference, and some CLIs have no hooks wired at all.

`stale` and `gone` are the states that make the bar honest, and neither has a triggering
hook by definition: `gone` is `/proc/<pid>` vanishing, which is not an event. Without
`asm-sweep.timer` running, dead agents stay frozen at their last state and the bar
quietly lies.

The costs that shape the painter were measured:

| call | cost | why it matters |
|---|---|---|
| `rename-tab-by-id` | **~2ms** | fire-and-forget, no reply awaited — blinking is nearly free |
| `list-panes --tab` | **~104ms** | tab→pane topology; refreshed every 10 frames, not every frame |
| `list-panes --json` | **~4700ms** | resolves every pane's command out of `ps`. **Never** use it here |
| `list-tabs --state` | **~103ms** | gives the ACTIVE column; only called when a bell is outstanding |

So it re-renames a tab only when the computed name actually *changes*, and it blocks on
a `SUBSCRIBE asm:transitions` read whose timeout **is** the frame interval — every wake
either delivers a real transition or is the next blink. Given this box's history of
being wedged by sustained polling, that conditionality is the point.

**Trap, cost an hour:** `read` returns non-zero at EOF even when it *did* populate the
variables — which a file written without a trailing newline always hits. A
`read ... || continue` in a render loop therefore skips every tab and paints nothing,
silently. Gate on the value, never on `read`'s exit status.

**The blink must not change the tab's width.** The first version wrapped the name in
three glyphs a side and toggled the whole thing on and off — `🔔🔔🔔 Deckard 🔔🔔🔔` is
21 columns, `Deckard` is 7, so a marked tab shoved every tab after it 14 columns
sideways four times a second. Now it appends **one** glyph and the blink *swaps* it for
a partner of identical width (`🟢` ⇄ `⚫`), so the bar never reflows.

That makes East_Asian_Width the binding constraint, and it is easy to break by eye:

| glyph | codepoint | EAW | safe as a marker? |
|---|---|---|---|
| `🔔` `🔴` `✅` `🟠` `⚫` `🔕` | U+1F514, U+1F534, U+2705, U+1F7E0, U+26AB, U+1F515 | **W** | yes — exactly 2 columns |
| `⚠️` `▫️` | U+26A0/U+25AB **+ VS16** | ambiguous | **no** — narrow base; terminals disagree on 1 vs 2 |
| `·` | U+00B7 | A | no — usually 1 column |
| `　` | U+3000 | F | 2 columns and invisible, but it is trailing whitespace and liable to be trimmed |

`⚠️` was in the original set and was itself a jitter source; `🟠` replaced it. Check any
replacement with
`python3 -c "import unicodedata;print(unicodedata.east_asian_width('X'))"` and require
`W`. The partner glyph is `TABPAINT_BLINK_ALT`.

This lands exactly on the ceiling described above — a name change, not a glow. That is
the honest maximum without owning the renderer. To go past it you must replace the
tab-bar plugin itself (fork `zellij:tab-bar`, or adopt zj-radar / zellaude below).

## Attribution — which tab fired?

| Source | Carries pane id? |
|---|---|
| Inside the pane: `$ZELLIJ_PANE_ID`, `$ZELLIJ_SESSION_NAME` | **Yes** — authoritative |
| `deckard.evt.attention` (NATS) | **Yes** — `zellij_pane_id`, `zellij_session_name` |
| `bloodbank.evt.agent.>` (NATS) | **Yes**, since 2026-09-04 — `zellij_origin()` in the agent-hooks publisher |
| `asm:a:{scope}` (Redis) | **Yes** — `zellij_pane` / `zellij_session` fields, plus `asm:idx:pane:{sess}:{pane}` |

A field census over 85 live envelopes, grepping every field name for
`pane|tab|zellij|pid|tty|mux`, once found **nothing** — attribution was
`data.working_directory` plus `actor.cli`, which cannot separate two tabs in the same
repo. `zellij_origin()` fixed that for every surface at once.

**But the pane is not the agent's identity, and this was settled by measurement, not
taste.** Pane presence is not a per-process invariant: over 12h of live events, 33 of 90
codex correlation-sessions contained *both* paned and unpaned events, and codex
`session.started` was 0/9 paned against 635/734 paned tool events. Headless hermes is
0/1292. So the ASM keys on the agent **process** (`cli:p:pid.starttime`) and carries the
pane as a field plus a secondary index. A pane-keyed store files one agent's tool events
and its session events in two different rows.

## Existing notification paths

Already working, and worth reusing rather than duplicating:

| Path | Status |
|---|---|
| `claude-notify` → `paplay` + ntfy push | audible + phone |
| `nlp hook notification` → Redis → Nanoleaf hex | **physical light wall** |
| deckard attention hook → `deckard.evt.attention` → amber key | Stream Deck |
| `zellij pipe zellij-attention::waiting::$ZELLIJ_PANE_ID` | **dead** — plugin never loaded |
| `bin/asm-tabpaint` → `asm:*` → tab glyph | **the tab bar**, since 2026-09-05 |

Each of these grew its own fold of the same stream — the Nanoleaf wall reconciles
`nlp:*` keys, Deckard keeps a private redb store, the tab painter had `agentstate:*`.
That is four state machines for one question. The ASM exists to be the one; point a new
surface at `asm:*` rather than inventing a fifth path.

Note `bloodbank.agent.session.ended` is misleadingly named: the Claude adapter maps
its `Stop` hook to it, and `Stop` fires at the end of *every* assistant turn. It means
"the agent stopped and is waiting for you", it fires many times per session, and it
fires under `--dangerously-skip-permissions`.

## Off-the-shelf, if maintaining a plugin is not wanted

- **[zj-radar](https://github.com/marktoda/zj-radar)** — pinned sidebar, live per-tab
  AI-agent status (`◆ needs you`, `⠋ working`, `● done`, `✗ error`, `○ idle`), repo +
  branch + elapsed, **click a row to jump to that tab**. Push-driven via `zellij pipe`
  from agent hooks. Requires zellij **≥ 0.44.3 exactly** — which is what is installed.
- **[zellaude](https://github.com/ishefi/zellaude)** — tab-bar replacement with per-tab
  Claude state glyphs and colours; auto-registers its own hooks.
- **[captain-miao](https://github.com/hyperlogue/captain-miao)** — standalone TUI
  mission control: status, cwd, model, context usage, git branch, transcript preview.

zj-radar's architecture is the model to copy regardless of whether it is adopted:
status arrives via an explicit `zellij pipe` broadcast from per-agent hooks, and runtime
reconfiguration happens over the same channel
(`zellij pipe --name zj_radar.config.v1 -- '{"density":"compact"}'`) rather than by
editing the layout.
