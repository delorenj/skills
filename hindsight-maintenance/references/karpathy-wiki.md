---
pipeline-status: new
---
# karpathy-wiki — nightly memory → compounding wiki

Read for the nightly job that compiles newly-retained memories into a Karpathy LLM wiki, so the
memory store gains a human-readable, compounding article layer on top of the raw facts.

Composes the **`karpathy-llm-wiki`** skill (`~/code/skillex/all-skills/karpathy-llm-wiki/SKILL.md`).
That skill owns the `raw/` + `wiki/` format and the Ingest/Query/Lint workflows; this reference only
supplies it the right inputs on a schedule.

## Wiki home

Default `~/hindsight-wiki/` (override with `HS_WIKI_DIR`). One wiki for the whole system; each Hindsight
**bank becomes a topic** (`raw/<bank>/`, `wiki/<bank>/`). First run initializes via the karpathy skill's
Ingest — do not hand-create `raw/`/`wiki/`.

## Procedure (per run)

1. **Pick the working set.** Banks with new memories since their watermark:
   ```bash
   for b in $(hs_banks); do
     n=$("$SKILL_DIR/scripts/new-memories.sh" "$b" --count)
     [ "$n" -gt 0 ] && echo "$b $n"
   done
   ```
   Skip banks with 0 new. On a busy night this is a handful of banks, not 141.

2. **Export new memories per bank** (oldest-first; each row `id|created_at|fact_type|context|text`):
   ```bash
   "$SKILL_DIR/scripts/new-memories.sh" "$b" > "/tmp/hs-new-$b.txt"
   ```
   Capture the **max `created_at`** in that batch — it becomes the new watermark after a successful compile.

3. **Ingest via the karpathy-llm-wiki skill.** Load that skill and run its **Ingest** workflow with:
   - source material = the exported memories for bank `$b`,
   - topic = `$b`,
   - a source slug like `YYYY-MM-DD-<bank>-memories`.

   The skill fetches into `raw/<bank>/`, compiles/merges into `wiki/<bank>/` articles, runs cascade
   updates, and appends to `wiki/log.md`. Let it own conflict handling and article structure —
   do not write wiki files directly here.

4. **Advance the watermark — only after Ingest succeeds** for that bank:
   ```bash
   "$SKILL_DIR/scripts/new-memories.sh" "$b" --advance "<max created_at from step 2>"
   ```
   Advancing only on success means a crash re-ingests (harmless — Ingest merges) rather than
   silently dropping a night's memories.

5. **Optional Lint** (weekly, not nightly): run the karpathy skill's **Lint** workflow to auto-fix
   OKF frontmatter, index consistency, and broken internal links.

## Notes

- Watermark files: `~/.hindsight/maintenance/wiki-<bank>.watermark` (ISO timestamp). Deleting one
  re-ingests that bank's full history on the next run.
- First-ever run has no watermarks → `new-memories.sh` defaults to "last 24h". To seed the wiki from
  full history instead, pass an old `--since` (e.g. `--since 2000-01-01T00:00:00Z`) per bank once.
- Keep nightly scope sane: if a bank dumped thousands of facts, ingest in date-bounded chunks rather
  than one giant source file.
