# Mise-Task-Managing - Getting Started

**Pages:** 1

---

## Getting Started ​

**URL:** https://mise.jdx.dev/getting-started.html

**Contents:**
- Getting Started ​
- 1. Install mise CLI ​
- 2. mise exec and run ​
- 3. Activate mise optional ​
- 4. Use tools from backends (npm, pipx, core, aqua, github) ​
  - 5. Setting environment variables ​
  - 6. Run a task ​
- 7. Next steps ​
  - Set up autocompletion ​
  - GitHub API rate limiting ​

This will show you how to install mise and get started with it. This is a suitable way when using an interactive shell like bash, zsh, or fish.

See installing mise for other ways to install mise (macport, apt, yum, nix, etc.).

By default, mise will be installed to ~/.local/bin (this is simply a suggestion. mise can be installed anywhere). You can verify the installation by running:

mise respects MISE_DATA_DIR and XDG_DATA_HOME if you'd like to change these locations.

Once mise is installed, you can immediately start using it. mise can be used to install and run tools, launch tasks, and manage environment variables.

The most essential feature mise provides is the ability to run tools with specific versions. A simple way to run a shell command with a given tool is to use mise x|exec. For example, here is how you can start a Python 3 interactive shell (REPL):

In the examples below, use ~/.local/bin/mise (or the absolute path to mise) if mise is not already on PATH

mise x|exec is a powerful way to load the current mise context (tools & environment variables) without modifying your shell session or running ad-hoc commands with mise tools set. Installing tools is as simple as running mise u|use.

Another useful command is mise r|run which allows you to run a mise task or a script with the mise context.

You can set a shell alias in your shell's rc file like alias x="mise x --" to save some keystrokes.

While using mise x|exec is useful, for interactive shells, you might prefer to activate mise to automatically load the mise context (tools and environment variables) in your shell session. Another option is to use shims.

For interactive shells, mise activate is recommended. In non-interactive sessions, like CI/CD, IDEs, and scripts, using shims might work best. You can also not use any and call mise exec/run directly instead. See this guide for more information.

Here is how you can activate mise depending on your shell and the installation method:

Make sure you restart your shell session after modifying your rc file in order for it to take effect. You can run mise dr|doctor to verify that mise is correctly installed and activated.

Now that mise is activated or its shims have been added to PATH, node is also available directly! (without using mise exec):

Note that when you ran mise use --global node@22, mise updated the global mise configuration.

Backends are ecosystems or package managers that mise uses to install tools. With mise use, you can install multiple tools from each backend.

For example, to install claude-code with the npm backend:

Install black with the pipx backend:

mise can also install tools directly from github with the github backend:

See Backends for more ecosystems and details.

You can set environment variables in mise.toml which will be set if mise is activated or if mise x|exec is used in a directory:

You can define simple tasks in mise.toml and run them with mise run:

mise tasks will automatically install all of the tools from mise.toml before running the task.

See tasks for more information on how to define and use tasks.

Follow the walkthrough for more examples on how to use mise.

See autocompletion to learn how to set up autocompletion for your shell.

Many tools in mise require the use of the GitHub API. Unauthenticated requests to the GitHub API are often rate limited. If you see 4xx errors while using mise, you can set MISE_GITHUB_TOKEN or GITHUB_TOKEN to a token generated from here which will likely fix the issue. The token does not require any scopes.

**Examples:**

Example 1 (unknown):
```unknown
curl https://mise.run | sh
```

Example 2 (unknown):
```unknown
~/.local/bin/mise --version
# mise 2024.x.x
```

Example 3 (unknown):
```unknown
mise exec python@3 -- python
# this will download and install Python if it is not already installed
# Python 3.13.2
# >>> ...
```

Example 4 (unknown):
```unknown
mise exec node@22 -- node -v
# v22.x.x
```

---
