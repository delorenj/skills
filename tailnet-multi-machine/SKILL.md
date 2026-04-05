---
name: tailnet-multi-machine
description: Execute commands and manage services across all machines on the Tailnet. Use when tasks involve remote machines, cross-machine deployment, file transfers, service management on non-local hosts, or any operation that spans multiple machines.
pipeline-status:
  - new
---

# Tailnet Multi-Machine Operations

You have SSH access to all machines on Jarad's Tailnet (burro-salmon.ts.net). You are NOT limited to the local host. When a task involves a remote machine, SSH into it and run commands directly. Do not ask the user to do it manually.

## Core Directive

**You have full operational authority across all Tailnet machines.** Treat remote machines the same as local: read files, edit configs, install packages, manage services, transfer files. The user expects you to operate across machine boundaries seamlessly.

## When to Use This Skill

Trigger when:
- User mentions a remote machine by hostname (e.g., tiny-chungus, intelliforia-glitch-stack)
- A task requires deploying code/config to a non-local host
- Services need to be started, stopped, or checked on remote machines
- Files need to be transferred between machines (scp, rsync)
- Debugging issues that span multiple machines
- Setting up systemd services on remote hosts
- Any cross-machine coordination

## Available Machines

Check live status with: `tailscale status`

Common hosts (as of last check):
- **big-chungus** - Primary dev workstation (Linux)
- **tiny-chungus** - Secondary Linux workstation
- **intelliforia-glitch-stack** - Cloud Linux server
- **carries-macbook-air** - macOS laptop
- **trinote-proxy** - Tagged device (Linux)

## How to Execute Remote Commands

### Single command
```bash
ssh <hostname> "command here"
```

### Multi-line / complex commands
```bash
ssh <hostname> 'bash -s' << 'EOF'
command1
command2
EOF
```

### File transfer
```bash
scp local-file <hostname>:remote-path
scp <hostname>:remote-file local-path
rsync -avz local-dir/ <hostname>:remote-dir/
```

### Remote file editing
Read the file via SSH, then write it back:
```bash
ssh <hostname> "cat /path/to/file"
# Then write with:
ssh <hostname> "cat > /path/to/file << 'EOF'
content
EOF"
```

## Operational Rules

1. **SSH host key changes**: On Tailnet machines, accept new host keys automatically. These machines get reinstalled. Use `ssh-keygen -R <host>` then `ssh -o StrictHostKeyChecking=accept-new`.

2. **Port selection**: Never assume standard ports (8080, 8081, 3000, etc.) are available. Always use random high ports (30000-60000 range). Use `shuf -i 30000-60000 -n 1` to generate.

3. **User context**: All machines use the `delorenj` user account. Home directory is `/home/delorenj` on Linux, `/Users/delorenj` on macOS.

4. **Package managers**: Arch Linux machines use `pacman`/`yay`. Ubuntu/Debian use `apt`. macOS uses `brew`. Check with `cat /etc/os-release` or `uname -s` if unsure.

5. **Systemd user services**: For per-user daemons on remote machines, use `systemctl --user` and place units in `~/.config/systemd/user/`. Enable lingering if the service should run without login: `loginctl enable-linger delorenj`.

6. **Config files**: Store app configs in `~/.config/<app-name>/` on remote machines.

7. **Parallelism**: When operating on multiple machines simultaneously, run independent SSH commands in parallel.
