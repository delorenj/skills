---
pipeline-status:
  - new
---
# Project creation via PJangler

PJangler owns project identity: the repository skeleton, the one ticket board,
and the canonical repo-root `.project.json`. Use its installed `pj` entry point
rather than invoking Copier, template scripts, or systemd directly. Who works in
the repository is Flume's record, not pjangler's — see step 2.

## 1. Bootstrap the repository

```bash
pj init --apply
# adopt the repo you are standing in; `pj init <name>` creates ./<name>
```

`--apply` (or `-y`) is what writes; a bare `pj init` is a dry run. The board is
created by default — `--skip-board` leaves the record unlinked and says so, and
`--live` is only for host-level effects such as systemd and notebook reconcile.

The resulting `.project.json` owns:

- `project_name`, `project_slug`, description, and absolute `repo_path`;
- the single `ticket_provider` binding (provider, workspace, identifier,
  board id, and state);
- an `agents` map that is a **one-way projection** of the org chart in
  `~/.hermes/agents-registry.yaml`. `pj init` carries forward whatever is
  already there and authors nothing; the handbook declares the projection
  (`agent_role_directory`, `writable_by: project-registry`).

There is no separate `.plane.json`, no role-suffixed PM board, and no board
identity inferred from a summary line. A valid Plane binding has `state:
linked` and a live-resolved identifier/board id. Never persist
`ticket_provider.board_url`; construct a URL transiently when presenting it.

CommonProject never copies the developer's global Git ignore. It preserves any
existing `.gitignore` and adds only the portable repository contract: `.env`,
`.env.*`, the committed `.env.op` exception, `.agents/local.json`, and the
generated `.agents/skills` projection. Backup/editor artifacts and client roots
such as `.claude/` and `.codex/` remain machine-wide policy; `.agents/` is the
only canonical agent-config tree committed by the project.

For an existing repository, run `gitignore-maintenance` after structural
bootstrap. Its effective-ignore audit distinguishes repo rules from the global
source and lists tracked matches with provenance. Review those paths before the
skill performs any explicit `git rm --cached`, commit, and push; pjangler itself
does not mutate the index.

Read and parse the raw manifest before mutation. Malformed JSON aborts with the
manifest and all other state byte-unchanged. Hold one project lock across
read/validation, the live Plane check-or-create, and atomic manifest
replacement so concurrent deploys cannot create or publish split identity.

## 2. Hire the PM

```bash
cd <repo>
flume hire pm
```

The PM is the only role the standard project deployment asks for. Flume renders
`agents/hermes/pm/` from its own version-locked template, creates the real named
profile, writes the org-chart row, and binds the agent to the board already
recorded in `.project.json` — it must not create a second board. `flume onboard
pm` is the convergent rerun.

Everything about that command — the abort gates, the before/after seal, the
profile and credential contract, the one per-agent unit, and the convergence
proof — is **agent-fleet-operations** `references/pm-deployment.md`. Do not
reconstruct it here; it is a contract with a machine-readable form
(`pm-deployment-contract.json`) and this file would drift from it.

The project side owes the hire three things and nothing else: valid
`.project.json` bytes, a `ticket_provider` whose state is `linked` with a
live-resolving identifier/board id, and a sealed working tree. Preserve dirty
work exactly; do not reset, clean, stash, rewrite, or convert repo-local runtime
into a tracked submodule.

## 3. What the repository must still be true about afterwards

The one deployment artifact that lands *in the repo* is the role directory, and
its runtime subtree is ignored, untracked local state — not a profile, submodule
or nested repository. Prove both halves:

```bash
git check-ignore -q -- agents/hermes/pm/runtime/
git ls-files -- agents/hermes/pm/runtime/  # stdout must be empty
```

`flume audit` owns this invariant (`hermes.untracked-runtimes`,
`hermes.runtime-singleton`); `pj audit` no longer knows those rule ids and errors
if asked for one. A green aggregate audit is not proof of a healthy deployment —
compare `.project.json` against the single matching `~/.hermes/agents-registry.yaml`
row directly, and run `flume review` for the workforce verdict.
