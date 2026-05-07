# Gotchas

Failure modes specific to `[custom.<name>]` modules. Match the symptom name to your live behavior, then apply the solution.

## Index

| Symptom | Section |
|---|---|
| Shell hangs, prompt unresponsive, fork bomb | [Shell recursion via re-entrant starship](#shell-recursion-via-re-entrant-starship) |
| Prompt feels sluggish | [Per-prompt latency cliff](#per-prompt-latency-cliff) |
| Module silently doesn't render | [Display conditions not met](#display-conditions-not-met) |
| Module shows but `$output` is empty/garbled | [Stdin vs argv shell mismatch](#stdin-vs-argv-shell-mismatch) |
| Output has weird characters or breaks colors | [Escaping and prompt-meaningful chars](#escaping-and-prompt-meaningful-chars) |
| `when = "true"` (a literal string) shows even when wrong | [when boolean vs string confusion](#when-boolean-vs-string-confusion) |
| Module renders in wrong place in prompt | [Custom module placement order](#custom-module-placement-order) |
| `format` produces extra spaces or no spaces | [Format string conditional groups](#format-string-conditional-groups) |
| Renders on Linux dev box but not in container | [OS gating and tool absence](#os-gating-and-tool-absence) |
| Caches go stale or never refresh | [Cache file mtime traps](#cache-file-mtime-traps) |

---

### "Shell recursion via re-entrant starship"

**Symptom:** Terminal hangs after enabling a custom module, often pegging a CPU; new shells take many seconds to start; sometimes a fork-bomb-like cascade.
**Cause:** `shell` is unset (or only the binary is given), so starship hands the command to a login/interactive shell that re-loads the user's profile (`.zshrc`, `.bashrc`, `$PROFILE`). That profile re-invokes `starship init`, which re-renders the prompt, which re-runs the custom command — infinite recursion.
**Solution:** Always pin `shell` with non-interactive flags. Use `['sh', '-c']` for POSIX, `['bash', '--noprofile', '--norc', '-c']` for bash, `['pwsh', '-NoProfile', '-Command', '-']` for PowerShell.

```toml
# ❌ BAD: implicit shell selection inherits user profile
[custom.foo]
command = 'echo hi'

# ❌ BAD: bash without no-profile flags
[custom.foo]
command = 'echo hi'
shell = ['bash']

# ✅ GOOD: explicit, non-interactive shell
[custom.foo]
command = 'echo hi'
shell = ['sh', '-c']
```

---

### "Per-prompt latency cliff"

**Symptom:** The prompt visibly lags after each command. `starship timings` reports the custom module taking >100ms.
**Cause:** The command performs network I/O, spawns expensive subprocesses, or reads large files on every prompt render. Even at 100ms, a typing user notices.
**Solution:** Cache to a file with mtime-based refresh, gate behind cheap `detect_*` triggers, or move the work to a background daemon that writes a status file the module just `cat`s.

```toml
# ❌ BAD: live network call on every prompt
[custom.weather]
command = 'curl -s wttr.in?format=%c%t'
shell = ['sh', '-c']

# ✅ GOOD: cache file with 1-hour refresh
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
```

Use `starship timings` to surface the offender. Anything >50ms is a candidate for caching or removal.

---

### "Display conditions not met"

**Symptom:** Module is configured, `starship explain` lists it, but it never appears in the prompt. `starship module <name>` prints nothing.
**Cause:** None of `detect_files`, `detect_folders`, `detect_extensions`, `when` (when true / exit-0), or `os` are matching the current context. With no display conditions set, the module always runs — but with at least one set, *only* matching conditions trigger it.
**Solution:** `cd` into a directory that should match and run `starship module <name>`. Inspect the actual triggers; remember `detect_*` are matched against the *cwd only*, not recursively. If you want recursive matching, use `when` with `find`.

```toml
# ❌ BAD: detect_files only matches files in cwd, not anywhere in repo
[custom.terraform]
command = 'echo tf'
detect_files = ['main.tf']    # misses subdirectories

# ✅ GOOD: detect_extensions catches *.tf anywhere in cwd; or use when for recursion
[custom.terraform]
command = 'echo tf'
detect_extensions = ['tf', 'tfvars']

# ✅ ALSO GOOD: explicit recursive search via when
[custom.terraform]
command = 'echo tf'
when = 'find . -maxdepth 3 -name "*.tf" -print -quit | grep -q .'
shell = ['sh', '-c']
```

---

### "Stdin vs argv shell mismatch"

**Symptom:** Module shows but `$output` is empty, garbled, or contains shell prompt fragments.
**Cause:** `command` is sent to the shell on stdin by default. Some shells (cmd, nushell) don't read commands from stdin and need them as argv. Conversely, when `shell` is given as a single element, starship tries to auto-add stdin/argv flags — getting it wrong silently.
**Solution:** Set `use_stdin` explicitly when in doubt. For nushell and cmd, use `use_stdin = false` and pass the command via the right flag.

```toml
# ❌ BAD: nushell with stdin (the default)
[custom.foo]
command = 'echo hi'
shell = ['nu']

# ✅ GOOD: nushell with -c and stdin disabled
[custom.foo]
command = 'echo hi'
shell = ['nu', '-c']
use_stdin = false

# ❌ BAD: PowerShell single-element shell — auto-flags may differ across versions
[custom.foo]
command = 'Write-Output hi'
shell = ['pwsh']

# ✅ GOOD: explicit flags
[custom.foo]
command = 'Write-Output hi'
shell = ['pwsh', '-NoProfile', '-Command', '-']
```

---

### "Escaping and prompt-meaningful chars"

**Symptom:** Output contains literal `\h`, `\u`, ANSI codes, or backticks; colors break for the rest of the prompt; previous-command output bleeds.
**Cause:** Prior to starship 1.20, output was unescaped. From 1.20+, output is escaped by default. If `unsafe_no_escape = true` is set, prompt-meaningful sequences in `$output` (bash `\h`, zsh `%n`, ANSI escapes, backticks in bash) are interpreted literally — sometimes with arbitrary code execution risk.
**Solution:** Leave `unsafe_no_escape = false` (the default). Only set it true if you're emitting deliberate prompt escape sequences and you fully trust the command output. For ANSI colors in output, prefer `style` and `format` — let starship apply colors, don't emit raw escapes.

```toml
# ❌ BAD: emitting raw ANSI from the command, with unsafe_no_escape
[custom.dangerous]
command = 'printf "\033[31mRED\033[0m"'
unsafe_no_escape = true
shell = ['sh', '-c']

# ✅ GOOD: plain output, color via style
[custom.safe]
command = 'echo RED'
style = 'bold red'
format = '[$output]($style)'
shell = ['sh', '-c']
```

---

### "when boolean vs string confusion"

**Symptom:** Module renders unconditionally despite a guard, or never renders despite a true-looking condition.
**Cause:** `when` accepts either a boolean (`true` / `false`, no quotes) OR a string shell command. `when = "true"` and `when = "false"` are *strings* — they invoke `/bin/sh -c "true"` (always exit 0, always show) or `/bin/sh -c "false"` (always exit non-zero, never show). They look like booleans but aren't.
**Solution:** Use unquoted `when = true` for "always show", unquoted `when = false` for "never show", and quoted strings only when the body is an actual command.

```toml
# ❌ AMBIGUOUS: looks like boolean but is a shell command (works by accident)
[custom.foo]
when = "true"

# ✅ GOOD: actual boolean
[custom.foo]
when = true

# ✅ GOOD: actual command
[custom.foo]
when = 'test -n "$AWS_PROFILE"'
shell = ['sh', '-c']
```

---

### "Custom module placement order"

**Symptom:** Custom modules render at the end of the prompt or in declaration order, but you wanted one in the middle and another at the right.
**Cause:** Without an explicit `${custom.<name>}` reference in the global `format`, all custom modules render at `$custom`, in declaration order.
**Solution:** Use `${custom.<name>}` in the global `format` to place a module exactly. Curly braces are required because of the dot.

```toml
# ❌ BAD: both modules render at the end, in declaration order
format = """
$directory $git_branch $character"""
[custom.k8s]
# ...
[custom.aws]
# ...

# ✅ GOOD: explicit placement
format = """
$directory${custom.k8s} $git_branch ${custom.aws}$character"""
[custom.k8s]
# ...
[custom.aws]
# ...
```

If you reference some custom modules explicitly and leave others implicit, the unreferenced ones still render at `$custom` (or at end-of-format if `$custom` is omitted).

---

### "Format string conditional groups"

**Symptom:** Extra leading/trailing spaces, missing separators, or symbols rendering even when output is empty.
**Cause:** Format strings have two grouping forms: square brackets `[...]` for style application and parentheses `(...)` for conditional rendering. A `(...)` group is rendered only if every variable inside resolves non-empty.
**Solution:** Wrap optional content in `(...)`. Put `$symbol` inside a `(...)` group with `$output` if you want the symbol to disappear when output is empty. Place spaces inside the conditional group, not outside.

```toml
# ❌ BAD: leading space appears even when output is empty
format = ' [$symbol$output]($style)'

# ✅ GOOD: leading space only when output is present
format = '[ $symbol$output]($style)'   # space inside the style bracket
format = '($symbol $output )'           # whole group conditional on $output

# ❌ BAD: symbol shows even when output is empty
format = '[$symbol $output]($style)'

# ✅ GOOD: symbol gated on output
format = '[($symbol )$output]($style)'
```

The starship docs' "Style Strings" and "Conditional Format Strings" sections cover the full grammar.

---

### "OS gating and tool absence"

**Symptom:** Module works on the author's machine, breaks elsewhere with cryptic shell errors, or hangs in containers without the required tool.
**Cause:** Custom commands assume tools (`jq`, `gh`, `playerctl`, `nvidia-smi`) that aren't universally present. When the tool is missing, the shell prints "command not found" to stderr and the prompt may render the empty stdout.
**Solution:** Gate on `command -v <tool> >/dev/null` in `when`. Use `os = 'linux'` / `'macos'` for OS-specific recipes. Suppress stderr inside the command (`2>/dev/null`) so the user never sees "command not found" flashes.

```toml
# ❌ BAD: assumes jq exists
[custom.tailscale]
command = 'tailscale status --json | jq -r ".Self.HostName"'
shell = ['sh', '-c']

# ✅ GOOD: gates on both tools, suppresses stderr
[custom.tailscale]
command = 'tailscale status --json 2>/dev/null | jq -r ".Self.HostName // empty"'
when = 'command -v tailscale >/dev/null && command -v jq >/dev/null'
shell = ['sh', '-c']
```

---

### "Cache file mtime traps"

**Symptom:** Cached module never refreshes, or refreshes on every prompt anyway, or breaks the first time it runs.
**Cause:** `find -mmin +N` returns nothing if the file doesn't exist, so the refresh branch is correctly taken on first run *only if* you also handle the missing-file case. Race conditions on concurrent prompts can corrupt the cache file.
**Solution:** Combine `[ ! -f "$cache" ] || [ "$(find ... -mmin +N)" ]`. Write to a temp file and `mv` for atomic refresh. Always `mkdir -p` the cache dir before writing.

```toml
# ❌ BAD: first run never refreshes (find returns empty for missing file)
[custom.thing]
command = '''
  cache="$HOME/.cache/thing"
  if [ "$(find "$cache" -mmin +60)" ]; then
    slow-call > "$cache"
  fi
  cat "$cache"
'''

# ✅ GOOD: handles missing-file case, atomic write, suppresses errors
[custom.thing]
command = '''
  cache="$HOME/.cache/thing"
  mkdir -p "$(dirname "$cache")"
  if [ ! -f "$cache" ] || [ "$(find "$cache" -mmin +60)" ]; then
    tmp=$(mktemp) && slow-call > "$tmp" 2>/dev/null && mv "$tmp" "$cache" || rm -f "$tmp"
  fi
  cat "$cache" 2>/dev/null
'''
shell = ['sh', '-c']
```

---

## Debugging Workflow

When a custom module misbehaves, work this sequence:

1. `starship explain` — confirms the module is registered with the expected config.
2. `starship module <name>` — runs only this module against current cwd.
3. `starship timings` — surfaces slow modules; sort by duration.
4. `STARSHIP_LOG=trace starship prompt 2>&1 | tail -100` — exposes trigger evaluation, command execution, output capture.
5. Run the `command` directly in the same shell starship would use: `sh -c '<your command>'`. If the output differs from the prompt, the difference is in escape handling or shell auto-detection.

`starship timings` is the most underused tool — run it whenever the prompt feels slow.
