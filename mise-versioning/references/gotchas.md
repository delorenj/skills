# Gotchas

Read a section only when the matching symptom appears.

## `mise run version` prints `v0.0.0` in a repo that clearly has a version

**Symptom:** the manifest exists but `current` reports `v0.0.0`.
**Cause:** the version-bearing file isn't in `.mise/version-files.conf`, or its version sits in a
spot the type's pattern doesn't match (e.g. indented under a TOML table, a non-`Version` MSBuild
property like `<VersionPrefix>`, a JS file exporting a string).
**Fix:** run `.mise/scripts/versioning.sh files` to see what's tracked. Add the missing file to
the manifest with the right type, or — if no built-in type matches its layout — add a `plain`
`VERSION` file as the canonical source and let the others drift-check against it.
**Why it matters:** `current` and every bump derive from the manifest only; an untracked file is
invisible and will silently fall out of parity.

## `--version` reports an old number though every manifest is in parity

**Symptom:** `mise run version` and all tracked files agree (e.g. 1.1.3), but the built CLI/server
answers `--version` (or its MCP/server-info handshake) with a stale value like `1.0.0`.
**Cause:** the program self-reports from a string literal in source — commander's
`.version("1.0.0")`, an `McpServer({ version: "1.0.0" })`, a `__version__ = "1.0.0"` — which no
manifest entry tracks and no built-in type can rewrite. Bumps move the manifests; the literal
never moves.
**Fix:** derive instead of duplicating — make the artifact read its version from the tracked
manifest at runtime (or inject it at build time). Per-stack recipes and a verify ritual:
[self-reported-version.md](./self-reported-version.md). Do **not** add the source file to the
conf; regex-rewriting code is the brittleness this engine deliberately avoids.
**Why it matters:** users trust `--version` over your manifests. Parity that stops at the file
boundary ships artifacts that lie about themselves (this exact incident: pjangler 1.1.3 reporting
1.0.0).

## A bump rewrote the wrong line in a TOML file

**Symptom:** a dependency pin or a nested `version =` got changed instead of the package version.
**Cause:** the file's real version is indented (so the anchored `^version` skipped it) **and** an
earlier unanchored match existed — or the manifest used `toml` on a file whose first top-level
`version =` isn't the package version.
**Fix:** confirm the package version is a column-0 `version = "X.Y.Z"` line. If the project's
layout is unusual, don't fight the regex — make a `plain VERSION` file canonical and remove the
ambiguous entry from the manifest. See [file-types.md](./file-types.md).

## `version:check` fails right after init

**Symptom:** init reports "synced" but a later `mise run version:check` shows DRIFT.
**Cause:** a versioned file was edited by hand (or by a package manager like `npm version`) after
the sync, reintroducing drift.
**Fix:** `mise run version:sync` to pull everything back to the highest, or `versioning.sh set
X.Y.Z` to force an explicit version everywhere. Prefer the mise tasks over hand-editing so parity
holds.

## Build runs but the version didn't bump

**Symptom:** `mise run build` builds but the version is unchanged.
**Cause:** the build isn't a mise task (it's `npm run build`, a Makefile target, etc.), so init's
`depends` wiring never reached it.
**Fix:** wrap the real build in a mise task that depends on the bump:
```toml
[tasks.build]
depends = ["version:bump-patch"]
run = "pnpm build"   # or: make build / cargo build --release / etc.
```
Then invoke `mise run build` instead of the underlying tool. init only auto-wires an existing
mise `[tasks.build]`; foreign build runners must be wrapped by hand (it tells you so).

## init changed a build task that already had `depends`

**Symptom:** the `[tasks.build]` table now has two `depends` lines or a `# NOTE:` comment.
**Cause:** init won't silently merge into an existing `depends` array — it injects a NOTE so you
decide ordering.
**Fix:** merge by hand into one array, putting the bump first:
`depends = ["version:bump-patch", "compile-assets"]`.

## Re-running init didn't pick up a newly added file

**Symptom:** added a new sub-package; init still tracks the old set.
**Cause:** init keeps an existing manifest by default (it's hand-editable and authoritative).
**Fix:** add the line to `.mise/version-files.conf` yourself, or re-run `init.sh --force` to
re-discover from scratch (this overwrites the manifest, so re-add any manual entries).

## `jq: command not found`

**Cause:** `json` entries require `jq`. **Fix:** install `jq`, or pin it in mise:
`mise use jq@latest`. Without `jq`, JSON files can't be read or written safely.
