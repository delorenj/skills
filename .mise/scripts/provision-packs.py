#!/usr/bin/env python3
"""Provision every Skillex pack this project declares.

Generic replacement for the retired `provision-bmad-skills.py` (PACKS-CONTRACT
section 7). It reads `.agents/skills.json`, resolves and verifies every entry in
`packs[]`, and materializes each member as a symlink under `.agents/skills/`.

Pack resolution and verification are NOT reimplemented here: they are imported
verbatim from the sibling `sync-skills.py` engine, so a pack that provisions
cleanly is a pack that syncs cleanly, with byte-identical error messages.

What this script owns is the transactional projection into the project:

  * every destination path is validated BEFORE anything is created or moved,
    and re-validated at the mutation boundary
  * `.agents` / `.agents/skills` may never be a symlink, and may never resolve
    outside the project
  * a failure at ANY point rolls the project back to its exact prior state, so
    one unsafe or tampered pack produces ZERO mutation
  * `.agents/skills.json` is rewritten atomically, preserving its mode

Only packs a project DECLARES in `packs[]` are provisioned. Nothing is pinned
implicitly -- in particular BMAD is not a pack: `bmad-method install` writes
bmad-* skills into `.agents/skills` itself, versioned per project by
`_bmad/_config/manifest.yaml`.
"""

from __future__ import annotations

import importlib.util
import json
import argparse
import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from typing import Callable

SKILLS_SCHEMA = "https://raw.githubusercontent.com/delorenj/skillex/main/skills.schema.json"
SKILLS_REGISTRY = "https://github.com/delorenj/skillex.git"

# BMAD is NOT a pack. `bmad-method install` writes bmad-* skills into
# .agents/skills itself, per project, versioned by _bmad/_config/manifest.yaml.
# This script used to pin a frozen `packs/bmad/<version>` in the registry and
# project a second copy of the same skills; when the registry dropped that pack
# the pin took every `pjangler project create` down with it on any machine
# without a warm cache. Only packs a project DECLARES are provisioned now.


def load_engine():
    """Import the sibling sync engine (its filename is not a valid module name)."""
    path = Path(__file__).resolve().parent / "sync-skills.py"
    spec = importlib.util.spec_from_file_location("skillex_sync_engine", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load the skills sync engine at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


engine = load_engine()


# --------------------------------------------------------------------------- #
# Pack selection
# --------------------------------------------------------------------------- #


def pack_root_override(name: str) -> Path | None:
    """Developer/test pin for one pack root, e.g. `PJ_PACK_ROOT_HERMES_BASE`."""
    generic = os.environ.get(f"PJ_PACK_ROOT_{re.sub(r'[^A-Z0-9]', '_', name.upper())}", "").strip()
    if generic:
        return Path(generic).expanduser().absolute()
    return None


def apply_root_override(entry: dict) -> dict:
    """Pin a declared pack at an overridden root without changing its identity."""
    if entry.get("source") or entry.get("registry_path"):
        return entry
    override = pack_root_override(entry["name"])
    if override is None:
        return entry
    pinned = dict(entry)
    pinned["source"] = override.as_uri()
    return pinned


def resolve_declared_packs(manifest: dict, base_dir: Path):
    """(declared_members, implicit_members, declared_packs, implicit_packs).

    `declared_members` are projected only; `implicit_members` are ALSO recorded
    in `skills[]` (the historical BMAD pin behaviour). Both are `name -> LEAF
    path`: under contract 3b flatten a member lives at
    `<root>/<container>/.../<name>`, at ANY depth, so the path may NOT be
    reconstructed from the name anywhere downstream.

    `declared_packs` / `implicit_packs` are one record per pack that resolved AND
    verified, keeping the pack's own root, its family root and its inventory
    SEPARATE — see `declared_pack_scope()` for why collapsing them into a flat
    root list silently deletes user skills. The records are also the ONLY
    reliable source of a pack's root now that `member.parent` is a container
    under flatten rather than the pack root.
    """
    entries = engine.validate_manifest_packs(manifest)
    default_registry = manifest.get("registry", SKILLS_REGISTRY)
    cache_dir = engine.ensure_cache_dir()
    registry_roots: dict = {}
    managed_roots = engine.default_managed_roots()

    declared_members: dict[str, Path] = {}
    declared_packs: list[dict] = []
    for entry in entries:
        members = engine.resolve_pack(
            apply_root_override(entry),
            cache_dir,
            base_dir,
            default_registry,
            registry_roots,
            managed_roots,
            on_resolved=declared_packs.append,
        )
        for name, path in members:
            # Later packs override earlier ones (contract section 5).
            declared_members[name] = path

    # Nothing is pinned implicitly any more. The empty pair is kept so every
    # caller keeps one shape and the manifest writer still evicts leftovers
    # from when something WAS pinned here.
    implicit_members: dict[str, Path] = {}
    implicit_packs: list[dict] = []
    return declared_members, implicit_members, declared_packs, implicit_packs


def declared_ownership_roots(declared_packs) -> list[Path]:
    """Roots that OWN `.agents/skills` entries planted for a declared pack.

    Ownership is deliberately WIDER than redundancy: a symlink into a sibling
    version of a declared pack is still this tool's own leftover, so the family
    root counts. Removing a manifest entry is a different, narrower question.
    """
    roots: list[Path] = []
    for pack in declared_packs:
        for root in (pack["root"], pack["family_root"]):
            if root is not None and root not in roots:
                roots.append(root)
    return roots


# --------------------------------------------------------------------------- #
# Manifest bookkeeping
# --------------------------------------------------------------------------- #


def manifest_entry_name(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        name = value.get("name")
        return name if isinstance(name, str) else None
    return None


# Imported, not re-implemented. A second copy of either helper is exactly how
# `sync-skills.py` and this script came to disagree about which pack version a
# name resolves to; there is now one definition and every surface shares it.
manifest_entry_source_path = engine.manifest_entry_source_path


def is_pack_managed_manifest_entry(value: object, expected_names: set[str], roots) -> bool:
    name = manifest_entry_name(value)
    if name is None:
        return False
    if name in expected_names:
        return True
    source_path = manifest_entry_source_path(value)
    if source_path is None or source_path.name != name:
        return False
    return any(is_contained_by(root, source_path) for root in roots)


is_contained_by = engine.is_contained_by


def declared_pack_scope(declared_packs) -> "engine.PackScope":
    """PACKS-CONTRACT section 6 redundancy for this manifest's declared packs.

    The rule itself lives in `engine.PackScope` so `sync-skills.py`, this script
    and pjangler's `isRedundantDeclaredPackEntry` cannot drift apart. It is
    deliberately narrow:

      * an entry whose resolved source lands inside the pack's OWN root is
        redundant — the pack projects it, so the hand-written entry is a
        duplicate; and
      * an entry landing in a SIBLING version of the same pack family is
        redundant ONLY when the resolved pack actually declares that name.
        Otherwise it is a skill this pack does not provide, and dropping it
        would lose it — "Never remove entries that point outside the pack."

    The family root therefore may NOT be flattened into the pack's own root:
    `packs/<name>/<other-version>/<skill>` is a different pack.
    """
    scope = engine.PackScope()
    for pack in declared_packs:
        scope.record(pack)
    return scope


# --------------------------------------------------------------------------- #
# Project destination safety
# --------------------------------------------------------------------------- #


def preflight_project_directory(project_root: Path, target: Path) -> None:
    try:
        relative = target.absolute().relative_to(project_root)
    except ValueError as error:
        raise ValueError(f"Project destination escapes {project_root}: {target}") from error
    if len(relative.parts) > 2:
        raise ValueError(f"Unexpected project skill destination depth: {target}")
    current = project_root
    for part in relative.parts:
        current = current / part
        if not current.exists() and not current.is_symlink():
            break
        if current.is_symlink():
            raise ValueError(f"Refusing symlinked project skill directory: {current}")
        if not current.is_dir():
            raise ValueError(f"Project skill parent is not a directory: {current}")


def prepare_project_skill_dirs(project_root: Path) -> tuple[Path, Path]:
    agents_dir = project_root / ".agents"
    skills_dir = agents_dir / "skills"
    # Validate the complete existing chain before creating or mutating anything.
    preflight_project_directory(project_root, agents_dir)
    preflight_project_directory(project_root, skills_dir)
    agents_dir.mkdir(exist_ok=True)
    skills_dir.mkdir(exist_ok=True)
    for path in (agents_dir, skills_dir):
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f"Unsafe project skill directory: {path}")
        resolved = path.resolve(strict=True)
        resolved.relative_to(project_root)
    return agents_dir, skills_dir


def lexical_link_target(link: Path) -> Path | None:
    if not link.is_symlink():
        return None
    target = Path(os.readlink(link))
    return (target if target.is_absolute() else link.parent / target).absolute()


def remove_entry(path: Path) -> None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return
    if stat.S_ISDIR(mode) and not stat.S_ISLNK(mode):
        shutil.rmtree(path)
    else:
        path.unlink()


def atomic_write(path: Path, content: bytes, mode: int) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


# --------------------------------------------------------------------------- #
# Provisioning
# --------------------------------------------------------------------------- #


def own_root() -> Path:
    """The repo this script file belongs to: <root>/.mise/scripts/<this>."""
    return Path(__file__).resolve().parents[2]


def resolved_project_root(requested: str | None) -> Path:
    """Resolve the repo to provision, refusing to infer it from cwd.

    A mise ENTER hook runs with cwd set to the directory the user cd'd into, not
    config_root -- including a PARENT config's hook. That is how 33GOD's copy of
    this script came to force-rewrite `pjangler/.agents/skills.json` and plant 75
    dangling pack links in `pjangler/.agents/skills`. `mise run <task>` does run
    at config_root, so the cwd assumption was only ever wrong on the hook path.
    """
    mine = own_root()
    if requested is None:
        requested = os.environ.get("MISE_CONFIG_ROOT") or None
    if requested is None:
        raise SystemExit(
            "provision-packs: --root (or $MISE_CONFIG_ROOT) is required; "
            "refusing to infer the subject repo from cwd"
        )
    resolved = Path(requested).resolve(strict=True)
    if resolved != mine:
        raise SystemExit(
            f"provision-packs: refusing to act on {resolved}; this script "
            f"belongs to {mine}.  A nested repo must ship its own "
            ".mise/scripts copy."
        )
    return resolved


def provision(
    *,
    root: str | None = None,
    after_preflight: Callable[[], None] | None = None,
    create_link: Callable[[Path, Path, int], None] | None = None,
    after_apply: Callable[[Path, Path], None] | None = None,
) -> int:
    project_root = resolved_project_root(root)
    agents_path = project_root / ".agents"
    skills_path = agents_path / "skills"
    agents_existed = agents_path.exists() or agents_path.is_symlink()
    skills_existed = skills_path.exists() or skills_path.is_symlink()

    # `.agents` is validated before the manifest inside it is read, so the read
    # can never traverse a symlink out of the project. `.agents/skills` is
    # validated by prepare_project_skill_dirs() below — after the packs are
    # resolved and verified, and still strictly before the first mutation.
    preflight_project_directory(project_root, agents_path)
    manifest_path = agents_path / "skills.json"
    if manifest_path.is_symlink():
        raise ValueError(f"Refusing symlinked skills manifest: {manifest_path}")
    if manifest_path.exists() and not manifest_path.is_file():
        raise ValueError(f"Skills manifest is not a regular file: {manifest_path}")
    manifest_existed = manifest_path.exists()
    manifest_bytes = engine.read_regular_file(manifest_path) if manifest_existed else None
    manifest_mode = stat.S_IMODE(manifest_path.lstat().st_mode) if manifest_existed else 0o644
    manifest = json.loads(manifest_bytes) if manifest_bytes is not None else {}
    if not isinstance(manifest, dict):
        raise ValueError(f"{manifest_path} must contain a JSON object")
    existing = manifest.get("skills", [])
    if not isinstance(existing, list):
        raise ValueError(f"{manifest_path} skills must be an array")

    declared_members, implicit_members, declared_packs, implicit_packs = resolve_declared_packs(
        manifest, agents_path
    )
    if after_preflight is not None:
        after_preflight()

    implicit_names = set(implicit_members)
    # From the resolve record, NOT `member.parent`: under contract 3b flatten a
    # member's parent is its container — possibly several levels below the pack
    # root — so deriving the root from a member would claim ownership of one
    # container instead of the whole pack.
    implicit_roots = {pack["root"] for pack in implicit_packs}
    declared_roots = declared_ownership_roots(declared_packs)
    declared_scope = declared_pack_scope(declared_packs)

    kept = [
        entry
        for entry in existing
        if not is_pack_managed_manifest_entry(entry, implicit_names, implicit_roots)
        and not declared_scope.is_redundant(entry)
    ]

    # Contract section 5: an explicit `skills[]` entry that SURVIVED the section 6
    # pruning always overrides a declared pack member of the same name.
    overridden = {
        name
        for name in (manifest_entry_name(entry) for entry in kept)
        if name is not None and name in declared_members
    }
    expected: dict[str, Path] = {
        name: path for name, path in declared_members.items() if name not in overridden
    }
    expected.update(implicit_members)

    agents_dir, skills_dir = prepare_project_skill_dirs(project_root)

    manifest["$schema"] = SKILLS_SCHEMA
    manifest["inherit_global"] = True
    manifest["registry"] = SKILLS_REGISTRY
    manifest["skills"] = [
        *kept,
        *[
            {"name": name, "source": implicit_members[name].as_uri()}
            for name in implicit_members
        ],
    ]
    next_manifest = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")

    ownership_roots = [*implicit_roots, *declared_roots]
    affected: list[str] = []
    stale_managed_names: set[str] = set()
    original_correct_links: dict[str, str] = {}
    managed_manifest_names = {
        name
        for entry in existing
        if is_pack_managed_manifest_entry(entry, implicit_names, ownership_roots)
        if (name := manifest_entry_name(entry)) is not None
    }
    for entry in skills_dir.iterdir():
        if entry.parent.resolve(strict=True) != skills_dir.resolve(strict=True):
            raise ValueError(f"Pack skill entry escapes skills directory: {entry}")
        engine.validate_skill_name(entry.name)
        link_target = lexical_link_target(entry)
        try:
            link_targets_pack = link_target is not None and any(
                is_contained_by(root, link_target) for root in ownership_roots
            )
        except OSError:
            link_targets_pack = False
        # PJAN-82: a DANGLING symlink here is stale by definition.
        #
        # An entry stopped being recognizable as pack-managed the moment its pack
        # declaration went away: `ownership_roots` no longer contains the pack, so
        # `link_targets_pack` is false, and the normalized manifest no longer names
        # it either — so the checks below skipped it and it stayed forever. That is
        # how momo, bloodbank and candystore each ended up with 76 links into
        # `~/.agents/.cache/registries/.../packs/bmad/6.10.1-next.31/`, a cache
        # directory that no longer exists. A link that resolves to nothing cannot be
        # a hand-authored skill and cannot be serving anyone, so it is reclaimable
        # regardless of where it points. A link that still RESOLVES is left alone
        # unless it is provably pack-managed.
        dangling_link = link_target is not None and not entry.exists()
        if (
            entry.name not in expected
            and entry.name not in managed_manifest_names
            and not link_targets_pack
            and not dangling_link
        ):
            continue
        target = expected.get(entry.name)
        if target is not None and link_target == target:
            original_correct_links[entry.name] = os.readlink(entry)
        else:
            affected.append(entry.name)
            if target is None:
                stale_managed_names.add(entry.name)
    for name, target in expected.items():
        link = skills_dir / engine.validate_skill_name(name)
        if link.parent.resolve(strict=True) != skills_dir.resolve(strict=True):
            raise ValueError(f"Pack skill destination escapes skills directory: {link}")
        if lexical_link_target(link) != target and name not in affected:
            affected.append(name)

    manifest_changed = manifest_bytes != next_manifest
    if not affected and not manifest_changed:
        return 0

    transaction = Path(tempfile.mkdtemp(prefix=".packs-transaction-", dir=agents_dir))
    backup = transaction / "entries"
    backup.mkdir()
    moved: list[str] = []

    def rollback() -> None:
        errors: list[str] = []
        try:
            for name in affected:
                remove_entry(skills_dir / engine.validate_skill_name(name))
            for name in original_correct_links:
                remove_entry(skills_dir / engine.validate_skill_name(name))
        except OSError as error:
            errors.append(f"remove applied projection: {error}")
        for name in reversed(moved):
            try:
                os.replace(backup / name, skills_dir / name)
            except OSError as error:
                errors.append(f"restore {name}: {error}")
        for name, raw_target in original_correct_links.items():
            try:
                (skills_dir / name).symlink_to(raw_target, target_is_directory=True)
            except OSError as error:
                errors.append(f"restore {name}: {error}")
        try:
            if manifest_bytes is None:
                remove_entry(manifest_path)
            else:
                atomic_write(manifest_path, manifest_bytes, manifest_mode)
        except OSError as error:
            errors.append(f"restore manifest: {error}")
        shutil.rmtree(transaction, ignore_errors=True)
        try:
            if not skills_existed and skills_dir.exists() and not any(skills_dir.iterdir()):
                skills_dir.rmdir()
            if not agents_existed and agents_dir.exists() and not any(agents_dir.iterdir()):
                agents_dir.rmdir()
        except OSError as error:
            errors.append(f"remove created directories: {error}")
        if errors:
            raise RuntimeError("Skillex pack rollback was incomplete: " + "; ".join(errors))

    link_creator = create_link or (
        lambda target, link, _index: link.symlink_to(target, target_is_directory=True)
    )
    try:
        for name in affected:
            entry = skills_dir / name
            if entry.exists() or entry.is_symlink():
                os.replace(entry, backup / name)
                moved.append(name)
        for index, (name, target) in enumerate(expected.items(), start=1):
            link = skills_dir / name
            if lexical_link_target(link) == target:
                continue
            link_creator(target, link, index)
        if manifest_changed:
            atomic_write(manifest_path, next_manifest, manifest_mode)
        # Re-validate every pack at the mutation boundary: a pack tampered with
        # after preflight must roll the whole projection back.
        postflight_declared, postflight_implicit, _, _ = resolve_declared_packs(
            manifest, agents_path
        )
        postflight = {**postflight_declared, **postflight_implicit}
        if {name: postflight.get(name) for name in expected} != expected:
            raise ValueError("Skillex pack inventory changed after preflight")
        if after_apply is not None:
            after_apply(manifest_path, skills_dir)
        for name in stale_managed_names:
            entry = skills_dir / name
            if entry.exists() or entry.is_symlink():
                raise ValueError(f"Applied pack projection retained stale managed entry: {name}")
        for name, target in expected.items():
            if lexical_link_target(skills_dir / name) != target:
                raise ValueError(f"Applied pack projection link differs from plan: {name}")
        final_mode = manifest_path.lstat().st_mode
        if (
            not stat.S_ISREG(final_mode)
            or engine.read_regular_file(manifest_path) != next_manifest
            or stat.S_IMODE(final_mode) != manifest_mode
        ):
            raise ValueError("Applied skills manifest differs from planned bytes or mode")
        final_manifest = json.loads(engine.read_regular_file(manifest_path))
        if (
            not isinstance(final_manifest, dict)
            or final_manifest.get("$schema") != SKILLS_SCHEMA
            or final_manifest.get("inherit_global") is not True
            or final_manifest.get("registry") != SKILLS_REGISTRY
            or not isinstance(final_manifest.get("skills"), list)
        ):
            raise ValueError("Applied skills manifest schema differs from plan")
    except Exception as error:
        try:
            rollback()
        except Exception as rollback_error:
            raise RuntimeError(f"Skillex pack provisioning failed ({error}); {rollback_error}") from error
        raise

    shutil.rmtree(transaction)
    return len(affected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision declared Skillex packs.")
    parser.add_argument(
        "--root",
        default=None,
        help=(
            "Project root to provision; defaults to $MISE_CONFIG_ROOT.  Never "
            "cwd -- see resolved_project_root()."
        ),
    )
    args = parser.parse_args()
    try:
        changed = provision(root=args.root)
    except (FileNotFoundError, OSError, ValueError, RuntimeError, engine.PackUnavailable) as error:
        raise SystemExit(
            f"Skillex pack provisioning failed: {error}; "
            "declare the pack in .agents/skills.json packs[] or install it locally"
        ) from error

    print(f"provision-packs: {changed} symlink(s) updated")


if __name__ == "__main__":
    main()
