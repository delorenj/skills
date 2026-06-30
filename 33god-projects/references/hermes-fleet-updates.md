---
pipeline-status:
  - new
---
# Hermes Fleet Updates

Use this workflow when updating Hermes itself, changing shared non-secret
defaults, or changing how future PM/scrum-master agents are provisioned. First
classify the update, then touch the narrowest source of truth.

## Classify the update

Pick one lane before editing files or restarting services:

- **Hermes core update:** new Hermes code in `~/.hermes/hermes-agent`.
- **Shared config update:** non-secret defaults in `~/.hermes/config.yaml`, such
  as `model.default`, provider, display, terminal, or tool settings.
- **Template/provisioning update:** future-agent behavior in
  `hermes-agent-template` or pjangler's vendored template submodule.
- **Runtime contract migration:** existing PM/scrum-master agents need a
  one-time backfill because the runtime/profile contract changed.

Do not use a template update when a core checkout update or one shared config
write solves the problem.

## Update Hermes core

The fleet launchers read `~/.hermes/fleet.env`, which points every generated
agent at the shared Hermes checkout and binary:

```bash
cd ~/.hermes/hermes-agent
git status --short
git pull --ff-only
```

If the checkout has local Hermes work, do not run `hermes update` or `git pull`
blindly. Preserve the work with a named stash, fast-forward the shared checkout,
then apply the stash without dropping it until tests pass:

```bash
git fetch origin --prune
git stash push -u -m "pre-core-hermes-update-YYYY-MM-DD-<topic>"
git merge --ff-only origin/main
git stash apply stash@{0}
```

Resolve conflicts against the updated architecture. As of June 2026, many
`hermes_cli/main.py` parser blocks live in `hermes_cli/subcommands/*`; add new
CLI flags and subcommands to the extracted parser module, not to the old inline
block.

Only reinstall dependencies when project dependencies changed. If `pyproject.toml`
or `uv.lock` changed, inspect the diff and preserve installed optional extras;
do not run a plain `uv sync` blindly because it can prune extras such as voice
or messaging integrations. If dependency files did not change, the editable
checkout makes the new code live without a reinstall.

For the shared dev/fleet checkout, sync the venv with the curated `all` extra,
`dev`, and any optional extras already present. Include `voice` when `numpy` or
`sounddevice` were installed even if `faster-whisper` was missing; otherwise the
sync can silently remove local audio support.

```bash
UV_PROJECT_ENVIRONMENT="$PWD/.venv" uv sync --locked \
  --extra all --extra dev \
  --extra anthropic --extra messaging --extra voice
```

Add any other observed installed extras, such as `exa`, `firecrawl`,
`parallel-web`, `fal`, `edge-tts`, `honcho`, or `bedrock`.

Restart long-running user services after the code update:

```bash
systemctl --user daemon-reload
systemctl --user try-restart 'hermes-*-gateway.service' 'hermes-*-consumer.service'
systemctl --user try-restart 'hermes-gateway*.service'
systemctl --user try-restart 'hermes-*-continuous-ticket-sentinel.timer'
```

Interactive `hermes` commands pick up the new code on their next launch.

## Update shared inherited config

For shared non-secret settings, edit only the fleet default profile:

```bash
HERMES_HOME="$HOME/.hermes" hermes config set model.default gpt-5.4
```

Inherited PM and scrum-master profiles pick this up automatically through
`runtime/profile.yaml`:

```yaml
config:
  inherit_from: default
  save_mode: delta
```

Do not patch every `agents/hermes/<role>/runtime/config.yaml` for shared
defaults. Runtime configs must stay override-only, usually just local settings
such as `terminal.cwd`.

## Update future-agent provisioning

pjangler runs the vendored template submodule at
`~/code/pjangler/templates/hermes-agent` unless `PJANGLER_HERMES_TEMPLATE`
points at a development checkout.

For durable future-agent changes:

1. Patch the template source of truth, usually
   `~/code/hermes-agent-template`.
2. Test with `PJANGLER_HERMES_TEMPLATE=~/code/hermes-agent-template` or a safe
   `copier copy -T --trust ... /tmp/...` render.
3. Push the template repo.
4. Bump pjangler's vendored submodule pointer:
   `git -C ~/code/pjangler submodule update --remote templates/hermes-agent`.
5. Commit the pjangler submodule pointer.

Future agents receive the new behavior. Existing agents do not change unless
you run a backfill.

## Backfill existing agents

Use backfill only when the runtime/profile contract changed or old agents are
missing inherited-profile wiring. Preferred repair targets:

- `agents/hermes/<role>/runtime/profile.yaml` contains
  `config.inherit_from: default` and `config.save_mode: delta`.
- `~/.hermes/profiles/<repo>-<role>` points at
  `agents/hermes/<role>/runtime/`.
- `role.yaml` has `profile: <repo>-<role>`.
- systemd user units set `HERMES_HOME` to the named profile path, not the raw
  runtime path.
- `runtime/config.yaml` contains only local overrides.

If the Hermes checkout has `scripts/migrate-repo-agents-inherited-config.py`,
prefer it for conventional PM and scrum-master migrations. Otherwise, patch the
items above manually and restart the affected user services.

## Verify

After any lane, verify the actual behavior:

```bash
source ~/.hermes/fleet.env
test -x "$HERMES_FLEET_BIN"
HERMES_HOME="$HOME/.hermes" hermes config get model.default
hermes -p <repo>-pm config get model.default
hermes -p <repo>-scrum-master config get model.default
hermes profile create inherited-test --inherit-config --no-alias
hermes profile show inherited-test
hermes -p inherited-test config get model.default
hermes profile delete inherited-test -y
```

For daemon-backed agents, also check:

```bash
systemctl --user status hermes-<repo>-pm-gateway.service
systemctl --user status hermes-<repo>-scrum-master-continuous-ticket-sentinel.timer
journalctl --user -u hermes-<repo>-scrum-master-continuous-ticket-sentinel.service -n 80 --no-pager
```

Continuous-ticket sentinels are one-minute oneshot services. A `try-restart` can
surface an existing provider/quota failure as a transient failed service even
when the timer remains healthy. Check the runtime log under
`agents/hermes/<role>/runtime/logs/continuous-ticket-sentinel.log`; repeated
`HTTP 429: Insufficient balance or no resource package` means the sentinel
workload reached the provider, not that the Hermes update failed. Wait for one
timer tick and confirm the service returns to `inactive (dead)` with the timer
`active (waiting)`.

Run the focused Hermes checks from the current test harness. If
`scripts/run_tests.sh ... -q` fails with an unrecognized `-q`, rerun without
`-q`; the wrapper now delegates to `run_tests_parallel.py`.

```bash
scripts/run_tests.sh tests/hermes_cli/test_config.py tests/hermes_cli/test_profiles.py
.venv/bin/python scripts/check-windows-footguns.py
```

## Pitfalls

- Do not copy `.env`, `auth.json`, sessions, memories, or gateway state between
  profiles. Only `config.yaml` participates in inheritance.
- Do not treat inherited config as a security boundary.
- Do not run template backfills for a simple shared default model change.
- Do not drop an update stash until the inherited-config tests and live smoke
  checks pass.
- Do not assume `scripts/check-windows-footguns.py` is executable; use
  `.venv/bin/python scripts/check-windows-footguns.py` if direct execution gets
  `permission denied`.
- Do not trust stale docs over `~/.hermes/fleet.env`, live `role.yaml`, systemd
  units, and the actual runtime/profile symlinks.
