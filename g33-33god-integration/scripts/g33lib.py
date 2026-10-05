#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""g33 shared library: YAML-subset reader, surgical TOML/YAML editors, CSV merge,
preflight checks, ecosystem routing, evidence-to-handoff, secret scrubbing,
canonical execution-readiness adapter (policyVersion 2), project-config loading.

Pure stdlib (Python >= 3.11, tomllib). No pyyaml, no network, no writes except
through the explicit installer entry points.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any

MODULE_CODE = "g33"
MODULE_NAME = "33GOD Integration"
MODULE_VERSION = "1.1.0"
MODULE_DIR_NAME = "g33-33god-integration"

CSV_HEADER = [
    "module", "skill", "display-name", "menu-code", "description", "action",
    "args", "phase", "after", "before", "required", "output-location", "outputs",
]
# bmb variant column order used by this repo's installed module-help.csv
CSV_HEADER_BMB = [
    "module", "skill", "display-name", "menu-code", "description", "action",
    "args", "phase", "preceded-by", "followed-by", "required",
    "output-location", "outputs",
]

_SECRET_KEY_RE = re.compile(
    r"token|secret|password|key|credential|passwd", re.IGNORECASE
)


def secret_free(value: Any) -> Any:
    """Recursively replace values whose key name looks secret-y."""
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if _SECRET_KEY_RE.search(str(k)) else secret_free(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [secret_free(item) for item in value]
    return value


def emit_json(payload: dict, path: Path | None = None) -> None:
    text = json.dumps(secret_free(payload), indent=2, ensure_ascii=False)
    if path is not None:
        path.write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")


# ---------------------------------------------------------------- YAML subset
#
# module.yaml uses a restricted subset: top-level scalar keys, quoted or bare
# strings, booleans, numbers, block scalar (`>` / `|`) values, and two-level
# variable tables (name -> {prompt/default/result/user_setting}).

_YAML_KV = re.compile(r'^([A-Za-z0-9_]+):\s*(.*)$')


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return ""
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if text in ("null", "~"):
        return None
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return json.loads(text) if text.startswith('"') else text[1:-1].replace("''", "'")
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def parse_module_yaml(text: str) -> dict[str, Any]:
    """Parse the module.yaml YAML subset into a dict (order preserved)."""
    result: dict[str, Any] = {}
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        m = _YAML_KV.match(line)
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2)
        if rest in (">", "|", ">-", "|-"):
            # block scalar: consume indented lines
            block: list[str] = []
            i += 1
            while i < n and (not lines[i].strip() or lines[i].startswith(" ")):
                block.append(lines[i])
                i += 1
            joined = "\n".join(l.rstrip() for l in block).strip("\n")
            result[key] = " ".join(joined.split()) if rest.startswith(">") else joined
            continue
        if rest == "":
            # nested table (one level)
            table: dict[str, Any] = {}
            i += 1
            while i < n and (lines[i].startswith("  ") and lines[i].strip()):
                sub = _YAML_KV.match(lines[i].strip())
                if sub:
                    table[sub.group(1)] = _parse_scalar(sub.group(2))
                i += 1
            result[key] = table
            continue
        result[key] = _parse_scalar(rest)
        i += 1
    return result


def load_module_yaml(path: Path) -> dict[str, Any]:
    return parse_module_yaml(path.read_text(encoding="utf-8"))


# --------------------------------------------- project runtime config (real)

HELP_CSV_ACTIVE = "_config/bmad-help.csv"
HELP_CSV_LEGACY = "module-help.csv"
CUSTOM_CONFIG_REL = Path("_bmad") / "custom" / "config.toml"


def load_project_config(project_root: Path) -> dict[str, Any]:
    """Load the g33 team TOML layer (custom/config.toml) if parseable.

    This is the same layer the REAL upstream resolver (resolve_config.py)
    merges; we read it directly so route/preflight consume the module config
    without shelling out. Returns {} when absent or unparsable.
    """
    path = Path(project_root) / CUSTOM_CONFIG_REL
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    module_tbl = data.get("modules", {})
    if isinstance(module_tbl, dict):
        g33 = module_tbl.get(MODULE_CODE)
        if isinstance(g33, dict):
            return dict(g33)
    return {}


def effective_config(module_root: Path, project_root: Path | None) -> dict[str, Any]:
    """Module answers effective at runtime: bundled defaults overlaid by the
    project's installed [modules.g33] answers (the layer the real resolver
    merges). Portable doctrine/output overrides come from the same table."""
    module = load_module_yaml(module_root / "assets" / "module.yaml")
    answers: dict[str, Any] = {}
    for var in ("ecosystem_root", "g33_output_folder", "doctrine_pointer"):
        spec = module.get(var)
        if isinstance(spec, dict) and "default" in spec:
            answers[var] = spec["default"]
        elif spec is not None and not isinstance(spec, dict):
            answers[var] = spec
    if project_root is not None:
        answers.update(load_project_config(project_root))
    return answers


# ------------------------------------------------------- surgical file editors

def replace_yaml_section(
    text: str, section: str, new_body_lines: list[str]
) -> tuple[str, bool]:
    """Replace (or append) a single top-level ``section:`` block in a YAML doc,
    leaving every other byte untouched. Returns (new_text, changed).
    """
    lines = text.splitlines(keepends=False)
    out: list[str] = []
    start = re.compile(rf"^{re.escape(section)}:\s*$")
    start_loose = re.compile(rf"^{re.escape(section)}:\s*#.*$")
    replaced = False
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not replaced and (start.match(line) or start_loose.match(line)):
            # skip old body (indented or blank lines)
            j = i + 1
            while j < n and (not lines[j].strip() or lines[j][0] in (" ", "\t")):
                j += 1
            out.append(f"{section}:")
            out.extend(new_body_lines)
            replaced = True
            i = j
            continue
        out.append(line)
        i += 1
    if not replaced:
        if out and out[-1].strip():
            out.append("")
        out.append(f"{section}:")
        out.extend(new_body_lines)
    new_text = "\n".join(out)
    if not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, new_text != text


def render_yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    # Quote strings consistently: YAML implicit booleans/numbers/null/dates
    # otherwise change their type while TOML retains strings.
    return json.dumps(str(value), ensure_ascii=False)


def build_module_yaml_section(module: dict[str, Any], answers: dict[str, Any]) -> list[str]:
    lines = ["  # managed by g33 installer; rerun replaces only this section"]
    for key in ("name", "description"):
        if key in module:
            lines.append(f"  {key}: {render_yaml_scalar(module[key])}")
    lines.append(f"  version: {render_yaml_scalar(module.get('module_version', MODULE_VERSION))}")
    for key in sorted(answers):
        lines.append(f"  {key}: {render_yaml_scalar(answers[key])}")
    return lines


TOML_TABLE_HEADER = "[modules.g33]"


def toml_statements(text: str) -> list[dict[str, Any]]:
    """Split validated TOML into whole statements, respecting multiline values.

    The real parser establishes statement boundaries; bracket-looking lines
    inside arrays or multiline strings cannot become synthetic table headers.
    Comments and blank lines remain individual, byte-preserved statements.
    """
    out = []
    buffer = []
    start = 0
    for index, line in enumerate(text.splitlines(keepends=True)):
        buffer.append(line)
        raw = "".join(buffer)
        try:
            parsed = tomllib.loads(raw)
        except tomllib.TOMLDecodeError:
            continue
        stripped = raw.strip()
        kind = ("table" if stripped.startswith("[") else
                "assignment" if parsed else "other")
        key = next(iter(parsed), None) if kind == "assignment" else None
        out.append({"text": raw, "kind": kind, "key": key,
                    "start": start, "end": index + 1})
        start = index + 1
        buffer = []
    if buffer:
        raise ValueError("incomplete TOML statement")
    return out


def toml_table_range(text: str, header: str) -> tuple[int, int] | None:
    statements = toml_statements(text)
    for index, item in enumerate(statements):
        if item["kind"] == "table" and item["text"].split("#", 1)[0].strip() == header:
            end = next((following["start"] for following in statements[index + 1:]
                        if following["kind"] == "table"), len(text.splitlines()))
            return item["end"], end
    return None


def toml_table_body(text: str, header: str) -> str | None:
    span = toml_table_range(text, header)
    if span is None:
        return None
    return "".join(text.splitlines(keepends=True)[span[0]:span[1]])


def replace_toml_table(
    text: str, table_header: str, new_body_lines: list[str]
) -> tuple[str, bool]:
    """Replace one parsed table body; preserve nested tables and foreign bytes."""
    span = toml_table_range(text, table_header)
    body = "\n".join(new_body_lines)
    if body and not body.endswith("\n"):
        body += "\n"
    if span is None:
        separator = "" if not text or text.endswith("\n\n") else "\n" if text.endswith("\n") else "\n\n"
        new_text = text + separator + "# g33 managed table — rerun replaces only this table\n" + table_header + "\n" + body
    else:
        lines = text.splitlines(keepends=True)
        new_text = "".join(lines[:span[0]]) + body + "".join(lines[span[1]:])
    return new_text, new_text != text


def render_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(render_toml_value(v) for v in value) + "]"
    return json.dumps(str(value), ensure_ascii=False)


def build_module_toml_rows(module: dict[str, Any], answers: dict[str, Any]) -> list[str]:
    rows = ["code = " + render_toml_value(module.get("code", MODULE_CODE)),
            "name = " + render_toml_value(module.get("name", MODULE_NAME)),
            "version = " + render_toml_value(module.get("module_version", MODULE_VERSION))]
    rows.extend(f"{key} = {render_toml_value(answers[key])}" for key in sorted(answers))
    return rows


def _toml_comments(raw: str) -> list[str]:
    """Extract comments outside quoted/multiline values before replacing a key."""
    comments = []
    quote = None
    index = 0
    while index < len(raw):
        char = raw[index]
        if quote:
            if quote.startswith('"') and char == "\\":
                index += 2
                continue
            if raw.startswith(quote, index):
                index += len(quote)
                quote = None
                continue
        elif char in ("'", '"'):
            quote = char * 3 if raw.startswith(char * 3, index) else char
            index += len(quote)
            continue
        elif char == "#":
            end = raw.find("\n", index)
            if end == -1:
                end = len(raw)
            comments.append(raw[index:end] + "\n")
            index = end
        index += 1
    return comments


def merge_toml_tables(managed_lines: list[str], operator_text: str | None) -> list[str]:
    """Replace managed assignments only; preserve comments and unknown values."""
    replacements = {item["key"]: item["text"] for item in
                    toml_statements("\n".join(managed_lines) + "\n")
                    if item["kind"] == "assignment"}
    chunks = []
    for item in toml_statements(operator_text or ""):
        if item["kind"] == "assignment" and item["key"] in replacements:
            replacement = replacements.pop(item["key"])
            # Keep the original statement byte-stable when values are unchanged.
            if tomllib.loads(item["text"]) == tomllib.loads(replacement):
                chunks.append(item["text"])
            else:
                chunks.extend(_toml_comments(item["text"]))
                chunks.append(replacement)
        else:
            chunks.append(item["text"])
    chunks.extend(replacements.values())
    return "".join(chunks).splitlines()


def merge_toml_tables_preserving_operator(
    managed_lines: list[str], operator_text: str | None
) -> list[str]:
    if not operator_text:
        return list(managed_lines)
    operator_keys = {item["key"] for item in toml_statements(operator_text)
                     if item["kind"] == "assignment"}
    absent = [item["text"] for item in toml_statements("\n".join(managed_lines) + "\n")
              if item["key"] not in operator_keys]
    return (operator_text + "".join(absent)).splitlines()


# ------------------------------------------------------------------- CSV merge

def merge_help_csv(target_text: str, source_csv_path: Path) -> tuple[str, list[dict]]:
    """Anti-zombie merge of module rows into a help CSV (bmad-help or legacy).

    Existing rows whose `module` column equals our display name are removed;
    our rows are appended (re-mapped onto the target's header variant).
    Other modules' rows and the header are preserved byte-for-byte semantics.
    Returns (new_text, appended_rows).
    """
    reader = csv.DictReader(io.StringIO(target_text)) if target_text.strip() else None
    target_header = list(reader.fieldnames or []) if reader else []
    target_rows = list(reader) if reader else []

    with source_csv_path.open("r", encoding="utf-8", newline="") as f:
        sreader = csv.DictReader(f)
        source_header = list(sreader.fieldnames or [])
        source_rows = list(sreader)

    if not target_header:
        target_header = CSV_HEADER_BMB
    module_col = "module"
    kept = [r for r in target_rows if r.get(module_col) != MODULE_NAME]
    appended: list[dict] = []
    for row in source_rows:
        mapped = {}
        for col in target_header:
            if col in ("after", "before") and col not in row:
                mapped[col] = row.get(
                    "preceded-by" if col == "after" else "followed-by", ""
                )
            elif col in ("preceded-by", "followed-by") and col not in row:
                mapped[col] = row.get(
                    "after" if col == "preceded-by" else "before", ""
                )
            else:
                mapped[col] = row.get(col, "")
        appended.append(mapped)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=target_header, lineterminator="\n")
    writer.writeheader()
    for row in kept:
        writer.writerow({col: row.get(col, "") for col in target_header})
    for row in appended:
        writer.writerow(row)
    return buf.getvalue(), appended


# ------------------------------------- canonical execution readiness (adapter)

# Ported from /home/delorenj/code/33GOD/pjangler/src/project/executionBinding.ts
# (policyVersion 2). This is an ADAPTER around the canonical contract: the
# field set mirrors executionReadiness() so g33 preflight and the canonical
# validator agree. Pure function, no state writes, no shelling out.

EXECUTION_LANES = [
    "Backlog", "Needs Re-evaluation", "Todo", "In Progress",
    "E2E Testing & QA", "Ready for Documentation", "Done",
    "Needs Attention", "Cancelled",
]
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_VALID_ROLES = {"pm", "operator", "reviewer", "interactive"}
_VALID_MODES = {"legacy", "shadow", "managed"}


def execution_readiness(manifest: dict[str, Any]) -> list[str]:
    """Canonical executionReadiness port. Returns a list of error strings
    (empty = ready). legacy/absent execution returns [] like the original."""
    execution = manifest.get("execution")
    if not execution or execution.get("mode") == "legacy":
        return []
    errors: list[str] = []
    if execution.get("mode") not in ("shadow", "managed"):
        errors.append("execution.mode must be legacy, shadow or managed")
    if not manifest.get("project_id"):
        errors.append("canonical project_id missing")
    tp = manifest.get("ticket_provider") or {}
    if (tp.get("type") != "plane" or not tp.get("workspace")
            or not tp.get("board_id")):
        errors.append("exact Plane binding missing")
    if execution.get("policy_version") != 2 or not execution.get("skill_version"):
        errors.append("execution policy or skill pin missing")
    states = execution.get("states") or {}
    for lane in EXECUTION_LANES:
        if not states.get(lane):
            errors.append(f"lane binding missing: {lane}")
    for pin in ("pilot_bundle_sha256", "momo_bundle_sha256"):
        if not _SHA256_RE.match(str(execution.get(pin) or "")):
            errors.append(f"{pin} missing")
    if not execution.get("working_label"):
        errors.append("working label binding missing")
    actors = execution.get("actors") or {}
    pm_actor = execution.get("pm_actor")
    controller = execution.get("controller_actor")
    pm = actors.get(pm_actor)
    if not pm or pm.get("role") != "pm":
        errors.append("PM actor enrollment missing")
    ctl = actors.get(controller)
    if not ctl or ctl.get("role") != "operator":
        errors.append("controller repair actor enrollment missing")
    ids: set[str] = set()
    for name, actor in (actors or {}).items():
        actor = actor or {}
        if (not actor.get("native_user_id")
                or not str(actor.get("key_ref", "")).startswith("op://")
                or not actor.get("runtime_id")):
            errors.append(
                f"actor {name}: native identity, op reference and runtime required")
        native = actor.get("native_user_id")
        if native in ids:
            errors.append(f"actor {name}: duplicate native identity")
        if native:
            ids.add(native)
        if actor.get("role") not in _VALID_ROLES:
            errors.append(f"actor {name}: invalid role")
        if name == pm_actor:
            planner = ((actor.get("runtime") or {}).get("planner_argv"))
            if (not isinstance(planner, list) or not planner
                    or any(not isinstance(x, str) or not x or "\0" in x
                           for x in planner)):
                errors.append("PM planner argv missing")
        runtime = actor.get("runtime") or {}
        if (runtime.get("adapter") != "systemd"
                or not re.match(r"^[a-zA-Z0-9_-]+$", str(runtime.get("unit_prefix") or ""))):
            errors.append(f"actor {name}: supervised runtime missing")
    if execution.get("legacy_writers_fenced") is not True:
        errors.append("legacy writers not fenced")
    return errors


def execution_mode_status(manifest: dict[str, Any]) -> str:
    """legacy|shadow|managed|invalid (invalid mode never downgrades to legacy)."""
    execution = manifest.get("execution")
    if not execution:
        return "legacy"
    mode = execution.get("mode")
    if mode in _VALID_MODES:
        return str(mode)
    return "invalid"


# ------------------------------------------------------------------ preflight

def run_preflight(project_root: Path, module_root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []

    def add(check: str, status: str, evidence: str) -> None:
        findings.append({"check": check, "status": status, "evidence": evidence})

    # 0. effective module config (consumed, not ornamental)
    config = effective_config(module_root, project_root)

    # 1. project binding
    pj = project_root / ".project.json"
    execution_status = "absent"
    manifest: dict[str, Any] = {}
    if not pj.is_file():
        add("project-binding", "FAIL", f"{pj} not found: missing ticket binding")
    else:
        try:
            manifest = json.loads(pj.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("not an object")
        except (OSError, json.JSONDecodeError, ValueError) as err:
            add("project-binding", "FAIL", f"cannot read {pj}: {err}")
            manifest = {}
        tp = manifest.get("ticket_provider") or {}
        if not tp.get("type"):
            add("project-binding", "FAIL", ".project.json has no ticket_provider.type")
        else:
            state = tp.get("state")
            missing_fields = [k for k in ("workspace", "board_id", "identifier")
                              if not tp.get(k)]
            if state == "linked" and not missing_fields:
                add("project-binding", "PASS",
                    f"ticket_provider {tp.get('type')} linked "
                    f"(workspace={tp.get('workspace')!r}, board_id present)")
            elif state == "linked":
                add("project-binding", "WARN",
                    f"ticket_provider {tp.get('type')} linked but missing "
                    f"{missing_fields}")
            else:
                add(
                    "project-binding", "WARN",
                    f"ticket_provider {tp.get('type')} state={state!r} (not linked)",
                )
        # 2. Krebs enrollment via the canonical adapter
        execution = manifest.get("execution")
        mode = (execution or {}).get("mode") if isinstance(execution, dict) else None
        if isinstance(execution, dict) and execution:
            execution_status = execution_mode_status(manifest)
            if execution_status == "legacy":
                add("krebs-enrollment", "WARN",
                    "execution.mode=legacy (explicit) — legacy adapter mode")
            elif execution_status == "invalid":
                add("krebs-enrollment", "FAIL",
                    f"execution.mode={mode!r} invalid (must be "
                    "legacy|shadow|managed) — not downgraded to legacy")
            elif execution_status == "managed":
                errors = execution_readiness(manifest)
                if errors:
                    add("krebs-enrollment", "FAIL",
                        "managed execution not ready (canonical "
                        f"executionReadiness): {'; '.join(errors)}")
                else:
                    add("krebs-enrollment", "PASS",
                        "mode=managed, canonical readiness satisfied "
                        f"({len((execution.get('actors') or {}))} actor(s))")
            else:  # shadow
                errors = execution_readiness(manifest)
                if errors:
                    add("krebs-enrollment", "WARN",
                        "mode=shadow — incremental enrollment allowed, NOT "
                        f"managed-ready: {'; '.join(errors[:5])}"
                        + (" …" if len(errors) > 5 else ""))
                else:
                    add("krebs-enrollment", "PASS",
                        "mode=shadow, canonical readiness fields complete "
                        "(shadow performs no mutations; does not certify "
                        "managed readiness)")
        else:
            execution_status = "legacy"
            add("krebs-enrollment", "WARN",
                "execution key absent — legacy adapter mode")

    # 3. tool availability
    for tool in ("px", "node", "uv", "python3"):
        found = shutil.which(tool)
        if found:
            add("tool-" + tool, "PASS", found)
        else:
            add("tool-" + tool, "WARN", f"{tool} not found on PATH")

    # 4. module + BMAD structure
    if (module_root / "SKILL.md").is_file() and (
        module_root / "assets" / "ecosystem-map.toml"
    ).is_file():
        add("module-files", "PASS", str(module_root))
    else:
        add("module-files", "FAIL", f"module incomplete at {module_root}")
    bmad_dir = project_root / "_bmad"
    if bmad_dir.is_dir():
        add("bmad-structure", "PASS", str(bmad_dir))
    else:
        add("bmad-structure", "FAIL", f"{bmad_dir} not found")
    resolver = bmad_dir / "scripts" / "resolve_config.py"
    if resolver.is_file():
        add("bmad-resolver", "PASS", str(resolver))
    else:
        add("bmad-resolver", "WARN", f"{resolver} not found (absent upstream baseline)")

    has_fail = any(f["status"] == "FAIL" for f in findings)
    return {
        "status": "FAIL" if has_fail else "PASS",
        "execution_mode": execution_status,
        "config": config,
        "findings": findings,
    }


# -------------------------------------------------------------------- routing

ROUTE_KEYWORDS: dict[str, list[str]] = {
    "execution": ["execute", "implement", "build", "code", "story", "dev", "fix", "bug"],
    "story_breakdown": ["breakdown", "epic", "child board", "stories", "split"],
    "analysis": ["analyze", "analysis", "plan", "spec", "architecture", "prd", "research"],
    "templates_deployment": ["template", "deploy", "provision", "release"],
    "skills": ["skill", "skillex", "pack", "agentpack"],
    "runtime": ["runtime", "supervise", "daemon", "profile", "hermes"],
    "event_naming": ["event", "naming", "bloodbank", "nats", "webhook"],
    "operational_evidence": ["evidence", "candystore", "context", "history", "session"],
    "ui": ["ui", "dashboard", "holocene", "display", "status page"],
    "project_provisioning": ["provision", "new project", "registry", "pjangler", "bootstrap"],
    "code_review": ["review", "reviewer", "audit code", "pr review"],
}


def load_ecosystem_map(module_root: Path) -> dict[str, Any]:
    with (module_root / "assets" / "ecosystem-map.toml").open("rb") as f:
        return tomllib.load(f)


def classify_route(request: str) -> list[str]:
    text = request.lower()
    scores: dict[str, int] = {}
    for route, words in ROUTE_KEYWORDS.items():
        score = sum(1 for w in words if w in text)
        if score:
            scores[route] = score
    ordered = sorted(scores, key=lambda r: -scores[r])
    if not ordered:
        return ["analysis"]
    return ordered


def ecosystem_route(
    module_root: Path, request: str, project_root: Path | None = None
) -> dict[str, Any]:
    cmap = load_ecosystem_map(module_root)
    config = effective_config(module_root, project_root)
    routes = classify_route(request)
    out_routes = []
    for r in routes:
        node = cmap.get("routes", {}).get(r)
        if not node:
            continue
        out_routes.append({
            "route": r,
            "label": node.get("label", ""),
            "owner": node.get("owner", ""),
            "entrypoint": node.get("entrypoint", ""),
            "notes": node.get("notes", ""),
        })
    meta = cmap.get("meta", {})
    # doctrine pointer: portable project override wins over the bundled default
    doctrine_pointer = config.get("doctrine_pointer") or meta.get(
        "doctrine_pointer", "momo/PILLARS.md")
    return {
        "request": request,
        "routes": out_routes,
        "ecosystem_root": config.get("ecosystem_root"),
        "g33_output_folder": config.get("g33_output_folder"),
        "doctrine": {
            "pointer": doctrine_pointer,
            "pillars": cmap.get("doctrine", {}).get("pillars", {}),
            "source": "project-config" if "doctrine_pointer" in config else "bundled-map",
        },
        "event_naming": {
            "contract": meta.get("event_naming_contract", ""),
            "shape": meta.get("event_type_shape", ""),
        },
    }


# --------------------------------------------------------- evidence to handoff

REQUIRED_BUNDLE_KEYS = ("acceptance_criteria", "worker_claims", "diff_path",
                        "test_proof_path")

_TEST_COUNT_ITEM = r"[0-9]+\s+(?:passed|failed|errors?|skipped|deselected|xfailed|xpassed|warnings?|rerun)"
_TEST_SUMMARY_RE = re.compile(
    rf"(?P<counts>{_TEST_COUNT_ITEM}(?:\s*,\s*{_TEST_COUNT_ITEM})*)"
    r"(?:\s+in\s+[0-9]+(?:\.[0-9]+)?s(?:\s+\([0-9]+:[0-9]{2}:[0-9]{2}\))?)?",
    re.IGNORECASE)
_TEST_COUNT_RE = re.compile(r"([0-9]+)\s+([a-z]+)", re.IGNORECASE)
_TEST_COUNT_MENTION_RE = re.compile(_TEST_COUNT_ITEM, re.IGNORECASE)
_MARKDOWN_FENCE_RUN_RE = re.compile(r"(?:\x60{3,}|~{3,})")
_EXIT_CODE_RE = re.compile(
    r"^\s*(?:command_)?exit(?:_code)?\s*[=:]\s*(-?\d+)\s*$",
    re.IGNORECASE | re.MULTILINE)


def _test_summary_counts(line: str) -> dict[str, int] | None:
    """Complete plain/pytest count summaries; never substring prose counts."""
    summary = line.strip()
    if summary.startswith("=") or summary.endswith("="):
        wrapped = re.fullmatch(r"={2,}\s*(.+?)\s*={2,}", summary)
        if not wrapped:
            return None
        summary = wrapped.group(1)
    parsed = _TEST_SUMMARY_RE.fullmatch(summary)
    if not parsed:
        return None
    counts = {}
    for count, label in _TEST_COUNT_RE.findall(parsed["counts"]):
        label = {"error": "errors", "warning": "warnings"}.get(label.lower(), label.lower())
        if label in counts:
            return None
        counts[label] = int(count)
    return counts


def parse_test_proof(text: str) -> dict[str, Any]:
    """Parse a test-proof log for pass/fail counts and exit codes.

    Supports N passed/failed/errors textual summaries with explicit exit-code
    markers after each command's summary. Unsupported, incomplete or ambiguous
    formats are unverified. Proof is plain/raw output: any Markdown delimiter
    run of three or more backticks/tildes anywhere makes it ambiguous, including
    nested/inline/control-adjacent or unterminated forms. This validates recorded
    output, not its provenance."""
    passed = failed = errors = 0
    exits = [int(m.group(1)) for m in _EXIT_CODE_RE.finditer(text)]
    # Each summary starts its own proof block. Only markers following that
    # summary, before the next summary, can attest its command exit. Duplicate
    # markers within A never cover a missing marker in B; stray/pre-summary
    # markers are ambiguous and cannot certify a run.
    blocks = []
    current = None
    ambiguous = bool(_MARKDOWN_FENCE_RUN_RE.search(text))
    marker_prefix = re.compile(r"^\s*(?:command_)?exit(?:_code)?\s*[=:]", re.IGNORECASE)
    note_header = re.compile(
        r"^\s*(?:#{1,6}\s*)?(?:expected|example|sample)"
        r"(?:\s+(?:output|result|summary))?\s*[:=]?\s*$", re.IGNORECASE)
    for line in text.splitlines():
        counts = _test_summary_counts(line)
        is_boundary = bool(re.match(r"^\s*(?:block\b|command\s*:|\$\s)", line, re.IGNORECASE))
        if note_header.fullmatch(line) or _MARKDOWN_FENCE_RUN_RE.search(line):
            ambiguous = True
            current = None
        if counts is not None:
            passed += counts.get("passed", 0)
            failed += counts.get("failed", 0)
            errors += counts.get("errors", 0)
            current = {"summary": line, "counts": counts, "exit_codes": [], "malformed": False}
            blocks.append(current)
        elif _TEST_COUNT_MENTION_RE.search(line):
            # Unsupported count-bearing text cannot add counts or disappear
            # silently next to a supported summary in a purported result log.
            ambiguous = True
            current = None
        elif is_boundary:
            current = None
        if marker_prefix.match(line):
            parsed = _EXIT_CODE_RE.fullmatch(line)
            if current is None:
                ambiguous = True
            elif parsed is None:
                current["malformed"] = True
            else:
                current["exit_codes"].append(int(parsed.group(1)))
    exits_complete = bool(blocks) and not ambiguous and all(
        block["exit_codes"] and not block["malformed"]
        and all(code == 0 for code in block["exit_codes"]) for block in blocks)
    recognizable = bool(blocks)
    return {
        "recognized": recognizable,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "exit_codes": exits,
        "blocks": blocks,
        "clean_pass": bool(
            recognizable and passed > 0 and not failed and not errors
            and exits_complete and all(e == 0 for e in exits)
        ),
    }


_DIFF_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$")


def parse_diff_evidence(text: str) -> dict[str, Any]:
    """Validate supported textual unified patches with exact hunk counts.

    Binary, combined and metadata-only changes are explicit unsupported proof,
    never success. This parses a recorded patch; it does not attest provenance
    or apply it to a checkout. No commands from evidence are executed.
    """
    lines = text.splitlines()
    changed = set()
    files = hunks = additions = deletions = 0

    def fail(reason):
        return {"valid": False, "reason": reason, "changed_paths": sorted(changed),
                "files": files, "hunks": hunks, "additions": additions, "deletions": deletions}

    def path_from_header(line):
        raw = line[4:].split("\t", 1)[0]
        if raw == "/dev/null":
            return None
        if raw.startswith('"'):
            raw = json.loads(raw)
        if raw.startswith(("a/", "b/")):
            raw = raw[2:]
        if not raw or raw.startswith("/") or ".." in raw.split("/") or "\x00" in raw:
            raise ValueError("unsupported absolute/escaping/empty diff path")
        return raw

    index = 0
    pending_git_file = False
    while index < len(lines):
        line = lines[index]
        if not line:
            index += 1
            continue
        if line.startswith("diff --git "):
            if pending_git_file:
                return fail("metadata-only/binary change is unsupported")
            pending_git_file = True
            index += 1
            continue
        if re.match(r"^(?:index [0-9a-f]+\.\.[0-9a-f]+(?: \d+)?|(?:new file|deleted file|old|new) mode \d+)$", line):
            if not pending_git_file:
                return fail("orphan Git metadata")
            index += 1
            continue
        if not line.startswith("--- "):
            return fail(f"unsupported/malformed patch content at line {index + 1}")
        if index + 1 >= len(lines) or not lines[index + 1].startswith("+++ "):
            return fail("old file header lacks matching new file header")
        try:
            old_path = path_from_header(line)
            new_path = path_from_header(lines[index + 1])
        except (ValueError, TypeError):
            return fail("invalid/unsupported patch path")
        if old_path is None and new_path is None:
            return fail("both patch paths are /dev/null")
        pending_git_file = False
        index += 2
        file_hunks = 0
        last_old_end = last_new_end = -1
        while index < len(lines) and lines[index].startswith("@@"):
            match = _DIFF_HUNK_RE.fullmatch(lines[index])
            if not match:
                return fail(f"malformed hunk header at line {index + 1}")
            old_start, old_count, new_start, new_count = (
                int(match.group(1)), int(match.group(2) or 1),
                int(match.group(3)), int(match.group(4) or 1))
            if (old_start < last_old_end or new_start < last_new_end
                    or (old_start == 0 and old_count) or (new_start == 0 and new_count)):
                return fail("invalid/overlapping hunk coordinates")
            last_old_end, last_new_end = old_start + old_count, new_start + new_count
            index += 1
            seen_old = seen_new = 0
            changed_here = False
            while index < len(lines) and (seen_old < old_count or seen_new < new_count):
                body = lines[index]
                if body == "\\ No newline at end of file":
                    if not (seen_old or seen_new):
                        return fail("orphan no-newline marker")
                    index += 1
                    continue
                if not body or body[0] not in " +-":
                    return fail(f"truncated/invalid hunk body at line {index + 1}")
                marker = body[0]
                if marker in " -": seen_old += 1
                if marker in " +": seen_new += 1
                if marker == "+": additions += 1; changed_here = True
                if marker == "-": deletions += 1; changed_here = True
                if seen_old > old_count or seen_new > new_count:
                    return fail("hunk body exceeds declared line counts")
                index += 1
            if seen_old != old_count or seen_new != new_count:
                return fail("hunk body does not match declared line counts")
            if not changed_here:
                return fail("hunk contains no changed lines")
            while index < len(lines) and lines[index] == "\\ No newline at end of file":
                index += 1
            file_hunks += 1
            hunks += 1
        if not file_hunks:
            return fail("file headers have no supported changed hunk")
        files += 1
        changed.update(p for p in (old_path, new_path) if p is not None)
    if pending_git_file or not files:
        return fail("no supported complete textual file patch")
    return {"valid": True, "reason": "supported unified patch parsed",
            "changed_paths": sorted(changed), "files": files, "hunks": hunks,
            "additions": additions, "deletions": deletions}


def link_claim_evidence(bundle: dict[str, Any], changed_paths: list[str]) -> dict[str, dict[str, Any]]:
    """Validate declared claim→known AC→parsed path links, not semantic acceptance."""
    claims = bundle.get("worker_claims") or []
    criteria = bundle.get("acceptance_criteria") or []
    links = bundle.get("claim_evidence") or []
    if not isinstance(links, list):
        return {}
    out, duplicates, seen = {}, set(), set()
    for link in links:
        if not isinstance(link, dict):
            continue
        claim = link.get("claim")
        acs, paths = link.get("acceptance_criteria"), link.get("diff_paths")
        valid = (isinstance(claim, str) and claim in claims and isinstance(acs, list)
                 and bool(acs) and all(isinstance(ac, str) and ac in criteria for ac in acs)
                 and isinstance(paths, list) and bool(paths)
                 and all(isinstance(path, str) and path in changed_paths for path in paths))
        if isinstance(claim, str):
            if claim in seen:
                duplicates.add(claim)
            seen.add(claim)
        if valid:
            out[claim] = link
    return {claim: link for claim, link in out.items() if claim not in duplicates}


def inspect_evidence_path(value: Any) -> dict[str, Any]:
    """Stat+hash a claimed evidence path. Never invents success."""
    if not value or not isinstance(value, str):
        return {"path": str(value), "exists": False, "status": "missing"}
    p = Path(value)
    if not p.exists():
        return {"path": value, "exists": False, "status": "missing"}
    if not p.is_file():
        return {"path": value, "exists": True, "status": "not-a-file"}
    try:
        data = p.read_bytes()
    except OSError as err:
        return {"path": value, "exists": True, "status": f"unreadable: {err}"}
    if not data.strip():
        return {"path": value, "exists": True, "size": 0,
                "sha256": hashlib.sha256(data).hexdigest(),
                "status": "empty"}
    return {"path": value, "exists": True, "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "status": "ok"}


def inspect_state_receipt(bundle: dict[str, Any], state: str) -> dict[str, Any]:
    """Validate a separate state receipt; test/diff evidence proves no install/deploy.

    Checks are recorded observations, not commands executed by this handoff.
    Schema/hash validity does not establish provenance or target reachability.
    Every supplied state receipt remains recorded-unverified.
    """
    value = bundle.get(f"{state}_evidence_path")
    evidence = inspect_evidence_path(value)
    evidence["recorded_claims"] = []
    if evidence["status"] != "ok":
        return evidence
    path = Path(value).resolve()
    unrelated = ("diff_path", "test_proof_path", f"{'deployed' if state == 'installed' else 'installed'}_evidence_path")
    if any(isinstance(bundle.get(key), str) and path == Path(bundle[key]).resolve()
           for key in unrelated):
        evidence["status"] = "not-separate-state-evidence"
        return evidence
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        checks = receipt.get("checks")
        claims = receipt.get("claims")
        valid = (receipt.get("state") == state and isinstance(claims, list)
                 and all(isinstance(c, str) and c.strip() for c in claims)
                 and isinstance(checks, list) and bool(checks)
                 and all(isinstance(c, dict) and isinstance(c.get("command"), str)
                         and c["command"].strip() and type(c.get("exit_code")) is int
                         and c["exit_code"] == 0 and isinstance(c.get("observed"), str)
                         and c["observed"].strip() for c in checks))
    except (OSError, ValueError, AttributeError, TypeError):
        valid = False
    if valid:
        evidence["recorded_claims"] = claims
        evidence["status"] = "recorded-unverified"
    else:
        evidence["status"] = "invalid-state-receipt"
    return evidence


def validate_bundle(bundle: dict[str, Any]) -> list[str]:
    errors = []
    for key in REQUIRED_BUNDLE_KEYS:
        if key not in bundle:
            errors.append(f"missing required key: {key}")
    for key in ("acceptance_criteria", "worker_claims", "installed", "deployed", "outstanding", "review_notes"):
        value = bundle.get(key)
        if value is not None and (not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value)):
            errors.append(f"{key} must be an array of nonempty strings")
    if "claim_evidence" in bundle and not isinstance(bundle["claim_evidence"], list):
        errors.append("claim_evidence must be an array")
    for path_key in ("diff_path", "test_proof_path"):
        value = bundle.get(path_key)
        if value is not None and not isinstance(value, str):
            errors.append(f"{path_key} must be a path string")
    for id_key in ("implementer", "reviewer"):
        value = bundle.get(id_key)
        if value is not None and not isinstance(value, str):
            errors.append(f"{id_key} must be a string when provided")
    return errors


def _pillar_citation(module_root: Path, doctrine_pointer: str) -> str:
    try:
        cmap = load_ecosystem_map(module_root)
        pillars = cmap.get("doctrine", {}).get("pillars", {})
    except (OSError, tomllib.TOMLDecodeError):
        pillars = {}
    nums = ", ".join(f"#{i.upper().lstrip('P')} {name}" for i, name in sorted(pillars.items()))
    return f"{doctrine_pointer} — {nums}"


def generate_handoff(module_root: Path, bundle: dict[str, Any],
                     project_root: Path | None = None) -> str:
    ac = bundle.get("acceptance_criteria") or []
    claims = bundle.get("worker_claims") or []
    diff = bundle.get("diff_path", "")
    tests = bundle.get("test_proof_path", "")
    review = bundle.get("review_notes") or []
    installed = bundle.get("installed") or []
    deployed = bundle.get("deployed") or []
    outstanding = bundle.get("outstanding") or []
    implementer = bundle.get("implementer")
    reviewer = bundle.get("reviewer")

    # ---- real evidence inspection (read + hash + parse, no trust)
    diff_ev = inspect_evidence_path(diff)
    proof_ev = inspect_evidence_path(tests)
    proof_parse: dict[str, Any] = {}
    if proof_ev["status"] == "ok":
        try:
            proof_parse = parse_test_proof(
                Path(tests).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            proof_parse = {"recognized": False}

    diff_parse = {"valid": False, "reason": diff_ev["status"], "changed_paths": []}
    if diff_ev["status"] == "ok":
        try:
            diff_parse = parse_diff_evidence(Path(diff).read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            diff_parse = {"valid": False, "reason": "unreadable/unsupported textual diff", "changed_paths": []}
    proof_clean = bool(proof_parse.get("clean_pass"))
    evidence_ok = bool(diff_parse["valid"] and proof_clean)
    linked_claims = link_claim_evidence(bundle, diff_parse["changed_paths"]) if evidence_ok else {}
    claims_certified = bool(claims) and all(claim in linked_claims for claim in claims)
    state_receipts = {state: inspect_state_receipt(bundle, state)
                      for state in ("installed", "deployed")}
    # identity validation for the attestation
    identities_ok = (
        isinstance(implementer, str) and bool(implementer.strip())
        and isinstance(reviewer, str) and bool(reviewer.strip())
        and implementer.strip() != reviewer.strip()
    )

    def bullet_list(items: list[str]) -> str:
        if not items:
            return "- none reported\n"
        return "".join(f"- {item}\n" for item in items)

    lines: list[str] = []
    lines.append("# Implementation Handoff (g33 evidence-to-handoff)\n")
    lines.append(
        "Separation of state: implemented / tested / installed / deployed / "
        "outstanding are distinct; each claim carries its evidence path.\n"
    )

    lines.append("## Implemented\n")
    for claim in claims:
        if claim in linked_claims:
            link = linked_claims[claim]
            lines.append(f"- {claim} — linked recorded evidence: "
                         f"AC {', '.join(link['acceptance_criteria'])}; "
                         f"changed paths {', '.join(link['diff_paths'])}; "
                         f"diff {diff_ev['sha256']}; tests {proof_ev['sha256']}\n")
        else:
            lines.append(f"- claimed-unverified: {claim}\n")
    if not claims:
        lines.append("- none reported\n")
    if claims and not claims_certified:
        lines.append("- [unverified — unresolved evidence or missing AC/path linkage; claims not certified]\n")
    lines.append("- Linkage validates recorded artifacts and references; semantic AC fulfillment requires independent review.\n")

    lines.append("\n## Tested\n")
    if proof_ev["status"] == "ok" and proof_parse:
        if proof_clean:
            lines.append(
                f"- test proof VERIFIED: {tests} "
                f"(sha256 {proof_ev.get('sha256', '')[:12]}…, "
                f"{proof_parse.get('passed', 0)} passed, "
                f"{proof_parse.get('failed', 0)} failed, "
                f"{proof_parse.get('errors', 0)} errors; "
                f"exit codes {proof_parse.get('exit_codes', [])})\n")
        else:
            lines.append(
                f"- test proof READ but NOT CLEAN: {tests} — "
                f"{proof_parse.get('passed', 0)} passed, "
                f"{proof_parse.get('failed', 0)} failed, "
                f"{proof_parse.get('errors', 0)} errors; "
                f"exit codes {proof_parse.get('exit_codes', [])}"
                + ("" if proof_parse.get("recognized") else
                   " (no recognizable test summary — cannot certify)") + "\n")
    elif proof_ev["status"] == "empty":
        lines.append(f"- test proof EMPTY: {tests} — cannot certify\n")
    elif tests:
        lines.append(
            f"- test proof MISSING ({proof_ev['status']}): {tests} — "
            "cannot certify\n")
    else:
        lines.append("- none reported\n")

    for state, state_claims in (("installed", installed), ("deployed", deployed)):
        lines.append(f"\n## {state.title()}\n")
        receipt = state_receipts[state]
        for claim in state_claims:
            lines.append(f"- claimed-unverified: {claim}\n")
        if not state_claims:
            lines.append("- none reported\n")
        if receipt.get("sha256"):
            lines.append(f"- recorded {state} evidence READ: {receipt['path']} "
                         f"(sha256 {receipt['sha256']}); {receipt['status']} — "
                         "independent provenance and target observation are unproven\n")
        if state_claims:
            lines.append(f"- {state} claims are NOT certified; receipt text/format cannot prove target state\n")

    lines.append("\n## Outstanding\n")
    lines.append(bullet_list([str(o) for o in outstanding]))

    lines.append("## Acceptance criteria\n")
    lines.append(bullet_list([str(a) for a in ac]) if ac else "- none provided\n")

    lines.append("\n## Diff\n")
    if diff_parse["valid"]:
        lines.append(
            f"- diff VERIFIED: {diff} (sha256 {diff_ev.get('sha256', '')[:12]}…, "
            f"{diff_ev.get('size')} bytes; {diff_parse['hunks']} hunks; "
            f"changed paths {', '.join(diff_parse['changed_paths'])})\n")
    elif diff_ev["status"] == "ok":
        lines.append(f"- diff READ but INVALID/UNSUPPORTED: {diff} — {diff_parse['reason']}; cannot certify\n")
    elif diff:
        lines.append(
            f"- diff MISSING ({diff_ev['status']}): {diff} — not verified\n")
    else:
        lines.append("- none provided\n")

    if review:
        lines.append("\n## Review notes\n")
        lines.append(bullet_list([str(r) for r in review]))

    lines.append("\n## Evidence verification\n")
    lines.append(
        f"- diff_path: {diff_ev['status']}"
        + (f" (sha256 {diff_ev['sha256']})" if diff_ev.get("sha256") else "") + "\n")
    lines.append(
        f"- test_proof_path: {proof_ev['status']}"
        + (f" (sha256 {proof_ev['sha256']})" if proof_ev.get("sha256") else "") + "\n")
    lines.append(
        "- overall: " + ("recorded diff/test evidence and claim links validated; independent acceptance and installed/deployed state remain unverified"
                          if evidence_ok and claims_certified else "unresolved evidence or unlinked claims — claims above are NOT certified") + "\n")

    lines.append("\n## Attestation\n")
    if identities_ok:
        lines.append(
            f"- Reviewer {reviewer!r} is a distinct identity from implementer "
            f"{implementer!r}: independence VALIDATED from bundle inputs.\n")
    elif implementer and reviewer and implementer.strip() == reviewer.strip():
        lines.append(
            f"- NOT VALIDATED: implementer and reviewer are the same identity "
            f"({implementer!r}) — independence requirement violated.\n")
    else:
        lines.append(
            "- NOT VALIDATED: distinct implementer/reviewer identities were "
            "not provided in the bundle; independence is unproven.\n")
    lines.append(
        "- Decision compass: "
        + _pillar_citation(module_root, str(
            (effective_config(module_root, project_root).get("doctrine_pointer"))
            or "momo/PILLARS.md")) + "\n")
    return "".join(lines)
