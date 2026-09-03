#!/usr/bin/env bash
# Install (or refresh) the systemd user timer for one project.
#
# A thin wrapper: the implementation is `activity-report install-timer`
# (scripts/ar/schedule.py), which copies the two template units from
# assets/systemd/ to ~/.config/systemd/user/, writes the project's time and
# zone into activity-report@<slug>.timer.d/schedule.conf, reloads, and
# enables the timer. This file only checks the two things Python cannot
# fix: that systemd is here at all, and that the user lingers.
#
# Usage:
#   scripts/install-timer.sh --project SLUG

set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "install-timer: systemctl not found; this host does not run systemd" >&2
  exit 2
fi

# Without lingering the user manager stops at logout and the timer sleeps
# with it. Enabling it is a one-time sudo, so it is a note, not a failure.
if ! loginctl show-user "${USER:-$(id -un)}" --property=Linger 2>/dev/null | grep -q 'Linger=yes'; then
  echo "install-timer: note: lingering is off for ${USER:-$(id -un)}; run once: sudo loginctl enable-linger ${USER:-$(id -un)}" >&2
fi

exec "$script_dir/activity-report" install-timer "$@"
