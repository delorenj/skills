---
pipeline-status: new
---
# Taxonomy spec

The exhaustive rules the CLI interprets. All of this is data in `assets/taxonomy.default.yaml` (the shipped **default profile** — Automatic AI client folders); a per-directory `<dir>/.curator/taxonomy.yaml` deep-merges over it, so a new directory only declares what differs. Edit the contract, not the code — and when a rule needs to change structurally, use [structure-evolution.md](./structure-evolution.md).

## `purpose`

A top-level string stating what the directory's curator is for. The agent consults it to judge files the deterministic rules can't classify; `plan` echoes it on `confidence: low` items. It is the one field every profile should set — it's what makes the curator *understand* the directory rather than just pattern-match it.

## Categories and classification

Files are classified by matching a category's `rules` (top-to-bottom, first category with any matching rule wins). **Exactly one** category match → route it (`confidence: medium`). **Zero or more than one** match (a keyword collision, e.g. a workshop PDF whose title merely says "based on transcripts") → park in the review queue: `client_dropbox`, `confidence: low`, `pipeline-status: new`. This is deliberate — ambiguity is handed to a human/agent, never guessed.

| Folder | Definition | Signals (any match) | Default `kind` |
|---|---|---|---|
| `threads/` | Communication involving **>1 person** | name matches transcript/xscript/otter/meeting/call/interview/email/mail/slack/thread/dm; frontmatter has `attendees`; sidecar `diarized: true` or `speaker_count ≥ 2` | `communication` |
| `workshop/` | **Single-author** work product | name matches strateg*/pricing/price/quote/plan/proposal/vision/approach/research/analysis/brief/memo/update/roadmap/spec/estimate/scope/deck | `work-product` |
| `client_dropbox/` | Raw client uploads + review queue | audio ext (`.ogg/.m4a/.mp3/.wav/.webm/.aac`) → `voice-note`; a `.meta.json` sidecar with a `model` key → `transcription` | `raw-upload` |

Rule predicates available (mix freely per rule): `name_regex`, `ext`, `has_frontmatter_key`, `meta_json_true`, `meta_json_key`, `meta_json_min: {key: N}`, and per-rule `kind` override.

**Not intake targets** (never routed/renamed): `profile.md`, `TASKS.md`, `docs/`, `_bmad-output/`, and anything in `ignore_dirs` (`.git`, `_bmad`, `_skf*`, `node_modules`, `worktrees`, `.curator`) or hidden (dot-prefixed).

## Naming

Canonical: **`YYYY-MM-DD-<slug>.<ext>`**. Timestamped items in `client_dropbox` use **`YYYY-MM-DD-HHMMSS-<slug>`** (avoids same-minute collisions).

Date resolution priority (the semantic date wins over the filename): explicit frontmatter `captured` → a leading filename date/time (`YYYY-MM-DD`, `YYYYMMDD`, `YYYY-MM-DD HH.MM.SS`, or compact `YYYYMMDDHHMM[SS]`) → other frontmatter dates (`date`/`created`/`modified`) → file mtime.

Slug construction:
1. `repairs` fix corrupted prefixes, e.g. `202607130email-` → `20260713-email-`.
2. `strip_substrings` remove cruft: `"Automatic AI LLC Mail - "`, `_otter_ai_transcript`, `"Personal Meeting Room"`, `"'s "`.
3. The leading date/time token is removed.
4. A leading **medium token** (`xscript`, `email`, `mail`, `slack`, `note`, `voice`) becomes the `kind` field and is dropped from the slug — mediums are labels, not filename segments.
5. What remains is slugified (lowercase, hyphen-separated, punctuation/em-dash stripped, capped at `slug_max_words`). If empty, fall back to the doc title/first heading (with date/extension tokens stripped), then to the `kind`.

Collisions append seconds, then `-2`, `-3`.

## Frontmatter schema (unified)

Written in this key order: `category, kind, title, source, captured, updated, pipeline-status, confidence, owner, tags, attendees`, then any preserved extras.

| Key | Meaning | Notes |
|---|---|---|
| `category` | Owning folder | lowercase; set by classification |
| `kind` | Medium/type label | lowercase; e.g. `transcript`, `email`, `work-product`, `voice-note`, `transcription`, `raw-upload` |
| `title` | Human title | from existing title, first `# heading`, or the cleaned filename |
| `source` | Provenance | defaults to the original filename |
| `captured` | Origination date (ISO `YYYY-MM-DD`) | the semantic date of the artifact |
| `updated` | Freshness (ISO datetime) | **bumped to now on intake/touch**; drives recency + mtime restore |
| `pipeline-status` | Workflow state | list; exactly one of `new`, `processing`, `processed`, `blocked` |
| `confidence` | Classification/synthesis certainty | `low`/`medium`/`high` |
| `tags`, `owner`, `attendees`, … | Optional labels / per-medium fields | `tags` is canonical (migrated from `labels`) |

**Legacy key migration** (`aliases`): `labels→tags`, `last_enriched→updated`, `last-verified→updated`, `modified→updated`, `created→captured`, `date→captured`, `prospect-name→person`, `Category→category`. Values are carried over; the old key is dropped. Existing non-schema keys (e.g. `description`, `key-points`, `enrichment-provider`) are **preserved** — enrichment is additive, never destructive.

PyYAML auto-parses ISO strings into date/datetime objects; the CLI re-emits `captured` as `YYYY-MM-DD` and `updated` as full ISO so both stay stable strings.

## Secrets

A file whose **name or content** matches the `secrets` patterns (`cred`, `password`, `secret`, `api-key`, `token`, `private key`, `.env`, `-----BEGIN … PRIVATE KEY-----`, `aws_secret_access_key`, `password:`/`api_key:` assignments) is **quarantined**: moved to `.curator/quarantine/` (git-ignored), `pipeline-status: blocked`, never enriched/committed/synced. Binary types (pdf/images/audio/zip) are skipped for content scanning. Tell the user; the real home for a credential is the 1Password DeLoSecrets vault.

## Recency / context stack

- `updated` is the single source of truth for freshness.
- `reindex` regenerates `_context-stack.md` at the client root: a newest-first table across `index_dirs` (`threads`, `workshop`, `client_dropbox`) plus `index_root_files` (`profile.md`, `TASKS.md`), each row `Updated | Category | Kind | Title | [[wikilink]]`.
- `reindex` also restores every file's mtime from its `updated` (`restore_mtime: true`) so `ls -lt`/`llr` reflect document freshness even after git/rclone rewrite mtimes. For non-markdown files (no embeddable frontmatter), freshness/kind/title come from `.curator/ledger.json`.

## Idempotency

`apply`/`normalize --apply` record each result in `.curator/ledger.json` keyed by content hash (`status: done`). Re-running skips files already recorded — this is what makes the n8n/Bloodbank drain safe to retry. Secrets are recorded `status: blocked`.
