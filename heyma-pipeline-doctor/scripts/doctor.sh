#!/usr/bin/env bash
# doctor.sh — one read-only pass over every moving part of the Wax audio pipeline.
#
# Prints a layered board so a human or an agent can see, in one screen, which
# stage is broken. Every check is cheap and read-only: no writes, no restarts,
# no uploads, no transcription. Safe to run at any time, including mid-recording.
#
# The ordering is a dependency order, not a priority order. A failure in an
# early layer invalidates the checks below it, so the board marks those SKIP
# rather than reporting a cascade of derived failures as if they were causes.
#
# Exit: 0 all pass, 1 at least one FAIL, 2 the environment could not be resolved.

set -uo pipefail

# ── resolution ───────────────────────────────────────────────────────────────
# Never assume a path. The daemon's own open file descriptors are the only
# authoritative answer to "which ledger is live" — a retired ~/audio/var/wax.db
# sat on disk for three weeks looking exactly like the real thing, and it sent a
# whole investigation down the wrong hole before anyone checked /proc.

REPO_DEFAULT=/home/delorenj/HeyMa
REPO="${WAX_REPO:-$REPO_DEFAULT}"
MAIN_PID="$(systemctl --user show -p MainPID --value waxd.service 2>/dev/null)"
[ "${MAIN_PID:-0}" = "0" ] && MAIN_PID=""

resolve_root() {
  # Prefer what the running daemon actually has open; fall back to the default.
  if [ -n "$MAIN_PID" ] && [ -r "/proc/$MAIN_PID/environ" ]; then
    local o
    o="$(tr '\0' '\n' < "/proc/$MAIN_PID/environ" 2>/dev/null |
         sed -n 's/^WAX_\(ROOT\|AUDIO_ROOT\)=//p' | head -1)"
    [ -n "$o" ] && { printf '%s\n' "$o"; return; }
  fi
  printf '%s\n' "$REPO"
}

ROOT="$(resolve_root)"
VAR="$ROOT/var"
DB="$VAR/wax.db"
STATE="$VAR/state.json"
INBOX="$ROOT/inbox"
WAX="$REPO/bin/wax"
PASSES_D="$REPO/components/wax/config/passes.d"
TITLE_YAML="$PASSES_D/title-slug.yaml"
MC="$(command -v mc || echo /usr/local/bin/mc)"

# If the daemon holds a ledger somewhere other than where we computed, believe it.
if [ -n "$MAIN_PID" ]; then
  held="$(ls -l "/proc/$MAIN_PID/fd" 2>/dev/null |
          sed -n 's|.*-> \(/.*wax\.db\)$|\1|p' | head -1)"
  [ -n "${held:-}" ] && DB="$held"
fi

SQ() { sqlite3 -readonly "file:${DB}?mode=ro" "$1" 2>/dev/null; }

# JGET takes a dotted path (JGET inbox.state) rather than a Python subscript
# expression. An earlier version passed "['inbox']['state']" through the shell
# into an eval, where the nested quotes collapsed and every lookup silently
# returned the empty string — which made the tray-honesty check PASS while the
# tray was lying. A check that fails open is worse than no check.
JGET() {
  STATE_FILE="$STATE" python3 - "$1" <<'PY' 2>/dev/null
import json, os, sys
cur = json.load(open(os.environ["STATE_FILE"]))
for part in sys.argv[1].split("."):
    if not isinstance(cur, dict) or part not in cur:
        sys.exit(1)
    cur = cur[part]
print("" if cur is None else cur)
PY
}

# A column that may not exist yet in an older ledger must not blank the whole row.
SQ_COL_EXISTS() { SQ "SELECT 1 FROM pragma_table_info('$1') WHERE name='$2';"; }

yamlval() { # yamlval KEY FILE — read a scalar out of a pass yaml env: block
  sed -n "s/^ *$1: *//p" "$2" 2>/dev/null | head -1 | tr -d "\"' " | tr -d '\r'
}

# ── options ──────────────────────────────────────────────────────────────────
WANT_JSON=0; ONLY_LAYER=""; ONLY_ID=""; QUICK=0; VERBOSE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --json)    WANT_JSON=1 ;;
    --layer)   ONLY_LAYER="${2:-}"; shift ;;
    --only)    ONLY_ID="${2:-}"; shift ;;
    --quick)   QUICK=1 ;;
    --verbose|-v) VERBOSE=1 ;;
    -h|--help)
      cat <<'USAGE'
doctor.sh — read-only health board for the Wax audio pipeline

  --json           machine-readable output
  --layer <name>   run one layer only (daemon|capture|paths|queue|stages|enrichment|
                   transcription|archive|events|desktop|deploy|hygiene)
  --only <id>      run one check by id
  --quick          skip the slow checks (S3 round-trips, test suite, candystore)
  --verbose        show the evidence line for passing checks too
USAGE
      exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

if [ -t 1 ] && [ "$WANT_JSON" = 0 ]; then
  G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; B=$'\033[2m'; C=$'\033[36m'; N=$'\033[0m'
else
  G=""; R=""; Y=""; B=""; C=""; N=""
fi

PASS=0; FAIL=0; WARN=0; SKIP=0
FAILED_LAYERS=""; FAILED_IDS=""
ROWS=""      # id|layer|status|label|evidence  (newline separated)
CUR_LAYER=""
LAYER_BLOCKED=""

layer() { CUR_LAYER="$1"; }

# check ID LABEL FAIL_HINT ; the check body is the function chk_<ID_with_underscores>
check() {
  local id="$1" label="$2" hint="$3"
  [ -n "$ONLY_LAYER" ] && [ "$ONLY_LAYER" != "$CUR_LAYER" ] && return 0
  [ -n "$ONLY_ID" ] && [ "$ONLY_ID" != "$id" ] && return 0

  local fn="chk_${id//-/_}" out status
  if printf '%s\n' "$LAYER_BLOCKED" | grep -qx "$CUR_LAYER"; then
    status=skip; out="upstream layer failed — result would be meaningless"
    SKIP=$((SKIP+1))
  else
    out="$("$fn" 2>&1)"; local rc=$?
    case $rc in
      0) status=pass; PASS=$((PASS+1)) ;;
      2) status=warn; WARN=$((WARN+1)) ;;
      3) status=skip; SKIP=$((SKIP+1)) ;;
      *) status=fail; FAIL=$((FAIL+1))
         FAILED_LAYERS="$FAILED_LAYERS$CUR_LAYER"$'\n'
         FAILED_IDS="$FAILED_IDS  $id"$'\n' ;;
    esac
    [ "$status" = fail ] && [ -z "$out" ] && out="$hint"
  fi
  ROWS="$ROWS$id|$CUR_LAYER|$status|$label|${out//$'\n'/ }"$'\n'

  [ "$WANT_JSON" = 1 ] && return 0
  local mark
  case $status in
    pass) mark="${G}✔${N}" ;;
    fail) mark="${R}✘${N}" ;;
    warn) mark="${Y}▲${N}" ;;
    skip) mark="${B}○${N}" ;;
  esac
  printf '  %b %-42s' "$mark" "$label"
  if [ "$status" = fail ] || [ "$status" = warn ] || { [ "$VERBOSE" = 1 ] && [ -n "$out" ]; }; then
    printf '\n      %b%s%b\n' "$B" "${out:0:220}" "$N"
  else
    printf '\n'
  fi
}

# Mark a layer fatal: everything after it in this layer is meaningless.
block_layer() { LAYER_BLOCKED="$LAYER_BLOCKED$1"$'\n'; }

banner() { [ "$WANT_JSON" = 1 ] && return 0; printf '\n%b%s%b\n' "$C" "$1" "$N"; }

# ═════════════════════════════ CHECKS ════════════════════════════════════════

# ── daemon ───────────────────────────────────────────────────────────────────
chk_waxd_active() {
  systemctl --user is-active --quiet waxd.service && return 0
  echo "waxd.service is $(systemctl --user is-active waxd.service 2>&1). Start: systemctl --user start waxd.service"
  return 1
}
chk_wax_cli() {
  local out rc
  out="$("$WAX" state --json 2>&1)"; rc=$?
  # `wax state` deliberately exits 2 when a machine reports error. That is a
  # healthy CLI delivering bad pipeline news, not a broken executable. Parse
  # the payload here and let stream-healthy classify the state separately.
  case "$rc" in 0|2) ;; *) echo "$out" | tail -2; return 1 ;; esac
  printf '%s' "$out" | python3 -c \
    'import json,sys; s=json.load(sys.stdin); assert "stream" in s and "inbox" in s' \
    >/dev/null 2>&1 && return 0
  echo "$out" | tail -2
  return 1
}
chk_state_fresh() {
  [ -f "$STATE" ] || { echo "no state mirror at $STATE"; return 1; }
  local age=$(( $(date +%s) - $(stat -c %Y "$STATE") ))
  [ "$age" -lt 180 ] && return 0
  echo "state.json is ${age}s old (tick writes it ~1/s). waxd is wedged or blocked in ledger.enrich()."
  return 1
}
chk_waxd_rss() {
  [ -n "$MAIN_PID" ] || return 3
  local rss; rss="$(awk '/VmRSS/{print $2}' "/proc/$MAIN_PID/status" 2>/dev/null)"
  [ -z "$rss" ] && return 3
  [ "$rss" -lt 524288 ] && return 0
  # Deliberately reads /proc, not systemd's MemoryCurrent: the cgroup figure counts
  # reclaimable page cache from transcription children and reads ~4 GB while the
  # daemon's true RSS is ~53 MB. Chasing that number wastes an afternoon.
  echo "waxd RSS $((rss/1024)) MB (>512 MB). This is the process, not the cgroup — a real leak."
  return 1
}
chk_waxd_socket() {
  [ -S "$VAR/waxd.sock" ] || { echo "no socket at $VAR/waxd.sock — server thread never bound; state.json is authoritative"; return 2; }
  timeout 8 python3 - "$VAR/waxd.sock" <<'PY' >/dev/null 2>&1 || { echo "socket present but not answering with a valid snapshot"; return 2; }
import socket, json, sys
s = socket.socket(socket.AF_UNIX); s.settimeout(5); s.connect(sys.argv[1])
b = b""
while True:
    c = s.recv(65536)
    if not c: break
    b += c
sys.exit(0 if "stream" in json.loads(b) else 1)
PY
  return 0
}

# ── capture ──────────────────────────────────────────────────────────────────
chk_stream_healthy() {
  local out rc
  out="$("$WAX" state stream --cold --json 2>&1)"; rc=$?
  case "$rc" in 0|2) ;; *) echo "$out" | tail -2; return 1 ;; esac

  local fields=()
  mapfile -t fields < <(STREAM_JSON="$out" python3 - <<'PY' 2>/dev/null
import json, os
s = json.loads(os.environ["STREAM_JSON"])
for key in ("state", "clause", "cause_code", "evidence"):
    print("" if s.get(key) is None else str(s.get(key)).replace("\n", " "))
PY
  )
  [ "${#fields[@]}" -eq 4 ] || { echo "wax returned an invalid stream snapshot"; return 1; }
  local s="${fields[0]}" clause="${fields[1]}" cause="${fields[2]}" evidence="${fields[3]}"
  case "$s" in
    ready|recording) return 0 ;;
    not-ready)
      echo "stream.state=$s clause=$clause cause=$cause evidence=$evidence"
      [ "$clause" = a ] && return 2
      return 1 ;;
    *)
      echo "stream.state=$s cause=$cause evidence=$evidence"
      return 1 ;;
  esac
}

# ── paths & ledger ───────────────────────────────────────────────────────────
chk_root_consistent() {
  [ -d "$ROOT" ] || { echo "resolved root $ROOT does not exist"; return 1; }
  [ "$ROOT" = "$REPO" ] && return 0
  echo "WAX_ROOT override in effect: $ROOT (repo is $REPO). Every path below follows the override."
  return 2
}
chk_ledger_live() {
  [ -f "$DB" ] || { echo "no ledger at $DB"; return 1; }
  [ -n "$MAIN_PID" ] || return 3
  ls -l "/proc/$MAIN_PID/fd" 2>/dev/null | grep -q "$DB\$" && return 0
  # Never judge liveness by mtime: WAL mode leaves wax.db untouched for hours
  # while every write lands in wax.db-wal.
  echo "daemon does not hold $DB open. It has: $(ls -l /proc/$MAIN_PID/fd 2>/dev/null | sed -n 's|.*-> \(/.*wax\.db\)$|\1|p' | head -1)"
  return 1
}
chk_no_stale_mirror() {
  [ -e "$HOME/audio/var/state.json" ] || return 0
  echo "$HOME/audio/var/state.json exists — a retired mirror that reads exactly like a live one and is false in every field. Retire it."
  return 1
}

# ── queue & inbox ────────────────────────────────────────────────────────────
chk_scheduler_enabled() {
  [ -e "$VAR/pipeline.enabled" ] && return 0
  echo "pipeline is operator-paused; recordings accumulate untranscribed. Re-enable: wax pipeline enable"
  return 1
}
chk_inbox_not_stranded() {
  local s; s="$(JGET inbox.state)"
  case "$s" in
    error|stopped)
      echo "inbox.state=$s cause=$(JGET inbox.cause_code) evidence=$(JGET inbox.evidence)"
      return 1 ;;
    "") return 3 ;;
    *) return 0 ;;
  esac
}
chk_inbox_no_subdir_blindspot() {
  local n
  n="$(find "$INBOX" -mindepth 2 -type f -size +64k \
        \( -iname '*.ogg' -o -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.wav' \
           -o -iname '*.opus' -o -iname '*.flac' \) \
        -not -path '*/.stversions/*' -not -path '*/.stfolder/*' 2>/dev/null | wc -l)"
  [ "$n" -eq 0 ] && return 0
  echo "$n audio file(s) one level deeper than the inbox root. If state.inbox_items() is non-recursive they are invisible to the worker forever while the inbox reports 'empty'."
  return 1
}
chk_no_phantom_items() {
  local n
  n="$(SQ "SELECT path FROM items WHERE state IN ('pending','archived','transcribed');" |
       while IFS= read -r p; do [ -e "$p" ] || echo x; done | wc -l)"
  [ "${n:-0}" -eq 0 ] && return 0
  echo "$n ledger row(s) point at audio that no longer exists — they inflate items.pending forever while queue.total stays 0."
  return 2
}

# ── stage outcomes (what the product itself will not tell you) ───────────────
chk_no_recent_pass_failures() {
  local n
  n="$(SQ "SELECT COUNT(*) FROM passes WHERE state<>'completed' AND updated_at > strftime('%Y-%m-%dT%H:%M:%SZ','now','-7 days');")"
  [ "${n:-0}" -eq 0 ] && return 0
  local expr="ep_slug"
  [ -n "$(SQ_COL_EXISTS passes reason_code)" ] && expr="ep_slug||'('||COALESCE(reason_code,'?')||')'"
  local why
  why="$(SQ "SELECT DISTINCT $expr FROM passes WHERE state<>'completed' AND updated_at > strftime('%Y-%m-%dT%H:%M:%SZ','now','-7 days');" | tr '\n' ' ')"
  [ -n "$why" ] || why="$(SQ "SELECT DISTINCT ep_slug FROM passes WHERE state<>'completed';" | tr '\n' ' ')"
  echo "$n failed pass row(s) in 7d: ${why:-unknown}. Detail: $(SQ "SELECT detail FROM passes WHERE state<>'completed' ORDER BY updated_at DESC LIMIT 1;" | head -c 120)"
  return 1
}
chk_recent_titles_slugged() {
  local n
  n="$(SQ "SELECT COUNT(*) FROM (SELECT item_id FROM transcripts ORDER BY created_at DESC LIMIT 10) t
           WHERE NOT EXISTS(SELECT 1 FROM passes p WHERE p.item_id=t.item_id AND p.ep_slug='title-slug' AND p.state='completed');")"
  [ "${n:-0}" -eq 0 ] && return 0
  echo "$n of the 10 newest transcripts have no completed title-slug — they keep bare timestamp filenames and have no title, summary, or vault taxonomy."
  return 1
}
chk_recent_diarized() {
  local n
  n="$(SQ "SELECT COUNT(*) FROM (SELECT diarized FROM transcripts ORDER BY created_at DESC LIMIT 5) WHERE diarized IS NOT 1;")"
  [ "${n:-0}" -eq 0 ] && return 0
  echo "$n of the last 5 transcripts are not diarized. Nothing else reports this — sanity.py never inspects diarized."
  return 1
}
chk_no_diarization_error_in_log() {
  local L; L="$(ls -t "$VAR"/logs/*/transcription.*.log 2>/dev/null | head -1)"
  [ -n "$L" ] || return 3
  local pattern='Missing dependency for diarization|Diarization device preflight failed|Failed to load diarization model|Diarization failed|DIARIZATION-DEGRADED'
  grep -Eq "$pattern" "$L" || return 0
  echo "$(grep -Em1 "$pattern" "$L")  [$L]"
  return 1
}
chk_tray_colour_honest() {
  local c f d
  c="$(JGET tray.colour)"
  f="$(SQ "SELECT COUNT(*) FROM passes WHERE state<>'completed' AND updated_at > strftime('%Y-%m-%dT%H:%M:%SZ','now','-7 days');")"
  d="$(SQ "SELECT COUNT(*) FROM (SELECT diarized FROM transcripts ORDER BY created_at DESC LIMIT 5) WHERE diarized IS NOT 1;")"
  [ "$c" != "green" ] && return 0
  [ "${f:-0}" -eq 0 ] && [ "${d:-0}" -eq 0 ] && return 0
  # This is the observability defect itself, not a symptom of one.
  echo "tray is GREEN while ${f:-0} pass failures and ${d:-0} undiarized transcripts exist. The icon is lying."
  return 1
}

# ── enrichment dependencies ──────────────────────────────────────────────────
title_base() {
  local b; b="$(yamlval WAX_TITLE_API_BASE "$TITLE_YAML")"
  [ -n "$b" ] || { b="$(yamlval WAX_OLLAMA_URL "$TITLE_YAML")"; [ -n "$b" ] && b="$b/v1"; }
  printf '%s\n' "$b"
}
chk_ep_registry_correct() {
  "$WAX" ep list --json 2>/dev/null | grep -q 'title-slug' && return 0
  echo "the runner's registry does not contain title-slug — it is reading the wrong passes.d. Check WAX_PASSES_DIR and component.ROOT."
  return 1
}
chk_ep_scripts_executable() {
  python3 - "$REPO" <<'PY' || return 1
import os, sys
sys.path.insert(0, sys.argv[1] + "/components/wax/src")
from wax import passes, component
bad = []
for slug, e in passes.registry().items():
    if not e.get("enabled"):
        continue
    cmd = (e.get("command") or [""])[0]
    p = str(cmd).replace("{component_root}", str(component.ROOT))
    if not os.access(p, os.X_OK):
        bad.append(f"{slug} -> {p}")
if bad:
    print("not executable: " + "; ".join(bad))
    sys.exit(1)
PY
  return 0
}
chk_title_provider_reachable() {
  local b; b="$(title_base)"
  [ -n "$b" ] || { echo "no provider base URL in $TITLE_YAML"; return 1; }
  curl -sf -m 8 "$b/models" >/dev/null 2>&1 && return 0
  # A provider that does not expose /models is not necessarily broken.
  curl -s -o /dev/null -m 8 "$b/models" -w '%{http_code}' 2>/dev/null | grep -qE '^(401|403)$' && {
    echo "$b/models answered but rejected the request — auth problem, not reachability"; return 1; }
  echo "cannot reach $b/models"
  return 1
}
chk_title_model_present() {
  local b m; b="$(title_base)"; m="$(yamlval WAX_TITLE_MODEL "$TITLE_YAML")"
  [ -n "$m" ] || { echo "no WAX_TITLE_MODEL pinned in $TITLE_YAML"; return 1; }
  curl -sf -m 10 "$b/models" 2>/dev/null |
    python3 -c "import sys,json;d=json.load(sys.stdin);ids={x.get('id') for x in (d.get('data') or d.get('models') or [])};sys.exit(0 if '$m' in ids else 1)" && return 0
  echo "pinned model '$m' is not offered by $b. Every title-slug run will fail instantly. Repin WAX_TITLE_MODEL in $TITLE_YAML."
  return 1
}
chk_title_api_key() {
  local ref; ref="$(yamlval WAX_TITLE_API_KEY_OP "$TITLE_YAML")"
  [ -n "$ref" ] || return 3
  timeout 12 op read "$ref" >/dev/null 2>&1 && return 0
  local fb; fb="$(yamlval WAX_TITLE_API_KEY_OP_FALLBACK "$TITLE_YAML")"
  if [ -n "$fb" ] && timeout 12 op read "$fb" >/dev/null 2>&1; then
    echo "the dedicated key at $ref does not exist; Wax is riding the shared key at $fb, which will break without warning when that one is rotated."
    return 2
  fi
  echo "no API key resolvable from $ref (nor the fallback). op auth: $(op whoami >/dev/null 2>&1 && echo ok || echo BROKEN)"
  return 1
}
chk_frontmatters_editor() {
  python3 - "$REPO" <<'PY' >/dev/null 2>&1 || { echo "the frontmatters editor the runner shells out to is not resolvable — every pass returning frontmatter fails at the apply step"; return 1; }
import sys
sys.path.insert(0, sys.argv[1] + "/components/wax/src")
from wax import passes
passes._frontmatters_command()
PY
  return 0
}

# ── transcription dependencies ───────────────────────────────────────────────
resolved_transcribe() { readlink -f "$(command -v transcribe 2>/dev/null || echo /nonexistent)"; }
chk_same_checkout() {
  local w t; w="$(dirname "$(dirname "$(readlink -f "$REPO/bin/waxd")")")"
  t="$(resolved_transcribe)"; [ -e "$t" ] || { echo "no 'transcribe' on PATH"; return 1; }
  t="$(dirname "$(dirname "$t")")"
  [ "$w" = "$t" ] && return 0
  # This split is what let a `git reset --hard` in one tree silently disable
  # diarization for the tree everyone was editing, for seven days.
  echo "daemon runs from $w but transcribe resolves to $t — two checkouts. Pin WAX_TRANSCRIBE in waxd.service."
  return 1
}
chk_diarization_imports() {
  local t d r; t="$(resolved_transcribe)"; [ -e "$t" ] || return 3
  r="$(dirname "$(dirname "$t")")"
  d="$r/.venv-diarization/bin/python"
  [ -x "$d" ] || { echo "no diarization venv at $d — repair with: mise run wax:diarization:install"; return 1; }
  PYTHONPATH="$r/components/wax/src" "$d" -c \
    'import librosa, nemo, torch, wax.diarization_sortformer' >/dev/null 2>&1 && return 0
  return 1
}
chk_diarization_device() {
  local value=""
  if [ -n "$MAIN_PID" ] && [ -r "/proc/$MAIN_PID/environ" ]; then
    value="$(tr '\0' '\n' < "/proc/$MAIN_PID/environ" 2>/dev/null |
             sed -n 's/^WAX_DIARIZATION_DEVICE=//p' | head -1)"
  fi
  value="${value:-cuda}"
  case "$value" in
    cuda) return 0 ;;
    cpu|auto)
      echo "WAX_DIARIZATION_DEVICE=$value permits CPU; production default is strict cuda"
      return 2 ;;
    *)
      echo "invalid WAX_DIARIZATION_DEVICE=$value (expected cuda, cpu, or auto)"
      return 1 ;;
  esac
}
chk_diarization_cuda() {
  local t d r out
  t="$(resolved_transcribe)"; [ -e "$t" ] || return 3
  r="$(dirname "$(dirname "$t")")"
  d="$r/.venv-diarization/bin/python"
  [ -x "$d" ] || return 3
  out="$(PYTHONPATH="$r/components/wax/src" timeout 120 "$d" -c \
    'import json; from wax.diarization_sortformer import cuda_smoke; print(json.dumps(cuda_smoke(), sort_keys=True))' 2>&1)" && {
      printf '%s\n' "$out" | tail -1
      return 0
    }
  printf '%s\n' "$out" | tail -3
  return 1
}
chk_sortformer_weights() {
  [ -d "$HOME/.cache/huggingface/hub/models--nvidia--diar_streaming_sortformer_4spk-v2" ] && return 0
  echo "Sortformer checkpoint not cached; the next job attempts a ~450 MB download and returns [] if offline"
  return 2
}

# ── archive ──────────────────────────────────────────────────────────────────
chk_s3_reachable() {
  [ "$QUICK" = 1 ] && return 3
  "$MC" ready delo >/dev/null 2>&1 && return 0
  echo "MinIO alias 'delo' not ready. Nothing can be archived; new recordings stash into recovered/unbacked."
  return 1
}
chk_s3_no_unbacked_audio() {
  [ "$QUICK" = 1 ] && return 3
  local out
  out="$(SQ "SELECT i.path FROM items i LEFT JOIN backups b ON b.item_id=i.item_id AND b.verified_at IS NOT NULL
             WHERE b.item_id IS NULL AND i.state NOT IN ('complete','skipped');" |
         while IFS= read -r p; do [ -f "$p" ] && echo "$p"; done)"
  [ -z "$out" ] && return 0
  # The one true emergency: irreplaceable audio with no verified copy.
  echo "UNBACKED AUDIO: $(printf '%s' "$out" | wc -l) file(s). Do not move or delete them. $(printf '%s' "$out" | head -3 | tr '\n' ' ')"
  return 1
}
chk_s3_free_space() {
  [ "$QUICK" = 1 ] && return 3
  "$MC" admin info --json delo 2>/dev/null |
    python3 -c 'import sys,json
d=json.load(sys.stdin)
a=min(x["availspace"] for s in d["info"]["servers"] for x in s["drives"])
print(f"{a/1e9:.0f} GB free")
sys.exit(0 if a>=100e9 else 1)' && return 0
  echo "MinIO below the 100 GB floor. When it fills, every new item halts at state 'failed' — safe but stopped, and nothing on screen says so."
  return 2
}
chk_s3_transcript_linked() {
  [ "$QUICK" = 1 ] && return 3
  local k; k="$(SQ "SELECT s3_key FROM backups ORDER BY verified_at DESC LIMIT 1")"
  [ -n "$k" ] || return 3
  "$MC" cat "delo/recordings/$k.wax.json" 2>/dev/null | grep -q '"transcript"' && return 0
  echo "newest object's sidecar has no transcript projection — archive.link_transcript is not running, so 'which audio has no transcript?' is unanswerable from S3 alone."
  return 2
}

# ── events ───────────────────────────────────────────────────────────────────
chk_nats_reachable() {
  timeout 6 python3 -c "import socket,sys
s=socket.create_connection(('127.0.0.1',4222),timeout=4)
sys.exit(0 if s.recv(4096).startswith(b'INFO') else 1)" 2>/dev/null && return 0
  echo "NATS down. Publishing is fail-open so recording still works, but events queue in the outbox."
  return 2
}
chk_outbox_draining() {
  local n
  n="$(SQ "SELECT COUNT(*) FROM outbox WHERE published_at IS NULL AND created_at < strftime('%Y-%m-%dT%H:%M:%SZ','now','-10 minutes');")"
  [ "${n:-0}" -eq 0 ] && return 0
  # waxd drains every 10 s, so a transient non-zero backlog is normal; only the
  # 10-minute-old rows mean the drain itself has stopped.
  echo "$n outbox row(s) unpublished for >10 min. Oldest subject: $(SQ "SELECT subject FROM outbox WHERE published_at IS NULL ORDER BY created_at LIMIT 1")"
  return 1
}

# ── desktop ──────────────────────────────────────────────────────────────────
chk_tray_registered() {
  timeout 8 gdbus call --session --dest org.kde.StatusNotifierWatcher \
    --object-path /StatusNotifierWatcher \
    --method org.freedesktop.DBus.Properties.Get \
    org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems 2>/dev/null |
    grep -q 'wax' && return 0
  echo "no wax item on the StatusNotifierWatcher bus — usually a locked screen (GNOME drops the watcher; tray.py rebuilds on return)."
  return 2
}
chk_tray_icons_present() {
  local c
  for c in green red yellow; do
    [ -s "$REPO/components/wax/assets/tray/wax-tray-icon-$c.png" ] || {
      echo "missing icon asset: wax-tray-icon-$c.png — set_icon_full fails per-colour and the handler silently clears registered"; return 1; }
  done
  return 0
}
chk_hotkey_dispatcher() {
  local unit="org.gnome.SettingsDaemon.MediaKeys.service"
  if systemctl --user is-active --quiet "$unit" &&
     busctl --user list --no-legend 2>/dev/null |
       awk '$1 == "org.gnome.SettingsDaemon.MediaKeys" { found=1 } END { exit !found }'; then
    return 0
  fi
  echo "GNOME MediaKeys has no live dispatcher even though its target may still say active. Configured shortcuts cannot fire. Restore: systemctl --user restart org.gnome.SettingsDaemon.MediaKeys.target"
  return 1
}
chk_hotkey_bound() {
  timeout 8 python3 <<'PY' 2>/dev/null && return 0
import os, shlex, subprocess, sys
b = "org.gnome.settings-daemon.plugins.media-keys"
p = subprocess.run(["gsettings","get",b,"custom-keybindings"],capture_output=True,text=True).stdout
g = lambda s,k: subprocess.run(["gsettings","get",f"{b}.custom-keybinding:{s}",k],
                               capture_output=True,text=True).stdout.strip().strip("'")
paths = [y.strip().strip("'") for y in p.replace("[","").replace("]","").split(",") if y.strip()]

def invokes_wax_toggle(command):
    try:
        argv = shlex.split(command)
    except ValueError:
        return False
    if not argv:
        return False
    executable = os.path.basename(argv[0])
    return ((executable == "wax-toggle" and len(argv) == 1) or
            (executable == "wax" and argv[1:] == ["rec", "toggle"]))

sys.exit(0 if any(invokes_wax_toggle(g(x,"command")) and g(x,"binding")
                  for x in paths) else 1)
PY
  # There is no evdev fallback: wax/hotkey.py does not exist despite the design doc.
  echo "no enabled GNOME keybinding invokes wax-toggle or 'wax rec toggle', and there is no evdev listener to fall back on. Recording becomes tray-menu / CLI only."
  return 2
}

# ── deploy & tests ───────────────────────────────────────────────────────────
chk_unit_matches_repo() {
  local tpl="$REPO/components/wax/deploy/systemd/user/waxd.service"
  local inst="$HOME/.config/systemd/user/waxd.service"
  [ -f "$tpl" ] && [ -f "$inst" ] || return 3
  # Compare only what systemd acts on — comments drift constantly and that is
  # not drift worth alarming on. The template carries @WAX_*@ tokens that
  # install-systemd-user renders, so RENDER them here rather than dropping
  # those lines: dropping them hid exactly the two directives (ExecStart and
  # WAX_TRANSCRIBE) that matter most, and made the check report them as
  # installed-only noise. (--dry-run cannot be diffed against one file either:
  # it emits waxd.service and wax-alert.service concatenated.)
  local norm='s/^[[:space:]]*//; s/[[:space:]]*$//; s/="/=/; s/"$//'
  local keep='^(ExecStart|Environment|Type|Restart|RestartSec|KillMode|TimeoutStopSec|OnFailure|WantedBy|After|PartOf)='
  local a b
  a="$(sed -e "s|@WAX_EXEC_START@|\"$REPO/bin/waxd\"|" \
           -e "s|@WAX_TRANSCRIBE_ENV@|\"WAX_TRANSCRIBE=$REPO/bin/transcribe\"|" \
           -e "/@WAX_DOCUMENTATION_URI@/d" "$tpl" |
        grep -E "$keep" | sed "$norm" | sort)"
  b="$(grep -E "$keep" "$inst" | sed "$norm" | sort)"
  [ "$a" = "$b" ] && return 0
  echo "installed waxd.service differs on: $(diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | grep -E '^[<>]' | tr '\n' ' ' | head -c 170). Reinstall: components/wax/deploy/install-systemd-user && systemctl --user daemon-reload"
  return 2
}
chk_alert_unit_shipped() {
  [ -f "$REPO/components/wax/deploy/systemd/user/wax-alert.service" ] && return 0
  echo "waxd.service declares OnFailure=wax-alert.service but deploy/ does not ship it — a fresh install has no crash-alert path."
  return 2
}
chk_capture_guard_active() {
  local unit=wax-capture-guard.service
  [ -f "$REPO/components/wax/deploy/systemd/user/$unit" ] || {
    echo "$unit is missing from deploy/; a graphical-session restart can strand a live recording."
    return 1
  }
  systemctl --user is-enabled --quiet "$unit" || {
    echo "$unit is not enabled. Reinstall Wax's user units, then enable it."
    return 1
  }
  systemctl --user is-active --quiet "$unit" || {
    echo "$unit is not active. Start it before the next logout or reboot."
    return 1
  }
  local installed
  installed="$(systemctl --user cat "$unit" 2>/dev/null)"
  printf '%s' "$installed" | grep -Fq "$REPO/bin/wax" &&
    printf '%s' "$installed" | grep -Fq 'rec quiesce' && return 0
  echo "$unit does not invoke this checkout's `wax rec quiesce`. Reinstall Wax's user units."
  return 1
}
chk_tests_pass() {
  [ "$QUICK" = 1 ] && return 3
  ( cd "$REPO/components/wax" && PYTHONPATH="$REPO/components/wax/src" \
      python3 -m pytest tests -q -p no:cacheprovider >/dev/null 2>&1 ) && return 0
  echo "test suite failing — re-run without redirection: cd $REPO/components/wax && python3 -m pytest tests -q"
  return 1
}

# ── repo hygiene (traps that have already cost debugging time) ───────────────
chk_no_root_passes_d() {
  [ -e "$REPO/passes.d" ] || return 0
  echo "$REPO/passes.d exists but is never loaded — a decoy registry. Editing it changes nothing."
  return 2
}
chk_no_stale_design_doc() {
  [ -e "$REPO/WAX-DESIGN.md" ] || return 0
  grep -q '/home/delorenj/audio/' "$REPO/WAX-DESIGN.md" 2>/dev/null || return 0
  echo "repo-root WAX-DESIGN.md still names the retired ~/audio layout. Canonical copy is components/wax/docs/WAX-DESIGN.md."
  return 2
}
chk_agents_md_current() {
  local f="$REPO/AGENTS.md"
  [ -f "$f" ] || { echo "no AGENTS.md"; return 2; }
  grep -qi 'waxd' "$f" && return 0
  echo "AGENTS.md never mentions waxd — it does not describe the running system, and it is loaded into every agent's context in this repo."
  return 2
  # Deliberately NOT grepping for retired names (n8n, Fireflies, watch_audio.sh):
  # a CORRECT AGENTS.md names them precisely to say they are retired, and two
  # earlier versions of this check flagged that negation as staleness. grep
  # cannot tell an assertion from its negation, so it must not pretend to.
  # Staleness of prose is a review job, not a check.
}
chk_legacy_dirs_quiet() {
  [ -d "$HOME/audio/inbox" ] || return 0
  local n; n="$(find "$HOME/audio/inbox" -maxdepth 1 -type f -newermt '-1 day' 2>/dev/null | wc -l)"
  [ "${n:-0}" -eq 0 ] && return 0
  echo "$n new file(s) in the legacy ~/audio/inbox that n8n may still watch — risks an out-of-band transcribe with no ledger row and a duplicate S3 object."
  return 1
}

# ═════════════════════════════ RUN ═══════════════════════════════════════════

if [ "$WANT_JSON" = 0 ]; then
  printf '\n%bWax pipeline doctor%b   root=%s\n' "$C" "$N" "$ROOT"
  printf '%bledger=%s  daemon=%s%b\n' "$B" "$DB" "${MAIN_PID:-not running}" "$N"
fi

banner "Daemon"
layer daemon
check waxd-active        "waxd.service is running"              "daemon down"
check wax-cli            "wax CLI answers from disk"            "CLI broken"
# Everything below reads state the daemon maintains. If it is down, say so once.
if ! systemctl --user is-active --quiet waxd.service; then block_layer queue; block_layer stages; fi
check state-fresh        "state mirror written within 180s"     "tick stopped"
check waxd-socket        "status socket answers"                "socket thread dead"
check waxd-rss           "daemon RSS under 512 MB"              "leak"

banner "Capture"
layer capture
check stream-healthy     "stream is recordable or recording"    "capture stranded"

banner "Paths & ledger"
layer paths
check root-consistent    "root resolves to the repo"            "override in effect"
check ledger-live        "daemon holds the live ledger open"    "wrong database"
check no-stale-mirror    "no retired ~/audio/var mirror"        "decoy mirror"

banner "Queue & inbox"
layer queue
check scheduler-enabled  "inbox scheduler enabled"              "operator-paused"
check inbox-not-stranded "inbox machine not error/stopped"      "stranded work"
check inbox-no-subdir-blindspot "no audio hidden in subdirs"    "invisible backlog"
check no-phantom-items   "every actionable item's audio exists" "phantom rows"

banner "Stage outcomes — what the product itself will not tell you"
layer stages
check no-recent-pass-failures   "no enrichment pass failed in 7d"      "passes burning"
check recent-titles-slugged     "10 newest transcripts are titled"     "no titles"
check recent-diarized           "5 newest transcripts are diarized"    "no speakers"
check no-diarization-error-in-log "newest log free of diarization error" "import failed"
check tray-colour-honest        "tray colour matches reality"          "the icon is lying"

banner "Enrichment dependencies"
layer enrichment
check ep-registry-correct    "registry loads the component passes.d"  "wrong registry"
check ep-scripts-executable  "every enabled pass script is runnable"  "missing script"
check title-provider-reachable "title provider API reachable"         "provider down"
check title-model-present    "pinned title model is offered"          "model missing"
check title-api-key          "title provider key resolves from 1Password" "no key"
check frontmatters-editor    "frontmatters editor resolvable"         "apply step will fail"

banner "Transcription dependencies"
layer transcription
check same-checkout       "daemon and transcriber share a checkout"  "two checkouts"
check diarization-imports "tracked diarizer and runtime import"      "diarization dead"
check diarization-device  "diarization policy requires CUDA"         "CPU selected"
check diarization-cuda    "Sortformer executes a CUDA forward pass"   "CUDA path broken"
check sortformer-weights  "Sortformer checkpoint cached"             "will download"

banner "Archive"
layer archive
check s3-reachable          "MinIO alias reachable"                 "archive down"
check s3-no-unbacked-audio  "no unbacked audio on disk"             "EMERGENCY"
check s3-free-space         "MinIO above the 100 GB floor"          "filling up"
check s3-transcript-linked  "newest object linked to its transcript" "linkage off"

banner "Events"
layer events
check nats-reachable   "NATS reachable"              "bus down"
check outbox-draining  "outbox draining"             "events stuck"

banner "Desktop"
layer desktop
check tray-registered    "tray registered on the SNI bus"  "no icon"
check tray-icons-present "all three icon assets present"   "missing asset"
check hotkey-dispatcher  "GNOME hotkey dispatcher running" "shortcuts inert"
check hotkey-bound       "record hotkey bound"             "no hotkey"

banner "Deploy & tests"
layer deploy
check unit-matches-repo   "installed unit matches the repo"  "deploy drift"
check alert-unit-shipped  "wax-alert.service is in deploy/"  "unshipped unit"
check capture-guard-active "session-shutdown capture guard active" "recording can strand"
check tests-pass          "component test suite passes"      "regression"

banner "Repo hygiene"
layer hygiene
check no-root-passes-d     "no decoy passes.d at the repo root"  "decoy"
check no-stale-design-doc  "no stale root design doc"            "stale doc"
check agents-md-current    "AGENTS.md describes Wax"             "stale context"
check legacy-dirs-quiet    "legacy ~/audio/inbox is quiet"       "double-transcribe risk"

# ── report ───────────────────────────────────────────────────────────────────
if [ "$WANT_JSON" = 1 ]; then
  printf '%s' "$ROWS" | python3 -c '
import sys, json
rows = []
for line in sys.stdin.read().splitlines():
    if not line.strip():
        continue
    p = line.split("|", 4)
    if len(p) == 5:
        rows.append(dict(zip(("id","layer","status","label","evidence"), p)))
print(json.dumps({
  "summary": {s: sum(1 for r in rows if r["status"] == s) for s in ("pass","fail","warn","skip")},
  "failed":  [r["id"] for r in rows if r["status"] == "fail"],
  "checks":  rows,
}, indent=1))'
else
  printf '\n%b── %d passed  %d failed  %d warned  %d skipped ──%b\n' \
    "$C" "$PASS" "$FAIL" "$WARN" "$SKIP" "$N"
  if [ "$FAIL" -gt 0 ]; then
    printf '\n%bFailing:%b\n%s' "$R" "$N" "$FAILED_IDS"
    printf '\n%bNext:%b load the playbook for the first failing layer:\n' "$C" "$N"
    printf '%s' "$FAILED_LAYERS" | grep -v '^$' | head -1 | while read -r l; do
      case "$l" in
        daemon|paths)   echo "  references/control-plane.md" ;;
        capture)        echo "  references/capture-ingest.md" ;;
        queue)          echo "  references/capture-ingest.md" ;;
        stages)         echo "  references/enrichment.md  (and transcription.md if diarization is red)" ;;
        enrichment)     echo "  references/enrichment.md" ;;
        transcription)  echo "  references/transcription.md" ;;
        archive)        echo "  references/archive.md" ;;
        events)         echo "  references/events.md" ;;
        desktop|deploy) echo "  references/control-plane.md" ;;
        hygiene)        echo "  references/control-plane.md" ;;
      esac
    done
  fi
fi

[ "$FAIL" -gt 0 ] && exit 1
exit 0
