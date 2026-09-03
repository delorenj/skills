# Harvest

**Harvest wide, render narrow.** Most of what you gather appears nowhere on the page. Gathering it is
how you know what *not* to say.

Tier 1 runs always. Tier 2 runs when a probe succeeds. Tier 3 is this user's setup — rich when present,
absent in most repos, and never load-bearing.

---

## Tier 1 — universal, seconds each

### 1. The diff itself

The one source that exists in every repo, and the one the meta-sources tempt you to skip.

```bash
git diff --stat "$BASE..HEAD"
git diff --numstat "$BASE..HEAD" -- '*.md' '*.yaml' '*.yml' '*.json' '*.toml' | sort -k1 -rn
```

Ranking doc/config changes **by bytes, not lines**, surfaces the run's own artifacts without knowing any
methodology — in one repo it ranked spec → README → contract → ledger → sprint file with zero BMAD
knowledge. A single 4 KB line beats forty short ones.

### 2. What needs a human

The highest value per line on the whole page.

```bash
git status --porcelain              # uncommitted
git stash list                      # stashes — check which were made IN-window
git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads   # ahead of upstream
git worktree list
```

### 3. What broke or was abandoned

One grep each, over the window's diff:

```bash
git diff "$BASE..HEAD" | grep -E '^\+.*(it\.skip|xfail|@pytest\.mark\.skip|t\.Skip|\.only\()'
git diff "$BASE..HEAD" | grep -E '^\+.*(TODO|FIXME|HACK|XXX)'
git diff "$BASE..HEAD" | grep -E '^-.*(assert|expect\()'      # removed assertions
```

Plus reverts, and CI steps that were disabled.

### 4. Orphaned and rewritten work

`git log` erases amends and resets; the reflog does not.

```bash
git reflog --date=iso | head -50
# a reflog sha that is no longer an ancestor of HEAD is work that was done and then rewritten
git merge-base --is-ancestor "$sha" HEAD || echo "orphaned: $sha"
```

Diff an orphan before dismissing it — a content-dropping amend is exactly what this catches.

### 5. Health at HEAD

One line on the page, and it is what makes a CAVEAT pill mean anything. Run the repo's own test command
if it is cheap and safe; otherwise report `not run` honestly. Never infer passing from a green console
earlier in the run.

### 6. Other repos

```bash
git rev-parse --show-superproject-working-tree     # a parent that holds a gitlink to this one
git submodule status --recursive
```

A run that bumps a gitlink changed *two* repos. If you sweep sibling repos, **filter by the run's own
commit trailer** — an unfiltered sweep attributes other agents' commits to this run.

---

## Tier 2 — when the probe succeeds

### 7. Ticket state changes

Discover the provider rather than assuming it: `.project.json` → `.momo/config.json` → the `gh` remote.
Then read the *activity feed*, which is the only thing that recovers a transition with its `old_value`
intact (Plane `issues/<id>/activities/`, GitHub `issues/{n}/timeline`, Jira `?expand=changelog`,
Linear `issue.history`).

Graceful degradation with zero API access: extract candidate ids from the window's commits with
`\b[A-Z][A-Z0-9]{1,9}-[0-9]+\b`.

**Use the board to label the window, never to define it** — an In-Progress stamp lands after the real
start and clips the planning phase.

**And never build a section out of ticket numbers.** The user's complaint is that he cannot remember
them. A ticket is evidence attached to a capability, not a heading.

### 8. Commit bodies — measure first, then decide

```bash
git log --since="$START" --format='%b' | wc -c
```

Above roughly 500 bytes median, bodies are a primary source for judgment calls, rejections and live
measurements — in one repo 29 KB of bodies carried a declined refactor with its reasoning, three
rejected review findings *with the evidence that refuted them*, and every live measurement. At or near
zero they are worthless. **Measure; do not assume either case.** Most repos are the second kind.

### 9. Artifact frontmatter

For in-window `.md` files with YAML frontmatter, lift `status`, `deferred`, `warnings`, `blocked`.
Generic across methodologies; costs one parse.

---

## Tier 3 — this user's setup; opportunistic only

`.bmad-loop/runs/*/state.json` (`started_at`, naive local time), `_bmad-output/**` specs and their
`## Auto Run Result`, a deferred-work ledger, `git unpushed`, workflow run records under the session
directory. Rich when present. **Absent in most repos — never let the skill's shape depend on them.**

---

## Live-system facts

A number the run measured against the real system belongs in the recap **even when no code changed**,
with the command to reproduce it beside it. It passes the "could git alone produce this" test more
cleanly than anything else on the page: it is knowledge the user did not have this morning.

Find them in commit bodies and artifact diffs — `[0-9]+ of [0-9]+`, `\d+ (agents|units|hosts|services|
rows|files)` — gated on co-occurrence with a liveness word (*live*, *host*, *real*, *measured*,
*observed*). Verify by re-running the command before printing the number; if it moved, print the new one
and say it moves.

## Redaction — allowlist, not blacklist

The page quotes command output, and the exposure is not only `op://` values: it is `.env` echoes, tokens
in URLs, API responses, internal hostnames, customer data.

**Only these may be quoted verbatim:** commit metadata, file paths, task/subcommand descriptions, ticket
titles, and probe output you explicitly captured for the page. Everything else is summarized, never
pasted. A blacklist regex will miss; an allowlist fails closed.
