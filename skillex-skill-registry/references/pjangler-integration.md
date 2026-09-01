# pjangler Integration: the `skills.project-manifest` Parity Rule

`pj audit` and `pj migrate` enforce the packs contract inside a CommonProject repo. This file maps every audit detail string to its cause and its fix.

## Reading Order

| Task | Read |
|---|---|
| Run the audit / migration | [Commands](#commands) |
| Decode an audit failure | [Every check, decoded](#every-check-decoded) |
| Adopt legacy committed skills into the manifest | [`--accept-registry-matches`](#--accept-registry-matches) |
| Understand why a script "differs from the shipped template" | [The template byte-equality contract](#the-template-byte-equality-contract) |

## Commands

```bash
pj audit                                   # all rules, current repo
pj audit --json
pj migrate skills.project-manifest --dry-run
pj migrate skills.project-manifest
pj migrate skills.project-manifest --accept-registry-matches
pj migrate --all --dry-run
pj init <name>                             # bootstrap: registry entry + CommonProject + .project.json
```

`pj init` scaffolds the CommonProject template, which is what plants `.mise/scripts/sync-skills.py`, `.mise/scripts/provision-packs.py`, the `skills-sync` / `skills-provision-packs` tasks, the `.agents/skills.json` watch, and the `mise enter` hooks. A repo created by `pj init` starts in parity; drift is what `audit` catches later.

> **Verified caveat — every command above must be run through the repo build, not the `pj` on PATH.** The globally installed `pj` (`@delorenj/pjangler` 1.2.25 on PATH) is a stale publish. It does **not** carry `--accept-registry-matches` (`pj migrate --help` omits it), and its `dist/index.js` contains **zero** occurrences of the pack-era audit detail strings decoded below (`grep -c 'should be symlinks into their declared'` → `0`, vs `1` in the repo build). It still assumes the hardcoded BMAD `6.10.1-next.31` pin and knows nothing about `packs[]`, so on a migrated manifest it invents failures: in `/home/delorenj/code/automatic-ai` today it reports `✖ skills.project-manifest — 6 Skillex migration issue(s) detected` where the repo build reports `✔ Skillex skills manifest parity verified`.
> ```bash
> alias pjr='node /home/delorenj/code/33GOD/pjangler/dist/index.js'
> pjr audit                        # the audit these tables decode
> pjr migrate --help               # shows --accept-registry-matches
> grep -c accept-registry-matches "$(readlink -f "$(command -v pj)")"   # 0 → your pj is stale
> ```
> Same version string, different bytes. **None of the detail strings decoded in this file can be produced by the stale binary.** If a flag looks missing, or `pj audit` reports something this file does not document, run the repo's `dist/index.js` (or rebuild + reinstall) before concluding the feature does not exist or the docs are wrong. Full write-up: [gotchas.md](./gotchas.md#the-pj-on-path-is-a-stale-build-pj-audit-lies-and-migrate-flags-are-missing).

## Every check, decoded

Rule id: `skills.project-manifest`. Each bullet is a literal `details` string from `pjangler/src/parity/index.ts`.

### Manifest shape

| Detail | Cause | Fix |
|---|---|---|
| `.agents/skills.json missing or invalid JSON` | No manifest, or unparseable | Create it; `provision-packs.py` never clobbers invalid JSON |
| `.agents/skills.json should set inherit_global: true` | Missing/false | Set it; provisioning force-writes it |
| `.agents/skills.json should set registry to https://github.com/delorenj/skillex.git` | Missing/other | Set it |
| `$schema still points at the retired …/skillex/schemas/main/…; it should be …` | Dead URL (404s) | `pj migrate` rewrites it |
| `.agents/skills.json should set $schema to …` | Absent or unrecognized | `pj migrate` writes the canonical URL |
| `.agents/skills.json should define a skills array` | `skills` missing or not an array | Add `"skills": []` |
| `should record all N BMAD <version> pack entries as file:// sources` | The implicit BMAD pin's members are missing or stale in `skills[]` | `mise run skills-provision-packs` |
| `skills[] duplicates N declared pack member(s) and should drop them: …` | §6 redundancy — hand-expanded entries a declared pack now provides | `pj migrate skills.project-manifest` |

### Projection

| Detail | Cause | Fix |
|---|---|---|
| `N managed pack skill path(s) should be symlinks into their declared Skillex pack` | `.agents/skills/<name>` is missing, a real directory, or points somewhere else | `mise run skills-provision-packs` |
| `.agents/skills/<name> is committed but absent from .agents/skills.json` | A legacy committed skill directory nobody declares | See [`--accept-registry-matches`](#--accept-registry-matches) |
| `Run \`pj migrate skills.project-manifest --accept-registry-matches\` to map N unmanaged committed skill(s) into the manifest` | Same as above, summary line | Same |

`bmad-*` names are deliberately excluded from the unmanaged-skill sweep: pinned pack names are already validated as symlinks by this rule, and off-pack `bmad-*` trees are re-materialized by the `bmad.scaffold` rule on every run. Mapping them would be undone by the next BMAD install and re-reported forever.

### mise wiring

| Detail | Fix |
|---|---|
| `mise.toml should run the shipped project-local sync-skills.py engine via config_root` | Restore `run = "python3 '{{config_root}}/.mise/scripts/sync-skills.py' --scope project"` |
| `mise.toml should provision declared Skillex packs before syncing skills` | Add the `provision-packs.py` invocation |
| `mise.toml should run the pack provisioner before project skill sync` | Provisioner appears *after* sync in the file — reorder |
| `mise.toml still references the retired skills-provision-bmad task/provision-bmad-skills.py script` | Remove both |
| `mise.toml still invokes the missing bare sync-skills.py executable` | It is a Python file, not an executable on PATH — use `python3 '{{config_root}}/…'` |
| `mise.toml should watch .agents/skills.json` | Add the `[[watch_files]]` block |
| `mise.toml should define a skills-sync task` | Add `[tasks.skills-sync]` |
| `skills-sync task should depend on skills-provision-packs` | Add `depends = ["skills-provision-packs"]` |
| `mise.toml still contains legacy skill-link wiring` | Remove `link-project-skills-to-clis.sh`, `unlink-project-skills-from-clis.sh`, `[tasks.skills-relink]` |

### Scripts

| Detail | Cause | Fix |
|---|---|---|
| `.mise/scripts/provision-bmad-skills.py is the retired BMAD-only provisioner and should be replaced by .mise/scripts/provision-packs.py` | Pre-packs repo | `pj migrate` writes the new file and removes the old one |
| `Skillex pack provisioning script is missing or unsafe` / `Project-local skills sync engine is missing or unsafe` | Absent, a symlink, or not a regular file | `pj migrate`. A present-but-unsafe file makes the finding **not fixable** — resolve by hand |
| `… differs from the shipped template` | Byte mismatch — see below | `pj migrate` overwrites with the template |
| `… is not executable` | Mode bits lost | `chmod +x` |

### Other

| Detail | Fix |
|---|---|
| `.mise/scripts/link-project-skills-to-clis.sh is a legacy symlink-era script and should be removed` | Delete it |
| `.agents/local.example.json still documents legacy skills overrides; drop the skills section` | Remove the `skills` key |
| `CLI skill topology: …` | A structural problem in the CLI skill directories. Makes the finding **not fixable**; `pj migrate` returns `blocked`. Fix by hand first |

An `optional: true` pack that is missing is reported as an advisory in the summary (`Skillex skills manifest parity verified (N optional pack(s) skipped)`), not as a failure.

## The template byte-equality contract

`pj audit` compares the repo's `.mise/scripts/provision-packs.py` and `.mise/scripts/sync-skills.py` **byte for byte** against `templateCommonProjectText(ctx, rel)` — the file at `pjangler/templates/commonproject/template/.mise/scripts/<name>.py`. One changed character produces `differs from the shipped template`.

`templates/commonproject` is a **git submodule** (`git@github.com:delorenj/CommonProject.git`, branch `main`). Editing the repo's copy is always wrong. Full procedure: [gotchas.md](./gotchas.md#project-local-skills-sync-engine-differs-from-the-shipped-template).

## `--accept-registry-matches`

By default `pj migrate skills.project-manifest` only **reports** legacy committed skills in `.agents/skills/` that no pack owns and no manifest entry names:

```
proposed mapping: skf-forger -> registry_path all-skills/skf-forger (exact content match)
17 legacy committed skill(s) left untouched; re-run with --accept-registry-matches to apply
```

With the flag, each one is:

1. **Moved** — never deleted — into `.agents/skills.bak/<name>`.
2. Recorded in `skills[]` as either
   - `{"name": …, "registry_path": "all-skills/<name>"}` when the tree is an **exact content match** for a registry skill (sha256 over the whole tree; `null` — never a match — for anything containing a symlink, device, fifo, or unreadable path), searching `all-skills/<name>` then `skills/<name>`; or
   - `{"name": …, "source": "file:///…/.agents/skills.bak/<name>"}` otherwise.

Notes:

- `.agents/skills.bak/` is a **sibling** of `.agents/skills/`, so the audit walk can never see its own backups and loop.
- It is deliberately **not** gitignored: an entry mapped to `file://…/.agents/skills.bak/<name>` makes that directory the manifest's source of truth, so ignoring it would break every other clone.
- If `.agents/skills.bak/<name>` already exists, that skill is **skipped** rather than overwritten.
- Registry matching is offline. With no local checkout on the ladder you get:
  `No local https://github.com/delorenj/skillex.git checkout is available; registry matching is skipped (set PJ_SKILLS_REGISTRY_ROOT or let skills-sync clone the registry)` — and every skill falls back to the `file://` backup form.

Always run `--dry-run` first, then re-run `pj audit`.

## Where the shared logic lives

| Surface | File | Owns |
|---|---|---|
| Sync engine | `pjangler/templates/commonproject/template/.mise/scripts/sync-skills.py` | resolve + verify packs, fan out to six CLI dirs |
| Provisioner | `…/template/.mise/scripts/provision-packs.py` | transactional projection into `.agents/skills/` (imports the resolver verbatim) |
| Parity, packs | `pjangler/src/parity/pack.ts` | pack-agnostic validator: inventory, payload, sealed verification, version ordering, minimal TOML reader |
| Parity, rule | `pjangler/src/parity/index.ts` | `skills.project-manifest` audit + migrate, registry ladder, redundancy, legacy mapping |
| Author side | `skillex/src/skillex/commands/pack.py` + `core/{loader,linter,payload,renderer}.py` | `pack render` / `verify` / `manifest` |
| Schema | `skillex/skills.schema.json` | the `$schema` target |

All of them must resolve every name to the same path. When two disagree, the cause is nearly always a divergent copy of a helper that was supposed to be imported — that is exactly why `provision-packs.py` imports `manifest_entry_source_path`, `is_contained_by` and `PackScope` from `sync-skills.py` rather than re-implementing them.
