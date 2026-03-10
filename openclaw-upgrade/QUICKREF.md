# OpenClaw Upgrade Quick Reference

## Automated Upgrade Script

```bash
# Safe upgrade with all checks
~/.agents/skills/openclaw-upgrade/scripts/upgrade.sh

# Upgrade to beta
~/.agents/skills/openclaw-upgrade/scripts/upgrade.sh beta

# Show help
~/.agents/skills/openclaw-upgrade/scripts/upgrade.sh --help
```

## Most Common Commands

```bash
# Standard upgrade (global install)
sudo npm i -g openclaw@latest

# Check version
openclaw --version

# Verify upgrade worked
openclaw doctor
```

## Quick Upgrade by Environment

### Production Server
```bash
sudo npm i -g openclaw@latest && openclaw doctor
```

### exe.dev VM
```bash
sudo npm i -g openclaw@latest && pkill -f openclaw-gateway && nohup openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &
```

### Development Machine
```bash
cd ~/code/openclaw && git pull --rebase && pnpm install && pnpm build
```

### macOS App
```bash
cd ~/code/openclaw && git pull && pnpm build && scripts/package-mac-app.sh
```

## Version Checks

```bash
# Current version
openclaw --version

# Latest available
npm view openclaw version --userconfig "$(mktemp)"

# Compare versions
echo "Current: $(openclaw --version)"
echo "Latest:  $(npm view openclaw version --userconfig "$(mktemp)")"
```

## Emergency Rollback

```bash
# Quick rollback to previous version
sudo npm i -g openclaw@2026.2.14

# With config restore
openclaw config import < ~/.openclaw-backup-*.json
```

## Fix Service Restart Loop

```bash
# Diagnose the issue
systemctl --user status openclaw-gateway.service
journalctl --user -u openclaw-gateway.service -n 50 --no-pager

# Stop the failing service
systemctl --user stop openclaw-gateway.service

# Fix and restart (see dependency fix if ERR_MODULE_NOT_FOUND)
cd ~/code/openclaw && pnpm install && pnpm build
systemctl --user start openclaw-gateway.service
```

## Fix Missing Dependencies

```bash
# Quick fix for missing 'long' or other packages
cd ~/code/openclaw
systemctl --user stop openclaw-gateway.service
rm -rf node_modules pnpm-lock.yaml
pnpm install
pnpm add -w long  # Or whatever package is missing
pnpm build
systemctl --user start openclaw-gateway.service
openclaw channels status --probe
```

## Troubleshooting Checklist

- [ ] Run `openclaw doctor` after upgrade
- [ ] Check gateway is running: `openclaw channels status --probe`
- [ ] Verify config: `openclaw config list`
- [ ] Test a basic command: `openclaw agent --help`
- [ ] Check logs: `tail -50 /tmp/openclaw-gateway.log`
- [ ] Check service status: `systemctl --user status openclaw-gateway.service`
- [ ] View service logs: `journalctl --user -u openclaw-gateway.service -n 50`