#!/usr/bin/env bash
# Sign in AS THE AGENT, clear new-user onboarding, and mint its own Plane API token
# straight into 1Password. The token is never printed and never written to disk.
# Reads: EMAIL, OP_ITEM, TASK, PLANE_BASE, AGENT, WORKSPACE, DISPLAY_NAME.
set -euo pipefail
: "${EMAIL:?}" "${OP_ITEM:?}" "${TASK:?}" "${PLANE_BASE:?}" "${AGENT:?}"
WORKSPACE="${WORKSPACE:-33god}"

# --vault is mandatory for a service account; without it `op item get` fails with
# "a vault query must be provided", which reads as "not found" and re-mints every run.
if op item get "$OP_ITEM" --vault DeLoSecrets --fields apiKey --reveal >/dev/null 2>&1; then
  echo "  token already stored — reusing (delete the apiKey field to rotate)" >&2; exit 0
fi

# Plane rejects a profile name containing digits: "Names can only contain letters,
# spaces, hyphens, and apostrophes". Every agent id here starts with one, so strip.
NAME="${DISPLAY_NAME:-$AGENT}"
NAME="$(printf '%s' "$NAME" | tr -cd "A-Za-z '-" | tr -s ' ' | sed 's/^ *//;s/ *$//')"
[[ -n "$NAME" ]] || NAME="Agent"

export PW="$(op read "op://DeLoSecrets/${OP_ITEM}/password")"
export EGO_BROWSER_REDACT="$PW"

OUT="$(ego-browser nodejs <<EOF 2>&1
const EMAIL = $(python3 -c 'import json,os;print(json.dumps(os.environ["EMAIL"]))');
const PW    = $(python3 -c 'import json,os;print(json.dumps(os.environ["PW"]))');
const NAME  = $(python3 -c 'import json,os;print(json.dumps(os.environ["NAME"]))');
const LABEL = 'hermes-${AGENT}';
const task  = await useOrCreateTaskSpace('${TASK}');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const clickText = (re) => js(\`(()=>{const b=[...document.querySelectorAll("button,a")].find(x=>\${re}.test(x.innerText)&&!x.disabled); if(b){b.click();return "ok"} return "no";})()\`);

// ── sign in ───────────────────────────────────────────────────────────────────
await gotoAndWait('${PLANE_BASE}/');
await sleep(4000);
if (!/onboarding|\\/${WORKSPACE}\\//.test(await js('location.href'))) {
  await fillInput('input[name=email]', EMAIL);
  await sleep(700); await clickText('/continue/i'); await sleep(4500);
  await fillInput('input[name=password]', PW);
  await sleep(600); await clickText('/continue|sign in|log in/i'); await sleep(9000);
}

// ── onboarding: profile, then JOIN the invited workspace ──────────────────────
for (let i = 0; i < 6 && /onboarding/.test(await js('location.href')); i++) {
  const html = await js('document.body.innerText');
  if (/Create your profile/i.test(html)) {
    await fillInput('input[name=first_name]', NAME); await sleep(1200);
  } else if (/Join invites/i.test(html)) {
    // The invite is a real checkbox. A real .click() is what React observes;
    // assigning .checked leaves its state false and Continue stays disabled.
    await js(\`(()=>{const c=document.querySelector('input[type=checkbox]'); c&&c.click();})()\`);
    await sleep(1200);
  }
  if (await clickText('/continue|next|get started|done/i') === 'no') break;
  await sleep(7000);
}

// ── mint ──────────────────────────────────────────────────────────────────────
await gotoAndWait('${PLANE_BASE}/settings/profile/api-tokens/');
await sleep(7000);
if (!/api-tokens/.test(await js('location.href'))) {
  cliLog('RESULT:not-signed-in url=' + (await js('location.href')));
} else {
  await js(\`(()=>{const b=[...document.querySelectorAll("button")].find(x=>/add access token/i.test(x.innerText)); b&&b.click();})()\`);
  await sleep(3000);
  await fillInput('input[placeholder="Title"]', LABEL);
  await sleep(700);

  // EXPIRATION IS REQUIRED and there is no validation message: with it unset the
  // Generate button is enabled, clicks, fires NO request, and the modal just sits
  // there. This single fact cost six attempts. Set it before submitting.
  await js(\`(()=>{const b=document.querySelector("[id^=headlessui-combobox-button]"); b&&b.click();})()\`);
  await sleep(2000);
  // Click the LEAF whose whole text is the option: the listbox container's innerText
  // concatenates every option, so a text match without the leaf test hits the container.
  const picked = await js(\`(()=>{const o=[...document.querySelectorAll("*")].filter(x=>x.children.length===0&&x.innerText&&x.innerText.trim()==="1 year"); if(!o.length) return "none"; o[0].click(); return "ok";})()\`);
  await sleep(2000);
  if (picked !== 'ok') cliLog('WARN: expiration not set — generate will silently no-op');

  await js(\`(()=>{const b=[...document.querySelectorAll("button")].filter(x=>/generate token/i.test(x.innerText)).pop(); b&&b.click();})()\`);
  let tok = '';
  for (let i = 0; i < 8 && !tok; i++) {
    await sleep(3000);
    tok = await js(\`(()=>{const t=document.body.innerText; let m=t.match(/[A-Za-z0-9_]{32,}/); if(m) return m[0];
      const v=[...document.querySelectorAll("input")].map(e=>e.value||"").find(v=>v.length>=32); return v||"";})()\`);
  }
  cliLog(tok ? 'RESULT:token ' + tok : 'RESULT:no-token ' + (await js('document.body.innerText.slice(0,300)')).replace(/\\s+/g,' '));
}
EOF
)"
unset PW EGO_BROWSER_REDACT

# Print everything EXCEPT the line carrying the token.
printf '%s\n' "$OUT" | grep -v 'RESULT:token' | sed 's/^/  /' >&2

TOKEN="$(printf '%s' "$OUT" | sed -n 's/.*RESULT:token \([A-Za-z0-9_-]*\).*/\1/p' | head -1)"
[[ -n "$TOKEN" ]] || { echo "  token mint failed (see above)" >&2; exit 1; }
op item edit "$OP_ITEM" --vault DeLoSecrets "apiKey[password]=${TOKEN}" >/dev/null
unset TOKEN
echo "  token minted and stored at op://DeLoSecrets/${OP_ITEM}/apiKey" >&2
