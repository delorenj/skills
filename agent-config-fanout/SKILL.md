---
name: agent-config-fanout
description: |
  Keep one hand-edited master config and generate per-agent CLI configs from it. Covers SSOT fan-out for agent hooks and skills: master-to-dialect propagation, ambiguity lock files, drift checks, skill packs, and the Bloodbank services/agent-hooks reference implementation. Use for hooks.master.json, hooks.mappings.lock.json, generated-config drift, fan-out, SSOT, agent hooks, inherit_global, .agents/skills.json, sync.py, sync-skills.py, provision-packs.py, skills-provision-packs, project-scoped hooks, skill fan-out, and new agent CLI dialects. Also use for skill packs: packs[], pack.toml, SHA256SUMS, sealed/immutable packs, payload verification, pack version resolution, include/exclude, and the six supported CLI skill dirs. Do NOT use for using pjangler to create projects or adoption checklists (33god-projects), event schemas or Bloodbank topology (bloodbank-integration), versioning (mise-versioning), or single-target config.
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
- **Destination topology is a security boundary.** In the skill fan-out engine every destination is validated *before* any clone, cache write, or link change, and re-validated at each mutation — one unsafe or broken symlink must produce **zero** mutation. Packs tighten this further: sealed payloads are checksum-verified and may contain no symlinks at all. See [references/skill-packs.md](references/skill-packs.md) → *Security invariants*.
- **A pack is one declaration, not a hand-expanded list.** `packs[]` names a versioned directory of skills; its members are resolved, verified, and fanned out as a unit. **Redundancy pruning runs BEFORE override:** a `skills[]` entry that a pack declared in the *same* manifest already provides is dropped and the pack member wins — it is not an override. Only entries that SURVIVE pruning override a pack member of the same name. ("An explicit `skills[]` entry always wins" was the pre-revision rule and a shipped bug.) See [references/skill-packs.md](references/skill-packs.md) → *Precedence*.

## Triage Table

| You want to… | Read first | Then |
|---|---|---|
| Build a NEW master → multi-dialect propagation engine | [references/ssot-fanout-engine.md](references/ssot-fanout-engine.md) | `assets/master.template.json`, `assets/mappings.lock.template.json` |
| Operate or extend the bloodbank `services/agent-hooks` reference instance — add an agent CLI, edit `hooks.master.json`, fix drift | [references/ssot-fanout-reference.md](references/ssot-fanout-reference.md) | [references/ssot-fanout-gotchas.md](references/ssot-fanout-gotchas.md) |
| Output drifts, sync isn't idempotent, an ambiguity won't clear, a merge ate sibling hooks | [references/ssot-fanout-gotchas.md](references/ssot-fanout-gotchas.md) | the matching engine/reference topic |
| Declare, resolve, seal, or verify a **skill pack** (`packs[]`, `pack.toml`, `SHA256SUMS`), or wire `provision-packs.py` / `skills-provision-packs` — the ENGINE contract | [references/skill-packs.md](references/skill-packs.md) | `skillex pack render` / `skillex pack verify` |
| **Operate the registry itself** — what is in `~/code/skillex` today, cut/bump/seal a pack, curate `all-skills/` and `skill-sets/`, fix a broken `.agents/skills.json`, decode a `pj audit` failure | → **`skillex-skill-registry`** at `/home/delorenj/code/33GOD/skills/skillex-skill-registry/` | this skill only for the fan-out engine mechanics |
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
