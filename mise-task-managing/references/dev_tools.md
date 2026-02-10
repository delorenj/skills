# Mise-Task-Managing - Dev Tools

**Pages:** 30

---

## Comparison to asdf ​

**URL:** https://mise.jdx.dev/dev-tools/comparison-to-asdf.html

**Contents:**
- Comparison to asdf ​
- Migrate from asdf to mise ​
- asdf in go (0.16+) ​
- Supply chain security ​
- UX ​
- Performance ​
- Windows support ​
- Security ​
- Command Compatibility ​
- Extra backends ​

mise can be used as a drop-in replacement for asdf. It supports the same .tool-versions files that you may have used with asdf and can use asdf plugins through the asdf backend.

It will not, however, reuse existing asdf directories (so you'll need to either reinstall them or move them), and 100% compatibility is not a design goal. That said, if you're coming from asdf-bash (0.15 and below), mise actually has fewer breaking changes than asdf-go (0.16 and above) despite 100% compatibility not being a design goal of mise.

Casual users coming from asdf have generally found mise to just be a faster, easier to use asdf.

Make sure you have a look at environments and tasks which are major portions of mise that have no asdf equivalent.

If you're moving from asdf to mise, please review #how-do-i-migrate-from-asdf for guidance.

asdf has gone through a rewrite in go. Because this is quite new as of this writing (2025-01-01), I'm going to keep information about 0.16+ asdf versions (which I call "asdf-go" vs "asdf-bash") in this section and the rest of this doc will apply to asdf-bash (0.15 and below).

In terms of performance, mise is still faster than the go asdf, however the difference is much closer. asdf is likely fast enough that the difference in overhead between asdf-go and mise may not even be enough to notice for you—after all there are plenty of people still using asdf-bash that claim they don't even notice how slow it is (don't ask me how):

I don't think performance is a good enough reason to switch though now that asdf-go is a thing. It's a reason, but it's a minor one. The improved security in mise, better DX, and lack of reliance on shims are all more important than performance.

Given they went through the trouble of rewriting asdf—that's also an indication they want to keep working on it (which is awesome that they're doing that btw). This does mean that some of what's written here may go out of date if they address some of the problems with asdf.

asdf plugins are not secure. This is explained in SECURITY.md, but the quick explanation is that asdf plugins involve shell code which can essentially do anything on your machine. It's dangerous code. What's worse is asdf plugins are rarely written by the tool vendor (who you need to trust anyway to use the tool), which means for every asdf plugin you use you'll be trusting a random developer to not go rogue and to not get hacked themselves and publish changes to a plugin with an exploit.

mise still uses asdf plugins for some tools, but we're actively reducing that count as well as moving things into the mise-plugins org. It looks like asdf has a similar model with their asdf-community org, but it isn't. asdf gives plugin authors commit access to their plugin in asdf-community when they move it in, which I feel like defeats the purpose of having a dedicated org in the first place. By the end of 2025 I would like for there to no longer be any asdf plugins in the registry that aren't owned by me.

I've also been adopting extra security verification steps when vendors offer that ability such as gpg verification on node installs, and native Cosign/SLSA/Minisign/GitHub attestation verification for aqua tools.

Some commands are the same in asdf but others have been changed. Everything that's possible in asdf should be possible in mise but may use slightly different syntax. mise has more forgiving commands, such as using fuzzy-matching, e.g.: mise install node@20. While in asdf you can run asdf install node latest:20, you can't use latest:20 in a .tool-versions file or many other places. In mise you can use fuzzy-matching everywhere.

asdf requires several steps to install a new runtime if the plugin isn't installed, e.g.:

In mise this can all be done in a single step which installs the plugin, installs the runtime, and sets the version:

If you have an existing .tool-versions file, or .mise.toml, you can install all plugins and runtimes with a single command:

I've found asdf to be particularly rigid and difficult to learn. It also made strange decisions like having asdf list all but asdf latest --all (why is one a flag and one a positional argument?). mise makes heavy use of aliases so you don't need to remember if it's mise plugin add node or mise plugin install node. If I can guess what you meant, then I'll try to get mise to respond in the right way.

That said, there are a lot of great things about asdf. It's the best multi-runtime manager out there and I've really been impressed with the plugin system. Most of the design decisions the authors made were very good. I really just have 2 complaints: the shims and the fact it's written in Bash.

asdf made (what I consider) a poor design decision to use shims that go between a call to a runtime and the runtime itself. e.g.: when you call node it will call an asdf shim file ~/.asdf/shims/node, which then calls asdf exec, which then calls the correct version of node.

These shims have terrible performance, adding ~120ms to every runtime call. mise activate does not use shims and instead updates PATH so that it doesn't have any overhead when simply calling binaries. These shims are the main reason that I wrote this. Note that in the demo GIF at the top of this README that mise isn't actually used when calling node -v for this reason. The performance is identical to running node without using mise.

I don't think it's possible for asdf to fix these issues. The author of asdf did a great writeup of performance problems. asdf is written in bash which certainly makes it challenging to be performant, however I think the real problem is the shim design. I don't think it's possible to fix that without a complete rewrite.

mise does call an internal command mise hook-env every time the directory has changed, but because it's written in Rust, this is very quick—taking ~10ms on my machine. 4ms if there are no changes, 14ms if it's a full reload.

tl;dr: asdf adds overhead (~120ms) when calling a runtime, mise adds a small amount of overhead (~ 5ms) when the prompt loads.

asdf does not run on Windows at all. With mise, tools using non-asdf backends can support Windows. Of course, this means the tool vendor must provide Windows binaries but if they do, and the backend isn't asdf, the tool should work on Windows.

asdf plugins are insecure. They typically are written by individuals with no ties to the vendors that provide the underlying tool. Where possible, mise does not use asdf plugins and instead uses backends like aqua and ubi which do not require separate plugins.

Aqua tools include native Cosign/SLSA/Minisign/GitHub attestation verification built into mise. See SECURITY for more information.

In nearly all places you can use the exact syntax that works in asdf, however this likely won't show up in the help or CLI reference. If you're coming from asdf and comfortable with that way of working you can almost always use the same syntax with mise, e.g.:

UPDATE (2025-01-01): asdf-go (0.16+) actually got rid of asdf global|local entirely in favor of asdf set which we can't support since we already have a command named mise set. mise command compatibility will likely not be as good with asdf-go 0.16+.

It's not recommended though. You almost always want to modify config files and install things so mise use node@20 saves an extra command. Also, the "@" in the command is preferred since it allows you to install multiple tools at once: mise use|install node@20 node@18. Also, there are edge cases where it's not possible—or at least very challenging—for us to definitively know which syntax is being used and so we default to mise-style. While there aren't many of these, asdf-compatibility is done as a "best-effort" in order to make transitioning from asdf feel familiar for those users who can rely on their muscle memory. Ensuring asdf-syntax works with everything is not a design goal.

mise has support for backends other than asdf plugins. For example you can install CLIs directly from cargo and npm:

**Examples:**

Example 1 (unknown):
```unknown
asdf plugin add node
asdf install node latest:20
asdf local node latest:20
```

Example 2 (unknown):
```unknown
mise use node@20
```

Example 3 (unknown):
```unknown
mise install
```

Example 4 (unknown):
```unknown
mise install node 20.0.0
mise local node 20.0.0
```

---

## mise ls ​

**URL:** https://mise.jdx.dev/cli/ls.html

**Contents:**
- mise ls ​
- Arguments ​
  - [INSTALLED_TOOL]… ​
- Flags ​
  - -c --current ​
  - -g --global ​
  - -l --local ​
  - -i --installed ​
  - --outdated ​
  - -J --json ​

List installed and active tool versions

This command lists tools that mise "knows about". These may be tools that are currently installed, or those that are in a config file (active) but may or may not be installed.

It's a useful command to get the current state of your tools.

Only show tool versions from [TOOL]

Only show tool versions currently specified in a mise.toml

Only show tool versions currently specified in the global mise.toml

Only show tool versions currently specified in the local mise.toml

Only show tool versions that are installed (Hides tools defined in mise.toml but not installed)

Display whether a version is outdated

Output in JSON format

Display missing tool versions

Display versions matching this prefix

List only tools that can be pruned with mise prune

Don't display headers

**Examples:**

Example 1 (unknown):
```unknown
$ mise ls
node    20.0.0 ~/src/myapp/.tool-versions latest
python  3.11.0 ~/.tool-versions           3.10
python  3.10.0

$ mise ls --current
node    20.0.0 ~/src/myapp/.tool-versions 20
python  3.11.0 ~/.tool-versions           3.11.0

$ mise ls --json
{
  "node": [
    {
      "version": "20.0.0",
      "install_path": "/Users/jdx/.mise/installs/node/20.0.0",
      "source": {
        "type": "mise.toml",
        "path": "/Users/jdx/mise.toml"
      }
    }
  ],
  "python": [...]
}
```

---

## mise outdated ​

**URL:** https://mise.jdx.dev/cli/outdated.html

**Contents:**
- mise outdated ​
- Arguments ​
  - [TOOL@VERSION]… ​
- Flags ​
  - -l --bump ​
  - -J --json ​
  - --no-header ​

Shows outdated tool versions

See mise upgrade to upgrade these versions.

Tool(s) to show outdated versions for e.g.: node@20 python@3.10 If not specified, all tools in global and local configs will be shown

Compares against the latest versions available, not what matches the current config

For example, if you have node = "20" in your config by default mise outdated will only show other 20.x versions, not 21.x or 22.x versions.

Using this flag, if there are 21.x or newer versions it will display those instead of 20.x.

Output in JSON format

Don't show table header

**Examples:**

Example 1 (unknown):
```unknown
$ mise outdated
Plugin  Requested  Current  Latest
python  3.11       3.11.0   3.11.1
node    20         20.0.0   20.1.0

$ mise outdated node
Plugin  Requested  Current  Latest
node    20         20.0.0   20.1.0

$ mise outdated --json
{"python": {"requested": "3.11", "current": "3.11.0", "latest": "3.11.1"}, ...}
```

---

## gem Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/gem.html

**Contents:**
- gem Backend ​
- Dependencies ​
- Usage ​
- Ruby upgrades ​
- Settings ​

mise can be used to install CLIs from RubyGems. The code for this is inside of the mise repository at ./src/backend/gem.rs.

This relies on having gem (provided with ruby) installed. You can install it with or without mise. Here is how to install ruby with mise:

The following installs the latest version of rubocop and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

If the ruby version used by a gem package changes, (by mise or system ruby), you may need to reinstall the gem. This can be done with:

Or you can reinstall all gems with:

Set these with mise settings set [VARIABLE] [VALUE] or by setting the environment variable listed.

No settings available.

**Examples:**

Example 1 (unknown):
```unknown
mise use -g ruby
```

Example 2 (unknown):
```unknown
mise use -g gem:rubocop
rubocop --version
```

Example 3 (unknown):
```unknown
[tools]
"gem:rubocop" = "latest"
```

Example 4 (unknown):
```unknown
mise install -f gem:rubocop
```

---

## Vfox Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/vfox.html

**Contents:**
- Vfox Backend ​
- Dependencies ​
- Usage ​
- Default plugin backend ​
- Plugins ​
  - Example: Plugin Usage ​

Vfox plugins may be used in mise to install tools.

The code for this is inside the mise repository at ./src/backend/vfox.rs.

No dependencies are required for vfox. Vfox lua code is read via a lua interpreter built into mise.

The following installs the latest version of cmake and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

On Windows, mise uses vfox plugins by default. If you'd like to use plugins by default even on Linux/macOS, set the following settings:

Now you can list available plugins with mise registry:

And they will be installed when running commands such as mise use -g cmake without needing to specify vfox:cmake.

In addition to the standard vfox plugins, mise supports modern plugins that can manage multiple tools using the plugin:tool format. These plugins are perfect for:

For more information, see:

**Examples:**

Example 1 (unknown):
```unknown
$ mise use -g vfox:version-fox/vfox-cmake
$ cmake --version
cmake version 3.21.3
```

Example 2 (unknown):
```unknown
[tools]
"vfox:version-fox/vfox-cmake" = "latest"
```

Example 3 (unknown):
```unknown
mise settings add disable_backends asdf
```

Example 4 (unknown):
```unknown
$ mise registry | grep vfox:
clang                         vfox:mise-plugins/vfox-clang
cmake                         vfox:mise-plugins/vfox-cmake
crystal                       vfox:mise-plugins/vfox-crystal
dart                          vfox:mise-plugins/vfox-dart
dotnet                        vfox:mise-plugins/vfox-dotnet
etcd                          aqua:etcd-io/etcd vfox:mise-plugins/vfox-etcd
flutter                       vfox:mise-plugins/vfox-flutter
gradle                        aqua:gradle/gradle vfox:mise-plugins/vfox-gradle
groovy                        vfox:mise-plugins/vfox-groovy
kotlin                        vfox:mise-plugins/vfox-kotlin
maven                         aqua:apache/maven vfox:mise-plugins/vfox-maven
php                           vfox:mise-plugins/vfox-php
scala                         vfox:mise-plugins/vfox-scala
terraform                     aqua:hashicorp/terraform vfox:mise-plugins/vfox-terraform
vlang                         vfox:mise-plugins/vfox-vlang
```

---

## Aliases ​

**URL:** https://mise.jdx.dev/dev-tools/aliases.html

**Contents:**
- Aliases ​
- Aliased Backends ​
- Aliased Versions ​
- Templates ​

Tools can be aliased so that something like node which normally maps to core:node can be changed to something like asdf:company/our-custom-node instead.

mise supports aliasing the versions of runtimes. One use-case for this is to define aliases for LTS versions of runtimes. For example, you may want to specify lts-hydrogen as the version for node@20.x so you can use set it with node lts-hydrogen in mise.toml/.tool-versions.

User aliases can be created by adding an alias.<PLUGIN> section to ~/.config/mise/config.toml:

Plugins can also provide aliases via a bin/list-aliases script. Here is an example showing node.js versions:

Because this is mise-specific functionality not currently used by asdf it isn't likely to be in any plugin currently, but plugin authors can add this script without impacting asdf users.

Alias values can be templates, see Templates for details.

**Examples:**

Example 1 (unknown):
```unknown
[alias]
node = 'asdf:company/our-custom-node' # shorthand for https://github.com/company/our-custom-node
erlang = 'asdf:https://github.com/company/our-custom-erlang'
```

Example 2 (unknown):
```unknown
[alias.node.versions]
my_custom_20 = '20'
```

Example 3 (unknown):
```unknown
#!/usr/bin/env bash

echo "lts-hydrogen 18"
echo "lts-gallium 16"
echo "lts-fermium 14"
```

Example 4 (unknown):
```unknown
[alias.node.versions]
current = "{{exec(command='node --version')}}"
```

---

## Dotnet backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/dotnet.html

**Contents:**
- Dotnet backend ​
- Usage ​
  - Supported Dotnet Syntax ​
- Settings ​
  - dotnet.package_flags
  - dotnet.registry_url
- Tool Options ​

The code for this is inside the mise repository at ./src/backend/dotnet.rs.

The dotnet backend requires having the .NET runtime installed. You can install it using mise:

This will install the .NET runtime, which is required for dotnet tools to work properly.

The following installs the latest version of GitVersion.Tool and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

The version will be set in ~/.config/mise/config.toml with the following format:

Set these with mise settings set [VARIABLE] [VALUE] or by setting the environment variable listed.

This is a list of flags to extend the search and install abilities of dotnet tools.

Here are the available flags:

URL to fetch dotnet tools from. This is used when installing dotnet tools.

By default, mise will use the nuget API to fetch.

However, you can set this to a different URL if you have a custom feed or want to use a different source.

The following tool-options are available for the dotnet backend—these go in [tools] in mise.toml.

**Examples:**

Example 1 (unknown):
```unknown
# Install the latest version
mise use dotnet

# Or install a specific version (8, 9, etc.)
mise use dotnet@8
mise use dotnet@9
```

Example 2 (unknown):
```unknown
$ mise use dotnet:GitVersion.Tool@5.12.0
$ dotnet-gitversion /version
5.12.0+Branch.support-5.x.Sha.3f75764963eb3d7956dcd5a40488c074dd9faf9e
```

Example 3 (unknown):
```unknown
[tools]
"dotnet:GitVersion.Tool" = "5.12.0"
```

Example 4 (unknown):
```unknown
$ mise use dotnet:GitVersion.Tool
$ dotnet-gitversion /version
6.1.0+Branch.main.Sha.8856e3041dbb768118a55a31ad4e465ae70c6767
```

---

## SPM Backend experimental ​

**URL:** https://mise.jdx.dev/dev-tools/backends/spm.html

**Contents:**
- SPM Backend experimental ​
- Dependencies ​
- Usage ​
  - Supported Syntax ​
- Tool Options ​
  - provider ​
  - api_url ​

You may install executables managed by Swift Package Manager directly from GitHub or GitLab releases.

The code for this is inside of the mise repository at ./src/backend/spm.rs.

This relies on having swift installed. You can either install it manually or with mise.

If you have Xcode installed and selected in your system via xcode-select, Swift is already available through the toolchain embedded in the Xcode installation.

The following installs the latest version of tuist and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

Other syntax may work but is unsupported and untested.

The following tool-options are available for the backend — these go in [tools] in mise.toml.

Set the provider type to use for fetching assets and release information. Either github or gitlab (default is github). Ensure the provider is set to the correct type if you use shorthand notation and api_url for self-hosted repositories as the type probably cannot be derived correctly from the URL.

Set the URL for the provider's API. This is useful when using a self-hosted instance.

**Examples:**

Example 1 (unknown):
```unknown
$ mise use -g spm:tuist/tuist
$ tuist --help
OVERVIEW: Generate, build and test your Xcode projects.

USAGE: tuist <subcommand>
...
```

Example 2 (unknown):
```unknown
[tools]
"spm:tuist/tuist" = "latest"
```

Example 3 (unknown):
```unknown
[tools]
"spm:patricklorran/ios-settings" = { version = "latest", provider = "gitlab" }
```

Example 4 (unknown):
```unknown
[tools]
"spm:acme/my-tool" = { version = "latest", provider = "gitlab", api_url = "https://gitlab.acme.com/api/v4" }
```

---

## Cargo Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/cargo.html

**Contents:**
- Cargo Backend ​
- Dependencies ​
- Usage ​
  - Using Git ​
- Settings ​
  - cargo.binstall
  - cargo.registry_name
- Tool Options ​
  - features ​
  - default-features ​

You may install packages directly from Cargo Crates even if there isn't an asdf plugin for it.

The code for this is inside the mise repository at ./src/backend/cargo.rs.

This relies on having cargo installed. You can either install it on your system via rustup:

Or you can install it via mise:

The following installs the latest version of eza and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

You can install any package from a Git repository using the mise command. This allows you to install a particular tag, branch, or commit revision:

This will execute a cargo install command with the corresponding Git options.

Set these with mise settings set [VARIABLE] [VALUE] or by setting the environment variable listed.

If true, mise will use cargo binstall instead of cargo install if cargo-binstall is installed and on PATH. This makes installing CLIs with cargo much faster by downloading precompiled binaries.

You can install it with mise:

Packages are installed from the official cargo registry.

You can set this to a different registry name if you have a custom feed or want to use a different source.

Please follow the cargo alternative registries documentation to configure your registry.

The following tool-options are available for the cargo backend—these go in [tools] in mise.toml.

Install additional components (passed as cargo install --features):

Disable default features (passed as cargo install --no-default-features):

Select the CLI bin name to install when multiple are available (passed as cargo install --bin):

Select the crate name to install when multiple are available (passed as cargo install --git=<repo> <crate>):

Use Cargo.lock (passes cargo install --locked) when building CLI. This is the default behavior, pass false to disable:

**Examples:**

Example 1 (unknown):
```unknown
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Example 2 (unknown):
```unknown
mise use -g rust
```

Example 3 (unknown):
```unknown
$ mise use -g cargo:eza
$ eza --version
eza - A modern, maintained replacement for ls
v0.17.1 [+git]
https://github.com/eza-community/eza
```

Example 4 (unknown):
```unknown
[tools]
"cargo:eza" = "latest"
```

---

## mise generate config ​

**URL:** https://mise.jdx.dev/cli/generate/config.html

**Contents:**
- mise generate config ​
- Flags ​
  - -t --tool-versions <TOOL_VERSIONS> ​
  - -o --output <OUTPUT> ​

[experimental] Generate a mise.toml file

Path to a .tool-versions file to import tools from

Output to file instead of stdout

**Examples:**

Example 1 (unknown):
```unknown
mise cf generate > mise.toml
mise cf generate --output=mise.toml
```

---

## mise ls-remote ​

**URL:** https://mise.jdx.dev/cli/ls-remote.html

**Contents:**
- mise ls-remote ​
- Arguments ​
  - [TOOL@VERSION] ​
  - [PREFIX] ​
- Flags ​
  - --all ​

List runtime versions available for install.

Note that the results may be cached, run mise cache clean to clear the cache and get fresh results.

Tool to get versions for

The version prefix to use when querying the latest version same as the first argument after the "@"

Show all installed plugins and versions

**Examples:**

Example 1 (unknown):
```unknown
$ mise ls-remote node
18.0.0
20.0.0

$ mise ls-remote node@20
20.0.0
20.1.0

$ mise ls-remote node 20
20.0.0
20.1.0
```

---

## GitLab Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/gitlab.html

**Contents:**
- GitLab Backend ​
- Usage ​
- Tool Options ​
  - Asset Autodetection ​
  - asset_pattern ​
  - version_prefix ​
  - Platform-specific Asset Patterns ​
  - checksum ​
  - Platform-specific Checksums ​
  - size ​

You may install GitLab release assets directly using the gitlab backend. This backend downloads release assets from GitLab repositories and is ideal for tools that distribute pre-built binaries through GitLab releases.

The code for this is inside of the mise repository at ./src/backend/gitlab.rs.

The following installs the latest version of gitlab-runner from GitLab releases and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

The following tool-options are available for the gitlab backend—these go in [tools] in mise.toml.

When no asset_pattern is specified, mise automatically selects the best asset for your platform. The system scores assets based on:

For most tools, you can simply install without specifying patterns:

The autodetection logic is implemented in src/backend/asset_detector.rs, which is shared by both the GitHub and GitLab backends.

Specifies the pattern to match against release asset names. This is useful when there are multiple assets for your OS/arch combination or when you need to override autodetection.

Specifies a custom version prefix for release tags. By default, mise handles the common v prefix (e.g., v1.0.0), but some repositories use different prefixes like release-, version-, or no prefix at all.

When version_prefix is configured, mise will:

For different asset patterns per platform:

Verify the downloaded file with a checksum:

Instead of specifying the checksum here, you can use mise.lock to manage checksums.

Verify the downloaded asset size:

You can specify different sizes for different platforms:

Number of directory components to strip when extracting archives:

If strip_components is not explicitly set, mise will automatically detect when to apply strip_components = 1. This happens when the extracted archive contains exactly one directory at the root level and no files. This is common with tools like ripgrep that package their binaries in a versioned directory (e.g., ripgrep-14.1.0-x86_64-unknown-linux-musl/rg). The auto-detection ensures the binary is placed directly in the install path where mise expects it.

Rename the downloaded binary to a specific name. This is useful when downloading single binaries that have platform-specific names:

When downloading single binaries (not archives), mise automatically removes OS/arch suffixes from the filename. For example, mytool-linux-x86_64 becomes mytool automatically. Use the bin option only when you need a specific custom name.

Specify the directory containing binaries within the extracted archive, or where to place the downloaded file. This supports templating with {name}, {version}, {os}, {arch}, and {ext}:

Binary path lookup order:

For self-hosted GitLab instances, specify the API URL:

If you are using a self-hosted GitLab instance, set the api_url tool option and optionally the MISE_GITLAB_ENTERPRISE_TOKEN environment variable for authentication:

No settings available.

**Examples:**

Example 1 (unknown):
```unknown
$ mise use -g gitlab:gitlab-org/gitlab-runner
$ gitlab-runner --version
gitlab-runner 16.8.0
```

Example 2 (unknown):
```unknown
[tools]
"gitlab:gitlab-org/gitlab-runner" = { version = "latest", asset_pattern = "gitlab-runner-linux-x64" }
```

Example 3 (unknown):
```unknown
mise install gitlab:user/repo
```

Example 4 (unknown):
```unknown
[tools."gitlab:gitlab-org/gitlab-runner"]
version = "latest"
asset_pattern = "gitlab-runner-linux-x64"
```

---

## mise sync ​

**URL:** https://mise.jdx.dev/cli/sync.html

**Contents:**
- mise sync ​
- Subcommands ​

Synchronize tools from other version managers with mise

---

## mise upgrade ​

**URL:** https://mise.jdx.dev/cli/upgrade.html

**Contents:**
- mise upgrade ​
- Arguments ​
  - [TOOL@VERSION]… ​
- Flags ​
  - -n --dry-run ​
  - -i --interactive ​
  - -j --jobs <JOBS> ​
  - -l --bump ​
  - --raw ​

Upgrades outdated tools

By default, this keeps the range specified in mise.toml. So if you have node@20 set, it will upgrade to the latest 20.x.x version available. See the --bump flag to use the latest version and bump the version in mise.toml.

This will update mise.lock if it is enabled, see https://mise.jdx.dev/configuration/settings.html#lockfile

Tool(s) to upgrade e.g.: node@20 python@3.10 If not specified, all current tools will be upgraded

Just print what would be done, don't actually do it

Display multiselect menu to choose which tools to upgrade

Number of jobs to run in parallel [default: 4]

Upgrades to the latest version available, bumping the version in mise.toml

For example, if you have node = "20.0.0" in your mise.toml but 22.1.0 is the latest available, this will install 22.1.0 and set node = "22.1.0" in your config.

It keeps the same precision as what was there before, so if you instead had node = "20", it would change your config to node = "22".

Directly pipe stdin/stdout/stderr from plugin to user Sets --jobs=1

**Examples:**

Example 1 (unknown):
```unknown
# Upgrades node to the latest version matching the range in mise.toml
$ mise upgrade node

# Upgrades node to the latest version and bumps the version in mise.toml
$ mise upgrade node --bump

# Upgrades all tools to the latest versions
$ mise upgrade

# Upgrades all tools to the latest versions and bumps the version in mise.toml
$ mise upgrade --bump

# Just print what would be done, don't actually do it
$ mise upgrade --dry-run

# Upgrades node and python to the latest versions
$ mise upgrade node python

# Show a multiselect menu to choose which tools to upgrade
$ mise upgrade --interactive
```

---

## Dev Tools ​

**URL:** https://mise.jdx.dev/dev-tools/

**Contents:**
- Dev Tools ​
- How it works ​
  - Tool Resolution Flow ​
  - Environment Integration ​
  - Path Management ​
  - Configuration Hierarchy ​
- Tool Options ​
  - Table Format (Recommended) ​
  - Dotted Notation ​
  - Generic Nested Support ​

Like asdf (or nvm or pyenv but for any language), it manages dev tools like node, python, cmake, terraform, and hundreds more.

mise is a tool that manages installations of programming language runtimes and other tools for local development. For example, it can be used to manage multiple versions of Node.js, Python, Ruby, Go, etc. on the same machine.

Once activated, mise can automatically switch between different versions of tools based on the directory you're in. This means that if you have a project that requires Node.js 18 and another that requires Node.js 22, mise will automatically switch between them as you move between the two projects. See tools available for mise with in the registry.

To know which tool version to use, mise will typically look for a mise.toml file in the current directory and its parents. To get an idea of how tools are specified, here is an example of a mise.toml file:

It's also compatible with asdf .tool-versions files as well as idiomatic version files like .node-version and .ruby-version. See configuration for more details.

mise is inspired by asdf and can leverage asdf's vast plugin ecosystem under the hood. However, it is much faster than asdf and has a more friendly user experience.

mise manages development tools through a sophisticated but user-friendly system that automatically handles tool installation, version management, and environment setup.

When you enter a directory or run a command, mise follows this process:

mise provides several ways to integrate with your development environment:

Automatic Activation: With mise activate, mise hooks into your shell prompt and automatically updates your environment when you change directories:

On-Demand Execution: Use mise exec to run commands with mise's environment without permanent activation:

Shims: mise can create lightweight wrapper scripts that automatically use the correct tool versions:

mise modifies your PATH environment variable to prioritize the correct tool versions:

This ensures that when you run node, you get the version specified in your project configuration, not a system-wide installation.

mise supports nested configuration that cascades from broad to specific settings:

Each level can override or extend the previous ones, giving you fine-grained control over tool versions across different contexts.

Tool options allow you to customize how tools are installed and configured. They support nested configurations for better organization, particularly useful for platform-specific settings.

The cleanest way to specify nested options is using TOML tables:

You can also use dotted notation for simpler nested configurations:

Any backend can use nested options for organizing complex configurations:

Internally, nested options are flattened to dot notation (e.g., platforms.macos-x64.url, database.host, cache.redis.port) for backend access.

Run a command immediately after a tool finishes installing by adding a postinstall field to that tool's configuration. This is separate from [hooks].postinstall and applies only to when a specific tool is installed.

You can restrict tools to specific operating systems using the os field:

The os field accepts an array of operating system identifiers:

If a tool specifies an os restriction and the current operating system is not in the list, mise will skip installing and using that tool.

mise uses intelligent caching to minimize overhead:

This ensures that mise adds minimal latency to your daily development workflow.

After activating, mise will update env vars like PATH whenever the directory is changed or the prompt is displayed. See the FAQ.

After activating, every time your prompt displays it will call mise hook-env to fetch new environment variables. This should be very fast. It exits early if the directory wasn't changed or mise.toml/.tool-versions files haven't been modified.

mise modifies PATH ahead of time so the runtimes are called directly. This means that calling a tool has zero overhead and commands like which node returns the real path to the binary. Other tools like asdf only support shim files to dynamically locate runtimes when they're called which adds a small delay and can cause issues with some commands. See shims for more information.

Here are some of the most important commands when it comes to working with dev tools. Click the header for each command to go to its reference documentation page to see all available flags/options and more examples.

For some users, mise use might be the only command you need to learn. It will do the following:

mise use node@22 will install the latest version of node-22 and create/update the mise.toml config file in the local directory. Anytime you're in that directory, that version of node will be used.

mise use -g node@22 will do the same but update the global config (~/.config/mise/config.toml) so unless there is a config file in the local directory hierarchy, node-22 will be the default version for the user.

mise install will install but not activate tools—meaning it will download/build/compile the tool into ~/.local/share/mise/installs but you won't be able to use it without "setting" the version in a .mise-toml or .tool-versions file.

If you're coming from asdf, there is no need to also run mise plugin add to first install the plugin, that will be done automatically if needed. Of course, you can manually install plugins if you wish or you want to use a plugin not in the default registry.

There are many ways it can be used:

mise x can be used for one-off commands using specific tools. e.g.: if you want to run a script with python3.12:

Python will be installed if it is not already. mise x will read local/global .mise-toml/.tool-versions files as well, so if you don't want to use mise activate or shims you can use mise by just prefixing commands with mise x --:

If you use this a lot, an alias can be helpful:

Similarly, mise run can be used to execute tasks which will also activate the mise environment with all of your tools.

mise provides several mechanisms to automatically install missing tools or versions as needed. Below, these are grouped by how and when they are triggered, with relevant settings for each. All mechanisms require the global auto_install setting to be enabled (all auto_install settings are enabled by default).

When you run a command like mise x or mise r, mise will automatically install any missing tool versions required to execute the command.

If you type a command in your shell (e.g., node) and it is not found, mise can attempt to auto-install the missing tool version if it knows which tool provides that binary.

Disable auto_install for specific tools by setting auto_install_disable_tools to a list of tool names.

**Examples:**

Example 1 (unknown):
```unknown
[tools]
node = '22'
python = '3'
ruby = 'latest'
```

Example 2 (unknown):
```unknown
eval "$(mise activate zsh)"  # In your ~/.zshrc
cd my-project               # Automatically loads mise.toml tools
```

Example 3 (unknown):
```unknown
mise exec -- node my-script.js  # Runs with tools from mise.toml
```

Example 4 (unknown):
```unknown
mise activate --shims  # Creates shims instead of modifying PATH
```

---

## npm Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/npm.html

**Contents:**
- npm Backend ​
- Dependencies ​
- Usage ​
- Settings ​
  - npm.bun

You may install packages directly from npmjs.org even if there isn't an asdf plugin for it.

The code for this is inside of the mise repository at ./src/backend/npm.rs.

This relies on having npm installed. You can install it with or without mise. Here is how to install npm with mise:

The following installs the latest version of prettier and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

Set these with mise settings set [VARIABLE] [VALUE] or by setting the environment variable listed.

If true, mise will use bun instead of npm if bun is installed and on PATH. This makes installing CLIs faster by using bun as the package manager.

You can install it with mise:

**Examples:**

Example 1 (unknown):
```unknown
mise use -g node
```

Example 2 (unknown):
```unknown
$ mise use -g npm:prettier
$ prettier --version
3.1.0
```

Example 3 (unknown):
```unknown
[tools]
"npm:prettier" = "latest"
```

Example 4 (sh):
```sh
mise use -g bun
```

---

## GitHub Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/github.html

**Contents:**
- GitHub Backend ​
- Usage ​
- Tool Options ​
  - Asset Autodetection ​
  - asset_pattern ​
  - version_prefix ​
  - Platform-specific Asset Patterns ​
  - checksum ​
  - Platform-specific Checksums ​
  - size ​

You may install GitHub release assets directly using the github backend. This backend downloads release assets from GitHub repositories and is ideal for tools that distribute pre-built binaries through GitHub releases.

The code for this is inside of the mise repository at ./src/backend/github.rs.

The following installs the latest version of ripgrep from GitHub releases and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

The following tool-options are available for the github backend—these go in [tools] in mise.toml.

When no asset_pattern is specified, mise automatically selects the best asset for your platform. The system scores assets based on:

For most tools, you can simply install without specifying patterns:

The autodetection logic is implemented in src/backend/asset_detector.rs, which is shared by both the GitHub and GitLab backends.

Specifies the pattern to match against release asset names. This is useful when there are multiple assets for your OS/arch combination or when you need to override autodetection.

Specifies a custom version prefix for release tags. By default, mise handles the common v prefix (e.g., v1.0.0), but some repositories use different prefixes like release-, version-, or no prefix at all.

When version_prefix is configured, mise will:

For different asset patterns per platform:

Verify the downloaded file with a checksum:

Instead of specifying the checksum here, you can use mise.lock to manage checksums.

Verify the downloaded asset size:

Number of directory components to strip when extracting archives:

If strip_components is not explicitly set, mise will automatically detect when to apply strip_components = 1. This happens when the extracted archive contains exactly one directory at the root level and no files. This is common with tools like ripgrep that package their binaries in a versioned directory (e.g., ripgrep-14.1.0-x86_64-unknown-linux-musl/rg). The auto-detection ensures the binary is placed directly in the install path where mise expects it.

Rename the downloaded binary to a specific name. This is useful when downloading single binaries that have platform-specific names:

When downloading single binaries (not archives), mise automatically removes OS/arch suffixes from the filename. For example, docker-compose-linux-x86_64 becomes docker-compose automatically. Use the bin option only when you need a specific custom name.

Specify the directory containing binaries within the extracted archive, or where to place the downloaded file. This supports templating with {name}, {version}, {os}, {arch}, and {ext}:

Binary path lookup order:

For GitHub Enterprise or self-hosted GitHub instances, specify the API URL:

If you are using a self-hosted GitHub instance, set the api_url tool option and optionally the MISE_GITHUB_ENTERPRISE_TOKEN environment variable for authentication:

No settings available.

**Examples:**

Example 1 (unknown):
```unknown
$ mise use -g github:BurntSushi/ripgrep
$ rg --version
ripgrep 14.1.1
```

Example 2 (unknown):
```unknown
[tools]
"github:BurntSushi/ripgrep" = "latest"
```

Example 3 (unknown):
```unknown
mise install github:user/repo
```

Example 4 (unknown):
```unknown
[tools]
"github:cli/cli" = { version = "latest", asset_pattern = "gh_*_linux_x64.tar.gz" }
```

---

## asdf Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/asdf.html

**Contents:**
- asdf Backend ​
- Writing asdf (legacy) plugins for mise ​

asdf is the original backend for mise.

It relies on asdf plugins for each tool. asdf plugins are more risky to use because they're typically written by a single developer unrelated to the tool vendor. They also generally do not function on Windows because they're written in bash which is often not available on Windows and the scripts generally are not written to be cross-platform.

asdf plugins are not used for tools inside the registry whenever possible. Sometimes it is not possible to use more secure backends like aqua/ubi because tools have complex install setups or need to export env vars.

All of these are hosted in the mise-plugins org to secure the supply chain so you do not need to rely on plugins maintained by anyone except me.

Because of the extra complexity of asdf tools and security concerns we are actively moving tools in the registry away from asdf where possible to backends like aqua and ubi which don't require plugins. That said, not all tools can function with ubi/aqua if they have a unique installation process or need to set env vars other than PATH.

See the asdf documentation for more information on writing plugins.

---

## Backend Architecture ​

**URL:** https://mise.jdx.dev/dev-tools/backend_architecture.html

**Contents:**
- Backend Architecture ​
- What are Backends? ​
- The Backend Trait System ​
- Backend Types ​
  - Core Tools ​
  - Language Package Managers ​
  - Universal Installers ​
    - aqua - Comprehensive Package Manager ​
    - ubi - Universal Binary Installer ​
  - Plugin Systems ​

Understanding how mise's backend system works can help you choose the right backend for your tools and troubleshoot issues when they arise. Most users don't need to explicitly choose backends since the mise registry defines smart defaults, but understanding the system helps when you need specific tools or want to optimize performance.

Backends are mise's way of supporting different tool installation methods. Each backend knows how to:

Think of backends as "adapters" that let mise work with different package managers and installation systems.

All backends implement a common interface (called a "trait" in Rust), which means they all provide the same basic functionality:

This design allows mise to treat all backends uniformly while each backend handles the specifics of its installation method.

Built directly into mise, written in Rust for performance and reliability:

Core tools like Node.js and Java are implemented as backends even though they represent single tools. This consistent backend architecture allows mise to handle all tools uniformly, whether they're complex ecosystems or individual tools.

Leverage existing language ecosystems:

Registry-based package manager with strong security features:

Zero-configuration installer that works with any GitHub/GitLab repository following standard conventions:

Support for external plugin ecosystems:

When you specify a tool, mise determines the backend using this priority:

The mise registry defines a priority order for which backend to use for each tool, so typically end-users don't need to know which backend to choose unless they want tools not available in the registry or want to override the default selection.

You can override the backend for any tool using the MISE_BACKENDS_<TOOL> environment variable pattern. The tool name is converted to SHOUTY_SNAKE_CASE (uppercase with underscores replacing hyphens).

The registry (mise registry) maps short names to full backend specifications with a preferred priority order:

Core tools should generally always be used when available, as they provide the best performance and integration with mise.

Some backends have dependencies on others:

mise automatically handles these dependencies, installing Node.js before npm tools, pipx before pipx tools, etc.

Some backends support additional configuration:

**Examples:**

Example 1 (unknown):
```unknown
pub trait Backend {
    async fn list_remote_versions(&self) -> Result<Vec<String>>;
    async fn install_version(&self, ctx: &InstallContext, tv: &ToolVersion) -> Result<()>;
    async fn uninstall_version(&self, tv: &ToolVersion) -> Result<()>;
    // ... other methods
}
```

Example 2 (unknown):
```unknown
# Use vfox backend for php
export MISE_BACKENDS_PHP='vfox:mise-plugins/vfox-php'
mise install php@latest
```

Example 3 (unknown):
```unknown
# ~/.config/mise/config.toml
[aliases]
go = "core:go"                    # Use core backend
terraform = "aqua:hashicorp/terraform"  # Use aqua backend
```

Example 4 (unknown):
```unknown
# ~/.config/mise/config.toml
[settings]
disable_backends = ["asdf", "vfox"] # Don't use these backends
```

---

## mise config generate ​

**URL:** https://mise.jdx.dev/cli/config/generate.html

**Contents:**
- mise config generate ​
- Flags ​
  - -t --tool-versions <TOOL_VERSIONS> ​
  - -o --output <OUTPUT> ​

Generate a mise.toml file

Path to a .tool-versions file to import tools from

Output to file instead of stdout

**Examples:**

Example 1 (unknown):
```unknown
mise cf generate > mise.toml
mise cf generate --output=mise.toml
```

---

## Dev Tools ​

**URL:** https://mise.jdx.dev/dev-tools/index.html

**Contents:**
- Dev Tools ​
- How it works ​
  - Tool Resolution Flow ​
  - Environment Integration ​
  - Path Management ​
  - Configuration Hierarchy ​
- Tool Options ​
  - Table Format (Recommended) ​
  - Dotted Notation ​
  - Generic Nested Support ​

Like asdf (or nvm or pyenv but for any language), it manages dev tools like node, python, cmake, terraform, and hundreds more.

mise is a tool that manages installations of programming language runtimes and other tools for local development. For example, it can be used to manage multiple versions of Node.js, Python, Ruby, Go, etc. on the same machine.

Once activated, mise can automatically switch between different versions of tools based on the directory you're in. This means that if you have a project that requires Node.js 18 and another that requires Node.js 22, mise will automatically switch between them as you move between the two projects. See tools available for mise with in the registry.

To know which tool version to use, mise will typically look for a mise.toml file in the current directory and its parents. To get an idea of how tools are specified, here is an example of a mise.toml file:

It's also compatible with asdf .tool-versions files as well as idiomatic version files like .node-version and .ruby-version. See configuration for more details.

mise is inspired by asdf and can leverage asdf's vast plugin ecosystem under the hood. However, it is much faster than asdf and has a more friendly user experience.

mise manages development tools through a sophisticated but user-friendly system that automatically handles tool installation, version management, and environment setup.

When you enter a directory or run a command, mise follows this process:

mise provides several ways to integrate with your development environment:

Automatic Activation: With mise activate, mise hooks into your shell prompt and automatically updates your environment when you change directories:

On-Demand Execution: Use mise exec to run commands with mise's environment without permanent activation:

Shims: mise can create lightweight wrapper scripts that automatically use the correct tool versions:

mise modifies your PATH environment variable to prioritize the correct tool versions:

This ensures that when you run node, you get the version specified in your project configuration, not a system-wide installation.

mise supports nested configuration that cascades from broad to specific settings:

Each level can override or extend the previous ones, giving you fine-grained control over tool versions across different contexts.

Tool options allow you to customize how tools are installed and configured. They support nested configurations for better organization, particularly useful for platform-specific settings.

The cleanest way to specify nested options is using TOML tables:

You can also use dotted notation for simpler nested configurations:

Any backend can use nested options for organizing complex configurations:

Internally, nested options are flattened to dot notation (e.g., platforms.macos-x64.url, database.host, cache.redis.port) for backend access.

Run a command immediately after a tool finishes installing by adding a postinstall field to that tool's configuration. This is separate from [hooks].postinstall and applies only to when a specific tool is installed.

You can restrict tools to specific operating systems using the os field:

The os field accepts an array of operating system identifiers:

If a tool specifies an os restriction and the current operating system is not in the list, mise will skip installing and using that tool.

mise uses intelligent caching to minimize overhead:

This ensures that mise adds minimal latency to your daily development workflow.

After activating, mise will update env vars like PATH whenever the directory is changed or the prompt is displayed. See the FAQ.

After activating, every time your prompt displays it will call mise hook-env to fetch new environment variables. This should be very fast. It exits early if the directory wasn't changed or mise.toml/.tool-versions files haven't been modified.

mise modifies PATH ahead of time so the runtimes are called directly. This means that calling a tool has zero overhead and commands like which node returns the real path to the binary. Other tools like asdf only support shim files to dynamically locate runtimes when they're called which adds a small delay and can cause issues with some commands. See shims for more information.

Here are some of the most important commands when it comes to working with dev tools. Click the header for each command to go to its reference documentation page to see all available flags/options and more examples.

For some users, mise use might be the only command you need to learn. It will do the following:

mise use node@22 will install the latest version of node-22 and create/update the mise.toml config file in the local directory. Anytime you're in that directory, that version of node will be used.

mise use -g node@22 will do the same but update the global config (~/.config/mise/config.toml) so unless there is a config file in the local directory hierarchy, node-22 will be the default version for the user.

mise install will install but not activate tools—meaning it will download/build/compile the tool into ~/.local/share/mise/installs but you won't be able to use it without "setting" the version in a .mise-toml or .tool-versions file.

If you're coming from asdf, there is no need to also run mise plugin add to first install the plugin, that will be done automatically if needed. Of course, you can manually install plugins if you wish or you want to use a plugin not in the default registry.

There are many ways it can be used:

mise x can be used for one-off commands using specific tools. e.g.: if you want to run a script with python3.12:

Python will be installed if it is not already. mise x will read local/global .mise-toml/.tool-versions files as well, so if you don't want to use mise activate or shims you can use mise by just prefixing commands with mise x --:

If you use this a lot, an alias can be helpful:

Similarly, mise run can be used to execute tasks which will also activate the mise environment with all of your tools.

mise provides several mechanisms to automatically install missing tools or versions as needed. Below, these are grouped by how and when they are triggered, with relevant settings for each. All mechanisms require the global auto_install setting to be enabled (all auto_install settings are enabled by default).

When you run a command like mise x or mise r, mise will automatically install any missing tool versions required to execute the command.

If you type a command in your shell (e.g., node) and it is not found, mise can attempt to auto-install the missing tool version if it knows which tool provides that binary.

Disable auto_install for specific tools by setting auto_install_disable_tools to a list of tool names.

**Examples:**

Example 1 (unknown):
```unknown
[tools]
node = '22'
python = '3'
ruby = 'latest'
```

Example 2 (unknown):
```unknown
eval "$(mise activate zsh)"  # In your ~/.zshrc
cd my-project               # Automatically loads mise.toml tools
```

Example 3 (unknown):
```unknown
mise exec -- node my-script.js  # Runs with tools from mise.toml
```

Example 4 (unknown):
```unknown
mise activate --shims  # Creates shims instead of modifying PATH
```

---

## Go Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/go.html

**Contents:**
- Go Backend ​
- Dependencies ​
- Usage ​
- Tool Options ​
  - tags ​

You may install packages directly via go install even if there isn't an asdf plugin for it.

The code for this is inside of the mise repository at ./src/backend/go.rs.

This relies on having go installed. Which you can install via mise:

Any method of installing go is fine if you want to install go some other way. mise will use whatever go is on PATH.

The following installs the latest version of hivemind and sets it as the active version on PATH:

The following tool-options are available for the go backend—these go in [tools] in mise.toml.

Specify go build tags (passed as go install --tags):

**Examples:**

Example 1 (unknown):
```unknown
mise use -g go
```

Example 2 (unknown):
```unknown
$ mise use -g go:github.com/DarthSim/hivemind
$ hivemind --help
Hivemind version 1.1.0
```

Example 3 (unknown):
```unknown
[tools]
"go:github.com/golang-migrate/migrate/v4/cmd/migrate" = { version = "latest", tags = "postgres" }
```

---

## Aqua Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/aqua.html

**Contents:**
- Aqua Backend ​
- Usage ​
- Settings ​
  - aqua.baked_registry
  - aqua.cosign
  - aqua.cosign_extra_args
  - aqua.github_attestations
  - aqua.minisign
  - aqua.registry_url
  - aqua.slsa

Aqua tools may be used natively in mise. aqua is the ideal backend to use for new tools since they don't require plugins, they work on windows, they offer security features in addition to checksums. aqua installs also show more progress bars, which is nice.

You do not need to separately install aqua. The aqua CLI is not used in mise at all. What is used is the aqua registry which is a bunch of yaml files that get compiled into the mise binary on release. Here's an example of one of these files: aqua:hashicorp/terraform. mise has a reimplementation of aqua that knows how to work with these files to install tools.

As of this writing, aqua is relatively new to mise and because a lot of tools are being converted from asdf to aqua, there may be some configuration in aqua tools that need to be tightened up. I put some common issues below and would strongly recommend contributing changes back to the aqua registry if you notice problems. The maintainer is super responsive and great to work with.

If all else fails, you can disable aqua entirely with MISE_DISABLE_BACKENDS=aqua.

Currently aqua tools don't support setting environment variables or doing more than simply downloading binaries though (and I'm not sure this functionality would ever get added), so some tools will likely always require plugins like asdf/vfox.

The code for this is inside the mise repository at ./src/backend/aqua.rs.

The following installs the latest version of ripgrep and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

Some tools will default to use aqua if they're specified in registry.toml to use the aqua backend. To see these tools, run mise registry | grep aqua:.

Use baked-in aqua registry.

Use cosign to verify aqua tool signatures.

Extra arguments to pass to cosign when verifying aqua tool signatures.

Enable/disable GitHub Artifact Attestations verification for aqua tools. When enabled, mise will verify the authenticity and integrity of downloaded tools using GitHub's artifact attestation system.

Use minisign to verify aqua tool signatures.

URL to fetch aqua registry from. This is used to install tools from the aqua registry.

If this is set, the baked-in aqua registry is not used.

By default, the official aqua registry is used: https://github.com/aquaproj/aqua-registry

Use SLSA to verify aqua tool signatures.

Aqua backend supports multiple security verification methods to ensure the integrity and authenticity of downloaded tools. mise provides native Rust implementation for all verification methods, eliminating the need for external CLI tools like cosign, slsa-verifier, or gh.

GitHub Artifact Attestations provide cryptographic proof that artifacts were built by specific GitHub Actions workflows. mise verifies these attestations natively to ensure the authenticity and integrity of downloaded tools.

Registry Configuration Example:

mise natively verifies Cosign signatures without requiring the cosign CLI tool to be installed.

mise natively verifies SLSA (Supply-chain Levels for Software Artifacts) provenance without requiring the slsa-verifier CLI tool.

During tool installation, mise will:

Example output during installation:

If verification fails:

To disable all verification temporarily:

Here's some common issues I've seen when working with aqua tools.

The aqua registry defines supported envs for each tool of the os/arch. I've noticed some of these are simply missing os/arch combos that are in fact supported—possibly because it was added after the registry was created for that tool.

The fix is simple, just edit the supported_envs section of registry.yaml for the tool in question.

This is a weird one that causes weird issues in mise. In general in mise we like versions like 1.2.3 with no decoration like v1.2.3 or cli-v1.2.3. This consistency not only makes mise.toml cleaner but, it also helps make things like mise up function right because it's able to parse it as semver without dealing with a bunch of edge-cases.

Really if you notice aqua tools are giving you versions that aren't simple triplets, it's worth fixing.

One common thing I've seen is registries using a version_filter expression like Version startsWith "Version startsWith "atlascli/"".

This ultimately causes the version to be atlascli/1.2.3 which is not what we want. The fix is to use version_prefix instead of version_filter and just put the prefix in the version_prefix field. In this example, it would be atlascli/. mise will automatically strip this out and add it back in, which it can't do with version_filter.

**Examples:**

Example 1 (unknown):
```unknown
$ mise use -g aqua:BurntSushi/ripgrep
$ rg --version
ripgrep 14.1.1
```

Example 2 (unknown):
```unknown
[tools]
"aqua:BurntSushi/ripgrep" = "latest"
```

Example 3 (unknown):
```unknown
# Enable/disable GitHub attestations verification (default: true)
export MISE_AQUA_GITHUB_ATTESTATIONS=true
```

Example 4 (unknown):
```unknown
packages:
  - type: github_release
    repo_owner: cli
    repo_name: cli
    github_artifact_attestations:
      signer_workflow: cli/cli/.github/workflows/deployment.yml
```

---

## pipx Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/pipx.html

**Contents:**
- pipx Backend ​
- Dependencies ​
- Usage ​
- Python upgrades ​
  - Supported Pipx Syntax ​
- Settings ​
  - pipx.registry_url
  - pipx.uvx
- Tool Options ​
  - extras ​

pipx is a tool for running Python CLIs in isolated virtualenvs. This is necessary for Python CLIs because it prevents conflicting dependencies between CLIs or between a CLI and Python projects. In essence, this backend lets you add Python CLIs to mise.

To be clear, pipx is not pip and it's not used to manage Python dependencies generally. mise is a tool manager, not a dependency manager like pip, uv, or poetry. You can, however, use mise to install said package managers. You'd want to use the pipx backend to install a CLI like "black", not a library like "NumPy" or "requests".

Somewhat confusingly, the pipx backend will actually default to using uvx (the equivalent of pipx for uv) if uv is installed. This should just mean that it installs much faster, but see below to disable or configure since occasionally tools don't work with uvx.

The pipx backend supports the following sources:

The code for this is inside of the mise repository at ./src/backend/pipx.rs.

This relies on having pipx installed. You can install it with or without mise. Here is how to install pipx with mise:

Other installation instructions

The following installs the latest version of black and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

If the python version used by a pipx package changes, (by mise or system python), you may need to reinstall the package. This can be done with:

Or you can reinstall all pipx packages with:

mise should do this automatically when using mise up python.

Other syntax may work but is unsupported and untested.

Set these with mise settings set [VARIABLE] [VALUE] or by setting the environment variable listed.

URL to use for pipx registry.

This is used to fetch the latest version of a package from the pypi registry.

The default is https://pypi.org/pypi/{}/json which is the JSON endpoint for the pypi registry.

You can also use the HTML endpoint by setting this to https://pypi.org/simple/{}/.

If true, mise will use uvx instead of pipx if uv is installed and on PATH. This makes installing CLIs much faster by using uv as the package manager.

You can install it with mise:

The following tool-options are available for the pipx backend—these go in [tools] in mise.toml.

Install additional components.

Additional arguments to pass to pipx when installing the package.

Set to false to always disable uv for this tool.

Additional arguments to pass to uvx when installing the package.

**Examples:**

Example 1 (unknown):
```unknown
mise use -g python
pip install --user pipx
```

Example 2 (unknown):
```unknown
$ mise use -g pipx:psf/black
$ black --version
black, 24.3.0
```

Example 3 (unknown):
```unknown
[tools]
"pipx:psf/black" = "latest"
```

Example 4 (unknown):
```unknown
mise install -f pipx:psf/black
```

---

## mise plugins update ​

**URL:** https://mise.jdx.dev/cli/plugins/update.html

**Contents:**
- mise plugins update ​
- Arguments ​
  - [PLUGIN]… ​
- Flags ​
  - -j --jobs <JOBS> ​

Updates a plugin to the latest version

note: this updates the plugin itself, not the runtime versions

Number of jobs to run in parallel Default: 4

**Examples:**

Example 1 (unknown):
```unknown
mise plugins update            # update all plugins
mise plugins update node       # update only node
mise plugins update node#beta  # specify a ref
```

---

## Tool Stubs ​

**URL:** https://mise.jdx.dev/dev-tools/tool-stubs.html

**Contents:**
- Tool Stubs ​
- Overview ​
- Tool (non-http) Stubs ​
- Configuration Fields ​
  - Optional Fields ​
- HTTP Stubs ​
  - Platform-Specific Binary Paths ​
- Generating Tool Stubs (http) ​
  - Basic Generation ​
  - Platform-Specific Generation ​

Tool stubs allow you to create executable files with embedded TOML configuration for tool execution. They provide a convenient way to define tool versions, backends, and execution parameters directly within executable scripts. They are also a good way to have some tools in mise lazy-load since the tools are only fetched when called and not when calling something like mise install.

This feature is inspired by dotslash, which pioneered the concept of executable files with embedded configuration for portable tool execution.

A tool stub is an executable file that begins with a shebang line pointing to mise tool-stub and contains TOML configuration specifying which tool to execute and how to execute it. When the stub is run, mise automatically installs the specified tool version (if needed) and executes it with the provided arguments.

Tool stubs can use any mise backend but because they default to http—and http backend tools have things like urls and don't require a version—the http stubs look a bit different than non-http stubs.

Tool stubs are particularly useful for adding less-commonly used tools to your mise setup. Since tools are only installed when their stub is first executed, you can define many tools without the overhead of installing them all upfront. This is perfect for specialized tools, testing utilities, or project-specific binaries that you might not use every day.

The -S flag tells env to split the command line on spaces, allowing multiple arguments to be passed to the interpreter. This is necessary because shebangs on Unix systems traditionally only support a single argument after the interpreter path. Using env -S mise tool-stub allows the shebang to work correctly by splitting it into env → mise → tool-stub.

Tool stub configuration is essentially a subset of what can be done in mise.toml [tools] sections, with the addition of a tool field to specify which tool to use. All the same options available for tool configuration in mise.toml are supported in tool stubs.

For multi-platform tarballs:

For platform-specific tarballs:

Different platforms may have different binary structures or names. You can specify platform-specific bin fields when the binary path differs between platforms:

The tool stub generator automatically detects when platforms have different binary paths and will generate platform-specific bin fields when needed, or use a global bin field when all platforms have the same binary structure.

tool stubs default to the HTTP backend if no tool field is specified and a url field is present. See the HTTP backend documentation for full details on configuring HTTP-based tools.

While you can manually create tool stubs with TOML configuration, mise provides a mise generate tool-stub command to automatically create stubs for HTTP-based tools.

When using platform-specific URLs, the tool stub generator will append new platforms to existing stub files rather than overwriting them. This allows you to incrementally build cross-platform tool stubs by running the command multiple times with different platforms.

Generate a tool stub for a tool distributed via HTTP:

For tools with different URLs per platform, you can generate all platforms at once:

Auto-Platform Detection: If the URL contains platform information, you can omit the platform prefix and let mise auto-detect it:

Or build them incrementally by adding platforms one at a time:

The generator will preserve existing configuration and merge new platforms into the [platforms] table. If you specify a platform that already exists, its URL will be updated.

The generator automatically detects and extracts various archive formats:

Running the generation command produces an executable stub like:

The generator automatically:

Make the stub executable and run it directly:

Execute using the mise tool-stub command—useful for testing if something isn't working right:

Tool stubs implement intelligent caching which reduces the overhead mise has when running stubs:

Cached stubs have ~4ms of overhead.

For basic use cases, you can quickly create simple tool stubs using the mise x command as an alternative to writing TOML configuration manually:

This approach is ideal for simple tool execution without the need for custom options, environment variables, or platform-specific settings. For more complex configurations, use the full TOML configuration format described above.

**Examples:**

Example 1 (unknown):
```unknown
#!/usr/bin/env -S mise tool-stub
# Optional comment describing the tool

version = "1.0.0"
tool = "python"
bin = "python"
```

Example 2 (unknown):
```unknown
#!/usr/bin/env -S mise tool-stub
url = "https://example.com/releases/1.0.0/tool-linux-x64.tar.gz"
```

Example 3 (unknown):
```unknown
#!/usr/bin/env -S mise tool-stub
[platforms.linux-x64]
url = "https://example.com/releases/1.0.0/tool-linux-x64.tar.gz"

[platforms.darwin-arm64]
url = "https://example.com/releases/1.0.0/tool-macos-arm64.tar.gz"
```

Example 4 (unknown):
```unknown
#!/usr/bin/env -S mise tool-stub
# Global bin field used when platforms have the same structure
bin = "bin/tool"

[platforms.linux-x64]
url = "https://example.com/tool-linux.tar.gz"
# Uses global bin field: "bin/tool"

[platforms.windows-x64]
url = "https://example.com/tool-windows.zip"
bin = "tool.exe"  # Platform-specific binary for Windows
```

---

## HTTP Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/http.html

**Contents:**
- HTTP Backend ​
- Usage ​
- Supported HTTP Syntax ​
- Tool Options ​
  - url (Required) ​
  - Platform-specific URLs ​
  - checksum ​
  - Platform-specific Checksums ​
  - size ​
  - Platform-specific Size ​

You may install tools directly from HTTP URLs using the http backend. This backend downloads files from any HTTP/HTTPS URL and is ideal for tools that distribute pre-built binaries or archives through direct download links.

The code for this is inside of the mise repository at ./src/backend/http.rs.

The following installs a tool from a direct HTTP URL:

The version will be set in ~/.config/mise/config.toml with the following format:

The following tool-options are available for the http backend—these go in [tools] in mise.toml.

Specifies the HTTP URL to download the tool from. The URL supports templating with :

You can also use static URLs without templating:

For tools that need different downloads per platform, use the table format:

You can use either macos or darwin, and x64 or amd64 for platform keys. macos and x64 are preferred in documentation and examples, but all variants are accepted.

OS/architecture values use mise's conventions: linux, macos, windows for operating systems and x64, arm64 for architectures. For platform-specific URLs, use the appropriate platform key (e.g., macos-x64, linux-arm64) and specify the full URL for each platform.

If you mess up and use something like darwin-aarch64 mise will try to figure out what you meant and do the right thing anyhow.

Verify the downloaded file with a checksum:

Instead of specifying the checksum here, you can use mise.lock to manage checksums.

Verify the downloaded file size:

You can specify different sizes for different platforms:

Number of directory components to strip when extracting archives:

If strip_components is not explicitly set, mise will automatically detect when to apply strip_components = 1. This happens when the extracted archive contains exactly one directory at the root level and no files. This is common with tools like ripgrep that package their binaries in a versioned directory (e.g., ripgrep-14.1.0-x86_64-unknown-linux-musl/rg). The auto-detection ensures the binary is placed directly in the install path where mise expects it.

Rename the downloaded binary to a specific name. This is useful when downloading single binaries that have platform-specific names:

When downloading single binaries (not archives), mise automatically removes OS/arch suffixes from the filename. For example, docker-compose-linux-x86_64 becomes docker-compose automatically. Use the bin option only when you need a specific custom name.

Specify the directory containing binaries within the extracted archive, or where to place the downloaded file. This supports templating with :

Binary path lookup order:

The HTTP backend implements an intelligent caching system to optimize disk usage and installation speed:

Downloaded and extracted files are cached in $MISE_CACHE_DIR/http-tarballs/ instead of being stored separately for each tool installation. By default:

Cache keys are generated based on the file content to ensure identical downloads are shared across tools:

Example cache directory structure:

Tool installations are symlinks to the cached extracted content:

This approach provides several benefits:

Each cache entry includes a metadata.json file with information about the cached content:

The HTTP backend cache follows mise's standard cache management:

**Examples:**

Example 1 (unknown):
```unknown
mise use -g http:my-tool[url=https://example.com/releases/my-tool-v1.0.0.tar.gz]@1.0.0
```

Example 2 (unknown):
```unknown
[tools]
"http:my-tool" = { version = "1.0.0", url = "https://example.com/releases/my-tool-v1.0.0.tar.gz" }
```

Example 3 (unknown):
```unknown
[tools]
"http:my-tool" = { version = "1.0.0", url = "https://example.com/releases/my-tool-v{{version}}.tar.gz" }
```

Example 4 (unknown):
```unknown
[tools]
"http:my-tool" = { version = "1.0.0", url = "https://example.com/releases/my-tool-v1.0.0.tar.gz" }
```

---

## mise version ​

**URL:** https://mise.jdx.dev/cli/version.html

**Contents:**
- mise version ​
- Flags ​
  - -J --json ​

Display the version of mise

Displays the version, os, architecture, and the date of the build.

If the version is out of date, it will display a warning.

Print the version information in JSON format

**Examples:**

Example 1 (unknown):
```unknown
mise version
mise --version
mise -v
mise -V
```

---

## Backends ​

**URL:** https://mise.jdx.dev/dev-tools/backends/

**Contents:**
- Backends ​

Backends are package managers or ecosystems that mise uses to install tools and plugins. Each backend can install and manage multiple tools from its ecosystem. For example, the npm backend can install many different tools like npm:prettier, or the pipx backend can install tools like pipx:black. This allows mise to support a wide variety of tools and languages by leveraging different package managers and their ecosystems.

When you run the mise use command, mise will determine the appropriate backend to use based on the tool you are trying to manage. The backend will then handle the installation, configuration, and any other necessary steps to ensure the tool is ready to use.

For more details on how backends fit into mise's overall design, see the backend architecture documentation.

Below is a list of the available backends in mise:

---

## Ubi Backend ​

**URL:** https://mise.jdx.dev/dev-tools/backends/ubi.html

**Contents:**
- Ubi Backend ​
- Usage ​
- Tool Options ​
  - exe ​
  - rename_exe ​
  - matching ​
  - matching_regex ​
  - provider ​
  - api_url ​
  - extract_all ​

You may install GitHub Releases and URL packages directly using ubi backend. ubi is directly compiled into the mise codebase so it does not need to be installed separately to be used. ubi is preferred over plugins for new tools since it doesn't require a plugin, supports Windows, and is really easy to use.

ubi doesn't require plugins or even any configuration for each tool. What it does is try to deduce what the proper binary/tarball is from GitHub releases and downloads the right one. As long as the vendor uses a somewhat standard labeling scheme for their releases, ubi should be able to figure it out.

The code for this is inside of the mise repository at ./src/backend/ubi.rs.

The following installs the latest version of goreleaser and sets it as the active version on PATH:

The version will be set in ~/.config/mise/config.toml with the following format:

The following tool-options are available for the ubi backend—these go in [tools] in mise.toml.

The exe option allows you to specify the executable name in the archive. This is useful when the archive contains multiple executables.

If you get an error like could not find any files named cli in the downloaded zip file, you can use the exe option to specify the executable name:

The rename_exe option allows you to specify the name of the executable once it has been extracted.

use the rename_exe option to specify the target executable name:

Set a string to match against the release filename when there are multiple files for your OS/arch, i.e. "gnu" or "musl". Note that this is only used when there is more than one matching release filename for your OS/arch. If only one release asset matches your OS/arch, then this will be ignored.

Set a regular expression string that will be matched against release filenames before matching against OS/arch. If the pattern yields a single match, that release will be selected. If no matches are found, this will result in an error.

Set the provider type to use for fetching assets and release information. Either github or gitlab (default is github). Ensure the provider is set to the correct type if you use api_url as the type probably cannot be derived correctly from the URL.

Set the URL for the provider's API. This is useful when using a self-hosted instance.

Set to true to extract all files in the tarball instead of just the "bin". Not compatible with exe nor rename_exe.

The directory in the tarball where the binary(s) are located. This is useful when the binary is not in the root of the tarball. This only makes sense when extract_all is set to true.

Binary path lookup order:

Set a regex to filter out tags that don't match the regex. This is useful when a vendor has a bunch of releases for unrelated CLIs in the same repo. For example, cargo-bins/cargo-binstall has a bunch of releases for unrelated CLIs that are not cargo-binstall. This option can be used to filter out those releases.

If you are using a self-hosted GitHub/GitLab instance, you can set the provider and api_url tool options. Additionally, you can set the MISE_GITHUB_ENTERPRISE_TOKEN or MISE_GITLAB_ENTERPRISE_TOKEN environment variable to authenticate with the API.

Sometimes vendors use strange formats for their releases that ubi can't figure out, possibly for a specific os/arch combination. For example this recently happened in this ticket because a vendor used "mac" instead of the more common "macos" or "darwin" tags.

Try using ubi by itself to see if the issue is related to mise or ubi:

Another issue is that a GitHub release may have a bunch of tarballs, some that don't contain the CLI you want, you can use the matching field in order to specify a string to match against the release.

ubi assumes that the repo name is the same as the binary name, however that is often not the case. For example, BurntSushi/ripgrep gives us a binary named rg not ripgrep. In this case, you can specify the binary name with the exe field:

This issue is actually with mise and not with ubi. mise needs to be able to list the available versions of the tools so that "latest" points to whatever is the actual latest release of the CLI. What sometimes happens is vendors will have GitHub releases for unrelated things. For example, cargo-bins/cargo-binstall is the repo for cargo-binstall, however it has a bunch of releases for unrelated CLIs that are not cargo-binstall. We need to filter these out and that can be specified with the tag_regex tool option:

Now when running mise ls-remote ubi:cargo-bins/cargo-binstall[tag_regex=^\d+\.] you should only see versions starting with a number. Note that this command is cached so you likely will need to run mise cache clear first.

**Examples:**

Example 1 (unknown):
```unknown
$ mise use -g ubi:goreleaser/goreleaser
$ goreleaser --version
1.25.1
```

Example 2 (unknown):
```unknown
[tools]
"ubi:goreleaser/goreleaser" = "latest"
```

Example 3 (unknown):
```unknown
[tools]
"ubi:cli/cli" = { version = "latest", exe = "gh" } # github's cli
```

Example 4 (unknown):
```unknown
[tools]
"ubi:cli/cli" = { version = "latest", exe = "gh", rename_exe = "github" } # github's cli
```

---
