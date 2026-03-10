---
name: openclaw-upgrade
description: Upgrade OpenClaw installations to the latest version. Handles global npm installs, local development setups, release channels (stable/beta/dev), configuration preservation, and platform-specific requirements. Use when updating OpenClaw, switching release channels, or troubleshooting update issues.
---

# OpenClaw Upgrade Skill

Complete upgrade management for OpenClaw installations across different environments and platforms.

## Core Upgrade Commands

### Global NPM Installation (Most Common)

#### Stable Release (Latest)
```bash
sudo npm i -g openclaw@latest
```

#### Beta Release
```bash
sudo npm i -g openclaw@beta
```

#### Specific Version
```bash
sudo npm i -g openclaw@2026.2.15
```

#### Dev Channel (Main Branch)
```bash
# Clone and build from source
git clone https://github.com/openclaw/openclaw.git /tmp/openclaw-dev
cd /tmp/openclaw-dev
pnpm install
pnpm build
sudo npm link
```

## Environment-Specific Upgrades

### exe.dev VM Upgrade

```bash
# SSH into the VM
ssh exe.dev
ssh vm-name

# Stop running gateway gracefully
pkill -f openclaw-gateway || true
# If still running after 5 seconds, force kill
sleep 5
pkill -9 -f openclaw-gateway 2>/dev/null || true

# Update OpenClaw
sudo npm i -g openclaw@latest

# Verify installation
openclaw --version

# Restart gateway with proper configuration
nohup openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &

# Verify gateway is running
openclaw channels status --probe
ss -ltnp | rg 18789
tail -n 120 /tmp/openclaw-gateway.log
```

### macOS App Upgrade

```bash
# Stop the app if running
osascript -e 'quit app "OpenClaw"'

# For development builds
cd ~/code/openclaw
git pull --rebase origin main
pnpm install
pnpm build
scripts/package-mac-app.sh

# Install the new app
cp -R dist/mac/OpenClaw.app /Applications/

# Restart
open -a OpenClaw
```

### Local Development Setup

```bash
cd ~/code/openclaw

# IMPORTANT: Commit or save your work before upgrading
# Check for uncommitted changes
git status

# If you have changes, commit them first:
# git add .
# git commit -m "WIP: saving work before upgrade"

# Update to latest
git fetch origin
git checkout main
git pull --rebase origin main

# Update dependencies
pnpm install

# Rebuild
pnpm build

# Run tests
pnpm test

# Return to your branch if needed
# git checkout <your-branch>
```

## Configuration Preservation

### Backup Before Upgrade

```bash
# Backup config
openclaw config export > ~/.openclaw-config-backup-$(date +%Y%m%d).json

# Backup credentials (if web provider)
cp -R ~/.openclaw/credentials ~/.openclaw-credentials-backup-$(date +%Y%m%d)

# Backup sessions (if applicable)
cp -R ~/.openclaw/sessions ~/.openclaw-sessions-backup-$(date +%Y%m%d)
```

### Restore After Upgrade

```bash
# Import config
openclaw config import < ~/.openclaw-config-backup-YYYYMMDD.json

# Restore credentials if needed
cp -R ~/.openclaw-credentials-backup-YYYYMMDD/* ~/.openclaw/credentials/

# Verify configuration
openclaw config list
openclaw channels status
```

## Version Management

### Check Current Version

```bash
# Installed version
openclaw --version

# Latest available version (without side effects)
npm view openclaw version --userconfig "$(mktemp)"

# Beta channel version
npm view openclaw@beta version --userconfig "$(mktemp)"
```

### List All Available Versions

```bash
npm view openclaw versions --json | jq -r '.[]' | tail -20
```

### Downgrade If Needed

```bash
# Downgrade to specific version
sudo npm i -g openclaw@2026.2.14

# Verify downgrade
openclaw --version
```

## Release Channel Information

### Channel Types

- **stable**: Tagged releases (e.g., v2026.2.15)
  - NPM dist-tag: `latest`
  - Install: `npm i -g openclaw@latest`

- **beta**: Pre-release versions
  - NPM dist-tag: `beta`
  - Format: `vYYYY.M.D-beta.N`
  - Install: `npm i -g openclaw@beta`

- **dev**: Latest main branch
  - No NPM release
  - Requires building from source
  - Clone and build locally

## Troubleshooting

### Permission Issues

```bash
# If global install fails with permissions
sudo npm i -g openclaw@latest

# Alternative: use a Node version manager
nvm use 22
npm i -g openclaw@latest
```

### Cache Issues

```bash
# Clear npm cache
npm cache clean --force

# Reinstall
sudo npm i -g openclaw@latest --force
```

### Gateway Won't Start After Upgrade

```bash
# Run doctor to check for issues
openclaw doctor

# Reset gateway mode
openclaw config set gateway.mode local

# Check for port conflicts
lsof -i :18789
```

### Service Stuck in Restart Loop (systemd)

```bash
# Check service status and restart count
systemctl --user status openclaw-gateway.service

# View recent logs to identify the error
journalctl --user -u openclaw-gateway.service -n 50 --no-pager

# Stop the failing service
systemctl --user stop openclaw-gateway.service

# If ERR_MODULE_NOT_FOUND errors appear, see Missing Dependencies section
```

### Missing Dependencies (ERR_MODULE_NOT_FOUND)

Common after upgrades or partial rebuilds. The `long` package is a frequent culprit.

```bash
# Stop the service first
systemctl --user stop openclaw-gateway.service

# Clean reinstall all dependencies
cd ~/code/openclaw
rm -rf node_modules pnpm-lock.yaml
pnpm install

# Add specific missing package (e.g., 'long')
pnpm add -w long

# Rebuild the project
pnpm build

# Restart the service
systemctl --user start openclaw-gateway.service

# Verify it's working
openclaw channels status --probe
```

### Build Failures After Dependency Fix

```bash
# If rolldown or other build tools fail
cd ~/code/openclaw

# Complete clean and rebuild
rm -rf node_modules dist .turbo
pnpm install
pnpm build

# If A2UI bundling fails
pnpm canvas:a2ui:bundle

# Then retry the build
pnpm build
```

### Configuration Lost After Upgrade

```bash
# Check if config exists
ls -la ~/.openclaw/config.json

# Restore from auto-backup if available
ls -la ~/.openclaw/config.json.*

# Reconfigure if needed
openclaw config set gateway.mode local
openclaw config set gateway.port 18789
```

## Platform-Specific Notes

### Docker Environments

```bash
# Inside container
npm i -g openclaw@latest

# Or rebuild image with new version
docker build --build-arg OPENCLAW_VERSION=latest -t openclaw:latest .
```

### CI/CD Pipelines

```yaml
# GitHub Actions example
- name: Install OpenClaw
  run: |
    npm i -g openclaw@latest
    openclaw --version
```

### Homebrew (macOS)

```bash
# If installed via Homebrew (not officially supported)
brew upgrade openclaw

# Or reinstall
brew uninstall openclaw
npm i -g openclaw@latest
```

## Advanced Scenarios

### Multi-Version Testing

```bash
# Install specific version in isolated environment
npx openclaw@2026.2.14 --version
npx openclaw@latest --version
```

### Build from Specific Commit

```bash
cd ~/code/openclaw
git fetch origin
git checkout <commit-hash>
pnpm install
pnpm build
sudo npm link
```

### Plugin Compatibility Check

```bash
# After upgrade, verify plugins
openclaw plugins list
openclaw plugins verify

# Reinstall plugins if needed
cd extensions/<plugin-name>
npm install --omit=dev
```

## Common Issues and Solutions

### The "long" Package Missing Issue

After certain upgrades or dependency updates, the gateway may fail with:
```
Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'long' imported from
/home/user/code/openclaw/node_modules/.pnpm/@whiskeysockets+baileys@*/...
```

This is commonly caused by incomplete dependency resolution. Solution:
```bash
cd ~/code/openclaw
systemctl --user stop openclaw-gateway.service
pnpm add -w long
pnpm build
systemctl --user start openclaw-gateway.service
```

### Service Restart Loop Detection

If the service shows high restart counts (e.g., "restart counter is at 72"):
1. Stop the service immediately to prevent resource waste
2. Check logs for the root cause (usually dependency issues)
3. Fix the underlying issue
4. Clear service failure state before restarting

## Best Practices

1. **Always backup configuration before major upgrades**
2. **Test in development environment first**
3. **Check changelog for breaking changes**
4. **Verify gateway connectivity after upgrade**
5. **Keep logs during upgrade for debugging**
6. **Monitor service restart count after upgrades**
7. **Clean reinstall dependencies if mysterious errors occur**

## Quick Upgrade Script

Use the provided upgrade script for safe, automated upgrades:

```bash
# Run the upgrade script
~/.agents/skills/openclaw-upgrade/scripts/upgrade.sh

# With options
~/.agents/skills/openclaw-upgrade/scripts/upgrade.sh --help
~/.agents/skills/openclaw-upgrade/scripts/upgrade.sh beta        # Upgrade to beta
~/.agents/skills/openclaw-upgrade/scripts/upgrade.sh 2026.3.1   # Specific version
```

The script handles:
- Configuration backup
- Dependency verification
- Service restart loop detection
- Automatic dependency fixes
- Rollback on failure

## Rollback Procedure

```bash
# If upgrade causes issues
# 1. Stop current processes
pkill -f openclaw || true

# 2. Downgrade to previous version
sudo npm i -g openclaw@<previous-version>

# 3. Restore configuration backup
openclaw config import < ~/.openclaw-backup-YYYYMMDD.json

# 4. Restart services
openclaw gateway run
```