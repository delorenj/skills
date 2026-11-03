# Project-scoped hooks

The hook bundle is an optional index-maintenance adapter. It is not the skill itself, not the CodeGraph Voyage sidecar, and not the companion MCP server:

- **Skill:** instructions and reusable scripts installed under `$HOME/.agents/skills/codegraph-voyage/`.
- **Hooks:** client lifecycle adapters that mark one project dirty and refresh once at session end.
- **Sidecar:** `tools/codegraph_voyage/` in the target project; performs status/index operations.
- **MCP server:** an interactive tool surface for explicit index/search/status/explore calls.

The hooks own only CodeGraph indexing behavior. They do not publish lifecycle events and must not be folded into Bloodbank or another global event publisher.

## Normalized lifecycle

`hooks/hooks.master.json` is the only hand-edited behavior manifest. `scripts/hooks-fanout.py render` projects it into deterministic JSON under `hooks/generated/`.

| Normalized role | Claude | Codex | Hermes | Behavior |
|---|---|---|---|---|
| `session_start` | `SessionStart` | `SessionStart` | `on_session_start` | Bounded local status probe only; no indexing and no provider call |
| `post_tool` | `PostToolUse` | `PostToolUse` | `post_tool_call` | Inspect bounded stdin and mark dirty only for likely mutations |
| `session_end` | `Stop` | `Stop` | `on_session_end` | If dirty and a real provider is opted in, run one bounded index under a nonblocking advisory lock |

Claude and Codex receive a mutating-tool matcher on `PostToolUse`. Hermes receives hook config plus owner-marked shell-hook allowlist metadata. Runtime payload parsing still tolerates common snake/camel-case field and tool-name dialects.

Every command has the owner marker `CODEGRAPH_VOYAGE_HOOK_OWNER=codegraph-voyage.hooks.v1` and invokes:

```text
$HOME/.agents/skills/codegraph-voyage/scripts/hook-runtime.py <normalized-role>
```

## Provider and remote-source policy

The default is `off`: the hooks track dirty state but never index. Allowed providers are `voyage`, `openrouter` and `automaticai`. `fake` is not an accepted hook provider (its vectors are hashes, not embeddings, and used to pollute real indexes); it and any unrecognized value are treated as `off` and noted in the hook log (an unrecognized value is never echoed). Source-derived text is never sent remotely without an explicit project/runtime choice.

To opt in, pick the provider whose model matches the project's existing sidecar (`codegraph-voyage status`) and use one of:

```bash
export CODEGRAPH_VOYAGE_HOOK_PROVIDER=automaticai   # or voyage | openrouter
export AUTOMATICAI_API_KEY="$(op read 'op://DeLoSecrets/NewAPI Virtual Keys/codegraph-voyage')"
```

or add this to the project's **gitignored** `.agents/local.json`:

```json
{
  "codegraph_voyage": {
    "hook_provider": "automaticai"
  }
}
```

The client process must inherit the provider's API key ambiently (`VOYAGE_API_KEY`, `OPENROUTER_API_KEY` or `AUTOMATICAI_API_KEY`). A key is never accepted by the master manifest, local JSON schema, hook command arguments, tool payloads, or diagnostic log. `CODEGRAPH_VOYAGE_HOOK_PROVIDER=off` disables session-end refresh without deleting pending dirty state.

## Render, inspect, install

Run from this skill directory:

```bash
python3 scripts/hooks-fanout.py render
python3 scripts/hooks-fanout.py check
python3 scripts/hooks-fanout.py check --project-root /absolute/project
python3 scripts/hooks-fanout.py install --project-root /absolute/project
python3 scripts/hooks-fanout.py uninstall --project-root /absolute/project
```

`check` is read-only. Install/uninstall merge by owner marker, preserve unrelated settings and sibling hooks, deduplicate owned hooks, use atomic replacement, and create `.bak` files only for destinations that actually change. All destinations are preflighted before mutation; a symlink or broken-symlink path component aborts the entire operation with zero writes.

The installer targets project-local `.claude/settings.json`, `.codex/hooks.json`, `.hermes/hooks.json`, and `.hermes/shell-hooks-allowlist.json`. It never edits live user-level client configuration unless an operator explicitly chooses such a directory as `--project-root`.

## Runtime state and limits

The runtime walks upward from recognized payload project/cwd fields (or process cwd) and acts only when both `.codegraph/codegraph.db` and `tools/codegraph_voyage/` exist. State remains under `.codegraph/`:

- `codegraph-voyage.dirty` — coalescing marker;
- `codegraph-voyage.lock` — advisory refresh lock;
- `codegraph-voyage-hooks.log` — bounded local diagnostic log.

Successful indexing clears the dirty marker. Failure or timeout retains it for a later session. Hooks always return success. `CODEGRAPH_VOYAGE_HOOK_TIMEOUT` configures the index bound (default 30 seconds, hard-clamped to 60); `CODEGRAPH_VOYAGE_HOOK_STATUS_TIMEOUT` configures the start probe (default 2 seconds, hard-clamped to 5).
