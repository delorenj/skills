#!/usr/bin/env bash
# survey.sh — read-only disk-space evidence report for Linux and macOS.
#
# Prints one markdown report to stdout. Changes nothing. Portable to the bash
# 3.2 that ships with macOS: no associative arrays, no mapfile, no GNU-only
# find/du/stat flags.
#
#   bash survey.sh > /tmp/disk-survey.md               # local
#   ssh host 'bash -s' < survey.sh > host-survey.md    # remote, nothing installed there
#   bash survey.sh --quick                             # skip the slow full-home walks
#
# Sizes are du's allocated KiB, so sparse files count as what they occupy.
# du double-counts nothing within one call, but hardlinked caches (uv, pnpm,
# bun, cargo targets) appear at full size here AND in the venv/node_modules
# that links them: removing the cache frees far less than it shows.

QUICK=0
[ "${1:-}" = "--quick" ] && QUICK=1

OS=$(uname -s)
HOST=$(hostname -s 2>/dev/null || hostname)
# The tailnet DNS label is the canonical machine name (the Mac's own hostname is
# mommymac, its display name "Carrie's MacBook Air"); machine profiles are keyed by it.
# The first DNSName in `status --json` belongs to Self.
TSNAME=""
if command -v tailscale >/dev/null 2>&1; then
  TSNAME=$(tailscale status --json 2>/dev/null | sed -n 's/.*"DNSName": *"\([^".]*\)\..*/\1/p' | head -1)
elif [ -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]; then
  TSNAME=$(/Applications/Tailscale.app/Contents/MacOS/Tailscale status --json 2>/dev/null | sed -n 's/.*"DNSName": *"\([^".]*\)\..*/\1/p' | head -1)
fi

# timeout(1) is GNU; macOS has it only as gtimeout from coreutils, if at all.
TMO=""
command -v timeout >/dev/null 2>&1 && TMO="timeout"
[ -z "$TMO" ] && command -v gtimeout >/dev/null 2>&1 && TMO="gtimeout"
# macOS ships neither: fall back to perl's alarm (perl is always there), else run unbounded.
tmo() {
  local s=$1; shift
  if [ -n "$TMO" ]; then "$TMO" "$s" "$@"
  elif command -v perl >/dev/null 2>&1; then perl -e 'alarm shift; exec @ARGV' "$s" "$@"
  else "$@"; fi
}

human() { awk -v k="$1" 'BEGIN{ if (k>=1048576) printf "%.1fG", k/1048576; else if (k>=1024) printf "%.0fM", k/1024; else printf "%dK", k }'; }

# size_list PATH... -> "KiB<TAB>path" lines for existing paths, biggest first
size_list() {
  local p
  for p in "$@"; do
    [ -e "$p" ] || continue
    tmo 120 du -sk "$p" 2>/dev/null | tail -1
  done | sort -rn
}

print_sizes() {  # stdin: KiB<TAB>path; $1 = min KiB to show
  local min=${1:-102400}
  while IFS="$(printf '\t')" read -r k p; do
    [ -n "$k" ] || continue
    [ "$k" -ge "$min" ] || continue
    printf -- '- %7s  %s\n' "$(human "$k")" "$p"
  done
}

# BSD du crosses into FileProvider mounts (Google Drive, iCloud) under
# ~/Library/CloudStorage; -I skips them. GNU du has no -I and needs none.
DU_SKIP=""
[ "$OS" = "Darwin" ] && DU_SKIP="-I CloudStorage"

section() { printf '\n## %s\n\n' "$1"; }

printf '# Disk survey: %s%s\n\n' "$HOST" "${TSNAME:+ (tailscale: $TSNAME)}"
printf -- '- generated: %s\n- os: %s %s\n- user: %s\n- mode: %s\n' \
  "$(date '+%Y-%m-%d %H:%M %Z')" "$OS" "$(uname -r)" "$(id -un)" "$([ $QUICK = 1 ] && echo quick || echo full)"
if sudo -n true 2>/dev/null; then echo "- sudo: passwordless (root-only probes ran)"; SUDO="sudo -n"; else echo "- sudo: NO (root-only probes skipped — say so before concluding anything about them)"; SUDO=""; fi
echo "- machine profile to load: references/machines/${TSNAME:-$HOST}.md"

# ---------------------------------------------------------------------------
section "Filesystems"
if [ "$OS" = "Darwin" ]; then
  df -h / /System/Volumes/Data 2>/dev/null
  echo
  echo '```'
  diskutil apfs list 2>/dev/null | grep -E 'Container disk|Capacity (Ceiling|In Use|Not Allocated)|Name:|Capacity Consumed|\(Role\)' | sed 's/^[| +-]*//'
  echo '```'
  echo
  echo "APFS local snapshots (Time Machine / os.update — hold deleted blocks until thinned):"
  tmutil listlocalsnapshots / 2>/dev/null | sed 's/^/    /'
  echo
  printf 'Purgeable (macOS counts it as "available" in Finder, df does not): '
  diskutil info / 2>/dev/null | awk -F: '/Purgeable|Container Free Space/{gsub(/^ +/,"",$2); printf "%s=%s; ", $1, $2}'
  echo
else
  df -hT -x tmpfs -x devtmpfs -x squashfs -x overlay -x efivarfs 2>/dev/null || df -h
  echo
  df -i / 2>/dev/null | tail -1 | awk '{print "inodes on /: " $5 " used"}'
fi

# ---------------------------------------------------------------------------
section "Top-level of \$HOME (incl. dotdirs, >=100M)"
( cd "$HOME" && for e in .[!.]* * ; do [ -e "$e" ] && [ ! -L "$e" ] && echo "$HOME/$e"; done ) 2>/dev/null \
  | while read -r p; do tmo 180 du -sk -x $DU_SKIP "$p" 2>/dev/null | tail -1; done | sort -rn | head -40 | print_sizes 102400

# ---------------------------------------------------------------------------
section "Known rebuildable caches and regrowers (>=100M)"
H=$HOME
if [ "$OS" = "Darwin" ]; then
  L="$H/Library"
  size_list \
    "$L/Caches" "$L/Logs" "$H/.Trash" \
    "$L/Developer/Xcode/DerivedData" "$L/Developer/Xcode/Archives" "$L/Developer/Xcode/iOS DeviceSupport" \
    "$L/Developer/Xcode/watchOS DeviceSupport" "$L/Developer/Xcode/CodingAssistant" \
    "$L/Developer/CoreSimulator/Devices" "$L/Developer/CoreSimulator/Caches" \
    /Library/Developer/CoreSimulator/Images /Library/Developer/CoreSimulator/Volumes \
    "$L/Containers/com.docker.docker" "$L/Application Support/com.docker.install" \
    "$L/Android/sdk/system-images" "$L/Android/sdk/ndk" "$H/.android/avd" \
    "$L/pnpm" "$H/.local/share/pnpm" "$H/.npm" "$H/.bun/install/cache" "$L/Caches/Yarn" \
    "$H/.gradle/caches" "$H/.gradle/wrapper/dists" "$H/.m2/repository" \
    "$H/.cocoapods" "$L/Caches/CocoaPods" "$H/.pub-cache" \
    "$H/.cargo/registry" "$H/.rustup/toolchains" "$H/go/pkg/mod" \
    "$H/.cache/uv" "$H/.local/share/uv" "$H/.cache/pip" "$H/.cache/huggingface" "$H/.local/share/mise/installs" \
    "$H/.cache" "$H/actions-runner/_work" "$H/actions-runner/_diag" \
    "$L/Application Support/Claude/vm_bundles" "$L/Application Support/Google/Chrome" \
    "$L/Application Support/Code/Cache" "$L/Application Support/Code/CachedData" \
    "$L/Application Support/Slack/Cache" "$L/Application Support/MobileSync/Backup" \
    "$L/Messages/Attachments" "$L/Mail" \
    /opt/homebrew/Caskroom "$L/Caches/Homebrew" \
    2>/dev/null | print_sizes 102400
else
  size_list \
    "$H/.cache" "$H/.local/share/Trash" "$H/.cache/uv" "$H/.cache/pip" "$H/.cache/huggingface" \
    "$H/.cache/go-build" "$H/go/pkg/mod" "$H/.npm" "$H/.bun/install/cache" "$H/.local/share/pnpm" \
    "$H/.cargo/registry" "$H/.rustup/toolchains" "$H/.gradle/caches" "$H/.m2/repository" \
    "$H/.local/share/mise/installs" "$H/.android/avd" "$H/Android/Sdk/system-images" \
    "$H/.claude/tmp" "$H/.claude/projects" "$H/.codex/sessions" "$H/.config/Claude/vm_bundles" \
    "$H/actions-runner/_work" "$H/.local/state" "$H/snap" \
    /var/log /var/log/journal /var/cache/apt /var/lib/snapd/snaps /var/lib/docker /var/lib/containerd /tmp \
    2>/dev/null | print_sizes 102400
fi
# Per-runner work dirs when several runners live side by side (macOS too: the
# Mac build host runs five, and only the shared one sits at ~/actions-runner/_work)
ls -d "$H"/actions-runner*/_work "$H"/actions-runner/*/_work 2>/dev/null | while read -r p; do size_list "$p"; done | print_sizes 524288

# ---------------------------------------------------------------------------
# Cheap enough for --quick, and the two biggest surprises on carries-macbook-air:
# a launchd crash loop had written 1.9 GiB of logs, a reconnect loop 0.8 GiB.
section "Runaway logs and state (>=100M under the usual log/state dirs) and restart loops"
tmo 60 find "$H/Library/Logs" "$H"/.[!.]*/logs "$H/.local/state" "$H/.pm2/logs" -maxdepth 3 -type f -size +204800 2>/dev/null \
  | while read -r f; do printf '%s\t%s\n' "$(du -sk "$f" 2>/dev/null | cut -f1)" "$f"; done | sort -rn | head -15 | print_sizes 102400
if [ "$OS" = "Darwin" ]; then
  # runs = launches since the agent was loaded. Thousands under KeepAlive (no
  # StartInterval) is a crash loop; a StartInterval agent racks up runs legitimately.
  for f in "$H"/Library/LaunchAgents/*.plist; do
    [ -f "$f" ] || continue
    l=$(basename "$f" .plist)
    info=$(launchctl print "gui/$(id -u)/$l" 2>/dev/null)
    r=$(printf '%s\n' "$info" | awk '$1=="runs" && $2=="=" {print $3; exit}')
    [ -n "$r" ] && [ "$r" -ge 100 ] 2>/dev/null || continue
    ex=$(printf '%s\n' "$info" | awk -F'= ' '/last exit code =/ {print $2; exit}')
    iv=$(plutil -extract StartInterval raw "$f" 2>/dev/null)
    kind="LOOP? KeepAlive/no schedule"; [ -n "$iv" ] && kind="periodic every ${iv}s"
    printf -- '- %7s runs  %s  [%s, last exit %s]  stderr: %s\n' "$r" "$l" "$kind" "${ex:-?}" "$(plutil -extract StandardErrorPath raw "$f" 2>/dev/null || echo none)"
  done | sort -t' ' -k2 -rn
else
  for scope in --user --system; do
    systemctl $scope list-units --type=service --all --no-legend --plain 2>/dev/null | awk '{print $1}' | while read -r u; do
      n=$(systemctl $scope show -p NRestarts --value "$u" 2>/dev/null)
      [ "${n:-0}" -ge 20 ] 2>/dev/null && printf -- '- %7s restarts  %s (%s)\n' "$n" "$u" "${scope#--}"
    done
  done
fi
echo "(no lines above = no runaway logs or state and no agent/service with 100+ launches / 20+ restarts)"

# ---------------------------------------------------------------------------
section "Docker"
if command -v docker >/dev/null 2>&1 && tmo 20 docker info >/dev/null 2>&1; then
  tmo 60 docker system df 2>/dev/null
  echo
  echo "(RECLAIMABLE counts shared layers: real savings are smaller. Named volumes hold data — never prune them blind.)"
else
  echo "docker not installed or daemon unreachable"
fi

# ---------------------------------------------------------------------------
if [ $QUICK = 0 ]; then
  section "Files >=1G under \$HOME (newest first)"
  if [ "$OS" = "Darwin" ]; then
    tmo 300 find "$HOME" -xdev \( -path "$HOME/Library/CloudStorage" -o -path "$HOME/Library/Mail" \) -prune -o -type f -size +2097152 -print 2>/dev/null \
      | while read -r f; do stat -f '%m%t%z%t%Sm%t%N' -t '%Y-%m-%d' "$f" 2>/dev/null; done \
      | sort -rn | head -40 | awk -F'\t' '{printf "- %6.1fG  %s  %s\n", $2/1073741824, $3, $4}'
  else
    tmo 300 /usr/bin/find "$HOME" -xdev -type f -size +1G -printf '%T@\t%s\t%TY-%Tm-%Td\t%p\n' 2>/dev/null \
      | sort -rn | head -40 | awk -F'\t' '{printf "- %6.1fG  %s  %s\n", $2/1073741824, $3, $4}'
  fi

  section "Written in the last 48h, >=200M (who is growing right now)"
  if [ "$OS" = "Darwin" ]; then
    tmo 300 find "$HOME" -xdev -path "$HOME/Library/CloudStorage" -prune -o -type f -mtime -2 -size +409600 -print 2>/dev/null \
      | while read -r f; do stat -f '%z%t%Sm%t%N' -t '%m-%d %H:%M' "$f" 2>/dev/null; done \
      | sort -rn | head -30 | awk -F'\t' '{printf "- %6.0fM  %s  %s\n", $1/1048576, $2, $3}'
  else
    tmo 300 /usr/bin/find / -xdev -type f -mmin -2880 -size +200M -printf '%s\t%TY-%Tm-%Td %TH:%TM\t%p\n' 2>/dev/null \
      | sort -rn | head -30 | awk -F'\t' '{printf "- %6.0fM  %s  %s\n", $1/1048576, $2, $3}'
  fi

  section "Logs >=50M (the ones that grow forever)"
  if [ "$OS" = "Darwin" ]; then
    tmo 240 find "$HOME" /Library/Logs /private/var/log -xdev -path "$HOME/Library/CloudStorage" -prune -o -type f \( -name '*.log' -o -name '*.log.*' -o -name '*.jsonl' -o -name '*.out' -o -name '*.err' \) -size +102400 -print 2>/dev/null \
      | while read -r f; do stat -f '%z%t%Sm%t%N' -t '%Y-%m-%d' "$f" 2>/dev/null; done \
      | sort -rn | head -30 | awk -F'\t' '{printf "- %6.0fM  %s  %s\n", $1/1048576, $2, $3}'
  else
    tmo 240 /usr/bin/find "$HOME" /var/log -xdev -type f \( -name '*.log' -o -name '*.log.*' -o -name '*.jsonl' -o -name '*.out' -o -name '*.err' \) -size +50M -printf '%s\t%TY-%Tm-%Td\t%p\n' 2>/dev/null \
      | sort -rn | head -30 | awk -F'\t' '{printf "- %6.0fM  %s  %s\n", $1/1048576, $2, $3}'
    command -v journalctl >/dev/null 2>&1 && { echo; journalctl --disk-usage 2>/dev/null; }
  fi
fi

# ---------------------------------------------------------------------------
section "Deleted but still open (space df counts but no file shows)"
# Sizes over 1 TiB are sparse mmaps (.NET runners, jellyfin), not real bytes.
if command -v lsof >/dev/null 2>&1; then
  tmo 60 $SUDO lsof -nP +L1 2>/dev/null | awk 'NR>1 && $7 ~ /^[0-9]+$/ && $7>104857600 && $7<1099511627776 && $NF !~ /memfd|doublemapper/ {printf "- %6.1fG  %s pid %s  %s\n",$7/1073741824,$1,$2,$NF}' | sort -rn | head -15
  [ -z "$SUDO" ] && echo "(no sudo: only this user's processes were visible)"
else
  echo "lsof not available"
fi

# ---------------------------------------------------------------------------
section "Cleanup automation already installed"
if [ "$OS" = "Darwin" ]; then
  ls "$HOME/Library/LaunchAgents" 2>/dev/null | grep -iE 'prune|clean|sweep|rotate|disk' | sed 's/^/- launchd: /'
  crontab -l 2>/dev/null | grep -iE 'prune|clean|sweep|rotate|rm ' | sed 's/^/- cron: /'
else
  systemctl --user list-timers --all --no-pager 2>/dev/null | grep -iE 'prune|clean|sweep|rotate|maintain|tmpfiles' | awk '{print "- user timer: " $(NF-1) "  next: " $1, $2, $3}'
  systemctl list-timers --all --no-pager 2>/dev/null | grep -iE 'prune|clean|logrotate|tmpfiles|fstrim' | awk '{print "- system timer: " $(NF-1)}'
  crontab -l 2>/dev/null | grep -iE 'prune|clean|sweep|rotate|rm ' | sed 's/^/- cron: /'
fi
echo
# A cron/cleanup `rm` whose target runs through a symlink is a loaded gun: while
# the link dangles it deletes nothing, and the day someone repoints the link it
# empties the real folder (carries-macbook-air: `rm -rf ~/gd/screenshots/*` every
# 2 min, ~/gd dangling, real synced Drive "screenshots" folders one rename away).
( set -f
  crontab -l 2>/dev/null | grep -v '^[[:space:]]*#' | grep -E '(^|[;&| ])rm ' | while IFS= read -r line; do
    for tok in $line; do
      case "$tok" in /*|'~'*) ;; *) continue ;; esac
      p=$(printf '%s' "$tok" | sed "s#^~#$HOME#"); p=${p%%[*?]*}; p=${p%/}
      cur=""; rest=${p#/}
      while [ -n "$rest" ]; do
        part=${rest%%/*}; [ "$part" = "$rest" ] && rest="" || rest=${rest#*/}
        cur="$cur/$part"
        case "$cur" in /tmp|/var|/etc) continue ;; esac   # macOS system symlinks into /private
        if [ -L "$cur" ]; then
          state="resolves"; [ -e "$cur" ] || state="DANGLING"
          echo "- WARNING cron rm target passes through symlink $cur -> $(readlink "$cur") ($state): if repointed, this job deletes under the new target"
          break
        fi
      done
    done
  done )
echo
echo "_End of survey. Compare against the machine profile before acting._"
