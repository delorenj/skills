# Validation Configuration

Validation profiles and selection strategies. Profiles trade strictness against noise. Pick the right one for your lifecycle stage and workflow type.

## Profile Overview

| Profile | Strictness | Use For | Typical Noise |
|---|---|---|---|
| `minimal` | Lowest | Quick checks during editing | Almost zero |
| `runtime` | Medium (recommended default) | Pre-deployment validation | Balanced |
| `ai-friendly` | Medium minus false positives | AI-generated configs | About 60 percent fewer false positives than `runtime` |
| `strict` | Highest | Production deployment, critical workflows | High |

## minimal

Use when: quick checks during editing, integration testing where you only care that connections resolve, rapid iteration sessions.

Validates:
- Only required fields
- Basic structure

Pros:
- Fastest
- Most permissive
- Lowest noise

Cons:
- May miss real issues
- Skips type checking and allowed-value enforcement

```javascript
validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "minimal"
});
```

## runtime (Recommended Default)

Use when: pre-deployment validation, the default profile for almost all use cases.

Validates:
- Required fields
- Value types
- Allowed values
- Basic dependencies

Pros:
- Balanced
- Catches real errors without overwhelming noise
- The right default for most situations

Cons:
- Some edge cases missed
- Some false positives still surface

```javascript
validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "runtime"
});
```

**This is the recommended profile for most use cases.** Start here. Only move to `strict` or `ai-friendly` if you have a specific reason.

## ai-friendly

Use when: AI-generated configurations, rapid generation loops, when warnings-as-noise are slowing the loop down.

Validates:
- Same checks as `runtime`
- Reduces false positives by about 60 percent
- More tolerant of minor issues

Pros:
- Less noisy for AI workflows
- Lets the loop converge faster
- Filters out the most common context-dependent warnings

Cons:
- May allow some questionable configs through
- Not appropriate for final production validation

```javascript
validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "ai-friendly"
});
```

## strict

Use when: production deployment, critical workflows, final pre-launch review, security-sensitive workflows.

Validates:
- Everything in `runtime`
- Plus best practices
- Plus performance concerns
- Plus security issues

Pros:
- Maximum safety
- Surfaces every concern

Cons:
- Many warnings, including false positives
- Too noisy for active development
- Requires manual triage of every warning

```javascript
validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "strict"
});
```

## Selection Strategy: Progressive Strictness

Move from permissive to strict as the workflow matures.

### Development Stage

```javascript
validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "ai-friendly"   // fewer warnings during active development
});
```

Goal: stay in flow, fix real errors, ignore noise.

### Pre-Production Stage

```javascript
validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "runtime"   // balanced validation before promoting
});
```

Goal: catch real issues that would block execution or cause runtime errors.

### Production Deployment

```javascript
validate_node({
  nodeType: "nodes-base.slack",
  config,
  profile: "strict"   // every warning, manual review of each
});
```

Goal: surface everything, accept or fix each warning consciously, document accepted false positives.

## Selection Strategy: Profile by Workflow Type

Different workflow categories warrant different defaults.

| Workflow Type | Default Profile | Accept | Fix |
|---|---|---|---|
| Quick automations (one-shot scripts) | `ai-friendly` | Most warnings | Errors + security warnings |
| Business-critical workflows | `strict` | Very few warnings | Everything possible |
| Integration testing | `minimal` | All warnings | Only errors that prevent execution |
| Internal tooling (your team only) | `runtime` | Context-dependent warnings | Errors + critical warnings |
| Customer-facing automation | `strict` | Almost nothing | Everything |
| AI-generated workflows | `ai-friendly` initially, then `runtime` | Noise during generation | All errors before deployment |

## Selection Strategy: Profile and Tooling

When you set up a validation pipeline or a recurring validation step, set the profile explicitly and document the choice.

### Per-Tool Profile Setting

`validate_node` and `validate_workflow` both accept `profile`. There is no global default that overrides the call site, so always set it explicitly.

### When to Override the Default

| Situation | Override To |
|---|---|
| You are AI-generating configs and the loop is slow due to warning noise | `ai-friendly` |
| You are reviewing a workflow for production launch | `strict` |
| You are doing a structural check (do nodes connect, do expressions parse) | `minimal` |
| You are running CI on every PR | `runtime` |
| You are about to enable a workflow on a critical schedule | `strict` |

## Dependency: Validation Tool Availability

The validation profiles are part of the n8n MCP tool surface. To call `validate_node` or `validate_workflow` with any profile, you need:

- The n8n-mcp server connected
- The target workflow accessible (for `validate_workflow`)
- The node type known to the server (for `validate_node`)

See [../mcp-tools/](../mcp-tools/) for the broader MCP setup and tool catalog.

## Dependency: Auto-Sanitization

Auto-sanitization runs automatically on workflow save regardless of validation profile. There is no profile setting that disables it. If you want to see what auto-sanitization will change, validate with `strict` and observe the operator_structure warnings, then save and observe that they disappear.

See [patterns.md](./patterns.md) (Trust Auto-Sanitization) for what it does and does not fix.

## Types

There are no custom TypeScript or schema types specific to validation profiles. The profile parameter is a string literal union: `"minimal" | "runtime" | "ai-friendly" | "strict"`. Any other string will be rejected.

## See Also

- [api.md](./api.md): Where the `profile` parameter is documented on each tool.
- [patterns.md](./patterns.md): Profile selection in the context of the validate, fix, revalidate loop.
- [gotchas.md](./gotchas.md): False positives that the `ai-friendly` profile suppresses.
- [../mcp-tools/](../mcp-tools/): MCP tool setup that hosts the validation tools.
