---
name: pjangler-parity-rules
description: Develop pjangler parity rules in src/parity/index.ts.
---

# Pjangler Parity Rules

Location: `src/parity/index.ts` in the pjangler repo.

## Architecture

Each parity rule is an object with:
- `id` — dotted name (e.g. `systemd.sentinel`, `hermes.registry-parity`)
- `title` — human-readable description
- `audit(ctx)` — returns `{ status, summary, details, fixable }`
- `migrate(ctx, finding)` — attempts to fix what audit caught; returns `{ status, summary, changedFiles, details }`

`ctx` contains: `repoRoot`, `pjanglerRoot`, `homeDir`, `dryRun`.

Rules are in the `RULES` array. `getParityRuleIds()` returns all IDs.

## Key functions

- `discoverRoles(repoRoot)` — walks `agents/hermes/*/role.yaml`, returns `RoleMeta[]` with `agentId`, `roleDir`, `roleYamlPath`, etc.
- `ownedRegistryEntries(registry, repoRoot)` — filters registry entries whose `role_dir` resolves to the same project root as `repoRoot`. Uses `realOrSelf(dirname(dirname(dirname(roleDir))))` comparison.
- `realOrSelf(path)` — `realpathSync` with fallback to the input string.
- `safeReadText(path)` — reads a file, returns `null` if it doesn't exist.

## Build and test

```bash
bun run typecheck && bun run build && bun run test
node dist/index.js audit          # run all rules
node dist/index.js migrate --all  # fix all fixable rules
```

## Pitfalls

### Profile-based / report-only rules

Some rules wrap a dedicated audit profile (e.g. the `momo-lifecycle-plane` profile that checks whether a repo is ready for the Momo PM orchestrator lifecycle). These rules cannot be fully auto-repaired by `pj migrate` and must be guarded so `pj project init` does not endlessly select them on legacy repos. See the `pjangler-parity` skill in the 33GOD PM runtime for the full recipe, including the guard pattern and the `momo-lifecycle-plane` regression-test fixture.

### `ownedRegistryEntries` scoping after a repo move

`ownedRegistryEntries` filters by `realOrSelf(repoRoot)`. After a repo moves (e.g. `code/pjangler` to `code/33GOD/pjangler`), registry entries with stale `role_dir` paths resolve to the old location, not the new `repoRoot`. The migrate loop over `ownedRegistryEntries` never sees them, so repoint logic doesn't fire even though audit catches the mismatch.

**Fix pattern**: Walk `roles` from `discoverRoles()` and look up each agent's entry in the registry by `agentId` directly. This mirrors what the audit does (it also walks `roles` and looks up by `agentId`).

### Systemd unit staleness

The `systemd.sentinel` migrate checks whether unit files exist and enables them. But after a repo move, unit files still exist with stale `ExecStart`/`WorkingDirectory` paths. The consumer crashes on start.

**Fix pattern**: Read each unit file and check whether it contains `/agents/hermes/` but not the current `role.roleDir`. If stale (or missing), re-run the provisioning script (`70-systemd.sh`) with `FORCE_SYSTEMD=1` to regenerate units, instead of just enabling them.

### Migrate must fix what audit catches

The audit and migrate functions can have different scoping. Audit walks `roles` and looks up registry entries by `agentId`; migrate walks `ownedRegistryEntries` which scopes by repo root. When these differ (repo move, stale paths), migrate silently no-ops while audit fails. Always ensure migrate covers the same entries audit checks.
