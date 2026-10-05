#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""g33 safe consumable installer for BMAD projects.

Installs the 33GOD Integration (g33) module ALONGSIDE an existing BMAD install:
- merges `_bmad/config.yaml` (YAML authoring layer) surgically (g33 section only)
- merges g33 rows into the ACTIVE help surface `_bmad/_config/bmad-help.csv`
  (falling back to legacy `_bmad/module-help.csv` when that is the installed
  surface), anti-zombie, other modules' rows preserved
- registers `[modules.g33]` in `_bmad/custom/config.toml` (team TOML layer the
  REAL upstream runtime resolver merges over base config) — only when the
  upstream resolver is present; additive merge preserves operator keys/arrays
- creates sparse team overrides in `_bmad/custom/` for every BMAD skill that
  (a) exists in the module's registry of planning/build/review surfaces and
  (b) is actually installed in the target project's skill root — using only
  customize.toml-supported keys (activation_steps_prepend/append,
  persistent_facts)

All conflicts are detected BEFORE any mutation; a rejected conflict leaves zero
mutations and exits nonzero. Operator edits are preserved on rerun; --force
re-emits managed keys while PRESERVING operator-added keys (additive, not
wholesale replace). --dry-run writes nothing. --answers consumes a JSON file
validated against the module.yaml variable table.

Supported layouts (documented): this module targets the BMAD 6.12.1-next.1
runtime layout (`_bmad/config.toml` + `_bmad/custom/config.toml` +
`_bmad/scripts/resolve_config.py` + `_bmad/_config/bmad-help.csv`). The
BMAD 6.12.0 pinned installer is YAML-manifest-only and has no TOML runtime
integration; on that layout g33 reports TOML registration explicitly
`unsupported` (inactive) and never claims an integrated active state.
PJAN-166 (YAML→TOML migration) is out of scope.

Exit codes: 0 = success (including preserved/skip outcomes and dry-run),
1 = validation/usage error, 2 = conflict (rejected before mutation) or
runtime error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g33lib as G  # noqa: E402

MODULE_ROOT = Path(__file__).resolve().parent.parent

CORE_KEYS = ("document_output_language", "output_folder", "project_name")
CORE_DEFAULTS = {
    "document_output_language": "English",
    "output_folder": "{project-root}/_bmad-output",
}

OVERRIDE_TEMPLATE = """# g33 team override for {skill} (supported customize.toml keys only).
# Sparse: scalars would replace defaults; arrays append in order.

[workflow]

activation_steps_prepend = [
  "{prepend}",
]

activation_steps_append = {append}

persistent_facts = [
  "{fact}",
]
"""

# Planning-family surfaces: emitted ONLY when the skill is actually installed
# in the target project's activation root (sparse overrides, no dead files).
PLANNING_SKILLS = ("bmad-prd", "bmad-spec", "bmad-architecture")
BUILD_SKILL = "bmad-build"
REVIEW_SKILL = "bmad-code-review"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _override_content(skill: str) -> str:
    if skill == BUILD_SKILL:
        return OVERRIDE_TEMPLATE.format(
            skill=skill,
            prepend=(
                "Consult the g33 33GOD Integration module: run its preflight "
                "and ecosystem-route before planning the build."),
            append="[]",
            fact=(
                "33GOD: run g33 preflight before build; route via g33 "
                "ecosystem-route; see modules.g33 in _bmad/custom/config.toml."),
        )
    if skill == REVIEW_SKILL:
        return OVERRIDE_TEMPLATE.format(
            skill=skill,
            prepend=(
                "Consult the g33 evidence-to-handoff separation "
                "(implemented/tested/installed/deployed/outstanding) when "
                "reviewing claims."),
            append="[]",
            fact=(
                "33GOD: reviewer must not be the implementer; check evidence "
                "paths in the handoff, see modules.g33 in "
                "_bmad/custom/config.toml."),
        )
    return OVERRIDE_TEMPLATE.format(
        skill=skill,
        prepend=(
            "Consult the g33 ecosystem owner map (assets/ecosystem-map.toml) "
            "before producing {kind} artifacts; route ownership via g33 "
            "ecosystem-route.").format(kind={
                "bmad-prd": "PRD", "bmad-spec": "spec",
                "bmad-architecture": "architecture"}.get(skill, skill)),
        append="[]",
        fact=(
            "33GOD: {kind} artifacts belong to the owning BMAD workflow; the "
            "g33 module map (modules.g33 in _bmad/custom/config.toml) records "
            "the ecosystem routing and doctrine pointer.").format(
                kind={"bmad-prd": "PRD", "bmad-spec": "spec",
                      "bmad-architecture": "architecture"}.get(skill, skill)),
    )


def _installed_skill_dirs(project_root: Path) -> dict[str, Path]:
    """Find skill dirs actually present in the project activation roots."""
    found: dict[str, Path] = {}
    for rel in (".agents/skills", "skills", "_bmad/skills"):
        root = project_root / rel
        if not root.is_dir():
            continue
        for skill in (BUILD_SKILL, REVIEW_SKILL, *PLANNING_SKILLS):
            cand = root / skill
            if cand.is_dir() and skill not in found:
                found[skill] = cand
    return found


def load_answers(path: Path | None, module: dict[str, Any]) -> dict[str, Any]:
    """Load and validate a --answers JSON file against the module variable
    table (module.yaml prompt/default keys). Unknown keys are rejected."""
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise ValueError(f"cannot read answers file {path}: {err}") from err
    if not isinstance(data, dict):
        raise ValueError("answers file must contain a JSON object")
    known: set[str] = set()
    for key, spec in module.items():
        if isinstance(spec, dict):
            known.add(key)
    unknown = sorted(set(data) - known)
    if unknown:
        raise ValueError(
            f"answers file contains unknown module variables: {unknown} "
            f"(supported: {sorted(known)})")
    return {k: v for k, v in data.items()
            if isinstance(v, (str, int, float, bool))}


def _parse_existing_yaml(text: str) -> dict[str, Any]:
    """Best-effort structural parse of the target config.yaml (subset).

    Raises ValueError on shapes we cannot safely merge into (tabs used for
    indentation, unclosed flow collections in top-level sections)."""
    for i, line in enumerate(text.splitlines()):
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise ValueError(f"tab indentation at config.yaml line {i + 1}")
    top: dict[str, Any] = {}
    current: str | None = None
    for i, line in enumerate(text.splitlines()):
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            continue
        key, rest = m.group(1), m.group(2).strip()
        if rest.startswith("[") and not _closed(rest):
            raise ValueError(
                f"unclosed flow collection at config.yaml line {i + 1}")
        if rest == "":
            current = key
            top[key] = {}
        else:
            if current is None:
                top[key] = rest
            elif isinstance(top.get(current), dict):
                top[current][key] = rest
    return top


def _closed(text: str) -> bool:
    depth = 0
    quote = None
    for ch in text:
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
    return depth <= 0


def _find_yaml_g33_shapes(text: str) -> list[tuple[int, str]]:
    """All top-level g33 key occurrences: (line_index, full_line)."""
    shapes = []
    for i, line in enumerate(text.splitlines()):
        if re.match(r"^g33\s*:", line):
            shapes.append((i, line))
    return shapes


def _toml_table_body(text: str, header: str) -> str | None:
    lines = text.splitlines()
    header_re = re.compile(r"^\s*" + re.escape(header) + r"\s*$")
    for i, line in enumerate(lines):
        if header_re.match(line):
            body = []
            for j in range(i + 1, len(lines)):
                candidate = lines[j]
                if candidate.lstrip().startswith("[") and candidate.strip():
                    break
                body.append(candidate)
            # trim trailing blank lines
            while body and not body[-1].strip():
                body.pop()
            return "\n".join(body)
    return None


def _table_code(body: str | None) -> str | None:
    if body is None:
        return None
    m = re.search(r'^\s*code\s*=\s*"([^"]*)"', body, re.MULTILINE)
    return m.group(1) if m else None


def plan_install(
    project_root: Path,
    force: bool,
    answers_path: Path | None = None,
) -> dict[str, Any]:
    """Compute the full action plan (preflight everything, mutate nothing)."""
    module = G.load_module_yaml(MODULE_ROOT / "assets" / "module.yaml")
    answers: dict[str, Any] = {}
    for var in ("ecosystem_root", "g33_output_folder"):
        spec = module.get(var)
        if isinstance(spec, dict) and "default" in spec:
            answers[var] = spec["default"]
    # --answers consumes + validates (overrides defaults)
    try:
        answers.update(load_answers(answers_path, module))
    except ValueError as err:
        return {
            "status": "error", "error": str(err),
            "actions": [], "conflicts": [], "preserved": [], "warnings": [],
        }

    bmad = project_root / "_bmad"
    resolver = bmad / "scripts" / "resolve_config.py"
    resolver_present = resolver.is_file()

    actions: list[dict[str, Any]] = []
    conflicts: list[dict[str, str]] = []
    preserved: list[dict[str, str]] = []
    warnings: list[str] = []

    if not bmad.is_dir():
        return {
            "status": "error",
            "error": f"not a BMAD project: {bmad} not found",
            "actions": [], "conflicts": [], "preserved": [], "warnings": warnings,
        }

    # ---------- prerequisite preflight: zero writes on any failure below
    # 1. malformed YAML target
    cfg_path = bmad / "config.yaml"
    cfg_text = cfg_path.read_text(encoding="utf-8") if cfg_path.exists() else ""
    if cfg_text:
        try:
            _parse_existing_yaml(cfg_text)
        except ValueError as err:
            conflicts.append({
                "path": str(cfg_path),
                "detail": f"malformed YAML authoring config: {err}",
                "remedy": "fix the YAML or remove the g33 section; installer "
                          "refuses to mutate an unparseable target",
            })
    # 2. foreign/duplicate g33 shapes in config.yaml
    shapes = _find_yaml_g33_shapes(cfg_text)
    if len(shapes) > 1:
        conflicts.append({
            "path": str(cfg_path),
            "detail": f"{len(shapes)} duplicate top-level g33 sections at "
                      f"lines {[s[0] + 1 for s in shapes]}",
            "remedy": "remove duplicate g33 sections; installer never creates them",
        })
    elif len(shapes) == 1:
        line_no, line_text = shapes[0]
        rest = line_text.split(":", 1)[1].strip()
        looks_managed = ("# managed by g33 installer" in cfg_text)
        if rest and not (rest.startswith("#")):
            conflicts.append({
                "path": str(cfg_path),
                "detail": f"foreign inline g33 value at line {line_no + 1}: "
                          f"{line_text!r}",
                "remedy": "g33 section must be a managed block; rename the "
                          "foreign key or convert it to a section",
            })
        elif rest.startswith("#") and not looks_managed:
            conflicts.append({
                "path": str(cfg_path),
                "detail": f"foreign g33 comment-only header at line "
                          f"{line_no + 1}: {line_text!r}",
                "remedy": "g33 section must be a managed block",
            })
        else:
            # bare g33: section header — foreign unless it carries the
            # managed marker inside the section body (P9 repro class)
            sect = _extract_managed_section(cfg_text)
            if sect is None or "# managed by g33 installer" not in (sect or ""):
                conflicts.append({
                    "path": str(cfg_path),
                    "detail": "foreign pre-existing g33: section "
                              "(no managed marker): "
                              + "; ".join((sect or "").strip().splitlines()[:2]),
                    "remedy": "owned by another writer; rename the foreign "
                              "key or remove the section (installer never "
                              "overwrites foreign content)",
                })

    # 3. symlinked targets (write would escape the project)
    for target in (cfg_path, bmad / "custom" / "config.toml",
                   bmad / G.HELP_CSV_ACTIVE, bmad / G.HELP_CSV_LEGACY):
        if target.is_symlink():
            conflicts.append({
                "path": str(target),
                "detail": f"target is a symlink to {target.resolve()}",
                "remedy": "installer refuses to write through symlinks; "
                          "replace with a regular file",
            })

    # 4. malformed custom/config.toml (tomllib — the real resolver's parser)
    custom_cfg = bmad / "custom" / "config.toml"
    custom_text = custom_cfg.read_text(encoding="utf-8") if custom_cfg.exists() else ""
    if custom_text:
        try:
            tomllib.loads(custom_text)
        except tomllib.TOMLDecodeError as err:
            conflicts.append({
                "path": str(custom_cfg),
                "detail": f"pre-broken custom/config.toml: {err}",
                "remedy": "fix the TOML first; the runtime resolver "
                          "(resolve_config.py) cannot load it",
            })
        else:
            existing_code = _table_code(_toml_table_body(custom_text, G.TOML_TABLE_HEADER))
            if existing_code is not None and existing_code != G.MODULE_CODE:
                conflicts.append({
                    "path": str(custom_cfg),
                    "detail": f"foreign [modules.g33] table (code="
                              f"{existing_code!r})",
                    "remedy": "owned by another module; rename or remove it",
                })

    # 5. incompatible layout: base config.toml present but unparseable
    base_cfg = bmad / "config.toml"
    if base_cfg.exists():
        try:
            tomllib.loads(base_cfg.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError) as err:
            conflicts.append({
                "path": str(base_cfg),
                "detail": f"malformed base _bmad/config.toml: {err}",
                "remedy": "repair the base runtime config before installing",
            })

    if conflicts:
        return {
            "status": "conflict",
            "module": module.get("code", G.MODULE_CODE),
            "version": str(module.get("module_version", G.MODULE_VERSION)),
            "actions": [],
            "conflicts": conflicts,
            "preserved": [],
            "warnings": warnings,
        }

    if not resolver_present:
        warnings.append(
            "absent upstream baseline: _bmad/scripts/resolve_config.py missing; "
            "TOML registration is UNSUPPORTED/INACTIVE on this layout "
            "(YAML-only registration is not an integrated active state; "
            "BMAD 6.12.0 pinned installer is YAML-manifest-only — "
            "PJAN-166 migration is out of scope)"
        )

    # ---------- config.yaml (YAML authoring layer)
    body = G.build_module_yaml_section(module, answers)
    core_additions: dict[str, str] = {}
    for key, default in CORE_DEFAULTS.items():
        if not re.search(rf"(?m)^{key}\s*:", cfg_text):
            core_additions[key] = default
    existing_g33_yaml = _extract_managed_section(cfg_text)
    new_cfg, cfg_changed = "", False
    if existing_g33_yaml is not None and not force:
        # preserve operator-edited managed values in the YAML section too:
        # keep the existing section body verbatim, re-emit only keys it lacks
        operator_keys = set()
        for ln in existing_g33_yaml.splitlines():
            m = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*:", ln)
            if m:
                operator_keys.add(m.group(1))
        additions = [ln for ln in body
                     if not (m := re.match(r"^\s*([A-Za-z0-9_.-]+)\s*:", ln))
                     or m.group(1) not in operator_keys]
        additions = [ln for ln in additions
                     if "managed by g33 installer" not in ln]
        if additions:
            merged_yaml_body = [
                ln for ln in existing_g33_yaml.splitlines() if ln.strip()
            ] + additions
            new_cfg, cfg_changed = G.replace_yaml_section(
                cfg_text, G.MODULE_CODE, merged_yaml_body)
    else:
        # no existing section (or --force): emit the managed body wholesale
        new_cfg, cfg_changed = G.replace_yaml_section(
            cfg_text, G.MODULE_CODE, body)
    if cfg_changed or core_additions:
        final_cfg = new_cfg
        if core_additions:
            prefix_lines = [f"{k}: {G.render_yaml_scalar(v)}" for k, v in core_additions.items()]
            existing_lines = final_cfg.splitlines()
            insert_at = 0
            for idx, line in enumerate(existing_lines):
                if line.strip() and not line.startswith((" ", "#")):
                    insert_at = idx
                    break
            else:
                insert_at = len(existing_lines)
            existing_lines[insert_at:insert_at] = prefix_lines
            final_cfg = "\n".join(existing_lines)
            if not final_cfg.endswith("\n"):
                final_cfg += "\n"
        detail = "section g33 rewritten" if cfg_changed else "section g33 unchanged"
        if core_additions:
            detail += f"; core keys added (absent): {sorted(core_additions)}"
        actions.append({
            "path": str(cfg_path), "action": "write",
            "detail": detail,
            "new_sha256": sha256_text(final_cfg),
            "_new_content": final_cfg,
        })
    else:
        actions.append({"path": str(cfg_path), "action": "already-present",
                        "detail": "g33 section current; no core keys to add"})

    # ---------- help CSV: ACTIVE surface _bmad/_config/bmad-help.csv first
    active_help = bmad / G.HELP_CSV_ACTIVE
    legacy_help = bmad / G.HELP_CSV_LEGACY
    # Layout rules (documented): when the resolver-based runtime is present
    # (6.12.1-next layout) the ACTIVE surface is _bmad/_config/bmad-help.csv —
    # used even if only the legacy module-help.csv exists (rows migrate).
    # Without the runtime resolver (6.12.0 YAML-only layout), the legacy file
    # is the only surface that exists; we merge in place rather than invent
    # a dead _config tree.
    if resolver_present:
        help_target = active_help
    elif legacy_help.exists():
        help_target = legacy_help
    else:
        help_target = legacy_help  # YAML-only layout canonical name
    csv_text = help_target.read_text(encoding="utf-8") if help_target.exists() else ""
    new_csv, appended = G.merge_help_csv(csv_text, MODULE_ROOT / "assets" / "module-help.csv")
    if new_csv != csv_text:
        actions.append({
            "path": str(help_target), "action": "write",
            "detail": f"merged {len(appended)} g33 row(s) into active help "
                      f"surface {help_target.relative_to(project_root)} "
                      "(anti-zombie)",
            "new_sha256": sha256_text(new_csv),
            "_new_content": new_csv,
        })
    else:
        actions.append({"path": str(help_target), "action": "already-present",
                        "detail": "g33 rows current"})

    # ---------- custom/config.toml [modules.g33] (TOML runtime registration)
    if resolver_present:
        rows = G.build_module_toml_rows(module, answers)
        existing_body = _toml_table_body(custom_text, G.TOML_TABLE_HEADER)
        if existing_body is None:
            merged_rows = rows
        elif force:
            # additive merge: managed keys re-emitted, operator unknown
            # keys/arrays preserved (F5: --force must not drop operator keys)
            merged_rows = G.merge_toml_tables(rows, existing_body)
        else:
            # non-force: operator edits win entirely for now — managed keys
            # are re-emitted ONLY when absent; operator values are kept
            merged_rows = G.merge_toml_tables_preserving_operator(
                rows, existing_body)
        new_toml, toml_changed = G.replace_toml_table(
            custom_text, G.TOML_TABLE_HEADER, merged_rows)
        if not toml_changed:
            actions.append({"path": str(custom_cfg), "action": "already-present",
                            "detail": "[modules.g33] current"})
        else:
            note = ("register [modules.g33] in team TOML layer"
                    + (" (additive merge: operator keys preserved)"
                       if existing_body is not None else ""))
            actions.append({
                "path": str(custom_cfg), "action": "write",
                "detail": note,
                "new_sha256": sha256_text(new_toml),
                "_new_content": new_toml,
            })
            # validate output before declaring success
            try:
                tomllib.loads(new_toml)
            except tomllib.TOMLDecodeError as err:  # pragma: no cover
                return {
                    "status": "error",
                    "error": f"planned TOML output would not parse: {err}",
                    "actions": [], "conflicts": [], "preserved": preserved,
                    "warnings": warnings,
                }
    else:
        preserved.append({
            "path": str(custom_cfg),
            "reason": "skipped: upstream resolver absent (TOML registration "
                      "unsupported/inactive on this layout)",
        })

    # ---------- per-skill team overrides (sparse: installed surfaces only)
    if resolver_present:
        installed = _installed_skill_dirs(project_root)
        emitted = []
        for skill in (BUILD_SKILL, REVIEW_SKILL, *PLANNING_SKILLS):
            if skill not in installed:
                continue
            p = bmad / "custom" / f"{skill}.toml"
            content = _override_content(skill)
            emitted.append(skill)
            if not p.exists():
                actions.append({
                    "path": str(p), "action": "create",
                    "detail": f"team override for installed skill {skill} "
                              "(supported customize.toml keys)",
                    "new_sha256": sha256_text(content),
                    "_new_content": content,
                })
            elif p.read_text(encoding="utf-8") == content:
                actions.append({"path": str(p), "action": "already-present",
                                "detail": "byte-identical"})
            else:
                # additive merge for operator-edited override: preserve their
                # added array entries and unknown keys; re-emit managed ones
                merged = _merge_override_file(p.read_text(encoding="utf-8"), skill)
                if merged == content:
                    actions.append({"path": str(p), "action": "already-present",
                                    "detail": "managed override current"})
                elif force:
                    actions.append({
                        "path": str(p), "action": "overwrite",
                        "detail": "--force: managed override re-emitted "
                                  "(operator entries preserved via merge)",
                        "new_sha256": sha256_text(merged),
                        "_new_content": merged,
                    })
                else:
                    preserved.append({
                        "path": str(p),
                        "reason": "operator-edited override preserved (use --force to overwrite)",
                    })
        if not emitted:
            warnings.append(
                "no BMAD skill surfaces found in the project activation roots "
                "checked (.agents/skills, skills, _bmad/skills); no per-skill "
                "overrides emitted")
    else:
        preserved.append({
            "path": str(bmad / "custom" / f"{BUILD_SKILL}.toml"),
            "reason": "skipped: upstream resolver absent (TOML registration "
                      "unsupported/inactive on this layout)",
        })

    return {
        "status": "ok",
        "module": module.get("code", G.MODULE_CODE),
        "version": str(module.get("module_version", G.MODULE_VERSION)),
        "answers": answers,
        "actions": actions,
        "conflicts": conflicts,
        "preserved": preserved,
        "warnings": warnings,
        "toml_active": resolver_present,
    }


def _extract_managed_section(text: str) -> str | None:
    """Current g33: section body (managed shape only) or None."""
    lines = text.splitlines()
    header = re.compile(r"^g33:\s*(#.*)?$")
    for i, line in enumerate(lines):
        if header.match(line):
            body = []
            for j in range(i + 1, len(lines)):
                if not lines[j].strip() or lines[j][0] not in (" ", "\t"):
                    break
                if lines[j].strip():
                    body.append(lines[j].rstrip())
            return "\n".join(body)
    return None


def _merge_override_file(current: str, skill: str) -> str:
    """Merge a managed override over the operator's file: keeps operator-added
    array entries and unknown keys, re-emits managed template content."""
    managed = _override_content(skill)
    # collect operator extra lines inside [workflow] arrays
    op_lines: list[str] = []
    in_workflow = False
    current_key = None
    for line in current.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_workflow = stripped == "[workflow]"
            current_key = None
            continue
        if not in_workflow or not stripped or stripped.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*=", stripped)
        if m:
            current_key = m.group(1)
            continue
        if current_key in ("activation_steps_prepend", "activation_steps_append",
                           "persistent_facts") and stripped not in (
                "]", "["):
            if stripped != "]":
                op_lines.append(stripped.rstrip(","))
    if not op_lines:
        return managed
    quote = '"'
    # append operator entries to the matching arrays in the managed template
    out: list[str] = []
    key = None
    for line in managed.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*=\s*\[$", line.strip())
        if m:
            key = m.group(1)
        if line.strip() == "]" and key in (
                "activation_steps_prepend", "activation_steps_append",
                "persistent_facts"):
            for e in op_lines:
                inner = e.strip().strip(quote)
                out.append(f'  "{inner}",')
            key = None
        out.append(line)
    return "\n".join(out)


def execute_plan(plan: dict[str, Any], dry_run: bool) -> list[dict[str, Any]]:
    performed: list[dict[str, Any]] = []
    for action in plan.get("actions", []):
        if action.get("action") in ("write", "create", "overwrite"):
            path = Path(action["path"])
            performed.append({
                "path": action["path"], "action": action["action"],
                "detail": action.get("detail", ""),
                **({"new_sha256": action["new_sha256"]} if not dry_run else {}),
            })
            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(action["_new_content"], encoding="utf-8")
    return performed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Install the g33 33GOD Integration BMAD expansion module "
            "(safe, idempotent, dry-run capable)."
        )
    )
    parser.add_argument("--project-root", required=True,
                        help="Absolute project root containing _bmad/")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview only — no writes")
    parser.add_argument("--json", action="store_true",
                        help="Machine-readable output (default)")
    parser.add_argument("--answers",
                        help="JSON answers file (keys validated against "
                             "module.yaml variables)")
    parser.add_argument("--force", action="store_true",
                        help="Re-emit managed g33 content (operator keys "
                             "still preserved via additive merge)")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        G.emit_json({"status": "error",
                     "error": f"project root not found: {project_root}"})
        return 1

    answers_path = Path(args.answers).resolve() if args.answers else None
    if answers_path is not None and not answers_path.is_file():
        G.emit_json({"status": "error",
                     "error": f"answers file not found: {answers_path}"})
        return 1

    plan = plan_install(project_root, force=args.force,
                        answers_path=answers_path)
    if plan.get("status") == "error":
        G.emit_json(plan)
        return 1
    if plan.get("status") == "conflict":
        G.emit_json(plan)
        return 2

    performed = execute_plan(plan, dry_run=args.dry_run)

    result = {
        "status": "ok",
        "module": plan["module"],
        "name": G.MODULE_NAME,
        "version": plan["version"],
        "dry_run": args.dry_run,
        "answers": plan.get("answers", {}),
        "toml_active": plan.get("toml_active", False),
        "activation": "active" if plan.get("toml_active") else "inactive",
        "actions": [
            {k: v for k, v in a.items() if not k.startswith("_")}
            for a in plan["actions"]
        ],
        "performed": performed,
        "conflicts": plan["conflicts"],
        "preserved": plan["preserved"],
        "warnings": plan["warnings"],
        "exit_hint": (
            "dry-run only; re-run without --dry-run to apply"
            if args.dry_run else "applied"
        ),
    }
    G.emit_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
