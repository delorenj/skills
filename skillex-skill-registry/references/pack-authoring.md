# Authoring, Versioning and Sealing Packs

How to cut a pack, what `pack.toml` means, what a seal covers, and how to run an upgrade end to end.

## Reading Order

| Task | Read |
|---|---|
| Create a brand-new pack | [Authoring a new pack](#authoring-a-new-pack) |
| Understand every key in `pack.toml` | [`pack.toml` anatomy](#packtoml-anatomy) |
| Decide flat vs versioned | [Flat vs versioned](#flat-vs-versioned) |
| Understand what sealing guarantees | [Sealing](#sealing) and [Payload](#payload) |
| Bump a pack to a new upstream version | [Worked example](#worked-example-upgrading-the-bmad-pack) |
| Read the exact `render` / `verify` flags | [Command reference](#command-reference) |

## `pack.toml` anatomy

Verbatim head and tail of `packs/bmad/6.10.2/pack.toml`, the reference implementation:

```toml
[pack]
name = "bmad"
version = "6.10.2"
description = "Immutable BMAD agent-skill payload, shared through symlink projections."

[source]
upstream = "bmad-method"
upstream_version = "6.10.2"
rendered_from = ".agent/skills"
payload_files = 1055

[freeform]
skills = [
  "bmad-advanced-elicitation",
  "bmad-agent-analyst",
  …
]

[policy]
immutable = true
sealed = true
project_projection = "symlink"
```

| Table / key | Role |
|---|---|
| `[pack].name` | Must equal the manifest entry's `name` and the `packs/<name>/` directory. Mismatch is a hard error. |
| `[pack].version` | Must equal the pinned `version` when the manifest pins one, and the `<version>/` directory. |
| `[pack].description` | Free text; shown by `skillex pack list`. |
| `[source].upstream`, `.upstream_version`, `.rendered_from` | Provenance. Free-form; not enforced. |
| `[source].payload_files` | Integer tripwire. **Verified for every pack, sealed or not** — a mismatch against the actual payload count (excluding `pack.toml`) is a hard error. Cheap detection of a truncated checkout. |
| `[freeform].skills` | The AUTHORITATIVE inventory when `pack.toml` exists. An absent section means an **empty** inventory, never "glob". Duplicates are an error. |
| `[policy].sealed` | `true` → consumers must verify `SHA256SUMS`. |
| `[policy].immutable` | `true` → `skillex pack render` refuses to re-render without `--force`. **Does NOT imply sealed.** |
| `[policy].project_projection` | Recorded by the renderer (`"symlink"` by default). Informational. |

Other `[policy]` keys occur in the wild and are simply ignored by the contract surfaces — `packs/hermes-base/0.18.2` carries `overlay_wins = true` and `base_readonly = true`.

## Flat vs versioned

```
packs/<name>/pack.toml            FLAT      one root, no version dir
packs/<name>/<version>/pack.toml  VERSIONED many roots, one per release
```

Use **versioned** whenever the pack tracks an upstream release, needs to be pinned, or will ever need two live versions side by side (which the redundancy rules explicitly support). Use **flat** only for a small, hand-maintained, unpinned bundle.

`packs/<name>/` with **no** `pack.toml` is also legal: the inventory is globbed from child directories holding a regular `SKILL.md`. See the [version-layout discriminator](./topology.md#the-version-layout-discriminator) for how the resolver tells a version layout from a flat pack.

## Payload

```
payload = pack.toml
        + every file recursively under each DECLARED skill directory
          (the FULL declared inventory, pre-include/exclude)
```

Narrowing what you *install* with `include`/`exclude` must never narrow what you *verify*.

Payload rules enforced while walking:

- **No symlinks anywhere** in the payload — a symlink is a hard error, not a skip.
- Only regular files and real directories. Sockets, fifos, devices → error.
- Files are opened `O_NOFOLLOW` and confirmed `S_ISREG` on the **file descriptor** before being read or hashed, so the check cannot be raced.
- Every declared skill directory must exist and contain a regular `SKILL.md`.
- Skill names are exactly one safe path component.

Files that are **neither payload nor listed** in `SHA256SUMS` are **IGNORED**: `.claude/`, `_bmad/`, `mise.toml`, `.project.json`, a stray `hermes-base-guard.py` at the pack root. They are not pack content.

## Sealing

A pack is **sealed** when `pack.toml` declares `[policy] sealed = true` **OR** the manifest entry sets `"sealed": true`.

> **The manifest may only TIGHTEN.** `sealed: true` forces verification even when `pack.toml` omits it. `sealed: false` in the manifest **cannot** disable a pack whose `pack.toml` declares `[policy] sealed = true`.

`immutable = true` alone does **not** imply sealed. Immutability is an *authoring* policy (the renderer refuses to overwrite); sealing is a *consumer-side* integrity check.

### Verification rules — all must hold

1. `SHA256SUMS` exists at the pack root and is a regular file.
2. Every payload file appears in `SHA256SUMS` with a matching sha256.
3. Every `SHA256SUMS` entry exists on disk with a matching sha256. `SHA256SUMS` may legitimately cover **extra non-payload files** (`README.md` is the live case in `packs/bmad/6.10.1-next.31`); those are still verified — they simply may not be **absent**.
4. No symlinks anywhere within the payload.
5. Paths in `SHA256SUMS` are relative, `/`-separated, no `.`/`..`/empty segments, no backslashes, not absolute. Duplicates are an error.
6. Everything else at the pack root is ignored.

Plus: a payload directory containing **no** payload file at any depth is *unauthenticated* — no checksum covers it, so it could be planted undetected. A sealed pack may not contain one.

Format: `<64-hex><two spaces><relative/path>`, sorted by path, trailing newline.

**Unsealed packs get STRUCTURAL validation only**: real pack root, `pack.toml` parses (if present), every declared skill dir exists with a regular `SKILL.md`, no symlinks in the payload, no path escapes, and the `payload_files` tripwire.

A **sealed** pack that is missing a declared skill, a `SKILL.md`, or a checksummed file has failed *integrity verification* — it is not "an uninstalled pack", so `optional: true` cannot suppress it.

## Authoring a new pack

```bash
cd ~/code/skillex

# 1. Assemble the tree. REAL directories only — symlinks are never pack content.
mkdir -p packs/my-pack/1.0.0
cp -r --dereference /source/skill-a packs/my-pack/1.0.0/skill-a
cp -r --dereference /source/skill-b packs/my-pack/1.0.0/skill-b

# 2. Plan only — enumerate skills and payload, write nothing.
uv run skillex pack render packs/my-pack/1.0.0 --name my-pack --version 1.0.0 --check

# 3. Write pack.toml + SHA256SUMS (sealed AND immutable by default).
uv run skillex pack render packs/my-pack/1.0.0 --name my-pack --version 1.0.0 \
  --description "What this pack is." \
  --upstream some-upstream --upstream-version 1.0.0 \
  --rendered-from ".agent/skills"

# 4. Verify against the contract.
uv run skillex pack verify packs/my-pack/1.0.0

# 5. COMMIT pack.toml AND SHA256SUMS. An uncommitted seal is invisible to every
#    other checkout — see gotchas.md.
git add packs/my-pack/1.0.0 && git commit -m "feat(packs): my-pack 1.0.0"
```

Then declare it:

```json
{ "packs": [ { "name": "my-pack", "version": "1.0.0" } ] }
```

`render` writes nothing unless the whole payload enumerates and hashes cleanly first, and refuses to overwrite a pack marked `[policy] immutable = true` without `--force`. It also refuses to write through a symlink or over a non-regular file.

`pack.toml` output is **deterministic**: same inputs → same bytes.

## Worked example: upgrading the bmad pack

`6.10.1-next.31` → `6.10.2`. All numbers below are verified against the registry.

### 1. What changed

|  | `6.10.1-next.31` | `6.10.2` |
|---|---|---|
| Declared skills | 76 | **75** |
| `[source].payload_files` | 1072 | **1055** |
| `[policy]` | `immutable`, `project_projection` | `immutable`, **`sealed = true`**, `project_projection` |
| `skillex pack verify` | VERIFIED, reported *unsealed* | VERIFIED, reported *sealed* |

**Dropped:** `bmad-deep-recon`, `bmad-editorial-review`, `bmad-review`
**Added:** `bmad-index-docs`, `bmad-shard-doc`

```bash
cd ~/code/skillex
python3 - <<'PY'
import tomllib
a = tomllib.load(open('packs/bmad/6.10.1-next.31/pack.toml','rb'))['freeform']['skills']
b = tomllib.load(open('packs/bmad/6.10.2/pack.toml','rb'))['freeform']['skills']
print('dropped:', sorted(set(a)-set(b)))
print('added:  ', sorted(set(b)-set(a)))
PY
```

### 2. Cut the new version

```bash
cd ~/code/skillex
mkdir -p packs/bmad/6.10.2
# populate from the upstream install (real dirs, no symlinks)
uv run skillex pack render packs/bmad/6.10.2 --name bmad --version 6.10.2 --check
uv run skillex pack render packs/bmad/6.10.2 --name bmad --version 6.10.2 \
  --description "Immutable BMAD agent-skill payload, shared through symlink projections." \
  --upstream bmad-method --upstream-version 6.10.2 --rendered-from ".agent/skills"
uv run skillex pack verify packs/bmad/6.10.2      # → "bmad@6.10.2 (sealed, 75 skills, pack.toml)  VERIFIED"
git add packs/bmad/6.10.2 && git commit -m "feat(packs): bmad 6.10.2"
```

**Do not delete the old version.** `6.10.1-next.31` is still the implicit pin used by `provision-packs.py` for repos that declare no `bmad` pack, and its tree is the resolution target for any surviving `skills[]` entry.

### 3. Point a project at it

```json
{
  "$schema": "https://raw.githubusercontent.com/delorenj/skillex/main/skills.schema.json",
  "inherit_global": true,
  "registry": "https://github.com/delorenj/skillex.git",
  "packs": [ { "name": "bmad", "version": "6.10.2" } ],
  "skills": [ … existing hand-expanded entries, leave them for now … ]
}
```

### 4. Let §6 pruning do the cleanup

> **Use the repo build, not the `pj` on PATH.** The installed `pj` is a stale publish: it has no `--accept-registry-matches`, none of the pack-era audit detail strings, and it still assumes the hardcoded BMAD `6.10.1-next.31` pin — so it reports migration issues that the current contract does not have. Set an alias for this whole section. Full detail: [gotchas.md](./gotchas.md#the-pj-on-path-is-a-stale-build-pj-audit-lies-and-migrate-flags-are-missing).

```bash
cd <repo>
alias pjr='node /home/delorenj/code/33GOD/pjangler/dist/index.js'

pjr audit                                   # reports the redundant entries by name
pjr migrate skills.project-manifest --dry-run
pjr migrate skills.project-manifest
```

73 of the 76 hand-expanded entries are dropped; the 3 names `6.10.2` no longer provides survive, still pinned at `6.10.1-next.31`. Expected projection: 75 + 3 = **78**. Full arithmetic in [manifest.md](./manifest.md#worked-example-historical-snapshot--will-not-reproduce-as-is).

### 5. Re-project and fan out

```bash
mise run skills-sync        # runs skills-provision-packs first, then sync-skills.py
pjr audit                   # skills.project-manifest → "Skillex skills manifest parity verified"
```

`pj audit` (the stale global) will **still** show `skills.project-manifest` failing here with six pre-pack-era issues even though the migration succeeded. That is the binary, not your repo — confirm with `pjr audit`.

### 6. Decide what to do about the 3 survivors

They are still real skills pointing into the old pack tree. Options:

- **Keep them.** They are the user's entries; nothing removes them.
- **Retire them.** Delete them from `skills[]` by hand; nothing else references them.
- **Re-home them.** Move the trees into `all-skills/` and rewrite each entry to a bare name or a `registry_path`. Once the source no longer points into `packs/bmad/`, rule (b) can never make them redundant again.

## Command reference

`skillex pack render --help` and `skillex pack verify --help` **crash** with a rich `MarkupError` (their help strings contain `[/<version>]`). The flags below were read from the source and exercised directly.

### `skillex pack render <root>`

| Flag | Default | Meaning |
|---|---|---|
| `--name <name>` | required | Must match the directory |
| `--version <ver>` | required | Must match the version dir |
| `--description <text>` | `""` | `[pack].description` |
| `--upstream <pkg>` | none | `[source].upstream` |
| `--upstream-version <v>` | `--version` | `[source].upstream_version` |
| `--rendered-from <path>` | none | `[source].rendered_from` |
| `--project-projection <s>` | `symlink` | `[policy].project_projection` |
| `--sealed` / `--no-sealed` | `--sealed` | `[policy].sealed` |
| `--immutable` / `--no-immutable` | `--immutable` | `[policy].immutable` |
| `--check` | off | Plan only; write nothing |
| `--force` | off | Re-render a pack marked immutable |

### `skillex pack verify <root>`

| Flag | Meaning |
|---|---|
| `--sealed` | Force checksum verification even if `pack.toml` omits `[policy] sealed` |

Exit 0 on clean or warnings-only; exit 1 when any ERROR-severity issue is found.

### Other subcommands

Executed and confirmed:

```bash
uv run skillex pack list                       # every pack root, version, description
uv run skillex pack show <name>                # slots + freeform skills (uses skills_root index)
uv run skillex pack lint <name>                # semantic lint against the skills index
uv run skillex pack manifest <skills.json>     # resolve packs[] offline; --verify, --registry-root
```

Present in the CLI but **not exercised here** (they mutate state — read `commands/pack.py` before relying on them): `pack create <name>`, `pack activate <name> --scope global|project [--dry-run]`, `pack deactivate --scope global|project`.

> **`show` / `lint` / `activate` use a DIFFERENT model.** They resolve members against `skills_root` (`all-skills/`) from `~/.config/skillex/skillex.toml`, not against the pack's own root. `skillex pack show folder-curator` happily prints `folder-curator` as a resolved member — because that skill exists in `all-skills/` — while `skillex pack verify packs/folder-curator` exits 1 with `SKILL_DIR_MISSING`, because the pack root has no such directory. **For contract work always use `verify` / `manifest`, never `show` / `lint`.**

### Lint rule codes emitted by `verify` / `manifest --verify`

`PACK_ROOT_INVALID`, `PACK_NAME_MISMATCH`, `PACK_VERSION_MISMATCH`, `PACK_NAME_NONCANONICAL` (warn), `PACK_EMPTY` (warn), `SKILL_NAME_UNSAFE`, `SKILL_DIR_MISSING`, `SKILL_MD_MISSING`, `SKILL_DUPLICATE_DECLARATION`, `SKILL_DIR_SYMLINK_SKIPPED` (warn), `PAYLOAD_INVALID`, `PAYLOAD_COUNT_MISMATCH`, `PAYLOAD_UNAUTHENTICATED_DIR`, `SUMS_MISSING`, `SUMS_MALFORMED`, `SUMS_UNCOVERED_FILE`, `SUMS_ORPHAN_ENTRY`, `SUMS_DIGEST_MISMATCH`.
