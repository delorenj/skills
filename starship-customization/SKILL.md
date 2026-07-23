---
name: starship-customization
description: Author custom starship prompt modules ([custom.NAME] blocks in starship.toml) for outside-the-box prompt segments beyond starship's built-in modules. Use when adding a custom prompt segment that runs a shell command, conditionally appears in specific dirs, or surfaces git/env/API/file state. Covers detect_files, detect_folders, detect_extensions, when conditions, shell selection (sh/bash/zsh/pwsh/nushell), require_repo, format/style strings, and a recipe cookbook (k8s context in helm dirs, AWS profile, weather, AI usage cost, now-playing, build status, branch staleness, Tailscale, package.json scripts, deployment env). Triggers on "starship custom module", "custom starship prompt", "starship.toml [custom.", "make my prompt show X", "outside-the-box prompt segment", "creative starship module". Do NOT use for built-in starship module config (see starship.rs/config), powerlevel10k / oh-my-zsh / pure / spaceship, generic shell config, or starship install.
---

# Starship Customization

Author `[custom.<name>]` blocks in `starship.toml` that surface arbitrary state in the prompt. Optimized for novel ideas the built-in modules don't cover.

## Operating Principles

1. **Performance is the first constraint.** Every custom module runs synchronously on every prompt render. A 200ms command makes the shell feel broken. Aim for <50ms; cache or short-circuit otherwise.
2. **Trigger before compute.** Use `detect_files` / `detect_folders` / `detect_extensions` / `os` / `require_repo` to skip the module entirely outside its relevant context. Only fall back to `when = "<cmd>"` when filesystem triggers are insufficient.
3. **Pin the shell.** Default shell selection is fragile across machines. Always set `shell = ['sh', '-c']` (or `['bash', '--noprofile', '--norc', '-c']` if bashisms are needed) to stop starship from inheriting heavy user profiles and to prevent recursion.
4. **Boring before clever.** A reliable two-line `[custom.foo]` beats a witty one-liner that breaks on macOS or in fish. If a recipe needs `awk`/`sed`/`jq`, gate it on `command -v`.
5. **The agent must produce a runnable TOML block, not pseudo-config.** Output a complete `[custom.<name>]` block the user can paste into `~/.config/starship.toml`.

## Quick Navigation

| Your situation | Read |
|---|---|
| Need the option list, defaults, and variable reference | [references/syntax.md](./references/syntax.md) |
| User has a creative idea, want a worked example to adapt | [references/recipes.md](./references/recipes.md) |
| Module silently doesn't appear, hangs, double-renders, or breaks the shell | [references/gotchas.md](./references/gotchas.md) |
| Verify generated TOML before handing it to the user | Run `starship explain` and `starship module <name>` (see Verification below) |

## Workflow

For any "make my prompt show X" request:

1. **Clarify the trigger surface.** Ask once if it isn't obvious: "Should this segment appear always, only inside a git repo, only when a specific file is present, or only on certain OSes?" Map the answer onto:
   - File present → `detect_files = ['Pipfile', 'pyproject.toml']`
   - Folder present → `detect_folders = ['.terraform', 'helm']`
   - Extension present → `detect_extensions = ['tf', 'tfvars']`
   - Git repo only → `require_repo = true`
   - OS-gated → `os = 'linux'` (or `'macos'`, `'windows'`, `'unix'`)
   - Custom logic → `when = "test -n \"$KUBECONFIG\""`
2. **Pick the cheapest command that yields the value.** Prefer reading env vars or files over spawning subprocesses. Examples:
   - `command = 'echo "$AWS_PROFILE"'` is free.
   - `command = 'aws sts get-caller-identity --query Account --output text'` is a network call — wrap in cache or skip.
3. **Pin the shell.** Always include `shell = ['sh', '-c']` (POSIX-portable) unless a specific shell feature is needed. See [references/gotchas.md](./references/gotchas.md) for the recursion failure mode if shell is left unset.
4. **Format and style.** Default format is `'[$symbol($output )]($style)'`. Customize for spacing/separators. Style strings accept color names, `bold`, `dimmed`, `bg:`, hex (`#a4ffea`), and palette references (`fg:my_color`).
5. **Write a complete TOML block** including a brief comment explaining what it shows and the trigger condition. Hand the user the path (`~/.config/starship.toml`) and the block.
6. **Verify.** Tell the user to run `starship explain` and `starship module <name>` to confirm the module is registered and produces output. If they're piping output through, also test `starship prompt` end-to-end.

## Custom Module Skeleton

```toml
# ~/.config/starship.toml
[custom.<name>]
command = '<shell command producing the segment text on stdout>'
shell = ['sh', '-c']
description = '<one-line description shown by `starship explain`>'

# Trigger (at least one is usually needed; otherwise the module always runs):
detect_files = []
detect_folders = []
detect_extensions = []
when = ''            # boolean true/false, or shell command (exit 0 = show)
require_repo = false
os = ''              # 'linux' | 'macos' | 'windows' | 'unix' | omit

# Presentation:
symbol = ''
style = 'bold cyan'
format = '[$symbol($output )]($style)'

# Performance / safety:
ignore_timeout = false   # true only if you accept blocking the prompt
unsafe_no_escape = false # leave false unless you're emitting prompt escapes deliberately
```

To register the module in a custom top-level prompt order, reference it as `${custom.<name>}` in the global `format =` string. Without that, starship appends all custom modules in declaration order at the `$custom` placeholder.

## Example: BMAD version and update indicator

Shows the installed BMAD core version when you're inside a BMAD project (it walks up the directory tree looking for `_bmad/`). Compares the installed version against the latest `bmad-method` release on npm, cached for one hour.

```toml
[custom.bmad]
command = '''
  dir="$PWD"
  while [ "$dir" != "/" ]; do
    [ -d "$dir/_bmad" ] && break
    dir=$(dirname "$dir")
  done
  [ "$dir" = "/" ] && exit 0

  installed=$(sed -n 's/^# Version: *//p' "$dir/_bmad/core/config.yaml" 2>/dev/null | head -n1)
  [ -z "$installed" ] && installed=$(sed -n 's/^version: *//p' "$dir/_bmad/config.yaml" 2>/dev/null | head -n1)
  [ -z "$installed" ] && exit 0

  cache="$HOME/.cache/starship-bmad-latest"
  mkdir -p "$(dirname "$cache")"
  if [ ! -f "$cache" ] || [ "$(find "$cache" -mmin +60)" ]; then
    tmp=$(mktemp) && npm view bmad-method version 2>/dev/null > "$tmp" && mv "$tmp" "$cache" || rm -f "$tmp"
  fi

  latest=$(cat "$cache" 2>/dev/null)
  if [ -z "$latest" ]; then
    echo "v$installed"
  else
    highest=$(printf '%s\n%s\n' "$installed" "$latest" | sort -V | tail -n1)
    if [ "$installed" = "$latest" ] || [ "$installed" = "$highest" ]; then
      echo "v$installed ✓"
    else
      echo "v$installed ↑$latest"
    fi
  fi
'''
when = true
shell = ['sh']
description = 'BMAD version and update indicator'
symbol = '🧠'
style = 'bold cyan'
format = ' [$symbol $output]($style)'
```

`shell = ['sh']` keeps the multi-line command readable by feeding it to `sh` on stdin; `when = true` lets the command itself decide whether `_bmad` is present. To keep the segment on the same line as your directory/git info, place `${custom.bmad}` *before* `$all` in your global `format` (e.g. `format = "$directory$git_branch$git_status ${custom.bmad}$all$character"`). See [references/recipes.md](./references/recipes.md#bmad-version-and-update-indicator) for more adaptation notes.

## Verification

After writing or editing a `[custom.<name>]` block:

```bash
starship explain                  # lists every active module and its config source
starship module <name>            # renders just this module's output
starship timings                  # surfaces slow modules; flag anything >50ms
STARSHIP_LOG=trace starship prompt 2>&1 | tail -50   # debug missing modules
```

If `starship module` prints nothing, the trigger conditions failed. Re-check `detect_*` and `when` against the actual cwd. If the module hangs the shell, suspect shell recursion — see gotchas.

## Out of Scope

- **Configuring built-in modules** (`[git_branch]`, `[python]`, `[character]`, palettes, etc.). Built-in module configuration is exhaustively covered by https://starship.rs/config; this skill is exclusively about `[custom.<name>]`. If the user asks to "make python show venv name", that's the built-in `python` module, not a custom one.
- **Starship installation, init lines for shells, or shell integration.** Defer to https://starship.rs/installing/.
- **Other prompt frameworks**: powerlevel10k, oh-my-zsh themes, pure, spaceship, fish-tide, lambda. Different config surface entirely.
- **Generic shell config** (aliases, functions, completions). Prompt-only.
- **Statusline tools that aren't starship** (tmux status, vim airline, Claude Code statusline-via-starship is a special case covered loosely in starship advanced docs but is not the focus here).
- **TransientPrompt, right-prompt, continuation prompt** — these are advanced starship features adjacent to custom modules. If the user is asking for a custom module *to be placed in* the right prompt, the custom module half is in-scope; the right-prompt enablement is a one-liner referencing starship's advanced docs.
