---
name: find-skills
description: Discover or import skills when the user explicitly asks to find, install, or extend agent capabilities. Do not intercept ordinary implementation or how-to requests.
---
# Skill discovery

First inspect available skills and the canonical Skillex catalog. Reuse an
existing capability when it fits; do not install a skill merely because a task
has a matching keyword.

For requested upstream discovery, identify the source repository, license,
intended runtime, dependencies, and overlap with current skills. Read the actual
entrypoint before recommending it. A marketplace listing is not validation.

For an accepted installation, use `skillex-skill-registry`: import a pinned
upstream into `all-skills`, select it in a set or scope manifest, preview sync,
then verify client discovery. Inspect the installed CLI's `vendor --help` before
using it; Python and Node releases have different command surfaces.
Do not run `npx skills add -g` against managed activation roots or edit host-owned
`.system` skills. External installers require a distinct, explicitly managed
ownership boundary rather than a second writer to the same path.
