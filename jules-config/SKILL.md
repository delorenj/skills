---
name: jules-config
description: Automatically configure any repository for Google Jules cloud VM execution, wrapping 1Password CLI dependencies safely, generating automated environment bootstrap scripts for databases (Postgres/MySQL) and runtimes, and writing the required documentation to AGENTS.md.
---

# Google Jules Project Configuration

Optimize any repository to run successfully and securely inside Google Jules's isolated cloud VM.

## Operating Principles

- **Graceful Fallbacks**: Cloud VM sandboxes lack access to host-specific tools (like 1Password CLI `op` authentication). Always wrap credential-pulling tasks with fallback options (like using `.env.example` or local defaults).
- **Service Port Invariance**: Local Postgres in a VM runs on standard port `5432` instead of host-mapped Docker ports (like `5439`). Ensure database URLs are adjusted for native services.
- **Self-Documenting**: Maintain a `## Jules Setup` section in `AGENTS.md` (or `README.md`) detailing the setup script and VM snapshot configuration.

## Quick Navigation

| Action | Command / File |
|---|---|
| Configure repository for Jules | `python3 /home/delorenj/.gemini/config/skills/jules-config/scripts/jules-init.py` |
| View/Edit Jules VM setup script | `scripts/jules-setup.sh` |
| Documented VM setup process | `AGENTS.md` or `README.md` |

## How to Run

To optimally configure the current repository, execute the following command from the root:

```bash
python3 /home/delorenj/.gemini/config/skills/jules-config/scripts/jules-init.py
```

This utility automatically:
1. Detects language runtime (Bun, Node, Python).
2. Detects database dependencies (PostgreSQL, MySQL).
3. Patches standard `mise.toml` hooks so `op` (1Password) doesn't hang.
4. Generates an executable `scripts/jules-setup.sh` that boots local services, provisions users/DBs, installs packages, runs migrations/seeds, and executes unit tests.
5. Documents the setup in `AGENTS.md` so the Jules agent inherits these VM bootstrap instructions.

## Out of Scope

This skill does NOT cover:
- **Deploying to production hosting**: Use docker compose, Traefik, or cloud hosting deployment scripts.
- **Tiller sheet synchronization credentials**: Jules does not run Google service account credentials; it runs against the mock database seeded by `seed.ts`.
- **Hindsight bank configuration**: Hindsight memory banks are configured via the Hindsight CLI separately.
