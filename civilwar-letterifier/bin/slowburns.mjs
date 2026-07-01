#!/usr/bin/env node
/**
 * slowburns — the SlowBurns CLI. Turn any text into a Ken Burns documentary
 * dispatch video in one command.
 *
 *   slowburns something.txt
 *
 * That reads something.txt, rewrites it as a solemn Civil War-era field
 * dispatch (burns-speak), narrates it in the period voice, lays a mournful
 * music bed and an always-on field-ambience bed underneath, renders the letter
 * in script on aged parchment with a slow Ken Burns drift, and writes a
 * uniquely named, time-ordered MP4 to ./out.
 *
 * Defaults (just `slowburns file.txt`): letterify ON, music ON, ambient ON.
 *
 * Usage:
 *   slowburns <input.txt> [options]
 *   slowburns --text "I'll be late, dropping the kids at camp."
 *
 * Options:
 *   --text "..."        Inline text instead of a file
 *   --raw               Skip letterify; treat the input as finished period prose
 *   --mode <m>          Letterify register: standard | field-note | full | executive
 *   --model <slug>      OpenRouter model for letterify (default anthropic/claude-sonnet-5)
 *   --signer <name>     How the letter is signed (default "J."); the model writes
 *                       a cohesive sign-off around it
 *   --no-music          Disable the music bed
 *   --no-ambient        Disable the field-ambience bed
 *   --music <file>      Use a specific music track
 *   --ambient <file>    Use a specific ambient track
 *   --font <style>      script (default) | dispatch
 *   --out <file>        Override the output path
 *   --keep-letter       (default behavior) also write the letter text beside the video
 *   -h, --help
 *
 * Prereqs: Node 18+, ffmpeg, ELEVENLABS_API_KEY (narration + beds) and
 * SLOWBURNS_OPENROUTER_API_KEY (letterify, via OpenRouter), in the environment
 * or a .env.local file.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {letterify} from '../scripts/letterify.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const NODE = process.execPath;
const AUDIO_RE = /\.(mp3|wav|ogg|m4a|flac)$/i;

const HELP = `slowburns — turn text into a Ken Burns documentary dispatch video.

Usage:
  slowburns <input.txt> [options]
  slowburns --text "..."

Options:
  --text "..."      Inline text instead of a file
  --raw             Skip letterify; treat input as finished period prose
  --mode <m>        standard | field-note | full | executive  (default standard)
  --model <slug>    OpenRouter model for letterify (default anthropic/claude-sonnet-5)
  --signer <name>   How the letter is signed (default "J.")
  --no-music        Disable the music bed
  --no-ambient      Disable the field-ambience bed
  --music <file>    Use a specific music track
  --ambient <file>  Use a specific ambient track
  --font <style>    script (default) | dispatch
  --out <file>      Override the output path (default ./out/slowburns-<ts>.mp4)
  -h, --help

Defaults: letterify on, music on, ambient on. Output lands in ./out.`;

// --- .env.local (for ANTHROPIC_API_KEY used by letterify in-process) -------
function loadEnvLocal() {
  for (const p of [path.join(process.cwd(), '.env.local'), path.join(ROOT, '.env.local')]) {
    if (!fs.existsSync(p)) continue;
    for (const line of fs.readFileSync(p, 'utf8').split('\n')) {
      const i = line.indexOf('=');
      if (i > 0 && !line.trim().startsWith('#')) {
        const k = line.slice(0, i).trim();
        let v = line.slice(i + 1).trim();
        if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
          v = v.slice(1, -1);
        }
        if (!process.env[k]) process.env[k] = v;
      }
    }
  }
}

// --- arg parsing -----------------------------------------------------------
function parseArgs(argv) {
  const o = {mode: 'standard', font: 'script'};
  const positional = [];
  const takesValue = new Set(['--text', '--mode', '--model', '--signer', '--music', '--ambient', '--font', '--out']);
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '-h' || a === '--help') o.help = true;
    else if (a === '--raw') o.raw = true;
    else if (a === '--no-music') o.noMusic = true;
    else if (a === '--no-ambient') o.noAmbient = true;
    else if (a === '--keep-letter') o.keepLetter = true; // default-on; accepted for clarity
    else if (takesValue.has(a)) {
      const v = argv[++i];
      if (v === undefined) fail(`Option ${a} needs a value.`);
      o[a.slice(2)] = v;
    } else if (a.startsWith('--')) fail(`Unknown option: ${a}`);
    else positional.push(a);
  }
  o.input = positional[0];
  return o;
}

function fail(msg) {
  console.error(`slowburns: ${msg}`);
  process.exit(1);
}

function slugify(s) {
  return String(s)
    .toLowerCase()
    .replace(/\.[^.]+$/, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 32)
    .replace(/-+$/g, '');
}

function timestamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return (
    `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}` +
    `-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`
  );
}

function listAudio(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((f) => AUDIO_RE.test(f)).map((f) => path.join(dir, f));
}

function run(script, args) {
  execFileSync(NODE, [path.join(ROOT, 'scripts', script), ...args], {cwd: ROOT, stdio: 'inherit'});
}

// Ensure a cached music bed exists; return ['--music', file] | ['--no-music'].
function resolveMusicArgs(o) {
  if (o.noMusic) return ['--no-music'];
  if (o.music) return ['--music', path.resolve(o.music)];
  const existing = listAudio(path.join(ROOT, 'assets', 'music'));
  if (existing.length) return ['--music', existing[0]];
  const dest = path.join(ROOT, 'assets', 'music', 'score.mp3');
  console.log('\nNo music bed found — synthesizing one (cached for future runs)…');
  run('make-music.mjs', ['--out', dest, '--seconds', '22']);
  return ['--music', dest];
}

// Ensure a cached ambient bed exists; return ['--ambient', file] | ['--no-ambient'].
function resolveAmbientArgs(o) {
  if (o.noAmbient) return ['--no-ambient'];
  if (o.ambient) return ['--ambient', path.resolve(o.ambient)];
  const sfx = path.join(ROOT, 'assets', 'sfx');
  const existing = listAudio(sfx);
  const named = existing.find((f) => /(^|\/)ambient\.[^/]+$/i.test(f));
  if (existing.length) return ['--ambient', named || existing[0]];
  const dest = path.join(sfx, 'ambient.mp3');
  console.log('\nNo ambient bed found — synthesizing one (cached for future runs)…');
  run('make-ambient.mjs', ['--out', dest, '--seconds', '22']);
  return ['--ambient', dest];
}

async function main() {
  const o = parseArgs(process.argv.slice(2));
  if (o.help) {
    console.log(HELP);
    return;
  }
  loadEnvLocal();

  // 1. Resolve the source text + a slug for the filename.
  let sourceText;
  let slug;
  if (o.text) {
    sourceText = o.text;
    slug = 'dispatch';
  } else if (o.input) {
    const file = path.resolve(o.input);
    if (!fs.existsSync(file)) fail(`No such file: ${o.input}`);
    sourceText = fs.readFileSync(file, 'utf8');
    slug = slugify(path.basename(o.input)) || 'dispatch';
  } else {
    console.error(HELP);
    process.exit(1);
  }
  if (!sourceText.trim()) fail('Input text is empty.');

  if (!['standard', 'field-note', 'full', 'executive'].includes(o.mode)) {
    fail(`Unknown --mode "${o.mode}" (use standard | field-note | full | executive).`);
  }

  // 2. Letterify (the only creative step) unless --raw.
  let note;
  if (o.raw) {
    note = sourceText.trim();
    console.log('\n— Using input verbatim (--raw) —');
  } else {
    console.log(`\n✒️  Letterifying (${o.mode})…`);
    note = await letterify(sourceText, {mode: o.mode, model: o.model, signer: o.signer});
  }
  console.log('\n┌─ The dispatch ───────────────────────────────────────────────');
  console.log(note.split('\n').map((l) => '│ ' + l).join('\n'));
  console.log('└──────────────────────────────────────────────────────────────\n');

  // 3. Unique, time-ordered output path in ./out (relative to cwd).
  const outFile = o.out
    ? path.resolve(o.out)
    : path.resolve(process.cwd(), 'out', `slowburns-${timestamp()}-${slug}.mp4`);

  // 4. Audio beds (default on, cached).
  const musicArgs = resolveMusicArgs(o);
  const ambientArgs = resolveAmbientArgs(o);

  // 5. Render via the existing pipeline (narrate → beds → props → remotion).
  console.log(`\n🎬 Rendering → ${outFile}`);
  run('build.mjs', [
    '--text', note,
    '--out', outFile,
    '--font', o.font === 'dispatch' ? 'dispatch' : 'script',
    ...musicArgs,
    ...ambientArgs,
  ]);

  // 6. Save the letter beside the video as a record.
  const letterFile = outFile.replace(/\.mp4$/i, '') + '.letter.txt';
  fs.writeFileSync(letterFile, note + '\n');

  console.log(`\n✅ Done.`);
  console.log(`   Video:  ${outFile}`);
  console.log(`   Letter: ${letterFile}`);
}

main().catch((e) => {
  console.error(`\nslowburns: ${e.message}`);
  process.exit(1);
});
