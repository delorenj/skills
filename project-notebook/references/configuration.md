# Project Notebook configuration

## Public commands

```text
pj notebook status [repo] [--local-only] [--json]
pj notebook create [repo] --live [--json]
pj notebook list notes [repo] [--limit N] [--cursor VALUE] [--json]
pj notebook add note [repo] --title TEXT (--text TEXT | --file PATH) [--json]
pj notebook get note NOTE_ID [repo] [--json]
pj notebook update note NOTE_ID [repo] [--title TEXT] (--text TEXT | --file PATH) [--json]
pj notebook delete note NOTE_ID [repo] [--yes] [--json]
pj notebook search notes QUERY [repo] [--limit N] [--json]
pj notebook overview [repo] [--set-file PATH] [--json]
pj notebook capture list [repo] [--state VALUE] [--json]
pj notebook capture retry RECEIPT_ID [repo] [--baseline GIT_REF] [--json]
pj notebook audit [repo] [--local-only] [--json]
pj notebook migrate [repo] [--apply] [--live] [--json]
```

The `hook` and `worker` command families are internal compatibility surfaces.
Do not invoke them for ordinary notebook work.

## Policy and credentials

Effective policy precedence is built-in safe defaults, global Project Registry
defaults, Project Manifest policy, then an explicit option for one invocation.
An explicit disable wins for hook behavior.

The Project Registry owns binding identifiers and binding state. The Project
Manifest mirrors binding fields for inspection and owns repository policy. It
must not contain a service URL, credential, or derived authentication value.
Resolve endpoint and authentication at runtime through PJangler's configured
secret boundary. Never put user content or secrets in argv or logs.

## Canonical Claude projection

Run the projector from this skill directory:

```text
python3 scripts/project-hooks.py check [--target PATH] [--json]
python3 scripts/project-hooks.py render
python3 scripts/project-hooks.py install [--target PATH]
python3 scripts/project-hooks.py uninstall [--target PATH]
```

The default target is `~/.claude/settings.json`; tests and packaged installers
may supply an isolated absolute target. `render` deterministically derives
`hooks/claude.settings.json` from `hooks/hooks.master.json`. `check` is
read-only. Install and uninstall take the Project Notebook advisory lock,
re-read live settings while locked, snapshot the exact preimage, and replace
the target only when owned semantics change. Directory traversal, private-state
creation, lock/snapshot access, temporary-file creation, and atomic replacement
are descriptor-relative with `O_DIRECTORY|O_NOFOLLOW`; an ancestor pathname
swap cannot redirect a write outside the directory already opened.

The only owned commands are an anchored `PJ_HOOK_OWNER=project-notebook.v1 `
prefix followed by exactly one recognized wrapper path for the same event:

```text
SessionStart  "$HOME/.agents/skills/project-notebook/hooks/session-start.sh"  timeout 3
SessionEnd    "$HOME/.agents/skills/project-notebook/hooks/session-end.sh"    timeout 1
```

`Stop` is not a session-close event and is always foreign. Prefix-similar,
unknown-wrapper, extra-argument, and event-mismatched commands are preserved
and reported rather than claimed.

Despite their stable `.sh` filenames, the wrappers are isolated
`/usr/bin/python3 -I` launchers. They derive the canonical user home from the
passwd database, then use only `<canonical-home>/.local/bin/pj`. Intermediate
launcher-parent symlinks are rejected. The launcher itself may be a symlink,
but its resolved absolute target and every target-path component must be owned
by the current user's primary user/group, must not be world-writable or carry
special mode bits, and the target must be a regular executable file. Private
primary-group write is accepted only when passwd and group enumeration proves
that no other group member or primary user can write through that group.

The resolved launcher is executed as an argument to fixed `/usr/bin/node`, not
through its shebang or inherited `PATH`. The child environment contains only
canonical `HOME`, `USER`, and `LOGNAME`; fixed `PATH` and locale values; and, if
present, `OPEN_NOTEBOOK_PASSWORD`. Unattended hooks do not forward an arbitrary
registry `auth.env_var`; configure this exact allowlisted variable for hook
authentication or use an interactive/public command path. Inputs such as
`BASH_ENV`, `NODE_OPTIONS`, `NODE_PATH`, and project-controlled environment
variables cannot redirect or preload the child.

Hook JSON is never staged to disk. Each wrapper reads at most 1,048,577 bytes;
if the sentinel byte is present, it fails open before creating a child because
the 1,048,576-byte request ceiling was exceeded. Valid-size input is sent over
stdin with an explicit child timeout shorter than the outer hook timeout.
Resolution, validation, input, timeout, and PJangler failures are bounded and
fail open without creating wrapper-local state.
