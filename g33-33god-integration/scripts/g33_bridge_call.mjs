#!/usr/bin/env node
/**
 * Test/probe harness: invoke the REAL g33 PJangler bridge through its
 * exported owner API (dynamic import — the same resolution path PJangler's
 * companion.ts uses) and print the reply as JSON.
 *
 * Usage: node g33_bridge_call.mjs '<request-json>' [--module PATH.mjs] [--python BIN]
 * Exit code is always 0 when the bridge replied (reply.status says the rest).
 */
import { pathToFileURL, fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";

const argv = process.argv.slice(2);
let requestJson = argv[0] ?? "{}";
let modulePath = resolve(import.meta.dirname || dirname(fileURLToPath(import.meta.url)), "g33_pjangler_bridge.mjs");
let python;
for (let i = 1; i < argv.length; i += 2) {
  if (argv[i] === "--module") modulePath = resolve(argv[i + 1]);
  else if (argv[i] === "--python") python = argv[i + 1];
}

const mod = await import(pathToFileURL(modulePath).href);
const callable = mod.g33Companion ?? mod.default;
if (typeof callable !== "function") {
  console.error(`export g33Companion not callable in ${modulePath}`);
  process.exit(3);
}
const request = JSON.parse(requestJson);
if (python) {
  request.options = { ...(request.options ?? {}), pythonExecutable: python };
}
const reply = await callable(request);
process.stdout.write(JSON.stringify(reply) + "\n");
