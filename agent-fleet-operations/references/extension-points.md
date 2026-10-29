# Extension points: where to add an MCP server, a hook, or a skill

The question this answers: *"I want capability X available to every agent client
— Claude Code, Codex, Copilot, Antigravity, Kimi, and the Hermes fleet. Where do
I put it?"*

There are three capability planes and they are **not** at the same maturity.
Two have a single source of truth that fans out; one does not.

| plane | SSOT today | fans out to Hermes? | status |
|---|---|---|---|
| **Hooks** | `bloodbank/services/agent-hooks/hooks.master.json` | yes | solved |
| **Skills** | Skillex (`sets/`, packs) + project `.agents/skills.json` | yes, strict profile projection | mandatory Skillex-only PM standard; legacy roots require explicit cutover |
| **MCP servers** | *none* | **no** | **gap — see below** |

Verified 2026-09-20. Re-verify with the probes at the bottom before trusting it;
this file is a map, and maps go stale.

---

## 1. Hooks — solved

**Global (every client, every project):** edit the master, then sync.

```bash
cd ~/code/33GOD/bloodbank/services/agent-hooks
$EDITOR hooks.master.json          # the ONLY hand-edited file
python3 sync.py --install          # emits every client dialect
python3 sync.py --check            # drift gate; use in CI
```

Dialect emitters live in `clients/`: `claude.py`, `codex.py`, `copilot.py`,
`antigravity.py`, `hermes.py`, `native.py` (over a shared `base.py`). **Adding a
new agent CLI means adding a client module here**, not hand-writing its config —
see the `agent-config-fanout` skill for the emitter contract and the
`hooks.mappings.lock.json` ambiguity ledger.

**How Hermes receives them:** as a `hooks:` block in `~/.hermes/config.yaml`
(the fleet base), where every profile inherits it through the generated
base+delta render. Each entry shells out to the canonical publisher, the
hook-hub client `bb-hook` (bloodbank `services/agent-hooks/hooks.master.json`
names it Hermes' publisher; `bloodbank/publish.py` is a legacy forwarder):

```yaml
hooks:
  on_session_start:
    - command: /home/delorenj/.agents/hooks/bb-hook --cli hermes --native on_session_start --deadline 15
      timeout: 16
```

Never write a Hermes-local publisher; always call
`~/.agents/hooks/bb-hook --cli hermes --native <event>`. `hermes.fleet-config`
fails a base whose four lifecycle events do not.

> Trap fixed 2026-08-17: this block existed on **3 of 36** profiles, so 33 agents
> published no lifecycle events at all. It now lives in the base. After changing
> it, run `hermes-profile-config.py render --all` or profiles keep the old copy.

**Project-scoped hooks:** supported by the fan-out (`inherit_global` +
project-scoped hook sets). See `agent-config-fanout`.

---

## 2. Skills — selection and profile ownership

**Global (every client, every project):** add the skill to the selected Skillex
set. `~/.agents/skills` projects canonical definitions from `all-skills/`; the
active selection is `~/.agents/skills.json`, not every skill in the catalog.

Hermes scans the active profile's `$HERMES_HOME/skills/` first, then configured
`skills.external_dirs`. The fleet base includes `~/.agents/skills`, but that
alone does not give Skillex exclusive ownership: profile-local copies win
same-name collisions and unrelated local skills remain visible. A profile
whose entire `skills/` root aliases `~/.hermes/skills` loads the default
profile's catalog and shares its writable state.

Relative `external_dirs` resolve against `$HERMES_HOME`, not the terminal CWD.
The old `./agents/skills` entry points inside the profile and is not the
project's `.agents/skills` projection. Use an absolute project projection path
or Hermes's trusted project discovery where the installed runtime supports it.

For PMs, use `skillex profile show <name> --project <repo> --json`, then
preview/apply `skillex profile sync <name> --project <repo> --skillex-only`.
Skillex-only is mandatory, not an overlay preference: preserve legacy children
outside discovery roots before cutover, disable bundled seeding, and set PM
`skills.external_dirs: []` through the locked delta/render workflow. Ordinary
sync honors the persistent strict marker; it refuses unknown children and
local shadows rather than adopting/deleting them. Whole-root aliases require
explicit `skillex migrate` inspection; migration preserves foreign children
and is not by itself an exclusive cutover. Never rerun full profile setup for
skills-only changes or author/install directly into generated roots.

Hermes seeds bundled skills unless the profile carries `.no-bundled-skills`.
`hermes skills opt-out` stops future seeding without removing existing content;
`--remove` removes only unmodified bundled copies. Do not run removal through a
profile root that still aliases the default profile's directory.

`/skills list` labels anything absent from Hermes's hub and bundled manifests
as `local`, including external Skillex skills. That label is not filesystem
ownership evidence; verify the skill's resolved path and precedence.

**Project-scoped:** declare membership in `<repo>/.agents/skills.json`, reconcile
its projection, then explicitly associate the PM profile with that repo. Verify
with the installed fleet Hermes runtime, not just a different PATH checkout.

---

## 3. MCP servers — the gap

**There is no MCP SSOT.** Every client keeps its own list, they have drifted
badly, and Hermes is the worst off:

| client | store | servers |
|---|---|---|
| Claude Code | `~/.claude.json` (+ project `.mcp.json`) | 2 global, plus per-project |
| Codex | `~/.codex/config.toml` | 5 |
| Gemini | `~/.gemini/settings.json` | 4 |
| **Hermes** | `~/.hermes/config.yaml` → `mcp_servers:` | 5 (`codegraph`, `flume`, `pjangler`, `plane`, `vox`) |

Two consequences worth internalizing:

1. **Adding an MCP server today means editing N files by hand**, and they
   silently diverge. There is no `--check` that would tell you.
2. **Hermes never reads a project `.mcp.json`.** Its "mcp_discovery" code is
   *tool* discovery from already-configured servers — it does not scan the
   working directory. So a project-scoped MCP server declared in `.mcp.json` is
   invisible to every Hermes agent. (33GOD's own `.mcp.json` declares
   `code-review-graph` and `codegraph-voyage`; no Hermes agent can see either.)

### What to do until an MCP SSOT exists

**A global MCP server, needed fleet-wide:** add it to `mcp_servers:` in
`~/.hermes/config.yaml` (the base — every profile inherits it), then:

```bash
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-profile-config.py render --all
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-profile-config.py check
```

Then add it to the other clients' stores by hand. Keep the command/args
identical across dialects — a path that differs per client is the drift that
`feedback_canonical_path_registries` warns about.

**A project-scoped MCP server that a Hermes PM must see:** put it in that
profile's `config.delta.yaml` under `mcp_servers:` — the delta layer is exactly
the right place for "this agent, this repo, this server", and it survives every
future base change:

```yaml
# ~/.hermes/profiles/<repo>-pm/config.delta.yaml
mcp_servers:
  code-review-graph:
    command: …
    args: […]
```

Then `render --profile <repo>-pm`. Do **not** put project servers in the base.

### The real fix (not yet built)

Mirror the hooks engine exactly: an `mcp.master.json` with per-dialect emitters
(`claude` → `~/.claude.json` / `.mcp.json`, `codex` → TOML, `hermes` → base
`mcp_servers` **or** a profile delta for project scope, `gemini` → settings
JSON), plus `--check` drift gating. The hooks fan-out in
`bloodbank/services/agent-hooks/` is the reference implementation and already
solves the hard parts (dialect emitters, ambiguity lock file, drift check);
MCP is the same shape with a different payload. Scope it against
`agent-config-fanout` rather than inventing a second engine.

---

## Probes — confirm this map is still true

```bash
# Which Hermes profiles resolve which capabilities?
python3 ~/code/33GOD/hermes-agent-template/scripts/hermes-profile-config.py status

# Do hooks/skills/MCP actually reach a given agent? (resolves through Hermes itself)
HERMES_HOME=~/.hermes/profiles/33god-pm python3 - <<'EOF'
import sys; sys.path.insert(0,"/home/delorenj/.hermes/hermes-agent")
from hermes_cli.config import load_config
c = load_config()
print("mcp_servers :", sorted((c.get("mcp_servers") or {}).keys()))
print("hooks       :", sorted((c.get("hooks") or {}).keys()))
print("skill dirs  :", (c.get("skills") or {}).get("external_dirs"))
EOF

# Hook fan-out drift
python3 ~/code/33GOD/bloodbank/services/agent-hooks/sync.py --check
```

A capability that does not appear in that middle probe **does not exist** for
that agent, no matter what any config file appears to say.
