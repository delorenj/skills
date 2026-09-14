---
name: telegram-reset-caf
description: Reset CoachingAgentFramework Telegram/onboarding dogfood state safely. Use when a CAF test client is stuck mid-interview, Telegram is replying from stale state, onboarding needs to be replayed, the poll bridge/API may be stale, or Damian asks to reset Telegram while preserving bot/group binding.
---

# Telegram Reset for CAF

Use this skill for local dogfood resets of Telegram onboarding and protocol test state.

## Default Intent

Reset the client so they can retest onboarding in Telegram without losing the bot token or group binding.

By default:

- Preserve Telegram user/group binding.
- Clear stale workflow sessions for onboarding.
- Clear legacy `seed_config` onboarding state.
- Clear program readiness state.
- Clear collected onboarding profile facts and objectives.
- Reset client lifecycle/stage to `onboarding`.
- Keep Telegram conversation history for observability unless explicitly asked to clear it.

## Required Safety Checks

Before resetting:

1. Confirm the repo root is `CoachingAgentFramework`.
2. Inspect running containers with `docker compose ps api telegram-poll-bridge`.
3. Prefer a targeted reset by `--client-id` or `--email`; never reset all clients.
4. Do not clear Telegram binding unless the user explicitly asks for re-binding.

## Main Command

From the repo root:

```bash
python3 skills/telegram-reset-caf/scripts/reset_telegram_state.py --email dami.miller@gmail.com --verify
```

If the Telegram bridge or API is stale, add:

```bash
python3 skills/telegram-reset-caf/scripts/reset_telegram_state.py --email dami.miller@gmail.com --restart-stack --verify
```

If the user explicitly wants to re-bind Telegram from scratch:

```bash
python3 skills/telegram-reset-caf/scripts/reset_telegram_state.py --email dami.miller@gmail.com --clear-binding --verify
```

## Lessons Learned

- The dashboard can be fresh while the API container is old. A 404 from a new dashboard button can mean the API image needs rebuilding.
- The API can be fresh while `telegram-poll-bridge` is old. If Telegram behavior feels stale, rebuild/restart the bridge too.
- CAF currently has more than one onboarding state layer:
  - legacy `seed_config.kind = telegram_onboarding_interview`
  - generic `workflow_sessions.workflow_id = damian-method.onboarding`
  - readiness `seed_config.kind = client_program_readiness`
- Clearing only one layer can leave the client stuck mid-interview.
- The built-in dashboard reset can clear Telegram binding. For retesting the interview in the same group, use the targeted reset script instead.

## Verification

After reset, verify:

- API is healthy.
- Telegram bridge is running.
- The client has no active onboarding workflow sessions.
- Profile fact count and objective count are zero, unless the user requested otherwise.
- Telegram binding is still present when preserving binding.

Then tell the user to send `hello` in the bound Telegram group. The expected behavior is a fresh onboarding welcome and the first baseline frequency question.
