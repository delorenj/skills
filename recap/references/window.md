# Resolving the window

A sha is an anchor you convert to an instant. **It is never the window.** Every rung below yields an
instant; every rung is then validated by its *output*, never by its error message.

Record which rung fired, and its confidence, in the provenance line.

## The chain — stop at the first rung that yields a validated instant

### 0. A prior recap  ·  universal  ·  free

```bash
ls .recaps/entries/*.json 2>/dev/null | sort | tail -1
```

Newest entry's `window.end` is where this one starts. Entries are one-file-per-run and the index is
derived from them — never merged — because parallel agents in one repo would otherwise race a shared
index and silently chain from the same anchor. (Measured on this machine: 95 overlapping session pairs
in a single project directory.)

**Refuse to chain from an entry whose `head_sha` is not an ancestor of local HEAD** — a pull from
another machine imports an anchor that postdates this clone:

```bash
git merge-base --is-ancestor "$entry_head" HEAD || echo "foreign anchor, fall through"
```

A stale anchor (last recap five days ago) is legitimate but wide. Emit the wide window for continuity and
render everything before this session as a collapsed **previously reported** band, so the surplus is
labelled surplus rather than re-reporting three days the user already read.

### 1. The session transcript  ·  universal where Claude Code is  ·  ~20 ms

```bash
sid="${CLAUDE_CODE_SESSION_ID:?}"
find "${CLAUDE_HOME:-$HOME/.claude}/projects" -maxdepth 2 -name "$sid.jsonl" -print -quit
```

**Find by filename. Never derive the directory by encoding the cwd** — `/` and `.` both encode to `-`,
and the collisions are live (128 project dirs here, including `-home-delorenj--agents` and
`-home-delorenj--claude`). Encoding gives you the *wrong session's* transcript and gives it to you
successfully, which is worse than failing.

Timestamps in the file are **not monotonic**. Sort them before taking min/max.

### 2. The harness session-start block  ·  this harness  ·  free, but demoted

The `# gitStatus` block injected at session start lists HEAD at that moment. Convert with
`git log -1 --format=%cI <sha>`. Demoted below the transcript because it is context rather than a file:
a subagent gets its own re-injected block and would report *its* start as the run's start — plausible,
precise-looking, wrong — and after compaction it may be stale or absent with no signal.

### 3. The reflog  ·  needs-git  ·  **validate the answer, not the warning**

```bash
LC_ALL=C git rev-parse "HEAD@{${N}.hours.ago}" 2>/dev/null
```

This exits **0** past the reflog horizon and prints a sha anyway. Verified here: `HEAD@{5000.hours.ago}`
returned rc=0 and a commit dated **three months** before the requested instant, with the only signal a
localizable stderr warning. Grepping for `only goes back to` is a locale-dependent string match on a
command that succeeded.

So validate the output:

```bash
want=$(( $(date +%s) - N*3600 ))
got=$(git log -1 --format=%ct "$sha")
# reject if |got - want| exceeds a tolerance you chose deliberately
```

### 4. Ask

Better than a wrong window. Say what you tried and what each rung returned.

## Then, always

### A. Refine with idle gaps

From the transcript, emit gaps > 2 h as run-boundary candidates. A "single session" is routinely two runs
with a night in the middle — the session this skill was built in spans 23.95 h around an 11 h 40 m sleep.
Without this the recap covers two runs and reads as one.

### B. Bound any session union — hard

One run can span several transcripts (`/clear`, auto-compact, an orchestrator re-spawn). Chaining them by
time adjacency alone is **transitive, and transitivity explodes**: applied to 53 transcripts in one
project directory it collapsed into 9 components, the largest 25 transcripts spanning **84.3 hours**,
returned with exactly the same confidence as a correct narrow window.

So: **max 2 hops**, and cap total span at a small multiple of the seed session's own duration. Prefer a
real spawn/parent link over time adjacency. Any union that grows past the cap is **ambiguous → ask**.
Fix the order too — union first, then gap-split — or the same input yields different windows on
different runs.

### C. Cross-check before using any sha range

`git log <sha>..HEAD` is **not a date range**. `A..HEAD` means "reachable from HEAD, not from A", so if
A sat on a side branch, everything on main since the branch point reappears — including commits *older*
than A. Measured in one repo: an anchor dated 2026-08-28 dragged in 119 commits reaching back to
2026-07-06; another dated 2026-08-17 reached back 203 commits.

```bash
anchor=$(git log -1 --format=%ct "$SHA")
oldest=$(git log --format=%ct "$SHA..HEAD" | sort -n | head -1)
[ -n "$oldest" ] && [ "$oldest" -lt "$anchor" ] && CONTAMINATED=1
```

**Harvest by date by default**; use sha ranges only as corroboration. The cross-check has false
negatives — a clean verdict is not proof the anchor is topologically sound.

```bash
git log --since="$START" --until="$END" --format='%h %cI %an %s'
```

Use `%cI`/`%ct` (committer date) everywhere, **never `%ad`** — a repo that rebases has author dates out
of topological order.

### D. Band the re-landed work separately

`--since` filters committer date, which is right for *landing* and wrong for *authorship*. A rebase or
cherry-pick during the window stamps old work with in-window committer dates, and every one of those
commits then reads as this run's output. Verified: 30 of 457 commits in one repo have `ct != at`, max
skew 6.5 h.

```bash
git log --since="$START" --format='%h %ct %at %s' |
  awk '{ if ($2 - $3 > 3600) print "re-landed: " $0 }'
```

Report those as **re-landed, not authored here**.

### E. Filter `--all`, or do not use it

`--all` traverses every ref including `refs/stash` (52 refs here) — a stash taken during the run appears
as a commit, and fetched branches from other contributors appear as your work. Filter by the run's own
trailer (`Co-Authored-By`, or whatever the session stamps) or drop `--all`.

## Timestamps

**Every internal timestamp is epoch seconds. ISO strings exist only at the render boundary.** Sources
disagree — transcripts are UTC, git and boards are local — and "normalize before comparing" is a
discipline, which fails. Parse naive values only with an explicitly declared timezone, or reject them.

## Blacklist

**`~/.claude/bloodbank-session.json` and `~/.claude/bloodbank-sessions/`.** It looks ideal — a JSON
`started_at` under `~/.claude`, updated seconds ago — and it is wrong, here by 24 h. Every SessionStart
hook, subagent spawns included, resets one home-scoped file shared by all concurrent sessions, and its
`session_id` is a hook-local uuid unrelated to Claude's.

## Degenerate cases

- **No commits at all.** Two of ten sampled repos have `.git` and zero commits. Every median and range
  computation divides by that. Fall to the transcript rung and report a diff-only recap.
- **No git.** The transcript rung and the probe engine still work against the working tree.
- **First run, no transcript, no reflog.** Ask. Do not invent.
