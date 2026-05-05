# Workflow Patterns

Patterns for skills that orchestrate multi-step processes. Match the pattern to the workflow shape: linear, branching, parallel, or retry-driven.

## Reading Order

| Task | Read |
|------|------|
| Linear multi-step task | [Sequential Workflows](#sequential-workflows) |
| Task with decision points | [Conditional Workflows](#conditional-workflows) |
| Independent steps that can run together | [Parallel Workflows](#parallel-workflows) |
| Steps that may fail and need re-attempt | [Retry Workflows](#retry-workflows) |
| Combining workflow patterns | [Composition](#composition-of-workflow-patterns) |
| Designing a new workflow | [Selection Guide](#selection-guide) |
| Debugging workflow design | [Gotchas](#gotchas) |

## Sequential Workflows

For linear tasks, break operations into clear, sequential steps. Give the agent an overview at the top, then expand each step:

```markdown
Filling a PDF form involves these steps:

1. Analyze the form (run analyze_form.py)
2. Create field mapping (edit fields.json)
3. Validate mapping (run validate_fields.py)
4. Fill the form (run fill_form.py)
5. Verify output (run verify_output.py)

### Step 1: Analyze the form
[detail]

### Step 2: Create field mapping
[detail]

[...]
```

Place the numbered overview before the detailed steps. The overview gives the agent a mental model before reading details.

### Sequential Workflow Anti-Pattern

Steps that assume previous output without validating:

```markdown
❌ BAD:
Step 2: Create field mapping based on Step 1 output.

✅ GOOD:
Step 2: Create field mapping.

Read fields.json (created in Step 1). If fields.json is missing or empty, return to Step 1.
For each field in fields.json:
  ...
```

The validation guard prevents cascading failure when an earlier step did not produce its expected output.

## Conditional Workflows

For tasks with branching logic, present decision points explicitly:

```markdown
1. Determine the modification type:
   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below
   **Reviewing existing content?** → Follow "Review workflow" below

2. Creation workflow:
   - Step 2.1: ...
   - Step 2.2: ...

3. Editing workflow:
   - Step 3.1: ...
   - Step 3.2: ...

4. Review workflow:
   - Step 4.1: ...
   - Step 4.2: ...
```

Each branch gets its own numbered subsection. The branches do not interleave; the agent commits to one branch and follows it through.

### N-Way Branching

For workflows with 4+ branches, switch to a routing table:

```markdown
1. Identify the operation type:

| Operation | Workflow | Branch |
|-----------|----------|--------|
| Create | Creation workflow | §2 |
| Edit | Editing workflow | §3 |
| Review | Review workflow | §4 |
| Delete | Deletion workflow | §5 |
| Export | Export workflow | §6 |
| Migrate | Migration workflow | §7 |

2. Follow the workflow for your operation type.
```

The table eliminates a long if-else chain in prose form.

## Parallel Workflows

For tasks with independent steps that can run together, mark the parallelism explicitly:

```markdown
After analysis is complete, run these steps IN PARALLEL (no dependencies between them):

- **Generate report:** run generate_report.py with analysis output
- **Notify stakeholders:** run notify.py with summary
- **Archive raw data:** run archive.py with timestamp

Wait for all three to complete before proceeding to the verification step.
```

The "IN PARALLEL" marker and the "no dependencies between them" justification tell the agent it is safe to dispatch concurrently. The "Wait for all three" sets the synchronization point.

## Retry Workflows

For steps that may fail (network calls, rate-limited APIs, transient errors), specify the retry policy:

```markdown
3. Upload to storage (with retry):
   - Attempt the upload
   - On failure with status 429 or 503: wait 2 seconds, retry up to 3 times with exponential backoff
   - On failure with status 4xx (other than 429): do not retry; report the error
   - On failure with status 5xx (other than 503): retry once after 5 seconds
   - After max retries: log the failure and continue with degraded output (do not abort the workflow)
```

Specify: which errors are retryable, how many attempts, the backoff strategy, and what to do on terminal failure. Vague "retry on failure" instructions produce inconsistent retry behavior.

## Composition of Workflow Patterns

Real workflows combine patterns. Document the composition explicitly:

```markdown
## Document Generation Workflow

This workflow uses three patterns:
- **Sequential** for the overall flow (analyze → generate → verify)
- **Conditional** within step 2 (different generation paths per document type)
- **Retry** within step 1 for the API call to the analysis service

### Step 1: Analyze (with retry)
[retry workflow detail]

### Step 2: Generate (conditional)
[conditional workflow detail]

### Step 3: Verify
[sequential continuation]
```

Naming the patterns at the top helps the agent build a structural model before reading details.

## Selection Guide

| Workflow shape | Pattern | Marker phrase |
|----------------|---------|---------------|
| Linear, step A then B then C | Sequential | "involves these steps" |
| Single decision then continue | Conditional (2-way) | "Determine the [type]: ... → ..." |
| Multi-way decision | Conditional (table) | "Identify the operation type: [table]" |
| Independent concurrent steps | Parallel | "IN PARALLEL (no dependencies)" |
| Error-prone external calls | Retry | "with retry: on failure with..." |
| Mixed shape | Composition | "This workflow uses [pattern1] and [pattern2]" |

## Gotchas

### "Workflow has no overview"

**Cause:** The agent reads through detailed steps without seeing the structure first.
**Solution:** Always include a numbered overview at the top before the detailed steps. The overview should be readable in 5 seconds.

### "Conditional branches are interleaved"

**Cause:** Steps from branch A and branch B alternate, confusing the agent about which branch it is in.
**Solution:** Group all of branch A under one heading, all of branch B under another. The agent commits to one branch and reads through it.

### "Parallel steps have hidden dependencies"

**Cause:** The author marks steps as parallel but they actually depend on each other.
**Solution:** Verify independence before marking parallel. If step B reads a file step A writes, they are not parallel; they are sequential.

### "Retry policy is vague"

**Cause:** "Retry on failure" without specifying which failures, how many times, or what to do at exhaustion.
**Solution:** Name the retryable errors, the count, the backoff, and the fallback. See [Retry Workflows](#retry-workflows) for a full template.

### "Steps assume previous output without checking"

**Cause:** Step 5 assumes step 4 produced a file; if step 4 failed silently, step 5 produces wrong output.
**Solution:** Add validation guards at each step boundary: `Read fields.json. If missing or empty, return to step N`.

### "Workflow exceeds the agent's working memory"

**Cause:** A 20-step linear workflow without checkpoints; the agent loses track partway through.
**Solution:** Break into phases with checkpoints. After each phase, summarize what has been completed and what remains. Save intermediate state to files when possible.

### "No termination condition"

**Cause:** A retry or iterative workflow has no clear exit, and the agent loops indefinitely.
**Solution:** Always specify the termination: "After max 3 attempts, abort", "Continue until the queue is empty or 100 items processed".

## See Also

- [output-patterns.md](./output-patterns.md) for patterns governing the result of a workflow
- [routing-mechanics.md](./routing-mechanics.md) for decision tree, triage table, and reading order table primitives that workflows often use
- [design-principles.md](./design-principles.md) for high-level skill structure
- [gotchas.md](./gotchas.md) for skill-creation failure modes broadly
