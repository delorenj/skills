---
name: product-manager-report-phase
description: ReportPhase for ProductManager feature discovery. Use to create the final overview report, summarize ResearchPhase and BrainstormPhase outputs, list feature candidates, recommend next actions, package feature docs, and deliver results to a repo docs folder, vault, email, Telegram, or another requested channel. Triggers on ReportPhase, discovery report, feature candidate report, PM summary, deliver results, vault note, email summary, Telegram summary, and final recommendation. Do NOT use as a substitute for research or feature spec creation.
---

# ProductManager ReportPhase

ReportPhase packages the discovery run so the owner can decide what to do next. The default delivery is a repo or vault artifact. Email or Telegram delivery only happens when the user explicitly requests it and the runner has a configured tool or credential path.

## Inputs

Read:

- `research.md`
- `candidate-matrix.md`
- `features/*.md`
- `evidence-log.md`
- User delivery preference, if any

## Report Template

Write `report.md`:

```markdown
# ProductManager Discovery Report: [Product]

## Executive Summary

## What Was Inspected

## Key Findings

## Ranked Feature Candidates

## Recommended Bet

## Feature Docs Created

## Evidence and Sources

## Risks / Unknowns

## Suggested Next Action

## Delivery Notes
```

## Delivery Modes

| Requested delivery | Behavior |
|---|---|
| Repo docs or no preference | Save under `docs/product-manager/<run>/report.md` |
| Vault | Save or copy to the user-named vault path; preserve repo links when possible |
| Email | Draft or send only with explicit recipient and available mail tool |
| Telegram | Send only with explicit chat/bot path and available Telegram/Hermes tool |

If a requested delivery tool is unavailable, save the report and include the exact blocked delivery step in `Delivery Notes`.

## Summary Style

- Lead with the recommendation.
- Keep the matrix scannable.
- Link every detailed feature doc.
- Keep rejected ideas visible enough that future agents do not rediscover them.
- Separate "verified" from "inferred" from "needs owner call."

## Completion Gate

The report is complete when:

- It links or names every artifact produced in the run.
- It includes a ranked recommendation and a next action.
- It names research gaps and delivery limitations.
- It can be read without opening every source file.

## Out of Scope

- **Initial discovery:** use `product-manager-research-phase`.
- **Candidate generation:** use `product-manager-brainstorm-phase`.
- **Detailed feature requirements:** use `product-manager-feature-doc-phase`.
