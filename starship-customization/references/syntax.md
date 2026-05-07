# Custom Module Syntax Reference

Distilled from https://starship.rs/config/#custom-commands. Use this file as the canonical option list when authoring or reviewing a `[custom.<name>]` block. The starship docs themselves are the source of truth if anything diverges.

## Block Form

```toml
[custom.<name>]
# options below
```

`<name>` is an arbitrary identifier. You may declare any number of custom modules. They render in declaration order at the `$custom` placeholder of the global `format` string, unless individually placed via `${custom.<name>}` in the global `format`.

## Display Conditions

A custom module renders only if **at least one** of the following is true:

- A file in cwd matches `detect_files`
- A folder in cwd matches `detect_folders`
- A file in cwd has an extension in `detect_extensions`
- The shell command in `when` exits with status 0
- The current OS matches `os`

If none of `detect_*`, `when`, or `os` are set, the module always renders.

`require_repo = true` is an *additional* gate (AND with the above): the module only renders inside a git repo. It is not sufficient on its own.

## Options

| Option | Type | Default | Purpose |
|---|---|---|---|
| `command` | string | `''` | Shell command whose stdout becomes `$output`. Passed on stdin to `shell` by default. |
| `when` | bool or string | `false` | `true` always shows; `false` never shows; a string is a shell command — exit 0 means show. |
| `require_repo` | bool | `false` | Gate on being inside a git repo. AND with other display conditions. |
| `shell` | list of strings | unset | Shell to execute `command` (and `when`, if string). See Shell Selection below. |
| `description` | string | `'<custom module>'` | Shown by `starship explain`. |
| `unsafe_no_escape` | bool | `false` | When false, prompt-meaningful chars in `$output` are escaped. Leave false unless you emit deliberate prompt escapes. |
| `detect_files` | list of strings | `[]` | File names to look for in cwd. |
| `detect_folders` | list of strings | `[]` | Folder names to look for in cwd. |
| `detect_extensions` | list of strings | `[]` | File extensions to look for in cwd. |
| `symbol` | string | `''` | Rendered as `$symbol` inside `format`. |
| `style` | string | `'bold green'` | Style applied via `($style)` in `format`. |
| `format` | string | `'[$symbol($output )]($style)'` | Layout of the rendered segment. |
| `disabled` | bool | `false` | Hard-disable the module without removing the block. |
| `os` | string | unset | Render only on this OS. Values: `linux`, `macos`, `windows`, `unix`, `freebsd`, `dragonfly`, `netbsd`, `openbsd`, `solaris`, `android`, `ios`. |
| `use_stdin` | bool | shell-dependent | If unset, command goes to shell stdin (default for sh/bash/zsh/pwsh) or as arg (cmd, nushell). Setting it explicitly disables shell auto-arg handling. |
| `ignore_timeout` | bool | `false` | Bypass global `command_timeout`. Use only when blocking the prompt is acceptable. |

## Variables

Available inside `format`:

| Variable | Meaning |
|---|---|
| `$output` | stdout of `command` (trailing newline stripped) |
| `$symbol` | mirrors the `symbol` option |
| `$style` | only valid inside a `($style)` style group, mirrors `style` |

## Shell Selection

`shell` is a non-empty list:
- First element: path to the interpreter.
- Remaining elements: arguments passed to the interpreter.

Auto-detection (when `shell` is unset or has only one element):
- Detected PowerShell → appends `-NoProfile -Command -`
- Detected Cmd → appends `/C` and forces `use_stdin = false`
- Detected Nushell → appends `-c` and forces `use_stdin = false`
- Otherwise → falls back to `$STARSHIP_SHELL`, then `sh` on Linux/macOS, `cmd /C` on Windows

**Always pin `shell` explicitly.** Recommended defaults:

```toml
shell = ['sh', '-c']                                 # POSIX, fastest, portable
shell = ['bash', '--noprofile', '--norc', '-c']      # bashisms only, skip user dotfiles
shell = ['pwsh', '-NoProfile', '-Command', '-']      # PowerShell Core
shell = ['nu', '-c']                                 # Nushell
```

The `--noprofile --norc` (bash) and `-NoProfile` (pwsh) flags are critical: they prevent the shell from re-loading the user's interactive profile (which may itself invoke starship), avoiding both prompt latency and recursion.

## Format String Rules

`format` is a starship format string. Key elements:

- `[text]($style)` — apply style to `text`.
- `($x )` — conditional group: rendered only if every variable inside `x` resolves non-empty.
- `$variable` — variable interpolation. Use `${custom.foo}` in the *global* `format` to place a custom module by name.
- Literals outside style groups appear as-is (good for separators, brackets, glyphs).

Example variations:

```toml
format = '[$symbol $output]($style) '         # symbol + space + output, trailing space
format = 'on [$output]($style) '              # literal "on " prefix
format = '[($symbol)$output]($style)'         # symbol omitted if unset, no spaces
format = '[\[$output\]]($style) '             # bracketed output, escaped brackets
```

## Top-Level Placement

Two options control where custom modules appear in the prompt:

1. **Default**: leave `$custom` in the global `format`. All custom modules render in declaration order at that point.
2. **Explicit**: reference `${custom.<name>}` directly in the global `format` (curly braces required because of the dot). Each named custom module is placed at its reference; remaining unreferenced custom modules still render at `$custom`.

```toml
# ~/.config/starship.toml
format = """
$directory${custom.k8s_helm}\
$git_branch$git_status\
$character"""

[custom.k8s_helm]
command = 'kubectl config current-context'
detect_folders = ['helm', 'charts']
shell = ['sh', '-c']
format = ' on [⎈ $output]($style)'
style = 'bold purple'
```

## Minimal Working Example

```toml
[custom.greeting]
command = 'echo hi'
when = 'true'
shell = ['sh', '-c']
format = '[$output]($style) '
style = 'bold yellow'
```

This always renders `hi ` in bold yellow. Use it as a sanity-check that a custom module is registered and `starship module greeting` prints output.

## Disabling Default Custom Behavior

If you want to silence all custom modules without removing them:

```toml
[custom]
disabled = true
```

This is the table-level disable for the entire custom group. Individual `[custom.<name>]` blocks can also set `disabled = true`.
