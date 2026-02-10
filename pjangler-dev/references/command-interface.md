# Command Interface Reference

## Interfaces

```typescript
export interface InvokeResult {
  success: boolean;
  message: string;
  filePath?: string;
}

export interface CommandContext {
  targetDir: string;
  force?: boolean;
}
```

## Base Command Class

```typescript
export abstract class Command {
  protected context: CommandContext;

  constructor(context: CommandContext) {
    this.context = context;
  }

  abstract invoke(): Promise<InvokeResult>;

  protected fileExists(filePath: string): boolean;
  protected writeFile(filePath: string, content: string): void;
  protected createDirectory(dirPath: string): void;
}
```

## Complete Examples

### Simple File Command

```typescript
import { Command, InvokeResult } from "./Command";

export class AddGitignore extends Command {
  async invoke(): Promise<InvokeResult> {
    const filePath = ".gitignore";

    if (this.fileExists(filePath) && !this.context.force) {
      return {
        success: false,
        message: "⚠️  .gitignore already exists",
        filePath
      };
    }

    const content = `node_modules
dist
.env
*.log
`;

    this.writeFile(filePath, content);
    return {
      success: true,
      message: "✅ Created .gitignore",
      filePath
    };
  }
}
```

### Directory Command

```typescript
import { Command, InvokeResult } from "./Command";

export class AddSrcStructure extends Command {
  async invoke(): Promise<InvokeResult> {
    this.createDirectory("src/components");
    this.createDirectory("src/utils");
    this.createDirectory("src/types");

    return {
      success: true,
      message: "✅ Created src/ directory structure",
      filePath: "src"
    };
  }
}
```

### Multi-File Command Module

When multiple related commands share a domain, group them in one file:

```typescript
// src/commands/PythonCommands.ts
import { Command, InvokeResult } from "./Command";

export class AddPyprojectToml extends Command {
  async invoke(): Promise<InvokeResult> {
    const filePath = "pyproject.toml";

    if (this.fileExists(filePath) && !this.context.force) {
      return {
        success: false,
        message: "⚠️  pyproject.toml already exists",
        filePath
      };
    }

    const content = `[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"

[tool.uv]
dev-dependencies = ["pytest", "ruff"]
`;

    this.writeFile(filePath, content);
    return {
      success: true,
      message: "✅ Created pyproject.toml",
      filePath
    };
  }
}

export class AddRuffConfig extends Command {
  async invoke(): Promise<InvokeResult> {
    const filePath = "ruff.toml";

    if (this.fileExists(filePath) && !this.context.force) {
      return {
        success: false,
        message: "⚠️  ruff.toml already exists",
        filePath
      };
    }

    const content = `line-length = 88
target-version = "py311"

[lint]
select = ["E", "F", "I", "UP"]
`;

    this.writeFile(filePath, content);
    return {
      success: true,
      message: "✅ Created ruff.toml",
      filePath
    };
  }
}
```

### Template File with Variables

For commands that generate files with project-specific content:

```typescript
import { Command, InvokeResult, CommandContext } from "./Command";
import { basename } from "path";

export class AddPackageJson extends Command {
  async invoke(): Promise<InvokeResult> {
    const filePath = "package.json";

    if (this.fileExists(filePath) && !this.context.force) {
      return {
        success: false,
        message: "⚠️  package.json already exists",
        filePath
      };
    }

    // Derive project name from directory
    const projectName = basename(this.context.targetDir);

    const content = `{
  "name": "${projectName}",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "start": "bun run src/index.ts",
    "dev": "bun --watch src/index.ts",
    "test": "bun test"
  }
}
`;

    this.writeFile(filePath, content);
    return {
      success: true,
      message: "✅ Created package.json",
      filePath
    };
  }
}
```
