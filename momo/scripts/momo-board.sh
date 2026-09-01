#!/usr/bin/env bash
# momo-board.sh — repo-agnostic board wrapper. Resolves the ticket provider from the
# nearest ancestor .project.json (ticket_provider.type) and dispatches:
#
#   plane | linear  -> the pjangler `tp` adapter installed in the repo's role_dir
#                      (<role_dir>/.scripts/lib/ticket-provider.sh) — unchanged.
#   trello          -> Momo's OWN bundled, self-contained adapter
#                      (scripts/providers/trello.py, stdlib-only). No per-repo scaffold,
#                      no role_dir required; lane mapping comes from <root>/.momo/config.json.
#
# Normalized ops (uniform across providers):
#   resolve | active_milestone | list_issues | get_issue <id>
#   | comment <id> <body> | transition <id> <backlog|unstarted|started|in_review|completed>
#
# For plane it maps the per-workspace secret PLANE_<WORKSPACE>_API_KEY into PLANE_API_KEY.
# The provider may also resolve that key from the inert shared Hermes fleet env.
# For trello it reads TRELLO_API_KEY/TRELLO_KEY + TRELLO_TOKEN from the env.
set -uo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ROOT=""
if [ "${1:-}" = "--root" ]; then ROOT="$2"; shift 2; fi

find_root() {
  local d="${1:-$PWD}"
  d="$(cd "$d" 2>/dev/null && pwd)" || return 1
  while [ "$d" != "/" ]; do
    [ -f "$d/.project.json" ] && { printf '%s\n' "$d"; return 0; }
    d="$(dirname "$d")"
  done
  return 1
}

if [ -z "$ROOT" ]; then
  ROOT="$(find_root "$PWD")" || {
    echo "momo-board: no .project.json found — not inside a pjangler CommonProject repo." >&2
    exit 2
  }
fi
PJ="$ROOT/.project.json"
[ -f "$PJ" ] || { echo "momo-board: $PJ not found." >&2; exit 2; }

# Resolve workspace, provider, and the first agent role_dir from .project.json.
CFG="$(python3 - "$PJ" <<'PY'
import json, sys, shlex
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    sys.stderr.write(f"momo-board: invalid .project.json: {e}\n")
    sys.exit(2)
tp = d.get("ticket_provider", {}) or {}
ws = tp.get("workspace", "") or ""
prov = tp.get("type", "") or ""
role_dir = ""
for v in (d.get("agents", {}) or {}).values():
    role_dir = v.get("role_dir", "") or role_dir
    if role_dir:
        break
print(f"WS={shlex.quote(ws)}")
print(f"PROVIDER={shlex.quote(prov)}")
print(f"ROLE_DIR={shlex.quote(role_dir)}")
PY
)" || { echo "momo-board: could not parse $PJ (invalid JSON)." >&2; exit 2; }
eval "$CFG"

# Trello: Momo's self-contained adapter — no role_dir / no installed scaffold needed.
if [ "${PROVIDER:-}" = "trello" ]; then
  cd "$ROOT" || exit 2
  exec python3 "$SKILL_DIR/scripts/providers/trello.py" --root "$ROOT" "$@"
fi

# plane / linear: delegate to the pjangler `tp` adapter installed in the role_dir.
[ -n "${ROLE_DIR:-}" ] || { echo "momo-board: no agents[].role_dir in $PJ." >&2; exit 2; }
ADAPTER="$ROOT/$ROLE_DIR/.scripts/lib/ticket-provider.sh"
[ -f "$ADAPTER" ] || { echo "momo-board: ticket adapter not found at $ADAPTER." >&2; exit 2; }

# Plane: map the per-workspace secret into the PLANE_API_KEY the adapter expects.
if [ "${PROVIDER:-}" = "plane" ]; then
  WSU="$(printf '%s' "${WS:-}" | tr '[:lower:]' '[:upper:]' | sed 's/[^A-Z0-9]/_/g')"
  var="PLANE_${WSU}_API_KEY"
  export PLANE_API_KEY="${PLANE_API_KEY:-${!var:-}}"
  fleet_env="${HERMES_FLEET_ENV:-${HOME:-}/.hermes/fleet.env}"
  fleet_has_key=0
  if [ -z "${PLANE_API_KEY:-}" ] && [ -f "$fleet_env" ]; then
    if python3 - "$fleet_env" "$var" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
key = sys.argv[2]
for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    if line.startswith("export "):
        line = line[7:].lstrip()
    name, sep, value = line.partition("=")
    if sep and name.strip() == key and value.strip().strip("'\""):
        raise SystemExit(0)
raise SystemExit(1)
PY
    then
      fleet_has_key=1
    fi
  fi
  if [ -z "${PLANE_API_KEY:-}" ] && [ "$fleet_has_key" -ne 1 ]; then
    echo "momo-board: WARN Plane credential unavailable (checked \$PLANE_API_KEY, \$$var, and $fleet_env)." >&2
  fi
fi

cd "$ROOT" || exit 2
# shellcheck disable=SC1090
. "$ADAPTER"
tp "$@"
