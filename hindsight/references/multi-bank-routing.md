# Multi-bank routing

## Multi-Bank Routing Architecture

For multi-agent or multi-project setups, use domain-first routing to prevent cross-project pollution and recall noise.

### Strategy

- **Primary bank = domain/product** (source of truth). Example: `wean`, `chorescore`, `33GOD`
  (exact case — `33god`/`33god-core`/`33god-infra` were consolidated into `33GOD`
  and deleted 2026-08-17; naming one silently creates a NEW empty bank)
- **Secondary bank(s) = role/hierarchy overlay**. Example: `exec-office` for leadership decisions
- **Global fallback bank**. Example: `33GOD` for org-wide context

Never make an agent-named bank the **canonical** store for project facts — a
repo's truth must stay readable by every agent that works it, and an agent bank
would hide it. That is a rule about *canonical project memory*, and it is not a
ban on agent banks.

### The two namespaces (identity vs. project)

Agent banks have their own distinct job, and the two namespaces are disjoint by
design — they answer opposite questions and must not be collapsed:

| | `agent-<profile>` | `<repo>` |
| --- | --- | --- |
| Anchored to | agent identity | repository |
| Path-dependent | **no** — follows the agent everywhere | yes |
| Written | automatically, by the Hermes memory provider | explicitly, via this CLI |
| Audience | that agent alone | every agent on the repo |
| Answers | "which projects has this agent worked on?" | "which agent experienced this fact?" |

Hermes wires the identity bank through `memory.bank_id_template:
agent-{profile}` in `~/.hermes/config.yaml`; `{profile}` resolves to the agent's
identity, never to `cwd`. Project banks are resolved per-repo by **Bank
Detection** above.

Routing test when retaining: *would another agent on this repo need this?*
Yes → repo bank (and name yourself in the content, so provenance survives).
Only true of you → identity bank.

### Routing Pattern

For each agent/session:

1. Resolve **writeBank** (where new memories are retained)
2. Resolve **recallBanks[]** (ordered primary -> secondary -> fallback)
3. On prompt build, recall from each bank and merge results
4. On run end/reset/tool-error, retain high-signal facts into writeBank

### Capture Policy (high signal only)

**Retain automatically for:**
- Explicit memory intent ("remember", "don't forget", preferences)
- Post-run user facts/decisions
- High-level architectural patterns
- Pre-reset session summaries
- Non-standard system paths/configs
- Tool errors (debugging context)

**Do NOT retain:**
- Cron/noise/system spam
- Tiny one-word messages
- Slash commands

### Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Cross-project pollution | writeBank too broad | Tighten routing to domain bank |
| Recall noise | Too many recallBanks or topK too high | Cap at 3-4 banks |
| Missed intent | Memory-intent regex too strict | Expand capture triggers |
| Latency spike | Recalling too many banks per prompt | Reduce recallBanks count |

## When to Retain

- Discovered a bug fix or workaround
- Found a project convention or pattern
- Learned a user preference
- Completed a significant task (summarize what was done)
- Found something that didn't work (negative knowledge is valuable)

## When to Recall

- Before starting any non-trivial task
- When working in an unfamiliar area of the codebase
- When making architectural or tooling decisions
- When the user asks about past work or patterns

## Best Practices

1. **Be specific**: "npm test requires --experimental-vm-modules" not "tests need a flag"
2. **Include outcomes**: Store what worked AND what didn't
3. **Use context categories**: Tag with the right context for better retrieval
4. **Recall first**: Check for relevant context before starting work
5. **Don't duplicate**: Check if knowledge already exists before retaining
6. **Use document_id**: Group related session facts so they compound, not duplicate
7. **Create mental models**: For topics you reflect on repeatedly
8. **Use directives**: For hard rules that must always be enforced during reflect

