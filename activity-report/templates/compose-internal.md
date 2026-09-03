Write the internal activity report for {{project_name}} ({{project_slug}}), audience {{audience}}, covering {{window_start}} to {{window_end}}.

Use the `activity-report` skill: invoke it first with the Skill tool and follow it. It is the workflow, not a suggestion. Its composition guide (references/composition.md) has the internal register, the six rules and the raw.txt format.

The digest for this window is already collected at
{{digest}}
Read it. Never run collect again, and never go looking for what the digest already answers: it is the whole window, and what is not in it did not observably happen. `git log`, `git show` and `git diff` are available when a commit subject in the digest needs a closer look.

The previous report was titled: {{previous_title}}

Write exactly ONE file:
{{raw_out}}

Line 1 is `# <title>` (the row title: plain text, at most 180 characters, specific to this window). Everything after line 1 is the body in the portal grammar: `## Heading`, `- bullet`, `| Metric | value |`, `HH:MM text` timeline lines, plain paragraphs, and `**bold**` inline. At most 5000 characters. No other markup: the portal renders anything else literally.

The internal report is dense, chronological and complete. Every ticket that moved, by key and title. Every commit that mattered. What each agent session did, what failed, what is uncommitted, what is unknown. Name the hard thing. Do not pad and do not editorialise.

When the file is written, run the lint and fix every error it reports until it passes:
{{lint_hint}}

Then stop. Do not emit, publish, verify or retain anything; the runner does that after you exit. Do not edit any other file.

You are running unattended. Nobody can answer a question, so make the call and note the assumption in the body under a `## Assumptions` heading.
