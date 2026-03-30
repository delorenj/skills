**Skill**: [mise-tasks](../SKILL.md) | **Related**: [semantic-release](../../semantic-release/SKILL.md) | [pypi-doppler](../../pypi-doppler/SKILL.md)

# Release Workflow Patterns for mise Tasks

Patterns and anti-patterns for orchestrating multi-phase release workflows with mise `[tasks]`. Based on real-world failures in Rust+Python (maturin) projects.

---

## The Core Problem: Unlinked Pipeline Stages

Release workflows have natural phases that must execute in order. When phases are defined as independent mise tasks without `depends`, nothing prevents running them out of order:

```toml
# ❌ BROKEN: publish has no dependency on build
[tasks."release:build-all"]
depends = ["release:version"]
run = "maturin build --release"

[tasks."release:pypi"]
# No depends! Can run before build-all completes
run = "./scripts/publish-to-pypi.sh"
```

**Failure mode**: Running `mise run release:pypi` before `mise run release:build-all` fails with "no wheels found". The publish script has a runtime check, but the task system doesn't enforce ordering — the failure happens late instead of being prevented by the DAG.

---

## Pattern 1: Full DAG with `depends`

**Use when**: You want a single command (`mise run release:full`) that does everything.

```toml
# Phase 1: Preflight
[tasks."release:preflight"]
description = "Validate prerequisites"
run = """
git update-index --refresh -q || true
[ -z "$(git status --porcelain)" ] || { echo "FAIL: dirty"; exit 1; }
[ "$(git branch --show-current)" = "main" ] || { echo "FAIL: not main"; exit 1; }
"""

# Phase 2: Sync
[tasks."release:sync"]
description = "Synchronize with remote"
depends = ["release:preflight"]
run = """
git pull --rebase origin main
git push origin main
"""

# Phase 3a: Version bump
[tasks."release:version"]
description = "Bump version via semantic-release"
depends = ["release:sync"]
run = "./scripts/semantic-release.sh"

# Phase 3b: Build (after version bump sets new version)
[tasks."release:build-all"]
description = "Build all platform artifacts"
depends = ["release:version"]
run = """
mise run release:macos-arm64
mise run release:linux
mise run release:sdist
# Consolidate artifacts to dist/
VERSION=$(grep '^version' Cargo.toml | head -1 | sed 's/.*= "\\(.*\\)"/\\1/')
cp -n target/wheels/*-${VERSION}-*.whl dist/ 2>/dev/null || true
cp -n target/wheels/*-${VERSION}.tar.gz dist/ 2>/dev/null || true
"""

# Phase 4: Smoke test (runs after build)
[tasks.smoke]
description = "Verify built artifacts"
depends = ["smoke:import", "smoke:process"]

# Phase 5: Postflight verification
[tasks."release:postflight"]
description = "Verify release state"
depends = ["smoke", "release:build-all"]
run = """
echo "Found $(find dist/ -name '*.whl' | wc -l | tr -d ' ') wheel(s)"
"""

# Phase 6: Publish (depends on build — CRITICAL)
[tasks."release:pypi"]
description = "Publish to PyPI"
depends = ["release:build-all"]
run = "./scripts/publish-to-pypi.sh"

# Orchestrator: single command for everything
[tasks."release:full"]
description = "Full release: version → build → smoke → publish"
depends = ["release:postflight", "release:pypi"]
run = "echo 'Release complete and published!'"
```

**Dependency DAG**:

```
preflight → sync → version → build-all → postflight ─┐
                                  ↓                    ↓
                            release:pypi ────→ release:full
```

**Key properties**:

- `mise run release:full` runs everything in correct order
- `mise run release:pypi` alone still works — it triggers build-all first
- `mise run release:build-all` alone still works — it triggers version first
- Every standalone invocation is safe because `depends` enforces prerequisites

---

## Pattern 2: Selective Re-Run with Shared Guards

**Use when**: You need to re-run individual phases (e.g., rebuild after fixing a compile error) without re-running the entire chain.

```toml
# Guard: check that version was bumped (artifact exists)
[tasks._guard-version-bumped]
hide = true
run = """
TAG=$(git describe --tags --exact-match HEAD 2>/dev/null || true)
[ -n "$TAG" ] || { echo "FAIL: HEAD is not tagged. Run release:version first."; exit 1; }
"""

# Guard: check that wheels exist
[tasks._guard-wheels-exist]
hide = true
run = """
VERSION=$(grep '^version' Cargo.toml | head -1 | sed 's/.*= "\\(.*\\)"/\\1/')
COUNT=$(find dist/ -name "*-${VERSION}-*.whl" 2>/dev/null | wc -l | tr -d ' ')
[ "$COUNT" -gt 0 ] || { echo "FAIL: No wheels for v${VERSION}. Run release:build-all first."; exit 1; }
"""

# Publish with guard (not depends on build)
[tasks."release:pypi"]
description = "Publish to PyPI (requires pre-built wheels)"
depends = ["_guard-wheels-exist"]
run = "./scripts/publish-to-pypi.sh"
```

**When to use this instead of Pattern 1**: When cross-platform builds are slow (e.g., remote Docker builds) and you want to re-run publish without rebuilding on every invocation.

---

## Anti-Patterns

### 1. Publish Without Build Dependency

```toml
# ❌ No depends — can run in any order
[tasks."release:build-all"]
run = "maturin build"

[tasks."release:pypi"]
run = "./scripts/publish-to-pypi.sh"
```

**Fix**: Add `depends = ["release:build-all"]` to `release:pypi`.

### 2. Missing sdist in Build Chain

```toml
# ❌ Only builds wheels, forgets source distribution
[tasks."release:build-all"]
run = """
mise run release:macos-arm64
mise run release:linux
"""
```

**Fix**: Add `mise run release:sdist` and copy all artifacts to `dist/`.

PyPI requires either a wheel per platform or an sdist for source-only installs. Missing sdist means users on unsupported platforms can't `pip install`.

### 3. Artifact Scatter

```toml
# ❌ Wheels land in different directories
[tasks."release:macos-arm64"]
run = "maturin build"  # → target/wheels/

[tasks."release:linux"]
run = "ssh remote 'maturin build' && scp remote:wheels/*.whl dist/"  # → dist/

[tasks."release:pypi"]
run = "uv publish"  # Looks in dist/ only
```

**Fix**: `release:build-all` should consolidate all artifacts into `dist/` after building. The publish step should only need to look in one place.

### 4. Orchestrator as Pass-Through

```toml
# ❌ release:full just prints a message, doesn't enforce anything
[tasks."release:full"]
depends = ["release:postflight"]
run = "echo 'Done! Now run: mise run release:pypi'"
```

**Fix**: Include `release:pypi` in the `depends` array so `release:full` is truly complete:

```toml
[tasks."release:full"]
depends = ["release:postflight", "release:pypi"]
run = "echo 'Released and published!'"
```

---

## Pattern 3: Native Workspace Publishing (Rust 1.90+)

**Use when**: Publishing multiple crates from a Cargo workspace to crates.io. **Requires Rust 1.90+** (stable Sept 2025).

**Use `cargo publish --workspace`** — a single native command that:

- Auto-discovers all publishable crates (skips `publish = false`)
- Topologically sorts by dependency order
- Pre-validates the entire workspace builds correctly before publishing any crate
- Handles crates.io index propagation between dependent publishes

```toml
[tasks."release:crates"]
description = "Publish to crates.io (native workspace publish)"
run = """
# Native workspace publish (Rust 1.90+) — one command, zero maintenance
cargo publish --workspace
"""
```

**Preflight dry-run**:

```toml
[tasks."release:crates-dry"]
description = "Dry-run crates.io workspace publish"
run = "cargo publish --workspace --dry-run"
```

**Why this supersedes all other approaches**:

| Approach                            | Problem                                                        |
| ----------------------------------- | -------------------------------------------------------------- |
| `for crate_dir in crates/*/`        | Filesystem alphabetical order ≠ dependency order               |
| Hardcoded list in task file         | Drifts when new crates are added — caused rangebar-py #113     |
| Manual `[workspace.metadata]` list  | Still requires human to update — redundant with cargo metadata |
| `cargo metadata` + Python topo sort | Works but bespoke — superseded by native Cargo in 1.90         |
| **`cargo publish --workspace`**     | **Zero maintenance, native, pre-validates, handles ordering**  |

**Setup**: Mark internal/non-publishable crates with `publish = false` in their `Cargo.toml`. Everything else publishes automatically. The `CARGO_REGISTRY_TOKEN` env var provides authentication.

### Legacy Fallback (Rust < 1.90)

For projects pinned below Rust 1.90, use `cargo metadata` with Kahn's topological sort as a fallback. See the [Rust 1.90 release notes](https://www.infoworld.com/article/4060262/rust-1-90-brings-workspace-publishing-support-to-cargo.html) for migration guidance.

---

## Checklist: Release Task Audit

When reviewing a release workflow in `.mise.toml`:

- [ ] Every phase task has `depends` on its prerequisites
- [ ] `release:pypi` (or equivalent publish) depends on build
- [ ] `release:build-all` includes sdist, not just wheels
- [ ] All build artifacts are consolidated to a single directory (`dist/`)
- [ ] `release:full` includes all phases including publish in its dependency chain
- [ ] Standalone invocation of any task is safe (prerequisites enforced by DAG)
- [ ] Version bump happens before build (so artifacts have correct version)
- [ ] Cross-compilation tools have their helper binaries declared (e.g., `cargo-zigbuild` for `maturin --zig`)
- [ ] **Crates.io publish uses `cargo publish --workspace` (Rust 1.90+), not hardcoded lists**
- [ ] **Preflight includes `cargo publish --workspace --dry-run`**

---

## Real-World Example: rangebar-py

The rangebar-py project (Rust+Python via maturin) hit the "publish without build" anti-pattern in production:

1. `mise run release:pypi` was called before wheels were built
2. The publish script detected "no wheels found" and failed
3. Wheels were built manually, then publish was re-run successfully
4. Both success and failure notifications arrived, causing confusion

**Root cause**: `release:pypi` had no `depends` — it was designed as a "manual step after `release:full`" but nothing enforced that ordering.

**Fix**: Added `depends = ["release:build-all"]` to `release:pypi` and included `release:pypi` in `release:full`'s dependency chain.

**Lesson**: If two tasks must always run in a specific order, use `depends`. "Manual step after X" is not enforcement — it's documentation that gets ignored under time pressure.

---

### 5. Filesystem-Order Crate Publishing

```bash
# ❌ Alphabetical order has no relation to dependency order
for crate_dir in crates/*/; do
    cargo publish -p "$(basename "$crate_dir")"
done

# ❌ Hardcoded list drifts when new crates are added
for crate in rangebar-core rangebar-providers; do
    cargo publish -p "$crate"
done
```

**Fix**: Use `cargo publish --workspace` (Rust 1.90+). It auto-discovers publishable crates, topologically sorts by dependency order, and pre-validates the entire workspace before publishing. See Pattern 3 above.

**Real-world failure (rangebar-py #113)**: `rangebar-hurst` was added as a workspace dependency of `rangebar-core` but not added to the hardcoded publish list. `cargo publish` for `rangebar-core` failed with "no matching package named rangebar-hurst found" — the crate existed locally but wasn't on crates.io. Three releases went unpublished before discovery. Native `cargo publish --workspace` would have caught this at pre-validation.

---

## Anti-Pattern 5: Implicit Tool Dependencies

### The Problem

Some tools require other tools to be installed but don't fail fast when they're missing. Instead, they produce incorrect results or cryptic errors late in the build.

**Real-world example**: maturin's `--zig` flag for cross-compilation.

```toml
# ❌ zig is installed, but cargo-zigbuild is missing
[tools]
zig = "<version>"
"cargo:maturin" = "latest"

[tasks."release:linux"]
run = """
maturin build --release \
    --target x86_64-unknown-linux-gnu \
    --zig \
    --compatibility manylinux_2_17
"""
```

**What happens**: The build appears to succeed, produces a wheel file, but the wheel fails manylinux_2_17 compliance check:

```
💥 maturin failed
  Caused by: Error ensuring manylinux_2_17 compliance
  Caused by: Your library is not manylinux_2_17 compliant because of
             too-recent versioned symbols: GLIBC_2.18, GLIBC_2.25, GLIBC_2.33
```

**Why it fails late**: maturin's `--zig` flag internally uses `cargo-zigbuild` to properly target glibc 2.17. Without `cargo-zigbuild`, maturin still uses zig as a linker but doesn't set the glibc version target, producing binaries linked against the host's glibc.

### The Fix

Declare all implicit dependencies explicitly in `[tools]`:

```toml
# ✅ All tools that work together are declared together
[tools]
zig = "<version>"
"cargo:maturin" = "latest"
"cargo:cargo-zigbuild" = "latest"  # Required for maturin --zig
```

### Common Implicit Dependencies

| Primary Tool         | Implicit Dependency    | Symptom if Missing                       |
| -------------------- | ---------------------- | ---------------------------------------- |
| `maturin --zig`      | `cargo-zigbuild`       | manylinux compliance failure             |
| `cargo build` (PyO3) | `python` in path       | "Python not found" during link           |
| `semantic-release`   | `bun` or `npm`         | "Cannot find module" errors              |
| `uv run --with`      | Network access         | Silent fallback to cached stale versions |
| `gh pr create`       | `GH_TOKEN` environment | 401 or prompt for login                  |

### The Lesson

**Tools that accept flags for integration features often have undeclared dependencies on other tools.** When a flag like `--zig` implies "use zig for cross-compilation," read the documentation to discover what else must be installed.

Practical rule: **If a tool flag name-checks another tool, check if that tool (or a helper for it) needs to be in `[tools]`.**

---

## Checklist Addition: Tool Dependencies

Add to the release task audit:

- [ ] Cross-compilation tools have their helper binaries declared (e.g., `cargo-zigbuild` for `maturin --zig`)
- [ ] Build tools that interact with language runtimes have those runtimes in `[tools]` (e.g., Python for PyO3)
- [ ] Tasks using external services have their CLI tools and credentials configured
