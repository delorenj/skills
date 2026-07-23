---
name: product-manager-research-phase
description: ResearchPhase for ProductManager feature candidate discovery. Use for product research, mock use, visual inspection, app walkthroughs, screenshot review, repo/document analysis, competitor research, market research, customer workflow evidence, and discovery evidence logs. Triggers on ResearchPhase, feature discovery research, product audit, inspect the app, use the product, visual QA for opportunities, and external research for feature ideas. Do NOT use for brainstorming or PRD writing without first gathering evidence.
---

# ProductManager ResearchPhase

ResearchPhase builds the evidence base for feature candidates. It answers: what does the product do, where does it feel weak, what do adjacent products teach us, and which user problems appear worth exploring?

## Workflow

1. **Frame the run.** Identify the product, target user, repo, live URL or dev command, and any user-stated goals.
2. **Read local context.** Inspect `README`, `AGENTS.md`, docs, screenshots, issues, analytics exports, feature specs, and relevant source directories.
3. **Mock-use the product.** Run the app or inspect an existing environment when feasible. Walk the primary workflows as a plausible user. Capture screenshots or notes for each friction point.
4. **Visually inspect.** Look for missing states, unclear hierarchy, awkward empty/loading/error states, hidden affordances, mismatched language, and workflows that require unnecessary memory.
5. **Research outside context.** Browse current competitors, category norms, pricing or packaging, app-store/review complaints, docs, and relevant product patterns. Cite URLs and access dates.
6. **Synthesize evidence.** Separate observations from inferences. Mark confidence and source quality.

## Evidence Log

Maintain `evidence-log.md` during the phase:

```markdown
# Evidence Log

## Product Context
- Source: `README.md`
- Finding:
- Implication:

## Mock Use
- Flow:
- Screenshot or URL:
- Observation:
- Friction:

## External Research
- Source:
- Accessed:
- Relevant quote or paraphrase:
- Implication:
```

## Research Output

Write `research.md`:

```markdown
# ResearchPhase: [Product]

## Product Thesis

## Target User and Jobs

## Current Surface Map

## Mock-Use Findings

## Visual Inspection Findings

## External Research Findings

## Opportunity Themes

## Evidence Gaps
```

## Quality Gate

Do not advance to BrainstormPhase until the run has:

- At least three product-surface observations.
- At least one actual or substitute visual inspection pass.
- At least three external or adjacent-product sources when the category is public.
- A clear statement of what could not be verified.

## Out of Scope

- **Generating feature lists:** use `product-manager-brainstorm-phase` after this phase.
- **Writing PRD-like docs:** use `product-manager-feature-doc-phase`.
- **Delivering summaries:** use `product-manager-report-phase`.
