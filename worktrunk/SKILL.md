---
name: worktrunk
description: How to use worktrunk (`wt`), the installed CLI for git worktree management built for parallel AI agents. Use when creating, switching, listing, rebasing, merging, or removing git worktrees; when running parallel agents that must not share a working directory; when a task needs isolation from a dirty or shared checkout; or when `wt` commands, hooks, or config need debugging. Covers the command surface, agent-specific invocation patterns, and the fleet-standard config. Policy (WHEN/WHERE/MAINTAIN) lives in the 33GOD `worktrees` skill — this skill is the HOW.
---

# Worktrunk (`wt`) — operator's guide

Worktrunk makes git worktrees as easy as branches. Worktrees are addressed by **branch name**; paths come from a configurable template. Docs: https://worktrunk.dev (machine-readable: https://worktrunk.dev/llms.txt).

## Install state (this machine)

- Binary: `~/.local/bin/wt` (also `git-wt`, so `git wt …` works). Verify: `wt --version`.
- User config: `~/.config/worktrunk/config.toml` — sets the fleet-standard path template (below).
- Shell integration: installed via `wt config shell install`. It lets interactive shells `cd` on `wt switch`. **Agent tool shells are non-interactive and fresh per call — see "Agent invocation patterns".**
- Upgrade: `cargo-binstall -y --root ~/.local worktrunk` (prebuilt; system cargo is too old to compile it).

## The path template is already set fleet-wide

`~/.config/worktrunk/config.toml` contains:

```toml
worktree-path = "{{ repo_path }}/.worktrees/{{ branch | sanitize }}"
```

Every `wt switch --create` lands the worktree at `<repo>/.worktrees/<branch>` (slashes in branch names become `-`). Do not override this per-repo. `.worktrees/` is in the machine-wide gitignore (`~/.config/git/ignore`), so worktrees never dirty `git status`.

## Core loop

```bash
wt switch -c feature-auth        # create branch + worktree, from default branch
wt switch -c fix -b develop      # create from a different base
wt list                          # status table: changes, ahead/behind main, unpushed
wt list --format json            # machine-readable, for scripting
# …work, commit, push…
wt merge main                    # commit → squash → rebase → push → cleanup, one command
```

`wt merge` fast-forwards the target branch, switches you back to the main worktree, and removes the feature worktree + branch in the background. This is the default way to land work.

Target/branch arguments accept shortcuts everywhere: `^` (default branch), `-` (previous), `@` (current), `pr:123` / `mr:123` (check out a PR/MR).

## Individual steps (`wt step`)

`wt merge` is these composed. Use the pieces when you want control:

| Command | Does |
|---|---|
| `wt step rebase [target]` | Rebase current branch onto target (default: default branch). **The maintenance command.** |
| `wt step commit` / `squash` | Commit / squash with LLM-generated message (needs `[commit.generation]` configured; not set fleet-wide — write your own commits instead) |
| `wt step diff` | All changes since branching (committed + staged + unstaged + untracked) |
| `wt step push [target]` | Fast-forward target branch to current branch |
| `wt step for-each <cmd>` | Run a command in every worktree (e.g. fleet-wide rebase) |
| `wt step prune` | Remove worktrees + branches already merged into the default branch |
| `wt step copy-ignored` | Copy gitignored files (.env, build caches) between worktrees |

## Removal

```bash
wt remove              # current worktree; deletes branch if merged
wt remove <branch> -y  # specific worktree, no prompt
wt step prune          # bulk-remove everything already merged
```

`wt remove` refuses to destroy unmerged work by default — land or deliberately discard first.

## Parallel agents

```bash
wt switch -x claude -c feature-a -- 'Add user authentication'
wt switch -x claude -c feature-b -- 'Fix the pagination bug'
```

`-x <program>` runs a program in the new worktree after switching; args after `--` go to it verbatim. One worktree per agent per task, always.

## Agent invocation patterns (read this before scripting `wt`)

- **Fresh shell per tool call.** `wt switch` cannot `cd` your next Bash call. Either `cd <repo>/.worktrees/<branch>` explicitly, use the global `-C <path>` flag (`wt -C <path> list`), or run the work via `wt switch <branch> -x <cmd>`.
- **Non-interactive:** pass `-y` to skip approval prompts (`wt remove -y`, `wt switch -c foo -y`).
- **Discover worktree paths** with `wt list --format json`, never by hardcoding — the template owns layout.
- **`wt step commit`/`squash`/`merge` with uncommitted changes try LLM commit messages**, which need `[commit.generation]` in user config (unset on this fleet). Commit your own work first, then `wt merge` runs clean.
- Logs for a misbehaving command: `-v` (info) or `-vv` (debug + subprocess logs in `.git/wt/logs/`).

## Project hooks (optional, per-repo)

A repo may carry a committed `.config/wt.toml` with hooks (`pre-start`, `pre-merge`, `post-merge`, …) — e.g. `pre-start: deps = "mise install"`. Check for one before assuming setup steps; run hooks manually with `wt hook <name>`. Create the file with `wt config create --project`.

## Config cheat sheet

| File | Scope | Committed |
|---|---|---|
| `~/.config/worktrunk/config.toml` | user: path template, LLM, list defaults | no |
| `.config/wt.toml` | project: hooks, dev-server URL | yes |

Inspect effective config and file locations with `wt config show`.
