# Feature anatomy

The target shape of a 33GOD feature. `†` marks a command, flag or route that does
not exist yet; do not call it, and do not write code that assumes it.

Source design: crank packaging study, 2026-11-05 (feature homes with claims, checks
and owned atoms). Its operator decisions are in the 33god-features `SKILL.md`; where
that file and this one disagree, `SKILL.md` wins.

## The repo

A single-repo capability is a **component**. A cross-repo capability becomes a
feature candidate when maintaining or extending its scattered parts becomes hard.
Promotion creates a dedicated formal **hub repo** (F1): GitHub, board, BMAD,
pjangler registration, a 33GOD submodule and root `feature.toml`. The hub owns the
feature domain and integration contracts; participant code stays in its component
repo. For crank, registry/engine belong to crank; the pj control-surface integration
belongs to pjangler and is tracked as part of the crank feature.

The manifest's participant links are part of the architecture to define, not an
already-implemented schema. The conventions below cover hub-owned payloads only:

| Path | Meaning |
|---|---|
| `bin/*` | Executables. Every file is linked into `~/.local/bin`; the glob is the list. |
| `hermes/jobs/*.toml` | Hermes jobs, upserted **by name**, `scheduler = "external"`. |
| `hermes/stubs/*.tmpl` | The only files allowed in a Hermes profile: rendered, logic-free stubs. |
| `.candybars/*.candybar.toml` | Project candybars (`candybar register --update --prune`). |
| `checks/*` | Executable checks. Exit 0/1, print `{ok, findings[], repair?}` JSON. |
| `migrations/` | State migrations with `up` and `down`. |
| `schemas/` | Redis key schemas and event payloads the feature owns. |
| `contracts/atoms/` | Contracts for atoms this feature **provides** (with live probes). |

## feature.toml

```toml
[feature]
name = "crank"
version = "0.4.0"                 # informational only: features track main (F3); no ranges anywhere
owner = "delorenj/crank"
scope = "host"                  # host | project
platforms = ["linux"]

[params]                        # rendered only into stubs and ~/.config/33god/features/<name>.env
hermes_profile = { default = "33god-pm" }

[requires]                      # atom = major version; resolved by a live probe, never a fixture
"pane.topology" = "1"             # owners: see 33GOD/features.toml [atoms]
"agent.session" = "1"
"project.identity" = "1"
"clock" = "1"

[provides]
"crank.binding" = { v = 1, cli = "zcrankctl keys --json", contract = "contracts/atoms/crank.binding.v1.toml" }

[skills]
select = ["crank-engine"]       # skillex owns the text; the feature owns the selection

[claims]                        # anything matching is this feature's, receipted or not
redis       = ["zcrank:*"]
paths       = ["~/.local/state/zcrank/", "~/.local/bin/zcrank*"]
hermes_jobs = ["crank-*"]
candybars   = ["project:crank"]

[state]
redis_schema = "schemas/redis/zcrank.v1.toml"
on_remove    = "export"         # JSONL archive, then SCAN + DEL per key on an explicit -p. Never FLUSH*.

[[implements]]                  # a known second implementation: checked live, never trusted
atom = "crank.binding"
by = "pjangler:src/crank/index.ts"
differential = "pj crank list --json"

[lint]                          # strings that must never appear in the feature or its declared consumers
forbidden = ["777c511a009c", "01a1793b", "/home/delorenj", '"Workspace"']
paths     = ["**", "consumer:pjangler/src/crank/**"]
```

## Atom contracts

An atom is a shared building block (list panes, which agent is in this pane, which
project is this directory). Its contract and live probe live in the **owning**
repo at `contracts/atoms/<atom>.v<major>.toml`:

```toml
[atom]
name = "project.identity"
major = 1
minor = 1
owner = "pjangler"
interface = { http = "GET http://127.0.0.1:8764/v1/resolve?cwd={cwd}", cli = "pj project resolve --json --cwd {cwd}" }
returns = { project_id = "string", root = "path", memory_bank = "string", board = "string?" }
[[probe]]                       # runs against the live box
cwd = "~/code/33GOD"
expect = '.project_id == "33god" and .memory_bank == "33GOD"'
```

A non-owner may serve an atom only as `provisional` (declared in its `[provides]`),
until the owner's interface exists and passes a live differential against it.

## Lifecycle (the engine is `pj feature`†)

| Verb | Does |
|---|---|
| `plan` / `add` (dry run) | Probe required atoms, sweep claims, lint, print the ordered steps. |
| `apply` | Journal each step; the **clock is registered last**; re-audit after each step. |
| `check [--absent] [--prove]` | Run `checks/*`; `--absent` proves nothing claimed remains. |
| `remove` | **Clock stops first**; export state; delete only what still matches the receipt; sweep claims. |
| `adopt` | Take over live artifacts (e.g. existing Candybar rows with their history) in place. |
| `why <atom>` | Owner, provider, consumers, and the duplicate copies still to retire. |

Installed state: receipt `~/.local/state/33god/features/<name>.json` (links carry
dev/ino, copies carry sha256, sources carry a commit) plus `<name>.journal` during
an apply. The world beats the receipt: a receipt only grants permission to delete
what still matches it; anything foreign is quarantined, never deleted.

Rollback is not a verb. Main is production: `git revert`, push, `pj feature apply`.

## Catalog and per-install choice

- `~/code/33GOD/features.toml` (tracked in delorenj/33god) is the full catalog: every
  feature, its repo, status, default, and the atoms it needs. It is also the map
  for expanding the pipeline, whether or not anything reads it.
- A host or container turns features off in its own untracked override,
  `~/.config/33god/features.toml`†: `[disable] crank = "reason"`.
