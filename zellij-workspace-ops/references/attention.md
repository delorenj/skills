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
is the tab **name**. `scripts/zellij-notify` uses `rename-tab-by-id`, which:

- mutates a tab by stable id **without stealing focus** — yanking focus off whatever the
  user is doing would be worse than no alert;
- still works when **no client is attached**, which matters because
  `go-to-tab-name` and `close-tab` are silent no-ops in that state.

It is wired to Claude Code's `Notification` hook (mark) and `UserPromptSubmit` (clear),
and follows the hook contract: never blocks, never fails a turn, no-op + exit 0 outside
zellij.

This lands exactly on the ceiling described above — a name change, not a glow. That is
the honest maximum without owning the renderer. To go past it you must replace the
tab-bar plugin itself (fork `zellij:tab-bar`, or adopt zj-radar / zellaude below).

## Attribution — which tab fired?

| Source | Carries pane id? |
|---|---|
| Inside the pane: `$ZELLIJ_PANE_ID`, `$ZELLIJ_SESSION_NAME` | **Yes** — authoritative |
| `deckard.evt.attention` (NATS) | **Yes** — `zellij_pane_id`, `zellij_session_name` |
| `bloodbank.evt.agent.>` (NATS) | **No** |

A field census over 85 live bloodbank envelopes, grepping every field name for
`pane|tab|zellij|pid|tty|mux`, found **nothing**. There, `data.working_directory` plus
`actor.cli` is the only attribution — which cannot separate two tabs in the same repo.

**The highest-leverage upstream fix is to publish `zellij_pane_id` on the main
bloodbank envelope.** One change makes attribution exact for every surface at once: the
Stream Deck, the Nanoleaf wall, and any tab animator.

## Existing notification paths

Already working, and worth reusing rather than duplicating:

| Path | Status |
|---|---|
| `claude-notify` → `paplay` + ntfy push | audible + phone |
| `nlp hook notification` → Redis → Nanoleaf hex | **physical light wall** |
| deckard attention hook → `deckard.evt.attention` → amber key | Stream Deck |
| `zellij pipe zellij-attention::waiting::$ZELLIJ_PANE_ID` | **dead** — plugin never loaded |

One event stream already feeds a Stream Deck and a light wall. **The tab bar is the
third consumer that was never written.** Prefer subscribing to the existing stream over
inventing a fourth path.

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
