# Tauri - Development

**Pages:** 13

---

## Debug in Neovim

**URL:** llms-txt#debug-in-neovim

**Contents:**
  - Prerequisites
  - Configuring nvim-dap
  - Starting the dev server
  - Example key bindings

There are many different plugins that can be used to debug Rust code in Neovim. This guide will show you how to set up `nvim-dap` and some additional plugins to debug Tauri application.

`nvim-dap` extension requires `codelldb` binary. Download the version for your system from https://github.com/vadimcn/codelldb/releases and unzip it. We will point to it later in the `nvim-dap` configuration.

### Configuring nvim-dap

Install [`nvim-dap`](https://github.com/mfussenegger/nvim-dap) and [`nvim-dap-ui`](https://github.com/rcarriga/nvim-dap-ui) plugins. Follow the instructions provided on their github pages or simply use your favourite plugin manager.
Note that `nvim-dap-ui` requires `nvim-nio` plugin.

Next, setup the plugin in your Neovim configuration:

This setup will ask you to point to the Tauri App binary you want to debug each time you lanuch the debugger.

Optionally, you can setup `nvim-dap-ui` plugin to toggle debugger view automatically each time debugging session starts and stops:

Lastly, you can change the default way the breakpoints are displayed in the editor:

### Starting the dev server

Since we're not using Tauri CLI to launch the app the development server will not start automatically. To control the state of development server from Neovim you can use the [overseer](https://github.com/stevearc/overseer.nvim/tree/master) plugin.

Best way to control tasks running in background is to use [VS Code style task](https://github.com/stevearc/overseer.nvim/blob/master/doc/guides.md#vs-code-tasks) configuration. To do this create a `.vscode/tasks.json` file in the projects directory.

You can find example task configuration for project using `trunk` below.

### Example key bindings

Below you can find example key bindings to start and control debugging sessions.

**Examples:**

Example 1 (unknown):
```unknown
This setup will ask you to point to the Tauri App binary you want to debug each time you lanuch the debugger.

Optionally, you can setup `nvim-dap-ui` plugin to toggle debugger view automatically each time debugging session starts and stops:
```

Example 2 (unknown):
```unknown
Lastly, you can change the default way the breakpoints are displayed in the editor:
```

Example 3 (unknown):
```unknown
### Starting the dev server

Since we're not using Tauri CLI to launch the app the development server will not start automatically. To control the state of development server from Neovim you can use the [overseer](https://github.com/stevearc/overseer.nvim/tree/master) plugin.

Best way to control tasks running in background is to use [VS Code style task](https://github.com/stevearc/overseer.nvim/blob/master/doc/guides.md#vs-code-tasks) configuration. To do this create a `.vscode/tasks.json` file in the projects directory.

You can find example task configuration for project using `trunk` below.
```

Example 4 (unknown):
```unknown
### Example key bindings

Below you can find example key bindings to start and control debugging sessions.
```

---

## CrabNebula DevTools

**URL:** llms-txt#crabnebula-devtools

import { Image } from 'astro:assets';
import devToolsPrint from '@assets/develop/Debug/crabnebula-devtools.png';

[CrabNebula](https://crabnebula.dev/) provides a free [DevTools](https://crabnebula.dev/devtools/) application for Tauri as part of its partnership with the Tauri project. This application allows you to instrument your Tauri app by capturing its embedded assets, Tauri configuration file, logs and spans and providing a web frontend to seamlessly visualize data in real time.

With the CrabNebula DevTools you can inspect your app's log events (including logs from dependencies), track down the performance of your command calls and overall Tauri API usage, with a special interface for Tauri events and commands, including payload, responses and inner logs and execution spans.

To enable the CrabNebula DevTools, install the devtools crate:

And initialize the plugin as soon as possible in your main function:

And then run your app as usual, if everything is set up correctly devtools will print the following message:

<Image src={devToolsPrint} alt="DevTools message on terminal" />

:::note
In this case we only initialize the devtools plugin for debug applications, which is recommended.
:::

For more information, see the [CrabNebula DevTools](https://docs.crabnebula.dev/devtools/get-started/) documentation.

**Examples:**

Example 1 (unknown):
```unknown
And initialize the plugin as soon as possible in your main function:
```

---

## Tauri Full Documentation

**URL:** llms-txt#tauri-full-documentation

> Tauri is a framework for building tiny, fast binaries for all major desktop and mobile platforms. Developers can integrate any frontend framework that compiles to HTML, JavaScript, and CSS for building their user experience while leveraging languages such as Rust, Swift, and Kotlin for backend logic when needed.

---

## Debug

**URL:** llms-txt#debug

**Contents:**
- Development Only Code
  - In Rust
- Rust Console
- WebView Console
  - Opening Devtools Programmatically
  - Using the Inspector in Production
- Debugging the Core Process

import CommandTabs from '@components/CommandTabs.astro';

With all the moving pieces in Tauri, you may run into a problem that requires debugging. There are many locations where error details are printed, and Tauri includes some tools to make the debugging process more straightforward.

## Development Only Code

One of the most useful tools in your toolkit for debugging is the ability to add debugging statements in your code. However, you generally don't want these to end up in production, which is where the ability to check whether you're running in development mode or not comes in handy.

{/* TODO: js version */}

The first place to look for errors is in the Rust Console. This is in the terminal where you ran, e.g., `tauri dev`. You can use the following code to print something to that console from within a Rust file:

Sometimes you may have an error in your Rust code, and the Rust compiler can give you lots of information. If, for example, `tauri dev` crashes, you can rerun it like this on Linux and macOS:

or like this on Windows (PowerShell):

This command gives you a granular stack trace. Generally speaking, the Rust compiler helps you by
giving you detailed information about the issue, such as:

Right-click in the WebView, and choose `Inspect Element`. This opens up a web-inspector similar to the Chrome or Firefox dev tools you are used to.
You can also use the `Ctrl + Shift + i` shortcut on Linux and Windows, and `Command + Option + i` on macOS to open the inspector.

The inspector is platform-specific, rendering the webkit2gtk WebInspector on Linux, Safari's inspector on macOS and the Microsoft Edge DevTools on Windows.

### Opening Devtools Programmatically

You can control the inspector window visibility by using the [`WebviewWindow::open_devtools`] and [`WebviewWindow::close_devtools`] functions:

### Using the Inspector in Production

By default, the inspector is only enabled in development and debug builds unless you enable it with a Cargo feature.

#### Create a Debug Build

To create a debug build, run the `tauri build --debug` command.

<CommandTabs
  npm="npm run tauri build -- --debug"
  yarn="yarn tauri build --debug"
  pnpm="pnpm tauri build --debug"
  deno="deno task tauri build --debug"
  bun="bun tauri build --debug"
  cargo="cargo tauri build --debug"
/>

Like the normal build and dev processes, building takes some time the first time you run this command but is significantly faster on subsequent runs.
The final bundled app has the development console enabled and is placed in `src-tauri/target/debug/bundle`.

You can also run a built app from the terminal, giving you the Rust compiler notes (in case of errors) or your `println` messages. Browse to the file `src-tauri/target/(release|debug)/[app name]` and run it in directly in your console or double-click the executable itself in the filesystem (note: the console closes on errors with this method).

##### Enable Devtools Feature

The devtools API is private on macOS. Using private APIs on macOS prevents your application from being accepted to the App Store.

To enable the devtools in **production builds**, you must enable the `devtools` Cargo feature in the `src-tauri/Cargo.toml` file:

## Debugging the Core Process

The Core process is powered by Rust so you can use GDB or LLDB to debug it. You can follow the [Debugging in VS Code] guide to learn how to use the LLDB VS Code Extension to debug the Core Process of Tauri applications.

[debugging in vs code]: /develop/debug/vscode/
[`WebviewWindow::open_devtools`]: https://docs.rs/tauri/2.0.0/tauri/webview/struct.WebviewWindow.html#method.open_devtools
[`WebviewWindow::close_devtools`]: https://docs.rs/tauri/2.0.0/tauri/webview/struct.WebviewWindow.html#method.close_devtools

**Examples:**

Example 1 (unknown):
```unknown
{/* TODO: js version */}

## Rust Console

The first place to look for errors is in the Rust Console. This is in the terminal where you ran, e.g., `tauri dev`. You can use the following code to print something to that console from within a Rust file:
```

Example 2 (unknown):
```unknown
Sometimes you may have an error in your Rust code, and the Rust compiler can give you lots of information. If, for example, `tauri dev` crashes, you can rerun it like this on Linux and macOS:
```

Example 3 (unknown):
```unknown
or like this on Windows (PowerShell):
```

Example 4 (unknown):
```unknown
This command gives you a granular stack trace. Generally speaking, the Rust compiler helps you by
giving you detailed information about the issue, such as:
```

---

## Mobile Plugin Development

**URL:** llms-txt#mobile-plugin-development

**Contents:**
- Initialize Plugin Project
  - Develop an Android Plugin
  - Develop an iOS Plugin
- Plugin Configuration
- Lifecycle Events
  - load
  - onNewIntent
- Adding Mobile Commands
- Command Arguments
  - Android

:::tip[Plugin Development]

Be sure that you're familiar with the concepts covered in the [Plugin Development guide](/develop/plugins/) as many concepts in this guide build on top of foundations covered there.

Plugins can run native mobile code written in Kotlin (or Java) and Swift. The default plugin template includes an Android library project using Kotlin and a Swift package including an example mobile command showing how to trigger its execution from Rust code.

## Initialize Plugin Project

Follow the steps in the [Plugin Development guide](/develop/plugins/#initialize-plugin-project) to initialize a new plugin project.

If you have an existing plugin and would like to add Android or iOS capabilities to it, you can use `plugin android init` and `plugin ios init` to bootstrap the mobile library projects and guide you through the changes needed.

The default plugin template splits the plugin's implementation into two separate modules: `desktop.rs` and `mobile.rs`.

The desktop implementation uses Rust code to implement a functionality, while the mobile implementation sends a message to the native mobile code to execute a function and get a result back. If shared logic is needed across both implementations, it can be defined in `lib.rs`:

This implementation simplifies the process of sharing an API that can be used both by commands and Rust code.

### Develop an Android Plugin

A Tauri plugin for Android is defined as a Kotlin class that extends `app.tauri.plugin.Plugin` and is annotated with `app.tauri.annotation.TauriPlugin`. Each method annotated with `app.tauri.annotation.Command` can be called by Rust or JavaScript.

Tauri uses Kotlin by default for the Android plugin implementation, but you can switch to Java if you prefer. After generating a plugin, right click the Kotlin plugin class in Android Studio and select the "Convert Kotlin file to Java file" option from the menu. Android Studio will guide you through the project migration to Java.

### Develop an iOS Plugin

A Tauri plugin for iOS is defined as a Swift class that extends the `Plugin` class from the `Tauri` package. Each function with the `@objc` attribute and the `(_ invoke: Invoke)` parameter (for example `@objc private func download(_ invoke: Invoke) { }`) can be called by Rust or JavaScript.

The plugin is defined as a [Swift package](https://www.swift.org/package-manager/) so that you can use its package manager to manage dependencies.

## Plugin Configuration

Refer to the [Plugin Configuration section](/develop/plugins/#plugin-configuration) of the Plugin Development guide for more details on developing plugin configurations.

The plugin instance on mobile has a getter for the plugin configuration:

<Tabs syncKey="mobileOs">
<TabItem label="Android">

</TabItem>
<TabItem label="iOS">

Plugins can hook into several lifecycle events:

- [load](#load): When the plugin is loaded into the web view
- [onNewIntent](#onnewintent): Android only, when the activity is re-launched

There are also the additional [lifecycle events for plugins](/develop/plugins/#lifecycle-events) in the Plugin Development guide.

- **When**: When the plugin is loaded into the web view
- **Why**: Execute plugin initialization code

<Tabs syncKey="mobileOs">
<TabItem label="Android">

</TabItem>
<TabItem label="iOS">

**Note**: This is only available on Android.

- **When**: When the activity is re-launched. See [Activity#onNewIntent](<https://developer.android.com/reference/android/app/Activity#onNewIntent(android.content.Intent)>) for more information.
- **Why**: Handle application re-launch such as when a notification is clicked or a deep link is accessed.

## Adding Mobile Commands

There is a plugin class inside the respective mobile projects where commands can be defined that can be called by the Rust code:

import { Tabs, TabItem } from '@astrojs/starlight/components';

<Tabs syncKey="mobileOs">
<TabItem label="Android">

If you want to use a Kotlin `suspend` function, you need to use a custom coroutine scope

:::note
On Android native commands are scheduled on the main thread. Performing long-running operations will cause the UI to freeze and potentially "Application Not Responding" (ANR) error.

If you need to wait for some blocking IO, you can launch a corouting like that:

</TabItem>
<TabItem label="iOS">

Use the [`tauri::plugin::PluginHandle`](https://docs.rs/tauri/2.0.0/tauri/plugin/struct.PluginHandle.html) to call a mobile command from Rust:

Arguments are serialized to commands and can be parsed on the mobile plugin with the `Invoke::parseArgs` function, taking a class describing the argument object.

On Android, the arguments are defined as a class annotated with `@app.tauri.annotation.InvokeArg`. Inner objects must also be annotated:

:::note
Optional arguments are defined as `var <argumentName>: Type? = null`

Arguments with default values are defined as `var <argumentName>: Type = <default-value>`

Required arguments are defined as `lateinit var <argumentName>: Type`
:::

On iOS, the arguments are defined as a class that inherits `Decodable`. Inner objects must also inherit the Decodable protocol:

:::note
Optional arguments are defined as `var <argumentName>: Type?`

Arguments with default values are **NOT** supported.
Use a nullable type and set the default value on the command function instead.

Required arguments are defined as `let <argumentName>: Type`
:::

If a plugin requires permissions from the end user, Tauri simplifies the process of checking and requesting permissions.

<Tabs syncKey="mobileOs">
<TabItem label="Android">

First define the list of permissions needed and an alias to identify each group in code. This is done inside the `TauriPlugin` annotation:

</TabItem>
<TabItem label="iOS">

First override the `checkPermissions` and `requestPermissions` functions:

Tauri automatically implements two commands for the plugin: `checkPermissions` and `requestPermissions`.
Those commands can be directly called from JavaScript or Rust:

<Tabs syncKey="lang">
<TabItem label="JavaScript">

</TabItem>
<TabItem label="Rust">

{/* TODO: Is this section a duplicate of Lifecycle Events above? */}

Plugins can emit events at any point of time using the `trigger` function:

<Tabs syncKey="mobileOs">
<TabItem label="Android">

</TabItem>
<TabItem label="iOS">

The helper functions can then be called from the NPM package by using the [`addPluginListener`](/reference/javascript/api/namespacecore/#addpluginlistener) helper function:

**Examples:**

Example 1 (unknown):
```unknown
This implementation simplifies the process of sharing an API that can be used both by commands and Rust code.

### Develop an Android Plugin

A Tauri plugin for Android is defined as a Kotlin class that extends `app.tauri.plugin.Plugin` and is annotated with `app.tauri.annotation.TauriPlugin`. Each method annotated with `app.tauri.annotation.Command` can be called by Rust or JavaScript.

Tauri uses Kotlin by default for the Android plugin implementation, but you can switch to Java if you prefer. After generating a plugin, right click the Kotlin plugin class in Android Studio and select the "Convert Kotlin file to Java file" option from the menu. Android Studio will guide you through the project migration to Java.

### Develop an iOS Plugin

A Tauri plugin for iOS is defined as a Swift class that extends the `Plugin` class from the `Tauri` package. Each function with the `@objc` attribute and the `(_ invoke: Invoke)` parameter (for example `@objc private func download(_ invoke: Invoke) { }`) can be called by Rust or JavaScript.

The plugin is defined as a [Swift package](https://www.swift.org/package-manager/) so that you can use its package manager to manage dependencies.

## Plugin Configuration

Refer to the [Plugin Configuration section](/develop/plugins/#plugin-configuration) of the Plugin Development guide for more details on developing plugin configurations.

The plugin instance on mobile has a getter for the plugin configuration:

<Tabs syncKey="mobileOs">
<TabItem label="Android">
```

Example 2 (unknown):
```unknown
</TabItem>
<TabItem label="iOS">
```

Example 3 (unknown):
```unknown
</TabItem>
</Tabs>

## Lifecycle Events

Plugins can hook into several lifecycle events:

- [load](#load): When the plugin is loaded into the web view
- [onNewIntent](#onnewintent): Android only, when the activity is re-launched

There are also the additional [lifecycle events for plugins](/develop/plugins/#lifecycle-events) in the Plugin Development guide.

### load

- **When**: When the plugin is loaded into the web view
- **Why**: Execute plugin initialization code

<Tabs syncKey="mobileOs">
<TabItem label="Android">
```

Example 4 (unknown):
```unknown
</TabItem>
<TabItem label="iOS">
```

---

## What is Tauri?

**URL:** llms-txt#what-is-tauri?

**Contents:**
- Why Tauri?
  - Secure Foundation
  - Smaller App Size
  - Flexible Architecture

Tauri is a framework for building tiny, fast binaries for all major desktop and mobile platforms. Developers can integrate any frontend framework that compiles to HTML, JavaScript, and CSS for building their user experience while leveraging languages such as Rust, Swift, and Kotlin for backend logic when needed.

Get started building with [`create-tauri-app`](https://github.com/tauri-apps/create-tauri-app) by using one of the below commands. Be sure to follow the [prerequisites guide](/start/prerequisites/) to install all of the dependencies required by Tauri. For a more detailed walk through, see [Create a Project](/start/create-project/#using-create-tauri-app)

import Cta from '../_fragments/cta.mdx';

After you've created your first app, take a look at [Project Structure](/start/project-structure/) to understand what each file does.

Or explore the project setups and features from the examples ([tauri](https://github.com/tauri-apps/tauri/tree/dev/examples) | [plugins-workspace](https://github.com/tauri-apps/plugins-workspace/tree/v2/examples/api))

Tauri has 3 main advantages for developers to build upon:

- Secure foundation for building apps
- Smaller bundle size by using the system's native webview
- Flexibility for developers to use any frontend and bindings for multiple languages

Learn more about the Tauri philosophy in the [Tauri 1.0 blog post](/blog/tauri-1-0/).

### Secure Foundation

By being built on Rust, Tauri is able to take advantage of the memory, thread, and type-safety offered by Rust. Apps built on Tauri can automatically get those benefits even without needing to be developed by Rust experts.

Tauri also undergoes a security audit for major and minor releases. This not only covers code in the Tauri organization, but also for upstream dependencies that Tauri relies on. Of course this doesn't mitigate all risks, but it provides a solid foundation for developers to build on top of.

Read the [Tauri security policy](https://github.com/tauri-apps/tauri/security/policy) and the [Tauri 2.0 audit report](https://github.com/tauri-apps/tauri/blob/dev/audits/Radically_Open_Security-v2-report.pdf).

Tauri apps take advantage of the web view already available on every user's system. A Tauri app only contains the code and assets specific for that app and doesn't need to bundle a browser engine with every app. This means that a minimal Tauri app can be less than 600KB in size.

Learn more about creating optimized apps in the [App Size concept](/concept/size/).

### Flexible Architecture

Since Tauri uses web technologies that means that virtually any frontend framework is compatible with Tauri. The [Frontend Configuration guide](/start/frontend/) contains common configurations for popular frontend frameworks.

Bindings between JavaScript and Rust are available to developers using the `invoke` function in JavaScript and Swift and Kotlin bindings are available for [Tauri Plugins](/develop/plugins/).

[TAO](https://github.com/tauri-apps/tao) is responsible for Tauri window creation and [WRY](https://github.com/tauri-apps/wry) is responsible for web view rendering. These are libraries maintained by Tauri and can be consumed directly if deeper system integration is required outside of what Tauri exposes.

In addition, Tauri maintains a number of plugins to extend what core Tauri exposes. You can find those plugins alongside those provided by the community in the [Plugins section](/plugin/).

---

## Prerequisites

**URL:** llms-txt#prerequisites

**Contents:**
- System Dependencies
  - Linux
  - macOS
  - Windows
- Rust
- Node.js

import { Tabs, TabItem, Card } from '@astrojs/starlight/components';

In order to get started building your project with Tauri you'll first need to install a few dependencies:

1. [System Dependencies](#system-dependencies)
2. [Rust](#rust)
3. [Configure for Mobile Targets](#configure-for-mobile-targets) (only required if developing for mobile)

## System Dependencies

Follow the link to get started for your respective operating system:

- [Linux](#linux) (see below for specific distributions)
- [macOS Catalina (10.15) and later](#macos)
- [Windows 7 and later](#windows)

Tauri requires various system dependencies for development on Linux. These may be different depending on your distribution but we've included some popular distributions below to help you get setup.

<Tabs syncKey="distro">
  <TabItem label="Debian">

</TabItem>
  <TabItem label="Arch">

</TabItem>
  <TabItem label="Fedora">

</TabItem>
  <TabItem label="Gentoo">

</TabItem>
  <TabItem label="OSTree">

</TabItem>
  <TabItem label="openSUSE">

</TabItem>
  <TabItem label="Alpine">

</TabItem>
  <TabItem label="NixOS">

:::note
Instructions for Nix/NixOS can be found in the [NixOS Wiki](https://wiki.nixos.org/wiki/Tauri).
:::

If your distribution isn't included above then you may want to check [Awesome Tauri on GitHub](https://github.com/tauri-apps/awesome-tauri#guides) to see if a guide has been created.

Next: [Install Rust](#rust)

Tauri uses [Xcode](https://developer.apple.com/xcode/resources/) and various macOS and iOS development dependencies.

Download and install Xcode from one of the following places:

- [Mac App Store](https://apps.apple.com/gb/app/xcode/id497799835?mt=12)
- [Apple Developer website](https://developer.apple.com/xcode/resources/).

Be sure to launch Xcode after installing so that it can finish setting up.

<details>
<summary>Only developing for desktop targets?</summary>
If you're only planning to develop desktop apps and not targeting iOS then you can install Xcode Command Line Tools instead:

Next: [Install Rust](#rust)

Tauri uses the Microsoft C++ Build Tools for development as well as Microsoft Edge WebView2. These are both required for development on Windows.

Follow the steps below to install the required dependencies.

#### Microsoft C++ Build Tools

1. Download the [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) installer and open it to begin installation.
2. During installation check the "Desktop development with C++" option.

![Visual Studio C++ Build Tools installer screenshot](@assets/start/prerequisites/visual-studio-build-tools-installer.png)

Next: [Install WebView2](#webview2).

:::tip
WebView 2 is already installed on Windows 10 (from version 1803 onward) and later versions of Windows. If you are developing on one of these versions then you can skip this step and go directly to [installing Rust](#rust).
:::

Tauri uses Microsoft Edge WebView2 to render content on Windows.

Install WebView2 by visiting the [WebView2 Runtime download section](https://developer.microsoft.com/en-us/microsoft-edge/webview2/#download-section). Download the "Evergreen Bootstrapper" and install it.

Next: [Check VBSCRIPT](#vbscript-for-msi-installers)

#### VBSCRIPT (for MSI installers)

:::note[MSI package building only]
This is only required if you plan to build MSI installer packages (`"targets": "msi"` or `"targets": "all"` in `tauri.conf.json`).
:::

Building MSI packages on Windows requires the VBSCRIPT optional feature to be enabled. This feature is enabled by default on most Windows installations, but may have been disabled on some systems.

If you encounter errors like `failed to run light.exe` when building MSI packages, you may need to enable the VBSCRIPT feature:

1. Open **Settings** → **Apps** → **Optional features** → **More Windows features**
2. Locate **VBSCRIPT** in the list and ensure it's checked
3. Click **Next** and restart your computer if prompted

**Note:** VBSCRIPT is currently enabled by default on most Windows installations, but is [being deprecated](https://techcommunity.microsoft.com/blog/windows-itpro-blog/vbscript-deprecation-timelines-and-next-steps/4148301) and may be disabled in future Windows versions.

Next: [Install Rust](#rust)

Tauri is built with [Rust](https://www.rust-lang.org) and requires it for development. Install Rust using one of following methods. You can view more installation methods at https://www.rust-lang.org/tools/install.

<Tabs syncKey="OS">
  <TabItem label="Linux and macOS" class="content">

Install via [`rustup`](https://github.com/rust-lang/rustup) using the following command:

:::tip[Security Tip]
We have audited this bash script, and it does what it says it is supposed to do. Nevertheless, before blindly curl-bashing a script, it is always wise to look at it first.

Here is the file as a plain script: [rustup.sh](https://sh.rustup.rs/)
:::

</TabItem>
  <TabItem label="Windows">

Visit https://www.rust-lang.org/tools/install to install `rustup`.

Alternatively, you can use `winget` to install rustup using the following command in PowerShell:

:::caution[MSVC toolchain as default]

For full support for Tauri and tools like [`trunk`](https://trunkrs.dev/) make sure the MSVC Rust toolchain is the selected `default host triple` in the installer dialog. Depending on your system it should be either `x86_64-pc-windows-msvc`, `i686-pc-windows-msvc`, or `aarch64-pc-windows-msvc`.

If you already have Rust installed, you can make sure the correct toolchain is installed by running this command:

**Be sure to restart your Terminal (and in some cases your system) for the changes to take affect.**

Next: [Configure for Mobile Targets](#configure-for-mobile-targets) if you'd like to build for Android and iOS, or, if you'd like to use a JavaScript framework, [install Node](#nodejs). Otherwise [Create a Project](/start/create-project/).

:::note[JavaScript ecosystem]
Only if you intend to use a JavaScript frontend framework
:::

1. Go to the [Node.js website](https://nodejs.org), download the Long Term Support (LTS) version and install it.
2. Check if Node was successfully installed by running:

**Examples:**

Example 1 (sh):
```sh
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libxdo-dev \
  libssl-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev
```

Example 2 (sh):
```sh
sudo pacman -Syu
sudo pacman -S --needed \
  webkit2gtk-4.1 \
  base-devel \
  curl \
  wget \
  file \
  openssl \
  appmenu-gtk-module \
  libappindicator-gtk3 \
  librsvg \
  xdotool
```

Example 3 (sh):
```sh
sudo dnf check-update
sudo dnf install webkit2gtk4.1-devel \
  openssl-devel \
  curl \
  wget \
  file \
  libappindicator-gtk3-devel \
  librsvg2-devel \
  libxdo-devel
sudo dnf group install "c-development"
```

Example 4 (sh):
```sh
sudo emerge --ask \
  net-libs/webkit-gtk:4.1 \
  dev-libs/libappindicator \
  net-misc/curl \
  net-misc/wget \
  sys-apps/file
```

---

## Develop

**URL:** llms-txt#develop

**Contents:**
  - Developing Your Desktop Application
  - Developing your Mobile Application
  - Reacting to Source Code Changes
  - Using the Browser DevTools
  - Source Control

import CommandTabs from '@components/CommandTabs.astro';

Now that you have [everything set up](/start/), you are ready to run your application using Tauri.

If you are using an UI framework or JavaScript bundler you likely have access to a development server
that will speed up your development process, so if you haven't configured your app's dev URL and script
that starts it, you can do so via the [devUrl](/reference/config/#devurl) and
[beforeDevCommand](/reference/config/#beforedevcommand) config values:

Every framework has its own development tooling. It is outside of the scope of this document to cover them all or stay up to date.

Please refer to your framework's documentation to learn more and determine the correct values to be configured.

Otherwise if you are not using a UI framework or module bundler you can point Tauri to your frontend source code
and the Tauri CLI will start a development server for you:

Note that in this example the `src` folder must include a `index.html` file along any other assets loaded by your frontend.

:::caution[Plain/Vanilla Dev Server Security]

The built-in Tauri development server does not support mutual authentication
or encryption. You should never use it for development on untrusted networks.
See the [development server security considerations](/security/lifecycle/#development-server)
for a more detailed explanation.

### Developing Your Desktop Application

To develop your application for desktop, run the `tauri dev` command.

<CommandTabs
  npm="npm run tauri dev"
  yarn="yarn tauri dev"
  pnpm="pnpm tauri dev"
  deno="deno task tauri dev"
  bun="bun tauri dev"
  cargo="cargo tauri dev"
/>

The first time you run this command, the Rust package manager may need **several minutes** to download and build all the required packages.
Since they are cached, subsequent builds are much faster, as only your code needs rebuilding.

Once Rust has finished building, the webview opens, displaying your web app.
You can make changes to your web app, and if your tooling supports it, the webview should update automatically, just like a browser.

#### Opening the Web Inspector

You can open the Web Inspector to debug your application by performing a right-click on the webview and clicking "Inspect" or
using the `Ctrl + Shift + I` shortcut on Windows and Linux or `Cmd + Option + I` shortcut on macOS.

### Developing your Mobile Application

Developing for mobile is similar to how desktop development works, but you must run `tauri android dev` or `tauri ios dev` instead:

<CommandTabs
  npm="npm run tauri [android|ios] dev"
  yarn="yarn tauri [android|ios] dev"
  pnpm="pnpm tauri [android|ios] dev"
  deno="deno task tauri [android|ios] dev"
  bun="bun tauri [android|ios] dev"
  cargo="cargo tauri [android|ios] dev"
/>

The first time you run this command, the Rust package manager may need **several minutes** to download and build all the required packages.
Since they are cached, subsequent builds are much faster, as only your code needs rebuilding.

#### Development Server

The development server on mobile works similarly to the desktop one, but if you are trying to run on a physical iOS device,
you must configure it to listen to a particular address provided by the Tauri CLI, defined in the `TAURI_DEV_HOST` environment variable.
This address is either a public network address (which is the default behavior) or the actual iOS device TUN address - which is more secure, but currently
needs Xcode to connect to the device.

To use the iOS device's address you must open Xcode before running the dev command and ensure your device
is connected via network in the Window > Devices and Simulators menu.
Then you must run `tauri ios dev --force-ip-prompt` to select the iOS device address (a IPv6 address ending with **::2**).

To make your development server listen on the correct host to be accessible by the iOS device you must tweak its configuration
to use the `TAURI_DEV_HOST` value if it has been provided. Here is an example configuration for Vite:

Check your framework's setup guide for more information.

:::note
Projects created with [create-tauri-app](https://github.com/tauri-apps/create-tauri-app) configures
your development server for mobile dev out of the box.
:::

#### Device Selection

By default the mobile dev command tries to run your application in a connected device,
and fallbacks to prompting you to select a simulator to use.
To define the run target upfront you can provide the device or simulator name as argument:

<CommandTabs
  npm="npm run tauri ios dev 'iPhone 15'"
  yarn="yarn tauri ios dev 'iPhone 15'"
  pnpm="pnpm tauri ios dev 'iPhone 15'"
  deno="deno task tauri ios dev 'iPhone 15'"
  bun="bun tauri ios dev 'iPhone 15'"
  cargo="cargo tauri ios dev 'iPhone 15'"
/>

#### Using Xcode or Android Studio

Alternatively you can choose to use Xcode or Android Studio to develop your application.
This can help you troubleshoot some development issues by using the IDE instead of the command line tools.
To open the mobile IDE instead of running on a connected device or simulator, use the `--open` flag:

<CommandTabs
  npm="npm run tauri [android|ios] dev --open"
  yarn="yarn tauri [android|ios] dev --open"
  pnpm="pnpm tauri [android|ios] dev --open"
  deno="deno task tauri [android|ios] dev --open"
  bun="bun tauri [android|ios] dev --open"
  cargo="cargo tauri [android|ios] dev --open"
/>

:::note
If you intend on running the application on a physical iOS device you must also provide the `--host` argument
and your development server must use the `process.env.TAURI_DEV_HOST` value as host.
See your framework's setup guide for more information.

<CommandTabs
  npm="npm run tauri [android|ios] dev --open --host"
  yarn="yarn tauri [android|ios] dev --open --host"
  pnpm="pnpm tauri [android|ios] dev --open --host"
  deno="deno task tauri [android|ios] dev --open --host"
  bun="bun tauri [android|ios] dev --open --host"
  cargo="cargo tauri [android|ios] dev --open --host"
/>
:::

:::caution
To use Xcode or Android Studio the Tauri CLI process **must** be running and **cannot** be killed.
It is recommended to use the `tauri [android|ios] dev --open` command and keep the process alive until you close the IDE.
:::

#### Opening the Web Inspector

Safari must be used to access the Web Inspector for your iOS application.

Open the Safari on your Mac machine, choose **Safari > Settings** in the menu bar, click **Advanced**, then select **Show features for web developers**.

If you are running on a physical device you must enable **Web Inspector** in **Settings > Safari > Advanced**.

After following all steps you should see a **Develop** menu in Safari, where you will find the connected devices and applications to inspect.
  Select your device or simulator and click on **localhost** to open the Safari Developer Tools window.

The inspector is enabled by default for Android emulators, but you must enable it for physical devices.
  Connect your Android device to the computer, open the **Settings** app in the Android device, select **About**, scroll to Build Number and tap that 7 times.
  This will enable Developer Mode for your Android device and the **Developer Options** settings.

To enable application debugging on your device you must enter the **Developer Options** settings, toggle on the developer options switch
  and enable **USB Debugging**.

:::note
  Each Android distribution has its own way to enable the Developer Mode, please check your manufacturer's documentation for more information.
  :::

The Web Inspector for Android is powered by Google Chrome's DevTools and can be accessed by navigating to `chrome://inspect` in the Chrome browser on your computer.
  Your device or emulator should appear in the remote devices list if your Android application is running, and you can open the developer tools
  by clicking **inspect** on the entry matching your device.

1. Error running build script on Xcode

Tauri hooks into the iOS Xcode project by creating a build phase that executes the Tauri CLI to compile the Rust source
as a library that is loaded at runtime. The build phase is executed on the Xcode process context, so it might not be able
to use shell modifications such as PATH additions, so be careful when using tools such as Node.js version managers which may not be compatible.

2. Network permission prompt on first iOS app execution

On the first time you execute `tauri ios dev` you might see iOS prompting you for permission to find and connect
to devices on your local network. This permission is required because to access your development server from an iOS device,
we must expose it in the local network. To run your app in your device you must click Allow and restart your application.

### Reacting to Source Code Changes

Similarly to how your webview reflects changes in real time,
Tauri watches your Rust files for changes so when you modify any of them your application is automatically rebuilt and restarted.

You can disable this behavior by using the `--no-watch` flag on the `tauri dev` command.

To restrict the files that are watched for changes you can create a `.taurignore` file in the src-tauri folder.
This file works just like a regular Git ignore file, so you can ignore any folder or file:

### Using the Browser DevTools

Tauri's APIs only work in your app window, so once you start using them you won't be able to open your frontend in your system's browser anymore.

If you prefer using your browser's developer tooling, you must configure [tauri-invoke-http](https://github.com/tauri-apps/tauri-invoke-http)
to bridge Tauri API calls through a HTTP server.

In your project repository, you **SHOULD** commit the `src-tauri/Cargo.lock` along with the `src-tauri/Cargo.toml` to git
because Cargo uses the lockfile to provide deterministic builds. As a result, it is recommended that all applications check in
their `Cargo.lock`. You **SHOULD NOT** commit the `src-tauri/target` folder or any of its contents.

**Examples:**

Example 1 (unknown):
```unknown
:::note

Every framework has its own development tooling. It is outside of the scope of this document to cover them all or stay up to date.

Please refer to your framework's documentation to learn more and determine the correct values to be configured.

:::

Otherwise if you are not using a UI framework or module bundler you can point Tauri to your frontend source code
and the Tauri CLI will start a development server for you:
```

Example 2 (unknown):
```unknown
Note that in this example the `src` folder must include a `index.html` file along any other assets loaded by your frontend.

:::caution[Plain/Vanilla Dev Server Security]

The built-in Tauri development server does not support mutual authentication
or encryption. You should never use it for development on untrusted networks.
See the [development server security considerations](/security/lifecycle/#development-server)
for a more detailed explanation.

:::

### Developing Your Desktop Application

To develop your application for desktop, run the `tauri dev` command.

<CommandTabs
  npm="npm run tauri dev"
  yarn="yarn tauri dev"
  pnpm="pnpm tauri dev"
  deno="deno task tauri dev"
  bun="bun tauri dev"
  cargo="cargo tauri dev"
/>

The first time you run this command, the Rust package manager may need **several minutes** to download and build all the required packages.
Since they are cached, subsequent builds are much faster, as only your code needs rebuilding.

Once Rust has finished building, the webview opens, displaying your web app.
You can make changes to your web app, and if your tooling supports it, the webview should update automatically, just like a browser.

#### Opening the Web Inspector

You can open the Web Inspector to debug your application by performing a right-click on the webview and clicking "Inspect" or
using the `Ctrl + Shift + I` shortcut on Windows and Linux or `Cmd + Option + I` shortcut on macOS.

### Developing your Mobile Application

Developing for mobile is similar to how desktop development works, but you must run `tauri android dev` or `tauri ios dev` instead:

<CommandTabs
  npm="npm run tauri [android|ios] dev"
  yarn="yarn tauri [android|ios] dev"
  pnpm="pnpm tauri [android|ios] dev"
  deno="deno task tauri [android|ios] dev"
  bun="bun tauri [android|ios] dev"
  cargo="cargo tauri [android|ios] dev"
/>

The first time you run this command, the Rust package manager may need **several minutes** to download and build all the required packages.
Since they are cached, subsequent builds are much faster, as only your code needs rebuilding.

#### Development Server

The development server on mobile works similarly to the desktop one, but if you are trying to run on a physical iOS device,
you must configure it to listen to a particular address provided by the Tauri CLI, defined in the `TAURI_DEV_HOST` environment variable.
This address is either a public network address (which is the default behavior) or the actual iOS device TUN address - which is more secure, but currently
needs Xcode to connect to the device.

To use the iOS device's address you must open Xcode before running the dev command and ensure your device
is connected via network in the Window > Devices and Simulators menu.
Then you must run `tauri ios dev --force-ip-prompt` to select the iOS device address (a IPv6 address ending with **::2**).

To make your development server listen on the correct host to be accessible by the iOS device you must tweak its configuration
to use the `TAURI_DEV_HOST` value if it has been provided. Here is an example configuration for Vite:
```

Example 3 (unknown):
```unknown
Check your framework's setup guide for more information.

:::note
Projects created with [create-tauri-app](https://github.com/tauri-apps/create-tauri-app) configures
your development server for mobile dev out of the box.
:::

#### Device Selection

By default the mobile dev command tries to run your application in a connected device,
and fallbacks to prompting you to select a simulator to use.
To define the run target upfront you can provide the device or simulator name as argument:

<CommandTabs
  npm="npm run tauri ios dev 'iPhone 15'"
  yarn="yarn tauri ios dev 'iPhone 15'"
  pnpm="pnpm tauri ios dev 'iPhone 15'"
  deno="deno task tauri ios dev 'iPhone 15'"
  bun="bun tauri ios dev 'iPhone 15'"
  cargo="cargo tauri ios dev 'iPhone 15'"
/>

#### Using Xcode or Android Studio

Alternatively you can choose to use Xcode or Android Studio to develop your application.
This can help you troubleshoot some development issues by using the IDE instead of the command line tools.
To open the mobile IDE instead of running on a connected device or simulator, use the `--open` flag:

<CommandTabs
  npm="npm run tauri [android|ios] dev --open"
  yarn="yarn tauri [android|ios] dev --open"
  pnpm="pnpm tauri [android|ios] dev --open"
  deno="deno task tauri [android|ios] dev --open"
  bun="bun tauri [android|ios] dev --open"
  cargo="cargo tauri [android|ios] dev --open"
/>

:::note
If you intend on running the application on a physical iOS device you must also provide the `--host` argument
and your development server must use the `process.env.TAURI_DEV_HOST` value as host.
See your framework's setup guide for more information.

<CommandTabs
  npm="npm run tauri [android|ios] dev --open --host"
  yarn="yarn tauri [android|ios] dev --open --host"
  pnpm="pnpm tauri [android|ios] dev --open --host"
  deno="deno task tauri [android|ios] dev --open --host"
  bun="bun tauri [android|ios] dev --open --host"
  cargo="cargo tauri [android|ios] dev --open --host"
/>
:::

:::caution
To use Xcode or Android Studio the Tauri CLI process **must** be running and **cannot** be killed.
It is recommended to use the `tauri [android|ios] dev --open` command and keep the process alive until you close the IDE.
:::

#### Opening the Web Inspector

- iOS

  Safari must be used to access the Web Inspector for your iOS application.

  Open the Safari on your Mac machine, choose **Safari > Settings** in the menu bar, click **Advanced**, then select **Show features for web developers**.

  If you are running on a physical device you must enable **Web Inspector** in **Settings > Safari > Advanced**.

  After following all steps you should see a **Develop** menu in Safari, where you will find the connected devices and applications to inspect.
  Select your device or simulator and click on **localhost** to open the Safari Developer Tools window.

- Android

  The inspector is enabled by default for Android emulators, but you must enable it for physical devices.
  Connect your Android device to the computer, open the **Settings** app in the Android device, select **About**, scroll to Build Number and tap that 7 times.
  This will enable Developer Mode for your Android device and the **Developer Options** settings.

  To enable application debugging on your device you must enter the **Developer Options** settings, toggle on the developer options switch
  and enable **USB Debugging**.

  :::note
  Each Android distribution has its own way to enable the Developer Mode, please check your manufacturer's documentation for more information.
  :::

  The Web Inspector for Android is powered by Google Chrome's DevTools and can be accessed by navigating to `chrome://inspect` in the Chrome browser on your computer.
  Your device or emulator should appear in the remote devices list if your Android application is running, and you can open the developer tools
  by clicking **inspect** on the entry matching your device.

#### Troubleshooting

1. Error running build script on Xcode

Tauri hooks into the iOS Xcode project by creating a build phase that executes the Tauri CLI to compile the Rust source
as a library that is loaded at runtime. The build phase is executed on the Xcode process context, so it might not be able
to use shell modifications such as PATH additions, so be careful when using tools such as Node.js version managers which may not be compatible.

2. Network permission prompt on first iOS app execution

On the first time you execute `tauri ios dev` you might see iOS prompting you for permission to find and connect
to devices on your local network. This permission is required because to access your development server from an iOS device,
we must expose it in the local network. To run your app in your device you must click Allow and restart your application.

### Reacting to Source Code Changes

Similarly to how your webview reflects changes in real time,
Tauri watches your Rust files for changes so when you modify any of them your application is automatically rebuilt and restarted.

You can disable this behavior by using the `--no-watch` flag on the `tauri dev` command.

To restrict the files that are watched for changes you can create a `.taurignore` file in the src-tauri folder.
This file works just like a regular Git ignore file, so you can ignore any folder or file:
```

---

## Plugin Development

**URL:** llms-txt#plugin-development

**Contents:**
- Naming Convention
- Initialize Plugin Project
- Mobile Plugin Development
- Plugin Configuration
- Lifecycle Events
  - setup
  - on_navigation
  - on_webview_ready
  - on_event
  - on_drop

{/* TODO: Add a CLI section */}

import CommandTabs from '@components/CommandTabs.astro';

{/* TODO: Link to windowing system, commands for sending messages, and event system */}

:::tip[Plugin Development]

This guide is for developing Tauri plugins. If you're looking for a list of the currently available plugins and how to use them then visit the [Features and Recipes list](/plugin/).

Plugins are able to hook into the Tauri lifecycle, expose Rust code that relies on the web view APIs, handle commands with Rust, Kotlin or Swift code, and much more.

Tauri offers a windowing system with web view functionality, a way to send messages between the Rust process and the web view, and an event system along with several tools to enhance the development experience. By design, the Tauri core does not contain features not needed by everyone. Instead it offers a mechanism to add external functionalities into a Tauri application called plugins.

A Tauri plugin is composed of a Cargo crate and an optional NPM package that provides API bindings for its commands and events. Additionally, a plugin project can include an Android library project and a Swift package for iOS. You can learn more about developing plugins for Android and iOS in the [Mobile Plugin Development guide](/develop/plugins/develop-mobile/).

{/* TODO: https://github.com/tauri-apps/tauri/issues/7749 */}

Tauri plugins have a prefix followed by the plugin name. The plugin name is specified on the plugin configuration under [`tauri.conf.json > plugins`](/reference/config/#pluginconfig).

By default Tauri prefixes your plugin crate with `tauri-plugin-`. This helps your plugin to be discovered by the Tauri community and to be used with the Tauri CLI. When initializing a new plugin project, you must provide its name. The generated crate name will be `tauri-plugin-{plugin-name}` and the JavaScript NPM package name will be `tauri-plugin-{plugin-name}-api` (although we recommend using an [NPM scope](https://docs.npmjs.com/about-scopes) if possible). The Tauri naming convention for NPM packages is `@scope-name/plugin-{plugin-name}`.

## Initialize Plugin Project

To bootstrap a new plugin project, run `plugin new`. If you do not need the NPM package, use the `--no-api` CLI flag. If you want to initialize the plugin with Android and/or iOS support, use the `--android` and/or `--ios` flags.

After installing, you can run the following to create a plugin project:

<CommandTabs npm="npx @tauri-apps/cli plugin new [name]" />

This will initialize the plugin at the directory `tauri-plugin-[name]` and, depending on the used CLI flags, the resulting project will look like this:

If you have an existing plugin and would like to add Android or iOS capabilities to it, you can use `plugin android add` and `plugin ios add` to bootstrap the mobile library projects and guide you through the changes needed.

## Mobile Plugin Development

Plugins can run native mobile code written in Kotlin (or Java) and Swift. The default plugin template includes an Android library project using Kotlin and a Swift package. It includes an example mobile command showing how to trigger its execution from Rust code.

Read more about developing plugins for mobile in the [Mobile Plugin Development guide](/develop/plugins/develop-mobile/).

## Plugin Configuration

In the Tauri application where the plugin is used, the plugin configuration is specified on `tauri.conf.json` where `plugin-name` is the name of the plugin:

The plugin's configuration is set on the `Builder` and is parsed at runtime. Here is an example of the `Config` struct being used to specify the plugin configuration:

Plugins can hook into several lifecycle events:

- [setup](#setup): Plugin is being initialized
- [on_navigation](#on_navigation): Web view is attempting to perform navigation
- [on_webview_ready](#on_webview_ready): New window is being created
- [on_event](#on_event): Event loop events
- [on_drop](#on_drop): Plugin is being deconstructed

There are additional [lifecycle events for mobile plugins](/develop/plugins/develop-mobile/#lifecycle-events).

- **When**: Plugin is being initialized
- **Why**: Register mobile plugins, manage state, run background tasks

- **When**: Web view is attempting to perform navigation
- **Why**: Validate the navigation or track URL changes

Returning `false` cancels the navigation.

- **When**: New window has been created
- **Why**: Execute an initialization script for every window

- **When**: Event loop events
- **Why**: Handle core events such as window events, menu events and application exit requested

With this lifecycle hook you can be notified of any event loop [events](https://docs.rs/tauri/2.0.0/tauri/enum.RunEvent.html).

- **When**: Plugin is being deconstructed
- **Why**: Execute code when the plugin has been destroyed

See [`Drop`](https://doc.rust-lang.org/std/ops/trait.Drop.html) for more information.

## Exposing Rust APIs

The plugin APIs defined in the project's `desktop.rs` and `mobile.rs` are exported to the user as a struct with the same name as the plugin (in pascal case). When the plugin is setup, an instance of this struct is created and managed as a state so that users can retrieve it at any point in time with a `Manager` instance (such as `AppHandle`, `App`, or` Window`) through the extension trait defined in the plugin.

For example, the [`global-shortcut plugin`](/plugin/global-shortcut/) defines a `GlobalShortcut` struct that can be read by using the `global_shortcut` method of the `GlobalShortcutExt` trait:

Commands are defined in the `commands.rs` file. They are regular Tauri applications commands. They can access the AppHandle and Window instances directly, access state, and take input the same way as application commands. Read the [Commands guide](/develop/calling-rust/) for more details on Tauri commands.

This command shows how to get access to the `AppHandle` and `Window` instance via dependency injection, and takes two input parameters (`on_progress` and `url`):

To expose the command to the webview, you must hook into the `invoke_handler()` call in `lib.rs`:

Define a binding function in `webview-src/index.ts` so that plugin users can easily call the command in JavaScript:

Be sure to build the TypeScript code prior to testing it.

### Command Permissions

By default your commands are not accessible by the frontend. If you try to execute one of them, you will get a denied error rejection.
To actually expose commands, you also need to define permissions that allow each command.

#### Permission Files

Permissions are defined as JSON or TOML files inside the `permissions` directory. Each file can define a list of permissions, a list of permission sets and your plugin's default permission.

A permission describes privileges of your plugin commands. It can allow or deny a list of commands and associate command-specific and global scopes.

Scopes allow your plugin to define deeper restrictions to individual commands.
Each permission can define a list of scope objects that define something to be allowed or denied either specific to a command or globally to the plugin.

Let's define an example struct that will hold scope data for a list of binaries a `shell` plugin is allowed to spawn:

Your plugin consumer can define a scope for a specific command in their capability file (see the [documentation](/reference/acl/scope/)).
You can read the command-specific scope with the [`tauri::ipc::CommandScope`](https://docs.rs/tauri/2.0.0/tauri/ipc/struct.CommandScope.html) struct:

When a permission does not define any commands to be allowed or denied, it's considered a scope permission and it should only define a global scope for your plugin:

You can read the global scope with the [`tauri::ipc::GlobalScope`](https://docs.rs/tauri/2.0.0/tauri/ipc/struct.GlobalScope.html) struct:

:::note
We recommend checking both global and command scopes for flexibility
:::

The scope entry requires the `schemars` dependency to generate a JSON schema so the plugin consumers know the format of the scope and have autocomplete in their IDEs.

To define the schema, first add the dependency to your Cargo.toml file:

**Examples:**

Example 1 (unknown):
```unknown
. tauri-plugin-[name]/
├── src/                - Rust code
│ ├── commands.rs       - Defines the commands the webview can use
| ├── desktop.rs        - Desktop implementation
| ├── error.rs          - Default error type to use in returned results
│ ├── lib.rs            - Re-exports appropriate implementation, setup state...
│ ├── mobile.rs         - Mobile implementation
│ └── models.rs         - Shared structs
├── permissions/        - This will host (generated) permission files for commands
├── android             - Android library
├── ios                 - Swift package
├── guest-js            - Source code of the JavaScript API bindings
├── dist-js             - Transpiled assets from guest-js
├── Cargo.toml          - Cargo crate metadata
└── package.json        - NPM package metadata
```

Example 2 (json):
```json
{
  "build": { ... },
  "tauri": { ... },
  "plugins": {
    "plugin-name": {
      "timeout": 30
    }
  }
}
```

Example 3 (unknown):
```unknown
## Lifecycle Events

Plugins can hook into several lifecycle events:

- [setup](#setup): Plugin is being initialized
- [on_navigation](#on_navigation): Web view is attempting to perform navigation
- [on_webview_ready](#on_webview_ready): New window is being created
- [on_event](#on_event): Event loop events
- [on_drop](#on_drop): Plugin is being deconstructed

There are additional [lifecycle events for mobile plugins](/develop/plugins/develop-mobile/#lifecycle-events).

### setup

- **When**: Plugin is being initialized
- **Why**: Register mobile plugins, manage state, run background tasks
```

Example 4 (unknown):
```unknown
### on_navigation

- **When**: Web view is attempting to perform navigation
- **Why**: Validate the navigation or track URL changes

Returning `false` cancels the navigation.
```

---

## flatpak-builder.yaml

**URL:** llms-txt#flatpak-builder.yaml

runtime: org.gnome.Platform
runtime-version: '46'
sdk: org.gnome.Sdk

command: <main_binary_name>
finish-args:
  - --socket=wayland # Permission needed to show the window
  - --socket=fallback-x11 # Permission needed to show the window
  - --device=dri # OpenGL, not necessary for all projects
  - --share=ipc
  - --talk-name=org.kde.StatusNotifierWatcher # Optional: needed only if your app uses the tray icon
  - --filesystem=xdg-run/tray-icon:create # Optional: needed only if your app uses the tray icon - see an alternative way below
  # - --env=WEBKIT_DISABLE_COMPOSITING_MODE=1 # Optional: may solve some issues with black webviews on Wayland

modules:
  - name: binary
    buildsystem: simple

sources:
      # A reference to the previously generated flatpak metainfo file
      - type: file
        path: flatpak.metainfo.xml
      # If you use GitHub releases, you can target an existing remote file
      - type: file
        url: https://github.com/your_username/your_repository/releases/download/v1.0.1/yourapp_1.0.1_amd64.deb
        sha256: 08305b5521e2cf0622e084f2b8f7f31f8a989fc7f407a7050fa3649facd61469 # This is required if you are using a remote source
        only-arches: [x86_64] # This source is only used on x86_64 Computers
      # You can also use a local file for testing
      # - type: file
      #   path: yourapp_1.0.1_amd64.deb
    build-commands:
      - set -e

# Extract the deb package
      - mkdir deb-extract
      - ar -x *.deb --output deb-extract
      - tar -C deb-extract -xf deb-extract/data.tar.gz

# Copy binary
      - 'install -Dm755 deb-extract/usr/bin/<executable_name> /app/bin/<executable_name>'

# If you bundle files with additional resources, you should copy them:
      - mkdir -p /app/lib/<product_name>
      - cp -r deb-extract/usr/lib/<product_name>/. /app/lib/<product_name>
      - find /app/lib/<product_name> -type f -exec chmod 644 {} \;

# Copy desktop file + ensure the right icon is set
      - sed -i 's/^Icon=.*/Icon=<identifier>/' deb-extract/usr/share/applications/<product_name>.desktop
      - install -Dm644 deb-extract/usr/share/applications/<product_name>.desktop /app/share/applications/<identifier>.desktop

# Copy icons
      - install -Dm644 deb-extract/usr/share/icons/hicolor/128x128/apps/<main_binary_name>.png /app/share/icons/hicolor/128x128/apps/<identifier>.png
      - install -Dm644 deb-extract/usr/share/icons/hicolor/32x32/apps/<main_binary_name>.png /app/share/icons/hicolor/32x32/apps/<identifier>.png
      - install -Dm644 deb-extract/usr/share/icons/hicolor/256x256@2/apps/<main_binary_name>.png /app/share/icons/hicolor/256x256@2/apps/<identifier>.png
      - install -Dm644 flatpak.metainfo.xml /app/share/metainfo/<identifier>.metainfo.xml
rust
TrayIconBuilder::new()
  .icon(app.default_window_icon().unwrap().clone())
  .temp_dir_path(app.path().app_cache_dir().unwrap()) // will save to the cache folder ($XDG_CACHE_HOME) where the app already has permission
  .build()
  .unwrap();
shell

**Examples:**

Example 1 (unknown):
```unknown
The Gnome 46 runtime includes all dependencies of the standard Tauri app with their correct versions.

:::note[Using tray-icon without changing the Flatpak manifest]
If you prefer not opening access from your app to $XDG_RUNTIME_DIR (where tray-icon is saved on linux), you can change the path tauri saves the tray image:
```

Example 2 (unknown):
```unknown
:::

**5. Install, and Test the app**
```

---

## we need to add schemars to both dependencies and build-dependencies because the scope.rs module is shared between the app code and build script

**URL:** llms-txt#we-need-to-add-schemars-to-both-dependencies-and-build-dependencies-because-the-scope.rs-module-is-shared-between-the-app-code-and-build-script

**Contents:**
- Managing State

[dependencies]
schemars = "0.8"

[build-dependencies]
schemars = "0.8"
rust title="build.rs"
#[path = "src/scope.rs"]
mod scope;

const COMMANDS: &[&str] = &[];

fn main() {
    tauri_plugin::Builder::new(COMMANDS)
        .global_scope_schema(schemars::schema_for!(scope::Entry))
        .build();
}
toml title="permissions/websocket.toml"
"$schema" = "schemas/schema.json"
[[set]]
identifier = "allow-websocket"
description = "Allows connecting and sending messages through a WebSocket"
permissions = ["allow-connect", "allow-send"]
toml title="permissions/default.toml"
"$schema" = "schemas/schema.json"
[default]
description = "Allows making HTTP requests"
permissions = ["allow-request"]
rust title="src/commands.rs"
const COMMANDS: &[&str] = &["upload"];

fn main() {
    tauri_plugin::Builder::new(COMMANDS).build();
}
```

See the [Permissions Overview](/security/permissions/) documentation for more information.

A plugin can manage state in the same way a Tauri application does. Read the [State Management guide](/develop/state-management/) for more information.

**Examples:**

Example 1 (unknown):
```unknown
In your build script, add the following code:
```

Example 2 (unknown):
```unknown
##### Permission Sets

Permission sets are groups of individual permissions that helps users manage your plugin with a higher level of abstraction.
For instance if a single API uses multiple commands or if there's a logical connection between a collection of commands, you should define a set containing them:
```

Example 3 (unknown):
```unknown
##### Default Permission

The default permission is a special permission set with identifier `default`. It's recommended that you enable required commands by default.
For instance the `http` plugin is useless without the `request` command allowed:
```

Example 4 (unknown):
```unknown
#### Autogenerated Permissions

The easiest way to define permissions for each of your commands is to use the autogeneration option defined in your plugin's build script defined in the `build.rs` file.
Inside the `COMMANDS` const, define the list of commands in snake_case (should match the command function name) and Tauri will automatically generate an `allow-$commandname` and a `deny-$commandname` permissions.

The following example generates the `allow-upload` and `deny-upload` permissions:
```

---

## Vite

**URL:** llms-txt#vite

**Contents:**
- Checklist
- Example configuration

import { Tabs, TabItem, Steps } from '@astrojs/starlight/components';

Vite is a build tool that aims to provide a faster and leaner development experience for modern web projects.
This guide is accurate as of Vite 5.4.8.

- Use `../dist` as `frontendDist` in `src-tauri/tauri.conf.json`.
- Use `process.env.TAURI_DEV_HOST` as the development server host IP when set to run on iOS physical devices.

## Example configuration

1.  ##### Update Tauri configuration

Assuming you have the following `dev` and `build` scripts in your `package.json`:

You can configure the Tauri CLI to use your Vite development server and dist folder
    along with the hooks to automatically run the Vite scripts:

<TabItem label="npm">

<TabItem label="yarn">

<TabItem label="pnpm">

<TabItem label="deno">

1.  ##### Update Vite configuration:

**Examples:**

Example 1 (json):
```json
{
      "scripts": {
        "dev": "vite",
        "build": "tsc && vite build",
        "preview": "vite preview",
        "tauri": "tauri"
      }
    }
```

Example 2 (json):
```json
// tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "npm run dev",
        "beforeBuildCommand": "npm run build",
        "devUrl": "http://localhost:5173",
        "frontendDist": "../dist"
      }
    }
```

Example 3 (json):
```json
// tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "yarn dev",
        "beforeBuildCommand": "yarn build",
        "devUrl": "http://localhost:5173",
        "frontendDist": "../dist"
      }
    }
```

Example 4 (json):
```json
// tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "pnpm dev",
        "beforeBuildCommand": "pnpm build",
        "devUrl": "http://localhost:5173",
        "frontendDist": "../dist"
      }
    }
```

---

## macOS Code Signing

**URL:** llms-txt#macos-code-signing

**Contents:**
- Prerequisites
- Signing
  - Creating a signing certificate
  - Downloading the certificate
  - Configuring Tauri
- Notarization
- Ad-Hoc Signing

import { Tabs, TabItem } from '@astrojs/starlight/components';

Code signing is required on macOS to allow your application to be listed in the [Apple App Store] and to prevent a warning that your application is broken and can not be started, when downloaded from the browser.

Code signing on macOS requires an [Apple Developer] account which is either paid (99$ per year) or on the free plan (only for testing and development purposes). You also need an Apple device where you perform the code signing. This is required by the signing process and due to Apple's Terms and Conditions.

:::note
Note when using a free Apple Developer account, you will not be able to notarize your application and it will still show up as not verified when opening the app.
:::

To setup code signing for macOS you must create an Apple code signing certificate and
install it to your Mac computer keychain or export it to be used in CI/CD platforms.

### Creating a signing certificate

To create a new signing certificate, you must generate a Certificate Signing Request (CSR) file from your Mac computer.
See [creating a certificate signing request] to learn how to create the CSR for code signing.

On your Apple Developer account, navigate to the [Certificates, IDs & Profiles page]
and click on the `Create a certificate` button to open the interface to create a new certificate.
Choose the appropriate certificate type (`Apple Distribution` to submit apps to the App Store, and `Developer ID Application` to ship apps outside the App Store).
Upload your CSR, and the certificate will be created.

Only the Apple Developer `Account Holder` can create _Developer ID Application_ certificates. But it can be associated with a different Apple ID by creating a CSR with a different user email address.

### Downloading the certificate

On the [Certificates, IDs & Profiles page], click on the certificate you want to use and click on the `Download` button.
It saves a `.cer` file that installs the certificate on the keychain once opened.

### Configuring Tauri

You can configure Tauri to use your certificate when building macOS apps on your local machine or when using CI/CD platforms.

With the certificate installed in your Mac computer keychain, you can configure Tauri to use it for code signing.

The name of the certificate's keychain entry represents the `signing identity`, which can also be found by executing:

This identity can be provided in the [`tauri.conf.json > bundle > macOS > signingIdentity`] configuration option or
via the `APPLE_SIGNING_IDENTITY` environment variable.

A signing certificate is only valid if associated with your Apple ID.
An invalid certificate won't be listed on the _Keychain Access > My Certificates_ tab
or the _security find-identity -v -p codesigning_ output.
If the certificate does not download to the correct location, make sure the "login" option is selected in _Keychain Access_
under "Default Keychains" when downloading the .cer file.

#### Signing in CI/CD platforms

To use the certificate in CI/CD platforms, you must export the certificate to a base64 string
and configure the `APPLE_CERTIFICATE` and `APPLE_CERTIFICATE_PASSWORD` environment variables:

1. Open the `Keychain Access` app, click the _My Certificates_ tab in the _login_ keychain and find your certificate's entry.
2. Expand the entry, right-click on the key item, and select `Export "$KEYNAME"`.
3. Select the path to save the certificate's `.p12` file and define a password for the exported certificate.
4. Convert the `.p12` file to base64 running the following script on the terminal:

5. Set the contents of the `certificate-base64.txt` file to the `APPLE_CERTIFICATE` environment variable.
6. Set the certificate password to the `APPLE_CERTIFICATE_PASSWORD` environment variable.

<details>
<summary>Example GitHub Actions configuration</summary>

- `APPLE_ID` - Your Apple ID email
- `APPLE_ID_PASSWORD` - Your Apple ID password
- `APPLE_CERTIFICATE` - The base64 encoded `.p12` file
- `APPLE_CERTIFICATE_PASSWORD` - The password for your exported `.p12` file
- `KEYCHAIN_PASSWORD` - The password for your keychain

Check out the official GitHub guide to learn [how to set up secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository).

To notarize your application, you must provide credentials for Tauri to authenticate with Apple. This can be done via the App Store Connect API, or via your Apple ID.

<Tabs>
  <TabItem label="App Store Connect">
    1. Open the [App Store Connect's Users and Access page], select the Integrations tab, click on the Add button and select a name and the Developer access.
    2. Set the `APPLE_API_ISSUER` environment variable to the value presented above the keys table.
    3. Set the `APPLE_API_KEY` environment variable to the value on the Key ID column on that table.
    4. Download the private key, which can only be done once and is only visible after a page reload (the button is shown on the table row for the newly created key).
    5. Set the `APPLE_API_KEY_PATH` environment variable to the file path of the downloaded private key.
  </TabItem>

<TabItem label="Apple ID">
    1. Set the `APPLE_ID` environment variable to your Apple account email.
    2. Set the `APPLE_PASSWORD` environment variable to an [app-specific password] for your Apple account.
    3. Set the `APPLE_TEAM_ID` environment variable to your Apple Team ID. You can find your Team ID in [your account's membership page][membership].
  </TabItem>
</Tabs>

:::note
Notarization is required when using a _Developer ID Application_ certificate.
:::

[Certificates]: https://developer.apple.com/account/resources/certificates/list
[membership]: https://developer.apple.com/account#MembershipDetailsCard
[Apple Developer]: https://developer.apple.com
[Apple App Store]: https://www.apple.com/app-store/
[App Store Connect's Users and Access page]: https://appstoreconnect.apple.com/access/users
[`tauri.conf.json > bundle > macOS > signingIdentity`]: /reference/config/#signingidentity
[creating a certificate signing request]: https://developer.apple.com/help/account/create-certificates/create-a-certificate-signing-request
[Certificates, IDs & Profiles page]: https://developer.apple.com/account/resources/certificates/list
[app-specific password]: https://support.apple.com/en-ca/HT204397

If you do not wish to provide an Apple-authenticated identity, but still wish to sign your application, you can configure an _ad-hoc_ signature.

This is useful on ARM (Apple Silicon) devices, where code-signing is required for all apps from the Internet.

:::caution
Ad-hoc code signing does not prevent MacOS from requiring users to
[whitelist the installation in their Privacy & Security settings](https://support.apple.com/guide/mac-help/open-a-mac-app-from-an-unknown-developer-mh40616/mac).
:::

To configure an ad-hoc signature, provide the pseudo-identity `-` to Tauri, e.g.

For details on configuring Tauri's signing identity, see [above](#configuring-tauri).

**Examples:**

Example 1 (sh):
```sh
security find-identity -v -p codesigning
```

Example 2 (sh):
```sh
openssl base64 -in /path/to/certificate.p12 -out certificate-base64.txt
```

Example 3 (yaml):
```yaml
name: 'build'

on:
  push:
    branches:
      - main

jobs:
  build-macos:
    needs: prepare
    strategy:
      matrix:
        include:
          - args: '--target aarch64-apple-darwin'
            arch: 'silicon'
          - args: '--target x86_64-apple-darwin'
            arch: 'intel'
    runs-on: macos-latest
    env:
      APPLE_ID: ${{ secrets.APPLE_ID }}
      APPLE_ID_PASSWORD: ${{ secrets.APPLE_ID_PASSWORD }}
    steps:
      - name: Import Apple Developer Certificate
        env:
          APPLE_CERTIFICATE: ${{ secrets.APPLE_CERTIFICATE }}
          APPLE_CERTIFICATE_PASSWORD: ${{ secrets.APPLE_CERTIFICATE_PASSWORD }}
          KEYCHAIN_PASSWORD: ${{ secrets.KEYCHAIN_PASSWORD }}
        run: |
          echo $APPLE_CERTIFICATE | base64 --decode > certificate.p12
          security create-keychain -p "$KEYCHAIN_PASSWORD" build.keychain
          security default-keychain -s build.keychain
          security unlock-keychain -p "$KEYCHAIN_PASSWORD" build.keychain
          security set-keychain-settings -t 3600 -u build.keychain
          security import certificate.p12 -k build.keychain -P "$APPLE_CERTIFICATE_PASSWORD" -T /usr/bin/codesign
          security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KEYCHAIN_PASSWORD" build.keychain
          security find-identity -v -p codesigning build.keychain
      - name: Verify Certificate
        run: |
          CERT_INFO=$(security find-identity -v -p codesigning build.keychain | grep "Apple Development")
          CERT_ID=$(echo "$CERT_INFO" | awk -F'"' '{print $2}')
          echo "CERT_ID=$CERT_ID" >> $GITHUB_ENV
          echo "Certificate imported."
      - uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          APPLE_CERTIFICATE: ${{ secrets.APPLE_CERTIFICATE }}
          APPLE_CERTIFICATE_PASSWORD: ${{ secrets.APPLE_CERTIFICATE_PASSWORD }}
          APPLE_SIGNING_IDENTITY: ${{ env.CERT_ID }}
        with:
          args: ${{ matrix.args }}
```

Example 4 (json):
```json
"signingIdentity": "-"
```

---
