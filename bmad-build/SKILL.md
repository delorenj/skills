---
name: bmad-build
description: 'Turns implementation work into working code, reviewed and verified in BMAD-enabled projects. Automatically select only when the project has _bmad/scripts/render_skill.py and the user delegates a feature, story, bug fix, or meaningful change; a bare story or issue link counts. In non-BMAD projects, use the repo-native workflow instead. Explicit BMAD requests activate the prerequisite check, not automatic installation. Skip obvious, low-risk mechanical maintenance, user-directed interactive edits, and version-control operations that only record existing work.'
---

## Applicability check — before running BMAD

Resolve `{project-root}` to the repository being worked on, not the directory containing this globally installed skill. Check the renderer without changing the current working directory:

```bash
test -f "{project-root}/_bmad/scripts/render_skill.py"
```

- If absent on an ordinary implementation request, this skill is **not applicable**. Return to the caller and continue the already-authorized task with the repo-native workflow (for Foundry game content, `ltf-make-game`). Do not run the renderer, report a failed build, or halt the user's task merely because this unrelated skill was selected.
- If absent on an explicit BMAD request (including `/bmad-build`), report the exact missing prerequisite and stop this skill. Do not silently substitute another workflow.
- In either case, do not install BMAD, create `_bmad/`, copy a renderer from another repo, or change global skill selection unless the user separately requests setup.
- Only when the renderer exists, proceed below. A renderer that exists but fails is a real BMAD failure; retain the failure handling below rather than bypassing it.

## Run in a BMAD-enabled project

Run the following command exactly once without changing the current working directory. Replace `{project-root}` with the absolute path to the project root and `{skill-root}` with the absolute path to this skill's directory:

```bash
uv run --no-cache "{project-root}/_bmad/scripts/render_skill.py" --project-root "{project-root}" --skill "{skill-root}"
```

- On success, read and follow the one absolute `workflow.md` instruction printed to stdout.
- On failure (including `uv` being unavailable), report the command output and HALT. Do not run any workflow source directly.
