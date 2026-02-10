# Tauri - Security

**Pages:** 8

---

## Tauri Ecosystem Security

**URL:** llms-txt#tauri-ecosystem-security

**Contents:**
  - Build Pipelines
  - Signed Commits
  - Code Review
  - Release Process

Our Tauri organization ecosystem is hosted on GitHub and facilitates several
features to make our repositories more resilient against adversaries targeting
our source code and releases.

To reduce risk and to comply with commonly adopted best practices we have the following methods
in place.

The process of releasing our source-code artifacts is highly automated
in GitHub build pipelines using GitHub actions, yet mandates kickoff and review from real humans.

Our core repositores require signed commits to reduce risk of impersonation and
to allow identification of attributed commits after detection of possible compromise.

All Pull Requests (PRs) merged into our repositories need approval from at least one maintainer of the
project, which in most cases is the working group.
Code is generally reviewed in PRs and default security workflows and checks are run to ensure
the code adheres to common standards.

Our working group reviews code changes, tags PRs with scope, and makes sure that everything stays up to date.
We strive to internally audit all security relevant PRs before publishing minor and major releases.

And when its time to publish a new version, one of the maintainers tags a new release on dev, which:

- Validates core
- Runs tests
- Audits security for crates and npm
- Generates changelogs
- Creates artifacts
- Creates a draft release

Then the maintainer reviews the release notes, edits if necessary, and a new release is forged.

---

## Security

**URL:** llms-txt#security

**Contents:**
- Trust Boundaries
- (Not) Bundling WebViews
- Ecosystem
- Coordinated Disclosure

import { CardGrid, LinkCard } from '@astrojs/starlight/components';

This page is designed to explain the high-level concepts and security features
at the core of Tauri's design and ecosystem that make you, your applications and your users more secure by default.

It also includes advice on best practices, how to report vulnerabilities to us
and references to detailed concept explanations.

It is important to remember that the security of your Tauri application is the sum
of the overall security of Tauri itself, all Rust and npm dependencies,
your code, and the devices that run the final application.
The Tauri team does its best to do their part, the security community does its part
and you should also follow some important best practices.

> Trust boundary is a term used in computer science and security which describes
> a boundary where program data or execution changes its level of "trust,"
> or where two principals with different capabilities exchange data or commands.
> [^wikipedia-trust-boundary]

[^wikipedia-trust-boundary]: [https://en.wikipedia.org/wiki/Trust_boundary](https://en.wikipedia.org/wiki/Trust_boundary).

Tauri's security model differentiates between Rust code written for the application's
core and frontend code written in any framework or language understood by the system
WebView.

Inspecting and strongly defining all data passed between boundaries is
very important to prevent trust boundary violations.
If data is passed without access control between these boundaries then
it's easy for attackers to elevate and abuse privileges.

The [IPC layer](/concept/inter-process-communication/) is the bridge for communication between these two trust
groups and ensures that boundaries are not broken.

![IPC Diagram](@assets/security/tauri-trust-boundaries.svg)

Any code executed by the plugins or the application core has full
access to all available system resources and is not constrained.

Any code executed in the WebView has only access to exposed system resources via the well-defined IPC layer.
Access to core application commands is configured and restricted by capabilities defined in the application configuration.
The individual command implementations enforce the optional fine-grained access levels also defined
in the capabilities configuration.

Learn more about the individual components and boundary enforcement:

<CardGrid>
  <LinkCard title="Permissions" href="/security/permissions/" />
  <LinkCard title="Scopes" href="/security/scope/" />
  <LinkCard title="Capabilities" href="/security/capabilities/" />
  <LinkCard title="Runtime Authority" href="/security/runtime-authority/" />
</CardGrid>

Tauri allows developers to choose their own frontend stack and framework.
This means that we cannot provide a hardening guide for every frontend stack of
of choice, but Tauri provides generic features to control and contain the attack surface.

<CardGrid>
  <LinkCard title="Content Security Policy (CSP)" href="/security/csp/" />
  <LinkCard
    title="Isolation Pattern"
    href="/concept/inter-process-communication/isolation/"
  />
</CardGrid>

## (Not) Bundling WebViews

Tauri's approach is to rely on the operating system WebView and not bundling
the WebView into the application binary.

This has a multitide of reasons but from a security perspective the most
important reason is the average time it takes from publication of a
security patched version of a WebView to being rolled out to the
application end user.

![IPC Diagram](@assets/security/tauri-update-lag.svg)

We have observed that WebView packet maintainer and operating system packet maintainers
are in average significantly faster to patch and roll out security patched
Webview releases than application developers who bundle the WebView directly
with their application.

There are exceptions from this observation and in theory both paths can be
taken in a similar time frame but this involves a larger overhead infrastructure
for each application.

Bundling has it's drawbacks from a Tauri application developer experience and
we do not think it is inherently insecure but the current design is a trade off
that significantly reduces known vulnerabilities in the wild.

The Tauri organization provides and maintains more than just the Tauri
repository, and to ensure we provide a reasonable secure
multi platform application framework, we make sure to go some extra miles.

To learn more about how we secure our development process,
what you could adapt and implement, what known threats your application
can face and what we plan to improve or harden in the future, you
can check out the following documents:

<CardGrid>
  <LinkCard title="Ecosystem Security" href="/security/ecosystem/" />
  <LinkCard title="Application Lifecycle Threats" href="/security/lifecycle/" />
  <LinkCard title="Future Work" href="/security/future/" />
</CardGrid>

## Coordinated Disclosure

If you feel that there is a security concern or issue with anything in Tauri
or other repositories in our organization, **please do not publicly comment on your findings**.
Instead, reach out directly to our security team.

The preferred disclosure method is via [Github Vulnerability Disclosure](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability#privately-reporting-a-security-vulnerability)
on the affected repository.
Most of our repositories have this feature enabled but if in doubt please submit via the [Tauri repository](https://github.com/tauri-apps/tauri/security/advisories/new).

Alternatively you can contact us via email at: [security@tauri.app](mailto:security@tauri.app).

Although we do not currently have a budget for security bounties,
in some cases, we will consider rewarding coordinated disclosure with our limited resources.

---

## Using Plugin Permissions

**URL:** llms-txt#using-plugin-permissions

import { Steps } from '@astrojs/starlight/components';
import ShowSolution from '@components/ShowSolution.astro'
import Cta from '@fragments/cta.mdx';

The goal of this exercise is to get a better understanding on how
plugin permissions can be enabled or disabled, where they are described
and how to use default permissions of plugins.

At the end you will have the ability to find and use permissions of
arbitrary plugins and understand how to custom tailor existing permissions.
You will have an example Tauri application where a plugin and plugin specific
permissions are used.

1. ### Create Tauri Application

Create your Tauri application.
    In our example we will facilitate [`create-tauri-app`](https://github.com/tauri-apps/create-tauri-app):

We will proceed in this step-by-step explanation with `pnpm` but you can choose another
    package manager and replace it in the commands accordingly.

2. ### Add the `file-system` Plugin to Your Application

To search for existing plugins you can use multiple resources.

The most straight forward way would be to check out if your plugin is already
    in the [Plugins](/plugin/) section of the documentation and therefore part of Tauri's
    maintained plugin set.
    The Filesystem plugin is part of the Tauri plugin workspace and you can add it to
    your project by following the [instructions](/plugin/file-system/#setup).

If the plugin is part of the community effort you can most likely find it
    on [crates.io](https://crates.io/search?q=tauri-plugin-) when searching for `tauri-plugin-<your plugin name>`.

<ShowSolution>
    If it is an existing plugin from our workspace you can use the automated way:

If you have found it on [crates.io](https://crates.io/crates/tauri-plugin-fs)
    you need to manually add it as a dependency and modify the Tauri builder
    to initialize the plugin:

Modify `lib.rs` to initialize the plugin:

3. ### Understand the Default Permissions of the `fs` Plugin
    
    Each plugin has a `default` permission set, which contains
    all permissions and scopes to use the plugin out of the box
    with a reasonable minimal feature set.
    
    In the case of official maintained plugins you can find a
    rendered description in the documentation
    (eg. [fs default](/plugin/file-system/#default-permission)).

In case you are figuring this out for a community plugin you
    need to check out the source code of the plugin.
    This should be defined in `your-plugin/permissions/default.toml`.

<ShowSolution>
    
    </ShowSolution>

4. ### Find the Right Permissions
      
      This step is all about finding the permissions you need to
      for your commands to be exposed to the frontend with the minimal
      access to your system.

The `fs` plugin has autogenerated permissions which will disable
      or enable individual commands and allow or disable global scopes.

These can be found in the [documentation](/plugin/file-system/#permission-table)
      or in the source code of the plugin (`fs/permissions/autogenerated`).

Let us assume we want to enable writing to a text file `test.txt`
      located in the users `$HOME` folder.

For this we would search in the autogenerated permissions for a
      permission to enable writing to text files like `allow-write-text-file`
      and then for a scope which would allow us to access the `$HOME/test.txt`
      file.

We need to add these to our `capabilities` section in our
      `src-tauri/tauri.conf.json` or in a file in the `src-tauri/capabilities/` folder.
      By default there is already a capability in `src-tauri/capabilities/default.json` we 
      can modify.

Since there are only autogenerated scopes in the `fs` plugin to
      access the full `$HOME` folder, we need to configure our own scope.
      This scope should be only enabled for the `write-text-file` command
      and should only expose our `test.txt` file.

<ShowSolution>
      
      </ShowSolution>
    5. ### Test Permissions in Practice

After we have added the necessary permission we want to
        confirm that our application can access the file and write
        it's content.

<ShowSolution>
        We can use this snippet in our application to write to the file:

Replacing the `src/main.ts` with this snippet means we do not need to modify the default `index.html`,
        when using the plain Vanilla+Typescript app.
        Entering any input into the input field of the running app will be
        written to the file on submit.

Let's test now in practice:

After writing into the input and clicking "Submit",
        we can check via our terminal emulator or by manually opening the
        file in your home folder.

You should be presented with your input and finished learning about using permissions from plugins in Tauri applications.
        🥳

If you encountered this error:

Then you very likely did not properly follow the [previous instructions](#find-the-right-permissions).
        </ShowSolution>

**Examples:**

Example 1 (unknown):
```unknown
pnpm create tauri-app
```

Example 2 (unknown):
```unknown
✔ Project name · plugin-permission-demo
    ✔ Choose which language to use for your frontend · TypeScript / JavaScript - (pnpm, yarn, npm, bun)
    ✔ Choose your package manager · pnpm
    ✔ Choose your UI template · Vanilla
    ✔ Choose your UI flavor · TypeScript

    Template created! To get started run:
    cd plugin-permission-demo
    pnpm install
    pnpm tauri dev
```

Example 3 (unknown):
```unknown
pnpm tauri add fs
```

Example 4 (sh):
```sh
cargo add tauri-plugin-fs
```

---

## Permissions

**URL:** llms-txt#permissions

**Contents:**
- Permission Identifier
- Configuration Files
- Examples

Permissions are descriptions of explicit privileges of commands.

It can enable commands to be accessible in the frontend of a Tauri application.
It can map scopes to commands and defines which commands are enabled.
Permissions can enable or deny certain commands, define scopes or combine both.

To grant or deny a permission to your app's window or webview,
you must reference the permission in a [capability](/security/capabilities/).

Permissions can be grouped as a set under a new identifier.
This is called a permission set. This allows you to combine scope related permissions
with command related permissions. It also allows to group or bundle operating
specific permissions into more usable sets.

As a plugin developer you can ship multiple, pre-defined, well named permissions
for all of your exposed commands.

As an application developer you can extend existing plugin permissions or
define them for your own commands.
They can be grouped or extended in a set to be re-used or to simplify the main
configuration files later.

## Permission Identifier

The permissions identifier is used to ensure that permissions can be re-used and have unique names.

With **name** we refer to the plugin crate name without the `tauri-plugin-` prefix.
This is meant as namespacing to reduce likelihood of naming conflicts.
When referencing permissions of the application itself it is not necessary.

- `<name>:default` Indicates the permission is the default for a plugin or application
- `<name>:<command-name>` Indicates the permission is for an individual command

The plugin prefix `tauri-plugin-` will be automatically prepended to the identifier of plugins
at compile time and is not required to be manually specified.

Identifiers are limited to ASCII lower case alphabetic characters `[a-z]` and the maximum length
of the identifier is currently limited to `116` due to the following constants:

## Configuration Files

Simplified example of an example Tauri **plugin** directory structure:

The default permission is handled in a special way,
as it is automatically added to the application
configuration, as long as the Tauri CLI is used to
add plugins to a Tauri application.

For **application** developers the structure is similar:

As an application developer the capability files can be written in `json`/`json5` or `toml`,
whereas permissions only can be defined in `toml`.

Example permissions from the `File System` plugin.

Example implementation extending above plugin permissions in your app:

**Examples:**

Example 1 (toml):
```toml
[[permission]]
identifier = "my-identifier"
description = "This describes the impact and more."
commands.allow = [
    "read_file"
]

[[scope.allow]]
my-scope = "$HOME/*"

[[scope.deny]]
my-scope = "$HOME/secret"
```

Example 2 (rust):
```rust
const IDENTIFIER_SEPARATOR: u8 = b':';
const PLUGIN_PREFIX: &str = "tauri-plugin-";

// https://doc.rust-lang.org/cargo/reference/manifest.html#the-name-field
const MAX_LEN_PREFIX: usize = 64 - PLUGIN_PREFIX.len();
const MAX_LEN_BASE: usize = 64;
const MAX_LEN_IDENTIFIER: usize = MAX_LEN_PREFIX + 1 + MAX_LEN_BASE;
```

Example 3 (sh):
```sh
tauri-plugin
├── README.md
├── src
│  └── lib.rs
├── build.rs
├── Cargo.toml
├── permissions
│  └── <identifier>.json/toml
│  └── default.json/toml
```

Example 4 (sh):
```sh
tauri-app
├── index.html
├── package.json
├── src
├── src-tauri
│   ├── Cargo.toml
│   ├── permissions
│      └── <identifier>.toml
|   ├── capabilities
│      └── <identifier>.json/.toml
│   ├── src
│   ├── tauri.conf.json
```

---

## Capabilities

**URL:** llms-txt#capabilities

**Contents:**
- Target Platform
- Remote API Access
- Security Boundaries
- Schema Files
- Configuration Files
- Core Permissions

Tauri provides application and plugin developers with a capabilities system,
to granually enable and constrain the core exposure to the application frontend running in the
system WebView.

Capabilities define which [permissions](/security/permissions/)
are granted or denied for which windows or webviews.

Capabilities can affect multiple windows and webviews and these can be
referenced in multiple capabilities.

Windows and WebViews which are part of more than one capability
effectively merge the security boundaries and permissions of all
involved capabilities.

Capability files are either defined as a JSON or a TOML file
inside the `src-tauri/capabilities` directory.

It is good practice to use individual files and only reference
them by identifier in the `tauri.conf.json` but it is also possible
to define them directly in the `capabilities` field.

All capabilities inside the `capabilities` directory are automatically enabled
by default.
Once capabilities are explicitly enabled in the `tauri.conf.json`,
only these are used in the application build.

For a full reference of the configuration scheme please see the
[references](/reference/config/) section.

The following example JSON defines a capability that allows the main window
use the default functionality of core plugins and the `window.setTitle` API.

These snippets are part of the
[Tauri configuration](/develop/configuration-files/#tauri-config) file.

This is likely the most common configuration method,
where the individual capabilities are inlined and only
permissions are referenced by identifier.

This requires well defined
capability files in the `capabilities` directory.

Inline capabilities can be mixed with pre-defined capabilities.

By default, all commands that you registered in your app
(using the
[`tauri::Builder::invoke_handler`](https://docs.rs/tauri/2.0.0/tauri/struct.Builder.html#method.invoke_handler)
function)
are allowed to be used by all the windows and webviews of the app.
To change that, consider using
[`AppManifest::commands`](https://docs.rs/tauri-build/2.0.0/tauri_build/struct.AppManifest.html#method.commands).

Capabilities can be platform-specific by defining the `platforms` array.
By default the capability is applied to all targets,
but you can select a subset of the `linux`, `macOS`, `windows`, `iOS` and `android` targets.

For example a capability for desktop operating systems.
Note it enables permissions on plugins that are only available on desktop:

And another example of a capability for mobile.
Note it enables permissions on plugins that are only available on mobile:

By default the API is only accessible to bundled code shipped with the Tauri App.
To allow remote sources access to certain Tauri Commands it is possible to define this in
the capability configuration file.

This example would allow to scan for NFC tags and to use the barcode scanner from
all subdomains of `tauri.app`.

On Linux and Android, Tauri is unable to distinguish between requests from an embedded `<iframe>` and the window itself.

Please consider usage of this feature very carefully and read more into the specific
security implications for your targeted operating system in the reference section of this feature.

## Security Boundaries

_What does it protect against?_

Depending on the permissions and capabilities it is able to:

- Minimize impact of frontend compromise
- Prevent or reduce (accidential) exposure of local system interfaces and data
- Prevent or reduce possible privilege escalation from frontend to backend/system

_What does it **not** protect against?_

- Malicious or insecure Rust code
- Too lax scopes and configuration
- Incorrect scope checks in the command implementation
- Intentional bypasses from Rust code
- Basically anything which was written in the rust core of an application
- 0-days or unpatched 1-days in the system WebView
- Supply chain attacks or otherwise compromised developer systems

The security boundaries are depending on window labels (**not titles**).
We recommend to only expose of the window creation functionality
to higher privileged windows.

Tauri generates JSON schemas with all the permissions available to
your application through `tauri-build`, allowing autocompletion in your IDE.
To use a schema, set the `$schema` property in your configuration file
(either .json or .toml) to one of the platform-specific schemas
located in the `gen/schemas` directory. Usually
you will set it to `../gen/schemas/desktop-schema.json` or
`../gen/schemas/mobile-schema.json` though you can also define a capability
for a specific target platform.

## Configuration Files

Simplified example of an example Tauri application directory structure:

Everything can be inlined into the `tauri.conf.json` but even a
little more advanced configuration would bloat this file and
the goal of this approach is that the permissions are abstracted
away whenever possible and simple to understand.

A list of all core permissions can be found on the [Core Permissions](/reference/acl/core-permissions/) page.

**Examples:**

Example 1 (unknown):
```unknown
These snippets are part of the
[Tauri configuration](/develop/configuration-files/#tauri-config) file.

This is likely the most common configuration method,
where the individual capabilities are inlined and only
permissions are referenced by identifier.

This requires well defined
capability files in the `capabilities` directory.
```

Example 2 (unknown):
```unknown
Inline capabilities can be mixed with pre-defined capabilities.
```

Example 3 (unknown):
```unknown
By default, all commands that you registered in your app
(using the
[`tauri::Builder::invoke_handler`](https://docs.rs/tauri/2.0.0/tauri/struct.Builder.html#method.invoke_handler)
function)
are allowed to be used by all the windows and webviews of the app.
To change that, consider using
[`AppManifest::commands`](https://docs.rs/tauri-build/2.0.0/tauri_build/struct.AppManifest.html#method.commands).
```

Example 4 (unknown):
```unknown
## Target Platform

Capabilities can be platform-specific by defining the `platforms` array.
By default the capability is applied to all targets,
but you can select a subset of the `linux`, `macOS`, `windows`, `iOS` and `android` targets.

For example a capability for desktop operating systems.
Note it enables permissions on plugins that are only available on desktop:
```

---

## Writing Plugin Permissions

**URL:** llms-txt#writing-plugin-permissions

import { Steps } from '@astrojs/starlight/components';
import ShowSolution from '@components/ShowSolution.astro'
import Cta from '@fragments/cta.mdx';

The goal of this exercise is to get a better understanding on how
plugin permissions can be created when writing your own plugin.

At the end you will have the ability to create simple permissions for
your plugins.
You will have an example Tauri plugin where permissions are partially autogenerated
and hand crafted.

1. ### Create a Tauri Plugin

In our example we will facilitate the Tauri [`cli`](/reference/cli/)
    to bootstrap a Tauri plugin source code structure.
    Make sure you have installed all [Prerequisites](/start/prerequisites/)
    and verify you have the Tauri CLI in the correct version
    by running `cargo tauri info`.

The output should indicate the `tauri-cli` version is `2.x`.
    We will proceed in this step-by-step explanation with `pnpm` but you can choose another
    package manager and replace it in the commands accordingly.

Once you have a recent version installed you can go
    ahead and create the plugin using the Tauri CLI.

<ShowSolution>
    
    </ShowSolution>

2. ### Create a New Command

To showcase something practical and simple let us assume
    our command writes user input to a file in our temporary folder while
    adding some custom header to the file.

Let's name our command `write_custom_file`, implement it in `src/commands.rs`
    and add it to our plugin builder to be exposed to the frontend.

Tauri's core utils will autogenerate `allow` and `deny` permissions for this
    command, so we do not need to care about this.

The command implementation:

Auto-Generate inbuilt permissions for your new command:

These inbuilt permissions will be automatically generated by the Tauri build
    system and will be visible in the `permissions/autogenerated/commands` folder.
    By default an `enable-<command>` and `deny-<command>` permission will
    be created.

</ShowSolution>
3. ### Expose the New Command

The previous step was to write the actual command implementation.
    Next we want to expose it to the frontend so it can be consumed.

<ShowSolution>
 
    Configure the Tauri builder to generate the invoke handler to pass frontend
    IPC requests to the newly implemented command:

Expose the new command in the frontend module.

This step is essential for the example application to successfully
    import the frontend module. This is for convenience and has
    no security impact, as the command handler is already generated
    and the command can be manually invoked from the frontend.

:::tip
    The invoke parameter needs to be CamelCase. In this example it is `userInput` instead of `user_input`. 
    :::

Make sure your package is built:

4. ### Define Default Plugin Permissions

As our plugin should expose the `write_custom_file` command by default
    we should add this to our `default.toml` permission.

<ShowSolution>
    Add this to our default permission set to allow the new command
    we just exposed.

5. ### Invoke Test Command from Example Application
    
    The created plugin directory structure contains an `examples/tauri-app` folder,
    which has a ready to use Tauri application to test out the plugin.

Since we added a new command we need to slightly modify the frontend to
    invoke our new command instead.

Running this and pressing the "Write" button you should be greeted with this:

And you should find a `test.txt` file in your temporary folder containing a message
    from our new implemented plugin command. 
    🥳

**Examples:**

Example 1 (sh):
```sh
mkdir -p tauri-learning
    cd tauri-learning
    cargo tauri plugin new test
    cd tauri-plugin-test
    pnpm install
    pnpm build
    cargo build
```

Example 2 (unknown):
```unknown
Auto-Generate inbuilt permissions for your new command:
```

Example 3 (unknown):
```unknown
These inbuilt permissions will be automatically generated by the Tauri build
    system and will be visible in the `permissions/autogenerated/commands` folder.
    By default an `enable-<command>` and `deny-<command>` permission will
    be created.

    </ShowSolution>
3. ### Expose the New Command

    The previous step was to write the actual command implementation.
    Next we want to expose it to the frontend so it can be consumed.

    <ShowSolution>
 
    Configure the Tauri builder to generate the invoke handler to pass frontend
    IPC requests to the newly implemented command:
```

Example 4 (unknown):
```unknown
Expose the new command in the frontend module.

    This step is essential for the example application to successfully
    import the frontend module. This is for convenience and has
    no security impact, as the command handler is already generated
    and the command can be manually invoked from the frontend.
```

---

## Capabilities for Different Windows and Platforms

**URL:** llms-txt#capabilities-for-different-windows-and-platforms

**Contents:**
- Content of this guide
- Prerequisites
- Guide
- Conclusion and Resources

import { Steps } from '@astrojs/starlight/components';
import ShowSolution from '@components/ShowSolution.astro'
import Cta from '@fragments/cta.mdx';

This guide will help you customize the capabilities of your Tauri app.

## Content of this guide

- Create multiple windows in a Tauri app
- Use different capabilities for different windows
- Use platform-specific capabilities

This exercise is meant to be read after completing [`Using Plugin Permissions`](/learn/security/using-plugin-permissions/).

<Steps>
1. ### Create Multiple Windows in a Tauri Application

Here we create an app with two windows labelled `first` and `second`.
   There are multiple ways to create windows in your Tauri application.

#### Create Windows with the Tauri Configuration File

In the Tauri configuration file, usually named `tauri.conf.json`:

<ShowSolution>
    
    </ShowSolution>

#### Create Windows Programmatically

In the Rust code to create a Tauri app:

<ShowSolution>
    
    </ShowSolution>

2. ### Apply Different Capabilities to Different Windows

The windows of a Tauri app can use different features or plugins of the Tauri backend.
    For better security it is recommended to only give the necessary capabilities to each window.
    We simulate a scenario where the `first` windows uses filesystem and dialog functionalities and `second`
    only needs dialog functionalities.

#### Separate capability files per category

It is recommended to separate the capability files per category of actions they enable.

<ShowSolution>
    JSON files in the `src-tauri/capabilities` will be taken into account for the capability system.
    Here we separate capabilities related to the filesystem and dialog window into `filesystem.json`
    and `dialog.json`.

*filetree of the Tauri project:*
    
    </ShowSolution>

#### Give filesystem capabilities to the `first` window

We give the `first` window the capability to have read access to the content of the `$HOME` directory.

<ShowSolution>
    Use the `windows` field in a capability file with one or multiple window labels.

#### Give dialog capabilities to the `first` and `second` window

We give to `first` and `second` windows the capability to create a "Yes/No" dialog

<ShowSolution>
    Use the `windows` field in a capability file with one or multiple window labels.

3. ### Make Capabilities Platform Dependent

We now want to customize the capabilities to be active only on certain platforms.
    We make our filesystem capabilities only active on `linux` and `windows`.

<ShowSolution>
    Use the `platforms` field in a capability file to make it platform-specific.

The currently available platforms are `linux`, `windows`, `macos`, `android`, and `ios`.
    </ShowSolution>
    
</Steps>

## Conclusion and Resources

We have learned how to create multiple windows in a Tauri app and give them specific capabilities. Furthermore these capabilities can also be targeted to certain platforms.

An example application that used window capabilities can be found in the [`api` example](https://github.com/tauri-apps/tauri/tree/dev/examples/api) of the [Tauri Github repository](https://github.com/tauri-apps/tauri).
The fields that can be used in a capability file are listed in the [Capability](/reference/acl/capability/) reference.

**Examples:**

Example 1 (javascript):
```javascript
"productName": "multiwindow",
      ...
      "app": {
        "windows": [
          {
            "label": "first",
            "title": "First",
            "width": 800,
            "height": 600
          },
          {
            "label": "second",
            "title": "Second",
            "width": 800,
            "height": 600
          }
        ],
      },
      ...
    }
```

Example 2 (rust):
```rust
tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![greet])
        .setup(|app| {
            let webview_url = tauri::WebviewUrl::App("index.html".into());
            // First window
            tauri::WebviewWindowBuilder::new(app, "first", webview_url.clone())
                .title("First")
                .build()?;
            // Second window
            tauri::WebviewWindowBuilder::new(app, "second", webview_url)
                .title("Second")
                .build()?;
            Ok(())
        })
        .run(context)
        .expect("error while running tauri application");
```

Example 3 (unknown):
```unknown
/src
    /src-tauri
      /capabilities
        filesystem.json
        dialog.json
      tauri.conf.json
    package.json
    README.md
```

Example 4 (unknown):
```unknown
</ShowSolution>

    #### Give dialog capabilities to the `first` and `second` window

    We give to `first` and `second` windows the capability to create a "Yes/No" dialog

    <ShowSolution>
    Use the `windows` field in a capability file with one or multiple window labels.
```

---

## Content Security Policy (CSP)

**URL:** llms-txt#content-security-policy-(csp)

Tauri restricts the [Content Security Policy] (CSP) of your HTML pages.
This can be used to reduce or prevent impact of common web based vulnerabilities
like cross-site-scripting (XSS).

Local scripts are hashed, styles and external scripts are referenced using a cryptographic nonce,
which prevents unallowed content from being loaded.

:::caution
Avoid loading remote content such as scripts served over a CDN as they introduce an attack vector.
In general any untrusted file can introduce new and subtle attack vectors.
:::

The CSP protection is only enabled if set on the Tauri configuration file.
You should make it as restricted as possible, only allowing the webview to load assets
from hosts you trust, and preferably own.
At compile time, Tauri appends its nonces and hashes to the relevant CSP attributes automatically
to bundled code and assets, so you only need to worry about what is unique to your application.

This is an example CSP configuration taken from the [`api`](https://github.com/tauri-apps/tauri/blob/dev/examples/api/src-tauri/tauri.conf.json#L22)
example of Tauri, but every application developer needs to tailor this to their own application needs.

:::tip
When using Rust to develop your frontend, or if your frontend otherwise uses WebAssembly, remember
to include `'wasm-unsafe-eval'` as a `script-src`.
:::

See [`script-src`], [`style-src`] and [CSP Sources] for more
information about this protection.

[content security policy]: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
[`script-src`]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/script-src
[`style-src`]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/style-src
[csp sources]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/Sources#sources

---
