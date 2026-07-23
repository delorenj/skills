---
name: agent-config-fanout
description: |
  Keep one hand-edited master config and generate per-agent CLI configs from it. Covers SSOT fan-out for agent hooks and skills: master-to-dialect propagation, ambiguity lock files, drift checks, and the Bloodbank services/agent-hooks reference implementation. Use for hooks.master.json, hooks.mappings.lock.json, generated-config drift, fan-out, SSOT, agent hooks, defer_to_global, .agents/local.json, sync.py, project-scoped hooks, skill fan-out, and new agent CLI dialects. Do NOT use for using pjangler to create projects or adoption checklists (33god-projects), event schemas or Bloodbank topology (bloodbank-integration), versioning (mise-versioning), or single-target config.
pipeline-status: new
---

# Agent Config Fan-out

Route here when the job is to propagate **one hand-edited master config** into the native config formats of multiple agent CLIs (Claude, Codex, Kimi, Hermes, Copilot, future tools), or to build that propagation engine for a new domain.

## Operating Principles

- **One hand-edited source of truth.** The master file (e.g. `hooks.master.json`) is the only artifact edited by hand. Every per-target config and machine map is generated.
- **Ambiguity is detected, resolved once, and remembered.** Divergent mappings across targets become lock-file entries (`hooks.mappings.lock.json`). Re-syncs apply them automatically.
- **Generated output is deterministic and idempotent.** A `--check` gate must return zero changed bytes when the master is unchanged.
- **Consumers fall back to an embedded default.** A generated map going missing must not break the consumer; generated values merge over a small embedded fallback.
- **Publishers stay normalized.** In the Bloodbank reference, every agent CLI invokes one canonical entrypoint (`~/.agents/hooks/bloodbank/publish.py --client <agent> --hook <event>`). Per-client code belongs behind adapters; legacy per-client `publish.py` files are wrappers, not new implementation homes.
- **`check` gates CI; `sync`/`apply` writes; `--resolve` records decisions.** Never hand-edit a generated file.

## Triage Table

| You want to… | Read first | Then |
|---|---|---|
| Build a NEW master → multi-dialect propagation engine | [references/ssot-fanout-engine.md](references/ssot-fanout-engine.md) | `assets/master.template.json`, `assets/mappings.lock.template.json` |
| Operate or extend the bloodbank `services/agent-hooks` reference instance — add an agent CLI, edit `hooks.master.json`, fix drift | [references/ssot-fanout-reference.md](references/ssot-fanout-reference.md) | [references/ssot-fanout-gotchas.md](references/ssot-fanout-gotchas.md) |
| Output drifts, sync isn't idempotent, an ambiguity won't clear, a merge ate sibling hooks | [references/ssot-fanout-gotchas.md](references/ssot-fanout-gotchas.md) | the matching engine/reference topic |
| Adopt the per-dev, committed project-scoped hook + skill fan-out layer in a repo | → **33god-projects** `references/project-scoped-hooks.md` | this skill only for the generic engine mechanics |

## Cross-Cutting Rules

- `role` is the normalization unit. Bindings that represent the same lifecycle moment must share the same `role` or divergence detection cannot see them.
- Lock keys are exact: `role:<role>` or `type:<value>` as emitted by `--check --json`.
- Renderers must be pure: no timestamps, no RNG, preserve master binding order, serialize consistently.
- Install must be surgical: merge only this system's entries into operator-owned files (e.g. `~/.claude/settings.json`), preserve siblings, back up first.
- Fleet-style targets (Hermes) discover live agents from `~/.hermes/agents-registry.yaml`; the target set is data, not hardcoded.

## Out of Scope

- **Project bootstrap decisions** (when to adopt hooks, per-repo checklist, `mise enter/leave` adoption) → `33god-projects`.
- **Event schemas or Bloodbank topology** the hooks emit/consume → `bloodbank-integration`.
- **Versioning many files in parity** → `mise-versioning`.
- **Single-target config** with no dialect/ambiguity dimension → template directly; the master/lock machinery is overkill.
- **Raw hook script bodies** that shape/publish individual events → owned by the canonical publisher and client adapters, not this propagation skill.
