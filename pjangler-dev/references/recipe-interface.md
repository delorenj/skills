# Recipe Interface Reference

## Interfaces

```typescript
import { Command, InvokeResult, CommandContext } from "../commands/Command";

export interface AddIngredient<T extends Command = Command> {
  new (context: CommandContext): T;
}
```

## Base Recipe Class

Four members are abstract. A recipe that supplies fewer does not compile.

```typescript
export abstract class Recipe<TInput = unknown> implements LifecycleRecipe<TInput> {
  abstract readonly metadata: RecipeMetadata;      // id, name, description, dependencies, commands, publicRuleIds
  abstract readonly checks: readonly RecipeCheck[]; // parity rules this recipe owns; [] is legitimate
  abstract init(ctx: LifecycleContext, input: TInput): Promise<RecipeInitResult>;
  protected abstract printNextSteps(): void;

  addIngredient<T extends Command>(CommandClass: AddIngredient<T>): this {
    this.ingredients.push(new CommandClass(this.context));
    return this;
  }

  /** The default `init` body: invoke every ingredient in order. */
  protected async invokeIngredients(ctx: LifecycleContext): Promise<RecipeInitResult> { /* … */ }
}
```

`execute()` is the compatibility wrapper that prints the banner and calls
`printNextSteps()` after a non-dry-run success; the lifecycle registry calls
`init`, `audit` and `migrate` directly.

## Complete Example

```typescript
import { Recipe } from "./Recipe";
import { AddDockerfile } from "../commands/AddDockerfile";
import { AddDockerCompose } from "../commands/AddDockerCompose";
import { AddDockerignore } from "../commands/AddDockerignore";
import type { CommandContext } from "../commands/Command";
import type { LifecycleContext, RecipeCheck, RecipeInitResult, RecipeMetadata } from "./types";

export class DockerRecipe extends Recipe {
  readonly checks: readonly RecipeCheck[] = [];
  readonly metadata: RecipeMetadata = {
    id: "docker",
    name: "docker",
    description: "Docker containerization setup",
    dependencies: [],
    commands: ["AddDockerfile", "AddDockerCompose", "AddDockerignore"],
    publicRuleIds: [],
  };

  constructor(context?: CommandContext) {
    super(context);
    this
      .addIngredient(AddDockerfile)
      .addIngredient(AddDockerCompose)
      .addIngredient(AddDockerignore);
  }

  override init(ctx: LifecycleContext, _input: unknown): Promise<RecipeInitResult> {
    return this.invokeIngredients(ctx);
  }

  protected printNextSteps(): void {
    console.log("🎉 Docker subsystem initialized successfully!");
    console.log("   Next steps:");
    console.log("   1. docker-compose up -d");
    console.log("   2. docker-compose logs -f");
  }
}
```

The catalog in `src/recipes/catalog.ts` names every production recipe; read the
one closest to what you are building rather than a paraphrase of it.
`ProjectRecipe` is the transactional outlier — it composes the other recipes and
turns a failed postcondition into a rollback — so do not copy its shape for a
plain subsystem.

## Registering a Recipe

Add the instance to the catalog, `src/recipes/catalog.ts`:

```typescript
import { NewRecipe } from "./NewRecipe";

export const recipeRegistry = new RecipeRegistry([
  …,
  new NewRecipe(),
]);
```

`pj add <id>` resolves through `recipeRegistry`, so that one line is the whole
registration; `src/index.ts` has no per-recipe branch. To also list the
subsystem in `pj subsystems` and in the "Available:" hint, add its id to
`LEGACY_PUBLIC_RECIPE_IDS` in `src/utils/registry.ts`.

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
