---
pipeline-status:
  - new
---
# Claude Code Journal Pipeline

A telemetry + reflection pipeline that produces a plain-English journal of how each Claude Code session interacted with Hindsight. Runs entirely via Claude Code hooks; no Claude action required.

This is the **Claude Code analog** of the OpenClaw plugin integration documented in `SKILL.md`. Both layers retain into the same banks; they're independent and complementary.

## What it produces

One markdown file per Claude Code session at `~/.claude/.hindsight-journal/YYYY-mm-dd-h-m-s.md` (timestamp = session start, local time). Each Stop event during the session rewrites the file with fresh telemetry, so the final state is the canonical record.

The journal answers six questions, in this order:

1. **Search terms elicited & how selected** — every prompt that triggered (or was evaluated for) a recall, with prompt length and the first 120 chars.
2. **Why recall was skipped** — when it was, and which guard rule fired (`empty_prompt`, `prompt_under_min_length`, `hindsight_binary_missing`).
3. **Bank resolved** — primary bank, banks touched, linked banks reached via Dream fanout, per-bank call/line counts.
4. **Effectiveness of returned data** *(LLM-synthesized)* — assesses whether recall plausibly saved tokens or surfaced noise.
5. **What could have been done differently in past sessions** *(LLM-synthesized)* — speculates on retain habits / tagging / bank scope that would have made *this* recall yield better hits.
6. **What was retained + rationale** — 6a lists every retain event from the session; 6b *(LLM-synthesized)* evaluates whether each reads as a self-contained fact or leans on stale references.

Plus a frontmatter block with counts/flags and a raw-telemetry JSONL appendix.

## Pipeline architecture

```
                 prompt arrives
                       │
                       ▼
  ┌──────────────────────────────────────┐
  │ UserPromptSubmit hook                │
  │ hindsight-recall.sh                  │──► writes <session_id>.jsonl
  │   - resolves bank                    │     {event:"recall", ...}
  │   - queries Hindsight                │     {event:"recall_skipped", ...}
  │   - injects context into prompt      │
  └──────────────────────────────────────┘
                       │
                Claude does work
                       │
  ┌──────────────────────────────────────┐
  │ PostToolUse hook (Write|Edit|MultiEdit) │
  │ hindsight-retain.sh                  │──► appends {event:"retain", ...}
  │   - retains edited file context      │
  └──────────────────────────────────────┘
                       │
              Claude finishes turn
                       │
  ┌──────────────────────────────────────┐
  │ Stop hook                            │
  │ hindsight-session-end.sh             │
  │   ├─ daemonizes journal-write.sh     │──► reads JSONL, calls reflect,
  │   │  (setsid + nohup, survives the   │     writes ~/.claude/.hindsight-journal/<start>.md
  │   │   hook's process-group reap)     │
  │   └─ legacy session-summary retain   │
  └──────────────────────────────────────┘
```

## File map

| Path | Role |
| --- | --- |
| `~/.claude/hooks/hindsight-recall.sh` | UserPromptSubmit — injects recall context, logs `recall` / `recall_skipped` events |
| `~/.claude/hooks/hindsight-retain.sh` | PostToolUse (file writes) — retains edit context, logs `retain` events |
| `~/.claude/hooks/hindsight-session-end.sh` | Stop — daemonizes the journal writer + legacy session-summary retain |
| `~/.claude/hooks/hindsight-journal-write.sh` | Reads telemetry, calls reflect, writes the journal markdown |
| `~/.claude/hooks/lib/hindsight-journal.sh` | Shared `journal_log` + `journal_session_id_from` helpers |
| `~/.claude/hooks/lib/hindsight-bank.sh` | Shared bank resolver (used by all three hooks) |
| `~/.claude/.hindsight-journal/YYYY-mm-dd-h-m-s.md` | Journal entries (one per session) |
| `~/.claude/.hindsight-journal/.sessions/<session_id>.jsonl` | Per-session telemetry log (append-only) |
| `~/.claude/.hindsight-journal/.sessions/<session_id>.reflect.txt` | Cached reflect output (debounced) |

## Telemetry event schema

The JSONL log carries three event types. All include `ts` (UTC ISO-8601) injected by the logger:

```jsonc
// User prompt triggered a recall
{ "event": "recall",
  "bank": "claude-runtime",
  "prompt_len": 84,
  "prompt_first120": "...",
  "primary_lines": 30,        // lines returned from primary bank
  "fallback_lines": 15,       // lines from 'general' fallback
  "linked_lines": 0,          // lines from Dream-fanout linked banks
  "total_lines": 45,
  "total_chars": 8345,
  "linked_banks": [],         // names of linked banks consulted
  "returned_anything": true,
  "ts": "2026-05-11T10:55:22Z" }

// Recall was skipped before hitting the API
{ "event": "recall_skipped",
  "reason": "prompt_under_min_length",   // empty_prompt | prompt_under_min_length | hindsight_binary_missing
  "min_length": 24,
  "prompt_len": 2,
  "prompt_first120": "hi",
  "ts": "..." }

// A file edit triggered a retain
{ "event": "retain",
  "bank": "claude-runtime",
  "context": "code-edit",
  "file": "hooks/foo.sh",
  "ext": "sh",
  "content_len": 80,
  "snippet": "...",
  "retained_text": "Edited hooks/foo.sh (sh): ...",
  "source": "auto_posttooluse",
  "ts": "..." }
```

## Environment knobs

All optional; reasonable defaults work out of the box.

| Variable | Default | Purpose |
| --- | --- | --- |
| `HS_JOURNAL_DIR` | `~/.claude/.hindsight-journal` | Root for markdown + `.sessions/` |
| `HS_JOURNAL_REFLECT` | `1` | `0` disables LLM-reflected sections entirely |
| `HS_JOURNAL_REFLECT_BUDGET` | `low` | `low` \| `mid` \| `high` — passed through to `hindsight memory reflect` |
| `HS_JOURNAL_REFLECT_DEBOUNCE_SECONDS` | `240` | Min seconds between fresh reflect calls per session; cached output is reused inside this window |
| `HS_JOURNAL_REFLECT_BANK` | cwd-resolved bank | Override which bank reflect runs against |
| `HS_JOURNAL_KEEP_TELEMETRY` | `1` | `0` deletes the JSONL after each successful journal write |
| `HINDSIGHT_PRIMARY_LINES` | `30` | Cap for primary-bank recall output lines (lives on `hindsight-recall.sh`, not journal-specific) |
| `HINDSIGHT_FALLBACK_LINES` | `15` | Same, for the `general` fallback |
| `HINDSIGHT_FANOUT` | `1` | `0` disables Dream-graph linked-bank fanout |
| `HINDSIGHT_FANOUT_MAX` | `2` | Cap on linked banks per recall |

## Manual operations

### Regenerate a session's journal

```bash
echo '{"session_id":"<uuid>","cwd":"/path/to/cwd"}' \
  | ~/.claude/hooks/hindsight-journal-write.sh
```

The script is idempotent: it always overwrites the same file (derived from the earliest event's timestamp).

### Force a fresh reflect

```bash
rm ~/.claude/.hindsight-journal/.sessions/<session_id>.reflect.txt
# then re-invoke as above
```

### Inspect raw telemetry

```bash
jq -c '{event, bank, total_lines, file}' \
  ~/.claude/.hindsight-journal/.sessions/<session_id>.jsonl
```

### Find the journal for the current session

The current `session_id` is in the hook JSON; if you don't have it handy, the most recent `.sessions/*.jsonl` by mtime is the current session's log:

```bash
ls -t ~/.claude/.hindsight-journal/.sessions/*.jsonl | head -1
```

## Known limitations

### Hindsight server reflect can return tool-call stubs

When the telemetry payload is thin (few recall/retain events), the backend model attached to `hindsight memory reflect` sometimes emits `<minimax:tool_call><invoke name="search_observations">...` instead of prose. The journal writer detects this pattern (and the related `<tool_call>` / `<tool:tool_call>` patterns) and writes a clear failure note instead of corrupted content:

> _Reflection failed: reflect backend returned a malformed tool-call stub instead of prose (raw saved to /tmp/hs-journal-reflect.out — likely a hindsight server prompt/template issue)_

The raw output is preserved at `/tmp/hs-journal-reflect.out` for inspection. This is a server-side template issue; the client plumbing is correct. Rich telemetry (3+ events) typically yields clean prose.

### Stop hooks fire per-turn, not per-session

Claude Code's Stop event fires after every assistant response, not just at session close. The pipeline handles this by:

- **Per-session filename** — derived from the *earliest* JSONL event timestamp, so each Stop overwrites the same file
- **Reflect debounce** — fresh reflect runs at most once per `HS_JOURNAL_REFLECT_DEBOUNCE_SECONDS`; subsequent Stops reuse the cached `<session_id>.reflect.txt`
- **Daemonized writer** — `hindsight-session-end.sh` launches the journal writer via `setsid nohup … </dev/null >/dev/null 2>&1 &`. Without this, Claude Code's hook reaper kills the writer mid-reflect (the 30-second LLM call never completes).

### `bash printf` and leading-dash format strings

Internal note for editors: `printf '- ...'` is interpreted by bash's builtin printf as a `-` flag attempt and fails with `invalid option`. Use `printf '%s\n' '- ...'` instead. The writer has been audited for this pattern.

### No discrete keyword extraction

The recall hook passes the full user prompt verbatim to `hindsight memory recall`; the server's embedding model handles semantic matching. The journal documents this honestly in section 1. If you want keyword extraction, that's a server-side or hook-side enhancement, not a journal feature.

## When to read the journal

- **After-action review** — what banks did this session touch, what came back, what was retained?
- **Tuning the memory system** — section 5 surfaces concrete missed-opportunity claims like *"all retains hit only `claude-runtime`; no retains tagged for `infra`"* that you can act on.
- **Debugging recall quality** — section 4 plus the raw telemetry tells you whether recall returned anything for a given prompt, and how much.
- **Auditing retain hygiene** — section 6 evaluates whether each retain reads as standalone or relies on stale references.

## When NOT to extend this in a new skill

This pipeline is **runtime infrastructure**, not a workflow Claude invokes. Don't fragment it into a separate `hindsight-journal` skill — keep the operational notes here in the `hindsight` skill and the executable bits in `~/.claude/hooks/`. The `hindsight-memory-governance` skill is already a deprecated shim for exactly this reason: memory tooling stays consolidated under one canonical skill.
