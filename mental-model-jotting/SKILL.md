---
name: mental-model-jotting
description: Capture durable mental-model memories during a work session with the `jot` command, so the session-end hook can flush them into question-framed Hindsight memories. Use whenever you learn something worth remembering — a gotcha, a non-obvious decision, negative knowledge ("X did NOT work"), a surprising discovery, or a "future-me will ask this" fact — and you want it to survive past this session. Triggers:"remember this, "jot that down", "capture this", "note for later", "save this insight", mental model, write-ahead memory, hindsight capture.
---

# Mental-Model Jotting

A **write-ahead log for memory.** The moment you hit something worth remembering, run `jot`. At session end a hook hands your jots to a cheap model that question-frames, dedups, and retains them into Hindsight. You make the _significance judgement_ (the expensive part, and only you have the reasoning); the flush does the mechanical polishing for free.

## The one command

```bash
jot "whatever you just learned, phrased however — one line"
```

That's it. Append as many as you want during the session; each is one line. Don't polish wording — the flush rewrites each into a question-framed memory. **Be specific**: keep exact names, paths, ports, flags, commands, error strings. A vague jot produces a vague memory.

## When to jot (the significance bar)

Jot when a fact would save a future engineer real time and is **not obvious from the code**:

- **Gotchas / footguns** — "zellij 0.44 can't name a token at creation (clap bug); rename it in tokens.db after."
- **Non-obvious decisions + the why** — "bind zellij to 0.0.0.0 not loopback because Traefik reaches the host via host.docker.internal."
- **Negative knowledge** — "`opencode run` is too slow for hooks (>2min); call the model API directly." Prevents repeating a dead end.
- **Surprising discoveries** — "hindsight hook scripts are hardlinked across ~/.agents and ~/.claude."
- **"Future-me will ask X"** — anything you'd want to re-derive later. Phrase toward the question if it helps.

## When NOT to jot

- Trivia, one-offs, or anything obvious from reading the code.
- Things already captured this session (the flush dedups, but don't spam).
- Secrets/tokens — jot the _shape_ ("token lives in $X"), never the value.

Prefer a few high-signal jots over many marginal ones. An empty jotfile is a fine outcome — the flush costs nothing when there's nothing to say.

## How it flows (you don't manage any of this)

1. `jot "…"` → appends to `~/.agents/journal/jots/<cwd-hash>.md` (worktrees isolate; override with `$HINDSIGHT_JOTFILE`).
2. Session ends → the `Stop`/session-end hook calls `hindsight-jot-flush.sh`.
3. It sends the jots to `deepseek-v4-flash` (direct HTTP), which emits `MEM|<context>|<question-framed memory>` lines, deduped against what was already retained this session.
4. Each is `hindsight memory retain`'d to the resolved bank; the jotfile is archived.

Because recall is **semantic, not tag-based**, memories are phrased to open with the question a future engineer would ask. You can jot in that shape too, but you don't have to.

## Related

- Retain a fact _right now_ (don't wait for session end): `hindsight memory retain <bank> "<fact>" --context <cat>` — see the `hindsight` skill.
- The habit is reinforced by the `question-framed-memories` feedback memory loaded each session.
