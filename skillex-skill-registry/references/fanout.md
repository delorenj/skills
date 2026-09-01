# Fan-out: `provision-packs.py`, `sync-skills.py`, and the mise tasks

How a manifest becomes symlinks on disk. This file covers the registry-operator view of the two shipped scripts. For the generic SSOT fan-out **engine pattern** (master→dialect propagation, lock files, drift gates), read `agent-config-fanout` instead.

## Reading Order

| Task | Read |
|---|---|
| Understand the two-stage pipeline | [The pipeline](#the-pipeline) |
| Wire or repair the mise tasks | [mise wiring](#mise-wiring) |
| Find out where a skill should have landed | [The six supported CLIs](#the-six-supported-clis) |
| Clean up `.augment/skills`, `.cursor/skills`, … | [Retired directories](#retired-directories) |
| Pin a pack to a local tree for testing | [Environment overrides](#environment-overrides) |
| Understand rollback / safety behaviour | [Transactional guarantees](#transactional-guarantees) |

## The pipeline

```
.agents/skills.json
        │
        ├─(1) provision-packs.py ──► <repo>/.agents/skills/<name> -> <pack-root>/<name>
        │        transactional; also rewrites .agents/skills.json
        │
        └─(2) sync-skills.py --scope project ──► <repo>/<cli>/skills/<name> -> resolved path
                 six CLI dirs; symlink-hostile preflight
```

Order is load-bearing: provision materializes `.agents/skills/`, then sync fans that out. The mise task graph and the `mise enter` hooks both encode it.

### `provision-packs.py`

Generic replacement for the retired `provision-bmad-skills.py`. It reads `<cwd>/.agents/skills.json`, resolves and verifies every `packs[]` entry, and materializes each member as a symlink under `.agents/skills/`.

Pack resolution and verification are **imported verbatim** from the sibling `sync-skills.py` (via `importlib.util.spec_from_file_location`, because `sync-skills.py` is not a valid module name). There is exactly one resolver; a pack that provisions cleanly is a pack that syncs cleanly, with byte-identical error messages.

What it owns:

- Transactional projection into `.agents/skills/`, with full rollback on any failure.
- Atomic rewrite of `.agents/skills.json`, preserving its mode, force-setting:
  - `$schema` → `https://raw.githubusercontent.com/delorenj/skillex/main/skills.schema.json`
  - `inherit_global` → `true`
  - `registry` → `https://github.com/delorenj/skillex.git`
- Pruning `skills[]` entries that §6 marks redundant against the manifest's own declared packs.
- The **implicit BMAD pin**.

```bash
cd <repo>
python3 .mise/scripts/provision-packs.py
# → "provision-packs: N symlink(s) updated"
```

Takes no arguments. Fails with `SystemExit` and the message *"Skillex pack provisioning failed: …; declare the pack in .agents/skills.json packs[] or install it locally"*.

#### The implicit BMAD pin

When the manifest declares **no** `bmad` pack, `provision-packs.py` synthesizes one:

```python
{"name": "bmad", "version": "6.10.1-next.31", "sealed": True, "optional": False}
```

It deliberately carries **no `source`** — it walks the same resolution ladder as any declared pack, so `bmad@6.10.1-next.31` can never mean two different roots in one process. `sealed: True` is supplied from the manifest side because that pack's `pack.toml` predates `[policy] sealed`, so the pinned release is still verified byte-for-byte.

Unlike declared packs, the implicit pin's members are **also written back into `skills[]`** as `file://` entries — the historical behaviour. Declaring `{"name":"bmad", …}` in `packs[]` takes over and the pin is not consulted.

### `sync-skills.py`

```bash
python3 .mise/scripts/sync-skills.py --scope project
python3 .mise/scripts/sync-skills.py --scope global
python3 .mise/scripts/sync-skills.py --scope project --prune-retired
```

| Flag | Meaning |
|---|---|
| `--scope global\|project` | **Required.** Selects the manifest and the CLI-dir table. `global` → `~/.agents/skills.json`, base `$HOME`. `project` → `$CWD/.agents/skills.json`, base `$CWD`. |
| `--prune-retired` | Opt in to removing managed symlinks left in retired CLI dirs. Without it, they are only **reported**. |

`--scope project` loads the global manifest as a lower layer only when the project manifest sets `inherit_global: true`.

It is the **only** surface authorized to clone a registry, and it clones only when no checkout exists anywhere on the ladder. An existing checkout is never `git pull`ed as a side effect of resolution.

## The six supported CLIs

`CLI_SKILL_DIRS` is a per-scope mapping, relative to `$HOME` for `--scope global` and to the project root for `--scope project`. Only opencode differs between scopes.

| CLI | global | project |
|---|---|---|
| Claude Code | `.claude/skills` | `.claude/skills` |
| Codex | `.codex/skills` | `.codex/skills` |
| Gemini | `.gemini/skills` | `.gemini/skills` |
| Copilot | `.copilot/skills` | `.copilot/skills` |
| **opencode** | **`.config/opencode/skills`** | **`.opencode/skills`** |
| Kimi Code | `.kimi-code/skills` | `.kimi-code/skills` |

A CLI directory is only written when its **parent** already exists — the sync does not create `.gemini/` for you, it creates `.gemini/skills/` inside an existing `.gemini/`.

### The canonical alias

Generated projects may expose the single managed projection to a CLI as `<cli>/skills -> .agents/skills`. This is the **only** symlinked CLI skills directory accepted, and it is matched **lexically** (never by resolving an arbitrary symlink, which would let cleanup traverse outside the project), then confirmed to resolve to the real managed projection. Every CLI that aliases `.agents/skills` names the same destination, so it is projected into once.

Inside that alias, a **real** (non-symlink) skill directory is never replaced — the sync fails before mutating anything rather than `rmtree` a hand-authored skill.

### Sync fails loudly when it has nowhere to write

If skills resolve but no supported CLI directory exists under the base, the sync **raises** rather than reporting success. Silently unprojecting every skill on a topology change is the failure this guards.

## Retired directories

Never written to again:

```
.augment/skills   .hermes/skills   .openclaw/skills
.kimi/skills      .crush/skills    .cursor/skills
```

Note `.kimi/skills` (retired) vs `.kimi-code/skills` (supported) — different CLIs.

Retired directories are **never auto-deleted**. `--prune-retired` removes **only** entries that are:

1. symlinks (real directories are never touched), **and**
2. whose `realpath` resolves **inside a known managed root**.

Managed roots = `~/.agents/.cache`, `~/code/skillex`, `$PJ_SKILLS_REGISTRY_ROOT` (when set), plus every registry checkout resolved this run and every pack root / pack family root touched this run. An unmanaged symlink — one pointing at your own tree — is left alone.

Without the flag:

```
sync-skills: 3 managed symlink(s) remain in retired CLI skill dirs under /home/…;
re-run with --prune-retired to remove them:
  would prune /home/…/.cursor/skills/foo -> /home/…/code/skillex/all-skills/foo
```

### `~/.hermes/skills` is NEVER pruned

`NEVER_PRUNE_DIRS = {".hermes/skills"}`. It is a **writable Hermes runtime OVERLAY**, not a projection of this manifest: the Hermes agent writes into it and it wins on name collision against the read-only base pack. It is excluded from the prune walk entirely — never written, never reported, never removed. Its contents are `33god-agent-fleet-operations` territory.

## mise wiring

From `pjangler/templates/commonproject/template/mise.toml.jinja`:

```toml
[[hooks.enter]]
script = "python3 '{{config_root}}/.mise/scripts/provision-packs.py'"
[[hooks.enter]]
script = "python3 '{{config_root}}/.mise/scripts/sync-skills.py' --scope project"

[[watch_files]]
patterns = [".agents/skills.json"]
task = "skills-sync"

[tasks.skills-sync]
description = "Sync skills from manifest to local CLI dirs"
depends = ["skills-provision-packs"]
run = "python3 '{{config_root}}/.mise/scripts/sync-skills.py' --scope project"

[tasks.skills-provision-packs]
description = "Provision every Skillex pack declared in .agents/skills.json"
run = "python3 '{{config_root}}/.mise/scripts/provision-packs.py'"
```

Retired names that `pj audit` reports and `pj migrate` removes: task `skills-provision-bmad`, script `.mise/scripts/provision-bmad-skills.py`, tasks `[tasks.skills-relink]`, and the scripts `link-project-skills-to-clis.sh` / `unlink-project-skills-from-clis.sh`.

```bash
mise run skills-sync          # provision then fan out
mise run skills-provision-packs
```

## Environment overrides

| Variable | Effect |
|---|---|
| `PJ_SKILLS_REGISTRY_ROOT` | Replaces the whole registry ladder with one checkout. In `sync-skills.py` an unusable value is a hard `PackUnavailable`, not a fallback. |
| `PJ_PACK_ROOT_<NAME>` | Pins one pack root. `<NAME>` is the pack name uppercased with every non-`[A-Z0-9]` byte replaced by `_` — `hermes-base` → `PJ_PACK_ROOT_HERMES_BASE`. Applied by `provision-packs.py` by rewriting the entry's `source` to the override's `file://` URI. |
| `PJ_BMAD_PACK_ROOT` | Legacy first-class alias for `PJ_PACK_ROOT_BMAD`. |

An override is skipped when the entry already sets `source` or `registry_path` — an explicit manifest source always wins.

## Transactional guarantees

Both scripts are deliberately hardened; do not weaken these when editing the template.

- **Preflight, then re-validate at the mutation boundary.** Every destination directory is validated *before* any registry clone, cache creation, or link change — so one unsafe or broken symlink produces **zero** mutation — and the whole destination chain is re-checked immediately before each individual mutation, because preflight and mutation are not atomic.
- **No symlinked destination directories**, except the canonical `<cli>/skills -> .agents/skills` alias.
- **Nothing escapes its root.** A skill destination must be exactly one component below its CLI directory.
- **Payloads contain only regular files and real directories**, opened `O_NOFOLLOW` and confirmed `S_ISREG` on the file descriptor.
- **Names are one safe path component** — for manifest names, inventory names, and every path inside `SHA256SUMS`.
- **`provision-packs.py` is transactional.** Affected entries are moved into a temp transaction dir; a failure at any point restores them and the original manifest bytes/mode, and removes `.agents/skills` / `.agents` if it created them. After applying, it **re-resolves every pack** and fails (rolling back) if the inventory changed since preflight.
