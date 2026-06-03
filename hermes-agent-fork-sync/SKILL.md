---
name: hermes-agent-fork-sync
description: Sync delorenj/hermes-agent fork with NousResearch/hermes-agent upstream while preserving fork-only paths, the agents/hermes/pm/runtime submodule, and the 3 fork-side code tweaks. Use when running /hermes-sync, when the user says "sync the fork", or when you need to pull in upstream hermes-agent commits without losing local customization.
---

# Hermes-Agent Fork Sync Skill

Procedure for syncing the **delorenj/hermes-agent** fork with **NousResearch/hermes-agent** upstream, capturing every gotcha encountered the first time we did this (May 2026, 828-commit catch-up).

## When to Use

- User says "sync the hermes-agent fork" or runs `/hermes-sync`
- After upstream releases (`NousResearch/hermes-agent` ships a new version)
- Before starting fork-side work that needs recent upstream features
- Periodically (recommend monthly) to keep divergence manageable

## Prerequisites

- Working directory: `~/code/hermes-agent`
- `origin` = `git@github.com:delorenj/hermes-agent.git`
- `upstream` = `git@github.com:NousResearch/hermes-agent.git` (add via `git remote add upstream …` if missing)
- `gh` CLI authenticated for `delorenj/hermes-agent`
- Submodule `agents/hermes/pm/runtime` checked out (it's at `git@github.com:delorenj/agent-hm-hermes-agent-pm.git`)

## The Fork-Only Inventory

These 12 top-level paths exist only in the fork and **must survive every sync**:

```
.agents/         Codex CLI's bundled skill system (imagegen, openai-docs,
                 plugin-creator, skill-creator, skill-installer)
.claude/         Claude Code project settings (settings.json)
.codex/          Codex CLI project state (installation id, logs db, skills)
.copier-answers.yml   Copier template state
.env.op          1Password env reference file (op:// references)
.gitmodules      Submodule definition for agents/hermes/pm/runtime
.mise/           mise task scripts and setup
.project.json    Project marker
CLAUDE.md        Claude Code instructions (DeLoNET conventions, paths)
GEMINI.md        Gemini instructions
agents/          DeLoNet PM agent home (with hermes/pm/runtime submodule)
mise.toml        mise tool config
```

Verify the inventory before each sync (upstream may add a path with the same name):

```bash
comm -23 \
  <(git ls-tree HEAD | awk '{print $NF}' | sort) \
  <(git ls-tree upstream/main | awk '{print $NF}' | sort)
```

## The 3 Fork-Side Code Tweaks

These are the only real code changes the fork has ever made. They **must be re-applied** if the relevant upstream files have changed.

### 1. `tools/transcription_tools.py`

In `_get_local_command_template()` (around line 156), insert dotenv loading before the `if configured: return configured` check:

```python
def _get_local_command_template() -> Optional[str]:
    configured = os.getenv(LOCAL_STT_COMMAND_ENV, "").strip()
    if not configured:
        try:
            from hermes_cli.env_loader import load_hermes_dotenv
            load_hermes_dotenv(hermes_home=get_hermes_home())
            configured = os.getenv(LOCAL_STT_COMMAND_ENV, "").strip()
        except Exception:
            configured = os.getenv(LOCAL_STT_COMMAND_ENV, "").strip()
    if configured:
        return configured
```

**Also add the import at the top of the file** (upstream's version does NOT import this):

```python
from hermes_constants import get_hermes_home
```

### 2. `tools/voice_mode.py`

In `check_voice_requirements()` (around line 1072), add a `local_command` branch between `local` and `groq`:

```python
elif stt_provider == "local":
    details_parts.append("STT provider: OK (local faster-whisper)")
elif stt_provider == "local_command":
    details_parts.append("STT provider: OK (custom local command)")
elif stt_provider == "groq":
    ...
```

### 3. `.gitignore`

Append (do NOT replace) these patterns after upstream's gitignore:

```
# Fork-only additions (delorenj/hermes-agent)
**/.claude/settings.local.json
*.mp4
*.mp3
*.zip
*.aab
.lastagent

# Codex runtime/state (committed accidentally in earlier auto-checkpoints,
# de-tracked separately when convenient)
.codex/tmp/
.codex/*.sqlite-shm
.codex/*.sqlite-wal
.codex/goals_*.sqlite
```

## Procedure

### Step 0 — Pre-flight

```bash
cd ~/code/hermes-agent
git fetch upstream
git fetch origin
git status   # confirm clean (or expect stash step to handle uncommitted)
```

### Step 1 — Inspect the divergence

```bash
# How far behind?
git log --oneline origin/main..upstream/main | wc -l

# Fork-only commits to evaluate
git log --oneline upstream/main..origin/main

# Fork-side file changes since divergence (ignore upstream evolution)
MERGE_BASE=$(git merge-base HEAD upstream/main)
git diff --name-status "$MERGE_BASE" HEAD | grep -E "^M\s"
```

**If a Modified (M) line appears for a file other than the 3 known tweaks and `package-lock.json`, STOP and inspect it** — there may be new fork-side intent that needs to be re-applied.

### Step 2 — Stash uncommitted work

```bash
SYNC_DATE=$(date +%Y-%m-%d)
git stash push -u -m "pre-sync-${SYNC_DATE}: PM/skill/codex"
```

Note submodule pointer (stash does NOT capture submodule HEAD):

```bash
git submodule status > /tmp/hermes-submodule-pre-sync.txt
```

### Step 3 — Create sync branch from upstream/main

```bash
git checkout -b "sync/upstream-${SYNC_DATE}" upstream/main
git branch --unset-upstream "sync/upstream-${SYNC_DATE}"   # CRITICAL — see gotcha #1
```

### Step 4 — Restore fork-only paths from main

```bash
git checkout main -- \
  .agents .claude .codex .copier-answers.yml .env.op \
  .gitmodules .mise .project.json \
  CLAUDE.md GEMINI.md agents mise.toml

git commit -m "chore(fork): preserve fork-only customization layer on top of upstream"
```

### Step 5 — Re-apply the 3 fork tweaks

For each of the 3 tweaks, **check whether upstream already has the change** before re-applying (upstream may have adopted it independently):

```bash
grep -n "load_hermes_dotenv" tools/transcription_tools.py  # tweak #1
grep -n "local_command" tools/voice_mode.py                # tweak #2
grep -n "\.lastagent" .gitignore                           # tweak #3
```

Then apply each missing tweak per the patterns above. Syntax-check Python:

```bash
python3 -c "import ast; ast.parse(open('tools/transcription_tools.py').read())"
python3 -c "import ast; ast.parse(open('tools/voice_mode.py').read())"
```

Commit:

```bash
git add tools/transcription_tools.py tools/voice_mode.py .gitignore
git commit -m "chore(fork): re-apply fork-side tweaks on top of upstream"
```

### Step 6 — Restore stash

```bash
git stash pop
```

The submodule pointer modification (if any) will reappear here — that's the user's pending bump. Leave it for them to commit deliberately.

### Step 7 — Push and PR

```bash
git push -u origin "sync/upstream-${SYNC_DATE}"

gh pr create --repo delorenj/hermes-agent \
  --base main \
  --head "sync/upstream-${SYNC_DATE}" \
  --title "sync: NousResearch/hermes-agent → fork (N upstream commits)" \
  --body "..."   # see PR body template below
```

**CRITICAL: pass `--repo delorenj/hermes-agent` explicitly** — see gotcha #2.

### Step 8 — Merge instructions (in PR body)

Because main is rewritten (fork's auto-checkpoint commits are dropped), the merge must be rebase or squash, then main needs a force-push:

```bash
git checkout main
git reset --hard origin/sync/upstream-${SYNC_DATE}
git push --force-with-lease origin main
```

## Quick Reference

| Task | Command |
|------|---------|
| Commits behind upstream | `git log --oneline origin/main..upstream/main \| wc -l` |
| Fork-only top-level paths | `comm -23 <(git ls-tree HEAD \| awk '{print $NF}' \| sort) <(git ls-tree upstream/main \| awk '{print $NF}' \| sort)` |
| Fork-side file edits | `git diff --name-status $(git merge-base HEAD upstream/main) HEAD \| grep '^M'` |
| Submodule pointer | `git ls-tree HEAD agents/hermes/pm/runtime` |
| Verify Python | `python3 -c "import ast; ast.parse(open('FILE').read())"` |

## Pitfalls (Learned the Hard Way)

### 1. Auto-tracking after `git checkout -b … upstream/main`

When you branch from `upstream/main`, the new branch is tracking `upstream`. `git push` would try to write to NousResearch. **Always run `git branch --unset-upstream` immediately.**

**How to apply:** Right after `git checkout -b sync/… upstream/main`, before any other operation.

### 2. `gh pr create` fails with cryptic error

Without `--repo OWNER/REPO`, `gh` can't always resolve the right repo (especially when both `origin` and `upstream` are GitHub remotes). The error is misleading:

```
GraphQL: Head sha can't be blank, Base sha can't be blank,
No commits between main and sync/upstream-…, Head ref must be a branch
```

**Why:** `gh` is failing repo resolution, not the diff calculation. Always pass `--repo delorenj/hermes-agent` explicitly.

### 3. `voice_mode.py` reverse-diff false positive

Running `git diff upstream/main HEAD -- tools/voice_mode.py` shows BOTH directions of change at once — fork's additions (small) AND upstream's additions the fork is missing (big, looks like fork "removed" them). Easy to misread as "the fork deleted upstream's WAV chunking."

**Why:** the fork didn't delete anything; upstream added the chunking logic AFTER the fork forked. The fork-side intent is `+` in `git diff <merge-base> HEAD`, NOT in `git diff upstream/main HEAD`.

**How to apply:** when isolating fork-side intent, always use `git diff $(git merge-base HEAD upstream/main) HEAD`, never `upstream/main HEAD`.

### 4. Stash does NOT capture submodule HEAD movements

`git stash push -u` stashes tracked file mods and untracked files. It does NOT stash:
- The submodule's HEAD inside `agents/hermes/pm/runtime`
- Any commits the user made in the submodule but not yet pointed to from the parent

**Why:** submodules are independent repos; the parent only tracks a gitlink to one SHA.

**How to apply:** before stashing, record `git submodule status` and the submodule's actual HEAD. After the sync, the modification reappears — that's intentional.

### 4b. `git stash pop` keeps the entry (won't auto-drop) when the stash includes a submodule pointer move

In Step 6, `git stash pop` ends with:

```
The stash entry is kept in case you need it again.
```

…even when there are **no conflicts** and the working tree applied perfectly. This is NOT a failure — git refuses to auto-drop because the stash carries a submodule gitlink movement (`agents/hermes/pm/runtime`) it can't cleanly reconcile its bookkeeping for.

**Why:** the same submodule-independence from gotcha #4 — stash apply can restore the gitlink in the working tree but git stays conservative about discarding the stash.

**How to apply:** don't panic and don't try to "resolve a conflict" that isn't there. Verify completeness, then drop manually:
```bash
git diff --name-only --diff-filter=U          # confirm: empty (no real conflicts)
comm -23 <(git stash show --name-only stash@{0} | sort) \
         <(git status --short | grep -vE '^\?\?' | awk '{print $2}' | sort)
# ^ empty output = every stashed file is reflected in the working tree
git stash drop stash@{0}                       # safe to drop once verified
```
If you skip the drop it's harmless (push only carries commits), but a stale stash can confuse the next run's LIFO pop — so clean it up.

### 5. Branch switch leaves submodule working dir behind

When you `git checkout -b … upstream/main` (which has no `agents/` directory), git emits:

```
warning: unable to rmdir 'agents/hermes/pm/runtime': Directory not empty
```

…and proceeds. The submodule's files stay on disk. **This is fine.** When you later `git checkout main -- agents`, the submodule pointer is re-established in the index, and the working dir is already in place.

### 6. The 3 auto-checkpoint commits look meaningful, aren't

Commits with messages like `CHont`, `checkpoint: <timestamp> auto-commit` from `Jarad DeLorenzo` are from Codex CLI's auto-commit feature. They bundle:

- Real tweaks (a few lines of code) — preserve via re-application
- Auto-regenerated `package-lock.json` (thousands of lines) — discard
- `.agents/skills/.system/` tree — preserve via `git checkout main --`

**Why:** Codex auto-commits everything in the working tree on a timer. The signal-to-noise ratio is terrible.

**How to apply:** always `git show --stat` each fork-only commit before deciding what to preserve. Real intent is the ≤10-line additions to non-lockfile files; everything else is noise.

### 7. `.gitignore` was REPLACED, not extended, by the auto-checkpoints

Earlier fork main had a tiny `.gitignore` (8 lines) instead of upstream's comprehensive ~80-line version. Some past `git add .` followed by auto-commit had overwritten it.

**Why:** the fork's `.gitignore` got blown away at some point and the auto-checkpoints captured the truncated version.

**How to apply:** the sync MUST take upstream's full gitignore as the base and APPEND fork-only patterns. Never let the fork's gitignore win the conflict.

### 8. Stale imports in re-applied tweaks

The fork's `transcription_tools.py` tweak calls `get_hermes_home()` but doesn't import it in upstream's current version of the file. The fork's old version must have had the import for some other reason.

**Why:** when you re-apply a tweak against an evolved upstream, the surrounding context (imports, helpers) may have changed.

**How to apply:** after re-applying any tweak, syntax-check (`python3 -c "import ast; ast.parse(...)"`) AND grep for every symbol the tweak references to make sure it resolves.

### 9. `.codex/` tracks runtime garbage

`.codex/logs_2.sqlite`, `.codex/state_5.sqlite`, `.codex/tmp/arg0/codex-…/*` are runtime files that got `git add`'d. Each sync will see them as modified.

**Why:** Codex CLI writes its state inside the project dir, and the fork tracks everything under `.codex/`.

**How to apply:** the sync's gitignore additions stop FUTURE additions, but already-tracked files need `git rm --cached` separately (do this in a one-off hygiene PR, not during sync).

### 10. Discarded checkpoints prevent fast-forward merge

After the sync, `origin/main` (with the 3 checkpoints) is not an ancestor of the sync branch — they've diverged. A normal merge would re-introduce the checkpoint SHAs.

**Why:** the sync drops 3 commits from main's history.

**How to apply:** in the PR body, document that the merge must be **squash or rebase**, and that main needs a `git push --force-with-lease` from the rebased tip afterward. Coordinate with collaborators (currently solo, so safe).

## Verification

After the sync PR merges and main is force-pushed:

```bash
# Confirm sync state
git fetch origin upstream
git log --oneline origin/main..upstream/main | wc -l   # should be 0 or small
git ls-tree origin/main agents/hermes/pm/runtime       # submodule pointer present

# Sanity-check tweaks survived
grep -q "load_hermes_dotenv" tools/transcription_tools.py && echo "tweak 1 ✓"
grep -q "local_command" tools/voice_mode.py && echo "tweak 2 ✓"
grep -q "\.lastagent" .gitignore && echo "tweak 3 ✓"

# Try a smoke import
python3 -c "from tools.transcription_tools import _get_local_command_template; print('import OK')"
```

## PR Body Template

```markdown
## Summary

Brings the fork up to date with `NousResearch/hermes-agent main` (N commits), discards the auto-checkpoint commits, preserves fork-only paths and the 3 fork code tweaks.

## Sync layout

Branch based on `upstream/main` (SHA — "TITLE") + two commits:

1. `chore(fork): preserve fork-only customization layer on top of upstream`
2. `chore(fork): re-apply fork-side tweaks on top of upstream`

## Merge instructions

Use **Rebase and merge** or **Squash and merge** (NOT regular merge). After merging, force-push main from the rebased tip:

```
git checkout main
git reset --hard origin/sync/upstream-YYYY-MM-DD
git push --force-with-lease origin main
```

## Test plan

- [ ] `python3 -c "import ast; ast.parse(open('tools/transcription_tools.py').read())"`
- [ ] `python3 -c "import ast; ast.parse(open('tools/voice_mode.py').read())"`
- [ ] `scripts/run_tests.sh tests/agent/ tests/tools/`
- [ ] `hermes` CLI starts cleanly
- [ ] Submodule `agents/hermes/pm/runtime` resolves to its tracked SHA
```
