# The `skills.json` Manifest

Full anatomy of `~/.agents/skills.json` (global) and `<repo>/.agents/skills.json` (project): entry forms, pack-root resolution, and the precedence order every surface must agree on.

## Reading Order

| Task | Read |
|---|---|
| Write a manifest from scratch | [Shape](#shape) then [packs entry forms](#packs-entry-forms) |
| Add a pack to an existing manifest | [packs entry forms](#packs-entry-forms) |
| Work out which copy of a pack will be used | [Pack root resolution](#pack-root-resolution) |
| Understand who wins between `packs[]` and `skills[]` | [Precedence](#precedence) — read it fully, it is subtle |
| Drop hand-expanded entries a pack now provides | [Redundancy (§6)](#redundancy-6) |
| Validate a manifest | [Validating](#validating) |

## Shape

```json
{
  "$schema": "https://raw.githubusercontent.com/delorenj/skillex/main/skills.schema.json",
  "scope": "project",
  "inherit_global": true,
  "registry": "https://github.com/delorenj/skillex.git",
  "packs": [ { "name": "bmad", "version": "6.10.2" } ],
  "skills": [ { "name": "foo", "source": "file:///home/delorenj/code/skillex/all-skills/foo" } ]
}
```

| Field | Meaning |
|---|---|
| `$schema` | Canonical URL above. The old `https://raw.githubusercontent.com/skillex/schemas/main/skills.schema.json` **404s**; it is accepted on read, reported by `pj audit`, rewritten by `pj migrate`. |
| `scope` | `"global"` or `"project"`. Documentation only — `sync-skills.py` takes scope from `--scope`, not from this field. |
| `inherit_global` | Only consulted for `--scope project`. When `true`, the global manifest is loaded as a lower-precedence layer. When absent/false, the global layer is **not loaded at all**. `provision-packs.py` force-writes this to `true`. |
| `registry` | Default registry URL for entries that do not override it. Defaults to `https://github.com/delorenj/skillex.git`. |
| `packs` | Optional array. NEW. |
| `skills` | Pre-existing array; meaning unchanged. |

The schema requires at least one of `skills` or `packs`.

> **Current state of the global manifest.** `~/.agents/skills.json` today contains only `{"scope":"global","skills":[…54 entries…]}` — no `$schema`, no `registry`, no `packs`. Adding `packs[]` there is legal and unblocked; nothing in the global layer declares a pack yet.

## `packs[]` entry forms

**String shorthand** — `"bmad"` → `{name:"bmad"}`; `"bmad@6.10.2"` → `{name:"bmad", version:"6.10.2"}`.

**Object form:**

| Field | Type | Meaning |
|---|---|---|
| `name` | string, **required** | Exactly one safe path component. The canonical shape `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` is enforced as a **warning** only, so pre-convention names such as `Kurzgesagt` stay resolvable. |
| `version` | string | Version directory under `packs/<name>/`. One path component. |
| `source` | string | `file://` URI, `git@…`, or `https://…`. **Mutually exclusive with `registry_path`.** |
| `registry` | string | Per-pack registry URL override. |
| `registry_path` | string | Explicit path inside the registry. Default `packs/<name>` or `packs/<name>/<version>`. |
| `include` | string[] | Materialize only these member names. |
| `exclude` | string[] | Skip these names. Applied **after** `include`. |
| `optional` | bool (default `false`) | A pack (or member) that is simply **not installed here** warns instead of failing. |
| `sealed` | bool | Force checksum verification. **Only TIGHTENS** — see [Sealing](./pack-authoring.md#sealing). |

`include` names that are not in the inventory produce a warning, not an error.

### `optional` narrows availability, never integrity

`optional: true` downgrades exactly one failure class: `PackUnavailable` — "the pack or a declared member is not installed here". Symlinks in the payload, path escapes, identity mismatches, digest mismatches, and a sealed pack missing a declared member **always raise** and are never suppressed.

## `skills[]` entry forms

- **Bare string** — `"foo"` → `all-skills/foo` in the registry. A string containing `/` is used verbatim as a `registry_path` (e.g. `"skill-sets/33god/hindsight"`).
- **`{name, source}`** — `source` is `file://…`, `git@…`, or `https://…`. `file://` paths are resolved **relative to the manifest's own directory** (`.agents/`) when relative.
- **`{name, registry_path}`** — resolved against the registry checkout ladder, same as packs.
- Optional `version` (git ref for git sources) and `registry` (per-entry override).

A `registry_path` entry that is absent from every checkout **warns and is skipped**; it does not fail the sync.

## Pack root resolution

1. **`source` set** → `file://` becomes a local path (relative to the manifest dir); a git URL is cloned into `~/.agents/.cache/skills/<name>` and `version` checked out.
2. **Otherwise** → `<registry-checkout>/<registry_path>`, where `registry_path` defaults to `packs/<name>/<version>` when `version` is set, else `packs/<name>`.
   - If `version` is omitted **and** `packs/<name>/pack.toml` is absent **and** `packs/<name>/` is a version layout ([discriminator](./topology.md#the-version-layout-discriminator)), the **highest** version directory is selected. Ordering is numeric-segment aware and a `-next.N` prerelease sorts **below** the same release. *This is the only implicit choice in the whole contract.*
3. **Registry checkout ladder, in order:**

   ```
   $PJ_SKILLS_REGISTRY_ROOT          (when set, used ALONE; absent → hard failure)
   ~/.agents/.cache/registries/<sanitized-url>
   ~/code/skillex
   ```

   `<sanitized-url>` = `re.sub(r"[^a-zA-Z0-9]", "_", url)`, so `https://github.com/delorenj/skillex.git` → `https___github_com_delorenj_skillex_git`. Three surfaces compute this name (`sync-skills.py:registry_cache_dir`, `skillex.paths.sanitize_registry_url`, pjangler `registryCacheDirName`) and must agree byte-for-byte.

   **An audit NEVER clones or fetches.** `sync-skills.py` may clone, but only when **no** checkout exists on the ladder; an existing checkout is never `git pull`ed as a side effect of resolution.

4. **Attestation promotion.** When several checkouts carry the same path, contract order picks the winner *except* that a root whose `pack.toml` positively identifies the entry (matching `name`, and `version` when pinned) outranks an unattested one. The promotion can only tighten — two attested roots are still broken by contract order. This is what stops a lagging cache clone from silently downgrading a sealed pack to structural-only. It is **not** protection against a cache clone that is attested but stale: see [gotchas.md](./gotchas.md#pj-audit-is-green-but-the-pack-i-just-rendered-is-not-the-one-being-used).

5. The pack root must be a **real directory**, and no component of the path from the registry root down to it may be a symlink.

## Inventory inside a pack

- **`pack.toml` present** → inventory = `[freeform].skills`, authoritative. `[pack].name` must equal the entry name; when `version` is pinned, `[pack].version` must match. Duplicates are an error.
- **`pack.toml` absent** → inventory = child directories that (a) do not start with `.` or `_` and (b) contain a **regular** `SKILL.md`. Symlinked children are skipped with a warning, never followed.
- Every name must be one safe path component; every entry must be a real directory with a regular `SKILL.md`.
- `include` then `exclude` are applied to produce the *members*. The **declared** inventory (pre-include/exclude) is what the payload and the seal cover.

## Precedence

Layers, lowest to highest:

```
1. global  packs[]     (array order; a later pack wins a name collision)
2. global  skills[]
3. project packs[]
4. project skills[]
```

**Then the subtle part.** Contract §5 was revised: **§6 redundancy pruning happens FIRST, and only the surviving `skills[]` entries override pack members.**

```
For each manifest layer, in order:
  1. Resolve every packs[] entry; later packs override earlier ones by name.
  2. For each skills[] entry in THIS layer:
       if §6 classifies it REDUNDANT against a pack declared in THIS SAME manifest
           → DROP it. The pack member wins. It is not an override.
       else
           → resolve it; it ALWAYS overrides a pack member of the same name.
```

Why this ordering matters: with the naive "explicit always wins" reading, a repo that declared `bmad@6.10.2` in `packs[]` while still carrying 76 hand-expanded `skills[]` entries pointing at `packs/bmad/6.10.1-next.31/…` would pin **every** member back to the old version. Pruning first means the 73 names the new pack provides follow the new pack, and only the 3 names it dropped stay pinned to the old tree. This was a shipped bug; get it right.

Implemented in `sync-skills.py:PackScope`, re-exported into `provision-packs.py` (`declared_pack_scope`), and mirrored by pjangler's `isRedundantDeclaredPackEntry`. All three must resolve every name to the same path.

## Redundancy (§6)

A `skills[]` entry is REDUNDANT against a declared pack when **either**:

- **(a)** its resolved source path is contained by that pack's **own resolved root**, or
- **(b)** its name is in that pack's **DECLARED inventory** (pre-`include`/`exclude`) **and** its resolved source path is contained by the pack **family** directory `packs/<name>/` — i.e. it points into *any* version of that pack.

Rules that keep this safe:

- Source paths are compared **LEXICALLY** — normalized absolute path, symlinks NOT resolved. Pure path math; it decides precedence, never safety.
- Only `file:` sources can ever be redundant. A `registry_path`, `git@`, or `https://` entry never is.
- Redundancy is **scoped to one manifest**. A project `skills[]` entry is weighed only against packs the *project* manifest declares. Cross-layer precedence still comes from the 1–4 ordering, so a project pack does override a global `skills[]` entry.
- The family root is **not** the pack's extent. `packs/<name>/<other-version>/<skill>` is a different pack; only names the resolved pack actually declares are shadowed there. Flattening the family root into the pack root silently deletes user skills.
- Entries pointing **outside** the pack — a local tree, a different registry, a customized copy — are never removed.

### Worked example (historical snapshot — will NOT reproduce as-is)

> **Two reasons this block does not reproduce today. Read both before running anything.**
>
> 1. **The migration has already been applied.** `/home/delorenj/code/automatic-ai/.agents/skills.json` now carries `packs: [{"name":"bmad","version":"6.10.2"}]` and exactly **3** `skills[]` entries — the survivors. The 76-entry pre-migration state below is a historical snapshot kept because the arithmetic is the point.
> 2. **The `pj` on PATH cannot produce these strings at all.** The detail strings quoted below exist only in the **repo build**; the stale global `pj` contains zero occurrences of `should be symlinks into their declared`. Every `pj audit` in this skill means `node /home/delorenj/code/33GOD/pjangler/dist/index.js audit` — see [gotchas.md](./gotchas.md#the-pj-on-path-is-a-stale-build-pj-audit-lies-and-migrate-flags-are-missing).

The pre-migration `/home/delorenj/code/automatic-ai/.agents/skills.json`:

```json
{
  "packs": [ { "name": "bmad", "version": "6.10.2" } ],
  "skills": [
    { "name": "bmad-advanced-elicitation",
      "source": "file:///home/delorenj/code/skillex/packs/bmad/6.10.1-next.31/bmad-advanced-elicitation" },
    …76 entries total, all pinned at 6.10.1-next.31…
  ]
}
```

Against *that* manifest, the **repo build** reported:

```bash
node /home/delorenj/code/33GOD/pjangler/dist/index.js audit
```

```
↳ .agents/skills.json skills[] duplicates 73 declared pack member(s) and should drop them: …
↳ 78 managed pack skill path(s) should be symlinks into their declared Skillex pack
```

What each binary prints **against the repo as it stands now** (both verified live):

```
node …/pjangler/dist/index.js audit   →  ✔ skills.project-manifest  Skillex skills manifest parity verified
pj audit                              →  ✖ skills.project-manifest  6 Skillex migration issue(s) detected
                                          (stale build; still assumes the hardcoded 6.10.1-next.31 pin
                                           and knows nothing about packs[] — ignore it)
```

The arithmetic:

- `6.10.1-next.31` declares 76 skills; `6.10.2` declares 75.
- 73 of the 76 hand-expanded names are in **6.10.2's** declared inventory and point into `packs/bmad/` → rule (b) → REDUNDANT → dropped.
- The 3 that survive are exactly the members `6.10.2` **dropped**: `bmad-deep-recon`, `bmad-editorial-review`, `bmad-review`. They are not in the new pack's inventory, so they are the user's and stay pinned at `6.10.1-next.31`.
- Expected projection = 75 pack members + 3 survivors = **78**.

And that is exactly what happened — the live manifest today holds `packs: [bmad@6.10.2]` plus those same 3 `skills[]` entries, all still pointing at `packs/bmad/6.10.1-next.31/…`. Confirm it yourself without trusting any binary:

```bash
python3 -c "import json;d=json.load(open('/home/delorenj/code/automatic-ai/.agents/skills.json'));print(d['packs'],len(d['skills']))"
# → [{'name': 'bmad', 'version': '6.10.2'}] 3
```

## Validating

```bash
# Resolve every packs[] entry offline and print the exact root chosen.
cd ~/code/skillex
uv run skillex pack manifest /path/to/repo/.agents/skills.json

# Same, plus full contract verification of each resolved pack.
uv run skillex pack manifest /path/to/repo/.agents/skills.json --verify

# Pin the ladder to one checkout (useful to prove a cache is shadowing).
uv run skillex pack manifest /path/to/repo/.agents/skills.json --verify \
  --registry-root ~/code/skillex
```

`--registry-root` is used **alone** when given — it replaces the ladder rather than prepending to it. The command never clones or fetches. Exit 1 when any non-optional pack fails to resolve or verify.

Real output shape (verified):

```
┃ name        ┃ version ┃ root                                          ┃ status   ┃
│ bmad        │ 6.10.2  │ /home/delorenj/code/skillex/packs/bmad/6.10.2 │ resolved │
│ hermes-base │ 0.18.2  │ /home/delorenj/.agents/.cache/registries/…    │ resolved │
```

Note the two packs resolving from **different checkouts** in one run — that is the ladder plus attestation promotion working, and it is exactly what you must inspect before trusting a GREEN audit.

Schema-level validation: the JSON Schema at `~/code/skillex/skills.schema.json` sets `additionalProperties: false` on the pack object form and encodes the `source`/`registry_path` mutual exclusion as `"not": {"required": ["source","registry_path"]}`.
