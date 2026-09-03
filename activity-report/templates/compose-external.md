Write the client-facing activity update for {{project_name}} ({{project_slug}}), audience {{audience}}, covering {{window_start}} to {{window_end}}.

Use the `activity-report` skill: invoke it first with the Skill tool and follow it. It is the workflow, not a suggestion. Its composition guide (references/composition.md) has the client register, the exemplar, the spin rule and the six rules in order of damage.

Read these before writing anything:

1. The digest, already collected: {{digest}}. Never run collect again. Internal-only tickets are not in this digest on purpose; tickets marked "surface": "always" carry the client-visible label and must be surfaced as momentum.
2. This run's internal report, the complete account of the window: {{internal_raw}}. If that says none, the internal pass did not run; work from the digest alone.

The previous update was titled: {{previous_title}}

Write exactly ONE file:
{{raw_out}}

Line 1 is `# <title>` (the row title: plain text, at most 180 characters, specific to this window). Everything after line 1 is the body in the portal grammar: `## Heading`, `- bullet`, `| Metric | value |`, `HH:MM text` timeline lines, plain paragraphs, and `**bold**` inline. At most 5000 characters. No other markup: the portal renders anything else literally.

The client reads this. 120 to 250 words. Lead with the outcome the client can see or feel. Name the hard thing honestly. Convert internal vocabulary into what the reader experiences. Never claim anything the digest and the internal report do not show. The lint refuses a ticket key, a commit sha, an agent name, a tool-call count, burndown language, a sprint number, the word "refactor", and the title of any internal-only ticket, verbatim or paraphrased. A quiet window gets a short, honest quiet update; never invent significance to fill it. End with what you need from the client, or with nothing.

When the file is written, run the lint and fix every error it reports until it passes:
{{lint_hint}}

Then stop. Do not emit, publish, verify or retain anything; the runner does that after you exit. Do not edit any other file.

You are running unattended. Nobody can answer a question, so make the call. Assumptions never go in the client body; the internal report already carries them.
