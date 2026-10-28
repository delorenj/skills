# Feedback loop

This skill is only cheap while its profiles are true. Every run pays a small
tax to keep them true, and that tax is part of the job. Skipping it is how the
next run ends up re-discovering the same 100 GB.

## When a run finishes (always)

1. **Run log.** Append one line to the machine profile and bump its
   "Last verified" date:

   ```bash
   "$SKILL_DIR/scripts/log-run.sh" <machine> "<free before>" "<free after>" "<one-line summary>"
   ```

   The script creates the profile from `_template.md` when the machine is new.
   Use the same unit for before and after.

2. **Profile deltas.** Edit `references/machines/<machine>.md` for anything the
   run learned:
   - **Space map**: sizes that moved by more than about 20% or 5 GB, new rows,
     rows that no longer exist.
   - **Known accumulators**: every regrower found, with its growth driver and
     the bound now installed (or "none: <reason>").
   - **Never touch / decisions**: tier-B answers the owner gave ("keep
     gruvato-backups", "delete old recordings after 90 days"), so the next run
     does not ask again.
   - **Targeted playbook**: commands that worked, corrected commands that did
     not, real yields instead of guesses.
   - **Gotchas**: every surprise (a lock, a permission wall, a tool that lied,
     something that broke).

3. **Promote general lessons.** A lesson that would help on another machine
   goes into the generic files, not just the profile:
   - a measurement trap goes into `strategy.md`;
   - an OS-specific command or location goes into `linux.md` or `macos.md`;
   - a fast emergency win goes into `emergency.md`;
   - a fix to the survey goes into `scripts/survey.sh` (keep it bash-3.2
     portable and read-only).

4. **Memory.** One `hindsight memory retain infra "<what filled it, what bounds
   it now, what did NOT work>"` per real finding, phrased as the question
   future-you would ask ("Why does the Mac's ~/.cache regrow 10 GB a week?").

5. **Land it.** The skill lives in the `skills` repo
   (`~/code/skillex/all-skills`, a submodule of skillex). Commit and push there,
   then commit the submodule pointer bump in `~/code/skillex` and push. Commit
   and push any repo that received cleanup automation (`~/code/infra` and so on).

## Done means

- The profile's `Last verified` is today.
- The run log has today's line with before and after.
- Every accumulator found in this run has a row with a bound or a stated reason
  why it has none.
- `git status` is clean in every repo you touched, and the commits are pushed.

## Drift checks worth doing at the start of a run

- Profile older than 30 days: treat its sizes as stale and lean on the survey.
- An accumulator listed as "bounded" whose path grew anyway: the bound is
  broken. Find out why before cleaning around it (a timer that never fires, a
  config the app no longer reads, a renamed path).
- A path in the profile that no longer exists: drop the row, and note the
  removal in the run log line.

## Improving the skill itself

If the workflow made you do something dumb (rediscover a path, ask a question
the profile could have answered, run a slow command the survey could have
covered), fix the skill in the same run: add it to the survey, the profile
template or the playbooks. Prefer making the survey smarter over adding prose.
