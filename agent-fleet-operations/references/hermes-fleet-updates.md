---
pipeline-status:
  - new
---
# Hermes Fleet Updates

Use this workflow when updating Hermes itself, changing shared non-secret
defaults, or changing how future employees are provisioned. First classify the
update, then touch the narrowest source of truth.

> **Runtime model (canonical, 2026-10-17): ONE install, ONE code path.** `~/.hermes/hermes-agent` is a
> checkout of `delorenj/hermes-agent` `main`. `hermes-gateway.service` (Hermes' own installer wrote it: ONE
> host gateway multiplexes every profile, including the Bloodbank fleet lane), `~/.local/bin/hermes`,
> `HERMES_FLEET_BIN` in `~/.hermes/fleet.env`, the template `[fleet]` config, every `agents/hermes/*/hermes`
> wrapper and every registry row resolve to its launcher `.hermes/bin/hermes`. There is no `releases/<sha>`
> checkout. Per-agent `hermes-<agent>-gateway.service` units, heartbeat timers, consumer units and checkpoint
> timers are retired. Drift guard: `mise run hermes:one` in `templates/hermes-agent`
> (`scripts/hermes-single-install-check.py`).

## Classify the update

Pick one lane before editing files or restarting services:

- **Hermes core update:** new Hermes code in `~/.hermes/hermes-agent`.
- **Shared config update:** non-secret defaults in `~/.hermes/config.yaml`, such
  as `model.default`, provider, display, terminal, or tool settings.
- **Template/provisioning update:** future-employee behavior in
  `hermes-agent-template` or flume's vendored template submodule.
- **Runtime contract migration:** existing employees need a one-time backfill
  because the runtime/profile contract changed.

Do not use a template update when a core checkout update or one shared config
write solves the problem.

## Update Hermes core

**What actually runs (2026-10-17).** One install, `~/.hermes/hermes-agent`, tracking `delorenj/main` (not Nous
`origin/main`; never run `hermes update`). Land fork changes through a clone, never by editing the install:

```bash
# 1. work in a full clone of the fork (a worktree of the install fails the home-IO test guard), test, push
git clone git@github.com:delorenj/hermes-agent.git ~/code/hermes-work && cd ~/code/hermes-work
HERMES_PYTHON=<venv-with-pytest> scripts/run_tests.sh tests/agent/<the tests>
git push origin HEAD:main
# 2. deploy: fast-forward the one install (Hermes sweeps stale __pycache__ via .bytecode-fingerprint)
git -C ~/.hermes/hermes-agent pull --ff-only
# 3. restart the ONE gateway; the wrapper waits for idle (active_agents == 0, no turn lease) and coalesces callers
hermes-gateway-restart --reason "<why>"
# 4. prove nothing drifted
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-single-install-check.py
```

A gateway is healthy when it logs `Gateway running with N platform(s)`, or
`No messaging platforms enabled` then `Gateway housekeeping started` for a
cron-only desk. PM work dispatched over Bloodbank runs inside
`hermes-fleet-bloodbank-gateway`, so a PM's Hindsight traffic shows up in
`~/.hermes/profiles/fleet-bloodbank-gateway/logs/agent.log`, not the desk's
own log. A desk-local `hermes -p <pm> chat` uses that desk's `.env` model
keys, which can be stale even while the fleet gateway works.

The older shared-checkout flow below is kept for the dev checkout:

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

For the shared dev checkout, sync the venv with the curated `all` extra, `dev`,
and any optional extras already present. Include `voice` when `numpy` or
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
hermes-gateway-restart --reason "<why>"   # waits for idle; it serves every profile (never raw systemctl restart)
```

Interactive `hermes` commands pick up the new code on their next launch.

### The real import env and the safe restart

When a gateway must load NEW Python code (a newly pip-installed package, a
first-time platform plugin), a plain restart is not always enough and the
import env is not the obvious one:

- The gateway process bootstraps through `hermes_bootstrap`, which redirects
  `sys.path` to a PM-managed env under
  `~/.hermes/installs/<release-id>/venv` — NOT the repo `.venv` and NOT the
  dev checkout. A package installed into the wrong env is invisible to the
  gateway no matter how many times you restart it. Verify before installing:
  read the unit's `ExecStart`, resolve which env `hermes_bootstrap` actually
  enters, and install there.
- Restarting the fleet gateway from inside a turn that the gateway itself is
  driving kills the dispatching process before its own completion events
  publish. Use `hermes-gateway-restart --reason "<why>"`: it detaches itself
  when run from inside the gateway and waits for your own turn to end. Never
  arm a cron line or a hand-rolled `systemd-run` timer for this.
- After any restart, prove liveness from the journal, not `is-active` alone:
  look for the platform-adapter attach line (e.g. `Bloodbank gateway
  connected`) and for the durable consumer's `num_pending` draining to 0 at
  `http://127.0.0.1:8222/jsz?streams=true&consumers=true`.

## Update shared base config

For shared non-secret settings, edit only the fleet default profile:

```bash
HERMES_HOME="$HOME/.hermes" hermes config set model.default gpt-5.4
```

Hermes has no native profile inheritance. After changing the base, regenerate
the real named desks from their override-only deltas and check drift:

```bash
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-profile-config.py render --all
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-profile-config.py check
```

Do not patch repo-local runtime config or hand-edit a named desk's generated
`config.yaml`. Local overrides belong in each real
`~/.hermes/profiles/<name>/config.delta.yaml` — and a delta that redeclares a
base LIST replaces it rather than extending it, which is what
`flume audit --rules hermes.delta-list-override` catches.

All seed, render, absorb, voice, channel, recovery, and backfill writers share
one per-profile transaction lock. The lock must be held before reading state
that will later be written back; channel work orders registry before profile.
Use [config-mutation-safety.md](config-mutation-safety.md) when changing any of
these paths, including their real-caller concurrency regressions.

## Update future-employee provisioning

`flume hire` runs the vendored template submodule at
`~/code/33GOD/flume/templates/hermes-agent`. Resolution order is: explicit
`PJANGLER_HERMES_TEMPLATE` → the vendored submodule (the version-locked default)
→ a `~/code/hermes-agent-template` dev checkout → the published
`gh:delorenj/hermes-agent-template`.

For durable future-employee changes:

1. Patch the template source of truth,
   `~/code/33GOD/hermes-agent-template`.
2. Test with `PJANGLER_HERMES_TEMPLATE=~/code/33GOD/hermes-agent-template` or a
   safe `copier copy -T --trust ... /tmp/...` render.
3. Push the template repo.
4. Bump flume's vendored submodule pointer:
   `git -C ~/code/33GOD/flume submodule update --remote templates/hermes-agent`.
5. Commit the flume submodule pointer.

Future employees receive the new behavior. Current ones do not change unless you
run a backfill.

The ticket-provider adapters (`plane.sh`, `linear.sh`, `trello.sh`) are canonical
in `~/code/33GOD/krebs/adapters/tp/` and vendored into
`template/.scripts/providers/`. Patch krebs first, then re-vendor; the two copies
are expected to be byte-identical.

## Backfill current employees

Use backfill only when the runtime/profile contract changed or old agents are
missing generated-desk wiring. Preferred repair targets:

- `~/.hermes/profiles/<repo>-<title>/` is a real directory with identity-only
  `profile.yaml`, a real `config.delta.yaml`, generated `config.yaml` carrying
  the renderer's header marker, and an explicit Hindsight bank pin.
- `agents/hermes/<title>/runtime/` is ignored/untracked local state, not a
  profile symlink target, submodule, or nested repository.
- `role.yaml` has `profile: <repo>-<title>`.
- systemd units set `HERMES_HOME` to the named desk path, not the raw runtime
  path.

Use the canonical profile renderer and flume's remediation surface for repairs.
Do not recreate the old symlink/native-inheritance layout manually.

```bash
flume audit                                        # the employee rules, this repo
flume remediate hermes.runtime-singleton --dry-run # plan before applying
flume remediate hermes.runtime-singleton
```

For fleet-bloodbank-standard drift (missing registry `bloodbank:` block, legacy
`consumer_unit`/`checkpoint_timer` keys, leftover consumer unit files), run
`flume audit` / `flume remediate hermes.registry-parity` in the repo instead of
hand patching — the rule converges all three.

`hermes.fleet-config` is intentionally not auto-fixable: those are fleet-wide
operator decisions, and `remediate` reports `blocked` rather than guessing a
value that changes every agent at once.

For a whole-workforce sweep against the current job description, run from the
flume repo:

```bash
mise run org:check   # dry run: drift between deployed employees and the template
mise run org:sync    # apply
```

An unchanged rerun must leave `agents-registry.yaml` byte-identical. Preserve
the original `provisioned_at` and all extension/unknown metadata; merge the
owned fields instead of rebuilding a row.

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

Existing Hermes runtimes should then call the hook-hub client
`~/.agents/hooks/bb-hook --cli hermes --native <event>` (bloodbank
`services/agent-hooks/hooks.master.json` names `bb-hook` as Hermes' publisher;
`bloodbank/publish.py` and `hermes/publish.py` are legacy forwarders to the hub).
Only do a runtime backfill when health shows an old config missed the generated
fan-out. `hermes.fleet-config` requires the base `hooks:` block to carry all four
events (`on_session_start`, `on_session_end`, `pre_tool_call`, `post_tool_call`)
and each of them to call that canonical publisher for its own native event.

## Verify

After any lane, verify the actual behavior:

```bash
source ~/.hermes/fleet.env
test -x "$HERMES_FLEET_BIN"
HERMES_HOME="$HOME/.hermes" hermes config get model.default
hermes -p <repo>-pm config get model.default
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-profile-config.py check
flume review --agent <repo>-pm
flume record
```

For daemon-backed agents, also check:

```bash
systemctl --user status hermes-<repo>-pm-gateway.service
systemctl --user status hermes-fleet-bloodbank-gateway.service
journalctl --user -u hermes-<repo>-pm-gateway.service -n 80 --no-pager
```

Use a bounded stabilization window rather than one `is-active` sample. Check
systemd `Result`, `ExecMainStatus`, and `NRestarts` repeatedly through the
deadline.

`flume review`'s verdict is three-way. `healthy` reads as in good standing,
`unhealthy` as on notice, and `unproven` as unable to assess — the last one means
the observation could not be trusted, so it is neither a pass nor a failure.
`health.proven` (verdict healthy AND fleet-complete) is what licenses a
whole-workforce claim.

Run the focused Hermes checks from the current test harness. If
`scripts/run_tests.sh ... -q` fails with an unrecognized `-q`, rerun without
`-q`; the wrapper now delegates to `run_tests_parallel.py`.

```bash
scripts/run_tests.sh tests/hermes_cli/test_config.py tests/hermes_cli/test_profiles.py
.venv/bin/python scripts/check-windows-footguns.py
```

## Pitfalls

- Do not copy `.env`, `auth.json`, sessions, memories, or gateway state between
  desks. Generated base-plus-delta config is not a security boundary.
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
- Do not patch Hermes runtime hooks by hand when the Bloodbank fan-out source can
  generate them.
- Do not drop an update stash until the generated-config tests and live smoke
  checks pass.
- Do not assume `scripts/check-windows-footguns.py` is executable; use
  `.venv/bin/python scripts/check-windows-footguns.py` if direct execution gets
  `permission denied`.
- Do not trust stale docs or success summaries over `~/.hermes/fleet.env`, live
  `.project.json`/registry/desk files, systemd state, and renderer checks.
