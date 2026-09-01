# Registry Gotchas

Every entry is **Symptom → Cause → Fix → Why**. All of them were reproduced against the live registry and the shipped code.

## Index

| Symptom you are seeing | Jump to |
|---|---|
| `… differs from the shipped template` after you edited a script | [Template byte-equality](#project-local-skills-sync-engine-differs-from-the-shipped-template) |
| Audit is GREEN but the pack on disk is not the one you rendered | [Registry-root ladder](#pj-audit-is-green-but-the-pack-i-just-rendered-is-not-the-one-being-used) |
| `SKILL_DIR_MISSING` / `SKILL_MD_MISSING` from a registry pack | [Known-bad packs](#known-bad-packs-in-the-registry-today) |
| `$schema still points at the retired …` | [Dead schema URL](#schema-still-points-at-the-retired-httpsrawgithubusercontentcomskillexschemasmainskillsschemajson) |
| `skillex pack render --help` explodes | [MarkupError](#the-render-and-verify-help-output-crashes-with-markuperror) |
| A declared pack materializes zero skills | [Symlink packs](#a-declared-pack-materializes-zero-skills-and-verify-still-says-verified) |
| A pack you know is sealed reports "unsealed" | [Seal is per-pack.toml](#a-pack-you-pinned-reports-unsealed-even-though-you-sealed-it) |
| Hand-expanded `skills[]` entries keep coming back / won't drop | [Redundancy scoping](#skills-entries-i-expected-pj-migrate-to-drop-are-still-there) |
| `pj migrate --help` has no `--accept-registry-matches`, **or `pj audit` output doesn't match these docs** | [Stale global `pj` binary](#the-pj-on-path-is-a-stale-build-pj-audit-lies-and-migrate-flags-are-missing) |
| Skills vanished from every CLI after a topology change | [Loud failure](#skills-disappeared-from-every-cli-directory) |

---

## `Project-local skills sync engine differs from the shipped template`

**Symptom.** `pj audit` reports `Project-local skills sync engine differs from the shipped template` and/or `Skillex pack provisioning script is missing or unsafe`, even though the script "works fine". Verified live: `/home/delorenj/code/automatic-ai`, `/home/delorenj/code/agentboard`, and `/home/delorenj/code/intelliforia-mobile` all carry drifted copies (automatic-ai's is 449 lines against the template's 1422).

**Cause.** The rule compares the repo's `.mise/scripts/sync-skills.py` and `.mise/scripts/provision-packs.py` **byte for byte** against `pjangler/templates/commonproject/template/.mise/scripts/<name>.py`. There is no fuzzy match, no version header, no "close enough". Editing the repo copy guarantees a permanent audit failure, and `pj migrate` will overwrite your edit.

**Fix.** Edit the **template**, which lives in the `templates/commonproject` **git submodule**, then propagate:

```bash
# 1. Edit the ONE source of truth (a git submodule: git@github.com:delorenj/CommonProject.git)
$EDITOR /home/delorenj/code/33GOD/pjangler/templates/commonproject/template/.mise/scripts/sync-skills.py

# 2. Commit INSIDE the submodule, then bump the pointer in pjangler
git -C /home/delorenj/code/33GOD/pjangler/templates/commonproject add -A
git -C /home/delorenj/code/33GOD/pjangler/templates/commonproject commit -m "fix(skills): …"
git -C /home/delorenj/code/33GOD/pjangler/templates/commonproject push
git -C /home/delorenj/code/33GOD/pjangler add templates/commonproject
git -C /home/delorenj/code/33GOD/pjangler commit -m "chore(templates): bump CommonProject"

# 3. Propagate into each consuming repo — never by hand
cd <repo> && pj migrate skills.project-manifest --dry-run && pj migrate skills.project-manifest
cd <repo> && pj audit
```

**Why.** These two scripts are a security boundary: they decide where symlinks land, whether a payload is verified, and what gets deleted. Byte equality is the cheapest possible proof that every repo is running the same audited code. A "small local tweak" is indistinguishable from a tampered projection engine, so the rule refuses to distinguish them.

---

## `pj audit` is GREEN but the pack I just rendered is not the one being used

**Symptom.** You render and seal `packs/<name>/<version>` in `~/code/skillex`, `skillex pack verify` says VERIFIED, and a project that declares the pack still audits GREEN — but with the *old* payload, or with the pack reported as **unsealed** and getting structural checks only.

**Cause.** The registry-root ladder resolves in this order:

```
$PJ_SKILLS_REGISTRY_ROOT                       (used ALONE when set)
~/.agents/.cache/registries/<sanitized-url>    ← the sync clone, and it is NEVER auto-pulled
~/code/skillex                                 ← where you actually work
```

The cache clone sits **above** your developer checkout. Nothing refreshes it: `sync-skills.py` only clones when there is no checkout at all, and never `git pull`s an existing one; audits never fetch by design. Attestation promotion (a root whose `pack.toml` identifies the entry outranks an unattested one) rescues the *unattested* case, but two attested roots are still broken by contract order — **the cache wins**.

Verified live today: the cache clone at `~/.agents/.cache/registries/https___github_com_delorenj_skillex_git` carries `packs/bmad/6.10.2/` skill directories but **no `pack.toml` and no `SHA256SUMS`**, because those two files are still **untracked** in `~/code/skillex`. Both checkouts are at commit `6c43b5e`. Today the dev copy wins only because the cache copy is unattested; the moment `pack.toml` is committed and the cache is pulled at a stale commit, contract order takes over and the cache shadows your work.

**Fix.**

```bash
# 1. SEE which root each pack actually resolved to.
cd ~/code/skillex
uv run skillex pack manifest <repo>/.agents/skills.json --verify

# 2. If a pack resolved to ~/.agents/.cache/registries/… and you expected ~/code/skillex:
#    (a) commit and push the pack, then refresh the cache
git -C ~/code/skillex add packs/<name>/<version>/pack.toml packs/<name>/<version>/SHA256SUMS
git -C ~/code/skillex commit -m "feat(packs): seal <name> <version>" && git -C ~/code/skillex push
git -C ~/.agents/.cache/registries/https___github_com_delorenj_skillex_git pull

#    (b) or drop the cache clone entirely and let sync-skills.py re-create it
rm -rf ~/.agents/.cache/registries/https___github_com_delorenj_skillex_git

#    (c) or pin the ladder for this shell / this run
export PJ_SKILLS_REGISTRY_ROOT=~/code/skillex
uv run skillex pack manifest <repo>/.agents/skills.json --verify --registry-root ~/code/skillex

# 3. Re-project and re-audit.
cd <repo> && mise run skills-sync && pj audit
```

Fast tell that a pack is unsealed when you expected sealed:

```bash
uv run skillex pack verify <resolved-root>
# → "<name>@<ver> (unsealed, N skills, no pack.toml (globbed))"   ← the smoking gun
```

**Why.** Pinned packs must resolve **offline** and an audit must never mutate the machine it is auditing, so nothing may fetch during resolution. That is the right trade — but it means the cache is a *snapshot*, and a snapshot that predates your render is indistinguishable from the real thing by directory name alone. `pack.toml` is the only positive identity a pack has; a bare `packs/<name>/<version>/` directory is an unattested claim resting on a directory name anyone can create. **Never trust GREEN without printing the resolved root.**

---

## Known-bad packs in the registry today

**Symptom.** Declaring one of these packs fails the sync, or `skillex pack verify` exits 1:

```
error SKILL_DIR_MISSING at [freeform].skills[folder-curator]: declared skill 'folder-curator'
      has no directory at /home/delorenj/code/skillex/packs/folder-curator/folder-curator
error SKILL_MD_MISSING at [freeform].skills[apple]: declared skill 'apple' has no SKILL.md
```

**Cause.** Four of the eight pack roots in the registry are broken. Verified:

| Pack | Declares | On disk | Result |
|---|---|---|---|
| `packs/folder-curator` | 1 skill | only `pack.toml` + `README.md` | `SKILL_DIR_MISSING` ×1, `PAYLOAD_INVALID`, exit 1 |
| `packs/hindsight-maintenance` | 1 skill | only `pack.toml` + `README.md` | `SKILL_DIR_MISSING` ×1, `PAYLOAD_INVALID`, exit 1 |
| `packs/product-manager` | 5 skills | only `pack.toml` + `README.md` | `SKILL_DIR_MISSING` ×5, `PAYLOAD_INVALID`, exit 1 |
| `packs/hermes-base/0.18.2` | 18 skills | all 18 dirs exist; **14 of them lack a `SKILL.md`** | `SKILL_MD_MISSING` ×**14**, exit 1 |

The first three were authored as `pack.toml`-only declarations — someone wrote `[freeform].skills` and never copied the trees in. (All three emit `PAYLOAD_INVALID` as well: the payload walk cannot open a skill directory that does not exist.)

`hermes-base/0.18.2` is **partially** broken, not wholly. It was harvested from `~/.hermes/hermes-agent/skills`, whose layout is inconsistent — some entries are single skills, others are one directory level shallower than a pack's:

- **4 declared members are fine** and are *not* reported: `computer-use`, `dogfood`, `hermes-desktop-plugins`, `yuanbao` each hold a regular `SKILL.md`.
- **14 fail.** 13 of them are *category* dirs holding sub-skills plus a `DESCRIPTION.md` (`apple`, `autonomous-ai-agents`, `creative`, `data-science`, `email`, `github`, `media`, `mlops`, `note-taking`, `productivity`, `research`, `smart-home`, `social-media`). The 14th, `software-development`, is a category dir holding 9 sub-skills with **no `DESCRIPTION.md` at all** — so "category dirs holding sub-skills and a `DESCRIPTION.md`" describes 13 of the 14, not all of them.

Adding `--sealed` adds `SUMS_MISSING` on top of the same 14 errors; the exit code stays 1.

**Fix.** Do not declare these in any `packs[]` until they are repaired. Until then, reference the underlying skills individually via `skills[]`. To repair:

```bash
cd ~/code/skillex
uv run skillex pack verify packs/folder-curator          # exit 1, lists exactly what is missing

# Option A — materialize the declared trees (REAL dirs, no symlinks)
cp -r --dereference all-skills/folder-curator packs/folder-curator/folder-curator
uv run skillex pack verify packs/folder-curator

# Option B — correct the declaration to match reality
$EDITOR packs/folder-curator/pack.toml    # empty [freeform].skills → PACK_EMPTY warning, exit 0

# hermes-base: restructure to one skill dir per SKILL.md, then re-render
uv run skillex pack render packs/hermes-base/0.18.2 --name hermes-base --version 0.18.2 --check
```

Use `packs/bmad/6.10.2` as the shape to copy. `packs/33god-dev` (0 skills, `PACK_EMPTY` **warning**, exit 0) is the benign case: an empty pack is legal, an empty-but-declared one is not.

**Why.** `[freeform].skills` is the *authoritative* inventory — the contract deliberately does not fall back to globbing when a `pack.toml` exists, because a silent fallback would let a truncated checkout look complete. So a declaration with no tree behind it is a hard error, by design, and it always will be.

---

## `$schema still points at the retired https://raw.githubusercontent.com/skillex/schemas/main/skills.schema.json`

**Symptom.** `pj audit` reports the retired `$schema`; editors show no completion or validation for `.agents/skills.json`.

**Cause.** The `github.com/skillex/schemas` repository does not exist — that URL **404s**. The canonical location is the schema committed at the skillex repo root.

**Fix.**

```json
"$schema": "https://raw.githubusercontent.com/delorenj/skillex/main/skills.schema.json"
```

```bash
pj migrate skills.project-manifest      # rewrites it, and provision-packs.py force-writes it too
```

The working copy on disk is `~/.agents/skills.schema.json`; the published file is `~/code/skillex/skills.schema.json`.

**Why.** The old URL is *accepted on read* so an un-migrated repo still audits rather than hard-failing on a cosmetic field — but it is reported every run and rewritten on migrate, so it cannot quietly persist. `provision-packs.py` also force-writes the canonical value on every provisioning run, which means a stale `$schema` in a project that provisions packs is self-healing.

---

## The render and verify help output crashes with MarkupError

**Symptom.**

```
$ uv run skillex pack render --help
MarkupError: closing tag '[/<version>]' at position 33 doesn't match any open tag
$ echo $?
1
```

Same for `skillex pack verify --help`. `skillex pack manifest --help` and `skillex pack list --help` work fine (exit 0).

**Cause.** Both commands declare `root: Path = typer.Argument(..., help="Pack root directory (packs/<name>[/<version>])")`. Typer renders help through `rich`, which parses `[/<version>]` as a **closing style tag** and raises before any help text is printed. The commands themselves are unaffected — only `--help` is broken.

**Fix.** Read the flags from [pack-authoring.md](./pack-authoring.md#command-reference) rather than from `--help`. To repair it upstream, escape the brackets in `skillex/src/skillex/commands/pack.py` (both `render_cmd` and `verify_cmd`) — e.g. `packs/<name>\[/<version>\]` — or wrap the string in `rich.markup.escape`. The same file already escapes lint messages for exactly this reason (`escape(issue.location)`), so the pattern is established.

**Why.** Worth flagging because a crashing `--help` reads like a broken install and sends you to reinstall the tool. It is a two-character formatting bug in a help string; the commands work.

---

## A declared pack materializes zero skills (and `verify` still says VERIFIED)

**Symptom.**

```
$ uv run skillex pack verify packs/Kurzgesagt
Kurzgesagt@0.0.0 (unsealed, 0 skills, no pack.toml (globbed))
  warn SKILL_DIR_SYMLINK_SKIPPED: 9 symlinked entries look like skills but are excluded
       from the inventory and the payload (symlinks are never pack content)
  warn PACK_EMPTY at (globbed): pack declares no skills (every candidate directory is a symlink)
VERIFIED (with warnings)          exit 0
```

**Cause.** `packs/Kurzgesagt/` is twelve **symlinks** into `all-skills/`. The contract excludes symlinks from both the globbed inventory and the payload, so the inventory is empty and the pack projects nothing. (Only 9 of the 12 are even *reported*: `ecosystem-patterns`, `hindsight` and `skill-creator` are **dangling** — their `all-skills/` targets no longer exist.) This is a skill-**set** that was filed under `packs/`.

**Fix.** Decide which role it should play:

```bash
# It is a curated loadout of catalog skills → it belongs in skill-sets/
git -C ~/code/skillex mv packs/Kurzgesagt skill-sets/kurzgesagt
# then reference members individually:
#   {"name": "agno", "registry_path": "skill-sets/kurzgesagt/agno"}

# It really should ship as a unit → dereference into real directories and render
cp -r --dereference packs/Kurzgesagt packs/kurzgesagt-real
uv run skillex pack render packs/kurzgesagt-real --name kurzgesagt --version 1.0.0 --check
```

**Why.** Symlinks are excluded from packs deliberately: a pack is meant to be a self-contained, hashable payload, and a symlink's content lives outside the pack root where no checksum can reach it. Allowing them would make a "sealed" pack seal nothing.

> **Kurzgesagt was the wrong example for the version-layout discriminator — now corrected.** The code comments in `sync-skills.py:select_pack_version`, `pack.ts:selectPackVersion`, `loader.py:select_pack_version` — and `agent-config-fanout/references/skill-packs.md` — used to justify the discriminator with *"`packs/Kurzgesagt/` is twelve skill directories and no `pack.toml`"*. On disk they are twelve **symlinks**, so the discriminator disqualifies the layout at the `is_symlink()` check and never reaches the `SKILL.md` test. The **rule was always correct and correctly implemented**; only the cited example was wrong. All four surfaces have been corrected — if you find a copy still citing Kurzgesagt as "twelve skill directories", it is stale, and the row `packs/Kurzgesagt/<skill dirs>  flat, NO pack.toml, 12 skill dirs` should read *12 symlinks, 0 members*.

---

## A pack you pinned reports "unsealed" even though you sealed it

**Symptom.** `skillex pack verify packs/bmad/6.10.1-next.31` prints `(unsealed, 76 skills, pack.toml)` and passes with structural checks only, even though a `SHA256SUMS` is right there.

**Cause.** Sealing is driven by `[policy] sealed = true` in `pack.toml`, **not** by the presence of `SHA256SUMS`. `6.10.1-next.31` predates the `sealed` key: its `[policy]` is `{immutable = true, project_projection = "symlink"}`. `immutable = true` alone does **not** imply sealed — immutability is an authoring policy, sealing is a consumer-side check.

**Fix.** Tighten from the consumer side, or re-render:

```bash
# Consumer side — force verification for one entry
#   {"name": "bmad", "version": "6.10.1-next.31", "sealed": true}
uv run skillex pack verify packs/bmad/6.10.1-next.31 --sealed

# Author side — re-render with the key (needs --force: the pack is immutable)
uv run skillex pack render packs/bmad/6.10.1-next.31 --name bmad --version 6.10.1-next.31 --force
```

`provision-packs.py` already does the consumer-side tightening for the implicit BMAD pin — it hardcodes `"sealed": True` for exactly this reason.

**Why.** The manifest may only **TIGHTEN**: `sealed: true` forces verification even when `pack.toml` omits it, but `sealed: false` in a manifest can never disable a pack whose `pack.toml` declares `[policy] sealed = true`. Integrity is a floor, never a ceiling.

---

## `skills[]` entries I expected `pj migrate` to drop are still there

**Symptom.** You declared `packs: [{"name":"bmad","version":"6.10.2"}]`, ran `pj migrate`, and a handful of hand-expanded `bmad-*` entries survived. Verified live: 73 of 76 dropped in `automatic-ai`, 3 survived.

**Cause.** By design. §6 marks an entry redundant only when **(a)** its resolved source lands inside the pack's own root, or **(b)** its **name is in the resolved pack's DECLARED inventory** *and* its source points into the pack family `packs/<name>/`. The 3 survivors — `bmad-deep-recon`, `bmad-editorial-review`, `bmad-review` — are exactly the members `6.10.2` **dropped**. They are not in the new inventory, so neither clause fires.

Other reasons an entry survives:

- Its source is not a `file:` URI (a `registry_path`, `git@`, `https://` entry is never redundant).
- It points **outside** `packs/<name>/` — a local tree, a different registry, a customized copy.
- The pack is declared in the **global** manifest and the entry is in the **project** manifest, or vice versa. Redundancy is scoped to a **single manifest**.

**Fix.** Nothing, usually — the survivors are correct. If you want them gone, remove them by hand, or re-home them out of `packs/` into `all-skills/` and rewrite the entry to a bare name.

```bash
pj audit    # names every entry it considers redundant; anything unlisted survives on purpose
```

**Why.** "Never remove entries that point outside the pack" is a hard rule: a customized copy of a pack member, or a skill a newer pack dropped, is the **user's**, and a migration that deletes it loses work with no recovery path. Pruning is deliberately narrow, and the family root is never treated as the pack's own extent — `packs/<name>/<other-version>/<skill>` is a different pack.

---

## The pj on PATH is a stale build: pj audit lies and migrate flags are missing

**This applies to EVERY `pj` invocation in this skill, not just `pj migrate --help`.** Read it before you trust any `pj` output you see quoted here.

**Symptom A.** `pj migrate --help` shows only `--all`, `--dry-run`, `--json`. Passing `--accept-registry-matches` errors.

**Symptom B.** `pj audit` reports a `skills.project-manifest` result that does not match anything documented — neither the pack-era duplicate/projection detail strings nor a clean pass. Verified live in `/home/delorenj/code/automatic-ai`:

```
# installed pj (stale) — reports six PRE-pack-era migration issues
$ pj audit
✖  skills.project-manifest    6 Skillex migration issue(s) detected
   ↳ .agents/skills.json should record all 76 BMAD 6.10.1-next.31 pack entries as file:// sources
   ↳ 76 managed BMAD skill path(s) should be symlinks into the 6.10.1-next.31 pack
   …

# repo build — the current contract
$ node /home/delorenj/code/33GOD/pjangler/dist/index.js audit
✔  skills.project-manifest    Skillex skills manifest parity verified
```

**Cause.** The `pj` on PATH is a stale publish. Verified: the globally installed `@delorenj/pjangler` (`~/.local/share/mise/installs/node/26.5.0/lib/node_modules/@delorenj/pjangler/dist/index.js`) reports version `1.2.25` and contains **zero** occurrences of `accept-registry-matches` and **zero** of `should be symlinks into their declared` — the repo's `dist/index.js` reports the **same** `1.2.25` and contains both. Same version string, different bytes. The stale build still carries the hardcoded BMAD `6.10.1-next.31` pin and knows nothing about `packs[]`, so on a migrated manifest it manufactures six issues that the current contract does not have.

**Fix.** Always drive contract work through the repo build:

```bash
node /home/delorenj/code/33GOD/pjangler/dist/index.js audit
node /home/delorenj/code/33GOD/pjangler/dist/index.js audit --json
node /home/delorenj/code/33GOD/pjangler/dist/index.js migrate --help    # confirms the flag exists
node /home/delorenj/code/33GOD/pjangler/dist/index.js migrate skills.project-manifest \
  --accept-registry-matches --dry-run
# or rebuild + reinstall the global package, then `pj` is safe again
```

Fast tell that your `pj` is stale:

```bash
grep -c accept-registry-matches "$(readlink -f "$(command -v pj)")"   # 0 → stale
grep -c accept-registry-matches /home/delorenj/code/33GOD/pjangler/dist/index.js
```

**Why.** A version string is not a build identity. When a pjangler feature described here appears to be missing — or `pj audit` reports something these docs never mention — check the repo build **before** concluding the feature does not exist or the docs are wrong. Otherwise you re-implement something that already shipped, or "fix" a manifest that was already correct.

---

## Skills disappeared from every CLI directory

**Symptom.** After moving a repo, changing its CLI layout, or removing a `.claude/` directory, `sync-skills.py` fails with:

```
No supported agent CLI skills directory exists under <base>; refusing to silently drop N skill(s): […]
```

**Cause.** A CLI skills directory is only written when its **parent** already exists — the sync creates `.claude/skills/`, not `.claude/`. If every one of the six parents is gone, there is nowhere to project.

**Fix.** Create the parent for at least one supported CLI, then re-run:

```bash
mkdir -p <repo>/.claude && python3 <repo>/.mise/scripts/sync-skills.py --scope project
```

Check the right paths for your scope — opencode is `.config/opencode/skills` globally but `.opencode/skills` in a project, and `.kimi/skills` is **retired** while `.kimi-code/skills` is supported. Full table: [fanout.md](./fanout.md#the-six-supported-clis).

**Why.** A sync that resolves skills but has nowhere to put them has **failed**. Reporting success there is how a topology change silently unprojects every skill in a repo and nobody notices until an agent starts answering without its skills — so the engine makes it loud instead.
