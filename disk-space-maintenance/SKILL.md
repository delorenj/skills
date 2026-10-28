---
name: disk-space-maintenance
description: Free disk space and keep it free, on any Linux or macOS machine, with ultra-targeted profiles for known DeLoNET machines (big-chungus, tiny-chungus, carries-macbook-air). Measures first, sorts every byte into rebuildable / owner-decision / never-touch, reclaims the safe tier, then bounds whatever regrows (logs, caches, state DBs, build output, docker) so the same pile does not come back. Use for "disk full", "low on space", "out of space", "no space left on device", "ENOSPC", "storage almost full", "Mac storage full", "System Data is huge", "free up space", "clean up the disk", "logs grow forever", "why is the disk filling up again", "docker eating disk", "emergency cleanup". Do NOT use for process/crash-loop/CPU/memory forensics on big-chungus (server-maintenance), for backup design, or for deleting a specific named file the user already chose.
---

# Disk space maintenance

Two jobs, always in this order: **get space back now**, then **stop it coming back**.
A cleanup that skips the second job is the reason the user is back the next day
(big-chungus: 98% full on 2026-10-14, "full again" on 2026-10-15).

## Principles

- **Measure before deleting, and measure the right thing.** Read
  [references/strategy.md](references/strategy.md) once per session: hardlinked
  caches, APFS purgeable space and snapshots, deleted-but-open files, docker
  "reclaimable", sparse images and G-vs-GiB all lie in predictable ways.
- **Every byte gets a class before anything is deleted.**
  **A** rebuildable, delete without asking · **B** owner decision · **C** never.
  When unsure, it is B. Personal data, another user's files, unpushed git work
  and live service state are never A.
- **Fix the accumulator, not just the pile.** For every item you clean, ask what
  wrote it and what bounds it now. No bound means it is not finished: add
  rotation, retention, an age rule or a scheduled prune at the source.
- **Prefer the tool's own cleanup command over `rm`** (`xcrun simctl delete
  unavailable`, `docker image prune`, `uv cache prune`, `pnpm store prune`,
  `brew cleanup`, `journalctl --vacuum-size`). It knows about locks, links and
  state you do not.
- **The machine profile is the baseline.** An observation is only an anomaly
  relative to `references/machines/<name>.md`. If the run contradicts the
  profile, the run wins and the profile gets fixed before you finish.

## Workflow

| Step | Do | Load |
|---|---|---|
| 0 Identify | Work out the machine, its disk and how urgent this is | — |
| 1 Survey | Run `scripts/survey.sh` (read-only) and read the one report | report |
| 2 Classify | Map the bytes into A/B/C against the profile | machine profile, [strategy](references/strategy.md) |
| 3 Reclaim A | Run tier A, measure each step | profile playbook, OS playbook |
| 4 Decide B | Put tier B to the owner as a short table, act on the answers | — |
| 5 Bound | Install a durable bound for each accumulator found | OS playbook |
| 6 Verify | Re-measure; prove each bound is installed and fires | — |
| 7 Feed back | Update the profile and this skill (mandatory) | [feedback loop](references/feedback-loop.md) |

### 0. Identify

- Machine name = the tailnet DNS label (`survey.sh` prints it and the profile
  path to load). Known profiles live in [references/machines/](references/machines/):
  [big-chungus](references/machines/big-chungus.md),
  [tiny-chungus](references/machines/tiny-chungus.md),
  [carries-macbook-air](references/machines/carries-macbook-air.md).
  No profile: proceed with the generic playbook, then create one from
  [references/machines/_template.md](references/machines/_template.md) in step 7.
- Remote machines run everything over ssh from big-chungus; the profile names the alias.
- Check recall for prior incidents: `hindsight memory recall infra "disk space <machine>"`.
- **Under ~3% free, or writes are already failing:** switch to
  [references/emergency.md](references/emergency.md) first, buy headroom in
  minutes, then come back to step 1. A full disk breaks the very tools a survey needs.

### 1. Survey

```bash
bash "$SKILL_DIR/scripts/survey.sh" > /tmp/disk-survey.md               # local
ssh <alias> 'bash -s' < "$SKILL_DIR/scripts/survey.sh" > /tmp/<m>-survey.md   # remote
```

`SKILL_DIR` is the directory this skill was loaded from (on big-chungus:
`~/.agents/skills/disk-space-maintenance`). Add `-- --quick` (remote) or `--quick`
(local) to skip the slow full-home walks; when the profile was verified within
the last day, quick is enough. The report covers filesystems,
snapshots, the top of `$HOME`, known caches, docker, files over 1G, what was
written in the last 48h, logs over 50M, runaway logs and restart loops,
deleted-but-open files and the cleanup automation already installed. Don't
redo these with ad-hoc commands; drill into what the report points at.

On big-chungus, also read the free-space trend (Prometheus on `localhost:9472`)
before blaming anything: "full again" is often a growth rate, not a pile.

### 2. Classify

Compare the report with the profile's **Space map** and **Known accumulators**.
Write down three lists with sizes: A, B, C. Account for the used figure as far as
you can, and name what you could not measure (no sudo, another user's home)
instead of quietly ignoring it. The OS playbooks list the usual suspects:
[Linux](references/linux.md), [macOS](references/macos.md).

### 3. Reclaim tier A

Biggest first, one category at a time, measuring free space before and after each.
Respect the preconditions in the profile (no CI job running, no build in
progress), and **re-check them immediately before each `rm`**: jobs start
mid-run. A step blocked by a busy check moves to the end of the run and is
retried, not dropped. A cache whose app is running on a live desktop is skipped
and recorded; don't quit the user's apps. Stop and reclassify anything that turns
out to be in use, holds the only copy of something, or that the profile got
wrong. A profile's "A" is a 30-minute-old opinion, and the run decides. Run long
or CPU-heavy work through `heavy` where it exists (big-chungus).

### 4. Decide tier B

Ask the owner once, with a compact table (path, size, what it is, your
recommendation). Use AskUserQuestion when the session is interactive. Delete only
the rows they approve. Don't re-ask about rows the profile already records a
decision for.
When acting on the answers, follow [Acting on tier-B answers](references/strategy.md):
archive, then verify, then delete; check for a live data location (sync tool or
app default) before deleting a personal folder; hand root-only removals to the
owner as a script instead of escalating.

### 5. Bound the accumulators

For each thing that regrows, install the bound closest to its source:

0. if the writer is broken or obsolete (a crash loop, a client of a retired
   service), retire it reversibly: unload it and move its unit or plist to an
   attic dir with a restore note;
1. the app's own retention setting (log size/keep count, execution pruning,
   session cleanup period), or a prune at the start of each run in the tool
   that writes per-run dirs (a small repo change: commit it there);
2. log rotation (logrotate or newsyslog, using copytruncate for files held open);
3. age rules (systemd-tmpfiles on Linux; a launchd agent on macOS);
4. a scheduled prune script (systemd timer or launchd agent) as the fallback.

The canonical copy of any script, unit, plist or config goes in a git repo and is
symlinked into place: `~/code/infra` for DeLoNET machines. Commit and push it.
An unversioned cleanup job is just one more thing that rots.

### 6. Verify

- Free space after vs before, in one unit (say GiB or GB, not both).
- Each bound: file in place, timer or agent loaded with a next run, a dry run or
  real run that acts on the target, and no errors in its log. Prove it in the
  scheduler's own context (`launchctl kickstart`, `systemctl start`), not just
  from your shell: cwd, PATH and environment differ there. A log line with an
  empty result, or a step that logs no exit code, counts as a failure until you
  prove otherwise (a launchd agent's `pnpm store prune` failed with EROFS in `/`
  behind an exit 0 and a blank log line).
- Nothing broke: the services and tools near what you cleaned still start.
  Interpreters and toolchains are the usual casualty.

### 7. Feed back (mandatory, not optional polish)

Follow [references/feedback-loop.md](references/feedback-loop.md). In short:
update the machine profile (space map, accumulators, decisions, gotchas),
append a run-log line with `scripts/log-run.sh`, promote machine-agnostic
lessons into the generic references, retain one hindsight memory per real
finding, then commit and push the skills repo. **A run is not done while the
profile's "Last verified" date is older than today.**

## Out of scope

- Why a process or container keeps dying, CPU or memory pressure, swap (use
  `server-maintenance` on big-chungus). Swap fills RAM, not disk, even when the
  user calls it "full".
- Designing backups or retention for data the user wants kept: point it out, ask.
- Hardware: failing SSDs, SMART errors, resizing partitions.
