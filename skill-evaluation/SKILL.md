---
name: skill-evaluation
description: Design and run comparative evaluations of agent skills when explicitly requested. Use for test prompts, baseline comparisons, grading, and iterative skill experiments; ordinary skill authoring uses the host skill-creator.
---
# Skill evaluation

Use the host's `skill-creator` for ordinary authoring. This skill provides the
optional evaluation harness imported from the Anthropic workflow.

1. Agree on the behavior being tested and representative positive/negative prompts.
2. Inspect available runtime tools and choose a bounded baseline and candidate run.
3. Use scripts from this skill directory only after inspecting their arguments.
   Spawn evaluation agents only when delegation is authorized.
4. Compare observed outputs against task-specific criteria; separate static review
   from model execution and avoid claiming statistical confidence from tiny samples.
5. Preserve prompts, relevant results, and limitations. Stop when the requested
   experiment is complete; an evaluation does not authorize installing its winner.

Read [evaluation methods](references/evaluation-workflow.md) for the harness,
grading, and optional iteration details.
