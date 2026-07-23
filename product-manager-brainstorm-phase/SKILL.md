---
name: product-manager-brainstorm-phase
description: BrainstormPhase for ProductManager feature candidate discovery. Use to turn ResearchPhase evidence into possible feature candidates, opportunity clusters, candidate matrices, RICE-style scoring, user-value scoring, effort/risk estimates, prioritization, and top recommendations. Triggers on BrainstormPhase, candidate generation, feature ideas from research, opportunity matrix, rank feature candidates, prioritize product ideas, and synthesize opportunities. Do NOT use before a research artifact or evidence base exists.
---

# ProductManager BrainstormPhase

BrainstormPhase converts evidence into ranked feature candidates. It should feel imaginative, but never detached from the research base.

## Inputs

Read these if present:

- `research.md`
- `evidence-log.md`
- Existing roadmap, issues, docs, or user notes
- Product constraints from `AGENTS.md`, architecture docs, or runtime evidence

If the evidence base is thin, list gaps and run a small ResearchPhase top-up before scoring.

## Candidate Generation

Generate candidates through four lenses:

1. **Friction removal:** what repeated pain did mock use reveal?
2. **Visibility:** what valuable state already exists but is hard to see, compare, or trust?
3. **Control:** where does the user need a safer, faster, or more reversible action?
4. **Category expectation:** what do adjacent products make users expect?

For each candidate, write the smallest useful version first. Add larger variants only after the small version is clear.

## Scoring

Use a 1-5 scale unless the user gives a different rubric:

| Score | Meaning |
|---|---|
| User value | How much pain or desire this addresses |
| Evidence strength | How directly the research supports it |
| Differentiation | How much it improves the product's position |
| Effort | Implementation and design complexity, reversed in final ranking |
| Risk | Data, UX, operational, or trust risk, reversed in final ranking |

Recommended score:

```text
(user_value * 2) + evidence_strength + differentiation - effort - risk
```

## Candidate Matrix

Write `candidate-matrix.md`:

```markdown
# BrainstormPhase Candidate Matrix

| Rank | Candidate | User Problem | Evidence | Value | Evidence | Diff | Effort | Risk | Score | Call |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|

## Top Recommendation

## Parked Ideas

## Rejected Ideas

## Assumptions to Validate
```

## Quality Gate

Before moving to FeatureDocPhase:

- Rank at least five candidates unless the product surface is tiny.
- Include at least one "do not build" call.
- Name the top candidate and why it wins.
- Identify the riskiest assumption for the top candidate.

## Out of Scope

- **Gathering initial evidence:** use `product-manager-research-phase`.
- **Writing detailed feature docs:** use `product-manager-feature-doc-phase`.
- **Sending or summarizing the run:** use `product-manager-report-phase`.
