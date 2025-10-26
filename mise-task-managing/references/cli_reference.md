# Mise-Task-Managing - Cli Reference

**Pages:** 45

---

## mise plugins ​

**URL:** https://mise.jdx.dev/cli/plugins.html

**Contents:**
- mise plugins ​
- Flags ​
  - -c --core ​
  - --user ​
  - -u --urls ​
- Subcommands ​

The built-in plugins only Normally these are not shown

List installed plugins

This is the default behavior but can be used with --core to show core and user plugins

Show the git url for each plugin e.g.: https://github.com/asdf-vm/asdf-nodejs.git

---

## mise ​

**URL:** https://mise.jdx.dev/cli/

**Contents:**
- mise ​
- Arguments ​
  - [TASK] ​
- Global Flags ​
  - -C --cd <DIR> ​
  - -E --env… <ENV> ​
  - -j --jobs <JOBS> ​
  - --raw ​
  - -y --yes ​
  - -q --quiet ​

Usage: mise [FLAGS] [TASK] <SUBCOMMAND>

Shorthand for mise task run <TASK>.

Change directory before running command

Set the environment for loading mise.<ENV>.toml

How many jobs to run in parallel [default: 8]

Read/write directly to stdin/stdout/stderr instead of by line

Answer yes to all confirmation prompts

Suppress non-error messages

Suppress all task output and mise non-error messages

Show extra output (use -vv for even more)

Do not load any config files

Can also use MISE_NO_CONFIG=1

---

## mise plugins link ​

**URL:** https://mise.jdx.dev/cli/plugins/link.html

**Contents:**
- mise plugins link ​
- Arguments ​
  - <NAME> ​
  - [DIR] ​
- Flags ​
  - -f --force ​

Symlinks a plugin into mise

This is used for developing a plugin.

The name of the plugin e.g.: node, ruby

The local path to the plugin e.g.: ./mise-node

Overwrite existing plugin

**Examples:**

Example 1 (unknown):
```unknown
# essentially just `ln -s ./mise-node ~/.local/share/mise/plugins/node`
$ mise plugins link node ./mise-node

# infer plugin name as "node"
$ mise plugins link ./mise-node
```

---

## mise uninstall ​

**URL:** https://mise.jdx.dev/cli/uninstall.html

**Contents:**
- mise uninstall ​
- Arguments ​
  - [INSTALLED_TOOL@VERSION]… ​
- Flags ​
  - -a --all ​
  - -n --dry-run ​

Removes installed tool versions

This only removes the installed version, it does not modify mise.toml.

Delete all installed versions

Do not actually delete anything

**Examples:**

Example 1 (unknown):
```unknown
# will uninstall specific version
$ mise uninstall node@18.0.0

# will uninstall the current node version (if only one version is installed)
$ mise uninstall node

# will uninstall all installed versions of node
$ mise uninstall --all node@18.0.0 # will uninstall all node versions
```

---

## mise generate tool-stub ​

**URL:** https://mise.jdx.dev/cli/generate/tool-stub.html

**Contents:**
- mise generate tool-stub ​
- Arguments ​
  - <OUTPUT> ​
- Flags ​
  - --version <VERSION> ​
  - -u --url <URL> ​
  - --platform-url… <PLATFORM_URL> ​
  - --platform-bin… <PLATFORM_BIN> ​
  - -b --bin <BIN> ​
  - --skip-download ​

Generate a tool stub for HTTP-based tools

This command generates tool stubs that can automatically download and execute tools from HTTP URLs. It can detect checksums, file sizes, and binary paths automatically by downloading and analyzing the tool.

When generating stubs with platform-specific URLs, the command will append new platforms to existing stub files rather than overwriting them. This allows you to incrementally build cross-platform tool stubs.

Output file path for the tool stub

URL for downloading the tool

Example: https://github.com/owner/repo/releases/download/v2.0.0/tool-linux-x64.tar.gz

Platform-specific URLs in the format platform:url or just url (auto-detect platform)

When the output file already exists, new platforms will be appended to the existing platforms table. Existing platform URLs will be updated if specified again.

If only a URL is provided (without platform:), the platform will be automatically detected from the URL filename.

Examples: --platform-url linux-x64:https://... --platform-url https://nodejs.org/dist/v22.17.1/node-v22.17.1-darwin-arm64.tar.gz

Platform-specific binary paths in the format platform:path

Examples: --platform-bin windows-x64:tool.exe --platform-bin linux-x64:bin/tool

Binary path within the extracted archive

If not specified and the archive is downloaded, will auto-detect the most likely binary

Skip downloading for checksum and binary path detection (faster but less informative)

Fetch checksums and sizes for an existing tool stub file

This reads an existing stub file and fills in any missing checksum/size fields by downloading the files. URLs must already be present in the stub.

HTTP backend type to use

**Examples:**

Example 1 (unknown):
```unknown
Generate a tool stub for a single URL:
$ mise generate tool-stub ./bin/gh --url "https://github.com/cli/cli/releases/download/v2.336.0/gh_2.336.0_linux_amd64.tar.gz"

Generate a tool stub with platform-specific URLs:
$ mise generate tool-stub ./bin/rg \
    --platform-url linux-x64:https://github.com/BurntSushi/ripgrep/releases/download/14.0.3/ripgrep-14.0.3-x86_64-unknown-linux-musl.tar.gz \
    --platform-url darwin-arm64:https://github.com/BurntSushi/ripgrep/releases/download/14.0.3/ripgrep-14.0.3-aarch64-apple-darwin.tar.gz

Append additional platforms to an existing stub:
$ mise generate tool-stub ./bin/rg \
    --platform-url linux-x64:https://example.com/rg-linux.tar.gz
$ mise generate tool-stub ./bin/rg \
    --platform-url darwin-arm64:https://example.com/rg-darwin.tar.gz
# The stub now contains both platforms

Use auto-detection for platform from URL:
$ mise generate tool-stub ./bin/node \
    --platform-url https://nodejs.org/dist/v22.17.1/node-v22.17.1-darwin-arm64.tar.gz
# Platform 'macos-arm64' will be auto-detected from the URL

Generate with platform-specific binary paths:
$ mise generate tool-stub ./bin/tool \
    --platform-url linux-x64:https://example.com/tool-linux.tar.gz \
    --platform-url windows-x64:https://example.com/tool-windows.zip \
    --platform-bin windows-x64:tool.exe

Generate without downloading (faster):
$ mise generate tool-stub ./bin/tool --url "https://example.com/tool.tar.gz" --skip-download

Fetch checksums for an existing stub:
$ mise generate tool-stub ./bin/jq --fetch
# This will read the existing stub and download files to fill in any missing checksums/sizes
```

---

## mise sync ruby ​

**URL:** https://mise.jdx.dev/cli/sync/ruby.html

**Contents:**
- mise sync ruby ​
- Flags ​
  - --brew ​

Symlinks all ruby tool versions from an external tool into mise

Get tool versions from Homebrew

**Examples:**

Example 1 (unknown):
```unknown
brew install ruby
mise sync ruby --brew
mise use -g ruby - Use the latest version of Ruby installed by Homebrew
```

---

## mise plugins ls ​

**URL:** https://mise.jdx.dev/cli/plugins/ls.html

**Contents:**
- mise plugins ls ​
- Flags ​
  - -u --urls ​

List installed plugins

Can also show remotely available plugins to install.

Show the git url for each plugin e.g.: https://github.com/asdf-vm/asdf-nodejs.git

**Examples:**

Example 1 (unknown):
```unknown
$ mise plugins ls
node
ruby

$ mise plugins ls --urls
node    https://github.com/asdf-vm/asdf-nodejs.git
ruby    https://github.com/asdf-vm/asdf-ruby.git
```

---

## mise doctor path ​

**URL:** https://mise.jdx.dev/cli/doctor/path.html

**Contents:**
- mise doctor path ​
- Flags ​
  - -f --full ​

Print the current PATH entries mise is providing

Print all entries including those not provided by mise

**Examples:**

Example 1 (unknown):
```unknown
Get the current PATH entries mise is providing
$ mise path
/home/user/.local/share/mise/installs/node/24.0.0/bin
/home/user/.local/share/mise/installs/rust/1.90.0/bin
/home/user/.local/share/mise/installs/python/3.10.0/bin
```

---

## mise sync node ​

**URL:** https://mise.jdx.dev/cli/sync/node.html

**Contents:**
- mise sync node ​
- Flags ​
  - --brew ​
  - --nvm ​
  - --nodenv ​

Symlinks all tool versions from an external tool into mise

For example, use this to import all Homebrew node installs into mise

This won't overwrite any existing installs but will overwrite any existing symlinks

Get tool versions from Homebrew

Get tool versions from nvm

Get tool versions from nodenv

**Examples:**

Example 1 (unknown):
```unknown
brew install node@18 node@20
mise sync node --brew
mise use -g node@18 - uses Homebrew-provided node
```

---

## mise implode ​

**URL:** https://mise.jdx.dev/cli/implode.html

**Contents:**
- mise implode ​
- Flags ​
  - --config ​
  - -n --dry-run ​

Removes mise CLI and all related data

Skips config directory by default.

Also remove config directory

List directories that would be removed without actually removing them

---

## mise plugins install ​

**URL:** https://mise.jdx.dev/cli/plugins/install.html

**Contents:**
- mise plugins install ​
- Arguments ​
  - [NEW_PLUGIN] ​
  - [GIT_URL] ​
- Flags ​
  - -f --force ​
  - -a --all ​
  - -v --verbose… ​
  - -j --jobs <JOBS> ​

note that mise automatically can install plugins when you install a tool e.g.: mise install node@20 will autoinstall the node plugin

This behavior can be modified in ~/.config/mise/config.toml

The name of the plugin to install e.g.: node, ruby Can specify multiple plugins: mise plugins install node ruby python

The git url of the plugin

Reinstall even if plugin exists

Install all missing plugins This will only install plugins that have matching shorthands. i.e.: they don't need the full git repo url

Show installation output

Number of jobs to run in parallel

**Examples:**

Example 1 (unknown):
```unknown
# install the poetry via shorthand
$ mise plugins install poetry

# install the poetry plugin using a specific git url
$ mise plugins install poetry https://github.com/mise-plugins/mise-poetry.git

# install the poetry plugin using the git url only
# (poetry is inferred from the url)
$ mise plugins install https://github.com/mise-plugins/mise-poetry.git

# install the poetry plugin using a specific ref
$ mise plugins install poetry https://github.com/mise-plugins/mise-poetry.git#11d0c1e
```

---

## mise backends ls ​

**URL:** https://mise.jdx.dev/cli/backends/ls.html

**Contents:**
- mise backends ls ​

List built-in backends

**Examples:**

Example 1 (unknown):
```unknown
$ mise backends ls
aqua
asdf
cargo
core
dotnet
gem
go
npm
pipx
spm
ubi
vfox
```

---

## mise alias set ​

**URL:** https://mise.jdx.dev/cli/alias/set.html

**Contents:**
- mise alias set ​
- Arguments ​
  - <PLUGIN> ​
  - <ALIAS> ​
  - [VALUE] ​

Add/update an alias for a backend/plugin

This modifies the contents of ~/.config/mise/config.toml

The backend/plugin to set the alias for

The value to set the alias to

**Examples:**

Example 1 (unknown):
```unknown
mise alias set maven asdf:mise-plugins/mise-maven
mise alias set node lts-jod 22.0.0
```

---

## mise install-into ​

**URL:** https://mise.jdx.dev/cli/install-into.html

**Contents:**
- mise install-into ​
- Arguments ​
  - <TOOL@VERSION> ​
  - <PATH> ​

Install a tool version to a specific path

Used for building a tool to a directory for use outside of mise

Tool to install e.g.: node@20

Path to install the tool into

**Examples:**

Example 1 (unknown):
```unknown
# install node@20.0.0 into ./mynode
$ mise install-into node@20.0.0 ./mynode && ./mynode/bin/node -v
20.0.0
```

---

## mise tool ​

**URL:** https://mise.jdx.dev/cli/tool.html

**Contents:**
- mise tool ​
- Arguments ​
  - <TOOL> ​
- Flags ​
  - -J --json ​
  - --backend ​
  - --description ​
  - --installed ​
  - --active ​
  - --requested ​

Gets information about a tool

Tool name to get information about

Output in JSON format

Only show backend field

Only show description field

Only show installed versions

Only show active versions

Only show requested versions

Only show config source

Only show tool options

**Examples:**

Example 1 (unknown):
```unknown
$ mise tool node
Backend:            core
Installed Versions: 20.0.0 22.0.0
Active Version:     20.0.0
Requested Version:  20
Config Source:      ~/.config/mise/mise.toml
Tool Options:       [none]
```

---

## mise completion ​

**URL:** https://mise.jdx.dev/cli/completion.html

**Contents:**
- mise completion ​
- Arguments ​
  - [SHELL] ​
- Flags ​
  - --include-bash-completion-lib ​

Generate shell completions

Shell type to generate completions for

Include the bash completion library in the bash completion script

This is required for completions to work in bash, but it is not included by default you may source it separately or enable this flag to include it in the script.

**Examples:**

Example 1 (unknown):
```unknown
mise completion bash --include-bash-completion-lib > ~/.local/share/bash-completion/completions/mise
mise completion zsh  > /usr/local/share/zsh/site-functions/_mise
mise completion fish > ~/.config/fish/completions/mise.fish
```

---

## mise cache clear ​

**URL:** https://mise.jdx.dev/cli/cache/clear.html

**Contents:**
- mise cache clear ​
- Arguments ​
  - [PLUGIN]… ​

Deletes all cache files in mise

Plugin(s) to clear cache for e.g.: node, python

---

## mise mcp ​

**URL:** https://mise.jdx.dev/cli/mcp.html

**Contents:**
- mise mcp ​

[experimental] Run Model Context Protocol (MCP) server

This command starts an MCP server that exposes mise functionality to AI assistants over stdin/stdout using JSON-RPC protocol.

The MCP server provides access to:

Note: This is primarily intended for integration with AI assistants like Claude, Cursor, or other tools that support the Model Context Protocol.

**Examples:**

Example 1 (unknown):
```unknown
# Start the MCP server (typically used by AI assistant tools)
$ mise mcp

# Example integration with Claude Desktop (add to claude_desktop_config.json):
{
  "mcpServers": {
    "mise": {
      "command": "mise",
      "args": ["mcp"]
    }
  }
}

# Interactive testing with JSON-RPC commands:
$ echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | mise mcp

# Resources you can query:
- mise://tools - List active tools
- mise://tools?include_inactive=true - List all installed tools
- mise://tasks - List all tasks
- mise://env - List environment variables
- mise://config - Show configuration info
```

---

## mise deactivate ​

**URL:** https://mise.jdx.dev/cli/deactivate.html

**Contents:**
- mise deactivate ​

Disable mise for current shell session

This can be used to temporarily disable mise in a shell session.

**Examples:**

Example 1 (unknown):
```unknown
mise deactivate
```

---

## mise latest ​

**URL:** https://mise.jdx.dev/cli/latest.html

**Contents:**
- mise latest ​
- Arguments ​
  - <TOOL@VERSION> ​
- Flags ​
  - -i --installed ​

Gets the latest available version for a plugin

Supports prefixes such as node@20 to get the latest version of node 20.

Tool to get the latest version of

Show latest installed instead of available version

**Examples:**

Example 1 (unknown):
```unknown
$ mise latest node@20  # get the latest version of node 20
20.0.0

$ mise latest node     # get the latest stable version of node
20.0.0
```

---

## mise registry ​

**URL:** https://mise.jdx.dev/cli/registry.html

**Contents:**
- mise registry ​
- Arguments ​
  - [NAME] ​
- Flags ​
  - -b --backend <BACKEND> ​
  - --hide-aliased ​

List available tools to install

This command lists the tools available in the registry as shorthand names.

For example, poetry is shorthand for asdf:mise-plugins/mise-poetry.

Show only the specified tool's full name

Show only tools for this backend

**Examples:**

Example 1 (unknown):
```unknown
$ mise registry
node    core:node
poetry  asdf:mise-plugins/mise-poetry
ubi     cargo:ubi-cli

$ mise registry poetry
asdf:mise-plugins/mise-poetry
```

---

## mise where ​

**URL:** https://mise.jdx.dev/cli/where.html

**Contents:**
- mise where ​
- Arguments ​
  - <TOOL@VERSION> ​

Display the installation path for a tool

The tool must be installed for this to work.

Tool(s) to look up e.g.: ruby@3 if "@<PREFIX>" is specified, it will show the latest installed version that matches the prefix otherwise, it will show the current, active installed version

**Examples:**

Example 1 (unknown):
```unknown
# Show the latest installed version of node
# If it is is not installed, errors
$ mise where node@20
/home/jdx/.local/share/mise/installs/node/20.0.0

# Show the current, active install directory of node
# Errors if node is not referenced in any .tool-version file
$ mise where node
/home/jdx/.local/share/mise/installs/node/20.0.0
```

---

## mise generate bootstrap ​

**URL:** https://mise.jdx.dev/cli/generate/bootstrap.html

**Contents:**
- mise generate bootstrap ​
- Flags ​
  - -l --localize ​
  - --localized-dir <LOCALIZED_DIR> ​
  - -V --version <VERSION> ​
  - -w --write <WRITE> ​

Generate a script to download+execute mise

This is designed to be used in a project where contributors may not have mise installed.

Sandboxes mise internal directories like MISE_DATA_DIR and MISE_CACHE_DIR into a .mise directory in the project

This is necessary if users may use a different version of mise outside the project.

Directory to put localized data into

Specify mise version to fetch

instead of outputting the script to stdout, write to a file and make it executable

**Examples:**

Example 1 (unknown):
```unknown
mise generate bootstrap >./bin/mise
chmod +x ./bin/mise
./bin/mise install – automatically downloads mise to .mise if not already installed
```

---

## mise alias unset ​

**URL:** https://mise.jdx.dev/cli/alias/unset.html

**Contents:**
- mise alias unset ​
- Arguments ​
  - <PLUGIN> ​
  - [ALIAS] ​

Clears an alias for a backend/plugin

This modifies the contents of ~/.config/mise/config.toml

The backend/plugin to remove the alias from

**Examples:**

Example 1 (unknown):
```unknown
mise alias unset maven
mise alias unset node lts-jod
```

---

## mise cache path ​

**URL:** https://mise.jdx.dev/cli/cache/path.html

**Contents:**
- mise cache path ​

Show the cache directory path

---

## mise sync python ​

**URL:** https://mise.jdx.dev/cli/sync/python.html

**Contents:**
- mise sync python ​
- Flags ​
  - --pyenv ​
  - --uv ​

Symlinks all tool versions from an external tool into mise

For example, use this to import all pyenv installs into mise

This won't overwrite any existing installs but will overwrite any existing symlinks

Get tool versions from pyenv

Sync tool versions with uv (2-way sync)

**Examples:**

Example 1 (unknown):
```unknown
pyenv install 3.11.0
mise sync python --pyenv
mise use -g python@3.11.0 - uses pyenv-provided python

uv python install 3.11.0
mise install python@3.10.0
mise sync python --uv
mise x python@3.11.0 -- python -V - uses uv-provided python
uv run -p 3.10.0 -- python -V - uses mise-provided python
```

---

## mise link ​

**URL:** https://mise.jdx.dev/cli/link.html

**Contents:**
- mise link ​
- Arguments ​
  - <TOOL@VERSION> ​
  - <PATH> ​
- Flags ​
  - -f --force ​

Symlinks a tool version into mise

Use this for adding installs either custom compiled outside mise or built with a different tool.

Tool name and version to create a symlink for

The local path to the tool version e.g.: ~/.nvm/versions/node/v20.0.0

Overwrite an existing tool version if it exists

**Examples:**

Example 1 (unknown):
```unknown
# build node-20.0.0 with node-build and link it into mise
$ node-build 20.0.0 ~/.nodes/20.0.0
$ mise link node@20.0.0 ~/.nodes/20.0.0

# have mise use the node version provided by Homebrew
$ brew install node
$ mise link node@brew $(brew --prefix node)
$ mise use node@brew
```

---

## mise alias ​

**URL:** https://mise.jdx.dev/cli/alias.html

**Contents:**
- mise alias ​
- Flags ​
  - -p --plugin <PLUGIN> ​
  - --no-header ​
- Subcommands ​

Manage version aliases.

filter aliases by plugin

Don't show table header

---

## mise bin-paths ​

**URL:** https://mise.jdx.dev/cli/bin-paths.html

**Contents:**
- mise bin-paths ​
- Arguments ​
  - [TOOL@VERSION]… ​

List all the active runtime bin paths

Tool(s) to look up e.g.: ruby@3

---

## mise generate github-action ​

**URL:** https://mise.jdx.dev/cli/generate/github-action.html

**Contents:**
- mise generate github-action ​
- Flags ​
  - --name <NAME> ​
  - -t --task <TASK> ​
  - -w --write ​

Generate a GitHub Action workflow file

This command generates a GitHub Action workflow file that runs a mise task like mise run ci when you push changes to your repository.

the name of the workflow to generate

The task to run when the workflow is triggered

write to .github/workflows/$name.yml

**Examples:**

Example 1 (unknown):
```unknown
mise generate github-action --write --task=ci
git commit -m "feat: add new feature"
git push # runs `mise run ci` on GitHub
```

---

## mise backends ​

**URL:** https://mise.jdx.dev/cli/backends.html

**Contents:**
- mise backends ​
- Subcommands ​

---

## mise plugins uninstall ​

**URL:** https://mise.jdx.dev/cli/plugins/uninstall.html

**Contents:**
- mise plugins uninstall ​
- Arguments ​
  - [PLUGIN]… ​
- Flags ​
  - -p --purge ​
  - -a --all ​

Also remove the plugin's installs, downloads, and cache

**Examples:**

Example 1 (unknown):
```unknown
mise uninstall node
```

---

## mise trust ​

**URL:** https://mise.jdx.dev/cli/trust.html

**Contents:**
- mise trust ​
- Arguments ​
  - [CONFIG_FILE] ​
- Flags ​
  - -a --all ​
  - --ignore ​
  - --untrust ​
  - --show ​

Marks a config file as trusted

This means mise will parse the file with potentially dangerous features enabled.

The config file to trust

Trust all config files in the current directory and its parents

Do not trust this config and ignore it in the future

No longer trust this config, will prompt in the future

Show the trusted status of config files from the current directory and its parents. Does not trust or untrust any files.

**Examples:**

Example 1 (unknown):
```unknown
# trusts ~/some_dir/mise.toml
$ mise trust ~/some_dir/mise.toml

# trusts mise.toml in the current or parent directory
$ mise trust
```

---

## mise alias ls ​

**URL:** https://mise.jdx.dev/cli/alias/ls.html

**Contents:**
- mise alias ls ​
- Arguments ​
  - [TOOL] ​
- Flags ​
  - --no-header ​

List aliases Shows the aliases that can be specified. These can come from user config or from plugins in bin/list-aliases.

For user config, aliases are defined like the following in ~/.config/mise/config.toml:

Show aliases for <TOOL>

Don't show table header

**Examples:**

Example 1 (unknown):
```unknown
[alias.node.versions]
lts = "22.0.0"
```

Example 2 (unknown):
```unknown
$ mise aliases
node  lts-jod      22
```

---

## mise cache ​

**URL:** https://mise.jdx.dev/cli/cache.html

**Contents:**
- mise cache ​
- Subcommands ​

Manage the mise cache

Run mise cache with no args to view the current cache directory.

---

## mise doctor ​

**URL:** https://mise.jdx.dev/cli/doctor.html

**Contents:**
- mise doctor ​
- Flags ​
  - -J --json ​
- Subcommands ​

Check mise installation for possible problems

**Examples:**

Example 1 (unknown):
```unknown
$ mise doctor
[WARN] plugin node is not installed
```

---

## mise generate ​

**URL:** https://mise.jdx.dev/cli/generate.html

**Contents:**
- mise generate ​
- Subcommands ​

Generate files for various tools/services

---

## mise search ​

**URL:** https://mise.jdx.dev/cli/search.html

**Contents:**
- mise search ​
- Arguments ​
  - [NAME] ​
- Flags ​
  - -i --interactive ​
  - -m --match-type <MATCH_TYPE> ​
  - --no-header ​

Search for tools in the registry

This command searches a tool in the registry.

By default, it will show all tools that fuzzy match the search term. For non-fuzzy matches, use the --match-type flag.

The tool to search for

Show interactive search

Match type: equal, contains, or fuzzy

Don't display headers

**Examples:**

Example 1 (unknown):
```unknown
$ mise search jq
Tool  Description
jq    Command-line JSON processor. https://github.com/jqlang/jq
jqp   A TUI playground to experiment with jq. https://github.com/noahgorstein/jqp
jiq   jid on jq - interactive JSON query tool using jq expressions. https://github.com/fiatjaf/jiq
gojq  Pure Go implementation of jq. https://github.com/itchyny/gojq

$ mise search --interactive
Tool
Search a tool
❯ jq    Command-line JSON processor. https://github.com/jqlang/jq
  jqp   A TUI playground to experiment with jq. https://github.com/noahgorstein/jqp
  jiq   jid on jq - interactive JSON query tool using jq expressions. https://github.com/fiatjaf/jiq
  gojq  Pure Go implementation of jq. https://github.com/itchyny/gojq
/jq 
esc clear filter • enter confirm
```

---

## mise reshim ​

**URL:** https://mise.jdx.dev/cli/reshim.html

**Contents:**
- mise reshim ​
- Flags ​
  - -f --force ​

Creates new shims based on bin paths from currently installed tools.

This creates new shims in ~/.local/share/mise/shims for CLIs that have been added. mise will try to do this automatically for commands like npm i -g but there are other ways to install things (like using yarn or pnpm for node) that mise does not know about and so it will be necessary to call this explicitly.

If you think mise should automatically call this for a particular command, please open an issue on the mise repo. You can also setup a shell function to reshim automatically (it's really fast so you don't need to worry about overhead):

Note that this creates shims for all installed tools, not just the ones that are currently active in mise.toml.

Removes all shims before reshimming

**Examples:**

Example 1 (unknown):
```unknown
npm() {
  command npm "$@"
  mise reshim
}
```

Example 2 (unknown):
```unknown
$ mise reshim
$ ~/.local/share/mise/shims/node -v
v20.0.0
```

---

## mise activate ​

**URL:** https://mise.jdx.dev/cli/activate.html

**Contents:**
- mise activate ​
- Arguments ​
  - [SHELL_TYPE] ​
- Flags ​
  - --shims ​
  - -q --quiet ​
  - --no-hook-env ​

Initializes mise in the current shell session

This should go into your shell's rc file or login shell. Otherwise, it will only take effect in the current session. (e.g. ~/.zshrc, ~/.zprofile, ~/.zshenv, ~/.bashrc, ~/.bash_profile, ~/.profile, ~/.config/fish/config.fish, or $PROFILE for powershell)

Typically, this can be added with something like the following:

However, this requires that "mise" is in your PATH. If it is not, you need to specify the full path like this:

Customize status output with status settings.

Shell type to generate the script for

Use shims instead of modifying PATH Effectively the same as:

mise activate --shims does not support all the features of mise activate. See https://mise.jdx.dev/dev-tools/shims.html#shims-vs-path for more information

Suppress non-error messages

Do not automatically call hook-env

This can be helpful for debugging mise. If you run eval "$(mise activate --no-hook-env)", then you can call mise hook-env manually which will output the env vars to stdout without actually modifying the environment. That way you can do things like mise hook-env --trace to get more information or just see the values that hook-env is outputting.

**Examples:**

Example 1 (unknown):
```unknown
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc
```

Example 2 (unknown):
```unknown
echo 'eval "$(/path/to/mise activate zsh)"' >> ~/.zshrc
```

Example 3 (unknown):
```unknown
PATH="$HOME/.local/share/mise/shims:$PATH"
```

Example 4 (unknown):
```unknown
eval "$(mise activate bash)"
eval "$(mise activate zsh)"
mise activate fish | source
execx($(mise activate xonsh))
(&mise activate pwsh) | Out-String | Invoke-Expression
```

---

## mise self-update ​

**URL:** https://mise.jdx.dev/cli/self-update.html

**Contents:**
- mise self-update ​
- Arguments ​
  - [VERSION] ​
- Flags ​
  - -f --force ​
  - --no-plugins ​
  - -y --yes ​

Uses the GitHub Releases API to find the latest release and binary. By default, this will also update any installed plugins. Uses the GITHUB_API_TOKEN environment variable if set for higher rate limits.

This command is not available if mise is installed via a package manager.

Update to a specific version

Update even if already up to date

Disable auto-updating plugins

Skip confirmation prompt

---

## mise plugins ls-remote ​

**URL:** https://mise.jdx.dev/cli/plugins/ls-remote.html

**Contents:**
- mise plugins ls-remote ​
- Flags ​
  - -u --urls ​
  - --only-names ​

List all available remote plugins

The full list is here: https://github.com/jdx/mise/blob/main/registry.toml

Show the git url for each plugin e.g.: https://github.com/mise-plugins/mise-poetry.git

Only show the name of each plugin by default it will show a "*" next to installed plugins

**Examples:**

Example 1 (unknown):
```unknown
mise plugins ls-remote
```

---

## mise generate devcontainer ​

**URL:** https://mise.jdx.dev/cli/generate/devcontainer.html

**Contents:**
- mise generate devcontainer ​
- Flags ​
  - -n --name <NAME> ​
  - -i --image <IMAGE> ​
  - -m --mount-mise-data ​
  - -w --write ​

Generate a devcontainer to execute mise

The name of the devcontainer

The image to use for the devcontainer

Bind the mise-data-volume to the devcontainer

write to .devcontainer/devcontainer.json

**Examples:**

Example 1 (unknown):
```unknown
mise generate devcontainer
```

---

## mise which ​

**URL:** https://mise.jdx.dev/cli/which.html

**Contents:**
- mise which ​
- Arguments ​
  - [BIN_NAME] ​
- Flags ​
  - --plugin ​
  - --version ​
  - -t --tool <TOOL@VERSION> ​

Shows the path that a tool's bin points to.

Use this to figure out what version of a tool is currently active.

Show the plugin name instead of the path

Show the version instead of the path

Use a specific tool@version e.g.: mise which npm --tool=node@20

**Examples:**

Example 1 (unknown):
```unknown
$ mise which node
/home/username/.local/share/mise/installs/node/20.0.0/bin/node

$ mise which node --plugin
node

$ mise which node --version
20.0.0
```

---

## mise alias get ​

**URL:** https://mise.jdx.dev/cli/alias/get.html

**Contents:**
- mise alias get ​
- Arguments ​
  - <PLUGIN> ​
  - <ALIAS> ​

Show an alias for a plugin

This is the contents of an alias.<PLUGIN> entry in ~/.config/mise/config.toml

The plugin to show the alias for

**Examples:**

Example 1 (unknown):
```unknown
$ mise alias get node lts-hydrogen
20.0.0
```

---
