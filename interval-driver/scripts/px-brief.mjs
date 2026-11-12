#!/usr/bin/env node
// Compact ticket view for interval agents: the lazy-load primitive.
//
// `px show <REF> --json` is ~50 KB (~12k tokens) on a busy ticket because it carries every
// comment's HTML. An agent that reads five of those per pass re-sends 60k tokens on every later
// LLM call. This prints the same ticket in ~1k tokens: header, a clipped description and the last
// few comments as plain text. Run it from the repo whose board you read (px resolves the board
// from the cwd).
//
//   px-brief.mjs GRUV-29 GRUV-78            # last 3 comments, 1200-char description
//   px-brief.mjs --comments 6 --chars 3000 GRUV-29
//   px-brief.mjs --full GRUV-29             # everything, still as plain text

import { execFile } from "node:child_process";
import { promisify } from "node:util";

const run = promisify(execFile);
const args = process.argv.slice(2);
let comments = 3;
let chars = 1200;
let commentChars = 500;
const refs = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === "--comments") comments = Number(args[++i]);
  else if (a === "--chars") chars = Number(args[++i]);
  else if (a === "--comment-chars") commentChars = Number(args[++i]);
  else if (a === "--full") (comments = Infinity), (chars = Infinity), (commentChars = Infinity);
  else if (a === "-h" || a === "--help") {
    console.log("usage: px-brief.mjs [--comments N] [--chars N] [--comment-chars N] [--full] REF...");
    process.exit(0);
  } else refs.push(a);
}
if (!refs.length) {
  console.error("px-brief: give at least one ticket ref");
  process.exit(2);
}

const flat = (s) => String(s ?? "").replace(/\s+/g, " ").trim();
const clip = (s, n) => (s.length > n ? `${s.slice(0, n)} …[+${s.length - n} chars]` : s);
const day = (s) => String(s ?? "").slice(0, 16).replace("T", " ");

let failed = 0;
for (const ref of refs) {
  let t;
  try {
    const { stdout } = await run("px", ["show", ref, "--json"], { maxBuffer: 64 << 20, timeout: 60_000 });
    t = JSON.parse(stdout).ticket;
  } catch (e) {
    console.log(`## ${ref}: UNREADABLE (${flat(e?.code ?? e?.message).slice(0, 80)})\n`);
    failed++;
    continue;
  }
  const labels = [...(t.label_names ?? [])].sort().join(", ");
  const all = Array.isArray(t.comments) ? t.comments : [];
  const shown = Number.isFinite(comments) ? all.slice(-comments) : all;
  const out = [
    `## ${t.ref} · ${t.lane ?? t.state_name} · p:${t.priority ?? "none"} · updated ${day(t.updated_at)}`,
    flat(t.name),
    `labels: ${labels || "-"}${t.parent_ref ? ` · parent ${t.parent_ref}` : ""}${t.target_date ? ` · due ${t.target_date}` : ""}`,
    `description: ${clip(flat(t.description_text), chars) || "-"}`,
    `comments: ${all.length}${shown.length < all.length ? ` (last ${shown.length})` : ""}`,
    ...shown.map((c) => `- ${day(c.created_at)} ${flat(c.actor_name)}: ${clip(flat(c.text ?? c.comment_html), commentChars)}`),
    "",
  ];
  console.log(out.join("\n"));
}
process.exit(failed === refs.length ? 1 : 0);
