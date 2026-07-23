---
name: domain-triage
description: "Stand up and operate domain-specific document triage: route an incoming artifact to the right entity (company/client/repo) folder or label, via a per-domain contract plus a memory bank. A domain = a folder-curator `.curator/taxonomy.yaml` with a `domain:` block (entity registry, contacts, routing, heuristics), a `.curator/TRIAGE.md` procedure, and a Hindsight bank. Two layers: folder-curator `plan` types a file (entity-blind); this skill's agent detects the entity, applies sub-rules (e.g. recruiter vs in-house), enriches, and routes using per-domain memory. Use when standing up triage for a folder (e.g. JobHunting), routing a dropped PDF/email/transcript/invite into the right company/client folder, telling recruiter from in-house HR, or draining a `_triage/` queue. Do NOT use for single-directory type-only curation (use folder-curator), memory mechanics (hindsight), the vault Inbox pipeline, Hermes fleet provisioning, or n8n wiring. Biases: labels over folders, deterministic-first, never guess an entity."
pipeline-status: new
---

# Domain Triage

Route each inbound artifact to its **entity** (company / client / repo / project) and enrich it — by
composing two engines you do not reimplement: **folder-curator** (deterministic typing) and
**Hindsight** (per-domain memory). One declarative contract per domain; adding the next domain is data
+ a bank, not code.

## Operating principles

- **A domain is data, not code.** Everything domain-specific lives in the contract + the bank. This
  skill is the reusable orchestration around them.
- **Deterministic first, judgment second.** Let folder-curator type the file; add the entity and
  routing judgment only where rules can't decide.
- **Never guess an entity.** If the company/client/repo isn't evidenced, park at low confidence — a
  misfile is worse than an unfiled item.
- **Labels over folders.** Routing is an entity *label* projected to a folder; it degrades to
  label-only when a domain flattens its folders.
- **Learn every pass.** New entity, new contact, or status change → retain it to the domain bank so
  the next triage is smarter. That recency is the point of a per-domain bank.

## Quick navigation

| Task | Read |
|---|---|
| Stand up a brand-new domain | [references/add-a-domain.md](references/add-a-domain.md) |
| The `domain:` block + `TRIAGE.md` schema | [references/domain-contract.md](references/domain-contract.md) |
| A complete worked instance | [references/jobhunting-example.md](references/jobhunting-example.md) |
| Failure modes & sharp edges | [references/gotchas.md](references/gotchas.md) |
| Paste-ready `domain:` block | `assets/taxonomy.domain-block.yaml` |
| Paste-ready procedure | `assets/TRIAGE.template.md` |
| Reusable drain runtime (discover / prep / apply) | `assets/domain-drain.py` |

## A domain = three ingredients

| Ingredient | What | Where |
|---|---|---|
| **Contract** | folder-curator `.curator/taxonomy.yaml`: `purpose` + file-**type** categories (Layer 1) + a `domain:` block (entity registry, contacts, routing, heuristics). | `<domain-dir>/.curator/taxonomy.yaml` |
| **Procedure** | the agent runbook: recognize → detect entity → classify type → sub-label → enrich → route → learn. | `<domain-dir>/.curator/TRIAGE.md` |
| **Memory** | a Hindsight bank named for the domain (registry, contacts, status, recency heuristics), recalled first to narrow the field. | bank `<domain>` |

## Two layers (why both)

- **Layer 1 — folder-curator (`plan`).** Returns `{category, kind, normalized_name, frontmatter}` from
  declarative rules. Fast, no LLM, but **entity-blind** — it types a file, it does not know *which*
  entity. The `domain:` block is deep-merged into the contract but the engine **ignores it** (unknown
  keys); it exists for Layer 2 to read.
- **Layer 2 — this skill's agent.** Detects the entity, applies domain sub-rules (recruiter vs
  in-house, active-client, etc.), enriches, and routes — reading the `domain:` block and recalling the
  Hindsight bank first.

## Operating procedure

Load the contract's `domain:` block, then
`hindsight memory recall <bank> "<one line about the file>" --budget low` to narrow the field. Then:

1. **Relevance gate.** If the file isn't in this domain, hand it back to the general pipeline.
2. **Type (Layer 1).** `folder-curator --client-root <dir> plan "<file>"`. If parked `dropbox/low`, classify from content.
3. **Entity (Layer 2 core).** Match the contract registry/aliases → map a sender/attendee via `contacts` → LLM-read the content → else **park at low confidence, don't guess**. First contact from a new entity opens a new folder (or sets the label).
4. **Sub-label.** Apply the domain's sub-rules (e.g. recruiter vs in-house — see the example).
5. **Enrich** frontmatter; preserve existing values, `unknown`/`unconfirmed` when not evidenced.
6. **Route:** high confidence → move + enrich; else park in `_triage/` at low confidence for a human.
7. **Learn:** `hindsight memory retain <bank> "<fact>" --context conventions`.

**Automate the deterministic parts** with `assets/domain-drain.py` (the reusable
runtime): `discover --root <dir>` lists every domain; `prep <domain-dir> <file>`
bundles the Layer-1 plan + a text preview (pdftotext for PDFs) + the registry + a
bank recall into ONE decision packet; `apply <domain-dir> <file> --entity <E> [...]
--apply` enriches the entity labels into frontmatter and routes per the contract
(`entity-folder` / `stage_subtrees` / `--agency` sub-rule), creating the folder on
first contact and optionally `--retain`ing the learned fact. You supply only the
entity/sub-type judgment (steps 3–4); the tool does the rest. Dry-run without `--apply`.

Read the references before authoring a domain — they hold the exact contract schema and a worked example.

## Folders or labels

Routing is an entity **label** (`company:`, `client:`, `repo:`). While folders exist it projects to a
folder (`route to <dir>/<Entity>/`); set `domain.routing.label_only_fallback: true` so it degrades to
"set the label, don't move" when a domain flattens — no contract change needed.

## Out of scope

- **Single-directory, type-only curation with no entity or memory** → use `folder-curator` directly (this skill *composes* it; it is not a replacement).
- **Memory retain/recall/bank mechanics in general** → use `hindsight`.
- **The vault's Inbox classifier→specialist pipeline** → that is `_vault/Workflows/` in DeLoDocs; this skill drains the `_triage/` lane it feeds, it does not replace it.
- **Provisioning a Hermes fleet agent** (systemd, board, runtime) → use `agent-fleet-operations`. A domain triager is a contract + bank, not a fleet daemon.
- **n8n / Bloodbank automation wiring** → use `delonet-n8n-architecture` and folder-curator's automation-runbook.
- **The folder-curator engine internals / its native `taxonomy.yaml` schema** → owned by the `folder-curator` skill; this skill only adds the `domain:` block convention on top.
