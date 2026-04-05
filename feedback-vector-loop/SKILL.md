---
name: feedback-vector-loop
description: Build reusable directional-feedback loops for any creative/agentic pipeline. Use when replacing binary thumbs-up/down with structured critique vectors (more/less/avoid/replace), compiling feedback into weight adjustments, ranking candidates with those vectors, and iteratively improving outputs with deterministic artifacts.
pipeline-status:
  - new
---

# Feedback Vector Loop

Use this skill to operationalize **directional feedback**:
- not just "good/bad"
- but "move output toward X and away from Y"

This pattern is reusable across brands (e.g., Jacksnaps, Digipop, any creative pipeline).

## When to use

- You have candidate outputs and human critique.
- Binary labels are too weak for improvement.
- You want iterative quality gains while preserving deterministic control.

## Core model

Each feedback record should include:
1. **Verdict**: `up | revise | down`
2. **Direction**:
   - `more[]`
   - `less[]`
   - `avoid[]`
   - `replace{old:new}`
3. Optional candidate context (`title`, `slogan`, `rationale`, etc.)

## Deterministic pipeline

1. Capture feedback log (`feedback_log.jsonl`).
2. Compile vector profile (`feedback_vector.json`).
3. Rank new candidates with base score + vector score.
4. Apply replacement rules and penalties/bonuses.
5. Emit stage trace and artifacts for auditability.

## Runbook

### 1) Compile vector from feedback

```bash
python scripts/compile_feedback_vector.py \
  --input <feedback_log.jsonl> \
  --output <feedback_vector.json>
```

### 2) Rank candidates with vector

```bash
python scripts/rank_candidates_with_vector.py \
  --candidates <candidates.json> \
  --vector <feedback_vector.json> \
  --output <ranked_candidates.json>
```

### 3) Validate data contract

Use `references/feedback-data-contract.md` for required fields.

## Design invariants

- Keep feedback rows append-only.
- Use weighted token adjustments, not opaque hidden state.
- Persist artifacts every run (traceability).
- Separate **creative generation** from **deterministic scoring**.

## Suggested artifact set per run

- `feedback_log.jsonl`
- `feedback_vector.json`
- `ranked_candidates.json`
- `stage_trace.jsonl`
- `summary.json`
