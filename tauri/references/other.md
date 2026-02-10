# Tauri - Other

**Pages:** 54

---

## State Management

**URL:** llms-txt#state-management

**Contents:**
- Mutability
  - When to use an async mutex
  - Do you need `Arc`?
- Accessing State
  - Access state in commands
  - Access state with the [`Manager`] trait
- Mismatching Types

In a Tauri application, you often need to keep track of the current state of your application or manage the lifecycle of things associated with it. Tauri provides an easy way to manage the state of your application using the [`Manager`] API, and read it when commands are called.

Here is a simple example:

You can later access your state with any type that implements the [`Manager`] trait, for example the [`App`] instance:

For more info, including accessing state in commands, see the [Accessing State](#accessing-state) section.

In Rust, you cannot directly mutate values which are shared between multiple threads or when ownership is controlled through a shared pointer such as [`Arc`] (or Tauri's [`State`]). Doing so could cause data races (for example, two writes happening simultaneously).

To work around this, you can use a concept known as [interior mutability](https://doc.rust-lang.org/book/ch15-05-interior-mutability.html). For example, the standard library's [`Mutex`] can be used to wrap your state. This allows you to lock the value when you need to modify it, and unlock it when you are done.

The state can now be modified by locking the mutex:

At the end of the scope, or when the `MutexGuard` is otherwise dropped, the mutex is unlocked automatically so that other parts of your application can access and mutate the data within.

### When to use an async mutex

To quote the [Tokio documentation](https://docs.rs/tokio/latest/tokio/sync/struct.Mutex.html#which-kind-of-mutex-should-you-use), it's often fine to use the standard library's [`Mutex`] instead of an async mutex such as the one Tokio provides:

> Contrary to popular belief, it is ok and often preferred to use the ordinary Mutex from the standard library in asynchronous code ... The primary use case for the async mutex is to provide shared mutable access to IO resources such as a database connection.

It's a good idea to read the linked documentation fully to understand the trade-offs between the two. One reason you _would_ need an async mutex is if you need to hold the `MutexGuard` across await points.

### Do you need `Arc`?

It's common to see [`Arc`] used in Rust to share ownership of a value across multiple threads (usually paired with a [`Mutex`] in the form of `Arc<Mutex<T>>`). However, you don't need to use [`Arc`] for things stored in [`State`] because Tauri will do this for you.

In case `State`'s lifetime requirements prevent you from moving your state into a new thread you can instead move an `AppHandle` into the thread and then retrieve your state as shown below in the "[Access state with the Manager trait](#access-state-with-the-manager-trait)" section. `AppHandle`s are deliberately cheap to clone for use-cases like this.

### Access state in commands

For more information on commands, see [Calling Rust from the Frontend](/develop/calling-rust/).

If you are using `async` commands and want to use Tokio's async [`Mutex`](https://docs.rs/tokio/latest/tokio/sync/struct.Mutex.html), you can set it up the same way and access the state like this:

Note that the return type must be [`Result`] if you use asynchronous commands.

### Access state with the [`Manager`] trait

Sometimes you may need to access the state outside of commands, such as in a different thread or in an event handler like `on_window_event`. In such cases, you can use the `state()` method of types that implement the [`Manager`] trait (such as the `AppHandle`) to get the state:

This method is useful when you cannot rely on command injection. For example, if you need to move the state into a thread where using an `AppHandle` is easier, or if you are not in a command context.

:::caution
If you use the wrong type for the [`State`] parameter, you will get a runtime panic instead of compile time error.

For example, if you use `State<'_, AppState>` instead of `State<'_, Mutex<AppState>>`, there won't be any state managed with that type.
:::

If you prefer, you can wrap your state with a type alias to prevent this mistake:

However, make sure to use the type alias as it is, and not wrap it in a [`Mutex`] a second time, otherwise you will run into the same issue.

[`Manager`]: https://docs.rs/tauri/latest/tauri/trait.Manager.html
[`State`]: https://docs.rs/tauri/latest/tauri/struct.State.html
[`Mutex`]: https://doc.rust-lang.org/stable/std/sync/struct.Mutex.html
[`Arc`]: https://doc.rust-lang.org/stable/std/sync/struct.Arc.html
[`App`]: https://docs.rs/tauri/latest/tauri/struct.App.html
[`Result`]: https://doc.rust-lang.org/stable/std/result/index.html

**Examples:**

Example 1 (rust):
```rust
use tauri::{Builder, Manager};

struct AppData {
  welcome_message: &'static str,
}

fn main() {
  Builder::default()
    .setup(|app| {
      app.manage(AppData {
        welcome_message: "Welcome to Tauri!",
      });
      Ok(())
    })
    .run(tauri::generate_context!())
    .unwrap();
}
```

Example 2 (rust):
```rust
let data = app.state::<AppData>();
```

Example 3 (rust):
```rust
use std::sync::Mutex;

use tauri::{Builder, Manager};

#[derive(Default)]
struct AppState {
  counter: u32,
}

fn main() {
  Builder::default()
    .setup(|app| {
      app.manage(Mutex::new(AppState::default()));
      Ok(())
    })
    .run(tauri::generate_context!())
    .unwrap();
}
```

Example 4 (rust):
```rust
let state = app.state::<Mutex<AppState>>();

// Lock the mutex to get mutable access:
let mut state = state.lock().unwrap();

// Modify the state:
state.counter += 1;
```

---

## Upgrade from Tauri 2.0 Beta

**URL:** llms-txt#upgrade-from-tauri-2.0-beta

**Contents:**
- Automated Migration
- Breaking Changes
  - Tauri Core Plugins
  - Built-In Development Server

import { Tabs, TabItem } from '@astrojs/starlight/components';
import CommandTabs from '@components/CommandTabs.astro';

This guide walks you through upgrading your Tauri 2.0 beta application to Tauri 2.0 release candidate.

## Automated Migration

The Tauri v2 CLI includes a `migrate` command that automates most of the process and helps you finish the migration:

<CommandTabs
  npm="npm install @tauri-apps/cli@latest
    npm run tauri migrate"
  yarn="yarn upgrade @tauri-apps/cli@latest
    yarn tauri migrate"
  pnpm="pnpm update @tauri-apps/cli@latest
    pnpm tauri migrate"
  cargo='cargo install tauri-cli --version "^2.0.0" --locked
    cargo tauri migrate'
/>

Learn more about the `migrate` command in the [Command Line Interface reference](/reference/cli/#migrate)

We have had several breaking changes going from beta to release candidate. These can be either auto-migrated (see above) or manually performed.

### Tauri Core Plugins

We changed how Tauri built-in plugins are addressed in the capabilities [PR #10390](https://github.com/tauri-apps/tauri/pull/10390).

To migrate from the latest beta version you need to prepend all core permission identifiers in your capabilities with `core:` or switch to the `core:default` permission and remove old core plugin identifiers.

We also added a new special `core:default` permission set which will contain all default permissions of all core plugins, so you can simplify the permissions boilerplate in your capabilities config.

### Built-In Development Server

We introduced changes to the network exposure of the built-in development server [PR #10437](https://github.com/tauri-apps/tauri/pull/10437) and [PR #10456](https://github.com/tauri-apps/tauri/pull/10456).

The built-in mobile development server no longer exposes network wide and tunnels traffic from the local machine directly to the device.

Currently this improvement does not automatically apply when running on iOS devices (either directly or from Xcode).
In this case we default to using the public network address for the development server,
but there's a way around it which involves opening Xcode to automatically start a connection between your macOS machine and your connected iOS device,
then running `tauri ios dev --force-ip-prompt` to select the iOS device's TUN address (ends with **::2**).

Your development server configuration needs to adapt to this change if running on a physical iOS device is intended.
Previously we recommended checking if the `TAURI_ENV_PLATFORM` environment variable matches either `android` or `ios`,
but since we can now connect to localhost unless using an iOS device, you should instead check the `TAURI_DEV_HOST` environment variable.
Here's an example of a Vite configuration migration:

:::note
The `internal-ip` NPM package is no longer required, you can directly use the TAURI_DEV_HOST value instead.
:::

**Examples:**

Example 1 (json):
```json
...
"permissions": [
    "path:default",
    "event:default",
    "window:default",
    "app:default",
    "image:default",
    "resources:default",
    "menu:default",
    "tray:default",
]
...
```

Example 2 (json):
```json
...
"permissions": [
    "core:path:default",
    "core:event:default",
    "core:window:default",
    "core:app:default",
    "core:image:default",
    "core:resources:default",
    "core:menu:default",
    "core:tray:default",
]
...
```

Example 3 (json):
```json
...
"permissions": [
    "core:default"
]
...
```

Example 4 (js):
```js
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { internalIpV4Sync } from 'internal-ip';

const mobile = !!/android|ios/.exec(process.env.TAURI_ENV_PLATFORM);

export default defineConfig({
  plugins: [svelte()],
  clearScreen: false,
  server: {
    host: mobile ? '0.0.0.0' : false,
    port: 1420,
    strictPort: true,
    hmr: mobile
      ? {
          protocol: 'ws',
          host: internalIpV4Sync(),
          port: 1421,
        }
      : undefined,
  },
});
```

---

## Snapcraft

**URL:** llms-txt#snapcraft

**Contents:**
- Prerequisites
- Configuration

import { Tabs, TabItem, Card } from '@astrojs/starlight/components';

**1. Install `snap`**

{/* prettier-ignore */}
<Tabs syncKey="distro">
  <TabItem label="Debian">
    
  </TabItem>
  <TabItem label="Arch">
    
  </TabItem>
  <TabItem label="Fedora">

Reboot your system afterwards.

**2. Install a base snap**

**3. Install `snapcraft`**

1. Create an UbuntuOne account.
2. Go to the [Snapcraft](https://snapcraft.io) website and register an App name.
3. Create a snapcraft.yaml file in your projects root.
4. Adjust the names in the snapcraft.yaml file.

```yaml
name: appname
base: core22
version: '0.1.0'
summary: Your summary # 79 char long summary
description: |
  Your description

grade: stable
confinement: strict

layout:
  /usr/lib/$SNAPCRAFT_ARCH_TRIPLET/webkit2gtk-4.1:
    bind: $SNAP/usr/lib/$SNAPCRAFT_ARCH_TRIPLET/webkit2gtk-4.1

apps:
  appname:
    command: usr/bin/appname
    desktop: usr/share/applications/appname.desktop
    extensions: [gnome]
    #plugs:
    #  - network
    # Add whatever plugs you need here, see https://snapcraft.io/docs/snapcraft-interfaces for more info.
    # The gnome extension already includes [ desktop, desktop-legacy, gsettings, opengl, wayland, x11, mount-observe, calendar-service ]
    #  - single-instance-plug # add this if you're using the single-instance plugin
    #slots:
    # Add the slots you need to expose to other snaps
    #  - single-instance-plug # add this if you're using the single-instance plugin

**Examples:**

Example 1 (shell):
```shell
sudo apt install snapd
```

Example 2 (shell):
```shell
sudo pacman -S --needed git base-devel
    git clone https://aur.archlinux.org/snapd.git
    cd snapd
    makepkg -si
    sudo systemctl enable --now snapd.socket
    sudo systemctl start snapd.socket
    sudo systemctl enable --now snapd.apparmor.service
```

Example 3 (shell):
```shell
sudo dnf install snapd
    # Enable classic snap support
    sudo ln -s /var/lib/snapd/snap /snap
```

Example 4 (shell):
```shell
sudo snap install core22
```

---

## RPM

**URL:** llms-txt#rpm

**Contents:**
- Limitations
- Configuring the RPM package
  - Add post, pre-install/remove script to the package
  - Setting the Conflict, Provides, Depends, Files, Obsoletes, DesktopTemplate, and Epoch
  - Add a license to the package

import ShowSolution from '@components/ShowSolution.astro';
import CommandTabs from '@components/CommandTabs.astro';
import { Steps } from '@astrojs/starlight/components';

:::note
Some sections in this guide are optional. This includes configuring scripts and certain other steps. Feel free to adapt the instructions based on your specific needs and requirements.
:::

This guide covers how to distribute and manage RPM packages, including retrieving package information, configuring scripts, setting dependencies, and signing packages.

GUI apps on macOS and Linux do not inherit the `$PATH` from your shell dotfiles (`.bashrc`, `.bash_profile`, `.zshrc`, etc). Check out Tauri's [fix-path-env-rs](https://github.com/tauri-apps/fix-path-env-rs) crate to fix this issue.

Core libraries such as glibc frequently break compatibility with older systems. For this reason, you must build your Tauri application using the oldest base system you intend to support. A relatively old system such as Ubuntu 18.04 is more suited than Ubuntu 22.04, as the binary compiled on Ubuntu 22.04 will have a higher requirement of the glibc version, so when running on an older system, you will face a runtime error like `/usr/lib/libc.so.6: version 'GLIBC_2.33' not found`. We recommend using a Docker container or GitHub Actions to build your Tauri application for Linux.

See the issues [tauri-apps/tauri#1355](https://github.com/tauri-apps/tauri/issues/1355) and [rust-lang/rust#57497](https://github.com/rust-lang/rust/issues/57497), in addition to the [AppImage guide](https://docs.appimage.org/reference/best-practices.html#binaries-compiled-on-old-enough-base-system) for more information.

## Configuring the RPM package

Tauri allows you to configure the RPM package by adding scripts, setting dependencies, adding a license, including custom files, and more.
For detailed information about configurable options, please refer to: [RpmConfig](https://v2.tauri.app/reference/config/#rpmconfig).

### Add post, pre-install/remove script to the package

The RPM package manager allows you to run scripts before or after the installation or removal of the package. For example, you can use these scripts to start a service after the package is installed.

Here's an example of how to add these scripts:

1. Create a folder named `scripts` in the `src-tauri` directory in your project.

2. Create the script files in the folder.

Now if we look inside `/src-tauri/scripts` we will see:

3. Add some content to the scripts

4. Add the scripts to the`tauri.conf.json` file

### Setting the Conflict, Provides, Depends, Files, Obsoletes, DesktopTemplate, and Epoch

- **conflict**: Prevents the installation of the package if it conflicts with another package.
  For example, if you update an RPM package that your app depends on and the new version is incompatible with your app.

- **provides**: Lists the RPM dependencies that your application provides.

- **depends**: Lists the RPM dependencies that your application needs to run.

- **files**: Specifies which files to include in the package.

- **obsoletes**: Lists the RPM dependencies that your application obsoletes.

:::note
If this package is installed, packages listed as "obsoletes" will be automatically removed if present.
:::

- **desktopTemplate**: Adds a custom desktop file to the package.

- **epoch**: Defines weighted dependencies based on version numbers.

:::caution
It is not recommended to use epoch unless necessary, as it alters how the package manager compares package versions.
For more information about epoch, please check: [RPM Packaging Guide](https://rpm-packaging-guide.github.io/#epoch-scriptlets-and-triggers).
:::

To use these options, add the following to your `tauri.conf.json` :

### Add a license to the package

To add a license to the package, add the following to the `src-tauri/cargo.toml` or in the `src-tauri/tauri.conf.json` file:

```toml title="src-tauri/cargo.toml"
[package]
name = "tauri-app"
version = "0.0.0"
description = "A Tauri App"
authors = ["you"]
edition = "2021"
license = "MIT" # add the license here

**Examples:**

Example 1 (bash):
```bash
mkdir src-tauri/scripts
```

Example 2 (bash):
```bash
touch src-tauri/scripts/postinstall.sh \
touch src-tauri/scripts/preinstall.sh \
touch src-tauri/scripts/preremove.sh \
touch src-tauri/scripts/postremove.sh
```

Example 3 (bash):
```bash
ls src-tauri/scripts/
postinstall.sh  postremove.sh  preinstall.sh  preremove.sh
```

Example 4 (unknown):
```unknown

```

---

## Calling the Frontend from Rust

**URL:** llms-txt#calling-the-frontend-from-rust

The `@tauri-apps/api` NPM package offers APIs to listen to both global and webview-specific events.

- Listening to global events

- Listening to webview-specific events

The `listen` function keeps the event listener registered for the entire lifetime of the application.
To stop listening on an event you can use the `unlisten` function which is returned by the `listen` function:

:::note
Always use the unlisten function when your execution context goes out of scope
such as when a component is unmounted.

When the page is reloaded or you navigate to another URL the listeners are unregistered automatically.
This does not apply to a Single Page Application (SPA) router though.
:::

Additionally Tauri provides a utility function for listening to an event exactly once:

:::note
Events emitted in the frontend also triggers listeners registed by these APIs.
For more information see the [Calling Rust from the Frontend] documentation.
:::

#### Listening to Events on Rust

Global and webview-specific events are also delivered to listeners registered in Rust.

- Listening to global events

- Listening to webview-specific events

The `listen` function keeps the event listener registered for the entire lifetime of the application.
To stop listening on an event you can use the `unlisten` function:

Additionally Tauri provides a utility function for listening to an event exactly once:

In this case the event listener is immediately unregistered after its first trigger.

[Calling Rust from the Frontend]: /develop/calling-rust/

**Examples:**

Example 1 (ts):
```ts
import { listen } from '@tauri-apps/api/event';

  type DownloadStarted = {
    url: string;
    downloadId: number;
    contentLength: number;
  };

  listen<DownloadStarted>('download-started', (event) => {
    console.log(
      `downloading ${event.payload.contentLength} bytes from ${event.payload.url}`
    );
  });
```

Example 2 (ts):
```ts
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';

  const appWebview = getCurrentWebviewWindow();
  appWebview.listen<string>('logged-in', (event) => {
    localStorage.setItem('session-token', event.payload);
  });
```

Example 3 (js):
```js
import { listen } from '@tauri-apps/api/event';

const unlisten = await listen('download-started', (event) => {});
unlisten();
```

Example 4 (js):
```js
import { once } from '@tauri-apps/api/event';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';

once('ready', (event) => {});

const appWebview = getCurrentWebviewWindow();
appWebview.once('ready', () => {});
```

---

## Selenium

**URL:** llms-txt#selenium

**Contents:**
- Create a Directory for the Tests
- Initializing a Selenium Project
- Testing
- Running the Test Suite

import CommandTabs from '@components/CommandTabs.astro';

Make sure to go through the [prerequisites instructions] to be able to follow this guide.

This WebDriver testing example will use [Selenium] and a popular Node.js testing suite. You are expected to already have
Node.js installed, along with `npm` or `yarn` although the [finished example project] uses `pnpm`.

## Create a Directory for the Tests

Let's create a space to write these tests in our project. We will be using a nested directory for
this example project as we will later also go over other frameworks, but typically you will only need to use one. Create
the directory we will use with `mkdir -p e2e-tests`. The rest of this guide will assume you are inside the
`e2e-tests` directory.

## Initializing a Selenium Project

We will be using a pre-existing `package.json` to bootstrap this test suite because we have already chosen specific
dependencies to use and want to showcase a simple working solution. The bottom of this section has a collapsed
guide on how to set it up from scratch.

We have a script that runs [Mocha] as a test framework exposed as the `test` command. We also have various dependencies
that we will be using to run the tests. [Mocha] as the testing framework, [Chai] as the assertion library, and
[`selenium-webdriver`] which is the Node.js [Selenium] package.

<details>
  <summary>Click me if you want to see how to set a project up from scratch</summary>

If you want to install the dependencies from scratch, just run the following command.

<CommandTabs
  npm="npm install mocha chai selenium-webdriver"
  yarn="yarn add mocha chai selenium-webdriver"
/>

I suggest also adding a `"test": "mocha"` item in the `package.json` `"scripts"` key so that running Mocha can be
called
simply with

<CommandTabs npm="npm test" yarn="yarn test" />

Unlike the [WebdriverIO Test Suite](/develop/tests/webdriver/example/webdriverio/#config), Selenium does not come out of the box with a Test Suite and
leaves it up to the developer to build those out. We chose [Mocha], which is pretty neutral and not related to WebDrivers, so our script will need to do a bit of work to set up everything for us in the correct order. [Mocha] expects a
testing file at `test/test.js` by default, so let's create that file now.

If you are familiar with JS testing frameworks, `describe`, `it`, and `expect` should look familiar. We also have
semi-complex `before()` and `after()` callbacks to set up and teardown mocha. Lines that are not the tests themselves
have comments explaining the setup and teardown code. If you were familiar with the Spec file from the
[WebdriverIO example](/develop/tests/webdriver/example/webdriverio/#spec), you notice a lot more code that isn't tests, as we have to set up a few
more WebDriver related items.

## Running the Test Suite

Now that we are all set up with our dependencies and our test script, let's run it!

<CommandTabs npm="npm test" yarn="yarn test" />

We should see output the following output:

We can see that our `Hello Tauri` test suite we created with `describe` had all 3 items we created with `it` pass their
tests!

With [Selenium] and some hooking up to a test suite, we just enabled e2e testing without modifying our Tauri
application at all!

[prerequisites instructions]: /develop/tests/webdriver/
[selenium]: https://selenium.dev/
[finished example project]: https://github.com/tauri-apps/webdriver-example
[mocha]: https://mochajs.org/
[chai]: https://www.chaijs.com/
[`selenium-webdriver`]: https://www.npmjs.com/package/selenium-webdriver

**Examples:**

Example 1 (json):
```json
{
  "name": "selenium",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "mocha"
  },
  "dependencies": {
    "chai": "^5.2.1",
    "mocha": "^11.7.1",
    "selenium-webdriver": "^4.34.0"
  }
}
```

Example 2 (javascript):
```javascript
import os from 'os';
import path from 'path';
import { expect } from 'chai';
import { spawn, spawnSync } from 'child_process';
import { Builder, By, Capabilities } from 'selenium-webdriver';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

// create the path to the expected application binary
const application = path.resolve(
  __dirname,
  '..',
  '..',
  'src-tauri',
  'target',
  'debug',
  'tauri-app'
);

// keep track of the webdriver instance we create
let driver;

// keep track of the tauri-driver process we start
let tauriDriver;
let exit = false;

before(async function () {
  // set timeout to 2 minutes to allow the program to build if it needs to
  this.timeout(120000);

  // ensure the app has been built
  spawnSync('yarn', ['tauri', 'build', '--debug', '--no-bundle'], {
    cwd: path.resolve(__dirname, '../..'),
    stdio: 'inherit',
    shell: true,
  });

  // start tauri-driver
  tauriDriver = spawn(
    path.resolve(os.homedir(), '.cargo', 'bin', 'tauri-driver'),
    [],
    { stdio: [null, process.stdout, process.stderr] }
  );
  tauriDriver.on('error', (error) => {
    console.error('tauri-driver error:', error);
    process.exit(1);
  });
  tauriDriver.on('exit', (code) => {
    if (!exit) {
      console.error('tauri-driver exited with code:', code);
      process.exit(1);
    }
  });

  const capabilities = new Capabilities();
  capabilities.set('tauri:options', { application });
  capabilities.setBrowserName('wry');

  // start the webdriver client
  driver = await new Builder()
    .withCapabilities(capabilities)
    .usingServer('http://127.0.0.1:4444/')
    .build();
});

after(async function () {
  // stop the webdriver session
  await closeTauriDriver();
});

describe('Hello Tauri', () => {
  it('should be cordial', async () => {
    const text = await driver.findElement(By.css('body > h1')).getText();
    expect(text).to.match(/^[hH]ello/);
  });

  it('should be excited', async () => {
    const text = await driver.findElement(By.css('body > h1')).getText();
    expect(text).to.match(/!$/);
  });

  it('should be easy on the eyes', async () => {
    // selenium returns color css values as rgb(r, g, b)
    const text = await driver
      .findElement(By.css('body'))
      .getCssValue('background-color');

    const rgb = text.match(/^rgb\((?<r>\d+), (?<g>\d+), (?<b>\d+)\)$/).groups;
    expect(rgb).to.have.all.keys('r', 'g', 'b');

    const luma = 0.2126 * rgb.r + 0.7152 * rgb.g + 0.0722 * rgb.b;
    expect(luma).to.be.lessThan(100);
  });
});

async function closeTauriDriver() {
  exit = true;
  // kill the tauri-driver process
  tauriDriver.kill();
  // stop the webdriver session
  await driver.quit();
}

function onShutdown(fn) {
  const cleanup = () => {
    try {
      fn();
    } finally {
      process.exit();
    }
  };

  process.on('exit', cleanup);
  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
  process.on('SIGHUP', cleanup);
  process.on('SIGBREAK', cleanup);
}

onShutdown(() => {
  closeTauriDriver();
});
```

Example 3 (text):
```text
➜  selenium git:(main) ✗ yarn test
yarn run v1.22.11
$ Mocha


  Hello Tauri
    ✔ should be cordial (120ms)
    ✔ should be excited
    ✔ should be easy on the eyes


  3 passing (588ms)

Done in 0.93s.
```

---

## bundle for distribution outside the macOS App Store

**URL:** llms-txt#bundle-for-distribution-outside-the-macos-app-store

cargo tauri bundle --bundles app,dmg

---

## Flathub

**URL:** llms-txt#flathub

**Contents:**
- Prerequisites

import { Tabs, TabItem, Card } from '@astrojs/starlight/components';

For detailed information on how Flatpak works, you can read [Building your first Flatpak](https://docs.flatpak.org/en/latest/first-build.html)

This guide assumes you want to distribute your Flatpak via [Flathub](https://flathub.org/), the most commonly used platform for Flatpak distribution. If you plan on using other platforms, please consult their documentation instead.

To test your app inside the Flatpak runtime you can build the Flatpak locally first before uploading your app to Flathub. This can also be helpful if you want to quickly share development builds.

**1. Install `flatpak` and `flatpak-builder`**

To build Flatpaks locally you need the `flatpak` and `flatpak-builder` tools. For example on Ubuntu you can run this command:

<Tabs syncKey="distro">
  <TabItem label="Debian">

</TabItem>
  <TabItem label="Arch">

</TabItem>
  <TabItem label="Fedora">

</TabItem>
  <TabItem label="Gentoo">

**2. Install the Flatpak Runtime**

**3. [Build the .deb of your tauri-app](https://v2.tauri.app/reference/config/#bundleconfig)**

**4. [Create an AppStream MetaInfo file](https://www.freedesktop.org/software/appstream/metainfocreator/#/guiapp)**

**5. Create the flatpak manifest**

**Examples:**

Example 1 (sh):
```sh
sudo apt install flatpak flatpak-builder
```

Example 2 (sh):
```sh
sudo pacman -S --needed flatpak flatpak-builder
```

Example 3 (sh):
```sh
sudo dnf install flatpak flatpak-builder
```

Example 4 (sh):
```sh
sudo emerge --ask \
sys-apps/flatpak \
dev-util/flatpak-builder
```

---

## Update it

**URL:** llms-txt#update-it

**Contents:**
- Adding additional libraries
- Submitting to flathub

flatpak -y --user update <your flatpak id>
shell
git clone --branch=new-pr git@github.com:your_github_username/flathub.git
shell
cd flathub
shell
git checkout -b your_app_name
```

**_5. Add your apps manifest to the branch. Commit your changes, and then push them._**

**_6. Open a pull request against the `new-pr` branch on github_**

**_7. Your app will now enter the review process in which you may be asked to make changes to your project._**

When your pull request is approved then you will receive an invitation to edit your apps repository. From here on you can update your app continuously.

You can read more about this [in the flatpak documentation](https://docs.flatpak.org/en/latest/dependencies.html#bundling)

**Examples:**

Example 1 (unknown):
```unknown
## Adding additional libraries

If your final binary requires more libraries than the default tauri app, you need to add them in your flatpak manifest.
There are two ways to do this. For fast local development, it may work to simply include the already built library file (`.so`) from your local system.
However, this is not recommended for the final build of the flatpak, as your local library file is not built for the flatpak runtime environment.
This can introduce various bugs that can be very hard to find.
Therefore, it is recommended to build the library your program depends on from source inside the flatpak as a build step.

## Submitting to flathub

**_1. Fork The [Flathub Repository](https://github.com/flathub/flathub/fork)_**

**_2. Clone the Fork_**
```

Example 2 (unknown):
```unknown
**_3. Enter the repository_**
```

Example 3 (unknown):
```unknown
**_4. Create a new branch_**
```

---

## WebDriver

**URL:** llms-txt#webdriver

**Contents:**
- System Dependencies
  - Linux
  - Windows
- Example Applications
- Continuous Integration (CI)

[WebDriver] is a standardized interface to interact with web documents primarily intended for automated testing.
Tauri supports the [WebDriver] interface by leveraging the native platform's [WebDriver] server underneath a
cross-platform wrapper [`tauri-driver`]. On desktop, only Windows and Linux are supported due to macOS not having
a WKWebView driver tool available. iOS and Android work through Appium 2, but the process is not currently streamlined.

## System Dependencies

Install the latest [`tauri-driver`] or update an existing installation by running:

Because we currently utilize the platform's native [WebDriver] server, there are some requirements for running
[`tauri-driver`] on supported platforms.

We use `WebKitWebDriver` on Linux platforms. Check if this binary exists already by running the `which WebKitWebDriver` command as
some distributions bundle it with the regular WebKit package. Other platforms may have a separate package for them, such
as `webkit2gtk-driver` on Debian-based distributions.

Make sure to grab the version of [Microsoft Edge Driver] that matches your Windows Edge version that the application is
being built and tested on. This should almost always be the latest stable version on up-to-date Windows installs. If the
two versions do not match, you may experience your WebDriver testing suite hanging while trying to connect.

You can use the [msedgedriver-tool](https://github.com/chippers/msedgedriver-tool) to download the appropriate Microsoft Edge Driver:

The download contains a binary called `msedgedriver.exe`. [`tauri-driver`] looks for that binary in the `$PATH` so make
sure it's either available on the path or use the `--native-driver` option on [`tauri-driver`]. You may want to download this automatically as part of the CI setup process to ensure the Edge, and Edge Driver versions
stay in sync on Windows CI machines. A guide on how to do this may be added at a later date.

## Example Applications

Below are step-by-step guides to show how to create a minimal example application that
is tested with WebDriver.

If you prefer to see the result of the guide and look over a finished minimal codebase that utilizes it, you
can look at https://github.com/tauri-apps/webdriver-example.

import { LinkCard, CardGrid } from '@astrojs/starlight/components';

<CardGrid>
  <LinkCard
    title="Selenium"
    href="/develop/tests/webdriver/example/selenium/"
  />
  <LinkCard
    title="WebdriverIO"
    href="/develop/tests/webdriver/example/webdriverio/"
  />
</CardGrid>

## Continuous Integration (CI)

The above examples also comes with a CI script to test with GitHub Actions, but you may still be interested in the below WebDriver CI guide as it explains the concept a bit more.

<LinkCard
  title="Continuous Integration (CI)"
  href="/develop/tests/webdriver/ci/"
/>

[webdriver]: https://www.w3.org/TR/webdriver/
[`tauri-driver`]: https://crates.io/crates/tauri-driver
[tauri-driver]: https://crates.io/crates/tauri-driver
[microsoft edge driver]: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/

**Examples:**

Example 1 (shell):
```shell
cargo install tauri-driver --locked
```

Example 2 (powershell):
```powershell
cargo install --git https://github.com/chippers/msedgedriver-tool
& "$HOME/.cargo/bin/msedgedriver-tool.exe"
```

---

## Calling Rust from the Frontend

**URL:** llms-txt#calling-rust-from-the-frontend

**Contents:**
- Commands
  - Basic Example
  - Passing Arguments
  - Returning Data
  - Error Handling
  - Async Commands
  - Channels
  - Accessing the WebviewWindow in Commands
  - Accessing an AppHandle in Commands
  - Accessing Managed State

import { Content as FrontendListen } from './_sections/frontend-listen.mdx';

This document includes guides on how to communicate with your Rust code from your application frontend.
To see how to communicate with your frontend from your Rust code, see [Calling the Frontend from Rust].

Tauri provides a [command](#commands) primitive for reaching Rust functions with type safety,
along with an [event system](#event-system) that is more dynamic.

Tauri provides a simple yet powerful `command` system for calling Rust functions from your web app.
Commands can accept arguments and return values. They can also return errors and be `async`.

Commands can be defined in your `src-tauri/src/lib.rs` file.
To create a command, just add a function and annotate it with `#[tauri::command]`:

:::note
Command names must be unique.
:::

:::note
Commands defined in the `lib.rs` file cannot be marked as `pub` due to a limitation in the glue code generation.
You will see an error like this if you mark it as a public function:

You will have to provide a list of your commands to the builder function like so:

Now, you can invoke the command from your JavaScript code:

#### Defining Commands in a Separate Module

If your application defines a lot of components or if they can be grouped,
you can define commands in a separate module instead of bloating the `lib.rs` file.

As an example let's define a command in the `src-tauri/src/commands.rs` file:

:::note
When defining commands in a separate module they should be marked as `pub`.
:::

:::note
The command name is not scoped to the module so they must be unique even between modules.
:::

In the `lib.rs` file, define the module and provide the list of your commands accordingly;

Note the `commands::` prefix in the command list, which denotes the full path to the command function.

The command name in this example is `my_custom_command` so you can still call it by executing `invoke("my_custom_command")`
in your frontend, the `commands::` prefix is ignored.

When using a Rust frontend to call `invoke()` without arguments, you will need to adapt your frontend code as below.
The reason is that Rust doesn't support optional arguments.

### Passing Arguments

Your command handlers can take arguments:

Arguments should be passed as a JSON object with camelCase keys:

:::note
You can use `snake_case` for the arguments with the `rename_all` attribute:

Arguments can be of any type, as long as they implement [`serde::Deserialize`].

The corresponding JavaScript:

Command handlers can return data as well:

The `invoke` function returns a promise that resolves with the returned value:

Returned data can be of any type, as long as it implements [`serde::Serialize`].

#### Returning Array Buffers

Return values that implements [`serde::Serialize`] are serialized to JSON when the response is sent to the frontend.
This can slow down your application if you try to return a large data such as a file or a download HTTP response.
To return array buffers in an optimized way, use [`tauri::ipc::Response`]:

If your handler could fail and needs to be able to return an error, have the function return a `Result`:

If the command returns an error, the promise will reject, otherwise, it resolves:

As mentioned above, everything returned from commands must implement [`serde::Serialize`], including errors.
This can be problematic if you're working with error types from Rust's std library or external crates as most error types do not implement it.
In simple scenarios you can use `map_err` to convert these errors to `String`:

Since this is not very idiomatic you may want to create your own error type which implements `serde::Serialize`.
In the following example, we use the [`thiserror`] crate to help create the error type.
It allows you to turn enums into error types by deriving the `thiserror::Error` trait.
You can consult its documentation for more details.

A custom error type has the advantage of making all possible errors explicit so readers can quickly identify what errors can happen.
This saves other people (and yourself) enormous amounts of time when reviewing and refactoring code later.<br/>
It also gives you full control over the way your error type gets serialized.
In the above example, we simply returned the error message as a string, but you could assign each error a code
so you could more easily map it to a similar looking TypeScript error enum for example:

In your frontend you now get a `{ kind: 'io' | 'utf8', message: string }` error object:

Asynchronous commands are preferred in Tauri to perform heavy work in a manner that doesn't result in UI freezes or slowdowns.

Async commands are executed on a separate async task using [`async_runtime::spawn`].
Commands without the _async_ keyword are executed on the main thread unless defined with _#[tauri::command(async)]_.

**If your command needs to run asynchronously, simply declare it as `async`.**

You need to be careful when creating asynchronous functions using Tauri.
Currently, you cannot simply include borrowed arguments in the signature of an asynchronous function.
Some common examples of types like this are `&str` and `State<'_, Data>`.
This limitation is tracked here: https://github.com/tauri-apps/tauri/issues/2533 and workarounds are shown below.

When working with borrowed types, you have to make additional changes. These are your two main options:

**Option 1**: Convert the type, such as `&str` to a similar type that is not borrowed, such as `String`.
This may not work for all types, for example `State<'_, Data>`.

**Option 2**: Wrap the return type in a [`Result`]. This one is a bit harder to implement, but works for all types.

Use the return type `Result<a, b>`, replacing `a` with the type you wish to return, or `()` if you wish to return `null`, and replacing `b` with an error type to return if something goes wrong, or `()` if you wish to have no optional error returned. For example:

- `Result<String, ()>` to return a String, and no error.
- `Result<(), ()>` to return `null`.
- `Result<bool, Error>` to return a boolean or an error as shown in the [Error Handling](#error-handling) section above.

##### Invoking from JavaScript

Since invoking the command from JavaScript already returns a promise, it works just like any other command:

The Tauri channel is the recommended mechanism for streaming data such as streamed HTTP responses to the frontend.
The following example reads a file and notifies the frontend of the progress in chunks of 4096 bytes:

See the [channels documentation] for more information.

### Accessing the WebviewWindow in Commands

Commands can access the `WebviewWindow` instance that invoked the message:

### Accessing an AppHandle in Commands

Commands can access an `AppHandle` instance:

`AppHandle` and `WebviewWindow` both take a generic parameter `R: Runtime`,
when the `wry` feature is enabled in `tauri` (which is enabled by default),
we default the generic to the `Wry` runtime so you can use it directly,
but if you want to use a different runtime, for example the [mock runtime],
you need to write your functions like this

### Accessing Managed State

Tauri can manage state using the `manage` function on `tauri::Builder`.
The state can be accessed on a command using `tauri::State`:

### Accessing Raw Request

Tauri commands can also access the full [`tauri::ipc::Request`] object which includes the raw body payload and the request headers.

In the frontend you can call invoke() sending a raw request body by providing an ArrayBuffer or Uint8Array on the payload argument,
and include request headers in the third argument:

### Creating Multiple Commands

The `tauri::generate_handler!` macro takes an array of commands. To register
multiple commands, you cannot call invoke_handler multiple times. Only the last
call will be used. You must pass each command to a single call of
`tauri::generate_handler!`.

Any or all of the above features can be combined:

The event system is a simpler communication mechanism between your frontend and the Rust.
Unlike commands, events are not type safe, are always async, cannot return values and only supports JSON payloads.

To trigger a global event you can use the [event.emit] or the [WebviewWindow#emit] functions:

:::note
Global events are delivered to **all** listeners
:::

To trigger an event to a listener registered by a specific webview you can use the [event.emitTo] or the [WebviewWindow#emitTo] functions:

:::note
Webview-specific events are **not** triggered to regular global event listeners.
To listen to **any** event you must provide the `{ target: { kind: 'Any' } }` option to the [event.listen] function,
which defines the listener to act as a catch-all for emitted events:

### Listening to Events

To learn how to listen to events and emit events from your Rust code, see the [Rust Event System documentation].

[Calling the Frontend from Rust]: /develop/calling-frontend/
[`async_runtime::spawn`]: https://docs.rs/tauri/2.0.0/tauri/async_runtime/fn.spawn.html
[`serde::serialize`]: https://docs.serde.rs/serde/trait.Serialize.html
[`serde::deserialize`]: https://docs.serde.rs/serde/trait.Deserialize.html
[`tauri::ipc::Response`]: https://docs.rs/tauri/2.0.0/tauri/ipc/struct.Response.html
[`tauri::ipc::Request`]: https://docs.rs/tauri/2.0.0/tauri/ipc/struct.Request.html
[`thiserror`]: https://github.com/dtolnay/thiserror
[`result`]: https://doc.rust-lang.org/std/result/index.html
[event.emit]: /reference/javascript/api/namespaceevent/#emit
[event.listen]: /reference/javascript/api/namespaceevent/#listen
[WebviewWindow#emit]: /reference/javascript/api/namespacewebviewwindow/#emit
[event.emitTo]: /reference/javascript/api/namespaceevent/#emitto
[WebviewWindow#emitTo]: /reference/javascript/api/namespacewebviewwindow/#emitto
[Rust Event System documentation]: /develop/calling-frontend/#event-system
[channels documentation]: /develop/calling-frontend/#channels
[Calling Rust from the Frontend]: /develop/calling-rust/
[mock runtime]: https://docs.rs/tauri/2.0.0/tauri/test/struct.MockRuntime.html

**Examples:**

Example 1 (unknown):
```unknown
:::note
Command names must be unique.
:::

:::note
Commands defined in the `lib.rs` file cannot be marked as `pub` due to a limitation in the glue code generation.
You will see an error like this if you mark it as a public function:
```

Example 2 (unknown):
```unknown
:::

You will have to provide a list of your commands to the builder function like so:
```

Example 3 (unknown):
```unknown
Now, you can invoke the command from your JavaScript code:
```

Example 4 (unknown):
```unknown
#### Defining Commands in a Separate Module

If your application defines a lot of components or if they can be grouped,
you can define commands in a separate module instead of bloating the `lib.rs` file.

As an example let's define a command in the `src-tauri/src/commands.rs` file:
```

---

## Debian

**URL:** llms-txt#debian

**Contents:**
- Limitations
- Custom Files
- Cross-Compiling for ARM-based Devices

import ShowSolution from '@components/ShowSolution.astro';
import { Steps } from '@astrojs/starlight/components';

The stock Debian package generated by the Tauri bundler has everything you need to ship your application to Debian-based Linux distributions, defining your application's icons, generating a Desktop file, and specifying the dependencies `libwebkit2gtk-4.1-0` and `libgtk-3-0`, along with `libappindicator3-1` if your app uses the system tray.

GUI apps on macOS and Linux do not inherit the `$PATH` from your shell dotfiles (`.bashrc`, `.bash_profile`, `.zshrc`, etc). Check out Tauri's [fix-path-env-rs](https://github.com/tauri-apps/fix-path-env-rs) crate to fix this issue.

Core libraries such as glibc frequently break compatibility with older systems. For this reason, you must build your Tauri application using the oldest base system you intend to support. A relatively old system such as Ubuntu 18.04 is more suited than Ubuntu 22.04, as the binary compiled on Ubuntu 22.04 will have a higher requirement of the glibc version, so when running on an older system, you will face a runtime error like `/usr/lib/libc.so.6: version 'GLIBC_2.33' not found`. We recommend using a Docker container or GitHub Actions to build your Tauri application for Linux.

See the issues [tauri-apps/tauri#1355](https://github.com/tauri-apps/tauri/issues/1355) and [rust-lang/rust#57497](https://github.com/rust-lang/rust/issues/57497), in addition to the [AppImage guide](https://docs.appimage.org/reference/best-practices.html#binaries-compiled-on-old-enough-base-system) for more information.

Tauri exposes a few configurations for the Debian package in case you need more control.

If your app depends on additional system dependencies you can specify them in `tauri.conf.json > bundle > linux > deb`.

To include custom files in the Debian package, you can provide a list of files or folders in `tauri.conf.json > bundle > linux > deb > files`. The configuration object maps the path in the Debian package to the path to the file on your filesystem, relative to the `tauri.conf.json` file. Here's an example configuration:

## Cross-Compiling for ARM-based Devices

This guide covers manual compilation. Check out our [GitHub Action guide](/distribute/pipelines/github/#arm-runner-compilation) for an example workflow that leverages QEMU to build the app. This will be much slower but will also be able to build AppImages.

Manual compilation is suitable when you don't need to compile your application frequently and prefer a one-time setup. The following steps expect you to use a Linux distribution based on Debian/Ubuntu.

1. #### Install Rust targets for your desired architecture
   - For ARMv7 (32-bit): `rustup target add armv7-unknown-linux-gnueabihf`
   - For ARMv8 (ARM64, 64-bit): `rustup target add aarch64-unknown-linux-gnu`

2. #### Install the corresponding linker for your chosen architecture
   - For ARMv7: `sudo apt install gcc-arm-linux-gnueabihf`
   - For ARMv8 (ARM64): `sudo apt install gcc-aarch64-linux-gnu`

3. #### Open or create the file `<project-root>/.cargo/config.toml` and add the following configurations accordingly

4. #### Enable the respective architecture in the package manager
   - For ARMv7: `sudo dpkg --add-architecture armhf`
   - For ARMv8 (ARM64): `sudo dpkg --add-architecture arm64`

5. #### Adjusting Package Sources

On Debian, this step should not be necessary, but on other distributions, you might need to edit /etc/apt/sources.list to include the ARM architecture variant. For example on Ubuntu 22.04 add these lines to the bottom of the file (Remember to replace jammy with the codename of your Ubuntu version):

Then, to prevent issues with the main packages, you have to add the correct main architecture to all other lines the file contained beforehand. For standard 64-bit systems you need to add [arch=amd64], the full file on Ubuntu 22.04 then looks similar to this:

6. #### Update the package information: `sudo apt-get update && sudo apt-get upgrade -y`

7. #### Install the required webkitgtk library for your chosen architecture
   - For ARMv7: `sudo apt install libwebkit2gtk-4.1-dev:armhf`
   - For ARMv8 (ARM64): `sudo apt install libwebkit2gtk-4.1-dev:arm64`

8. #### Install OpenSSL or use a vendored version

This is not always required so you may want to proceed first and check if you see errors like `Failed to find OpenSSL development headers`.
   - Either install the development headers system-wide:
     - For ARMv7: `sudo apt install libssl-dev:armhf`
     - For ARMv8 (ARM64): `sudo apt install libssl-dev:arm64`
   - Or enable the vendor feature for the OpenSSL Rust crate which will affect all other Rust dependencies using the same minor version. You can do so by adding this to the dependencies section in your `Cargo.toml` file:

9. #### Set the `PKG_CONFIG_SYSROOT_DIR` to the appropriate directory based on your chosen architecture
   - For ARMv7: `export PKG_CONFIG_SYSROOT_DIR=/usr/arm-linux-gnueabihf/`
   - For ARMv8 (ARM64): `export PKG_CONFIG_SYSROOT_DIR=/usr/aarch64-linux-gnu/`

10. #### Build the app for your desired ARM version
    - For ARMv7: cargo tauri build --target armv7-unknown-linux-gnueabihf
    - For ARMv8 (ARM64): cargo tauri build --target aarch64-unknown-linux-gnu

Choose the appropriate set of instructions based on whether you want to cross-compile your Tauri application for ARMv7 or ARMv8 (ARM64). Please note that the specific steps may vary depending on your Linux distribution and setup.

**Examples:**

Example 1 (json):
```json
{
  "bundle": {
    "linux": {
      "deb": {
        "files": {
          "/usr/share/README.md": "../README.md", // copies the README.md file to /usr/share/README.md
          "/usr/share/assets": "../assets/" // copies the entire assets directory to /usr/share/assets
        }
      }
    }
  }
}
```

Example 2 (toml):
```toml
[target.armv7-unknown-linux-gnueabihf]
   linker = "arm-linux-gnueabihf-gcc"

   [target.aarch64-unknown-linux-gnu]
   linker = "aarch64-linux-gnu-gcc"
```

Example 3 (unknown):
```unknown
deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-backports main restricted universe multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security multiverse
```

Example 4 (unknown):
```unknown
# See http://help.ubuntu.com/community/UpgradeNotes for how to upgrade to
   # newer versions of the distribution.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy main restricted
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy main restricted

   ## Major bug fix updates produced after the final release of the
   ## distribution.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted

   ## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
   ## team. Also, please note that software in universe WILL NOT receive any
   ## review or updates from the Ubuntu security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy universe
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy universe
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates universe
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-updates universe

   ## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
   ## team, and may not be under a free licence. Please satisfy yourself as to
   ## your rights to use the software. Also, please note that software in
   ## multiverse WILL NOT receive any review or updates from the Ubuntu
   ## security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy multiverse
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy multiverse
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates multiverse

   ## N.B. software from this repository may not have been tested as
   ## extensively as that contained in the main release, although it includes
   ## newer versions of some applications which may provide useful features.
   ## Also, please note that software in backports WILL NOT receive any review
   ## or updates from the Ubuntu security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-backports main restricted universe multiverse
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-backports main restricted universe multiverse

   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security main restricted
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security main restricted
   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security universe
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security universe
   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security multiverse
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security multiverse

   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-backports main restricted universe multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security multiverse
```

---

## Create a Project

**URL:** llms-txt#create-a-project

**Contents:**
- Using `create-tauri-app`
- Manual Setup (Tauri CLI)
- Next Steps

import { Steps } from '@astrojs/starlight/components';

import Cta from '@fragments/cta.mdx';

One thing that makes Tauri so flexible is its ability to work with virtually any frontend framework. We've created the [`create-tauri-app`](https://github.com/tauri-apps/create-tauri-app) utility to help you create a new Tauri project using one of the officially maintained framework templates.

`create-tauri-app` currently includes templates for vanilla (HTML, CSS and JavaScript without a framework), [Vue.js](https://vuejs.org), [Svelte](https://svelte.dev), [React](https://reactjs.org/), [SolidJS](https://www.solidjs.com/), [Angular](https://angular.io/), [Preact](https://preactjs.com/), [Yew](https://yew.rs/), [Leptos](https://github.com/leptos-rs/leptos), and [Sycamore](https://sycamore-rs.netlify.app/). You can also find or add your own community templates and frameworks in the [Awesome Tauri repo](https://github.com/tauri-apps/awesome-tauri).

{/* TODO: redirect to integrate to existing front-end project specific docs */}
Alternatively, you can [add Tauri to an existing project](#manual-setup-tauri-cli) to quickly turn your existing codebase into a Tauri app.

## Using `create-tauri-app`

To get started using `create-tauri-app` run one of the below commands in the folder you'd like to setup your project. If you're not sure which command to use we recommend the Bash command on Linux and macOS and the PowerShell command on Windows.

Follow along with the prompts to choose your project name, frontend language, package manager, and frontend framework, and frontend framework options if applicable.

:::tip[Not sure what to choose?]

We recommend starting with the vanilla template (HTML, CSS, and JavaScript without a frontend framework) to get started. You can always [integrate a frontend framework](/start/frontend/) later.

- Choose which language to use for your frontend: `TypeScript / JavaScript`
- Choose your package manager: `pnpm`
- Choose your UI template: `Vanilla`
- Choose your UI flavor: `TypeScript`

#### Scaffold a new project

1. Choose a name and a bundle identifier (unique-id for your app):
   
2. Select a flavor for your frontend. First the language:
   
3. Select a package manager (if there are multiple available):

Options for **TypeScript / JavaScript**:

4. Select a UI Template and flavor (if there are multiple available):

Options for **Rust**:

Options for **TypeScript / JavaScript**:

Options for **.NET**:

Once completed, the utility reports that the template has been created and displays how to run it using the configured package manager. If it detects missing dependencies on your system, it prints a list of packages and prompts how to install them.

{/* TODO: Can CTA offer to install the deps? */}

#### Start the development server

After `create-tauri-app` has completed, you can navigate into your project's folder, install dependencies, and then use the [Tauri CLI](/reference/cli/) to start the development server:

import CommandTabs from '@components/CommandTabs.astro';

<CommandTabs
  npm="cd tauri-app
    npm install
    npm run tauri dev"
  yarn="cd tauri-app
    yarn install
    yarn tauri dev"
  pnpm="cd tauri-app
    pnpm install
    pnpm tauri dev"
  deno="cd tauri-app
    deno install
    deno task tauri dev"
  bun="cd tauri-app
    bun install
    bun tauri dev
  "
  cargo="cd tauri-app
    cargo tauri dev"
/>

You'll now see a new window open with your app running.

**Congratulations!** You've made your Tauri app! 🚀

## Manual Setup (Tauri CLI)

If you already have an existing frontend or prefer to set it up yourself, you can use the Tauri CLI to initialize the backend for your project separately.

:::note
The following example assumes you are creating a new project. If you've already initialized the frontend of your application, you can skip the first step.
:::

1. Create a new directory for your project and initialize the frontend. You can use plain HTML, CSS, and JavaScript, or any framework you prefer such as Next.js, Nuxt, Svelte, Yew, or Leptos. You just need a way of serving the app in your browser. Just as an example, this is how you would setup a simple Vite app:

<CommandTabs
            npm="mkdir tauri-app
                cd tauri-app
                npm create vite@latest ."
            yarn="mkdir tauri-app
                cd tauri-app
                yarn create vite ."
            pnpm="mkdir tauri-app
                cd tauri-app
                pnpm create vite ."
            deno="mkdir tauri-app
                cd tauri-app
                deno run -A npm:create-vite ."
            bun="mkdir tauri-app
                cd tauri-app
                bun create vite"
        />

2. Then, install Tauri's CLI tool using your package manager of choice. If you are using `cargo` to install the Tauri CLI, you will have to install it globally.

<CommandTabs
            npm="npm install -D @tauri-apps/cli@latest"
            yarn="yarn add -D @tauri-apps/cli@latest"
            pnpm="pnpm add -D @tauri-apps/cli@latest"
            deno="deno add -D npm:@tauri-apps/cli@latest"
            bun="bun add -D @tauri-apps/cli@latest"
            cargo='cargo install tauri-cli --version "^2.0.0" --locked'
        />

3. Determine the URL of your frontend development server. This is the URL that Tauri will use to load your content. For example, if you are using Vite, the default URL is `http://localhost:5173`.

4. In your project directory, initialize Tauri:

<CommandTabs
            npm="npx tauri init"
            yarn="yarn tauri init"
            pnpm="pnpm tauri init"
            deno="deno task tauri init"
            bun="bun tauri init"
            cargo="cargo tauri init"
        />

After running the command it will display a prompt asking you for different options:

This will create a `src-tauri` directory in your project with the necessary Tauri configuration files.

5. Verify your Tauri app is working by running the development server:

<CommandTabs
            npm="npx tauri dev"
            yarn="yarn tauri dev"
            pnpm="pnpm tauri dev"
            deno="deno task tauri dev"
            bun="bun tauri dev"
            cargo="cargo tauri dev"
        />

This command will compile the Rust code and open a window with your web content.

**Congratulations!** You've created a new Tauri project using the Tauri CLI! 🚀

- [Learn about the project layout and what each file does](/start/project-structure/)
- [Add and Configure a Frontend Framework](/start/frontend/)
- [Tauri Command Line Interface (CLI) Reference](/reference/cli/)
- [Learn how to develop your Tauri app](/develop/)
- [Discover additional features to extend Tauri](/plugin/)

**Examples:**

Example 1 (unknown):
```unknown
? Project name (tauri-app) ›
   ? Identifier (com.tauri-app.app) ›
```

Example 2 (unknown):
```unknown
? Choose which language to use for your frontend ›
   Rust  (cargo)
   TypeScript / JavaScript  (pnpm, yarn, npm, bun)
   .NET  (dotnet)
```

Example 3 (unknown):
```unknown
? Choose your package manager ›
   pnpm
   yarn
   npm
   bun
```

Example 4 (unknown):
```unknown
? Choose your UI template ›
   Vanilla
   Yew
   Leptos
   Sycamore
```

---

## Leptos

**URL:** llms-txt#leptos

**Contents:**
- Checklist
- Example Configuration

import { Tabs, TabItem, Steps } from '@astrojs/starlight/components';
import CommandTabs from '@components/CommandTabs.astro';

Leptos is a Rust based web framework. You can read more about Leptos on their [official website](https://leptos.dev/). This guide is accurate as of Leptos version 0.6.

- Use SSG, Tauri doesn't officially support server based solutions.
- Use `serve.ws_protocol = "ws"` so that the hot-reload websocket can connect properly for mobile development.
- Enable `withGlobalTauri` to ensure that Tauri APIs are available in the `window.__TAURI__` variable and can be imported using `wasm-bindgen`.

## Example Configuration

1. ##### Update Tauri configuration

1. ##### Update Trunk configuration

**Examples:**

Example 1 (json):
```json
// src-tauri/tauri.conf.json
   {
     "build": {
       "beforeDevCommand": "trunk serve",
       "devUrl": "http://localhost:1420",
       "beforeBuildCommand": "trunk build",
       "frontendDist": "../dist"
     },
     "app": {
       "withGlobalTauri": true
     }
   }
```

Example 2 (toml):
```toml
// Trunk.toml
   [build]
   target = "./index.html"

   [watch]
   ignore = ["./src-tauri"]

   [serve]
   port = 1420
   open = false
   ws_protocol = "ws"
```

---

## AppImage

**URL:** llms-txt#appimage

**Contents:**
- Limitations
- Multimedia support via GStreamer
- Custom Files
- AppImages for ARM-based devices

`AppImage` is a distribution format that does not rely on the system installed packages and instead bundles all dependencies and files needed by the application. For this reason, the output file is larger but easier to distribute since it is supported on many Linux distributions and can be executed without installation. The user just needs to make the file executable (`chmod a+x MyProject.AppImage`) and can then run it (`./MyProject.AppImage`).

AppImages are convenient, simplifying the distribution process if you cannot make a package targeting the distribution's package manager. Still, you should carefully use it as the file size grows from the 2-6 MB range to 70+ MB.

GUI apps on macOS and Linux do not inherit the `$PATH` from your shell dotfiles (`.bashrc`, `.bash_profile`, `.zshrc`, etc). Check out Tauri's [fix-path-env-rs](https://github.com/tauri-apps/fix-path-env-rs) crate to fix this issue.

Core libraries such as glibc frequently break compatibility with older systems. For this reason, you must build your Tauri application using the oldest base system you intend to support. A relatively old system such as Ubuntu 18.04 is more suited than Ubuntu 22.04, as the binary compiled on Ubuntu 22.04 will have a higher requirement of the glibc version, so when running on an older system, you will face a runtime error like `/usr/lib/libc.so.6: version 'GLIBC_2.33' not found`. We recommend using a Docker container or GitHub Actions to build your Tauri application for Linux.

See the issues [tauri-apps/tauri#1355](https://github.com/tauri-apps/tauri/issues/1355) and [rust-lang/rust#57497](https://github.com/rust-lang/rust/issues/57497), in addition to the [AppImage guide](https://docs.appimage.org/reference/best-practices.html#binaries-compiled-on-old-enough-base-system) for more information.

## Multimedia support via GStreamer

If your app plays audio/video you need to enable `tauri.conf.json > bundle > linux > appimage > bundleMediaFramework`. This will increase the size of the AppImage bundle to include additional gstreamer files needed for media playback. This flag is currently only fully supported on Ubuntu build systems. Make sure that your build system has all the plugins your app may need at runtime.

GStreamer plugins in the `ugly` package are licensed in a way that may make it hard to distribute them as part of your app.

{/* TODO: Add some reference links for gst setup/plugins */}

To include custom files in the AppImage that you do not want to include via Tauri's [`resources` feature](/develop/resources/), you can provide a list of files or folders in `tauri.conf.json > bundle > linux > appimage > files`. The configuration object maps the path in the AppImage to the path to the file on your filesystem, relative to the `tauri.conf.json` file. Here's an example configuration:

Note that the destination paths must currently begin with `/usr/`.

## AppImages for ARM-based devices

:::note[August 2025 Update]
Github has [released](https://github.blog/changelog/2025-08-07-arm64-hosted-runners-for-public-repositories-are-now-generally-available/#get-started) publicly available `ubuntu-22.04-arm` and `ubuntu-24.04-arm` runners. You can use these to build your app with no changes, a typical build should take ~10 minutes.
:::

`linuxdeploy`, the AppImage tooling Tauri uses, currently [does not support cross-compiling] ARM AppImages. This means ARM AppImages can only be built on ARM devices or emulators.

Check out our [GitHub Action guide](/distribute/pipelines/github/#arm-runner-compilation) for an example workflow that leverages QEMU to build the app. Note that this is extremely slow and only recommended in public repositories where Build Minutes are free. In private repositories GitHub's ARM runners should be more cost-efficient and much easier to set up.

[does not support cross-compiling]: https://github.com/linuxdeploy/linuxdeploy/issues/258

---

## name: org.net_mydomain_MyApp.SingleInstance # Remember to change net_mydomain_MyApp to your app ID with "_" instead of "." and "-"

**URL:** llms-txt#name:-org.net_mydomain_myapp.singleinstance-#-remember-to-change-net_mydomain_myapp-to-your-app-id-with-"_"-instead-of-"."-and-"-"

**Contents:**
  - Explanation
- Building
- Testing
- Releasing Manually
- Building automatically

package-repositories:
  - type: apt
    components: [main]
    suites: [noble]
    key-id: 78E1918602959B9C59103100F1831DDAFC42E99D
    url: http://ppa.launchpad.net/snappy-dev/snapcraft-daily/ubuntu

parts:
  build-app:
    plugin: dump
    build-snaps:
      - node/20/stable
      - rustup/latest/stable
    build-packages:
      - libwebkit2gtk-4.1-dev
      - build-essential
      - curl
      - wget
      - file
      - libxdo-dev
      - libssl-dev
      - libayatana-appindicator3-dev
      - librsvg2-dev
      - dpkg
    stage-packages:
      - libwebkit2gtk-4.1-0
      - libayatana-appindicator3-1
    source: .
    override-build: |
      set -eu
      npm install
      npm run tauri build -- --bundles deb
      dpkg -x src-tauri/target/release/bundle/deb/*.deb $SNAPCRAFT_PART_INSTALL/
      sed -i -e "s|Icon=appname|Icon=/usr/share/icons/hicolor/32x32/apps/appname.png|g" $SNAPCRAFT_PART_INSTALL/usr/share/applications/appname.desktop
sh
sudo snapcraft
shell
snap run your-app
shell
snapcraft login # Login with your UbuntuOne credentials
snapcraft upload --release=stable mysnap_latest_amd64.snap
```

## Building automatically

1. On your apps developer page click on the `builds` tab.
2. Click `login with github`.
3. Enter in your repository's details.

**Examples:**

Example 1 (unknown):
```unknown
### Explanation

- The `name` variable defines the name of your app and is required to be set to the name that you have registered earlier.
- The `base` variable defines which core you are using.
- The `version` variable defines the version, and should be updated with each change to the source repository.
- The `apps` section allows you to expose the desktop and binary files to allow the user to run your app.
- The `package-repositories` section allows you to add a package repository to help you satisfy your dependencies.
- `build-packages`/`build-snaps` defines the build dependencies for your snap.
- `stage-packages`/`stage-snaps` defines the runtime dependencies for your snap.
- The `override-build` section runs a series of commands after the sources were pulled.

## Building
```

Example 2 (unknown):
```unknown
## Testing

{/* TODO: This seems to be wrong */}
```

Example 3 (unknown):
```unknown
## Releasing Manually
```

---

## CrabNebula Cloud

**URL:** llms-txt#crabnebula-cloud

**Contents:**
- Distributing with CrabNebula Cloud

## Distributing with CrabNebula Cloud

[CrabNebula](https://crabnebula.dev) is an official Tauri partner providing services and tooling for Tauri applications.
The [CrabNebula Cloud](https://crabnebula.dev/cloud/) is a platform for application distribution that seamlessly integrates with the Tauri updater.

The Cloud offers a Content Delivery Network (CDN) that is capable of shipping your application installers and updates globally while being cost effective and exposing download metrics.

With the CrabNebula Cloud service it is simple to implement multiple release channels, download buttons for your application website and more.

Setting up your Tauri app to use the Cloud is easy: all you need to do is to sign in to the [Cloud website] using your GitHub account, create your organization and application and install its CLI to create a release and upload the Tauri bundles. Additionally, a [GitHub Action] is provided to simplify the process of using the CLI on GitHub workflows.

For more information, see the [CrabNebula Cloud documentation].

[GitHub Action]: https://github.com/crabnebula-dev/cloud-release/
[Cloud website]: https://web.crabnebula.cloud/
[CrabNebula Cloud documentation]: https://docs.crabnebula.dev/cloud/

---

## single-instance-plug:

**URL:** llms-txt#single-instance-plug:

---

## Maintainer:

**URL:** llms-txt#maintainer:

pkgname=<pkgname>-git
pkgver=<pkgver>
pkgrel=1
pkgdesc="Description of your app"
arch=('x86_64' 'aarch64')
url="https://github.com/<user>/<project>"
license=('MIT')
depends=('cairo' 'desktop-file-utils' 'gdk-pixbuf2' 'glib2' 'gtk3' 'hicolor-icon-theme' 'libsoup' 'pango' 'webkit2gtk-4.1')
makedepends=('git' 'openssl' 'appmenu-gtk-module' 'libappindicator-gtk3' 'librsvg' 'cargo' 'pnpm' 'nodejs')
provides=('<pkgname>')
conflicts=('<binname>' '<pkgname>')
source=("git+${url}.git")
sha256sums=('SKIP')

pkgver() {
	cd <project>
	( set -o pipefail
	  git describe --long --abbrev=7 2>/dev/null | sed 's/\([^-]*-g\)/r\1/;s/-/./g' ||
	  printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short=7 HEAD)"
	)
}

prepare() {
	cd <project>
	pnpm install
}

build() {
	cd <project>
	pnpm tauri build -b deb
}

package() {
	cp -a <project>/src-tauri/target/release/bundle/deb/<project>_${pkgver}_*/data/* "${pkgdir}"
}
```

[`async_runtime::spawn`]: https://docs.rs/tauri/2.0.0/tauri/async_runtime/fn.spawn.html
[`serde::serialize`]: https://docs.serde.rs/serde/trait.Serialize.html
[`serde::deserialize`]: https://docs.serde.rs/serde/trait.Deserialize.html
[`thiserror`]: https://github.com/dtolnay/thiserror
[`result`]: https://doc.rust-lang.org/std/result/index.html

---

## Window Menu

**URL:** llms-txt#window-menu

**Contents:**
- Creating a base-level menu
- Listening to events on custom menu items
- Creating a multi-level menu
- Creating predefined menu
- Change menu status

import { Tabs, TabItem } from '@astrojs/starlight/components';

Native application menus can be attached to both to a window or system tray. Available on desktop.

## Creating a base-level menu

To create a base-level native window menu, and attach to a window. You can create various types of menu items including basic items, check items, and separators:

<Tabs>
<TabItem label="JavaScript">

Use the [`Menu.new`] static function to create a window menu:

<TabItem label="Rust">

## Listening to events on custom menu items

Each custom menu item triggers an event when clicked. Use the `on_menu_event` API to handle them.

<Tabs>
<TabItem label="JavaScript">

<TabItem label="Rust">

## Creating a multi-level menu

Multi-level menus allow you to group menu items under categories like "File," "Edit," etc. These will appear as part of the application window for Windows or Linux, or in the menu bar on MacOS.

**Note:** When using submenus on MacOS, all items must be grouped under a submenu. Top-level items will be ignored. Additionally, the first submenu will be placed under the application's about menu by default, regardless of the `text` label. You should include a submenu as the first entry (say, an "About" submenu) to fill this space.

:::note
Icon support for submenus is available since Tauri 2.8.0.
:::

<Tabs>
<TabItem label="JavaScript">

<TabItem label="Rust">

Note that you need to enable `image-ico` or `image-png` feature to use this API:

## Creating predefined menu

To use built-in (native) menu items that has predefined behavior by the operating system or Tauri:

<Tabs>
<TabItem label="JavaScript">

<TabItem label="Rust">

For more preset capabilities, please refer to the documentation [`PredefinedMenuItem`].

:::tip
The menu builder has dedicated methods to add each predefined menu item so you can call `.copy()` instead of `.item(&PredefinedMenuItem::copy(app, None)?)`.
:::

## Change menu status

If you want to change the status of the menu, such as text, icon, or check status, you can `set_menu` again:

<Tabs>
<TabItem label="JavaScript">

<TabItem label="Rust">

[`PredefinedMenuItem`]: https://docs.rs/tauri/latest/tauri/menu/struct.PredefinedMenuItem.html
[`Menu.new`]: https://v2.tauri.app/reference/javascript/api/namespacemenu/#new-2

**Examples:**

Example 1 (javascript):
```javascript
import { Menu } from '@tauri-apps/api/menu';

const menu = await Menu.new({
  items: [
    {
      id: 'quit',
      text: 'Quit',
      action: () => {
        console.log('quit pressed');
      },
    },
    {
      id: 'check_item',
      text: 'Check Item',
      checked: true,
    },
    {
      type: 'Separator',
    },
    {
      id: 'disabled_item',
      text: 'Disabled Item',
      enabled: false,
    },
    {
      id: 'status',
      text: 'Status: Processing...',
    },
  ],
});

// If a window was not created with an explicit menu or had one set explicitly,
// this menu will be assigned to it.
menu.setAsAppMenu().then(async (res) => {
  console.log('menu set success', res);

  // Update individual menu item text
  const statusItem = await menu.get('status');
  if (statusItem) {
    await statusItem.setText('Status: Ready');
  }
});
```

Example 2 (rust):
```rust
use tauri::menu::MenuBuilder;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let menu = MenuBuilder::new(app)
                .text("open", "Open")
                .text("close", "Close")
                .check("check_item", "Check Item")
                .separator()
                .text("disabled_item", "Disabled Item")
                .text("status", "Status: Processing...")
                .build()?;

            app.set_menu(menu.clone())?;

            // Update individual menu item text
            menu
                .get("status")
                .unwrap()
                .as_menuitem_unchecked()
                .set_text("Status: Ready")?;

            Ok(())
        })
        .run(tauri::generate_context!());
}
```

Example 3 (javascript):
```javascript
import { Menu } from '@tauri-apps/api/menu';

const menu = await Menu.new({
  items: [
    {
      id: 'Open',
      text: 'open',
      action: () => {
        console.log('open pressed');
      },
    },
    {
      id: 'Close',
      text: 'close',
      action: () => {
        console.log('close pressed');
      },
    },
  ],
});

await menu.setAsAppMenu();
```

Example 4 (rust):
```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use tauri::menu::{MenuBuilder};

fn main() {
  tauri::Builder::default()
        .setup(|app| {
            let menu = MenuBuilder::new(app)
                .text("open", "Open")
                .text("close", "Close")
                .build()?;

            app.set_menu(menu)?;

            app.on_menu_event(move |app_handle: &tauri::AppHandle, event| {

                println!("menu event: {:?}", event.id());

                match event.id().0.as_str() {
                    "open" => {
                        println!("open event");
                    }
                    "close" => {
                        println!("close event");
                    }
                    _ => {
                        println!("unexpected menu event");
                    }
                }
            });

            Ok(())
        })
}
```

---

## App Icons

**URL:** llms-txt#app-icons

**Contents:**
- Command Usage
- Creating icons manually
  - Android
  - iOS

{/* TODO: More platform specific explanations like macOS requiring padding in the icon (waiting for https://github.com/tauri-apps/tauri/pull/11037) */}

import CommandTabs from '@components/CommandTabs.astro';

Tauri ships with a default iconset based on its logo. This is NOT what you want when you ship your application. To remedy this common situation, Tauri provides the `icon` command that will take an input file (`"./app-icon.png"` by default) and create all the icons needed for the various platforms.

:::note[Note on filetypes]

- `icon.icns` = macOS
- `icon.ico` = Windows
- `*.png` = Linux
- `Square*Logo.png` & `StoreLogo.png` = Currently unused but intended for AppX/MS Store targets.

Some icon types may be used on platforms other than those listed above (especially `png`). Therefore we recommend including all icons even if you intend to only build for a subset of platforms.

<CommandTabs
  npm="npm run tauri icon"
  yarn="yarn tauri icon"
  pnpm="pnpm tauri icon"
  cargo="cargo tauri icon"
  deno="deno task tauri icon"
/>

The **desktop** icons will be placed in your `src-tauri/icons` folder by default, where they will be included in your built app automatically. If you want to source your icons from a different location, you can edit this part of the `tauri.conf.json` file:

The **mobile** icons will be placed into the Xcode and Android Studio projects directly!

## Creating icons manually

If you prefer to build these icons yourself, for example if you want to have a simpler design for small sizes or because you don't want to depend on the CLI's internal image resizing, you must make sure your icons meet some requirements:

- `icon.icns`: The required layer sizes and names for the [`icns`] file are described [in the Tauri repo]
- `icon.ico`: The [`ico`] file must include layers for 16, 24, 32, 48, 64 and 256 pixels. For an optimal display of the ICO image _in development_, the 32px layer should be the first layer.
- `png`: The requirements for the png icons are: width == height, RGBA (RGB + Transparency), and 32bit per pixel (8bit per channel). Commonly expected sizes on desktop are 32, 128, 256, and 512 pixels. We recommend to at least match the output of `tauri icon`: `32x32.png`, `128x128.png`, `128x128@2x.png`, and `icon.png`.

On Android you will need png icons with the same requirements but in different sizes. They will also need to be placed directly in the Android Studio project:

- `src-tauri/gen/android/app/src/main/res/`
  - `mipmap-hdpi/`
    - `ic_launcher.png` & `ic_launcher_round.png`: 49x49px
    - `ic_launcher_foreground.png`: 162x162px
  - `mipmap-mdpi/`
    - `ic_launcher.png` & `ic_launcher_round.png`: 48x48px
    - `ic_launcher_foreground.png`: 108x108px
  - `mipmap-xhdpi/`
    - `ic_launcher.png` & `ic_launcher_round.png`: 96x96px
    - `ic_launcher_foreground.png`: 216x216px
  - `mipmap-xxhdpi/`
    - `ic_launcher.png` & `ic_launcher_round.png`: 144x144px
    - `ic_launcher_foreground.png`: 324x324px
  - `mipmap-xxxhdpi/`
    - `ic_launcher.png` & `ic_launcher_round.png`: 192x192px
    - `ic_launcher_foreground.png`: 432x432px

If `tauri icon` cannot be used, we recommend checking out Android Studio's [Image Asset Studio] instead.

On iOS you will need png icons with the same requirements but **without transparency** and in different sizes. They will also need to be placed directly in the Xcode project into `src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/`. The following icons are expected:

- 20px in 1x, 2x, 3x, with an extra icon
- 29px in 1x, 2x, 3x, with an extra icon
- 40px in 1x, 2x, 3x, with an extra icon
- 60px in 2x, 3x
- 76px in 1x, 2x
- 83.5px in 2x
- 512px in 2x saved as `AppIcon-512@2x.png`

The file names are in the format of `AppIcon-{size}x{size}@{scaling}{extra}.png`. For the 20px icons this means you need icons in sizes 20x20, 40x40 and 60x60 named as `AppIcon-20x20@1x.png`, `AppIcon-20x20@2x.png`, `AppIcon-20x20@3x.png` and `2x` saved additionally as `AppIcon-20x20@2x-1.png` ("extra icon").

[in the tauri repo]: https://github.com/tauri-apps/tauri/blob/1.x/tooling/cli/src/helpers/icns.json
[`icns`]: https://en.wikipedia.org/wiki/Apple_Icon_Image_format
[`ico`]: https://en.wikipedia.org/wiki/ICO_(file_format)
[image asset studio]: https://developer.android.com/studio/write/create-app-icons

**Examples:**

Example 1 (console):
```console
> pnpm tauri icon --help

Generate various icons for all major platforms

Usage: pnpm run tauri icon [OPTIONS] [INPUT]

Arguments:
  [INPUT]  Path to the source icon (squared PNG or SVG file with transparency) [default: ./app-icon.png]

Options:
  -o, --output <OUTPUT>        Output directory. Default: 'icons' directory next to the tauri.conf.json file
  -v, --verbose...             Enables verbose logging
  -p, --png <PNG>              Custom PNG icon sizes to generate. When set, the default icons are not generated
      --ios-color <IOS_COLOR>  The background color of the iOS icon - string as defined in the W3C's CSS Color Module Level 4 <https://www.w3.org/TR/css-color-4/> [default: #fff]
  -h, --help                   Print help
  -V, --version                Print version
```

Example 2 (json):
```json
{
  "bundle": {
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  }
}
```

---

## Continuous Integration

**URL:** llms-txt#continuous-integration

**Contents:**
- GitHub Actions

It is possible to run [WebDriver] tests with [`tauri-driver`] on your CI. The following example uses the [WebdriverIO] example we [previously built together] and
GitHub Actions.

The WebDriver tests are executed on Linux by creating a fake display.
Some CI systems such as GitHub Actions also support running WebDriver tests on Windows.

The following GitHub Actions assumes:

1. The Tauri application is in the `src-tauri` folder.
2. The [WebDriverIO] test runner is in the `e2e-tests` directory and runs when `yarn test` is used in that directory.

```yaml title=".github/workflows/webdriver.yml"

---

## Isolation Pattern

**URL:** llms-txt#isolation-pattern

**Contents:**
- Why
- When
- How
  - Approximate Steps of an IPC Message
  - Performance Implications
  - Limitations
- Recommendations
- Creating the Isolation Application
- Configuration

The Isolation pattern is a way to intercept and modify Tauri API messages sent by the frontend before they get to Tauri Core, all with JavaScript. The secure JavaScript code that is injected by the Isolation pattern is referred to as the Isolation application.

The Isolation pattern's purpose is to provide a mechanism for developers to help protect their application from unwanted or malicious frontend calls to Tauri Core. The need for the Isolation pattern rose out of threats coming from untrusted content running on the frontend, a common case for applications with many dependencies. See [Security: Threat Models] for a list of many sources of threats that an application may see.

The largest threat model described above that the Isolation pattern was designed in mind was Development Threats. Not only do many frontend build-time tools consist of many dozen (or hundreds) of often deeply-nested dependencies, but a complex application may also have a large amount of (also often deeply-nested) dependencies that are bundled into the final output.

Tauri highly recommends using the isolation pattern whenever it can be used. Because the Isolation application intercepts _**all**_ messages from the frontend, it can _always_ be used.

Tauri also strongly suggests locking down your application whenever you use external Tauri APIs. As the developer, you can utilize the secure Isolation application to try and verify IPC inputs, to make sure they are within some expected parameters. For example, you may want to check that a call to read or write a file is not trying to access a path outside your application's expected locations. Another example is making sure that a Tauri API HTTP fetch call is only setting the Origin header to what your application expects it to be.

That said, it intercepts _**all**_ messages from the frontend, so it will even work with always-on APIs such as [Events]. Since some events may cause your own rust code to perform actions, the same sort of validation techniques can be used with them.

The Isolation pattern is all about injecting a secure application in between your frontend and Tauri Core to intercept and modify incoming IPC messages. It does this by using the sandboxing feature of `<iframe>`s to run the JavaScript securely alongside the main frontend application. Tauri enforces the Isolation pattern while loading the page, forcing all IPC calls to Tauri Core to instead be routed through the sandboxed Isolation application first. Once the message is ready to be passed to Tauri Core, it is encrypted using the browser's [SubtleCrypto] implementation and passed back to the main frontend application. Once there, it is directly passed to Tauri Core, where it is then decrypted and read like normal.

To ensure that someone cannot manually read the keys for a specific version of your application and use that to modify the messages after being encrypted, new keys are generated each time your application is run.

### Approximate Steps of an IPC Message

To make it easier to follow, here's an ordered list with the approximate steps an IPC message will go through when being sent to Tauri Core with the Isolation pattern:

1. Tauri's IPC handler receives a message
2. IPC handler -> Isolation application
3. `[sandbox]` Isolation application hook runs and potentially modifies the message
4. `[sandbox]` Message is encrypted with AES-GCM using a runtime-generated key
5. `[encrypted]` Isolation application -> IPC handler
6. `[encrypted]` IPC handler -> Tauri Core

_Note: Arrows (->) indicate message passing._

### Performance Implications

Because encryption of the message does occur, there are additional overhead costs compared to the [Brownfield pattern], even if the secure Isolation application doesn't do anything. Aside from performance-sensitive applications (who likely have a carefully-maintained and small set of dependencies, to keep the performance adequate), most applications should not notice the runtime costs of encrypting/decrypting the IPC messages, as they are relatively small and AES-GCM is relatively fast. If you are unfamiliar with AES-GCM, all that is relevant in this context is that it's the only authenticated mode algorithm included in [SubtleCrypto] and that you probably already use it every day under the hood with [TLS][transport_layer_security].

There is also a cryptographically secure key generated once each time the Tauri application is started. It is not generally noticeable if the system already has enough entropy to immediately return enough random numbers, which is extremely common for desktop environments. If running in a headless environment to perform some [integration testing with WebDriver] then you may want to install some sort of entropy-generating service such as `haveged` if your operating system does not have one included. <sup>Linux 5.6 (March 2020) now includes entropy generation using speculative execution.</sup>

There are a few limitations in the Isolation pattern that arose out of platform inconsistencies. The most significant limitation is due to external files not loading correctly inside sandboxed `<iframes>` on Windows. Because of this, we have implemented a simple script inlining step during build time that takes the content of scripts relative to the Isolation application and injects them inline. This means that typical bundling or simple including of files like `<script src="index.js"></script>` still works properly, but newer mechanisms such as ES Modules will _not_ successfully load.

Because the point of the Isolation application is to protect against Development Threats, we highly recommend keeping your Isolation application as simple as possible. Not only should you strive to keep dependencies of your isolation application minimal, but you should also consider keeping its required build steps minimal. This would allow you to not need to worry about supply chain attacks against your Isolation application on top of your frontend application.

## Creating the Isolation Application

In this example, we will make a small hello-world style Isolation application and hook it up to an imaginary existing Tauri application. It will do no verification of the messages passing through it, only print the contents to the WebView console.

For the purposes of this example, let's imagine we are in the same directory as `tauri.conf.json`. The existing Tauri application has its `frontendDist` set to `../dist`.

`../dist-isolation/index.html`:

`../dist-isolation/index.js`:

Now, all we need to do is set up our `tauri.conf.json` [configuration](#configuration) to use the Isolation pattern, and have just bootstrapped to the Isolation pattern from the [Brownfield pattern].

Let's assume that our main frontend `frontendDist` is set to `../dist`. We also output our Isolation application to `../dist-isolation`.

[transport_layer_security]: https://en.wikipedia.org/wiki/Transport_Layer_Security
[security: threat models]: /security/lifecycle/
[events]: /reference/javascript/api/namespaceevent/
[subtlecrypto]: https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto
[brownfield pattern]: /concept/inter-process-communication/brownfield/
[integration testing with webdriver]: /develop/tests/webdriver/

**Examples:**

Example 1 (html):
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Isolation Secure Script</title>
  </head>
  <body>
    <script src="index.js"></script>
  </body>
</html>
```

Example 2 (javascript):
```javascript
window.__TAURI_ISOLATION_HOOK__ = (payload) => {
  // let's not verify or modify anything, just print the content from the hook
  console.log('hook', payload);
  return payload;
};
```

Example 3 (json):
```json
{
  "build": {
    "frontendDist": "../dist"
  },
  "app": {
    "security": {
      "pattern": {
        "use": "isolation",
        "options": {
          "dir": "../dist-isolation"
        }
      }
    }
  }
}
```

---

## Embedding Additional Files

**URL:** llms-txt#embedding-additional-files

**Contents:**
- Configuration
- Resolve resource file paths
  - Path syntax
  - Android
- Reading resource files
  - Rust
  - JavaScript
- Permissions
  - Examples

import { Tabs, TabItem } from '@astrojs/starlight/components';

You may need to include additional files in your application bundle that aren't part of your frontend (your `frontendDist`) directly or which are too big to be inlined into the binary. We call these files `resources`.

To bundle the files of your choice, add the `resources` property to the `bundle` object in your `tauri.conf.json` file.

To include a list of files:

<Tabs syncKey="explanation">
<TabItem label="Syntax">

</TabItem>
<TabItem label="Explanation">

The bundled files will be in `$RESOURCES/` with the original directory structure preserved,
for example: `./path/to/some-file.txt` -> `$RESOURCE/path/to/some-file.txt`

To fine control where the files will get copied to, use a map instead:

<Tabs syncKey="explanation">
<TabItem label="Syntax">

</TabItem>
<TabItem label="Explanation">

To learn about where `$RESOURCE` resolves to on each platforms, see the documentation of [`resource_dir`]

<details>
<summary>Source path syntax</summary>

In the following explanations "target resource directory" is either the value after the colon in the object notation, or a reconstruction of the original file paths in the array notation.

- `"dir/file.txt"`: copies the `file.txt` file into the target resource directory.
- `"dir/"`: copies all files **and directories** _recursively_ into the target resource directory. Use this if you also want to preserve the file system structure of your files and directories.
- `"dir/*"`: copies all files in the `dir` directory _non-recursively_ (sub-directories will be ignored) into the target resource directory.
- `"dir/**`: throws an error because `**` only matches directories and therefore no files can be found.
- `"dir/**/*"`: copies all files in the `dir` directory _recursively_ (all files in `dir/` and all files in all sub-directories) into the target resource directory.
- `"dir/**/**`: throws an error because `**` only matches directories and therefore no files can be found.

## Resolve resource file paths

To resolve the path for a resource file, instead of manually calculating the path, use the following APIs

<Tabs syncKey="lang">
<TabItem label="Rust">

On the Rust side, you need an instance of the [`PathResolver`] which you can get from [`App`] and [`AppHandle`],
then call [`PathResolver::resolve`]:

To use it in a command:

</TabItem>
<TabItem label="JavaScript">

To resolve the path in JavaScript, use [`resolveResource`]:

The path in the API calls can be either a normal relative path like `folder/json_file.json` that resolves to `$RESOURCE/folder/json_file.json`,
or a paths like `../relative/folder/toml_file.toml` that resolves to `$RESOURCE/_up_/relative/folder/toml_file.toml`,
these APIs use the same rules as you write `tauri.conf.json > bundle > resources`, for example:

Currently the resources are stored in the APK as assets so the return value of those APIs are not normal file system paths,
we use a special URI prefix `asset://localhost/` here that can be used with the [`fs` plugin],
with that, you can read the files through [`FsExt::fs`] like this:

If you want or must have the resource files to be on a real file system, copy the contents out manually through the [`fs` plugin]

## Reading resource files

In this example we want to bundle additional i18n json files like this:

On the Rust side, you need an instance of the [`PathResolver`] which you can get from [`App`] and [`AppHandle`]:

For the JavaScript side, you can either use a command like the one above and call it through `await invoke('hello')` or access the files using the [`fs` plugin].

When using the [`fs` plugin], in addition to the [basic setup], you'll also need to configure the access control list to enable any plugin APIs you need as well as the permissions to access the `$RESOURCE` folder:

:::note
Here we use `fs:allow-resource-read-recursive` to allow for full recursive read access to the complete `$RESOURCE` folder, files, and subdirectories.
For more information, read [Scope Permissions] for other options, or [Scopes] for more fine-grained control.
:::

Since we replace `../` to `_up_` in relative paths and the root to `_root_` in abosolute paths when using a list,
those files will be in sub folders inside the resource directory,
to allow those paths in Tauri's [permission system](/security/capabilities/),
use `$RESOURCE/**/*` to allow recursive access to those files

With a file bundled like this:

To use it with the [`fs` plugin]:

To use it with the [`opener` plugin]:

[`resource_dir`]: https://docs.rs/tauri/latest/tauri/path/struct.PathResolver.html#method.resource_dir
[`pathresolver`]: https://docs.rs/tauri/latest/tauri/path/struct.PathResolver.html
[`PathResolver::resolve`]: https://docs.rs/tauri/latest/tauri/path/struct.PathResolver.html#method.resolve
[`resolveResource`]: https://tauri.app/reference/javascript/api/namespacepath/#resolveresource
[`app`]: https://docs.rs/tauri/latest/tauri/struct.App.html
[`apphandle`]: https://docs.rs/tauri/latest/tauri/struct.AppHandle.html
[`fs` plugin]: /plugin/file-system/
[`FsExt::fs`]: https://docs.rs/tauri-plugin-fs/latest/tauri_plugin_fs/trait.FsExt.html#tymethod.fs
[basic setup]: /plugin/file-system/#setup
[Scope Permissions]: /plugin/file-system/#scopes
[scopes]: /plugin/file-system/#scopes
[`opener` plugin]: /plugin/opener/

**Examples:**

Example 1 (unknown):
```unknown
</TabItem>
<TabItem label="Explanation">
```

Example 2 (unknown):
```unknown
</TabItem>
</Tabs>

The bundled files will be in `$RESOURCES/` with the original directory structure preserved,
for example: `./path/to/some-file.txt` -> `$RESOURCE/path/to/some-file.txt`

To fine control where the files will get copied to, use a map instead:

<Tabs syncKey="explanation">
<TabItem label="Syntax">
```

Example 3 (unknown):
```unknown
</TabItem>
<TabItem label="Explanation">
```

Example 4 (unknown):
```unknown
</TabItem>
</Tabs>

To learn about where `$RESOURCE` resolves to on each platforms, see the documentation of [`resource_dir`]

<details>
<summary>Source path syntax</summary>

In the following explanations "target resource directory" is either the value after the colon in the object notation, or a reconstruction of the original file paths in the array notation.

- `"dir/file.txt"`: copies the `file.txt` file into the target resource directory.
- `"dir/"`: copies all files **and directories** _recursively_ into the target resource directory. Use this if you also want to preserve the file system structure of your files and directories.
- `"dir/*"`: copies all files in the `dir` directory _non-recursively_ (sub-directories will be ignored) into the target resource directory.
- `"dir/**`: throws an error because `**` only matches directories and therefore no files can be found.
- `"dir/**/*"`: copies all files in the `dir` directory _recursively_ (all files in `dir/` and all files in all sub-directories) into the target resource directory.
- `"dir/**/**`: throws an error because `**` only matches directories and therefore no files can be found.

</details>

## Resolve resource file paths

To resolve the path for a resource file, instead of manually calculating the path, use the following APIs

<Tabs syncKey="lang">
<TabItem label="Rust">

On the Rust side, you need an instance of the [`PathResolver`] which you can get from [`App`] and [`AppHandle`],
then call [`PathResolver::resolve`]:
```

---

## macOS Application Bundle

**URL:** llms-txt#macos-application-bundle

**Contents:**
- File structure
- Native configuration
  - Info.plist localization
- Entitlements
- Minimum system version
- Including macOS frameworks
- Adding custom files

import CommandTabs from '@components/CommandTabs.astro';

An application bundle is the package format that is executed on macOS. It is a simple directory that includes everything your application requires for successful operation,
including your app executable, resources, the Info.plist file and other files such as macOS frameworks.

To package your app as a macOS application bundle you can use the Tauri CLI and run the `tauri build` command in a Mac computer:

<CommandTabs
  npm="npm run tauri build -- --bundles app"
  yarn="yarn tauri build --bundles app"
  pnpm="pnpm tauri build --bundles app"
  deno="deno task tauri build --bundles app"
  bun="bun tauri build --bundles app"
  cargo="cargo tauri build --bundles app"
/>

GUI apps on macOS and Linux do not inherit the `$PATH` from your shell dotfiles (`.bashrc`, `.bash_profile`, `.zshrc`, etc). Check out Tauri's [fix-path-env-rs](https://github.com/tauri-apps/fix-path-env-rs) crate to fix this issue.

The macOS app bundle is a directory with the following structure:

See the [official documentation](https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/BundleTypes/BundleTypes.html) for more information.

## Native configuration

The app bundle is configured by the `Info.plist` file, which includes key-value pairs with your app identity and configuration values read by macOS.

Tauri automatically configures the most important properties such as your app binary name, version. bundle identifier, minimum system version and more.

To extend the configuration file, create an `Info.plist` file in the `src-tauri` folder and include the key-pairs you desire:

This `Info.plist` file is merged with the values generated by the Tauri CLI. Be careful when overwriting default values such as application version as they might conflict with other configuration values
and introduce unexpected behavior.

See the [official Info.plist documentation] for more information.

### Info.plist localization

The `Info.plist` file by itself only supports a single language, typically English. If you want to support multiple languages, you can create `InfoPlist.strings` files for each additional language. Each file belongs in its own language specific `lproj` directory in the `Resources` directory in the application bundle.

To bundle these files automatically you can leverage Tauri's [resources] feature. To do that, create a file structure in your project following this pattern:

While the `infoplist` directory name can be chosen freely, as long as you update it in the resources config below, the `lproj` directories must follow the `<lang-code>.lproj` naming and the string catalogue files must be named `InfoPlist.strings` (capital i and p). For most cases the language code should be a two letter code following [BCP 47].

For the `Info.plist` example shown above, the `de.lproj > InfoPlist.strings` file could look like this:

Lastly, make Tauri pick up these files by using the resources feature mentioned above:

An entitlement is a special Apple configuration key-value pair that acts as a right or privilege that grants your app particular capabilities,
such as act as the user's default email client and using the App Sandbox feature.

Entitlements are applied when your application is signed. See the [code signing documentation] for more information.

To define the entitlements required by your application, you must create the entitlements file and configure Tauri to use it.

1. Create a `Entitlements.plist` file in the `src-tauri` folder and configure the key-value pairs you app requires:

2. Configure Tauri to use the Entitlements.plist file:

See the [official documentation](https://developer.apple.com/documentation/bundleresources/entitlements) for more information.

## Minimum system version

By default your Tauri application supports macOS 10.13 and above. If you are using an API that requires a newer macOS system and want to enforce that requirement in your app bundle,
you can configure the [`tauri.conf.json > bundle > macOS > minimumSystemVersion`] value:

## Including macOS frameworks

If your application requires additional macOS frameworks to run, you can list them in the [`tauri.conf.json > bundle > macOS > frameworks`] configuration.
The frameworks list can include either system or custom frameworks and dylib files.

- To reference a system framework you can just use its name (without the .framework extension) instead of absolute path
- System frameworks must exist in either the `$HOME/Library/Frameworks`, `/Library/Frameworks/`, or `/Network/Library/Frameworks/`
- To reference local frameworks and dylib files you must use the complete path to the framework, relative to the `src-tauri` directory

## Adding custom files

You can use the [`tauri.conf.json > bundle > macOS > files`] configuration to add custom files to your application bundle,
which maps the destination path to its source relative to the `tauri.conf.json` file.
The files are added to the `<product-name>.app/Contents` folder.

In the above example, the `profile-name.provisionprofile` file is copied to `<product-name>.app/Contents/embedded.provisionprofile`
and the `docs/index.md` file is copied to `<product-name>.app/Contents/SharedSupport/docs.md`.

[`tauri.conf.json > bundle > macOS > frameworks`]: /reference/config/#frameworks-1
[`tauri.conf.json > bundle > macOS > files`]: /reference/config/#files-2
[`tauri.conf.json > bundle > resources`]: /reference/config/#resources
[official Info.plist documentation]: https://developer.apple.com/documentation/bundleresources/information_property_list
[code signing documentation]: /distribute/sign/macos/
[`tauri.conf.json > bundle > macOS > minimumSystemVersion`]: /reference/config/#minimumsystemversion
[resources]: /develop/resources/
[BCP 47]: https://www.rfc-editor.org/rfc/bcp/bcp47.txt

**Examples:**

Example 1 (unknown):
```unknown
├── <productName>.app
│   ├── Contents
│   │   ├── Info.plist
│   │   ├── ...additional files from [`tauri.conf.json > bundle > macOS > files`]
│   ├── MacOS
│   │   ├── <app-name> (app executable)
│   ├── Resources
│   │   ├── icon.icns (app icon)
│   │   ├── ...resources from [`tauri.conf.json > bundle > resources`]
│   ├── _CodeSignature (codesign information generated by Apple)
│   ├── Frameworks
│   ├── PlugIns
│   ├── SharedSupport
```

Example 2 (unknown):
```unknown
This `Info.plist` file is merged with the values generated by the Tauri CLI. Be careful when overwriting default values such as application version as they might conflict with other configuration values
and introduce unexpected behavior.

See the [official Info.plist documentation] for more information.

### Info.plist localization

The `Info.plist` file by itself only supports a single language, typically English. If you want to support multiple languages, you can create `InfoPlist.strings` files for each additional language. Each file belongs in its own language specific `lproj` directory in the `Resources` directory in the application bundle.

To bundle these files automatically you can leverage Tauri's [resources] feature. To do that, create a file structure in your project following this pattern:
```

Example 3 (unknown):
```unknown
While the `infoplist` directory name can be chosen freely, as long as you update it in the resources config below, the `lproj` directories must follow the `<lang-code>.lproj` naming and the string catalogue files must be named `InfoPlist.strings` (capital i and p). For most cases the language code should be a two letter code following [BCP 47].

For the `Info.plist` example shown above, the `de.lproj > InfoPlist.strings` file could look like this:
```

Example 4 (unknown):
```unknown
Lastly, make Tauri pick up these files by using the resources feature mentioned above:
```

---

## src-tauri/Cargo.toml

**URL:** llms-txt#src-tauri/cargo.toml

**Contents:**
  - References
- Remove Unused Commands

[profile.dev]
incremental = true # Compile your binary in smaller steps.
rustflags = ["-Zthreads=8"] # Better compile performance.

[profile.release]
codegen-units = 1 # Allows LLVM to perform better optimization.
lto = true # Enables link-time-optimizations.
opt-level = "s" # Prioritizes small binary size. Use `3` if you prefer speed.
panic = "abort" # Higher performance by disabling panic handlers.
strip = true # Ensures debug symbols are removed.
trim-paths = "all" # Removes potentially privileged information from your binaries.
rustflags = ["-Cdebuginfo=0", "-Zthreads=8"] # Better compile performance.
json title=tauri.conf.json
{
  "build": {
    "removeUnusedCommands": true
  }
}
```

to remove commands that're never allowed in your capability files (ACL), so you don't have to pay for what you don't use

:::tip
To maximize the benefit of this, only include commands that you use in the ACL instead of using `defaults`s
:::

:::note
This feature requires `tauri@2.4`, `tauri-build@2.1`, `tauri-plugin@2.1` and `tauri-cli@2.4`
:::

:::note
This won't be accounting for dynamically added ACLs at runtime so make sure to check it when using this
:::

<details>
<summary>How does it work under the hood?</summary>

`tauri-cli` will communicate with `tauri-build` and the build script of `tauri`, `tauri-plugin` through an environment variable
and let them generate a list of allowed commands from the ACL,
this will then be used by the `generate_handler` macro to remove unused commands based on that

An internal detail is this environment variable is currently `REMOVE_UNUSED_COMMANDS`,
and it's set to project's directory, usually the `src-tauri` directory, this is used for the build scripts to find the capability files,
and although it's not encouraged, you can still set this environment variable yourself if you can't or don't want to use `tauri-cli` to get this to work
(**do note that as this is an implementation detail, we don't guarantee the stability of it**)

**Examples:**

Example 1 (unknown):
```unknown
</TabItem>
</Tabs>

### References

:::note
This is not a complete reference over all available options, merely the ones that we'd like to draw extra attention to.
:::

- [incremental:](https://doc.rust-lang.org/cargo/reference/profiles.html#incremental) Compile your binary in smaller steps.
- [codegen-units:](https://doc.rust-lang.org/cargo/reference/profiles.html#codegen-units) Speeds up compile times at the cost of compile time optimizations.
- [lto:](https://doc.rust-lang.org/cargo/reference/profiles.html#lto) Enables link time optimizations.
- [opt-level:](https://doc.rust-lang.org/cargo/reference/profiles.html#opt-level) Determines the focus of the compiler. Use `3` to optimize performance, `z` to optimize for size, and `s` for something in-between.
- [panic:](https://doc.rust-lang.org/cargo/reference/profiles.html#panic) Reduce size by removing panic unwinding.
- [strip:](https://doc.rust-lang.org/cargo/reference/profiles.html#strip) Strip either symbols or debuginfo from a binary.
- [rpath:](https://doc.rust-lang.org/cargo/reference/profiles.html#rpath) Assists in finding the dynamic libraries the binary requires by hard coding information into the binary.
- [trim-paths:](https://rust-lang.github.io/rfcs/3127-trim-paths.html) Removes potentially privileged information from binaries.
- [rustflags:](https://doc.rust-lang.org/nightly/cargo/reference/unstable.html#profile-rustflags-option) Sets Rust compiler flags on a profile by profile basis.
  - `-Cdebuginfo=0`: Whether debuginfo symbols should be included in the build.
  - `-Zthreads=8`: Increases the number of threads used during compilation.

## Remove Unused Commands

In Pull Request [`feat: add a new option to remove unused commands`](https://github.com/tauri-apps/tauri/pull/12890), we added in a new option in the tauri config file
```

---

## Install the flatpak

**URL:** llms-txt#install-the-flatpak

flatpak-builder --force-clean --user --disable-cache --repo flatpak-repo flatpak flatpak-builder.yaml

---

## Future Work

**URL:** llms-txt#future-work

**Contents:**
  - Binary Analysis
  - WebView Hardening
  - Fuzzing

This section describes topics we started or would like to tackle
in the future to make Tauri apps even more secure.
If you feel interested in these topics or have pre-existing
knowledge we are always happy to welcome new contributors
and advice via GitHub or other community platforms like Discord.

To allow pentesters, auditors and automated security checks
do to their job properly it is very valuable to provide insight even from
compiled binaries. Not all companies are open source or provide source code
for audits, red-teams and other security testing.

Another often overlooked point is that providing inbuilt metadata empowers
users of your application to audit their systems for known vulnerabilities
at scale without dedicating their lifetime and efforts into it.

If your threatmodel depends on security by obscurity this section will be
providing some tools and points which hopefully will make you reconsider.

For Rust there is `cargo-auditable` to create [SBOMs](https://en.wikipedia.org/wiki/Software_supply_chain)
and provide exact crate versions and dependencies of a binary without breaking reproducible builds.

For the frontend stack we are not aware of similar solutions, so extracting
the frontend assets from the binary should be a straightforward process.
Afterwards it should be possible to use tooling like `npm audit` or similar.
There are already [blog posts](https://infosecwriteups.com/reverse-engineering-a-native-desktop-application-tauri-app-5a2d92772da5)
about the process but no simple tooling is available.

We are planning to provide such tooling or make it easier to extract assets,
when compiling a Tauri app with certain features.

To use pentesting tools like [Burpsuite](https://portswigger.net/burp),
[Zap](https://www.zaproxy.org/) or [Caido](https://caido.io/) it is necessary
to intercept traffic from the webview and pass it through the testing proxy.
Currently Tauri has no inbuilt method to do so but there is ongoing work to
ease this process.

All of these tools allow to properly test and inspect Tauri applications
without source code access and should be considered when building a Tauri application.

We are planning to further support and implement related features in the future.

### WebView Hardening

In Tauri's current threat model and boundaries we are not able to add more
security constraints to the WebView itself and since it is the biggest part of
our stack which is written in an memory unsafe language, we are planning to research and
consider ways to further sandbox and isolate the webview processes.

Inbuilt and external sandboxing methods will be evaluated to reduce attack impact
and to enforce the IPC bridge for system access.
We believe that this part of our stack is the weak link but current generation WebViews
are improving in their hardening and exploit resilience.

To allow more efficient and simplify the process of fuzzing Tauri applications
we aim to further implement our mock runtimes and other tooling to make it easier
to configure and build for individual Tauri applications.

Tauri is supporting a multitude of Operating Systems and CPU architectures, usually
apps have only few or no possible memory unsafe code.
No pre-existing fuzzing tooling and libraries support these uncommon fuzzing use case,
so we need to implement it and support existing libraries like [libAFL](https://github.com/AFLplusplus/LibAFL)
to build Tauri fuzzing frameworks.

The goal is to make fuzzing accessible and efficient for Tauri application developers.

---

## Upgrade from Tauri 1.0

**URL:** llms-txt#upgrade-from-tauri-1.0

**Contents:**
- Preparing for Mobile
- Automated Migration
- Summary of Changes
  - Tauri Configuration
  - New Cargo Features
  - Removed Cargo Features
  - Rust Crate Changes
  - JavaScript API Changes
  - Environment Variables Changes
  - Event System

import { Tabs, TabItem } from '@astrojs/starlight/components';
import CommandTabs from '@components/CommandTabs.astro';

This guide walks you through upgrading your Tauri 1.0 application to Tauri 2.0.

## Preparing for Mobile

The mobile interface of Tauri requires your project to output a shared library. If you are targeting mobile for your existing application, you must change your crate to produce that kind of artifact along with the desktop executable.

1. Change the Cargo manifest to produce the library. Append the following block:

2. Rename `src-tauri/src/main.rs` to `src-tauri/src/lib.rs`. This file will be shared by both desktop and mobile targets.

3. Rename the `main` function header in `lib.rs` to the following:

The `tauri::mobile_entry_point` macro prepares your function to be executed on mobile.

4. Recreate the `main.rs` file calling the shared run function:

## Automated Migration

This command is not a substitude for this guide! Please read the _whole_ page regardless of whether you chose to use the command.

The Tauri v2 CLI includes a `migrate` command that automates most of the process and helps you finish the migration:

<CommandTabs
  npm="npm install @tauri-apps/cli@latest
    npm run tauri migrate"
  yarn="yarn upgrade @tauri-apps/cli@latest
    yarn tauri migrate"
  pnpm="pnpm update @tauri-apps/cli@latest
    pnpm tauri migrate"
  cargo='cargo install tauri-cli --version "^2.0.0" --locked
    cargo tauri migrate'
/>

Learn more about the `migrate` command in the [Command Line Interface reference](/reference/cli/#migrate)

## Summary of Changes

Below is a summary of the changes from Tauri 1.0 to Tauri 2.0:

### Tauri Configuration

- `package > productName` and `package > version` moved to top-level object.
- the binary name is no longer renamed to match `productName` automatically, so you must add a `mainBinaryName` string to the top-level object matching `productName`.
- `package` removed.
- `tauri` key renamed to `app`.
- `tauri > allowlist` removed. Refer to [Migrate Permissions](#migrate-permissions).
- `tauri > allowlist > protocol > assetScope` moved to `app > security > assetProtocol > scope`.
- `tauri > cli` moved to `plugins > cli`.
- `tauri > windows > fileDropEnabled` renamed to `app > windows > dragDropEnabled`.
- `tauri > updater > active` removed.
- `tauri > updater > dialog` removed.
- `tauri > updater` moved to `plugins > updater`.
- `bundle > createUpdaterArtifacts` added, must be set when using the app updater.
  - set it to `v1Compatible` when upgrading from v1 apps that were already distributed. See the [updater guide](/plugin/updater/) for more information.
- `tauri > systemTray` renamed to `app > trayIcon`.
- `tauri > pattern` moved to `app > security > pattern`.
- `tauri > bundle` moved top-level.
- `tauri > bundle > identifier` moved to top-level object.
- `tauri > bundle > dmg` moved to `bundle > macOS > dmg`
- `tauri > bundle > deb` moved to `bundle > linux > deb`
- `tauri > bundle > appimage` moved to `bundle > linux > appimage`
- `tauri > bundle > macOS > license` removed, use `bundle > licenseFile` instead.
- `tauri > bundle > windows > wix > license` removed, use `bundle > licenseFile` instead.
- `tauri > bundle > windows > nsis > license` removed, use `bundle > licenseFile` instead.
- `tauri > bundle > windows > webviewFixedRuntimePath` removed, use `bundle > windows > webviewInstallMode` instead.
- `build > withGlobalTauri` moved to `app > withGlobalTauri`.
- `build > distDir` renamed to `frontendDist`.
- `build > devPath` renamed to `devUrl`.

[Tauri 2.0 Configuration API reference](/reference/config/)

### New Cargo Features

- linux-protocol-body: Enables custom protocol request body parsing, allowing the IPC to use it. Requires webkit2gtk 2.40.

### Removed Cargo Features

- reqwest-client: reqwest is now the only supported client.
- reqwest-native-tls-vendored: use `native-tls-vendored` instead.
- process-command-api: use the `shell` plugin instead (see instructions in the following section).
- shell-open-api: use the `shell` plugin instead (see instructions in the following section).
- windows7-compat: moved to the `notification` plugin.
- updater: Updater is now a plugin.
- linux-protocol-headers: Now enabled by default since we upgraded our minimum webkit2gtk version.
- system-tray: renamed to `tray-icon`.

### Rust Crate Changes

- `api` module removed. Each API module can be found in a Tauri plugin.
- `api::dialog` module removed. Use `tauri-plugin-dialog` instead. [Migration](#migrate-to-dialog-plugin)
- `api::file` module removed. Use Rust's [`std::fs`](https://doc.rust-lang.org/std/fs/) instead.
- `api::http` module removed. Use `tauri-plugin-http` instead. [Migration](#migrate-to-http-plugin)
- `api::ip` module rewritten and moved to `tauri::ipc`. Check out the new APIs, specially `tauri::ipc::Channel`.
- `api::path` module functions and `tauri::PathResolved` moved to `tauri::Manager::path`. [Migration](#migrate-path-to-tauri-manager)
- `api::process::Command`, `tauri::api::shell` and `tauri::Manager::shell_scope` APIs removed. Use `tauri-plugin-shell` instead. [Migration](#migrate-to-shell-plugin)
- `api::process::current_binary` and `tauri::api::process::restart` moved to `tauri::process`.
- `api::version` module has been removed. Use the [semver crate](https://docs.rs/semver/latest/semver/) instead.
- `App::clipboard_manager` and `AppHandle::clipboard_manager` removed. Use `tauri-plugin-clipboard` instead. [Migration](#migrate-to-clipboard-plugin)
- `App::get_cli_matches` removed. Use `tauri-plugin-cli` instead. [Migration](#migrate-to-cli-plugin)
- `App::global_shortcut_manager` and `AppHandle::global_shortcut_manager` removed. Use `tauri-plugin-global-shortcut` instead. [Migration](#migrate-to-global-shortcut-plugin)
- `Manager::fs_scope` removed. The file system scope can be accessed via `tauri_plugin_fs::FsExt`.
- `Plugin::PluginApi` now receives a plugin configuration as a second argument.
- `Plugin::setup_with_config` removed. Use the updated `tauri::Plugin::PluginApi` instead.
- `scope::ipc::RemoteDomainAccessScope::enable_tauri_api` and `scope::ipc::RemoteDomainAccessScope::enables_tauri_api` removed. Enable each core plugin individually via `scope::ipc::RemoteDomainAccessScope::add_plugin` instead.
- `scope::IpcScope` removed, use `scope::ipc::Scope` instead.
- `scope::FsScope`, `scope::GlobPattern` and `scope::FsScopeEvent` removed, use `scope::fs::Scope`, `scope::fs::Pattern` and `scope::fs::Event` respectively.
- `updater` module removed. Use `tauri-plugin-updater` instead. [Migration](#migrate-to-updater-plugin)
- `Env.args` field has been removed, use `Env.args_os` field instead.
- `Menu`, `MenuEvent`, `CustomMenuItem`, `Submenu`, `WindowMenuEvent`, `MenuItem` and `Builder::on_menu_event` APIs removed. [Migration](#migrate-to-menu)
- `SystemTray`, `SystemTrayHandle`, `SystemTrayMenu`, `SystemTrayMenuItemHandle`, `SystemTraySubmenu`, `MenuEntry` and `SystemTrayMenuItem` APIs removed. [Migration](#migrate-to-tray-icon-module)

### JavaScript API Changes

The `@tauri-apps/api` package no longer provides non-core modules. Only the previous `tauri` (now `core`), `path`, `event` and `window` modules are exported. All others have been moved to plugins.

- `@tauri-apps/api/tauri` module renamed to `@tauri-apps/api/core`. [Migration](#migrate-to-core-module)
- `@tauri-apps/api/cli` module removed. Use `@tauri-apps/plugin-cli` instead. [Migration](#migrate-to-cli-plugin)
- `@tauri-apps/api/clipboard` module removed. Use `@tauri-apps/plugin-clipboard` instead. [Migration](#migrate-to-clipboard-plugin)
- `@tauri-apps/api/dialog` module removed. Use `@tauri-apps/plugin-dialog` instead. [Migration](#migrate-to-dialog-plugin)
- `@tauri-apps/api/fs` module removed. Use `@tauri-apps/plugin-fs` instead. [Migration](#migrate-to-file-system-plugin)
- `@tauri-apps/api/global-shortcut` module removed. Use `@tauri-apps/plugin-global-shortcut` instead. [Migration](#migrate-to-global-shortcut-plugin)
- `@tauri-apps/api/http` module removed. Use `@tauri-apps/plugin-http` instead. [Migration](#migrate-to-http-plugin)
- `@tauri-apps/api/os` module removed. Use `@tauri-apps/plugin-os` instead. [Migration](#migrate-to-os-plugin)
- `@tauri-apps/api/notification` module removed. Use `@tauri-apps/plugin-notification` instead. [Migration](#migrate-to-notification-plugin)
- `@tauri-apps/api/process` module removed. Use `@tauri-apps/plugin-process` instead. [Migration](#migrate-to-process-plugin)
- `@tauri-apps/api/shell` module removed. Use `@tauri-apps/plugin-shell` instead. [Migration](#migrate-to-shell-plugin)
- `@tauri-apps/api/updater` module removed. Use `@tauri-apps/plugin-updater` instead [Migration](#migrate-to-updater-plugin)
- `@tauri-apps/api/window` module renamed to `@tauri-apps/api/webviewWindow`. [Migration](#migrate-to-new-window-api)

The v1 plugins are now published as `@tauri-apps/plugin-<plugin-name>`. Previously they were available from git as `tauri-plugin-<plugin-name>-api`.

### Environment Variables Changes

Most of the environment variables read and written by the Tauri CLI were renamed for consistency and prevention of mistakes:

- `TAURI_PRIVATE_KEY` -> `TAURI_SIGNING_PRIVATE_KEY`
- `TAURI_KEY_PASSWORD` -> `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`
- `TAURI_SKIP_DEVSERVER_CHECK` -> `TAURI_CLI_NO_DEV_SERVER_WAIT`
- `TAURI_DEV_SERVER_PORT` -> `TAURI_CLI_PORT`
- `TAURI_PATH_DEPTH` -> `TAURI_CLI_CONFIG_DEPTH`
- `TAURI_FIPS_COMPLIANT` -> `TAURI_BUNDLER_WIX_FIPS_COMPLIANT`
- `TAURI_DEV_WATCHER_IGNORE_FILE` -> `TAURI_CLI_WATCHER_IGNORE_FILENAME`
- `TAURI_TRAY` -> `TAURI_LINUX_AYATANA_APPINDICATOR`
- `TAURI_APPLE_DEVELOPMENT_TEAM` -> `APPLE_DEVELOPMENT_TEAM`
- `TAURI_PLATFORM` -> `TAURI_ENV_PLATFORM`
- `TAURI_ARCH` -> `TAURI_ENV_ARCH`
- `TAURI_FAMILY` -> `TAURI_ENV_FAMILY`
- `TAURI_PLATFORM_VERSION` -> `TAURI_ENV_PLATFORM_VERSION`
- `TAURI_PLATFORM_TYPE` -> `TAURI_ENV_PLATFORM_TYPE`
- `TAURI_DEBUG` -> `TAURI_ENV_DEBUG`

The event system was redesigned to be easier to use. Instead of relying on the source of the event, it now has a simpler implementation that relies on event targets.

- The `emit` function now emits the event to all event listeners.
- Added a new `emit_to`/`emitTo` function to trigger an event to a specific target.
- `emit_filter` now filters based on [`EventTarget`](https://docs.rs/tauri/2.0.0/tauri/event/enum.EventTarget.html) instead of a window.
- Renamed `listen_global` to `listen_any`. It now listens to all events regardless of their filters and targets.
- JavaScript: `event.listen()` behaves similar to `listen_any`. It now listens to all events regardless of their filters and targets, unless a target is set in the `Options`.
- JavaScript: `WebviewWindow.listen` etc. only listen to events emitted to the respective `EventTarget`.

### Multiwebview support

Tauri v2 introduces multiwebview support currently behind an `unstable` feature flag.
In order to support it, we renamed the Rust `Window` type to `WebviewWindow` and the Manager `get_window` function to `get_webview_window`.

The `WebviewWindow` JS API type is now re-exported from `@tauri-apps/api/webviewWindow` instead of `@tauri-apps/api/window`.

### New origin URL on Windows

On Windows the frontend files in production apps are now hosted on `http://tauri.localhost` instead of `https://tauri.localhost`. Because of this IndexedDB, LocalStorage and Cookies will be reset unless `dangerousUseHttpScheme` was used in v1. To prevent this you can set `app > windows > useHttpsScheme` to `true` or use `WebviewWindowBuilder::use_https_scheme` to keep using the `https` scheme.

## Detailed Migration Steps

Common scenarios you may encounter when migrating your Tauri 1.0 app to Tauri 2.0.

### Migrate to Core Module

The `@tauri-apps/api/tauri` module was renamed to `@tauri-apps/api/core`.
Simply rename the module import:

### Migrate to CLI Plugin

The Rust `App::get_cli_matches` JavaScript `@tauri-apps/api/cli` APIs have been removed. Use the `@tauri-apps/plugin-cli` plugin instead:

1. Add to cargo dependencies:

**Examples:**

Example 1 (toml):
```toml
// src-tauri/Cargo.toml
[lib]
name = "app_lib"
crate-type = ["staticlib", "cdylib", "rlib"]
```

Example 2 (rust):
```rust
// src-tauri/src/lib.rs
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // your code here
}
```

Example 3 (rust):
```rust
// src-tauri/src/main.rs
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
  app_lib::run();
}
```

Example 4 (diff):
```diff
- import { invoke } from "@tauri-apps/api/tauri"
+ import { invoke } from "@tauri-apps/api/core"
```

---

## run this action when the repository is pushed to

**URL:** llms-txt#run-this-action-when-the-repository-is-pushed-to

---

## Command Scopes

**URL:** llms-txt#command-scopes

**Contents:**
- Examples

A scope is a granular way to define (dis)allowed behavior of a Tauri command.

Scopes are categorized into `allow` or `deny` scopes, where `deny` always
supersedes the `allow` scope.

The scope type needs be of any [`serde`](https://docs.rs/serde/latest/serde/) serializable type.
These types are plugin-specific in general. For scoped commands implemented in a Tauri application
the scope type needs to be defined in the application and then enforced in the command implementation.

For instance, the [`Fs`](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/fs) plugin allows you to use scopes to allow or deny certain directories and files
and the [`http`](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/http) plugin uses scopes to filter URLs that are allowed to be reached.

The scope is passed to the command and handling or properly enforcing is implemented
by the command itself.

Command developers need to ensure that there are no scope bypasses possible.
The scope validation implementation should be audited to ensure correctness.

These examples are taken from the [`Fs`](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/fs) plugin permissions:

The scope type in this plugin for all commands is a string,
which contains a [`glob`](https://docs.rs/glob/latest/glob/) compatible path.

The above scopes can be used to allow access to the `APPLOCALDATA` folder, while
preventing access to the `EBWebView` subfolder on windows, which contains sensitive webview data.

These can merged into a set, which reduces duplicate configuration and makes it more
understandable for anyone looking into the application configuration.

First the deny scopes are merged into `deny-default`:

Afterwards deny and allow scopes are merged:

These scopes can be either used for all commands, by extending the global scope of the plugin,
or for only selected commands when they are used in combination with a enabled command inside a permission.

Reasonable read only file access to files in the `APPLOCALDATA` could look like this:

These examples only highlight the scope functionality itself. Each plugin or application developer
needs to consider reasonable combinations of scope depending on their use cases.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown
The above scopes can be used to allow access to the `APPLOCALDATA` folder, while
preventing access to the `EBWebView` subfolder on windows, which contains sensitive webview data.

These can merged into a set, which reduces duplicate configuration and makes it more
understandable for anyone looking into the application configuration.

First the deny scopes are merged into `deny-default`:
```

Example 3 (unknown):
```unknown
Afterwards deny and allow scopes are merged:
```

Example 4 (unknown):
```unknown
These scopes can be either used for all commands, by extending the global scope of the plugin,
or for only selected commands when they are used in combination with a enabled command inside a permission.

Reasonable read only file access to files in the `APPLOCALDATA` could look like this:
```

---

## ...  rest of the file

**URL:** llms-txt#...--rest-of-the-file

**Contents:**
- Building the RPM package
- Signing the RPM package
  - Verify the signature
- Debugging the RPM package
  - Getting information about the package
  - Query specific information about the package
  - Checking the content of the package
  - Debugging scripts
  - Checking dependencies
  - List packages that depend on a specific package

json title="src-tauri/tauri.conf.json"
{
  "bundle": {
    "licenseFile": "../LICENSE", // put the path to the license file here
    "license": "MIT" // add the license here
  }
}
bash
gpg --gen-key
bash
export TAURI_SIGNING_RPM_KEY=$(cat /home/johndoe/my_super_private.key)
bash
export TAURI_SIGNING_RPM_KEY_PASSPHRASE=password
bash
gpg --export -a 'Tauri-App' > RPM-GPG-KEY-Tauri-App
bash
sudo rpm --import RPM-GPG-KEY-Tauri-App
bash title="~/.rpmmacros"
%_signature gpg
%_gpg_path /home/johndoe/.gnupg
%_gpg_name Tauri-App
%_gpgbin /usr/bin/gpg2
%__gpg_sign_cmd %{__gpg} \
    gpg --force-v3-sigs --digest-algo=sha1 --batch --no-verbose --no-armor \
    --passphrase-fd 3 --no-secmem-warning -u "%{_gpg_name}" \
    -sbo %{__signature_filename} %{__plaintext_filename}
bash
rpm  -v --checksig tauri-app-0.0.0-1.x86_64.rpm
bash
rpm -qip package_name.rpm
bash
rpm  -qp --queryformat '[%{NAME} %{VERSION} %{RELEASE} %{ARCH} %{SIZE}\n]' package_name.rpm
bash
rpm -qlp package_name.rpm
bash
rpm -qp --scripts package_name.rpm
bash
rpm -qp --requires package_name.rpm
bash
rpm -q --whatrequires package_name.rpm
bash
rpm -ivvh package_name.rpm
bash
rpm -Uvvh package_name.rpm
toml
   [target.armv7-unknown-linux-gnueabihf]
   linker = "arm-linux-gnueabihf-gcc"

[target.aarch64-unknown-linux-gnu]
   linker = "aarch64-linux-gnu-gcc"
   
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-backports main restricted universe multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security multiverse
   
   # See http://help.ubuntu.com/community/UpgradeNotes for how to upgrade to
   # newer versions of the distribution.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy main restricted
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy main restricted

## Major bug fix updates produced after the final release of the
   ## distribution.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted

## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
   ## team. Also, please note that software in universe WILL NOT receive any
   ## review or updates from the Ubuntu security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy universe
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy universe
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates universe
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-updates universe

## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
   ## team, and may not be under a free licence. Please satisfy yourself as to
   ## your rights to use the software. Also, please note that software in
   ## multiverse WILL NOT receive any review or updates from the Ubuntu
   ## security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy multiverse
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy multiverse
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates multiverse

## N.B. software from this repository may not have been tested as
   ## extensively as that contained in the main release, although it includes
   ## newer versions of some applications which may provide useful features.
   ## Also, please note that software in backports WILL NOT receive any review
   ## or updates from the Ubuntu security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-backports main restricted universe multiverse
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-backports main restricted universe multiverse

deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security main restricted
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security main restricted
   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security universe
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security universe
   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security multiverse
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security multiverse

deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-backports main restricted universe multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security multiverse
   toml
   openssl-sys = {version = "0.9", features = ["vendored"]}
   ```

9. #### Set the `PKG_CONFIG_SYSROOT_DIR` to the appropriate directory based on your chosen architecture
   - For ARMv7: `export PKG_CONFIG_SYSROOT_DIR=/usr/arm-linux-gnueabihf/`
   - For ARMv8 (ARM64): `export PKG_CONFIG_SYSROOT_DIR=/usr/aarch64-linux-gnu/`

10. #### Build the app for your desired ARM version
    - For ARMv7: cargo tauri build --target armv7-unknown-linux-gnueabihf
    - For ARMv8 (ARM64): cargo tauri build --target aarch64-unknown-linux-gnu

Choose the appropriate set of instructions based on whether you want to cross-compile your Tauri application for ARMv7 or ARMv8 (ARM64). Please note that the specific steps may vary depending on your Linux distribution and setup.

**Examples:**

Example 1 (unknown):
```unknown
And for `src-tauri/tauri.conf.json`
```

Example 2 (unknown):
```unknown
## Building the RPM package

To build the RPM package, you can use the following command:

<CommandTabs
  npm="npm run tauri build"
  yarn="yarn tauri build"
  pnpm="pnpm tauri build"
  deno="deno task tauri build"
  bun="bun tauri build"
  cargo="cargo tauri build"
/>

This command will build the RPM package in the `src-tauri/target/release/bundle/rpm` directory.

## Signing the RPM package

Tauri allows you to sign the package with the key you have in your system during the build process.
To do this, you will need to generate a GPG key.

#### Generate a GPG key

To generate a GPG key you can use the following command:
```

Example 3 (unknown):
```unknown
Follow the instruction to generate the key.

Once the key is generated, you will need to add it to your environment variable.
You can do this by adding the following to your .bashrc or .zshrc file or just export it in the terminal:
```

Example 4 (unknown):
```unknown
If you have a passphrase for the key, you can add it to the environment variable:
```

---

## the name of our workflow

**URL:** llms-txt#the-name-of-our-workflow

jobs:
  # a single job named test
  test:
    # the display name of the test job
    name: WebDriverIO Test Runner

# run on the matrix platform
    runs-on: ${{ matrix.platform }}
    strategy:
      # do not fail other matrix runs if one fails
      fail-fast: false
      # set all platforms our test should run on
      matrix:
        platform: [ubuntu-latest, windows-latest]

# the steps our job runs **in order**
    steps:
      # checkout the code on the workflow runner
      - uses: actions/checkout@v4

# install system dependencies that Tauri needs to compile on Linux.
      # note the extra dependencies for `tauri-driver` to run which are: `webkit2gtk-driver` and `xvfb`
      - name: Tauri dependencies
        if: matrix.platform == 'ubuntu-latest'
        run: |
          sudo apt-get update &&
          sudo apt-get install -y \
          libwebkit2gtk-4.1-dev \
          libayatana-appindicator3-dev \
          webkit2gtk-driver \
          xvfb

# install a matching Microsoft Edge Driver version using msedgedriver-tool
      - name: install msdgedriver (Windows)
        if: matrix.platform == 'windows-latest'
        run: |
          cargo install --git https://github.com/chippers/msedgedriver-tool
          & "$HOME/.cargo/bin/msedgedriver-tool.exe"
          $PWD.Path >> $env:GITHUB_PATH

# install latest stable Rust release
      - name: Setup rust-toolchain stable
        uses: dtolnay/rust-toolchain@stable

# setup caching for the Rust target folder
      - name: Setup Rust cache
        uses: Swatinem/rust-cache@v2
        with:
          workspaces: src-tauri

# we run our Rust tests before the webdriver tests to avoid testing a broken application
      - name: Cargo test
        run: cargo test

# install the latest stable node version at the time of writing
      - name: Node 24
        uses: actions/setup-node@v4
        with:
          node-version: 24
          cache: 'yarn'

# install the application Node.js dependencies with Yarn
      - name: Yarn install
        run: yarn install --frozen-lockfile

# install the e2e-tests Node.js dependencies with Yarn
      - name: Yarn install
        run: yarn install --frozen-lockfile
        working-directory: e2e-tests

# install the latest version of `tauri-driver`.
      # note: the tauri-driver version is independent of any other Tauri versions
      - name: Install tauri-driver
        run: cargo install tauri-driver --locked

# run the WebdriverIO test suite on Linux.
      # we run it through `xvfb-run` (the dependency we installed earlier) to have a fake
      # display server which allows our application to run headless without any changes to the code
      - name: WebdriverIO (Linux)
        if: matrix.platform == 'ubuntu-latest'
        run: xvfb-run yarn test
        working-directory: e2e-tests

# run the WebdriverIO test suite on Windows.
      # in this case we can run the tests directly.
      - name: WebdriverIO (Windows)
        if: matrix.platform == 'windows-latest'
        run: yarn test
        working-directory: e2e-tests
```

[previously built together]: /develop/tests/webdriver/example/webdriverio/
[webdriver]: https://www.w3.org/TR/webdriver/
[`tauri-driver`]: https://crates.io/crates/tauri-driver
[webdriverio]: https://webdriver.io/

---

## Brownfield Pattern

**URL:** llms-txt#brownfield-pattern

**Contents:**
- Configuration

_**This is the default pattern.**_

This is the simplest and most straightforward pattern to use Tauri with, because it tries to be as compatible as possible with existing frontend projects. In short, it tries to require nothing
additional to what an existing web frontend might use inside a browser.
Not _**everything**_ that works in existing browser applications will work out-of-the-box.

If you are unfamiliar with Brownfield software development in general, the [Brownfield Wikipedia article]
provides a nice summary. For Tauri, the existing software is current browser support and behavior, instead of
legacy systems.

Because the Brownfield pattern is the default pattern, it doesn't require a configuration option to be set. To explicitly set
it, you can use the `app > security > pattern` object in the `tauri.conf.json` configuration file.

_**There are no additional configuration options for the brownfield pattern.**_

[brownfield wikipedia article]: https://en.wikipedia.org/wiki/Brownfield_(software_development)

**Examples:**

Example 1 (json):
```json
{
  "app": {
    "security": {
      "pattern": {
        "use": "brownfield"
      }
    }
  }
}
```

---

## Splashscreen

**URL:** llms-txt#splashscreen

**Contents:**
- Prerequisites
- Steps
- Discuss

import { Image } from 'astro:assets';
import step_1 from '@assets/learn/splashscreen/step_1.png';
import step_3 from '@assets/learn/splashscreen/step_3.png';
import { Steps, Tabs, TabItem } from '@astrojs/starlight/components';
import ShowSolution from '@components/ShowSolution.astro';
import CTA from '@fragments/cta.mdx';

In this lab we'll be implementing a basic splashscreen functionality in a Tauri app. Doing so
is quite straight forward, a splashscreen is effectively just a matter of creating a new window
that displays some contents during the period your app is doing some heavy setup related tasks
and then closing it when setting up is done.

:::tip[Create a lab app]

If you are not an advanced user it's **highly recommended** that you use the options and frameworks provided here. It's just a lab, you can delete the project when you're done.

- Project name: `splashscreen-lab`
- Choose which language to use for your frontend: `Typescript / Javascript`
- Choose your package manager: `pnpm`
- Choose your UI template: `Vanilla`
- Choose your UI flavor: `Typescript`

1. ##### Install dependencies and run the project

Before you start developing any project it's important to build and run the initial template, just to validate your setup is working as intended.

<ShowSolution>
    
    <Image src={step_1} alt="Successful run of the created template app."/>
    </ShowSolution>

1. ##### Register new windows in `tauri.conf.json`

The easiest way of adding new windows is by adding them directly to `tauri.conf.json`. You can also create them dynamically at startup,
   but for the sake of simplicity lets just register them instead. Make sure you have a window with the label `main` that's being created as a hidden window and a window with the label `splashscreen` that's created as being shown directly. You can leave all other options as their defaults, or tweak them based on preference.

<ShowSolution>
    
    </ShowSolution>

1. ##### Create a new page to host your splashscreen

Before you begin you'll need to have some content to show. How you develop new pages depend on your chosen framework,
   most have the concept of a "router" that handles page navigation which should work just like normal in Tauri, in which case
   you just create a new splashscreen page. Or as we're going to be doing here, create a new `splashscreen.html` file to host the contents.

What's important here is that you can navigate to a `/splashscreen` URL and be shown the contents you want for your splashscreen. Try running the app again after this step!

<ShowSolution>
    
    <Image src={step_3} alt="The splashscreen we just created."/>
    </ShowSolution>

1. ##### Start some setup tasks

Since splashscreens are generally intended to be used for the sake of hiding heavy setup related tasks, lets fake giving the app something heavy to do, some in the frontend and some in the backend.

To fake heavy setup in the frontend we're going to be using a simple `setTimeout` function.
    
    The easiest way to fake heavy operations in the backend is by using the Tokio crate, which is the Rust crate that Tauri uses in the backend to provide an asynchronous runtime. While Tauri provides the runtime there are various utilities that Tauri doesn't re-export from it, so we'll need to add the crate to our project in order to access them. This is a perfectly normal practice within the Rust ecosystem.

Don't use `std::thread::sleep` in async functions, they run cooperatively in a concurrent environment not in parallel, meaning that if you sleep the thread instead of the Tokio task you'll be locking all tasks scheduled to run on that thread from being executed, causing your app to freeze.

1. ##### Run the application

You should now see a splashscreen window pop up, both the frontend and backend will perform their respective heavy 3 second setup tasks, after which the splashscreen disappears and the main window is shown!

##### Should you have a splashscreen?

In general having a splashscreen is an admittance of defeat that you couldn't make your
app load fast enough to not need one. In fact it tends to be better to just go straight
to a main window that then shows some little spinner somewhere in a corner informing the
user there's still setup tasks happening in the background.

However, with that said, it can be a stylistic choice that you want to have a splashscreen,
or you might have some very particular requirement that makes it impossible to start the
app until some tasks are performed. It's definitely not *wrong* to have a splashscreen, it
just tends to not be necessary and can make users feel like the app isn't very well optimized.

**Examples:**

Example 1 (unknown):
```unknown
<Image src={step_1} alt="Successful run of the created template app."/>
    </ShowSolution>

1. ##### Register new windows in `tauri.conf.json`

   The easiest way of adding new windows is by adding them directly to `tauri.conf.json`. You can also create them dynamically at startup,
   but for the sake of simplicity lets just register them instead. Make sure you have a window with the label `main` that's being created as a hidden window and a window with the label `splashscreen` that's created as being shown directly. You can leave all other options as their defaults, or tweak them based on preference.

    <ShowSolution>
```

Example 2 (unknown):
```unknown
</ShowSolution>

1. ##### Create a new page to host your splashscreen

   Before you begin you'll need to have some content to show. How you develop new pages depend on your chosen framework,
   most have the concept of a "router" that handles page navigation which should work just like normal in Tauri, in which case
   you just create a new splashscreen page. Or as we're going to be doing here, create a new `splashscreen.html` file to host the contents.

   What's important here is that you can navigate to a `/splashscreen` URL and be shown the contents you want for your splashscreen. Try running the app again after this step!

    <ShowSolution>
```

Example 3 (unknown):
```unknown
<Image src={step_3} alt="The splashscreen we just created."/>
    </ShowSolution>

1. ##### Start some setup tasks

    Since splashscreens are generally intended to be used for the sake of hiding heavy setup related tasks, lets fake giving the app something heavy to do, some in the frontend and some in the backend.

    To fake heavy setup in the frontend we're going to be using a simple `setTimeout` function.
    
    The easiest way to fake heavy operations in the backend is by using the Tokio crate, which is the Rust crate that Tauri uses in the backend to provide an asynchronous runtime. While Tauri provides the runtime there are various utilities that Tauri doesn't re-export from it, so we'll need to add the crate to our project in order to access them. This is a perfectly normal practice within the Rust ecosystem.

    Don't use `std::thread::sleep` in async functions, they run cooperatively in a concurrent environment not in parallel, meaning that if you sleep the thread instead of the Tokio task you'll be locking all tasks scheduled to run on that thread from being executed, causing your app to freeze.

    <ShowSolution>
```

Example 4 (unknown):
```unknown

```

---

## Application Lifecycle Threats

**URL:** llms-txt#application-lifecycle-threats

**Contents:**
- Upstream Threats
  - Keep Your Applications Up-To-Date
  - Evaluate Your Dependencies
- Development Threats
  - Development Server
  - Harden Development machines
  - Ensure Source Control Authentication and Authorization
- Buildtime Threats
  - Reproducible Builds
- Distribution Threats

Tauri applications are composed of many pieces at different points in time of the application lifecycle.
Here we describe classical threats and what you SHOULD do about them.

All of these distinct steps are described in the following sections.

![Threat Stages During Development](@assets/concept/application-flow-simple.svg)

:::note
The weakest link in your application lifecycle essentially defines your security.
Each step can compromise the assumptions and integrity of all subsequent steps,
so it is important to see the whole picture at all times.
:::

Tauri is a direct dependency on your project, and we maintain strict authorial control
of commits, reviews, pull requests, and releases.
We do our best to maintain up-to-date dependencies and take action to either update
or fork and fix. Other projects may not be so well maintained, and may not even
have ever been audited.

Please consider their health when integrating them, otherwise, you may have adopted
architectural debt without even knowing it.

### Keep Your Applications Up-To-Date

When releasing your app into the wild, you are also shipping a bundle that has Tauri in it.
Vulnerabilities affecting Tauri may impact the security of your application.
By updating Tauri to the latest version, you ensure that critical vulnerabilities
are already patched and cannot be exploited in your application.
Also be sure to keep your compiler (`rustc`) and transpilers (`nodejs`) up to date,
because there are often security issues that are resolved.
This also is true for your development system in general.

### Evaluate Your Dependencies

While NPM and Crates.io provide many convenient packages,
it is your responsibility to choose trustworthy third-party libraries - or
rewrite them in Rust. If you do use outdated libraries which are affected by
known vulnerabilities or are unmaintained, your application security and good
night's sleep could be in jeopardy.

Use tooling like [`npm audit`](https://docs.npmjs.com/cli/v10/commands/npm-audit)
and [`cargo audit`](https://crates.io/crates/cargo-audit) to automate this process,
and lean on the security community's important work.

Recent trends in the rust ecosystem like [`cargo-vet`](https://github.com/mozilla/cargo-vet)
or [`cargo crev`](https://github.com/crev-dev/cargo-crev) can
help to further reduce likelihood of supply chain attacks.
To find out on whose shoulders you stand, you can use the [`cargo supply chain`](https://github.com/rust-secure-code/cargo-supply-chain)
tool.

One practice that we highly recommend, is to only ever consume critical dependencies
from git using hash revisions at best or named tags as second best.
This holds for Rust as well as the Node ecosystem.

## Development Threats

We assume that you, the developer, care for your development environment.
It is on you to make sure that your operating system, build toolchains, and
associated dependencies are kept up to date and reasonable secured.

A genuine risk all of us face is what is known as "supply-chain attacks",
which are usually considered to be attacks on direct dependencies of your project.
However, a growing class of attacks in the wild directly target development machines,
and you would be well off to address this head-on.

### Development Server

Tauri application frontends can be developed using a number of web frameworks.
Each of these frameworks usually ship their own development server, which is exposing
the frontend assets via an open port to the local system or network.
This allows the frontend to be hot-reloaded and debugged in the WebView or Browser.

In practice this connection is often neither encrypted nor authenticated by default.
This is also the case for the built-in Tauri development server and exposes your
frontend and assets to the local network. Additionally, this allows attackers
to push their own frontend code to development devices in the same network as the attacker.
Depending on what kind of functionality is exposed this could lead to device compromise
in the worst case.

You should only develop on trusted networks where you can safely expose your
development device. If this is not possible you MUST ensure that your development
server uses **mutual** authentication and encryption (e.g. mTLS) for connections
with your development devices.

:::note
The built-in Tauri development server does not support
mutual authentication and transport encryption at the moment and should not be used on untrusted networks.
:::

### Harden Development machines

Hardening your development systems depends on various factors and on your personal
threat model but some generic advice we recommend to follow:

- Never use administrative accounts for day to day tasks like coding
- Never use production secrets on development machines
- Prevent secrets to be checked into source code version control
- Use security hardware tokens or similar to reduce impact of compromised systems
- Keep your system up to date
- Keep your installed applications to a minimum

A more practical collection of procedures can be found
in an [awesome security hardening collection](https://github.com/decalage2/awesome-security-hardening).

You can of course virtualise your development environment to keep attackers at bay,
but this won't protect you from attacks that target your project rather than just your machine.

### Ensure Source Control Authentication and Authorization

If you are working like the majority of developers, using source code version control tools and
service providers is an essential step during development.

To ensure that your source code can not be modified by unauthorized actors it is important
to understand and correctly set up up access control for your source code version control system.

Also, consider requiring all (regular) contributors to sign their commits to prevent situations where malicious
commits are attributed to non-compromised or non-maliocious contributors.

Modern organizations use CI/CD to manufacture binary artifacts.

You need to be able to fully trust these remote (and third party owned) systems,
as they have access to source code, secrets and are able to modify builds without
you being able to verifiably prove that the produced binaries are the same as your local code.
This means either you trust a reputable provider or host these systems on your own and controlled
hardware.

At Tauri, we provide a GitHub Workflow for building on multiple platforms.
If you create your own CI/CD and depend on third-party tooling, be wary of actions
whose versions you have not explicitly pinned.

You should sign your binaries for the platform you are shipping to.
While this can be complicated and somewhat costly to set up, end users expect that your
app is verifiably from you.

If cryptographic secrets are properly stored on hardware tokens,
a compromised build system won't be able to leak involved signing keys,
but could use them to sign malicious releases.

### Reproducible Builds

To combat backdoor injection at build time, you need your builds to be reproducible,
so that you can verify that the build assets are exactly the same when you build them
locally or on another independent provider.

The first problem is that Rust is by default not fully **reliably** producing reproducible
builds. It supports this in theory, but there are still bugs, and it recently broke on a release.

You can keep track of the current state in the rust project's
[public bug tracker](https://github.com/rust-lang/rust/labels/A-reproducibility).

The next problem you will encounter is that many common frontend bundlers do not produce
reproducible output either, so the bundled assets may also break reproducible builds.

This means that you cannot fully rely on reproducible builds by default, and
sadly need to fully trust your build systems.

## Distribution Threats

We have done our best to make shipping hot updates to the app as
straightforward and secure as possible.
However, all bets are off if you lose control of the manifest server,
the build server, or the binary hosting service.

If you build your own system, consult a professional OPS architect and build it properly.

If you are looking for another trusted distribution solution for Tauri apps
our partner CrabNebula has an offering: [https://crabnebula.dev/cloud](https://crabnebula.dev/cloud)

We assume the webview is insecure, which has led Tauri to implement several protections
regarding webview access to system APIs in the context of loading untrusted userland content.

Using the [Content Security Policy](/security/csp/) will lockdown types of
communication that the Webview can undertake.
Furthermore, [Capabilities](/security/capabilities/) can prevent untrusted content or scripts from accessing
the API within the Webview.

We also recommend to setup an easy and secure way to report vulnerabilities similar to
[our process](/security/#coordinated-disclosure).

---

## interface: dbus

**URL:** llms-txt#interface:-dbus

---

## Runtime Authority

**URL:** llms-txt#runtime-authority

The runtime authority is part of the Tauri Core.
It holds all permissions, capabilities and scopes at runtime to enforce
which window can access which command and passes scopes to commands.

Whenever a Tauri command is invoked from the webview the runtime authority
receives the invoke request, makes sure that the origin is allowed to actually
use the requested command, checks if the origin is part of capabilities and
if scopes are defined for the command and applicable then they are injected into
the invoke request, which is then passed to the proper Tauri command.

If the origin is not allowed to call the command, the runtime authority will deny
the request and the Tauri command is never invoked.

![IPC Diagram](@assets/concept/runtime-authority.svg)

---

## bus: session

**URL:** llms-txt#bus:-session

---

## Windows Installer

**URL:** llms-txt#windows-installer

**Contents:**
- Building
  - Build Windows apps on Linux and macOS
  - Building for 32-bit or ARM
- Supporting Windows 7
- FIPS Compliance
- WebView2 Installation Options
  - Downloaded Bootstrapper
  - Embedded Bootstrapper
  - Offline Installer
  - Fixed Version

import CommandTabs from '@components/CommandTabs.astro';
import { Tabs, TabItem } from '@astrojs/starlight/components';

Tauri applications for Windows are either distributed as Microsoft Installers (`.msi` files) using the [WiX Toolset v3]
or as setup executables (`-setup.exe` files) using [NSIS].

Please note that `.msi` installers can **only be created on Windows** as WiX can only run on Windows systems.
Cross-compilation for NSIS installers is shown below.

This guide provides information about available customization options for the installer.

To build and bundle your app into a Windows installer you can use the Tauri CLI and run the `tauri build` command in a Windows computer:

<CommandTabs
  npm="npm run tauri build"
  yarn="yarn tauri build"
  pnpm="pnpm tauri build"
  deno="deno task tauri build"
  bun="bun tauri build"
  cargo="cargo tauri build"
/>

:::note[VBSCRIPT requirement for MSI packages]

Building MSI packages (`"targets": "msi"` or `"targets": "all"` in `tauri.conf.json`) requires the VBSCRIPT optional feature to be enabled on Windows. This feature is enabled by default on most Windows installations, but if you encounter errors like `failed to run light.exe`, you may need to enable it manually through **Settings** → **Apps** → **Optional features** → **More Windows features**. See the [Prerequisites guide](/start/prerequisites/#vbscript-for-msi-installers) for detailed instructions.

### Build Windows apps on Linux and macOS

Cross compiling Windows apps on Linux and macOS hosts is possible with caveats when using [NSIS].
It is not as straight forward as compiling on Windows directly and is not tested as much.
Therefore it should only be used as a last resort if local VMs or CI solutions like GitHub Actions don't work for you.

Signing cross compiled Windows installers requires an external signing tool.
See the [signing documentation] for more information.

Since Tauri officially only supports the MSVC Windows target, the setup is a bit more involved.

<Tabs syncKey="OS">
<TabItem label="Linux">
Some Linux distributions have NSIS available in their repositories, for example on Ubuntu you can install NSIS by running this command:

But on many other distributions you have to compile NSIS yourself or download Stubs and Plugins manually that weren't included in the distro's binary package.
Fedora for example only provides the binary but not the Stubs and Plugins:

<TabItem label="macOS">
On macOS you will need [Homebrew] to install NSIS:

#### Install LLVM and the LLD Linker

Since the default Microsoft linker only works on Windows we will also need to install a new linker.
To compile the Windows Resource file which is used for setting the app icon among other things
we will also need the `llvm-rc` binary which is part of the LLVM project.

<Tabs syncKey="OS">
<TabItem label="Linux">

On Linux you also need to install the `clang` package if you added dependencies that compile C/C++ dependencies as part of their build scripts.
Default Tauri apps should not require this.

</TabItem>
<TabItem label="macOS">

On macOS you also have to add `/opt/homebrew/opt/llvm/bin` to your `$PATH` as suggested in the install output.

#### Install the Windows Rust target

Assuming you're building for 64-bit Windows systems:

#### Install `cargo-xwin`

Instead of setting the Windows SDKs up manually we will use [`cargo-xwin`] as Tauri's "runner":

By default `cargo-xwin` will download the Windows SDKs into a project-local folder.
If you have multiple projects and want to share those files you can set the `XWIN_CACHE_DIR` environment variable with a path to the preferred location.

#### Building the App

Now it should be as simple as adding the runner and target to the `tauri build` command:

<CommandTabs
  npm="npm run tauri build -- --runner cargo-xwin --target x86_64-pc-windows-msvc"
  yarn="yarn tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc"
  pnpm="pnpm tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc"
  deno="deno task tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc"
  bun="bun tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc"
  cargo="cargo tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc"
/>

The build output will then be in `target/x86_64-pc-windows-msvc/release/bundle/nsis/`.

### Building for 32-bit or ARM

The Tauri CLI compiles your executable using your machine's architecture by default.
Assuming that you're developing on a 64-bit machine, the CLI will produce 64-bit applications.

If you need to support **32-bit** machines, you can compile your application with a **different** [Rust target][platform support]
using the `--target` flag:

<CommandTabs
  npm="npm run tauri build -- --target i686-pc-windows-msvc"
  yarn="yarn tauri build --target i686-pc-windows-msvc"
  pnpm="pnpm tauri build --target i686-pc-windows-msvc"
  deno="deno task tauri build --target i686-pc-windows-msvc"
  bun="bun tauri build --target i686-pc-windows-msvc"
  cargo="cargo tauri build --target i686-pc-windows-msvc"
/>

By default, Rust only installs toolchains for your machine's target,
so you need to install the 32-bit Windows toolchain first: `rustup target add i686-pc-windows-msvc`.

If you need to build for **ARM64** you first need to install additional build tools.
To do this, open `Visual Studio Installer`, click on "Modify", and in the "Individual Components" tab install the "C++ ARM64 build tools".
At the time of writing, the exact name in VS2022 is `MSVC v143 - VS 2022 C++ ARM64 build tools (Latest)`.  
Now you can add the rust target with `rustup target add aarch64-pc-windows-msvc` and then use the above-mentioned method to compile your app:

<CommandTabs
  npm="npm run tauri build -- --target aarch64-pc-windows-msvc"
  yarn="yarn tauri build --target aarch64-pc-windows-msvc"
  pnpm="pnpm tauri build --target aarch64-pc-windows-msvc"
  deno="deno task tauri build --target aarch64-pc-windows-msvc"
  bun="bun tauri build --target aarch64-pc-windows-msvc"
  cargo="cargo tauri build --target aarch64-pc-windows-msvc"
/>

Note that the NSIS installer itself will still be x86 running on the ARM machine via emulation. The app itself will be a native ARM64 binary.

## Supporting Windows 7

By default, the Microsoft Installer (`.msi`) does not work on Windows 7 because it needs to download the WebView2 bootstrapper if not installed
(which might fail if TLS 1.2 is not enabled in the operating system). Tauri includes an option to embed the WebView2 bootstrapper
(see the [Embedding the WebView2 Bootstrapper](#embedded-bootstrapper) section below).
The NSIS based installer (`-setup.exe`) also supports the `downloadBootstrapper` mode on Windows 7.

Additionally, to use the Notification API in Windows 7, you need to enable the `windows7-compat` Cargo feature:

If your system requires the MSI bundle to be FIPS compliant you can set the `TAURI_BUNDLER_WIX_FIPS_COMPLIANT` environment variable to `true`
before running `tauri build`. In PowerShell you can set it for the current terminal session like this:

## WebView2 Installation Options

The installers by default download the WebView2 bootstrapper and executes it if the runtime is not installed.
Alternatively, you can embed the bootstrapper, embed the offline installer, or use a fixed WebView2 runtime version.
See the following table for a comparison between these methods:

| Installation Method                                | Requires Internet Connection? | Additional Installer Size | Notes                                                                                                                   |
| :------------------------------------------------- | :---------------------------- | :------------------------ | :---------------------------------------------------------------------------------------------------------------------- |
| [`downloadBootstrapper`](#downloaded-bootstrapper) | Yes                           | 0MB                       | `Default` <br /> Results in a smaller installer size, but is not recommended for Windows 7 deployment via `.msi` files. |
| [`embedBootstrapper`](#embedded-bootstrapper)      | Yes                           | ~1.8MB                    | Better support on Windows 7 for `.msi` installers.                                                                      |
| [`offlineInstaller`](#offline-installer)           | No                            | ~127MB                    | Embeds WebView2 installer. Recommended for offline environments.                                                        |
| [`fixedVersion`](#fixed-version)                   | No                            | ~180MB                    | Embeds a fixed WebView2 version.                                                                                        |
| [`skip`](#skipping-installation)                   | No                            | 0MB                       | ⚠️ Not recommended <br /> Does not install the WebView2 as part of the Windows Installer.                               |

On Windows 10 (April 2018 release or later) and Windows 11, the WebView2 runtime is distributed as part of the operating system.

### Downloaded Bootstrapper

This is the default setting for building the Windows Installer. It downloads the bootstrapper and runs it.
Requires an internet connection but results in a smaller installer size.
This is not recommended if you're going to be distributing to Windows 7 via `.msi` installers.

### Embedded Bootstrapper

To embed the WebView2 Bootstrapper, set the [webviewInstallMode] to `embedBootstrapper`.
This increases the installer size by around 1.8MB, but increases compatibility with Windows 7 systems.

### Offline Installer

To embed the WebView2 Bootstrapper, set the [webviewInstallMode] to `offlineInstaller`.
This increases the installer size by around 127MB, but allows your application to be installed even if an internet connection is not available.

Using the runtime provided by the system is great for security as the webview vulnerability patches are managed by Windows.
If you want to control the WebView2 distribution on each of your applications
(either to manage the release patches yourself or distribute applications on environments where an internet connection might not be available)
Tauri can bundle the runtime files for you.

Distributing a fixed WebView2 Runtime version increases the Windows Installer by around 180MB.

1. Download the WebView2 fixed version runtime from [Microsoft's website][download-webview2-runtime].
   In this example, the downloaded filename is `Microsoft.WebView2.FixedVersionRuntime.128.0.2739.42.x64.cab`
2. Extract the file to the core folder:

3. Configure the WebView2 runtime path in `tauri.conf.json`:

4. Run `tauri build` to produce the Windows Installer with the fixed WebView2 runtime.

### Skipping Installation

You can remove the WebView2 Runtime download check from the installer by setting [webviewInstallMode] to `skip`.
Your application WILL NOT work if the user does not have the runtime installed.

Your application WILL NOT work if the user does not have the runtime installed and won't attempt to install it.

## Customizing the WiX Installer

See the [WiX configuration] for the complete list of customization options.

### Installer Template

The `.msi` Windows Installer package is built using the [WiX Toolset v3].
Currently, apart from pre-defined [configurations][WiX configuration], you can change it by using a custom WiX source code
(an XML file with a `.wxs` file extension) or through WiX fragments.

#### Replacing the Installer Code with a Custom WiX File

The Windows Installer XML defined by Tauri is configured to work for the common use case
of simple webview-based applications (you can find it [here][default wix template]).
It uses [handlebars] so the Tauri CLI can brand your installer according to your `tauri.conf.json` definition.
If you need a completely different installer, a custom template file can be configured on [`tauri.bundle.windows.wix.template`].

#### Extending the Installer with WiX Fragments

A [WiX fragment] is a container where you can configure almost everything offered by WiX.
In this example, we will define a fragment that writes two registry entries:

Save the fragment file with the `.wxs` extension in the `src-tauri/windows/fragments` folder and reference it on `tauri.conf.json`:

Note that `ComponentGroup`, `Component`, `FeatureGroup`, `Feature` and `Merge` element ids must be referenced on the `wix` object
of `tauri.conf.json` on the `componentGroupRefs`, `componentRefs`, `featureGroupRefs`, `featureRefs` and `mergeRefs`
respectively to be included in the installer.

### Internationalization

The WiX Installer is built using the `en-US` language by default.
Internationalization (i18n) can be configured using the [`tauri.bundle.windows.wix.language`] property,
defining the languages Tauri should build an installer against.
You can find the language names to use in the Language-Culture column on [Microsoft's website][localizing the error and actiontext tables].

#### Compiling a WiX Installer for a Single Language

To create a single installer targeting a specific language, set the `language` value to a string:

#### Compiling a WiX Installer for Each Language in a List

To compile an installer targeting a list of languages, use an array.
A specific installer for each language will be created, with the language key as a suffix:

#### Configuring the WiX Installer Strings for Each Language

A configuration object can be defined for each language to configure localization strings:

The `localePath` property defines the path to a language file, a XML configuring the language culture:

The `WixLocalization` element's `Culture` field must match the configured language.

Currently, Tauri references the following locale strings: `LaunchApp`, `DowngradeErrorMessage`, `PathEnvVarFeature` and `InstallAppFeature`.
You can define your own strings and reference them on your custom template or fragments with `"!(loc.TheStringId)"`.
See the [WiX localization documentation] for more information.

## Customizing the NSIS Installer

See the [NSIS configuration] for the complete list of customization options.

### Installer Template

The NSIS Installer's `.nsi` script defined by Tauri is configured to work for the common use case
of simple webview-based applications (you can find it [here][default nsis template]).
It uses [handlebars] so the Tauri CLI can brand your installer according to your `tauri.conf.json` definition.
If you need a completely different installer, a custom template file can be configured on [`tauri.bundle.windows.nsis.template`].

### Extending the Installer

If you only need to extend some installation steps you might be able to use installer hooks instead of replacing the entire installer template.

- `NSIS_HOOK_PREINSTALL`: Runs before copying files, setting registry key values and creating shortcuts.
- `NSIS_HOOK_POSTINSTALL`: Runs after the installer has finished copying all files, setting the registry keys and created shortcuts.
- `NSIS_HOOK_PREUNINSTALL`: Runs before removing any files, registry keys and shortcuts.
- `NSIS_HOOK_POSTUNINSTALL`: Runs after files, registry keys and shortcuts have been removed.

For example, create a `hooks.nsh` file in the `src-tauri/windows` folder and define the hooks you need:

Then you must configure Tauri to use that hook file:

#### Installing Dependencies with Hooks

You can use installer hooks to automatically install system dependencies that your application requires. This is particularly useful for runtime dependencies like Visual C++ Redistributables, DirectX, OpenSSL or other system libraries that may not be present on all Windows systems.

**MSI Installer Example (Visual C++ Redistributable):**

**Key considerations:**

- A good practice is to always check if the dependency is already installed using registry keys or file existence or via Windows [where] command.
- Use `/passive`, `/quiet`, or `/silent` flags to avoid interrupting the installation flow. Check out [msiexec] options for `.msi` files, or the setup manual for app-specific flags
- Include `/norestart` to prevent automatic system reboots during installation for setups that restarts user devices
- Clean up temporary files and bundled installers to avoid bloating the application
- Consider that dependencies might be shared with other applications when uninstalling
- Provide meaningful error messages if installation fails

Ensure to bundle the dependency installers in your `src-tauri/resources` folder and add to `tauri.conf.json` so they get bundled, and can be accessed during installation from `$INSTDIR\resources\`:

By default the installer will install your application for the current user only.
The advantage of this option is that the installer does not require Administrator privileges to run,
but the app is installed in the `%LOCALAPPDATA%` folder instead of `C:/Program Files`.

If you prefer your app installation to be available system-wide (which requires Administrator privileges)
you can set [installMode] to `perMachine`:

Alternatively you can let the user choose whether the app should be installed for the current user only or system-wide
by setting the [installMode] to `both`.
Note that the installer will require Administrator privileges to execute.

See [NSISInstallerMode] for more information.

### Internationalization

The NSIS Installer is a multi-language installer, which means you always have a single installer which contains all the selected translations.

You can specify which languages to include using the [`tauri.bundle.windows.nsis.languages`](/reference/config/#languages) property.
A list of languages supported by NSIS is available in [the NSIS GitHub project].
There are a few [Tauri-specific translations] required, so if you see untranslated texts feel free to open a feature request in [Tauri's main repo].
You can also provide [custom translation files](/reference/config/#customlanguagefiles).

By default the operating system default language is used to determine the installer language.
You can also configure the installer to display a language selector before the installer contents are rendered:

### Minimum Webview2 version

If your app requires features only available in newer Webview2 versions (such as custom URI schemes), you can instruct the Windows installer
to verify the current Webview2 version and run the Webview2 bootstrapper if it does not match the target version.

[wix toolset v3]: https://wixtoolset.org/documentation/manual/v3/
[nsis]: https://nsis.sourceforge.io/Main_Page
[platform support]: https://doc.rust-lang.org/nightly/rustc/platform-support.html
[webviewinstallmode]: /reference/config/#webviewinstallmode
[download-webview2-runtime]: https://developer.microsoft.com/en-us/microsoft-edge/webview2/#download-section
[default wix template]: https://github.com/tauri-apps/tauri/blob/dev/crates/tauri-bundler/src/bundle/windows/msi/main.wxs
[default nsis template]: https://github.com/tauri-apps/tauri/blob/dev/crates/tauri-bundler/src/bundle/windows/nsis/installer.nsi
[handlebars]: https://docs.rs/handlebars/latest/handlebars/
[`tauri.bundle.windows.wix.template`]: /reference/config/#template-2
[`tauri.bundle.windows.nsis.template`]: /reference/config/#template-1
[wix fragment]: https://wixtoolset.org/documentation/manual/v3/xsd/wix/fragment.html
[`tauri.bundle.windows.wix.language`]: /reference/config/#language
[wix localization documentation]: https://wixtoolset.org/documentation/manual/v3/howtos/ui_and_localization/make_installer_localizable.html
[localizing the error and actiontext tables]: https://docs.microsoft.com/en-us/windows/win32/msi/localizing-the-error-and-actiontext-tables
[the nsis github project]: https://github.com/kichik/nsis/tree/9465c08046f00ccb6eda985abbdbf52c275c6c4d/Contrib/Language%20files
[tauri-specific translations]: https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-bundler/src/bundle/windows/nsis/languages
[tauri's main repo]: https://github.com/tauri-apps/tauri/issues/new?assignees=&labels=type%3A+feature+request&template=feature_request.yml&title=%5Bfeat%5D+
[signing documentation]: /distribute/sign/windows/
[WiX configuration]: /reference/config/#wixconfig
[NSIS configuration]: /reference/config/#nsisconfig
[installMode]: /reference/config/#installmode
[NSISInstallerMode]: /reference/config/#nsisinstallermode
[where]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/where
[msiexec]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/msiexec

**Examples:**

Example 1 (unknown):
```unknown
But on many other distributions you have to compile NSIS yourself or download Stubs and Plugins manually that weren't included in the distro's binary package.
Fedora for example only provides the binary but not the Stubs and Plugins:
```

Example 2 (unknown):
```unknown
</TabItem>

<TabItem label="macOS">
On macOS you will need [Homebrew] to install NSIS:
```

Example 3 (unknown):
```unknown
</TabItem>
</Tabs>

#### Install LLVM and the LLD Linker

Since the default Microsoft linker only works on Windows we will also need to install a new linker.
To compile the Windows Resource file which is used for setting the app icon among other things
we will also need the `llvm-rc` binary which is part of the LLVM project.

<Tabs syncKey="OS">
<TabItem label="Linux">
```

Example 4 (unknown):
```unknown
On Linux you also need to install the `clang` package if you added dependencies that compile C/C++ dependencies as part of their build scripts.
Default Tauri apps should not require this.

</TabItem>
<TabItem label="macOS">
```

---

## single-instance:

**URL:** llms-txt#single-instance:

---

## v20.10.0

**URL:** llms-txt#v20.10.0

---

## Distributing with CrabNebula Cloud

**URL:** llms-txt#distributing-with-crabnebula-cloud

[CrabNebula] is an official Tauri partner providing services and tooling for Tauri applications.
The [CrabNebula Cloud] is a platform for application distribution that seamlessly integrates with the Tauri updater.

The Cloud offers a Content Delivery Network (CDN) that is capable of shipping your application installers and
updates globally while being cost effective and exposing download metrics.

With the CrabNebula Cloud service it is simple to implement multiple release channels,
download buttons for your application website and more.

Setting up your Tauri app to use the Cloud is easy: all you need to do is to sign in to the [Cloud website] using your GitHub account,
create your organization and application and install its CLI to create a release and upload the Tauri bundles.
Additionally, a [GitHub Action] is provided to simplify the process of using the CLI on GitHub workflows.

For more information, see the [CrabNebula Cloud documentation].

[CrabNebula]: https://crabnebula.dev
[CrabNebula Cloud]: https://crabnebula.dev/cloud/
[GitHub Action]: https://github.com/crabnebula-dev/cloud-release/
[Cloud website]: https://web.crabnebula.cloud/
[CrabNebula Cloud documentation]: https://docs.crabnebula.dev/cloud/

---

## System Tray

**URL:** llms-txt#system-tray

**Contents:**
- Configuration
- Usage
  - Create a Tray Icon
  - Change the Tray Icon
  - Add a Menu
  - Listen to Tray Events

import { Icon } from '@astrojs/starlight/components';
import { Tabs, TabItem } from '@astrojs/starlight/components';

Tauri allows you to create and customize a system tray for your application.
This can enhance the user experience by providing quick access to common actions.

First of all, update your `Cargo.toml` to include the necessary feature for the system tray.

The tray API is available in both JavaScript and Rust.

### Create a Tray Icon

<Tabs synckey="language">
<TabItem label="JavaScript">
Use the [`TrayIcon.new`] static function to create a new tray icon:

See [`TrayIconOptions`] for more information on the customization options.

<TabItem label="Rust">

See [`TrayIconBuilder`] for more information on customization options.

### Change the Tray Icon

When creating the tray you can use the application icon as the tray icon:

<Tabs syncKey="lang">
<TabItem label="JavaScript">

<TabItem label="Rust">

To attach a menu that is displayed when the tray is clicked, you can use the `menu` option.

:::note
By default the menu is displayed on both left and right clicks.

To prevent the menu from popping up on left click, call the [`menu_on_left_click(false)`][TrayIconBuilder::menu_on_left_click] Rust function
or set the [`menuOnLeftClick`] JavaScript option to `false`.
:::

{/* TODO: link to the menu plugin documentation page */}

<Tabs syncKey="lang">
<TabItem label="JavaScript">

<TabItem label="Rust">

#### Listen to Menu Events

<Tabs syncKey="lang">
<TabItem label="JavaScript">
On JavaScript you can attach a menu click event listener directly to the menu item:

- Using a shared menu click handler

- Using a dedicated menu click handler

<TabItem label="Rust">
Use the [`TrayIconBuilder::on_menu_event`] method to attach a tray menu click event listener:

### Listen to Tray Events

The tray icon emits events for the following mouse events:

- click: triggered when the cursor receives a single left, right or middle click, including information on whether the mouse press was released or not
- Double click: triggered when the cursor receives a double left, right or middle click
- Enter: triggered when the cursor enters the tray icon area
- Move: triggered when the cursor moves around the tray icon area
- Leave: triggered when the cursor leaves the tray icon area

:::note
Linux: Unsupported. The event is not emitted even though the icon is shown and will still show a context menu on right click.
:::

<Tabs>
<TabItem label="JavaScript">

See [`TrayIconEvent`][js TrayIconEvent] for more information on the event payload.

<TabItem label="Rust">

See [`TrayIconEvent`][rust TrayIconEvent] for more information on the event type.

For detailed information about creating menus, including menu items, submenus, and dynamic updates, see the [Window Menu](/learn/window-menu/) documentation.

[`TrayIcon.new`]: /reference/javascript/api/namespacetray/#new
[`TrayIconOptions`]: /reference/javascript/api/namespacetray/#trayiconoptions
[`TrayIconBuilder`]: https://docs.rs/tauri/2.0.0/tauri/tray/struct.TrayIconBuilder.html
[TrayIconBuilder::menu_on_left_click]: https://docs.rs/tauri/2.0.0/tauri/tray/struct.TrayIconBuilder.html#method.menu_on_left_click
[`menuOnLeftClick`]: /reference/javascript/api/namespacetray/#properties-1
[`TrayIconBuilder::on_menu_event`]: https://docs.rs/tauri/2.0.0/tauri/tray/struct.TrayIconBuilder.html#method.on_menu_event
[js TrayIconEvent]: /reference/javascript/api/namespacetray/#trayiconevent
[rust TrayIconEvent]: https://docs.rs/tauri/2.0.0/tauri/tray/enum.TrayIconEvent.html

**Examples:**

Example 1 (unknown):
```unknown
## Usage

The tray API is available in both JavaScript and Rust.

### Create a Tray Icon

<Tabs synckey="language">
<TabItem label="JavaScript">
Use the [`TrayIcon.new`] static function to create a new tray icon:
```

Example 2 (unknown):
```unknown
See [`TrayIconOptions`] for more information on the customization options.

</TabItem>

<TabItem label="Rust">
```

Example 3 (unknown):
```unknown
See [`TrayIconBuilder`] for more information on customization options.

</TabItem>
</Tabs>

### Change the Tray Icon

When creating the tray you can use the application icon as the tray icon:

<Tabs syncKey="lang">
<TabItem label="JavaScript">
```

Example 4 (unknown):
```unknown
</TabItem>

<TabItem label="Rust">
```

---

## Tests

**URL:** llms-txt#tests

Tauri offers support for both unit and integration testing utilizing a mock runtime. Under the mock runtime, native
webview libraries are not executed. [See more about the mock runtime here].

Tauri also provides support for end-to-end testing support utilizing the WebDriver protocol. Both desktop and mobile
work with it, except for macOS which does not provide a desktop WebDriver client. [See more about WebDriver support here].

We offer [tauri-action] to help run GitHub actions, but any sort of CI/CD runner can be used with Tauri as long as each
platform has the required libraries installed to compile against.

[See more about the mock runtime here]: /develop/tests/mocking/
[See more about WebDriver support here]: /develop/tests/webdriver/
[tauri-action]: https://github.com/tauri-apps/tauri-action

---

## Embedding External Binaries

**URL:** llms-txt#embedding-external-binaries

**Contents:**
- Running it from Rust
- Running it from JavaScript
- Passing arguments

You may need to embed external binaries to add additional functionality to your application or prevent users from installing additional dependencies (e.g., Node.js or Python). We call this binary a `sidecar`.

Binaries are executables written in any programming language. Common use cases are Python CLI applications or API servers bundled using `pyinstaller`.

To bundle the binaries of your choice, you can add the `externalBin` property to the `tauri > bundle` object in your `tauri.conf.json`.
The `externalBin` configuration expects a list of strings targeting binaries either with absolute or relative paths.

Here is a Tauri configuration snippet to illustrate a sidecar configuration:

The relative paths are relative to the `tauri.conf.json` file which is in the `src-tauri` directory.
So `binaries/my-sidecar` would represent `<PROJECT ROOT>/src-tauri/binaries/my-sidecar`.

To make the external binary work on each supported architecture, a binary with the same name and a `-$TARGET_TRIPLE` suffix must exist on the specified path.
For instance, `"externalBin": ["binaries/my-sidecar"]` requires a `src-tauri/binaries/my-sidecar-x86_64-unknown-linux-gnu` executable on Linux or `src-tauri/binaries/my-sidecar-aarch64-apple-darwin` on Mac OS with Apple Silicon.

You can find your **current** platform's `-$TARGET_TRIPLE` suffix by looking at the `host:` property reported by the following command:

If the `grep` and `cut` commands are available, as they should on most Unix systems, you can extract the target triple directly with the following command:

On Windows you can use PowerShell instead:

Here's a Node.js script to append the target triple to a binary:

Note that this script will not work if you compile for a different architecture than the one its running on,
so only use it as a starting point for your own build scripts.

## Running it from Rust

:::note
Please follow the [shell plugin guide](/plugin/shell/) first to set up and initialize the plugin correctly.
Without the plugin being initialized and configured the example won't work.
:::

On the Rust side, import the `tauri_plugin_shell::ShellExt` trait and call the `shell().sidecar()` function on the AppHandle:

:::note
The `sidecar()` function expects just the filename, NOT the whole path configured in the `externalBin` array.

Given the following configuration:

The appropriate way to execute the sidecar is by calling `app.shell().sidecar(name)` where `name` is either `"app"`, `"my-sidecar"` or `"sidecar"`
instead of `"binaries/app"` for instance.

You can place this code inside a Tauri command to easily pass the AppHandle or you can store a reference to the AppHandle in the builder script to access it elsewhere in your application.

## Running it from JavaScript

When running the sidecar, Tauri requires you to give the sidecar permission to run the `execute` or `spawn` method on the child process. To grant this permission, go to the file `<PROJECT ROOT>/src-tauri/capabilities/default.json` and add the section below to the permissions array. Don't forget to name your sidecar according to the relative path mentioned earlier.

The `shell:allow-execute` identifier is used because the sidecar's child process will be started using the `command.execute()` method. To run it with `command.spawn()`, you need to change the identifier to `shell:allow-spawn` or add another entry to the array with the same structure as the one above, but with the identifier set to `shell:allow-spawn`.

In the JavaScript code, import the `Command` class from the `@tauri-apps/plugin-shell` module and use the `sidecar` static method.

:::note
The string provided to `Command.sidecar` must match one of the strings defined in the `externalBin` configuration array.
:::

You can pass arguments to Sidecar commands just like you would for running normal [Command][std::process::Command].

Arguments can be either **static** (e.g. `-o` or `serve`) or **dynamic** (e.g. `<file_path>` or `localhost:<PORT>`). A value of `true` will allow any arguments to be passed to the command. `false` will disable all arguments. If neither `true` or `false` is set, you define the arguments in the exact order in which you'd call them. Static arguments are defined as-is, while dynamic arguments can be defined using a regular expression.

First, define the arguments that need to be passed to the sidecar command in `src-tauri/capabilities/default.json`:

:::note
If you are migrating from Tauri v1, the `migrate` command in Tauri v2 CLI should take care of this for you. Read [Automated Migration](/start/migrate/from-tauri-1/#automated-migration) for more.
:::

Then, to call the sidecar command, simply pass in **all** the arguments as an array.

[std::process::Command]: https://doc.rust-lang.org/std/process/struct.Command.html

**Examples:**

Example 1 (unknown):
```unknown
:::note

The relative paths are relative to the `tauri.conf.json` file which is in the `src-tauri` directory.
So `binaries/my-sidecar` would represent `<PROJECT ROOT>/src-tauri/binaries/my-sidecar`.

:::

To make the external binary work on each supported architecture, a binary with the same name and a `-$TARGET_TRIPLE` suffix must exist on the specified path.
For instance, `"externalBin": ["binaries/my-sidecar"]` requires a `src-tauri/binaries/my-sidecar-x86_64-unknown-linux-gnu` executable on Linux or `src-tauri/binaries/my-sidecar-aarch64-apple-darwin` on Mac OS with Apple Silicon.

You can find your **current** platform's `-$TARGET_TRIPLE` suffix by looking at the `host:` property reported by the following command:
```

Example 2 (unknown):
```unknown
If the `grep` and `cut` commands are available, as they should on most Unix systems, you can extract the target triple directly with the following command:
```

Example 3 (unknown):
```unknown
On Windows you can use PowerShell instead:
```

Example 4 (unknown):
```unknown
Here's a Node.js script to append the target triple to a binary:
```

---

## 10.2.3

**URL:** llms-txt#10.2.3

**Contents:**
- Configure for Mobile Targets
  - Android
  - iOS
- Troubleshooting

sh
export JAVA_HOME=/opt/android-studio/jbr
sh
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
ps
[System.Environment]::SetEnvironmentVariable("JAVA_HOME", "C:\Program Files\Android\Android Studio\jbr", "User")
sh
export ANDROID_HOME="$HOME/Android/Sdk"
export NDK_HOME="$ANDROID_HOME/ndk/$(ls -1 $ANDROID_HOME/ndk)"
sh
export ANDROID_HOME="$HOME/Library/Android/sdk"
export NDK_HOME="$ANDROID_HOME/ndk/$(ls -1 $ANDROID_HOME/ndk)"
ps
[System.Environment]::SetEnvironmentVariable("ANDROID_HOME", "$env:LocalAppData\Android\Sdk", "User")
$VERSION = Get-ChildItem -Name "$env:LocalAppData\Android\Sdk\ndk" | Select-Object -Last 1
[System.Environment]::SetEnvironmentVariable("NDK_HOME", "$env:LocalAppData\Android\Sdk\ndk\$VERSION", "User")
ps
[System.Environment]::GetEnvironmentVariables("User").GetEnumerator() | % { Set-Item -Path "Env:\$($_.key)" -Value $_.value }
sh
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android
sh
rustup target add aarch64-apple-ios x86_64-apple-ios aarch64-apple-ios-sim
sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
sh
brew install cocoapods
```

Next: [Create a project](/start/create-project/).

If you run into any issues during installation be sure to check the [Troubleshooting Guide](/develop/debug/) or reach out on the [Tauri Discord](https://discord.com/invite/tauri).

<Card title="Next Steps" icon="rocket">

Now that you've installed all of the prerequisites you're ready to [create your first Tauri project](/start/create-project/)!

**Examples:**

Example 1 (unknown):
```unknown
It's important to restart your Terminal to ensure it recognizes the new installation. In some cases, you might need to restart your computer.

While npm is the default package manager for Node.js, you can also use others like pnpm or yarn. To enable these, run `corepack enable` in your Terminal. This step is optional and only needed if you prefer using a package manager other than npm.

Next: [Configure for Mobile Targets](#configure-for-mobile-targets) or [Create a project](/start/create-project/).

## Configure for Mobile Targets

If you'd like to target your app for Android or iOS then there are a few additional dependencies that you need to install:

- [Android](#android)
- [iOS](#ios)

### Android

1. Download and install [Android Studio from the Android Developers website](https://developer.android.com/studio)
2. Set the `JAVA_HOME` environment variable:

{/* TODO: Can this be done in the 4th step? */}

<Tabs syncKey="prereqs">
<TabItem label="Linux">
```

Example 2 (unknown):
```unknown
</TabItem>
<TabItem label="macOS">
```

Example 3 (unknown):
```unknown
</TabItem>
<TabItem label="Windows">
```

Example 4 (unknown):
```unknown
</TabItem>
</Tabs>
3. Use the SDK Manager in Android Studio to install the following:

- Android SDK Platform
- Android SDK Platform-Tools
- NDK (Side by side)
- Android SDK Build-Tools
- Android SDK Command-line Tools

Selecting "Show Package Details" in the SDK Manager enables the installation of older package versions. Only install older versions if necessary, as they may introduce compatibility issues or security risks.

4. Set `ANDROID_HOME` and `NDK_HOME` environment variables.

<Tabs syncKey="prereqs">
<TabItem label="Linux">
```

---

## DMG

**URL:** llms-txt#dmg

**Contents:**
- Window background
- Window size and position
- Icon position

import CommandTabs from '@components/CommandTabs.astro';
import { Image } from 'astro:assets';
import StandardDmgLight from '@assets/distribute/dmg/standard-dmg-light.png';
import StandardDmgDark from '@assets/distribute/dmg/standard-dmg-dark.png';

The DMG (Apple Disk Image) format is a common macOS installer file that wraps your [App Bundle][App Bundle distribution guide] in a user-friendly installation window.

The installer window includes your app icon and the Applications folder icon, where the user is expected to drag the app icon to the Applications folder icon to install it.
It is the most common installation method for macOS applications distributed outside the App Store.

This guide only covers details for distributing apps outside the App Store using the DMG format.
See the [App Bundle distribution guide] for more information on macOS distribution options and configurations.
To distribute your macOS app in the App Store, see the [App Store distribution guide].

To create an Apple Disk Image for your app you can use the Tauri CLI and run the `tauri build` command in a Mac computer:

<CommandTabs
  npm="npm run tauri build -- --bundles dmg"
  yarn="yarn tauri build --bundles dmg"
  pnpm="pnpm tauri build --bundles dmg"
  deno="deno task tauri build --bundles dmg"
  bun="bun tauri build --bundles dmg"
  cargo="cargo tauri build --bundles dmg"
/>

<Image
  class="dark:sl-hidden"
  src={StandardDmgLight}
  alt="Standard DMG window"
/>
<Image
  class="light:sl-hidden"
  src={StandardDmgDark}
  alt="Standard DMG window"
/>

GUI apps on macOS and Linux do not inherit the `$PATH` from your shell dotfiles (`.bashrc`, `.bash_profile`, `.zshrc`, etc). Check out Tauri's [fix-path-env-rs](https://github.com/tauri-apps/fix-path-env-rs) crate to fix this issue.

You can set a custom background image to the DMG installation window with the [`tauri.conf.json > bundle > macOS > dmg > background`] configuration option:

For instance your DMG background image can include an arrow to indicate to the user that it must drag the app icon to the Applications folder.

## Window size and position

The default window size is 660x400. If you need a different size to fit your custom background image, set the [`tauri.conf.json > bundle > macOS > dmg > windowSize`] configuration:

Additionally you can set the initial window position via [`tauri.conf.json > bundle > macOS > dmg > windowPosition`]:

You can change the app and _Applications folder_ icon position
with the [appPosition] and [applicationFolderPosition] configuration values respectively:

:::caution
Due to a known issue, icon sizes and positions are not applied when creating DMGs on CI/CD platforms.
See [tauri-apps/tauri#1731] for more information.
:::

[App Bundle distribution guide]: /distribute/macos-application-bundle/
[App Store distribution guide]: /distribute/app-store/
[appPosition]: /reference/config/#appposition
[applicationFolderPosition]: /reference/config/#applicationfolderposition
[tauri-apps/tauri#1731]: https://github.com/tauri-apps/tauri/issues/1731

**Examples:**

Example 1 (unknown):
```unknown
For instance your DMG background image can include an arrow to indicate to the user that it must drag the app icon to the Applications folder.

## Window size and position

The default window size is 660x400. If you need a different size to fit your custom background image, set the [`tauri.conf.json > bundle > macOS > dmg > windowSize`] configuration:
```

Example 2 (unknown):
```unknown
Additionally you can set the initial window position via [`tauri.conf.json > bundle > macOS > dmg > windowPosition`]:
```

Example 3 (unknown):
```unknown
## Icon position

You can change the app and _Applications folder_ icon position
with the [appPosition] and [applicationFolderPosition] configuration values respectively:
```

---

## Contributor:

**URL:** llms-txt#contributor:

**Contents:**
  - Building from source

pkgname=<pkgname>
pkgver=1.0.0
pkgrel=1
pkgdesc="Description of your app"
arch=('x86_64' 'aarch64')
url="https://github.com/<user>/<project>"
license=('MIT')
depends=('cairo' 'desktop-file-utils' 'gdk-pixbuf2' 'glib2' 'gtk3' 'hicolor-icon-theme' 'libsoup' 'pango' 'webkit2gtk-4.1')
options=('!strip' '!debug')
install=${pkgname}.install
source_x86_64=("${url}/releases/download/v${pkgver}/appname_${pkgver}_amd64.deb")
source_aarch64=("${url}/releases/download/v${pkgver}/appname_${pkgver}_arm64.deb")
sha256sums_x86_64=('ca85f11732765bed78f93f55397b4b4cbb76685088553dad612c5062e3ec651f')
sha256sums_aarch64=('ed2dc3169d34d91188fb55d39867713856dd02a2360ffe0661cb2e19bd701c3c')
package() {
	# Extract package data
	tar -xvf data.tar.gz -C "${pkgdir}"

}
ini title="my-tauri-app.install"
post_install() {
	gtk-update-icon-cache -q -t -f usr/share/icons/hicolor
	update-desktop-database -q
}

post_upgrade() {
	post_install
}

post_remove() {
	gtk-update-icon-cache -q -t -f usr/share/icons/hicolor
	update-desktop-database -q
}

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown
### Building from source
```

---

## Upgrade & Migrate

**URL:** llms-txt#upgrade-&-migrate

Learn about common scenarios and steps to upgrade from Tauri 1.0 or migrate from another framework.

import { LinkCard, CardGrid } from '@astrojs/starlight/components';

<CardGrid>
  <LinkCard
    title="Upgrade from Tauri 1.0"
    href="/start/migrate/from-tauri-1/"
    description="Read more about the updates you need to make to a version 1 project in order to upgrade to version 2."
  />
  <LinkCard
    title="Migrate from Tauri 2.0 beta"
    href="/start/migrate/from-tauri-2-beta/"
    description="Read more about the updates required for the 2.0 beta project to upgrade to 2.0."
  />
</CardGrid>

---

## Cargo.toml

**URL:** llms-txt#cargo.toml

**Contents:**
  - Migrate to Tray Icon Module
  - Migrate to Updater Plugin
  - Migrate Path to Tauri Manager
  - Migrate to new Window API
  - Migrate Embedded Additional Files (Resources)
  - Migrate Embedded External Binaries (Sidecar)
  - Migrate Permissions

[dependencies]
tauri-plugin-shell = "2"
rust
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
}
json
// package.json
{
  "dependencies": {
    "@tauri-apps/plugin-shell": "^2.0.0"
  }
}
javascript
import { Command, open } from '@tauri-apps/plugin-shell';
const output = await Command.create('echo', 'message').execute();

await open('https://github.com/tauri-apps/tauri');
rust
use tauri_plugin_shell::ShellExt;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            app.shell().open("https://github.com/tauri-apps/tauri", None)?;
            Ok(())
        })
}
rust
use tauri_plugin_shell::ShellExt;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let status = tauri::async_runtime::block_on(async move { app.shell().command("which").args(["ls"]).status().await.unwrap() });
            println!("`which` finished with status: {:?}", status.code());
            Ok(())
        })
}
rust
use tauri_plugin_shell::ShellExt;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let output = tauri::async_runtime::block_on(async move { app.shell().command("echo").args(["TAURI"]).output().await.unwrap() });
            assert!(output.status.success());
            assert_eq!(String::from_utf8(output.stdout).unwrap(), "TAURI");
            Ok(())
        })
}
rust
use tauri_plugin_shell::{ShellExt, process::CommandEvent};

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                let (mut rx, mut child) = handle.shell().command("cargo")
                    .args(["tauri", "dev"])
                    .spawn()
                    .expect("Failed to spawn cargo");

let mut i = 0;
                while let Some(event) = rx.recv().await {
                    if let CommandEvent::Stdout(line) = event {
                        println!("got: {}", String::from_utf8(line).unwrap());
                       i += 1;
                       if i == 4 {
                           child.write("message from Rust\n".as_bytes()).unwrap();
                           i = 0;
                       }
                   }
                }
            });
            Ok(())
        })
}
rust
let tray = tauri::tray::TrayIconBuilder::with_id("my-tray").build(app)?;
rust
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};

tauri::Builder::default()
    .setup(|app| {
        let toggle = MenuItemBuilder::with_id("toggle", "Toggle").build(app)?;
        let menu = MenuBuilder::new(app).items(&[&toggle]).build()?;
        let tray = TrayIconBuilder::new()
            .menu(&menu)
            .on_menu_event(move |app, event| match event.id().as_ref() {
                "toggle" => {
                    println!("toggle clicked");
                }
                _ => (),
            })
            .on_tray_icon_event(|tray, event| {
                if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                } = event
                {
                    let app = tray.app_handle();
                    if let Some(webview_window) = app.get_webview_window("main") {
                       let _ = webview_window.unminimize();
                       let _ = webview_window.show();
                       let _ = webview_window.set_focus();
                    }
                }
            })
            .build(app)?;

Ok(())
    })
toml
[dependencies]
tauri-plugin-updater = "2"
rust
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
}
json
// package.json
{
  "dependencies": {
    "@tauri-apps/plugin-updater": "^2.0.0"
  }
}
javascript
import { check } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';

const update = await check();
if (update?.available) {
  console.log(`Update to ${update.version} available! Date: ${update.date}`);
  console.log(`Release notes: ${update.body}`);
  await update.downloadAndInstall();
  // requires the `process` plugin
  await relaunch();
}
rust
use tauri_plugin_updater::UpdaterExt;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            let handle = app.handle();
            tauri::async_runtime::spawn(async move {
                let response = handle.updater().check().await;
            });
            Ok(())
        })
}
rust
fn main() {
    let mut updater = tauri_plugin_updater::Builder::new();
    #[cfg(target_os = "macos")]
    {
        updater = updater.target("darwin-universal");
    }
    tauri::Builder::default()
        .plugin(updater.build())
}
rust
use tauri::{path::BaseDirectory, Manager};

tauri::Builder::default()
    .setup(|app| {
        let home_dir_path = app.path().home_dir().expect("failed to get home dir");

let path = app.path().resolve("path/to/something", BaseDirectory::Config)?;

### Migrate to new Window API

On the Rust side, `Window` was renamed to `WebviewWindow`, its builder `WindowBuilder` is now named `WebviewWindowBuilder` and `WindowUrl` is now named `WebviewUrl`.

Additionally, the `Manager::get_window` function was renamed to `get_webview_window` and
the window's `parent_window` API was renamed to `parent_raw` to support a high level window parent API.

On the JavaScript side, the `WebviewWindow` class is now exported in the `@tauri-apps/api/webviewWindow` path.

The `onMenuClicked` function was removed, you can intercept menu events when creating a menu in JavaScript instead.

### Migrate Embedded Additional Files (Resources)

On the JavaScript side, make sure you [Migrate to File System Plugin](#migrate-to-file-system-plugin).
Additionally, note the changes made to the v1 allowlist in [Migrate Permissions](#migrate-permissions).

On the Rust side, make sure you [Migrate Path to Tauri Manager](#migrate-path-to-tauri-manager).

### Migrate Embedded External Binaries (Sidecar)

In Tauri v1, the external binaries and their arguments were defined in the allowlist. In v2, use the new permissions system. Read [Migrate Permissions](#migrate-permissions) for more information.

On the JavaScript side, make sure you [Migrate to Shell Plugin](#migrate-to-shell-plugin).

On the Rust side, `tauri::api::process` API has been removed. Use `tauri_plugin_shell::ShellExt` and `tauri_plugin_shell::process::CommandEvent` APIs instead. Read the [Embedding External Binaries](/develop/sidecar/#running-it-from-rust) guide to see how.

The "process-command-api" features flag has been removed in v2. So running the external binaries does not require this feature to be defined in the Tauri config anymore.

### Migrate Permissions

The v1 allowlist have been rewritten to a completely new system for permissions that works for individual plugins and is much more configurable for multiwindow and remote URL support.
This new system works like an access control list (ACL) where you can allow or deny commands, allocate permissions to a specific set of windows and domains, and define access scopes.

To enable permissions for your app, you must create capability files inside the `src-tauri/capabilities` folder, and Tauri will automatically configure everything else for you.

The `migrate` CLI command automatically parses your v1 allowlist and generates the associated capability file.

To learn more about permissions and capabilities, see [the security documentation](/security/).

**Examples:**

Example 1 (unknown):
```unknown
2. Use in JavaScript or Rust project:

<Tabs syncKey="lang">
<TabItem label="JavaScript">
```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</TabItem>
<TabItem label="Rust">

- Open an URL
```

---

## AUR

**URL:** llms-txt#aur

---

## Run it

**URL:** llms-txt#run-it

flatpak run <your flatpak id> # or via your desktop environment

---

## WebdriverIO

**URL:** llms-txt#webdriverio

**Contents:**
- Create a Directory for the Tests
- Initializing a WebdriverIO Project
- Config
- Spec
- Running the Test Suite

import CommandTabs from '@components/CommandTabs.astro';

Make sure to go through the [prerequisites instructions] to be able to follow this guide.

This WebDriver testing example will use [WebdriverIO], and its testing suite. It is expected to have Node.js already
installed, along with `npm` or `yarn` although the [finished example project] uses `pnpm`.

## Create a Directory for the Tests

Let's create a space to write these tests in our project. We will be using a nested directory for
this example project as we will later also go over other frameworks, but typically you only need to use one. Create
the directory we will use with `mkdir e2e-tests`. The rest of this guide assumes you are inside the
`e2e-tests` directory.

## Initializing a WebdriverIO Project

We will be using a pre-existing `package.json` to bootstrap this test suite because we have already chosen specific
[WebdriverIO] config options and want to showcase a simple working solution. The bottom of this section has a collapsed
guide on setting it up from scratch.

We have a script that runs a [WebdriverIO] config as a test suite exposed as the `test` command. We also have various
dependencies added by the `@wdio/cli` command when we first set it up. In short, these dependencies are for
the most simple setup using a local WebDriver runner, [Mocha] as the test framework, and a simple Spec Reporter.

<details>
  <summary>Click me if you want to see how to set a project up from scratch</summary>

The CLI is interactive, and you may choose the tools to work with yourself. Note that you will likely diverge from
the rest of the guide, and you need to set up the differences yourself.

Let's add the [WebdriverIO] CLI to this npm project.

<CommandTabs npm="npm install @wdio/cli" yarn="yarn add @wdio/cli" />

To then run the interactive config command to set up a [WebdriverIO] test suite, you can then run:

<CommandTabs npm="npx wdio config" yarn="yarn wdio config" />

You may have noticed that the `test` script in our `package.json` mentions a file `wdio.conf.js`. That's the [WebdriverIO]
config file which controls most aspects of our testing suite.

If you are interested in the properties on the `config` object, we [suggest reading the documentation][webdriver documentation].
For non-WDIO specific items, there are comments explaining why we are running commands in `onPrepare`, `beforeSession`,
and `afterSession`. We also have our specs set to `"./test/specs/**/*.js"`, so let's create a spec now.

A spec contains the code that is testing your actual application. The test runner will load these specs and automatically
run them as it sees fit. Let's create our spec now in the directory we specified.

`test/specs/example.e2e.js`:

The `luma` function on top is just a helper function for one of our tests and is not related to the actual testing of
the application. If you are familiar with other testing frameworks, you may notice similar functions being exposed that
are used, such as `describe`, `it`, and `expect`. The other APIs, such as items like `$` and its exposed methods, are
covered by the [WebdriverIO API docs].

## Running the Test Suite

Now that we are all set up with config and a spec let's run it!

<CommandTabs npm="npm test" yarn="yarn test" />

We should see output the following output:

We see the Spec Reporter tell us that all 3 tests from the `test/specs/example.e2e.js` file, along with the final report
`Spec Files: 1 passed, 1 total (100% completed) in 00:00:01`.

Using the [WebdriverIO] test suite, we just easily enabled e2e testing for our Tauri application from just a few lines
of configuration and a single command to run it! Even better, we didn't have to modify the application at all.

[prerequisites instructions]: /develop/tests/webdriver/
[webdriverio]: https://webdriver.io/
[finished example project]: https://github.com/tauri-apps/webdriver-example
[mocha]: https://mochajs.org/
[webdriver documentation]: https://webdriver.io/docs/configurationfile
[webdriverio api docs]: https://webdriver.io/docs/api

**Examples:**

Example 1 (json):
```json
{
  "name": "webdriverio",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "wdio run wdio.conf.js"
  },
  "dependencies": {
    "@wdio/cli": "^9.19.0"
  },
  "devDependencies": {
    "@wdio/local-runner": "^9.19.0,
    "@wdio/mocha-framework": "^9.19.0",
    "@wdio/spec-reporter": "^9.19.0"
  }
}
```

Example 2 (javascript):
```javascript
import os from 'os';
import path from 'path';
import { spawn, spawnSync } from 'child_process';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

// keep track of the `tauri-driver` child process
let tauriDriver;
let exit = false;

export const config = {
  host: '127.0.0.1',
  port: 4444,
  specs: ['./develop/tests/specs/**/*.js'],
  maxInstances: 1,
  capabilities: [
    {
      maxInstances: 1,
      'tauri:options': {
        application: '../src-tauri/target/debug/tauri-app',
      },
    },
  ],
  reporters: ['spec'],
  framework: 'mocha',
  mochaOpts: {
    ui: 'bdd',
    timeout: 60000,
  },

  // ensure the rust project is built since we expect this binary to exist for the webdriver sessions
  onPrepare: () => {
    // Remove the extra `--` if you're not using npm!
    spawnSync(
      'npm',
      ['run', 'tauri', 'build', '--', '--debug', '--no-bundle'],
      {
        cwd: path.resolve(__dirname, '..'),
        stdio: 'inherit',
        shell: true,
      }
    );
  },

  // ensure we are running `tauri-driver` before the session starts so that we can proxy the webdriver requests
  beforeSession: () => {
    tauriDriver = spawn(
      path.resolve(os.homedir(), '.cargo', 'bin', 'tauri-driver'),
      [],
      { stdio: [null, process.stdout, process.stderr] }
    );

    tauriDriver.on('error', (error) => {
      console.error('tauri-driver error:', error);
      process.exit(1);
    });
    tauriDriver.on('exit', (code) => {
      if (!exit) {
        console.error('tauri-driver exited with code:', code);
        process.exit(1);
      }
    });
  },

  // clean up the `tauri-driver` process we spawned at the start of the session
  // note that afterSession might not run if the session fails to start, so we also run the cleanup on shutdown
  afterSession: () => {
    closeTauriDriver();
  },
};

function closeTauriDriver() {
  exit = true;
  tauriDriver?.kill();
}

function onShutdown(fn) {
  const cleanup = () => {
    try {
      fn();
    } finally {
      process.exit();
    }
  };

  process.on('exit', cleanup);
  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
  process.on('SIGHUP', cleanup);
  process.on('SIGBREAK', cleanup);
}

// ensure tauri-driver is closed when our test process exits
onShutdown(() => {
  closeTauriDriver();
});
```

Example 3 (javascript):
```javascript
// calculates the luma from a hex color `#abcdef`
function luma(hex) {
  if (hex.startsWith('#')) {
    hex = hex.substring(1);
  }

  const rgb = parseInt(hex, 16);
  const r = (rgb >> 16) & 0xff;
  const g = (rgb >> 8) & 0xff;
  const b = (rgb >> 0) & 0xff;
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

describe('Hello Tauri', () => {
  it('should be cordial', async () => {
    const header = await $('body > h1');
    const text = await header.getText();
    expect(text).toMatch(/^[hH]ello/);
  });

  it('should be excited', async () => {
    const header = await $('body > h1');
    const text = await header.getText();
    expect(text).toMatch(/!$/);
  });

  it('should be easy on the eyes', async () => {
    const body = await $('body');
    const backgroundColor = await body.getCSSProperty('background-color');
    expect(luma(backgroundColor.parsed.hex)).toBeLessThan(100);
  });
});
```

Example 4 (text):
```text
➜  webdriverio git:(main) ✗ yarn test
yarn run v1.22.11
$ wdio run wdio.conf.js

Execution of 1 workers started at 2021-08-17T08:06:10.279Z

[0-0] RUNNING in undefined - /develop/tests/specs/example.e2e.js
[0-0] PASSED in undefined - /develop/tests/specs/example.e2e.js

 "spec" Reporter:
------------------------------------------------------------------
[wry 0.12.1 linux #0-0] Running: wry (v0.12.1) on linux
[wry 0.12.1 linux #0-0] Session ID: 81e0107b-4d38-4eed-9b10-ee80ca47bb83
[wry 0.12.1 linux #0-0]
[wry 0.12.1 linux #0-0] » /develop/tests/specs/example.e2e.js
[wry 0.12.1 linux #0-0] Hello Tauri
[wry 0.12.1 linux #0-0]    ✓ should be cordial
[wry 0.12.1 linux #0-0]    ✓ should be excited
[wry 0.12.1 linux #0-0]    ✓ should be easy on the eyes
[wry 0.12.1 linux #0-0]
[wry 0.12.1 linux #0-0] 3 passing (244ms)


Spec Files:	 1 passed, 1 total (100% completed) in 00:00:01

Done in 1.98s.
```

---
