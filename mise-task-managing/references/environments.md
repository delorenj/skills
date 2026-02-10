# Mise-Task-Managing - Environments

**Pages:** 12

---

## Secrets ​

**URL:** https://mise.jdx.dev/environments/secrets/

**Contents:**
- Secrets ​

Use mise to manage sensitive environment variables securely. There are multiple supported approaches:

---

## mise set ​

**URL:** https://mise.jdx.dev/cli/set.html

**Contents:**
- mise set ​
- Arguments ​
  - [ENV_VAR]… ​
- Flags ​
  - --file <FILE> ​
  - -g --global ​
  - -E --env <ENV> ​
  - --prompt ​
  - --age-encrypt ​
  - --age-recipient… <RECIPIENT> ​

Set environment variables in mise.toml

By default, this command modifies mise.toml in the current directory. Use -E <env> to create/modify environment-specific config files like mise.<env>.toml.

Environment variable(s) to set e.g.: NODE_ENV=production

The TOML file to update

Can be a file path or directory. If a directory is provided, will create/use mise.toml in that directory. Defaults to MISE_DEFAULT_CONFIG_FILENAME environment variable, or mise.toml.

Set the environment variable in the global config file

Create/modify an environment-specific config file like .mise.<env>.toml

Prompt for environment variable values

[experimental] Encrypt the value with age before storing

[experimental] Age recipient (x25519 public key) for encryption

Can be used multiple times. Requires --age-encrypt.

[experimental] SSH recipient (public key or path) for age encryption

Can be used multiple times. Requires --age-encrypt.

[experimental] Age identity file for encryption

Defaults to ~/.config/mise/age.txt if it exists

**Examples:**

Example 1 (unknown):
```unknown
$ mise set NODE_ENV=production

$ mise set NODE_ENV
production

$ mise set -E staging NODE_ENV=staging
# creates or modifies mise.staging.toml

$ mise set
key       value       source
NODE_ENV  production  ~/.config/mise/config.toml

$ mise set --prompt PASSWORD
Enter value for PASSWORD: [hidden input]

[experimental] Age Encryption:

$ mise set --age-encrypt API_KEY=secret

$ mise set --age-encrypt --prompt API_KEY
Enter value for API_KEY: [hidden input]
```

---

## mise shell ​

**URL:** https://mise.jdx.dev/cli/shell.html

**Contents:**
- mise shell ​
- Arguments ​
  - <TOOL@VERSION>… ​
- Flags ​
  - -j --jobs <JOBS> ​
  - --raw ​
  - -u --unset ​

Sets a tool version for the current session.

Only works in a session where mise is already activated.

This works by setting environment variables for the current shell session such as MISE_NODE_VERSION=20 which is "eval"ed as a shell function created by mise activate.

Number of jobs to run in parallel [default: 4]

Directly pipe stdin/stdout/stderr from plugin to user Sets --jobs=1

Removes a previously set version

**Examples:**

Example 1 (unknown):
```unknown
$ mise shell node@20
$ node -v
v20.0.0
```

---

## mise en ​

**URL:** https://mise.jdx.dev/cli/en.html

**Contents:**
- mise en ​
- Arguments ​
  - [DIR] ​
- Flags ​
  - -s --shell <SHELL> ​

Starts a new shell with the mise environment built from the current configuration

This is an alternative to mise activate that allows you to explicitly start a mise session. It will have the tools and environment variables in the configs loaded. Note that changing directories will not update the mise environment.

Directory to start the shell in

**Examples:**

Example 1 (unknown):
```unknown
$ mise en .
$ node -v
v20.0.0

Skip loading bashrc:
$ mise en -s "bash --norc"

Skip loading zshrc:
$ mise en -s "zsh -f"
```

---

## Shims ​

**URL:** https://mise.jdx.dev/dev-tools/shims.html

**Contents:**
- Shims ​
- Overview of the mise activation methods ​
  - PATH activation ​
  - Shims ​
- How to add mise shims to PATH ​
  - mise reshim ​
- Shims vs PATH ​
  - Env vars and shims ​
  - Hooks and shims ​
  - which ​

There are several ways for the mise context (dev tools, environment variables) to be loaded into your shell:

This page will help you understand the differences between these methods and how to use them. In particular, it will help you decide if you should use shims or mise activate in your shell.

Mise's "PATH" activation method updates environment variables every time the prompt is displayed. In particular, it updates the PATH environment variable, which is used by your shell to search for the programs it can run.

This is the method used when you add the echo 'eval "$(mise activate bash)"' >> ~/.bashrc line to your shell rc file (in this case, for bash).

For example, by default, your PATH variable might look like this:

If using mise activate, mise will automatically add the required tools to PATH.

In this example, the python bin directory was added at the beginning of the PATH, making it available in the current shell session.

While the PATH design of mise works great in most cases, there are some situations where shims are preferable. This is the case when you are not using an interactive shell (for example, when using mise in an IDE or a script).

mise activate --shims does not support all the features of mise activate. See shims vs path for more information.

When using shims, mise places small executables (shims) in a directory that is included in your PATH. You can think of shims as symlinks to the mise binary that intercept commands and load the appropriate context.

By default, the shim directory is located at ~/.local/share/mise/shims. When installing a tool (for example, node), mise will add some entries for every binary provided by this tool in the shims directory (for example, ~/.local/share/mise/shims/node).

To avoid calling ~/.local/share/mise/shims/node, you can add the shims directory to your PATH.

This will effectively make all dev tools available in your current shell session as well as non-interactive environments.

mise activate --shims is a shorthand for adding the shims directory to PATH.

The recommended way to add shims to PATH is to call mise activate --shims in one of your shell initialization file. For example, you can do the following:

In this example, we use mise activate --shims in the non-interactive shell configuration file (like .bash_profile or .zprofile) and mise activate in the interactive shell configuration file (like .bashrc or .zshrc)

mise activate will remove the shims directory from the PATH so it's fine to call mise activate --shims in your shell profile file then later call mise activate in an interactive session.

To force mise to update the content of the shims directory, you can manually call mise reshim.

Note that mise already runs a reshim anytime a tool is installed/updated/removed, so you don't need to use it for those scenarios. It is also done by default when using most tools such as npm.

mise reshim only creates/removes the shims. Some users sometimes use it as a "fix it" button, but it is only necessary if ~/.local/share/mise/shims doesn't contain something it should.

Do not add additional executable in the mise directory, mise will delete them with the next reshim.

The following features are affected when shims are used instead of PATH activation:

In general, using PATH (mise activate) instead of shims for interactive situations is recommended.

The way activate works is every time the prompt is displayed, mise-en-place will determine what PATH and other env vars should be and export them. This is why it doesn't work well for non-interactive situations like scripts. The prompt never gets displayed so you have to manually call mise hook-env to get mise to update the env vars. (though there are exceptions, see hook on cd)

A downside of shims is that the environment variables are only loaded when a shim is called. This means if you set an environment variable in mise.toml, it will only be used when a shim is called.

The following example only works under mise activate:

But this will work in either:

Also, mise x|exec and mise r|run can be used to get the environment even if you don't need any mise tools:

In general, tasks are a good way to ensure that the mise environment is always loaded.

The hooks cd, enter, exit, and watch_files only trigger with mise activate. However preinstall and postinstall still work with shims because they don't require shell integration.

which is a command that a lot of users find great value in. Using shims effectively "break" which and cause it to show the location of the shim. A workaround is to use mise which will show the actual location. Some users prefer the "cleanliness" of running which node and getting back a real path with a version number inside of it. e.g:

Truthfully, you're probably not going to notice a difference in performance when using shims vs. using mise activate.

If you are calling a shim from within a bash script like this:

You'll pay the mise penalty every time you call it within the loop. However, if you did the same thing but call a subprocess from within a shim (say, node creating a node subprocess), you will not pay a new penalty. This is because when a shim is called, mise sets up the environment with PATH for all tools and those PATH entries will be before the shim directory.

In other words, which is better in terms of performance just depends on how you're calling mise. Really though most users will not notice a few ms lag on their terminal caused by mise activate.

The only difference between these would be that using hook-env you will need to call it again if you change directories but with shims that won't be necessary. The shims directory will be removed by mise activate automatically so you won't need to worry about dealing with shims in your PATH.

There are many ways to load the mise environment that don't require either, chiefly: mise x|exec, mise r|run or mise en.

These will both load all the tools and env vars before executing something. This might be ideal because you don't need to modify your shell rc file at all and the environment is always loaded explicitly. Some might find this is a "clean" way of working.

The obvious downside is that anytime one wants to use mise they need to prefix it with mise exec|run. Though, you can easily alias them to mx|mr.

This is the method Jeff uses

Part of the reason for this is I often need to make sure I'm on my development version of mise. If you work on mise yourself I would recommend working in a similar way and disabling mise activate or shims while you are working on it.

See How I use mise for more information.

For some shells (bash, zsh, fish, xonsh), mise hooks into the cd command, while in others, it only runs when the prompt is displayed. This relies on chpwd in zsh, PROMPT_COMMAND in bash, fish_prompt in fish, and on_chdir in xonsh.

The upside is that it doesn't run as frequently but since mise is written in Rust the cost for executing mise is negligible (a few ms).

If you run a set of commands in a single line like the following:

If using mise activate, in shell without hook on cd, this will use the tools from ~, not from ~/src/proj1 or ~/src/proj2 even after the directory changed.

This is because, in these shells mise runs just before your prompt gets displayed whereas in others, it hooks on cd. Note that shims will always work with the inline example above.

rc files like .zshrc are unusual. It's a script but also runs only for interactive sessions. If you need to access tools provided by mise inside of an rc file you have 2 options:

**Examples:**

Example 1 (unknown):
```unknown
echo $PATH
/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
```

Example 2 (unknown):
```unknown
PATH="$HOME/.local/share/mise/installs/python/3.13.0/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
```

Example 3 (unknown):
```unknown
ls -l ~/.local/share/mise/shims/node
# [...] ~/.local/share/mise/shims/node -> ~/.local/bin/mise
```

Example 4 (unknown):
```unknown
mise use -g node@20
npm install -g prettier@3.1.0

~/.local/share/mise/shims/node -v
# v20.0.0
~/.local/share/mise/shims/prettier -v
# 3.1.0
```

---

## mise env ​

**URL:** https://mise.jdx.dev/cli/env.html

**Contents:**
- mise env ​
- Arguments ​
  - [TOOL@VERSION]… ​
- Flags ​
  - -J --json ​
  - --json-extended ​
  - -D --dotenv ​
  - --redacted ​
  - -s --shell <SHELL> ​
  - --values ​

Exports env vars to activate mise a single time

Use this if you don't want to permanently install mise. It's not necessary to use this if you have mise activate in your shell rc file.

Output in JSON format

Output in JSON format with additional information (source, tool)

Output in dotenv format

Only show redacted environment variables

Shell type to generate environment variables for

Only show values of environment variables

**Examples:**

Example 1 (unknown):
```unknown
eval "$(mise env -s bash)"
eval "$(mise env -s zsh)"
mise env -s fish | source
execx($(mise env -s xonsh))
```

---

## Environments ​

**URL:** https://mise.jdx.dev/environments/

**Contents:**
- Environments ​
- Using environment variables ​
- Environment in tasks ​
- Lazy eval ​
- Redactions ​
  - Viewing Redacted Environment Variables ​
- Required Variables ​
  - Required Variable Behavior ​
  - Validation Behavior ​
  - Use Cases ​

Like direnv it manages environment variables for different project directories.

Use mise to specify environment variables used for different projects.

To get started, create a mise.toml file in the root of your project directory:

To clear an env var, set it to false:

You can also use the CLI to get/set env vars:

Additionally, the mise env [--json] [--dotenv] command can be used to export the environment variables in various formats (including PATH and environment variables set by tools or plugins).

Environment variables are available when using mise x|exec, or with mise r|run (i.e. with tasks):

You can of course combine them with tools:

If mise is activated, it will automatically set environment variables in the current shell session when you cd into a directory.

If you are using shims, the environment variables will be available when using the shim:

Finally, you can also use mise en to start a new shell session with the environment variables set.

It is also possible to define environment inside a task

Environment variables typically are resolved before tools—that way you can configure tool installation with environment variables. However, sometimes you want to access environment variables produced by tools. To do that, turn the value into a map with tools = true:

Variables can be redacted from the output by setting redact = true:

You can also use the redactions array to mark multiple environment variables as sensitive:

The mise env command provides flags to work with redacted variables:

Because mise may output sensitive values that could show up in CI logs you'll need to be configure your CI setup to know which values are sensitive.

For example, when using GitHub Actions, you should use ::add-mask:: to prevent secrets from appearing in logs:

Note: If you're using mise-action, it will automatically redact values marked with redact = true or matching patterns in the redactions array.

You can mark environment variables as required by setting required = true. This ensures that the variable is defined either before mise runs or in a later config file (like mise.local.toml):

You can also provide help text to guide users on how to set the variable:

When a required variable is missing, mise will show the help text in the error message to assist users.

When a variable is marked as required = true, mise validates that it is defined through one of these sources:

Required variables are useful for:

config_root is the canonical project root directory that mise uses when resolving relative paths inside configuration files. Generally, when you use relative paths in mise you're referring to this directory.

Here's some example config files and their config_root:

You can see the implementation in config_root.rs.

env._.* define special behavior for setting environment variables. (e.g.: reading env vars from a file). Since nested environment variables do not make sense, we make use of this fact by creating a key named "_" which is a TOML table for the configuration of these directives.

In mise.toml: env._.file can be used to specify a dotenv file to load.

This uses dotenvy under the hood. If you have problems with the way env._.file works, you will likely need to post an issue there, not to mise since there is not much mise can do about the way that crate works.

The env._.file directive supports:

You can set MISE_ENV_FILE=.env to automatically load dotenv files in any directory.

See secrets for ways to read encrypted files with env._.file.

PATH is treated specially. Use env._.path to add extra directories to the PATH, making any executables in those directories available in the shell without needing to type the full path:

The env._.path directive supports:

Relative paths like tools/bin or ./tools/bin are resolved against {{config_root}}. For example, with a config file at /path/to/project/.config/mise/config.toml, tools/bin resolves to /path/to/project/tools/bin.

Source an external bash script and pull exported environment variables out of it:

This must be a script that runs in bash as if it were executed like this:

The shebang will be ignored. See #1448 for a potential alternative that would work with binaries or other script languages.

The env._.source directive supports:

Plugins can provide their own env._ directives that dynamically set environment variables and modify your PATH. This is particularly useful for:

Simple plugin activation:

Plugin with configuration options:

When you use env._.<plugin-name>, mise:

The configuration options you provide (the TOML table after =) are passed to the plugin's hooks via ctx.options, allowing plugins to be configured per-project or per-environment.

The plugin could then fetch secrets from HashiCorp Vault and expose them as environment variables.

The plugin could detect the current git branch and set ENVIRONMENT=production when on main, or ENVIRONMENT=development otherwise.

See Environment Plugins in the Plugins documentation for a complete guide to creating your own environment plugins.

For a working example, see the mise-env-sample repository.

It may be necessary to use multiple env._ directives, however TOML fails with this syntax because it has 2 identical keys in a table:

For this use-case, you can optionally make [env] an array-of-tables instead by using [[env]] instead:

It works identically but you can have multiple tables.

Environment variable values can be templates, see Templates for details.

You can use the value of an environment variable in later env vars:

Of course the ordering matters when doing this.

**Examples:**

Example 1 (unknown):
```unknown
[env]
NODE_ENV = 'production'
```

Example 2 (unknown):
```unknown
[env]
NODE_ENV = false # unset a previously set NODE_ENV
```

Example 3 (unknown):
```unknown
mise set NODE_ENV=development
# mise set NODE_ENV
# development

mise set
# key       value        source
# NODE_ENV  development  mise.toml

cat mise.toml
# [env]
# NODE_ENV = 'development'

mise unset NODE_ENV
```

Example 4 (unknown):
```unknown
mise set MY_VAR=123
mise exec -- echo $MY_VAR
# 123
```

---

## sops experimental ​

**URL:** https://mise.jdx.dev/environments/secrets/sops.html

**Contents:**
- sops experimental ​
- Example ​
- Encrypt with sops ​
- Redaction ​
  - CI masking (GitHub Actions) ​
- Settings ​
- sops.age_key
- sops.age_key_file
- sops.age_recipients
- sops.rops

mise reads encrypted secret files and makes values available as environment variables via env._.file.

mise will automatically decrypt the file if it is sops-encrypted.

Currently age is the only sops encryption method supported.

Install tools: mise use -g sops age

Generate an age key and note the public key:

The -i overwrites the file. The encrypted file is safe to commit. Set SOPS_AGE_KEY_FILE=~/.config/mise/age.txt to decrypt/edit with sops.

Now mise env exposes the values.

Mark secrets from files as sensitive:

Work with redacted values:

If you use mise-action, values marked redact = true are masked automatically.

The age private key to use for sops secret decryption.

Path to the age private key file to use for sops secret decryption.

The age public keys to use for sops secret encryption.

Use rops to decrypt sops files. Disable to shell out to sops which will slow down mise but sops may offer features not available in rops.

If true, fail when sops decryption fails (including when sops is not available, the key is missing, or the key is invalid). If false, skip decryption and continue in these cases.

**Examples:**

Example 1 (unknown):
```unknown
{
  "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
  "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
```

Example 2 (unknown):
```unknown
[env]
_.file = ".env.json"
```

Example 3 (unknown):
```unknown
age-keygen -o ~/.config/mise/age.txt
# Public key: <public key>
```

Example 4 (unknown):
```unknown
sops encrypt -i --age "<public key>" .env.json
```

---

## mise.lock Lockfile experimental ​

**URL:** https://mise.jdx.dev/dev-tools/mise-lock.html

**Contents:**
- mise.lock Lockfile experimental ​
- Overview ​
- Enabling Lockfiles ​
- How It Works ​
- File Format ​
  - Platform Information ​
  - Platform Keys ​
  - Legacy Format Migration ​
- Workflow ​
  - Initial Setup ​

mise.lock is a lockfile that pins exact versions and checksums of tools for reproducible environments. When enabled, mise will automatically maintain this file to ensure consistent tool versions across different machines and deployments.

The lockfile serves similar purposes to package-lock.json in npm or Cargo.lock in Rust:

Lockfiles are controlled by the lockfile setting:

mise.lock is a TOML file with a platform-based format that organizes asset information by platform:

Each platform in a tool's [tools.name.platforms] section uses a key format like "os-arch" (e.g., "linux-x64", "macos-arm64") and can contain:

The platform key format is generally os-arch but can be customized by backends:

Older lockfiles with separate [tools.name.assets] and [tools.name.checksums] sections are automatically migrated to the new platform-based [tools.name.platforms] format when read. The migration is seamless and maintains all existing functionality.

When you want to update tool versions:

Backend support for lockfile features varies:

If checksums become invalid or you need to regenerate them:

When merging branches with different lockfiles:

Since lockfiles are still experimental, enable them with:

The platform-based format provides several advantages:

**Examples:**

Example 1 (unknown):
```unknown
# Enable lockfiles globally
mise settings lockfile=true

# Or set in mise.toml
[settings]
lockfile = true
```

Example 2 (unknown):
```unknown
# Example mise.lock
[tools.node]
version = "20.11.0"
backend = "core:node"

[tools.node.platforms.linux-x64]
checksum = "sha256:a6c213b7a2c3b8b9c0aaf8d7f5b3a5c8d4e2f4a5b6c7d8e9f0a1b2c3d4e5f6a7"
size = 23456789
url = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-linux-x64.tar.xz"

[tools.python]
version = "3.11.7"
backend = "core:python"

[tools.python.platforms.linux-x64]
checksum = "sha256:def456..."
size = 12345678

[tools.ripgrep]
version = "14.1.1"
backend = "aqua:BurntSushi/ripgrep"

[tools.ripgrep.platforms.linux-x64]
checksum = "sha256:4cf9f2741e6c465ffdb7c26f38056a59e2a2544b51f7cc128ef28337eeae4d8e"
size = 1234567
```

Example 3 (unknown):
```unknown
# Create the lockfile
touch mise.lock

# Install tools (this will populate the lockfile)
mise install
```

Example 4 (unknown):
```unknown
# Install exact versions from lockfile
mise install

# Update tools and lockfile
mise upgrade
```

---

## Direct age Encryption experimental ​

**URL:** https://mise.jdx.dev/environments/secrets/age.html

**Contents:**
- Direct age Encryption experimental ​
- Quick start ​
- CLI flags ​
- Storage format ​
- Decryption identities ​
- Defaults for recipients (encryption) ​
- Settings ​
- age.identity_files
- age.key_file
- age.ssh_identity_files

Encrypt individual environment variable values directly in mise.toml using age encryption. The age tool is not required—mise has support built-in.

This is a simple method of storing encrypted environment variables directly in mise.toml. You can use it simply by running mise set --age-encrypt <key>=<value>. By default, mise will use your ssh key (~/.ssh/id_ed25519 or ~/.ssh/id_rsa) if it exists.

It's recommended to use --prompt to avoid accidentally exposing the value to your shell history. You don't have to though, you can use mise set --age-encrypt DB_PASSWORD="password123".

If no recipients are provided explicitly, mise will try defaults (see below).

Encrypted values are stored as base64 along with a format field:

mise looks for identities in this order:

Decrypted values are always marked as redacted.

If no identities are found or decryption fails, mise returns the encrypted value as-is (non-strict behavior).

When --age-encrypt is used without explicit recipients, mise attempts to derive recipients from:

If none are found, the command fails with an error asking you to provide recipients or configure settings.age.key_file.

[experimental] List of age identity files to use for decryption.

[experimental] Path to the age private key file to use for encryption/decryption.

[experimental] List of SSH identity files to use for age decryption.

**Examples:**

Example 1 (unknown):
```unknown
age-keygen -o ~/.config/mise/age.txt
# Note the public key output for encryption
```

Example 2 (unknown):
```unknown
mise set --age-encrypt --prompt DB_PASSWORD
# Enter value for DB_PASSWORD: [hidden input]
```

Example 3 (unknown):
```unknown
[env]
DB_PASSWORD = { age = { value = "<base64>" } }
```

Example 4 (unknown):
```unknown
mise env  # Variables are decrypted automatically
```

---

## Config Environments ​

**URL:** https://mise.jdx.dev/configuration/environments.html

**Contents:**
- Config Environments ​

It's possible to have separate mise.toml files in the same directory for different environments like development and production. To enable, either set the -E,--env option or MISE_ENV environment variable to an environment like development or production. mise will then look for a mise.{MISE_ENV}.toml file in the current directory, parent directories and the MISE_CONFIG_DIR directory.

mise will also look for "local" files like mise.local.toml and mise.{MISE_ENV}.local.toml in the current directory and parent directories. These are intended to not be committed to version control. (Add mise.local.toml and mise.*.local.toml to your .gitignore file.)

The priority of these files goes in this order (top overrides bottom):

If MISE_OVERRIDE_CONFIG_FILENAMES is set, that will be used instead of all of this.

You can also use paths like mise/config.{MISE_ENV}.toml or .config/mise.{MISE_ENV}.toml Those rules follow the order in Configuration.

Use mise config to see which files are being used.

The rules around which file is written are different because we ultimately need to choose one. See the docs for mise use for more information.

Multiple environments can be specified, e.g. MISE_ENV=ci,test with the last one taking precedence.

---

## Settings ​

**URL:** https://mise.jdx.dev/configuration/settings.html

**Contents:**
- Settings ​
- activate_aggressive
- all_compile
- always_keep_download
- always_keep_install
- arch
- auto_install
- auto_install_disable_tools
- cache_prune_age
- color

The following is a list of all of mise's settings. These can be set via mise settings key=value, by directly modifying ~/.config/mise/config.toml or local config, or via environment variables.

Some of them also can be set via global CLI flags.

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

Example 1 (toml):
```toml
[tools]
node = '20'
python = '3.12'
```

Example 2 (sh):
```sh
eval "$(mise activate zsh)"
PATH="/some/other/python:$PATH"
```

Example 3 (unknown):
```unknown
mise settings add idiomatic_version_file_enable_tools node
mise settings add idiomatic_version_file_enable_tools python
```

Example 4 (toml):
```toml
[tools]
node = "22"
gh = "latest"
```

---
