---
pipeline-status:
  - new
---
# Skill packs (`packs[]` in `.agents/skills.json`)

A **pack** is a directory of skills in the registry, addressed by name (and usually version),
that a manifest declares as ONE entry instead of listing every member skill by hand. Declaring
`{"name": "bmad", "version": "6.10.2"}` materializes all 75 of its skills.

> **This file is the ENGINE-side view of the packs contract.** For **registry operations** — what is
> in `~/code/skillex` today, cutting/versioning/sealing a pack, `skillex pack render|verify|manifest`,
> curating `all-skills/` and `skill-sets/`, fixing a broken `.agents/skills.json`, and the
> `pj audit` / `pj migrate` failure catalogue — use the registry-operations hub skill:
> **`/home/delorenj/code/33GOD/skills/skillex-skill-registry/`**
> ([topology](/home/delorenj/code/33GOD/skills/skillex-skill-registry/references/topology.md) ·
> [manifest](/home/delorenj/code/33GOD/skills/skillex-skill-registry/references/manifest.md) ·
> [pack authoring](/home/delorenj/code/33GOD/skills/skillex-skill-registry/references/pack-authoring.md) ·
> [gotchas](/home/delorenj/code/33GOD/skills/skillex-skill-registry/references/gotchas.md)).
> That skill links back here for the fan-out engine mechanics; the two are complementary halves of
> one contract and must not disagree.

This file is the operator reference for the packs contract. The three implementations that MUST
agree on it:

| Surface | Where | Owns |
|---|---|---|
| `sync-skills.py` | `<repo>/.mise/scripts/sync-skills.py` (rendered by CommonProject) | resolve + verify packs, fan out every skill into the six CLI dirs |
| `provision-packs.py` | `<repo>/.mise/scripts/provision-packs.py` | transactional projection of pack members into `.agents/skills/` (imports the resolver from `sync-skills.py` verbatim — no second implementation) |
| `pjangler` parity | `pjangler/src/parity/pack.ts` + `index.ts` | `pj audit` reports drift, `pj migrate` rewrites manifests, mise tasks, and script names |
| `skillex pack` | `skillex/src/skillex/commands/pack.py` | author side: `render` writes `pack.toml` + `SHA256SUMS`, `verify` checks a pack against this contract |

## Manifest shape

```json
{
  "$schema": "https://raw.githubusercontent.com/delorenj/skillex/main/skills.schema.json",
  "scope": "project",
  "inherit_global": true,
  "registry": "https://github.com/delorenj/skillex.git",
  "packs": [ { "name": "bmad", "version": "6.10.2" } ],
  "skills": [ { "name": "foo", "source": "file:///..." } ]
}
```

`packs` is an OPTIONAL array added alongside the pre-existing `skills`. `skills` keeps its exact
prior meaning — nothing about individual skill entries changed.

> The canonical `$schema` is `https://raw.githubusercontent.com/delorenj/skillex/main/skills.schema.json`
> (the file is committed at the skillex repo root and mirrored at `~/.agents/skills.schema.json`).
> The old `https://raw.githubusercontent.com/skillex/schemas/main/skills.schema.json` **404s**. It
> is accepted on read so an un-migrated repo still audits; `pj audit` reports it and `pj migrate`
> rewrites it.

## Pack entry forms

**String shorthand** — `"bmad"` → `{name:"bmad"}`; `"bmad@6.10.2"` → `{name:"bmad",version:"6.10.2"}`.

**Object form:**

| Field | Type | Meaning |
|---|---|---|
| `name` | string, **required** | One path component matching `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`. A non-conforming (but still safe) name warns rather than fails, so pre-convention packs stay resolvable. |
| `version` | string | Version directory under `packs/<name>/`. One path component. Omitted → see resolution step 2. |
| `source` | string | `file://` URI, `git@…`, or `https://…` override. **Mutually exclusive with `registry_path`.** |
| `registry` | string | Per-pack registry URL override. |
| `registry_path` | string | Explicit path inside the registry. Default `packs/<name>` or `packs/<name>/<version>`. |
| `include` | string[] | Only materialize these skill names. |
| `exclude` | string[] | Skip these names. Applied **after** `include`. |
| `optional` | bool (false) | A missing/unresolvable pack warns instead of failing. |
| `sealed` | bool | Force checksum verification. **May only TIGHTEN** (see Sealing). |

## Resolution order (pack root)

1. **`source` set** → resolve like a skill source. `file://` → local path (relative to the
   manifest's directory); git URL → clone into `~/.agents/.cache/skills/<name>` and check out
   `version` if given.
2. **Otherwise** → `<registry-checkout>/<registry_path>`, where `registry_path` defaults to
   `packs/<name>/<version>` when `version` is set, else `packs/<name>`.
   - If `version` is omitted **and** `packs/<name>/pack.toml` does not exist **and**
     `packs/<name>/` contains only subdirectories, the **highest** version directory is selected
     by PEP440/semver-ish ordering (numeric-segment aware; a `-next.N` prerelease sorts below the
     same release). **This is the only implicit choice in the whole contract.**
3. **Registry checkout roots**, tried in order: `$PJ_SKILLS_REGISTRY_ROOT` (if set) →
   `~/.agents/.cache/registries/<sanitized-url>` → `~/code/skillex`.
   An **audit NEVER clones or fetches.** `sync-skills.py` may clone (it always could), but it will
   not fetch when a checkout already exists — a pinned pack must resolve offline.

   `<sanitized-url>` is a **wire format, not an implementation detail**: every non-alphanumeric
   byte becomes `_` — `re.sub(r"[^a-zA-Z0-9]", "_", url)` / `url.replace(/[^a-zA-Z0-9]/g, "_")`.
   So `https://github.com/delorenj/skillex.git` → `https___github_com_delorenj_skillex_git`.
   Three surfaces address this one directory (`sync-skills.py:registry_cache_dir`,
   `skillex.paths.sanitize_registry_url`, pjangler `registryCacheDirName`) and they must agree
   byte-for-byte. When they don't, one manifest resolves to **two different checkouts on one
   machine**, and the same pack is SHA256SUMS-verified by one surface and structurally-only
   checked by another. `sync-skills.py` is the only surface allowed to clone, so it owns the
   name; the others follow.
4. The pack root MUST be a **real directory, not a symlink**, and no component of the path from
   the registry root down to it may be a symlink.

### "Only subdirectories" is necessary but not sufficient

A `packs/<name>/` with no `pack.toml` whose children are **real directories that each hold a regular
`SKILL.md`** satisfies "only subdirectories" and is emphatically **not** a version layout — it is a
**flat pack**, and the glob inventory below applies instead. The discriminator is what those children
*are*: a child holding a regular `SKILL.md` is a skill, so its parent cannot be a version root.
Contrast `packs/bmad/`, which is also `pack.toml`-less and also all real directories, but whose
children (`6.10.1-next.31/`, `6.10.2/`) hold **no** top-level `SKILL.md` — that is a version layout,
and the highest version is auto-selected.

> **`packs/Kurzgesagt/` is NOT an example of this rule.** Its twelve children are all **symlinks**
> (three of them — `ecosystem-patterns`, `hindsight`, `skill-creator` — dangling), so the layout is
> disqualified one check earlier, at the `is_symlink()` / `isSymbolicLink()` test in step 4, and never
> reaches the `SKILL.md` test at all. The glob inventory then yields **0** members, because symlinks
> are excluded from both the inventory and the payload. `skillex pack verify packs/Kurzgesagt` reports
> `0 skills`, `SKILL_DIR_SYMLINK_SKIPPED` for 9 of the 12 (dangling links are never candidates, so
> they are not even reported), and `PACK_EMPTY`. Earlier revisions of this file and of the three
> `select_pack_version` code comments cited it as "twelve skill directories"; that was wrong, and the
> rule above is the corrected statement.

Layouts in the wild that all must work:

```
packs/33god-dev/pack.toml           flat, unversioned, pack.toml, ZERO skill dirs
packs/folder-curator/pack.toml      flat, unversioned, pack.toml
packs/Kurzgesagt/<symlinks>         flat, NO pack.toml, 12 SYMLINKS -> 0 members
                                    (a skill-SET misfiled under packs/)
packs/bmad/<version>/               versioned, pack.toml
packs/hermes-base/0.18.2/           versioned, pack.toml, plus a stray hermes-base-guard.py
                                    at the pack root (rule 6: ignored, not payload)
```

## Skill inventory inside a pack

- **`pack.toml` exists** → inventory = `[freeform].skills`, the authoritative list of names.
  Validate `[pack].name == entry.name`, and when `entry.version` is set,
  `[pack].version == entry.version`. Duplicate names are an error.
- **`pack.toml` absent** → inventory = child directories that (a) do not start with `.` or `_`,
  and (b) contain a regular `SKILL.md`. A symlinked child is skipped with a warning.
- Every inventory name must be a **single safe path component**.
- Every inventory entry must be a **real directory** containing a **regular (non-symlink)**
  `SKILL.md`.
- Apply `include`, then `exclude`.

`pack.toml` shape (as written by `skillex pack render`):

```toml
[pack]
name = "bmad"
version = "6.10.2"
description = "Immutable BMAD agent-skill payload, shared through symlink projections."

[source]
upstream = "bmad-method"
upstream_version = "6.10.2"
rendered_from = ".agent/skills"
payload_files = 1055          # cross-check: payload count excluding pack.toml itself

[policy]
sealed = true
immutable = true

[freeform]
skills = [ "bmad-advanced-elicitation", "bmad-agent-analyst", … ]
```

`[source].payload_files`, when present and an integer, is verified against the actual payload
count for **every** pack — sealed or not. It is a cheap tripwire for a truncated checkout.

## Sealing and the payload

A pack is **sealed** when `pack.toml` has `[policy] sealed = true` **OR** the manifest entry sets
`sealed: true`. `[policy] immutable = true` **alone does NOT imply sealed** — immutability is an
authoring policy (`skillex pack render` refuses to re-render without `--force`); sealing is a
consumer-side integrity check.

> **The manifest may only TIGHTEN.** `sealed: true` in the manifest forces verification even if
> `pack.toml` omits it. `sealed: false` in the manifest **cannot** disable a pack whose
> `pack.toml` declares `[policy] sealed = true`.

**payload** = `pack.toml` + every file recursively under each **DECLARED** skill directory
(pre-`include`/`exclude`: the full declared inventory — narrowing what you install must not
narrow what you verify).

Verification rules, all of which must hold:

1. `SHA256SUMS` exists at the pack root and is a regular file.
2. Every payload file appears in `SHA256SUMS` with a matching sha256.
3. Every `SHA256SUMS` entry exists on disk with a matching sha256. `SHA256SUMS` may legitimately
   cover **extra non-payload files** such as `README.md`; those are still verified. It may **not**
   reference a path that is absent.
4. **No symlinks anywhere within the payload** — only regular files and real directories.
5. Paths in `SHA256SUMS` are relative, `/`-separated, with no `.`/`..`/empty segments, no
   backslashes, and not absolute. Duplicates are an error.
6. Files that are neither payload nor listed in `SHA256SUMS` are **IGNORED** (`.claude/`,
   `_bmad/`, `mise.toml`, `.project.json`, …).

Format: `SHA256SUMS` lines are `<64-hex><two spaces><relative/path>`, sorted by path.

Rule 3's "extra files are legal" clause is what keeps the older pinned
`packs/bmad/6.10.1-next.31` pack (76 skills, 1072 payload files, `SHA256SUMS` also covering
`README.md`) verifying byte-for-byte under the generic rules.

An empty directory inside the payload has nothing to hash and therefore cannot be authenticated;
sealed verification rejects unauthenticated empty directories rather than silently trusting them.

**Unsealed packs get STRUCTURAL validation only:** pack root is a real dir, `pack.toml` parses (if
present), every declared skill dir exists with a regular `SKILL.md`, no symlinks in the skill
payload, no path escapes.

### `optional` narrows to availability, never to integrity

Only "the pack (or a declared member) is simply not installed here" is downgraded to a warning by
`"optional": true`. Symlinks in the payload, path escapes, identity mismatches, and checksum
mismatches **always raise** and are never suppressed.

## Precedence

Lowest to highest:

1. global `packs[]` (in array order; a later pack wins a name collision)
2. global `skills[]`
3. project `packs[]`
4. project `skills[]`

Within `packs[]`, later entries override earlier ones. (Project layers only participate when the
project manifest sets `inherit_global: true` — otherwise the global layer is not loaded at all for
`--scope project`.)

**Then the subtle part: §6 redundancy pruning runs FIRST.** Contract §5 was revised. The old rule —
*"an explicit `skills[]` entry ALWAYS overrides a pack member of the same name"* — is **wrong** and
was a shipped bug; do not implement it. The correct two-step order, per manifest layer:

```
1. Resolve every packs[] entry; later packs override earlier ones by name.
2. For each skills[] entry in THIS layer:
     if "Migration semantics" below classifies it REDUNDANT against a pack declared
     in THIS SAME manifest
         -> DROP it. The pack member wins. It is NOT an override.
     else
         -> resolve it; it then ALWAYS overrides a pack member of the same name.
```

Only entries that **survive** pruning override pack members. Why it matters: with the naive
"explicit always wins" reading, a repo declaring `bmad@6.10.2` in `packs[]` while still carrying 76
hand-expanded `skills[]` entries pointing at `packs/bmad/6.10.1-next.31/…` would pin **every** member
back to the old version. Pruning first means the 73 names the new pack provides follow the new pack,
and only the 3 names it dropped stay pinned to the old tree.

Implemented in `sync-skills.py:PackScope`, re-exported into `provision-packs.py`
(`declared_pack_scope`), and mirrored by pjangler's `isRedundantDeclaredPackEntry` — all three must
resolve every name to the same path.

## Migration semantics

Declaring a pack **REPLACES** hand-expanded per-skill entries for that pack's members. When
`packs[]` names a pack, any `skills[]` entry whose resolved source path is contained by that pack's
root — or whose name is in the pack inventory and whose source points into *any* version of that
pack — is REDUNDANT and is removed by `pj migrate`. **Entries pointing outside the pack are never
removed.**

## Task and script naming

- `sync-skills.py` **keeps its name** and gained native `packs[]` support.
- `provision-bmad-skills.py` is **RENAMED to `provision-packs.py`** and generalized to provision
  every declared pack. `pj migrate` writes the new file and removes the old one; `pj audit`
  reports the stale file.
- The mise task `skills-provision-bmad` is **renamed to `skills-provision-packs`**, and
  `skills-sync` `depends` on it — provision materializes `.agents/skills/`, then sync fans that
  out to the CLI dirs. The `mise enter` hooks run in the same order.

```toml
[tasks.skills-sync]
description = "Sync skills from manifest to local CLI dirs"
depends = ["skills-provision-packs"]
run = "python3 '{{config_root}}/.mise/scripts/sync-skills.py' --scope project"

[tasks.skills-provision-packs]
description = "Provision every Skillex pack declared in .agents/skills.json"
run = "python3 '{{config_root}}/.mise/scripts/provision-packs.py'"
```

A project that declares **no** `bmad` pack still gets the pinned BMAD pack expanded into
`skills[]`, exactly as before. Declaring `{"name": "bmad", …}` in `packs[]` takes over and the pin
is not consulted.

## Fan-out targets — exactly six CLIs, scope aware

`CLI_SKILL_DIRS` is a per-scope mapping (relative to `$HOME` for `--scope global`, to the project
root for `--scope project`). Only opencode differs between scopes.

| CLI | global | project |
|---|---|---|
| Claude Code | `.claude/skills` | `.claude/skills` |
| Codex | `.codex/skills` | `.codex/skills` |
| Gemini | `.gemini/skills` | `.gemini/skills` |
| Copilot | `.copilot/skills` | `.copilot/skills` |
| opencode | `.config/opencode/skills` | `.opencode/skills` |
| Kimi Code | `.kimi-code/skills` | `.kimi-code/skills` |

**RETIRED — never written to again:** `.augment/skills`, `.hermes/skills`, `.openclaw/skills`,
`.kimi/skills`, `.crush/skills`, `.cursor/skills`.

Retired directories are **never auto-deleted**. `sync-skills.py --prune-retired` (opt-in) removes
ONLY entries in retired dirs that are **symlinks whose target resolves inside a known managed
root** (the registry checkout, a pack root, or `~/.agents/.cache`). Real directories and unmanaged
symlinks are never touched. Without the flag, sync only **reports** what it would prune.

> `~/.hermes/skills` is a writable Hermes runtime **OVERLAY**, not a projection of this manifest.
> It is never written to, never reported, and never pruned — it is excluded from the prune walk
> entirely (`NEVER_PRUNE_DIRS`).

## Security invariants (do not weaken these)

The pack path is attacker-adjacent: a registry checkout, a cache directory, and a project tree are
all things another process can mutate mid-run. The engine is deliberately hardened.

- **Preflight, then re-validate at the mutation boundary.** Every destination directory is
  validated *before* any registry clone, cache creation, or link change — so **one unsafe or broken
  symlink produces ZERO mutation** — and the whole destination chain is re-checked immediately
  before each individual mutation, because preflight and mutation are not atomic.
- **No symlinked destination directories, ever.** The single exception is the canonical alias
  `<cli>/skills -> .agents/skills`, matched **lexically** (never by resolving an arbitrary
  symlink, which would let cleanup traverse outside the project) and then confirmed to resolve to
  the real managed projection.
- **Nothing may escape its root.** Destinations are checked with `relative_to` against a resolved
  root; a skill destination must be exactly one component below its CLI directory.
- **Pack payloads contain only regular files and real directories.** A symlink found while walking
  the payload is a hard error, not a skip. Files are opened `O_NOFOLLOW` and confirmed
  `S_ISREG` on the *file descriptor* before being read or hashed, so the check cannot be raced.
- **Skill and pack names are exactly one safe path component.** `.`, `..`, absolute paths,
  slashes, and backslashes are all rejected — for manifest names, inventory names, and every path
  inside `SHA256SUMS`.
- **`provision-packs.py` is transactional.** A failure at any point rolls the project back to its
  exact prior state; `.agents/skills.json` is rewritten atomically, preserving its mode.

## Authoring a pack

```bash
# plan only — enumerate skills and payload, write nothing
skillex pack render packs/<name>/<version> --name <name> --version <version> --check

# write pack.toml + SHA256SUMS (sealed + immutable by default)
skillex pack render packs/<name>/<version> --name <name> --version <version> \
  --description "…" --upstream <pkg> --upstream-version <v>

# consumer-side check; --sealed forces verification even if pack.toml omits [policy] sealed
skillex pack verify packs/<name>/<version>
```

`render` refuses to overwrite a pack marked `[policy] immutable = true` without `--force`, and
writes nothing unless the whole payload enumerates and hashes cleanly first.
