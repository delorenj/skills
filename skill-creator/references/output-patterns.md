# Output Patterns

Patterns for skills that produce structured output (reports, commit messages, formatted documents, generated code). Match the pattern to the strictness needed.

## Reading Order

| Task | Read |
|------|------|
| Output must match exact format (API responses, data formats) | [Template Pattern: Strict variant](#template-pattern-strict-variant) |
| Output should follow a default but allow adaptation | [Template Pattern: Flexible variant](#template-pattern-flexible-variant) |
| Output quality depends on stylistic examples | [Examples Pattern](#examples-pattern) |
| Output combines multiple parts that must be assembled | [Composition Pattern](#composition-pattern) |
| Skill produces output that fails in subtle ways | [Gotchas](#gotchas) |

## Template Pattern: Strict Variant

For strict requirements (API responses, data formats, where deviation breaks downstream consumers):

```markdown
## Report structure

ALWAYS use this exact template structure:

# [Analysis Title]

## Executive summary
[One-paragraph overview of key findings]

## Key findings
- Finding 1 with supporting data
- Finding 2 with supporting data
- Finding 3 with supporting data

## Recommendations
1. Specific actionable recommendation
2. Specific actionable recommendation
```

The `ALWAYS use this exact template structure` directive removes ambiguity. Bracketed placeholders signal what content goes where.

## Template Pattern: Flexible Variant

For flexible guidance (reports where adaptation improves clarity, where the agent has judgment to apply):

```markdown
## Report structure

Here is a sensible default format, but use your best judgment:

# [Analysis Title]

## Executive summary
[Overview]

## Key findings
[Adapt sections based on what you discover]

## Recommendations
[Tailor to the specific context]

Adjust sections as needed for the specific analysis type.
```

The `use your best judgment` and `Adapt sections` signals tell the agent that the template is a starting point, not a contract.

## Examples Pattern

For skills where output quality depends on seeing examples (style, voice, level of detail), provide input/output pairs:

```markdown
## Commit message format

Generate commit messages following these examples:

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware

**Example 2:**
Input: Fixed bug where dates displayed incorrectly in reports
Output:
fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently across report generation

Follow this style: type(scope): brief description, then detailed explanation.
```

Examples teach the agent the desired style and level of detail more reliably than descriptions alone. Two to four examples is usually enough.

### When to Add a Counter-Example

If a common failure mode exists, include one bad example explicitly:

```markdown
**Avoid this style:**
Input: Fixed bug
Output: Fixed the bug in reports module

(Too generic. The output should name what was broken and what fixed it.)
```

Counter-examples are powerful but expensive on tokens. Use them only when the common failure is hard to describe abstractly.

## Composition Pattern

For output assembled from multiple parts (a report with a header, body sections, and a footer), describe the composition explicitly:

```markdown
## Report composition

Each report consists of these parts in order:

1. **Header** (required): Title, date, author. See [header template](./report-header.md).
2. **Executive summary** (required): One paragraph, no longer than 100 words.
3. **Findings sections** (1+ required): One per discovered issue. Use the finding template.
4. **Recommendations** (required): Numbered list, prioritized.
5. **Appendices** (optional): Raw data, methodology notes.

Generate parts in order. Do not skip required parts. Validate each part before moving to the next.
```

The numbered sequence and "do not skip required parts" instruction prevent the agent from fusing multiple parts or omitting them.

## Pattern Selection Guide

| Output type | Pattern |
|-------------|---------|
| Structured data (JSON, YAML, fixed-format text) | Template Strict |
| Reports with judgment-based adaptation | Template Flexible |
| Style-driven output (commit messages, prose, names) | Examples |
| Multi-part documents | Composition |
| Code with project conventions | Examples (with code examples) |

## Gotchas

### "Output ignores the template"

**Cause:** Template is shown but not introduced as authoritative.
**Solution:** Use phrases like `ALWAYS use this exact template` or `The output MUST follow this structure`. Place the directive before the template, not after.

### "Examples produce wooden output"

**Cause:** All examples follow exactly the same shape; the agent over-fits and produces output identical to the examples.
**Solution:** Vary the examples. Include short and long inputs, technical and non-technical content, edge cases. The variance teaches generalization.

### "Output is too verbose"

**Cause:** Template includes long placeholder text; the agent treats placeholders as size cues.
**Solution:** Use short bracketed placeholders. Add explicit length constraints: `[Overview, max 3 sentences]` or `[One-paragraph summary, no more than 100 words]`.

### "Output omits required sections"

**Cause:** Required and optional sections are not visually distinguished.
**Solution:** Mark required sections explicitly: `## Executive summary (required)`. Add a checklist at the end: `Before delivering: confirm all required sections are present.`

### "Counter-examples become anti-templates"

**Cause:** A counter-example is shown without enough context; the agent treats it as another acceptable variant.
**Solution:** Always pair counter-examples with explanations: `Avoid this style: ...` and `Reason: ...`. Use formatting that makes the bad example visually distinct (block quote, ❌ marker).

## See Also

- [workflows.md](./workflows.md) for procedural patterns when output requires multiple steps
- [routing-mechanics.md](./routing-mechanics.md) for navigation tables, triage tables, and the Four-Part Gotcha Structure that complements output patterns
- [design-principles.md](./design-principles.md) for high-level skill structure
- [gotchas.md](./gotchas.md) for skill-creation failure modes broadly
