# Mise-Task-Managing - Configuration

**Pages:** 15

---

## mise unset ​

**URL:** https://mise.jdx.dev/cli/unset.html

**Contents:**
- mise unset ​
- Arguments ​
  - [ENV_KEY]… ​
- Flags ​
  - -f --file <FILE> ​
  - -g --global ​

Remove environment variable(s) from the config file.

By default, this command modifies mise.toml in the current directory.

Environment variable(s) to remove e.g.: NODE_ENV

Specify a file to use instead of mise.toml

Use the global config file

**Examples:**

Example 1 (unknown):
```unknown
# Remove NODE_ENV from the current directory's config
$ mise unset NODE_ENV

# Remove NODE_ENV from the global config
$ mise unset NODE_ENV -g
```

---

## mise settings ​

**URL:** https://mise.jdx.dev/cli/settings.html

**Contents:**
- mise settings ​
- Arguments ​
  - [SETTING] ​
  - [VALUE] ​
- Global Flags ​
  - -l --local ​
- Flags ​
  - -a --all ​
  - -J --json ​
  - --json-extended ​

Show current settings

This is the contents of ~/.config/mise/config.toml

Note that aliases are also stored in this file but managed separately with mise aliases

Use the local config file instead of the global one

Output in JSON format

Output in JSON format with sources

Output in TOML format

**Examples:**

Example 1 (unknown):
```unknown
# list all settings
$ mise settings

# get the value of the setting "always_keep_download"
$ mise settings always_keep_download

# set the value of the setting "always_keep_download" to "true"
$ mise settings always_keep_download=true

# set the value of the setting "node.mirror_url" to "https://npm.taobao.org/mirrors/node"
$ mise settings node.mirror_url https://npm.taobao.org/mirrors/node
```

---

## mise fmt ​

**URL:** https://mise.jdx.dev/cli/fmt.html

**Contents:**
- mise fmt ​
- Flags ​
  - -a --all ​
  - -c --check ​
  - -s --stdin ​

Sorts keys and cleans up whitespace in mise.toml

Format all files from the current directory

Check if the configs are formatted, no formatting is done

Read config from stdin and write its formatted version into stdout

---

## mise settings get ​

**URL:** https://mise.jdx.dev/cli/settings/get.html

**Contents:**
- mise settings get ​
- Arguments ​
  - <SETTING> ​
- Flags ​
  - -l --local ​

Show a current setting

This is the contents of a single entry in ~/.config/mise/config.toml

Note that aliases are also stored in this file but managed separately with mise aliases get

Use the local config file instead of the global one

**Examples:**

Example 1 (unknown):
```unknown
$ mise settings get idiomatic_version_file
true
```

---

## mise settings unset ​

**URL:** https://mise.jdx.dev/cli/settings/unset.html

**Contents:**
- mise settings unset ​
- Arguments ​
  - <KEY> ​
- Flags ​
  - -l --local ​

This modifies the contents of ~/.config/mise/config.toml

The setting to remove

Use the local config file instead of the global one

**Examples:**

Example 1 (unknown):
```unknown
mise settings unset idiomatic_version_file
```

---

## mise lock ​

**URL:** https://mise.jdx.dev/cli/lock.html

**Contents:**
- mise lock ​
- Arguments ​
  - [TOOL]… ​
- Flags ​
  - -p --platform… <PLATFORM> ​
  - -f --force ​
  - -n --dry-run ​
  - -j --jobs <JOBS> ​

Update lockfile checksums and URLs for all specified platforms

Updates checksums and download URLs for all platforms already specified in the lockfile. If no lockfile exists, shows what would be created based on the current configuration. This allows you to refresh lockfile data for platforms other than the one you're currently on. Operates on the lockfile in the current config root. Use TOOL arguments to target specific tools.

Tool(s) to update in lockfile e.g.: node python If not specified, all tools in lockfile will be updated

Comma-separated list of platforms to target e.g.: linux-x64,macos-arm64,windows-x64 If not specified, all platforms already in lockfile will be updated

Update all tools even if lockfile data already exists

Show what would be updated without making changes

Number of jobs to run in parallel [default: 4]

$ mise lock Update lockfile in current directory for all platforms $ mise lock node python Update only node and python $ mise lock --platform linux-x64 Update only linux-x64 platform $ mise lock --dry-run Show what would be updated or created $ mise lock --force Re-download and update even if data exists

---

## mise config get ​

**URL:** https://mise.jdx.dev/cli/config/get.html

**Contents:**
- mise config get ​
- Arguments ​
  - [KEY] ​
- Flags ​
  - -f --file <FILE> ​

Display the value of a setting in a mise.toml file

The path of the config to display

The path to the mise.toml file to edit

If not provided, the nearest mise.toml file will be used

**Examples:**

Example 1 (unknown):
```unknown
$ mise toml get tools.python
3.12
```

---

## mise use ​

**URL:** https://mise.jdx.dev/cli/use.html

**Contents:**
- mise use ​
- Arguments ​
  - [TOOL@VERSION]… ​
- Flags ​
  - -f --force ​
  - --fuzzy ​
  - -g --global ​
  - -n --dry-run ​
  - -e --env <ENV> ​
  - -j --jobs <JOBS> ​

Installs a tool and adds the version to mise.toml.

This will install the tool version if it is not already installed. By default, this will use a mise.toml file in the current directory.

In the following order:

Use the --global flag to use the global config file instead.

Tool(s) to add to config file

e.g.: node@20, cargo:ripgrep@latest npm:prettier@3 If no version is specified, it will default to @latest

Tool options can be set with this syntax:

Force reinstall even if already installed

Save fuzzy version to config file

e.g.: mise use --fuzzy node@20 will save 20 as the version this is the default behavior unless MISE_PIN=1

Use the global config file (~/.config/mise/config.toml) instead of the local one

Perform a dry run, showing what would be installed and modified without making changes

Create/modify an environment-specific config file like .mise.<env>.toml

Number of jobs to run in parallel [default: 4]

Directly pipe stdin/stdout/stderr from plugin to user Sets --jobs=1

Remove the plugin(s) from config file

Specify a path to a config file or directory

If a directory is specified, it will look for a config file in that directory following the rules above.

Save exact version to config file e.g.: mise use --pin node@20 will save 20.0.0 as the version Set MISE_PIN=1 to make this the default behavior

Consider using mise.lock as a better alternative to pinning in mise.toml: https://mise.jdx.dev/configuration/settings.html#lockfile

**Examples:**

Example 1 (unknown):
```unknown
mise use ubi:BurntSushi/ripgrep[exe=rg]
```

Example 2 (unknown):
```unknown
# run with no arguments to use the interactive selector
$ mise use

# set the current version of node to 20.x in mise.toml of current directory
# will write the fuzzy version (e.g.: 20)
$ mise use node@20

# set the current version of node to 20.x in ~/.config/mise/config.toml
# will write the precise version (e.g.: 20.0.0)
$ mise use -g --pin node@20

# sets .mise.local.toml (which is intended not to be committed to a project)
$ mise use --env local node@20

# sets .mise.staging.toml (which is used if MISE_ENV=staging)
$ mise use --env staging node@20
```

---

## mise settings ls ​

**URL:** https://mise.jdx.dev/cli/settings/ls.html

**Contents:**
- mise settings ls ​
- Arguments ​
  - [SETTING] ​
- Flags ​
  - -a --all ​
  - -l --local ​
  - -J --json ​
  - --json-extended ​
  - -T --toml ​

Show current settings

This is the contents of ~/.config/mise/config.toml

Note that aliases are also stored in this file but managed separately with mise aliases

Use the local config file instead of the global one

Output in JSON format

Output in JSON format with sources

Output in TOML format

**Examples:**

Example 1 (unknown):
```unknown
$ mise settings ls
idiomatic_version_file = false
...

$ mise settings ls python
default_packages_file = "~/.default-python-packages"
...
```

---

## mise config ls ​

**URL:** https://mise.jdx.dev/cli/config/ls.html

**Contents:**
- mise config ls ​
- Flags ​
  - --no-header ​
  - --tracked-configs ​
  - -J --json ​

List config files currently in use

Do not print table header

List all tracked config files

Output in JSON format

**Examples:**

Example 1 (unknown):
```unknown
$ mise config ls
Path                        Tools
~/.config/mise/config.toml  pitchfork
~/src/mise/mise.toml        actionlint, bun, cargo-binstall, cargo:cargo-edit, cargo:cargo-insta
```

---

## mise settings add ​

**URL:** https://mise.jdx.dev/cli/settings/add.html

**Contents:**
- mise settings add ​
- Arguments ​
  - <SETTING> ​
  - <VALUE> ​
- Flags ​
  - -l --local ​

Adds a setting to the configuration file

Used with an array setting, this will append the value to the array. This modifies the contents of ~/.config/mise/config.toml

Use the local config file instead of the global one

**Examples:**

Example 1 (unknown):
```unknown
mise settings add disable_hints python_multi
```

---

## mise settings set ​

**URL:** https://mise.jdx.dev/cli/settings/set.html

**Contents:**
- mise settings set ​
- Arguments ​
  - <SETTING> ​
  - <VALUE> ​
- Flags ​
  - -l --local ​

This modifies the contents of ~/.config/mise/config.toml

Use the local config file instead of the global one

**Examples:**

Example 1 (unknown):
```unknown
mise settings idiomatic_version_file=true
```

---

## mise config set ​

**URL:** https://mise.jdx.dev/cli/config/set.html

**Contents:**
- mise config set ​
- Arguments ​
  - <KEY> ​
  - <VALUE> ​
- Flags ​
  - -f --file <FILE> ​
  - -t --type <TYPE> ​

Set the value of a setting in a mise.toml file

The path of the config to display

The value to set the key to

The path to the mise.toml file to edit

If not provided, the nearest mise.toml file will be used

**Examples:**

Example 1 (unknown):
```unknown
$ mise config set tools.python 3.12
$ mise config set settings.always_keep_download true
$ mise config set env.TEST_ENV_VAR ABC
$ mise config set settings.disable_tools --type list node,rust

# Type for `settings` is inferred
$ mise config set settings.jobs 4
```

---

## mise unuse ​

**URL:** https://mise.jdx.dev/cli/unuse.html

**Contents:**
- mise unuse ​
- Arguments ​
  - <INSTALLED_TOOL@VERSION>… ​
- Flags ​
  - -g --global ​
  - -e --env <ENV> ​
  - -p --path <PATH> ​
  - --no-prune ​

Removes installed tool versions from mise.toml

By default, this will use the mise.toml file that has the tool defined.

In the following order:

Will also prune the installed version if no other configurations are using it.

Use the global config file (~/.config/mise/config.toml) instead of the local one

Create/modify an environment-specific config file like .mise.<env>.toml

Specify a path to a config file or directory

If a directory is specified, it will look for a config file in that directory following the rules above.

Do not also prune the installed version

**Examples:**

Example 1 (unknown):
```unknown
# will uninstall specific version
$ mise unuse node@18.0.0

# will uninstall specific version from global config
$ mise unuse -g node@18.0.0

# will uninstall specific version from .mise.local.toml
$ mise unuse --env local node@20

# will uninstall specific version from .mise.staging.toml
$ mise unuse --env staging node@20
```

---

## mise config ​

**URL:** https://mise.jdx.dev/cli/config.html

**Contents:**
- mise config ​
- Flags ​
  - --no-header ​
  - --tracked-configs ​
  - -J --json ​
- Subcommands ​

Do not print table header

List all tracked config files

Output in JSON format

**Examples:**

Example 1 (unknown):
```unknown
$ mise config ls
Path                        Tools
~/.config/mise/config.toml  pitchfork
~/src/mise/mise.toml        actionlint, bun, cargo-binstall, cargo:cargo-edit, cargo:cargo-insta
```

---
