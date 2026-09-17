---
name: mise-configuration
description: Configure mise tools and nonsecret environment settings, or wrap a task with process-scoped vault resolution. Use for mise configuration; task graphs belong to mise-tasks.
---
# Mise configuration

Read the repository's existing `mise.toml`, local overrides, and applicable
instructions. Use installed `mise --help`, `mise config --help`, and tool/task
help to confirm supported syntax. Avoid printing resolved secret environments.

Keep portable tool versions and nonsecret defaults in tracked configuration.
Keep machine-specific overrides local. Preserve user-defined tasks and settings.
Credential references belong in `.env.op`; wrap secret-consuming commands with
`op run --env-file .env.op -- <command>`. Never write the resolved values to disk.
Use `delonet-dotenv` for DeLoNET vault/service details when applicable.

Use `mise-tasks` only when the request needs task dependencies or a reusable
workflow. Configuration changes do not require inventing task graphs, migrating
unrelated tools, or changing trust settings. Validate with the installed config
parser and the affected task, keeping credential output suppressed.
