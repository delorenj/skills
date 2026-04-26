---
pipeline-status:
  - new
---
# Self-Improving Agent

Structured learning loop for agent work. This skill does not rewrite prompts or mutate skills from raw experience. It records bounded observations, rolls them into episodes, extracts candidate lessons after repeated failures, and publishes the resulting `agent.learning.*` events to Bloodbank on a best-effort basis.

## Operating Model

The loop is deliberately split into four stages:

1. Observation
   - Capture minimal metadata from tool use.
   - Redact obvious secrets and keep only short previews.
   - Never persist full prompts, diffs, or command output by default.
2. Episode creation
   - Collapse a session into a compact success/failure record.
   - Preserve the dominant failure mode, task tags, and evidence references.
3. Candidate extraction
   - Propose a lesson only after repeated failure modes.
   - Store candidates separately from active guidance.
4. Validation and promotion
   - Default validation result is `needs_more_data`.
   - Promotion, rejection, and rollback are explicit operations.

The base skill stays stable. Durable guidance lives in an overlay lesson store.

## State Layout

Runtime state lives outside the repo by default:

```text
~/.local/share/33god/self-improving-agent/
  working/
    current_session.json
    last_error.json
    session_end.json
    observations.jsonl
    events.jsonl
    hook-runtime.log
  candidates/
    open.jsonl
    validated.jsonl
    rejected.jsonl
  lessons/
    active.json
    archive.jsonl
  episodes.jsonl
```

Override the root with `SELF_IMPROVING_AGENT_STATE_DIR`.

## Bloodbank / Holyfields Integration

Holyfields defines the schema family:

- `agent.learning.observation.recorded`
- `agent.learning.episode.created`
- `agent.learning.candidate.extracted`
- `agent.learning.candidate.validated`
- `agent.learning.lesson.promoted`
- `agent.learning.lesson.rejected`
- `agent.learning.lesson.rolled_back`
- `agent.learning.retrieval.applied`

The runtime publishes them through the Bloodbank CLI surface:

```bash
uv run bb publish <routing-key> --json -
```

Publishing is best-effort:

- Set `SELF_IMPROVING_AGENT_DISABLE_BLOODBANK=1` to disable publish attempts.
- Set `SELF_IMPROVING_AGENT_BLOODBANK_ROOT` if Bloodbank is not at `~/code/33GOD/bloodbank`.
- Local state is still written even when Bloodbank is unavailable.

## Hook Installation

Use the hook wrappers directly. Do not interpolate raw tool payloads into the shell command.

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

The wrappers read `TOOL_NAME`, `TOOL_INPUT`, `TOOL_OUTPUT`, and `EXIT_CODE` from the hook environment when the host provides them. Positional fallbacks are kept only for backward compatibility.

## Manual Operations

Run these from the skill repo:

```bash
python3 scripts/hook_runtime.py retrieve-lessons --target-skill code-reviewer --task-tag verification
python3 scripts/hook_runtime.py promote-candidate <candidate-id> --rollout-status active --ttl-days 30
python3 scripts/hook_runtime.py reject-candidate <candidate-id> --reason "bad generalization"
python3 scripts/hook_runtime.py rollback-lesson <lesson-id> --reason "false positive"
```

## Environment Variables

- `SELF_IMPROVING_AGENT_AGENT_NAME`
- `SELF_IMPROVING_AGENT_STATE_DIR`
- `SELF_IMPROVING_AGENT_LOG_PATH`
- `SELF_IMPROVING_AGENT_BLOODBANK_ROOT`
- `SELF_IMPROVING_AGENT_DISABLE_BLOODBANK`
- `SELF_IMPROVING_AGENT_SEED_PATTERNS`
- `SELF_IMPROVING_AGENT_SESSION_KEY`

## Seed Lessons

`memory/semantic-patterns.json` is treated as a seed corpus, not a live mutation target. The runtime bootstraps those patterns into the active lesson store the first time state is created, then all subsequent promotion and rollback happens in external runtime state.

## Verification

Current local verification:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Bloodbank-side verification for the event surface:

```bash
uv run pytest tests/test_agent_feedback_refactor.py tests/test_agent_learning_registry.py
```
