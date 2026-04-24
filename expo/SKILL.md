---
name: expo
description: Master skill hub for Expo and EAS. Use when building, shipping, or upgrading Expo apps — including API routes, CI/CD workflows, deployment (App Store, Play Store, EAS Hosting), dev clients, IDE integration (Android Studio, VS Code), native modules (Swift/Kotlin Expo Modules API), Tailwind/NativeWind setup, or Expo SDK upgrades. Routes to domain-specific references via progressive discovery.
version: 1.0.0
license: MIT
pipeline-status:
  - new
---

# Expo

> **Progressive discovery.** This file is a router. Read only the reference(s) relevant to the current task. Do not load everything upfront.

## Routing

Match the task to a reference. Each reference is self-contained.

| Task                                                    | Reference                                   |
| ------------------------------------------------------- | ------------------------------------------- |
| Build server endpoints with `+api.ts`                   | `references/api-routes.md`                  |
| Write or edit `.eas/workflows/*.yml`                    | `references/cicd-workflows.md`              |
| Ship to iOS/Android stores or EAS Hosting               | `references/deployment.md`                  |
| Build a custom Expo Go dev client                       | `references/dev-client.md`                  |
| Integrate the project with Android Studio or VS Code    | `references/ide-integration.md`             |
| Write a native module (Swift/Kotlin) or config plugin   | `references/module.md`                      |
| Set up Tailwind v4 / NativeWind v5 / react-native-css   | `references/tailwind-setup.md`              |
| Upgrade Expo SDK, migrate deprecated packages           | `references/upgrading.md`                   |

If the task spans multiple domains (e.g. "ship an API route to production"), read each reference in turn rather than trying to recall across them.

## Quick Decision Flow

```
Starting something new?
    ├── New app / feature / module? ───→ module.md (if native) | api-routes.md (if server)
    ├── Setting up styling? ────────────→ tailwind-setup.md
    └── Need IDE configured? ───────────→ ide-integration.md

Testing on device?
    └── Need custom native code? ───────→ dev-client.md

Shipping?
    ├── Automating the pipeline? ──────→ cicd-workflows.md
    └── Submitting to a store/host? ───→ deployment.md

Maintaining?
    └── SDK bump or package swap? ─────→ upgrading.md
```

## Scripts

The `cicd-workflows` reference uses Node helpers in `scripts/` for schema fetch and YAML validation. Paths are relative to this SKILL.md:

```bash
# Fetch a resource (ETag-cached)
node {baseDir}/scripts/fetch.js <url>

# Validate one or more workflow files against the live schema
[ -d "{baseDir}/scripts/node_modules" ] || npm install --prefix {baseDir}/scripts
node {baseDir}/scripts/validate.js <workflow.yml> [workflow2.yml ...]
```

`{baseDir}` resolves to the `expo/` skill root.

## Nested References

Some references have their own supporting files. The overview always lists them:

- `references/deployment.md` → `references/deployment/{app-store-metadata,ios-app-store,play-store,testflight,workflows}.md`
- `references/module.md` → `references/module/{native-module,native-view,lifecycle,config-plugin,module-config}.md`
- `references/upgrading.md` → `references/upgrading/{new-architecture,react-19,react-compiler,native-tabs,expo-av-to-audio,expo-av-to-video}.md`

## Rules for Agents Using This Skill

1. Read the router, pick one reference, read it, act.
2. Do not prefetch nested references until the overview tells you to.
3. Never assume API shape from memory — if the reference cites a schema or official doc, fetch it.
4. For API routes and deployment secrets: never commit keys, never return them to the client. See `api-routes.md` for the enforcement pattern.
