---
name: pjangler-dev
description: |
  Develop pjangler itself: author Commands (atomic file/dir operations), Recipes (composed subsystem bootstrappers), and register them in the CLI. Covers the Command/Recipe architecture, project registry implementation, CommonProject copier implementation, and pjangler dist/build/regression workflows. Use when creating a pjangler Command or Recipe, registering a recipe, adding subsystem bootstrapping, changing templates/commonproject, authoring a parity rule, debugging pjangler tests, or changing the CLI/MCP server. Triggers: pjangler command, pjangler recipe, add subsystem, bootstrap, project scaffolding, CommonProject template, project registry, pjangler CLI, pjangler MCP. Do NOT use for: USING pjangler to create a 33god project (→ 33god-projects); generic agent-config fan-out engine mechanics (→ agent-config-fanout); versioning many files in parity (→ mise-versioning); event schema naming (→ bloodbank-integration).
---

# Pjangler Development

This skill covers **developing pjangler** — authoring Commands (atomic file/dir operations) and Recipes (composed subsystem bootstrappers) and registering them in the CLI.

For *using* pjangler to create a 33god project — bootstrapping CommonProject, the `.project.json` source of truth, mise/bmad/hindsight/bloodbank wiring, and adopting the project-scoped per-dev agent-hooks layer — use the **`33god-projects`** skill instead.

Employees are not in this repo. The `hermes-agent` template, the hire/onboard/offboard commands, the org chart, and the eight `hermes.*` / `systemd.sentinel` parity rules live in **Flume** (`~/code/33GOD/flume`, `packages/flume-hr/`) — → **agent-fleet-operations**.

For the generic SSOT config fan-out engine (master→multi-dialect propagation, lock files, generated-config drift) that pjangler recipes may consume, use the **`agent-config-fanout`** skill.

For repository ignore simplification or tracked-ignored index reconciliation,
use **`gitignore-maintenance`**. CommonProject owns only a small portable repo
contract and must never copy `core.excludesFile`; pjangler parity may remove
exact legacy lines it generated, but it must never run bulk `git rm --cached`.

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

#### Shelling out to an external CLI

A Command or rule may need a tool this repo does not own — `copier`, `op`, `px`.
The house pattern is `spawnSync` with `shell: false` and an explicit `timeout`,
after probing with `which` and failing with an actionable install hint
(`runPx` in `src/parity/rules.ts`, behind the `board.schema` rule, is the
reference; `src/lifecycle/preflight.ts` is the version that additionally pins
the resolved binary's identity).

Two rules for anything that reaches a live remote service:
- treat "the tool is missing" and "the service is unreachable" as **skip**, not
  failure — a hard failure here can roll back an in-flight project transaction;
- never pass a destructive flag from an automated path.

## Command Patterns

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
import type { LifecycleContext, RecipeCheck, RecipeInitResult, RecipeMetadata } from "./types";

export class <Name>Recipe extends Recipe {
  readonly checks: readonly RecipeCheck[] = [];
  readonly metadata: RecipeMetadata = {
    id: "<name>",
    name: "<name>",
    description: "<what this subsystem bootstraps>",
    dependencies: [],
    commands: ["AddSomeFile", "AddAnotherFile"],
    publicRuleIds: [],
  };

  constructor(context?: CommandContext) {
    super(context);
    this
      .addIngredient(AddSomeFile)
      .addIngredient(AddAnotherFile);
  }

  override init(ctx: LifecycleContext, _input: unknown): Promise<RecipeInitResult> {
    return this.invokeIngredients(ctx);
  }

  protected printNextSteps(): void {
    console.log("🎉 <Name> subsystem initialized!");
  }
}
```

`metadata`, `checks` and `init` are abstract on the base class; a recipe without
all three does not compile. An empty `checks` is legitimate — `DockerRecipe`
carries the reasoning: a rule that cannot tell what pjangler wrote from what the
operator wrote by hand is worse than no rule.

Register the instance in the catalog, `src/recipes/catalog.ts`:

```typescript
export const recipeRegistry = new RecipeRegistry([
  …,
  new <Name>Recipe(),
]);
```

That is the whole registration — `pj add <name>` resolves through the same
registry, so there is no switch statement to update. Adding the id to
`LEGACY_PUBLIC_RECIPE_IDS` in `src/utils/registry.ts` is what additionally lists
it in `pj subsystems`.

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
bun /home/delorenj/code/33GOD/pjangler/src/index.ts add <subsystem>
```

## Vendored template

`templates/commonproject` is pjangler's one git submodule, and the one copier template it deploys. `scripts/check-submodule-contract.mjs`, `package.json` `files`, and the release tarball contract all name exactly that one; adding a second means updating all three.

## Out of Scope

- **Using pjangler to create/wire a 33god project** → `33god-projects`.
- **Generic SSOT config fan-out engine mechanics** → `agent-config-fanout`.
- **Versioning many files in parity** → `mise-versioning`.
- **Event schema naming or Bloodbank topology** → `bloodbank-integration`.
