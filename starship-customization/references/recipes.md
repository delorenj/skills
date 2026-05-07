# Recipe Cookbook

Outside-the-box `[custom.<name>]` modules. Each recipe is paste-ready into `~/.config/starship.toml`. Adapt names, paths, and styles to taste.

Pick a recipe by intent:

| Intent | Recipe |
|---|---|
| Show context only when relevant tool is in use | [Kubernetes context in helm dirs](#kubernetes-context-in-helm-dirs), [Terraform workspace](#terraform-workspace), [Docker compose project](#docker-compose-project) |
| Surface env state | [AWS profile + region](#aws-profile-and-region), [GCP project](#gcp-project), [Active Tailscale node](#active-tailscale-node), [Deployment env (dev/staging/prod)](#deployment-environment-marker) |
| Make the prompt feel alive | [Now-playing track](#now-playing-track), [Weather glyph](#weather-glyph), [Pomodoro timer](#pomodoro-timer), [Unread mail count](#unread-mail-count) |
| Surface project metadata | [package.json scripts present](#packagejson-scripts-present), [pyproject venv name](#pyproject-venv-name), [Mise tasks present](#mise-tasks-present), [Branch staleness](#branch-staleness-vs-main) |
| Surface system or AI state | [AI usage cost today](#ai-usage-cost-today), [GPU temp / VRAM](#gpu-temp-and-vram), [Battery low warning](#battery-low-warning) |
| Build / CI signal | [Last build status](#last-build-status), [Pending PR count](#pending-pr-count), [Failing tests counter](#failing-tests-counter) |
| Just for fun | [Random kaomoji](#random-kaomoji), [Cat fact rotator](#cat-fact-rotator) |

All recipes pin `shell = ['sh', '-c']` unless a different shell is required.

---

## Kubernetes context in helm dirs

Show the current kube context, but only when you're inside a directory that looks like helm work.

```toml
[custom.k8s_helm]
command = 'kubectl config current-context 2>/dev/null'
detect_folders = ['helm', 'charts', 'k8s', 'kubernetes']
detect_files = ['Chart.yaml', 'kustomization.yaml']
shell = ['sh', '-c']
description = 'Kubernetes context (helm/k8s dirs only)'
symbol = '⎈ '
style = 'bold purple'
format = ' on [$symbol$output]($style)'
```

## Terraform workspace

```toml
[custom.tf_workspace]
command = 'terraform workspace show 2>/dev/null'
detect_extensions = ['tf', 'tfvars']
detect_folders = ['.terraform']
shell = ['sh', '-c']
description = 'Terraform workspace'
symbol = '🏗 '
style = 'fg:#7B42BC bold'
format = ' [$symbol$output]($style)'
```

## Docker compose project

Surface the compose project name from `COMPOSE_PROJECT_NAME` or fallback to dirname.

```toml
[custom.compose_project]
command = '''
  if [ -n "$COMPOSE_PROJECT_NAME" ]; then
    echo "$COMPOSE_PROJECT_NAME"
  else
    basename "$PWD"
  fi
'''
detect_files = ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']
shell = ['sh', '-c']
description = 'Docker compose project'
symbol = ' '
style = 'bold blue'
format = ' [$symbol$output]($style)'
```

## AWS profile and region

```toml
[custom.aws_profile]
command = '''
  prof="${AWS_PROFILE:-${AWS_DEFAULT_PROFILE:-default}}"
  region="${AWS_REGION:-${AWS_DEFAULT_REGION:-}}"
  if [ -n "$region" ]; then
    echo "$prof@$region"
  else
    echo "$prof"
  fi
'''
when = 'test -n "$AWS_PROFILE" -o -n "$AWS_DEFAULT_PROFILE"'
shell = ['sh', '-c']
description = 'AWS profile (and region if set)'
symbol = '☁ '
style = 'bold #FF9900'
format = ' [$symbol$output]($style)'
```

## GCP project

```toml
[custom.gcp_project]
command = 'gcloud config get-value project 2>/dev/null'
when = 'command -v gcloud >/dev/null && test -n "$(gcloud config get-value project 2>/dev/null)"'
shell = ['sh', '-c']
description = 'Active GCP project'
symbol = ' '
style = 'fg:#4285F4'
format = ' [$symbol$output]($style)'
```

## Active Tailscale node

Show this machine's tailnet hostname when tailscaled is running.

```toml
[custom.tailscale]
command = 'tailscale status --json 2>/dev/null | jq -r ".Self.HostName // empty"'
when = 'command -v tailscale >/dev/null && tailscale status --peers=false >/dev/null 2>&1'
shell = ['sh', '-c']
description = 'Tailscale node name'
symbol = '🔒 '
style = 'fg:#7c5cff'
format = ' [$symbol$output]($style)'
```

## Deployment environment marker

Switches color/glyph based on env name in `$DEPLOY_ENV` or a `.env-marker` file.

```toml
[custom.deploy_env]
command = '''
  env="${DEPLOY_ENV:-$(cat .env-marker 2>/dev/null)}"
  case "$env" in
    prod*|production) printf "%s" "🔴 prod" ;;
    stag*|staging)    printf "%s" "🟡 staging" ;;
    dev*|development) printf "%s" "🟢 dev" ;;
    *) ;;
  esac
'''
when = 'test -n "$DEPLOY_ENV" -o -f .env-marker'
shell = ['sh', '-c']
description = 'Deployment environment'
style = 'bold'
format = ' [$output]($style)'
```

## Now-playing track

macOS (uses `osascript`):

```toml
[custom.spotify]
command = '''osascript -e 'tell application "Spotify" to if it is running then artist of current track & " — " & name of current track' 2>/dev/null'''
when = '''osascript -e 'application "Spotify" is running' 2>/dev/null | grep -q true'''
shell = ['sh', '-c']
os = 'macos'
description = 'Spotify now playing'
symbol = '♫ '
style = 'fg:#1DB954'
format = ' [$symbol$output]($style)'
```

Linux (mpris via `playerctl`):

```toml
[custom.now_playing]
command = 'playerctl metadata --format "{{ artist }} — {{ title }}" 2>/dev/null'
when = 'command -v playerctl >/dev/null && playerctl status 2>/dev/null | grep -q Playing'
shell = ['sh', '-c']
os = 'linux'
description = 'MPRIS now playing'
symbol = '♫ '
style = 'fg:#a4ffea'
format = ' [$symbol$output]($style)'
```

## Weather glyph

Single-character glyph from wttr.in, cached for an hour. Avoid hammering the API on every prompt.

```toml
[custom.weather]
command = '''
  cache="$HOME/.cache/starship-weather"
  mkdir -p "$(dirname "$cache")"
  if [ ! -f "$cache" ] || [ "$(find "$cache" -mmin +60)" ]; then
    curl -sf --max-time 2 'https://wttr.in/?format=%c%t' > "$cache" || true
  fi
  cat "$cache" 2>/dev/null
'''
shell = ['sh', '-c']
description = 'Weather (cached 1h)'
style = 'fg:#a4ffea'
format = ' [$output]($style)'
```

## Pomodoro timer

Reads remaining seconds from `~/.cache/pomodoro` (written by an external timer). Hides when expired.

```toml
[custom.pomodoro]
command = '''
  end=$(cat "$HOME/.cache/pomodoro" 2>/dev/null) || exit 0
  now=$(date +%s)
  remaining=$(( end - now ))
  [ "$remaining" -le 0 ] && exit 0
  printf "%d:%02d" $((remaining/60)) $((remaining%60))
'''
when = 'test -f "$HOME/.cache/pomodoro"'
shell = ['sh', '-c']
description = 'Pomodoro time remaining'
symbol = '🍅 '
style = 'bold red'
format = ' [$symbol$output]($style)'
```

## Unread mail count

Reads from `~/Maildir/INBOX/new`. Hides on zero.

```toml
[custom.mail]
command = '''
  count=$(find "$HOME/Maildir/INBOX/new" -type f 2>/dev/null | wc -l | tr -d ' ')
  [ "$count" -gt 0 ] && echo "$count"
'''
when = 'test -d "$HOME/Maildir/INBOX/new"'
shell = ['sh', '-c']
description = 'Unread mail (Maildir)'
symbol = '✉ '
style = 'bold yellow'
format = ' [$symbol$output]($style)'
```

## package.json scripts present

Show a glyph if the project has scripts defined; click-bait for `npm run`.

```toml
[custom.npm_scripts]
command = '''
  count=$(jq -r '.scripts // {} | keys | length' package.json 2>/dev/null)
  [ "${count:-0}" -gt 0 ] && echo "$count"
'''
detect_files = ['package.json']
shell = ['sh', '-c']
description = 'npm script count'
symbol = '📦 '
style = 'bold green'
format = ' [$symbol$output scripts]($style)'
```

## pyproject venv name

Surface the venv name (not just `(.venv)`) — pulls from `pyproject.toml`.

```toml
[custom.py_project]
command = '''
  python -c "import tomllib,sys; print(tomllib.loads(open('pyproject.toml','rb').read().decode()).get('project',{}).get('name',''))" 2>/dev/null
'''
detect_files = ['pyproject.toml']
shell = ['sh', '-c']
description = 'pyproject project name'
symbol = '🐍 '
style = 'fg:#3776AB'
format = ' [$symbol$output]($style)'
```

## Mise tasks present

```toml
[custom.mise_tasks]
command = '''
  mise tasks ls --no-header 2>/dev/null | wc -l | tr -d ' '
'''
when = 'command -v mise >/dev/null && (test -f .mise.toml -o -f mise.toml -o -f .config/mise/config.toml)'
shell = ['sh', '-c']
description = 'mise task count'
symbol = '⚙ '
style = 'fg:#a4ffea'
format = ' [$symbol$output tasks]($style)'
```

## Branch staleness vs main

Number of commits the current branch is behind `origin/main`. Hides when zero or not a repo.

```toml
[custom.branch_stale]
command = '''
  base=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/@@')
  [ -z "$base" ] && exit 0
  behind=$(git rev-list --count "HEAD..$base" 2>/dev/null)
  [ "${behind:-0}" -gt 0 ] && echo "$behind"
'''
require_repo = true
shell = ['sh', '-c']
description = 'Commits behind origin default branch'
symbol = '↓'
style = 'bold red'
format = ' [$symbol$output]($style)'
```

## AI usage cost today

Reads a daily total from a JSONL log written by an LLM client wrapper. Aggregates today's `usd` field.

```toml
[custom.ai_cost]
command = '''
  log="$HOME/.local/share/ai/usage-$(date +%Y-%m-%d).jsonl"
  [ -f "$log" ] || exit 0
  jq -r '.usd // 0' "$log" 2>/dev/null \
    | awk '{ s += $1 } END { if (s > 0) printf "$%.2f", s }'
'''
shell = ['sh', '-c']
description = "Today's AI spend"
symbol = '🧠 '
style = 'fg:#ff9f43'
format = ' [$symbol$output]($style)'
```

## GPU temp and VRAM

NVIDIA only; gated on `nvidia-smi` presence.

```toml
[custom.gpu]
command = '''
  nvidia-smi --query-gpu=temperature.gpu,memory.used,memory.total \
    --format=csv,noheader,nounits 2>/dev/null \
    | awk -F', ' 'NR==1 { printf "%d°C %d/%dMB", $1, $2, $3 }'
'''
when = 'command -v nvidia-smi >/dev/null'
shell = ['sh', '-c']
description = 'GPU temp / VRAM'
symbol = '🖳 '
style = 'fg:#76b900'
format = ' [$symbol$output]($style)'
```

## Battery low warning

Linux UPower-style. Only renders below 20% on battery.

```toml
[custom.battery_low]
command = '''
  state=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null)
  pct=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null)
  [ "$state" = "Discharging" ] && [ "${pct:-100}" -lt 20 ] && echo "${pct}%"
'''
when = 'test -d /sys/class/power_supply/BAT0'
shell = ['sh', '-c']
os = 'linux'
description = 'Battery low warning'
symbol = '🪫 '
style = 'bold red'
format = ' [$symbol$output]($style)'
```

## Last build status

Reads a status file written by your CI runner / git hook.

```toml
[custom.build_status]
command = '''
  s=$(cat .build-status 2>/dev/null) || exit 0
  case "$s" in
    pass) echo "✓" ;;
    fail) echo "✗" ;;
    running) echo "…" ;;
    *) ;;
  esac
'''
detect_files = ['.build-status']
shell = ['sh', '-c']
description = 'Last build status marker'
style = 'bold'
format = ' [$output]($style)'
```

## Pending PR count

GitHub `gh` CLI; cached for 5 minutes to keep the prompt fast.

```toml
[custom.gh_prs]
command = '''
  cache="$HOME/.cache/starship-gh-prs"
  mkdir -p "$(dirname "$cache")"
  if [ ! -f "$cache" ] || [ "$(find "$cache" -mmin +5)" ]; then
    gh pr status --json number --jq '. | length' 2>/dev/null > "$cache" || echo 0 > "$cache"
  fi
  c=$(cat "$cache")
  [ "${c:-0}" -gt 0 ] && echo "$c"
'''
require_repo = true
when = 'command -v gh >/dev/null'
shell = ['sh', '-c']
description = 'Open PR count for current repo'
symbol = ' '
style = 'bold magenta'
format = ' [$symbol$output]($style)'
```

## Failing tests counter

Reads jest/pytest junit-xml summary file written by your test runner.

```toml
[custom.failing_tests]
command = '''
  f=$(find . -maxdepth 3 -name 'junit*.xml' -newer /tmp 2>/dev/null | head -1)
  [ -z "$f" ] && exit 0
  failures=$(grep -oE 'failures="[0-9]+"' "$f" | head -1 | grep -oE '[0-9]+')
  [ "${failures:-0}" -gt 0 ] && echo "$failures"
'''
require_repo = true
shell = ['sh', '-c']
description = 'Failing tests from latest junit'
symbol = '✗'
style = 'bold red'
format = ' [$symbol $output]($style)'
```

## Random kaomoji

Pure delight. No-op outside of vibes.

```toml
[custom.kaomoji]
command = '''
  set -- "(╯°□°)╯︵ ┻━┻" "ʕ•ᴥ•ʔ" "(ノ◕ヮ◕)ノ" "(づ｡◕‿‿◕｡)づ" "¯\_(ツ)_/¯" "(◉◡◉)"
  shift $(( $(date +%S) % $# ))
  echo "$1"
'''
when = 'true'
shell = ['sh', '-c']
description = 'Random kaomoji per second'
style = 'dimmed'
format = ' [$output]($style)'
```

## Cat fact rotator

Rotates a fact every prompt from a local file. (Falls back silently if file missing.)

```toml
[custom.catfact]
command = '''
  f="$HOME/.cache/catfacts.txt"
  [ -f "$f" ] || exit 0
  awk -v n="$RANDOM" 'BEGIN { srand(n) } { lines[NR]=$0 } END { print lines[int(rand()*NR)+1] }' "$f"
'''
when = 'test -f "$HOME/.cache/catfacts.txt"'
shell = ['sh', '-c']
description = 'Random cat fact'
symbol = '🐈 '
style = 'dimmed italic'
format = ' [$symbol$output]($style)'
```

---

## Patterns Across Recipes

Reusable techniques worth lifting into your own recipes:

1. **Cache files for slow commands.** Pattern: write to `~/.cache/starship-<name>`, refresh based on `find -mmin +N`. Used in [Weather](#weather-glyph), [Pending PR count](#pending-pr-count).
2. **Hide on zero.** Pattern: `[ "${count:-0}" -gt 0 ] && echo "$count"`. Custom modules render only on non-empty `$output`. Used in [Mail](#unread-mail-count), [Branch staleness](#branch-staleness-vs-main), [Failing tests](#failing-tests-counter).
3. **Compound triggers.** Combine `detect_files` + `when` + `require_repo` so the module only runs when worth running. The cheapest gate (`detect_files`) runs first.
4. **`exit 0` to mean "render nothing".** Empty stdout with `exit 0` hides the module without erroring.
5. **`command -v` guards.** Always gate on tool presence (`when = 'command -v foo >/dev/null'`) so the module degrades silently on machines without the tool.
6. **OS gating.** Use `os = 'linux'` / `'macos'` for platform-specific recipes rather than `uname` checks inside `when` — it's faster and clearer.
