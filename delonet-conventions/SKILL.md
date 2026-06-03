---
name: delonet-conventions
description: This skill defines system conventions such as file naming and paths, shell configuration, container hosting and other custom systems. Use this skill when working on a task that requires interacting with or configuring the filesystem, containers, or services in the DeLoNET home environment.
pipeline-status:
  - new
---

# Standards And Conventions for DeLoNET Linux Workstations

> Important: Strict adherence to PROGRESSIVE DISCOVERY strategy. Once you have the info you require to complete your task, stop reading IMMEDIATELY and proceed to the next step.

## Skill Directory

> TODO:
> This will be a directory of references in the form of a decision tree.

## How the User's Home is Organized

The top-level directory structure of the user's home directory is split into several notable sections:

1. `docker/`
2. `code/`
3. ``

## Scripting, Shell Config, and Secrets

This top-level domain is managed by my `ZSH Custom` repository `delorenj/zshyzsh`. This is how I keep parity between my various machines.

- To share configuration of an app, I simply move `~/.config/app` to `$ZSH_CUSTOM` (aka `zshyzsh`, `$ZC`) and symlink it back to `~/.config/app`.
- Aliases are combined into `$ZC/aliases.zsh` and loaded automatically.
- Secrets are stored in `$ZC/secrets.zsh` and loaded automatically.
- Shell completions are stored in `$ZC/completions/app.zsh` and loaded automatically.
- Scripts are stored in `$ZC/scripts/some_script.zsh` and are linked to `~/.local/bin/some_script`.
- Shortcut commands too complex for aliases are implemented as zsh functions or sometimes python and grouped by topic in `$ZC/`
  - i.e. `$ZC/docker-commands.zsh`, `$ZC/github.zsh`

> TODO:
> I am progressively migrating my secrets from the questionable unencrypted flat file to my 1pass CLI vault, [DeLoSecrets](ogoabqae7c6xgdbl5wccfwcnke)

## Docker Containers and Compose Stacks

## Obsidian Vault and Knowledge Base Artifact Organization

## Code Repository Organization

## Tooling and Package Management

Mise is my tooling and package versioning utility of choice.

- EVERYTHING that CAN be managed with Mise should be managed with Mise.
  - This is not yet the case.
  - If you find one, migrate it to Mise and remove the old tooling.

> [!IMPORTANT] **Critical Pattern:**
> Every repo in `$CODE` (ideally) has a matching folder in `$VAULT/Projects/` for non-tracked brainstorming and iteration documents.
> There is a `helper.zsh` script function `syncDocs` that ensures this relationship is maintained.

> [!IMPORTANT] **Critical Convention**
> `exported` paths are ALWAYS in caps.
> `aliases` and `functions` are ALWAYS lowercase.

- For every exported path, there should be an alias to navigate to it quickly.
  - `alias zv='cd $ZV'` to go to the vault.

**Critical Pattern:** I write code in the terminal, but I like to view my docs in Obsidian. To accomplish this, I came up with a hack; every repo in `$CODE` has a corresponding folder of the same name in `$VAULT/Projects/`.

> Note: This is still an unsolved problem. While this hack technicall works, it's not without its drawbacks.

- There's no single source of truth since the docs are duplicated.
- I tried symlinking but it causes too many issues with rendering in Obsidian and conflicts.

## Muxers, Terminal Emulators, Editors and IDE's

- [Lazyvim](https://www.lazyvim.org/) for all my editing needs.
- [Alacritty](https://github.com/alacritty/alacritty) as my primary terminal emulator.
- [Zellij](https://zellij.dev) as my terminal multiplexer.
- [Zed](https://zed.dev) is my primary IDE but I rarely use it.

## Tips, Non-negotiables, Pet Peeves, and General Advice

- NEVER put documents randomly in the root of a repo - use the vault for that
- After each large task, prune and refactor docs to keep them minimal and useful.

> [!IMPORTANT] **Document Pruning Rule:**
> Rule of thumb: If you created 10 docs in a session, delete 9 of them and keep only the best one.

## Network Architecture

- **Cloudflare Tunnel** for external access (no public IP needed)
- **[Traefik](~/docker/core/traefik)** as reverse proxy for service routing and SSL
- **Proxy network** (`proxy`) for inter-service communication
- **Direct container routing** for simple services, **Traefik routing** for complex multi-domain apps

See `references/docker_patterns.md` for Cloudflare Tunnel + Traefik setup.

**Communication Style:**

- Direct, concise, technical authority
- No em dashes
- Medium-depth explanations (~200 words)
- Speak as peer and best friend that's hanging out having some beer and coding together!
- Don't be serious all the time - absurd humor is welcome!
