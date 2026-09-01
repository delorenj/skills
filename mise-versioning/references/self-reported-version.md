# Self-reported versions: make the artifact tell the truth

The manifest keeps *files* in parity. It cannot help an artifact that answers `--version`
(or an MCP/server info handshake) from a **string literal in source** — that literal is
invisible to the conf, survives every bump, and lies a little more each release.
Real incident: pjangler shipped 1.1.3 while `pj --version` said `1.0.0` — commander's
`.version("1.0.0")` had never been wired to `package.json` (PJAN-2).

**Rule: the version a program reports must be *derived* from a tracked manifest — read at
runtime or injected at build time. Never a second copy.**

Do NOT solve this by adding the source file to `.mise/version-files.conf`: no built-in type
rewrites arbitrary source, and regex-rewriting code is exactly the brittleness the engine's
column-0 anchoring exists to avoid. Derive; don't duplicate.

## Recipes by stack

### Node / TypeScript (ESM, incl. bundled CLIs)

Walk up from the module to `package.json` — works from `src/` in dev and from a bundled
`dist/` in the published install (esbuild & friends leave `import.meta.url` pointing at the
output file):

```ts
// src/utils/version.ts
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const VERSION: string = (() => {
  try {
    let dir = dirname(fileURLToPath(import.meta.url));
    for (let i = 0; i < 4; i++) {
      try {
        return JSON.parse(readFileSync(join(dir, "package.json"), "utf8")).version ?? "0.0.0";
      } catch {
        const parent = dirname(dir);
        if (parent === dir) break;
        dir = parent;
      }
    }
  } catch { /* fall through */ }
  return "0.0.0";
})();
```

Then `program.version(VERSION)` / `new McpServer({ version: VERSION })`. Ship `package.json`
in the npm tarball (it always is). CJS is a one-liner: `require("../package.json").version`.

### Python

```python
from importlib.metadata import version
__version__ = version("your-distribution-name")   # reads installed metadata from pyproject.toml
```

For argparse: `parser.add_argument("--version", action="version", version=__version__)`.

### Rust

```rust
const VERSION: &str = env!("CARGO_PKG_VERSION");   // compile-time, from Cargo.toml — already derived
```

### Go

No manifest to read; inject at build time from the canonical version:

```toml
[tasks.build]
depends = ["version:bump-patch"]
run = 'go build -ldflags "-X main.version=$(mise run version | tr -d v)" ./...'
```

(or `runtime/debug.ReadBuildInfo()` when versions come from module tags.)

### Shell scripts

Read the tracked `plain` file: `VERSION="$(cat "$(dirname "$0")/../VERSION")"`.

## Verify (always, once per repo)

After wiring, prove the derivation end to end:

```bash
mise run version:bump-patch && mise run build   # or however the artifact is produced
<artifact> --version          # MUST equal: mise run version (sans the leading v)
```

If the repo ships an executable, consider pinning this as a task so drift can't regress:

```toml
[tasks."version:verify"]
description = "Artifact self-reports the canonical version"
run = 'test "v$(<artifact> --version)" = "$(mise run version)"'
```
