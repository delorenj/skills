---
pipeline-status:
  - new
---
# Appendix

## Event Family

The runtime publishes these Holyfields-defined routing keys:

| Routing Key | Purpose |
|-------------|---------|
| `agent.learning.observation.recorded` | One structured tool outcome |
| `agent.learning.episode.created` | One normalized session summary |
| `agent.learning.candidate.extracted` | A proposed lesson from repeated failures |
| `agent.learning.candidate.validated` | Validation result for a candidate |
| `agent.learning.lesson.promoted` | Manual or controlled activation of a lesson |
| `agent.learning.lesson.rejected` | Explicit rejection of a candidate |
| `agent.learning.lesson.rolled_back` | Removal of an active lesson |
| `agent.learning.retrieval.applied` | Runtime retrieval of relevant lessons |

## State Tree

```text
${SELF_IMPROVING_AGENT_STATE_DIR:-~/.local/share/33god/self-improving-agent}/
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

## Redaction Rules

The runtime keeps previews small and redacts obvious secrets before persistence:

- OpenAI-style `sk-...` tokens
- bearer tokens
- `api_key`, `token`, `secret`, `password` assignments
- AWS access key ids

The goal is not perfect DLP. The goal is to avoid shipping raw sensitive payloads into local logs and Bloodbank events by default.

## Promotion Policy

Promotion should remain gated by evidence:

1. Candidate exists in `candidates/open.jsonl`
2. Validation result is reviewed
3. Human or controlling workflow promotes explicitly
4. Active lesson gets a TTL and rollout status

Recommended rollout sequence:

1. `shadow`
2. observe for false positives
3. `active`

## Rollback Policy

Rollback should be cheap:

```bash
python3 scripts/hook_runtime.py rollback-lesson <lesson-id> --reason "false positive" --rollback-scope full
```

Rollback removes the lesson from `lessons/active.json` and appends the archived record to `lessons/archive.jsonl`.

## Validation Template

Use this when reviewing a candidate before promotion:

```markdown
## Candidate Review

**Candidate ID**: <candidate-id>
**Rule**: <lesson text>
**Supporting Episodes**: <episode ids>

### Checks
- [ ] The rule is operational, not philosophical
- [ ] The trigger conditions are narrow
- [ ] The rule would have prevented the cited failures
- [ ] The rule is unlikely to fire on unrelated tasks
- [ ] A rollback path exists

### Decision
- Promote to `shadow`
- Promote to `active`
- Reject
- Needs more data

### Notes
- <why>
```

## Manual Commands

```bash
python3 scripts/hook_runtime.py retrieve-lessons --target-skill self-improving-agent --task-tag verification
python3 scripts/hook_runtime.py promote-candidate <candidate-id> --rollout-status active --ttl-days 30
python3 scripts/hook_runtime.py reject-candidate <candidate-id> --reason "bad generalization"
python3 scripts/hook_runtime.py rollback-lesson <lesson-id> --reason "false positive"
```

## Cross-Repo Verification

Self-improving-agent:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Bloodbank:

```bash
uv run pytest tests/test_agent_feedback_refactor.py tests/test_agent_learning_registry.py
```

Holyfields:

```bash
mise run validate:schemas
mise run generate:python
uv run pytest tests/python/test_agent_learning_models.py
```
