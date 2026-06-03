# Version file types

`versioning.sh` reads and writes a fixed set of file types, declared one per line in
`.mise/version-files.conf` as `<type> <path>`. The canonical version is the **highest**
semver across every entry; writes push that version into all entries.

| type | matches | read | write | stored as |
|---|---|---|---|---|
| `json` | `package.json`, any JSON with top-level `version` | `jq .version` | `jq` (2-space indent) | `X.Y.Z` |
| `toml` | `pyproject.toml`, generic TOML | first `^version = "…"` | `sed` first match | `X.Y.Z` |
| `cargo` | `Cargo.toml` | `^version = "…"` (top-level only) | `sed` first match | `X.Y.Z` |
| `csproj` | `*.csproj` | first `<Version>…</Version>` | `sed` first match | `X.Y.Z` |
| `gradle` | `build.gradle(.kts)` | first `version = "…"` / `version '…'` | `sed` first match | `X.Y.Z` |
| `plain` | `VERSION`, `version.txt` | first line | overwrite whole file | `X.Y.Z` |
| `gittag` | the repo itself (path `.`) | highest `v*` tag | `git tag -a vX.Y.Z` | `vX.Y.Z` |

## Why anchored patterns matter

`toml`/`cargo` match `^version` anchored at column 0. This deliberately skips indented or
inline `version = "…"` keys — e.g. a Cargo dependency `serde = { version = "1.0" }` or a
`[tool.uv]` pinned dep — so only the package's own version is rewritten. If a project keeps
its real version indented under a table in a non-standard way, the regex will miss it; add a
`plain` sidecar file instead, or extend the type table in `versioning.sh`.

## Adding a new type

All logic is in `.mise/scripts/versioning.sh`. To support another format, add a branch to both
`read_version()` and `write_version()` keyed on the new type string, then reference it in the
manifest. Keep reads tolerant (missing file → print nothing, exit 0) and writes a no-op when the
file is absent, so `check`/`sync` never crash on a partially-present monorepo.

## gittag semantics

`gittag` writes create an **annotated** tag `vX.Y.Z` and skip silently if that tag already
exists (so re-running a sync is safe). Tags are local until pushed — bumping does not
`git push --tags`. If a release flow needs the tag remote, push it explicitly after the bump,
or wrap the bump task with a follow-on push step.
