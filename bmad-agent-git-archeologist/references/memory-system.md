# Memory System for GitArcheologist

**Sidecar location:** `{project-root}/_bmad/memory/bmad-agent-git-archeologist-sidecar/`

**Hindsight banks (resolved on activation):**
- `$BANK` — project bank. Restored feature context lands here.
- `$ARCHEOLOGY_BANK` (`${BANK}-archeology`) — meta-bank. Loss patterns, dig records, synthesized learnings.

## Two-Lane Architecture

The sidecar holds **agent-internal operational state**: in-flight digs, dig history log, access boundaries, user preferences. Loaded on activation.

Hindsight holds **project-level shared knowledge**: restored feature context, loss patterns. Written during/after every dig. This is the real deliverable of the agent's work.

Don't confuse the two. Sidecar = agent's notebook. Hindsight = project memory.

## Sidecar Files

### `index.md` — Primary Entry Point

Loaded on activation. Contains:

- Current active dig (if any) — feature name, lead, epoch bounds, progress
- Resolved bank names for this project
- Pointer to other sidecar files
- One-line summary of the last few completed digs

Updated immediately when a dig starts, progresses, or completes.

### `access-boundaries.md` — Access Control

Loaded on activation. Defines what the agent can read, write, and must never touch.

**Read access:**
- `{project-root}/.git` (via `git` CLI only, not direct reads)
- `{project-root}/docs/**`
- `{project-root}/_bmad/**`
- `{project-root}/app/**`, `{project-root}/extension/**` and other source trees (read-only during dig)
- `{project-root}/CLAUDE.md`
- Plane board (via MCP or `gh`/curl if CLI available)
- GitHub (via `gh` CLI)

**Write access:**
- `{project-root}/_bmad/memory/bmad-agent-git-archeologist-sidecar/**` — own sidecar
- Hindsight banks (via `hindsight memory retain`) — project bank and archeology bank
- Plane tickets (create/comment, if dig requires)
- GitHub PR comments (if dig requires)

**Deny zones:**
- Never modify source code during a dig. Archeology is observation and memory-writing, not refactoring.
- Never force-push, reset, or rewrite git history.
- Never delete archeology bank entries without explicit user instruction.

Before any write, verify the path is in-bounds. If uncertain, ask.

### `chronology.md` — Dig Log

Append-only. One line per dig: date, feature hunted, outcome (recovered/partial/cold), bank written to.

Prune entries older than six months unless they're referenced by a higher-order pattern in the archeology bank.

### `patterns.md` — User Preferences

Append-only. Captures how this user likes digs handled: narration register, tolerance for autonomous writes, preferred commit-range heuristics, etc.

## Persistence Strategy

**Write-through (immediate):**
- Restored feature context → Hindsight project bank
- Loss pattern → Hindsight archeology bank
- Dig record → `chronology.md`
- Active dig state → `index.md`

**Checkpoint (periodic):**
- `patterns.md` when user guidance accumulates
- Synthesis entries to archeology bank (via `review-losses` capability)

## First Run

If sidecar doesn't exist, load `./init.md` for onboarding.
