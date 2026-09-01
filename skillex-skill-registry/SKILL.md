---
name: skillex-skill-registry
description: |
  Operate the Skillex skill registry at ~/code/skillex: author, version, render, seal and verify PACKS; curate all-skills/ and skill-sets/; declare packs and skills in .agents/skills.json. Use when cutting or upgrading a pack, running skillex pack render/verify/manifest, editing a global or project .agents/skills.json, resolving packs[] vs skills[] precedence and redundant entries, wiring the mise skills-sync and skills-provision-packs tasks, or fixing pj audit failures on skills.project-manifest. Triggers: skillex, skill pack, packs[], pack.toml, SHA256SUMS, sealed pack, payload_files, all-skills, skill-sets, skills.schema.json, inherit_global, PJ_SKILLS_REGISTRY_ROOT, provision-packs.py, sync-skills.py, accept-registry-matches, bmad pack. Do NOT use for: SSOT fan-out engine mechanics or hooks.master.json (agent-config-fanout); SKILL.md content or topology (skill-creator); pjangler Commands/Recipes (project-jangler); project bootstrap (33god-projects); ~/.hermes/skills overlay (33god-agent-fleet-operations).
---

# Skillex Skill Registry

Registry-operations hub for `~/code/skillex`. Everything here is about **which skills exist, where they live, how they are bundled into packs, and how a manifest turns that into a projection on disk** — never about what a SKILL.md says.

The generic SSOT fan-out ENGINE (master→dialect propagation, lock files, drift gates, and the mechanics of `sync.py` / `sync-skills.py` as a fan-out pattern) belongs to **`agent-config-fanout`**; its `references/skill-packs.md` is the engine-side view of the same contract. This skill is the operator's view: run the registry, cut packs, fix broken manifests.

## Routing

| Task | Read |
|---|---|
| Where does a skill/pack/skill-set live? What is in the registry today? | [references/topology.md](./references/topology.md) |
| Write or fix a `.agents/skills.json`; precedence; redundancy pruning; resolution ladder | [references/manifest.md](./references/manifest.md) |
| Cut a new pack, bump a pack version, render/seal/verify, `pack.toml` anatomy | [references/pack-authoring.md](./references/pack-authoring.md) |
| Worked upgrade: bmad `6.10.1-next.31` → `6.10.2` end to end | [references/pack-authoring.md](./references/pack-authoring.md#worked-example-upgrading-the-bmad-pack) |
| Skills not appearing in a CLI; mise tasks; the six CLI dirs; retired dirs; `--prune-retired` | [references/fanout.md](./references/fanout.md) |
| `pj audit` / `pj migrate` on `skills.project-manifest`; `--accept-registry-matches` | [references/pjangler-integration.md](./references/pjangler-integration.md) |
| Something is broken and you need symptom → cause → fix → why | [references/gotchas.md](./references/gotchas.md) |

## Operating Principles

- **Three roles, one catalog.** `packs/` are SOURCES, `skill-sets/` are SELECTIONS, `all-skills/` is the CATALOG. Confusing them is the root of most registry damage.
- **Never edit a repo's `.mise/scripts/*.py`.** Those are byte-compared against the pjangler CommonProject template. Edit the template, propagate, re-audit.
- **Resolution is offline by construction.** `pj audit` and `skillex pack manifest` NEVER clone or fetch. Only `sync-skills.py` may clone, and only when no checkout exists at all.
- **Sealing is opt-in and one-way.** A manifest may TIGHTEN a pack's seal, never loosen it.
- **Symlinks are never pack content.** A pack member must be a real directory holding a regular `SKILL.md`. Symlink-composed trees are skill-sets, not packs.
- **Verify before you trust GREEN.** A pack can resolve, pass, and still be the wrong copy on disk. Always print the resolved root.

## Topology in one screen

```
~/code/skillex/                      git@github.com:delorenj/skillex.git
├── all-skills/<name>/SKILL.md       CATALOG — one real dir per skill, the SSoT
├── skill-sets/<set>/<name>          SELECTIONS — symlinks into all-skills/ (or 33GOD/skills/)
├── packs/<name>/pack.toml           SOURCE — flat pack
├── packs/<name>/<version>/          SOURCE — versioned pack (pack.toml + SHA256SUMS)
└── skills.schema.json               canonical $schema target
```

Consumers:

```
~/.agents/skills.json                GLOBAL manifest      → --scope global
<repo>/.agents/skills.json           PROJECT manifest     → --scope project
<repo>/.agents/skills/<name>         pack projection written by provision-packs.py
<home|repo>/<cli>/skills/<name>      symlinks written by sync-skills.py (six CLIs)
```

## Command surface

Read-only commands marked ✅ were **executed and their output confirmed**. Commands marked ⚠️ **mutate state and were NOT executed** — read the implementation before relying on them. Commands marked ❌ **do not work on the `pj` currently on PATH**.

```bash
# --- registry side (run from ~/code/skillex) — all read-only ---
uv run skillex pack list                                  # ✅ every pack root + version
uv run skillex pack verify packs/bmad/6.10.2              # ✅ contract check; exit 1 on error
uv run skillex pack verify packs/hermes-base/0.18.2 --sealed   # ✅ 14 SKILL_MD_MISSING + SUMS_MISSING, exit 1
uv run skillex pack render packs/<name>/<ver> --name <name> --version <ver> --check   # ✅ --check writes nothing
uv run skillex pack render …                              # ⚠️ WITHOUT --check this WRITES pack.toml + SHA256SUMS
uv run skillex pack manifest <repo>/.agents/skills.json --verify   # ✅ resolve packs[] offline

# --- project side — ALL of these mutate the repo; none were executed here ---
python3 .mise/scripts/provision-packs.py                  # ⚠️ materializes packs into .agents/skills/
python3 .mise/scripts/sync-skills.py --scope project      # ⚠️ writes/removes symlinks in six CLI dirs
python3 .mise/scripts/sync-skills.py --scope global       # ⚠️ same, under $HOME
python3 .mise/scripts/sync-skills.py --scope project --prune-retired   # ⚠️ DELETES retired CLI dirs
mise run skills-sync                                      # ⚠️ runs skills-provision-packs, then the sync

# --- parity side: use the REPO BUILD, the pj on PATH is stale ---
alias pjr='node /home/delorenj/code/33GOD/pjangler/dist/index.js'
pjr audit                                                 # ✅ read-only, verified
pj audit                                                  # ❌ stale build — invents pre-pack-era failures
pjr migrate skills.project-manifest --dry-run             # ✅ read-only, verified
pjr migrate skills.project-manifest --accept-registry-matches   # ⚠️ REWRITES the manifest
pj migrate … --accept-registry-matches                    # ❌ flag absent from the installed pj
```

> **The `pj` on PATH is a stale publish.** It has zero occurrences of `accept-registry-matches` and zero of the pack-era audit detail strings, yet reports the same version (`1.2.25`) as the repo build. Every `pj` invocation in this skill means the repo build. See [gotchas](./references/gotchas.md#the-pj-on-path-is-a-stale-build-pj-audit-lies-and-migrate-flags-are-missing).

`skillex pack render --help` and `skillex pack verify --help` **crash** (exit 1) — see [gotchas](./references/gotchas.md#the-render-and-verify-help-output-crashes-with-markuperror). Read the flags from [pack-authoring.md](./references/pack-authoring.md) instead.

## Decision tree: which lever do I pull?

```
Want a skill available everywhere?
├─ It is one skill, hand-maintained      → add to `skills[]` in ~/.agents/skills.json
├─ It is a coherent bundle you ship      → cut a pack, declare it in `packs[]`
└─ It is a curated loadout of existing
   catalog skills                        → skill-sets/<set>/ symlinks (NOT a pack)

A declared pack is not showing up?
├─ Does it resolve?                      → `skillex pack manifest … --verify` (prints the root)
├─ Does it verify?                       → `skillex pack verify <root>`
├─ Did it get projected?                 → ls <repo>/.agents/skills/<name>
└─ Did it get fanned out?                → ls <repo>/.claude/skills/<name>

`pj audit` fails on skills.project-manifest?
└─ → references/pjangler-integration.md (each detail string maps to one check)
```

## Cross-cutting rules

1. **The manifest precedence order is `global packs[] → global skills[] → project packs[] → project skills[]`, but §6 redundancy pruning runs FIRST.** A `skills[]` entry a declared pack already provides is *redundant*, not an override — it is dropped, and the pack member wins. Only entries that SURVIVE pruning override pack members. Getting this backwards was a shipped bug. Full rules and a live worked example: [manifest.md](./references/manifest.md#precedence).
2. **Redundancy is scoped to ONE manifest.** A project `skills[]` entry is weighed only against packs declared in the *project* manifest, never against global packs.
3. **`packs/<name>/` is a family, not an extent.** `packs/bmad/6.10.2` and `packs/bmad/6.10.1-next.31` are different packs. Only names in the resolved pack's DECLARED inventory are shadowed across sibling versions.
4. **The registry-root ladder is `PJ_SKILLS_REGISTRY_ROOT` → `~/.agents/.cache/registries/<sanitized-url>` → `~/code/skillex`,** where `<sanitized-url>` is `re.sub(r"[^a-zA-Z0-9]", "_", url)`. Three surfaces compute that name and must agree byte-for-byte.
5. **`~/.hermes/skills` is a writable Hermes runtime OVERLAY.** It is never written, never reported, never pruned — it is excluded from the prune walk entirely.
6. **`$schema` is `https://raw.githubusercontent.com/delorenj/skillex/main/skills.schema.json`.** The old `.../skillex/schemas/main/...` URL 404s; it is accepted on read, reported by audit, rewritten by migrate.
7. **Every registry mutation is followed by a verify.** `skillex pack render` then `skillex pack verify`; `pj migrate` then `pj audit`.

## Out of scope

- **Generic SSOT config fan-out engine mechanics** — `hooks.master.json`, dialect mappings, `hooks.mappings.lock.json`, generated-config drift gates → `agent-config-fanout`.
- **Authoring SKILL.md content** — topology (standalone/member/hub), `references/` taxonomy, description keyword density, gotcha prose style → `skill-creator`.
- **Developing pjangler itself** — Commands, Recipes, the CLI/MCP server, template authoring → `project-jangler`.
- **Bootstrapping a 33god project** — `pj init`, `.project.json`, Hermes PM provisioning, adoption checklists → `33god-projects`.
- **Hermes fleet operations** — `~/.hermes/fleet.env`, `config.yaml` `skills.external_dirs`, systemd units, and what lives inside the `~/.hermes/skills` overlay → `33god-agent-fleet-operations`.
- **mise task syntax in general** → `mise-tasks`; **version parity across many files** → `mise-versioning`.
