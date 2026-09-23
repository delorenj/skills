#!/usr/bin/env bash
# Create the agent's Plane account via the authenticated Mac profile.
# Reads: EMAIL, OP_ITEM, TASK, PLANE_BASE.  Prints only status — never the password.
set -euo pipefail
: "${EMAIL:?}" "${OP_ITEM:?}" "${TASK:?}" "${PLANE_BASE:?}"

export PW="$(op read "op://DeLoSecrets/${OP_ITEM}/password")"
[[ -n "$PW" ]] || { echo "no password stored for ${OP_ITEM}" >&2; exit 1; }

# The password must ride inside the heredoc — ego lite has no env passthrough. The audit
# log records the forwarded SCRIPT verbatim, so EGO_BROWSER_REDACT masks the literal before
# it is written. Without this the password is persisted in plaintext at
# ~/.local/state/ego-browser/audit.log forever.
export EGO_BROWSER_REDACT="$PW"
OUT="$(ego-browser nodejs <<EOF 2>&1
const EMAIL = $(python3 -c 'import json,os;print(json.dumps(os.environ["EMAIL"]))');
const PW    = $(python3 -c 'import json,os;print(json.dumps(os.environ["PW"]))');
const task = await useOrCreateTaskSpace('${TASK}');
await gotoAndWait('${PLANE_BASE}/');
await new Promise(r => setTimeout(r, 4000));

// React-controlled inputs: a plain .value assignment is discarded. Use the native setter
// so React's onChange fires and its internal state actually updates.
const setVal = (sel, v) => js(\`(()=>{const i=document.querySelector(\${JSON.stringify(sel)});
  if(!i) return 'no-input'; const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  s.call(i, \${JSON.stringify(v)}); i.dispatchEvent(new Event('input',{bubbles:true})); return 'ok';})()\`);

await setVal('input[name=email]', EMAIL);
await new Promise(r => setTimeout(r, 600));
await js(\`(()=>{const b=[...document.querySelectorAll('button')].find(x=>/continue/i.test(x.innerText)); if(b){b.click();return 'ok'} return 'no-button';})()\`);
await new Promise(r => setTimeout(r, 5000));

const txt = await js('document.body.innerText.slice(0,400)');
if (/Welcome back|Enter password/i.test(txt) && !/Create your Plane account/i.test(txt)) {
  cliLog('RESULT:exists'); // account already there — sign-in branch
} else if (/Create your Plane account/i.test(txt)) {
  await setVal('input[name=password]', PW);
  await new Promise(r => setTimeout(r, 300));
  await setVal('input[name=confirm_password]', PW);
  await new Promise(r => setTimeout(r, 500));
  await js(\`(()=>{const b=[...document.querySelectorAll('button')].find(x=>/create account/i.test(x.innerText)); if(b){b.click();return 'ok'} return 'no-button';})()\`);
  await new Promise(r => setTimeout(r, 9000));
  const after = await js('location.href');
  cliLog('RESULT:created url=' + after);
} else {
  cliLog('RESULT:unknown text=' + txt.replace(/\s+/g,' ').slice(0,200));
}
EOF
)"
unset PW EGO_BROWSER_REDACT

case "$OUT" in
  *RESULT:created*) echo "  account created" >&2 ;;
  *RESULT:exists*)  echo "  account already exists — reusing" >&2 ;;
  *) echo "  signup did not reach a known state:" >&2; echo "$OUT" | tail -5 >&2; exit 1 ;;
esac
