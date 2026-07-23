---
name: review-losses
description: Surface patterns from the archeology meta-bank to inform workflow mitigations and prevent future losses.
---

# Review Losses

## Outcome

A diagnosis of **how features get lost** in this project, drawn from accumulated archeology bank entries. Actionable mitigations that can be baked into future workflows (PR templates, commit conventions, session-report discipline, GOD doc coverage, etc.).

## Process

Recall the archeology bank broadly:

```bash
hindsight memory recall "$ARCHEOLOGY_BANK" "all losses" --budget high
```

Synthesize the entries along these axes:

- **Mechanism of loss** — squash, rebase, refactor-without-replacement, agent amnesia, checkpoint burial, branch abandonment, epic transition
- **Domain clustering** — do losses concentrate in certain codebase areas (UI state, background jobs, OAuth flows)?
- **Temporal clustering** — do losses cluster around certain events (epic boundaries, release cuts, velocity spikes)?
- **Breadcrumb quality** — when losses happened, what trail survived? What didn't?

## Deliverable

Present findings in character:

- **The pattern** — named and described in one sentence
- **Evidence** — cite specific lost features and archeology bank entries
- **The mitigation** — concrete change to workflow, tooling, or convention
- **Who owns the fix** — which GOD doc, which process, which human

Example:

> "Three losses this quarter follow the same pattern: UI state stores ripped out during epic transitions without updating the owning GOD.md. The sidecar, the billing widget, the session timer — all three. The mitigation: the pre-commit GOD freshness hook should hard-fail on Zustand store deletions if the owning GOD.md isn't staged. That closes the loop."

## Persistence

Write the synthesis back to the archeology bank as a higher-order memory:

```bash
hindsight memory retain "$ARCHEOLOGY_BANK" "PATTERN: <name>. <description>. Mitigation: <action>." --context conventions
```

This turns accumulated losses into institutional learning. Over time the archeology bank becomes a map of where the project bleeds memory, and what to do about it.
