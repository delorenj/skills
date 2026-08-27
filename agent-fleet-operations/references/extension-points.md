# Extension points: where to add an MCP server, a hook, or a skill

The question this answers: *"I want capability X available to every agent client
— Claude Code, Codex, Copilot, Antigravity, Kimi, and the Hermes fleet. Where do
I put it?"*

There are three capability planes and they are **not** at the same maturity.
Two have a single source of truth that fans out; one does not.

| plane | SSOT today | fans out to Hermes? | status |
|---|---|---|---|
| **Hooks** | `bloodbank/services/agent-hooks/hooks.master.json` | yes | solved |
| **Skills** | Skillex (`skill-sets/global`, packs) + project `.agents/skills.json` | yes | solved |
| **MCP servers** | *none* | **no** | **gap — see below** |

Verified 2026-08-17. Re-verify with the probes at the bottom before trusting it;
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
`antigravity.py`, `hermes.py`. **Adding a new agent CLI means adding a client
module here**, not hand-writing its config — see the `agent-config-fanout` skill
for the emitter contract and the `hooks.mappings.lock.json` ambiguity ledger.

**How Hermes receives them:** as a `hooks:` block in `~/.hermes/config.yaml`
(the fleet base), where every profile inherits it through the generated
base+delta render. Each entry shells out to the canonical publisher:

```yaml
hooks:
  on_session_start:
    - command: python3 /home/delorenj/.agents/hooks/bloodbank/publish.py --client hermes --hook on_session_start
      timeout: 5
```

Never write a Hermes-local publisher; always call
`~/.agents/hooks/bloodbank/publish.py --client hermes`.

> Trap fixed 2026-08-17: this block existed on **3 of 36** profiles, so 33 agents
> published no lifecycle events at all. It now lives in the base. After changing
> it, run `hermes-profile-config.py render --all` or profiles keep the old copy.

**Project-scoped hooks:** supported by the fan-out (`inherit_global` +
project-scoped hook sets). See `agent-config-fanout`.

---

## 2. Skills — solved

**Global (every client, every project):** add the skill to Skillex's global
skill-set. `~/.agents/skills` is a symlink to
`~/code/skillex/skill-sets/global`, which in turn resolves into the
`skillex/all-skills` repo — so a skill is one directory with a `SKILL.md`.

Hermes picks these up because the fleet base sets:

```yaml
skills:
  external_dirs:
    - /home/delorenj/.agents/skills   # global, all agents
    - ./agents/skills                 # project-local, relative to cwd
```

Both entries are inherited by every profile via the base. The skills **index**
(name + description) sits in every agent's volatile system-prompt tier, so a
skill is genuinely fleet-visible; the body loads on demand, which means the
`description:` field is what determines whether it ever fires. Write triggers,
not prose.

**Project-scoped:** declare in the repo's `.agents/skills.json` (plus `packs[]`
for versioned bundles) and run the project's `skills:sync` mise task. The
`./agents/skills` entry above is what makes the result visible to a Hermes agent
whose `terminal.cwd` is that repo.

> Trap fixed 2026-08-17: seven profiles had **zero** `external_dirs` because they
> were standalone config files that inherited nothing from the fleet base.

---

## 3. MCP servers — the gap

**There is no MCP SSOT.** Every client keeps its own list, they have drifted
badly, and Hermes is the worst off:

| client | store | servers |
|---|---|---|
| Claude Code | `~/.claude.json` (+ project `.mcp.json`) | many |
| Codex | `~/.codex/config.toml` | several |
| Gemini | `~/.gemini/settings.json` | one |
| **Hermes** | `~/.hermes/config.yaml` → `mcp_servers:` | **4** |

Two consequences worth internalizing:

1. **Adding an MCP server today means editing N files by hand**, and they
   silently diverge. There is no `--check` that would tell you.
2. **Hermes never reads a project `.mcp.json`.** Its "mcp_discovery" code is
   *tool* discovery from already-configured servers — it does not scan the
   working directory. So a project-scoped MCP server declared in `.mcp.json` is
   invisible to the entire Hermes fleet. (33GOD's own `.mcp.json` declares
   `code-review-graph`; no Hermes agent can see it.)

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
