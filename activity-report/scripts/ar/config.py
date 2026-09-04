"""Project and configuration resolution.

The canonical location of a project's settings is the `activity_report` block
in its repo-root `.project.json` (pjangler preserves unknown top-level keys).
`--project <slug>` resolves the repo through `pjangler project show`, otherwise
the nearest `.project.json` above cwd wins.
"""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .common import AUDIENCES, SKILL_NAME, ConfigError, eprint, read_json

DEFAULTS: dict = {
    "enabled": True,
    "audiences": ["internal", "external"],
    "timezone": "America/New_York",
    "extra_repo_paths": [],
    "schedule": {"at": "03:00"},
    "window": {"cap_hours": 24, "min_minutes": 60},
    "hindsight": {"bank": None, "recall": True, "retain": True, "retain_audiences": ["internal"]},
    "board": {
        "api_key_ref": None,
        "exposure_labels": {"external": "xp:external", "internal": "xp:internal"},
        "max_live_fetches": 50,
    },
    "compose": {"model": None, "timeout_minutes": 30},
    "lint": {"extra_identifiers": [], "banned_terms": []},
    "output": {"runtime_dir": "runtime/activity-report", "durable_html_dir": None},
    "portal": None,
}

CONFIG_KEY = "activity_report"
PROJECT_FILE = ".project.json"
ENTRY_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "activity-report")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")


@dataclass
class Project:
    slug: str
    name: str
    identifier: str | None
    workspace: str | None
    board_id: str | None
    provider_type: str | None
    repo_path: str
    extra_repo_paths: list[str]
    config: dict
    tz: str
    project_json_path: str
    ticket_provider: dict = field(default_factory=dict)
    config_source: str = "block"   # "block" when .project.json carries activity_report, else "defaults"

    @property
    def roots(self) -> list[str]:
        return [self.repo_path, *self.extra_repo_paths]

    @property
    def repo_names(self) -> list[str]:
        return [os.path.basename(r.rstrip("/")) for r in self.roots]

    def as_dict(self) -> dict:
        return {
            "slug": self.slug, "name": self.name, "identifier": self.identifier,
            "workspace": self.workspace, "board_id": self.board_id, "provider_type": self.provider_type,
            "repo_path": self.repo_path, "extra_repo_paths": list(self.extra_repo_paths),
            "timezone": self.tz, "project_json_path": self.project_json_path,
            "config_source": self.config_source, "config": self.config,
        }


@dataclass
class ScopeSet:
    """Every directory whose activity belongs to the project, matched on a path boundary."""
    roots: list[str]
    worktrees: list[str]
    missing: list[str]

    def all_paths(self) -> list[str]:
        return [*self.roots, *self.worktrees]

    def contains(self, path: str | None) -> bool:
        if not path:
            return False
        candidate = os.path.normpath(path)
        for p in self.all_paths():
            if candidate == p or candidate.startswith(p + os.sep):
                return True
        return False

    def as_dict(self) -> dict:
        return {"roots": list(self.roots), "worktrees": list(self.worktrees), "missing": list(self.missing)}


# -- helpers ------------------------------------------------------------------

def deep_merge(base: dict, override: dict) -> dict:
    """Dicts merge recursively; anything else in `override` replaces (including null)."""
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def find_project_json(start: str | None = None) -> str | None:
    here = os.path.realpath(start or os.getcwd())
    while True:
        candidate = os.path.join(here, PROJECT_FILE)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def _pjangler_repo_path(slug: str) -> str:
    try:
        proc = subprocess.run(
            ["pjangler", "project", "show", slug, "--json"],
            capture_output=True, text=True, timeout=60, check=False,
        )
    except FileNotFoundError as exc:
        raise ConfigError("`pjangler` is not on PATH; --project <slug> needs it (or run from inside the repo)") from exc
    except subprocess.TimeoutExpired as exc:
        raise ConfigError("`pjangler project show` timed out") from exc
    if proc.returncode != 0:
        raise ConfigError(f"pjangler does not know project {slug!r}: {proc.stderr.strip() or proc.stdout.strip()}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"pjangler project show {slug} did not return JSON") from exc
    repo_path = payload.get("repo_path") or (payload.get("project") or {}).get("repo_path")
    if not repo_path:
        raise ConfigError(f"pjangler project {slug!r} has no repo_path")
    return repo_path


def validate_config(config: dict) -> None:
    if config.get("enabled") is not True:
        raise ConfigError(f"{CONFIG_KEY}.enabled is not true; nothing to do for this project")
    audiences = config.get("audiences")
    if not isinstance(audiences, list) or not audiences or any(a not in AUDIENCES for a in audiences) \
            or len(set(audiences)) != len(audiences):
        raise ConfigError(f"{CONFIG_KEY}.audiences must be a non-empty subset of {list(AUDIENCES)}")
    tz = config.get("timezone")
    try:
        ZoneInfo(str(tz))
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ConfigError(f"{CONFIG_KEY}.timezone {tz!r} is not an IANA zone") from exc
    window = config.get("window") or {}
    cap = window.get("cap_hours")
    if not isinstance(cap, (int, float)) or isinstance(cap, bool) or cap <= 0 or cap > 744:
        raise ConfigError(f"{CONFIG_KEY}.window.cap_hours must be a number in (0, 744]")
    minimum = window.get("min_minutes")
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 0:
        raise ConfigError(f"{CONFIG_KEY}.window.min_minutes must be a non-negative integer")
    at = (config.get("schedule") or {}).get("at")
    if not isinstance(at, str) or not _TIME_RE.match(at):
        raise ConfigError(f"{CONFIG_KEY}.schedule.at must be HH:MM (24 h), got {at!r}")
    for path in config.get("extra_repo_paths") or []:
        if not isinstance(path, str) or not os.path.isabs(path):
            raise ConfigError(f"{CONFIG_KEY}.extra_repo_paths entries must be absolute paths, got {path!r}")
    output = config.get("output") or {}
    if not isinstance(output.get("runtime_dir"), str) or os.path.isabs(output["runtime_dir"]):
        raise ConfigError(f"{CONFIG_KEY}.output.runtime_dir must be a repo-relative path")
    durable = output.get("durable_html_dir")
    if durable is not None and (not isinstance(durable, str) or os.path.isabs(durable)):
        raise ConfigError(f"{CONFIG_KEY}.output.durable_html_dir must be null or a repo-relative path")
    portal = config.get("portal")
    if portal is not None:
        if not isinstance(portal, dict) or not portal.get("project_id"):
            raise ConfigError(f"{CONFIG_KEY}.portal must be null or carry project_id")
        portal.setdefault("kind", "automatic-ai")
    retain_audiences = (config.get("hindsight") or {}).get("retain_audiences")
    if not isinstance(retain_audiences, list) or any(a not in AUDIENCES for a in retain_audiences):
        raise ConfigError(f"{CONFIG_KEY}.hindsight.retain_audiences must be a list drawn from {list(AUDIENCES)}")
    board = config.get("board") or {}
    labels = board.get("exposure_labels") or {}
    if not labels.get("external") or not labels.get("internal") or labels["external"] == labels["internal"]:
        raise ConfigError(f"{CONFIG_KEY}.board.exposure_labels needs distinct external and internal names")


def load_project(slug: str | None = None, cwd: str | None = None) -> Project:
    """Resolve the project and its merged config. Raises ConfigError (exit 2)."""
    path = find_project_json(cwd)
    if slug:
        if path:
            try:
                if read_json(path).get("project_slug") != slug:
                    path = None
            except (OSError, ValueError):
                path = None
        if not path:
            repo_path = _pjangler_repo_path(slug)
            path = os.path.join(repo_path, PROJECT_FILE)
            if not os.path.isfile(path):
                raise ConfigError(f"{path} does not exist; pjangler's repo_path for {slug} is stale")
    if not path:
        raise ConfigError(f"no {PROJECT_FILE} above {cwd or os.getcwd()}; pass --project <slug> or run inside a pjangler project")
    try:
        manifest = read_json(path)
    except ValueError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ConfigError(f"{path} must hold an object")

    project_slug = manifest.get("project_slug")
    if not isinstance(project_slug, str) or not _SLUG_RE.match(project_slug):
        raise ConfigError(f"{path}: project_slug {project_slug!r} is not a lowercase slug")
    if slug and project_slug != slug:
        raise ConfigError(f"{path} belongs to {project_slug!r}, not {slug!r}")

    repo_path = manifest.get("repo_path") or os.path.dirname(os.path.realpath(path))
    if not os.path.isdir(repo_path):
        raise ConfigError(f"{path}: repo_path {repo_path!r} is not a directory")

    block = manifest.get(CONFIG_KEY)
    source = "block"
    if block is None:
        block, source = {}, "defaults"
    if not isinstance(block, dict):
        raise ConfigError(f"{path}: {CONFIG_KEY} must be an object")
    config = deep_merge(DEFAULTS, block)
    validate_config(config)

    provider = manifest.get("ticket_provider") or {}
    return Project(
        slug=project_slug,
        name=str(manifest.get("project_name") or project_slug),
        identifier=provider.get("identifier") or None,
        workspace=provider.get("workspace") or None,
        board_id=provider.get("board_id") or None,
        provider_type=provider.get("type") or None,
        repo_path=os.path.realpath(repo_path),
        extra_repo_paths=[os.path.realpath(p) for p in config.get("extra_repo_paths") or []],
        config=config,
        tz=config["timezone"],
        project_json_path=path,
        ticket_provider=dict(provider),
        config_source=source,
    )


def hindsight_bank(project: Project) -> str:
    """The bank this project's memory lives in: the config value, else the repo basename.

    Names shaped like an agent's private bank are refused unless set explicitly,
    so a project cannot silently read or write a PM's memory.
    """
    explicit = (project.config.get("hindsight") or {}).get("bank")
    if explicit:
        return str(explicit)
    bank = os.path.basename(project.repo_path.rstrip("/"))
    if bank.startswith("agent-") or bank.endswith("-field-ops"):
        raise ConfigError(f"refusing implicit Hindsight bank {bank!r}; set {CONFIG_KEY}.hindsight.bank explicitly")
    return bank


def _git_worktrees(root: str) -> list[str]:
    try:
        proc = subprocess.run(["git", "-C", root, "worktree", "list", "--porcelain"],
                              capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    paths = []
    for line in proc.stdout.splitlines():
        if line.startswith("worktree "):
            paths.append(os.path.normpath(line[len("worktree "):].strip()))
    return paths


def scope_set(project: Project) -> ScopeSet:
    roots, worktrees, missing = [], [], []
    for root in project.roots:
        root = os.path.normpath(root)
        if not os.path.isdir(os.path.join(root, ".git")) and not os.path.isfile(os.path.join(root, ".git")):
            missing.append(root)
            continue
        if root not in roots:
            roots.append(root)
        for wt in _git_worktrees(root):
            if wt not in roots and wt not in worktrees and os.path.isdir(wt):
                worktrees.append(wt)
        local = os.path.join(root, ".claude", "worktrees")
        if os.path.isdir(local):
            for name in sorted(os.listdir(local)):
                wt = os.path.join(local, name)
                if os.path.isdir(wt) and wt not in worktrees:
                    worktrees.append(wt)
    return ScopeSet(roots=roots, worktrees=worktrees, missing=missing)


# -- commands ---------------------------------------------------------------

def resolve_cmd(args) -> int:
    project = load_project(args.project)
    scope = scope_set(project)
    if args.json:
        print(json.dumps({"project": project.as_dict(), "scope": scope.as_dict()}, indent=2))
        return 0
    print(f"project   {project.slug}  ({project.name})")
    print(f"manifest  {project.project_json_path}  [{project.config_source}]")
    print(f"board     {project.provider_type or '-'} {project.workspace or ''} {project.identifier or ''} {project.board_id or ''}".rstrip())
    print(f"timezone  {project.tz}    audiences {', '.join(project.config['audiences'])}    schedule {project.config['schedule']['at']}")
    print(f"window    cap {project.config['window']['cap_hours']} h, min {project.config['window']['min_minutes']} min")
    print(f"hindsight {hindsight_bank(project)}")
    portal = project.config.get("portal")
    print(f"portal    {portal['kind'] + ' ' + portal['project_id'] if portal else '-'}")
    for root in scope.roots:
        print(f"root      {root}")
    for wt in scope.worktrees:
        print(f"worktree  {wt}")
    for m in scope.missing:
        print(f"MISSING   {m}  (configured but not a git checkout)")
    return 0


def _shim_target() -> str:
    linked = os.path.join(os.path.expanduser("~"), ".agents", "skills", SKILL_NAME, "scripts", "activity-report")
    return linked if os.path.exists(linked) else ENTRY_SCRIPT


def init_cmd(args) -> int:
    rc = 0
    bin_dir = os.path.join(os.path.expanduser("~"), ".local", "bin")
    os.makedirs(bin_dir, exist_ok=True)
    shim = os.path.join(bin_dir, SKILL_NAME)
    target = _shim_target()
    if os.path.islink(shim) and os.readlink(shim) == target:
        print(f"shim      {shim} -> {target} (already)")
    elif os.path.exists(shim) and not os.path.islink(shim):
        eprint(f"shim      {shim} exists and is not a symlink; leaving it alone")
        rc = 2
    else:
        if os.path.islink(shim):
            os.unlink(shim)
        os.symlink(target, shim)
        print(f"shim      {shim} -> {target}")

    try:
        project = load_project(args.project)
    except ConfigError as exc:
        print(f"project   none ({exc})")
        print("          add this block to the repo's .project.json to enable the skill:")
        print(json.dumps({CONFIG_KEY: DEFAULTS}, indent=2))
        return rc
    print(f"project   {project.slug}  [{project.config_source}]")
    if project.config_source == "defaults":
        print(f"          no {CONFIG_KEY} block in {project.project_json_path}; defaults apply. Suggested block:")
        print(json.dumps({CONFIG_KEY: DEFAULTS}, indent=2))

    runtime_rel = project.config["output"]["runtime_dir"]
    probe = os.path.join(project.repo_path, runtime_rel, project.slug, "probe")
    check = subprocess.run(["git", "-C", project.repo_path, "check-ignore", "-q", probe],
                           capture_output=True, text=True, check=False)
    if check.returncode == 0:
        print(f"gitignore {runtime_rel}/ is ignored")
    else:
        gitignore = os.path.join(project.repo_path, ".gitignore")
        pattern = runtime_rel.rstrip("/") + "/"
        with open(gitignore, "a", encoding="utf-8") as fh:
            fh.write(f"\n# activity-report per-run files (digest, bodies, event); the durable html is tracked elsewhere\n{pattern}\n")
        print(f"gitignore appended {pattern} to {gitignore}")
    return rc
