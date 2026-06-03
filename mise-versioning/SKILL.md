---
name: mise-versioning
description: Provision any repository with an opinionated, stack-agnostic semantic-versioning workflow built on mise tasks. The `init` command installs `.mise/scripts/versioning.sh` and wires mise tasks `version` (print current vX.Y.Z), `version:bump`/`version:bump-patch` (→vX.Y.Z+1), `version:bump-minor` (→vX.Y+1.0), `version:bump-major` (→vX+1.0.0), plus `version:check` and `version:sync`. Discovers every version-bearing file (package.json, pyproject.toml, Cargo.toml, *.csproj, build.gradle, VERSION, git tags) and keeps them in parity — on conflict the highest semver wins and the rest are bumped to match. Wraps existing build tasks to bump-patch first. Use when the user says "add versioning", "set up version bumping", "init versioning", "version this repo", "mise version tasks", "semver workflow", "keep versions in sync", or "bump the version across all files". Do NOT use for changelogs/release notes (use product-changelog), publishing packages to npm/PyPI/crates, or mise config unrelated to versions.
---

# mise-versioning

Drop a uniform `version` / `version:bump-*` task interface onto any repo, regardless of stack.
All bump logic lives in one installed file (`.mise/scripts/versioning.sh`); mise tasks are thin
wrappers. Every version-bearing file in the repo is kept at the same semver — the highest wins.

## The contract this skill guarantees

After `init`, the repo exposes exactly these mise tasks (and nothing the user must learn beyond them):

| task | effect |
|---|---|
| `version` | print current version as `vX.Y.Z` (the highest across all tracked files) |
| `version:bump` / `version:bump-patch` | `vX.Y.Z` → `vX.Y.(Z+1)` (alias — same task) |
| `version:bump-minor` | `vX.Y.Z` → `vX.(Y+1).0` |
| `version:bump-major` | `vX.Y.Z` → `v(X+1).0.0` |
| `version:check` | exit nonzero + list drift if files disagree |
| `version:sync` | force every file up to the highest version |

Every bump rewrites **all** tracked files in their native format and (if tracked) creates a
`vX.Y.Z` git tag, so a frontend `package.json` and a backend `pyproject.toml` never diverge.

## Running `init`

`init` is the single entry point. It is idempotent — safe to re-run.

```bash
bash scripts/init.sh          # run from inside the target repo (cwd anywhere within it)
# flags: --force (re-discover the manifest)  --seed X.Y.Z (initial version)  --no-git-tag
```

What it does, in order:

1. **Ensure mise.** If `mise.toml` is absent, create a minimal one.
2. **Install the engine.** Copy `assets/versioning.sh` → `.mise/scripts/versioning.sh` (chmod +x).
3. **Discover version files** → write `.mise/version-files.conf` (a `<type> <path>` manifest).
   Skipped if a manifest already exists unless `--force`.
4. **Merge the tasks** into `mise.toml` inside a managed `# >>> mise-versioning >>>` block
   (replaced wholesale on re-run, never duplicated).
5. **Resolve parity.** Run `version:check`; if files disagree, `version:sync` to the highest.
6. **Wrap the build.** If `mise.toml` has a `[tasks.build]`, add `depends = ["version:bump-patch"]`.

After running, **review `.mise/version-files.conf`** — it is hand-editable and authoritative.
Add or remove entries the auto-discovery missed before relying on bumps.

## After init: judgment the script leaves to you

`init` handles the mechanical 90%. Finish these by hand when they apply:

- **Foreign build runners.** init only auto-wires an existing mise `[tasks.build]`. If the repo
  builds via `npm run build`, a Makefile, `cargo build`, etc., wrap it so the version bumps first:
  ```toml
  [tasks.build]
  depends = ["version:bump-patch"]
  run = "pnpm build"
  ```
  Invoke `mise run build` thereafter, not the underlying tool.
- **Build task that already had `depends`.** init injects a `# NOTE:` rather than guessing merge
  order. Combine into one array with the bump first: `depends = ["version:bump-patch", "…"]`.
- **Unusual version locations.** If a file's version isn't matched (indented TOML, a non-standard
  property, a version embedded in source), prefer a canonical `plain` `VERSION` file over fighting
  the matcher. See [references/file-types.md](./references/file-types.md).

## How parity & "highest wins" work

The canonical version is computed fresh on every call as the max semver across all manifest
entries. There is no separate "source of truth" file — any tracked file can carry the version, and
they are reconciled upward. This is what lets `init` adopt a repo whose files already disagree:
`version:sync` pulls the laggards up to the leader. Bumps always start from the canonical value, so
a stray un-bumped file can never silently lower the version.

## Supported file types

`json` · `toml` · `cargo` · `csproj` · `gradle` · `plain` · `gittag`. Read/write rules, the
column-0 anchoring that protects dependency pins, and how to add a new type are in
[references/file-types.md](./references/file-types.md).

## Troubleshooting

When a bump touches the wrong line, `check` flags drift after init, the build doesn't bump, or
`current` reads `v0.0.0` in a versioned repo — see [references/gotchas.md](./references/gotchas.md).

## Out of scope

- **Changelogs / release notes.** This skill moves version numbers; it does not write release
  prose. Use the `product-changelog` skill.
- **Publishing / releasing.** No `npm publish`, `uv publish`, `cargo publish`, GitHub Releases, or
  `git push --tags`. Bumps and tags stay local; wire release steps separately.
- **Deriving versions from commit history** (Conventional Commits, semantic-release, release-please).
  This workflow is explicit-bump, not commit-inferred. If the user wants commit-driven versioning,
  that's a different tool — don't bolt it on here.
- **Non-version mise configuration** (tool pinning, env, unrelated tasks). init touches only its
  managed block and an existing `build` task.
