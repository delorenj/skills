---
pipeline-status:
  - new
---
# Shell Configuration Patterns (zshyzsh)

## Philosophy

**Cross-Platform, Modular Configuration:** A comprehensive shell system optimized for power users working across macOS and Linux environments with intelligent platform detection and automated setup.

**Base Directory:** `~/.config/zshyzsh/` (aliased as `$ZC`)

**Critical Convention:** `exported` paths are ALWAYS in caps. `aliases` and `functions` are ALWAYS lowercase. For every exported path, there should be an alias to navigate to it quickly.

## Directory Structure

```
~/.config/zshyzsh/
├── README.md                    # Documentation and usage guide
├── aliases.zsh                  # Custom command aliases
├── secrets.zsh                  # Secrets (migrating to 1password DeLoSecrets vault)
├── completions/                 # Shell completions
│   └── app.zsh                 # Per-app completion scripts
├── scripts/                     # Standalone scripts
│   └── some_script.zsh         # Linked to ~/.local/bin/some_script
├── functions by topic:          # Complex commands too long for aliases
│   ├── docker-commands.zsh
│   └── github.zsh
├── platforms/                   # OS-specific configurations
│   ├── macos-init.zsh          # macOS-specific setup
│   └── linux-init.zsh          # Linux-specific setup
├── zellij/                      # Terminal multiplexer configs
│   ├── config.kdl              # Zellij configuration
│   ├── layouts/                # Custom layouts
│   │   ├── default.kdl
│   │   ├── dev.kdl
│   │   └── workspace.kdl
│   └── setup-zellij-v2.sh      # Setup automation
└── alacritty/                   # Terminal emulator configs
    └── themes/                 # Color schemes
```

## Path Exports and Aliases Pattern

Every exported path gets a matching lowercase alias for quick navigation:

```bash
# Path exports (ALWAYS CAPS)
export CODE="$HOME/code"
export VAULT="$HOME/code/DeLoDocs"
export CONTAINERS="$HOME/docker"
export ZSHYZSH="$HOME/.config/zshyzsh"
export ZC="$ZSHYZSH"

# Navigation aliases (ALWAYS LOWERCASE)
alias code='cd $CODE'
alias vault='cd $VAULT'
alias containers='cd $CONTAINERS'
alias zc='cd $ZC'
```

## Core Configuration (.zshrc)

### Base Setup
```bash
# Path configuration
export PATH=$HOME/bin:/usr/local/bin:$PATH
export PATH=$HOME/.npm-global/bin:$PATH
export PATH=$HOME/.local/bin:$PATH

# Editor preferences
export EDITOR='nvim'
export VISUAL='nvim'

# Mise activation (tool version management, replaces asdf/nvm/pyenv etc.)
eval "$($HOME/.local/bin/mise activate zsh)"

# Starship prompt
eval "$(starship init zsh)"

# Platform detection
export OSTYPE=$(uname -s)
```

## Platform-Specific Patterns

### macOS Configuration (platforms/macos-init.zsh)
```bash
# Package manager
export HOMEBREW_PREFIX="/opt/homebrew"
eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"

# Python version handling (use python3 explicitly)
alias python='python3'
alias pip='pip3'

# macOS-specific tools
alias open-with='open -a'

# GNU tools with g prefix
alias sed='gsed'
alias awk='gawk'
```

### Linux Configuration (platforms/linux-init.zsh)
```bash
# Package manager (apt-based)
alias update='sudo apt update && sudo apt upgrade -y'
alias install='sudo apt install'

# System information
alias sysinfo='neofetch'

# Linux-specific tools
alias pbcopy='xclip -selection clipboard'
alias pbpaste='xclip -selection clipboard -o'
```

## Alias Patterns

### Git Aliases
```bash
# Status and diff
alias gs='git status'
alias gd='git diff'
alias gdc='git diff --cached'

# Branch management
alias gb='git branch'
alias gba='git branch -a'
alias gbd='git branch -d'

# Commit operations
alias gc='git commit -m'
alias gca='git commit --amend'

# Log viewing
alias gl='git log --oneline --graph --decorate'
alias gla='git log --oneline --graph --decorate --all'
```

### Docker Aliases
```bash
# Compose shortcuts (docker compose v2, NOT docker-compose)
alias dc='docker compose'
alias dcu='docker compose up -d'
alias dcd='docker compose down'
alias dcl='docker compose logs -f'
alias dcr='docker compose restart'

# Container operations
alias dps='docker ps'
alias dpsa='docker ps -a'
alias di='docker images'
alias drm='docker rm'
alias drmi='docker rmi'

# Docker cleanup
alias docker-clean='docker system prune -a --volumes'
```

### Mise Aliases
```bash
# Mise (tool version manager, replaces asdf/nvm/pyenv)
alias mr='mise run'
alias ml='mise list'
alias mi='mise install'
```

### System Aliases
```bash
# Navigation
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# Listing
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'

# Safety nets
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
```

## Function Patterns

### Directory Management
```bash
# Create and enter directory
mkcd() {
  mkdir -p "$1" && cd "$1"
}

# Find and cd to directory
fcd() {
  local dir
  dir=$(find ${1:-.} -type d 2> /dev/null | fzf +m) && cd "$dir"
}
```

### Git Functions
```bash
# Clone and enter repository
gclone() {
  git clone "$1" && cd "$(basename "$1" .git)"
}
```

### Docker Functions
```bash
# Enter running container
dexec() {
  docker exec -it "$1" /bin/bash || docker exec -it "$1" /bin/sh
}

# Tail logs for container
dlogs() {
  docker logs -f "$1"
}

# Quick compose up with rebuild
dcup-rebuild() {
  docker compose down
  docker compose build --no-cache
  docker compose up -d
}
```

### Development Functions
```bash
# Port killer
killport() {
  lsof -ti:$1 | xargs kill -9
}

# Quick Python virtual environment
venv-create() {
  python -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
}
```

## Zellij Integration

### Configuration (zellij/config.kdl)
```kdl
keybinds {
    normal {
        bind "Ctrl p" { SwitchToMode "Pane"; }
        bind "Ctrl t" { SwitchToMode "Tab"; }
        bind "Ctrl s" { SwitchToMode "Scroll"; }
    }
}

default_layout "default"
auto_layout true
```

### Session Management
```bash
# Start named session
zellij-start() {
  zellij attach -c "$1"
}

# Session shortcuts
alias zl='zellij list-sessions'
alias za='zellij attach'
alias zk='zellij kill-session'
```

## Cross-Platform Compatibility

### Detection Pattern
```bash
# Detect platform and load appropriate config
case "$OSTYPE" in
  darwin*)
    source ~/.config/zshyzsh/platforms/macos-init.zsh
    ;;
  linux*)
    if [[ -n "$DISPLAY" ]]; then
      source ~/.config/zshyzsh/platforms/linux-desktop-init.zsh
    else
      source ~/.config/zshyzsh/platforms/linux-server-init.zsh
    fi
    ;;
esac
```

## Performance Optimization

### Completion Caching
```bash
autoload -Uz compinit
if [[ -n ${ZDOTDIR}/.zcompdump(#qN.mh+24) ]]; then
  compinit
else
  compinit -C
fi
```

### Lazy Loading (for tools not yet migrated to Mise)
```bash
# Example: lazy load a tool that can't be managed by Mise
expensive-tool() {
  unset -f expensive-tool
  eval "$(expensive-tool init -)"
  expensive-tool "$@"
}
```

## Migration Checklist

When setting up on a new machine:

- [ ] Clone zshyzsh config repo
- [ ] Symlink ~/.zshrc to config
- [ ] Install mise (`curl https://mise.run | sh`)
- [ ] Run `mise install` to get all tools
- [ ] Source platform-specific configs
- [ ] Test Zellij integration
- [ ] Configure git credentials
