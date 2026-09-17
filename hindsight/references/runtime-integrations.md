# Runtime integrations

Load only when configuring or diagnosing the named runtime integration. Verify
installed hooks and config before accepting historical paths or automation claims.
Do not change schedulers, capture policy, or other clients during ordinary recall.

## OpenClaw Plugin Integration

The local OpenClaw plugin (`workspace/.openclaw/extensions/hindsight-memory/`) automates capture and recall so agents don't need to manually call hindsight. Config lives in `openclaw.json` under `plugins.entries.hindsight-memory`.

### What the plugin automates

| Hook | Behavior |
|------|----------|
| `before_prompt_build` | Auto-recall from resolved banks, inject as context |
| `message_received` | Capture explicit memory intent ("remember", "prefer", "always", "never") |
| `agent_end` | Capture high-signal user messages from the run |
| `before_reset` | Summarize last 16 messages before `/new` clears context |
| `before_compaction` | Snapshot first 20 messages (initial requirements, arch decisions) before compression |
| `session_end` | Capture session summary with git diff stats |
| `after_tool_call` | Capture tool errors as debugging context |

### Routing resolution order

The plugin resolves writeBank and recallBanks per-request through layered routing:

1. Start with `defaultBank` + `globalRecallBanks`
2. Apply `agentRoutes[agentId]` override
3. Apply `sessionPrefixRoutes` (longest-prefix match on session key)
4. Apply `workspaceRoutes` (substring match on workspace dir)
5. Apply `channelRoutes` (exact match on channel ID)
6. Dedupe and cap at `maxRecallBanks` (default: 4)

### Noise filtering

The plugin skips: messages < 24 chars, slash commands, system messages, heartbeat pings, cron hooks, and upstream errors. The `MEMORY_INTENT_RE` pattern triggers immediate capture for explicit memory phrases.

### Key config knobs

| Setting | Default | Purpose |
|---------|---------|---------|
| `recallTopK` | 4 | Max memories per bank per recall |
| `maxPromptChars` | 1200 | Truncation limit for recall queries |
| `maxCaptureChars` | 1200 | Truncation limit for retained content |
| `maxItemsPerRun` | 3 | Max user messages captured per agent run |
| `includeWriteBankInRecall` | true | Auto-include writeBank in recall list |

## Claude Code Hook Integration

The Claude Code analog of the OpenClaw plugin. Three hooks under `~/.claude/hooks/` auto-recall on every user prompt, auto-retain on every file edit, and emit a per-session journal at `~/.claude/.hindsight-journal/YYYY-mm-dd-h-m-s.md` that explains in plain English what was searched, what bank was resolved, how effective the recall was, and what was retained (with LLM-synthesized rationale for the subjective parts).

| Hook (settings.json event) | Script | Behavior |
|---|---|---|
| `UserPromptSubmit` | `hindsight-recall.sh` | Resolve bank, recall context, inject into prompt, log `recall`/`recall_skipped` event |
| `PostToolUse` (Write\|Edit\|MultiEdit) | `hindsight-retain.sh` | Retain edited file context, log `retain` event |
| `Stop` | `hindsight-session-end.sh` | Daemonize journal writer (`setsid nohup`), legacy session-summary retain |

The Stop hook **must** detach the journal writer with `setsid nohup … </dev/null >/dev/null 2>&1 &` — Claude Code reaps the hook's process group on return, killing any plain `&` background that's still waiting on the 30-second `hindsight memory reflect` call.

Full reference (event schema, env knobs, manual ops, failure modes): `references/claude-code-journal.md`.

## Deterministic Governance (Single-Skill Canonical)

This `hindsight` skill is the **single canonical memory package**. Keep governance here (do not split into a second memory-governance skill).

### OpenClaw integration checks (only when that integration is in scope)

- `hindsight-memory` plugin enabled
- `autoRecall=true`
- `autoCapture=true`
- `captureDirectIntent=true`
- `captureToolErrors=true`
- Explicit `defaultBank` and `agentRoutes`

### Deterministic audit

Run:

```bash
python3 /home/delorenj/.agents/skills/hindsight/scripts/audit_hindsight_memory.py
```

Use this audit only for an installed OpenClaw integration. Interpret failure against that host's selected integration; absence on another host is not policy drift.

## Governance Principles

### Clock independence

Three independent clocks operate in the OpenClaw runtime. They must not be conflated:

- **Heartbeat** (agent runtime): Owns triage/dispatch loops and proactive checks
- **Cron** (scheduler): Owns exact-time reminders and isolated scheduled tasks
- **Hindsight** (memory backend): Owns memory extraction, indexing, and consolidation independently

When scheduler repair is part of the request, inspect duplicate jobs and their owners before changing them. A recall/retain request does not authorize scheduler changes.

### Automated curation replaces manual promotion

The old pattern of writing daily logs to `memory/YYYY-MM-DD.md` and manually promoting to `MEMORY.md` is replaced by Hindsight's hierarchy:

| Old (file-based) | New (Hindsight) |
|-------------------|-----------------|
| Daily log entries | Raw facts (auto-captured by plugin) |
| Manual promotion review | Observations (auto-consolidated from facts) |
| Curated MEMORY.md | Mental models (user-created summaries) |

The plugin's `before_compaction` and `session_end` hooks ensure context survives session boundaries without manual intervention.
