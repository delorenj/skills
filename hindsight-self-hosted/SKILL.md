---
name: hindsight-self-hosted
description: Store team knowledge, project conventions, and learnings from tasks. Use to remember context across sessions via shared Hindsight memory banks.
---

# Hindsight Memory (Self-Hosted)

You have persistent memory via a self-hosted Hindsight server. This is a shared team memory bank.

## Bank Detection

Auto-detect bank from git repo name:

```bash
BANK=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "general")
```

## Commands

### Store a memory

```bash
hindsight memory retain $BANK "description of what you learned" --context <category>
```

Context categories: `architecture`, `conventions`, `debugging`, `deployment`, `dependencies`, `preferences`, `session-summary`, `code-edit`

### Recall memories

```bash
hindsight memory recall $BANK "what are you looking for?"
```

### Reflect (synthesize with reasoning)

```bash
hindsight memory reflect $BANK "question to reason about"
```

## When to Retain

- Bug fixes and workarounds discovered
- Project conventions and patterns found
- User preferences learned (attribute by name: "Alice prefers X")
- Architecture decisions and their rationale
- Things that did NOT work (negative knowledge is valuable)
- Significant task completions (summarize what was done)

## When to Recall

- Before starting any non-trivial task
- When working in unfamiliar code
- When making architecture or tooling decisions
- When a team member asks about past work

## Best Practices

1. **Be specific**: "npm test requires --experimental-vm-modules" not "tests need a flag"
2. **Include outcomes**: Store what worked AND what didn't
3. **Use context categories**: Tag for better retrieval
4. **Attribute preferences**: "Alice prefers X" not just "User prefers X"
5. **Don't duplicate**: Recall first to check if knowledge already exists
