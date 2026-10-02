#!/usr/bin/env bash
# Build and install the pinned, patched cli-web-search for the web-search wrapper, and leave a read-only config stub.
# The binary lives outside PATH on purpose: the wrapper is the only entry point and verifies the digest recorded
# here before it hands the binary an API key. Idempotent; --force rebuilds.
set -euo pipefail

PIN=72f581e54df8b538a1769d4027b2d73a2309f7d4
REPO=https://github.com/scottgl9/cli-web-search
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PATCH="$HERE/patches/0001-providers-no-redirects.patch"
PREFIX=${PREFIX:-$HOME/.local/libexec/web-search}
BIN="$PREFIX/bin/cli-web-search"
MARK="$PREFIX/installed"
patch_sha=$(sha256sum "$PATCH" | cut -d' ' -f1)

recorded() { sed -n 's/.*\b'"$1"'=\([^ ]*\).*/\1/p' "$MARK" 2>/dev/null || true; }

if [[ "${1:-}" != "--force" && -x "$BIN" && "$(recorded sha)" == "$PIN" && "$(recorded patch)" == "$patch_sha" \
      && "$(recorded bin)" == "$(sha256sum "$BIN" | cut -d' ' -f1)" ]]; then
  echo "cli-web-search already installed from the pinned, patched source"
else
  command -v cargo >/dev/null || { echo "cargo not found (install rust via mise or rustup)" >&2; exit 1; }
  work=$(mktemp -d)
  trap 'rm -rf "$work"' EXIT
  git clone -q "$REPO" "$work/src"
  git -C "$work/src" checkout -q "$PIN"
  [[ "$(git -C "$work/src" rev-parse HEAD)" == "$PIN" ]] || { echo "pinned commit mismatch" >&2; exit 1; }
  git -C "$work/src" apply --check "$PATCH"
  git -C "$work/src" apply "$PATCH"
  mkdir -p "$work/home" "$work/cargo"
  # Throwaway HOME and CARGO_HOME, no inherited tokens. This limits what the environment exposes to the 15 dependency
  # build scripts; it is not a sandbox (they can still read files by absolute path). Default features: no MCP server.
  env -i HOME="$work/home" CARGO_HOME="$work/cargo" RUSTUP_HOME="${RUSTUP_HOME:-$HOME/.rustup}" \
    PATH="$HOME/.cargo/bin:$(dirname "$(command -v cargo)"):/usr/local/bin:/usr/bin:/bin" \
    cargo install --path "$work/src" --locked --root "$PREFIX"
  mkdir -p "$PREFIX"
  echo "sha=$PIN patch=$patch_sha bin=$(sha256sum "$BIN" | cut -d' ' -f1)" > "$MARK"
fi

# `cli-web-search config set` writes env-supplied keys to config.yaml in plaintext. An empty read-only directory in
# the way makes that fail instead of persisting a key.
cfg="${XDG_CONFIG_HOME:-$HOME/.config}/cli-web-search"
if [[ -L "$cfg" || ( -e "$cfg" && ! -d "$cfg" ) ]]; then
  echo "WARNING: $cfg is a symlink or not a directory: remove it, then re-run, to get the read-only stub" >&2
elif [[ -f "$cfg/config.yaml" ]]; then
  echo "WARNING: $cfg/config.yaml exists and may contain plaintext keys: review and delete it" >&2
elif [[ ! -e "$cfg" ]]; then
  mkdir -p "$cfg"
  chmod 500 "$cfg"
  echo "created read-only config stub $cfg"
elif [[ -z "$(ls -A "$cfg")" ]]; then
  chmod 500 "$cfg"
fi

if [[ -e "$HOME/.local/bin/cli-web-search" ]]; then
  echo "NOTE: an older copy at ~/.local/bin/cli-web-search bypasses the wrapper's integrity check: remove it with" >&2
  echo "      cargo uninstall --root ~/.local cli-web-search" >&2
fi

"$BIN" --version
echo "next: $HERE/web-search doctor --live"
