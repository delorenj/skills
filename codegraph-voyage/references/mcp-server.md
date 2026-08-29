# Companion MCP server

The packaged server lives at `mcp-servers/codegraph-voyage-mcp/` in the Skillex repository. The target project must contain both `.codegraph/codegraph.db` and `tools/codegraph_voyage/`.

## Install

From the package directory:

```bash
python3 -m pip install -e .
# or
uv pip install -e .
```

## Stdio

```json
{
  "mcpServers": {
    "codegraph-voyage": {
      "command": "codegraph-voyage-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

Set `VOYAGE_API_KEY` in the server process environment only when using `provider: "voyage"`. Load it from 1Password with `op read "op://DeLoSecrets/Voyage AI/API Key"`; do not place it in a tool call.

## SSE

```bash
codegraph-voyage-mcp --transport sse --host 127.0.0.1 --port 8765
```

Connect to `http://127.0.0.1:8765/sse`. The SSE transport is intended for trusted local networks unless separately protected.

## Tools

- `index`: build or update symbol embeddings. Supports provider, model, dimensions, file and kind filters, and source-line limits.
- `search` and `semantic_candidates`: hybrid semantic retrieval with configurable result count and filters.
- `status`: inspect the CodeGraph and sidecar indexes.
- `explore`: retrieve candidates and invoke CodeGraph exploration; `dry_run` previews the generated query.

All tools validate `<project_path>/.codegraph/codegraph.db` before execution. The server invokes `python3 -m tools.codegraph_voyage` without a shell, with the project as both working directory and `PYTHONPATH`.
