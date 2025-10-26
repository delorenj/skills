# Tauri - Plugins

**Pages:** 5

---

## Check https://v2.tauri.app/plugin/single-instance/ for details

**URL:** llms-txt#check-https://v2.tauri.app/plugin/single-instance/-for-details

---

## Updating Dependencies

**URL:** llms-txt#updating-dependencies

**Contents:**
- Update npm Packages
- Update Cargo Packages
- Sync npm Packages and Cargo Crates versions

{/* TODO: Add plugin update example */}

import CommandTabs from '@components/CommandTabs.astro';

## Update npm Packages

If you are using the `tauri` package:

<CommandTabs
  npm="npm install @tauri-apps/cli@latest @tauri-apps/api@latest"
  yarn="yarn up @tauri-apps/cli @tauri-apps/api"
  pnpm="pnpm update @tauri-apps/cli @tauri-apps/api --latest"
/>

You can also detect what the latest version of Tauri is on the command line, using:

<CommandTabs
  npm="npm outdated @tauri-apps/cli"
  yarn="yarn outdated @tauri-apps/cli"
  pnpm="pnpm outdated @tauri-apps/cli"
/>

## Update Cargo Packages

You can check for outdated packages with [`cargo outdated`] or on the crates.io pages: [tauri] / [tauri-build].

Go to `src-tauri/Cargo.toml` and change `tauri` and `tauri-build` to

where `%version%` is the corresponding version number from above.

Then do the following:

Alternatively, you can run the `cargo upgrade` command provided by [cargo-edit] which does all of this automatically.

## Sync npm Packages and Cargo Crates versions

Since the JavaScript APIs rely on Rust code in the backend, adding a new feature requires upgrading both sides to ensure compatibility. Please make sure you have the same minor version of the npm package `@tauri-apps/api` and cargo crate `tauri` synced

And for the plugins, we might introduce this type of changes in patch releases, so we bump the npm package and cargo crate versions together, and you need to keep the exact versions synced, for example, you need the same version (e.g. `2.2.1`) of the npm package `@tauri-apps/plugin-fs` and cargo crate `tauri-plugin-fs`

[`cargo outdated`]: https://github.com/kbknapp/cargo-outdated
[tauri]: https://crates.io/crates/tauri/versions
[tauri-build]: https://crates.io/crates/tauri-build/versions
[cargo-edit]: https://github.com/killercup/cargo-edit

**Examples:**

Example 1 (toml):
```toml
[build-dependencies]
tauri-build = "%version%"

[dependencies]
tauri = { version = "%version%" }
```

Example 2 (shell):
```shell
cd src-tauri
cargo update
```

---

## Plugins

**URL:** llms-txt#plugins

---

## Mock Tauri APIs

**URL:** llms-txt#mock-tauri-apis

**Contents:**
- IPC Requests
  - Mocking Commands for `invoke`
  - Mocking Events
- Windows

import SinceVersion from '../../../../components/SinceVersion.astro';

When writing your frontend tests, having a "fake" Tauri environment to simulate windows or intercept IPC calls is common, so-called _mocking_.
The [`@tauri-apps/api/mocks`] module provides some helpful tools to make this easier for you:

Remember to clear mocks after each test run to undo mock state changes between runs! See [`clearMocks()`] docs for more info.

Most commonly, you want to intercept IPC requests; this can be helpful in a variety of situations:

- Ensure the correct backend calls are made
- Simulate different results from backend functions

Tauri provides the mockIPC function to intercept IPC requests. You can find more about the specific API in detail [here][`mockipc()`].

The following examples use [Vitest], but you can use any other frontend testing library such as jest.

### Mocking Commands for `invoke`

Sometimes you want to track more information about an IPC call; how many times was the command invoked? Was it invoked at all?
You can use [`mockIPC()`] with other spying and mocking tools to test this:

To mock IPC requests to a sidecar or shell command you need to grab the ID of the event handler when `spawn()` or `execute()` is called and use this ID to emit events the backend would send back:

<SinceVersion version="2.7.0" />

There is partial support of the [Event System] to simulate events emitted by your Rust code via the `shouldMockEvents` option:

`emitTo` and `emit_filter` are **not** supported yet.

Sometimes you have window-specific code (a splash screen window, for example), so you need to simulate different windows.
You can use the [`mockWindows()`] method to create fake window labels. The first string identifies the "current" window (i.e., the window your JavaScript believes itself in), and all other strings are treated as additional windows.

[`mockWindows()`] only fakes the existence of windows but no window properties. To simulate window properties, you need to intercept the correct calls using [`mockIPC()`]

[`@tauri-apps/api/mocks`]: /reference/javascript/api/namespacemocks/
[`mockipc()`]: /reference/javascript/api/namespacemocks/#mockipc
[`mockwindows()`]: /reference/javascript/api/namespacemocks/#mockwindows
[`clearmocks()`]: /reference/javascript/api/namespacemocks/#clearmocks
[vitest]: https://vitest.dev
[Event System]: /develop/calling-frontend/#event-system

**Examples:**

Example 1 (javascript):
```javascript
import { beforeAll, expect, test } from "vitest";
import { randomFillSync } from "crypto";

import { mockIPC } from "@tauri-apps/api/mocks";
import { invoke } from "@tauri-apps/api/core";

// jsdom doesn't come with a WebCrypto implementation
beforeAll(() => {
  Object.defineProperty(window, 'crypto', {
    value: {
      // @ts-ignore
      getRandomValues: (buffer) => {
        return randomFillSync(buffer);
      },
    },
  });
});


test("invoke simple", async () => {
  mockIPC((cmd, args) => {
    // simulated rust command called "add" that just adds two numbers
    if(cmd === "add") {
      return (args.a as number) + (args.b as number);
    }
  });
});
```

Example 2 (javascript):
```javascript
import { beforeAll, expect, test, vi } from "vitest";
import { randomFillSync } from "crypto";

import { mockIPC } from "@tauri-apps/api/mocks";
import { invoke } from "@tauri-apps/api/core";

// jsdom doesn't come with a WebCrypto implementation
beforeAll(() => {
  Object.defineProperty(window, 'crypto', {
    value: {
      // @ts-ignore
      getRandomValues: (buffer) => {
        return randomFillSync(buffer);
      },
    },
  });
});


test("invoke", async () => {
  mockIPC((cmd, args) => {
    // simulated rust command called "add" that just adds two numbers
    if(cmd === "add") {
      return (args.a as number) + (args.b as number);
    }
  });

  // we can use the spying tools provided by vitest to track the mocked function
  const spy = vi.spyOn(window.__TAURI_INTERNALS__, "invoke");

  expect(invoke("add", { a: 12, b: 15 })).resolves.toBe(27);
  expect(spy).toHaveBeenCalled();
});
```

Example 3 (javascript):
```javascript
mockIPC(async (cmd, args) => {
  if (args.message.cmd === 'execute') {
    const eventCallbackId = `_${args.message.onEventFn}`;
    const eventEmitter = window[eventCallbackId];

    // 'Stdout' event can be called multiple times
    eventEmitter({
      event: 'Stdout',
      payload: 'some data sent from the process',
    });

    // 'Terminated' event must be called at the end to resolve the promise
    eventEmitter({
      event: 'Terminated',
      payload: {
        code: 0,
        signal: 'kill',
      },
    });
  }
});
```

Example 4 (javascript):
```javascript
import { mockIPC, clearMocks } from '@tauri-apps/api/mocks';
import { emit, listen } from '@tauri-apps/api/event';
import { afterEach, expect, test, vi } from 'vitest';

test('mocked event', () => {
  mockIPC(() => {}, { shouldMockEvents: true }); // enable event mocking

  const eventHandler = vi.fn();
  listen('test-event', eventHandler);

  emit('test-event', { foo: 'bar' });
  expect(eventHandler).toHaveBeenCalledWith({
    event: 'test-event',
    payload: { foo: 'bar' },
  });
});
```

---

## Add these lines only if you're using the single-instance plugin

**URL:** llms-txt#add-these-lines-only-if-you're-using-the-single-instance-plugin

---
