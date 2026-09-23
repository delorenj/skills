#!/usr/bin/env bash
# Provision a full Plane identity for a Hermes agent: email -> account -> membership -> token.
# Idempotent: every step checks for its own prior result and resumes rather than duplicating.
#
#   provision-plane-identity.sh <agent-id> [--dry-run]
#
# Secrets NEVER touch disk or the audit log. Password and token go straight into 1Password;
# the agent registry receives only the op:// reference.
set -euo pipefail

AGENT="${1:?usage: provision-plane-identity.sh <agent-id> [--dry-run]}"
DRY=0; [[ "${2:-}" == "--dry-run" ]] && DRY=1

PLANE_BASE="${PLANE_BASE:-https://plane.delo.sh}"
WORKSPACE="${PLANE_WORKSPACE:-33god}"
EMAIL="${AGENT}@delo.sh"
FORWARD_TO="${AGENT_EMAIL_FORWARD_TO:-jaradd@gmail.com}"
CF_API="${CF_API:-https://api.cloudflare.com/client/v4}"
CF_ZONE="${CF_ZONE_DELO_SH:-eabc163cde3e31680f10fc313aecdda3}"
OP_ITEM="Plane Agent ${AGENT}"
TASK="plane-iam-${AGENT}"

log()  { printf '  %s\n' "$*" >&2; }
step() { printf '\n[%s] %s\n' "$1" "$2" >&2; }
die()  { printf 'FATAL: %s\n' "$*" >&2; exit 1; }
run()  { if (( DRY )); then log "DRY-RUN: would $*"; else "$@"; fi; }

command -v ego-browser >/dev/null || die "ego-browser not on PATH (the Mac bridge)"
command -v op          >/dev/null || die "1Password CLI not on PATH"

# A rate-limited vault makes every later step fail as if the credential were wrong.
op read "op://DeLoSecrets/Plane/Main/apiKey" >/dev/null 2>&1 \
  || die "1Password is unreachable or rate-limited — stop and wait it out (see SKILL.md)"
ego-browser doctor >/dev/null 2>&1 || die "ego-browser bridge is down — run 'ego-browser doctor'"

PLANE_KEY="$(op read 'op://DeLoSecrets/Plane/Main/apiKey')"

# ── 1. email ────────────────────────────────────────────────────────────────────
step 1 "Cloudflare email routing: ${EMAIL} -> ${FORWARD_TO}"
# Two credential shapes live in the vault and they authenticate DIFFERENTLY.
#   Cloudflare-EmailRouting/token  -> a scoped token, "Authorization: Bearer".
#                                     Verified 2026-09-20: it authenticates for NEITHER read nor
#                                     write on this zone (code 10000 on both list and create).
#   Cloudflare/globalAPIToken      -> a 37-char GLOBAL API KEY. Not a bearer token; it needs
#                                     X-Auth-Key + X-Auth-Email or Cloudflare 400s.
# Pick whichever actually works by PROVING a read first, then reuse that mode for the write.
CF_SCOPED="$(op read 'op://DeLoSecrets/Cloudflare-EmailRouting/token' 2>/dev/null || true)"
CF_GLOBAL="$(op read 'op://DeLoSecrets/Cloudflare/globalAPIToken' 2>/dev/null || true)"
CF_EMAIL="${CLOUDFLARE_ACCOUNT_EMAIL:-jaradd@gmail.com}"
cf_curl() {
  if [[ "${CF_MODE}" == "global" ]]; then
    curl -sS -H "X-Auth-Key: ${CF_GLOBAL}" -H "X-Auth-Email: ${CF_EMAIL}" "$@"
  else
    curl -sS -H "Authorization: Bearer ${CF_SCOPED}" "$@"
  fi
}
cf_list() { cf_curl "${CF_API}/zones/${CF_ZONE}/email/routing/rules?per_page=200"; }

# Prove the credential before trusting anything it says. A failed LIST returns no rules, which
# is indistinguishable from "no rule exists" — and that is precisely how an idempotent step
# creates a duplicate. This exact bug produced a "Duplicated Zone rule" on 2026-09-20.
CF_MODE=""; CF_RULES=""
for mode in scoped global; do
  case "$mode" in
    scoped) [[ -n "$CF_SCOPED" ]] || continue ;;
    global) [[ -n "$CF_GLOBAL" ]] || continue ;;
  esac
  CF_MODE="$mode"
  CF_RULES="$(cf_list)"
  if echo "$CF_RULES" | grep -q '"success": *true'; then
    log "cloudflare auth: ${mode}"
    break
  fi
  CF_MODE=""
done
[[ -n "$CF_MODE" ]] || die "no Cloudflare credential can read this zone (tried scoped token and global API key)"

EXISTING_RULE="$(printf '%s' "$CF_RULES" | python3 -c "
import sys,json
addr=sys.argv[1]; d=json.load(sys.stdin)
if not d.get('success'):
    sys.stderr.write('cloudflare list failed: %s\\n' % d.get('errors')); sys.exit(2)
for r in d.get('result') or []:
    for m in r.get('matchers') or []:
        if m.get('field')=='to' and m.get('value')==addr:
            print(r.get('tag') or r.get('id')); sys.exit(0)
" "$EMAIL")" || die "could not read existing email rules — refusing to risk a duplicate"

if [[ -n "$EXISTING_RULE" ]]; then
  log "rule exists (${EXISTING_RULE}) — reusing"
else
  BODY="$(python3 -c "
import json,sys
print(json.dumps({'name':f'hermes:{sys.argv[1]}','enabled':True,'priority':100,
 'matchers':[{'field':'to','type':'literal','value':sys.argv[2]}],
 'actions':[{'type':'forward','value':[sys.argv[3]]}]}))" "$AGENT" "$EMAIL" "$FORWARD_TO")"
  if (( DRY )); then log "DRY-RUN: would POST email routing rule"; else
    RESP="$(cf_curl -X POST "${CF_API}/zones/${CF_ZONE}/email/routing/rules" \
      -H 'Content-Type: application/json' -d "$BODY")"
    echo "$RESP" | grep -q '"success": *true' || die "email rule create failed: $RESP"
    log "rule created"
  fi
fi

# ── 2. password ─────────────────────────────────────────────────────────────────
step 2 "password into 1Password (never to disk)"
# --vault is MANDATORY for a service account: `op item get` without it fails with
# "a vault query must be provided when this command is called by a service account",
# which reads as "item not found" and makes this step create a duplicate every run.
if op item get "$OP_ITEM" --vault DeLoSecrets --fields password --reveal >/dev/null 2>&1; then
  log "password already stored — reusing"
else
  if (( DRY )); then log "DRY-RUN: would generate + store password"; else
    PW="$(openssl rand -base64 24 | tr -d '\n/+=' | head -c 28)Aa1!"
    op item create --category=login --title="$OP_ITEM" --vault=DeLoSecrets \
      "username=${EMAIL}" "password=${PW}" "url=${PLANE_BASE}" >/dev/null \
      || op item edit "$OP_ITEM" --vault=DeLoSecrets "password=${PW}" >/dev/null
    unset PW
    log "password generated and stored"
  fi
fi

# ── 3. account (ego-browser) ────────────────────────────────────────────────────
step 3 "create the Plane account as ${EMAIL} (ego-browser)"
if (( DRY )); then log "DRY-RUN: would sign up via ego-browser"; else
  EMAIL="$EMAIL" OP_ITEM="$OP_ITEM" TASK="$TASK" PLANE_BASE="$PLANE_BASE" \
  "$(dirname "$0")/ego-signup.sh" || die "signup step failed"
fi

# ── 4. workspace membership ─────────────────────────────────────────────────────
step 4 "add ${EMAIL} to workspace '${WORKSPACE}'"
IS_MEMBER="$(curl -sS -H "X-API-Key: ${PLANE_KEY}" \
  "${PLANE_BASE}/api/v1/workspaces/${WORKSPACE}/members/" \
  | python3 -c "
import sys,json
addr=sys.argv[1]; d=json.load(sys.stdin)
rows = d if isinstance(d,list) else d.get('results',[])
for m in rows:
    mm = m.get('member') or m
    if (mm.get('email') or '').lower()==addr.lower():
        print(mm.get('id') or ''); break
" "$EMAIL")"
if [[ -n "$IS_MEMBER" ]]; then
  log "already a member (${IS_MEMBER})"
else
  # Payload is a FLAT dict with a singular `email`. {"emails":[{...}]} is silently
  # rejected with {"email":["This field is required."]} and a 200-shaped body, so an
  # unchecked POST reports success and invites nobody. Verify the response.
  if (( DRY )); then log "DRY-RUN: would invite ${EMAIL}"; else
    INV="$(curl -sS -X POST "${PLANE_BASE}/api/v1/workspaces/${WORKSPACE}/invitations/" \
      -H "X-API-Key: ${PLANE_KEY}" -H 'Content-Type: application/json' \
      -d "{\"email\":\"${EMAIL}\",\"role\":15}")"
    if echo "$INV" | grep -q '"id"'; then
      log "invitation created"
    elif echo "$INV" | grep -qi 'already\|exists'; then
      log "invitation already exists — reusing"
    else
      die "invitation failed: $INV"
    fi
  fi
fi

# ── 5+6. mint the token (ego-browser) and store it ──────────────────────────────
step 5 "mint the agent's own API token (ego-browser) and store it"
if (( DRY )); then log "DRY-RUN: would mint + store token"; else
  EMAIL="$EMAIL" OP_ITEM="$OP_ITEM" TASK="$TASK" PLANE_BASE="$PLANE_BASE" AGENT="$AGENT" \
  "$(dirname "$0")/ego-mint-token.sh" || die "token mint failed"
fi

# ── 7. registry ─────────────────────────────────────────────────────────────────
step 7 "record the identity in the agent registry"
run flume iam record "$AGENT" \
  --email "$EMAIL" \
  --key-ref "op://DeLoSecrets/${OP_ITEM}/apiKey" \
  --member-id "${IS_MEMBER:-pending}"

printf '\n✔ %s provisioned: %s\n' "$AGENT" "$EMAIL" >&2
printf '  verify: curl -s -H "X-API-Key: $(op read %s)" %s/api/v1/users/me/ | jq -r .email\n' \
  "\"op://DeLoSecrets/${OP_ITEM}/apiKey\"" "$PLANE_BASE" >&2
