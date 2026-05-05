# Skill Anatomy

Reference for the structural elements that make up a skill, what each element is for, and what to exclude.

## Reading Order

| Task | Read |
|------|------|
| Creating your first skill | This file end-to-end |
| Deciding what goes in references/ vs SKILL.md | [Reference vs Body](#reference-files-references) section |
| Choosing between scripts, references, and assets | [Bundled Resources](#bundled-resources-optional) section |
| Trimming a bloated skill | [What to Not Include](#what-to-not-include-in-a-skill) section |
| Splitting a long SKILL.md | See [design-principles.md](./design-principles.md) progressive disclosure section |

## Top-Level Structure

Every skill consists of a required `SKILL.md` file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (required: name, description)
│   └── Markdown body (required)
└── Bundled resources (optional)
    ├── scripts/      Executable code (Python, Bash, etc.)
    ├── references/   Documentation loaded into context as needed
    └── assets/       Files used in skill output (templates, images, fonts)
```

## SKILL.md (Required)

Every `SKILL.md` consists of:

- **Frontmatter (YAML):** Contains `name` and `description`. These are the only fields the harness reads to decide when the skill triggers. Be clear and comprehensive. See [frontmatter-guide.md](./frontmatter-guide.md) for the full frontmatter design specification.
- **Body (Markdown):** Instructions for using the skill and its bundled resources. Loaded only AFTER the skill triggers.

## Bundled Resources (Optional)

### Scripts (`scripts/`)

Executable code (Python, Bash, etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

- **When to include:** When the same code is being rewritten repeatedly, or deterministic reliability is needed
- **Examples:** `scripts/rotate_pdf.py` for PDF rotation, `scripts/init_skill.py` for skill scaffolding
- **Benefits:** Token-efficient, deterministic, may be executed without loading into context
- **Note:** Scripts may still need to be read by the agent for patching or environment-specific adjustments. Test scripts by running them, not by reading them.

### Reference Files (`references/`)

Documentation loaded into context as needed to inform the agent's process and thinking.

- **When to include:** For documentation the agent should reference while working
- **Examples:** `references/finance.md` for financial schemas, `references/policies.md` for company policies, `references/api_docs.md` for API specifications
- **Use cases:** Database schemas, API documentation, domain knowledge, company policies, detailed workflow guides
- **Benefits:** Keeps SKILL.md lean, loaded only when the agent determines it is needed
- **Best practice:** If files exceed 10k words, include `grep` search patterns in SKILL.md so the agent can target sections instead of loading the whole file
- **Avoid duplication:** Information should live in either SKILL.md or in references files, not both. Prefer references unless content is truly core to the skill.

### Assets (`assets/`)

Files not intended to be loaded into context, but used within the output the skill produces.

- **When to include:** When the skill needs files that will be used in the final output
- **Examples:** `assets/logo.png` for brand assets, `assets/slides.pptx` for PowerPoint templates, `assets/frontend-template/` for HTML/React boilerplate, `assets/font.ttf` for typography
- **Use cases:** Templates, images, icons, boilerplate code, fonts, sample documents that get copied or modified
- **Benefits:** Separates output resources from documentation; the agent uses these files without loading them into context

## What to Not Include in a Skill

A skill should only contain essential files that directly support its functionality. Do NOT create extraneous documentation or auxiliary files such as:

- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- VERSION
- USAGE.md

The skill should only contain the information needed for an AI agent to execute the task. It should not contain auxiliary context about the skill creation process, setup or testing procedures, or user-facing documentation. Additional documentation files add clutter and confusion.

If you find yourself wanting to write a README, ask: "Is this for a human reading the repository, or for an agent doing the work?" If human, it does not belong in the skill.

## Reference vs Body: Where Content Lives

Use this decision rule for any new content:

| Content type | Where it lives |
|---|---|
| Procedural instructions ("when starting, do X then Y") | SKILL.md body |
| Routing tables, decision trees, navigation | SKILL.md body |
| Long-form domain knowledge (schemas, policies, APIs) | `references/<topic>.md` |
| Variant-specific patterns (AWS vs GCP, framework A vs B) | `references/<variant>.md` |
| Error catalogs and troubleshooting | `references/gotchas.md` |
| Output format templates and examples | `references/output-patterns.md` |
| Code that runs deterministically | `scripts/` |
| Files copied verbatim into output | `assets/` |

If the content is conditional ("only relevant when the user is doing X"), it belongs in `references/`. If the content is procedural ("the agent must always do this"), it belongs in the body.

## See Also

- [topology-decision.md](./topology-decision.md) for the standalone/member/hub choice that determines which structural elements apply
- [taxonomy-templates.md](./taxonomy-templates.md) for reference taxonomy templates by domain type
- [design-principles.md](./design-principles.md) for progressive disclosure patterns and how to structure a multi-domain skill
- [frontmatter-guide.md](./frontmatter-guide.md) for description-writing rules that determine triggering reliability
- [output-patterns.md](./output-patterns.md) for templates and examples patterns
- [workflows.md](./workflows.md) for sequential and conditional process patterns
- [gotchas.md](./gotchas.md) for common skill-creation failure modes
