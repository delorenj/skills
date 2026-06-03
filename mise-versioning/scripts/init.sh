#!/usr/bin/env bash
# init.sh — provision the current repo with the mise-versioning workflow.
#
# Idempotent. Safe to re-run. Run from anywhere inside the target repo.
#
#   init.sh [--force] [--seed X.Y.Z] [--no-git-tag]
#
#   --force       Overwrite an existing .mise/version-files.conf manifest.
#   --seed VER    Initial version when the repo has none anywhere (default 0.1.0).
#   --no-git-tag  Do not add a `gittag` entry to the manifest.
#
# Produces, in the repo root:
#   .mise/scripts/versioning.sh    all versioning logic (the single source)
#   .mise/version-files.conf       discovered version-bearing files (review this)
#   mise.toml                      version[:bump-*|:check|:sync] tasks (managed block)
# and wraps any mise `build` task to depend on version:bump-patch.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS="$SCRIPT_DIR/../assets"
FORCE=0; SEED="0.1.0"; WITH_GITTAG=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --seed) SEED="${2:?}"; shift ;;
    --no-git-tag) WITH_GITTAG=0 ;;
    *) echo "init: unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"
MISE_TOML="$REPO_ROOT/mise.toml"
MANIFEST="$REPO_ROOT/.mise/version-files.conf"
say() { printf '\033[1;36m::\033[0m %s\n' "$1"; }

# --- 1. ensure mise.toml ------------------------------------------------------
if [[ ! -f "$MISE_TOML" ]]; then
  say "no mise.toml found — creating one"
  printf '# Managed by mise (https://mise.jdx.dev)\n\n' > "$MISE_TOML"
else
  say "mise.toml present"
fi

# --- 2. install versioning.sh -------------------------------------------------
mkdir -p "$REPO_ROOT/.mise/scripts"
install -m 0755 "$ASSETS/versioning.sh" "$REPO_ROOT/.mise/scripts/versioning.sh"
say "installed .mise/scripts/versioning.sh"

# --- 3. discover version-bearing files ---------------------------------------
# Emits "<type> <path>" lines. Always returns 0 (never trips set -e).
discover() {
  local f
  # JSON manifests carrying a top-level "version"
  while IFS= read -r f; do
    if jq -e 'has("version")' "$f" >/dev/null 2>&1; then printf 'json %s\n' "${f#./}"; fi
  done < <(find . -name package.json -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null)

  # Cargo / pyproject (both read by versioning.sh; cargo guards [package].version)
  while IFS= read -r f; do printf 'cargo %s\n' "${f#./}"; done \
    < <(find . -name Cargo.toml -not -path '*/target/*' -not -path '*/.git/*' 2>/dev/null)
  while IFS= read -r f; do
    if grep -qE '^version[[:space:]]*=' "$f" 2>/dev/null; then printf 'toml %s\n' "${f#./}"; fi
  done < <(find . -name pyproject.toml -not -path '*/.git/*' -not -path '*/.venv/*' 2>/dev/null)

  # .NET / Gradle
  while IFS= read -r f; do
    if grep -qE '<Version>' "$f" 2>/dev/null; then printf 'csproj %s\n' "${f#./}"; fi
  done < <(find . -name '*.csproj' -not -path '*/.git/*' 2>/dev/null)
  while IFS= read -r f; do
    if grep -qE '^[[:space:]]*version[[:space:]]*[=]?[[:space:]]*["'\'']' "$f" 2>/dev/null; then
      printf 'gradle %s\n' "${f#./}"
    fi
  done < <(find . \( -name build.gradle -o -name build.gradle.kts \) -not -path '*/.git/*' 2>/dev/null)

  # Plain VERSION files
  for f in VERSION VERSION.txt version.txt; do
    if [[ -f "$f" ]]; then printf 'plain %s\n' "$f"; fi
  done
  return 0
}

if [[ -f "$MANIFEST" && $FORCE -eq 0 ]]; then
  say "manifest exists (.mise/version-files.conf) — keeping it; pass --force to regenerate"
else
  say "discovering version-bearing files…"
  {
    echo "# mise-versioning manifest: <type> <path>"
    echo "# types: json toml cargo csproj gradle plain gittag"
    discover | sort -u || true
    if [[ $WITH_GITTAG -eq 1 ]] && git rev-parse --git-dir >/dev/null 2>&1; then
      echo "gittag ."
    fi
  } > "$MANIFEST"
  grep -v '^#' "$MANIFEST" | sed 's/^/    /' || true
fi

ENTRIES="$(grep -vcE '^[[:space:]]*(#|$)' "$MANIFEST" || true)"
if [[ "${ENTRIES:-0}" -eq 0 ]]; then
  say "no version files discovered — seeding a root VERSION file at $SEED"
  printf '%s\n' "$SEED" > "$REPO_ROOT/VERSION"
  { grep -v '^gittag' "$MANIFEST" 2>/dev/null; echo "plain VERSION";
    [[ $WITH_GITTAG -eq 1 ]] && git rev-parse --git-dir >/dev/null 2>&1 && echo "gittag ."; } \
    > "$MANIFEST.tmp" && mv "$MANIFEST.tmp" "$MANIFEST"
fi

# --- 4. merge the mise tasks block (idempotent) ------------------------------
if grep -q '# >>> mise-versioning >>>' "$MISE_TOML"; then
  say "refreshing mise-versioning task block"
  sed -i '/# >>> mise-versioning >>>/,/# <<< mise-versioning <<</d' "$MISE_TOML"
  sed -i -e :a -e '/^\n*$/{$d;N;ba}' "$MISE_TOML"  # trim trailing blank lines
fi
printf '\n' >> "$MISE_TOML"
cat "$ASSETS/version-tasks.toml" >> "$MISE_TOML"
say "merged version tasks into mise.toml"

# --- 5. resolve parity (highest wins) ----------------------------------------
VSH="$REPO_ROOT/.mise/scripts/versioning.sh"
if "$VSH" check >/dev/null 2>&1; then
  say "all versioned files already in parity ($("$VSH" current))"
else
  say "files out of parity — syncing all up to the highest version"
  "$VSH" sync >/dev/null
  say "synced to $("$VSH" current)"
fi

# --- 6. wrap a mise build task to bump patch first ---------------------------
if grep -qE '^\[tasks\.("?build"?)\]' "$MISE_TOML"; then
  if awk '
      /^\[tasks\.("?build"?)\]/{inb=1; next}
      /^\[/{inb=0}
      inb && /version:bump-patch/{found=1}
      END{exit !found}' "$MISE_TOML"; then
    say "build task already depends on version:bump-patch"
  elif awk '
      /^\[tasks\.("?build"?)\]/{inb=1; print; print "depends = [\"version:bump-patch\"]"; next}
      /^\[/{inb=0}
      inb && /^depends[[:space:]]*=/{print "# NOTE: add \"version:bump-patch\" to the depends below"; print; next}
      {print}' "$MISE_TOML" > "$MISE_TOML.tmp"; then
    mv "$MISE_TOML.tmp" "$MISE_TOML"
    say "wrapped mise build task -> depends on version:bump-patch (review if it already had a depends list)"
  fi
else
  say "no mise [tasks.build] found — if this repo builds via npm/pnpm/make/etc., wrap it manually (see SKILL.md)"
fi

say "done. Try:  mise run version   |   mise run version:bump-patch"
