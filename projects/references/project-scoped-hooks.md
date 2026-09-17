# Project-scoped hooks and skills

Read the current CommonProject template before adopting or repairing generated
project setup. `.agents/` owns project declarations. Agent hook dialect files
are generated views; edit their master and preserve unrelated client settings.
Use agent-config-fanout for master mappings, native hook adapters, drift checks,
and idempotent generation.

For skills, edit `<repo>/.agents/skills.json` and the selected reference-only
compositions. Skillex reconciles one project `.agents/skills` root; CLI skill
roots alias it. Follow skillex-skill-registry for preview, apply, source and
consumer checks. Do not copy SKILL.md payloads into packs or CLI roots, and do
not resurrect the obsolete provision-packs-then-sync-skills sequence.

Project inheritance composes global and project selections without copying
bytes. Verify the compiled target map using the installed CLI; preserve
installer-owned and foreign content until its ownership is resolved.

For credentials in enter/run hooks, use process injection through delonet-dotenv.
Never render resolved credentials into `.env`. Validate the actual enter/leave
and native hook path when changing hooks; a generated file alone is not proof.
