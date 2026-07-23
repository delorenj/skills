---
pipeline-status: new
---
# Structure evolution (recommend → approve → apply)

The current folder layout is the owner's working *vision*, not a proven optimum. This procedure lets the taxonomy improve over time: examine the current structure plus whatever just arrived, **recommend** changes, and — only on explicit approval — **apply** them and propagate the change to the contract, the docs, and every downstream consumer. This is judgment work: the agent drives it, the human approves it. It is never automatic.

## When to run it

- A new file (or batch) doesn't fit any category cleanly — it keeps landing in the `client_dropbox` review queue at `confidence: low`.
- The review queue accumulates several items that clearly share a theme → a category or rule is missing.
- You observe drift: coexisting filename conventions, two frontmatter schemas, `tags` vs `labels`, a canonical file that has been renamed and now has stale references.
- The owner asks to add/rename/retire a category, or change a naming or frontmatter rule.

## Inputs

1. **Current structure** — run `folder-curator --client-root . reindex` and read `_context-stack.md`; scan the category folders and `.curator/ledger.json`; note review-queue (`pipeline-status: new`, `confidence: low`) items and any secrets in quarantine.
2. **The contract** — `assets/taxonomy.default.yaml` merged with `.curator/taxonomy.yaml`.
3. **The incoming input** — the file or list under consideration.

## Produce a proposal (never auto-apply)

Emit a written **review artifact** the owner can accept or reject, containing:

- **Diagnosis** — the specific gap/drift, with evidence (e.g. "6 review-queue items are pricing sheets → `workshop` rule misses the word 'estimate'"; "`labels` still appears in 3 files").
- **Proposed contract edits** — concretely, the YAML diff: a new/renamed `categories` entry, an added `rules` predicate, a new `aliases` mapping, a `strip_substrings`/`repairs` addition. Prefer the smallest declarative change that generalizes.
- **File migrations** — which files move/rename/re-enrich as a result (get this from a `normalize` dry-run after the proposed edit).
- **Doc + downstream updates** — which `AGENTS.md` files change, and whether the skill package or the n8n node must be regenerated.
- **Risk/consequences** — placement-vs-metadata mismatches, links that would break, provenance concerns.

Bias toward **labels over folders**: add a `kind`/`tags` value or a classification rule before adding a new top-level folder. Add a folder only when a whole *class* of documents recurs and a frontmatter label can't express the distinction people actually navigate by.

## On approval, apply as one coherent change

1. **Edit the contract** — the per-client `.curator/taxonomy.yaml` for client-specific rules; `assets/taxonomy.default.yaml` only for changes that should apply to *every* client.
2. **Migrate files** — `normalize --apply` (name + frontmatter), plus any category folder renames (e.g. the `Research/ → workshop/` rename) done with `git mv` where files are tracked.
3. **Reindex** — regenerate `_context-stack.md` and restore mtimes.
4. **Update the docs** — reconcile `/home/delorenj/code/AutomaticAI/AGENTS.md` (the authoritative taxonomy) and the nested `Prospects/<client>/AGENTS.md`; fix stale references (e.g. a profile once called `Client Profile.md` that is now `profile.md`). These `AGENTS.md` files are the agent-agnostic instruction surface — `CLAUDE.md`/`GEMINI.md` are symlinks to them, so updating `AGENTS.md` updates every harness at once.
5. **Propagate to consumers when the skill itself changed:**
   - If `SKILL.md`, `references/`, or `assets/taxonomy.default.yaml` changed → re-fan-out: `skillex pack activate <pack> --scope global` (and `--scope project` in the repo), then `skillex status` to confirm every harness relinked.
   - If classification rules changed and the n8n custom node is live → regenerate `n8n-nodes-folder-curator` from the contract and redeploy (see [automation-runbook.md](./automation-runbook.md)); until then the transitional Execute-Command CLI already reflects the new contract with no rebuild.
6. **Record the decision** — a one-line rationale in the proposal's resolution (optionally a Bloodbank decision event or a hindsight retain) so the *why* survives.

## Discipline

- Change **data (the contract), not code.** Keep rules declarative so the CLI and the n8n node stay in sync.
- Migrate in **one coherent pass**; a half-applied taxonomy change leaves the repo inconsistent.
- Preserve provenance and confidentiality throughout (the same rules as intake): never fabricate, never leak, never touch `.env*` or quarantined secrets.
- Seed cases this procedure already owns: the `Research → workshop` rename, unifying the two coexisting frontmatter schemas (`person`/`captured`/`last-verified` vs `prospect-name`/`created`/`modified`), and standardizing `labels → tags`.
