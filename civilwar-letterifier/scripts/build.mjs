#!/usr/bin/env node
/**
 * build.mjs — the multimodal pipeline for the Civil War Letterifier.
 *
 * The ONLY creative/agentic input is the note text itself — the period prose
 * (including its own cohesive closing sign-off and signature) written by
 * translating the source message. Everything else — the date line, title,
 * narrator voice, music, ambient bed, and render — is deterministic and handled
 * here. Given that note text, this:
 *   1. narrates it with ElevenLabs (Cartesia capacity fallback) -> remotion/public/narration.mp3
 *   2. resolves a music bed (drop-in or auto) -> remotion/public/music.mp3
 *   2b. resolves the ambient bed (assets/sfx) -> remotion/public/ambient.mp3
 *   3. writes render props                    -> remotion/props.json
 *   4. renders the Ken Burns documentary clip -> out/<name>.mp4
 *
 * The narrator voice is hardcoded (the custom "Civil War Veteran"); it is not
 * parameterized — see scripts/narrate.mjs. The ambient bed (assets/sfx) is an
 * always-on field-atmosphere layer beneath everything for the whole film,
 * independent of the optional music bed.
 *
 * Usage — pass the note as text, a text file, or a spec's letterText:
 *   node scripts/build.mjs --text "My dear colleagues, ..." --out out/letter.mp4
 *   node scripts/build.mjs --file note.txt
 *   node scripts/build.mjs --spec letter.json            (uses only .letterText)
 *   node scripts/build.mjs --text "..." --auto-music
 *   node scripts/build.mjs --text "..." --music assets/music/ashokan.mp3
 *   node scripts/build.mjs --text "..." --font dispatch  (script is the default)
 *
 * The date line ("From the Encampment, this Nth day of <Month>") is generated
 * from today's date; the title is a fixed constant below. The signature is NOT
 * added here — it is part of the letterified note (the model writes its own).
 *
 * Auth: process environment only: ELEVENLABS_API_KEY (or ELEVEN_API_KEY), plus
 * optional CARTESIA_API_KEY/CARTESIA_VOICE_ID for bounded capacity fallback.
 * Requires Node 18+ (fetch) and,
 * for rendering, the remotion/ project deps (auto-installed on first run).
 */
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {resolveJobNarrationPaths} from './narrate.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const REMOTION = path.join(ROOT, 'remotion');
const PUBLIC = path.join(REMOTION, 'public');

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  if (i === -1) return def;
  const v = process.argv[i + 1];
  return v && !v.startsWith('--') ? v : true; // bare flag -> true
}
function failIdentity(message) {
  console.error(`Error: ${message}`);
  process.exit(1);
}
function parseNarrationIdentityArgs(argv) {
  const values = {};
  for (const [key, flag] of [['jobId', '--job-id'], ['claimOperationId', '--claim-operation-id']]) {
    const positions = [];
    for (let i = 0; i < argv.length; i += 1) {
      if (argv[i] === flag) positions.push(i);
      if (argv[i].startsWith(`${flag}=`)) {
        failIdentity(`${flag} must be supplied once as ${flag} <value>.`);
      }
    }
    if (positions.length > 1) failIdentity(`${flag} must not be repeated.`);
    if (positions.length === 0) continue;
    const value = argv[positions[0] + 1];
    if (value === undefined || value.startsWith('--')) {
      failIdentity(`${flag} needs a value.`);
    }
    if (value.trim().length === 0 || value.length > 256 || /[\0-\x1f\x7f]/.test(value)) {
      failIdentity(`${flag} must be a nonempty, bounded identity without control characters.`);
    }
    values[key] = value;
  }
  if (Boolean(values.jobId) !== Boolean(values.claimOperationId)) {
    failIdentity('--job-id and --claim-operation-id must be supplied together.');
  }
  return values.jobId ? values : null;
}
function run(cmd, args, cwd, {input} = {}) {
  console.log(`\n$ ${cmd} ${args.join(' ')}`);
  execFileSync(cmd, args, {
    cwd: cwd || ROOT,
    stdio: input === undefined ? 'inherit' : ['pipe', 'inherit', 'inherit'],
    input,
  });
}

// --- Deterministic scaffolding --------------------------------------------
// The title card + date line never come from the agent. The signature is NOT
// here — it's part of the letterified note (the model writes its own cohesive
// sign-off), so it matches the letter's content instead of being a fixed string.
const TITLE = 'A Letter from the Front';

// "From the Encampment, this 30th day of June" — derived from today's date.
function periodDateLine() {
  const d = new Date();
  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
  ];
  const day = d.getDate();
  const j = day % 10;
  const k = day % 100;
  const suffix =
    j === 1 && k !== 11 ? 'st' :
    j === 2 && k !== 12 ? 'nd' :
    j === 3 && k !== 13 ? 'rd' : 'th';
  return `From the Encampment, this ${day}${suffix} day of ${months[d.getMonth()]}`;
}

// --- Inputs (the note is the ONLY creative input) -------------------------
// Accept the period prose as --text, --file <txt>, or --spec <json>.letterText.
function readNoteText() {
  const t = arg('text');
  if (t && t !== true) return t;
  const f = arg('file');
  if (f && f !== true) return fs.readFileSync(path.resolve(f), 'utf8').trim();
  const s = arg('spec');
  if (s && s !== true) {
    const spec = JSON.parse(fs.readFileSync(path.resolve(s), 'utf8'));
    if (spec.letterText) return String(spec.letterText).trim();
  }
  return null;
}
const letterText = readNoteText();
if (!letterText) {
  console.error('Error: provide the note via --text "...", --file <txt>, or --spec <letter.json> (with letterText).');
  process.exit(1);
}

const musicPath = arg('music'); // explicit drop-in track
const autoMusic = arg('auto-music', false);
const noMusic = arg('no-music', false); // force voice-only (overrides drop-in/auto)
const ambientPath = arg('ambient'); // explicit ambient track (else assets/sfx)
const ambientVolume = parseFloat(arg('ambient-volume', '0.16'));
const noAmbient = arg('no-ambient', false); // force-skip the ambient layer

function pickRandomTrack(dir) {
  const files = fs.readdirSync(dir).filter((f) => /\.(mp3|wav|ogg|m4a|flac)$/i.test(f));
  if (files.length === 0) return null;
  return path.join(dir, files[Math.floor(Math.random() * files.length)]);
}
// The ambient bed lives in assets/sfx. Prefer a track literally named
// "ambient.*"; otherwise fall back to any audio file (random if several).
function pickAmbientTrack(dir) {
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir).filter((f) => /\.(mp3|wav|ogg|m4a|flac)$/i.test(f));
  if (files.length === 0) return null;
  const named = files.find((f) => /^ambient\.(mp3|wav|ogg|m4a|flac)$/i.test(f));
  const chosen = named || files[Math.floor(Math.random() * files.length)];
  return path.join(dir, chosen);
}
const outFile = path.resolve(arg('out', path.join(ROOT, 'out', 'letter.mp4')));
const narrationIdentity = parseNarrationIdentityArgs(process.argv.slice(2));
const introPad = parseFloat(arg('intro-pad', '3.5'));
const outroPad = parseFloat(arg('outro-pad', '4'));
const accentColor = arg('accent', '#5a2a16');
const fontStyle = arg('font') === 'dispatch' ? 'dispatch' : 'script';

fs.mkdirSync(path.dirname(outFile), {recursive: true});
const localOutputIdentity = crypto.createHash('sha256').update(outFile).digest('hex');
const narration = resolveJobNarrationPaths({
  workRoot: path.dirname(outFile),
  jobId: narrationIdentity?.jobId || 'local-render',
  claimOperationId: narrationIdentity?.claimOperationId
    ? narrationIdentity.claimOperationId
    : `output-${localOutputIdentity}`,
});
fs.mkdirSync(narration.publicDir, {recursive: true});

// --- 1. Narration ---------------------------------------------------------
// narrate.mjs uses the fixed Eleven narrator and an explicitly configured
// Cartesia fallback voice; no provider retry loop is permitted.
run('node', [
  path.join(ROOT, 'scripts', 'narrate.mjs'),
  '--stdin',
  '--out', narration.out,
  '--receipt', narration.receiptPath,
  '--operation-id', narration.operationId,
], ROOT, {input: letterText});

// --- 2. Music bed ---------------------------------------------------------
const musicDest = path.join(narration.publicDir, 'music.mp3');
let hasMusic = false;
if (noMusic) {
  console.log('\nMusic disabled (--no-music). Voice only.');
} else if (musicPath && musicPath !== true) {
  fs.copyFileSync(path.resolve(musicPath), musicDest);
  hasMusic = true;
  console.log(`\nUsing drop-in music: ${musicPath}`);
} else if (autoMusic) {
  run('node', [
    path.join(ROOT, 'scripts', 'make-music.mjs'),
    '--out', musicDest,
    '--seconds', '22',
  ]);
  hasMusic = true;
} else {
  const randomTrack = pickRandomTrack(path.join(ROOT, 'assets', 'music'));
  if (randomTrack) {
    fs.copyFileSync(randomTrack, musicDest);
    hasMusic = true;
    console.log(`\nUsing random music: ${randomTrack}`);
  } else {
    console.log('\nNo music selected (pass --music <file> or --auto-music). Voice only.');
  }
}

// --- 2b. Ambient bed ------------------------------------------------------
// Always-on field atmosphere, layered beneath everything for the whole film,
// independent of whether a music bed was selected. Resolved from --ambient or,
// by default, from assets/sfx/.
const ambientDest = path.join(narration.publicDir, 'ambient.mp3');
let hasAmbient = false;
if (noAmbient) {
  console.log('\nAmbient bed disabled (--no-ambient).');
} else if (ambientPath && ambientPath !== true) {
  fs.copyFileSync(path.resolve(ambientPath), ambientDest);
  hasAmbient = true;
  console.log(`\nUsing drop-in ambient bed: ${ambientPath}`);
} else {
  const ambientTrack = pickAmbientTrack(path.join(ROOT, 'assets', 'sfx'));
  if (ambientTrack) {
    fs.copyFileSync(ambientTrack, ambientDest);
    hasAmbient = true;
    console.log(`\nUsing ambient bed: ${ambientTrack}`);
  } else {
    console.log('\nNo ambient bed found in assets/sfx (skipping ambient layer).');
  }
}

// --- 3. Props -------------------------------------------------------------
const props = {
  letterText,
  dateLine: periodDateLine(),
  signature: '', // the sign-off is written into letterText by letterify
  title: TITLE,
  fontStyle,
  hasMusic,
  hasAmbient,
  narrationFile: 'narration.mp3',
  musicFile: 'music.mp3',
  ambientFile: 'ambient.mp3',
  ambientVolume,
  introPad,
  outroPad,
  accentColor,
};
const propsPath = narration.propsPath;
fs.writeFileSync(propsPath, JSON.stringify(props, null, 2), {mode: 0o600});
console.log(`\nWrote props -> ${propsPath}`);

// --- 4. Render ------------------------------------------------------------
let renderFailure;
try {
  if (!fs.existsSync(path.join(REMOTION, 'node_modules'))) {
    console.log('\nInstalling Remotion deps (first run only)…');
    run('npm', ['install'], REMOTION);
  }
  run('npx', [
    'remotion', 'render', 'CivilWarLetter', outFile,
    `--props=${propsPath}`,
    `--public-dir=${narration.publicDir}`,
  ], REMOTION);
} catch (error) {
  renderFailure = error;
  throw error;
} finally {
  try {
    fs.rmSync(propsPath, {force: true});
  } catch (cleanupError) {
    if (!renderFailure) throw cleanupError;
  }
}

console.log(`\n✅ Done. Your dispatch awaits: ${outFile}`);
