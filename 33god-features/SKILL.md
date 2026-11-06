---
name: 33god-features
description: Rules for the system-wide 33GOD feature migration (initiative I-9). Load before any change that adds, moves, installs, schedules or edits something spanning 33GOD repos - crank/zcrank, the ASM (asmctl, asm-tabpaint), Deckard agent state, pane/tab discovery, zellij calls, agent process or session detection, project identity from cwd, hook-hub handlers, hindsight hooks, target-watch, g33, git guards, a Hermes job or Candybar manifest that belongs to a feature, features.toml, feature.toml, pins, or any new script that reads panes, agents or sessions. Says which repo owns each shared building block, where new code goes, and what not to copy.
---

# 33GOD features: the migration rules

33GOD grew features (crank, tab painting, hindsight hooks…) that are spread across
repos, Hermes profiles and `~/.local/bin`, with 2-6 copies of the same building
block. We are moving, one slice at a time, to: **every feature in a formal repo,
every shared building block ("atom") with exactly one owner**. Every change you make
while this runs must move toward that, never away.

Where the truth lives (this skill holds rules, not status):

| What | Where |
|---|---|
| Catalog of features + atom owners | `~/code/33GOD/features.toml` |
| Progress, delegations, tickets | `~/code/33GOD/_bmad-output/planning-artifacts/initiatives.md` → **I-9** (and I-8 for crank) |
| Ownership study (why ASM + zellij-driver) | `…/planning-artifacts/33god-features/asm-ownership-study.md` |
| Feature design (manifest, lifecycle) | `…/planning-artifacts/33god-features/feature-packaging-design.md`; summary in `references/feature-anatomy.md` |

## Every prompt: the four checks

Before writing code, a script, a job, a hook or a schedule:

1. **Which feature is this?** Find it in `features.toml`. If it is not there, add a
   `[feature.<name>]` row (`status = "planned"`) in the same change.
2. **Which atoms does it read or do?** Look up each owner in `features.toml [atoms]`.
   Call the owner's interface. If that does not exist yet, call the listed
   `provisional` provider. **Never write a new copy** of pane listing, agent
   detection, session lookup, agent state, tab-name canon, zellij invocation or
   project identity. If you truly must, file a ticket on the owner's board and say
   so in your report.
3. **Where does the code go?** In the feature's `repo`. If that repo does not exist
   yet (`status` is `scattered` or `embedded`), change the piece where it lives today.
   Never start a new location, and never put logic in a Hermes profile or
   `~/.local/bin` copy. Those hold links and rendered stubs only.
4. **Does it respect the layers?** A lower layer never imports, calls or names a
   higher one (table below).

## Rules

Decided by the operator on 2026-11-06:

- **F1. A feature lives in a formal repo.** Formal means its own GitHub repo,
  `.project.json` with a Plane board, BMAD, registered with pj, a 33GOD submodule,
  and `feature.toml` at its root. Crank is the first one (`delorenj/crank`).
- **F2. `33GOD/features.toml` is the catalog and the planning map.** Keep it true
  whether or not anything reads it. An install disables features only in its own
  untracked `~/.config/33god/features.toml` (`[disable] crank = "reason"`).
- **F3. No pins.** Features track main. A pin is a temporary bandage that carries a
  reason and an open exit ticket, and it is removed as soon as the fix merges.
  Precedent: CAND-49's pinned Hermes image, dropped by CAND-52.

Standing rules carried by the design:

- **One owner per atom.** Any other implementation is either `provisional` (until
  the owner's interface passes a live differential) or declared `[[implements]]`
  and checked live. Products (Deckard, Wingman) and control surfaces (pj,
  Holocene) consume. They never own a primitive. PJAN-202's `panes.ts` is the
  cautionary tale: good code in the wrong layer.
- **Hosts hold pointers, never logic.** A Hermes profile holds only generated
  stubs, and all logic runs from one checkout. The stale profile `zcrank.py` is
  what goes wrong otherwise.
- **Address by name. Ids live only in receipts.** Never hardcode a Hermes job id,
  a Candybar id, a zellij session name ("Workspace") or `/home/delorenj` in feature code.
- **Clock last on install, first on remove.** Candybar is the only clock (load
  the `candybar` skill).
- **The world beats the receipt.** Uninstall sweeps everything matching a
  feature's claims. A receipt only permits deleting what still matches it;
  anything foreign is quarantined, not deleted.
- **No fixtures.** Atom contracts carry live probes. Redis `127.0.0.1:6379` is
  production: tests use a throwaway `redis-server` on a random port, deletes are
  `SCAN` + `DEL` of exact keys on an explicit `-p`, and nothing ever runs `FLUSH*`.

## Layers (proposed, awaiting approval; see I-9)

| Layer | Owns | Must never |
|---|---|---|
| L0 Host: zellij, /proc, Redis, NATS, systemd | Raw machinery | Hold 33GOD logic |
| L1a **bloodbank** | Hook intake (`hooks.master.json`, bb-hook, hook-hub), event schemas, transport | Hold a state fold, import the ASM in-process (it does today: `publisher.py:136`), name a product in a subject (`deckard.evt.attention`) |
| L1b **zellij-driver** (repurposed) | Every zellij call: topology by tab/pane id, readiness, focus, rename, verified pane input | Know what an agent is |
| L2 **asm** (new, out of bloodbank) | Agent process detection, identity (pid + start time; Hermes profile when headless), native session id, live state, attention/ack | Type into a pane, focus, rename, or use a pane as identity |
| L2' Peer owners: pjangler (project identity), Candybar (clock), Krebs (ticket lifecycle) | One fact each | Re-derive agent or terminal state |
| L3 Features: crank, hindsight-hooks… | Their own state (`zcrank:*`), jobs and schedules | Keep a private copy of topology, detection or state |
| L4 Control surfaces: pj, Holocene | Wrapping and chaining lower commands, read models | Grow their own primitive |
| L5 Products: Deckard, Wingman, painters | Rendering and acting through lower layers. Deckard's lights and media are commands to delohome, playerctl and wpctl | Run a second agent-state machine |

Until the split is approved, today's homes stand. The ASM code is in
`bloodbank/services/agent-hooks/` and the best pane/agent reader is
`pj crank panes --json` (provisional). Read through those, and do not add new readers.

## Not yours to decide (open operator decisions)

Leave these alone and ask, or work around them:

- Approve the ASM / zellij-driver split, and the repo name and visibility for `asm`.
- Whether to repurpose zellij-driver or start a fresh terminal-driver repo.
- Deckard's stranger-install goal (ADR-001/G6): keep a no-Redis fallback fold, or require the ASM.
- Whether a failed tool call is "red", and how long amber (needs-input) lasts.
- The 15 s `asm-sweep.timer`: a recorded exception in the asm repo, or compute staleness on read.
- Whether an embedded `features/<name>/` folder inside an owning repo satisfies F1.
- Who owns the crank registry (crank repo, recommended, or pjangler as I-8 says today).

## Live traps (2026-11-06; re-verify before relying on them)

- **ASM identity has been broken since 2026-09-13 (BB-33).** Claude agents appear
  twice, ghost rows `asm:a:*:x:22822.11015` never expire, and `session_id` is
  empty on every row. Do not build on `asm:a:*` session ids until BB-33 lands.
- **`test_asm.py` defaults to production Redis (BB-32).** Never run it bare.
- **The Hermes economics cap on crank-beat stays until I-8 lands.** It is the
  operator's call. Candybar logs a cap refusal as success, so read
  `~/.hermes/profiles/33god-pm/cron/usage_audit.jsonl` for the truth.
- **crank-watchdog's argv keeps `candybar.transition_exec`.** It is the only
  writer of the report that `zcrank-gate` reads.
- **Two Hermes jobs are named `cronjob_manage`** (777c511a009c and 9b5dadbd1e4d),
  so lookup by name raises `AmbiguousJobReference`. Rename them before addressing
  either by name.
- **Deployed binaries lag main.** Deckard (2026-10-15) lacks the DECK-42
  readiness check. The pj main checkout may lack recent pjangler work, so rebuild
  before trusting `pj` output.

## Commands

| Today | Planned (`†` = does not exist yet; never call it) |
|---|---|
| `pj crank panes --json` (agent panes, provisional) | `asmctl agents --json --topology`† |
| `asmctl` (human output) | `asmctl state|watch|doctor --json`† |
| `deckard status` | `zdrive tabs|panes|focus|rename|send --json`† |
| `uv run candybar show|history|doctor` | `pj feature check|plan|apply|remove|why`† |
| `px` on the owning board | `GET :8764/v1/resolve?cwd=`† |

## When something lands

Update `features.toml` (status, atom `state`) and I-9's delegations first. Then,
if a rule or decision changed, update this skill in `~/code/skillex/all-skills/33god-features/`
(delorenj/skills), push it, and bump the `all-skills` pointer in `~/code/skillex`.
Don't record status here. Status belongs in I-9 and `features.toml`.
