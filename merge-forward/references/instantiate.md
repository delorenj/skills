# Porting merge-forward to another monorepo

The base skill (`skills/merge-forward`) is ecosystem-agnostic. To adopt it in another root monorepo you create a thin repo-specific extension and, optionally, the self-tuning session-end hook.

## 1. Create the extension skill

Create `skills/<repo>-merge-forward/` next to the base, containing only:

- `SKILL.md` — frontmatter (`name: <repo>-merge-forward`, a description naming the repo's components so triggers fire), then:
  - a one-line statement that this skill extends `merge-forward` (relative link `../merge-forward/SKILL.md`);
  - the environment model if it differs from the base defaults;
  - the **product authority boundaries**: which component owns which truth, and the rule to stop and surface boundary redraws;
  - repo-specific workflow deltas (coordination ledger location, pin/image topology);
  - any session-end rebalancing configuration notes.
- `references/gates.md` — only contract-specific gates (e.g. "use the real broker when claiming durability"), deferring to `../../merge-forward/references/gates.md` for the universal menu.
- `agents/openai.yaml` — display name and default prompt for the extension.

Keep the extension under ~120 lines. If you find yourself copying base prose, link it instead.

## 2. Pick tuner invariants (required for self-tuning)

Choose the short list of strings that must survive any automated edit — the repo's load-bearing doctrine. The 33GOD example:

```python
REQUIRED_INVARIANTS = (
    "one user and one decision-maker",
    "pre-production",
    "Lifecycle", "Momo", "Holocene", "Bloodbank",
    "component `main`", "root `main`",
)
```

Every invariant string must appear verbatim in the extension's `SKILL.md`, or validation rejects every candidate forever.

## 3. Wire the self-tuning hook (optional but recommended)

Copy from the 33GOD root repo:

- `.agents/hooks/merge-forward/session-end.sh` — update the `WORKER` path to point at your extension's `scripts/rebalance.py`.
- `.agents/hooks/lib/hook-guard.sh`, `.agents/hooks/lib/local-config.sh` — unchanged; gives you the per-dev kill switch via `.agents/local.json`.
- `.agents/hooks/hooks.master.json` + `.agents/hooks/sync.py` — the single-source-of-truth hook fanout; add the `merge-forward-session-rebalance` entry and run `mise run hooks-sync` to inject per-client configs (claude/codex/kimi dialects).
- `scripts/rebalance.py` — copy verbatim into your extension. It derives `SKILL_DIR` and `REPO_ROOT` from its own location, and names its state dir (`~/.local/state/<skill-name>`) and temp dirs after the skill, so the only edits needed are `REQUIRED_INVARIANTS` and the env var prefix if you want isolation.

Guards you get for free: async detach (never blocks session exit), flock mutex, debounce/quiet-window, recursion guard, clean-`main` requirement, candidate-only editing with an `ALLOWED_RELATIVE` whitelist, invariant preservation, validator + line-growth budget, auto-commit of applied edits (opt out with `GOD_MERGE_FORWARD_REBALANCE_NO_COMMIT=1`), and fail-open behavior throughout.

## 4. Telemetry (optional)

If the repo has an event bus, have the tuner emit one event per mutation cycle (see `rebalance.py` in 33GOD for a bloodbank example). Telemetry must be fail-open: a broker outage must never block or crash tuning.

## 5. Verify

1. `python3 scripts/rebalance.py --client test --input <(echo '{}') --dry-run --force` from the repo root.
2. End a real agent session in the repo; check `~/.local/state/<skill-name>/rebalance.log` for a `result=` line.
3. Confirm a dirty skill tree yields `deferred`, a clean one yields `applied`/`no-change`, and `applied` is followed by a tuner-authored commit on `main`.
