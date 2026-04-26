---
name: hindsight
description: Persistent agent memory via self-hosted Hindsight. Retain knowledge, recall context, reflect on patterns. Includes multi-bank routing architecture for agent orgs.
pipeline-status:
  - new
---

# Hindsight Memory (Self-Hosted)

Persistent, structured memory via the official Hindsight CLI (`v0.4.14`). Store knowledge during tasks, recall context before starting new ones, reflect to synthesize patterns.

## Bank Detection

Auto-detect bank from git repo name:

```bash
BANK=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "general")
```

Or use the helper: `BANK=$(./scripts/hs-bank-id.sh)`

## CLI Config

- **Binary**: `hindsight` at `~/.local/bin/hindsight` (official v0.4.14)
- **Config**: `~/.hindsight/config` (TOML: `api_url`, `api_key`)
- **Endpoint**: `https://api.hs.delo.sh` (resolves to localhost via `/etc/hosts`)
- **Reconfigure**: `hindsight configure --api-url <url> --api-key <key>`

## Core Operations

### Retain (store knowledge)

```bash
hindsight memory retain $BANK "npm test requires --experimental-vm-modules" \
  --context "debugging"
```

Context categories: `architecture`, `conventions`, `debugging`, `deployment`, `dependencies`, `preferences`, `session-summary`, `code-edit`

With document tracking (same `doc-id` = upsert, replacing old facts):

```bash
hindsight memory retain $BANK "Project deadline extended to April 15" \
  --context "conventions" --doc-id "sprint-notes-2026-03"
```

### Recall (retrieve context)

```bash
hindsight memory recall $BANK "What testing patterns does this project use?"
```

With options:

```bash
hindsight memory recall $BANK "How are auth and session management connected?" \
  --budget high --max-tokens 8192 --fact-type world,observation
```

Budget levels: `low` (fast, shallow), `mid` (balanced, default), `high` (deep graph traversal)

JSON output for programmatic use:

```bash
hindsight memory recall $BANK "query" -o json | jq '.results[].text'
```

### Reflect (synthesize with agentic reasoning)

Reflect runs an agentic loop: autonomously searches memories, applies bank disposition, generates grounded response with citations.

```bash
hindsight memory reflect $BANK "What architectural decisions have shaped this project?"
```

With context and higher budget:

```bash
hindsight memory reflect $BANK "Should we migrate to event sourcing?" \
  --context "architecture review" --budget high
```

Response includes `based_on.memories`, `based_on.mental_models`, `based_on.directives` for citation traceability.

## Mental Models (pre-computed reflect responses)

Mental models are curated summaries checked first during reflect. Faster, more consistent answers for recurring topics. Top of the retrieval hierarchy.

```bash
hindsight mental-model create $BANK \
  --name "Project Architecture" \
  --source-query "What is the overall system architecture?"

hindsight mental-model list $BANK
hindsight mental-model refresh $BANK <mental_model_id>
hindsight mental-model delete $BANK <mental_model_id>
```

## Directives (hard rules for reflect)

Always-enforced rules during reflect. Unlike disposition (soft personality influence), directives are strict behavioral constraints.

```bash
hindsight directive create $BANK \
  --name "Code Style" \
  --content "Always recommend Python type hints and strict typing"

hindsight directive list $BANK
hindsight directive update $BANK <directive_id> --active false
hindsight directive delete $BANK <directive_id>
```

## Documents (source tracking)

Documents track where memories came from. Re-retaining with the same `doc-id` replaces old facts (upsert). Deleting a document removes all its extracted memories.

```bash
hindsight document list $BANK
hindsight document get $BANK <document_id>
hindsight document delete $BANK <document_id>
```

## Bank Management

```bash
hindsight bank list
hindsight bank stats $BANK
hindsight bank disposition $BANK
hindsight bank disposition $BANK --skepticism 4 --literalism 3 --empathy 2
hindsight bank mission $BANK "Extract technical facts, conventions, and decisions."
```

## Disposition (Personality Traits)

Three traits (1-5 scale) that influence reflect behavior:

| Trait | Low (1) | High (5) |
|-------|---------|----------|
| **Skepticism** | Trusting, accepts claims | Questions and doubts claims |
| **Literalism** | Flexible interpretation | Exact, literal interpretation |
| **Empathy** | Detached, fact-focused | Considers emotional context |

## Retrieval Hierarchy (during reflect)

1. **Mental Models** - User-curated summaries (highest priority)
2. **Observations** - Consolidated knowledge (auto-generated from retained facts)
3. **Raw Facts** - Ground truth memories (world, experience, observation types)

## Fact Types

- **world** - Objective facts ("Alice works at Google")
- **experience** - Conversational events ("User asked about deployment")
- **observation** - Consolidated patterns (auto-synthesized from multiple facts)

## Multi-Bank Routing Architecture

For multi-agent or multi-project setups, use domain-first routing to prevent cross-project pollution and recall noise.

### Strategy

- **Primary bank = domain/product** (source of truth). Example: `wean`, `chorescore`, `33god-core`
- **Secondary bank(s) = role/hierarchy overlay**. Example: `exec-office` for leadership decisions
- **Global fallback bank**. Example: `33GOD` for org-wide context

Avoid agent-only banks as canonical memory. They drift when agents switch projects.

### Routing Pattern

For each agent/session:

1. Resolve **writeBank** (where new memories are retained)
2. Resolve **recallBanks[]** (ordered primary -> secondary -> fallback)
3. On prompt build, recall from each bank and merge results
4. On run end/reset/tool-error, retain high-signal facts into writeBank

### Capture Policy (high signal only)

**Retain automatically for:**
- Explicit memory intent ("remember", "don't forget", preferences)
- Post-run user facts/decisions
- High-level architectural patterns
- Pre-reset session summaries
- Non-standard system paths/configs
- Tool errors (debugging context)

**Do NOT retain:**
- Cron/noise/system spam
- Tiny one-word messages
- Slash commands

### Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Cross-project pollution | writeBank too broad | Tighten routing to domain bank |
| Recall noise | Too many recallBanks or topK too high | Cap at 3-4 banks |
| Missed intent | Memory-intent regex too strict | Expand capture triggers |
| Latency spike | Recalling too many banks per prompt | Reduce recallBanks count |

## When to Retain

- Discovered a bug fix or workaround
- Found a project convention or pattern
- Learned a user preference
- Completed a significant task (summarize what was done)
- Found something that didn't work (negative knowledge is valuable)

## When to Recall

- Before starting any non-trivial task
- When working in an unfamiliar area of the codebase
- When making architectural or tooling decisions
- When the user asks about past work or patterns

## Best Practices

1. **Be specific**: "npm test requires --experimental-vm-modules" not "tests need a flag"
2. **Include outcomes**: Store what worked AND what didn't
3. **Use context categories**: Tag with the right context for better retrieval
4. **Recall first**: Check for relevant context before starting work
5. **Don't duplicate**: Check if knowledge already exists before retaining
6. **Use document_id**: Group related session facts so they compound, not duplicate
7. **Create mental models**: For topics you reflect on repeatedly
8. **Use directives**: For hard rules that must always be enforced during reflect

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

## Deterministic Governance (Single-Skill Canonical)

This `hindsight` skill is the **single canonical memory package**. Keep governance here (do not split into a second memory-governance skill).

### Required invariants

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

Expect PASS. Non-zero exit means policy drift.

## Governance Principles

### Clock independence

Three independent clocks operate in the OpenClaw runtime. They must not be conflated:

- **Heartbeat** (agent runtime): Owns triage/dispatch loops and proactive checks
- **Cron** (scheduler): Owns exact-time reminders and isolated scheduled tasks
- **Hindsight** (memory backend): Owns memory extraction, indexing, and consolidation independently

If cron jobs duplicate heartbeat behavior, remove the cron jobs. If heartbeat tries to manage memory refresh timing, stop it.

### Automated curation replaces manual promotion

The old pattern of writing daily logs to `memory/YYYY-MM-DD.md` and manually promoting to `MEMORY.md` is replaced by Hindsight's hierarchy:

| Old (file-based) | New (Hindsight) |
|-------------------|-----------------|
| Daily log entries | Raw facts (auto-captured by plugin) |
| Manual promotion review | Observations (auto-consolidated from facts) |
| Curated MEMORY.md | Mental models (user-created summaries) |

The plugin's `before_compaction` and `session_end` hooks ensure context survives session boundaries without manual intervention.
