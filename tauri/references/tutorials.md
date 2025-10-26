# Tauri - Tutorials

**Pages:** 7

---

## Next.js

**URL:** llms-txt#next.js

**Contents:**
- Checklist
- Example Configuration

import { Tabs, TabItem, Steps } from '@astrojs/starlight/components';
import CommandTabs from '@components/CommandTabs.astro';

Next.js is a meta framework for React. Learn more about Next.js at https://nextjs.org. This guide is accurate as of Next.js 14.2.3.

- Use static exports by setting `output: 'export'`. Tauri doesn't support server-based solutions.
- Use the `out` directory as `frontendDist` in `tauri.conf.json`.

## Example Configuration

1.  ##### Update Tauri configuration

<TabItem label="npm">

<TabItem label="yarn">

<TabItem label="pnpm">

<TabItem label="deno">

2.  ##### Update Next.js configuration

3.  ##### Update package.json configuration

**Examples:**

Example 1 (json):
```json
// src-tauri/tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "npm run dev",
        "beforeBuildCommand": "npm run build",
        "devUrl": "http://localhost:3000",
        "frontendDist": "../out"
      }
    }
```

Example 2 (json):
```json
// src-tauri/tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "yarn dev",
        "beforeBuildCommand": "yarn build",
        "devUrl": "http://localhost:3000",
        "frontendDist": "../out"
      }
    }
```

Example 3 (json):
```json
// src-tauri/tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "pnpm dev",
        "beforeBuildCommand": "pnpm build",
        "devUrl": "http://localhost:3000",
        "frontendDist": "../out"
      }
    }
```

Example 4 (json):
```json
// src-tauri/tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "deno task dev",
        "beforeBuildCommand": "deno task build",
        "devUrl": "http://localhost:3000",
        "frontendDist": "../out"
      }
    }
```

---

## Trunk

**URL:** llms-txt#trunk

**Contents:**
- Checklist
- Example Configuration

import { Tabs, TabItem, Steps } from '@astrojs/starlight/components';

Trunk is a WASM web application bundler for Rust. Learn more about Trunk at https://trunkrs.dev. This guide is accurate as of Trunk 0.17.5.

- Use SSG, Tauri doesn't officially support server based solutions.
- Use `serve.ws_protocol = "ws"` so that the hot-reload websocket can connect properly for mobile development.
- Enable `withGlobalTauri` to ensure that Tauri APIs are available in the `window.__TAURI__` variable and can be imported using `wasm-bindgen`.

## Example Configuration

1. ##### Update Tauri configuration

1. ##### Update Trunk configuration

**Examples:**

Example 1 (json):
```json
// tauri.conf.json
   {
     "build": {
       "beforeDevCommand": "trunk serve",
       "beforeBuildCommand": "trunk build",
       "devUrl": "http://localhost:8080",
       "frontendDist": "../dist"
     },
     "app": {
       "withGlobalTauri": true
     }
   }
```

Example 2 (toml):
```toml
# Trunk.toml
   [watch]
   ignore = ["./src-tauri"]

   [serve]
   ws_protocol = "ws"
```

---

## Node.js as a sidecar

**URL:** llms-txt#node.js-as-a-sidecar

**Contents:**
- Goals
- Implementation Details
- Prerequisites
- Guide

import CommandTabs from '@components/CommandTabs.astro';
import { Tabs, TabItem, Steps } from '@astrojs/starlight/components';
import CTA from '@fragments/cta.mdx';

In this guide we are going to package a Node.js application to a self contained binary
to be used as a sidecar in a Tauri application without requiring the end user to have a Node.js installation.
This example tutorial is applicable for desktop operating systems only.

We recommend reading the general [sidecar guide] first for a deeper understanding of how Tauri sidecars work.

- Package a Node.js application as a binary.
- Integrate this binary as a Tauri sidecar.

## Implementation Details

- For this we use the [pkg] tool, but any other tool that can compile JavaScript or Typescript into a binary application will work.
- You can also embed the Node runtime itself into your Tauri application and ship bundled JavaScript as a resource, but this will ship the JavaScript content as readable-ish files and the runtime is usually larger than a `pkg` packaged application.

In this example we will create a Node.js application that reads input from the command line [process.argv]
and writes output to stdout using [console.log]. <br/>
You can leverage alternative inter-process communication systems such as a localhost server, stdin/stdout or local sockets.
Note that each has their own advantages, drawbacks and security concerns.

An existing Tauri application set up with the shell plugin, that compiles and runs for you locally.

:::tip[Create a lab app]

If you are not an advanced user it's **highly recommended** that you use the options and frameworks provided here. It's just a lab, you can delete the project when you're done.

- Project name: `node-sidecar-lab`
- Choose which language to use for your frontend: `Typescript / Javascript`
- Choose your package manager: `pnpm`
- Choose your UI template: `Vanilla`
- Choose your UI flavor: `Typescript`

:::note
Please follow the [shell plugin guide](/plugin/shell/) first to set up and initialize the plugin correctly.
Without the plugin being initialized and configured the example won't work.
:::

1.  ##### Initialize Sidecar Project

Let's create a new Node.js project to contain our sidecar implementation.
    Create a new directory **in your Tauri application root folder** (in this example we will call it `sidecar-app`)
    and run the `init` command of your preferred Node.js package manager inside the directory:

<CommandTabs npm="npm init" yarn="yarn init" pnpm="pnpm init" />

We will compile our Node.js application to a self container binary using [pkg] among other options.
    Let's install it as a development dependency into the new `sidecar-app`:

<CommandTabs
      npm="npm add @yao-pkg/pkg --save-dev"
      yarn="yarn add @yao-pkg/pkg --dev"
      pnpm="pnpm add @yao-pkg/pkg --save-dev"
    />

1.  ##### Write Sidecar Logic

Now we can start writing JavaScript code that will be executed by our Tauri application.

In this example we will process a command from the command line argmuents and write output to stdout,
    which means our process will be short lived and only handle a single command at a time.
    If your application must be long lived, consider using alternative inter-process communication systems.

Let's create a `index.js` file in our `sidecar-app` directory and write a basic Node.js app:

1.  ##### Package the Sidecar

To package our Node.js application into a self contained binary, create a script in `package.json`:

<CommandTabs npm="npm run build" yarn="yarn build" pnpm="pnpm build" />

This will create the `sidecar-app/my-sidecar` binary on Linux and macOS, and a `sidecar-app/my-sidecar.exe` executable on Windows.

For sidecar applications, we need to ensure that the binary is named in the correct pattern, for more information read [Embedding External Binaries](https://tauri.app/develop/sidecar/)
    To rename this file to the expected Tauri sidecar filename and also move to our Tauri project, we can use the following Node.js script as a starting example:

And run `node rename.js` from the `sidecar-app` directory.

At this step the `/src-tauri/binaries` directory should contain the renamed sidecar binary.

1.  ##### Setup plugin-shell permission

After installing the [shell plugin](/plugin/shell/) make sure you configure the required capabilities.

Note that we use `"args": true` but you can optionally provide an array `["hello"]`, [read more](/develop/sidecar/#passing-arguments).

1.  ##### Configure the Sidecar in the Tauri Application

Now that we have our Node.js application ready, we can connect it to our Tauri application
    by configuring the [`bundle > externalBin`] array:

The Tauri CLI will handle the bundling of the sidecar binary as long as it exists as `src-tauri/binaries/my-sidecar-<target-triple>`.

1.  ##### Execute the Sidecar

We can run the sidecar binary either from Rust code or directly from JavaScript.

<Tabs syncKey="lang">

<TabItem label="JavaScript">

Let's execute the `hello` command in the Node.js sidecar directly:

<TabItem label="Rust">

Let's pipe a `hello` Tauri command to the Node.js sidecar:

Register it in `invoke_handler` and call it in the frontend with:

<CommandTabs
      npm="npm run tauri dev"
      yarn="yarn tauri dev"
      pnpm="pnpm tauri dev"
      deno="deno task tauri dev"
      bun="bun tauri dev"
      cargo="cargo tauri dev"
    />

Open the DevTools with F12 (or `Cmd+Option+I` on macOS) and you should see the output of the sidecar command.

If you find any issues, please open an issue on [GitHub](https://github.com/tauri-apps/tauri-docs).

[sidecar guide]: /develop/sidecar/
[process.argv]: https://nodejs.org/docs/latest/api/process.html#processargv
[console.log]: https://nodejs.org/api/console.html#consolelogdata-args
[pkg]: https://github.com/vercel/pkg
[`bundle > externalBin`]: /reference/config/#externalbin

**Examples:**

Example 1 (unknown):
```unknown
1.  ##### Package the Sidecar

    To package our Node.js application into a self contained binary, create a script in `package.json`:
```

Example 2 (unknown):
```unknown
<CommandTabs npm="npm run build" yarn="yarn build" pnpm="pnpm build" />

    This will create the `sidecar-app/my-sidecar` binary on Linux and macOS, and a `sidecar-app/my-sidecar.exe` executable on Windows.

    For sidecar applications, we need to ensure that the binary is named in the correct pattern, for more information read [Embedding External Binaries](https://tauri.app/develop/sidecar/)
    To rename this file to the expected Tauri sidecar filename and also move to our Tauri project, we can use the following Node.js script as a starting example:
```

Example 3 (unknown):
```unknown
And run `node rename.js` from the `sidecar-app` directory.

    At this step the `/src-tauri/binaries` directory should contain the renamed sidecar binary.

1.  ##### Setup plugin-shell permission

    After installing the [shell plugin](/plugin/shell/) make sure you configure the required capabilities.

    Note that we use `"args": true` but you can optionally provide an array `["hello"]`, [read more](/develop/sidecar/#passing-arguments).
```

Example 4 (unknown):
```unknown
1.  ##### Configure the Sidecar in the Tauri Application

    Now that we have our Node.js application ready, we can connect it to our Tauri application
    by configuring the [`bundle > externalBin`] array:
```

---

## SvelteKit

**URL:** llms-txt#sveltekit

**Contents:**
- Checklist
- Example Configuration

import { Tabs, TabItem, Steps } from '@astrojs/starlight/components';
import CommandTabs from '@components/CommandTabs.astro';

SvelteKit is a meta framework for Svelte. Learn more about SvelteKit at https://svelte.dev/. This guide is accurate as of SvelteKit 2.20.4 / Svelte 5.25.8.

- Use [SSG](https://svelte.dev/docs/kit/adapter-static) and [SPA](https://svelte.dev/docs/kit/single-page-apps) via `static-adapter`. Tauri doesn't support server-based solutions.
- If using SSG **with prerendering**, be aware that `load` functions will not have access to tauri APIs during the build process of your app. Using SPA mode (without prerendering) is recommended since the load functions will only run in the webview with access to tauri APIs.
- Use `build/` as `frontendDist` in `tauri.conf.json`.

## Example Configuration

1.  ##### Install `@sveltejs/adapter-static`

<CommandTabs
      npm="npm install --save-dev @sveltejs/adapter-static"
      yarn="yarn add -D @sveltejs/adapter-static"
      pnpm="pnpm add -D @sveltejs/adapter-static"
      deno="deno add -D npm:@sveltejs/adapter-static"
    />

1.  ##### Update Tauri configuration

<TabItem label="npm">

<TabItem label="yarn">

<TabItem label="pnpm">

<TabItem label="deno">

1.  ##### Update SvelteKit configuration:

1.  ##### Disable SSR

Lastly, we need to disable SSR by adding a root `+layout.ts` file (or `+layout.js` if you are not using TypeScript) with these contents:

Note that `static-adapter` doesn't require you to disable SSR for the whole app but it makes it possible to use APIs that depend on the global window object (like Tauri's API) without [Client-side checks](https://svelte.dev/docs/kit/faq#how-do-i-use-x-with-sveltekit-how-do-i-use-a-client-side-only-library-that-depends-on-document-or-window).

Furthermore, if you prefer Static Site Generation (SSG) over Single-Page Application (SPA) mode, you can change the adapter configurations and `+layout.ts` according to the [adapter docs](https://svelte.dev/docs/kit/adapter-static).

**Examples:**

Example 1 (json):
```json
// tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "npm run dev",
        "beforeBuildCommand": "npm run build",
        "devUrl": "http://localhost:5173",
        "frontendDist": "../build"
      }
    }
```

Example 2 (json):
```json
// tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "yarn dev",
        "beforeBuildCommand": "yarn build",
        "devUrl": "http://localhost:5173",
        "frontendDist": "../build"
      }
    }
```

Example 3 (json):
```json
// tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "pnpm dev",
        "beforeBuildCommand": "pnpm build",
        "devUrl": "http://localhost:5173",
        "frontendDist": "../build"
      }
    }
```

Example 4 (json):
```json
// tauri.conf.json
    {
      "build": {
        "beforeDevCommand": "deno task dev",
        "beforeBuildCommand": "deno task build",
        "devUrl": "http://localhost:5173",
        "frontendDist": "../build"
      }
    }
```

---

## Learn

**URL:** llms-txt#learn

**Contents:**
- More Resources
  - Books
  - Guides & Tutorials

import { Card, CardGrid, LinkCard } from '@astrojs/starlight/components';
import AwesomeTauri from '@components/AwesomeTauri.astro';
import BookItem from '@components/BookItem.astro';
import RoseRustBook from '@assets/learn/community/HTML_CSS_JavaScript_and_Rust_for_Beginners_A_Guide_to_Application_Development_with_Tauri.png';

The Learning category is intended to provide end-to-end learning experiences on a Tauri related topic.

These tutorials will guide you through a specific topic and help you apply knowledge from the guides and reference documentation.

For security related topics, you can learn about the permissions system. You will get practical insight into how to use it, extend it, and write your own permissions.

<CardGrid>
  <LinkCard
    title="Using Plugin Permissions"
    href="/learn/security/using-plugin-permissions/"
  />
  <LinkCard
    title="Capabilities for Different Windows and Platforms"
    href="/learn/security/capabilities-for-windows-and-platforms/"
  />
  <LinkCard
    title="Writing Plugin Permissions"
    href="/learn/security/writing-plugin-permissions/"
  />
</CardGrid>

To learn how to write your own splash screen or use a node.js sidecar, check out:

<CardGrid>
  <LinkCard title="Splashcreen" href="/learn/splashscreen/" />
  <LinkCard title="Node.js as a Sidecar" href="/learn/sidecar-nodejs/" />
</CardGrid>

This section contains learning resources created by the Community that are not hosted on this website.

<LinkCard
  title="Have something to share?"
  description="Open a pull request to show us your amazing resource."
  href="https://github.com/tauri-apps/awesome-tauri/pulls"
/>

<BookItem
  image={RoseRustBook}
  title="HTML, CSS, JavaScript, and Rust for Beginners: A Guide to Application Development with Tauri"
  alt="HTML, CSS, JavaScript, and Rust for Beginners Book Cover"
  author="James Alexander Rose"
  links={[
    {
      preText: 'Paperback on Amazon:',
      text: 'Buy Here',
      url: 'https://www.amazon.com/dp/B0DR6KZVVW',
    },
    {
      preText: 'Free PDF version:',
      text: 'Download (PDF 4MB)',
      url: '/assets/learn/community/HTML_CSS_JavaScript_and_Rust_for_Beginners_A_Guide_to_Application_Development_with_Tauri.pdf',
    },
  ]}
/>

### Guides & Tutorials

<AwesomeTauri section="guides-no-official-no-video" />

<AwesomeTauri section="guides-no-official-only-video" />

---

## Qwik

**URL:** llms-txt#qwik

**Contents:**
- Checklist
- Example Configuration

import { Steps, TabItem, Tabs } from '@astrojs/starlight/components';
import CommandTabs from '@components/CommandTabs.astro';

This guide will walk you through creating your Tauri app using the Qwik web framework. Learn more about Qwik at https://qwik.dev.

- Use [SSG](https://qwik.dev/docs/guides/static-site-generation/). Tauri doesn't support server-based solutions.
- Use `dist/` as `frontendDist` in `tauri.conf.json`.

## Example Configuration

1.  ##### Create a new Qwik app

<CommandTabs
      npm={`npm create qwik@latest
    cd <PROJECT>`}
      yarn={`yarn create qwik@latest
    cd <PROJECT>`}
      pnpm={`pnpm create qwik@latest
    cd <PROJECT>`}
      deno={`deno run -A npm:create-qwik@latest
    cd <PROJECT>`}
    />

1.  ##### Install the `static adapter`

<CommandTabs
      npm="npm run qwik add static"
      yarn="yarn qwik add static"
      pnpm="pnpm qwik add static"
      deno="deno task qwik add static"
    />

1.  ##### Add the Tauri CLI to your project

<CommandTabs
      npm="npm install -D @tauri-apps/cli@latest"
      yarn="yarn add -D @tauri-apps/cli@latest"
      pnpm="pnpm add -D @tauri-apps/cli@latest"
      deno="deno add -D npm:@tauri-apps/cli@latest"
    />

1.  ##### Initiate a new Tauri project

<CommandTabs
      npm="npm run tauri init"
      yarn="yarn tauri init"
      pnpm="pnpm tauri init"
      deno="deno task tauri init"
    />

1.  ##### Tauri configuration

<TabItem label="npm">

<TabItem label="yarn">

<TabItem label="pnpm">

<TabItem label="deno">

1.  ##### Start your `tauri` app

<CommandTabs
      npm="npm run tauri dev"
      yarn="yarn tauri dev"
      pnpm="pnpm tauri dev"
      deno="deno task tauri dev"
    />

**Examples:**

Example 1 (json):
```json
// tauri.conf.json
    {
      "build": {
        "devUrl": "http://localhost:5173"
        "frontendDist": "../dist",
        "beforeDevCommand": "npm run dev",
        "beforeBuildCommand": "npm run build"
      }
    }
```

Example 2 (json):
```json
// tauri.conf.json
    {
      "build": {
        "devUrl": "http://localhost:5173"
        "frontendDist": "../dist",
        "beforeDevCommand": "yarn dev",
        "beforeBuildCommand": "yarn build"
      }
    }
```

Example 3 (json):
```json
// tauri.conf.json
    {
      "build": {
        "devUrl": "http://localhost:5173"
        "frontendDist": "../dist",
        "beforeDevCommand": "pnpm dev",
        "beforeBuildCommand": "pnpm build"
      }
    }
```

Example 4 (json):
```json
// tauri.conf.json
    {
      "build": {
        "devUrl": "http://localhost:5173"
        "frontendDist": "../dist",
        "beforeDevCommand": "deno task dev",
        "beforeBuildCommand": "deno task build"
      }
    }
```

---

## Nuxt

**URL:** llms-txt#nuxt

**Contents:**
- Checklist
- Example Configuration

import { Tabs, TabItem, Steps } from '@astrojs/starlight/components';

Nuxt is a meta framework for Vue. Learn more about Nuxt at https://nuxt.com. This guide is accurate as of Nuxt 3.17.

- Use SSG by setting `ssr: false`. Tauri doesn't support server based solutions.
- Use default `../dist` as `frontendDist` in `tauri.conf.json`.
- Compile using `nuxi build`.
- (Optional): Disable telemetry by setting `telemetry: false` in `nuxt.config.ts`.

## Example Configuration

1.  ##### Update Tauri configuration

<TabItem label="npm">

</TabItem>
              <TabItem label="yarn">

</TabItem>
              <TabItem label="pnpm">

</TabItem>
              <TabItem label="deno">

1.  ##### Update Nuxt configuration

**Examples:**

Example 1 (json):
```json
// tauri.conf.json
        {
          "build": {
            "beforeDevCommand": "npm run dev",
            "beforeBuildCommand": "npm run build",
            "devUrl": "http://localhost:3000",
            "frontendDist": "../dist"
          }
        }
```

Example 2 (json):
```json
// tauri.conf.json
        {
          "build": {
            "beforeDevCommand": "yarn dev",
            "beforeBuildCommand": "yarn build",
            "devUrl": "http://localhost:3000",
            "frontendDist": "../dist"
          }
        }
```

Example 3 (json):
```json
// tauri.conf.json
        {
          "build": {
            "beforeDevCommand": "pnpm dev",
            "beforeBuildCommand": "pnpm build",
            "devUrl": "http://localhost:3000",
            "frontendDist": "../dist"
          }
        }
```

Example 4 (json):
```json
// tauri.conf.json
        {
          "build": {
            "beforeDevCommand": "deno task dev",
            "beforeBuildCommand": "deno task generate",
            "devUrl": "http://localhost:3000",
            "frontendDist": "../dist"
          }
        }
```

---
