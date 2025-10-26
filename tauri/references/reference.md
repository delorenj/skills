# Tauri - Reference

**Pages:** 9

---

## Window Customization

**URL:** llms-txt#window-customization

**Contents:**
- Configuration
- Usage
  - Creating a Custom Titlebar
  - Manual Implementation of `data-tauri-drag-region`
  - (macOS) Transparent Titlebar with Custom Window Background Color

import { Icon } from '@astrojs/starlight/components';

Tauri provides lots of options for customizing the look and feel of your app's window. You can create custom titlebars, have transparent windows, enforce size constraints, and more.

There are three ways to change the window configuration:

- <Icon name="external" class="inline-icon" /> [Through
  tauri.conf.json](/reference/config/#windowconfig)
- <Icon name="external" class="inline-icon" /> [Through the JavaScript
  API](/reference/javascript/api/namespacewindow/#window)
- <Icon name="external" class="inline-icon" /> [Through the Window in
  Rust](https://docs.rs/tauri/2.0.0/tauri/window/struct.Window.html)

- [Creating a Custom Titlebar](#creating-a-custom-titlebar)
- [(macOS) Transparent Titlebar with Custom Window Background Color](#macos-transparent-titlebar-with-custom-window-background-color)

### Creating a Custom Titlebar

A common use of these window features is creating a custom titlebar. This short tutorial will guide you through that process.

:::note
For macOS, using a custom titlebar will also lose some features provided by the system, such as [moving or aligning the window](https://support.apple.com/guide/mac-help/work-with-app-windows-mchlp2469/mac). Another approach to customizing the titlebar but keeping native functions could be making the titlebar transparent and setting the window background color. See the usage [(macOS) Transparent Titlebar with Custom Window Background Color](#macos-transparent-titlebar-with-custom-window-background-color).
:::

Set `decorations` to `false` in your `tauri.conf.json`:

Add window permissions in capability file.

By default, all plugin commands are blocked and cannot be accessed. You must define a list of permissions in your `capabilities` configuration.

See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions.

| Permission                                   | Description                                                                    |
| -------------------------------------------- | ------------------------------------------------------------------------------ |
| `core:window:default`                        | Default permissions for the plugin. Except `window:allow-start-dragging`.      |
| `core:window:allow-close`                    | Enables the close command without any pre-configured scope.                    |
| `core:window:allow-minimize`                 | Enables the minimize command without any pre-configured scope.                 |
| `core:window:allow-start-dragging`           | Enables the start_dragging command without any pre-configured scope.           |
| `core:window:allow-toggle-maximize`          | Enables the toggle_maximize command without any pre-configured scope.          |
| `core:window:allow-internal-toggle-maximize` | Enables the internal_toggle_maximize command without any pre-configured scope. |

Add this CSS sample to keep it at the top of the screen and style the buttons:

Put this at the top of your `<body>` tag:

Note that you may need to move the rest of your content down so that the titlebar doesn't cover it.

On Windows, if you just want a title bar that doesn't need custom interactions, you can use

to make the title bar work with touch and pen inputs

Use this code snippet to make the buttons work:

Note that if you are using a Rust-based frontend, you can copy the code above into a `<script>` element in your `index.html` file.

:::note
`data-tauri-drag-region` will only work on the element to which it is directly applied. If you want the drag behavior to apply to child elements as well, you'll need to add it to each child individually.

This behavior is preserved so that interactive elements like buttons and inputs can function properly.
:::

### Manual Implementation of `data-tauri-drag-region`

For use cases where you customize the drag behavior, you can manually add an event listener with `window.startDragging` instead of using `data-tauri-drag-region`.

From the code in the previous section, we remove `data-tauri-drag-region` and add an `id`:

Add an event listener to the titlebar element:

### (macOS) Transparent Titlebar with Custom Window Background Color

We are going to create the main window and change its background color from the Rust side.

Remove the main window from the `tauri.conf.json` file:

Add `cocoa` crate to dependencies so that we can use it to call the macOS native API:

Create the main window and change its background color:

**Examples:**

Example 1 (unknown):
```unknown
#### Permissions

Add window permissions in capability file.

By default, all plugin commands are blocked and cannot be accessed. You must define a list of permissions in your `capabilities` configuration.

See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions.
```

Example 2 (unknown):
```unknown
| Permission                                   | Description                                                                    |
| -------------------------------------------- | ------------------------------------------------------------------------------ |
| `core:window:default`                        | Default permissions for the plugin. Except `window:allow-start-dragging`.      |
| `core:window:allow-close`                    | Enables the close command without any pre-configured scope.                    |
| `core:window:allow-minimize`                 | Enables the minimize command without any pre-configured scope.                 |
| `core:window:allow-start-dragging`           | Enables the start_dragging command without any pre-configured scope.           |
| `core:window:allow-toggle-maximize`          | Enables the toggle_maximize command without any pre-configured scope.          |
| `core:window:allow-internal-toggle-maximize` | Enables the internal_toggle_maximize command without any pre-configured scope. |

#### CSS

Add this CSS sample to keep it at the top of the screen and style the buttons:
```

Example 3 (unknown):
```unknown
#### HTML

Put this at the top of your `<body>` tag:
```

Example 4 (unknown):
```unknown
Note that you may need to move the rest of your content down so that the titlebar doesn't cover it.

:::tip

On Windows, if you just want a title bar that doesn't need custom interactions, you can use
```

---

## Frontend Configuration

**URL:** llms-txt#frontend-configuration

**Contents:**
- Configuration Checklist
- JavaScript
- Rust

import { LinkCard, CardGrid } from '@astrojs/starlight/components';

Tauri is frontend agnostic and supports most frontend frameworks out of the box. However, sometimes a framework need a bit of extra configuration to integrate with Tauri. Below is a list of frameworks with recommended configurations.

If a framework is not listed then it may work with Tauri with no additional configuration needed or it could have not been documented yet. Any contributions to add a framework that may require additional configuration are welcome to help others in the Tauri community.

## Configuration Checklist

Conceptually Tauri acts as a static web host. You need to provide Tauri with a folder containing some mix of HTML, CSS, Javascript and possibly WASM that can be served to the webview Tauri provides.

Below is a checklist of common scenarios needed to integrate a frontend with Tauri:

{/* TODO: Link to core concept of SSG/SSR, etc. */}
{/* TODO: Link to mobile development server guide */}
{/* TODO: Concept of how to do a client-server relationship? */}

- Use static site generation (SSG), single-page applications (SPA), or classic multi-page apps (MPA). Tauri does not natively support server based alternatives (such as SSR).
- For mobile development, a development server of some kind is necessary that can host the frontend on your internal IP.
- Use a proper client-server relationship between your app and your API's (no hybrid solutions with SSR).

{/* TODO: Help me with the wording here lol */}
For most projects we recommend [Vite](https://vitejs.dev/) for SPA frameworks such as React, Vue, Svelte, and Solid, but also for plain JavaScript or TypeScript projects. Most other guides listed here show how to use Meta-Frameworks as they are typically designed for SSR and therefore require special configuration.

<CardGrid>
  <LinkCard title="Next.js" href="/start/frontend/nextjs/" />
  <LinkCard title="Nuxt" href="/start/frontend/nuxt/" />
  <LinkCard title="Qwik" href="/start/frontend/qwik/" />
  <LinkCard title="SvelteKit" href="/start/frontend/sveltekit/" />
  <LinkCard title="Vite (recommended)" href="/start/frontend/vite/" />
</CardGrid>

<CardGrid>
  <LinkCard title="Leptos" href="/start/frontend/leptos/" />
  <LinkCard title="Trunk" href="/start/frontend/trunk/" />
</CardGrid>

:::tip[Framework Not Listed?]

Don't see a framework listed? It may work with Tauri without any additional configuration required. Read the [configuration checklist](/start/frontend/#configuration-checklist) for any common configurations to check for.

---

## bundle for App Store distribution

**URL:** llms-txt#bundle-for-app-store-distribution

**Contents:**
- Versioning
- Signing
- Distributing
  - Linux
  - macOS
  - Windows
  - Android
  - iOS
  - Cloud Services

cargo tauri bundle --bundles app --config src-tauri/tauri.appstore.conf.json"
/>

Your application version can be defined in the [`tauri.conf.json > version`] configuration option,
which is the recommended way for managing the app version. If that config value is not set,
Tauri uses the `package > version` value from your `src-tauri/Cargo.toml` file instead.

:::note
Some platforms have some limitations and special cases for the version string.
See the individual distribution documentation pages for more information.
:::

Code signing enhances the security of your application by applying a digital signature to your
application's executables and bundles, validating your identity of the provider of your application.

Signing is required on most platforms. See the documentation for each platform for more information.

<CardGrid>
  <LinkCard
    title="macOS"
    href="/distribute/sign/macos/"
    description="Code signing and notarization for macOS apps"
  />
  <LinkCard
    title="Windows"
    href="/distribute/sign/windows/"
    description="Code signing Windows installers"
  />
  <LinkCard
    title="Linux"
    href="/distribute/sign/linux/"
    description="Code signing Linux packages"
  />
  <LinkCard
    title="Android"
    href="/distribute/sign/android/"
    description="Code signing for Android"
  />
  <LinkCard
    title="iOS"
    href="/distribute/sign/ios/"
    description="Code signing for iOS"
  />

Learn how to distribute your application for each platform.

For Linux you can distribute your app using the Debian package, Snap, AppImage, Flatpak, RPM or Arch User Repository (AUR) formats.

<CardGrid>
  <LinkCard
    title="AppImage"
    href="/distribute/appimage/"
    description="Distribute as an AppImage"
  />
  <LinkCard
    title="AUR"
    href="/distribute/aur/"
    description="Publishing To The Arch User Repository"
  />
  <LinkCard
    title="Debian"
    href="/distribute/debian/"
    description="Distribute as a Debian package"
  />
  {/*  <LinkCard
    title="Flathub"
    href="/distribute/flatpak/"
    description="Distribute as a Flatpak"
  /> */}
  <LinkCard
    title="RPM"
    href="/distribute/rpm/"
    description="Distribute as an RPM package"
  />
  <LinkCard
    title="Snapcraft"
    href="/distribute/snapcraft/"
    description="Distribute on Snapcraft.io"
  />
</CardGrid>

<LinkButton href="/distribute/sign/linux/">Code signing</LinkButton>

For macOS you can either distribute your application directly to the App Store or ship a DMG installer as direct download.
Both methods requires code signing, and distributing outside the App Store also requires notarization.

<CardGrid>
  <LinkCard
    title="App Bundle"
    href="/distribute/macos-application-bundle/"
    description="Distribute macOS apps as an App Bundle"
  />
  <LinkCard
    title="App Store"
    href="/distribute/app-store/"
    description="Distribute iOS and macOS apps to the App Store"
  />
  <LinkCard
    title="DMG"
    href="/distribute/dmg/"
    description="Distribute macOS apps as Apple Disk Images"
  />
</CardGrid>

<LinkButton href="/distribute/sign/macos/">
  Code signing and notarization
</LinkButton>

Learn how to distribute to the Microsoft Store or configure a Windows installer.

<CardGrid>
  <LinkCard
    title="Microsoft Store"
    href="/distribute/microsoft-store/"
    description="Distribute Windows apps to the Microsoft Store"
  />
  <LinkCard
    title="Windows Installer"
    href="/distribute/windows-installer/"
    description="Distribute installers for Windows"
  />
</CardGrid>

<LinkButton href="/distribute/sign/windows/">Code signing</LinkButton>

Distribute your Android application to Google Play.

<CardGrid>
  <LinkCard
    title="Google Play"
    href="/distribute/google-play/"
    description="Distribute Android apps to Google Play"
  />
</CardGrid>

<LinkButton href="/distribute/sign/android/">Code signing</LinkButton>

Learn how to upload your application to the App Store.

<CardGrid>
  <LinkCard
    title="App Store"
    href="/distribute/app-store/"
    description="Distribute iOS and macOS apps to the App Store"
  />
</CardGrid>

<LinkButton href="/distribute/sign/ios/">Code signing</LinkButton>

Distribute your application to Cloud services that globally distribute your application and support auto updates out of the box.

<CardGrid>
  <LinkCard
    title="CrabNebula Cloud"
    href="/distribute/crabnebula-cloud/"
    description="Distribute your app using CrabNebula"
  />
</CardGrid>

[`tauri.conf.json > version`]: /reference/config/#version

---

## HTTP Headers

**URL:** llms-txt#http-headers

**Contents:**
  - Header Names
  - How to Configure Headers
  - Example
  - Frameworks

import SinceVersion from '../../../components/SinceVersion.astro';

<SinceVersion version="2.1.0" />

A header defined in the configuration gets sent along the responses to the webview.
This doesn't include IPC messages and error responses.
To be more specific, every response sent via the `get_response` function in
<a href="https://github.com/tauri-apps/tauri/blob/8e8312bb8201ccc609e4bbc1a990bdc314daa00f/crates/tauri/src/protocol/tauri.rs#L103" target="_blank">crates/tauri/src/protocol/tauri.rs ↗</a>
will include those headers.

The header names are limited to:
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Credentials" target="_blank">Access-Control-Allow-Credentials ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Headers" target="_blank">Access-Control-Allow-Headers ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Methods" target="_blank">Access-Control-Allow-Methods ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Expose-Headers" target="_blank">Access-Control-Expose-Headers ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Max-Age" target="_blank">Access-Control-Max-Age ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy" target="_blank">Cross-Origin-Embedder-Policy ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Opener-Policy" target="_blank">Cross-Origin-Opener-Policy ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Resource-Policy" target="_blank">Cross-Origin-Resource-Policy ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy" target="_blank">Permissions-Policy ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Service-Worker-Allowed" target="_blank">Service-Worker-Allowed ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Timing-Allow-Origin" target="_blank">Timing-Allow-Origin ↗</a>
- <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Content-Type-Options" target="_blank">X-Content-Type-Options ↗</a>
- Tauri-Custom-Header

:::note
`Tauri-Custom-Header` is not intended for production use.
:::

:::note
<a href="../csp/">The Content-Security-Policy (CSP)</a> is not defined here.
:::

### How to Configure Headers

- with a string
- with an array of strings
- with an object/key-value, where the values must be strings
- with null

The header values are always converted to strings for the actual response. Depending on how the configuration file looks, some header values need to be composed.
Those are the rules on how a composite gets created:

- `string`: stays the same for the resulting header value
- `array`: items are joined by `, ` for the resulting header value
- `key-value`: items are composed from: key + space + value. Items are then joined by `; ` for the resulting header value
- `null`: header will be ignored

:::note
`Tauri-Custom-Header` is not intended for production use.
For Tests: Remember to set `Access-Control-Expose-Headers` accordingly.
:::

In this example `Cross-Origin-Opener-Policy` and `Cross-Origin-Embedder-Policy` are set to
allow for the use of <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer" target="_blank">`SharedArrayBuffer ↗`</a>.
`Timing-Allow-Origin` grants scripts loaded from the listed websites to access detailed network timing data via the <a href="https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Resource_timing" target="_blank">Resource Timing API ↗</a>.

For the helloworld example, this config results in:

Some development environments require extra settings, to emulate the production environment.

#### JavaScript/TypeScript

For setups running the build tool **Vite** (those include **Qwik, React, Solid, Svelte, and Vue**) add the wanted headers to `vite.config.ts`.

Sometimes the `vite.config.ts` is integrated into the frameworks configuration file, but the setup stays the same.
In case of **Angular** add them to `angular.json`.

And in case of **Nuxt** to `nuxt.config.ts`.

**Next.js** doesn't rely on **Vite**, so the approach is different.
Read more about it <a href="https://nextjs.org/docs/pages/api-reference/next-config-js/headers" target="_blank">here ↗</a>.
The headers are defined in `next.config.js`.

For **Yew** and **Leptos** add the headers to `Trunk.toml`

**Examples:**

Example 1 (unknown):
```unknown
:::note
`Tauri-Custom-Header` is not intended for production use.
For Tests: Remember to set `Access-Control-Expose-Headers` accordingly.
:::

In this example `Cross-Origin-Opener-Policy` and `Cross-Origin-Embedder-Policy` are set to
allow for the use of <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer" target="_blank">`SharedArrayBuffer ↗`</a>.
`Timing-Allow-Origin` grants scripts loaded from the listed websites to access detailed network timing data via the <a href="https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Resource_timing" target="_blank">Resource Timing API ↗</a>.

For the helloworld example, this config results in:
```

Example 2 (unknown):
```unknown
### Frameworks

Some development environments require extra settings, to emulate the production environment.

#### JavaScript/TypeScript

For setups running the build tool **Vite** (those include **Qwik, React, Solid, Svelte, and Vue**) add the wanted headers to `vite.config.ts`.
```

Example 3 (unknown):
```unknown
Sometimes the `vite.config.ts` is integrated into the frameworks configuration file, but the setup stays the same.
In case of **Angular** add them to `angular.json`.
```

Example 4 (unknown):
```unknown
And in case of **Nuxt** to `nuxt.config.ts`.
```

---

## App Size

**URL:** llms-txt#app-size

**Contents:**
- Cargo Configuration

import { Tabs, TabItem } from '@astrojs/starlight/components';

While Tauri by default provides very small binaries it doesn't hurt to push the limits a bit, so here are some tips and tricks for reaching optimal results.

## Cargo Configuration

One of the simplest frontend agnostic size improvements you can do to your project is adding a Cargo profile to it.

Dependent on whether you use the stable or nightly Rust toolchain the options available to you differ a bit. It's recommended you stick to the stable toolchain unless you're an advanced user.

<Tabs>
<TabItem label="Stable">
```toml

---

## Configuration Files

**URL:** llms-txt#configuration-files

**Contents:**
- Tauri Config
  - Supported Formats

import CommandTabs from '@components/CommandTabs.astro';

Since Tauri is a toolkit for building applications there can be many files to configure project settings. Some common files that you may run across are `tauri.conf.json`, `package.json` and `Cargo.toml`. We briefly explain each on this page to help point you in the right direction for which files to modify.

The Tauri configuration is used to define the source of your Web app, describe your application's metadata, configure bundles, set plugin configurations, modify runtime behavior by configuring windows, tray icons, menus and more.

This file is used by the Tauri runtime and the Tauri CLI. You can define build settings (such as the [command run before `tauri build`][before-build-command] or [`tauri dev`][before-dev-command] kicks in), set the [name](/reference/config/#productname) and [version of your app](/reference/config/#version), [control the Tauri runtime][appconfig], and [configure plugins].

:::tip
You can find all of the options in the [configuration reference].
:::

### Supported Formats

The default Tauri config format is JSON. The JSON5 or TOML format can be enabled by adding the `config-json5` or `config-toml` feature flag (respectively) to the `tauri` and `tauri-build` dependencies in `Cargo.toml`.

The structure and values are the same across all formats, however, the formatting should be consistent with the respective file's format:

```toml title=Tauri.toml
[build]
dev-url = "http://localhost:3000"

**Examples:**

Example 1 (unknown):
```unknown
The structure and values are the same across all formats, however, the formatting should be consistent with the respective file's format:
```

Example 2 (unknown):
```unknown

```

---

## Project Structure

**URL:** llms-txt#project-structure

**Contents:**
- Next Steps

A Tauri project is usually made of 2 parts, a Rust project and a JavaScript project (optional),
and typically the setup looks something like this:

In this case, the JavaScript project is at the top level, and the Rust project is inside `src-tauri/`,
the Rust project is a normal [Cargo project](https://doc.rust-lang.org/cargo/guide/project-layout.html) with some extra files:

- `tauri.conf.json` is the main configuration file for Tauri, it contains everything from the application identifier to dev server url,
  this file is also a marker for the [Tauri CLI](/reference/cli/) to find the Rust project,
  to learn more about it, see [Tauri Config](/develop/configuration-files/#tauri-config)
- `capabilities/` directory is the default folder Tauri reads [capability files](/security/capabilities/) from (in short, you need to allow commands here to use them in your JavaScript code),
  to learn more about it, see [Security](/security/)
- `icons/` directory is the default output directory of the [`tauri icon`](/reference/cli/#icon) command, it's usually referenced in `tauri.conf.json > bundle > icon` and used for the app's icons
- `build.rs` contains `tauri_build::build()` which is used for tauri's build system
- `src/lib.rs` contains the Rust code and the mobile entry point (the function marked with `#[cfg_attr(mobile, tauri::mobile_entry_point)]`),
  the reason we don't write directly in `main.rs` is because we compile your app to a library in mobile builds and load them through the platform frameworks
- `src/main.rs` is the main entry point for the desktop, and we run `app_lib::run()` in `main` to use the same entry point as mobile,
  so to keep it simple, don't modify this file, modify `lib.rs` instead. Note that `app_lib` corresponds to `[lib.name]` in Cargo.toml.

Tauri works similar to a static web host, and the way it builds is that you would compile your JavaScript project to static files first,
and then compile the Rust project that will bundle those static files in,
so the JavaScript project setup is basically the same as if you were to build a static website,
to learn more, see [Frontend Configuration](/start/frontend/)

If you want to work with Rust code only, simply remove everything else and use the `src-tauri/` folder as your top level project or as a member of your Rust workspace

- [Add and Configure a Frontend Framework](/start/frontend/)
- [Tauri Command Line Interface (CLI) Reference](/reference/cli/)
- [Learn how to develop your Tauri app](/develop/)
- [Discover additional features to extend Tauri](/plugin/)

**Examples:**

Example 1 (unknown):
```unknown
.
├── package.json
├── index.html
├── src/
│   ├── main.js
├── src-tauri/
│   ├── Cargo.toml
│   ├── Cargo.lock
│   ├── build.rs
│   ├── tauri.conf.json
│   ├── src/
│   │   ├── main.rs
│   │   └── lib.rs
│   ├── icons/
│   │   ├── icon.png
│   │   ├── icon.icns
│   │   └── icon.ico
│   └── capabilities/
│       └── default.json
```

---

## App Store

**URL:** llms-txt#app-store

**Contents:**
- Requirements
- Changing App Icon
- Setting up
- Build and upload
  - macOS
  - iOS
  - Authentication

import CommandTabs from '@components/CommandTabs.astro';

The [Apple App Store] is the app marketplace maintained by Apple.
You can distribute your Tauri app targeting macOS and iOS via this App Store.

This guide only covers details for distributing apps directly to the App Store.
See the general [App Bundle][App Bundle distribution guide] for more information on macOS distribution options and configurations.

Distributing iOS and macOS apps requires enrolling to the [Apple Developer] program.

Additionally, you must setup code signing for [macOS][macOS code signing] and [iOS][iOS code signing].

After running `tauri ios init` to setup the Xcode project, you can use the `tauri icon` command to update the app icons.

<CommandTabs
  npm="npm run tauri icon /path/to/app-icon.png -- --ios-color #fff"
  yarn="yarn tauri icon /path/to/app-icon.png --ios-color #fff"
  pnpm="pnpm tauri icon /path/to/app-icon.png --ios-color #fff"
  deno="deno task tauri icon /path/to/app-icon.png --ios-color #fff"
  bun="bun tauri icon /path/to/app-icon.png --ios-color #fff"
  cargo="cargo tauri icon /path/to/app-icon.png --ios-color #fff"
/>

The `--ios-color` argument defines the background color for the iOS icons.

After enrolling to the Apple Developer program, the first step to distribute your Tauri app in the App Store
is to register your app in the [App Store Connect][app-store-connect-apps].

:::note
The value provided in the _Bundle ID_ field **must** match the identifier defined in [`tauri.conf.json > identifier`].
:::

The Tauri CLI can package your app for macOS and iOS. Running on a macOS machine is a requirement.

Tauri derives the [`CFBundleVersion`](https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleversion) from the value defined in [`tauri.conf.json > version`].
You can set a custom bundle version in the [`tauri.conf.json > bundle > iOS > bundleVersion`] or [`tauri.conf.json > bundle > macOS > bundleVersion`] configuration
if you need a different bundle version scheme e.g. sequential codes:

:::caution
Code signing is required. See the documentation for [macOS][macOS code signing] and [iOS][iOS code signing].
:::

Note that Tauri leverages Xcode for the iOS app so you can use Xcode to archive and distribute for iOS instead of the Tauri CLI.
To open the iOS project in Xcode for building you must run the following command:

<CommandTabs
  npm="npm run tauri ios build -- --open"
  yarn="yarn tauri ios build --open"
  pnpm="pnpm tauri ios build --open"
  deno="deno task tauri ios build --open"
  bun="bun tauri ios build --open"
  cargo="cargo tauri ios build --open"
/>

To upload your app to the App Store, first you must ensure all required configuration options are set
so you can package the App Bundle, create a signed `.pkg` file and upload it.

The following sections will guide you through the process.

Your app must include some configurations to be accepted by the App Store verification system.

:::tip
The following sections guides you through configuring your app for App Store submissions.

To apply the following config changes only when building for App Store, you can create a separate Tauri configuration file:

Then merge that config file with the main one when bundling your Tauri app for App Store:

<CommandTabs
  npm="npm run tauri build -- --no-bundle
npm run tauri bundle -- --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
  yarn="yarn tauri build --no-bundle
yarn tauri bundle --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
  pnpm="pnpm tauri build --no-bundle
pnpm tauri bundle --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
  deno="deno task tauri build --no-bundle
deno task tauri bundle --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
  bun="bun tauri build --no-bundle
bun tauri bundle --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
  cargo="cargo tauri build --no-bundle
cargo tauri bundle --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
/>

This is particularly useful when setting up your CI/CD to upload your app to the App Store while not requiring the provision profile locally or
when compiling the app for distribution outside the App Store.

Your app must define its [`tauri.conf.json > bundle > category`] to be displayed in the App Store:

- Provisioning profile

You must also create a provisioning profile for your app to be accepted by Apple.

In the [Identifiers](https://developer.apple.com/account/resources/identifiers/list) page,
create a new App ID and make sure its "Bundle ID" value matches the identifier set in [`tauri.conf.json > identifier`].

Navigate to the [Profiles](https://developer.apple.com/account/resources/profiles/list) page to create a new provisioning profile.
For App Store macOS distribution, it must be a "Mac App Store Connect" profile.
Select the appropriate App ID and link the certificate you are using for code signing.

After creating the provisioning profile, download it and save it to a known location and configure Tauri to include it in your app bundle:

Your app must comply with encryption export regulations.
See the [official documentation](https://developer.apple.com/documentation/security/complying-with-encryption-export-regulations?language=objc)
for more information.

Create a Info.plist file in the src-tauri folder:

Your app must include the App Sandbox capability to be distributed in the App Store.
Additionally, you must also set your App ID and Team ID in the code signing entitlements.

Create a `Entitlements.plist` file in the `src-tauri` folder:

Note that you must replace `$IDENTIFIER` with the [`tauri.conf.json > identifier`] value
and `$TEAM_ID` with your Apple Developer team ID, which can be found in the `App ID Prefix` section in the
[Identifier](https://developer.apple.com/account/resources/identifiers/list) you created for the provisioning profile.

And reference that file in the macOS bundle configuration [`tauri.conf.json > bundle > macOS > entitlements`]:

You now must build your application with code signing enabled for the entitlements to apply.

Make sure your app works when running in an App Sandbox context.

You must upload your macOS application as a `.pkg` file to the App Store.
Run the following command to package your app as a macOS App Bundle (`.app` extension):

:::note
The above command creates an Universal App Binary application, supporting both Apple Silicon and Intel processors.

If you prefer to only support Apple Silicon instead, you must change [`tauri.conf.json > bundle > macOS > minimumSystemVersion`] to `12.0`:

And change the CLI command and output path based on the Mac system you are running:

- if your build system uses an Apple Silicon chip, remove the `--target universal-apple-darwin` arguments and use `target/release`
  instead of `target/universal-apple-darwin/release` in the paths referenced below.
- if your build system uses an Intel chip:
  - install the Rust Apple Silicon target:
    
  - change the `universal-apple-darwin` argument to `aarch64-apple-darwin`
    and use `target/aarch64-apple-darwin/release` instead of `target/universal-apple-darwin/release` in the paths referenced below.

See the [App Bundle distribution guide] for more information on configuration options.

To generate a signed `.pkg` from your app bundle, run the following command:

Note that you must replace _$APPNAME_ with your app name.

:::note
You must sign the PKG with a _Mac Installer Distribution_ signing certificate.
:::

Now you can use the [`altool`] CLI to upload your app PKG to the App Store:

Note that `altool` requires an App Store Connect API key to upload your app.
See the [authentication section] for more information.

Your app will then be validated by Apple and available in TestFlight if approved.

To build your iOS app, run the `tauri ios build` command:

<CommandTabs
  npm="npm run tauri ios build -- --export-method app-store-connect"
  yarn="yarn tauri ios build --export-method app-store-connect"
  pnpm="pnpm tauri ios build --export-method app-store-connect"
  deno="deno task tauri ios build --export-method app-store-connect"
  bun="bun tauri ios build --export-method app-store-connect"
  cargo="cargo tauri ios build --export-method app-store-connect"
/>

The generated IPA file can be found in `src-tauri/gen/apple/build/arm64/$APPNAME.ipa`.

Note that you must replace _$APPNAME_ with your app name.

Now you can use the `altool` CLI to upload your iOS app to the App Store:

Note that `altool` requires an App Store Connect API key to upload your app.
See the [authentication section] for more information.

Your app will then be validated by Apple and available in TestFlight if approved.

The iOS and macOS apps are uploaded using `altool`, which uses an App Store Connect API key to authenticate.

To create a new API key, open the [App Store Connect's Users and Access page], select the Integrations > Individual Keys tab, click on the Add button and select a name and the Developer access.
The `APPLE_API_ISSUER` (Issuer ID) is presented above the keys table, and the `APPLE_API_KEY_ID` is the value on the Key ID column on that table.
You also need to download the private key, which can only be done once and is only visible after a page reload (the button is shown on the table row for the newly created key).
The private key file path must be saved as `AuthKey\_<APPLE_API_KEY_ID>.p8` in one of these directories:`<current-working-directory>/private_keys`, `~/private_keys`, `~/.private_keys`or`~/.appstoreconnect/private_keys`.

[App Bundle distribution guide]: /distribute/macos-application-bundle/
[Apple Developer]: https://developer.apple.com
[Apple App Store]: https://www.apple.com/store
[`altool`]: https://help.apple.com/itc/apploader/#/apdATD1E53-D1E1A1303-D1E53A1126
[macOS code signing]: /distribute/sign/macos/
[iOS code signing]: /distribute/sign/ios/
[app-store-connect-apps]: https://appstoreconnect.apple.com/apps
[`tauri.conf.json > identifier`]: /reference/config/#identifier
[`tauri.conf.json > bundle > category`]: /reference/config/#category
[`tauri.conf.json > bundle > macOS > entitlements`]: /reference/config/#entitlements
[`tauri.conf.json > bundle > macOS > minimumSystemVersion`]: /reference/config/#minimumsystemversion
[App Store Connect's Users and Access page]: https://appstoreconnect.apple.com/access/users
[authentication section]: #authentication

**Examples:**

Example 1 (unknown):
```unknown
:::caution
Code signing is required. See the documentation for [macOS][macOS code signing] and [iOS][iOS code signing].
:::

Note that Tauri leverages Xcode for the iOS app so you can use Xcode to archive and distribute for iOS instead of the Tauri CLI.
To open the iOS project in Xcode for building you must run the following command:

<CommandTabs
  npm="npm run tauri ios build -- --open"
  yarn="yarn tauri ios build --open"
  pnpm="pnpm tauri ios build --open"
  deno="deno task tauri ios build --open"
  bun="bun tauri ios build --open"
  cargo="cargo tauri ios build --open"
/>

### macOS

To upload your app to the App Store, first you must ensure all required configuration options are set
so you can package the App Bundle, create a signed `.pkg` file and upload it.

The following sections will guide you through the process.

#### Setup

Your app must include some configurations to be accepted by the App Store verification system.

:::tip
The following sections guides you through configuring your app for App Store submissions.

To apply the following config changes only when building for App Store, you can create a separate Tauri configuration file:
```

Example 2 (unknown):
```unknown
Then merge that config file with the main one when bundling your Tauri app for App Store:

<CommandTabs
  npm="npm run tauri build -- --no-bundle
npm run tauri bundle -- --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
  yarn="yarn tauri build --no-bundle
yarn tauri bundle --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
  pnpm="pnpm tauri build --no-bundle
pnpm tauri bundle --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
  deno="deno task tauri build --no-bundle
deno task tauri bundle --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
  bun="bun tauri build --no-bundle
bun tauri bundle --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
  cargo="cargo tauri build --no-bundle
cargo tauri bundle --bundles app --target universal-apple-darwin --config src-tauri/tauri.appstore.conf.json"
/>

This is particularly useful when setting up your CI/CD to upload your app to the App Store while not requiring the provision profile locally or
when compiling the app for distribution outside the App Store.

:::

- Category

Your app must define its [`tauri.conf.json > bundle > category`] to be displayed in the App Store:
```

Example 3 (unknown):
```unknown
- Provisioning profile

You must also create a provisioning profile for your app to be accepted by Apple.

In the [Identifiers](https://developer.apple.com/account/resources/identifiers/list) page,
create a new App ID and make sure its "Bundle ID" value matches the identifier set in [`tauri.conf.json > identifier`].

Navigate to the [Profiles](https://developer.apple.com/account/resources/profiles/list) page to create a new provisioning profile.
For App Store macOS distribution, it must be a "Mac App Store Connect" profile.
Select the appropriate App ID and link the certificate you are using for code signing.

After creating the provisioning profile, download it and save it to a known location and configure Tauri to include it in your app bundle:
```

Example 4 (unknown):
```unknown
- Info.plist

Your app must comply with encryption export regulations.
See the [official documentation](https://developer.apple.com/documentation/security/complying-with-encryption-export-regulations?language=objc)
for more information.

Create a Info.plist file in the src-tauri folder:
```

---

## Microsoft Store

**URL:** llms-txt#microsoft-store

**Contents:**
- Requirements
- Changing App Icon
- Setting up
- Build and upload
  - Offline Installer
  - Publisher
  - Upload

import CommandTabs from '@components/CommandTabs.astro';

Microsoft Store is the Windows app store operated by Microsoft.

This guide only covers details for distributing Windows Apps directly to the Microsoft Store.
See the [Windows Installer guide] for more information on Windows installer distribution options and configurations.

To publish apps on the Microsoft Store you must have a Microsoft account
and [enroll] as a developer either as an individual or as a company.

The Tauri CLI can generate all icons your app needs, including Microsoft Store icons.
Use the `tauri icon` command to generate app icons from a single PNG or SVG source:

<CommandTabs
  npm="npm run tauri icon /path/to/app-icon.png"
  yarn="yarn tauri icon /path/to/app-icon.png"
  pnpm="pnpm tauri icon /path/to/app-icon.png"
  deno="deno task tauri icon /path/to/app-icon.png"
  bun="bun tauri icon /path/to/app-icon.png"
  cargo="cargo tauri icon /path/to/app-icon.png"
/>

After you have enrolled as a developer with your Microsoft account you need to register your app in the [Apps and Games] page.
Click `New Product`, select `EXE or MSI app` and reserve a unique name for your app.

Currently Tauri only generates [EXE and MSI][Windows Installer guide] installers, so you must create a Microsoft Store application
that only links to the unpacked application.
The installer linked in the Microsoft Installer must be offline, [handle auto-updates] and be [code signed].

See the [official publish documentation] for more information.

### Offline Installer

The Windows installer distributed through the Microsoft Store must use the [Offline Installer] Webview2 installation option.

To only apply this installer configuration when bundling for Microsoft Store, you can define a separate Tauri configuration file:

Then merge that config file with the main one when bundling your Tauri app for Microsoft Store:

<CommandTabs
  npm="npm run tauri build -- --no-bundle
npm run tauri bundle -- --config src-tauri/tauri.microsoftstore.conf.json"
  yarn="yarn tauri build --no-bundle
yarn tauri bundle --config src-tauri/tauri.microsoftstore.conf.json"
  pnpm="pnpm tauri build --no-bundle
pnpm tauri bundle --config src-tauri/tauri.microsoftstore.conf.json"
  deno="deno task tauri build --no-bundle
deno task tauri bundle --config src-tauri/tauri.microsoftstore.conf.json"
  bun="bun tauri build --no-bundle
bun tauri bundle --config src-tauri/tauri.microsoftstore.conf.json"
  cargo="cargo tauri build --no-bundle
cargo tauri bundle --config src-tauri/tauri.microsoftstore.conf.json"
/>

This is particularly useful when setting up your CI/CD to upload your app to the Microsoft Store while having a separate configuration
for the Windows installer you distribute outside the app store.

Your application [publisher] name cannot match the application product name.

If the publisher configuration value is not set, Tauri derives it from the second part of your bundle identifier.
Since the publisher name cannot match the product name, the following configuration is invalid:

In this case you can define the [publisher] value separately to fix this conflict:

After building the Windows installer for Microsoft Store, you can upload it to the distribution service of your choice
and link it in your application page in the Microsoft Store website.

[Windows Installer guide]: /distribute/windows-installer/
[enroll]: https://learn.microsoft.com/en-us/windows/apps/get-started/sign-up
[Apps and Games]: https://partner.microsoft.com/en-us/dashboard/apps-and-games/overview
[handle auto-updates]: /plugin/updater/
[code signed]: /distribute/sign/windows/
[Offline Installer]: /distribute/windows-installer/#offline-installer
[official publish documentation]: https://learn.microsoft.com/en-us/windows/apps/publish/
[publisher]: /reference/config/#publisher

**Examples:**

Example 1 (unknown):
```unknown
Then merge that config file with the main one when bundling your Tauri app for Microsoft Store:

<CommandTabs
  npm="npm run tauri build -- --no-bundle
npm run tauri bundle -- --config src-tauri/tauri.microsoftstore.conf.json"
  yarn="yarn tauri build --no-bundle
yarn tauri bundle --config src-tauri/tauri.microsoftstore.conf.json"
  pnpm="pnpm tauri build --no-bundle
pnpm tauri bundle --config src-tauri/tauri.microsoftstore.conf.json"
  deno="deno task tauri build --no-bundle
deno task tauri bundle --config src-tauri/tauri.microsoftstore.conf.json"
  bun="bun tauri build --no-bundle
bun tauri bundle --config src-tauri/tauri.microsoftstore.conf.json"
  cargo="cargo tauri build --no-bundle
cargo tauri bundle --config src-tauri/tauri.microsoftstore.conf.json"
/>

This is particularly useful when setting up your CI/CD to upload your app to the Microsoft Store while having a separate configuration
for the Windows installer you distribute outside the app store.

### Publisher

Your application [publisher] name cannot match the application product name.

If the publisher configuration value is not set, Tauri derives it from the second part of your bundle identifier.
Since the publisher name cannot match the product name, the following configuration is invalid:
```

Example 2 (unknown):
```unknown
In this case you can define the [publisher] value separately to fix this conflict:
```

---
