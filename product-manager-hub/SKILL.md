---
name: product-manager
description: Skill-set hub for the ProductManager agent and its discovery workflows. Routes ProductManager, PM discovery, feature candidate research, mock use, visual inspection, external research, BrainstormPhase, FeatureDocPhase, and ReportPhase tasks to product-manager-agent plus product-manager-research-phase, product-manager-brainstorm-phase, product-manager-feature-doc-phase, and product-manager-report-phase. Use when composing the complete feature-candidate discovery workflow. Do NOT use for implementation-only work.
---

# ProductManager Skill Set

Use this hub to run the ProductManager feature discovery loop end to end or to load one phase precisely.

## Triage

| Task signal | Load |
|---|---|
| ProductManager persona, PM discovery agent, feature candidate workflow | `../product-manager-agent/SKILL.md` |
| ResearchPhase, mock use, visual inspection, external research, product audit | `../product-manager-research-phase/SKILL.md` |
| BrainstormPhase, candidate generation, opportunity matrix, prioritization | `../product-manager-brainstorm-phase/SKILL.md` |
| FeatureDocPhase, PRD-like doc, acceptance criteria, selected candidate spec | `../product-manager-feature-doc-phase/SKILL.md` |
| ReportPhase, discovery report, vault/email/Telegram delivery, final summary | `../product-manager-report-phase/SKILL.md` |

## Common Combinations

| Scenario | Load in order |
|---|---|
| Full discovery run | product-manager-agent -> product-manager-research-phase -> product-manager-brainstorm-phase -> product-manager-feature-doc-phase -> product-manager-report-phase |
| Quick candidate sweep | product-manager-agent -> product-manager-research-phase -> product-manager-brainstorm-phase |
| Turn an existing idea into a doc | product-manager-agent -> product-manager-feature-doc-phase -> product-manager-report-phase |
| Summarize an existing run | product-manager-agent -> product-manager-report-phase |

## Cross-Cutting Rules

- Keep artifacts under `docs/product-manager/` unless the user names another path.
- Treat screenshots, source files, app walkthroughs, and external links as evidence, not decoration.
- Send email or Telegram only when the user explicitly requests that delivery mode.
- Do not implement feature code from this skill set.

## Out of Scope

- **Implementation:** use development, architecture, or planning skills after the owner accepts a feature doc.
- **Pure market research without product inspection:** use a research-specific skill and import findings here later.
- **Backlog operations:** use ticket or Plane skills for board changes.
