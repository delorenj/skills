# Mise and project configuration

Use the current CommonProject/PJangler template as the source for generated task
structure. Inspect the installed mise and project commands before changing an
existing repository; do not assume a historical enter-hook layout is current.

- Keep nonsecret environment literals in the project's declared configuration.
- Keep credential references in `.env.op`. Secret-consuming tasks invoke
  `op run --env-file .env.op -- <command>` so values live only in process memory.
- Never resolve credentials to `.env` on directory entry. If an old template does
  that, repair the owning template and migrate the affected project explicitly.
- `AGENTS.md` is the source; CLI agentfiles may alias it. Preserve foreign files
  when refreshing links.
- Select skills in `.agents/skills.json` and use Skillex for activation. Do not
  copy skill definitions or add a competing enter-hook installer.
- Hook configuration and skill activation have different owners. Use
  `agent-config-fanout` for hook dialects and `skillex-skill-registry` for skills.

Use `mise-tasks` for task dependency graphs and `mise-configuration` for tools,
nonsecret environment settings, and process-scoped secret wrappers. Run the
repository's existing validation and inspect the resulting configuration diff.
