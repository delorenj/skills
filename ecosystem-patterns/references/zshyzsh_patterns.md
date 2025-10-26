# Shell Configuration Patterns (zshyzsh)

## Philosophy

**Cross-Platform, Modular Configuration:** A comprehensive shell system optimized for power users working across macOS and Linux environments with intelligent platform detection and automated setup.

**Base Directory:** `~/.config/zshyzsh/`

## Directory Structure

```
~/.config/zshyzsh/
├── README.md                    # Documentation and usage guide
├── aliases.zsh                  # Custom command aliases
├── functions.zsh                # Shell functions and utilities
├── terminal_logger.sh           # Session logging system
├── platforms/                   # OS-specific configurations
│   ├── macos-init.zsh          # macOS-specific setup
│   └── linux-init.zsh          # Linux-specific setup
├── zellij/                      # Terminal multiplexer configs
│   ├── config.kdl              # Zellij configuration
│   ├── layouts/                # Custom layouts
│   │   ├── default.kdl
│   │   ├── dev.kdl
│   │   └── workspace.kdl
│   ├── setup-zellij-v2.sh      # Setup automation
│   └── test-setup.sh           # Configuration tester
├── alacritty/                   # Terminal emulator configs
│   └── themes/                 # Color schemes
└── fabric/                      # AI workflow patterns
    └── patterns/               # Prompt patterns
```

## Core Configuration (.zshrc)

### Base Setup
```bash
# Path configuration
export PATH=$HOME/bin:/usr/local/bin:$PATH
export PATH=$HOME/.npm-global/bin:$PATH
export PATH=$HOME/.local/bin:$PATH

# Oh-My-Zsh configuration
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"  # or starship for advanced theming

# Essential plugins
plugins=(
  git                    # Git version control integration
  asdf                   # Version manager for runtimes
  docker                 # Docker container management
  docker-compose         # Docker Compose commands
  kubectl                # Kubernetes CLI autocompletion
  python                 # Python development helpers
  pip                    # Python package manager
  npm                    # Node Package Manager
  node                   # NodeJS environment helpers
  vscode                 # VS Code integration
  dirhistory             # Navigate with Alt+Left/Right
  extract                # Extract archives with 'x'
  sudo                   # ESC twice for sudo
  command-not-found      # Suggest package installation
)

source $ZSH/oh-my-zsh.sh
```

### Environment Variables
```bash
# Editor preferences
export EDITOR='vim'
export VISUAL='code'

# Language settings
export LANG=en_US.UTF-8

# Tool integrations
eval "$(/Users/delorenj/.local/bin/mise activate zsh)"
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

# Spotlight search
alias spotlight='mdfind'

# Docker Desktop specific
export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
```

### Linux Configuration (platforms/linux-init.zsh)
```bash
# Package manager (apt-based)
alias update='sudo apt update && sudo apt upgrade -y'
alias install='sudo apt install'

# System information
alias sysinfo='neofetch'

# Docker via system service
export DOCKER_HOST="unix:///var/run/docker.sock"

# Linux-specific tools
alias pbcopy='xclip -selection clipboard'
alias pbpaste='xclip -selection clipboard -o'
```

## Alias Patterns

### Git Aliases (Enhanced)
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
alias gcn='git commit --no-verify -m'

# Log viewing
alias gl='git log --oneline --graph --decorate'
alias gla='git log --oneline --graph --decorate --all'

# Worktree operations (iMi integration)
alias gwl='git worktree list'
alias gwa='git worktree add'
alias gwr='git worktree remove'
```

### Docker Aliases
```bash
# Compose shortcuts
alias dc='docker-compose'
alias dcu='docker-compose up -d'
alias dcd='docker-compose down'
alias dcl='docker-compose logs -f'
alias dcr='docker-compose restart'

# Container operations
alias dps='docker ps'
alias dpsa='docker ps -a'
alias di='docker images'
alias drm='docker rm'
alias drmi='docker rmi'

# Docker cleanup
alias docker-clean='docker system prune -a --volumes'
alias docker-nuke='docker stop $(docker ps -aq) && docker rm $(docker ps -aq)'
```

### Development Aliases
```bash
# Project navigation
alias code-dir='cd ~/code'
alias projects='cd ~/code/projects'

# Quick edits
alias zshconfig='code ~/.zshrc'
alias zshload='source ~/.zshrc'

# Mise (tool version manager)
alias mr='mise run'
alias ml='mise list'
alias mi='mise install'

# Common development tasks
alias serve='python -m http.server'
alias ports='lsof -i -P -n | grep LISTEN'
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

# Disk usage
alias df='df -h'
alias du='du -h'
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

# Create feature branch (iMi pattern)
gfeature() {
  git worktree add "feature-$1" -b "feature/$1"
}

# Quick commit and push
quick-commit() {
  git add .
  git commit -m "$1"
  git push
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
  docker-compose down
  docker-compose build --no-cache
  docker-compose up -d
}
```

### Development Functions
```bash
# Port killer
killport() {
  lsof -ti:$1 | xargs kill -9
}

# Project initializer
init-project() {
  local name=$1
  mkdir -p ~/code/$name/trunk-main
  cd ~/code/$name
  git clone "git@github.com:delorenj/$name.git" trunk-main
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
// Terminal multiplexer configuration
keybinds {
    normal {
        bind "Ctrl p" { SwitchToMode "Pane"; }
        bind "Ctrl t" { SwitchToMode "Tab"; }
        bind "Ctrl s" { SwitchToMode "Scroll"; }
    }
}

// Session naming from directory
default_layout "default"
auto_layout true

// Copy/paste behavior
copy_command "pbcopy"  // macOS
// copy_command "xclip -selection clipboard"  // Linux
```

### Layouts (zellij/layouts/dev.kdl)
```kdl
layout {
    pane split_direction="vertical" {
        pane name="editor" size="70%"
        pane split_direction="horizontal" {
            pane name="terminal" size="50%"
            pane name="logs" size="50%"
        }
    }
}
```

### Session Management
```bash
# Start named session
zellij-start() {
  zellij attach -c "$1"
}

# List sessions
alias zl='zellij list-sessions'

# Attach to session
alias za='zellij attach'

# Kill session
alias zk='zellij kill-session'
```

## Terminal Logging System

### Logger Configuration (terminal_logger.sh)
```bash
# Configuration
LOG_DIR="$HOME/terminal-logs"
SESSION_LOG="$LOG_DIR/$(date +%Y%m%d-%H%M).log"

# Initialize logging
init_logger() {
  mkdir -p "$LOG_DIR"
  exec > >(tee -a "$SESSION_LOG")
  exec 2>&1
}

# Log command execution
preexec() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] COMMAND: $1" >> "$SESSION_LOG"
}
```

### Integration with Zellij
```bash
# Zellij session-specific logging
if [[ -n "$ZELLIJ" ]]; then
  SESSION_NAME=$(zellij list-sessions | grep "CURRENT" | awk '{print $1}')
  LOG_DIR="$HOME/terminal-logs/$SESSION_NAME"
  mkdir -p "$LOG_DIR"
fi
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

### Path Normalization
```bash
# Normalize paths across platforms
normalize_path() {
  local path="$1"
  # Convert Windows-style paths if needed
  path="${path//\\//}"
  # Expand tilde
  path="${path/#\~/$HOME}"
  echo "$path"
}
```

## AI Workflow Integration (Fabric Patterns)

### Pattern Structure
```
fabric/patterns/
├── code_review/
│   └── system.md
├── commit_message/
│   └── system.md
└── documentation/
    └── system.md
```

### Quick Access Functions
```bash
# Code review with AI
ai-review() {
  git diff | fabric --pattern code_review
}

# Generate commit message
ai-commit() {
  git diff --cached | fabric --pattern commit_message
}

# Document function
ai-doc() {
  cat "$1" | fabric --pattern documentation
}
```

## Performance Optimization

### Lazy Loading
```bash
# Lazy load nvm
nvm() {
  unset -f nvm
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  nvm "$@"
}

# Lazy load pyenv
pyenv() {
  unset -f pyenv
  eval "$(command pyenv init -)"
  pyenv "$@"
}
```

### Completion Caching
```bash
# Cache completion results
autoload -Uz compinit
if [[ -n ${ZDOTDIR}/.zcompdump(#qN.mh+24) ]]; then
  compinit
else
  compinit -C
fi
```

## Best Practices

1. **Modular Organization** - Separate configs by platform and purpose
2. **Cross-Platform Compatibility** - Test on both macOS and Linux
3. **Lazy Loading** - Delay expensive operations
4. **Alias Safety** - Add confirmation for destructive commands
5. **Function Documentation** - Comment complex functions
6. **Version Control** - Track dotfiles in git
7. **Backup Strategy** - Keep pre-change backups
8. **Performance Monitoring** - Profile slow startup

## Troubleshooting

### Slow Startup
```bash
# Profile zsh startup
zsh -xv 2>&1 | ts -i '%.s' > /tmp/zsh-startup.log

# Identify slow plugins
time zsh -i -c exit
```

### Path Issues
```bash
# Check PATH order
echo $PATH | tr ':' '\n'

# Reset PATH
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
```

### Permission Issues
```bash
# Fix zsh directory permissions
compaudit | xargs chmod g-w
compaudit | xargs chown $USER
```

## Migration Checklist

When setting up on a new machine:

- [ ] Install oh-my-zsh
- [ ] Clone zshyzsh config repo
- [ ] Symlink ~/.zshrc to config
- [ ] Install required tools (mise, starship, etc.)
- [ ] Source platform-specific configs
- [ ] Test Zellij integration
- [ ] Verify terminal logging
- [ ] Set up completion caching
- [ ] Configure git credentials
- [ ] Test Docker integration
