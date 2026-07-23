---
pipeline-status: new
---
# Add a new domain

Stand up triage for a new directory in four steps. Everything is additive — no engine code changes.

## 1. Write the contract

Create `<domain-dir>/.curator/taxonomy.yaml`. It is a folder-curator contract (deep-merged over the
shipped default), so declare only:

- `purpose:` — one paragraph the agent reads to judge ambiguous files.
- `frontmatter:` — add the entity label(s) to `order` + `defaults` (e.g. `company`, `client`, `repo`,
  and any sub-label like `contact-type`).
- `categories:` — the file **types** for this domain (email, transcript, invite, doc, intel, …), as
  first-match-wins `name_regex` rules. Overlapping matches park in the ingest queue by design.
- `domain:` — the Layer-2 block (entity registry, contacts, routing, heuristics). Copy
  `assets/taxonomy.domain-block.yaml` and fill it in.

Ground the `name_regex` rules in the directory's **real filenames** (`ls` first). Validate a few:

```bash
folder-curator --client-root <domain-dir> plan "<a real file>"    # no writes; shows category/kind
```

## 2. Write the procedure

Copy `assets/TRIAGE.template.md` to `<domain-dir>/.curator/TRIAGE.md` and fill in the entity-detection
order and any sub-rules. This is the agent runbook; keep it specific to how *this* domain's entities
and sub-types are told apart.

## 3. Seed the memory bank

Create a Hindsight bank named for the domain and seed the registry + heuristics (bank is created
implicitly on first retain):

```bash
hindsight bank mission <domain> "Triage inbound <domain> artifacts: identify the entity and type, then route."
hindsight memory retain <domain> "Entity registry: <list of known entities -> folders/status>." --context conventions
hindsight memory retain <domain> "Entity-detection rule / sub-rule: <how to tell entities and sub-types apart>." --context conventions
hindsight memory recall <domain> "<a test question>" --budget low       # verify
```

Keep the bank and the contract's `domain:` block in sync — the block is the offline mirror, the bank is
the live, recency-ranked store. When triage learns something new, retain it (step 7 of the procedure).

## 4. Register the domain

Add a row to the domain registry so the orchestrator (and future you) can discover it:

- In DeLoDocs: `_vault/Workflows/domain-triage/README.md` → the registry table.
- Elsewhere: wherever that repo keeps its triage index.

## Notes

- **Physical layout is the domain's choice.** folder-curator's own `categories` map to type-subfolders
  at the client-root; a domain that routes by *entity* (like JobHunting) keeps entity folders at the
  root and uses the engine only for `plan` typing + enrichment — **do not run `apply`/`normalize
  --apply` at an entity-organized root** (it would reshuffle files by type). See gotchas.
- **Labels vs folders:** set `domain.routing.mode` and `label_only_fallback` per the domain's direction.
