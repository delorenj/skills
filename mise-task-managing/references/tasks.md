# Mise-Task-Managing - Tasks

**Pages:** 26

---

## Running Tasks ​

**URL:** https://mise.jdx.dev/tasks/running-tasks.html

**Contents:**
- Running Tasks ​
- Task Grouping ​
- Wildcards ​
  - Examples ​
- Running on file changes ​
- Watching files ​
- mise run shorthand ​
- Execution order ​

See available tasks with mise tasks. To show tasks hidden with property hide=true, use the option --hidden.

List dependencies of tasks with mise task deps [tasks]....

Run a task with mise task run <task>, mise run <task>, mise r <task>, or just mise <task>—however that last one you should never put into scripts or documentation because if mise ever adds a command with that name in a future mise version, the task will be shadowed and must be run with one of the other forms.

Most mise users will have an alias for mise run like alias mr='mise run'.

By default, tasks will execute with a maximum of 4 parallel jobs. Customize this with the --jobs option, jobs setting or MISE_JOBS environment variable. The output normally will be by line, prefixed with the task label. By printing line-by-line we avoid interleaving output from parallel executions. However, if --jobs == 1, the output will be set to interleave.

To just print stdout/stderr directly, use --interleave, the task_output setting, or MISE_TASK_OUTPUT=interleave.

Stdin is not read by default. To enable this, set raw = true on the task that needs it. This will prevent it running in parallel with any other task—a RWMutex will get a write lock in this case. This also prevents redactions applied to the output.

Extra arguments will be passed to the task, for example, if we want to run in release mode:

If there are multiple commands, the args are only passed to the last command.

You can define arguments/flags for tasks which will provide validation, parsing, autocomplete, and documentation.

Autocomplete will work automatically for tasks if the usage CLI is installed and mise completions are working.

Markdown documentation can be generated with mise generate task-docs.

Multiple tasks/arguments can be separated with this ::: delimiter:

mise will run the task named "default" if no task is specified—and you've created one named "default". You can also alias a different task to "default".

Tasks can be grouped semantically by using name prefixes separated with :s. For example all testing related tasks may begin with test:. Nested grouping can also be used to further refine groups and simplify pattern matching. For example running mise run test:**:local will matchtest:units:local, test:integration:local and test:e2e:happy:local (See Wildcards for more information).

Glob style wildcards are supported when running tasks or specifying tasks dependencies.

Available Wildcard Patterns:

mise run generate:{completions,docs:*}

And with dependencies:

It's often handy to only execute a task if the files it uses changes. For example, we might only want to run cargo build if an ".rs" file changes. This can be done with the following config:

Now if target/debug/mycli is newer than Cargo.toml or any ".rs" file, the task will be skipped. This uses last modified timestamps. It wouldn't be hard to add checksum support.

Run a task when the source changes with mise watch

Currently, this just shells out to watchexec (which you can install however you want including with mise: mise use -g watchexec@latest. This may change in the future.)

Tasks can be run with mise run <TASK> or mise <TASK>—if the name doesn't conflict with a mise command. Because mise may later add a command with a conflicting name, it's recommended to use mise run <TASK> in scripts and documentation.

You can use depends, wait_for and depends_post to control the order of execution.

This will ensure that the build task is run before the test task.

You can also define a mise task to run other tasks in parallel or in series:

**Examples:**

Example 1 (unknown):
```unknown
mise run build --release
```

Example 2 (unknown):
```unknown
mise run build arg1 arg2 ::: test arg3 arg4
```

Example 3 (unknown):
```unknown
[tasks."lint:eslint"] # using a ":" means we need to add quotes
run = "eslint ."
[tasks."lint:prettier"]
run = "prettier --check ."
[tasks.lint]
depends = ["lint:*"]
wait_for = ["render"] # does not add as a dependency, but if it is already running, wait for it to finish
```

Example 4 (unknown):
```unknown
[tasks.build]
description = 'Build the CLI'
run = "cargo build"
sources = ['Cargo.toml', 'src/**/*.rs'] # skip running if these files haven't changed
outputs = ['target/debug/mycli']
```

---

## mise run ​

**URL:** https://mise.jdx.dev/cli/run.html

**Contents:**
- mise run ​
- Flags ​
  - --no-cache ​
  - -C --cd <CD> ​
  - -c --continue-on-error ​
  - -n --dry-run ​
  - -f --force ​
  - -s --shell <SHELL> ​
  - -t --tool… <TOOL@VERSION> ​
  - -j --jobs <JOBS> ​

This command will run a tasks, or multiple tasks in parallel. Tasks may have dependencies on other tasks or on source files. If source is configured on a tasks, it will only run if the source files have changed.

Tasks can be defined in mise.toml or as standalone scripts. In mise.toml, tasks take this form:

Alternatively, tasks can be defined as standalone scripts. These must be located in mise-tasks, .mise-tasks, .mise/tasks, mise/tasks or .config/mise/tasks. The name of the script will be the name of the tasks.

Do not use cache on remote tasks

Change to this directory before executing the command

Continue running tasks even if one fails

Don't actually run the tasks(s), just print them in order of execution

Force the tasks to run even if outputs are up to date

Shell to use to run toml tasks

Defaults to sh -c -o errexit -o pipefail on unix, and cmd /c on Windows Can also be set with the setting MISE_UNIX_DEFAULT_INLINE_SHELL_ARGS or MISE_WINDOWS_DEFAULT_INLINE_SHELL_ARGS Or it can be overridden with the shell property on a task.

Tool(s) to run in addition to what is in mise.toml files e.g.: node@20 python@3.10

Number of tasks to run in parallel [default: 4] Configure with jobs config or MISE_JOBS env var

Read/write directly to stdin/stdout/stderr instead of by line Redactions are not applied with this option Configure with raw config or MISE_RAW env var

Don't show any output except for errors

Timeout for the task to complete e.g.: 30s, 5m

Hides elapsed time after each task completes

Default to always hide with MISE_TASK_TIMINGS=0

Don't show extra output

Change how tasks information is output when running tasks

**Examples:**

Example 1 (unknown):
```unknown
[tasks.build]
run = "npm run build"
sources = ["src/**/*.ts"]
outputs = ["dist/**/*.js"]
```

Example 2 (unknown):
```unknown
$ cat .mise/tasks/build&lt;&lt;EOF
#!/usr/bin/env bash
npm run build
EOF
$ mise run build
```

Example 3 (unknown):
```unknown
# Runs the "lint" tasks. This needs to either be defined in mise.toml
# or as a standalone script. See the project README for more information.
$ mise run lint

# Forces the "build" tasks to run even if its sources are up-to-date.
$ mise run build --force

# Run "test" with stdin/stdout/stderr all connected to the current terminal.
# This forces `--jobs=1` to prevent interleaving of output.
$ mise run test --raw

# Runs the "lint", "test", and "check" tasks in parallel.
$ mise run lint ::: test ::: check

# Execute multiple tasks each with their own arguments.
$ mise tasks cmd1 arg1 arg2 ::: cmd2 arg1 arg2
```

---

## mise tasks add ​

**URL:** https://mise.jdx.dev/cli/tasks/add.html

**Contents:**
- mise tasks add ​
- Arguments ​
  - <TASK> ​
  - [-- RUN]… ​
- Flags ​
  - --description <DESCRIPTION> ​
  - -a --alias… <ALIAS> ​
  - --depends-post… <DEPENDS_POST> ​
  - -w --wait-for… <WAIT_FOR> ​
  - -D --dir <DIR> ​

Description of the task

Other names for the task

Dependencies to run after the task runs

Wait for these tasks to complete if they are to run

Run the task in a specific directory

Hide the task from mise task and completions

Directly connect stdin/stdout/stderr

Glob patterns of files this task uses as input

Glob patterns of files this task creates, to skip if they are not modified

Run the task in a specific shell

Do not print the command before running

Do not print the command or its output

Add dependencies to the task

Command to run on windows

Create a file task instead of a toml task

**Examples:**

Example 1 (unknown):
```unknown
mise task add pre-commit --depends "test" --depends "render" -- echo pre-commit
```

---

## mise watch ​

**URL:** https://mise.jdx.dev/cli/watch.html

**Contents:**
- mise watch ​
- Arguments ​
  - [TASK] ​
  - [ARGS]… ​
- Flags ​
  - -w --watch… <PATH> ​
  - -W --watch-non-recursive… <PATH> ​
  - -F --watch-file <PATH> ​
  - -c --clear <MODE> ​
  - -o --on-busy-update <MODE> ​

Run task(s) and watch for changes to rerun it

This command uses the watchexec tool to watch for changes to files and rerun the specified task(s). It must be installed for this command to work, but you can install it with mise use -g watchexec@latest.

Tasks to run Can specify multiple tasks by separating with ::: e.g.: mise run task1 arg1 arg2 ::: task2 arg1 arg2

Task and arguments to run

Watch a specific file or directory

By default, Watchexec watches the current directory.

When watching a single file, it's often better to watch the containing directory instead, and filter on the filename. Some editors may replace the file with a new one when saving, and some platforms may not detect that or further changes.

Upon starting, Watchexec resolves a "project origin" from the watched paths. See the help for '--project-origin' for more information.

This option can be specified multiple times to watch multiple files or directories.

The special value '/dev/null', provided as the only path watched, will cause Watchexec to not watch any paths. Other event sources (like signals or key events) may still be used.

Watch a specific directory, non-recursively

Unlike '-w', folders watched with this option are not recursed into.

This option can be specified multiple times to watch multiple directories non-recursively.

Watch files and directories from a file

Each line in the file will be interpreted as if given to '-w'.

For more complex uses (like watching non-recursively), use the argfile capability: build a file containing command-line options and pass it to watchexec with @path/to/argfile.

The special value '-' will read from STDIN; this in incompatible with '--stdin-quit'.

Clear screen before running command

If this doesn't completely clear the screen, try '--clear=reset'.

What to do when receiving events while the command is running

Default is to 'do-nothing', which ignores events while the command is running, so that changes that occur due to the command are ignored, like compilation outputs. You can also use 'queue' which will run the command once again when the current run has finished if any events occur while it's running, or 'restart', which terminates the running command and starts a new one. Finally, there's 'signal', which only sends a signal; this can be useful with programs that can reload their configuration without a full restart.

The signal can be specified with the '--signal' option.

Restart the process if it's still running

This is a shorthand for '--on-busy-update=restart'.

Send a signal to the process when it's still running

Specify a signal to send to the process when it's still running. This implies '--on-busy-update=signal'; otherwise the signal used when that mode is 'restart' is controlled by '--stop-signal'.

See the long documentation for '--stop-signal' for syntax.

Signals are not supported on Windows at the moment, and will always be overridden to 'kill'. See '--stop-signal' for more on Windows "signals".

Signal to send to stop the command

This is used by 'restart' and 'signal' modes of '--on-busy-update' (unless '--signal' is provided). The restart behaviour is to send the signal, wait for the command to exit, and if it hasn't exited after some time (see '--timeout-stop'), forcefully terminate it.

The default on unix is "SIGTERM".

Input is parsed as a full signal name (like "SIGTERM"), a short signal name (like "TERM"), or a signal number (like "15"). All input is case-insensitive.

On Windows this option is technically supported but only supports the "KILL" event, as Watchexec cannot yet deliver other events. Windows doesn't have signals as such; instead it has termination (here called "KILL" or "STOP") and "CTRL+C", "CTRL+BREAK", and "CTRL+CLOSE" events. For portability the unix signals "SIGKILL", "SIGINT", "SIGTERM", and "SIGHUP" are respectively mapped to these.

Time to wait for the command to exit gracefully

This is used by the 'restart' mode of '--on-busy-update'. After the graceful stop signal is sent, Watchexec will wait for the command to exit. If it hasn't exited after this time, it is forcefully terminated.

Takes a unit-less value in seconds, or a time span value such as "5min 20s". Providing a unit-less value is deprecated and will warn; it will be an error in the future.

The default is 10 seconds. Set to 0 to immediately force-kill the command.

This has no practical effect on Windows as the command is always forcefully terminated; see '--stop-signal' for why.

Translate signals from the OS to signals to send to the command

Takes a pair of signal names, separated by a colon, such as "TERM:INT" to map SIGTERM to SIGINT. The first signal is the one received by watchexec, and the second is the one sent to the command. The second can be omitted to discard the first signal, such as "TERM:" to not do anything on SIGTERM.

If SIGINT or SIGTERM are mapped, then they no longer quit Watchexec. Besides making it hard to quit Watchexec itself, this is useful to send pass a Ctrl-C to the command without also terminating Watchexec and the underlying program with it, e.g. with "INT:INT".

This option can be specified multiple times to map multiple signals.

Signal syntax is case-insensitive for short names (like "TERM", "USR2") and long names (like "SIGKILL", "SIGHUP"). Signal numbers are also supported (like "15", "31"). On Windows, the forms "STOP", "CTRL+C", and "CTRL+BREAK" are also supported to receive, but Watchexec cannot yet deliver other "signals" than a STOP.

Time to wait for new events before taking action

When an event is received, Watchexec will wait for up to this amount of time before handling it (such as running the command). This is essential as what you might perceive as a single change may actually emit many events, and without this behaviour, Watchexec would run much too often. Additionally, it's not infrequent that file writes are not atomic, and each write may emit an event, so this is a good way to avoid running a command while a file is partially written.

An alternative use is to set a high value (like "30min" or longer), to save power or bandwidth on intensive tasks, like an ad-hoc backup script. In those use cases, note that every accumulated event will build up in memory.

Takes a unit-less value in milliseconds, or a time span value such as "5sec 20ms". Providing a unit-less value is deprecated and will warn; it will be an error in the future.

The default is 50 milliseconds. Setting to 0 is highly discouraged.

Exit when stdin closes

This watches the stdin file descriptor for EOF, and exits Watchexec gracefully when it is closed. This is used by some process managers to avoid leaving zombie processes around.

Don't load gitignores

Among other VCS exclude files, like for Mercurial, Subversion, Bazaar, DARCS, Fossil. Note that Watchexec will detect which of these is in use, if any, and only load the relevant files. Both global (like '~/.gitignore') and local (like '.gitignore') files are considered.

This option is useful if you want to watch files that are ignored by Git.

Don't load project-local ignores

This disables loading of project-local ignore files, like '.gitignore' or '.ignore' in the watched project. This is contrasted with '--no-vcs-ignore', which disables loading of Git and other VCS ignore files, and with '--no-global-ignore', which disables loading of global or user ignore files, like '~/.gitignore' or '~/.config/watchexec/ignore'.

Supported project ignore files:

VCS ignore files (Git, Mercurial, Bazaar, Darcs, Fossil) are only used if the corresponding VCS is discovered to be in use for the project/origin. For example, a .bzrignore in a Git repository will be discarded.

Don't load global ignores

This disables loading of global or user ignore files, like '~/.gitignore', '~/.config/watchexec/ignore', or '%APPDATA%\Bazzar\2.0\ignore'. Contrast with '--no-vcs-ignore' and '--no-project-ignore'.

Supported global ignore files

Like for project files, Git and Bazaar global files will only be used for the corresponding VCS as used in the project.

Don't use internal default ignores

Watchexec has a set of default ignore patterns, such as editor swap files, *.pyc, *.pyo, .DS_Store, .bzr, _darcs, .fossil-settings, .git, .hg, .pijul, .svn, and Watchexec log files.

Don't discover ignore files at all

This is a shorthand for '--no-global-ignore', '--no-vcs-ignore', '--no-project-ignore', but even more efficient as it will skip all the ignore discovery mechanisms from the get go.

Note that default ignores are still loaded, see '--no-default-ignore'.

Don't ignore anything at all

This is a shorthand for '--no-discover-ignore', '--no-default-ignore'.

Note that ignores explicitly loaded via other command line options, such as '--ignore' or '--ignore-file', will still be used.

Wait until first change before running command

By default, Watchexec will run the command once immediately. With this option, it will instead wait until an event is detected before running the command as normal.

Sleep before running the command

This option will cause Watchexec to sleep for the specified amount of time before running the command, after an event is detected. This is like using "sleep 5 && command" in a shell, but portable and slightly more efficient.

Takes a unit-less value in seconds, or a time span value such as "2min 5s". Providing a unit-less value is deprecated and will warn; it will be an error in the future.

Poll for filesystem changes

By default, and where available, Watchexec uses the operating system's native file system watching capabilities. This option disables that and instead uses a polling mechanism, which is less efficient but can work around issues with some file systems (like network shares) or edge cases.

Optionally takes a unit-less value in milliseconds, or a time span value such as "2s 500ms", to use as the polling interval. If not specified, the default is 30 seconds. Providing a unit-less value is deprecated and will warn; it will be an error in the future.

Aliased as '--force-poll'.

Use a different shell

By default, Watchexec will use '$SHELL' if it's defined or a default of 'sh' on Unix-likes, and either 'pwsh', 'powershell', or 'cmd' (CMD.EXE) on Windows, depending on what Watchexec detects is the running shell.

With this option, you can override that and use a different shell, for example one with more features or one which has your custom aliases and functions.

If the value has spaces, it is parsed as a command line, and the first word used as the shell program, with the rest as arguments to the shell.

The command is run with the '-c' flag (except for 'cmd' on Windows, where it's '/C').

The special value 'none' can be used to disable shell use entirely. In that case, the command provided to Watchexec will be parsed, with the first word being the executable and the rest being the arguments, and executed directly. Note that this parsing is rudimentary, and may not work as expected in all cases.

Using 'none' is a little more efficient and can enable a stricter interpretation of the input, but it also means that you can't use shell features like globbing, redirection, control flow, logic, or pipes.

$ watchexec -n -- zsh -x -o shwordsplit scr

Use with powershell core:

$ watchexec --shell=pwsh -- Test-Connection localhost

$ watchexec --shell=cmd -- dir

Use with a different unix shell:

$ watchexec --shell=bash -- 'echo $BASH_VERSION'

Use with a unix shell and options:

$ watchexec --shell='zsh -x -o shwordsplit' -- scr

Shorthand for '--shell=none'

Configure event emission

Watchexec can emit event information when running a command, which can be used by the child process to target specific changed files.

One thing to take care with is assuming inherent behaviour where there is only chance. Notably, it could appear as if the RENAMED variable contains both the original and the new path being renamed. In previous versions, it would even appear on some platforms as if the original always came before the new. However, none of this was true. It's impossible to reliably and portably know which changed path is the old or new, "half" renames may appear (only the original, only the new), "unknown" renames may appear (change was a rename, but whether it was the old or new isn't known), rename events might split across two debouncing boundaries, and so on.

This option controls where that information is emitted. It defaults to 'none', which doesn't emit event information at all. The other options are 'environment' (deprecated), 'stdio', 'file', 'json-stdio', and 'json-file'.

The 'stdio' and 'file' modes are text-based: 'stdio' writes absolute paths to the stdin of the command, one per line, each prefixed with create:, remove:, rename:, modify:, or other:, then closes the handle; 'file' writes the same thing to a temporary file, and its path is given with the $WATCHEXEC_EVENTS_FILE environment variable.

There are also two JSON modes, which are based on JSON objects and can represent the full set of events Watchexec handles. Here's an example of a folder being created on Linux:

"tags": [ { "kind": "path", "absolute": "/home/user/your/new-folder", "filetype": "dir" }, { "kind": "fs", "simple": "create", "full": "Create(Folder)" }, { "kind": "source", "source": "filesystem", } ], "metadata": { "notify-backend": "inotify" }

The fields are as follows:

The 'json-stdio' mode will emit JSON events to the standard input of the command, one per line, then close stdin. The 'json-file' mode will create a temporary file, write the events to it, and provide the path to the file with the $WATCHEXEC_EVENTS_FILE environment variable.

Finally, the 'environment' mode was the default until 2.0. It sets environment variables with the paths of the affected files, for filesystem events:

$WATCHEXEC_COMMON_PATH is set to the longest common path of all of the below variables, and so should be prepended to each path to obtain the full/real path. Then:

Multiple paths are separated by the system path separator, ';' on Windows and ':' on unix. Within each variable, paths are deduplicated and sorted in binary order (i.e. neither Unicode nor locale aware).

This is the legacy mode, is deprecated, and will be removed in the future. The environment is a very restricted space, while also limited in what it can usefully represent. Large numbers of files will either cause the environment to be truncated, or may error or crash the process entirely. The $WATCHEXEC_COMMON_PATH is also unintuitive, as demonstrated by the multiple confused queries that have landed in my inbox over the years.

Only emit events to stdout, run no commands.

This is a convenience option for using Watchexec as a file watcher, without running any commands. It is almost equivalent to using cat as the command, except that it will not spawn a new process for each event.

This option requires --emit-events-to to be set, and restricts the available modes to stdio and json-stdio, modifying their behaviour to write to stdout instead of the stdin of the command.

Add env vars to the command

This is a convenience option for setting environment variables for the command, without setting them for the Watchexec process itself.

Use key=value syntax. Multiple variables can be set by repeating the option.

Configure how the process is wrapped

By default, Watchexec will run the command in a process group in Unix, and in a Job Object in Windows.

Some Unix programs prefer running in a session, while others do not work in a process group.

Use 'group' to use a process group, 'session' to use a process session, and 'none' to run the command directly. On Windows, either of 'group' or 'session' will use a Job Object.

Alert when commands start and end

With this, Watchexec will emit a desktop notification when a command starts and ends, on supported platforms. On unsupported platforms, it may silently do nothing, or log a warning.

When to use terminal colours

Setting the environment variable NO_COLOR to any value is equivalent to --color=never.

Print how long the command took to run

This may not be exactly accurate, as it includes some overhead from Watchexec itself. Use the time utility, high-precision timers, or benchmarking tools for more accurate results.

Don't print starting and stopping messages

By default Watchexec will print a message when the command starts and stops. This option disables this behaviour, so only the command's output, warnings, and errors will be printed.

Ring the terminal bell on command completion

Set the project origin

Watchexec will attempt to discover the project's "origin" (or "root") by searching for a variety of markers, like files or directory patterns. It does its best but sometimes gets it it wrong, and you can override that with this option.

The project origin is used to determine the path of certain ignore files, which VCS is being used, the meaning of a leading '/' in filtering patterns, and maybe more in the future.

When set, Watchexec will also not bother searching, which can be significantly faster.

Set the working directory

By default, the working directory of the command is the working directory of Watchexec. You can change that with this option. Note that paths may be less intuitive to use with this.

Filename extensions to filter to

This is a quick filter to only emit events for files with the given extensions. Extensions can be given with or without the leading dot (e.g. 'js' or '.js'). Multiple extensions can be given by repeating the option or by separating them with commas.

Filename patterns to filter to

Provide a glob-like filter pattern, and only events for files matching the pattern will be emitted. Multiple patterns can be given by repeating the option. Events that are not from files (e.g. signals, keyboard events) will pass through untouched.

Files to load filters from

Provide a path to a file containing filters, one per line. Empty lines and lines starting with '#' are ignored. Uses the same pattern format as the '--filter' option.

This can also be used via the $WATCHEXEC_FILTER_FILES environment variable.

[experimental] Filter programs.

/!\ This option is EXPERIMENTAL and may change and/or vanish without notice.

Provide your own custom filter programs in jaq (similar to jq) syntax. Programs are given an event in the same format as described in '--emit-events-to' and must return a boolean. Invalid programs will make watchexec fail to start; use '-v' to see program runtime errors.

In addition to the jaq stdlib, watchexec adds some custom filter definitions:

'path | file_meta' returns file metadata or null if the file does not exist.

'path | file_size' returns the size of the file at path, or null if it does not exist.

'path | file_read(bytes)' returns a string with the first n bytes of the file at path. If the file is smaller than n bytes, the whole file is returned. There is no filter to read the whole file at once to encourage limiting the amount of data read and processed.

'string | hash', and 'path | file_hash' return the hash of the string or file at path. No guarantee is made about the algorithm used: treat it as an opaque value.

'any | kv_store(key)', 'kv_fetch(key)', and 'kv_clear' provide a simple key-value store. Data is kept in memory only, there is no persistence. Consistency is not guaranteed.

'any | printout', 'any | printerr', and 'any | log(level)' will print or log any given value to stdout, stderr, or the log (levels = error, warn, info, debug, trace), and pass the value through (so '[1] | log("debug") | .[]' will produce a '1' and log '[1]').

All filtering done with such programs, and especially those using kv or filesystem access, is much slower than the other filtering methods. If filtering is too slow, events will back up and stall watchexec. Take care when designing your filters.

If the argument to this option starts with an '@', the rest of the argument is taken to be the path to a file containing a jaq program.

Jaq programs are run in order, after all other filters, and short-circuit: if a filter (jaq or not) rejects an event, execution stops there, and no other filters are run. Additionally, they stop after outputting the first value, so you'll want to use 'any' or 'all' when iterating, otherwise only the first item will be processed, which can be quite confusing!

Find user-contributed programs or submit your own useful ones at <https://github.com/watchexec/watchexec/discussions/592>.

Regexp ignore filter on paths:

'all(.tags[] | select(.kind == "path"); .absolute | test("[.]test[.]js$")) | not'

Pass any event that creates a file:

'any(.tags[] | select(.kind == "fs"); .simple == "create")'

Pass events that touch executable files:

'any(.tags[] | select(.kind == "path" && .filetype == "file"); .absolute | metadata | .executable)'

Ignore files that start with shebangs:

'any(.tags[] | select(.kind == "path" && .filetype == "file"); .absolute | read(2) == "#!") | not'

Filename patterns to filter out

Provide a glob-like filter pattern, and events for files matching the pattern will be excluded. Multiple patterns can be given by repeating the option. Events that are not from files (e.g. signals, keyboard events) will pass through untouched.

Files to load ignores from

Provide a path to a file containing ignores, one per line. Empty lines and lines starting with '#' are ignored. Uses the same pattern format as the '--ignore' option.

This can also be used via the $WATCHEXEC_IGNORE_FILES environment variable.

Filesystem events to filter to

This is a quick filter to only emit events for the given types of filesystem changes. Choose from 'access', 'create', 'remove', 'rename', 'modify', 'metadata'. Multiple types can be given by repeating the option or by separating them with commas. By default, this is all types except for 'access'.

This may apply filtering at the kernel level when possible, which can be more efficient, but may be more confusing when reading the logs.

Don't emit fs events for metadata changes

This is a shorthand for '--fs-events create,remove,rename,modify'. Using it alongside the '--fs-events' option is non-sensical and not allowed.

Print events that trigger actions

This prints the events that triggered the action when handling it (after debouncing), in a human readable form. This is useful for debugging filters.

Use '-vvv' instead when you need more diagnostic information.

This shows the manual page for Watchexec, if the output is a terminal and the 'man' program is available. If not, the manual page is printed to stdout in ROFF format (suitable for writing to a watchexec.1 file).

**Examples:**

Example 1 (unknown):
```unknown
* 'path', along with:
  + `absolute`, an absolute path.
  + `filetype`, a file type if known ('dir', 'file', 'symlink', 'other').
* 'fs':
  + `simple`, the "simple" event type ('access', 'create', 'modify', 'remove', or 'other').
  + `full`, the "full" event type, which is too complex to fully describe here, but looks like 'General(Precise(Specific))'.
* 'source', along with:
  + `source`, the source of the event ('filesystem', 'keyboard', 'mouse', 'os', 'time', 'internal').
* 'keyboard', along with:
  + `keycode`. Currently only the value 'eof' is supported.
* 'process', for events caused by processes:
  + `pid`, the process ID.
* 'signal', for signals sent to Watchexec:
  + `signal`, the normalised signal name ('hangup', 'interrupt', 'quit', 'terminate', 'user1', 'user2').
* 'completion', for when a command ends:
  + `disposition`, the exit disposition ('success', 'error', 'signal', 'stop', 'exception', 'continued').
  + `code`, the exit, signal, stop, or exception code.
```

Example 2 (unknown):
```unknown
$ mise watch build
Runs the "build" tasks. Will re-run the tasks when any of its sources change.
Uses "sources" from the tasks definition to determine which files to watch.

$ mise watch build --glob src/**/*.rs
Runs the "build" tasks but specify the files to watch with a glob pattern.
This overrides the "sources" from the tasks definition.

$ mise watch build --clear
Extra arguments are passed to watchexec. See `watchexec --help` for details.

$ mise watch serve --watch src --exts rs --restart
Starts an api server, watching for changes to "*.rs" files in "./src" and kills/restarts the server when they change.
```

---

## Monorepo Tasks experimental ​

**URL:** https://mise.jdx.dev/tasks/monorepo.html

**Contents:**
- Monorepo Tasks experimental ​
- Overview ​
  - Benefits ​
- Configuration ​
  - Enabling Monorepo Mode ​
  - Example Structure ​
- Task Path Syntax ​
  - Absolute Paths ​
  - Current config_root Tasks ​
  - Wildcard Patterns ​

mise supports monorepo-style task organization with target path syntax. This feature allows you to manage tasks across multiple projects in a single repository, where each project can have its own mise.toml configuration with tools, environment variables, and tasks that may be different from where the task is called from.

When experimental_monorepo_root is enabled in your root mise.toml, mise will automatically discover tasks in subdirectories and prefix them with their relative path from the monorepo root. This creates a unified task namespace across your entire repository.

The directory containing a mise.toml file is called the config_root. In monorepo mode, each project can have its own config_root with its own configuration, separate from the monorepo root. Note that if you use one of the alternate paths in a subdirectory like ./projects/frontend/.mise/config.toml, the config_root will be ./projects/frontend–not ./projects/frontend/.mise.

Add experimental_monorepo_root = true to your root mise.toml:

This feature requires MISE_EXPERIMENTAL=1 environment variable.

With this structure, tasks will be automatically namespaced:

Monorepo tasks use special path syntax with // and : prefixes. You can run these tasks directly with mise or with mise run. With non-monorepo tasks, the guidance is to avoid using the direct syntax for scripts because it could conflict with future core mise commands. However, mise will never define commands with a // or : prefix, so this guidance does not apply to monorepo tasks.

Use // prefix to specify the absolute path from the monorepo root:

Use : prefix to run tasks in the current config_root:

Optional Colon Syntax

The leading : is optional when running tasks from subdirectories or defining task dependencies. While both syntaxes work, we encourage using the : prefix to be explicit about monorepo task references.

Running from subdirectory:

The bare name syntax (without :) is supported primarily to ease migration from non-monorepo to monorepo configurations. When migrating, you won't need to update all your task dependencies immediately - they'll continue to work. However, using the : prefix makes it clear you're referencing a task in the current config_root.

mise supports two types of wildcards for flexible task execution:

Use ellipsis (...) to match any directory depth:

Additional glob patterns may be added in a future version so mise //projects/*:build and mise '//projects/**:build' will likely be supported. We're using ... because it matches how bazel and buck2 do it.

Use asterisk (*) to match task names:

You can combine both types of wildcards for powerful patterns:

Subdirectory tasks automatically inherit tools and environment variables from parent config files in the hierarchy. However, each subdirectory can also define its own tools and environment variables in its config_root. This allows you to:

For large monorepos, you can control task discovery depth with the task.monorepo_depth setting (default: 5):

This limits how deep mise will search for task files:

Reduce this value if you notice slow task discovery in very large monorepos, especially if your projects are concentrated at a specific depth level.

The following directories are automatically excluded from task discovery:

The difference between mise tasks and mise tasks --all:

Given this structure:

When in projects/frontend/:

Place commonly-used tools and environment in the root mise.toml to avoid repetition:

Only override tools in subdirectories when they genuinely need different versions:

Prefix related tasks with common names to enable pattern matching:

Then run all test tasks: mise '//...:test*'

Organize projects in subdirectories to enable targeted execution:

Then run tasks by group:

The monorepo ecosystem offers many excellent tools, each with different strengths. Here's how mise's Monorepo Tasks compares:

Taskfile and Just are fantastic for single-project task automation. They're lightweight and easy to set up, but they weren't designed with monorepos in mind. While you can have multiple Taskfiles/Justfiles in a repo, they don't provide unified task discovery, cross-project wildcards, or automatic tool/environment inheritance across projects.

mise's advantage: Automatic task discovery across the entire monorepo with a unified namespace and powerful wildcard patterns.

Nx, Turborepo, and Lerna are powerful tools specifically designed for JavaScript/TypeScript monorepos.

mise's advantage: Language-agnostic support. While these tools excel in JS/TS ecosystems, mise works equally well with Rust, Go, Python, Ruby, or any mix of languages. You also get unified tool version management (not just tasks) and environment variables across your entire stack.

Bazel (Google) and Buck2 (Meta) are industrial-strength build systems designed for massive, multi-language monorepos at companies with thousands of engineers.

Both are extremely powerful but come with significant complexity:

mise's advantage: Simplicity through non-hermetic builds. mise doesn't try to control your entire build environment in isolation - instead, it manages tools and tasks in a flexible, practical way. This "non-hermetic" approach means you can use mise without restructuring your entire codebase or learning a new language. You get powerful monorepo task management with simple TOML configuration - enough power for most teams without the enterprise-level complexity that hermetic builds require.

Rush (Microsoft) offers strict dependency management and build orchestration for JavaScript monorepos, with a focus on safety and convention adherence.

Moon is a newer Rust-based build system that aims to be developer-friendly while supporting multiple languages.

mise's Monorepo Tasks aims to hit the sweet spot between simplicity and power:

When to consider alternatives:

The best tool is the one that fits your team's needs. mise's Monorepo Tasks is designed for teams who want powerful monorepo management without the complexity overhead, especially when working across multiple languages.

**Examples:**

Example 1 (unknown):
```unknown
# /myproject/mise.toml
experimental_monorepo_root = true

[tools]
# Tools defined here are inherited by all subdirectories
node = "20"
```

Example 2 (unknown):
```unknown
myproject/
├── mise.toml (with experimental_monorepo_root = true)
├── projects/
│   ├── frontend/
│   │   └── mise.toml (with tasks: build, test)
│   └── backend/
│       └── mise.toml (with tasks: build, test)
```

Example 3 (unknown):
```unknown
# Direct syntax (preferred for monorepo tasks)
mise //projects/frontend:build

# Also works with 'run'
mise run //projects/frontend:build

# Need quotes for wildcards
mise '//projects/frontend:*'
```

Example 4 (unknown):
```unknown
# Run build task in frontend project
mise //projects/frontend:build

# Run test task in backend project
mise //projects/backend:test
```

---

## Task Configuration ​

**URL:** https://mise.jdx.dev/tasks/task-configuration.html

**Contents:**
- Task Configuration ​
- Task properties ​
  - run ​
  - run_windows ​
  - description ​
  - alias ​
  - depends ​
  - depends_post ​
  - wait_for ​
  - env ​

This is an exhaustive list of all the configuration options available for tasks in mise.toml or as file tasks.

All examples are in toml-task format instead of file, however they apply in both except where otherwise noted.

The command(s) to run. This is the only required property for a task.

You can now mix scripts with task references:

Simple forms still work and are equivalent:

Windows-specific variant of run supporting the same structured syntax:

A description of the task. This is used in (among other places) the help output, completions, mise run (without arguments), and mise tasks.

An alias for the task so you can run it with mise run <alias> instead of the full task name.

Tasks that must be run before this task. This is a list of task names or aliases. Arguments can be passed to the task, e.g.: depends = ["build --release"]. If multiple tasks have the same dependency, that dependency will only be run once. mise will run whatever it can in parallel (up to --jobs) through the use of depends and related properties.

Like depends but these tasks run after this task and its dependencies complete. For example, you may want a postlint task that you can run individually without also running lint:

Similar to depends, it will wait for these tasks to complete before running however they won't be added to the list of tasks to run. This is essentially optional dependencies.

Environment variables specific to this task. These will not be passed to depends tasks.

Tools to install and activate before running the task. This is useful for tasks that require a specific tool to be installed or a tool with a different version. It will only be used for that task, not dependencies.

The directory to run the task from. The most common way this is used is when you want the task to execute in the user's current directory:

Hide the task from help, completion, and other output like mise tasks. Useful for deprecated or internal tasks you don't want others to easily see.

A message to show before running the task. This is useful for tasks that are destructive or take a long time to run. The user will be prompted to confirm before the task is run.

Connects the task directly to the shell's stdin/stdout/stderr. This is useful for tasks that need to accept input or output in a way that mise's normal task handling doesn't support. This is not recommended to use because it really screws up the output whenever mise runs tasks in parallel. Ensure when using this that no other tasks are running at the same time.

In the future we could have a property like single = true or something that prevents multiple tasks from running at the same time. If that sounds useful, search/file a ticket.

Files or directories that this task uses as input, if this and outputs is defined, mise will skip executing tasks where the modification time of the oldest output file is newer than the modification time of the newest source file. This is useful for tasks that are expensive to run and only need to be run when their inputs change.

The task itself will be automatically added as a source, so if you edit the definition that will also cause the task to be run.

This is also used in mise watch to know which files/directories to watch.

This can be specified with relative paths to the config file and/or with glob patterns, e.g.: src/**/*.rs. Ensure you don't go crazy with adding a ton of files in a glob though—mise has to scan each and every one to check the timestamp.

Running the above will only execute cargo build if mise.toml, Cargo.toml, or any ".rs" file in the src directory has changed since the last build.

The task_source_files function can be used to iterate over a task's sources within its template context.

The counterpart to sources, these are the files or directories that the task will create/modify after it executes.

auto = true is an alternative to specifying output files manually. In that case, mise will touch an internally tracked file based on the hash of the task definition (stored in ~/.local/state/mise/task-outputs/<hash> if you're curious). This is useful if you want mise run to execute when sources change but don't want to have to manually touch a file for sources to work.

The shell to use to run the task. This is useful if you want to run a task with a different shell than the default such as fish, zsh, or pwsh. Generally though, it's recommended to use a shebang instead because that will allow IDEs with mise support to show syntax highlighting and linting for the script.

Suppress mise's output for the task such as showing the command that is run, e.g.: [build] $ cargo build. When this is set, mise won't show any output other than what the script itself outputs. If you'd also like to hide even the output that the task emits, use silent.

Suppress all output from the task. If set to "stdout" or "stderr", only that stream will be suppressed.

For comprehensive information about task arguments and the usage field, see the dedicated Task Arguments page.

More advanced usage specs can be added to the task's usage field. This only applies to toml-tasks.

Both args and flags in usage specs can specify an environment variable as an alternative source for their value. This allows task arguments to be provided through environment variables when not specified on the command line.

The precedence order is:

For positional arguments:

File tasks (tasks defined as executable files in mise-tasks/ or .mise/tasks/) also support the env attribute:

The env attribute works seamlessly with tera templates in task commands:

The values from environment variables will be available both as $usage_* environment variables and through tera template functions.

Environment variables can satisfy required argument checks. If an argument is marked as required (using angle brackets <arg>), providing its value through the environment variable specified in the env attribute fulfills that requirement:

Vars are variables that can be shared between tasks like environment variables but they are not passed as environment variables to the scripts. They are defined in the vars section of the mise.toml file.

Like most configuration in mise, vars can be defined across several files. So for example, you could put some vars in your global mise config ~/.config/mise/config.toml, use them in a task at ~/src/work/myproject/mise.toml. You can also override those vars in "later" config files such as ~/src/work/myproject/mise.local.toml and they will be used inside tasks of any config file.

As of this writing vars are only supported in TOML tasks. I want to add support for file tasks, but I don't want to turn all file tasks into tera templates just for this feature.

Options available in the top-level mise.toml [task_config] section. These apply to all tasks which are included by that config file or use the same root directory, e.g.: ~/src/myprojec/mise.toml's [task_config] applies to file tasks like ~/src/myproject/mise-tasks/mytask but not to tasks in ~/src/myproject/subproj/mise.toml.

Change the default directory tasks are run from.

Add toml files containing toml tasks, or file tasks to include when looking for tasks.

If using included task toml files, note that they have a different format than the mise.toml file. They are just a list of tasks. The file should be the same format as the [tasks] section of mise.toml but without the [task] prefix:

If you want auto-completion/validation in included toml tasks files, you can use the following JSON schema: https://mise.jdx.dev/schema/mise-task.json

mise supports monorepo-style task organization with target path syntax. Enable it by setting experimental_monorepo_root = true in your root mise.toml.

For complete documentation on monorepo tasks including:

See the dedicated Monorepo Tasks documentation.

Redactions are a way to hide sensitive information from the output of tasks. This is useful for things like API keys, passwords, or other sensitive information that you don't want to accidentally leak in logs or other output.

A list of environment variables to redact from the output.

Running the above task will output echo [redacted] instead.

You can also specify these as a glob pattern, e.g.: redactions.env = ["SECRETS_*"].

Vars are variables that can be shared between tasks like environment variables but they are not passed as environment variables to the scripts. They are defined in the vars section of the mise.toml file.

Like [env], vars can also be read in as a file:

Secrets are also supported as vars.

The following settings control task behavior. These can be set globally in ~/.config/mise/config.toml or per-project in mise.toml:

Pushes tools' bin-paths to the front of PATH instead of allowing modifications of PATH after activation to take precedence. For example, if you have the following in your mise.toml:

But you also have this in your ~/.zshrc:

What will happen is /some/other/python will be used instead of the python installed by mise. This means you typically want to put mise activate at the end of your shell config so nothing overrides it.

If you want to always use the mise versions of tools despite what is in your shell config, set this to true. In that case, using this example again, /some/other/python will be after mise's python in PATH.

Default: false unless running NixOS or Alpine (let me know if others should be added)

Do not use precompiled binaries for all languages. Useful if running on a Linux distribution like Alpine that does not use glibc and therefore likely won't be able to run precompiled binaries.

Note that this needs to be setup for each language. File a ticket if you notice a language that is not working with this config.

should mise keep downloaded files after installation

should mise keep install files after installation even if the installation fails

Architecture to use for precompiled binaries. This is used to determine which precompiled binaries to download. If unset, mise will use the system's architecture.

Automatically install missing tools when running mise x, mise run, or as part of the 'not found' handler.

List of tools to skip automatically installing when running mise x, mise run, or as part of the 'not found' handler.

The age of the cache before it is considered stale. mise will occasionally delete cache files which have not been accessed in this amount of time.

Set to 0s to keep cache files indefinitely.

Use color in mise terminal output

The default config filename read. mise use and other commands that create new config files will use this value. This must be an env var.

The default .tool-versions filename read. This will not ignore .tool-versions—use override_tool_versions_filename for that. This must be an env var.

Backends to disable such as asdf or pipx

Disable the default mapping of short tool names like php -> asdf:mise-plugins/asdf-php. This parameter disables only for the backends vfox and asdf.

Turns off helpful hints when using different mise features

Tools defined in mise.toml that should be ignored

Tools defined in mise.toml that should be used - all other tools are ignored

Enables profile-specific config files such as .mise.development.toml. Use this for different env vars or different tool versions in development/staging/production environments. See Configuration Environments for more on how to use this feature.

Multiple envs can be set by separating them with a comma, e.g. MISE_ENV=ci,test. They will be read in order, with the last one taking precedence.

Path to a file containing environment variables to automatically load.

Automatically install missing tools when running mise x.

Enables experimental features. I generally will publish new features under this config which needs to be enabled to use them. While a feature is marked as "experimental" its behavior may change or even disappear in any release.

The idea is experimental features can be iterated on this way so we can get the behavior right, but once that label goes away you shouldn't expect things to change without a proper deprecation—and even then it's unlikely.

Also, I very often will use experimental as a beta flag as well. New functionality that I want to test with a smaller subset of users I will often push out under experimental mode even if it's not related to an experimental feature.

If you'd like to help me out, consider enabling it even if you don't have a particular feature you'd like to try. Also, if something isn't working right, try disabling it if you can.

duration that remote version cache is kept for "fast" commands (represented by PREFER_STALE), these are always cached. For "slow" commands like mise ls-remote or mise install:

Timeout in seconds for HTTP requests to fetch new tool versions in mise.

Path to the global mise config file. Default is ~/.config/mise/config.toml. This must be an env var.

Path which is used as {{config_root}} for the global config file. Default is $HOME. This must be an env var.

Path to a file containing default go packages to install when installing go

Mirror to download go sdk tarballs from.

URL to fetch go from.

Defaults to ~/.local/share/mise/installs/go/.../bin. Set to true to override GOBIN if previously set. Set to false to not set GOBIN (default is ${GOPATH:-$HOME/go}/bin).

[deprecated] Set to true to set GOPATH=~/.local/share/mise/installs/go/.../packages.

Sets GOROOT=~/.local/share/mise/installs/go/.../.

Set to true to skip checksum verification when downloading go sdk tarballs.

Use gpg to verify all tool signatures.

Uses an exponential backoff strategy. The duration is calculated by taking the base (10ms) to the n-th power.

Timeout in seconds for all HTTP requests in mise.

By default, idiomatic version files are disabled. You can enable them for specific tools with this setting.

For example, to enable idiomatic version files for node and python:

See Idiomatic Version Files for more information.

This is a list of config paths that mise will ignore.

How many jobs to run concurrently such as tool installs.

[!NOTE] This feature is experimental and may change in the future.

Read/update lockfiles for tool versions. This is useful when you'd like to have loose versions in mise.toml like this:

But you'd like the versions installed to be consistent within a project. When this is enabled, mise will update mise.lock files next to mise.toml files containing pinned versions. When installing tools, mise will reference this lockfile if it exists and this setting is enabled to resolve versions.

The lockfiles are not created automatically. To generate them, run the following (assuming the config file is mise.toml):

The lockfile is named the same as the config file but with .lock instead of .toml as the extension, e.g.:

Set to false to disable the "command not found" handler to autoinstall missing tool versions. Disable this if experiencing strange behavior in your shell when a command is not found.

Important limitation: This handler only installs missing versions of tools that already have at least one version installed. mise cannot determine which tool provides a binary without having the tool installed first, so it cannot auto-install completely new tools.

This also runs in shims if the terminal is interactive.

OS to use for precompiled binaries.

If set, mise will ignore default config files like mise.toml and use these filenames instead. This must be an env var.

If set, mise will ignore .tool-versions files and use these filenames instead. Can be set to none to disable .tool-versions. This must be an env var.

Enables extra-secure behavior. See Paranoid.

This sets --pin by default when running mise use in mise.toml files. This can be overridden by passing --fuzzy on the command line.

How long to wait before updating plugins automatically (note this isn't currently implemented).

Suppress all output except errors.

Connect stdin/stdout/stderr to child processes.

Use a custom file for the shorthand aliases. This is useful if you want to share plugins within an organization.

Shorthands make it so when a user runs something like mise install elixir mise will automatically install the asdf-elixir plugin. By default, it uses the shorthands in registry.toml.

The file should be in this toml format:

Suppress all mise run|watch output except errors—including what tasks output.

Path to the system mise config file. Default is /etc/mise/config.toml. This must be an env var.

Paths that mise will not look for tasks in.

Change output style when executing tasks. This controls the output of mise run.

Mise will always fetch the latest tasks from the remote, by default the cache is used.

Automatically install missing tools when executing tasks.

Tasks to skip when running mise run.

Default timeout for tasks. Can be overridden by individual tasks.

Show completion message with elapsed time for each task on mise run. Default shows when output type is prefix.

Enable terminal progress indicators using OSC 9;4 escape sequences. This provides native progress bars in the terminal window chrome for terminals that support it, including Ghostty, VS Code's integrated terminal, Windows Terminal, and VTE-based terminals (GNOME Terminal, Ptyxis, etc.).

When enabled, mise will send progress updates to the terminal during operations like tool installations. The progress bar appears in the terminal's window UI, separate from the text output.

mise automatically detects whether your terminal supports OSC 9;4 and will only send these sequences if supported. Terminals like Alacritty, iTerm2, WezTerm, and kitty do not support OSC 9;4 and will not receive these sequences.

Set to false to disable this feature if you prefer not to see these indicators.

This is a list of config paths that mise will automatically mark as trusted.

List of default shell arguments for unix to be used with file. For example sh.

List of default shell arguments for unix to be used with inline commands. For example, sh, -c for sh.

Map of URL patterns to replacement URLs. This feature supports both simple hostname replacements and advanced regex-based URL transformations for download mirroring and custom registries.

See URL Replacements for more information.

Determines whether to use a specified shell for executing tasks in the tasks directory. When set to true, the shell defined in the file will be used, or the default shell specified by windows_default_file_shell_args or unix_default_file_shell_args will be applied. If set to false, tasks will be executed directly as programs.

Set to "false" to disable using mise-versions as a quick way for mise to query for new versions. This host regularly grabs all the latest versions of core and community plugins. It's faster than running a plugin's list-all command and gets around GitHub rate limiting problems when using it.

mise-versions itself also struggles with rate limits but you can help it to fetch more frequently by authenticating with its GitHub app. It does not require any permissions since it simply fetches public repository information.

See Troubleshooting for more information.

Shows more verbose output such as installation logs when installing tools.

List of default shell arguments for Windows to be used for file commands. For example, cmd, /c for cmd.exe.

List of default shell arguments for Windows to be used for inline commands. For example, cmd, /c for cmd.exe.

List of executable extensions for Windows. For example, exe for .exe files, bat for .bat files, and so on.

This will automatically answer yes or no to prompts. This is useful for scripting.

[experimental] List of age identity files to use for decryption.

[experimental] Path to the age private key file to use for encryption/decryption.

[experimental] List of SSH identity files to use for age decryption.

Use baked-in aqua registry.

Use cosign to verify aqua tool signatures.

Extra arguments to pass to cosign when verifying aqua tool signatures.

Enable/disable GitHub Artifact Attestations verification for aqua tools. When enabled, mise will verify the authenticity and integrity of downloaded tools using GitHub's artifact attestation system.

Use minisign to verify aqua tool signatures.

URL to fetch aqua registry from. This is used to install tools from the aqua registry.

If this is set, the baked-in aqua registry is not used.

By default, the official aqua registry is used: https://github.com/aquaproj/aqua-registry

Use SLSA to verify aqua tool signatures.

If true, mise will use cargo binstall instead of cargo install if cargo-binstall is installed and on PATH. This makes installing CLIs with cargo much faster by downloading precompiled binaries.

You can install it with mise:

Packages are installed from the official cargo registry.

You can set this to a different registry name if you have a custom feed or want to use a different source.

Please follow the cargo alternative registries documentation to configure your registry.

This is a list of flags to extend the search and install abilities of dotnet tools.

Here are the available flags:

URL to fetch dotnet tools from. This is used when installing dotnet tools.

By default, mise will use the nuget API to fetch.

However, you can set this to a different URL if you have a custom feed or want to use a different source.

If true, compile erlang from source. If false, use precompiled binaries. If not set, use precompiled binaries if available.

Compile node from source.

Install a specific node flavor like glibc-217 or musl. Use with unofficial node build repo.

Use gpg to verify node tool signatures.

Mirror to download node tarballs from.

If true, mise will use bun instead of npm if bun is installed and on PATH. This makes installing CLIs faster by using bun as the package manager.

You can install it with mise:

URL to use for pipx registry.

This is used to fetch the latest version of a package from the pypi registry.

The default is https://pypi.org/pypi/{}/json which is the JSON endpoint for the pypi registry.

You can also use the HTML endpoint by setting this to https://pypi.org/simple/{}/.

If true, mise will use uvx instead of pipx if uv is installed and on PATH. This makes installing CLIs much faster by using uv as the package manager.

You can install it with mise:

Path to a file containing default python packages to install when installing a python version.

URL to fetch python patches from to pass to python-build.

Directory to fetch python patches from.

Specify the architecture to use for precompiled binaries.

Specify the flavor to use for precompiled binaries.

Options are available here: https://gregoryszorc.com/docs/python-build-standalone/main/running.html

Specify the architecture to use for precompiled binaries. If on an old CPU, you may want to set this to "x86_64" for the most compatible binaries. See https://gregoryszorc.com/docs/python-build-standalone/main/running.html for more information.

URL to fetch pyenv from for compiling python with python-build.

Integrate with uv to automatically create/source venvs if uv.lock is present.

Arguments to pass to uv when creating a venv.

Automatically create virtualenvs for python tools.

Arguments to pass to python when creating a venv. (not used for uv venv creation)

Prefer to use venv from Python's standard library.

A list of patch files or URLs to apply to ruby source.

Path to a file containing default ruby gems to install when installing ruby.

Options to pass to ruby-build.

URL to fetch ruby-build from.

Use ruby-install instead of ruby-build.

Options to pass to ruby-install.

URL to fetch ruby-install from.

Set to true to enable verbose output during ruby installation.

Path to the cargo home directory. Defaults to ~/.cargo or %USERPROFILE%\.cargo

Path to the rustup home directory. Defaults to ~/.rustup or %USERPROFILE%\.rustup

The age private key to use for sops secret decryption.

Path to the age private key file to use for sops secret decryption.

The age public keys to use for sops secret encryption.

Use rops to decrypt sops files. Disable to shell out to sops which will slow down mise but sops may offer features not available in rops.

If true, fail when sops decryption fails (including when sops is not available, the key is missing, or the key is invalid). If false, skip decryption and continue in these cases.

Show a warning if tools are not installed when entering a directory with a mise.toml file.

Disable tools with disable_tools.

Show configured env vars when entering a directory with a mise.toml file.

Show configured tools when entering a directory with a mise.toml file.

Truncate status messages.

Use gpg to verify swift tool signatures.

Override the platform to use for precompiled binaries.

When using monorepo mode (experimental_monorepo_root = true), this controls how deep mise will search for task files in subdirectories.

Performance tip: Reduce this value if you have a very large monorepo and notice slow task discovery. For example, if your projects are all at projects/*, set to 2.

Or via environment variable:

If empty (default), uses default exclusions: node_modules, target, dist, build. If you specify any patterns, ONLY those patterns will be excluded (defaults are NOT included). For example, setting to [".temp", "vendor"] will exclude only those two directories.

When enabled, mise will skip directories that are ignored by .gitignore files when discovering tasks in a monorepo.

**Examples:**

Example 1 (unknown):
```unknown
[tasks.grouped]
run = [
  { task = "t1" },          # run t1 (with its dependencies)
  { tasks = ["t2", "t3"] }, # run t2 and t3 in parallel (with their dependencies)
  "echo end",               # then run a script
]
```

Example 2 (unknown):
```unknown
tasks.a = "echo hello"
tasks.b = ["echo hello"]
tasks.c.run = "echo hello"
[tasks.d]
run = "echo hello"
[tasks.e]
run = ["echo hello"]
```

Example 3 (unknown):
```unknown
[tasks.build]
run = "cargo build"
run_windows = "cargo build --features windows"
```

Example 4 (unknown):
```unknown
[tasks.build]
description = "Build the CLI"
run = "cargo build"
```

---

## mise generate git-pre-commit ​

**URL:** https://mise.jdx.dev/cli/generate/git-pre-commit.html

**Contents:**
- mise generate git-pre-commit ​
- Flags ​
  - --hook <HOOK> ​
  - -t --task <TASK> ​
  - -w --write ​

Generate a git pre-commit hook

This command generates a git pre-commit hook that runs a mise task like mise run pre-commit when you commit changes to your repository.

Staged files are passed to the task as STAGED.

For more advanced pre-commit functionality, see mise's sister project: https://hk.jdx.dev/

Which hook to generate (saves to .git/hooks/$hook)

The task to run when the pre-commit hook is triggered

write to .git/hooks/pre-commit and make it executable

**Examples:**

Example 1 (unknown):
```unknown
mise generate git-pre-commit --write --task=pre-commit
git commit -m "feat: add new feature" # runs `mise run pre-commit`
```

---

## Tasks ​

**URL:** https://mise.jdx.dev/tasks/

**Contents:**
- Tasks ​
- Tasks in mise.toml files ​
- File Tasks ​
- Environment variables passed to tasks ​

Like make it manages tasks used to build and test projects.

You can define tasks in mise.toml files or as standalone shell scripts. These are useful for things like running linters, tests, builders, servers, and other tasks that are specific to a project. Of course, tasks launched with mise will include the mise environment—your tools and env vars defined in mise.toml.

Here's my favorite features about mise's task runner:

There are 2 ways to define tasks: inside of mise.toml files or as standalone shell scripts.

Tasks are defined in the [tasks] section of the mise.toml file.

You can then run the task with mise run build (or mise build if it doesn't conflict with an existing command).

You can also define tasks as standalone shell scripts. All you have to do is to create an executable file in a specific directory like mise-tasks.

You can then run the task with mise run build like for TOML tasks. See the file tasks reference for more information.

The following environment variables are passed to the task:

**Examples:**

Example 1 (unknown):
```unknown
[tasks.build]
description = "Build the CLI"
run = "cargo build"
```

Example 2 (unknown):
```unknown
#!/usr/bin/env bash
#MISE description="Build the CLI"
cargo build
```

---

## mise generate task-stubs ​

**URL:** https://mise.jdx.dev/cli/generate/task-stubs.html

**Contents:**
- mise generate task-stubs ​
- Flags ​
  - -m --mise-bin <MISE_BIN> ​
  - -d --dir <DIR> ​

Generates shims to run mise tasks

By default, this will build shims like ./bin/<task>. These can be paired with mise generate bootstrap so contributors to a project can execute mise tasks without installing mise into their system.

Path to a mise bin to use when running the task stub.

Use --mise-bin=./bin/mise to use a mise bin generated from mise generate bootstrap

Directory to create task stubs inside of

**Examples:**

Example 1 (unknown):
```unknown
$ mise task add test -- echo 'running tests'
$ mise generate task-stubs
$ ./bin/test
running tests
```

---

## mise tasks ​

**URL:** https://mise.jdx.dev/cli/tasks.html

**Contents:**
- mise tasks ​
- Arguments ​
  - [TASK] ​
- Global Flags ​
  - -x --extended ​
  - --no-header ​
  - --hidden ​
  - -g --global ​
  - -J --json ​
  - -l --local ​

Task name to get info of

Do not print table header

Only show global tasks

Output in JSON format

Only show non-global tasks

Load all tasks from the entire monorepo, including sibling directories. By default, only tasks from the current directory hierarchy are loaded.

Sort by column. Default is name.

Sort order. Default is asc.

**Examples:**

Example 1 (unknown):
```unknown
mise tasks ls
```

---

## Task System Architecture ​

**URL:** https://mise.jdx.dev/tasks/architecture.html

**Contents:**
- Task System Architecture ​
- Task Dependency System ​
  - Dependency Graph Resolution ​
  - Dependency Types ​
    - depends - Prerequisites ​
    - depends_post - Cleanup Tasks ​
    - wait_for - Soft Dependencies ​
- Parallel Execution Engine ​
  - Job Control ​
  - Example Execution Flow ​

Understanding how mise's task system works helps you write more efficient tasks and troubleshoot dependency issues.

mise uses a sophisticated dependency graph system to manage task execution order and parallelism. This ensures tasks run in the correct order while maximizing performance through parallel execution.

When you run mise run build, mise creates a directed acyclic graph (DAG) of all tasks and their dependencies:

This graph ensures that:

mise supports three types of task dependencies:

Tasks that must complete successfully before this task runs:

Tasks that run after this task completes (whether successful or failed):

Tasks that should run first if they're in the current execution, but don't fail if they're not available:

mise executes tasks in parallel up to the configured job limit:

The default is 4 parallel jobs, but you can configure this globally:

Execution with --jobs 2:

mise discovers tasks from multiple sources in this order:

When you run mise run build, mise:

Tasks are inherited from parent directories but can be overridden:

In frontend/, you have access to: lint (inherited), test (overridden), build (inherited), bundle (local).

Use task arguments for conditional behavior:

Tasks can specify dependencies at runtime:

Reference tasks from other directories:

Tasks can skip execution if sources haven't changed:

mise will only run the task if:

Use mise run --force to ignore source/output checking:

Use mise watch for continuous development:

This automatically reruns tasks when their source files change.

Circular Dependencies:

Solution: Remove the circular reference or use wait_for instead of depends.

Missing Dependencies:

Solution: Define the missing task or remove the dependency.

Slow Parallel Execution:

The task architecture is designed to scale from simple single-task projects to complex multi-service applications with intricate build dependencies.

**Examples:**

Example 1 (unknown):
```unknown
[tasks.test]
depends = ["lint", "build"]
run = "npm test"
```

Example 2 (unknown):
```unknown
[tasks.deploy]
depends = ["build", "test"]
depends_post = ["cleanup", "notify"]
run = "kubectl apply -f deployment.yaml"
```

Example 3 (unknown):
```unknown
[tasks.integration-test]
wait_for = ["start-services"]  # Only waits if start-services is also being run
run = "npm run test:integration"
```

Example 4 (unknown):
```unknown
mise run test --jobs 8        # Use 8 parallel jobs
mise run test -j 1            # Force sequential execution
```

---

## TOML-based Tasks ​

**URL:** https://mise.jdx.dev/tasks/toml-tasks.html

**Contents:**
- TOML-based Tasks ​
- Trivial task examples ​
- Detailed task examples ​
- Adding tasks ​
- Common options ​
  - Run command ​
  - Specifying which directory to use ​
  - Adding a description and alias ​
  - Dependencies ​
  - Environment variables ​

Tasks can be defined in mise.toml files in different ways. Trivial tasks can be written into a [tasks] section, while more detailed tasks each get their own section.

You can use environment variables or vars to define common arguments:

You can edit the mise.toml file directly or using mise tasks add

will add the following to mise.toml:

For an exhaustive list, see task configuration.

Provide the script to run. Can be a single command or an array of commands:

Commands are run in series. If a command fails, the task will stop and the remaining commands will not run.

You can specify an alternate command to run on Windows by using the run_windows key:

The dir property determines the cwd in which the task is executed. You can use the directory from where the task was run with dir = "{{cwd}}":

Also, MISE_ORIGINAL_CWD is set to the original working directory and will be passed to the task.

You can add a description to a task and alias for a task.

You can specify dependencies for a task. Dependencies are run before the task itself. If a dependency fails, the task will not run.

There are other ways to specify dependencies, see wait_for and depends_post

You can specify environment variables for a task:

If you want to skip executing a task if certain files haven't changed (up-to-date), you should specify sources and outputs:

You can use sources alone if with mise watch to run the task when the sources change. You can use the task_source_files() function to get the resolved paths of a task's sources from within its template.

A message to show before running the task. The user will be prompted to confirm before the task is run.

Tasks are executed with set -e (set -o erropt) if the shell is sh, bash, or zsh. This means that the script will exit if any command fails. You can disable this by running set +e in the script.

You can specify a shell command to run the script with (default is sh -c or cmd /c):

By using a shebang (or shell), you can run tasks in different languages (e.g., Python, Node.js, Ruby, etc.):

A shebang is the character sequence #! at the beginning of a script file that tells the system which program should be used to interpret/execute the script. The env command comes from GNU Coreutils. mise does not use env but will behave similarly.

For example, #!/usr/bin/env python will run the script with the Python interpreter found in the PATH.

The -S flag allows passing multiple arguments to the interpreter. It treats the rest of the line as a single argument string to be split.

This is useful when you need to specify interpreter flags or options. Example: #!/usr/bin/env -S python -u will run Python with unbuffered output.

You can specify a file to run as a task:

Task files can be fetched remotely with multiple protocols:

Please note that the file will be downloaded and executed. Make sure you trust the source.

Url format must follow these patterns git::<protocol>://<url>//<path>?<ref>

Each task file is cached in the MISE_CACHE_DIR directory. If the file is updated, it will not be re-downloaded unless the cache is cleared.

You can reset the cache by running mise cache clear.

You can use the MISE_TASK_REMOTE_NO_CACHE environment variable to disable caching of remote tasks.

For comprehensive information about task arguments, see the dedicated Task Arguments page.

By default, arguments are passed to the last script in the run array. So if a task was defined as:

Then running mise run test foo bar will pass foo bar to ./scripts/test-e2e.sh but not to cargo test.

The recommended way to define arguments is using the usage field:

Arguments defined in the usage field are available as environment variables prefixed with usage_.

See the Task Arguments page for complete documentation.

Deprecated - Removal in 2026.11.0

Using Tera template functions (arg(), option(), flag()) in run scripts is deprecated and will be removed in mise 2026.11.0. Versions >= 2026.5.0 will show a deprecation warning.

Why it's being removed:

Please migrate to using the usage field instead. See the migration guide.

You can define arguments using Tera template functions (deprecated):

Then running mise run test foo bar will pass foo bar to cargo test. mise run test --e2e-args baz will pass baz to ./scripts/test-e2e.sh.

These are defined in scripts with {{arg()}}. They are used for positional arguments where the order matters.

These are defined in scripts with {{option()}}. They are used for named arguments where the order doesn't matter.

Flags are like options except they don't take values. They are defined in scripts with {{flag()}}.

The value will be true if the flag is passed, and false otherwise.

More advanced usage specs can be added to the task's usage field:

Arguments and flags defined in the usage spec are also set in the environment before running each script defined in the run field. The name of each variable is prepended with usage_ keyword.

**Examples:**

Example 1 (unknown):
```unknown
build = "cargo build"
test = "cargo test"
lint = "cargo clippy"
```

Example 2 (unknown):
```unknown
[tasks.cleancache]
run = "rm -rf .cache"
hide = true # hide this task from the list

[tasks.clean]
depends = ['cleancache']
run = "cargo clean" # runs as a shell command

[tasks.build]
description = 'Build the CLI'
run = "cargo build"
alias = 'b' # `mise run b`

[tasks.test]
description = 'Run automated tests'
# multiple commands are run in series
run = [
    'cargo test',
    './scripts/test-e2e.sh',
]
dir = "{{cwd}}" # run in user's cwd, default is the project's base directory

[tasks.lint]
description = 'Lint with clippy'
env = { RUST_BACKTRACE = '1' } # env vars for the script
# you can specify a multiline script instead of individual commands
run = """
#!/usr/bin/env bash
cargo clippy
"""

[tasks.ci] # only dependencies to be run
description = 'Run CI tasks'
depends = ['build', 'lint', 'test']

[tasks.release]
confirm = 'Are you sure you want to cut a new release?'
description = 'Cut a new release'
file = 'scripts/release.sh' # execute an external script
```

Example 3 (unknown):
```unknown
[env]
VERBOSE_ARGS = '--verbose'

# Vars can be shared between tasks like environment variables,
# but they are not passed as environment variables to the scripts
[vars]
e2e_args = '--headless'

[tasks.test]
run = './scripts/test-e2e.sh {{vars.e2e_args}} $VERBOSE_ARGS'
```

Example 4 (unknown):
```unknown
mise task add pre-commit --depends "test" --depends "render" -- echo pre-commit
```

---

## mise tasks run ​

**URL:** https://mise.jdx.dev/cli/tasks/run.html

**Contents:**
- mise tasks run ​
- Arguments ​
  - [TASK] ​
  - [ARGS]… ​
- Flags ​
  - --no-cache ​
  - -C --cd <CD> ​
  - -c --continue-on-error ​
  - -n --dry-run ​
  - -f --force ​

This command will run a tasks, or multiple tasks in parallel. Tasks may have dependencies on other tasks or on source files. If source is configured on a tasks, it will only run if the source files have changed.

Tasks can be defined in mise.toml or as standalone scripts. In mise.toml, tasks take this form:

Alternatively, tasks can be defined as standalone scripts. These must be located in mise-tasks, .mise-tasks, .mise/tasks, mise/tasks or .config/mise/tasks. The name of the script will be the name of the tasks.

Tasks to run Can specify multiple tasks by separating with ::: e.g.: mise run task1 arg1 arg2 ::: task2 arg1 arg2

Arguments to pass to the tasks. Use ":::" to separate tasks

Do not use cache on remote tasks

Change to this directory before executing the command

Continue running tasks even if one fails

Don't actually run the tasks(s), just print them in order of execution

Force the tasks to run even if outputs are up to date

Shell to use to run toml tasks

Defaults to sh -c -o errexit -o pipefail on unix, and cmd /c on Windows Can also be set with the setting MISE_UNIX_DEFAULT_INLINE_SHELL_ARGS or MISE_WINDOWS_DEFAULT_INLINE_SHELL_ARGS Or it can be overridden with the shell property on a task.

Tool(s) to run in addition to what is in mise.toml files e.g.: node@20 python@3.10

Number of tasks to run in parallel [default: 4] Configure with jobs config or MISE_JOBS env var

Read/write directly to stdin/stdout/stderr instead of by line Redactions are not applied with this option Configure with raw config or MISE_RAW env var

Don't show any output except for errors

Timeout for the task to complete e.g.: 30s, 5m

Hides elapsed time after each task completes

Default to always hide with MISE_TASK_TIMINGS=0

Don't show extra output

Change how tasks information is output when running tasks

**Examples:**

Example 1 (unknown):
```unknown
[tasks.build]
run = "npm run build"
sources = ["src/**/*.ts"]
outputs = ["dist/**/*.js"]
```

Example 2 (unknown):
```unknown
$ cat .mise/tasks/build&lt;&lt;EOF
#!/usr/bin/env bash
npm run build
EOF
$ mise run build
```

Example 3 (unknown):
```unknown
# Runs the "lint" tasks. This needs to either be defined in mise.toml
# or as a standalone script. See the project README for more information.
$ mise run lint

# Forces the "build" tasks to run even if its sources are up-to-date.
$ mise run build --force

# Run "test" with stdin/stdout/stderr all connected to the current terminal.
# This forces `--jobs=1` to prevent interleaving of output.
$ mise run test --raw

# Runs the "lint", "test", and "check" tasks in parallel.
$ mise run lint ::: test ::: check

# Execute multiple tasks each with their own arguments.
$ mise tasks cmd1 arg1 arg2 ::: cmd2 arg1 arg2
```

---

## File Tasks ​

**URL:** https://mise.jdx.dev/tasks/file-tasks.html

**Contents:**
- File Tasks ​
- Task Configuration ​
- Shebang ​
- Editing tasks ​
- Task Grouping ​
- Arguments ​
  - Example file task with arguments ​
  - Example of a NodeJS file task with arguments ​
- CWD ​
- Running tasks directly ​

In addition to defining tasks through the configuration, they can also be defined as standalone script files in one of the following directories:

Note that you can configure directories using the task_config section.

Here is an example of a file task that builds a Rust CLI:

Ensure that the file is executable, otherwise mise will not be able to detect it.

Having the code in a bash file and not TOML helps make it work better in editors since they can do syntax highlighting and linting more easily.

They also still work great for non-mise users—though of course they'll need to find a different way to install their dev tools the tasks might use.

All configuration options can be found here task configuration You can provide additional configuration for file tasks by adding #MISE comments at the top of the file.

Assuming that file was located in mise-tasks/build, it can then be run with mise run build (or with its alias: mise run b).

Beware of formatters changing #MISE to # MISE. It's intentionally ignored by mise to avoid unintentional configuration. To workaround this, use the alternative: # [MISE].

The shebang line is optional, but if it is present, it will be used to determine the shell to run the script with. You can also use it to run the script with various programming languages.

This script can be edited with by running mise task edit build (using $EDITOR). If it doesn't exist it will be created. This is convenient for quickly editing or creating new scripts.

File tasks in mise-tasks, .mise/tasks, mise/tasks, or .config/mise/tasks can be grouped into sub-directories which will automatically apply prefixes to their names when loaded.

Example: With a folder structure like below:

Running mise tasks will give the below output:

For comprehensive information about task arguments, see the dedicated Task Arguments page.

usage spec can be used within these files to provide argument parsing, autocompletion, documentation when running mise and can be exported to markdown. Essentially this turns tasks into fully-fledged CLIs.

The usage CLI is not required to execute mise tasks with the usage spec. However, for completions to work, the usage CLI must be installed and available in the PATH.

Here is an example of a file task that builds a Rust CLI using some of the features of usage:

Note: The :? syntax (e.g., ${usage_profile:?}) helps shellcheck understand these variables will be set by usage, avoiding warnings about unset variables. The --profile flag has default="debug" set in the usage spec to provide a fallback value.

If you have installed usage, completions will be enabled for your task. In this example,

(Note that cli and markdown help for tasks is not yet implemented in mise as of this writing but that is planned.)

If you don't get any autocomplete suggestions, use the -v (verbose) flag to see what's going on. For example, if you use mise run build -v and have an invalid usage spec, you will see an error message such as DEBUG failed to parse task file with usage

Here is how you can use usage to parse arguments in a Node.js script:

If you pass an invalid argument, you will get an error message:

Autocomplete will show the available choices for the output_file argument if usage is installed.

mise sets the current working directory to the directory of mise.toml before running tasks. This can be overridden by setting dir="{{cwd}}" in the task header:

Also, the original working directory is available in the MISE_ORIGINAL_CWD environment variable:

Tasks don't need to be configured as part of a config, you can just run them directly by passing the path to the script:

Note that the path must start with / or ./ to be considered a file path. (On Windows it can be C:\ or .\)

**Examples:**

Example 1 (unknown):
```unknown
#!/usr/bin/env bash
#MISE description="Build the CLI"
cargo build
```

Example 2 (unknown):
```unknown
chmod +x mise-tasks/build
```

Example 3 (unknown):
```unknown
#MISE description="Build the CLI"
#MISE alias="b"
#MISE sources=["Cargo.toml", "src/**/*.rs"]
#MISE outputs=["target/debug/mycli"]
#MISE env={RUST_BACKTRACE = "1"}
#MISE depends=["lint", "test"]
#MISE tools={rust="1.50.0"}
```

Example 4 (unknown):
```unknown
#!/usr/bin/env node
//MISE description="Hello, World in Node.js"

console.log("Hello, World!");
```

---

## mise tool-stub ​

**URL:** https://mise.jdx.dev/cli/tool-stub.html

**Contents:**
- mise tool-stub ​
- Arguments ​
  - <FILE> ​
  - [ARGS]… ​

Tool stubs are executable files containing TOML configuration that specify which tool to run and how to run it. They provide a convenient way to create portable, self-contained executables that automatically manage tool installation and execution.

A tool stub consists of: - A shebang line: #!/usr/bin/env -S mise tool-stub - TOML configuration specifying the tool, version, and options - Optional comments describing the tool's purpose

Example stub file: #!/usr/bin/env -S mise tool-stub # Node.js v20 development environment

tool = "node" version = "20.0.0" bin = "node"

The stub will automatically install the specified tool version if missing and execute it with any arguments passed to the stub.

For more information, see: https://mise.jdx.dev/dev-tools/tool-stubs.html

Path to the TOML tool stub file to execute

The stub file must contain TOML configuration specifying the tool and version to run. At minimum, it should specify a 'version' field. Other common fields include 'tool', 'bin', and backend-specific options.

Arguments to pass to the tool

All arguments after the stub file path will be forwarded to the underlying tool. Use '--' to separate mise arguments from tool arguments if needed.

---

## mise test-tool ​

**URL:** https://mise.jdx.dev/cli/test-tool.html

**Contents:**
- mise test-tool ​
- Arguments ​
  - [TOOLS]… ​
- Flags ​
  - -a --all ​
  - --all-config ​
  - --include-non-defined ​
  - -j --jobs <JOBS> ​
  - --raw ​

Test a tool installs and executes

Test every tool specified in registry.toml

Test all tools specified in config files

Also test tools not defined in registry.toml, guessing how to test it

Number of jobs to run in parallel [default: 4]

Directly pipe stdin/stdout/stderr from plugin to user Sets --jobs=1

**Examples:**

Example 1 (unknown):
```unknown
mise test-tool ripgrep
```

---

## mise tasks info ​

**URL:** https://mise.jdx.dev/cli/tasks/info.html

**Contents:**
- mise tasks info ​
- Arguments ​
  - <TASK> ​
- Flags ​
  - -J --json ​

Get information about a task

Name of the task to get information about

Output in JSON format

**Examples:**

Example 1 (unknown):
```unknown
$ mise tasks info
Name: test
Aliases: t
Description: Test the application
Source: ~/src/myproj/mise.toml

$ mise tasks info test --json
{
  "name": "test",
  "aliases": "t",
  "description": "Test the application",
  "source": "~/src/myproj/mise.toml",
  "depends": [],
  "env": {},
  "dir": null,
  "hide": false,
  "raw": false,
  "sources": [],
  "outputs": [],
  "run": [
    "echo \"testing!\""
  ],
  "file": null,
  "usage_spec": {}
}
```

---

## mise install ​

**URL:** https://mise.jdx.dev/cli/install.html

**Contents:**
- mise install ​
- Arguments ​
  - [TOOL@VERSION]… ​
- Flags ​
  - -n --dry-run ​
  - -f --force ​
  - -j --jobs <JOBS> ​
  - --raw ​
  - -v --verbose… ​

Install a tool version

Installs a tool version to ~/.local/share/mise/installs/<PLUGIN>/<VERSION> Installing alone will not activate the tools so they won't be in PATH. To install and/or activate in one command, use mise use which will create a mise.toml file in the current directory to activate this tool when inside the directory. Alternatively, run mise exec <TOOL>@<VERSION> -- <COMMAND> to execute a tool without creating config files.

Tools will be installed in parallel. To disable, set --jobs=1 or MISE_JOBS=1

Tool(s) to install e.g.: node@20

Show what would be installed without actually installing

Force reinstall even if already installed

Number of jobs to run in parallel [default: 4]

Directly pipe stdin/stdout/stderr from plugin to user Sets --jobs=1

Show installation output

This argument will print plugin output such as download, configuration, and compilation output.

**Examples:**

Example 1 (unknown):
```unknown
mise install node@20.0.0  # install specific node version
mise install node@20      # install fuzzy node version
mise install node         # install version specified in mise.toml
mise install              # installs everything specified in mise.toml
```

---

## mise generate task-docs ​

**URL:** https://mise.jdx.dev/cli/generate/task-docs.html

**Contents:**
- mise generate task-docs ​
- Flags ​
  - -I --index ​
  - -i --inject ​
  - -m --multi ​
  - -o --output <OUTPUT> ​
  - -r --root <ROOT> ​
  - -s --style <STYLE> ​

Generate documentation for tasks in a project

write only an index of tasks, intended for use with --multi

inserts the documentation into an existing file

This will look for a special comment, <!-- mise-tasks -->, and replace it with the generated documentation. It will replace everything between the comment and the next comment, <!-- /mise-tasks --> so it can be run multiple times on the same file to update the documentation.

render each task as a separate document, requires --output to be a directory

writes the generated docs to a file/directory

root directory to search for tasks

**Examples:**

Example 1 (unknown):
```unknown
mise generate task-docs
```

---

## mise cache prune ​

**URL:** https://mise.jdx.dev/cli/cache/prune.html

**Contents:**
- mise cache prune ​
- Arguments ​
  - [PLUGIN]… ​
- Flags ​
  - --dry-run ​
  - -v --verbose… ​

Removes stale mise cache files

By default, this command will remove files that have not been accessed in 30 days. Change this with the MISE_CACHE_PRUNE_AGE environment variable.

Plugin(s) to clear cache for e.g.: node, python

Just show what would be pruned

---

## mise tasks deps ​

**URL:** https://mise.jdx.dev/cli/tasks/deps.html

**Contents:**
- mise tasks deps ​
- Arguments ​
  - [TASKS]… ​
- Flags ​
  - --hidden ​
  - --dot ​

Display a tree visualization of a dependency graph

Tasks to show dependencies for Can specify multiple tasks by separating with spaces e.g.: mise tasks deps lint test check

Display dependencies in DOT format

**Examples:**

Example 1 (unknown):
```unknown
# Show dependencies for all tasks
$ mise tasks deps

# Show dependencies for the "lint", "test" and "check" tasks
$ mise tasks deps lint test check

# Show dependencies in DOT format
$ mise tasks deps --dot
```

---

## mise exec ​

**URL:** https://mise.jdx.dev/cli/exec.html

**Contents:**
- mise exec ​
- Arguments ​
  - [TOOL@VERSION]… ​
  - [-- COMMAND]… ​
- Flags ​
  - -c --command <C> ​
  - -j --jobs <JOBS> ​
  - --raw ​

Execute a command with tool(s) set

use this to avoid modifying the shell session or running ad-hoc commands with mise tools set.

Tools will be loaded from mise.toml, though they can be overridden with <RUNTIME> args Note that only the plugin specified will be overridden, so if a mise.toml file includes "node 20" but you run mise exec python@3.11; it will still load node@20.

The "--" separates runtimes from the commands to pass along to the subprocess.

Tool(s) to start e.g.: node@20 python@3.10

Command string to execute (same as --command)

Command string to execute

Number of jobs to run in parallel [default: 4]

Directly pipe stdin/stdout/stderr from plugin to user Sets --jobs=1

**Examples:**

Example 1 (unknown):
```unknown
$ mise exec node@20 -- node ./app.js  # launch app.js using node-20.x
$ mise x node@20 -- node ./app.js     # shorter alias

# Specify command as a string:
$ mise exec node@20 python@3.11 --command "node -v && python -V"

# Run a command in a different directory:
$ mise x -C /path/to/project node@20 -- node ./app.js
```

---

## mise tasks ls ​

**URL:** https://mise.jdx.dev/cli/tasks/ls.html

**Contents:**
- mise tasks ls ​
- Flags ​
  - -x --extended ​
  - --no-header ​
  - --hidden ​
  - -g --global ​
  - -J --json ​
  - -l --local ​
  - --all ​
  - --sort <COLUMN> ​

List available tasks to execute These may be included from the config file or from the project's .mise/tasks directory mise will merge all tasks from all parent directories into this list.

So if you have global tasks in ~/.config/mise/tasks/* and project-specific tasks in ~/myproject/.mise/tasks/*, then they'll both be available but the project-specific tasks will override the global ones if they have the same name.

Do not print table header

Only show global tasks

Output in JSON format

Only show non-global tasks

Load all tasks from the entire monorepo, including sibling directories. By default, only tasks from the current directory hierarchy are loaded.

Sort by column. Default is name.

Sort order. Default is asc.

**Examples:**

Example 1 (unknown):
```unknown
mise tasks ls
```

---

## Task Arguments ​

**URL:** https://mise.jdx.dev/tasks/task-arguments.html

**Contents:**
- Task Arguments ​
- Recommended Methods ​
  - 1. Usage Field (Preferred) ​
    - Quick Example ​
- Complete Usage Specification Reference ​
  - Positional Arguments (arg) ​
    - Basic Syntax ​
    - With Defaults ​
    - Variadic Arguments ​
    - Environment Variable Backing ​

Task arguments allow you to pass parameters to tasks, making them more flexible and reusable. There are three ways to define task arguments in mise, but only two are recommended for current use.

The usage field is the recommended approach for defining task arguments. It provides a clean, declarative syntax that works with both TOML tasks and file tasks.

Arguments defined in the usage field are automatically available as environment variables prefixed with usage_:

Positional arguments are defined with arg and must be provided in order.

Priority order: CLI argument > Environment variable > Default value

Flags are boolean options that can be enabled/disabled.

Flags can also accept values (making them similar to options):

Priority order: CLI flag > Environment variable > Config file > Default value

Options are flags that require a value. In mise's usage syntax, these are defined as flags with <value> placeholders.

Options support all the same features as flags (environment variables, config backing, choices, etc.).

Custom completion can be defined for any argument or flag by name:

Output format (split on : for value and description):

For detailed help text, use multi-line format:

Hide arguments from help output (useful for deprecated or internal options):

For file tasks, you can define arguments directly in the file using special #MISE or #USAGE comment syntax:

Use #MISE (uppercase, recommended) or #USAGE for defining arguments in file tasks. # [MISE] or # [USAGE] are also accepted as workarounds for formatters.

Deprecated - Removal in 2026.11.0

The Tera template method for defining task arguments is deprecated and will be removed in mise 2026.11.0.

Why it's being removed:

Migration required: Please migrate to the usage field method before 2026.11.0.

Previously, you could define arguments inline in run scripts using Tera template functions:

Problems with this approach:

Empty strings during parsing: During spec collection (first pass), template functions return empty strings, so you can't use them in templates like:

Escaping complexity: Different shell types require different escaping:

No help generation: Doesn't generate proper --help output

Here's how to migrate from Tera templates to the usage field:

**Examples:**

Example 1 (unknown):
```unknown
[tasks.deploy]
description = "Deploy application"
usage = '''
arg "<environment>" help="Target environment" choices=["dev", "staging", "prod"]
flag "-v --verbose" help="Enable verbose output"
option "--region <region>" help="AWS region" default="us-east-1" env="AWS_REGION"
'''
run = '''
echo "Deploying to $usage_environment in $usage_region"
[[ "$usage_verbose" == "true" ]] && set -x
./deploy.sh "$usage_environment" "$usage_region"
'''
```

Example 2 (unknown):
```unknown
# Execute with arguments
$ mise run deploy staging --verbose --region us-west-2

# Inside the task, these are available as:
# $usage_environment = "staging"
# $usage_verbose = "true"
# $usage_region = "us-west-2"
```

Example 3 (unknown):
```unknown
$ mise run deploy --help
Deploy application

Usage: deploy <environment> [OPTIONS]

Arguments:
  <environment>  Target environment [possible values: dev, staging, prod]

Options:
  -v, --verbose          Enable verbose output
      --region <region>  AWS region [env: AWS_REGION] [default: us-east-1]
  -h, --help            Print help
```

Example 4 (unknown):
```unknown
arg "<name>" help="Description"               # Required positional arg
arg "[name]" help="Description"               # Optional positional arg
arg "<file>"                                  # Completed as filename
arg "<dir>"                                   # Completed as directory
```

---

## mise tasks edit ​

**URL:** https://mise.jdx.dev/cli/tasks/edit.html

**Contents:**
- mise tasks edit ​
- Arguments ​
  - <TASK> ​
- Flags ​
  - -p --path ​

Edit a tasks with $EDITOR

The tasks will be created as a standalone script if it does not already exist.

Display the path to the tasks instead of editing it

**Examples:**

Example 1 (unknown):
```unknown
mise tasks edit build
mise tasks edit test
```

---

## mise prune ​

**URL:** https://mise.jdx.dev/cli/prune.html

**Contents:**
- mise prune ​
- Arguments ​
  - [INSTALLED_TOOL]… ​
- Flags ​
  - -n --dry-run ​
  - --configs ​
  - --tools ​

Delete unused versions of tools

mise tracks which config files have been used in ~/.local/state/mise/tracked-configs Versions which are no longer the latest specified in any of those configs are deleted. Versions installed only with environment variables MISE_<PLUGIN>_VERSION will be deleted, as will versions only referenced on the command line mise exec <PLUGIN>@<VERSION>.

You can list prunable tools with mise ls --prunable

Prune only these tools

Do not actually delete anything

Prune only tracked and trusted configuration links that point to non-existent configurations

Prune only unused versions of tools

**Examples:**

Example 1 (unknown):
```unknown
$ mise prune --dry-run
rm -rf ~/.local/share/mise/versions/node/20.0.0
rm -rf ~/.local/share/mise/versions/node/20.0.1
```

---
