# Bounded acceptance gates (base)

Use this reference to choose the smallest gate set that proves the active slice. Do not run every gate in this file. The repo extension adds contract-specific gates on top of these.

## Gate selection

| Slice type | Required gates | Usually unnecessary |
|---|---|---|
| Docs or boundary text | changed-file lint/link check; contradiction search in directly affected docs | service startup, whole-stack Compose, independent review |
| Template or generated config | generator test; representative generated-output comparison; syntax validation | container build unless output is a runnable service |
| Single component | affected unit/component tests; build; changed service health check | unrelated components, full history scan, whole-stack test |
| Two-component contract | producer tests; consumer tests; one real contract smoke; compatibility assertion | broad ecosystem review |
| Root pin or image update | exact remote commit/digest exists; manifest consistency; affected Compose profile resolves | anonymous clone if onboarding already passed |
| Milestone integration | full Compose resolution; required services healthy; one end-to-end pipeline path | repeated repository archaeology |

## Universal preflight

Before editing, record:

- root and affected component `HEAD` and branch;
- clean/dirty state and unrelated WIP;
- current root pin or image digest;
- exact acceptance commands for the slice.

Use current files, remote refs, tests, and runtime state. Treat stale planning reports as hints.

## One-time component onboarding

Run these once when a component first becomes a formal part of the stack:

- classify it as runnable service, library/SDK, template/configuration, or root-only assembly;
- require a component-owned Dockerfile only for a runnable service;
- build the service image successfully;
- define a useful health check;
- publish or otherwise make the exact source/image artifact reachable;
- verify the root can fetch the exact source commit or pull the immutable image;
- perform a current-tip credential scan before first public publication;
- record its product authority and direct dependencies;
- add the smallest root Compose/profile and manifest declarations that can start it.

Do not repeat onboarding on every commit. Repeat only a gate invalidated by a material packaging, publication, ownership, or delivery-model change.

## Recurring component slice

For an ordinary component change, require:

1. tests covering the changed behavior;
2. native build or package validation;
3. changed service startup and health, when runnable;
4. immediate consumer contract smoke, when an interface changed;
5. clean focused diff;
6. merge to component `main`.

## Recurring root slice

After the component is on `main`:

1. verify the exact component commit or image digest exists remotely;
2. update root pin/digest and only affected manifests;
3. run Compose configuration validation for affected profiles;
4. start changed services and direct dependencies;
5. run one root acceptance check for the observable outcome;
6. verify changed root/component docs do not contradict ownership;
7. merge root to `main` immediately.

## Review escalation triggers

Add one independent review only when at least one trigger is present:

- credentials/authentication changed;
- destructive storage behavior changed;
- first public publication is occurring;
- component authority or event-schema compatibility changed;
- three or more components must change atomically;
- no deterministic acceptance test can prove the behavior.

Record the trigger in the root coordination ledger. Absence of a trigger means deterministic validation is the review.

## Finding triage

A review finding blocks only when all are true:

- it applies to the exact target commit;
- it is reproducible in the repository or runtime;
- it violates the slice contract or a standing product boundary;
- the repair belongs inside the active slice.

Discard context-missing, hypothetical, unrelated, or already-disproved findings. Record useful deferred work without expanding the slice.

## Negative controls

When a gate claims to fail closed, test one representative negative control. Examples:

- wrong component SHA is rejected;
- credential-bearing source URL is rejected without printing it;
- malformed event envelope is rejected;
- a component cannot author truth owned by another component;
- missing required image digest fails Compose validation.

One meaningful negative control is better than many source-substring assertions.

## Stop rules

- Gate passes: merge now.
- Main moved: integrate it, rerun invalidated gates, merge now.
- Unrelated existing gate fails: record it and continue unless it invalidates the slice proof.
- Agent/provider fails: retry or switch once, then execute locally.
- Cleanup is blocked but product state is correct: report the residue and continue.
- Slice grows beyond one observable outcome: split it before adding more gates.
- Verified component commit exists off `main`: merge it before starting anything else.

## Status format

Use this compact update during execution:

```text
DONE: <durable commits already on main>
NOW: <single command/gate or repair in progress>
NEXT: <next merge or gate>
BLOCKERS: <none or concrete evidence>
```

At completion, include component commit, root commit, image digest when applicable, acceptance commands, and the next slice. Do not attach a separate evidence dossier.
