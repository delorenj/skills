# cli-web-search reference

Upstream: https://github.com/scottgl9/cli-web-search (Rust, Apache-2.0, one author). Pinned to
`72f581e54df8b538a1769d4027b2d73a2309f7d4` plus `scripts/patches/0001-providers-no-redirects.patch`. Binary:
`~/.local/libexec/web-search/bin/cli-web-search` (0.1.0, default features, so no MCP server; deliberately not on
PATH). Facts below were observed on this machine on 2026-10-02 or read from the pinned source. Prefer the wrapper;
this is background for when you must go beyond it. Never call the raw binary with keys on argv.

## Commands and flags

`cli-web-search [OPTIONS] [QUERY] [COMMAND]`; commands `config`, `providers`, `cache`, `fetch <URL>`.

| Flag | Meaning |
| --- | --- |
| `-p/--provider brave\|tavily\|ddg\|google\|serper\|firecrawl\|serpapi\|bing` | a preference, not a filter: moves it first; the rest stay as fallbacks |
| `-f/--format json\|markdown\|text` | default text (aborts on some non-ASCII snippets, `text.rs:70`); always use `json` |
| `-n/--num-results N` | default 10, sent to every provider |
| `--date-range day\|week\|month\|year` | Brave `freshness`; ignored by Tavily |
| `--safe-search off\|moderate\|strict` | Brave only |
| `--timeout S` | per HTTP request, default 30; with 3 attempts a failure can take 3 x S |
| `--include-domains/--exclude-domains` | parsed and **never used** (no-ops on every provider); the wrapper offers `--site` instead |
| `--no-cache`, `cache clear\|stats` | inert: the cache is per process |
| `-v/-vv/-vvv`, `-q` | logs go to STDOUT; `RUST_LOG=off` is the only clean fix |

`fetch <URL>`: `-f text|html|markdown`, `--timeout`, `--json`, `--stdout`, `-q`, `-o FILE`, `--max-length BYTES`
(panics on a non-ASCII boundary; never use). Without `--stdout` it writes under `~/.cache/cli-web-search/fetch/`.

Parsing quirks: exactly one positional query (quote it); a query equal to a subcommand name runs the subcommand;
a query starting with `-` needs `--`; `--help` after a subcommand is unreliable (root help, or a "no providers
configured" error), so use the root `--help` and this page.

## Keys and providers

Only `CLI_WEB_SEARCH_*` variables are read; bare `TAVILY_API_KEY` and `BRAVE_API_KEY` are ignored.

| Provider | Env | Request | Honors |
| --- | --- | --- | --- |
| brave | `CLI_WEB_SEARCH_BRAVE_API_KEY` | GET `api.search.brave.com/res/v1/web/search`, header `X-Subscription-Token` | `-n`, date range, safe search |
| tavily | `CLI_WEB_SEARCH_TAVILY_API_KEY` | POST `api.tavily.com/search`, key in the JSON body (`search_depth: basic`) | `-n` only |

A provider exists only if its key (or a config entry) exists, so with only one key exported there is no
fallback. Registration order is brave, google, duckduckgo, tavily, ...; `-p` just reorders. Fallback is sequential
and first-success-wins. 401/403 aborts the chain; Brave answers a bad key with 422, which falls through. An empty
result list counts as success upstream (the wrapper treats it as a reason to try the next provider).
Retries: 3 attempts on network errors and 429 with 0.5 s and 1 s backoff; `Retry-After` is honored uncapped.

## Output shapes

Search (`-f json`, pretty-printed): `{query, provider, timestamp, total_results, search_time_ms, results:[{title,
url, snippet, position, source?, published_date?}]}`. No score, content or answer fields.

Fetch (`--json --stdout`): `{url, final_url, status, content_type, content, content_length, title}`.
Errors are plain text on stderr (`Error: ...`), never JSON. Exit codes: 0 ok (even with zero results), 1 runtime
error, 2 usage error, 134 abort (release profile is `panic = abort`).

Observed with real keys:

| | Brave | Tavily |
| --- | --- | --- |
| latency | 0.7 to 1.2 s | 1.4 to 2.0 s |
| snippet | 12 to 540 chars | 1,200 to 1,500 chars of page excerpt |
| extras | `source` (domain), `published_date` ("17 hours ago", "1 week ago" or "February 3, 2026", sometimes absent) | none |
| auth | header | body `api_key` (current Tavily docs show a Bearer header, but the body form still works with a valid key) |

`fetch` of a small page takes about 0.1 s. A 40 MiB page peaked at 1.2 GiB resident (roughly 30x amplification
in the hand-written HTML-to-text loops), which is why the wrapper caps the child at 2 GiB.

## Known upstream defects (all handled by the wrapper unless noted)

1. Logs print to stdout, so a failover WARN line corrupts JSON. Handled: `RUST_LOG=off`.
2. Panics (exit 134) on non-ASCII byte boundaries in `text.rs:70` and `fetch.rs:177`, and on a Kelvin sign before
   `<title>` (`fetch.rs:217`). Handled: JSON format, no `--max-length`; the title case cannot be avoided (exit 5).
3. `config set` merges the environment into the config and persists every env-supplied key to a plaintext
   `config.yaml` (it also prints the key and value you pass it; `config get` and `list` show keys masked). Handled:
   read-only config stub.
4. `fetch` has no SSRF filter and no body size limit. Handled: the wrapper's egress proxy (every hop checked, the
   validated address pinned) plus the memory and output caps.
5. Provider clients followed cross-host redirects (forwarding the Brave header or Tavily body key). Handled by the patch.
6. `-p` does not restrict providers; the `defaults:` block and `default_provider` are never read; `config validate`
   reports an invalid key as "Not configured" and spends a real call; a malformed config.yaml is silently ignored.
7. Docs drift: the README suggests `-p duckduckgo` (the value is `ddg`) and claims domain filtering works.
8. `--json` without `--stdout` hand-builds invalid JSON for titles ending in a backslash (the wrapper always uses `--stdout`).
9. The CLI's own HTML conversion drops link URLs, destroys code indentation, glues table cells and nav items together
   (`HomeProductsPricing`), keeps `display:none` and `<noscript>` text, and also pushes plain-text, JSON and XML bodies
   through the HTML stripper, deleting every `<...>` span. Handled: the wrapper fetches the raw body with `-f html`
   and converts it itself (`scripts/html2md.py`), showing non-HTML bodies raw.
