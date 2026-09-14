---
name: shell-secret-sourcing
description: Diagnose and standardize secrets that are sourced indirectly through shell startup files, shell functions, or repo-local env files rather than a dedicated credential manager API. Use when the wrong API key keeps reappearing, env vars seem haunted, a helper like `opg` works in an interactive shell but fails in automation, or you need to replace hardcoded secrets with dynamic lookup.
pipeline-status:
  - new
---

# Shell Secret Sourcing

Use this when a credential appears to come from "somewhere in the shell" instead of the app config itself.

## Trigger signals

- The user says they do not know where an API key is coming from.
- App/provider config looks correct, but requests still use the wrong credential.
- A repo-local `.env` or shell startup file may be overriding runtime config.
- A helper command works interactively but fails from Python subprocesses, non-login shells, or service contexts.

## Core rule

Trace the credential source before changing app config again.

Wrong-key incidents are often caused by env injection from startup files (`~/.spawnrc`, `.bashrc`, `.zshrc`, `.profile`) or repo-local `.env` files, not by the application's provider/model settings.

## Diagnostic sequence

1. Check whether the relevant env var is already present in the current shell.
2. Search likely injection points first:
   - `~/.spawnrc`
   - shell startup files
   - repo-local `.env` files
3. Distinguish binaries from shell functions.
   - If `command -v foo` fails but interactive shells can run `foo`, check whether it is a shell function or alias.
4. If the helper is a shell function, source the defining file explicitly in the correct shell before using it in automation.
5. Replace hardcoded secret exports with dynamic lookup.
6. Verify in a clean shell, then verify with a trivial application request.

## Durable pattern: shell function backed secret lookup

If the secret helper is a zsh function rather than a binary, use a form like:

```bash
zsh -fc 'source ~/.config/zshyzsh/helpers.zsh; opg openrouter hermes'
```

Why:
- `opg` is not guaranteed to exist on `PATH` as an executable.
- Python `subprocess.run(["opg", ...])` and non-zsh shells can fail even when the interactive shell works.
- Explicitly sourcing the helper file makes the function available in non-interactive automation contexts.

## Preferred remediation

Instead of storing a raw secret in shell startup files or `.env`, export it from command substitution using the helper lookup. This keeps the source of truth in the credential manager while preserving compatibility with tools that still expect an env var.

## Verification

You are done only when both are true:
- a clean shell resolves the env var from the intended dynamic source
- the target application succeeds with a minimal request using that env source

## Pitfalls

- Do not assume the current app config is the source of the key.
- Do not assume a helper name is a binary just because it works in an interactive shell.
- Do not print or copy the secret into notes, skills, or chat output.
- If a service is already running, remember that fixing the shell/env source does not update the live process until restart/reload.
