---
name: codegraph-voyage
description: Use for symbol-level semantic code search, hybrid retrieval, or CodeGraph exploration seeded with vector candidates.
---

# CodeGraph Voyage

`codegraph-voyage` is a symbol-level semantic retrieval sidecar for CodeGraph. It builds embeddings from `.codegraph/codegraph.db`, stores them separately in `.codegraph/codegraph-voyage.db`, and combines lexical and vector candidates for search and `codegraph explore`.

Use it when the user asks for semantic code search, hybrid lexical/vector retrieval, or a CodeGraph exploration seeded by semantically relevant symbols. Run commands from a project root containing `.codegraph/codegraph.db`, using the installed `codegraph-voyage` CLI (alias `cgv`).

## CLI

```bash
codegraph-voyage index [--provider voyage|openrouter|automaticai] [--model MODEL] [--dimensions N]
codegraph-voyage search "query" [--provider voyage|openrouter|automaticai] [--top-k N] [--json]
codegraph-voyage status
codegraph-voyage purge (--fake | --model MODEL [--dimensions N]) [--dry-run]
codegraph-voyage explore "query" [--provider voyage|openrouter|automaticai] [--dry-run]
```

`search` is also available as `semantic_candidates`. Index before searching when `.codegraph/codegraph-voyage.db` is absent or stale. Use `status` to inspect the CodeGraph and embedding indexes.

The `fake` provider is test-only: it writes hash vectors, not semantic embeddings, so never run it on a real project.
The sidecar refuses to store fake vectors beside real ones, a real-provider `index` purges any leftovers, and `status` flags them (`purge --fake` removes them on demand).
The `voyage` provider sends locally sanitized source-derived text to Voyage AI.
The `openrouter` provider sends requests to OpenRouter's OpenAI-compatible embeddings API.

Defaults can be persisted in `~/.config/codegraph-voyage/config.toml` (e.g. `provider = "openrouter"`, `model = "voyage-4"`).

## Credentials

Load the necessary key into the environment:

For Voyage:
```bash
export VOYAGE_API_KEY="$(op read 'op://DeLoSecrets/Voyage AI/API Key')"
codegraph-voyage index --provider voyage
```

For OpenRouter:
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
codegraph-voyage index --provider openrouter --model "voyage-4"
```

Never put secrets in CLI arguments, source files, logs, or MCP tool arguments.

## Project-scoped lifecycle hooks

This skill includes an optional hook bundle that keeps an existing CodeGraph Voyage index fresh without joining or modifying any global lifecycle publisher. The hook runtime is project-scoped and only acts when the project contains both `.codegraph/codegraph.db` and `tools/codegraph_voyage/`.

```bash
# Generate deterministic native fragments under hooks/generated/
python3 scripts/hooks-fanout.py render
python3 scripts/hooks-fanout.py check

# Install into one project only (surgical merge; unrelated hooks are preserved)
python3 scripts/hooks-fanout.py install --project-root /absolute/project
python3 scripts/hooks-fanout.py uninstall --project-root /absolute/project
```

The runtime defaults to `off`: it marks dirty state but never indexes. Refreshing is an explicit per-project opt-in with `CODEGRAPH_VOYAGE_HOOK_PROVIDER=<voyage|openrouter|automaticai>` in the client runtime environment or `{"codegraph_voyage":{"hook_provider":"automaticai"}}` (same values) in gitignored `.agents/local.json`. Pick the provider whose model matches the project's existing sidecar (`codegraph-voyage status`). The client must inherit that provider's API key (`VOYAGE_API_KEY`, `OPENROUTER_API_KEY` or `AUTOMATICAI_API_KEY`); never put a key in hook JSON, config arguments, logs, or tool payloads. `fake` (and any unknown value) is rejected and treated as `off`, because fake vectors are not semantic and used to fill real indexes.

Read [references/hooks.md](references/hooks.md) for lifecycle behavior, generated client mappings, safety properties, and local configuration.

## Companion MCP server

Use the packaged `codegraph-voyage-mcp` server when an MCP client should invoke the sidecar interactively. Its tools are `index`, `search`, `semantic_candidates`, `status`, and `explore`; every call requires an explicit `project_path`. The MCP server is separate from both this instructional skill and the optional lifecycle hooks. It inherits `VOYAGE_API_KEY` from its environment and never accepts the key as a tool argument.

Read [references/mcp-server.md](references/mcp-server.md) for installation, transport configuration, and tool details.
