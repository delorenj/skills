# Recipe Interface Reference

## Interfaces

```typescript
import { Command, InvokeResult, CommandContext } from "../commands/Command";

export interface AddIngredient<T extends Command = Command> {
  new (context: CommandContext): T;
}
```

## Base Recipe Class

```typescript
export abstract class Recipe {
  protected context: CommandContext;
  protected ingredients: Command[] = [];

  constructor(context: CommandContext) {
    this.context = context;
  }

  addIngredient<T extends Command>(CommandClass: AddIngredient<T>): this {
    this.ingredients.push(new CommandClass(this.context));
    return this;
  }

  async execute(): Promise<void> {
    console.log(`🚀 Initializing ${this.constructor.name.replace('Recipe', '').toLowerCase()} subsystem...`);

    for (const command of this.ingredients) {
      const result = await command.invoke();

      if (result.success) {
        console.log(result.message);
      } else {
        console.log(result.message);
      }
    }

    this.printNextSteps();
  }

  protected abstract printNextSteps(): void;
}
```

## Complete Examples

### Basic Recipe

```typescript
import { Recipe } from "./Recipe";
import { AddDockerfile } from "../commands/AddDockerfile";
import { AddDockerCompose } from "../commands/AddDockerCompose";
import { AddDockerignore } from "../commands/AddDockerignore";
import type { CommandContext } from "../commands/Command";

export class DockerRecipe extends Recipe {
  constructor(context: CommandContext) {
    super(context);
    this
      .addIngredient(AddDockerfile)
      .addIngredient(AddDockerCompose)
      .addIngredient(AddDockerignore);
  }

  protected printNextSteps(): void {
    console.log("🎉 Docker subsystem initialized successfully!");
    console.log("   Next steps:");
    console.log("   1. docker-compose up -d");
    console.log("   2. docker-compose logs -f");
  }
}
```

### Recipe with Multiple Command Sources

```typescript
import { Recipe } from "./Recipe";
import { AddPackageJson, AddReadme, AddSrcDirectory } from "../commands/NodeCommands";
import { AddGitignore } from "../commands/AddGitignore";
import type { CommandContext } from "../commands/Command";

export class NodeRecipe extends Recipe {
  constructor(context: CommandContext) {
    super(context);
    this
      .addIngredient(AddPackageJson)
      .addIngredient(AddReadme)
      .addIngredient(AddSrcDirectory)
      .addIngredient(AddGitignore);
  }

  protected printNextSteps(): void {
    console.log("🎉 Node.js project initialized successfully!");
    console.log("   Next steps:");
    console.log("   1. bun install");
    console.log("   2. bun run dev");
  }
}
```

### Recipe with Extensive Setup

```typescript
import { Recipe } from "./Recipe";
import { AddMiseToml } from "../commands/AddMiseToml";
import { AddDotenv } from "../commands/AddDotenv";
import { AddMiseTasksStructure } from "../commands/AddMiseTasksStructure";
import { AddMiseBaseToml } from "../commands/AddMiseBaseToml";
import { AddMiseBaseScript } from "../commands/AddMiseBaseScript";
import type { CommandContext } from "../commands/Command";

export class MiseRecipe extends Recipe {
  constructor(context: CommandContext) {
    super(context);
    this
      .addIngredient(AddMiseToml)
      .addIngredient(AddDotenv)
      .addIngredient(AddMiseTasksStructure)
      .addIngredient(AddMiseBaseToml)
      .addIngredient(AddMiseBaseScript);
  }

  protected printNextSteps(): void {
    console.log("🎉 Mise subsystem initialized successfully!");
    console.log("   Next steps:");
    console.log("   1. mise install");
    console.log("   2. mise run dev");
  }
}
```

## Registering a Recipe in CLI

Add to `src/index.ts`:

```typescript
import { NewRecipe } from "./recipes/NewRecipe";

// In the init command switch statement:
case "new":
  const newRecipe = new NewRecipe(context);
  await newRecipe.execute();
  break;

// Update the list command to include it:
program
  .command("list")
  .action(() => {
    console.log("Available subsystems:");
    console.log("  mise    - Mise task runner and environment setup");
    console.log("  docker  - Docker containerization setup");
    console.log("  node    - Node.js project template");
    console.log("  new     - New subsystem description");  // Add here
  });
```

## Recipe Design Patterns

### Layered Subsystem

When a subsystem has core + optional layers:

```typescript
export class ApiRecipe extends Recipe {
  constructor(context: CommandContext) {
    super(context);
    // Core files
    this
      .addIngredient(AddServerTs)
      .addIngredient(AddRoutesTs);

    // Config files
    this
      .addIngredient(AddEnv)
      .addIngredient(AddTsConfig);

    // Dev tooling
    this
      .addIngredient(AddPrettierConfig)
      .addIngredient(AddEslintConfig);
  }
}
```

### Domain-Grouped Commands

For complex subsystems, group commands by domain in separate files:

```
src/commands/
├── ApiCommands.ts        # AddServerTs, AddRoutesTs, AddMiddleware
├── ConfigCommands.ts     # AddEnv, AddTsConfig, AddPackageJson
└── ToolingCommands.ts    # AddPrettierConfig, AddEslintConfig
```

Then compose in the recipe:

```typescript
import { AddServerTs, AddRoutesTs } from "../commands/ApiCommands";
import { AddEnv, AddTsConfig } from "../commands/ConfigCommands";
import { AddPrettierConfig } from "../commands/ToolingCommands";
```
