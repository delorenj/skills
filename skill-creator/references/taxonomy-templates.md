# Reference Taxonomy Templates

The references taxonomy is the structure of files inside a skill's `references/` directory (for standalone and member skills) or inside each `references/<topic>/` (for reference-hubs). Pick a template by domain type. Uniformity within a skill is a feature: agents that learn the structure from one topic generalize it to all others.

## Reading Order

| Task | Read |
|------|------|
| New skill, picking taxonomy | [Selection Guide](#selection-guide) and your domain's template |
| Hub skill, designing topic taxonomy | [API/Product Domain Template](#apiproduct-domain-template) |
| Meta-skill (skill about skills, code review, planning) | [Meta-Domain Template](#meta-domain-template) |
| Workflow-orchestration skill | [Workflow-Domain Template](#workflow-domain-template) |
| Tool/CLI-focused skill | [Tool-Domain Template](#tool-domain-template) |
| Mixing taxonomies | [Hybrid and Custom Taxonomies](#hybrid-and-custom-taxonomies) |
| Failure modes | [Gotchas](#gotchas) |

## Selection Guide

| Skill type | Template | Files per topic |
|---|---|---|
| API/SDK/product (one product or a hub of many) | API/Product | README, api, patterns, gotchas, configuration |
| Meta-skill (about authoring, reviewing, designing) | Meta | anatomy/principles, frontmatter-guide, gotchas, output-patterns, workflows |
| Workflow orchestration (multi-step procedures) | Workflow | phases, decision-points, gotchas, output-templates |
| Tool/CLI (a single command or tool family) | Tool | commands, configuration, recipes, gotchas |
| Mixed | Hybrid | See [Hybrid](#hybrid-and-custom-taxonomies) |

## API/Product Domain Template

Used by reference-hubs covering APIs, SDKs, or platform products. The cloudflare hub uses this for every topic under `references/`.

```
references/<topic>/
├── README.md          Overview, when-to-use, quick start, reading order, links to siblings
├── api.md             Method signatures, parameter tables, examples per method
├── patterns.md        Copy-paste-ready implementation patterns (caching, sessions, etc.)
├── gotchas.md         Common errors in four-part structure (Cause/Solution/bad-good code)
└── configuration.md   Setup, CLI commands, binding snippets, type declarations
```

For non-hub members of an API/product domain (e.g., `cloudflare-wrangler` as a standalone-shaped member), the same files appear directly under `references/` without a topic prefix.

### File scoping rules (strict)

| File | Contains | Does NOT contain |
|------|----------|------------------|
| README.md | Overview, comparison tables, quick start (5-10 lines), reading order, sibling links | Method details, error catalogs, deep config |
| api.md | Method signatures, params, return types, per-method examples | Setup steps, error patterns, architectural patterns |
| patterns.md | Composite patterns (multi-method recipes), good/bad comparisons | Single-method docs, config |
| gotchas.md | Quoted error names, Cause, Solution, bad/good code | Method docs, normal usage |
| configuration.md | Setup, bindings, type generation, local dev | Usage patterns, error handling |

The strictness is the point. An agent that knows the rule never has to guess where to look.

## Meta-Domain Template

Used by skills about skills, code review, planning, or any process that operates on artifacts rather than producing operational output.

```
references/
├── anatomy.md             Structural reference (what the artifacts contain)
├── design-principles.md   Conceptual model (why the structure exists)
├── frontmatter-guide.md   How to write metadata that triggers/routes correctly
├── gotchas.md             Common authoring failure modes (four-part structure)
├── output-patterns.md     Output format templates (when meta-skill produces structured output)
└── workflows.md           Sequential/conditional process patterns
```

Optional additions for meta-domain hubs:
- `topology-decision.md` if the meta-skill includes topology choices
- `taxonomy-templates.md` if the meta-skill teaches reference design
- `routing-mechanics.md` if the meta-skill teaches hub routing
- `migration.md` if the meta-skill teaches restructuring

The `skill-creator` skill itself uses an extended Meta template with all four optional additions.

### File scoping rules

| File | Contains |
|------|----------|
| anatomy.md | What the artifact's parts are and what each part is for |
| design-principles.md | Why the structure works (concise, progressive disclosure, etc.) |
| frontmatter-guide.md | Specific authoring rules for metadata fields |
| gotchas.md | Failure-mode catalog with bad/good examples |
| output-patterns.md | Templates for output when the meta-skill produces structured artifacts |
| workflows.md | Multi-step process patterns the meta-skill might teach |

## Workflow-Domain Template

Used by skills that orchestrate multi-step procedures (build-release pipelines, incident response, debugging methodologies).

```
references/
├── phases.md              Each phase, what it accomplishes, entry and exit criteria
├── decision-points.md     Branching logic at key decisions
├── gotchas.md             Common failure modes (four-part structure)
└── output-templates.md    Templates for outputs at each phase
```

Optional additions:
- `tools-<name>.md` per supporting tool (e.g., `tools-grafana.md`, `tools-pagerduty.md`)
- `escalation.md` for workflows that involve handoffs

### File scoping rules

| File | Contains |
|------|----------|
| phases.md | One section per phase, with entry/exit criteria and outputs |
| decision-points.md | Branching tables and decision tree diagrams |
| gotchas.md | Phase-specific failure modes with recovery actions |
| output-templates.md | Templates for status reports, runbooks, incident summaries |

## Tool-Domain Template

Used by skills covering a single CLI tool, command, or tightly-scoped utility.

```
references/
├── commands.md            Per-command syntax, flags, examples
├── configuration.md       Config file format, environment variables, secrets
├── recipes.md             Common task workflows (compose multiple commands)
└── gotchas.md             Common errors and version-specific issues
```

Examples: `cloudflare-wrangler`, a hypothetical `git-flow` or `terraform-cli` skill.

### File scoping rules

| File | Contains |
|------|----------|
| commands.md | Subcommand-by-subcommand reference |
| configuration.md | Config schema, env vars, auth setup |
| recipes.md | Multi-step task recipes that compose commands |
| gotchas.md | Error catalog (four-part) including version-specific issues |

## Hybrid and Custom Taxonomies

Some skills span domains. Use these rules to combine templates:

1. **Always include `gotchas.md`.** Every domain has failure modes worth cataloging.
2. **Use the more specific template for the dominant domain.** A skill that is 80% API and 20% workflow uses the API template plus a `workflows.md` from the Meta template.
3. **Custom files are allowed but should be obvious from name alone.** A `migration-checklist.md` is fine; a `misc.md` is not.
4. **Justify any deviation in a one-line note at the top of the README or the relevant file.** "This skill adds `escalation.md` because incident handoffs are domain-specific" is enough.

### Hybrid Example: `cloudflare-agents-sdk`

This skill is API-product-domain (Agents SDK methods) plus workflow-domain (build-an-agent procedures). Its taxonomy combines both:

```
references/
├── README.md          (API domain)
├── api.md             (API domain)
├── patterns.md        (API domain)
├── gotchas.md         (always)
├── configuration.md   (API domain)
└── workflows.md       (Workflow domain - the multi-step build process)
```

## Topic Naming Conventions

For reference-hubs with `references/<topic>/` subdirectories:

- Use the canonical product/feature name in lowercase kebab-case: `kv/`, `durable-objects/`, `workers-ai/`
- Match the name the user would search for, not internal codenames
- Avoid plural inconsistency: pick `workers/` OR `worker/`, not both

For non-hub skills with flat `references/`:

- Name files by what they contain, not by sequence: `api.md` not `step3.md`
- Use the same names across similar skills: `gotchas.md`, not `errors.md` in one skill and `pitfalls.md` in another

## Reading Order Tables

Every README.md in a reference taxonomy must include a reading order table. For non-hub flat references, every reference file (or at minimum the longest one) must include one at the top.

Template:

```markdown
## Reading Order

| Task | Files to Read |
|------|---------------|
| Quick start | README.md → configuration.md |
| Implement feature X | api.md → patterns.md |
| Debug error Y | gotchas.md → api.md |
| Performance tuning | gotchas.md (performance) → patterns.md (caching) |
```

Map task type to file sequence. Avoid prose explanations of "when to read what."

See [routing-mechanics.md](./routing-mechanics.md) for the full reading-order pattern.

## Gotchas

### Mixing taxonomies within one skill

**Symptom:** Half the topics under `references/` use API template; the other half are ad-hoc. Agents lose the pattern after the first inconsistent topic.

**Solution:** Pick one template per skill. Hybrid is fine if applied consistently. Inconsistency is not.

### Using domain-inappropriate template

**Symptom:** A meta-skill with `api.md` and `configuration.md` files that have nothing to fill them with.

**Solution:** Pick the template by what the skill actually contains, not by what cloudflare uses.

### Missing gotchas.md

**Symptom:** All other files present, but no gotchas.md. Agents have no failure-mode catalog.

**Solution:** Always include gotchas.md. Even if empty at first, the file's existence creates a place for failure-mode capture during iteration.

### Reading order table missing

**Symptom:** README.md lists files but does not say when to read each. Agent reads files in alphabetical or random order.

**Solution:** Add a reading order table mapping task type to file sequence. Non-negotiable.

### Topic directories with non-uniform file counts

**Symptom:** `kv/` has 5 files, `d1/` has 3 files, `r2/` has 7 files. Agent's mental model of the taxonomy fails.

**Solution:** Enforce uniformity. If a file is genuinely empty for a topic, leave it with a one-line note ("This product has no setup; bindings are zero-config"). Empty files preserve the pattern.

## See Also

- [topology-decision.md](./topology-decision.md) for choosing the topology that determines whether topic directories apply
- [routing-mechanics.md](./routing-mechanics.md) for reading order tables and triage
- [design-principles.md](./design-principles.md) for the progressive-disclosure rationale behind taxonomy uniformity
- [frontmatter-guide.md](./frontmatter-guide.md) for the optional `references:` frontmatter field that pre-warms specific taxonomy directories
