---
pipeline-status: new
---
# The `domain:` block and `TRIAGE.md`

Two conventions this skill adds on top of folder-curator. Neither is known to the folder-curator engine
— the engine deep-merges the `domain:` block but ignores unknown keys, so it is pure Layer-2 data.

## The `domain:` block (in `.curator/taxonomy.yaml`)

```yaml
domain:
  name: <domain>              # matches the Hindsight bank name
  memory_bank: <domain>
  routing:
    mode: entity-folder        # entity-folder | label-only
    entity_key: company        # the frontmatter label that carries the entity (company|client|repo|…)
    new_entity: create-folder  # what to do on first contact with an unknown entity
    label_only_fallback: true  # if the domain flattens folders, set the label instead of moving
  recruiters_subtree: "Recruiters/<Agency>/"   # OPTIONAL: sub-rule destinations (domain-specific)

  entities:                    # the registry — known entities and where they live
    - {name: <Entity>, folder: <Folder>, status: <status>, notes: <optional>}

  contacts:                    # person/sender/attendee -> entity + sub-type (grows over time)
    - {name: <Contact>, company: <Entity>, type: <sub-type>, agency: <optional>}

  heuristics:                  # plain-language rules the agent applies (entity detection, sub-rules, recency)
    - "<how to tell entities apart / a sub-rule / a recency signal>"
```

- `entities` uses `company`/`client`/`repo` naming per the domain, but keep the key `entities` (or a
  domain-appropriate alias) consistent with what `TRIAGE.md` reads.
- The block is the **offline mirror** of the Hindsight bank. The bank is authoritative and
  recency-ranked; the block guarantees routing works without a network call.

## `TRIAGE.md` (the agent runbook)

Sections, in order:

1. **Inputs** — which `domain:` keys to load, and the `hindsight memory recall <bank> "…"` to run first.
2. **Procedure** — the 7 steps (relevance gate → type → entity → sub-label → enrich → route → learn),
   specialized with this domain's entity-detection order and sub-rules.
3. **Enrichment** — the exact frontmatter keys this domain writes.
4. **Worked signals** — 2-3 real files annotated with the decision, so the rules stay grounded.

## Frontmatter this skill writes

Beyond folder-curator's core (`category, kind, title, source, captured, updated, pipeline-status`),
a domain adds its entity + sub-labels, e.g.:

```yaml
company: <Entity>          # or client / repo — the entity_key
contact-type: <sub-type>   # a domain sub-label (e.g. recruiter | in-house-hr | none)
contact: <person>
route-reason: "<one line: why this entity + type + destination>"
confidence: high | medium | low
```

Preserve any pre-existing values; use `unknown`/`unconfirmed` when not evidenced. `confidence: low`
means the entity wasn't resolved — the file stays in `_triage/` for a human.
