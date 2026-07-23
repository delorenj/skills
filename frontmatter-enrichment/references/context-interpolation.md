---
pipeline-status: new
---
# Context interpolation — the memory-driven values

This is why the enricher is driven by the repo's **Hermes PM** and not a generic editor: the PM's memory
knows *why a file exists* and *its role in the plan*. Without that, enrichment is just guessing at tags.

## Which fields to interpolate (and which to leave alone)

| Interpolate (from context) | Leave alone (provenance) |
|---|---|
| `title`, `description`, `summary` | `source`, `captured`, `vault-id`, `created_at` |
| `tags`, `domain`, `subdomain`, `pillar` | `category`, `kind` (folder-curator set these) |
| `why` / `context` (role in the plan) | the entity label (`company`/`client`/… — domain-triage set it) |

Never overwrite provenance or upstream-decided fields. Interpolated values must be evidenced; if you
can't ground a value, omit it or use `unconfirmed`.

## Context sources (in order of signal)

1. **Hindsight bank recall** — the strongest signal:
   `hindsight memory recall <repo-bank> "<file topic / entity>" --budget mid`. Returns recency-ranked
   facts: what's active, recent related work, decisions. This is where "there was a deluge of X last
   week → this new file is probably about X" comes from.
2. **The PM's durable memory** — `runtime/memories/MEMORY.md` (auto-injected when the PM drives) and
   `runtime/decisions/*.md` (why calls were made).
3. **Recency compass** — `llr` (mtime-sorted) around the file's siblings; a cluster of same-topic files
   just created implies this one shares that plan context.
4. **Repo event stream** (if wired) — Bloodbank repo-scoped events (`bloodbank.evt.v1.repo.<repo>.>`)
   the PM already consumes; recent ticket/decision events explain *why now*.

## Deriving "why / role in the plan"

Combine the entity + type + recall into one grounded sentence. Examples:
- transcript in `Asana/`, recall says "Asana interviewing, technical loop next" →
  `why: "Prep artifact for the Asana technical interview loop (active pipeline)"`.
- a `posting.md` just created in a new company folder, recall shows a recruiter intro this week →
  `why: "Opportunity opened from <recruiter> intro on <date>; sourcing/qualification stage"`.

Keep it to one or two sentences, factual, and traceable to the recalled evidence. If recall is empty and
the file gives no signal, set `why: unconfirmed` rather than inventing a narrative.

## Feeding context to an LLM enrichment pass

When the PM runs this as an LLM stage, put the recall output + recent-activity list into the prompt
alongside the file — the existing inbox pipeline's failing was passing *only* file-stat metadata. The
manifest for enrichment should include: the file, its already-set category/kind/entity, the bank recall,
and the 5-10 most recent sibling/topic files (title + captured). That context is what makes the values
plan-aware instead of generic.
