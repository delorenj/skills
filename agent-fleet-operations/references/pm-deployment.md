# Clean PM deployment contract

Use this contract for the first hire into a repository and for every rerun. The
supported entry point is:

```bash
cd <repo>
flume hire pm --yes
```

Do not replace the command with hand-rendering, a template install script, or
manual systemd/profile edits. A successful command summary is a claim to
verify, not proof of a healthy deployment.

The convergent rerun is meant to be `flume onboard pm`. Onboarding *is* hiring
run again: every step is marker-guarded and the registry write is an upsert.
`--force` is deliberately not offered on `onboard`, because onboarding an employee
must never become a way to overwrite one. In the current build, though, hire
refuses a non-empty role dir, so `onboard` stops at "Hermes target directory is
not empty" on every deployed employee. Until that is fixed, converge a deployed
employee with its own steps from the role dir: `30-telegram.sh` (with
`SKIP_TELEGRAM=1` to record the channel as deferred), `70-systemd.sh` and
`80-registry.sh`. Refresh the role's scripts first (`flume remediate
hermes.pm-scaffold <repo> --scripts-only`): an 80-registry.sh older than
template 5ee1909 writes `systemd.gateway_state`/`heartbeat_state`, which the
handbook retires. `80-registry.sh` rewrites the whole registry through
`yaml.safe_dump`; see SKILL.md for the one-row alternative, which copies only
handbook-declared fields, never the simulated row verbatim.

The machine-readable normative assertions are in
[pm-deployment-contract.json](pm-deployment-contract.json). Configuration may
add optional skills or stricter checks, but may not weaken that contract.

## Abort gates before mutation

Only read-only inspection may precede these gates:

1. Read and hash the raw `.project.json`, then parse it. Malformed JSON aborts
   the deployment with `.project.json` and every other surface byte-unchanged.
2. Inspect the expected desk path with link-aware metadata. If it is a legacy
   profile symlink, abort before rendering, unlinking, migrating, or writing
   anything; a separate explicitly authorized migration
   (`flume remediate hermes.runtime-singleton`) must resolve it.

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
- the expected named desk path and whether its `config.yaml`,
  `config.delta.yaml`, `profile.yaml`, and `hindsight/config.json` exist;
- exact user-unit file, enabled, active, failed, and restart states for
  `hermes-<agent-id>-gateway.service`;
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
  and the real, override-only `<profile>/config.delta.yaml`, and carries the
  renderer's generated-header marker. Edit the delta and render; never
  hand-edit the generated file and never symlink it — it detaches on the first
  Hermes write.
- `<profile>/config.delta.yaml` exists as a real file even when empty. Absent
  means "not under base-plus-delta inheritance", which is a failure; empty means
  "no overrides", which is fine.
- `<profile>/profile.yaml` is identity metadata, not a native inheritance
  mechanism. Hermes does not interpret `config.inherit_from` there.
- `<profile>/hindsight/config.json` explicitly pins the identity-memory bank
  for that desk (normally `agent-<agent-id>`).
- Repo-local `agents/hermes/pm/runtime/` is ignored, untracked local state. It
  may be the target of explicit owned-state links, but it is not the desk
  directory, a submodule, or a nested Git repository.
- Prove runtime exclusion with **both** checks; an ignore rule alone cannot
  untrack a path:

  ```bash
  git check-ignore -q -- agents/hermes/pm/runtime/
  git ls-files -- agents/hermes/pm/runtime/  # stdout must be empty
  ```
- The registry row and `.project.json` agree on repo, board, agent id, role, and
  `profile_name`, and the row advertises
  `bloodbank: {enabled, gateway_scope: fleet, target_agent_id: <agent-id>}`
  (an absent `enabled` means enabled; only an explicit `false` quarantines). A
  Plane binding is valid only when `ticket_provider.state` is `linked`, its
  identifier and board id resolve against the live Plane project, and
  `.project.json` does **not** persist `ticket_provider.board_url`; derive URLs
  transiently from live configuration.
- Hold one project-scoped lock across manifest read, validation, live Plane
  check-or-create, and write. Replace `.project.json` atomically; never expose a
  truncated or partially updated manifest.
- Profile config writers follow the separate shared lock/order and exact
  replacement contract in
  [config-mutation-safety.md](config-mutation-safety.md). Initial deployment is
  a writer: its existence check and empty-delta seed must occur under that same
  profile lock.

## Required skill core

The core is **pinned by the host config**, not by this document:

```bash
sed -n '/^symlinked_runtime_skills/,/^]/p' ~/.config/hermes-agent-template/config.toml
```

Read that list, then prove every member resolves to a regular
`~/.agents/skills/<name>/SKILL.md`. The pinned name is the *directory* under
`~/.agents/skills/`, which is not always the skill's frontmatter `name:` —
`33god-projects` ships in the `projects/` directory, so check the path that is
actually pinned.

Configuration may append optional skills but must never subtract, rename, or
replace a pinned member. A missing member is a hard failure, never a warning
followed by a completion marker. `flume audit --rules hermes.runtime-singleton`
proves the desk's Skillex projection; it does not substitute for reading the pin.

## Service state is conditional

Per agent there is exactly one unit: `hermes-<agent-id>-gateway.service`, chat
ingress. Per-agent heartbeat timers are retired and provisioning removes any it
finds, recording `service_state.heartbeat: retired`. Liveness is the gateway's
own `Restart=on-failure`; scheduling is Bloodbank; persistence is krebs leases.
A heartbeat timer, a per-agent Bloodbank consumer, a checkpoint timer, or a
filesystem inbox is drift.

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
A deferred gateway is judged by its required disabled/inactive state, not by
forcing it active for the probe.

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

For leak eradication or history cleanup, follow
[secret-migration.md](secret-migration.md). Current files, a clean branch tip,
or a normal `git log` scan do not cover databases/caches, the index, reflogs,
unreachable local objects, or pushed reachable history. Rotation/retirement and
private-remote force rewriting require explicit authorization.

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
files, and systemd state. `flume hire` already runs its own postcondition pass —
the eight employee rules, plus a `pj audit --rules mise.config-root,sot.project-json
--json` probe for the two project contracts it changes or depends on. A probe
that cannot reach `pj` reports **unable to assess**, is surfaced, and does not
fail the hire; treat that as an unread surface you still owe evidence for.

Run the applicable read-only checks yourself:

```bash
flume audit --json                 # the eight employee rules for this repo
flume review --agent <agent-id>    # nine observation domains, read-only
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-profile-config.py check
```

Treat their summaries as aggregate claims: the specific repo/profile/service
evidence above still has to agree. A `flume review` verdict of `unproven`
("unable to assess") is not a pass.

Then rerun `flume onboard pm` (or, on a deployed employee, the 30/70/80 steps
above). The second run must not duplicate registry or
project entries, replace a real desk with a symlink, dirty tracked repo content,
enable a credential-less gateway, alter the shared fleet gateway, or create
retired units. Stable files should be byte-identical except for documented
runtime timestamps/logs.

With unchanged inputs, the registry must be byte-identical across the rerun. In
particular, preserve the original `provisioned_at` and every extension/unknown
metadata field; merge owned keys rather than reconstructing the row.

The deployment is complete only when all of these assertions hold:

| Surface | Required postcondition |
|---|---|
| Target and nested repos | mandatory dirty/untracked hashes match; every nested HEAD/index/status preserved; both runtime exclusion checks pass |
| Project identity | atomic `.project.json`; one PM; live Plane identifier/id; `state: linked`; no persisted `board_url` |
| Org chart | one matching row with the `bloodbank` block; rerun byte-identical; `provisioned_at` and extension metadata preserved |
| Desk | real directory; generated config with render marker + real delta + identity metadata + explicit memory pin |
| Skills | every `symlinked_runtime_skills` member resolves; optional additions do not subtract one |
| Gateway | delta explicitly disables unverified channels; verified channel is stable across the bounded window |
| Retired units | no `hermes-<agent>-heartbeat.*`, `-consumer.service`, or `-checkpoint.timer` exists |
| Shared gateway | file/config/enabled/active state unchanged |
| Rerun | no duplicate entries, retired units, new tracked dirt, or stable-state drift |

If a required deployment skill is absent, repair its Skillex manifest/projection
and validate `~/.agents/skills/<name>/SKILL.md`. Do not fabricate a placeholder
or let the deployer mark the step complete after only warning.
