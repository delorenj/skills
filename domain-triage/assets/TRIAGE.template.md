---
pipeline-status: new
---
# <Domain> Triage — agent procedure (Layer 2)

The domain-specific triage agent for `<domain-dir>/`. Runs on top of folder-curator (Layer 1) and is
informed by the **`<domain>` Hindsight bank** + the `domain:` block in `.curator/taxonomy.yaml`.
Invoked by the orchestrator when a file lands that looks like <domain> material, or to drain `_triage/`.

## Inputs (load first)
1. `.curator/taxonomy.yaml` → `domain.entities`, `domain.contacts`, `domain.heuristics`, `domain.routing`.
2. `hindsight memory recall <domain> "<one line about the file>" --budget low` — recency-ranked context.

## Procedure (deterministic first, judgment second)
0. **Relevance gate.** Is this <domain> material at all? If not → hand back to the general pipeline.
1. **Type (Layer 1).** `folder-curator --client-root . plan "<file>"` → category + kind. If parked
   `dropbox/low` (ambiguous, or a `.md` the engine can't type), classify from content.
2. **Entity.** (1) exact match to `domain.entities`; (2) sender/attendee via `domain.contacts`;
   (3) LLM read of content; (4) still unknown → leave in `_triage/` at `confidence: low`. **Never guess.**
   First contact from a new entity → open a new `<Entity>/` folder (or set the label).
3. **Sub-label.** <Fill in the domain's sub-rule, e.g. recruiter vs in-house; how each is told apart
   and where each routes.>
4. **Enrich** frontmatter (preserve existing; `unknown`/`unconfirmed` when not evidenced):
   `category, kind, title, <entity_key>, <sub-label>, source, captured, updated, pipeline-status, confidence, route-reason`.
5. **Route.** High confidence → move + enrich. Otherwise → park in `_triage/` at `confidence: low`.
6. **Learn.** New entity/contact/status → `hindsight memory retain <domain> "<fact>" --context conventions`.

## Worked signals (keep 2-3 real, annotated examples here)
- `<real/path>` — <what it is> → `<entity_key>: <Entity>, <sub-label>: <value>` → `<destination>`.
