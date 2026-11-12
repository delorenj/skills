#!/usr/bin/env bash
# The Dev Journal's unattended entrypoint: verify yesterday's report, generate it when
# missing, then deliver it. ONE copy, here. infra/scripts/dev-journal-hermes-nightly.sh
# and dev-journal-ensure-nightly.sh on the big-chungus host are three-line shims that
# exec this file; a peer host's Candybar manifest runs it directly.
#
#   nightly.sh [nightly|ensure] [--date YYYY-MM-DD]
#
#   nightly  (default) verify; run if unverified; ALWAYS distribute; exit 1 if the run
#            or the distribution failed. Prints `Dev Journal <date>: run=N distribute=N`.
#   ensure   the missed-nightly recovery: if a verified report exists, re-deliver it
#            best-effort and exit 0; otherwise run it, deliver best-effort when it now
#            verifies, and exit non-zero when it still does not.
#
# The date is yesterday in the CONFIG's timezone (the report is about a day that has
# finished), computed in Python: BSD date has no `-d yesterday`. `--date` pins it for a
# backfill or a proof; nothing else about the run changes.
#
# Host-owned values come from the environment or ~/.config/33god/host.env, never from
# this file (see hostenv.py): DDR_CONFIG (the report.json), DDR_MIRROR_DIR (forced to
# `disabled` below: a scheduled run must not write a git-tracked mirror), the Resend key
# reference, the sender and the digest footer (consumed by distribute.py).
#
# Exit status is trustworthy by construction: it is derived from `reportctl verify`
# reading the published artifact back, never from a scheduler's own account of itself.
set -uo pipefail

# macOS and a launchd job start with almost no PATH. Append, never prepend: a host
# whose PATH already works keeps resolving the same python3 it always did.
export PATH="$PATH:$HOME/.local/bin:$HOME/.local/share/mise/shims:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

# Resolve this file through symlinks (BSD readlink has no -f) so the sibling files are found.
src="${BASH_SOURCE[0]}"
while [ -h "$src" ]; do
  dir="$(cd -P "$(dirname "$src")" && pwd)"
  src="$(readlink "$src")"
  case "$src" in /*) ;; *) src="$dir/$src" ;; esac
done
script_dir="$(cd -P "$(dirname "$src")" && pwd)"
reportctl="$script_dir/reportctl"

mode="nightly"; report_date=""
while [ $# -gt 0 ]; do
  case "$1" in
    nightly|ensure) mode="$1"; shift ;;
    --date) [ $# -ge 2 ] || { echo "nightly.sh: --date needs a value" >&2; exit 2; }; report_date="$2"; shift 2 ;;
    --date=*) report_date="${1#*=}"; shift ;;
    -h|--help) sed -n '2,/^set -uo/p' "$0" | sed '$d;s/^# \{0,1\}//'; exit 0 ;;
    *) echo "nightly.sh: unknown argument: $1" >&2; exit 2 ;;
  esac
done

if ! config="$(python3 "$script_dir/hostsettings.py" get DDR_CONFIG "$HOME/.config/delonet-daily-report/report.json")"; then
  echo "nightly.sh: could not read the host overlay (DDR_CONFIG)" >&2
  exit 2
fi
config="${config/#\~/$HOME}"
if [ ! -f "$config" ]; then
  echo "nightly.sh: no report config at $config (set DDR_CONFIG)" >&2
  exit 2
fi

if [ -z "$report_date" ]; then
  if ! report_date="$(python3 - "$config" <<'PY'
import datetime as dt
import json
import sys
from zoneinfo import ZoneInfo

zone = ZoneInfo(json.load(open(sys.argv[1], encoding="utf-8"))["timezone"])
print((dt.datetime.now(zone).date() - dt.timedelta(days=1)).isoformat())
PY
)" || [ -z "$report_date" ]; then
    echo "nightly.sh: could not derive yesterday's date from the timezone in $config" >&2
    exit 2
  fi
fi

export DDR_MIRROR_DIR="disabled"

verified() {
  local result
  result="$("$reportctl" --config "$config" verify --date "$report_date" 2>/dev/null || true)"
  python3 -c 'import json, sys; sys.exit(0 if json.load(sys.stdin).get("ok") is True else 1)' \
    <<<"$result" >/dev/null 2>&1
}

nightly() {
  local run_status=0 distribution_status
  if ! verified; then
    "$reportctl" --config "$config" run --date "$report_date" || run_status=$?
    # A partial collector result is still a verified, published journal. The
    # outbox reconciler handles any completion-event delivery retry.
    if verified; then
      run_status=0
    elif (( run_status == 0 )); then
      run_status=1
    fi
  fi

  "$reportctl" --config "$config" distribute --date "$report_date"
  distribution_status=$?

  printf 'Dev Journal %s: run=%s distribute=%s\n' "$report_date" "$run_status" "$distribution_status"
  if (( run_status != 0 || distribution_status != 0 )); then
    return 1
  fi
}

ensure() {
  if verified; then
    printf 'Verified Dev Journal already exists for %s\n' "$report_date"
    "$reportctl" --config "$config" distribute --date "$report_date" || true
    return 0
  fi

  printf 'Generating missing Dev Journal for %s\n' "$report_date"
  local run_status=0
  "$reportctl" --config "$config" run --date "$report_date" || run_status=$?
  if verified; then
    "$reportctl" --config "$config" distribute --date "$report_date" || true
    return 0
  fi
  if (( run_status == 0 )); then
    return 1
  fi
  return "$run_status"
}

"$mode"
exit $?
