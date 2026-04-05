---
pipeline-status:
  - new
---
# 33GOD Reference Index

Use this file to choose exactly where to go next.

## Decision Tree

Are you...

- Creating/cloning/bootstrap a project? → `project-creation.md`
- About to execute a new task? → `task-execution.md`
- Writing, refactorying, or deploying code? → `coding-workflow.md`
- Building or registering a new service? → `service-development.md`
- Creating or encapsulating a new workflow? → `workflow-generation.md`
- Are you adding/changing/pruning event/command contracts? → `event-command-lifecycle.md`
- Planning platform-wide coordination/status/delegation? → `platform-lifecycle.md`
- **Deploying/configuring infrastructure or external access? → `infrastructure-deployment.md`**
- Performing repo maintenance? → `repo-maintenance.md`
- Checking for documentation drift or updating documentation? → `god-doc-policy.md`

## Core locations

- Monorepo root: `~/code/33GOD/`
- System GOD doc: `~/code/33GOD/docs/GOD.md`
- Domain GOD docs: `~/code/33GOD/docs/domains/{domain}/GOD.md`
- Component GOD docs: `~/code/33GOD/{component}/GOD.md`
- Compose source of truth: `~/code/33GOD/compose.yml`
- Infrastructure/Tunnel: `~/docker/stacks/cloudflare-tunnel/`

## Routing rule

Do not read all references by default. Load only the section required by the active task.
