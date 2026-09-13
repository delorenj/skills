---
name: gitignore-maintenance
description: Simplify and reconcile a repository's Git ignore policy against the active system-wide core.excludesFile. Use when a repo .gitignore is bloated or redundant, applying personal global ignore rules, verifying backup and agent-tool exclusions, finding tracked files that now match ignore rules, untracking ignored backups/caches/runtime state/generated agent projections with git rm --cached while preserving local copies, or committing and pushing a gitignore parity cleanup. Do NOT use for broken refs, detached HEAD, or damaged worktree metadata; use unfuck-my-git-state instead.
---

# Gitignore Maintenance

Keep personal invariants in the machine-wide excludes file and keep only the
repository's own contract in `.gitignore`. Then reconcile the index explicitly:
an ignore rule affects untracked files, never files already in Git.

## Invariants

- Resolve the active global file; never assume or copy a hard-coded path:
  `git config --show-origin --path --get core.excludesFile`. When unset, Git's
  implicit default is `${XDG_CONFIG_HOME:-$HOME/.config}/git/ignore`.
- The global file owns things that are never source on this machine: backup
  variants, editor/OS debris, local credentials, common caches/runtime
  sidecars, and non-canonical agent-client projections.
- `.agents/` is canonical. Never ignore it wholesale. Generated leaves such as
  `.agents/skills/` may be ignored; `.claude/`, `.codex/`, and equivalent client
  projections belong in the global policy.
- A repo `.gitignore` owns project facts: generated output, runtime roots,
  vendored/generated trees, local datasets, and narrow exceptions needed by a
  fresh clone. Do not globalize `build/`, `dist/`, media, models, or other names
  that can be source in another repository.
- `.git/info/exclude` is only for clone-specific exceptions that should not be
  shared or made global.
- Never use `git clean`, `git reset --hard`, `rm`, or
  `git rm -r --cached .` for this workflow. Never temporarily remove
  `.gitignore`.

## Integration ownership

- **CommonProject/PJangler (new repos)** preserve existing `.gitignore` content
  and append only the portable repository contract. They never copy
  `core.excludesFile` or make client-specific agent roots canonical.
- **PJangler parity (structural upgrades)** may remove only exact legacy
  `.gitignore` lines it previously generated. It must not untrack files.
- **This skill (existing repos)** owns effective-rule provenance, repo
  simplification, reviewed index reconciliation, local-copy proof, and the
  commit/push handoff.
- **Skillex (distribution)** selects this skill in `sets/min-global`; projects
  consume the global projection and do not vendor another copy.

## 1. Preflight and audit

Read repository instructions first, then run from the target repository:

```bash
git status --short --branch
git diff --cached --name-status
git config --show-origin --path --get core.excludesFile
python3 "$SKILL_DIR/scripts/audit_gitignore.py" --repo .
```

Set `SKILL_DIR` to this skill's loaded directory if the harness did not provide
it. The audit is read-only. It reports:

- every tracked path currently matched by the effective ignore stack, with the
  winning source, line, and pattern;
- exact textual overlaps between repository `.gitignore` files and the global
  file. These are candidates, not automatic deletions: local ordering and
  negations can make an identical pattern meaningful.

Use the helper's `--json` output for automation or unusual filenames; never
split its human-readable path output on whitespace.

When the machine policy itself is in doubt, probe the user's minimum contract:

```bash
git check-ignore -v --no-index -- _probe.bak _probe.bk _probe.backup .claude/_probe .codex/_probe
git check-ignore -v --no-index -- .agents/_probe
```

Every path in the first command must name the global file as its winning
source. The second command must print nothing: canonical `.agents/` remains
visible. Fix or locate the global policy before removing any local fallback.

Stop before mutation when the index already contains unrelated staged changes,
or when an existing user edit overlaps a `.gitignore` or candidate path.
Checkpoint/isolate that work according to repository policy; never absorb it
into the parity commit.

## 2. Simplify `.gitignore`

Classify each non-comment rule before changing it:

1. **Personal invariant already global** — remove only when the global file
   demonstrably covers the same intended paths and local rule ordering is not
   changing the result.
2. **Project contract** — keep it. Prefer anchored, narrow rules such as
   `/var/` over vague cross-repository rules.
3. **Intentional tracked exception** — retain or add the narrowest `!path`
   exception. If a parent directory is excluded, unexclude the parent before
   the file.
4. **Unknown** — inspect the producer and repository docs. A filename alone is
   not evidence that an artifact is generated.

Use actual probes, including tracked paths:

```bash
git check-ignore -v --no-index -- path/to/probe
git status --short --ignored
```

Remember that `.bak` matches only a file literally named `.bak`; `*.bak`
matches backup suffixes. Do not broaden a rule merely to shorten the file.

## 3. Reconcile tracked files

Rerun the audit after simplifying. Review every `tracked_ignored` entry and put
it in exactly one bucket:

- **Untrack** — clear backup, cache, runtime state, generated output, or
  non-canonical projection whose canonical source is known.
- **Keep tracked** — intentional source/configuration. Add a narrow negation,
  then verify it disappears from the audit.
- **Investigate** — ambiguous ownership or provenance. Do not mutate it yet.

For the reviewed untrack bucket, use explicit paths only:

```bash
git rm --cached -- path/one path/two
```

`--cached` removes index entries and leaves working copies in place. Record
which candidates existed before the command, then verify those same paths still
exist. If Git requests `-f`, stop and understand the staged/index mismatch;
never add force reflexively.

A tracked credential requires more than parity: move the value to the approved
secret store, replace it with a safe reference/template, rotate it when
appropriate, and treat history cleanup as a separate explicitly authorized
operation. Untracking alone does not erase history.

## 4. Verify, commit, push, and restore

The staged diff must contain only the `.gitignore` edits and reviewed index
deletions:

```bash
git diff --cached --name-status
git diff --cached --check
python3 "$SKILL_DIR/scripts/audit_gitignore.py" --repo .
git ls-files --error-unmatch .gitignore
```

The second audit should contain no unexplained `tracked_ignored` paths. Confirm
each formerly tracked working copy that existed at preflight still exists and
is now ignored with `git check-ignore -v --no-index`.

Commit and push when the request or repository policy calls for parity
publication:

```bash
git commit -m "chore(git): align repository with global ignore policy"
git push
git rev-list --count '@{upstream}..HEAD'
```

The final count must be `0`. If there is no branch, remote, or upstream, report
that concrete blocker instead of inventing a publication target.

There is normally nothing to restore: `git rm --cached` preserved every working
copy and `.gitignore` never moved. If a pre-existing/legacy cleanup physically
removed a file, restore only a path proven present at preflight, from the saved
pre-cleanup commit, after it is untracked and ignored. Never restore a plaintext
credential.

## Completion evidence

Report the resolved global ignore source, removed repo-rule categories,
untracked paths, intentional exceptions, validation results, commit ID, push
destination, and any ambiguous paths left untouched.
