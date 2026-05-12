# Adding a new harness (Cursor, Aider, Codex CLI, OpenCode, Cody, ...)

Reuse the Copilot pattern unless the new harness has unusual constraints. The Copilot publisher is small and harness-agnostic; the harness-specific work is the hook-config file and a hook-name → event-subject mapping.

## Workflow

### 1. Identify the harness's hook surface

For each candidate, locate:

- The hook-config format and discovery path (e.g., `~/.copilot/hooks/*.json`, `~/.config/<harness>/hooks.toml`, in-repo `.<harness>/hooks/`).
- The list of lifecycle events the harness exposes (session start/end, pre/post tool, prompt submit, error, stop, etc.).
- How the harness passes context to the hook command (stdin JSON, env vars, argv).

Most modern CLIs (Copilot, Claude Code, Cursor, Aider, OpenCode) converge on **stdin JSON + a shell command per hook entry**. Codex CLI uses TOML config and env-var context. Cody uses VS Code extension events.

### 2. Decide on the subject root

Use `event.<harness>.<entity>.<action>` where `<harness>` is the short, lowercase name (`copilot`, `aider`, `cursor`, `codex`, `opencode`, `cody`). The `agent.*` root is reserved for Claude Code by precedent.

Define one envelope `type` per harness lifecycle event. The seven Copilot types are a good starter set; trim or extend as the harness exposes more or fewer.

### 3. Write or reuse the publisher

The default move: **reuse `bloodbank/services/copilot-hooks/copilot_hook_publish.py` verbatim**. Pass a different `--source` and a different hook→subject map.

When you need a per-harness publisher:

1. Copy `services/copilot-hooks/` to `services/<harness>-hooks/`.
2. Edit the `HOOK_SUBJECT_MAP` and the envelope `source` to `urn:33god:integration:<harness>-cli`.
3. Keep it stdlib-only unless the harness's hook script can already invoke a venv.

### 4. Write the hooks config

One file per harness, mirroring the Copilot shape:

```json
{
  "version": 1,
  "hooks": {
    "<harnessHookName>": [{
      "type": "command",
      "bash": "exec python3 /abs/path/to/publisher.py <harnessHookName>",
      "timeoutSec": 5
    }],
    ...
  }
}
```

Adapt to the harness's config format (TOML, YAML, etc.) but keep two things constant:

- **timeoutSec ≤ 5s.** Hooks must not visibly slow the agent.
- **`exec` the python.** Saves a fork on hot-path hooks (preToolUse / postToolUse).

### 5. Install at the harness's user-level hooks dir

```bash
mkdir -p ~/.config/<harness>/hooks   # or wherever the harness looks
ln -snf ~/code/33GOD/bloodbank/services/<harness>-hooks/hooks.<ext> \
        ~/.config/<harness>/hooks/bloodbank.<ext>
```

Symlinks keep the canonical config in the repo so edits propagate without re-installing.

### 6. Verify

Run each hook by hand against the publisher, then check the toaster log and ntfy stream:

```bash
for h in $(jq -r '.hooks | keys[]' ~/code/33GOD/bloodbank/services/<harness>-hooks/hooks.json); do
  echo "{\"probe\":\"$h\"}" | python3 ~/code/33GOD/bloodbank/services/<harness>-hooks/publisher.py "$h"
done
docker logs bloodbank-event-toaster --tail 30 | grep "toasted: <harness>"
```

Then trigger the harness in real use and confirm matching titles on `https://ntfy.delo.sh/bloodbank`.

### 7. Record the integration

- Update `references/hooks/README.md`'s "Subject layout per harness" table.
- `hindsight memory retain bloodbank "<harness> hooks integrated at services/<harness>-hooks/; subjects event.<harness>.*" --context architecture`.

## When the simple pattern doesn't fit

Reach for a daemon (the Claude Code / hookd pattern) only if:

- The harness fires hooks faster than ~50 events/sec sustained (publisher fork overhead matters).
- You need on-host enrichment (git branch, session_id correlation across hooks) that's expensive to recompute each event.
- The harness's hooks pass only opaque blobs and you want a single place to parse & enrich.

Otherwise stick with the stdlib publisher. It's ~80 lines of code and has zero deployment story.

## Out of scope for the integration

- Modifying the harness itself. Always tap public hooks, never patch the harness binary.
- Filtering events on the producer side. Publish everything; let downstream consumers filter.
- Pre-aggregating tool calls. Each PreToolUse / PostToolUse fires its own envelope; downstream services can correlate by session_id.
