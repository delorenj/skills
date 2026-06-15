# Provider Rotation Notes

A rotation strategy is only as good as the quota facts provided.

## Inputs

Each provider entry needs:

- provider name
- model or route
- requests per minute (`rpm`)
- daily request limit (`daily_requests`)
- token-per-minute limit (`tpm`) when available
- whether the provider is free, paid, tiered, or overflow
- source URL and last-verified date, maintained by the team

## Calculation

For each provider:

```text
min_interval_seconds = 60 / rpm
allocation_daily_requests = min(remaining_daily_need, daily_requests)
```

For continuous use, the effective need is:

```text
effective_daily_need = max(desired_daily_requests, desired_rpm * 60 * 24)
```

If desired RPM or daily need exceeds known capacity, lower concurrency first. Only then add a paid overflow route.

## Recommended default

- Claude/Codex premium for decisions and final synthesis.
- OpenRouter free/funded `:free` models for cheap scouts where latency/reliability is acceptable.
- Gemini free only after reading active project quotas from AI Studio.
- Kimi direct only after confirming current Moonshot tier limits.
- Hermes/OpenRouter paid overflow for high-reliability continuous runs.

## Hard rule

Do not create throwaway accounts or rotate identities to bypass provider limits. That is not optimization; that is ToS Jenga with a blindfold.
