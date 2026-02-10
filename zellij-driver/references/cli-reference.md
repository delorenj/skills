# Perth CLI Reference

## Commands

### pane

Create, open, and manage panes.

```bash
znav pane <name> [--tab <tab>] [--session <session>] [--meta key=value...]
```

**Arguments:**
- `<name>`: Pane name (required for subcommands)
- `--tab`: Create pane in specific tab
- `--session`: Target session (defaults to current)
- `--meta`: Key-value metadata pairs

**Subcommands:**

#### pane log
```bash
znav pane log <name> "<summary>" [options]
```
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--type` | `-t` | `checkpoint` | Entry type: `checkpoint`, `milestone`, `exploration` |
| `--source` | `-s` | `manual` | Entry source: `manual`, `agent`, `automated` |
| `--artifacts` | `-a` | `[]` | File paths related to this work |

**Examples:**
```bash
znav pane log api "Fixed null pointer" --type milestone
znav pane log research "Explored Redis alternatives" -t exploration
znav pane log worker "Completed analysis" -s agent -a src/main.rs
```

#### pane history
```bash
znav pane history <name> [options]
```
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--last` | `-n` | `100` | Limit entries shown |
| `--format` | `-f` | `text` | Output format |

**Formats:**
| Format | Description |
|--------|-------------|
| `text` | Human-readable with colors |
| `json` | Pretty-printed JSON with schema |
| `json-compact` | Single-line JSON for piping |
| `markdown` | YAML frontmatter (Obsidian) |
| `context` | LLM-optimized narrative (~1000 tokens) |

**Examples:**
```bash
znav pane history api --last 5
znav pane history api -f json | jq '.entries[].summary'
znav pane history api -f context | pbcopy  # For LLM prompt
```

#### pane info
```bash
znav pane info <name>
```
Returns pane metadata including session, tab, position, status.

#### pane snapshot
```bash
znav pane snapshot <name>
```
Generate AI-powered summary. Requires:
- LLM provider configured
- Consent granted (`znav config consent --grant`)

### tab

Tab operations.

```bash
znav tab <name>
```
Switch to or create named tab.

### list

Display all tracked panes in tree format.

```bash
znav list
```

**Output:**
```
session-name
├── tab-1
│   ├── pane-a
│   └── pane-b [stale]
└── tab-2
    └── pane-c
```

### reconcile

Synchronize Redis state with actual Zellij layout.

```bash
znav reconcile
```
- Marks missing panes as stale
- Updates last-seen timestamps
- Reports sync statistics

### migrate

Migrate from v1.0 (`znav:*`) to v2.0 (`perth:*`) keyspace.

```bash
znav migrate [--dry-run]
```
| Option | Description |
|--------|-------------|
| `--dry-run` | Preview without changes |

### config

View and modify configuration.

#### config show
```bash
znav config show
```
Display all settings with sources (default/file/env).

#### config set
```bash
znav config set <key> <value>
```
| Key | Description |
|-----|-------------|
| `redis_url` | Redis connection URL |
| `llm.provider` | LLM provider: `anthropic`, `openai`, `ollama`, `none` |
| `llm.model` | Model override |
| `llm.max_tokens` | Max response tokens |

#### config consent
```bash
znav config consent --grant
znav config consent --revoke
```
Manage LLM data sharing consent.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ZELLIJ_SESSION_NAME` | Current session (set by Zellij) |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `NO_COLOR` | Disable colored output |

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | General error |
| `2` | Configuration error |
| `3` | LLM error (timeout, API failure) |

## JSON Output Schema

### IntentEntry
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-06T12:00:00.000Z",
  "summary": "Description of work",
  "entry_type": "checkpoint",
  "source": "manual",
  "artifacts": ["path/to/file.rs"],
  "commands_run": null,
  "goal_delta": null
}
```

### History Response
```json
{
  "schema_version": "2.0",
  "pane_name": "my-feature",
  "generated_at": "2025-01-06T12:00:00.000Z",
  "total_entries": 15,
  "entries": [...]
}
```

### PaneInfo Response
```json
{
  "pane_name": "my-feature",
  "session": "main",
  "tab": "development",
  "pane_id": null,
  "created_at": "2025-01-06T10:00:00Z",
  "last_seen": "2025-01-06T12:00:00Z",
  "last_accessed": "2025-01-06T12:00:00Z",
  "meta": {"position": "0"},
  "status": "found",
  "source": "redis"
}
```
