---
pipeline-status:
  - new
---
# Hermes Fleet Updates

Use this workflow when updating Hermes itself, changing shared non-secret
defaults, or changing how future PM agents are provisioned. First
classify the update, then touch the narrowest source of truth.

> **Service model (canonical, 2026-08):** per agent, ONLY a chat gateway
> service and a heartbeat timer exist. Bloodbank command ingress is the single
> fleet-shared `hermes-fleet-bloodbank-gateway.service`. Per-agent consumer
> units and checkpoint timers are retired — treat any sighting as drift and
> converge it with `pj migrate hermes.registry-parity`.

## Classify the update

Pick one lane before editing files or restarting services:

- **Hermes core update:** new Hermes code in `~/.hermes/hermes-agent`.
- **Shared config update:** non-secret defaults in `~/.hermes/config.yaml`, such
  as `model.default`, provider, display, terminal, or tool settings.
- **Template/provisioning update:** future-agent behavior in
  `hermes-agent-template` or pjangler's vendored template submodule.
- **Runtime contract migration:** existing PM agents need a
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
systemctl --user try-restart 'hermes-*-gateway.service'
systemctl --user try-restart 'hermes-fleet-bloodbank-gateway.service'
```

Interactive `hermes` commands pick up the new code on their next launch.

## Update shared base config

For shared non-secret settings, edit only the fleet default profile:

```bash
HERMES_HOME="$HOME/.hermes" hermes config set model.default gpt-5.4
```

Hermes has no native profile inheritance. After changing the base, regenerate
the real named profiles from their override-only deltas and check drift:

```bash
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-profile-config.py render --all
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-profile-config.py check
```

Do not patch repo-local runtime config or hand-edit a named profile's generated
`config.yaml`. Local overrides belong in each real
`~/.hermes/profiles/<name>/config.delta.yaml`.

All seed, render, absorb, voice, channel, recovery, and backfill writers share
one per-profile transaction lock. The lock must be held before reading state
that will later be written back; channel work orders registry before profile.
Use [config-mutation-safety.md](config-mutation-safety.md) when changing any of
these paths, including their real-caller concurrency regressions.

## Update future-agent provisioning

pjangler runs the vendored template submodule at
`~/code/33GOD/pjangler/templates/hermes-agent` unless `PJANGLER_HERMES_TEMPLATE`
points at a development checkout.

For durable future-agent changes:

1. Patch the template source of truth,
   `~/code/33GOD/hermes-agent-template`.
2. Test with `PJANGLER_HERMES_TEMPLATE=~/code/33GOD/hermes-agent-template` or a safe
   `copier copy -T --trust ... /tmp/...` render.
3. Push the template repo.
4. Bump pjangler's vendored submodule pointer:
   `git -C ~/code/33GOD/pjangler submodule update --remote templates/hermes-agent`.
5. Commit the pjangler submodule pointer.

Future agents receive the new behavior. Existing agents do not change unless
you run a backfill.

## Backfill existing agents

Use backfill only when the runtime/profile contract changed or old agents are
missing generated-profile wiring. Preferred repair targets:

- `~/.hermes/profiles/<repo>-<role>/` is a real directory with identity-only
  `profile.yaml`, a real `config.delta.yaml`, generated `config.yaml`, and an
  explicit Hindsight bank pin.
- `agents/hermes/<role>/runtime/` is ignored/untracked local state, not a
  profile symlink target, submodule, or nested repository.
- `role.yaml` has `profile: <repo>-<role>`.
- systemd user units set `HERMES_HOME` to the named profile path, not the raw
  runtime path.

Use the canonical profile renderer and PJangler migration/parity surfaces for
repairs. Do not recreate the old symlink/native-inheritance layout manually.

For fleet-bloodbank-standard drift (missing registry `bloodbank:` block, legacy
`consumer_unit`/`checkpoint_timer` keys, leftover consumer unit files), run
`pj audit` / `pj migrate hermes.registry-parity` in the repo instead of hand
patching — the parity rule converges all three.

An unchanged rerun must leave `agents-registry.yaml` byte-identical. Preserve
the original `provisioned_at` and all extension/unknown metadata; merge the
owned fields instead of rebuilding a registry row.

## Update Bloodbank hook fan-out

Hermes lifecycle hook wiring is generated by Bloodbank, not hand-maintained in
each runtime. When a hook event, env allowlist, or command shape changes, patch
`~/code/33GOD/bloodbank/services/agent-hooks/hooks.master.json` and the Hermes
adapter, then deploy from the Bloodbank repo:

```bash
cd ~/code/33GOD/bloodbank
mise run deploy
mise run health:hooks:check
```

Existing Hermes runtimes should then call
`~/.agents/hooks/bloodbank/publish.py --client hermes --hook <event>`. Only do a
runtime backfill when health shows an old config missed the generated fan-out.

## Verify

After any lane, verify the actual behavior:

```bash
source ~/.hermes/fleet.env
test -x "$HERMES_FLEET_BIN"
HERMES_HOME="$HOME/.hermes" hermes config get model.default
hermes -p <repo>-pm config get model.default
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-profile-config.py check
```

For daemon-backed agents, also check:

```bash
systemctl --user status hermes-<repo>-pm-gateway.service
systemctl --user status hermes-<repo>-pm-heartbeat.timer
systemctl --user status hermes-fleet-bloodbank-gateway.service
journalctl --user -u hermes-<repo>-pm-heartbeat.service -n 80 --no-pager
```

Use a bounded stabilization window rather than one `is-active` sample. Check
systemd `Result`, `ExecMainStatus`, and `NRestarts` repeatedly through the
deadline, and require the latest heartbeat service result to succeed.

Heartbeats are one-minute oneshot services. A `try-restart` can
surface an existing provider/quota failure as a transient failed service even
when the timer remains healthy. Check the runtime log under
`agents/hermes/pm/runtime/logs/heartbeat.log`; repeated
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
  profiles. Generated base-plus-delta config is not a security boundary.
- Do not store literal credentials in `~/.hermes/.env`; nonsecret toggles may
  remain. Import credentials to DeLoSecrets, map their environment names with
  `secrets.onepassword.env` `op://` references, render/check, and verify the
  actual process without exposing values. Treat that migration as a separate
  approval-gated operation.
- Secret values may enter validation only through a pipe, anonymous FD, or the
  validating process's memory, never curl argv or unrelated child
  environments. A transient 1Password validation failure preserves the last
  valid reference and marker so a healthy rerun can recover.
- A clean tip is not secret-eradication proof. Use
  [secret-migration.md](secret-migration.md) for current files/databases/caches,
  index and local-object coverage, pushed-history proof, and the separate
  authorization gates around rotation and private-remote rewriting.
- Normal Git and release transactions must execute repository and global hooks;
  never use `--no-verify`, `GIT_GUARD_OFF`, or an equivalent bypass.
- For tracked backups, match `*.bak`, `*.bak-*`, `*.orig`, `*~`, and
  `*-backup.*`; add the proper ignore patterns, untrack indexed files with
  scoped `git rm --cached`, commit/push, and verify the remote tree. Preserve
  unrelated dirty runtime state throughout.
- Do not run template backfills for a simple shared default model change.
- Do not patch Hermes runtime hooks by hand when the Bloodbank fan-out source can generate them.
- Do not drop an update stash until the generated-config tests and live smoke
  checks pass.
- Do not assume `scripts/check-windows-footguns.py` is executable; use
  `.venv/bin/python scripts/check-windows-footguns.py` if direct execution gets
  `permission denied`.
- Do not trust stale docs or success summaries over `~/.hermes/fleet.env`, live
  `.project.json`/registry/profile files, systemd state, and renderer checks.
