## Common failures and responses

### Alias list has extra or missing models

- Report OpenCode config drift.
- Do not continue with unapproved providers or direct model IDs.
- Ask whether to repair config or proceed with an explicit exception.

### OpenRouter auth fails

- Ask the user to refresh OpenRouter auth/key.
- Provide any login/auth URL verbatim.
- Do not switch to OpenAI, Anthropic, Kimi, Copilot, or other providers.

### Free model throttles

- Tell the user `openrouter/free-lunch` is throttled.
- Use `openrouter/3-buck-chuck` only after acknowledging the paid fallback.

### Plan is unclear or contradictory

- Ask OpenCode to rewrite the plan.
- Do not switch to Build mode until the plan is coherent.
