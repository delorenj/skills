---
name: opencode-controller
description: Control and operate OpenCode for coding work using the local OpenRouter-only preset setup. Use this skill to manage OpenCode sessions, select one of the approved model aliases (openrouter/fusion, openrouter/3-buck-chuck, openrouter/free-lunch), switch Plan/Build agents, and coordinate implementation through OpenCode.
---

# OpenCode Controller

## Local contract

- Assume OpenCode is configured for OpenRouter only.
- Do not ask which provider to use unless verification shows config drift.
- Use only these model aliases:
  - `openrouter/fusion`: default for planning, orchestration, technical judgment, and complex implementation.
  - `openrouter/3-buck-chuck`: budget default for focused build, QA, and routine implementation.
  - `openrouter/free-lunch`: free/low-risk option for smoke checks, simple tasks, or explicit user requests.
- If another model/provider is requested, confirm the exception before using it.

## Pre-flight

1. Confirm the working directory and user goal.
2. Choose a model alias:
   - Use `openrouter/fusion` when unsure.
   - Use `openrouter/3-buck-chuck` for cost-sensitive direct work.
   - Use `openrouter/free-lunch` only when quality/rate-limit risk is acceptable.
3. If model availability is uncertain, run:
   `opencode models openrouter --pure`
   Expected output is exactly:
   `openrouter/3-buck-chuck`, `openrouter/free-lunch`, `openrouter/fusion`.
4. If OpenRouter auth fails, ask the user to refresh OpenRouter auth/key. Do not switch providers.

## Core rule

When using this skill, operate OpenCode as the implementation surface. Do not silently bypass it and edit files directly unless the user explicitly pivots away from OpenCode.

## Session management

- Start OpenCode in the target project:
  `opencode`
- Open the session selector:
  `/sessions`
- Reuse the existing project session when present.
- Create a new session only when the user asks or no project session exists.

## Model selection

- Open the model selector:
  `/models`
- Select the chosen alias:
  - `openrouter/fusion`
  - `openrouter/3-buck-chuck`
  - `openrouter/free-lunch`
- Do not select raw model IDs such as direct DeepSeek, Kimi, OpenAI, Anthropic, or Copilot routes.

## Agent control

- Open the agent selector:
  `/agents`
- Start in Plan for non-trivial work.
- Switch to Build only after the plan is clear and accepted.
- Use Build directly only for tiny, well-scoped tasks where planning overhead is unnecessary.

## Plan behavior

- Ask OpenCode to analyze the task and propose a step-by-step plan.
- Let OpenCode ask clarification questions.
- Review the plan before Build.
- If the plan is vague, risky, or contradicts repo evidence, ask OpenCode to revise it.
- Do not allow code generation while still in Plan.

## Build behavior

- Switch to Build after plan acceptance.
- Ask OpenCode to implement the approved plan.
- If OpenCode asks a question during Build, switch back to Plan, answer there, and confirm/revise the plan before returning to Build.

## Completion

- Continue Plan -> Build -> verification until the requested outcome is complete.
- Verify with targeted commands, tests, logs, or visible runtime evidence.
- Report the selected model alias, session handling, files changed, and verification evidence.

## Failure handling

- If the three aliases are not the only OpenRouter models visible, report config drift before continuing.
- If an alias is unavailable, stop and report which alias failed.
- If auth fails, ask for OpenRouter auth repair. Do not fall back to another provider.
- If free models throttle, switch to `openrouter/3-buck-chuck` only after telling the user.

## Output format

- Show slash commands explicitly when driving the TUI.
- State the selected model alias.
- State whether an existing session was reused or a new one was created.
- Provide login/auth URLs verbatim if OpenCode emits them.
