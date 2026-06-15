# SSOT config fan-out — the engine pattern & how to build one

Keep one hand-edited master file and **generate** every downstream config from it. The targets are
heterogeneous — each speaks its own dialect (different key names, nesting, invocation shape) — so the
master maps a *canonical* model onto each target. When two targets would map the "same thing"
differently, or a mapping is otherwise ambiguous, the decision is made once and recorded in a lock file
so the next sync applies it automatically.

Canonical instance: `services/agent-hooks/hooks.master.json` in bloodbank — operate/copy it via
[ssot-fanout-reference.md](./ssot-fanout-reference.md); symptoms & fixes in
[ssot-fanout-gotchas.md](./ssot-fanout-gotchas.md). This file is the design you copy when building a fan-out
engine for a new domain (e.g. the project-scoped `AgentHooksRecipe` in this skill's main body).

## Operating principles

- **One source of truth.** The master file is the *only* hand-edited artifact. Every per-target config and
  every per-consumer map is GENERATED. Never hand-edit a generated file or a consumer's embedded fallback —
  edit the master and re-run sync. Drift is a bug, not a state to tolerate.
- **Generated output is deterministic and idempotent.** No timestamps, no random ordering. Re-running sync
  with an unchanged master writes zero bytes. This is what lets `--check` diff generated-on-disk against
  generated-from-master and gate CI.
- **Ambiguity is detected, resolved once, and remembered.** The engine surfaces ambiguities; each resolution
  is written to the lock keyed by a *stable* id. The next run auto-applies it — so re-syncs, and even adding
  a brand-new target whose decisions are already made, are seamless.
- **Consumers read the projection, fall back to an embedded default.** A target's runtime loads the generated
  map but degrades to a small embedded default if it's missing/corrupt — a generated artifact going missing
  must never silently break the consumer.
- **Validate the projection against the domain's contract.** Generated output must satisfy whatever
  schema/regex/allowlist the targets require; sync asserts this, it doesn't template blindly.
- **`check` is the gate; `sync` is the apply.** CI runs `--check` (read-only, nonzero on drift or unresolved
  ambiguity). Humans run `--sync` (writes) and `--resolve` (interactive, appends to lock).

## The three artifacts

| Artifact | Role | Hand-edited? |
|---|---|---|
| `*.master.json` (SSOT) | canonical model + per-target bindings/dialect | **yes — the only one** |
| `*.mappings.lock.json` | remembered resolutions for ambiguous/divergent mappings | only via `--resolve` (or a reviewed seed) |
| `sync.py` (engine) | detect → resolve → generate; `--check` / `--apply` / `--resolve` | yes (it's code) |

…producing, per target: its **native config** (the dialect file the tool actually loads) and, optionally, a
**machine map** the consumer reads at runtime (e.g. `event_map.generated.json`).

The master separates *what* (a canonical **catalog** keyed by id, each with a `role` — the cross-target
normalization unit) from *how each target expresses it* (**targets**: per target a `dialect`, output paths, a
`runner`/command template, and **bindings** mapping the target's *native* names → a catalog entry + role +
dialect detail). `role` is the key idea: divergence is detected when the **same role maps to different
canonical entries across targets** — exactly the ambiguity the lock resolves.

## Build workflow (a fan-out engine for a new domain)

1. Copy `assets/master.template.json` and `assets/mappings.lock.template.json`; fill the catalog + targets +
   bindings for your domain.
2. Adapt `sync.py` using the design below. Keep generation deterministic.
3. Point each consumer at its generated map with an embedded fallback (merge generated OVER default).
4. Wire `check` (CI gate) and `sync` (apply) tasks, plus a verifier that builds one output per binding and
   validates it against the domain's contract.
5. Seed the lock with the resolutions you make on first run; thereafter re-syncs are seamless.

---

# Engine design — the algorithm in detail

Read this with `assets/master.template.json` and `assets/mappings.lock.template.json` open. The reference
implementation (`services/agent-hooks/sync.py`) is the working version of everything here — copy and adapt it.

## Master (SSOT) schema

```
{
  "version": 1,
  "catalog": {                       // canonical model, keyed by stable id
    "<canonical-id>": {
      "role": "<role>",              // cross-target normalization unit (drives divergence detection)
      ...domain fields (type, bucket, kind, …)
    }
  },
  "targets": {                       // == "agents" in agent-hooks
    "<target>": {
      "dialect": "<dialect>",        // selects the renderer
      "config_target": "<path|null>",       // native config to generate (null = none, e.g. a watcher)
      "map_target": "<path|null>",          // machine map the consumer reads at runtime
      "runner": "... {service_dir} ...",    // command template; {service_dir} → abs path
      "bindings": [
        { "native": "<native-name>", "role": "<role>", "ref": "<canonical-id>",
          "arg": "<consumer-arg>", "matcher": "<x|null>", "payload": "stdin|empty|...",
          "extra_args": [ ... ] }
      ]
    }
  }
}
```

## Lock (resolution memory) schema

```
{
  "version": 1,
  "policy": { "on_unresolved": "prompt", "on_recorded": "apply" },
  "resolutions": {
    "role:<role>":  { "resolution": "<canonical value>", "strategy": "unify-to",
                      "diverged": {<target>: <old value>}, "rationale": "...",
                      "decided_at": "YYYY-MM-DD", "decided_by": "..." },
    "type:<value>": { "resolution": "<legal value>", ... }   // for contract-illegal entries
  }
}
```

## `effective(binding)` — the resolution rule

This single function makes the lock authoritative and re-syncs seamless:

```
role = binding.role
if lock.resolutions["role:" + role] exists:
    return that resolution          # lock OVERRIDES the binding's catalog ref
else:
    return catalog[binding.ref].value
```

Because the lock overrides per-binding refs, any target (even a newly added one) whose role is already
decided is normalized to the remembered value — no per-target edits needed.

## detect → resolve → generate

**detect_ambiguities(master, lock)** returns the OPEN (unresolved) ones; empty == clean:

1. **illegal-value** — a catalog value (that is actually emitted) fails the domain contract
   (regex/allowlist/etc.). Skip if `type:<value>` is in the lock.
2. **divergent-role** — collect each non-inert target's *catalog* value per role; if a role has >1
   distinct value and no `role:<role>` lock entry → ambiguity (candidates = the distinct values).
3. **missing-artifact** — an emitted value has no backing schema/contract artifact.

**resolve** — if `--resolve` and a TTY: print each ambiguity + candidates, read a choice + rationale,
write `resolutions[id]`, save lock. Non-TTY with open ambiguities → refuse to apply (nonzero).

**generate(master, lock)** → `{path: content}` for every target with a `config_target`/`map_target`:
- machine map: `{ "_do_not_edit": "...", "map": { <arg>: <effective(binding)> } }`.
- native config: dispatch on `dialect` to a renderer.

## Dialect renderers

Each renderer turns bindings into the target's native structure. Keep them pure and ordered by the
master's binding order (determinism). The command for a binding is typically:

```
prefix + runner + " " + arg + "".join(" " + e for e in extra_args)
```

where `prefix` depends on `payload` and dialect (`"cat | "` for stdin; `""` or `"echo '{}' | "` for
empty). Resolve `{service_dir}` in `runner` to `os.path.dirname(os.path.abspath(__file__))`.

## Commands & exit codes

- `--check` [`--json`]: compare generated-from-master to on-disk; report ambiguities + stale files.
  Exit `0` clean · `3` unresolved ambiguity · `4` artifacts stale (run apply) · `2` load error.
- `--apply` [`--resolve`]: refuse if unresolved ambiguities (unless `--resolve` clears them), else write
  only files whose content changed (so a no-op run reports `0 changed`).
- `--resolve`: interactive; append decisions to the lock.
- `--install`: deploy generated artifacts to each target's *live* location (a `live_target` per target
  in the master) — symlink for link-style targets, surgical inner-hook JSON merge for merge-style ones
  (see the granularity-trap gotcha), backing up the live file only on real change. `deploy` =
  `--apply --install` (regenerate then install). Keep generate (repo artifacts) separate from install
  (operator's live files) so CI can gate on `--check` without touching live configs.

## Consumer side (fallback merge)

The runtime that consumes a generated map must not hard-depend on it:

```
def resolve_map(dir, default_map):
    merged = dict(default_map)         # small embedded canonical fallback
    generated = load(dir/"X.generated.json")   # None on missing/corrupt
    if generated: merged.update(generated)      # generated WINS; aliases in default survive
    return merged
```

Merge (not replace) so migration aliases living only in the embedded default keep working while the
generated projection stays authoritative for canonical names.

## Verifier (the smoketest)

For every binding, build one representative output from `effective(binding)` (fill required fields from
the domain schema) and assert it satisfies the contract. This catches a binding that maps to something
legal-but-unschemaed, or a renderer that emits a malformed command. Run it in the `--check` gate chain.
