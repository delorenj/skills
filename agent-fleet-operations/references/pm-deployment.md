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

## Seal the before-state

Before invoking the deployer, capture enough state to prove what it changed:

- target repository root, branch, HEAD, and `git status --short`, including
  nested repositories and submodules;
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

Record hashes or targeted diffs for shared files when practical. Never print
credential values. Preserve dirty work exactly as found: do not reset, clean,
stash, rewrite, or absorb changes in the target repository or any nested
repository merely to make provisioning easier.

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
- The registry and `.project.json` agree on repo, board, agent id, role, and
  `profile_name`.

## Service state is conditional

Heartbeat/reconciliation and chat ingress are independent:

- The heartbeat timer is the PM's sentinel/reconciliation scheduler. It should
  be enabled and active; its oneshot service may be inactive between ticks, but
  the most recent invocation must have succeeded.
- A per-agent gateway is healthy only when the agent has its own chat-channel
  credential and the service is enabled and active without restart churn.
- If no channel credential was supplied, provisioning must explicitly defer
  chat ingress and leave `hermes-<agent-id>-gateway.service` disabled and
  inactive. Missing credentials must never produce an enabled crash loop, and
  a deferred gateway must not be reported as a healthy chat channel.
- The fleet-shared Bloodbank gateway is not part of per-agent provisioning. Its
  unit file, state, and config must remain unchanged.

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

The deployment is complete only when all of these assertions hold:

| Surface | Required postcondition |
|---|---|
| Target and nested repos | pre-existing dirty state preserved; no generated runtime tracked |
| Project identity | `.project.json` has one correct PM entry and board binding |
| Fleet registry | one matching row with the same agent/profile/project identity |
| Profile | real directory; generated config + real delta + metadata + explicit memory pin |
| Gateway | credentialed: enabled/active; uncredentialed: explicitly deferred, disabled/inactive |
| Heartbeat | timer enabled/active; latest service run successful |
| Shared gateway | file/config/enabled/active state unchanged |
| Rerun | no duplicate entries, retired units, new tracked dirt, or stable-state drift |

If a required deployment skill is absent, repair its Skillex manifest/projection
and validate `~/.agents/skills/<name>/SKILL.md`. Do not fabricate a placeholder
or let the deployer mark the step complete after only warning.
