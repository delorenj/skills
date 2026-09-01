# Adding a new harness (Cursor, Aider, OpenCode, Cody, ...)

Do **not** copy an existing per-client publisher tree. Bloodbank now has one
canonical publisher (`services/agent-hooks/publish.py`) and one shared pipeline
(`core/publisher.py`). A new harness adds a client adapter plus fan-out metadata.

## Workflow

### 1. Identify the harness hook surface

For each candidate, locate:

- The hook-config format and discovery path (for example
  `~/.config/<harness>/hooks.toml` or in-repo `.<harness>/hooks/`).
- Native lifecycle events: session start/end, user prompt, pre/post tool,
  subagent/invocation, error, stop.
- Payload transport: stdin JSON, env vars, argv, shell vs `shell=False`.
- Timeout and approval/allowlist semantics.

### 2. Map native events to canonical lifecycle roles

Edit `~/code/33GOD/bloodbank/services/agent-hooks/hooks.master.json`.

- Add `agents.<harness>` with `dialect`, `runner`, `config_target`,
  `event_map_target`, `actor`, and `bindings`.
- Use existing roles when semantics match (`session_start`, `post_tool`,
  `subagent_stop`, etc.) so lock-file decisions apply automatically.
- Prefer this runner shape for generated live configs:

```json
"runner": "python3 {hooks_dir}/bloodbank/publish.py --client <harness> --hook"
```

`{hooks_dir}` resolves to `~/.agents/hooks`, and install ensures
`~/.agents/hooks/bloodbank -> services/agent-hooks`.

### 3. Add a client adapter

Create `services/agent-hooks/clients/<harness>.py`.

The adapter owns only harness-specific work:

- read payload and resolve the hook name
- flatten/wrap odd payload shapes
- select actor/model fields
- choose session file path and reset/archive behavior
- shape `data` for each canonical `ce_type`

Shared work stays in `core.publisher`: event-map lookup, envelope construction,
NATS publish, fail-open behavior, strict-mode handling, health-compatible logging,
and session causation updates.

Register the adapter in `services/agent-hooks/clients/__init__.py`. Add a tiny
`<harness>/publish.py` wrapper only when old commands or external tools may still
call a per-client path; wrappers are compatibility shims, not implementation
homes.

### 4. Generate and install configs

```bash
cd ~/code/33GOD/bloodbank
mise run hooks:check
mise run hooks:sync
mise run deploy
```

`deploy` updates live Claude/Codex JSON surgically, refreshes Copilot symlinks,
seeds Hermes fleet runtime hooks/allowlists, and creates the canonical
`~/.agents/hooks/bloodbank` link if missing.

### 5. Verify

Run both SSOT and deployed-config checks:

```bash
mise run smoketest:agent-hooks-ssot
BLOODBANK_ENABLED=false python3 services/agent-hooks/health/hook_healthcheck.py --check
```

Then smoke the canonical path directly:

```bash
printf '{"probe":"session"}' \
  | BLOODBANK_ENABLED=false python3 ~/.agents/hooks/bloodbank/publish.py \
      --client <harness> --hook <native-event>
```

With NATS up, remove `BLOODBANK_ENABLED=false`, set `BLOODBANK_HOOK_VERBOSE=1`,
and tail `bloodbank-event-toaster`.

### 6. Record the integration

- Update `references/hooks/README.md` with the supported harness.
- Update `services/agent-hooks/README.md` in Bloodbank.
- Retain the durable fact in Hindsight:

```bash
hindsight memory retain bloodbank \
  "<harness> hooks integrated through services/agent-hooks/publish.py with client adapter clients/<harness>.py" \
  --context architecture
```

## When the adapter boundary is not enough

Reach for a daemon only if the public hook command cannot meet the operational
constraints:

- sustained event rate is high enough that one Python process per event is too
  expensive
- payload parsing/enrichment requires long-lived cached state
- the harness only emits opaque data that needs a supervisor process

Even then, keep event types and generated config bindings in `hooks.master.json`,
and keep the daemon as a client implementation behind the same canonical
lifecycle contract.

## Out of scope

- Modifying the harness binary.
- Inventing provider-specific event types. Provider identity goes in `actor`.
- Filtering out semantically valid lifecycle events on the producer side.
- Pre-aggregating tool calls; downstream consumers correlate with
  `correlationid`, `causationid`, `ordering_key`, and tool/session IDs.
