# Validation

Validation is the iterative feedback loop that catches misconfigured nodes, broken expressions, missing required fields, and structural workflow problems before deployment. The n8n validation tools (`validate_node`, `validate_workflow`, and friends) return structured errors, warnings, and suggestions. Expect 2 to 3 validate, fix, revalidate cycles per node. This reference explains how to interpret the results, which warnings are real, which are false positives, and how to recover from broken state.

## When to Use

| Situation | What to Read |
|---|---|
| You just got a validation error and need to interpret it | [gotchas.md](./gotchas.md) |
| You are wiring `validate_node` or `validate_workflow` into a flow | [api.md](./api.md) |
| You want to know the validate, fix, revalidate cadence | [patterns.md](./patterns.md) |
| A warning seems wrong or noisy and you want to know if it is safe to ignore | [gotchas.md](./gotchas.md) (False Positives section) |
| You are picking a profile (`strict` vs `runtime` vs `ai-friendly` vs `minimal`) | [configuration.md](./configuration.md) |
| You are recovering from a workflow with broken connections or stale references | [patterns.md](./patterns.md) (Recovery Patterns) |

## Quick Start

```javascript
// 1. Configure your node
let config = {
  resource: "message",
  operation: "post",
  channel: "#general",
  text: "Hello"
};

// 2. Validate it
const result = validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "runtime"   // recommended default
});

// 3. Check valid field
if (!result.valid) {
  // Fix errors first, warnings second
  result.errors.forEach(err => console.log(err.property, err.message, err.fix));
}

// 4. Revalidate. Repeat until valid.
```

The golden rules:

1. Validate after every significant configuration change.
2. Fix errors before warnings.
3. Use the `runtime` profile by default.
4. Read the full error message, it usually contains the fix.
5. Trust auto-sanitization for IF/Switch operator structure (do not manually fix `singleValue`).

## Reading Order

| Task | Files to Read |
|---|---|
| Interpret a single validation error | [gotchas.md](./gotchas.md), [api.md](./api.md) |
| Build a validate, fix, revalidate loop | [patterns.md](./patterns.md), [api.md](./api.md) |
| Pick a validation profile for your stage | [configuration.md](./configuration.md), [patterns.md](./patterns.md) |
| Triage warnings (fix vs accept) | [gotchas.md](./gotchas.md) (False Positives), [configuration.md](./configuration.md) |
| Recover from broken connections or stale references | [patterns.md](./patterns.md), [gotchas.md](./gotchas.md) |
| Onboard to n8n validation from scratch | [README.md](./README.md), [api.md](./api.md), [patterns.md](./patterns.md), [gotchas.md](./gotchas.md), [configuration.md](./configuration.md) |

## In This Reference

- **[api.md](./api.md)**: Tool signatures and parameter shapes for `validate_node`, `validate_workflow`, `n8n_autofix_workflow`, and `n8n_update_partial_workflow` (the auto-fix and cleanup tool). Includes the validation result structure.
- **[patterns.md](./patterns.md)**: The iterative validation loop, progressive validation, error triage, edit-then-revalidate, recovery strategies, and auto-sanitization behavior.
- **[gotchas.md](./gotchas.md)**: Every error type (`missing_required`, `invalid_value`, `type_mismatch`, `invalid_expression`, `invalid_reference`, `patchNodeField` errors, workflow-level errors) and every documented false positive, each in the four-part bad/good format.
- **[configuration.md](./configuration.md)**: The four validation profiles (`minimal`, `runtime`, `ai-friendly`, `strict`), selection criteria, and profile strategies by workflow type and lifecycle stage.

## Philosophy

Validation is iterative, not one-shot. Telemetry shows 7,841 occurrences of the configure, validate, fix, revalidate pattern, with average 23 seconds spent reading errors and 58 seconds spent fixing per cycle. Plan for it. Embrace it.

Validation is also not a binary signal. Errors block execution and must be fixed. Warnings are context-dependent: roughly 40 percent are acceptable false positives in specific use cases. The `ai-friendly` profile reduces false positives by about 60 percent. Pick your profile to match your stage and accept what you can defend.

## See Also

- [../mcp-tools/](../mcp-tools/): How to call the `validate_*` MCP tools and their place in the broader tool surface.
- [../node-configuration/](../node-configuration/): Required fields, allowed values, and discriminators (`resource`, `operation`, `mode`) that `missing_required` and `invalid_value` errors point you back to.
- [../expressions/](../expressions/): Expression syntax for fixing `invalid_expression` errors (missing `={{ }}`, node references, safe navigation, webhook `.body` gotcha).
- [../workflow-patterns/](../workflow-patterns/): Structural patterns for connections, branches, and triggers that `validate_workflow` checks against.
