#!/usr/bin/env bash
# The unattended entry point: one project, every configured audience, internal
# first. `activity-report run` execs this file; its Candybar candybar runs that.
#
# Per audience, in order:
#
#   collect   deterministic. Candystore + git + board + Hindsight into one digest.
#   compose   a headless agent reads the digest and follows the activity-report
#             skill to write ONE raw.txt. Prose needs judgment, so this stage
#             cannot be a shell script.
#   lint      refuse the text before anything downstream sees it.
#   render    raw.txt -> markdown + one self-contained html document.
#   assemble  digest + bodies -> the event data object, contract-checked.
#   emit      bb-emit --check, then --strict publish.
#   verify    read the event back out of Candystore, independently of what the
#             emitter or the agent believes.
#   portal    the client-portal row (external => visible to the client).
#   retain    the raw report into the project's Hindsight bank.
#   copy      the html into the repo's durable dir, if configured.
#
# Verify is not paranoia. The standing failure mode of every publisher on this
# machine is stopping while everything downstream keeps looking healthy: the
# portal simply keeps showing an older update and nobody notices for a week.
# A run reports success only after the projection has the event.
#
# The compose stage gets a deliberately narrow tool grant: files, the lint,
# and read-only git. It is not bypassPermissions. An agent running unattended
# at 03:00 with nobody watching should be able to do this job and nothing
# else; if it ever needs a tool outside that list, the right outcome is a
# loud failure in the log, not an improvised action. Never widen the grant.
#
# Exit codes: 0 done (an audience with nothing to do counts as done), 2 config
# or compose failure, 3 lint, contract or verify refused, 5 another run holds
# the lock. The overall code is the worst per-audience code.
#
# Usage:
#   scripts/run.sh --project SLUG [--audience A]... [--dry-run] [--since T] [--until T] [--force]
#   ACTIVITY_REPORT_DRY=1 scripts/run.sh --project SLUG     # same as --dry-run
#
# --dry-run still emits the event, with generator.dry_run=true, so a parallel
# night shows up in Candystore; it writes no portal row, retains nothing and
# copies nothing into the repo.

set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
skill_dir="$(cd -- "$script_dir/.." && pwd -P)"
cli="$script_dir/activity-report"
templates_dir="$skill_dir/templates"

log() { printf '%s  %s\n' "$(date -u +%FT%TZ)" "$*"; }
usage() { sed -n 's/^# \{0,1\}//; /^Usage:/,/^$/p' "$0"; }

project=""; dry_run=0; since=""; until_=""; force=0
audiences=()
while [ $# -gt 0 ]; do
  case "$1" in
    --project)    [ $# -ge 2 ] || { echo "run.sh: --project needs a value" >&2; exit 2; }; project="$2"; shift 2 ;;
    --project=*)  project="${1#*=}"; shift ;;
    --audience)   [ $# -ge 2 ] || { echo "run.sh: --audience needs a value" >&2; exit 2; }; audiences+=("$2"); shift 2 ;;
    --audience=*) audiences+=("${1#*=}"); shift ;;
    --dry-run)    dry_run=1; shift ;;
    --since)      [ $# -ge 2 ] || { echo "run.sh: --since needs a value" >&2; exit 2; }; since="$2"; shift 2 ;;
    --since=*)    since="${1#*=}"; shift ;;
    --until)      [ $# -ge 2 ] || { echo "run.sh: --until needs a value" >&2; exit 2; }; until_="$2"; shift 2 ;;
    --until=*)    until_="${1#*=}"; shift ;;
    --force)      force=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    *) echo "run.sh: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
if [ -n "${ACTIVITY_REPORT_DRY:-}" ]; then dry_run=1; fi

# cron and systemd start with almost no PATH, and mise shims are how every
# other tool in this repo is reached.
export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# A stale key in the environment does not expire -- it authenticates as the
# wrong account, which is worse. Same rule as every other script here.
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN

# The compose stage reaches a model the way every agent on a 33GOD host does:
# through that host's AutomaticAI gateway. There is no claude.ai login to fall back
# on. Which gateway, which route and which token belong to the HOST, so none of them
# is in this file: they come from the environment or ~/.config/33god/host.env
# (`activity-report host-config` reads them; hostenv.py is the one parser):
#
#   ACTIVITY_REPORT_GATEWAY_URL        the gateway base URL
#   ACTIVITY_REPORT_GATEWAY_ROUTE      the default route (a project's compose.model replaces it)
#   ACTIVITY_REPORT_GATEWAY_TOKEN_REF  op://... or env:NAME for this job's own token
#   SECRET_RESOLVER                    auto (default) | op | interim -- how the ref resolves
#
# The token is read once per run into this process and never written anywhere.
# ANTHROPIC_API_KEY is cleared because an interactive shell may hold another vendor's
# key in it (Kimi Code reuses Anthropic's variable names), and an API key or OAuth
# token would outrank the gateway token. Every model slot is pinned to one route, so
# no helper lands on another account; left alone, the CLI takes its model from
# ~/.claude/settings.json. The token's scope must include the route.
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL CLAUDE_CODE_OAUTH_TOKEN

trap 'log "run.sh: unexpected error at line $LINENO (exit $?)"' ERR

# The compose stage's tool grant is Bash(activity-report lint:*), which only
# works if the shim is on PATH. Fail before spending a compose on it.
if ! command -v activity-report >/dev/null 2>&1; then
  log "FATAL: activity-report is not on PATH; run \`$cli init\` to install the ~/.local/bin shim"
  exit 2
fi

# -- resolve the project -------------------------------------------------------
resolve_args=()
if [ -n "$project" ]; then resolve_args=(--project "$project"); fi
if ! config_json="$("$cli" resolve ${resolve_args[@]+"${resolve_args[@]}"} --json)"; then
  log "FATAL: could not resolve the project${project:+ $project}"
  exit 2
fi
# One JSON parse, exported as shell-quoted assignments. No jq on this path.
eval "$(python3 -c '
import json, shlex, sys
p = json.load(sys.stdin)["project"]
c = p["config"]
def put(name, value):
    if isinstance(value, bool):
        value = "1" if value else ""
    print(f"{name}={shlex.quote(str(value) if value is not None else str())}")
put("slug", p["slug"])
put("name", p["name"])
put("repo_path", p["repo_path"])
put("tz", p["timezone"])
put("config_audiences", " ".join(c["audiences"]))
put("model", (c.get("compose") or {}).get("model"))
put("timeout_minutes", int((c.get("compose") or {}).get("timeout_minutes") or 30))
put("runtime_dir", c["output"]["runtime_dir"])
put("durable_html_dir", (c.get("output") or {}).get("durable_html_dir"))
put("portal_configured", bool(c.get("portal")))
put("retain", (c.get("hindsight") or {}).get("retain", True))
' <<<"$config_json")"

# This host's gateway. Fail before any collect when the host has not declared one.
if ! host_json="$("$cli" host-config --json)"; then
  log "FATAL: could not read the host overlay (activity-report host-config)"
  exit 2
fi
eval "$(python3 -c '
import json, shlex, sys
h = json.load(sys.stdin)
for name in ("gateway_url", "gateway_route", "gateway_token_ref", "host_env"):
    print(f"{name}={shlex.quote(str(h.get(name) or str()))}")
' <<<"$host_json")"
missing=""
[ -n "$gateway_url" ] || missing="$missing ACTIVITY_REPORT_GATEWAY_URL"
[ -n "$gateway_route" ] || [ -n "$model" ] || missing="$missing ACTIVITY_REPORT_GATEWAY_ROUTE"
[ -n "$gateway_token_ref" ] || missing="$missing ACTIVITY_REPORT_GATEWAY_TOKEN_REF"
if [ -n "$missing" ]; then
  log "FATAL: this host has no compose gateway; set${missing} in the environment or $host_env"
  exit 2
fi

if [ ${#audiences[@]} -eq 0 ]; then read -r -a audiences <<<"$config_audiences"; fi
for a in "${audiences[@]}"; do
  case "$a" in
    internal|external) ;;
    *) log "FATAL: audience must be internal or external, got '$a'"; exit 2 ;;
  esac
done

run_id="$(python3 -c 'import uuid; print(uuid.uuid4())')"
# Provisional label: the window end in the project zone. Collect decides the
# real window; its digest carries the label the run's files are named by.
# Computed in Python, with the same parser collect uses for --until: BSD date has
# no `-d`, and a label this script and the digest disagree on renames the run's files.
if ! label="$(python3 -c '
import sys
sys.path.insert(0, sys.argv[1])
from ar.common import label_for, parse_iso, utc_now
print(label_for(parse_iso(sys.argv[3]) if sys.argv[3] else utc_now(), sys.argv[2]))
' "$script_dir" "$tz" "$until_")" || [ -z "$label" ]; then
  log "FATAL: cannot derive the run label (timezone '$tz', --until '$until_')"
  exit 2
fi

work="$repo_path/$runtime_dir/$slug"
log_dir="${XDG_STATE_HOME:-$HOME/.local/state}/activity-report/$slug"
mkdir -p "$work" "$log_dir"

# One run per project at a time. A catch-up after a long sleep must not race
# the timer's regular run for the same window.
lock="$work/.lock"
exec 9>"$lock"
# macOS ships no flock(1), so the lock is taken with flock(2) from Python on the
# inherited fd 9 -- the same advisory lock on every host. It belongs to the open
# file description behind fd 9, so it outlives the helper and ends with this shell.
lock_rc=0
python3 -c '
import fcntl, sys
try:
    fcntl.flock(9, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError:
    sys.exit(1)
' || lock_rc=$?
if [ "$lock_rc" -eq 1 ]; then
  log "another activity-report run holds $lock; exit 5"
  exit 5
elif [ "$lock_rc" -ne 0 ]; then
  log "FATAL: could not take the lock $lock (helper exited $lock_rc)"
  exit 2
fi

# Read once, before any audience spends a collect on a compose that cannot
# start. Not exported: only the compose subshell puts it in the environment.
route="${model:-$gateway_route}"
if ! gateway_token="$("$cli" secret read --ref "$gateway_token_ref")" || [ -z "$gateway_token" ]; then
  log "FATAL: could not read the gateway token $gateway_token_ref; cannot compose"
  exit 2
fi

dry_note=""
if [ "$dry_run" -eq 1 ]; then dry_note=" [dry run]"; fi

step() {
  # step NAME command... -> the command's exit code, logged when non-zero.
  local name="$1"; shift
  local rc=0
  "$@" || rc=$?
  if [ "$rc" -ne 0 ]; then log "FAILED: $name exited $rc"; fi
  return "$rc"
}

# GNU `timeout` on Linux, `gtimeout` under Homebrew coreutils, and neither on a stock
# macOS or a launchd PATH: ar-timeout.py keeps the same contract (exit 124, SIGKILL after
# the grace period) so a hung compose is bounded everywhere.
if command -v timeout >/dev/null 2>&1; then
  timeout_cmd=(timeout)
elif command -v gtimeout >/dev/null 2>&1; then
  timeout_cmd=(gtimeout)
else
  timeout_cmd=(python3 "$script_dir/ar-timeout.py")
fi

internal_raw=""

run_audience() {
  local audience="$1"
  local digest="$work/$label-$audience.digest.json"

  # -- 1. collect --------------------------------------------------------------
  local collect_args=(collect --project "$slug" --audience "$audience" --run-id "$run_id" --out "$digest")
  if [ -n "$since" ]; then collect_args+=(--since "$since"); fi
  if [ -n "$until_" ]; then collect_args+=(--until "$until_"); fi
  if [ "$force" -eq 1 ]; then collect_args+=(--force); fi
  log "collecting"
  local crc=0
  "$cli" "${collect_args[@]}" || crc=$?
  if [ "$crc" -eq 4 ]; then
    log "nothing to do for $audience (collect exited 4)"
    return 4
  fi
  if [ "$crc" -ne 0 ]; then
    log "FAILED: collect exited $crc"
    return "$crc"
  fi
  if [ ! -s "$digest" ]; then
    log "FAILED: collect exited 0 but wrote no digest at $digest"
    return 2
  fi

  # The digest's label names the run's files; it normally equals the
  # provisional one and differs only if the clock crossed a minute.
  eval "$(python3 -c '
import json, shlex, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
w = d.get("window") or {}
prev = d.get("previous_report") or {}
def put(name, value):
    print(f"{name}={shlex.quote(str(value) if value is not None else str())}")
put("digest_label", d.get("label"))
put("window_start", w.get("start"))
put("window_end", w.get("end"))
put("previous_title", prev.get("title") or "none")
' "$digest")"
  local eff_label="${digest_label:-$label}"
  if [ "$eff_label" != "$label" ]; then
    log "note: digest label $eff_label differs from provisional $label; files use $eff_label"
    mv -f "$digest" "$work/$eff_label-$audience.digest.json"
    digest="$work/$eff_label-$audience.digest.json"
  fi
  local base="$work/$eff_label-$audience"
  local raw="$base.raw.txt" md="$base.md" html="$base.html" event="$base.event.json"
  local compose_json="$base.compose.json" emit_json="$base.emit.json"
  local lint_json="$work/$eff_label-external.lint.json"
  log "digest: $digest ($(wc -c <"$digest" | tr -d ' ') bytes), window $window_start to $window_end"

  # -- 2. compose --------------------------------------------------------------
  local claude_bin="$HOME/.local/bin/claude"
  if [ ! -x "$claude_bin" ]; then claude_bin="$(command -v claude || true)"; fi
  if [ -z "$claude_bin" ]; then
    log "FATAL: no claude binary; cannot compose"
    return 2
  fi
  local lint_hint="activity-report lint --audience $audience $raw --digest $digest"
  if [ "$audience" = external ]; then lint_hint="$lint_hint --lint-json $lint_json"; fi
  local template="$templates_dir/compose-$audience.md"
  local prompt
  prompt="$(python3 -c '
import sys
text = open(sys.argv[1], encoding="utf-8").read()
pairs = sys.argv[2:]
for key, value in zip(pairs[::2], pairs[1::2]):
    text = text.replace("{{" + key + "}}", value)
sys.stdout.write(text)
' "$template" \
      digest "$digest" raw_out "$raw" internal_raw "${internal_raw:-none}" lint_hint "$lint_hint" \
      project_name "$name" project_slug "$slug" audience "$audience" \
      window_start "$window_start" window_end "$window_end" previous_title "$previous_title")"

  # Exactly the tools this job needs: files, the lint, read-only git. A stale
  # raw.txt from an earlier attempt must not pass for this one.
  rm -f "$raw"
  local tools="Read,Write,Edit,Glob,Grep,Skill,Bash(activity-report lint:*),Bash(git log:*),Bash(git show:*),Bash(git diff:*)"
  log "composing $audience (headless, scoped tool grant, $route via $gateway_url, timeout ${timeout_minutes}m)"
  local compose_rc=0
  (
    cd "$repo_path"
    export ANTHROPIC_BASE_URL="$gateway_url"
    export ANTHROPIC_AUTH_TOKEN="$gateway_token"
    export ANTHROPIC_MODEL="$route"
    export ANTHROPIC_DEFAULT_OPUS_MODEL="$route"
    export ANTHROPIC_DEFAULT_SONNET_MODEL="$route"
    export ANTHROPIC_DEFAULT_HAIKU_MODEL="$route"
    export CLAUDE_CODE_SUBAGENT_MODEL="$route"
    export CLAUDE_CODE_EFFORT_LEVEL=xhigh
    "${timeout_cmd[@]}" --kill-after=60s "${timeout_minutes}m" "$claude_bin" --print --output-format json \
      --model "$route" \
      --allowed-tools "$tools" \
      --append-system-prompt "You are the unattended activity-report job for $name. Nobody is watching. Finish the whole task without asking questions." \
      "$prompt"
  ) >"$compose_json" || compose_rc=$?
  log "compose exited $compose_rc"

  # The model that actually answered: the modelUsage entry with the most
  # output tokens, by canonical name. Falls back to the requested route.
  local compose_model
  compose_model="$(python3 -c '
import json, sys
try:
    doc = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception:
    sys.exit(0)
if not isinstance(doc, dict):
    sys.exit(0)
best, best_out = "", -1
for label, stats in (doc.get("modelUsage") or {}).items():
    stats = stats or {}
    out = stats.get("outputTokens") or 0
    if out > best_out:
        best, best_out = str(stats.get("canonicalModel") or label), out
print(best[:120])
print(str(doc.get("is_error")).lower(), doc.get("num_turns"), doc.get("total_cost_usd"), doc.get("stop_reason"))
' "$compose_json")"
  local compose_stats
  compose_stats="$(printf '%s\n' "$compose_model" | sed -n 2p)"
  compose_model="$(printf '%s\n' "$compose_model" | sed -n 1p)"
  if [ -z "$compose_model" ]; then compose_model="$route"; fi
  log "compose model: ${compose_model:-unknown}; is_error/turns/cost/stop: ${compose_stats:-unknown}"

  if [ "$compose_rc" -ne 0 ] || [ ! -s "$raw" ]; then
    if [ -s "$raw" ]; then
      log "FAILED: compose exited $compose_rc (raw.txt present). Digest kept at $digest"
    else
      log "FAILED: compose exited $compose_rc and wrote no $raw. Digest kept at $digest"
    fi
    return 2
  fi

  # -- 3. lint -----------------------------------------------------------------
  local lint_args=(lint --project "$slug" --audience "$audience" "$raw" --digest "$digest")
  if [ "$audience" = external ]; then lint_args+=(--lint-json "$lint_json"); fi
  local lrc=0
  step lint "$cli" "${lint_args[@]}" || lrc=$?
  if [ "$lrc" -ne 0 ]; then
    log "lint refused $raw; nothing emitted for $audience"
    return "$lrc"
  fi
  if [ "$audience" = internal ]; then internal_raw="$raw"; fi

  # -- 4. render, assemble, emit -----------------------------------------------
  step render "$cli" render --project "$slug" --audience "$audience" "$raw" --digest "$digest" --md "$md" --html "$html" || return $?
  local assemble_args=(assemble --project "$slug" --audience "$audience" --digest "$digest" --raw "$raw" --md "$md" --html "$html" --out "$event")
  if [ -n "$compose_model" ]; then assemble_args+=(--model "$compose_model"); fi
  if [ "$dry_run" -eq 1 ]; then assemble_args+=(--dry-run); fi
  step assemble "$cli" "${assemble_args[@]}" || return $?
  step emit "$cli" emit --project "$slug" "$event" --out "$emit_json" || return $?

  # -- 5. verify, portal, retain, copy -----------------------------------------
  if [ "$dry_run" -eq 1 ]; then
    log "dry run: skipping verify, portal, retain and the durable copy"
    return 0
  fi
  step verify "$cli" verify --project "$slug" --run-id "$run_id" --audience "$audience" || return $?

  if [ -n "$portal_configured" ]; then
    step portal "$cli" portal --project "$slug" "$event" || return $?
  else
    log "no portal configured; skipping the portal row"
  fi

  if [ -n "$retain" ]; then
    local rrc=0
    "$cli" retain --project "$slug" --audience "$audience" "$raw" --digest "$digest" || rrc=$?
    if [ "$rrc" -ne 0 ]; then log "warning: retain exited $rrc (the event is published; memory is not)"; fi
  else
    log "hindsight.retain is false; skipping retain"
  fi

  if [ -n "$durable_html_dir" ]; then
    local durable="$repo_path/$durable_html_dir/$eff_label-$audience.html"
    mkdir -p "$(dirname "$durable")"
    cp -f "$html" "$durable"
    log "durable copy: $durable"
  fi
  return 0
}

overall=0
for audience in "${audiences[@]}"; do
  log_file="$log_dir/$label-$audience.log"
  exec > >(tee -a "$log_file") 2>&1
  log "===== $name ($slug) $audience, run $run_id, label $label$dry_note ====="
  rc=0
  run_audience "$audience" || rc=$?
  case "$rc" in
    0) log "===== $audience done =====" ;;
    4) log "===== $audience: nothing to do ====="; rc=0 ;;
    *) log "===== $audience FAILED (exit $rc) =====" ;;
  esac
  if [ "$rc" -gt "$overall" ]; then overall=$rc; fi
done
exit "$overall"
