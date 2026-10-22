# Provenance: what was ported, and from where

## Upstream

- **Microsoft's official Power Automate plugin** for Claude Code and GitHub Copilot CLI:
  `power-automate@power-platform-skills`, marketplace `microsoft/power-platform-skills`
  (MIT), directory `plugins/power-automate`. Documented at
  <https://learn.microsoft.com/en-us/power-automate/power-automate-plugin-external-tools>.
- Ported from version **3.2.1**, repository commit
  `c4305aaf7130bb1d805afebc5911f34450ad305d` (2026-10-22).
- It bundles **FlowAgent** (`server/mcp.mjs`, one self-contained ESM file, 62 MCP tools),
  eleven Claude/Copilot skills (setup, browse-flows, create-flow, build-flow, debug-flow,
  diagnose-flow, manage-flows, manage-desktop-flows, route-environments, report-issue,
  telemetry), reference docs, and Microsoft Learn's MCP server
  (`https://learn.microsoft.com/api/mcp`).

Other candidates found and not used: the third-party *Flow Studio Power Automate* plugin (needs
a paid FlowStudio API key and a hosted MCP), and Microsoft's `dataverse` plugin (Dataverse
records and solutions, not flows).

## What this skill does with it

- It does NOT copy the 2.7 MB engine. `pa` finds it in the Claude Code plugin cache, the Copilot
  CLI plugin directory, or its own sparse checkout (`pa engine install`, into
  `~/.agents/.cache/power-platform-skills`), and talks MCP over stdio to it. Any agent with a
  shell gets every tool; any agent with MCP support registers `pa serve`.
- The plugin's skills and references were rewritten as `SKILL.md` and `references/*.md`:
  definition rules, connection patterns, error fixes, auth model. Claude-only parts were left
  out (`allowed-tools` lists, slash commands, `${CLAUDE_PLUGIN_ROOT}`, AskUserQuestion).
- Added beyond upstream: device-code sign-in for passkey accounts (`pa login`, including the
  Connectivity cache seed), the profile file, `pa rest`, `pa export`, `pa batch`, MCP snippets
  for other CLIs, Teams event patterns and the licensing analysis.

## The Claude Code plugin's own hooks and telemetry

Installing the plugin in Claude Code adds two hooks that run in EVERY session: `UserPromptSubmit`
(every prompt) and `PreToolUse` on `Skill` calls. Each spawns `node` to record a `skill_started`
event when the prompt or call is one of the plugin's skills. Remote transmission is ON by
default (pseudonymous: tenant id, Dataverse org id, Entra object id, versions; no prompts or
flow content). Opt out with `/power-automate:telemetry off` (saved in
`~/.power-platform-skills/config.json`) or `POWER_PLATFORM_SKILLS_TELEMETRY_POWER_AUTOMATE_OPTOUT=1`.
`pa` sets that variable and `FLOWAGENT_TELEMETRY=0` for every engine it starts, unless the caller
set them. To drop the hooks entirely, `claude plugin disable power-automate@power-platform-skills`;
`pa` keeps working from the cached engine (or `pa engine install`).

## Updating

```bash
claude plugin marketplace update power-platform-skills   # if the Claude Code plugin is the engine source
pa engine update                                          # if the sparse checkout is
pa engine                                                 # shows which engine and version pa will use
pa tools --json > /tmp/tools.json                          # then refresh references/engine-tools.md
```

After an upstream update, diff the plugin's `references/*.md` and `skills/*/SKILL.md` against
the summary here, and re-run `validate_flow` on `references/patterns/*.json`.
