# Clean PM deployment contract

Use this contract for the first deployment into a repository and for every
rerun. The supported entry point is:

```bash
cd <repo>
pj hermes-agent --yes
```

Do not replace the command with hand-rendering, a template install script, or
manual systemd/profile edits. A successful command summary is a claim to
verify, not proof of a healthy deployment.

The machine-readable normative assertions are in
[pm-deployment-contract.json](pm-deployment-contract.json). Configuration may
add optional skills or stricter checks, but may not weaken that contract.

## Abort gates before mutation

Only read-only inspection may precede these gates:

1. Read and hash the raw `.project.json`, then parse it. Malformed JSON aborts
   the deployment with `.project.json` and every other surface byte-unchanged.
2. Inspect the expected profile path with link-aware metadata. If it is a
   legacy symlink, abort before rendering, unlinking, migrating, or writing
   anything; a separate explicitly authorized migration must resolve it.

## Seal the before-state

Before invoking the deployer, capture enough state to prove what it changed:

- target repository root, branch, HEAD, and porcelain status including all
  untracked paths;
- hashes of the unstaged binary diff, staged binary diff/index listing, and a
  path/type/mode/content manifest for **every** dirty or untracked file (hash a
  symlink's target text rather than following it);
- every nested Git repository and submodule's HEAD, index listing/hash, full
  status, dirty-content hashes, and untracked-content hashes;
- repo-root `.project.json`, especially `repo_path`, ticket-provider binding,
  and existing agent entries;
- the matching row (or confirmed absence) in
  `~/.hermes/agents-registry.yaml`;
- the expected named profile path and whether its `config.yaml`,
  `config.delta.yaml`, `profile.yaml`, and `hindsight/config.json` exist;
- exact user-unit file, enabled, active, failed, and restart states for the
  target gateway and heartbeat timer/service;
- the enabled/active state and unit-file identity of the fleet-shared
  `hermes-fleet-bloodbank-gateway.service`.

These hashes are mandatory before **and** after every run, not best-effort
diagnostics. Never print credential values. Preserve dirty work exactly as
found: do not reset, clean, stash, rewrite, or absorb changes in the target
repository or any nested repository merely to make provisioning easier.

## Expected materialized state

- `~/.hermes/profiles/<agent-id>/` is a **real named directory**, not a symlink
  to repo-local runtime state.
- `<profile>/config.yaml` is a generated deep merge of the shared fleet base
  and the real, override-only `<profile>/config.delta.yaml`. Edit the delta and
  render; never hand-edit the generated file.
- `<profile>/profile.yaml` is identity metadata, not a native inheritance
  mechanism. Hermes does not interpret `config.inherit_from` there.
- `<profile>/hindsight/config.json` explicitly pins the identity-memory bank
  for that profile (normally `agent-<agent-id>`).
- Repo-local `agents/hermes/pm/runtime/` is ignored, untracked local state. It
  may be the target of explicit owned-state links, but it is not the profile
  directory, a submodule, or a nested Git repository.
- Prove runtime exclusion with **both** checks; an ignore rule alone cannot
  untrack a path:

  ```bash
  git check-ignore -q -- agents/hermes/pm/runtime/
  git ls-files -- agents/hermes/pm/runtime/  # stdout must be empty
  ```
- The registry and `.project.json` agree on repo, board, agent id, role, and
  `profile_name`. A Plane binding is valid only when
  `ticket_provider.state` is `linked`, its identifier and board id resolve
  against the live Plane project, and `.project.json` does **not** persist
  `ticket_provider.board_url`; derive URLs transiently from live configuration.
- Hold one project-scoped lock across manifest read, validation, live Plane
  check-or-create, and write. Replace `.project.json` atomically; never expose a
  truncated or partially updated manifest.

## Required skill core

Every PM must resolve this exact immutable core to regular
`~/.agents/skills/<name>/SKILL.md` files:

1. `33god-projects`
2. `delonet-conventions`
3. `delonet-dotenv`
4. `hermes-pm-template-maintenance`
5. `hindsight`
6. `subagent-driven-development`

Configuration may append optional skills but must never subtract, rename, or
replace a core member. A missing core member is a hard failure, never a warning
followed by a completion marker.

## Service state is conditional

Heartbeat/reconciliation and chat ingress are independent:

- The heartbeat timer is the PM's sentinel/reconciliation scheduler. It should
  be enabled and active; its oneshot service may be inactive between ticks, but
  the most recent invocation must have succeeded.
- A per-agent gateway is healthy only when the agent has its own verified
  chat-channel credential and the service is enabled and stable without
  restart churn.
- If no channel credential was supplied, provisioning must explicitly defer
  chat ingress and leave `hermes-<agent-id>-gateway.service` disabled and
  inactive. Missing credentials must never produce an enabled crash loop, and
  a deferred gateway must not be reported as a healthy chat channel.
- Deferred Telegram or Slack must also override any fleet-base enablement in
  the profile delta:

  ```yaml
  platforms:
    telegram:
      enabled: false
    slack:
      enabled: false
  ```

  Only verified ownership of that agent's dedicated credential may flip the
  corresponding value to `true`.
- The fleet-shared Bloodbank gateway is not part of per-agent provisioning. Its
  unit file, state, and config must remain unchanged.

Service success requires a bounded stabilization window, not one
`is-active` sample. Through the deadline, inspect systemd `Result`,
`ExecMainStatus`, and `NRestarts`; require success/zero and no restart growth.
Also wait for and verify the latest heartbeat service result while confirming
the timer remains enabled/active. A deferred gateway is judged by its required
disabled/inactive state, not by forcing it active for the probe.

There is no per-agent Bloodbank consumer, checkpoint timer, or filesystem
inbox. Their presence is drift.

## Credential boundary

`~/.hermes/.env` may contain nonsecret feature flags, paths, and endpoints, but
must not contain literal API keys, bot tokens, passwords, or service-account
tokens. Hermes v0.20.1+ can resolve `secrets.onepassword.env` mappings at
startup. The safe migration is:

1. import each credential into the `DeLoSecrets` vault;
2. map the environment variable to its `op://DeLoSecrets/<item>/<field>`
   reference in the shared or profile delta config;
3. render affected profiles and remove the literal from `.env`;
4. verify `hermes secrets onepassword status` and dry-run `sync` without
   printing values;
5. restart only the explicitly in-scope processes and verify their environment
   contains the variable name while logs/output do not expose its value.

Do not migrate or display a live secret as an incidental part of a deployment.
That is a separate, approval-gated operation. The 1Password authentication
credential itself must likewise come from the existing secret manager/runtime
injection path, never a newly written plaintext file.

Secret **values** may enter a validation command only through a pipe, anonymous
file descriptor, or the validating process's memory. Never put one in curl
arguments or export it to unrelated child processes. A transient 1Password
validation failure must preserve the previously valid `op://` reference and
its success marker; it must not write a failed candidate or erase known-good
state. A later healthy rerun must retry and converge without manual cleanup.

## Git and cleanup transactions

Normal commits, releases, and pushes must run both repository and global Git
hooks. Never use `--no-verify`, `GIT_GUARD_OFF`, or an equivalent bypass to
land deployment work.

Tracked backup cleanup uses the actual globs `*.bak`, `*.bak-*`, `*.orig`,
`*~`, and `*-backup.*` (not `.bak`). An ignore rule does not untrack an indexed
file: use a scoped `git rm --cached`/equivalent untracking transaction, commit
and push it, then verify the backup is absent with `git ls-tree` against the
remote branch. Do not delete or rewrite unrelated dirty runtime state while
cleaning tracked backups.

## Verify and prove convergence

After the command, directly re-read `.project.json`, the registry row, profile
files, and systemd state. Run the applicable read-only `pj audit` and renderer
`check`, but treat their summaries as aggregate claims: the specific
repo/profile/service evidence above still has to agree.

Then rerun `pj hermes-agent --yes`. The second run must not duplicate registry
or project entries, replace a real profile with a symlink, dirty tracked repo
content, enable a credential-less gateway, alter the shared fleet gateway, or
create retired units. Stable files should be byte-identical except for
documented runtime timestamps/logs.

With unchanged inputs, the fleet registry must be byte-identical across the
rerun. In particular, preserve the original `provisioned_at` and every
extension/unknown metadata field; merge owned keys rather than reconstructing
the row.

The deployment is complete only when all of these assertions hold:

| Surface | Required postcondition |
|---|---|
| Target and nested repos | mandatory dirty/untracked hashes match; every nested HEAD/index/status preserved; both runtime exclusion checks pass |
| Project identity | atomic `.project.json`; one PM; live Plane identifier/id; `state: linked`; no persisted `board_url` |
| Fleet registry | one matching row; rerun byte-identical; `provisioned_at` and extension metadata preserved |
| Profile | real directory; generated config + real delta + metadata + explicit memory pin |
| Skills | immutable six-skill core present; optional additions do not subtract it |
| Gateway | delta explicitly disables unverified channels; verified channel is stable across the bounded window |
| Heartbeat | timer enabled/active; latest service run successful within the bounded window |
| Shared gateway | file/config/enabled/active state unchanged |
| Rerun | no duplicate entries, retired units, new tracked dirt, or stable-state drift |

If a required deployment skill is absent, repair its Skillex manifest/projection
and validate `~/.agents/skills/<name>/SKILL.md`. Do not fabricate a placeholder
or let the deployer mark the step complete after only warning.
