---
name: folder-curator
description: Curate any watched directory with a purpose-bound ruleset — classify, rename (datetime prefix), enrich (YAML frontmatter), and route each incoming file to its home; keep a cross-medium recency/context stack (newest on top); and evolve the ruleset itself. Driven by a per-directory contract (.curator/taxonomy.yaml) declaring the directory's purpose and categories; ships with an Automatic AI client/prospect profile (threads/, workshop/, client_dropbox/). Use when a file lands in a curated or watched directory and needs naming, frontmatter, or placement; to organize, file, sort, triage, or curate documents, transcripts, emails, voice notes, or work products; to normalize filenames/frontmatter; to regenerate the context stack (_context-stack.md); to quarantine an uploaded credential; or to propose and apply a taxonomy change. Do NOT use to author the n8n workflow or node (use delonet-n8n-architecture), define Bloodbank schemas (bloodbank-integration), or for BMAD artifacts under _bmad-output/.
pipeline-status: new
---

# Folder Curator

A purpose-bound curator for any watched directory. Each arriving file is deterministically **classified → renamed → enriched → routed** to its home, and every folder stays ordered by document freshness (newest on top). One declarative contract per directory — `.curator/taxonomy.yaml` — declares that directory's **purpose** and its categories/rules; the shipped default (`assets/taxonomy.default.yaml`) is the Automatic AI client/prospect profile. The CLI is the executor — you invoke it, you don't re-implement its rules; when the rules can't decide, you judge in light of the directory's stated `purpose`.

## Operating principles

- **Flat categories, labels over nesting.** Structure lives in frontmatter (`kind`, `tags`), not deep folders. Add a folder only when a whole *class* of docs earns one.
- **The contract is the source of truth.** Classification/naming/enrichment rules are data in `taxonomy.yaml`. Don't hardcode judgments the contract should own — edit the contract (see structure-evolution).
- **Deterministic first, judgment second.** Run the CLI. It routes confident cases and parks ambiguous ones in the review queue (`pipeline-status: new`) for you to decide. Only override when you have real evidence.
- **Purpose guides judgment.** Each curated directory declares a `purpose` in its contract (and `plan` echoes it on low-confidence items). When the rules can't classify deterministically, choose what best serves that purpose — never guess mechanically.
- **Never fabricate provenance.** Preserve existing frontmatter; use `unknown`/`unconfirmed`; a newer `updated` is a relevance signal, not proof of correctness.
- **Secrets never get filed.** A credential/secret is quarantined and blocked — never renamed-into-place, committed, or synced.

## Quick navigation

| Task | Read |
|---|---|
| Full category rules, naming, and frontmatter schema | [references/taxonomy-spec.md](references/taxonomy-spec.md) |
| Propose/apply a change to the taxonomy itself | [references/structure-evolution.md](references/structure-evolution.md) |
| Wire the Bloodbank-fed n8n automation | [references/automation-runbook.md](references/automation-runbook.md) |
| Set up the Google Drive inbound/outbound syncs | [references/drive-sync.md](references/drive-sync.md) |

## The curation procedure

Run from (or point `--client-root` at) the target directory. The installed CLI is `folder-curator` (on `PATH`); the portable form is `uv run <skill-root>/scripts/folder_curator.py`.

1. **Plan (no writes)** — see where a file will go and how it will be named/enriched. This is also the exact "file in → destination out" contract the n8n workflow consumes:
   ```bash
   folder-curator --client-root . plan "<file>"
   ```
   It returns JSON: `{action, category, destination, normalized_name, kind, title, confidence, pipeline-status, frontmatter}`.
2. **Judge only if `confidence: low`.** Low confidence means the file matched zero or *multiple* categories and was parked in the review category (the ingest folder — `client_dropbox` in the default profile) as `pipeline-status: new`; `plan` echoes the directory's `purpose` to guide you. Decide the real category from evidence, then either move it yourself with correct frontmatter or adjust `.curator/taxonomy.yaml` so the rule generalizes.
3. **Apply** — move + rename + enrich, idempotently (a content-hash ledger + `pipeline-status` prevent re-processing). Sidecars (`*.meta.json`) travel with their partner:
   ```bash
   folder-curator --client-root . apply "<file>"
   ```
4. **Reindex** — regenerate `_context-stack.md` (newest-first, cross-medium) and restore each file's mtime from its `updated` field so `ls -lt`/`llr` agree. `apply` does this automatically; run it explicitly after hand-edits:
   ```bash
   folder-curator --client-root . reindex
   ```

To migrate a repo's existing files to the standard in one pass, dry-run first, then apply:
```bash
folder-curator --client-root . normalize            # dry-run: prints the rename+enrich plan
folder-curator --client-root . normalize --apply    # writes it
```

### Triage — recursively reconcile the whole tree

`triage` walks the entire directory (git-aware: it honors `.gitignore`, so generated trees like `runtime/`, `.curator/`, `node_modules/` are never touched) and reconciles everything at once — relocating files you dropped in the wrong folder, renaming to canonical form, enriching, and quarantining secrets. **Always dry-run first.**

```bash
folder-curator --client-root . triage            # dry-run: what it WOULD do
folder-curator --client-root . triage --apply    # execute
```

Two safety rules keep it conservative: it only **relocates on a confident (medium+) match** — a low-confidence file is flagged `review (left in place)` and never yanked into the ingest folder — and it skips `triage.protect_files` (`profile.md`, `AGENTS.md`, `mise.toml`, …). Files already correctly filed return `keep` and are untouched **even if you've edited their contents** (edits ≠ re-triage).

### Transforms — PDF → Markdown, original archived to S3

When the contract enables `transforms.pdf_to_markdown`, `triage` derives a markdown copy of each PDF (via the `pdf2md` primitive, pymupdf4llm) and preserves the original off-site. The invariant is **back up + verify, THEN delete the local original** — never the reverse; a failed/unverified backup keeps the PDF and emits `curator.file.failed`. Two modes (`via`):

- `event` (default) — emit `curator.file.received`; the n8n "PDF → Markdown (archived)" subworkflow does convert + S3 put + verify + delete as visible canvas topology.
- `inline` — do it in-process (standalone, no n8n). Requires a valid `mc` alias in `backup.dest` (an unknown alias is refused — mc would otherwise silently copy locally and greenlight a bad delete).

Enable per directory in `.curator/taxonomy.yaml`; it ships **off**.

## Point it at a new directory

`folder-curator` curates any directory, not just client repos. To adopt a new one:

1. Create `<dir>/.curator/taxonomy.yaml` — set at least a `purpose` and `categories` (folder → classification rules). Anything omitted inherits the shipped default. Same engine, different purpose.
2. `folder-curator --client-root <dir> normalize` (dry-run) to preview, then `--apply`.
3. Thereafter `plan`/`apply` new arrivals and `reindex` to refresh the stack.

## The default profile — Automatic AI client folders

The shipped default profile's categories (flat, at the directory root; override per directory). Full rules in [references/taxonomy-spec.md](references/taxonomy-spec.md).

| Folder | Holds | Typical `kind` |
|---|---|---|
| `threads/` | Communications involving **more than one person** — transcripts, email, Slack, meetings | `communication`, `transcript`, `email` |
| `workshop/` | **Single-author** work products — strategy, pricing, plans, proposals, research, updates | `work-product` |
| `client_dropbox/` | The client's **raw uploads** + the review queue for ambiguous items | `raw-upload`, `voice-note`, `transcription` |

- `profile.md`, `TASKS.md`, `docs/`, `_bmad-output/` are **not** intake targets — leave them.
- **Canonical filename:** `YYYY-MM-DD-<slug>.<ext>` (timestamped dropbox items use `YYYY-MM-DD-HHMMSS-<slug>`). The semantic date (`captured`/frontmatter) wins over a filename date. Old medium tokens (`xscript`, `email`) become the `kind` field, not part of the name.
- **Frontmatter (unified):** `category, kind, title, source, captured, updated, pipeline-status` are core; `confidence, owner, tags`, and per-medium keys (`attendees`, `duration`) are optional. Keys are kebab-case, dates ISO. `pipeline-status ∈ {new, processing, processed, blocked}` — exactly one active.
- **`updated`** is the freshness field (bumped on every touch); it drives the recency stack and mtime restore.

## Safety guardrails

- **Secrets:** files matching credential patterns (name or content) go to `.curator/quarantine/` with `pipeline-status: blocked`. Never enrich, commit, or sync them; tell the user, and point to the 1Password DeLoSecrets vault for the real destination.
- **Never scan or route into** `.git/`, dot-dirs, `_bmad*`, `node_modules`, or `worktrees/` (the contract's `ignore_dirs`/`ignore_hidden`).
- **Confidentiality:** all client material is confidential. Do not read/quote `.env*`; do not send content externally without authorization.

## Out of scope

- **Authoring the n8n workflow or the `n8n-nodes-folder-curator` node** → `delonet-n8n-architecture` (this skill provides the `plan` contract the node consumes; see references/automation-runbook.md for wiring).
- **Defining/validating Bloodbank event schemas** → `bloodbank-integration`.
- **Infra paths, rclone remotes, container/service names** → `delonet-conventions`.
- **BMAD planning/implementation artifacts** under `_bmad-output/` — never intake or reorganize those.
