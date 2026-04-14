#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
state_root="${SELF_IMPROVING_AGENT_STATE_DIR:-${HOME}/.local/share/33god/self-improving-agent}"
log_path="${SELF_IMPROVING_AGENT_LOG_PATH:-${state_root}/working/hook-runtime.log}"

export TOOL_NAME="${TOOL_NAME:-${3:-bash}}"
export TOOL_OUTPUT="${TOOL_OUTPUT:-${1:-}}"
export EXIT_CODE="${EXIT_CODE:-${2:-0}}"

mkdir -p "$(dirname "${log_path}")"

if ! python3 "${repo_root}/scripts/hook_runtime.py" post-tool >/dev/null 2>>"${log_path}"; then
  echo "[self-improving-agent] PostToolUse runtime failed" >&2
fi

exit 0
