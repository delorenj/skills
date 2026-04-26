---
name: self-improving-agent
description: Controlled self-referential learning loop with structured observations, external runtime state, Holyfields-defined learning events, and manual promotion/rollback of lessons.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
pipeline-status:
  - new
---

# Self-Improving Agent

This skill is a controlled learning loop for agent work. It improves future behavior by collecting structured evidence, not by letting raw transcripts rewrite the skill itself.

## Non-Negotiables

1. Raw experience does not edit the base skill.
2. Hooks capture metadata only; they do not persist full prompts or raw tool output.
3. Candidate lessons are separate from active lessons.
4. Automatic validation may label a candidate `needs_more_data`, but promotion is still controlled.
5. Rollback must be cheap and explicit.

## Runtime Contract

The runtime lives in three places:

- `hooks/`
  - stable shell entrypoints for tool/session hooks
- `scripts/hook_runtime.py`
  - CLI for hook ingestion, promotion, rejection, rollback, and retrieval
- `runtime/learning_core.py`
  - state management, redaction, candidate extraction, and Bloodbank publishing

Runtime state is external by default:

```text
~/.local/share/33god/self-improving-agent/
```

That keeps the repo clean and makes rollback independent of the skill checkout.

## Learning Lifecycle

### 1. Observation

`pre-tool` and `post-tool` record:

- tool name
- derived decision type
- task tags
- short redacted previews
- outcome
- failure mode
- verification status

### 2. Episode Creation

`finalize-session` collapses the session into a single episode with:

- summary
- outcome
- dominant failure mode
- supporting observation ids
- task tags
- optional feedback summary

### 3. Candidate Extraction

Repeated failure modes may generate candidate lessons. Current heuristics intentionally stay narrow:

- `verification_failed`
- `search_skipped`

### 4. Validation

Automatic validation is conservative. The default output is:

- `decision: needs_more_data`

This prevents the runtime from auto-promoting unproven rules.

### 5. Promotion / Rejection / Rollback

Promotion and rollback are explicit CLI actions:

```bash
python3 scripts/hook_runtime.py promote-candidate <candidate-id> --rollout-status active
python3 scripts/hook_runtime.py reject-candidate <candidate-id> --reason "bad generalization"
python3 scripts/hook_runtime.py rollback-lesson <lesson-id> --reason "false positive"
```

## Bloodbank Event Surface

Holyfields is the schema source of truth. The runtime emits:

- `agent.learning.observation.recorded`
- `agent.learning.episode.created`
- `agent.learning.candidate.extracted`
- `agent.learning.candidate.validated`
- `agent.learning.lesson.promoted`
- `agent.learning.lesson.rejected`
- `agent.learning.lesson.rolled_back`
- `agent.learning.retrieval.applied`

Publishing uses the Bloodbank CLI as the safest external surface:

```bash
uv run bb publish <routing-key> --json -
```

If Bloodbank is missing or disabled, the runtime still writes local state and event logs.

## Hook Wiring

Use the shell wrappers directly:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit",
        "hooks": [
          { "type": "command", "command": "bash ${SKILLS_DIR}/self-improving-agent/hooks/pre-tool.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash ${SKILLS_DIR}/self-improving-agent/hooks/post-bash.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "bash ${SKILLS_DIR}/self-improving-agent/hooks/session-end.sh" }
        ]
      }
    ]
  }
}
```

The wrappers prefer hook-provided environment variables and only use positional args as a compatibility fallback. Hook stderr is written to `${SELF_IMPROVING_AGENT_LOG_PATH}` or `${SELF_IMPROVING_AGENT_STATE_DIR}/working/hook-runtime.log`.

## Seed Memory vs Active Lessons

`memory/semantic-patterns.json` is treated as a seed file. It bootstraps initial lessons into runtime state when no active lesson store exists. It is not the active mutation surface.

Active lessons live in:

- `lessons/active.json`
- `lessons/archive.jsonl`

Candidates live in:

- `candidates/open.jsonl`
- `candidates/validated.jsonl`
- `candidates/rejected.jsonl`

## Retrieval

Use targeted retrieval rather than dumping all prior learning into context:

```bash
python3 scripts/hook_runtime.py retrieve-lessons --target-skill code-reviewer --task-tag verification --limit 3
```

Only the most relevant active lessons should be surfaced for a task.

## Verification

Local runtime:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Bloodbank compatibility:

```bash
uv run pytest tests/test_agent_feedback_refactor.py tests/test_agent_learning_registry.py
```

Holyfields schema/codegen verification belongs in the Holyfields repo and should be rerun whenever the `agent.learning.*` contracts change.
