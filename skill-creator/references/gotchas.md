# Skill Creation Gotchas

Catalog of common skill-creation failure modes with the cause, the fix, and a bad/good code pair where applicable. Each entry is structured for fast pattern matching against live symptoms.

## Reading Order

| Symptom | Read |
|---------|------|
| Skill is not triggering when it should | [Skill does not trigger](#skill-does-not-trigger) |
| Skill triggers for wrong tasks | [Skill triggers for wrong domains](#skill-triggers-for-wrong-domains) |
| Reference files are never loaded | [Agent ignores reference files](#agent-ignores-reference-files) |
| SKILL.md is over 500 lines and growing | [SKILL.md grows past 500 lines](#skillmd-grows-past-500-lines) |
| Validation fails with frontmatter errors | [Non-standard frontmatter fields break compatibility](#non-standard-frontmatter-fields-break-compatibility) |
| Scripts produce errors at runtime | [Script tested by reading not by running](#script-tested-by-reading-not-by-running) |
| Skill explains itself instead of executing | [SKILL.md is documentation about the skill](#skillmd-is-documentation-about-the-skill) |
| References point to other references in chains | [Deeply nested references](#deeply-nested-references) |

## Common Errors

### "Skill does not trigger"

**Cause:** Description is too abstract; no concrete artifact names, file types, library names, or action verbs.

**Solution:** Pack the description with concrete trigger keywords. Include every artifact name (`SKILL.md`, `init_skill.py`, `.skill`), every action verb (create, update, package, scaffold), and every domain term a user might say.

```yaml
# ❌ BAD: vague description that does not trigger reliably
---
name: skill-creator
description: Guide for creating effective skills.
---
```

```yaml
# ✅ GOOD: keyword-dense description with explicit signals
---
name: skill-creator
description: Create, structure, improve, and package skills for agentic CLI tools. Use when creating a new SKILL.md, updating an existing skill's frontmatter or body, designing a references/ directory, adding scripts/ or assets/ bundled resources, running init_skill.py to scaffold, running package_skill.py to build a .skill file, or applying progressive disclosure to a skill.
---
```

See [frontmatter-guide.md](./frontmatter-guide.md) for the full description specification.

### "Agent ignores reference files"

**Cause:** Reference files are mentioned in SKILL.md without explicit conditions for when to load them. The agent does not know they exist as actionable resources.

**Solution:** Replace passive mentions with conditional loading instructions tied to specific tasks.

```markdown
❌ BAD:
This skill has additional reference material in references/.

❌ STILL BAD:
See references/output-patterns.md for more details.

✅ GOOD:
**For producing structured output (reports, commit messages, formatted documents):** load references/output-patterns.md.
**For multi-step procedures with branching logic:** load references/workflows.md.
**For debugging skill quality issues:** load references/gotchas.md.
```

A reading order table in SKILL.md is even stronger because it transforms the conditional from prose into a lookup.

### "SKILL.md grows past 500 lines"

**Cause:** Anatomy reference, design principles, procedural steps, and examples all live in the body. The body becomes a textbook rather than an instruction set.

**Solution:** Extract permanent reference material to `references/`. Keep only procedural steps, routing tables, and decision trees in the body. Target <200 lines for SKILL.md body.

Material that almost always belongs in references:
- Detailed schema documentation
- Anti-pattern catalogs
- Multi-paragraph design rationale
- Variant-specific patterns (AWS vs GCP, framework A vs B)
- Long worked examples

Material that almost always belongs in the body:
- The decision tree at the top
- The reading order table or quick navigation
- The numbered process steps
- Cross-cutting rules
- Out-of-scope declarations

### "Skill triggers for wrong domains"

**Cause:** No out-of-scope declaration. The agent expands the skill's perceived domain to fill uncertainty.

**Solution:** Add an explicit "Out of Scope" section at the bottom of SKILL.md (or a "when to skip" clause in the description) that names what the skill does NOT cover and where to go instead.

```markdown
## Out of Scope

This skill covers SKILL.md packages for agentic CLI tools (Claude Code, Codex, OpenCode). It does NOT cover:
- MCP tool definitions or the Claude API tool_use format (load mcp-builder skill)
- Raw system prompt engineering (load prompt-engineering skill)
- Anthropic plugin manifest format (load plugin-builder skill)
```

The redirect to the alternative skill is essential. Without it, the agent has no path forward when this skill is wrong.

### "Non-standard frontmatter fields break compatibility"

**Cause:** Fields like `license`, `pipeline-status`, `version`, `author`, or `tags` added beyond `name` and `description`. Some harnesses ignore them; others fail validation.

**Solution:** Only `name` and `description` are guaranteed to be read by every harness. Specific harnesses may support extensions like `references`, but assume nothing else.

```yaml
# ❌ BAD: non-standard fields
---
name: skill-creator
description: ...
license: Complete terms in LICENSE.txt
pipeline-status:
  - new
version: 1.0.0
---
```

```yaml
# ✅ GOOD: only the guaranteed-portable fields
---
name: skill-creator
description: ...
---
```

License text belongs in a `LICENSE` or `LICENSE.txt` file at the skill root. Versioning happens at the distribution layer (the `.skill` file or git tag), not in frontmatter.

### "Script tested by reading not by running"

**Cause:** Step 4 of the creation process says to test scripts. The agent reads the script and infers correctness rather than executing it.

**Solution:** Always execute scripts. Compare actual output against expected. Reading code does not surface runtime errors, missing dependencies, environment-specific failures, or incorrect arguments.

```bash
# ❌ BAD: reading the script and trusting it
cat scripts/init_skill.py | head -50
# (agent decides it looks correct without running it)

# ✅ GOOD: actually running the script with test input
python scripts/init_skill.py test-skill --path /tmp/test-output
ls -la /tmp/test-output/test-skill/
# (agent confirms the output structure matches expectations)
```

This applies to packaging too: run `scripts/package_skill.py` against the in-progress skill before declaring the skill ready.

### "SKILL.md is documentation about the skill"

**Cause:** Author writes about the skill ("This skill is for...", "How this skill works...") instead of writing instructions FOR the agent.

**Solution:** Rewrite in imperative form. Every paragraph should be an instruction or a fact the agent acts on, not a description of the skill.

```markdown
❌ BAD: third-person documentation
## About This Skill
This skill helps Claude understand how to create skills. It includes references for various patterns.

✅ GOOD: imperative instructions for the agent
## Operating Principles
Before advising on frontmatter, verify the harness supported fields.
Before advising on script APIs, run the scripts and check output.
Prefer concrete tested examples over abstract descriptions.
```

The body is loaded into context to act on, not to read about. Cut every meta-statement.

### "Deeply nested references"

**Cause:** Reference files link to other reference files that link to yet more reference files. The agent has to traverse multiple hops to reach the relevant content.

**Solution:** Flatten. All references load directly from SKILL.md or from the first reference loaded. The agent should never need three hops.

```
❌ BAD:
SKILL.md → references/overview.md → references/api/index.md → references/api/methods/get.md

✅ GOOD:
SKILL.md → references/api.md (with reading order table to relevant sections)
```

If a reference file is so long it requires sub-files, restructure: split it into multiple peer references at the same level (`api-read.md`, `api-write.md`, `api-list.md`) rather than nesting.

### "Reading order tables are missing or wrong"

**Cause:** Reference directories that contain multiple files have no entry-point guidance. The agent reads files in alphabetical order or guesses.

**Solution:** Add a reading order table at the top of either the longest reference or a dedicated `README.md` (if the references directory has one). Map task types to file sequences.

```markdown
| Task | Files to Read |
|------|---------------|
| Quick start | overview.md → configuration.md |
| Implement feature | api.md → patterns.md |
| Debug issues | gotchas.md → api.md |
```

### "Examples are abstract or use placeholder names"

**Cause:** Examples like `function foo() { ... }` or "consider a generic API skill" provide no concrete grounding.

**Solution:** Use real, complete, runnable examples with realistic names. The cost of writing a real example once is paid back every time the agent uses the skill.

```markdown
❌ BAD: abstract example
"For example, when building a skill for X, include scripts that..."

✅ GOOD: concrete worked example
"When building a pdf-editor skill for queries like 'rotate this PDF':
1. Identify that PDF rotation requires re-writing the same code each time
2. Add scripts/rotate_pdf.py to the skill
3. Test with: python scripts/rotate_pdf.py input.pdf 90 output.pdf
4. Include a one-line usage hint in SKILL.md body"
```

## Performance Tips

| Scenario | Recommendation | Why |
|----------|----------------|-----|
| Description over 200 words | Compress without losing keywords | Metadata is in context for every prompt; bloat is paid repeatedly |
| Body over 200 lines | Extract reference content | Body loads on every trigger; references load only when needed |
| Many similar references | Consolidate into a single file with sections | Fewer hops, better grep targeting |
| Reference files over 1000 lines | Add reading order table at top | Prevents whole-file loading for narrow tasks |
| Scripts under 50 lines used once | Inline the logic into the body or a one-time prompt | Script overhead exceeds the benefit |

## Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Description target | 50-200 words | Too short hurts triggering; too long bloats metadata |
| SKILL.md body target | <200 lines | Hard cap at 500; excessive bodies indicate missing references |
| Reference file recommendation | 100-1000 lines | Below 100 may not justify a separate file; above 1000 needs splitting or a reading order table |
| Reference nesting depth | 1 level | All references load from SKILL.md or from the first reference |
| Frontmatter fields | 2 (name, description) | Plus optional `references` for hubs |

## See Also

- [frontmatter-guide.md](./frontmatter-guide.md) for description-writing rules
- [design-principles.md](./design-principles.md) for progressive disclosure patterns
- [anatomy.md](./anatomy.md) for what content belongs where
- [topology-decision.md](./topology-decision.md) for topology-specific gotchas (premature hub, missing scope contract)
- [routing-mechanics.md](./routing-mechanics.md) for the canonical Four-Part Gotcha Structure used in hub gotchas catalogs
- [migration.md](./migration.md) for failure modes specific to migration between topologies
- [taxonomy-templates.md](./taxonomy-templates.md) for taxonomy-mismatch gotchas
- [output-patterns.md](./output-patterns.md) for output format gotchas
- [workflows.md](./workflows.md) for procedural design gotchas
