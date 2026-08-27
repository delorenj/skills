# Profile config mutation safety

Use this contract whenever a Hermes path can read and then rewrite a named
profile's `config.delta.yaml` or generated `config.yaml`. It applies to initial
seeding, channel adoption and rotation, voice reconciliation, render, absorb,
recovery, and fleet backfill. A helper is not safe if a real caller snapshots
state before reaching it.

## One lock domain

- Require a real profile directory; reject legacy profile symlinks before any
  read or mutation. Derive one stable lock identity for the profile without
  following a caller-controlled symlink.
- Open the adjacent lock with no-follow semantics, verify the opened inode is a
  regular file, restrict it to mode `0600`, mark its descriptor close-on-exec,
  and use an exclusive kernel lock. Revalidate the profile through a trusted
  directory descriptor after locking. The lock file may persist, but ownership
  must release on normal exit, exception, signal, and process death; children
  must not inherit the descriptor.
- Use a finite configurable timeout and report timeout as failure. Invalid or
  non-finite timeout values fail closed rather than silently waiting forever.
- Inventory every writer. Initial seed, channel, voice, renderer, absorb,
  migration, recovery, and fleet-sync/backfill paths must all enter this same
  lock domain before checking existence, reading, snapshotting, or writing the
  config pair.

Registry-aware channel work has one global order:

```text
registry lock -> profile lock -> snapshot/check -> write/rollback -> unlock
```

Config-only work takes only the profile lock. No path may take profile then
registry, recursively reacquire a non-reentrant lock, or invoke an unlocked
writer from inside a locked wrapper.

Invocation credentials can be validated before locking because they are not
durable state. Durable `op://` references, channel identity, registry claims,
role metadata, and existing generated/delta content that may be written back
must be read only after the required locks are held. If slow external
validation happens optimistically, re-read and compare all durable inputs under
the locks and retry or abort on change; never commit the earlier snapshot.

## Replacement and exact rollback

When a candidate config is installed and then validated, keep a protected
same-directory recovery name that does not resemble a source backup (`*.bak`,
`*.orig`, `*~`, or `*-backup.*`). Serialize stale recovery, snapshot, install,
validation, commit, and cleanup under the profile lock.

Preserve the operator's original inode, not merely equivalent content. One
portable shape is a same-filesystem hard-link recovery entry followed by an
atomic candidate replacement:

1. Validate parent/target/recovery path types without following symlinks.
2. Record original device/inode, byte digest, mode, and nanosecond mtime.
3. Create and directory-fsync the protected recovery link before installing the
   fully written, file-fsynced candidate with atomic replacement.
4. On failure or an uncommitted recovery record at the next run, atomically put
   the recovery inode back at the operator path and directory-fsync it.
5. Verify inode, bytes, mode, and mtime match the pre-state. Only then may an
   optional post-restore validator run; validation failure must never prevent
   restoration.
6. On success, remove recovery state and directory-fsync the cleanup.

A hard link shares the original mode, so do not `chmod` it. Create it through a
trusted directory descriptor with exclusive/no-follow checks, and require the
parent directory or ACL to protect the recovery name. If those protections are
not available, fail before installing the candidate.

If the filesystem cannot preserve the original inode safely, fail before
installing the candidate or use an equally strong platform primitive. A copied
snapshot that creates a new inode does not meet exact restoration.

## Regression proof

Exercise top-level callers, not only their final helper:

- Voice pauses after its locked snapshot; a channel rotation reaches the
  profile lock and blocks. After release, both changes survive.
- Channel pauses after acquiring registry then profile and snapshotting; voice
  blocks. After release, both changes survive.
- A tokenless adoption caller pauses at its snapshot boundary while a distinct
  rotation is attempted in both orders. It must observe the winning durable
  references and identity or retry/fail without reverting them.
- Initial seed and each backfill writer contend the same held profile lock and
  time out without creating, truncating, or replacing either config file.
- A bounded waiter returns a truthful timeout. Killing a lock holder releases
  ownership, and the next real caller converges without manual lock-file
  deletion.
- Crash injection at every recovery phase either leaves the original exact or
  causes the next locked run to restore it before attempting a new install.

Assert final delta, generated config, registry claim, role metadata, markers,
and protected recovery state. A final semantic YAML comparison alone cannot
detect stale references, lost comments, inode changes, or false completion.
