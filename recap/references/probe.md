# The differential probe

*What can I do now that I couldn't before* is two halves, and **"before" is the hard half.** It is also
mechanically derivable: ask the software what it could do at the base of the window, ask HEAD the same
question, and diff the answers.

This is the **primary** capability source. Prose mining — commit bodies, CHANGELOG, task descriptions —
is corroboration only, because prose an agent already wrote in capability-first register is circular,
and because it is not portable. Measured over 60 repos on this machine:

| signal | repos with it |
|---|---|
| `justfile` | **0** |
| `Makefile` | 1 (a vendored clone) |
| `mise.toml` with any tasks | ~15 |
| user-authored `CHANGELOG` | ~4 |
| median commit body ≥ 500 bytes | 3 of 10 sampled — two of them the repos this skill was designed in |

A design that leans on prose answers the user's question in a quarter of his projects and produces a
prettier commit log in the rest.

## Set up the boundary

Cheapest first. A worktree only when you must execute base code.

```bash
git show "$BASE:path/to/file"                 # read a file as it was — no checkout
git worktree add /tmp/recap-base "$BASE"      # when you must RUN the old code
# ... probe ...
git worktree remove /tmp/recap-base --force
```

The worktree is disposable and must be removed — this shop's hard rule is that nothing is left in a
worktree. Never probe by checking out over the user's working tree.

## Probes, by what the thing is

Run the ones that apply. Each yields before/after pairs in exactly the shape a capability card needs.

### A CLI

The highest-yield probe there is.

```bash
diff <(cd /tmp/recap-base && <cmd> --help 2>&1) <(<cmd> --help 2>&1)
```

New subcommands, new flags, changed defaults and removed options fall straight out. Recurse one level
into subcommands that changed. If the CLI needs a build, build both sides or say you could not.

Guard: running base code executes code the user may not have reviewed. Use `--help`/`--version` only,
never a subcommand with side effects.

### A library

Exported surface, base vs HEAD:

- **Python** — top-level `def`/`class`, and `__all__` if present
- **TypeScript / JS** — `export` statements, or the built `.d.ts`
- **Rust** — `pub fn`, `pub struct`, `pub trait`
- **Go** — exported (capitalised) identifiers
- **C/C++** — public headers

```bash
diff <(git show "$BASE:src/index.ts" | grep -E '^export ') <(grep -E '^export ' src/index.ts)
```

A new export is a new capability *for the importer*, and the invocation is the import line.

### A service

- **Routes** — decorators (`@app.get`, `@router.post`), router registrations, or an OpenAPI/schema file.
  A new route is a capability and its invocation is the URL.
- **New required env vars** — the diff of whatever reads config, plus `.env.example`.
- **New config keys** — schema files, defaults, validation.

### Anything at all

- **New tests, by name.** Test names are capability sentences an engineer already wrote:
  `git diff "$BASE..HEAD" -- '*test*' | grep -E '^\+.*(def test_|it\(|test\(|func Test)'`
- **Migrations** — a new migration is a schema capability with downstream consequences.
- **Dependencies** — added, removed, or a breaking range bump.
- **Changed defaults** — a default value moving is a silent behaviour change for every existing caller,
  and it is the single most common thing a commit log fails to surface.

### Declared task vocabulary, where it exists

`mise tasks`, `npm run`, `just --list`, `make help` — intersected with the files the window changed.
This names *which* capability moved, which is genuinely useful, but it cannot say what it does now that
it didn't. Pair it with a probe; never ship it alone.

## Turning a probe into a card

```
headline    Fleet status now reports real systemd health per agent
invocation  pjangler fleet status --domain systemd
before      The systemd domain answered `unsupported` for every agent.
evidence    47842aa · contracts/fleet-contract.yaml (schema 4→5)
```

The `before` line comes from the probe, so it is a fact rather than a recollection.

## Verify before you headline

Run the invocation in its safest read-only form — `--help`, `--version`, a task the repo declares
read-only. A "you can now run X" that errors when the user pastes it is worse than saying nothing.

Anything you could not verify is labelled unverified and **never headlines**.

## When the probe finds nothing

That is a real and common result, and the correct output is one honest line: *no user-facing capability
changed in this window* — followed by the bands that do have content. Most long runs produce proof,
cleanup, refactoring and knowledge. Do not manufacture cards from refactors.
