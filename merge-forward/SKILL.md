---
name: merge-forward
description: Incremental delivery workflow for a monorepo and its component repositories. Use when implementing, integrating, pinning, containerizing, publishing, or composing changes across a root repo and its components; especially when work risks long-lived branches, broad component freezes, excessive review or security ceremony, submodule or image drift, or delayed merges to main. Produces the smallest observable slice, bounded verification, immediate component and root main merges, and concise status reporting. Repo-specific extensions (e.g. 33god-merge-forward) layer product authority boundaries and repo-specific gates onto this base.
---

# Merge Forward (base)

This is the generic base skill. It is ecosystem-agnostic on purpose. A repo-specific extension skill (named `<repo>-merge-forward`) supplies product authority boundaries, contract-specific gates, and tuner invariants. Read [references/instantiate.md](references/instantiate.md) to port this base to another monorepo.

## Mission

Ship one observable improvement at a time and merge it to `main` as soon as its affected behavior is proven.

Default environment model (an extension may restate or override these):

- one user and one decision-maker;
- pre-production and not serving live users;
- rapid architectural learning is more valuable than speculative protection;
- Git history is sufficient change history; do not manufacture evidence packets;
- component development must resume quickly after each narrow integration slice.

Obey platform safety rules and never expose credentials, but do not import production deployment, rollback, compliance, stakeholder, incident, or audit ceremony unless the user explicitly asks for it.

## Product authority boundaries

The base defines none. The repo extension must name which component owns which truth (lifecycle, events, persistence, rendering, identity, and so on) and must stop and surface any change that redraws those boundaries. Do not let a generic framework silently reassign ownership.

## Merge-forward invariants

1. Treat `main` as integration truth. A verified change left only on a feature branch is unfinished.
2. Work on one slice at a time. Finish its component and root merges before beginning another slice.
3. Lock only the repositories and interfaces touched by the active slice. Never freeze the ecosystem.
4. Keep branches short-lived. If a slice cannot be completed before changing focus or handing off, split it smaller.
5. Merge the component repository first, then update and merge the root pin or image digest.
6. Preserve unrelated local work. Use a worktree only when the primary checkout is dirty or the user is actively using it.
7. Validate changed behavior and its immediate contract boundary. Do not repeatedly revalidate unchanged history or the whole ecosystem.
8. Reproduce review findings before treating them as blockers. Prose-only speculation does not block a merge.
9. Do not start a new review layer after a repair unless the repair materially changed the reviewed behavior.
10. Report status in plain English throughout the run.

Read the extension's gate reference before selecting acceptance gates or escalating review depth; the universal gate menu lives in [references/gates.md](references/gates.md).

## Component lock protocol

A lock is an advisory edit boundary, not a development freeze.

- Lock only the owning component and, when unavoidable, its single direct producer or consumer.
- Leave every unrelated component available for normal development.
- Start the lock when implementation begins.
- End the lock as soon as the component commit is on component `main` and the exact pin or digest is on root `main`.
- Never hold a global monorepo lock.
- Never begin a second slice while the first slice has verified commits waiting off `main`.
- If more than one producer-consumer pair must move atomically, split the protocol change into backward-compatible increments or obtain explicit user approval for the broader lock.

## Workflow

### 1. Recover current truth

Inspect, without mutating:

- root and affected component `git status`, branch, `HEAD`, upstream, and recent commits;
- the root coordination ledger and the most recently changed relevant artifacts;
- root topology, component manifests, Compose declarations, and current pins;
- any running worker or worktree already assigned to the same slice.

Use the code graph first for code exploration when it is populated and current. Fall back to `rg` and direct file reads when the graph is empty, stale, or lacks the relevant surface.

Do not trust an old report over current source, tests, runtime state, or remote refs.

Give the user this recap before changing anything:

```text
DONE: <last durable result already on main>
NOW: <single active slice>
NEXT: <merge or next executable gate>
BLOCKERS: <none, or one concrete blocker>
```

Keep one root coordination entry. Do not create competing ledgers for the same slice.

### 2. Define the smallest mergeable slice

Write a slice contract before editing:

```text
Outcome: <one behavior visible to a user or adjacent component>
Repos: <root plus the minimum affected components>
Authority: <which component owns the behavior>
Acceptance: <3-7 observable checks>
Merge order: <producer/component main -> consumer main if needed -> root main>
Out of scope: <tempting adjacent work deliberately deferred>
```

A valid slice normally changes one component or one producer-consumer boundary. Split broad requests by executable outcomes, not by documentation, implementation, and testing phases.

Classify each touched artifact:

- **Runnable service:** own a Dockerfile and publish a commit-addressed image.
- **Library or SDK:** publish or pin the native package/source artifact; do not invent a container.
- **Template or configuration:** validate generated output; do not invent a container.
- **Root assembly:** pin existing artifacts and prove the affected Compose path.

### 3. Establish a fresh baseline

- Start from the current component `main` and current root `main`.
- Record exact starting SHAs and image digests in the task entry.
- If the primary checkout contains unrelated work, create one isolated worktree for the slice.
- Do not copy credentials, sessions, local runtime databases, caches, or generated agent state into source.
- Do not create nested runtime gitlinks. Repo-local runtimes are ignored operational checkouts or external fleet state.

Do not run a full repository-history audit as routine baseline work.

### 4. Implement component-first

Change the owning component before changing root assembly.

For coupled components:

1. implement and merge the producer or authority owner;
2. implement and merge its immediate consumer;
3. update root pins, image digests, Compose, and cross-component checks.

For runnable services:

- keep the Dockerfile in the component repository;
- tag images with the component commit SHA;
- prefer registry images in the root Compose stack;
- use a development override for local builds when useful;
- add only the health check and configuration needed to exercise the slice.

Do not bundle unrelated cleanup, architecture, documentation, or hardening into the slice.

### 5. Run bounded verification

Select the minimum sufficient gates from the gate references.

Default verification consists of:

1. affected unit or component tests;
2. one contract smoke test when an adjacent component is involved;
3. `docker compose config` when Compose changed;
4. startup and health proof for each changed runnable service;
5. changed-boundary documentation parity;
6. clean diff and exact pin/digest checks.

Run a real transport or persistence test only when the slice claims transport or persistence behavior.

Use one implementation pass and one deterministic validation pass by default. Escalate to independent code review only for a concrete reason listed in the gate reference.

When a gate fails:

- fix a failure caused by the slice;
- record but do not absorb an unrelated pre-existing failure;
- rerun only the affected gate and any gate invalidated by the repair;
- reduce the slice if its verification surface has become disproportionate.

### 6. Merge the component immediately

Once component acceptance passes:

1. commit the focused component diff;
2. update from component `main` if it moved;
3. rerun only invalidated gates;
4. merge to component `main` without waiting for another slice;
5. push component `main` when publication is in scope;
6. verify the remote contains the exact commit or image.

A pull request is optional. Do not require one for a single-user pre-production system.

Do not leave root pointing at a feature-only component commit longer than the active merge operation.

### 7. Advance root main immediately

Update only what the accepted component slice requires:

- exact component SHA or immutable image digest;
- relevant Compose service/profile and health wiring;
- root manifest or topology entry;
- affected cross-component acceptance test;
- root/component boundary documentation if the contract changed.

Run the root gates selected for the slice, commit the focused root diff, merge it to root `main`, and push when publication is in scope.

If root `main` moved, integrate it and rerun the targeted root gate. Do not restart component archaeology.

### 8. Unlock and hand off

After root `main` contains the verified slice:

- mark the root task entry complete with component/root SHAs and image digest;
- remove the slice worktree with normal Git worktree commands when safe;
- leave unrelated WIP untouched;
- report `DONE / NOW / NEXT / BLOCKERS`;
- select the next smallest slice.

Never keep several verified slices queued on a long-lived integration branch.

## Review and verification budget

Use no independent reviewer by default for docs, templates, isolated tests, or single-component changes with deterministic gates.

Use at most one independent review pass when the slice includes one of these:

- credential or authentication handling;
- destructive data migration or deletion;
- first-time public repository or package publication;
- a change to component authority or event schema compatibility;
- an interface change spanning three or more components;
- behavior that cannot be proven by a deterministic test.

After review:

1. reproduce each finding against the exact target commit;
2. discard findings disproved by executable evidence;
3. repair confirmed slice-blocking findings together;
4. rerun affected deterministic gates;
5. use one focused rereview only if the repair cannot be proven directly.

Do not commission blind, edge-case, acceptance, security, and architecture reviewers simultaneously for an ordinary slice.

## Security proportionality

Always:

- avoid printing, committing, or publishing actual credentials;
- use secret references such as 1Password references where supported;
- respect tool and platform safety enforcement;
- preserve unrelated user data and WIP.

Perform an explicit current-tip secret check when first making a repository public or when changing credential-bearing surfaces. Expand to reachable-history scanning only when current evidence indicates a historical credential, or the user explicitly requests it.

Do not block product integration on cleanup of an agent-owned temporary directory. Report its path and continue when product state is unaffected.

## Anti-ceremony rules

Do not add these unless the user explicitly requests them or current evidence makes them necessary:

- rollback or production deployment plans;
- stakeholder, approval, incident, compliance, or audit workflows;
- multi-day component freezes;
- full-history scans for ordinary commits;
- anonymous clone proofs after every pin update;
- whole-stack tests for an isolated component edit;
- evidence bundles duplicating command output and Git history;
- repeated reviews of unchanged code;
- sub-orchestrators for one well-bounded slice;
- fixes for unrelated warnings discovered during validation.

If an automated policy forces extra work, state exactly which external rule requires it. Do not describe self-imposed ceremony as mandatory security enforcement.

## Agent orchestration limits

- Execute a straightforward slice directly or assign one worker.
- Use parallel workers only for genuinely independent slices that can each merge separately. If the user interrupts or changes the objective, stop workers serving the old slice, treat late results as stale, and define the replacement slice before continuing.
- Do not create a manager-of-managers hierarchy unless the user explicitly asks for it and at least three independent deliverables justify it.
- Update the root task entry immediately when a worker starts and when it finishes.
- On agent quota or provider failure, retry once or switch tools once. Then continue locally; do not build a resume chain.
- Keep reviewer and worker prompts scoped to exact repos, commits, acceptance checks, and prohibited side effects.

## Session-end rebalancing

This base is designed to be self-tuning: a repo-scoped session-end hook can improve the extension skill from concrete session evidence. The hook must remain asynchronous, debounced, recursion-guarded, and limited to the extension skill directory.

Apply automatic tuning only from a clean `main` checkout. Build and validate changes in a temporary candidate first, preserve the extension's declared invariants, and commit tuner-applied edits automatically with a clearly tuner-authored message so the dirty-tree guard can never deadlock on its own output. Never push automatically. Prefer removing or narrowing disproven ceremony over accumulating more rules. Allow per-dev disablement through a local, uncommitted config.

Treat a dirty skill or non-`main` checkout as a deferred update, not a reason to disturb active work. Emit a telemetry event for every tuning cycle that mutates the skill, and never let telemetry failure block or crash the tuner.

## Definition of done

A slice is done only when:

- its observable acceptance checks pass;
- changed component commits are on component `main`;
- root `main` contains exact published SHAs or image digests;
- affected Compose configuration resolves;
- the root task entry states what shipped and what comes next;
- no unrelated WIP was incorporated.

The broader platform is not required to be perfect before a completed slice reaches `main`.
