#!/usr/bin/env bash
# test_transcriber_resolution.sh — the resolution order behind `same-checkout`.
#
# Proven false positive (2026-10-17): ~/.local/bin/transcribe is a modified
# COPY of the repo shim, not a symlink, so the old PATH-only resolution rooted
# the transcriber at ~/.local and the board reported "two checkouts" against a
# correctly pinned daemon. The functions under test pin the order the daemon
# itself uses: WAX_TRANSCRIBE pin → canonical repo shim → PATH.
#
# Self-contained and read-only. The "daemon" is a child bash process whose
# *initial* environment carries the pin (a post-exec `export` would not appear
# in /proc/<pid>/environ, which is the point of spawning children). Nothing
# here calls systemctl, restarts, or mutates the real daemon or repo.
#
# Run: bash scripts/tests/test_transcriber_resolution.sh

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCTOR="$HERE/../doctor.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp/opencode}/wax-doctor-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

# ── child: runs with a controlled initial environment ────────────────────────
# Invoked as: bash "$0" --child <case> <repo> <funcs.sh>
# Any WAX_TRANSCRIBE the case needs is supplied by the parent via `env`, so it
# is genuinely visible through /proc/self/environ.
if [ "${1:-}" = "--child" ]; then
  case="$2"; REPO="$3"; . "$4"
  MAIN_PID="$$"    # this process is the "daemon"; /proc/$$/environ is its truth
  rc=0
  case "$case" in
    pin-wins)
      [ "$(resolved_transcribe)" = "$(readlink -f "$WAX_TRANSCRIBE")" ] \
        || { echo "resolved to '$(resolved_transcribe)', expected the pin $WAX_TRANSCRIBE"; rc=1; } ;;
    repo-shim)
      [ "$(resolved_transcribe)" = "$(readlink -f "$REPO/bin/transcribe")" ] \
        || { echo "resolved to '$(resolved_transcribe)', expected the repo shim despite the PATH decoy"; rc=1; } ;;
    path-fallback)
      [ "$(resolved_transcribe)" = "$(readlink -f "$(command -v transcribe)")" ] \
        || { echo "resolved to '$(resolved_transcribe)', expected the PATH fallback"; rc=1; } ;;
    nothing-resolves)
      [ -z "$(resolved_transcribe)" ] \
        || { echo "resolved to '$(resolved_transcribe)' with no pin, no shim, no PATH entry"; rc=1; } ;;
    same-checkout-pass)
      out="$(chk_same_checkout)" && exit 0
      echo "$out"; exit 1 ;;
    same-checkout-fail)
      if out="$(chk_same_checkout)"; then
        echo "same-checkout passed a pin outside the repo: $out"; exit 1
      fi
      exit 0 ;;
  esac
  exit "$rc"
fi

# ── parent: fixtures ─────────────────────────────────────────────────────────
fail=0; pass=0
ok()  { pass=$((pass+1)); printf '  ok   %s\n' "$1"; }
bad() { fail=$((fail+1)); printf '  FAIL %s\n' "$1"; }

[ -f "$DOCTOR" ] || { echo "doctor.sh not found at $DOCTOR"; exit 2; }

# Extract the shipped functions verbatim — the test must not drift from a copy.
extract_fn() { sed -n "/^$1() {/,/^}/p" "$DOCTOR"; }
FUNCS="$TMP/funcs.sh"
{
  extract_fn daemon_env_value
  extract_fn resolve_transcriber
  extract_fn resolved_transcribe
  extract_fn chk_same_checkout
} > "$FUNCS"
grep -q '^resolved_transcribe() {' "$FUNCS" \
  || { echo "could not extract the resolver functions from doctor.sh"; exit 2; }

REPO="$TMP/repo";  mkdir -p "$REPO/bin"
DECOY="$TMP/decoy"; mkdir -p "$DECOY/bin"
printf '#!/bin/sh\n' > "$REPO/bin/transcribe";  chmod +x "$REPO/bin/transcribe"
printf '#!/bin/sh\n' > "$REPO/bin/waxd";       chmod +x "$REPO/bin/waxd"
printf '#!/bin/sh\n' > "$DECOY/bin/transcribe"; chmod +x "$DECOY/bin/transcribe"   # the ~/.local fork shape: a copy, not a symlink
DECOYPATH="$DECOY/bin:$PATH"

run() { # run <case> [env VAR=VAL ...]
  local case="$1"; shift
  env "$@" PATH="$DECOYPATH" bash "$0" --child "$case" "$REPO" "$FUNCS"
}

echo "transcriber resolution order (daemon pin → repo shim → PATH):"

# 1. The daemon pin wins even with a PATH decoy shaped like the 2026-10-17 fork.
if run pin-wins WAX_TRANSCRIBE="$REPO/bin/transcribe" >/dev/null; then
  ok "daemon WAX_TRANSCRIBE pin wins over a PATH decoy"
else bad "daemon WAX_TRANSCRIBE pin ignored (the 2026-10-17 false positive is back)"; fi

# 2. Unpinned: this checkout's canonical shim wins over the PATH decoy.
if run repo-shim >/dev/null; then
  ok "repo shim preferred when no pin is set"
else bad "unpinned resolution fell through to PATH"; fi

# 3. No pin, no repo shim: PATH is the last resort.
mv "$REPO/bin/transcribe" "$REPO/bin/transcribe.away"
if run path-fallback >/dev/null; then
  ok "PATH fallback used only as a last resort"
else bad "PATH fallback not reached"; fi

# 4. Nothing resolves at all: empty, not a bogus /nonexistent path.
#    (Repo shim still moved aside; PATH stripped of every transcribe.)
if env -u WAX_TRANSCRIBE PATH=/usr/bin:/bin bash "$0" --child nothing-resolves "$REPO" "$FUNCS" >/dev/null; then
  ok "empty result when nothing resolves"
else bad "resolver fabricated a path from nothing"; fi
mv "$REPO/bin/transcribe.away" "$REPO/bin/transcribe"

# 5. chk_same_checkout end-to-end: a pinned-in-repo daemon passes beside a decoy fork.
if run same-checkout-pass WAX_TRANSCRIBE="$REPO/bin/transcribe" >/dev/null; then
  ok "same-checkout passes with the daemon pin inside the repo (PATH fork present)"
else bad "same-checkout false-positives a correctly pinned daemon"; fi

# 6. A pin genuinely outside the repo still fails — the check keeps its teeth.
if run same-checkout-fail WAX_TRANSCRIBE="$DECOY/bin/transcribe" >/dev/null; then
  ok "same-checkout still fails a pin outside the deployed repo"
else bad "same-checkout no longer catches a real two-checkout split"; fi

printf '%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
