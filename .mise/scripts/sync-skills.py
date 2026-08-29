#!/usr/bin/env python3
"""
sync-skills.py — manifest-driven skill fanout.

Projects the `skills[]` entries and the `packs[]` members declared by the global
and project `.agents/skills.json` manifests into every supported agent CLI
skills directory.  Replaces the old symlink-based skillex monolithic fanout.
"""

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlparse

DEFAULT_REGISTRY = "https://github.com/delorenj/skillex.git"

# The supported agent CLI skill directories, per scope (relative to home for
# `--scope global`, to the project root for `--scope project`).  Exactly six
# CLIs are supported; opencode uses a different path per scope.
CLI_SKILL_DIRS = {
    "global": [
        ".claude/skills",
        ".codex/skills",
        ".gemini/skills",
        ".copilot/skills",
        ".config/opencode/skills",
        ".kimi-code/skills",
    ],
    "project": [
        ".claude/skills",
        ".codex/skills",
        ".gemini/skills",
        ".copilot/skills",
        ".opencode/skills",
        ".kimi-code/skills",
    ],
}

# Directories this engine used to write to.  They are never written to any more
# and never auto-deleted; `--prune-retired` opts in to removing ONLY managed
# symlinks left behind inside them.
RETIRED_CLI_SKILL_DIRS = [
    ".augment/skills",
    ".hermes/skills",
    ".openclaw/skills",
    ".kimi/skills",
    ".crush/skills",
    ".cursor/skills",
]

# `~/.hermes/skills` is a writable Hermes runtime OVERLAY, not a projection of
# this manifest.  It is never written to, never reported, and never pruned.
NEVER_PRUNE_DIRS = {".hermes/skills"}

# The single managed projection every CLI skills directory may alias.
MANAGED_SKILLS_RELATIVE = (".agents", "skills")

# The canonical identifier shape the contract mandates for pack and skill names
# (section 1): lowercase alphanumerics and dashes, no leading/trailing dash.
CANONICAL_NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")

# Canonical pack identifier shape.  Enforced as a WARNING so packs that predate
# the convention stay resolvable; the hard requirement (one safe path
# component) is enforced by validate_skill_name().
PACK_NAME_PATTERN = CANONICAL_NAME_PATTERN


class PackUnavailable(Exception):
    """The pack (or a declared member of it) is simply not installed here.

    Only this failure class is downgraded to a warning by `"optional": true`.
    Integrity failures — symlinks in the payload, path escapes, identity
    mismatches, checksum mismatches — always raise and are never suppressed.
    """


# --------------------------------------------------------------------------- #
# Which repo does this script own?
#
# A mise ENTER hook runs with cwd set to the directory the user cd'd into, not
# to config_root -- and that is true for a PARENT config's hook too, so entering
# 33GOD/pjangler fired 33GOD's copy of this script with cwd=pjangler. It then
# loaded pjangler's manifest and rewrote pjangler's .agents/ and CLI skill dirs.
# `mise run <task>` DOES run at config_root, which is why the cwd assumption
# looked correct for years: only the enter-hook path was ever wrong.
#
# So the subject is taken explicitly, defaulting to $MISE_CONFIG_ROOT (mise
# exports it per hook, correctly), and it must match the root this script file
# actually lives in. A repo-local script never acts on cwd, and never on a
# sibling.
# --------------------------------------------------------------------------- #


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sync skills from manifest to agent CLIs."
    )
    parser.add_argument(
        "--scope",
        choices=["global", "project"],
        required=True,
        help="Whether to sync global skills or project-local skills.",
    )
    parser.add_argument(
        "--prune-retired",
        action="store_true",
        help=(
            "Remove managed symlinks left behind in retired CLI skill "
            "directories.  Without this flag they are only reported."
        ),
    )
    parser.add_argument(
        "--no-reconcile",
        action="store_true",
        help=(
            "Keep managed projection links this sync did not declare.  By "
            "default a projection is reconciled: a symlink into a managed "
            "registry root that no declared skill or pack accounts for is "
            "removed, because leaving it is what turns a projection into "
            "sediment (81 of pjangler's 132 links were dangling)."
        ),
    )
    parser.add_argument(
        "--root",
        default=os.environ.get("MISE_CONFIG_ROOT") or None,
        help=(
            "Project root this sync owns; defaults to $MISE_CONFIG_ROOT.  Never "
            "cwd: a parent mise config's enter hook runs with cwd set to the "
            "child directory you entered, so cwd names a sibling repo."
        ),
    )
    return parser.parse_args()


def own_root():
    """The repo this script file belongs to: <root>/.mise/scripts/<this>."""
    return pathlib.Path(__file__).resolve().parents[2]


def resolved_project_root(args):
    mine = own_root()
    if args.scope != "project":
        return mine
    if not args.root:
        raise SystemExit(
            "sync-skills: --root (or $MISE_CONFIG_ROOT) is required for "
            "--scope project; refusing to infer the subject repo from cwd"
        )
    requested = pathlib.Path(args.root).resolve(strict=True)
    if requested != mine:
        raise SystemExit(
            f"sync-skills: refusing to act on {requested}; this script belongs "
            f"to {mine}.  A nested repo must ship its own .mise/scripts copy."
        )
    return requested


def load_manifest(manifest_path):
    if not manifest_path.exists():
        return {"skills": []}
    with open(manifest_path, "r") as handle:
        return json.load(handle)


def validate_skill_name(name):
    if not isinstance(name, str) or not name:
        raise ValueError("Skill name must be a non-empty string")
    if name in {".", ".."} or Path(name).is_absolute():
        raise ValueError(f"Unsafe skill name: {name!r}")
    if "/" in name or "\\" in name or Path(name).name != name:
        raise ValueError(f"Skill name must be one path component: {name!r}")
    return name


def manifest_skill_name(skill):
    if isinstance(skill, str):
        path = skill if "/" in skill else f"all-skills/{skill}"
        return validate_skill_name(path.split("/")[-1])
    if not isinstance(skill, dict):
        raise ValueError(f"Skill entry must be a string or object: {skill!r}")
    return validate_skill_name(skill.get("name"))


def validate_manifest_skill_names(manifest):
    skills = manifest.get("skills", [])
    if not isinstance(skills, list):
        raise ValueError("Manifest skills must be an array")
    for skill in skills:
        manifest_skill_name(skill)


def validate_manifest_packs(manifest):
    """Normalize + validate every `packs[]` entry without touching the disk."""
    packs = manifest.get("packs", [])
    if packs is None:
        return []
    if not isinstance(packs, list):
        raise ValueError("Manifest packs must be an array")
    return [normalize_pack_entry(entry) for entry in packs]


def assert_real_directory_chain(root, target):
    root = root.resolve(strict=True)
    target = target.absolute()
    try:
        relative = target.relative_to(root)
    except ValueError as error:
        raise ValueError(f"Destination escapes root {root}: {target}") from error
    current = root
    for part in relative.parts:
        current = current / part
        if not current.exists() and not current.is_symlink():
            break
        if current.is_symlink():
            raise ValueError(f"Refusing symlinked destination directory: {current}")
        if not current.is_dir():
            raise ValueError(f"Destination parent is not a directory: {current}")


def cli_skill_dirs(scope):
    try:
        return CLI_SKILL_DIRS[scope]
    except KeyError as error:
        raise ValueError(f"Unknown scope: {scope!r}") from error


def managed_skills_dir(base):
    return base.joinpath(*MANAGED_SKILLS_RELATIVE)


def lexical_symlink_target(link):
    """Lexically expand a symlink WITHOUT resolving it.

    Resolving an arbitrary directory symlink here would let the cleanup below
    traverse outside the project (or through a broken target) before failing.
    """
    raw_target = Path(os.readlink(link))
    lexical = raw_target if raw_target.is_absolute() else link.parent / raw_target
    return Path(os.path.normpath(str(lexical)))


def assert_nonrecursive_skill_link(destination, source):
    """Reject a link that would point from inside a skill back to that skill.

    A repository may legitimately be the source of a globally distributed
    skill.  When fanout runs inside that same repository, however, projecting
    ``<repo>/.claude/skills/<name> -> <repo>`` creates an unbounded filesystem
    cycle for every symlink-following walker.  Compare the lexical destination
    against the resolved source so the check also catches a catalog alias that
    points at the repository root.

    The one safe equality is an existing real directory in the shared managed
    projection.  That directory is already in its final location and the
    caller preserves it instead of creating a symlink.
    """
    destination = Path(destination).absolute()
    source = Path(source).resolve(strict=True)
    if destination == source and is_real_directory(destination):
        return
    try:
        destination.relative_to(source)
    except ValueError:
        return
    raise ValueError(
        "Refusing recursive skill symlink: destination "
        f"{destination} is inside its resolved source {source}"
    )


def assert_nonrecursive_skill_topology(active_cli_dirs, skill_sources):
    """Validate every proposed source/destination pair before any mutation."""
    for _cli_dir, expected_cli in active_cli_dirs:
        for name, source in skill_sources.items():
            assert_nonrecursive_skill_link(expected_cli / validate_skill_name(name), source)


def preflight_cli_dirs(
    cli_dirs_base,
    skill_names,
    scope="project",
    skill_sources=None,
):
    # Re-validate here rather than trusting the caller: this is the guard that
    # decides where mutations may land, and `expected_cli / ".."` would satisfy
    # the containment check below on its own.
    skill_names = [validate_skill_name(name) for name in skill_names]
    base = cli_dirs_base.resolve(strict=True)
    active = []
    claimed = set()

    def assert_destinations_contained(expected_cli):
        for name in skill_names:
            destination = expected_cli / name
            if destination.parent != expected_cli or len(destination.relative_to(expected_cli).parts) != 1:
                raise ValueError(f"Skill destination escapes CLI directory: {destination}")

    def add_target(cli_dir, expected_cli):
        assert_destinations_contained(expected_cli)
        # Every CLI that aliases `.agents/skills` names the SAME destination.
        # Project into it once; a second pass would only churn its own links.
        if expected_cli in claimed:
            return
        claimed.add(expected_cli)
        active.append((cli_dir, expected_cli))

    for cli_rel_path in cli_skill_dirs(scope):
        cli_dir = base / cli_rel_path
        parent = cli_dir.parent
        if not parent.exists() and not parent.is_symlink():
            continue
        assert_real_directory_chain(base, parent)
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError(f"Unsafe CLI destination parent: {parent}")
        if cli_dir.is_symlink():
            # Generated projects intentionally expose the single managed skill
            # projection to the agent CLIs as `<cli>/skills -> .agents/skills`.
            # Accept only that exact lexical alias (relative or absolute form).
            managed_skills = managed_skills_dir(base)
            canonical_alias = lexical_symlink_target(cli_dir) == managed_skills
            if not canonical_alias:
                raise ValueError(f"Refusing symlinked CLI skills directory: {cli_dir}")
            assert_real_directory_chain(base, managed_skills)
            if (
                not managed_skills.exists()
                or managed_skills.is_symlink()
                or not managed_skills.is_dir()
            ):
                raise ValueError(
                    f"Managed skills alias target is not a real directory: {managed_skills}"
                )
            resolved_cli = cli_dir.resolve(strict=True)
            if resolved_cli != managed_skills.resolve(strict=True):
                raise ValueError(
                    f"Managed skills alias escapes managed project skills: {cli_dir}"
                )
            # The alias makes `.agents/skills` this CLI's skills directory, so
            # that IS where this CLI's projection has to land.  Skipping it
            # instead would silently drop every `skills[]` entry on a project
            # where every supported CLI is aliased -- `provision-packs.py`
            # only ever materializes pack members.
            managed_expected = managed_skills.parent.resolve(strict=True) / managed_skills.name
            # Containment first, so an escaping name is reported as an escape
            # rather than as whatever it happens to collide with.
            assert_destinations_contained(managed_expected)
            # `.agents/skills` is shared with the pack provisioner and may hold
            # real, hand-authored skill directories.  Never let the fanout
            # rmtree one of those; fail here, before anything is mutated.
            for name in skill_names:
                destination = managed_skills / name
                if not is_real_directory(destination):
                    continue
                source = skill_sources.get(name) if skill_sources is not None else None
                if source is not None and destination.resolve(strict=True) == Path(source).resolve(strict=True):
                    # A project-local skill may deliberately live in the
                    # canonical managed directory. Every supported CLI aliases
                    # this same projection, so the directory is already in its
                    # final location and must remain real.
                    continue
                if skill_sources is not None:
                    raise ValueError(
                        "Refusing to replace a real skill directory in the managed "
                        f"projection: {destination}"
                    )
            add_target(managed_skills, managed_expected)
            continue
        else:
            if cli_dir.exists() and not cli_dir.is_dir():
                raise ValueError(f"CLI skills destination is not a directory: {cli_dir}")
            real_parent = parent.resolve(strict=True)
            expected_cli = real_parent / cli_dir.name
            if cli_dir.exists() and cli_dir.resolve(strict=True) != expected_cli:
                raise ValueError(f"CLI skills directory escapes its parent: {cli_dir}")
        add_target(cli_dir, expected_cli)
    if skill_sources is not None:
        assert_nonrecursive_skill_topology(active, skill_sources)
    return active


def revalidate_cli_dir(cli_dirs_base, cli_dir, expected_cli):
    """Revalidate the complete destination chain at the mutation boundary."""
    base = cli_dirs_base.resolve(strict=True)
    assert_real_directory_chain(base, cli_dir.parent)
    if cli_dir.parent.is_symlink() or not cli_dir.parent.is_dir():
        raise ValueError(f"Unsafe CLI destination parent after preflight: {cli_dir.parent}")
    current_expected = cli_dir.parent.resolve(strict=True) / cli_dir.name
    if current_expected != expected_cli:
        raise ValueError(f"CLI destination parent changed after preflight: {cli_dir}")
    if cli_dir.is_symlink():
        raise ValueError(f"CLI skills directory changed to a symlink after preflight: {cli_dir}")
    if cli_dir.exists():
        if not cli_dir.is_dir() or cli_dir.resolve(strict=True) != expected_cli:
            raise ValueError(f"Unsafe CLI skills directory after preflight: {cli_dir}")


def ensure_cache_dir():
    cache_dir = Path(os.path.expanduser("~/.agents/.cache/skills"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def registry_cache_dir(registry_url):
    """Where a registry URL is cloned to / read back from.

    The directory NAME is a wire format shared with two other surfaces that
    address this exact directory on this exact machine:

      * skillex ``src/skillex/paths.py`` -> ``sanitize_registry_url()``
      * pjangler ``src/parity/index.ts`` -> ``registryCacheDirName()``

    If they disagree, one manifest resolves to two different checkouts on one
    machine and one of them is an unverified stale clone. This script is the
    only surface allowed to CLONE, so it owns the name and the others follow.
    Every non-alphanumeric byte becomes ``_``, so the result is always exactly
    one safe path component - no separator, no ``.``, no ``..``.

    Do not change this regex here alone.
    """
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", registry_url)
    if not safe_name:
        # Would collapse to the registries/ parent and hand back the cache dir
        # itself as if it were a checkout.
        raise ValueError(f"Registry URL has no usable cache directory name: {registry_url!r}")
    return Path(os.path.expanduser("~/.agents/.cache/registries")) / safe_name


def sync_registry(registry_url):
    cache_dir = registry_cache_dir(registry_url)

    if cache_dir.exists():
        try:
            print(f"Updating registry {registry_url}...")
            subprocess.run(
                ["git", "-C", str(cache_dir), "pull"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as error:
            print(
                f"Warning: Failed to update registry {registry_url}: "
                f"{error.stderr.decode()}",
                file=sys.stderr,
            )
    else:
        cache_dir.parent.mkdir(parents=True, exist_ok=True)
        print(f"Cloning registry {registry_url}...")
        subprocess.run(["git", "clone", registry_url, str(cache_dir)], check=True)

    return cache_dir


def sync_git_skill(name, source, version, cache_dir):
    target_dir = cache_dir / name
    if target_dir.exists():
        # Just pull if it exists
        try:
            print(f"Updating git skill {name} in cache...")
            subprocess.run(
                ["git", "-C", str(target_dir), "pull"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as error:
            print(
                f"Warning: Failed to update {name}: {error.stderr.decode()}",
                file=sys.stderr,
            )
    else:
        print(f"Cloning git skill {name} to cache...")
        subprocess.run(["git", "clone", source, str(target_dir)], check=True)

    if version:
        subprocess.run(
            ["git", "-C", str(target_dir), "checkout", version], check=True
        )

    return target_dir


def resolve_skill_path(
    skill, cache_dir, base_dir, default_registry, registry_roots
):
    if isinstance(skill, str):
        path = skill if "/" in skill else f"all-skills/{skill}"
        name = validate_skill_name(path.split("/")[-1])
        skill = {"name": name, "registry_path": path}

    name = validate_skill_name(skill.get("name"))

    if "registry_path" in skill:
        registry_url = skill.get("registry", default_registry)
        # Walk the same stable, memoized checkout ladder as packs[]. A path
        # absent from the cache may legitimately exist in the developer
        # checkout; existing checkouts are never fetched as a side effect.
        attempted = []
        for root in registry_root_candidates(registry_url, registry_roots):
            full_path = root / skill["registry_path"]
            attempted.append(full_path)
            if full_path.exists():
                return name, full_path
        print(
            f"Warning: Registry skill {name} not found in: {attempted}",
            file=sys.stderr,
        )
        return name, None

    source = skill.get("source", "")
    if source.startswith("git@") or source.startswith("https://"):
        return name, sync_git_skill(
            name, source, skill.get("version"), cache_dir
        )
    parsed = urlparse(source)
    if parsed.scheme == "file":
        if parsed.netloc not in {"", "localhost"}:
            raise ValueError(f"Non-local file URI authority for skill {name}: {parsed.netloc}")
        if parsed.query or parsed.fragment:
            raise ValueError(f"file:// source must encode query/fragment characters: {source}")
        local_path = Path(unquote(parsed.path))
        full_path = (base_dir / local_path).resolve()
        if not full_path.exists():
            print(
                f"Warning: Local skill {name} not found at {full_path}",
                file=sys.stderr,
            )
            return name, None
        return name, full_path

    print(
        f"Warning: Unknown source type for skill {name}: {source}",
        file=sys.stderr,
    )
    return name, None


# --------------------------------------------------------------------------- #
# Packs
# --------------------------------------------------------------------------- #


def validate_path_component(value, label):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    if value in {".", ".."} or Path(value).is_absolute():
        raise ValueError(f"Unsafe {label}: {value!r}")
    if "/" in value or "\\" in value or Path(value).name != value:
        raise ValueError(f"{label} must be one path component: {value!r}")
    return value


def safe_relative_path(value, label):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    if "\\" in value:
        raise ValueError(f"{label} must not contain backslashes: {value!r}")
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"Unsafe {label}: {value!r}")
    return path


def manifest_entry_source_path(value):
    """The `file:` source of a `skills[]` entry as a normalized absolute path.

    LEXICAL on purpose: `os.path.abspath` normalizes without resolving symlinks,
    so this matches `provision-packs.py` and pjangler byte-for-byte. It is a pure
    predicate helper — it decides precedence, never safety, and never touches the
    filesystem. `None` for anything that is not a local `file:` source.
    """
    if not isinstance(value, dict):
        return None
    source = value.get("source")
    if not isinstance(source, str) or not source.startswith("file:"):
        return None
    try:
        parsed = urlparse(source)
        if parsed.netloc not in {"", "localhost"}:
            return None
        return Path(os.path.abspath(unquote(parsed.path)))
    except (OSError, ValueError):
        return None


def is_contained_by(root, target):
    try:
        target.relative_to(root)
    except ValueError:
        return False
    return True


class PackScope:
    """Declared-pack ownership for ONE manifest (PACKS-CONTRACT section 6).

    Section 6 pruning runs BEFORE the section 5 override: a `skills[]` entry a
    declared pack already provides is redundant, not an override. Keeping that
    decision here — and scoped to a single manifest — is what makes
    `sync-skills.py`, `provision-packs.py`, and `pj audit` resolve every name to
    the same path.

    Deliberately narrow. An entry only counts as redundant when its own resolved
    source lands inside the pack, or when it is a declared member pointing into
    another version of the same pack family. An entry pointing anywhere else — a
    local tree, a different registry, a customized copy — is the user's and is
    never pruned.
    """

    def __init__(self):
        self.roots = []
        self.family_roots = {}

    def record(self, resolved):
        """Absorb one `resolve_pack` `on_resolved` record."""
        root = resolved["root"]
        if root not in self.roots:
            self.roots.append(root)
        family_root = resolved.get("family_root")
        if family_root is not None:
            # `packs/<name>/<version>` -> `packs/<name>` is the pack family. Only
            # DECLARED names are attached: the family root is not the pack's own
            # extent, so a sibling version only shadows names this pack provides.
            # Under flatten those names are the FLATTENED ones — see
            # `resolve_pack` — which is what a `skills[]` entry would be named.
            self.family_roots.setdefault(family_root, set()).update(resolved["declared"])

    def is_redundant(self, skill_entry):
        source_path = manifest_entry_source_path(skill_entry)
        if source_path is None:
            return False
        # (a) the entry's own source lands inside a resolved pack root. Holds
        # unchanged under flatten: a hand-written entry pointing at the leaf
        # `<root>/apple/apple-notes` is contained by `<root>`, so the pack still
        # wins and the entry is still pruned.
        if any(is_contained_by(root, source_path) for root in self.roots):
            return True
        # (b) a declared member pointing into ANY version of the same pack.
        # Name lookup is TOLERANT here, matching pjangler's
        # `skillManifestEntryName`: redundancy is a precedence question, so a
        # malformed entry is simply "not redundant" rather than a hard failure.
        # The strict `validate_skill_name()` gate still runs before any symlink.
        name = skill_entry.get("name")
        if not isinstance(name, str):
            return False
        return any(
            name in members and is_contained_by(family, source_path)
            for family, members in self.family_roots.items()
        )


def normalize_pack_entry(entry):
    """String shorthand or object -> validated object form."""
    if isinstance(entry, str):
        raw = entry.strip()
        if "@" in raw:
            name, _, version = raw.partition("@")
            entry = {"name": name, "version": version}
        else:
            entry = {"name": raw}
    if not isinstance(entry, dict):
        raise ValueError(f"Pack entry must be a string or object: {entry!r}")

    normalized = dict(entry)
    name = validate_skill_name(normalized.get("name"))
    if not PACK_NAME_PATTERN.match(name):
        print(
            f"Warning: pack name {name!r} does not match the canonical "
            f"{PACK_NAME_PATTERN.pattern} shape",
            file=sys.stderr,
        )
    normalized["name"] = name

    if normalized.get("version") is not None:
        normalized["version"] = validate_path_component(
            normalized["version"], f"pack {name} version"
        )
    if normalized.get("source") and normalized.get("registry_path"):
        raise ValueError(
            f"Pack {name} may not set both `source` and `registry_path`"
        )
    if normalized.get("source") is not None and not isinstance(normalized["source"], str):
        raise ValueError(f"Pack {name} source must be a string")
    if normalized.get("registry") is not None and not isinstance(normalized["registry"], str):
        raise ValueError(f"Pack {name} registry must be a string")
    if normalized.get("registry_path") is not None:
        safe_relative_path(normalized["registry_path"], f"pack {name} registry_path")
    for key in ("include", "exclude"):
        values = normalized.get(key)
        if values is None:
            continue
        if not isinstance(values, list):
            raise ValueError(f"Pack {name} {key} must be an array of skill names")
        for value in values:
            validate_skill_name(value)
    for key in ("optional", "sealed", "flatten"):
        if key in normalized and normalized[key] is not None and not isinstance(normalized[key], bool):
            raise ValueError(f"Pack {name} {key} must be a boolean")
    return normalized


def version_sort_key(version):
    """PEP440/semver-ish ordering: numeric-segment aware, prereleases sort low."""

    def segments(text):
        parts = []
        for chunk in re.split(r"[._]", text):
            if not chunk:
                continue
            if chunk.isdigit():
                parts.append((0, int(chunk), ""))
            else:
                parts.append((1, 0, chunk))
        return tuple(parts)

    release, separator, prerelease = version.partition("-")
    return (
        segments(release),
        1 if not separator else 0,
        segments(prerelease),
    )


def read_regular_file(path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError(f"Pack entry is not a regular file: {path}")
        with os.fdopen(os.dup(descriptor), "rb") as handle:
            return handle.read()
    finally:
        os.close(descriptor)


def hash_regular_file(path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError(f"Pack entry is not a regular file: {path}")
        digest = hashlib.sha256()
        with os.fdopen(os.dup(descriptor), "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def is_real_directory(path):
    try:
        return stat.S_ISDIR(os.lstat(path).st_mode)
    except OSError:
        return False


def is_regular_file(path):
    try:
        return stat.S_ISREG(os.lstat(path).st_mode)
    except OSError:
        return False


def assert_real_pack_directory(path, label):
    try:
        mode = os.lstat(path).st_mode
    except OSError as error:
        raise PackUnavailable(f"{label} is not present: {path}") from error
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise ValueError(f"{label} must be a real directory: {path}")
    return path


def assert_no_symlink_components(root, relative):
    current = Path(root)
    for part in Path(relative).parts:
        current = current / part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError as error:
            raise PackUnavailable(f"Pack path is not present: {current}") from error
        if stat.S_ISLNK(mode):
            raise ValueError(f"Refusing symlinked pack path component: {current}")
    return current


def safe_checksum_path(value):
    path = Path(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"Unsafe checksum path: {value!r}")
    return path


def scan_children(directory):
    with os.scandir(directory) as entries:
        return sorted(entries, key=lambda item: item.name)


def registry_root_candidates(registry_url, roots_cache, allow_clone=True):
    """Existing registry checkouts for `registry_url`, in contract order.

    Candidate order is contract section 2 step 3:
      `PJ_SKILLS_REGISTRY_ROOT` | `~/.agents/.cache/registries/<sanitized-url>` |
      `~/code/skillex`.

    `packs[]` and `skills[]` share this resolver and its memo. Existing
    checkouts are never fetched: pinned packs must resolve offline and a sync
    must not mutate a checkout merely by reading it. When no checkout exists,
    this script may clone the registry once because it is the only surface
    authorized to do so.
    """
    if registry_url in roots_cache:
        return roots_cache[registry_url]

    def adopt(candidate):
        try:
            if candidate.is_dir():
                return candidate.resolve(strict=True)
        except OSError:
            pass
        return None

    override = os.environ.get("PJ_SKILLS_REGISTRY_ROOT", "").strip()
    if override:
        pinned = adopt(Path(override).expanduser())
        if pinned is None:
            raise PackUnavailable(
                f"Explicit registry checkout is not available for {registry_url}: {override}"
            )
        roots_cache[registry_url] = [pinned]
        return roots_cache[registry_url]

    roots = []
    for candidate in (registry_cache_dir(registry_url), Path(os.path.expanduser("~/code/skillex"))):
        existing = adopt(candidate)
        if existing is not None and existing not in roots:
            roots.append(existing)

    if not roots and allow_clone:
        try:
            roots.append(sync_registry(registry_url).resolve(strict=True))
        except (subprocess.CalledProcessError, OSError) as error:
            raise PackUnavailable(
                f"No registry checkout available for {registry_url}: {error}"
            ) from error

    if not roots:
        raise PackUnavailable(f"No registry checkout available for {registry_url}")
    roots_cache[registry_url] = roots
    return roots


def registry_root(registry_url, roots_cache, allow_clone=True):
    """Compatibility helper for callers that need the first checkout only."""
    return registry_root_candidates(registry_url, roots_cache, allow_clone)[0]


def select_pack_version(pack_dir):
    """Highest version subdirectory, or None when this is not a version layout.

    "Only subdirectories" is necessary but NOT sufficient.  A pack.toml-less
    `packs/<name>/` whose children are REAL directories that each hold a regular
    SKILL.md satisfies that test and is emphatically not a version layout -- it
    is a flat pack, and the contract section 3 glob inventory applies instead.
    The discriminator is what those children ARE: a child holding a regular
    SKILL.md is a skill, so its parent cannot be a version root.  Contrast
    `packs/bmad/`, also pack.toml-less and also all real directories, but whose
    children (1.2.0-next.3/, 1.3.0/) hold no top-level SKILL.md -- that IS a
    version layout and the highest version is selected.

    `packs/Kurzgesagt/` is NOT an example of this: its twelve children are all
    symlinks, so it is disqualified one check earlier by the S_ISDIR-on-lstat
    test below and never reaches the SKILL.md test.  (Earlier revisions of this
    comment cited it as "twelve skill directories"; that was wrong.)
    """
    versions = []
    for entry in scan_children(pack_dir):
        if entry.name.startswith("."):
            continue
        if not stat.S_ISDIR(entry.stat(follow_symlinks=False).st_mode):
            # Not a pure "only subdirectories" layout -> flat pack.
            return None
        if is_regular_file(Path(entry.path) / "SKILL.md"):
            return None
        versions.append(entry.name)
    if not versions:
        return None
    return max(versions, key=version_sort_key)


def resolve_pack_root_in_registry(checkout_root, entry, registry_url):
    """Resolve one pack inside one checkout, distinguishing absence from hostility."""
    name = entry["name"]
    version = entry.get("version")
    if entry.get("registry_path"):
        relative = safe_relative_path(entry["registry_path"], f"pack {name} registry_path")
    else:
        relative = Path("packs") / name
        pack_dir = checkout_root / relative
        assert_no_symlink_components(checkout_root, relative)
        assert_real_pack_directory(pack_dir, f"Pack {name} directory")
        if version:
            relative = relative / version
        elif not is_regular_file(pack_dir / "pack.toml"):
            selected = select_pack_version(pack_dir)
            if selected is not None:
                relative = relative / selected

    root = checkout_root / relative
    assert_no_symlink_components(checkout_root, relative)
    assert_real_pack_directory(root, f"Pack {name} root")

    metadata = read_pack_metadata(root)
    attested = metadata is not None
    if metadata is not None:
        pack = metadata.get("pack", {})
        if not isinstance(pack, dict):
            raise ValueError(f"Pack {name} pack.toml [pack] must be a table")
        if pack.get("name") != name:
            raise ValueError(f"Pack {name} pack.toml declares name {pack.get('name')!r}")
        if version and pack.get("version") != version:
            raise ValueError(
                f"Pack {name} pack.toml declares version {pack.get('version')!r}, "
                f"manifest pins {version!r}"
            )
    return root, f"{registry_url}:{relative.as_posix()}", attested


def resolve_pack_root(entry, base_dir, cache_dir, registry_roots, default_registry):
    """(pack_root, description) for a normalized pack entry."""
    name = entry["name"]
    version = entry.get("version")
    source = entry.get("source")

    if source:
        if source.startswith("git@") or source.startswith("https://"):
            root = sync_git_skill(name, source, version, cache_dir)
            return assert_real_pack_directory(Path(root).absolute(), f"Pack {name} root"), source
        parsed = urlparse(source)
        if parsed.scheme != "file":
            raise ValueError(f"Unknown pack source type for {name}: {source}")
        if parsed.netloc not in {"", "localhost"}:
            raise ValueError(f"Non-local file URI authority for pack {name}: {parsed.netloc}")
        if parsed.query or parsed.fragment:
            raise ValueError(f"file:// pack source must encode query/fragment characters: {source}")
        local_path = Path(unquote(parsed.path))
        root = (base_dir / local_path).absolute()
        return assert_real_pack_directory(root, f"Pack {name} root"), source

    registry_url = entry.get("registry", default_registry)
    matches = []
    first_unavailable = None
    for checkout_root in registry_root_candidates(registry_url, registry_roots):
        try:
            matches.append(resolve_pack_root_in_registry(checkout_root, entry, registry_url))
        except PackUnavailable as error:
            if first_unavailable is None:
                first_unavailable = error
    if not matches:
        raise first_unavailable or PackUnavailable(
            f"Pack {name} is unavailable in every registry checkout for {registry_url}"
        )
    # A positively identified pack outranks a same-shaped but unattested tree;
    # contract order still breaks ties. Present-but-hostile metadata raises in
    # resolve_pack_root_in_registry and is never bypassed.
    root, description, _attested = next(
        (match for match in matches if match[2]), matches[0]
    )
    return root, description


def read_pack_metadata(root):
    try:
        raw = read_regular_file(root / "pack.toml")
    except FileNotFoundError:
        return None
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Pack metadata at {root / 'pack.toml'} does not parse: {error}") from error


def pack_flatten_enabled(metadata, entry):
    """Contract section 3b: is this pack projected through a flatten expansion?

    Enabled when EITHER `pack.toml [policy] flatten = true` OR the manifest pack
    entry sets `"flatten": true`. Layout is a property of the PACK, so pack.toml
    is the natural home; the manifest field exists for packs that ship no
    pack.toml. Neither side can turn the other OFF — this is a union, not an
    override, because a nested pack projected flat-side-up would produce
    container directories where the CLIs expect skills.

    OFF unless someone says otherwise: every pack that predates 3b keeps its
    exact section 3 inventory.
    """
    if entry.get("flatten") is True:
        return True
    policy = metadata.get("policy", {}) if isinstance(metadata, dict) else {}
    return isinstance(policy, dict) and policy.get("flatten") is True


def container_leaves(container):
    """Every skill reachable under `container`, at ANY depth (contract 3b).

    Returns `(leaves, symlinked)`, both lists of POSIX-style paths relative to
    `container`, in walk order.

    The descent rule is the whole of the expansion: descend while a node is a
    container; a node holding a regular SKILL.md IS a skill and is never
    descended into. That mirrors upstream `agent/skill_utils.py`'s
    `iter_skill_index_files`, a depth-agnostic `os.walk`, and it is why
    hermes-base's `mlops/evaluation/lm-evaluation-harness` IS a member —
    `mlops/evaluation` carries only a DESCRIPTION.md, so it is another container
    and the walk continues through it.

    Stopping at the first SKILL.md on each branch is also what keeps a skill's own
    references/, scripts/, assets/ and templates/ subtree from contributing a
    second member — the same reason upstream prunes SKILL_SUPPORT_DIRS only under
    a directory that already has a SKILL.md.

    Skip rules match section 3's glob exactly, at every level. Symlinks are never
    followed, so the descent cannot cycle.

    Deliberately iterative, not recursive. Nesting depth here is a property of a
    directory tree this process did not create, and Python's recursion limit
    (~1000 frames) is FAR below the depth a filesystem accepts — PATH_MAX allows
    roughly 2000 levels of two-character segments. A recursive walk raises
    `RecursionError` on such a tree, which is a hard crash of `sync-skills.py`
    rather than a finding, and it would disagree with the two surfaces that do
    resolve it (skillex's `flatten_inventory` and pjangler's `packContainerLeaves`
    both handle it). `frames` is an explicit stack of partially-consumed child
    iterators, so it reproduces the recursive pre-order EXACTLY — a container's
    subtree is emitted in the position the container itself occupied — while the
    depth it can carry is bounded by the heap instead of the C stack.
    """
    leaves = []
    symlinked = []
    # Each frame is (prefix, iterator over that directory's sorted children).
    frames = [("", iter(scan_children(container)))]

    while frames:
        prefix, children = frames[-1]
        descended = False
        for child in children:
            if child.name.startswith(".") or child.name.startswith("_"):
                continue
            relative = f"{prefix}/{child.name}" if prefix else child.name
            mode = child.stat(follow_symlinks=False).st_mode
            if stat.S_ISLNK(mode):
                symlinked.append(relative)
                continue
            if not stat.S_ISDIR(mode):
                continue
            child_path = Path(child.path)
            # A symlinked SKILL.md is not a regular file, so the leaf is skipped.
            if is_regular_file(child_path / "SKILL.md"):
                leaves.append(relative)
                continue
            # Still a container: keep descending. Suspending THIS frame mid-iterator
            # is what preserves pre-order; the loop resumes it once the child's
            # subtree is exhausted.
            frames.append((relative, iter(scan_children(child_path))))
            descended = True
            break
        if not descended:
            frames.pop()

    return leaves, symlinked


def has_flattenable_children(directory):
    """True when a skill is reachable ANYWHERE under `directory`.

    The discriminator between "a CONTAINER of skills" and "an ordinary directory
    that happens to sit in the pack root" (docs/, assets/, ...). Used only on the
    section 3 GLOB path, where a container has to be recognized without a
    pack.toml to declare it.

    Written in terms of `container_leaves` so the glob's notion of "container" can
    never drift from what the expansion actually reaches: a directory that
    qualifies here always contributes at least one member, and one that does not
    could never have contributed any.
    """
    leaves, _ = container_leaves(directory)
    return bool(leaves)


def flatten_pack_inventory(root, name, declared):
    """Contract section 3b: expand a declared inventory by DESCENT.

    Returns an ordered list of `(projected_name, relative_path)`. The projected
    name is the LEAF basename; the relative path is where that leaf actually
    lives, which under flatten is no longer `<root>/<name>` — `apple-notes`
    resolves to `<root>/apple/apple-notes` and `vllm` to
    `<root>/mlops/inference/vllm`. The path may be ANY number of segments deep, so
    every caller has to carry the pair and never rebuild the path from the name.

    Container-level files (Hermes' `DESCRIPTION.md`) are NOT projected, at any
    level. They stay in the pack and remain part of the sealed payload, because
    the payload is still "every file under each DECLARED entry" and the container
    is what was declared. Sealing is completely unaffected by this expansion.
    """
    inventory = []
    seen = {}

    def claim(leaf_name, relative, declared_as_is=False):
        """Project one leaf.  Returns True when it was actually claimed.

        `declared_as_is` marks the one case where the name was NOT lifted off
        the filesystem: a declared entry that is already a skill keeps the
        author's string, exactly as it would without flatten.  It defaults to
        False so the canonical gate below is the fail-safe direction for any
        future call site.
        """
        if not declared_as_is and not CANONICAL_NAME_PATTERN.match(leaf_name):
            # Contract 3b.  Flatten is the ONLY place a projected skill name is
            # lifted straight off the filesystem — without it a pack.toml pack
            # projects exactly the strings its author typed into
            # `[freeform].skills`.  `validate_skill_name()` only asks for one
            # safe path component, which happily admits `-rf`, `--help`, `*`,
            # and names carrying newlines or tabs; those become argv- and
            # glob-hostile symlink names in all six CLI skill directories.
            # Skipped rather than raised so one odd upstream directory cannot
            # brick a whole pack.  `!r` keeps control characters escaped in the
            # warning itself.
            print(
                f"Warning: pack {name} leaf {leaf_name!r} at {relative} is not a canonical "
                f"skill name ({CANONICAL_NAME_PATTERN.pattern}); skipping",
                file=sys.stderr,
            )
            return False
        validate_skill_name(leaf_name)
        previous = seen.get(leaf_name)
        if previous is not None:
            # Ambiguous pack: two leaves would project onto one CLI destination,
            # and which one won would depend on inventory order. Refuse rather
            # than silently pick. (Across packs this is fine — section 5
            # precedence decides — but within ONE pack there is no rule to
            # apply.)
            raise ValueError(
                f"Pack {name} flattens to a duplicate skill name {leaf_name!r}: "
                f"{root / previous} and {root / relative}"
            )
        seen[leaf_name] = relative
        inventory.append((leaf_name, relative))
        return True

    for entry_name in declared:
        container = root / entry_name
        assert_real_pack_directory(container, f"Pack skill {entry_name}")
        if is_regular_file(container / "SKILL.md"):
            # Already a leaf. Taken as-is, exactly as without flatten — the name
            # is the author's declared string, not a filesystem basename.
            claim(entry_name, Path(entry_name), declared_as_is=True)
            continue

        # A CONTAINER. Descend it to ANY depth: the walk stops on each branch at
        # the first directory carrying a SKILL.md, so a container of containers
        # (hermes-base's `mlops/`) resolves the way upstream's depth-agnostic
        # `iter_skill_index_files` does.
        leaves, symlinked = container_leaves(container)
        for relative in symlinked:
            # Defence in depth: `walk_pack_subtree` already refuses symlinks
            # anywhere in the payload, so a symlinked leaf normally fails
            # verification before this runs.
            print(
                f"Warning: pack {name} member {entry_name}/{relative} is a symlink; skipping",
                file=sys.stderr,
            )
        contributed = 0
        for relative in leaves:
            # NAME is the leaf basename; PATH may be any number of segments deep.
            if claim(
                relative.rsplit("/", 1)[-1],
                Path(entry_name).joinpath(*relative.split("/")),
            ):
                contributed += 1
        if contributed == 0:
            # A container whose ENTIRE subtree yields no PROJECTABLE skill —
            # either it holds none at all, or every leaf it holds was rejected
            # by the canonical-name gate.  Reported, never silently dropped.
            print(
                f"Warning: pack {name} declared entry {entry_name!r} is a container "
                f"that contributes no skills",
                file=sys.stderr,
            )
    return inventory


def pack_inventory(root, name, declared, flatten):
    """The projected inventory as ordered `(name, relative_path)` pairs.

    Without flatten a member is `<root>/<name>` exactly as before; with flatten
    it is the section 3b expansion. Everything downstream — include/exclude,
    section 6 redundancy, the symlink target — consumes this one shape.
    """
    if flatten:
        return flatten_pack_inventory(root, name, declared)
    return [(item, Path(item)) for item in declared]


def pack_declared_skills(root, metadata, entry, flatten=False):
    """The full declared inventory (pre-include/exclude).

    Under flatten these are the DECLARED entries, which may be containers rather
    than skills — the section 3b expansion into projected skill names happens
    later, in `pack_inventory()`. Keeping the two apart is what leaves sealing
    untouched: the payload is defined over what is DECLARED.
    """
    name = entry["name"]
    if metadata is not None:
        pack = metadata.get("pack", {})
        if not isinstance(pack, dict):
            raise ValueError(f"Pack {name} pack.toml [pack] must be a table")
        if pack.get("name") != name:
            raise ValueError(
                f"Pack {name} pack.toml declares name {pack.get('name')!r}"
            )
        if entry.get("version") and pack.get("version") != entry["version"]:
            raise ValueError(
                f"Pack {name} pack.toml declares version {pack.get('version')!r}, "
                f"manifest pins {entry['version']!r}"
            )
        freeform = metadata.get("freeform", {})
        if not isinstance(freeform, dict):
            raise ValueError(f"Pack {name} pack.toml [freeform] must be a table")
        declared = freeform.get("skills", [])
        if not isinstance(declared, list) or not all(isinstance(item, str) for item in declared):
            raise ValueError(f"Pack {name} pack.toml [freeform].skills must be an array of strings")
        if len(set(declared)) != len(declared):
            raise ValueError(f"Pack {name} pack.toml declares duplicate skills")
        for item in declared:
            validate_skill_name(item)
        return list(declared)

    declared = []
    for child in scan_children(root):
        if child.name.startswith(".") or child.name.startswith("_"):
            continue
        mode = child.stat(follow_symlinks=False).st_mode
        if stat.S_ISLNK(mode):
            print(
                f"Warning: pack {name} member {child.name!r} is a symlink; skipping",
                file=sys.stderr,
            )
            continue
        if not stat.S_ISDIR(mode):
            continue
        if not is_regular_file(Path(child.path) / "SKILL.md"):
            # Section 3 stops here: no SKILL.md, not a skill.  Under flatten a
            # SKILL.md-less child may instead be a CONTAINER, and skipping it
            # would make the manifest's `"flatten": true` a no-op for exactly
            # the pack.toml-less packs it exists to serve.  The extra condition
            # keeps ordinary directories (docs/, assets/) out of the inventory —
            # and therefore out of the sealed payload.
            if not (flatten and has_flattenable_children(Path(child.path))):
                continue
        declared.append(validate_skill_name(child.name))
    return declared


def walk_pack_subtree(root, relative_root, files, directories):
    def visit(directory):
        for child in scan_children(directory):
            path = Path(child.path)
            relative = path.relative_to(root).as_posix()
            mode = child.stat(follow_symlinks=False).st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"Pack payload may not contain symlinks: {path}")
            if stat.S_ISDIR(mode):
                directories.add(relative)
                visit(path)
            elif stat.S_ISREG(mode):
                files[relative] = hash_regular_file(path)
            else:
                raise ValueError(
                    f"Pack payload may contain only regular files and directories: {path}"
                )

    directories.add(Path(relative_root).as_posix())
    visit(root / relative_root)


def pack_payload(root, metadata, declared, flatten=False):
    """payload = pack.toml + every file under each DECLARED skill directory.

    UNCHANGED by contract section 3b: declaring a container already covers its
    leaves recursively, so a flattened pack seals and verifies byte-for-byte the
    same as before. The one concession is the SKILL.md requirement below — under
    flatten a declared entry is allowed to be a container, and demanding a
    SKILL.md at its root would reject the very layout 3b exists to project.
    """
    files = {}
    directories = set()
    if metadata is not None:
        files["pack.toml"] = hash_regular_file(root / "pack.toml")
    for name in declared:
        skill_dir = root / name
        assert_real_pack_directory(skill_dir, f"Pack skill {name}")
        if not flatten and not is_regular_file(skill_dir / "SKILL.md"):
            raise PackUnavailable(
                f"Pack skill {name} is missing a regular SKILL.md: {skill_dir}"
            )
        walk_pack_subtree(root, name, files, directories)
    return files, directories


def parse_checksums(root):
    raw = read_regular_file(root / "SHA256SUMS")
    expected = {}
    for line in raw.decode("utf-8").splitlines():
        if not line:
            continue
        digest, separator, value = line.partition("  ")
        if (
            separator != "  "
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            raise ValueError(f"Invalid SHA256SUMS entry in {root}: {line}")
        relative = safe_checksum_path(value).as_posix()
        if relative in expected:
            raise ValueError(f"Duplicate SHA256SUMS entry in {root}: {relative}")
        expected[relative] = digest
    return expected


def verify_sealed_pack(root, files, directories):
    expected = parse_checksums(root)

    missing = sorted(set(files) - set(expected))
    if missing:
        raise ValueError(
            f"Pack payload at {root} is not covered by SHA256SUMS: {missing[:5]}"
        )
    for relative, digest in files.items():
        if expected[relative] != digest:
            raise ValueError(f"Pack digest mismatch at {root}: {relative}")

    for relative, digest in sorted(expected.items()):
        if relative in files:
            continue
        path = safe_checksum_path(relative)
        try:
            assert_no_symlink_components(root, path)
            actual = hash_regular_file(root / path)
        except (FileNotFoundError, PackUnavailable) as error:
            # `assert_no_symlink_components` reports an absent component as
            # PackUnavailable.  Inside a seal it is nothing of the sort: rule 3
            # says a checksummed path may not be absent, so this is an
            # integrity failure and must never be `optional`-suppressed.
            raise ValueError(
                f"SHA256SUMS at {root} references a missing path: {relative}"
            ) from error
        if actual != digest:
            raise ValueError(f"Pack digest mismatch at {root}: {relative}")

    covered = set()
    for relative in files:
        parts = relative.split("/")
        for index in range(1, len(parts)):
            covered.add("/".join(parts[:index]))
    unauthenticated = sorted(directory for directory in directories if directory not in covered)
    if unauthenticated:
        raise ValueError(
            f"Pack at {root} contains unauthenticated empty directories: {unauthenticated[:5]}"
        )


def verify_pack(root, metadata, declared, sealed, flatten=False):
    """Structural validation always; checksum verification when sealed.

    A seal is a COMPLETENESS claim: the pack asserts that exactly this payload,
    and every path its SHA256SUMS names, is present with these digests.  So a
    sealed pack that is missing a declared skill, a SKILL.md, or a checksummed
    file has failed integrity verification -- it is not "an uninstalled pack".
    Nothing raised from here while `sealed` may therefore be a PackUnavailable,
    because that class (and only that class) is what `"optional": true`
    downgrades to a warning in resolve_pack().
    """
    try:
        files, directories = pack_payload(root, metadata, declared, flatten=flatten)
        if metadata is not None:
            payload_files = metadata.get("source", {}).get("payload_files")
            if isinstance(payload_files, int):
                actual = sum(1 for relative in files if relative != "pack.toml")
                if actual != payload_files:
                    raise ValueError(
                        f"Pack at {root} declares {payload_files} payload files but has {actual}"
                    )
        if sealed:
            if not is_regular_file(root / "SHA256SUMS"):
                raise ValueError(f"Sealed pack at {root} has no regular SHA256SUMS")
            verify_sealed_pack(root, files, directories)
    except PackUnavailable as error:
        if not sealed:
            # Unsealed packs get structural validation only, and a missing
            # member there really is "not installed here" -- still optional.
            raise
        raise ValueError(
            f"Sealed pack at {root} failed integrity verification: {error}"
        ) from error
    return files


def resolve_pack(
    entry,
    cache_dir,
    base_dir,
    default_registry,
    registry_roots,
    managed_roots,
    on_resolved=None,
):
    """Resolve one normalized pack entry to an ordered list of (name, path).

    `on_resolved`, when given, is called once per pack that resolved AND
    verified, with a record describing WHERE the pack came from:

        {"name", "root", "family_root", "declared"}

    `root` is the exact pack root (e.g. `packs/bmad/1.3.0`); `family_root` is
    `packs/bmad` when the pack lives under a version directory, else None. The
    two are reported SEPARATELY on purpose: a sibling version under the same
    family root is NOT this pack, so callers must never treat the family root
    as the pack's own extent. `declared` is the full inventory before
    include/exclude, so a caller can tell "this pack provides that name" from
    "some other version of this pack does".

    Under flatten (contract 3b) `declared` carries the FLATTENED names, because
    that is what the pack PROVIDES and section 6 clause (b) asks what a pack
    provides. The container names it was declared with are an implementation
    detail of the pack's on-disk layout, and no `skills[]` entry is ever named
    after one. Section 6 clause (a) is unaffected: a leaf at
    `<root>/apple/apple-notes` is still contained by `<root>`.

    Returned paths are LEAF paths and are no longer necessarily `<root>/<name>`.
    """
    name = entry["name"]
    optional = bool(entry.get("optional", False))
    try:
        root, description = resolve_pack_root(
            entry, base_dir, cache_dir, registry_roots, default_registry
        )

        family_root = root.parent if root.parent.name == name else None
        managed_roots.add(root)
        if family_root is not None:
            # `packs/<name>/<version>` -> the whole family is a managed root.
            managed_roots.add(family_root)

        metadata = read_pack_metadata(root)
        flatten = pack_flatten_enabled(metadata, entry)
        declared = pack_declared_skills(root, metadata, entry, flatten=flatten)

        sealed = bool(entry.get("sealed", False))
        policy = metadata.get("policy", {}) if isinstance(metadata, dict) else {}
        if isinstance(policy, dict) and policy.get("sealed") is True:
            # The manifest may only TIGHTEN: `sealed: false` cannot disable this.
            sealed = True

        verify_pack(root, metadata, declared, sealed, flatten=flatten)
        # Expansion runs INSIDE the try, and strictly after verification: an
        # integrity check must never be gated on how a pack is projected, and a
        # member that vanished between the two is `optional`-suppressible here
        # exactly as it is above.
        inventory = pack_inventory(root, name, declared, flatten)
    except PackUnavailable as error:
        if optional:
            print(f"Warning: optional pack {name} skipped: {error}", file=sys.stderr)
            return []
        raise ValueError(f"Pack {name} could not be resolved: {error}") from error

    provided = [item for item, _relative in inventory]
    if on_resolved is not None:
        on_resolved(
            {
                "name": name,
                "root": root,
                "family_root": family_root,
                "declared": list(provided),
            }
        )

    # include/exclude apply AFTER expansion, to the FLATTENED names (contract
    # 3b): a manifest names the skills it wants, and under flatten a container
    # name is not one of them.
    members = list(inventory)
    include = entry.get("include")
    if include is not None:
        wanted = set(include)
        unknown = sorted(wanted - set(provided))
        if unknown:
            print(
                f"Warning: pack {name} include names not in inventory: {unknown}",
                file=sys.stderr,
            )
        members = [item for item in members if item[0] in wanted]
    exclude = entry.get("exclude")
    if exclude:
        unwanted = set(exclude)
        members = [item for item in members if item[0] not in unwanted]

    print(
        f"pack {name}"
        + (f"@{entry['version']}" if entry.get("version") else "")
        + f" -> {root} "
        f"({len(members)}/{len(inventory)} skill(s), "
        f"{'sealed' if sealed else 'unsealed'}, "
        + (f"flattened from {len(declared)} declared entries, " if flatten else "")
        + f"via {description})"
    )
    return [
        (validate_skill_name(item), root / relative) for item, relative in members
    ]


# --------------------------------------------------------------------------- #
# Retired directories
# --------------------------------------------------------------------------- #


def default_managed_roots():
    roots = set()
    for candidate in (
        Path(os.path.expanduser("~/.agents/.cache")),
        Path(os.path.expanduser("~/code/skillex")),
    ):
        try:
            if candidate.is_dir():
                roots.add(candidate.resolve(strict=True))
        except OSError:
            continue
    override = os.environ.get("PJ_SKILLS_REGISTRY_ROOT", "").strip()
    if override:
        try:
            roots.add(Path(override).expanduser().resolve(strict=True))
        except OSError:
            pass
    return roots


def is_inside_managed_root(target, managed_roots):
    for root in managed_roots:
        try:
            Path(target).relative_to(root)
            return True
        except ValueError:
            continue
    return False


def handle_retired_dirs(cli_dirs_base, managed_roots, prune=False):
    base = cli_dirs_base.resolve(strict=True)
    candidates = []
    for cli_rel_path in RETIRED_CLI_SKILL_DIRS:
        if cli_rel_path in NEVER_PRUNE_DIRS:
            continue
        retired = base / cli_rel_path
        if not retired.exists() and not retired.is_symlink():
            continue
        assert_real_directory_chain(base, retired.parent)
        if retired.is_symlink():
            print(
                f"sync-skills: retired {retired} is a symlink; leaving it alone",
                file=sys.stderr,
            )
            continue
        if not retired.is_dir():
            continue
        real_retired = retired.resolve(strict=True)
        if real_retired != retired.parent.resolve(strict=True) / retired.name:
            raise ValueError(f"Retired skills directory escapes its parent: {retired}")
        for child in scan_children(real_retired):
            if not stat.S_ISLNK(child.stat(follow_symlinks=False).st_mode):
                continue
            target = os.path.realpath(child.path)
            if not is_inside_managed_root(target, managed_roots):
                continue
            candidates.append((Path(child.path), target))

    if not candidates:
        return 0

    if not prune:
        print(
            f"sync-skills: {len(candidates)} managed symlink(s) remain in retired "
            f"CLI skill dirs under {base}; re-run with --prune-retired to remove them:"
        )
        for link, target in candidates:
            print(f"  would prune {link} -> {target}")
        return 0

    pruned = 0
    for link, target in candidates:
        parent = link.parent
        assert_real_directory_chain(base, parent)
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError(f"Retired skills parent changed after preflight: {parent}")
        try:
            mode = os.lstat(link).st_mode
        except FileNotFoundError:
            continue
        if not stat.S_ISLNK(mode):
            raise ValueError(f"Retired entry is no longer a symlink: {link}")
        os.unlink(link)
        pruned += 1
        print(f"pruned {link} -> {target}")
    print(f"sync-skills: pruned {pruned} retired symlink(s) under {base}")
    return pruned


# --------------------------------------------------------------------------- #
# Fanout
# --------------------------------------------------------------------------- #


def reconcile_projection(real_cli_dir, skills_map, managed_roots):
    """Remove managed projection links this sync does not account for.

    `fanout_to_cli` only ever added and overwrote. Nothing removed a link, so a
    projection was a monotonically growing record of every skill the repo ever
    declared: rename a skill, retire a pack, or move a registry cache and the
    old link stayed forever, dangling. Measured on the reporting machine: 81 of
    pjangler's 132 `.claude/skills` links pointed at BMAD pack versions that no
    longer exist, and a hand-planted broken link -- including one whose name IS
    a declared entry -- survived a re-run untouched.

    Deliberately narrow. Only a SYMLINK is ever removed, and only when its
    LEXICAL target (never a resolved one -- resolving a hostile link would walk
    outside the project first) lies inside a managed registry root. So:

      - a real directory is never touched: that is BMAD's installer output in
        `<cli>/skills`, or a hand-authored skill in `.agents/skills`;
      - a link pointing anywhere outside the managed roots is the operator's
        own and is left alone;
      - a pack member survives, because `skills_map` already contains every
        name the declared packs resolved to before fanout runs.
    """
    removed = []
    try:
        entries = sorted(os.listdir(real_cli_dir))
    except OSError:
        return removed
    for name in entries:
        if name in skills_map:
            continue
        candidate = real_cli_dir / name
        if not candidate.is_symlink():
            continue
        try:
            target = lexical_symlink_target(candidate)
        except OSError:
            continue
        dangling = not candidate.exists()
        # A DANGLING link is removed wherever it points. It names a skill and
        # resolves to nothing, so it cannot be serving anyone, and the managed-root
        # test would miss exactly the ones that hurt most: the relics of a retired
        # intermediate hop. `<repo>/.claude/skills/hindsight ->
        # 33GOD/skills/hindsight` outlived that farm entry and is not inside any
        # registry root, so it would have rotted here forever. A link that still
        # resolves is only removed inside a managed root, where this engine is the
        # only writer.
        if not dangling and not is_inside_managed_root(target, managed_roots):
            continue
        state = "dangling" if dangling else "undeclared"
        candidate.unlink()
        removed.append((candidate, target, state))
        print(f"✗ {candidate} ({state} -> {target})")
    return removed

def fanout_to_cli(
    cli_dirs_base,
    skills_map,
    active_cli_dirs=None,
    before_mutation=None,
    scope="project",
    managed_roots=None,
    reconcile=True,
):
    """
    Creates symlinks in each of the supported CLI skill dirs relative to
    cli_dirs_base pointing to the resolved paths in skills_map.
    """
    skill_names = [validate_skill_name(name) for name in skills_map]
    if active_cli_dirs is None:
        active_cli_dirs = preflight_cli_dirs(
            cli_dirs_base,
            skill_names,
            scope,
            skill_sources=skills_map,
        )
    if skill_names and not active_cli_dirs:
        # A sync that resolves skills but has nowhere to put them has FAILED.
        # Reporting success here is how a topology change silently unprojects
        # every skill; make it loud instead.
        raise ValueError(
            f"No supported agent CLI skills directory exists under {cli_dirs_base}; "
            f"refusing to silently drop {len(skill_names)} skill(s): "
            f"{sorted(skill_names)[:5]}"
        )
    if before_mutation is not None:
        before_mutation()
    linked_total = 0
    for cli_dir, expected_cli in active_cli_dirs:
        revalidate_cli_dir(cli_dirs_base, cli_dir, expected_cli)
        if not cli_dir.is_symlink():
            cli_dir.mkdir(parents=True, exist_ok=True)
        revalidate_cli_dir(cli_dirs_base, cli_dir, expected_cli)
        real_cli_dir = expected_cli.resolve(strict=True)

        for name, actual_path in skills_map.items():
            revalidate_cli_dir(cli_dirs_base, cli_dir, expected_cli)
            symlink_target = real_cli_dir / name
            if symlink_target.parent != real_cli_dir:
                raise ValueError(f"Skill destination escapes CLI directory: {symlink_target}")
            assert_nonrecursive_skill_link(symlink_target, actual_path)

            # A project-local source may already be the exact destination in
            # the shared `.agents/skills` projection. Preserve that real
            # directory; replacing it with a self-referential symlink would
            # destroy the source.
            if (
                is_real_directory(symlink_target)
                and symlink_target.resolve(strict=True) == Path(actual_path).resolve(strict=True)
            ):
                continue

            # If it's a symlink already pointing to the right place, skip
            if (
                symlink_target.is_symlink()
                and os.readlink(symlink_target) == str(actual_path)
            ):
                continue

            # If it exists but is wrong, remove it
            if symlink_target.exists() or symlink_target.is_symlink():
                revalidate_cli_dir(cli_dirs_base, cli_dir, expected_cli)
                if symlink_target.is_dir() and not symlink_target.is_symlink():
                    shutil.rmtree(symlink_target)
                else:
                    symlink_target.unlink()

            revalidate_cli_dir(cli_dirs_base, cli_dir, expected_cli)
            assert_nonrecursive_skill_link(symlink_target, actual_path)
            os.symlink(actual_path, symlink_target)
            linked_total += 1
            print(f"→ {symlink_target} -> {actual_path}")

    removed_total = 0
    if reconcile and managed_roots:
        for cli_dir, expected_cli in active_cli_dirs:
            revalidate_cli_dir(cli_dirs_base, cli_dir, expected_cli)
            removed_total += len(
                reconcile_projection(
                    expected_cli.resolve(strict=True), skills_map, managed_roots
                )
            )

    print(
        f"sync-skills: {linked_total} new/updated symlink(s), "
        f"{removed_total} stale link(s) removed "
        f"across CLIs in {cli_dirs_base}"
    )


def report_global_inheritance(global_manifest_path):
    """Verify that the user scope is reachable; project NOTHING from it.

    `inherit_global: true` used to prepend the whole global manifest as layer 0
    of a PROJECT run, so every global skill was materialized as a fresh symlink
    inside every project CLI skill dir -- 38 resolvable global skills x2 present
    CLI dirs = 76 links per project, re-created on every `cd`.

    That work is dead. Every agent CLI installed on a machine like this one
    reads the user scope implicitly, and each of its global skill roots is
    already a single dir-level symlink to ~/.agents/skills:

        ~/.claude/skills ~/.codex/skills ~/.gemini/skills ~/.copilot/skills
        ~/.kimi-code/skills ~/.config/opencode/skills ~/.openclaw/skills

    One projection, N aliases -- so a global skill is visible in a project
    because the CLI inherits the user scope, not because someone copied a link
    into the repo. A project projection holds only that repo's own declared
    skills and its declared packs.

    What is left here is the check: if the user-scope alias is missing or points
    somewhere else, global skills are NOT reachable and the operator should hear
    about it rather than have this script quietly paper over it with copies.
    """
    home = Path(os.path.expanduser("~"))
    managed = managed_global_skills_dir(home)
    reachable, broken = [], []
    for cli_rel_path in cli_skill_dirs("global"):
        alias = home / cli_rel_path
        if not alias.exists() and not alias.is_symlink():
            continue
        try:
            if alias.resolve(strict=True) == managed.resolve(strict=True):
                reachable.append(cli_rel_path)
                continue
        except OSError:
            pass
        broken.append(cli_rel_path)
    # This runs from an enter hook on every `cd`, so say nothing when the user
    # scope is intact. Report only what an operator has to act on.
    if not broken and reachable:
        return
    declared = len(load_manifest(global_manifest_path).get("skills", []))
    for cli_rel_path in broken:
        print(
            f"Warning: ~/{cli_rel_path} does not resolve to {managed}; global "
            f"skills are not reachable for that CLI.  Fix the alias "
            f"(ln -sfn {managed} ~/{cli_rel_path}); do not copy links into "
            f"projects.",
            file=sys.stderr,
        )
    if not reachable:
        print(
            f"Warning: no user-scope alias of {managed} was found, so none of "
            f"the {declared} global skill(s) declared in {global_manifest_path} "
            f"are reachable from any CLI.",
            file=sys.stderr,
        )


def managed_global_skills_dir(home):
    """The single user-scope projection every global CLI root aliases."""
    return home.joinpath(*MANAGED_SKILLS_RELATIVE)

def manifest_layer(manifest_path):
    manifest = load_manifest(manifest_path)
    validate_manifest_skill_names(manifest)
    packs = validate_manifest_packs(manifest)
    return {
        "manifest": manifest,
        "packs": packs,
        "base_dir": manifest_path.parent,
        "registry": manifest.get("registry", DEFAULT_REGISTRY),
    }


def main():
    args = parse_args()

    project_root = resolved_project_root(args)
    global_manifest_path = Path(os.path.expanduser("~/.agents/skills.json"))
    project_manifest_path = project_root / ".agents" / "skills.json"

    # Destination topology is a security boundary.  Validate every active CLI
    # directory before cloning/updating registries, creating caches, or changing
    # any skill link so one unsafe/broken symlink produces zero mutation.
    #
    # Precedence, lowest to highest (contract section 5):
    #   global packs[] -> global skills[] -> project packs[] -> project skills[]
    layers = []
    if args.scope == "global":
        preflight_base = Path(os.path.expanduser("~"))
        print(f"Loading global manifest from {global_manifest_path}")
        layers.append(manifest_layer(global_manifest_path))
    else:
        preflight_base = project_root
        print(f"Loading project manifest from {project_manifest_path}")
        project_layer = manifest_layer(project_manifest_path)
        if project_layer["manifest"].get("inherit_global", False):
            report_global_inheritance(global_manifest_path)
        layers.append(project_layer)

    preflight_names = []
    for layer in layers:
        preflight_names.extend(
            manifest_skill_name(skill)
            for skill in layer["manifest"].get("skills", [])
        )
    preflight_cli_dirs(preflight_base, preflight_names, args.scope)

    cache_dir = ensure_cache_dir()

    skills_to_sync = {}  # name -> actual_path
    # ONE stable memo of registry URL -> ordered checkout roots, shared by
    # `packs[]` and `skills[]`. Existing roots are never refreshed mid-run.
    registry_roots = {}
    managed_roots = default_managed_roots()

    for layer in layers:
        # Section 6 redundancy is scoped to ONE manifest: a project `skills[]`
        # entry is weighed only against packs the project manifest declares,
        # never against the global manifest's packs.  This is exactly the scope
        # provision-packs.py and `pj audit` use, so all three surfaces resolve
        # every name to the same path.  Cross-layer precedence still comes from
        # the 1-4 ordering above, so a project pack does override a global
        # `skills[]` entry.
        pack_scope = PackScope()
        for entry in layer["packs"]:
            for name, path in resolve_pack(
                entry,
                cache_dir,
                layer["base_dir"],
                layer["registry"],
                registry_roots,
                managed_roots,
                on_resolved=pack_scope.record,
            ):
                # Later packs override earlier ones.
                skills_to_sync[name] = path
        for skill in layer["manifest"].get("skills", []):
            # Contract section 5 step 1: an entry a declared pack already
            # provides is REDUNDANT, not an override.  Dropping it here is what
            # keeps `bmad-help` from pinning itself to a stale pack version
            # while its 74 siblings follow the declared pack.
            if pack_scope.is_redundant(skill):
                print(
                    f"Skipping redundant skills[] entry {manifest_skill_name(skill)}: "
                    f"provided by a declared pack"
                )
                continue
            name, path = resolve_skill_path(
                skill,
                cache_dir,
                layer["base_dir"],
                layer["registry"],
                registry_roots,
            )
            if path:
                # Contract section 5 step 2: a surviving explicit skills[] entry
                # always overrides a pack member.
                skills_to_sync[name] = path

    managed_roots.update(
        Path(root)
        for roots in registry_roots.values()
        for root in roots
    )

    # Re-validate the full destination topology, now including every
    # pack-derived skill name, immediately before the first mutation.
    active_cli_dirs = preflight_cli_dirs(
        preflight_base,
        [validate_skill_name(name) for name in skills_to_sync],
        args.scope,
        skill_sources=skills_to_sync,
    )

    fanout_to_cli(
        preflight_base,
        skills_to_sync,
        active_cli_dirs=active_cli_dirs,
        scope=args.scope,
        managed_roots=managed_roots,
        reconcile=not args.no_reconcile,
    )

    handle_retired_dirs(preflight_base, managed_roots, prune=args.prune_retired)


if __name__ == "__main__":
    main()
