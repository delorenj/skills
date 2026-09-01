# Registry Topology and the SSoT Model

Where every artifact lives in `~/code/skillex`, what role it plays, and what the registry actually contains today.

## Reading Order

| Task | Read |
|---|---|
| Understand packs vs skill-sets vs all-skills | [The Three Roles](#the-three-roles) |
| Decide which one a new thing should be | [Choosing a role](#choosing-a-role) |
| Find the registry on disk / in git | [Registry location](#registry-location) |
| Audit what is in the registry right now | [Registry inventory (verified)](#registry-inventory-verified) |
| Understand pack layouts that must all work | [Pack layouts in the wild](#pack-layouts-in-the-wild) |

## Registry location

| Thing | Value |
|---|---|
| Git remote | `git@github.com:delorenj/skillex.git` |
| Canonical developer checkout | `~/code/skillex` |
| Sync clone cache | `~/.agents/.cache/registries/https___github_com_delorenj_skillex_git` |
| Git-skill clone cache | `~/.agents/.cache/skills/<name>` |
| Registry URL used by manifests | `https://github.com/delorenj/skillex.git` |
| skillex CLI config | `~/.config/skillex/skillex.toml` — both roots are stored as **absolute** paths: `skills_root = "/home/delorenj/code/skillex/all-skills"`, `packs_root = "/home/delorenj/code/skillex/packs"` |
| Canonical schema | `~/code/skillex/skills.schema.json`, mirrored at `~/.agents/skills.schema.json` |

## The Three Roles

```
packs/       SOURCES     self-contained, materializable, addressed by ONE manifest entry
skill-sets/  SELECTIONS  curated loadouts, symlink compositions, NOT materializable
all-skills/  CATALOG     one real directory per skill; the single source of truth
```

### `all-skills/` — the CATALOG

Visible children are **not** all skills. The directory also contains support
directories, manifests, and aliases, so raw `ls` counts are not a stable catalog
metric. A resolvable bare-name entry must be either a real directory containing
`SKILL.md` or a symlink that resolves to such a directory.

A skill *authored here* exists here **once**; everything else references it.
Aliases may surface skills authored in `/home/delorenj/code/33GOD/skills/`, but
an alias must never resolve to a repository root or to an ancestor of a fanout
destination. Never duplicate skill *content* into a skill-set or a pack that
also lives here — copy or symlink, never fork.

Referenced from a manifest by bare-string shorthand: `"foo"` expands to `all-skills/foo` (see [manifest.md](./manifest.md#skills-entry-forms)).

### `skill-sets/<name>/` — SELECTIONS

Directories of **symlinks** into `all-skills/` (and occasionally into `/home/delorenj/code/33GOD/skills/...`). Eight sets today: `33god`, `cloudflare-focused`, `delodocs`, `global`, `hyperframes`, `n8n`, `product-manager`, `tflo`.

A skill-set is addressed from a manifest as a `registry_path`, one entry per member:

```json
{ "name": "hindsight", "registry_path": "skill-sets/33god/hindsight" }
```

**A skill-set is NOT a pack.** The pack contract excludes symlinks from both the inventory and the payload, so pointing `packs[]` at a symlink tree yields an empty pack. `packs/Kurzgesagt/` is exactly this mistake, preserved in the registry — see [gotchas.md](./gotchas.md#a-declared-pack-materializes-zero-skills-and-verify-still-says-verified).

### `packs/<name>[/<version>]/` — SOURCES

A pack is a self-contained tree of **real** skill directories that a manifest declares as one entry. Declaring `{"name":"bmad","version":"6.10.2"}` materializes all 75 members. Packs carry their own identity (`pack.toml`), their own integrity (`SHA256SUMS`), and their own version directory.

Full anatomy: [pack-authoring.md](./pack-authoring.md).

## Choosing a role

```
New thing to add to the registry
├─ One skill you will hand-maintain and reuse everywhere
│  └─ all-skills/<name>/ ................ CATALOG entry; reference by bare name
├─ A curated loadout of EXISTING catalog skills for one context
│  └─ skill-sets/<set>/<name> -> ../../all-skills/<name> ......... SELECTION
└─ A versioned bundle you ship, pin, and verify as a unit
   (upstream import, vendored release, sealed payload)
   └─ packs/<name>/<version>/ ........... SOURCE; declare in packs[]
```

Tiebreakers:

- Does it need a **version pin**? → pack.
- Does it need **integrity verification** (SHA256SUMS, sealing)? → pack.
- Do the members already exist in `all-skills/`? → skill-set, not a pack.
- Is it a single capability? → catalog entry, referenced directly in `skills[]`.

## Registry inventory (verified)

Run `cd ~/code/skillex && uv run skillex pack list` for the live view. As verified for this document:

| Pack | Layout | Declared skills | Seal | `skillex pack verify` |
|---|---|---|---|---|
| `packs/bmad/6.10.2` | versioned | 75 | `sealed = true` | **VERIFIED** (exit 0) |
| `packs/bmad/6.10.1-next.31` | versioned | 76 | no `sealed` key | VERIFIED, reported *unsealed* |
| `packs/hermes-base/0.18.2` | versioned | 18 | no `sealed` key (has `overlay_wins`, `base_readonly`) | **FAILED** — **14** × `SKILL_MD_MISSING` (14 of the 18 declared members lack a `SKILL.md`; exit 1). With `--sealed`, the same 14 plus `SUMS_MISSING`, still exit 1. |
| `packs/33god-dev` | flat | 0 | none | VERIFIED with `PACK_EMPTY` warning |
| `packs/Kurzgesagt` | flat, no `pack.toml` | 0 (12 symlinks, **9 reported skipped**) | none | VERIFIED with warnings (exit 0) |
| `packs/folder-curator` | flat | 1 | none | **FAILED** — `SKILL_DIR_MISSING` (exit 1) |
| `packs/hindsight-maintenance` | flat | 1 | none | **FAILED** — `SKILL_DIR_MISSING` |
| `packs/product-manager` | flat | 5 | none | **FAILED** — 5 × `SKILL_DIR_MISSING` |

Four of the eight pack roots are **broken today**. Details and the fix for each: [gotchas.md](./gotchas.md#known-bad-packs-in-the-registry-today).

> **Why Kurzgesagt says 9 and not 12.** `packs/Kurzgesagt/` holds twelve symlinks, but `SKILL_DIR_SYMLINK_SKIPPED` names only **9** of them. `ecosystem-patterns`, `hindsight` and `skill-creator` are **dangling** — their `all-skills/` targets no longer exist — so they never become candidates and are never counted as skipped. `12 symlinks → 9 reported skipped → 0 members` is the full chain.

Treat `packs/bmad/6.10.2` as the reference implementation of a correct pack.

## Pack layouts in the wild

All of these are legal and all of them are exercised by the shipped resolver:

```
packs/33god-dev/pack.toml               flat, unversioned, pack.toml, ZERO skill dirs
packs/folder-curator/pack.toml          flat, unversioned, pack.toml
packs/Kurzgesagt/<symlinks>             flat, NO pack.toml (glob inventory applies)
packs/bmad/<version>/pack.toml          versioned, pack.toml + SHA256SUMS
packs/hermes-base/0.18.2/               versioned, pack.toml, plus a stray
                                        hermes-base-guard.py + README.md at the
                                        pack root (non-payload, ignored)
```

### The version-layout discriminator

`packs/<name>/` is treated as a **version layout** (and the highest version auto-selected) only when *every* non-dotted child is:

1. a real directory (not a symlink, not a stray file), **and**
2. does **not** contain a regular `SKILL.md`.

Any symlink, any stray file, or any child holding a `SKILL.md` makes it a **flat pack** instead, and the glob inventory applies. Implemented identically in `sync-skills.py:select_pack_version`, `pjangler/src/parity/pack.ts:selectPackVersion`, and `skillex/core/loader.py:select_pack_version`.

> **Kurzgesagt is not an example of condition 2.** The code comments in all three surfaces used to justify this rule with "`packs/Kurzgesagt/` is twelve skill directories". On disk it is twelve **symlinks**, so it is disqualified by condition **1** and never reaches the `SKILL.md` test. The rule was always correct; only the cited rationale was wrong, and the comments in all three surfaces have since been corrected. Condition 2 is what separates a `pack.toml`-less directory of **real** skill directories (a flat pack, glob inventory) from `packs/bmad/`, whose children `6.10.1-next.31/` and `6.10.2/` are real directories that hold **no** top-level `SKILL.md` (a version layout). See [gotchas.md](./gotchas.md#a-declared-pack-materializes-zero-skills-and-verify-still-says-verified).

## Where a projection lands

| Layer | Path | Written by |
|---|---|---|
| Pack projection (project) | `<repo>/.agents/skills/<name>` → pack root | `provision-packs.py` |
| CLI fan-out (project) | `<repo>/<cli>/skills/<name>` → resolved path | `sync-skills.py --scope project` |
| CLI fan-out (global) | `~/<cli>/skills/<name>` → resolved path | `sync-skills.py --scope global` |
| Legacy backup | `<repo>/.agents/skills.bak/<name>` | `pj migrate … --accept-registry-matches` |

Details, the six CLI directories, and the retired list: [fanout.md](./fanout.md).
