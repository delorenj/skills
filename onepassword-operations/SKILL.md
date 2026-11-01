---
name: onepassword-operations
description: Use when bootstrapping or operating 1Password CLI, Connect, and local Redis read caching on a personal Mac. Guides owner-authorized agent execution and secret-safe verification.
---

# 1Password operations

This is a **procedure for the machine owner's local agent**, not an agent persona, a remote-access grant, or a preinstalled implementation. The agent executes checkpoints, makes owner-authorized changes, and records observed results; never mark an unperformed step complete. Do not request credentials in chat, copy another person's identity or vault data, or paste resolved values into a log.

| Need | Read |
| --- | --- |
| First setup, existing-install reconciliation, account sign-in, Connect provisioning/deployment, portable cache adapter, acceptance tests | [Bootstrap agent workflow](references/bootstrap.md) |
| Application configuration and `.env`/`.env.op` reference split | [Runtime](references/runtime.md); [examples](templates/env.op.example) and [nonsecret example](templates/env.example) |
| Daily cache/Connect operations, rotation, outage and security handling | [Operations](references/operations.md) |
| Check required environment *names* inside `op run` without exposing values | `python3 scripts/check-env.py NAME [NAME ...]` ([script](scripts/check-env.py)) |

The checker only observes a process environment. It does **not** authenticate, resolve references, prove vault permissions, or install software. On the Studio, the previous observation was native `op` 2.41.1, 1Password.app installed but `op account list` empty, and a healthy dedicated Docker Redis at `~/infra/onepassword/compose.cache.json`; **all observations must be rechecked locally**. Connect and owner authentication were not provisioned by this skill. No installer/activation is bundled; do not run Linux scripts unmodified on macOS.
