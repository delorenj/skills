# Fleet secret migration and eradication

Use this workflow when moving a Hermes credential into DeLoSecrets, retiring
one, or proving that a leaked value is absent. Containment, current-state
migration, history rewriting, and consumer rollout are distinct operations with
separate authorization boundaries.

## Scan without disclosure

Never print the value, put it in argv, export it to scanner children, or write a
plaintext search pattern. Keep exact matching inside one trusted process fed by
an anonymous pipe/FD, or compare non-reversible fingerprints where that is
sufficient. Sanitize paths and counts in evidence.

Inventory all relevant surfaces:

- current tracked, untracked, and ignored text plus structured databases,
  write-ahead logs, caches, generated configs, and runtime state;
- the Git index and staged blobs, not only worktree files;
- every local branch, tag, and other reachable ref;
- reflog-reachable and unreachable local objects, including dangling blobs and
  commits that ordinary `--all` scans omit;
- the fetched branch and tag tips that are reachable on each pushed remote.

Record the remote's advertised refs and fetch branches, tags, and accessible
review/release refs into an isolated namespace without merging before evaluating
pushed history. A local clean tip or stale `origin/*` snapshot proves only that
local state. Tool output saying "no findings" is credible only when the evidence
identifies every surface actually scanned and the scanner was tested against a
synthetic matching fixture without exposing it.

## Contain and migrate current consumers

Rotation or retirement changes external security state and always needs
explicit authorization. Once authorized:

1. Revoke or rotate the exposed credential first; history cleanup cannot make
   a still-valid value safe.
2. Inventory every consumer and its reload/restart behavior.
3. Store the replacement in the approved vault and persist only its `op://`
   reference in configuration.
4. Remove current plaintext copies transactionally, then validate consumers
   through their real health paths without displaying either value.
5. Preserve a transiently unavailable vault's last known-good reference and
   completion state; a healthy rerun must revalidate and converge.

Do not declare retirement complete until old-value authentication fails where
safe to test and every required consumer is healthy on the replacement.

## Rewrite private remote history only with authorization

Force rewriting branches or tags is destructive and separately requires an
explicitly named private remote and ref scope. Before rewriting:

- freeze pushes and enumerate branch, tag, review, release, automation, mirror,
  and deployment refs that can keep the object reachable;
- create named, access-controlled, time-bounded rollback refs for every old tip;
  record their object IDs without recording secret content;
- document which clones, forks, mirrors, bundles, caches, and CI artifacts can
  reintroduce the old objects.

Rewrite the authorized refs, force-update with lease or an equivalent
old-object guard, then fetch into a brand-new clean clone from the remote and
repeat the full reachable-history scan there. Also verify all consumers on the
rotated credential.

Invalidate old clones before lifting the push freeze: require reclone or a
verified cleanup, remove stale worktrees/bundles/caches, and use server-side
controls where available to reject pushes containing old history. Retain the
protected rollback refs only for the approved recovery window; they are proof
and recovery material, but they also intentionally keep the sanitized objects
reachable. Delete them and run the remote's supported object-retirement process
only after clean-clone proof, consumer health, and rollback-window approval.

## Completion evidence

A complete report distinguishes:

- credential revoked/rotated;
- current files, databases, caches, and index clean;
- local reachable, reflog, and unreachable object scans clean;
- authorized pushed refs rewritten and clean-clone scan clean;
- consumers healthy on the replacement;
- old clones and other reintroduction paths invalidated;
- rollback refs either retained until a stated deadline or explicitly retired.

If any item is unverified, report it as remaining exposure or deferred proof,
not as a clean migration.
