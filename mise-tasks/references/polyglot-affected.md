# Polyglot Monorepo Affected Detection

Guide for choosing the right tool for affected detection in polyglot monorepos (Python + Rust + TypeScript).

## Why Pants + mise?

**mise** excels at runtime version management and environment configuration, but has **no native affected detection**. You need manual git scripts to detect which packages changed.

**Pants** provides:

- Native affected detection (`--changed-since=origin/main`)
- Auto-inferred dependencies (no manual BUILD file maintenance)
- Native Python support (uv, ruff, pytest integration)
- Excellent mise coexistence

**Combination**: mise handles runtimes, Pants handles builds.

---

## Tool Comparison

### Affected Detection Capabilities

| Tool          | Affected Detection      | How It Works                       |
| ------------- | ----------------------- | ---------------------------------- |
| **Nx**        | Native (graph-aware)    | Analyzes project graph + git diff  |
| **Turborepo** | Native (git-based)      | `--filter=...[origin/main]` syntax |
| **mise**      | None (manual)           | Requires custom git scripts        |
| **Pants**     | Native (git-integrated) | `--changed-since=origin/main`      |
| **Bazel**     | Via bazel-diff          | External tool required             |

### Language Support

| Tool          | Python                  | Rust                  | TypeScript   | Polyglot Friendliness |
| ------------- | ----------------------- | --------------------- | ------------ | --------------------- |
| **Nx**        | Plugin-based            | New plugin            | Native       | Improving             |
| **Turborepo** | Needs wrapper           | Needs wrapper         | Native       | Poor                  |
| **mise**      | Native                  | Native                | Native       | Excellent             |
| **Pants**     | Native (uv/ruff/pytest) | Community plugin      | Native       | Excellent             |
| **Bazel**     | rules_python            | rules_rust (official) | rules_nodejs | Excellent             |

### Scaling & Complexity

| Tool          | Learning Curve | Setup Time | Scalability    | Remote Caching |
| ------------- | -------------- | ---------- | -------------- | -------------- |
| **Nx**        | Medium         | 2-4 hours  | 100+ packages  | Native         |
| **Turborepo** | Low            | 1-2 hours  | 50+ packages   | Native         |
| **mise**      | Low            | 30 min     | 20 packages    | None           |
| **Pants**     | Low            | 2-4 hours  | 200 packages   | REAPI          |
| **Bazel**     | High           | 1-2 weeks  | 1000+ packages | Native         |

---

## Recommendation by Scale

| Scale                                | Tool                     | Rationale                                      |
| ------------------------------------ | ------------------------ | ---------------------------------------------- |
| **< 10 packages**                    | mise + custom git script | Minimal overhead                               |
| **10-50 packages (Python-heavy)**    | **Pants + mise**         | Native Python, auto-inference, native affected |
| **50+ packages (balanced polyglot)** | Bazel                    | Proven scale, remote execution                 |
| **JS-only monorepo**                 | Turborepo or Nx          | Excellent JS tooling                           |

---

## Pants + mise Integration Guide

### Architecture

```
monorepo/
├── mise.toml                    # Runtime versions + env vars (SSoT)
├── pants.toml                   # Pants configuration
├── BUILD                        # Root BUILD file (minimal)
├── packages/
│   ├── core-python/
│   │   ├── mise.toml           # Package-specific env (optional)
│   │   └── BUILD               # Auto-generated: python_sources()
│   ├── core-rust/
│   │   └── BUILD               # cargo-pants plugin
│   └── core-bun/
│       └── BUILD               # pants-js plugin
```

### pants.toml Configuration

```toml
[GLOBAL]
pants_version = "<version>"
backend_packages = [
    "pants.backend.python",
    "pants.backend.python.lint.ruff",
    "pants.backend.experimental.rust",
    "pants.backend.experimental.javascript",
]

[python]
interpreter_constraints = [">=3.11"]

[source]
root_patterns = ["packages/*"]

[python-bootstrap]
# Use mise-managed Python (mise sets PATH)
search_path = ["<PATH>"]
```

### mise.toml Configuration

```toml
# Runtime versions - Pants inherits from PATH
[tools]
python = "<version>"
node = "<version>"
rust = "<version>"

[env]
PANTS_CONCURRENT = "true"

# Convenience wrappers for Pants commands
[tasks."test:affected"]
description = "Test affected packages via Pants"
run = "pants --changed-since=origin/main test"

[tasks."lint:affected"]
description = "Lint affected packages via Pants"
run = "pants --changed-since=origin/main lint"

[tasks.test-all]
description = "Test all packages"
run = "pants test ::"

[tasks."pants:tailor"]
description = "Generate BUILD files"
run = "pants tailor"

[tasks."pants:check"]
description = "Type-check all Python"
run = "pants check ::"
```

### BUILD File Patterns

**Python package** (auto-generated by `pants tailor`):

```python
# packages/core-python/BUILD
python_sources()
python_tests()

# Pants auto-infers dependencies from imports - no manual deps!
```

**Rust package** (cargo-pants plugin):

```python
# packages/core-rust/BUILD
cargo_package()
```

**TypeScript package** (pants-js plugin):

```python
# packages/core-bun/BUILD
javascript_sources()
javascript_tests()
```

---

## Native Affected Commands

```bash
# Test only affected packages
pants --changed-since=origin/main test

# Lint only affected packages
pants --changed-since=origin/main lint

# Build only affected packages
pants --changed-since=origin/main package

# See what's affected (dry run)
pants --changed-since=origin/main list

# Test all packages
pants test ::

# Generate BUILD files
pants tailor
```

---

## Migration Paths

### mise-only → Pants + mise

1. **Keep mise.toml** - continues to manage Python/Rust/Node versions
2. **Add pants.toml** - minimal config (see above)
3. **Generate BUILD files** - `pants tailor` auto-creates them
4. **Replace affected.sh** - use `pants --changed-since=origin/main`
5. **Update CI** - replace `mise run test:affected` with `pants --changed-since test`

### Pants + mise → Bazel

If Rust becomes dominant (50%+ of codebase) or you scale beyond 200 packages:

1. Evaluate Bazel's rules_rust (official, mature)
2. Use Pants v2.23+ workspace environments to invoke Bazel for Rust
3. Consider full Bazel migration only if team can dedicate build infrastructure resources

---

## Fallback: mise-only Affected Detection

For < 10 packages where Pants is overkill:

```toml
# mise.toml - manual git-based affected detection
[tasks."_get-changed-packages"]
description = "Get packages with changes since origin/main"
hide = true
run = '''
git diff --name-only origin/main 2>/dev/null | \
  grep -E '^packages/[^/]+/' | \
  cut -d/ -f2 | \
  sort -u
'''

[tasks."test:affected"]
description = "Test only packages with changes"
run = '''
for pkg in $(mise run _get-changed-packages); do
  echo "Testing: $pkg"
  mise run "test:$pkg" || exit 1
done
'''
```

**Limitation**: This doesn't understand transitive dependencies. If `shared-types` changes, packages depending on it won't be detected unless they also changed.

---

## Why Not Nx/Turborepo for Polyglot?

Both require `package.json` wrapper files in non-JS packages:

```json
// packages/core-python/package.json (REQUIRED by Turborepo)
{
  "name": "core-python",
  "scripts": { "test": "uv run pytest" }
}
```

This adds friction and doesn't leverage language-native tooling. Pants and mise treat all languages as first-class citizens.

---

## Related Resources

- [Level 11: Pants + mise](../SKILL.md#level-11-polyglot-monorepo-with-pants--mise) - Quick reference in main skill
- [Bootstrap Monorepo](./bootstrap-monorepo.md) - Autonomous polyglot monorepo bootstrap meta-prompt
- [Pants Documentation](https://www.pantsbuild.org/)
- [mise Documentation](https://mise.jdx.dev/)
