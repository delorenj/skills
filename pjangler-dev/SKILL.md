---
name: pjangler-dev
description: "Two build-tooling capabilities. (A) Develop pjangler itself — author Commands (atomic file/dir operations) and Recipes (composed subsystem bootstrappers) and register them in the CLI. (B) The SSOT config fan-out engine — keep ONE hand-edited master file (e.g. hooks.master.json) and generate every downstream config from it for heterogeneous targets that each speak their own dialect, with a lock file (hooks.mappings.lock.json) recording how ambiguous/divergent mappings were resolved so re-syncs are seamless. Canonical instance: bloodbank services/agent-hooks (hooks.master.json → sync.py → per-agent generated configs + event_map.generated.json, gated by `mise run hooks:check` / `hooks:sync`). Use when: creating a pjangler Command or Recipe, registering a recipe, adding subsystem bootstrapping; OR designing a NEW master-config → multi-dialect propagation engine with ambiguity-resolution memory, adding a new agent CLI/target to agent-hooks, editing hooks.master.json, fixing generated-config drift, or resolving an ambiguous mapping. Keywords: pjangler command, pjangler recipe, add subsystem, bootstrap, project scaffolding, SSOT, single source of truth, fan-out, master→dialect, generated-config drift, lock file, ambiguity resolution. Do NOT use for: USING pjangler to create a 33god project, or the project-scoped per-dev agent-hooks layer's adoption/mechanics (both → 33god-projects); bumping versions across files (mise-versioning); defining event schemas or the naming contract (bloodbank docs); single-target config templating with no dialect/ambiguity dimension (just template it)."
pipeline-status:
  - new
---

# Pjangler Development & the SSOT config fan-out engine

This skill covers two build-tooling jobs:

1. **Developing pjangler** — authoring Commands (atomic file/dir ops) and Recipes (composed
   subsystem bootstrappers) and registering them in the CLI. This is the bulk of the body below.
2. **The SSOT config fan-out engine** — building a master→multi-dialect propagation engine with
   ambiguity-resolution memory (and operating bloodbank's canonical `services/agent-hooks`
   instance). See the engine references in the next section.

For *using* pjangler to create a 33god project — bootstrapping CommonProject, provisioning a Hermes
PM or Ticket Sentinel, the `.project.json` source of truth, mise/bmad/hindsight/bloodbank wiring,
**and adopting the project-scoped per-dev agent-hooks layer** — use the **`33god-projects`** skill
instead.

## SSOT config fan-out engine

| You want to… | Read |
|---|---|
| Build a NEW master → multi-dialect propagation engine (pattern, schemas, detect→resolve→generate, dialect renderers, exit codes, consumer fallback) | [references/ssot-fanout-engine.md](references/ssot-fanout-engine.md) + `assets/master.template.json`, `assets/mappings.lock.template.json` |
| Operate/extend the bloodbank `services/agent-hooks` instance — add an agent CLI, edit `hooks.master.json`, resolve a mapping | [references/ssot-fanout-reference.md](references/ssot-fanout-reference.md) |
| Output drifts, sync isn't idempotent, a consumer broke, an ambiguity won't clear, a merge ate sibling hooks | [references/ssot-fanout-gotchas.md](references/ssot-fanout-gotchas.md) |

The project-scoped per-dev agent-hooks **application** of this engine (Claude/Codex/Hermes/Kimi,
`.agents/local.json` opt-out, `mise enter/leave`) is documented operationally in **`33god-projects`**
(`references/project-scoped-hooks.md` + `references/project-scoped-internals.md`); the
`AgentHooksRecipe` follow-up below is how you'd templatize it into pjangler.

## Developing pjangler

Pjangler uses a Command Pattern architecture where Commands are atomic operations and Recipes compose Commands into subsystem bootstrappers.

> **Vendored templates:** the copier templates pjangler deploys are git submodules under
> `templates/commonproject` and `templates/hermes-agent`. `RunCopierTemplate` resolves the
> hermes template as: `PJANGLER_HERMES_TEMPLATE` env → vendored `templates/hermes-agent` →
> `~/code/hermes-agent-template` → `gh:delorenj/hermes-agent-template`. The `hermes-agent`
> recipe passes `ticket_provider` + `with_scrum_master` and the template binds agents to the
> repo's one board recorded in `.project.json` (it does not mint role-suffixed boards).

## Architecture Overview

```
src/
├── commands/           # Atomic file/directory operations
│   ├── Command.ts      # Base class with helpers
│   └── Add*.ts         # Individual commands
├── recipes/            # Composed command sequences
│   ├── Recipe.ts       # Base class with execution logic
│   └── *Recipe.ts      # Subsystem recipes
└── index.ts            # CLI entry point
```

## Creating a Command

Commands are atomic operations that create files or directories.

### Step 1: Create the Command File

Create `src/commands/Add<Name>.ts`:

```typescript
import { Command, InvokeResult } from "./Command";

export class Add<Name> extends Command {
  async invoke(): Promise<InvokeResult> {
    const filePath = "<target-file>";

    // Check existing (skip if exists unless force)
    if (this.fileExists(filePath) && !this.context.force) {
      return {
        success: false,
        message: "⚠️  <file> already exists",
        filePath
      };
    }

    const content = `<file-content>`;

    this.writeFile(filePath, content);
    return {
      success: true,
      message: "✅ Created <file>",
      filePath
    };
  }
}
```

### Available Helpers

The Command base class provides:
- `this.context.targetDir` - Target directory path
- `this.context.force` - Whether to overwrite existing files
- `this.fileExists(path)` - Check if file exists relative to targetDir
- `this.writeFile(path, content)` - Write file, creating dirs as needed
- `this.createDirectory(path)` - Create directory structure

### Command Patterns

- **File creation** (most common): guard with `if (this.fileExists(path) && !this.context.force)`, then `this.writeFile(path, content)`.
- **Directory creation**: `this.createDirectory("src/components")`.
- **Multiple files**: export several `Command` subclasses from one `<Domain>Commands.ts`.

Full signatures and worked examples: [references/command-interface.md](references/command-interface.md).

## Creating a Recipe

Recipes compose Commands into subsystem bootstrappers.

### Step 1: Create the Recipe File

Create `src/recipes/<Name>Recipe.ts`:

```typescript
import { Recipe } from "./Recipe";
import { AddSomeFile } from "../commands/AddSomeFile";
import { AddAnotherFile } from "../commands/AddAnotherFile";
import type { CommandContext } from "../commands/Command";

export class <Name>Recipe extends Recipe {
  constructor(context: CommandContext) {
    super(context);
    this
      .addIngredient(AddSomeFile)
      .addIngredient(AddAnotherFile);
  }

  protected printNextSteps(): void {
    console.log("🎉 <Name> subsystem initialized!");
    console.log("   Next steps:");
    console.log("   1. <first step>");
    console.log("   2. <second step>");
  }
}
```

### Step 2: Register in CLI

Add to `src/index.ts`:

```typescript
import { <Name>Recipe } from "./recipes/<Name>Recipe";

// In the switch statement:
case "<name>":
  const recipe = new <Name>Recipe(context);
  await recipe.execute();
  break;
```

Update the list command output to include the new subsystem.

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Command | `Add<Target>.ts` | `AddDockerfile.ts` |
| Recipe | `<Subsystem>Recipe.ts` | `DockerRecipe.ts` |
| Multi-command file | `<Domain>Commands.ts` | `NodeCommands.ts` |

## Testing Commands

Run manually to verify:

```bash
cd /tmp/test-project
bun /home/delorenj/code/pjangler/src/index.ts init <subsystem>
```

Check generated files match expectations.

## Worked target: a project-scoped agent-hooks recipe (open follow-up)

The per-dev, committed **agent hooks + skill fan-out** layer (Claude/Codex/Hermes/Kimi hooks +
skills installed via `mise enter/leave`) is currently hand-adopted in **CoachingAgentFramework**
(`~/code/CoachingAgentFramework/.agents/hooks/` + `.mise/scripts/`) and is **not yet a pjangler
recipe**. Templatizing it is a prime recipe candidate. Source of truth for *what it does* and the
adopt-checklist: the **`33god-projects`** skill → `references/project-scoped-hooks.md` (+
`references/project-scoped-internals.md` for the dialect mechanics); for the generic
master→dialect engine you'd build the recipe on top of: [references/ssot-fanout-engine.md](references/ssot-fanout-engine.md)
and [references/ssot-fanout-gotchas.md](references/ssot-fanout-gotchas.md).

To build it: author Commands that drop the CAF files (parameterized off `context` — project name,
pinned Hindsight bank), then an `AgentHooksRecipe` composing them in order:

- `AddHooksMaster` → `.agents/hooks/hooks.master.json` (SSOT)
- `AddHookSyncEngine` → `sync.py` + `lib/{local-config,hook-guard}.sh`
- `AddHindsightHooks` → `hindsight/*` + `hermes/hindsight-hook.sh` (adapter)
- `AddSkillLinker` → `.mise/scripts/link-project-skills-to-clis.sh` (+ unlink)
- `AddHindsightSetup` → `.mise/scripts/hindsight-setup.sh`
- `AddLocalConfigExample` → `.agents/local.example.json` + `.gitignore` entries
- `WireMiseAgentHooks` → patch `mise.toml` enter/leave/watch_files/tasks

`WireMiseAgentHooks` is the only non-drop-a-file Command — it must **merge** into an existing
`mise.toml` (append to `[hooks].enter/leave`, add `watch_files` + tasks) idempotently, not overwrite.

## Out of scope

- **Using pjangler to create/wire a 33god project** (CommonProject, Hermes PM/Ticket Sentinel,
  `.project.json`, mise/bmad/hindsight wiring) → `33god-projects`.
- **The project-scoped per-dev agent-hooks layer** — its adoption checklist and dialect mechanics
  (guard wrapper, `mise enter/leave`, `defer_to_global`, Kimi/Codex/Hermes specifics) →
  `33god-projects` (`references/project-scoped-hooks.md` + `references/project-scoped-internals.md`).
- **Versioning many files in parity** (`package.json`/`pyproject.toml`/tags) → `mise-versioning`.
- **Defining the event schemas or naming contract** the agent-hooks system targets → that's
  `bloodbank/docs/event-naming.md` and `schemas/`, not this engine.
- **Single-target config with no dialect or ambiguity dimension** (plain env substitution, one
  output) → just template it directly; the master/lock machinery is overkill.

## Reference

For detailed interfaces and examples, see:
- [references/command-interface.md](references/command-interface.md) - Full Command interface
- [references/recipe-interface.md](references/recipe-interface.md) - Full Recipe interface
- [references/ssot-fanout-engine.md](references/ssot-fanout-engine.md) - SSOT fan-out engine: pattern + build design
- [references/ssot-fanout-reference.md](references/ssot-fanout-reference.md) - bloodbank `services/agent-hooks` canonical instance
- [references/ssot-fanout-gotchas.md](references/ssot-fanout-gotchas.md) - fan-out engine gotchas (drift, idempotency, surgical merge)
