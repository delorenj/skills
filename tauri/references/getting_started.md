# Tauri - Getting Started

**Pages:** 2

---

## Start

**URL:** llms-txt#start

---

## start the dev server

**URL:** llms-txt#start-the-dev-server

**Contents:**
  - Platform-specific Configuration
  - Extending the Configuration
- `Cargo.toml`
- `package.json`

before-dev-command = "npm run dev"

[bundle]
active = true
icon = ["icons/app.png"]

[[app.windows]]
title = "MyApp"

[plugins.updater]
pubkey = "updater pub key"
endpoints = ["https://my.app.updater/{{target}}/{{current_version}}"]
json title=tauri.conf.json
{
  "productName": "MyApp",
  "bundle": {
    "resources": ["./resources"]
  },
  "plugins": {
    "deep-link": {}
  }
}
json title=tauri.linux.conf.json
{
  "productName": "my-app",
  "bundle": {
    "resources": ["./linux-assets"]
  },
  "plugins": {
    "cli": {
      "description": "My app",
      "subcommands": {
        "update": {}
      }
    },
    "deep-link": {}
  }
}
json
{
  "productName": "my-app",
  "bundle": {
    "resources": ["./linux-assets"]
  },
  "plugins": {
    "cli": {
      "description": "My app",
      "subcommands": {
        "update": {}
      }
    },
    "deep-link": {}
  }
}
json title=src-tauri/tauri.beta.conf.json
{
  "productName": "My App Beta",
  "identifier": "com.myorg.myappbeta"
}
toml title=Cargo.toml
[package]
name = "app"
version = "0.1.0"
description = "A Tauri App"
authors = ["you"]
license = ""
repository = ""
default-run = "app"
edition = "2021"
rust-version = "1.57"

[build-dependencies]
tauri-build = { version = "2.0.0" }

[dependencies]
serde_json = "1.0"
serde = { version = "1.0", features = ["derive"] }
tauri = { version = "2.0.0", features = [ ] }

tauri-build = { version = "=2.0.0" }
json title=package.json
{
  "scripts": {
    "dev": "command to start your app development mode",
    "build": "command to build your app frontend",
    "tauri": "tauri"
  },
  "dependencies": {
    "@tauri-apps/api": "^2.0.0.0",
    "@tauri-apps/cli": "^2.0.0.0"
  }
}
json title=tauri.conf.json
{
  "build": {
    "beforeDevCommand": "yarn dev",
    "beforeBuildCommand": "yarn build"
  }
}
```

:::note
The `"tauri"` script is only needed when using `npm`
:::

The dependencies object specifies which dependencies Node.js should download when you run either `yarn`, `pnpm install` or `npm install` (in this case the Tauri CLI and API).

In addition to the `package.json` file you may see either a `yarn.lock`, `pnpm-lock.yaml` or `package-lock.json` file. These files assist in ensuring that when you download the dependencies later you'll get the exact same versions that you have used during development (similar to `Cargo.lock` in Rust).

To learn more about the `package.json` file format please refer to the [official documentation][npm-package].

[configuration reference]: /reference/config/
[before-dev-command]: /reference/config/#beforedevcommand-1
[before-build-command]: /reference/config/#beforebuildcommand
[appconfig]: /reference/config/#appconfig
[configure plugins]: /reference/config/#plugins
[semantic versioning]: https://semver.org
[cargo-manifest]: https://doc.rust-lang.org/cargo/reference/manifest.html
[npm-package]: https://docs.npmjs.com/cli/v8/configuring-npm/package-json
[tauri Cargo features]: https://docs.rs/tauri/2.0.0/tauri/#cargo-features
[JSON Merge Patch (RFC 7396)]: https://datatracker.ietf.org/doc/html/rfc7396

**Examples:**

Example 1 (unknown):
```unknown
Note that JSON5 and TOML supports comments, and TOML can use kebab-case for config names which are more idiomatic. Field names are case-sensitive in all 3 formats.

### Platform-specific Configuration

In addition to the default configuration file, Tauri can read a platform-specific configuration from:

- `tauri.linux.conf.json` or `Tauri.linux.toml` for Linux
- `tauri.windows.conf.json` or `Tauri.windows.toml` for Windows
- `tauri.macos.conf.json` or `Tauri.macos.toml` for macOS
- `tauri.android.conf.json` or `Tauri.android.toml` for Android
- `tauri.ios.conf.json` or `Tauri.ios.toml` for iOS

The platform-specific configuration file gets merged with the main configuration object following the [JSON Merge Patch (RFC 7396)] specification.

For example, given the following base `tauri.conf.json`:
```

Example 2 (unknown):
```unknown
And the given `tauri.linux.conf.json`:
```

Example 3 (unknown):
```unknown
The resolved configuration for Linux would be the following object:
```

Example 4 (unknown):
```unknown
Additionally you can provide a configuration to be merged via the CLI, see the following section for more information.

### Extending the Configuration

The Tauri CLI allows you to extend the Tauri configuration when running one of the `dev`, `android dev`, `ios dev`, `build`, `android build`, `ios build` or `bundle` commands.
The configuration extension can be provided by the `--config` argument either as a raw JSON string or as a path to a JSON file.
Tauri uses the [JSON Merge Patch (RFC 7396)] specification to merge the provided configuration value with the originally resolved configuration object.

This mechanism can be used to define multiple flavours of your application or have more flexibility when configuring your application bundles.

For instance to distribute a completely isolated _beta_ application you can use this feature to configure a separate application name and identifier:
```

---
