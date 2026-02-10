# Tauri - Core Concepts

**Pages:** 7

---

## Debug in VS Code

**URL:** llms-txt#debug-in-vs-code

**Contents:**
- All platforms with vscode-lldb extension
  - Prerequisites
  - Configure launch.json
- With Visual Studio Windows Debugger on Windows
  - Prerequisites
  - Configure launch.json and tasks.json

This guide will walk you through setting up VS Code for debugging the [Core Process of your Tauri app](/concept/process-model/#the-core-process).

## All platforms with vscode-lldb extension

Install the [`vscode-lldb`] extension.

[`vscode-lldb`]: https://marketplace.visualstudio.com/items?itemName=vadimcn.vscode-lldb

### Configure launch.json

Create a `.vscode/launch.json` file and paste the below JSON contents into it:

This uses `cargo` directly to build the Rust application and load it in both development and production modes.

Note that it does not use the Tauri CLI, so exclusive CLI features are not executed. The `beforeDevCommand` and `beforeBuildCommand` scripts must be executed beforehand or configured as a task in the `preLaunchTask` field. Below is an example `.vscode/tasks.json` file that has two tasks, one for a `beforeDevCommand` that spawns a development server and one for `beforeBuildCommand`:

Now you can set breakpoints in `src-tauri/src/main.rs` or any other Rust file and start debugging by pressing `F5`.

## With Visual Studio Windows Debugger on Windows

Visual Studio Windows Debugger is a Windows-only debugger that is generally faster than [`vscode-lldb`] with better support for some Rust features such as enums.

Install the [C/C++](https://marketplace.visualstudio.com/items?itemName=ms-vscode.cpptools) extension and follow https://code.visualstudio.com/docs/cpp/config-msvc#_prerequisites to install Visual Studio Windows Debugger.

### Configure launch.json and tasks.json

Note that it does not use the Tauri CLI, so exclusive CLI features are not executed. The `tasks.json` is the same as with `lldb`, except you need to add a config group and target your `preLaunchTask` from `launch.json` to it if you want it to always compile before launching.

Here is an example of running a dev server (equivalent of `beforeDevCommand`) and the compilation (`cargo build`) as a group, to use it, change the `preLaunchTask` config in `launch.json` to `dev` (or anything you named your group).

**Examples:**

Example 1 (unknown):
```unknown
This uses `cargo` directly to build the Rust application and load it in both development and production modes.

Note that it does not use the Tauri CLI, so exclusive CLI features are not executed. The `beforeDevCommand` and `beforeBuildCommand` scripts must be executed beforehand or configured as a task in the `preLaunchTask` field. Below is an example `.vscode/tasks.json` file that has two tasks, one for a `beforeDevCommand` that spawns a development server and one for `beforeBuildCommand`:
```

Example 2 (unknown):
```unknown
Now you can set breakpoints in `src-tauri/src/main.rs` or any other Rust file and start debugging by pressing `F5`.

## With Visual Studio Windows Debugger on Windows

Visual Studio Windows Debugger is a Windows-only debugger that is generally faster than [`vscode-lldb`] with better support for some Rust features such as enums.

### Prerequisites

Install the [C/C++](https://marketplace.visualstudio.com/items?itemName=ms-vscode.cpptools) extension and follow https://code.visualstudio.com/docs/cpp/config-msvc#_prerequisites to install Visual Studio Windows Debugger.

### Configure launch.json and tasks.json
```

Example 3 (unknown):
```unknown
Note that it does not use the Tauri CLI, so exclusive CLI features are not executed. The `tasks.json` is the same as with `lldb`, except you need to add a config group and target your `preLaunchTask` from `launch.json` to it if you want it to always compile before launching.

Here is an example of running a dev server (equivalent of `beforeDevCommand`) and the compilation (`cargo build`) as a group, to use it, change the `preLaunchTask` config in `launch.json` to `dev` (or anything you named your group).
```

---

## Inter-Process Communication

**URL:** llms-txt#inter-process-communication

**Contents:**
- Events
- Commands

import { CardGrid, LinkCard } from '@astrojs/starlight/components';

Inter-Process Communication (IPC) allows isolated processes to communicate securely and is key to building more complex applications.

Learn more about the specific IPC patterns in the following guides:

<CardGrid>
  <LinkCard
    title="Brownfield"
    href="/concept/inter-process-communication/brownfield/"
  />
  <LinkCard
    title="Isolation"
    href="/concept/inter-process-communication/isolation/"
  />
</CardGrid>

Tauri uses a particular style of Inter-Process Communication called [Asynchronous Message Passing], where processes exchange _requests_ and _responses_ serialized using some simple data representation. Message Passing should sound familiar to anyone with web development experience, as this paradigm is used for client-server communication on the internet.

Message passing is a safer technique than shared memory or direct function access because the recipient is free to reject or discard requests as it sees fit. For example, if the Tauri Core process determines a request to be malicious, it simply discards the requests and never executes the corresponding function.

In the following, we explain Tauri's two IPC primitives - `Events` and `Commands` - in more detail.

Events are fire-and-forget, one-way IPC messages that are best suited to communicate lifecycle events and state changes. Unlike [Commands](#commands), Events can be emitted by both the Frontend _and_ the Tauri Core.

<figcaption>Events sent between the Core and the Webview.</figcaption>
</figure>

Tauri also provides a [foreign function interface]-like abstraction on top of IPC messages[^1]. The primary API, `invoke`, is similar to the browser's `fetch` API and allows the Frontend to invoke Rust functions, pass arguments, and receive data.

Because this mechanism uses a [JSON-RPC] like protocol under the hood to serialize requests and responses, all arguments and return data must be serializable to JSON.

<figcaption>IPC messages involved in a command invocation.</figcaption>
</figure>

[^1]: Because Commands still use message passing under the hood, they do not share the same security pitfalls as real FFI interfaces do.

[asynchronous message passing]: https://en.wikipedia.org/wiki/Message_passing#Asynchronous_message_passing
[json-rpc]: https://www.jsonrpc.org
[foreign function interface]: https://en.wikipedia.org/wiki/Foreign_function_interface

**Examples:**

Example 1 (unknown):
```unknown
<figcaption>Events sent between the Core and the Webview.</figcaption>
</figure>

## Commands

Tauri also provides a [foreign function interface]-like abstraction on top of IPC messages[^1]. The primary API, `invoke`, is similar to the browser's `fetch` API and allows the Frontend to invoke Rust functions, pass arguments, and receive data.

Because this mechanism uses a [JSON-RPC] like protocol under the hood to serialize requests and responses, all arguments and return data must be serializable to JSON.

<figure>
```

---

## Process Model

**URL:** llms-txt#process-model

**Contents:**
- Why Multiple Processes?
- The Core Process
- The WebView Process

Tauri employs a multi-process architecture similar to Electron or many modern web browsers. This guide explores the reasons behind the design choice and why it is key to writing secure applications.

## Why Multiple Processes?

In the early days of GUI applications, it was common to use a single process to perform computation, draw the interface and react to user input. As you can probably guess, this meant that a long-running, expensive computation would leave the user interface unresponsive, or worse, a failure in one app component would bring the whole app crashing down.

It became clear that a more resilient architecture was needed, and applications began running different components in different processes. This makes much better use of modern multi-core CPUs and creates far safer applications. A crash in one component doesn't affect the whole system anymore, as components are isolated on different processes. If a process gets into an invalid state, we can easily restart it.

We can also limit the blast radius of potential exploits by handing out only the minimum amount of permissions to each process, just enough so they can get their job done. This pattern is known as the [Principle of Least Privilege], and you see it in the real world all the time. If you have a gardener coming over to trim your hedge, you give them the key to your garden. You would **not** give them the keys to your house; why would they need access to that? The same concept applies to computer programs. The less access we give them, the less harm they can do if they get compromised.

Each Tauri application has a core process, which acts as the application's entry point and which is the only component with full access to the operating system.

The Core's primary responsibility is to use that access to create and orchestrate application windows, system-tray menus, or notifications. Tauri implements the necessary cross-platform abstractions to make this easy. It also routes all [Inter-Process Communication] through the Core process, allowing you to intercept, filter, and manipulate IPC messages in one central place.

The Core process should also be responsible for managing global state, such as settings or database connections. This allows you to easily synchronize state between windows and protect your business-sensitive data from prying eyes in the Frontend.

We chose Rust to implement Tauri because of its concept of [Ownership]
guarantees memory safety while retaining excellent performance.

<figcaption>Simplified representation of the Tauri process model. A single Core process manages one or more WebView processes.</figcaption>
</figure>

## The WebView Process

The Core process doesn't render the actual user interface (UI) itself; it spins up WebView processes that leverage WebView libraries provided by the operating system. A WebView is a browser-like environment that executes your HTML, CSS, and JavaScript.

This means that most of your techniques and tools used in traditional web development can be used to create Tauri applications. For example, many Tauri examples are written using the [Svelte] frontend framework and the [Vite] bundler.

Security best practices apply as well; for example, you must always sanitize user input, never handle secrets in the Frontend, and ideally defer as much business logic as possible to the Core process to keep your attack surface small.

Unlike other similar solutions, the WebView libraries are **not** included in your final executable but dynamically linked at runtime[^1]. This makes your application _significantly_ smaller, but it also means that you need to keep platform differences in mind, just like traditional web development.

[^1]:
    Currently, Tauri uses [Microsoft Edge WebView2] on Windows, [WKWebView] on
    macOS and [webkitgtk] on Linux.

[principle of least privilege]: https://en.wikipedia.org/wiki/Principle_of_least_privilege
[inter-process communication]: /concept/inter-process-communication/
[ownership]: https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html
[microsoft edge webview2]: https://docs.microsoft.com/en-us/microsoft-edge/webview2/
[wkwebview]: https://developer.apple.com/documentation/webkit/wkwebview
[webkitgtk]: https://webkitgtk.org
[svelte]: https://svelte.dev/
[vite]: https://vitejs.dev/

---

## Tauri Architecture

**URL:** llms-txt#tauri-architecture

**Contents:**
- Introduction
  - What Tauri is Not
- Core Ecosystem
  - tauri
  - tauri-runtime
  - tauri-macros
  - tauri-utils
  - tauri-build
  - tauri-codegen
  - tauri-runtime-wry

Tauri is a polyglot and generic toolkit that is very composable and allows engineers to make a wide variety of applications. It is used for building applications for desktop computers using a combination of Rust tools and HTML rendered in a Webview. Apps built with Tauri can ship with any number of pieces of an optional JS API and Rust API so that webviews can control the system via message passing. Developers can extend the default API with their own functionality and bridge the Webview and Rust-based backend easily.

Tauri apps can have [tray-type interfaces](/learn/system-tray/). They can be [updated](/plugin/updater/) and are managed by the user's operating system as expected. They are very small because they use the OS's webview. They do not ship a runtime since the final binary is compiled from Rust. This makes the [reversing of Tauri apps not a trivial task](/security/).

### What Tauri is Not

Tauri is not a lightweight kernel wrapper. Instead, it directly uses [WRY](#wry) and [TAO](#tao) to do the heavy lifting in making system calls to the OS.

Tauri is not a VM or virtualized environment. Instead, it is an application toolkit that allows making Webview OS applications.

<figcaption>Simplified representation of the Tauri architecture.</figcaption>
</figure>

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri)

This is the major crate that holds everything together. It brings the runtimes, macros, utilities and API into one final product. It reads the [`tauri.conf.json`](/reference/config/) file at compile time to bring in features and undertake the actual configuration of the app (and even the `Cargo.toml` file in the project's folder). It handles script injection (for polyfills / prototype revision) at runtime, hosts the API for systems interaction, and even manages the updating process.

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-runtime)

The glue layer between Tauri itself and lower-level webview libraries.

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-macros)

Creates macros for the context, handler, and commands by leveraging the [`tauri-codegen`](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-codegen) crate.

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-utils)

Common code that is reused in many places and offers useful utilities like parsing configuration files, detecting platform triples, injecting the CSP, and managing assets.

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-build)

Applies the macros at build-time to rig some special features needed by `cargo`.

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-codegen)

Embeds, hashes, and compresses assets, including icons for the app as well as the system tray. Parses [`tauri.conf.json`](/reference/config/) at compile time and generates the Config struct.

### tauri-runtime-wry

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-runtime-wry)

This crate opens up direct systems-level interactions specifically for WRY, such as printing, monitor detection, and other windowing-related tasks.

### API (JavaScript / TypeScript)

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/packages/api)

A typescript library that creates `cjs` and `esm` JavaScript endpoints for you to import into your frontend framework so that the Webview can call and listen to backend activity. Also ships in pure typescript, because for some frameworks this is more optimal. It uses the message passing of webviews to their hosts.

### Bundler (Rust / Shell)

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-bundler)

A library that builds a Tauri app for the platform it detects or is told. Currently supports macOS, Windows and Linux - but in the near future will support mobile platforms as well. May be used outside of Tauri projects.

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-cli)

This Rust executable provides the full interface to all of the required activities for which the CLI is required. It runs on macOS, Windows, and Linux.

### cli.js (JavaScript)

[View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/packages/cli)

Wrapper around [`cli.rs`](https://github.com/tauri-apps/tauri/blob/dev/crates/tauri-cli) using [`napi-rs`](https://github.com/napi-rs/napi-rs) to produce npm packages for each platform.

### create-tauri-app (JavaScript)

[View on GitHub](https://github.com/tauri-apps/create-tauri-app)

A toolkit that will enable engineering teams to rapidly scaffold out a new `tauri-apps` project using the frontend framework of their choice (as long as it has been configured).

The Tauri-Apps organization maintains two "upstream" crates from Tauri, namely TAO for creating and managing application windows, and WRY for interfacing with the Webview that lives within the window.

[View on GitHub](https://github.com/tauri-apps/tao)

Cross-platform application window creation library in Rust that supports all major platforms like Windows, macOS, Linux, iOS and Android. Written in Rust, it is a fork of [winit](https://github.com/rust-windowing/winit) that we have extended for our own needs - like menu bar and system tray.

[View on GitHub](https://github.com/tauri-apps/wry)

WRY is a cross-platform WebView rendering library in Rust that supports all major desktop platforms like Windows, macOS, and Linux.
Tauri uses WRY as the abstract layer responsible to determine which webview is used (and how interactions are made).

## Additional Tooling

[View on GitHub](https://github.com/tauri-apps/tauri-action)

GitHub workflow that builds Tauri binaries for all platforms. Even allows creating a (very basic) Tauri app even if Tauri is not set up.

[View on GitHub](https://github.com/tauri-apps/tauri-vscode)

This project enhances the Visual Studio Code interface with several nice-to-have features.

### vue-cli-plugin-tauri

[View on GitHub](https://github.com/tauri-apps/vue-cli-plugin-tauri)

Allows you to very quickly install Tauri in a vue-cli project.

[Tauri Plugin Guide](/develop/plugins/)

Generally speaking, plugins are authored by third parties (even though there may be official, supported plugins). A plugin generally does 3 things:

1. Enables Rust code to do "something".
2. Provides interface glue to make it easy to integrate into an app.
3. Provides a JavaScript API for interfacing with the Rust code.

Here are some examples of Tauri Plugins:

- [tauri-plugin-fs](https://github.com/tauri-apps/tauri-plugin-fs)
- [tauri-plugin-sql](https://github.com/tauri-apps/tauri-plugin-sql)
- [tauri-plugin-stronghold](https://github.com/tauri-apps/tauri-plugin-stronghold)

Tauri itself is licensed under MIT or Apache-2.0. If you repackage it and modify any source code, it is your responsibility to verify that you are complying with all upstream licenses. Tauri is provided AS-IS with no explicit claim for suitability for any purpose.

Here you may peruse our [Software Bill of Materials](https://app.fossa.com/projects/git%2Bgithub.com%2Ftauri-apps%2Ftauri).

---

## Concept

**URL:** llms-txt#concept

---

## Debug in JetBrains IDEs

**URL:** llms-txt#debug-in-jetbrains-ides

**Contents:**
- Setting up a Cargo project
- Setting up Run Configurations
  - Tauri App
  - Development Server
- Launching a Debugging Session

{/* TODO: Add support to light/dark mode images */}

In this guide, we'll be setting up JetBrains RustRover for debugging the [Core Process of your Tauri app](/concept/process-model/#the-core-process). It also mostly applies to IntelliJ and CLion.

## Setting up a Cargo project

Depending on which frontend stack is used in a project, the project directory may or may not be a Cargo project. By default, Tauri places the Rust project in a subdirectory called `src-tauri`. It creates a Cargo project in the root directory only if Rust is used for frontend development as well.

If there's no `Cargo.toml` file at the top level, you need to attach the project manually. Open the Cargo tool window (in the main menu, go to **View | Tool Windows | Cargo**), click **+** (**Attach Cargo Project**) on the toolbar, and select the `src-tauri/Cargo.toml` file.

Alternatively, you could create a top-level Cargo workspace manually by adding the following file to the project's root directory:

Before you proceed, make sure that your project is fully loaded. If the Cargo tool window shows all the modules and targets of the workspace, you're good to go.

## Setting up Run Configurations

You will need to set up two separate Run/Debug configurations:

- one for launching the Tauri app in debugging mode,
- another one for running your frontend development server of choice.

1. In the main menu, go to **Run | Edit Configurations**.
2. In the **Run/Debug Configurations** dialog:

- To create a new configuration, click **+** on the toolbar and select **Cargo**.

![Add Run/Debug Configuration](@assets/develop/Debug/rustrover/add-cargo-config-light.png)
{/* ![Add Run/Debug Configuration](@assets/develop/Debug/rustrover/add-cargo-config-dark.png#gh-dark-mode-only) */}

With that created, we need to configure RustRover, so it instructs Cargo to build our app without any default features. This will tell Tauri to use your development server instead of reading assets from the disk. Normally this flag is passed by the Tauri CLI, but since we're completely sidestepping that here, we need to pass the flag manually.

![Add `--no-default-features` flag](@assets/develop/Debug/rustrover/set-no-default-features-light.png)
{/* ![Add `--no-default-features` flag](@assets/develop/Debug/rustrover/set-no-default-features-dark.png#gh-dark-mode-only) */}

Now we can optionally rename the Run/Debug Configuration to something more memorable, in this example we called it "Run Tauri App", but you can name it whatever you want.

![Rename Configuration](@assets/develop/Debug/rustrover/rename-configuration-light.png)
{/* ![Rename Configuration](@assets/develop/Debug/rustrover/rename-configuration-dark.png#gh-dark-mode-only) */}

### Development Server

The above configuration will use Cargo directly to build the Rust application and attach the debugger to it. This means we completely sidestep the Tauri CLI, so features like the `beforeDevCommand` and `beforeBuildCommand` will **not** be executed. We need to take care of that by running the development server manually.

To create the corresponding Run configuration, you need to check the actual development server in use. Look for the `src-tauri/tauri.conf.json` file and find the following line:

For `npm`, `pnpm`, or `yarn`, you could use the **npm** Run Configuration, for example:

![NPM Configuration](@assets/develop/Debug/rustrover/npm-configuration-light.png)
{/* ![NPM Configuration](@assets/develop/Debug/rustrover/npm-configuration-dark.png#gh-dark-mode-only) */}

Make sure you have the correct values in the **Command**, **Scripts**, and **Package Manager** fields.

If your development server is `trunk` for Rust-based WebAssembly frontend frameworks, you could use the generic **Shell Script** Run Configuration:

![Trunk Serve Configuration](@assets/develop/Debug/rustrover/trunk-configuration-light.png)
{/* ![Trunk Serve Configuration](@assets/develop/Debug/rustrover/trunk-configuration-dark.png#gh-dark-mode-only) */}

## Launching a Debugging Session

To launch a debugging session, you first need to run your development server, and then start debugging the Tauri App by clicking the **Debug** button next to the Run Configurations Switcher. RustRover will automatically recognize breakpoints placed in any Rust file in your project and stop on the first one hit.

![Debug Session](@assets/develop/Debug/rustrover/debug-session-light.png)
{/* ![Debug Session](@assets/develop/Debug/rustrover/debug-session-dark.png#gh-dark-mode-only) */}

From this point, you can explore the values of your variables, step further into the code, and check what's going at runtime in detail.

[core process of your tauri app]: ../../../../concept/process-model#the-core-process

**Examples:**

Example 1 (unknown):
```unknown
Before you proceed, make sure that your project is fully loaded. If the Cargo tool window shows all the modules and targets of the workspace, you're good to go.

## Setting up Run Configurations

You will need to set up two separate Run/Debug configurations:

- one for launching the Tauri app in debugging mode,
- another one for running your frontend development server of choice.

### Tauri App

1. In the main menu, go to **Run | Edit Configurations**.
2. In the **Run/Debug Configurations** dialog:

- To create a new configuration, click **+** on the toolbar and select **Cargo**.

![Add Run/Debug Configuration](@assets/develop/Debug/rustrover/add-cargo-config-light.png)
{/* ![Add Run/Debug Configuration](@assets/develop/Debug/rustrover/add-cargo-config-dark.png#gh-dark-mode-only) */}

With that created, we need to configure RustRover, so it instructs Cargo to build our app without any default features. This will tell Tauri to use your development server instead of reading assets from the disk. Normally this flag is passed by the Tauri CLI, but since we're completely sidestepping that here, we need to pass the flag manually.

![Add `--no-default-features` flag](@assets/develop/Debug/rustrover/set-no-default-features-light.png)
{/* ![Add `--no-default-features` flag](@assets/develop/Debug/rustrover/set-no-default-features-dark.png#gh-dark-mode-only) */}

Now we can optionally rename the Run/Debug Configuration to something more memorable, in this example we called it "Run Tauri App", but you can name it whatever you want.

![Rename Configuration](@assets/develop/Debug/rustrover/rename-configuration-light.png)
{/* ![Rename Configuration](@assets/develop/Debug/rustrover/rename-configuration-dark.png#gh-dark-mode-only) */}

### Development Server

The above configuration will use Cargo directly to build the Rust application and attach the debugger to it. This means we completely sidestep the Tauri CLI, so features like the `beforeDevCommand` and `beforeBuildCommand` will **not** be executed. We need to take care of that by running the development server manually.

To create the corresponding Run configuration, you need to check the actual development server in use. Look for the `src-tauri/tauri.conf.json` file and find the following line:
```

---

## Core Concepts

**URL:** llms-txt#core-concepts

import { CardGrid, LinkCard } from '@astrojs/starlight/components';

Tauri has a variety of topics that are considered to be core concepts, things any developer should be aware of when developing their applications. Here's a variety of topics that you should get more intimately familiar with if you want to get the most out of the framework.

<CardGrid>
  <LinkCard
    title="Tauri Architecture"
    href="/concept/architecture/"
    description="Architecture and ecosystem."
  />
  <LinkCard
    title="Inter-Process Communication (IPC)"
    href="/concept/inter-process-communication/"
    description="The inner workings on the IPC."
  />
  <LinkCard
    title="Security"
    href="/security/"
    description="How Tauri enforces security practices."
  />
  <LinkCard
    title="Process Model"
    href="/concept/process-model/"
    description="Which processes Tauri manages and why."
  />
  <LinkCard
    title="App Size"
    href="/concept/size/"
    description="How to make your app as small as possible."
  />
</CardGrid>

---
