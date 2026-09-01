---
name: pjangler-dev
description: |
  Develop pjangler itself: author Commands (atomic file/dir operations), Recipes (composed subsystem bootstrappers), and register them in the CLI. Covers the Command/Recipe architecture, project registry implementation, CommonProject copier implementation, and pjangler dist/build/regression workflows. Use when creating a pjangler Command or Recipe, registering a recipe, adding subsystem bootstrapping, changing templates/commonproject or templates/hermes-agent, debugging pjangler tests, or changing the CLI/MCP server. Triggers: pjangler command, pjangler recipe, add subsystem, bootstrap, project scaffolding, CommonProject template, hermes-agent template, pjangler CLI, pjangler MCP. Do NOT use for: USING pjangler to create a 33god project (→ 33god-projects); generic agent-config fan-out engine mechanics (→ agent-config-fanout); versioning many files in parity (→ mise-versioning); event schema naming (→ bloodbank-integration).
---

# Pjangler Development

This skill covers **developing pjangler** — authoring Commands (atomic file/dir operations) and Recipes (composed subsystem bootstrappers) and registering them in the CLI.

For *using* pjangler to create a 33god project — bootstrapping CommonProject, provisioning a Hermes PM or Ticket Sentinel, the `.project.json` source of truth, mise/bmad/hindsight/bloodbank wiring, and adopting the project-scoped per-dev agent-hooks layer — use the **`33god-projects`** skill instead.

For the generic SSOT config fan-out engine (master→multi-dialect propagation, lock files, generated-config drift) that pjangler recipes may consume, use the **`agent-config-fanout`** skill.

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

Create `src/commands/Add<Name>.ts`:

```typescript
import { Command, InvokeResult } from "./Command";

export class Add<Name> extends Command {
  async invoke(): Promise<InvokeResult> {
    const filePath = "<target-file>";

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

- `this.context.targetDir` - Target directory path
- `this.context.force` - Whether to overwrite existing files
- `this.fileExists(path)` - Check if file exists relative to targetDir
- `this.writeFile(path, content)` - Write file, creating dirs as needed
- `this.createDirectory(path)` - Create directory structure

### Command Patterns

- **File creation** (most common): guard with `if (this.fileExists(path) && !this.context.force)`, then `this.writeFile(path, content)`.
- **Directory creation**: `this.createDirectory("src/components")`.
- **Multiple files**: export several `Command` subclasses from one `<Domain>Commands.ts`.

Full signatures: [references/command-interface.md](references/command-interface.md).

## Creating a Recipe

Create `src/recipes/<Name>Recipe.ts`:

```typescript
import { Recipe } from "./Recipe";
import { AddSomeFile } from "../commands/AddSomeFile";
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
  }
}
```

Register in `src/index.ts`:

```typescript
import { <Name>Recipe } from "./recipes/<Name>Recipe";

// In the switch statement:
case "<name>":
  const recipe = new <Name>Recipe(context);
  await recipe.execute();
  break;
```

Full interface: [references/recipe-interface.md](references/recipe-interface.md).

## File Naming Conventions

| Type | Pattern | Example |
|---|---|---|
| Command | `Add<Target>.ts` | `AddDockerfile.ts` |
| Recipe | `<Subsystem>Recipe.ts` | `DockerRecipe.ts` |
| Multi-command file | `<Domain>Commands.ts` | `NodeCommands.ts` |

## Testing Commands

```bash
cd /tmp/test-project
bun /home/delorenj/code/pjangler/src/index.ts init <subsystem>
```

## Vendored templates

The copier templates pjangler deploys are git submodules under `templates/commonproject` and `templates/hermes-agent`. `RunCopierTemplate` resolves the hermes template as: `PJANGLER_HERMES_TEMPLATE` env → vendored `templates/hermes-agent` → `~/code/hermes-agent-template` → `gh:delorenj/hermes-agent-template`.

## Out of Scope

- **Using pjangler to create/wire a 33god project** → `33god-projects`.
- **Generic SSOT config fan-out engine mechanics** → `agent-config-fanout`.
- **Versioning many files in parity** → `mise-versioning`.
- **Event schema naming or Bloodbank topology** → `bloodbank-integration`.
