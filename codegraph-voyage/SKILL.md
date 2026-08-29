---
name: codegraph-voyage
description: Use for symbol-level semantic code search, hybrid retrieval, or CodeGraph exploration seeded with vector candidates.
---

# CodeGraph Voyage

`codegraph-voyage` is a symbol-level semantic retrieval sidecar for CodeGraph. It builds embeddings from `.codegraph/codegraph.db`, stores them separately in `.codegraph/codegraph-voyage.db`, and combines lexical and vector candidates for search and `codegraph explore`.

Use it when the user asks for semantic code search, hybrid lexical/vector retrieval, or a CodeGraph exploration seeded by semantically relevant symbols. Run commands from a project root containing `.codegraph/codegraph.db` and the `tools/codegraph_voyage/` sidecar package.

## CLI

```bash
python3 -m tools.codegraph_voyage index [--provider fake|voyage] [--dimensions N]
python3 -m tools.codegraph_voyage search "query" [--provider fake|voyage] [--top-k N] [--json]
python3 -m tools.codegraph_voyage status
python3 -m tools.codegraph_voyage explore "query" [--provider fake|voyage] [--dry-run]
```

`search` is also available as `semantic_candidates`. Index before searching when `.codegraph/codegraph-voyage.db` is absent or stale. Use `status` to inspect the CodeGraph and embedding indexes.

The `fake` provider is deterministic, offline, and suitable for development and CI. The `voyage` provider sends locally sanitized source-derived text to Voyage AI. Use it only when remote processing is acceptable.

## Voyage credentials

Load the key into the environment from 1Password, then run the command:

```bash
export VOYAGE_API_KEY="$(op read 'op://DeLoSecrets/Voyage AI/API Key')"
python3 -m tools.codegraph_voyage index --provider voyage
```

Never put the key in CLI arguments, source files, logs, or MCP tool arguments.

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

The runtime defaults to the offline deterministic `fake` provider. Remote Voyage processing is never automatic: opt in per project with `CODEGRAPH_VOYAGE_HOOK_PROVIDER=voyage` in the client runtime environment or `{"codegraph_voyage":{"hook_provider":"voyage"}}` in gitignored `.agents/local.json`. The client must inherit `VOYAGE_API_KEY`; never put that key in hook JSON, config arguments, logs, or tool payloads. Set the provider to `off` to disable refreshes.

Read [references/hooks.md](references/hooks.md) for lifecycle behavior, generated client mappings, safety properties, and local configuration.

## Companion MCP server

Use the packaged `codegraph-voyage-mcp` server when an MCP client should invoke the sidecar interactively. Its tools are `index`, `search`, `semantic_candidates`, `status`, and `explore`; every call requires an explicit `project_path`. The MCP server is separate from both this instructional skill and the optional lifecycle hooks. It inherits `VOYAGE_API_KEY` from its environment and never accepts the key as a tool argument.

Read [references/mcp-server.md](references/mcp-server.md) for installation, transport configuration, and tool details.
