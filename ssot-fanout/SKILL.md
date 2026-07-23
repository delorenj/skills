---
name: ssot-fanout
description: >-
  Single-source-of-truth config fan-out: keep ONE master file (e.g. hooks.master.json) and propagate it to many downstream targets that each have their own native format/dialect, with a lock file (hooks.mappings.lock.json) recording how ambiguous/divergent mappings were resolved so re-syncs are seamless. Reference implementation: bloodbank services/agent-hooks — hooks.master.json → sync.py → per-agent generated configs + event_map.generated.json, gated by `mise run hooks:check` / `hooks:sync`. Use when adding a new agent CLI or target to agent-hooks, editing hooks.master.json, fixing generated-config drift, resolving an ambiguous mapping, or designing a NEW master-config → multi-dialect propagation engine with ambiguity-resolution memory. Keywords: SSOT, single source of truth, fan-out, generated-config drift. Do NOT use for bumping versions across files (use mise-versioning), defining event schemas or the event-naming contract, or single-target config templating with no dialect/ambiguity dimension.
---

# ssot-fanout

Keep one hand-edited master file and **generate** every downstream config from it. The targets are
heterogeneous — each speaks its own dialect (different key names, nesting, invocation shape) — so the
master maps a *canonical* model onto each target. When two targets would map the "same thing"
differently, or a mapping is otherwise ambiguous, the decision is made once and recorded in a lock
file so the next sync applies it automatically.

This is the pattern behind `services/agent-hooks/hooks.master.json` in bloodbank; that system is the
canonical reference implementation (see [references/reference-implementation.md](./references/reference-implementation.md)).

## Operating principles

- **One source of truth.** The master file is the *only* hand-edited artifact. Every per-target
  config and every per-consumer map is GENERATED. Never hand-edit a generated file or a consumer's
  embedded fallback — edit the master and re-run sync. Drift is a bug, not a state to tolerate.
- **Generated output is deterministic and idempotent.** No timestamps, no random ordering. Re-running
  sync with an unchanged master writes zero bytes. This is what lets `--check` diff generated-on-disk
  against generated-from-master and gate CI.
- **Ambiguity is detected, resolved once, and remembered.** The engine surfaces ambiguities; each
  resolution is written to the lock keyed by a *stable* id. The next run auto-applies it — so re-syncs,
  and even adding a brand-new target whose decisions are already made, are seamless.
- **Consumers read the projection, fall back to an embedded default.** A target's runtime loads the
  generated map but degrades to a small embedded default if it's missing/corrupt — a generated artifact
  going missing must never silently break the consumer.
- **Validate the projection against the domain's contract.** Generated output must satisfy whatever
  schema/regex/allowlist the targets require; sync asserts this, it doesn't template blindly.
- **`check` is the gate; `sync` is the apply.** CI runs `--check` (read-only, nonzero on drift or
  unresolved ambiguity). Humans run `--sync` (writes) and `--resolve` (interactive, appends to lock).

## Quick navigation

| Situation | Read |
|---|---|
| Operate the existing bloodbank agent-hooks system (add an agent CLI, fix drift, resolve a mapping) | [references/reference-implementation.md](./references/reference-implementation.md) |
| Build a NEW master → multi-dialect propagation engine for another domain | [references/engine-design.md](./references/engine-design.md) + `assets/master.template.json`, `assets/mappings.lock.template.json` |
| Output drifts, sync isn't idempotent, a consumer broke, an ambiguity won't clear | [references/gotchas.md](./references/gotchas.md) |

## The three artifacts

| Artifact | Role | Hand-edited? |
|---|---|---|
| `*.master.json` (SSOT) | canonical model + per-target bindings/dialect | **yes — the only one** |
| `*.mappings.lock.json` | remembered resolutions for ambiguous/divergent mappings | only via `--resolve` (or a reviewed seed) |
| `sync.py` (engine) | detect → resolve → generate; `--check` / `--apply` / `--resolve` | yes (it's code) |

…producing, per target: its **native config** (the dialect file the tool actually loads) and,
optionally, a **machine map** the consumer reads at runtime (e.g. `event_map.generated.json`).

## The master's shape

The master separates *what* (a canonical catalog) from *how each target expresses it*:

- **catalog** — canonical entries keyed by id, each with a `role` (the cross-target normalization unit)
  plus whatever the domain needs (a type, a bucket, etc.).
- **targets** — per target: its `dialect`, output paths, a `runner`/command template, and **bindings**
  mapping the target's *native* names → a catalog entry + role + dialect detail (matcher, payload mode,
  timeouts, extra args).

`role` is the key idea: divergence is detected when the **same role maps to different canonical entries
across targets**. That is exactly the ambiguity the lock resolves.

## Workflow — operating an existing system

1. Edit the master (`hooks.master.json`): add/adjust catalog entries or a target's bindings.
2. `mise run hooks:check` (read-only). It reports drift (generated files stale) and **ambiguities**.
3. If an ambiguity is unresolved, resolve it once: `python3 sync.py --apply --resolve` (prompts and
   appends to the lock), or seed the lock entry by hand and re-check. A decision already in the lock
   applies automatically — nothing to do.
4. `mise run hooks:sync` to regenerate every target's native config + machine map (idempotent).
5. Verify: `mise run smoketest:agent-hooks-ssot` (every binding builds a contract+schema-valid output).

## Workflow — building the pattern for a new domain

1. Copy `assets/master.template.json` and `assets/mappings.lock.template.json`; fill the catalog +
   targets + bindings for your domain.
2. Adapt `sync.py` ([references/engine-design.md](./references/engine-design.md) gives the algorithm
   and each dialect renderer). Keep generation deterministic.
3. Point each consumer at its generated map with an embedded fallback (merge generated OVER default).
4. Wire `check` (CI gate) and `sync` (apply) tasks, plus a verifier that builds one output per binding
   and validates it against the domain's contract.
5. Seed the lock with the resolutions you make on first run; thereafter re-syncs are seamless.

## Out of scope

- **Versioning many files in parity** (`package.json`/`pyproject.toml`/tags) → use `mise-versioning`.
- **Defining the event schemas or naming contract** the agent-hooks system targets → that's
  `bloodbank/docs/event-naming.md` and `schemas/`, not this pattern.
- **Writing an individual hook script / publisher's data-shaping logic** → this skill owns the
  *propagation* of the mapping, not the per-event handler bodies.
- **Single-target config with no dialect or ambiguity dimension** (plain env substitution, one output)
  → just template it directly; the master/lock machinery is overkill.
