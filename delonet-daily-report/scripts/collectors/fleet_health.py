"""Hermes fleet health, assembled from observable facts rather than self-report.

Why this collector exists
-------------------------
On 2026-08-18 the ``candystore-daily-journal`` Hermes cron job fired at 06:00,
could not find its skill, produced nothing -- and recorded ``last_status: "ok"``.
The scheduler's own account of itself was wrong, and nothing downstream noticed.

So the rule here is absolute: **``last_status`` is a claim, never evidence.**
Every job that claims ``ok`` is reported as ``unverified`` unless something
independent of the scheduler contradicts or corroborates it. The presence of a
file in ``cron/output/`` does not corroborate anything either -- the very output
file written by the run that lied says, in its own text, that the skill was
skipped. It is counted as an observation and nothing more.

The fleet model this collector measures against
-----------------------------------------------
* **One host gateway.** Since 2026-10-11 a single systemd --user unit,
  ``hermes-gateway.service``, serves every profile: chat platforms and the
  Bloodbank fleet command lane. There is no per-agent gateway unit. A registry
  row that still names ``hermes-<agent>-gateway.service`` is a stale projection
  of the retired per-agent model -- reported once, in aggregate, as registry
  drift, never as N gateway outages. A per-agent gateway unit that systemd
  *has* loaded is the dangerous case (2026-10-20: one took the host role and
  blocked Bloodbank for three hours) and is reported as a conflict.
* **Candybar is the single clock.** A Hermes job Candybar runs is pinned
  ``scheduler: external``; its run facts live in the candybar registry, not in
  ``jobs.json``. A disabled, unpinned job is a dormant ledger entry nothing
  schedules -- not a live claim. An enabled, unpinned Hermes job is a second
  clock. An active ``hermes-*`` timer that is not in Candybar's own
  ``deploy/scheduling-policy.json`` exception register is a second clock too.

What is treated as evidence
---------------------------
* does the referenced skill actually resolve for **that profile**, the way
  Hermes resolves it: the profile's ``skills/`` dir, ``skills.create_dir``,
  ``skills.external_dirs``, and a trusted project's ``.hermes/skills`` /
  ``.agents/skills`` when the job runs in one (a broken symlink resolves to
  nothing -- this is the exact shape of the 2026-08-18 failure);
* does the profile directory named by the registry exist;
* is the host gateway unit loaded and active, and is any per-agent gateway
  unit loaded beside it;
* does the profile a candybar's Hermes runner targets exist, and is the job it
  names present and pinned ``scheduler: external``;
* when did the profile's ``cron/ticker_heartbeat`` last move;
* is a job's ``next_run_at`` already in the past (a ticker that stopped ticking);
* does a timer have no next elapse at all.

Status semantics
----------------
``status`` describes **this collector's coverage of its sources**, not the health
of the fleet. A fleet full of dead gateways that was measured completely is
``complete`` with alarming metrics; a healthy fleet measured with systemd
unreachable is ``partial``. Conflating the two is how a report ends up hiding a
gap behind good news.

Every source read is read-only. Subprocess calls carry an explicit timeout.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collectors.base import SectionResult, allowlist, run_collector  # noqa: E402
from reportctl_contracts import ConfigError  # noqa: E402
from reportctl_runtime import run_command  # noqa: E402

SECTION_ID = "fleet-health"

DEFAULT_HERMES_HOME = "~/.hermes"
DEFAULT_TICKER_STALE_SECONDS = 900
DEFAULT_COMMAND_TIMEOUT = 20
DEFAULT_MAX_DETAIL_LINES = 200
DEFAULT_MAX_AGE_HOURS = 24

#: Where the candybar control plane answers on the host (Epic 7: migrated
#: cron jobs are registered there, so a report that only read systemd timers
#: and Hermes jobs.json would go blind to them). Set the section option
#: ``candybar_api_url`` to "" to drop the source entirely.
DEFAULT_CANDYBAR_API_URL = "http://127.0.0.1:8700"
DEFAULT_HTTP_TIMEOUT = 5
CANDYBAR_SOURCE_ID = "candybar-api"

#: The one host gateway. The registry's ``gateways.*.systemd_unit`` names it
#: as well; every name found there is honoured alongside this default. Set
#: the section option ``host_gateway_unit`` to override it.
DEFAULT_HOST_GATEWAY_UNIT = "hermes-gateway.service"

#: The retired per-agent gateway unit shape.
PER_AGENT_GATEWAY_RE = re.compile(r"^hermes-(?P<agent>.+)-gateway\.service$")

#: Candybar's exception register for native timers. Optional: when it cannot
#: be read, timers are listed but not classified as exempt or not.
DEFAULT_SCHEDULING_POLICY = "~/code/33GOD/candybar/deploy/scheduling-policy.json"

#: Migrated candybars name the Hermes job they run in their description --
#: "(was hermes <profile>:<job_id>)", the migration ledger's convention. The
#: API exposes no runner config, so this is the only link the report has.
HERMES_TARGET_RE = re.compile(
    r"\bwas hermes (?P<profile>[A-Za-z0-9._-]+):(?P<job>[0-9a-f]{6,64})\b"
)

#: Mirrors hermes-agent ``agent/skill_utils.py``: directories never indexed as
#: skills, and support dirs not descended into once a directory has SKILL.md.
SKILL_WALK_EXCLUDED = frozenset(
    {
        ".git", ".github", ".hub", ".archive", ".curator_backups", ".locks",
        ".venv", "venv", "node_modules", "site-packages", "__pycache__",
        ".tox", ".nox", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    }
)
SKILL_SUPPORT_DIRS = frozenset({"references", "templates", "assets", "scripts"})
PROJECT_SKILLS_SUBDIRS = (".hermes/skills", ".agents/skills")
SKILL_WALK_MAX_DEPTH = 6

#: Longest string copied out of any source file. Values from disk are clipped so
#: an oversized field cannot dominate the artifact.
MAX_TEXT = 120

#: Plausible epoch-microsecond window (2001-09-09 .. 2096-10-02). systemd reports
#: monotonic values for some timers; anything outside this window is unknown, not
#: guessed at.
EPOCH_US_MIN = 1_000_000_000_000_000
EPOCH_US_MAX = 4_000_000_000_000_000

#: The structural field allowlist for this collector. Records are assembled by
#: explicit extraction and then filtered through ``allowlist`` again, so no raw
#: source payload -- notably a cron job's ``prompt`` or a provider ``base_url`` --
#: can reach the artifact even if the assembly code is later changed carelessly.
FLEET_FIELDS = frozenset(
    {
        # containers
        "observed_at",
        "sources",
        "agents",
        "units",
        "timers",
        "profiles",
        "jobs",
        # source records
        "source",
        "ok",
        "reason",
        "path",
        # registry agents
        "agent",
        "profile_name",
        "profile_dir_present",
        "gateway_unit",
        "gateway_unit_known",
        "gateway_unit_active",
        "gateway_model",
        "served_by",
        "heartbeat_timer",
        "heartbeat_timer_known",
        # systemd units
        "unit",
        "kind",
        "load_state",
        "active_state",
        "sub_state",
        # systemd timers
        "last_trigger_at",
        "next_elapse_at",
        "never_triggered",
        "no_next_elapse",
        "policy_exempt",
        # host gateway
        "host_gateway",
        "per_agent_gateway_units",
        # profiles
        "profile",
        "cron_dir",
        "cron_dir_shared_with",
        "jobs_total",
        "jobs_enabled",
        "jobs_readable",
        "ticker_present",
        "ticker_age_seconds",
        "ticker_stale",
        # cron jobs
        "job_id",
        "name",
        "enabled",
        "state",
        "schedule",
        "last_status",
        "last_run_at",
        "next_run_at",
        "next_run_in_past",
        "last_error_present",
        "last_error_chars",
        "skills",
        "missing_skills",
        "scheduler",
        "schedule_owner",
        "pinned_enabled",
        "candybar",
        "verification",
        "output_files",
        "output_latest_at",
        # candybars (the candybar registry, read over its HTTP API)
        "candybars",
        "timezone",
        "noise",
        "last_result",
        "last_finished_at",
        "last_trigger",
        "hermes_target",
        "hermes_target_problem",
    }
)

#: The four sources this section always needs. ``complete`` requires all of
#: them; the candybar API is a fifth source whenever ``candybar_api_url`` is
#: set (the default), and the same honesty rule applies to it.
SOURCE_IDS = ("agents-registry", "systemd-units", "systemd-timers", "hermes-profiles")


# --------------------------------------------------------------------------- #
# small helpers                                                               #
# --------------------------------------------------------------------------- #


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _iso(moment: dt.datetime | None) -> str | None:
    if moment is None:
        return None
    return moment.astimezone(dt.UTC).isoformat().replace("+00:00", "Z")


def _clip(value: Any, limit: int = MAX_TEXT) -> str:
    """Copy a string out of a source file, bounded. Non-strings become ''."""
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _epoch_us(value: Any) -> dt.datetime | None:
    if not isinstance(value, int) or isinstance(value, bool):
        return None
    if not EPOCH_US_MIN <= value <= EPOCH_US_MAX:
        return None
    return dt.datetime.fromtimestamp(value / 1_000_000, tz=dt.UTC)


def _parse_dt(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.UTC)


def _option(options: Any, key: str, default: Any) -> Any:
    if not isinstance(options, dict):
        return default
    value = options.get(key, default)
    return default if value is None else value


def _int_option(options: Any, key: str, default: int, *, low: int, high: int) -> int:
    value = _option(options, key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return max(low, min(high, int(value)))


def _path_option(options: Any, key: str, default: Path) -> Path:
    value = _option(options, key, None)
    if isinstance(value, str) and value.strip():
        return Path(value).expanduser()
    return default


# --------------------------------------------------------------------------- #
# sources                                                                     #
# --------------------------------------------------------------------------- #


def _read_registry(path: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Return ``(agents, gateways, reason)``; a non-empty reason means the source failed."""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - PyYAML ships with the fleet
        return {}, {}, f"PyYAML unavailable: {exc}"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, {}, f"cannot read {path}: {exc.strerror or exc}"
    try:
        document = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return {}, {}, f"cannot parse {path}: {type(exc).__name__}"
    if not isinstance(document, dict):
        return {}, {}, f"{path} is not a YAML mapping"
    agents = document.get("agents")
    if not isinstance(agents, dict):
        return {}, {}, f"{path} has no agents mapping"
    gateways = document.get("gateways")
    return agents, gateways if isinstance(gateways, dict) else {}, ""


def _host_gateway_units(gateways: dict[str, Any], default: str) -> list[str]:
    """Every unit name that IS the host gateway: the option, plus whatever the
    registry's top-level ``gateways`` block names (``systemd_unit``)."""
    names: list[str] = [default] if default else []
    for value in gateways.values():
        if isinstance(value, dict):
            unit = _clip(value.get("systemd_unit"), 96)
            if unit and unit not in names:
                names.append(unit)
    return names


def _read_policy_exemptions(path: Path) -> tuple[set[str], str]:
    """Native timers Candybar's own policy register exempts (``systemd:user:<unit>``)."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return set(), f"{path}: {type(exc).__name__}"
    entries = document.get("exceptions") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        return set(), f"{path}: no exceptions array"
    exempt: set[str] = set()
    for entry in entries:
        ident = entry.get("id") if isinstance(entry, dict) else None
        if isinstance(ident, str) and ident.startswith("systemd:user:"):
            exempt.add(ident[len("systemd:user:"):])
    return exempt, ""


def _systemctl_json(args: list[str], timeout: int) -> tuple[list[dict[str, Any]], str]:
    command = ["systemctl", "--user", "--no-pager", "--output=json", *args]
    try:
        completed = run_command(command, timeout=timeout)
    except ConfigError as exc:
        return [], str(exc)
    try:
        payload = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as exc:
        return [], f"systemctl produced unparseable JSON: {exc}"
    if not isinstance(payload, list):
        return [], "systemctl produced a non-array JSON document"
    return [row for row in payload if isinstance(row, dict)], ""


def _read_units(pattern: str, timeout: int) -> tuple[list[dict[str, Any]], str]:
    rows, reason = _systemctl_json(["list-units", "--all", pattern], timeout)
    if reason:
        return [], reason
    units = []
    for row in rows:
        unit = _clip(row.get("unit"))
        if not unit:
            continue
        units.append(
            {
                "unit": unit,
                "kind": unit.rsplit(".", 1)[-1] if "." in unit else "",
                "load_state": _clip(row.get("load"), 32),
                "active_state": _clip(row.get("active"), 32),
                "sub_state": _clip(row.get("sub"), 32),
            }
        )
    return units, ""


def _read_timers(prefix: str, timeout: int) -> tuple[dict[str, dict[str, Any]], str]:
    rows, reason = _systemctl_json(["list-timers", "--all"], timeout)
    if reason:
        return {}, reason
    timers: dict[str, dict[str, Any]] = {}
    for row in rows:
        unit = _clip(row.get("unit"))
        if not unit.startswith(prefix):
            continue
        last, nxt = _epoch_us(row.get("last")), _epoch_us(row.get("next"))
        timers[unit] = {
            "unit": unit,
            "last_trigger_at": _iso(last),
            "next_elapse_at": _iso(nxt),
            "never_triggered": last is None,
            "no_next_elapse": nxt is None,
        }
    return timers, ""


def _http_json(url: str, timeout: int) -> Any:
    """One GET that parses as JSON. Any failure raises ConfigError (a reason)."""
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(1_000_000)
    except (OSError, urllib.error.URLError) as exc:
        raise ConfigError(f"GET {url}: {exc}") from exc
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"GET {url}: unparseable JSON ({type(exc).__name__})") from exc


def _read_candybars(base_url: str, timeout: int) -> tuple[list[dict[str, Any]], str]:
    """The candybar registry over its HTTP API: one record per registered job.

    Migrated cron jobs left systemd timers and Hermes jobs.json behind, so
    this is the only place the report still sees them. Each record carries the
    latest invocation's self-contained result fields; the API is the
    scheduler's own record-keeping, so a ``fail`` there is a fact about the
    run, and ``enabled`` is a fact about the registry -- neither is a claim by
    the job.
    """
    base = base_url.rstrip("/")
    try:
        payload = _http_json(f"{base}/candybars", timeout)
    except ConfigError as exc:
        return [], str(exc)
    if not isinstance(payload, list):
        return [], "GET /candybars returned a non-array JSON document"
    candybars: list[dict[str, Any]] = []
    for row in payload:
        if not isinstance(row, dict):
            return [], "GET /candybars returned a non-object entry"
        candybar_id = _clip(row.get("id"), 64)
        target = HERMES_TARGET_RE.search(row.get("description") or "") if isinstance(
            row.get("description"), str
        ) else None
        record = {
            "name": _clip(row.get("name"), 64),
            "schedule": _clip(row.get("schedule"), 64),
            "timezone": _clip(row.get("timezone"), 64),
            "enabled": row.get("enabled") is True,
            "noise": row.get("noise") is True,
            "last_result": "",
            "last_finished_at": None,
            "last_trigger": "",
            # "<profile>:<job_id>" of the Hermes job this candybar runs, when
            # its description follows the migration convention; else "".
            "hermes_target": f"{target['profile']}:{target['job']}" if target else "",
            "hermes_target_problem": "",
        }
        if candybar_id:
            try:
                latest = _http_json(
                    f"{base}/candybars/{candybar_id}/invocations?limit=1", timeout
                )
            except ConfigError as exc:
                return [], str(exc)
            invocations = (
                latest.get("invocations") if isinstance(latest, dict) else None
            )
            if not isinstance(invocations, list):
                return [], f"GET invocations for {record['name'] or candybar_id}: no array"
            if invocations and isinstance(invocations[0], dict):
                first = invocations[0]
                record["last_result"] = _clip(first.get("result"), 32)
                record["last_finished_at"] = _clip(first.get("finishedAt"), 40) or None
                record["last_trigger"] = _clip(first.get("trigger"), 32)
        candybars.append(record)
    return candybars, ""


def _read_frontmatter_name(skill_md: Path) -> str:
    """The ``name:`` a SKILL.md declares, or '' -- Hermes resolves by it too."""
    try:
        with skill_md.open(encoding="utf-8", errors="replace") as handle:
            first = handle.readline()
            if first.strip() != "---":
                return ""
            for _ in range(40):
                line = handle.readline()
                if not line or line.strip() == "---":
                    return ""
                if line.startswith("name:"):
                    return line[len("name:"):].strip().strip("'\"")
    except OSError:
        return ""
    return ""


def _skill_aliases(root: Path, cache: dict[str, frozenset[str]]) -> frozenset[str]:
    """Every name a skill under ``root`` answers to, the way Hermes indexes it:
    its directory name, its path relative to the root, and its declared name.

    Walks with symlinks followed (a dangling link is simply not found), prunes
    the directories Hermes prunes, and never descends into a skill's support
    dirs. Cached per resolved root: profiles share external dirs.
    """
    try:
        key = str(root.resolve())
    except (OSError, RuntimeError):
        return frozenset()
    if key in cache:
        return cache[key]
    aliases: set[str] = set()
    base_depth = len(Path(key).parts)
    try:
        walker = os.walk(key, followlinks=True)
        for current, dirs, files in walker:
            depth = len(Path(current).parts) - base_depth
            has_skill = "SKILL.md" in files
            dirs[:] = [
                d
                for d in dirs
                if d not in SKILL_WALK_EXCLUDED
                and not (has_skill and d in SKILL_SUPPORT_DIRS)
                and depth < SKILL_WALK_MAX_DEPTH
            ]
            if has_skill and current != key:
                skill_dir = Path(current)
                aliases.add(skill_dir.name)
                aliases.add(skill_dir.relative_to(key).as_posix())
                declared = _read_frontmatter_name(skill_dir / "SKILL.md")
                if declared:
                    aliases.add(declared)
    except OSError:
        pass
    cache[key] = frozenset(aliases)
    return cache[key]


def _load_profile_skill_config(profile_dir: Path) -> dict[str, Any]:
    """The ``skills:`` block of a profile's generated config.yaml ({} if none)."""
    try:
        import yaml
    except ImportError:  # pragma: no cover
        return {}
    try:
        document = yaml.safe_load((profile_dir / "config.yaml").read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError):
        return {}
    skills = document.get("skills") if isinstance(document, dict) else None
    return skills if isinstance(skills, dict) else {}


def _str_list(raw: Any) -> list[str]:
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    return [text for text in (str(item).strip() for item in raw) if text]


def _profile_path(profile_dir: Path, entry: str) -> Path:
    """Expand ``~``/``${VAR}`` and anchor a relative entry at the profile home."""
    path = Path(os.path.expanduser(os.path.expandvars(entry)))
    return path if path.is_absolute() else profile_dir / path


def _skill_roots(
    profile_dir: Path, skill_config: dict[str, Any], workdir: str | None
) -> list[Path]:
    """The roots Hermes searches for this profile, in its precedence order:
    trusted project (only when the job runs inside one), local profile skills,
    ``skills.create_dir``, ``skills.external_dirs``."""
    roots: list[Path] = []
    if workdir and skill_config.get("project_discovery") is not False:
        trusted = set()
        for entry in _str_list(skill_config.get("trusted_project_dirs")):
            try:
                trusted.add(_profile_path(profile_dir, entry).resolve())
            except (OSError, RuntimeError):
                continue
        try:
            current = Path(workdir).expanduser().resolve()
            home = Path.home().resolve()
            for _ in range(64):
                if (current / ".git").exists():
                    if current != home and current in trusted:
                        roots.extend(current / sub for sub in PROJECT_SKILLS_SUBDIRS)
                    break
                if current.parent == current:
                    break
                current = current.parent
        except (OSError, RuntimeError):
            pass
    roots.append(profile_dir / "skills")
    create_dir = skill_config.get("create_dir")
    if isinstance(create_dir, str) and create_dir.strip():
        roots.append(_profile_path(profile_dir, create_dir.strip()))
    roots.extend(_profile_path(profile_dir, entry) for entry in _str_list(skill_config.get("external_dirs")))
    return roots


def _resolve_skill(
    roots: list[Path], name: str, disabled: set[str], cache: dict[str, frozenset[str]]
) -> bool:
    """True only when ``name`` resolves to a real skill (a readable SKILL.md) in
    one of the profile's roots and is not disabled for the profile.

    Symlinks are followed, so a dangling ``skills/<name>`` link -- precisely
    the 2026-08-18 failure -- resolves to False.
    """
    if not name or name in {".", ".."} or ".." in name.split("/") or name.startswith("/"):
        return False
    if name in disabled:
        return False
    return any(name in _skill_aliases(root, cache) for root in roots)


def _job_skills(job: dict[str, Any]) -> list[str]:
    names: list[str] = []
    single = job.get("skill")
    if isinstance(single, str) and single.strip():
        names.append(_clip(single, 64))
    plural = job.get("skills")
    if isinstance(plural, list):
        for item in plural:
            if isinstance(item, str) and item.strip():
                names.append(_clip(item, 64))
    seen: set[str] = set()
    return [name for name in names if not (name in seen or seen.add(name))]


def _output_observation(cron_dir: Path, job_id: str) -> tuple[int, str | None]:
    """Count files under ``cron/output/<job_id>`` -- an observation, not proof."""
    if not job_id:
        return 0, None
    directory = cron_dir / "output" / job_id
    try:
        entries = [entry for entry in directory.iterdir() if entry.is_file()]
    except OSError:
        return 0, None
    latest = None
    for entry in entries:
        try:
            stamp = dt.datetime.fromtimestamp(entry.stat().st_mtime, tz=dt.UTC)
        except OSError:
            continue
        if latest is None or stamp > latest:
            latest = stamp
    return len(entries), _iso(latest)


def _empty_job(profile: str) -> dict[str, Any]:
    """Every job record carries the full shape, so a malformed entry is reported
    rather than crashing whatever reads the records later."""
    return {
        "profile": profile,
        "job_id": "",
        "name": "",
        "enabled": False,
        "state": "",
        "schedule": "",
        "last_status": "",
        "last_run_at": None,
        "next_run_at": None,
        "next_run_in_past": False,
        "last_error_present": False,
        "last_error_chars": 0,
        "skills": [],
        "missing_skills": [],
        "scheduler": "",
        # Who decides when this job runs: "candybar" (pinned external),
        # "hermes" (enabled, unpinned: a second clock), or "dormant" (nothing).
        "schedule_owner": "dormant",
        "pinned_enabled": False,
        "candybar": "",
        "verification": "not-claimed",
        "output_files": 0,
        "output_latest_at": None,
    }


def _read_job(
    job: Any,
    profile: str,
    cron_dir: Path,
    roots_for: Any,
    disabled: set[str],
    cache: dict[str, frozenset[str]],
    now: dt.datetime,
) -> dict[str, Any]:
    if not isinstance(job, dict):
        record = _empty_job(profile)
        record["name"] = "<malformed job entry>"
        record["verification"] = "unreadable"
        return record
    job_id = _clip(job.get("id"), 64)
    skills = _job_skills(job)
    workdir = job.get("workdir") if isinstance(job.get("workdir"), str) else None
    roots = roots_for(workdir)
    missing = [name for name in skills if not _resolve_skill(roots, name, disabled, cache)]
    next_run = _parse_dt(job.get("next_run_at"))
    last_run = _parse_dt(job.get("last_run_at"))
    external = job.get("scheduler") == "external"
    raw_enabled = job.get("enabled") is True
    # ``enabled`` keeps its historical meaning: the Hermes ticker owns the job.
    enabled = raw_enabled and not external
    # A pin is Candybar's whatever ``enabled`` says: the ticker never fires a
    # pinned job, and the candybar runner's ``cron run`` fires it either way.
    if external:
        owner = "candybar"
    else:
        owner = "hermes" if raw_enabled else "dormant"
    last_status = _clip(job.get("last_status"), 32)
    last_error = job.get("last_error")
    error_present = isinstance(last_error, str) and bool(last_error.strip())
    schedule = job.get("schedule")
    schedule_expr = ""
    if isinstance(schedule, dict):
        schedule_expr = _clip(schedule.get("expr") or schedule.get("display"), 64)
    if not schedule_expr:
        schedule_expr = _clip(job.get("schedule_display"), 64)

    # last_status is a claim. It is only ever downgraded here, never trusted --
    # and it is only a live claim for a job the Hermes ticker still owns. A
    # Candybar-run job's run facts are the candybar invocation record; a
    # dormant entry's last_status is history, not a claim about today.
    if owner == "candybar":
        verification = "candybar-managed"
    elif owner == "dormant":
        verification = "dormant"
    elif last_status != "ok" or last_run is None:
        verification = "not-claimed"
    elif missing or error_present:
        verification = "contradicted"
    else:
        verification = "unverified"

    output_files, output_latest = _output_observation(cron_dir, job_id)
    return {
        **_empty_job(profile),
        "job_id": job_id,
        "name": _clip(job.get("name"), 64),
        "enabled": enabled,
        "state": _clip(job.get("state"), 32),
        "schedule": schedule_expr,
        "last_status": last_status,
        "last_run_at": _iso(last_run),
        "next_run_at": _iso(next_run),
        "next_run_in_past": bool(enabled and next_run is not None and next_run < now),
        "last_error_present": error_present,
        "last_error_chars": len(last_error) if error_present else 0,
        "skills": skills,
        "missing_skills": missing,
        "scheduler": _clip(job.get("scheduler"), 32),
        "schedule_owner": owner,
        "pinned_enabled": raw_enabled,
        "verification": verification,
        "output_files": output_files,
        "output_latest_at": output_latest,
    }


def _read_ticker(cron_dir: Path, now: dt.datetime, stale_seconds: int) -> dict[str, Any]:
    ticker = cron_dir / "ticker_heartbeat"
    try:
        age = int((now - dt.datetime.fromtimestamp(ticker.stat().st_mtime, tz=dt.UTC)).total_seconds())
    except OSError:
        return {"ticker_present": False, "ticker_age_seconds": -1, "ticker_stale": True}
    return {
        "ticker_present": True,
        "ticker_age_seconds": age,
        "ticker_stale": age > stale_seconds,
    }


def _read_profiles(
    profiles_dir: Path, now: dt.datetime, stale_seconds: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    try:
        entries = sorted(entry for entry in profiles_dir.iterdir())
    except OSError as exc:
        return [], [], f"cannot list {profiles_dir}: {exc.strerror or exc}"

    profiles: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    seen_cron_dirs: dict[str, str] = {}
    alias_cache: dict[str, frozenset[str]] = {}
    for entry in entries:
        try:
            if not entry.is_dir():
                continue
        except OSError:
            continue
        profile = _clip(entry.name, 64)
        cron_dir = entry / "cron"  # often a symlink into a component runtime dir
        try:
            resolved = cron_dir.resolve(strict=True)
        except (OSError, RuntimeError):
            # Recorded, never dropped: a profile with no cron directory is a fact
            # about the fleet, and silently omitting it is how gaps hide.
            profiles.append(
                {
                    "profile": profile,
                    "cron_dir": "",
                    "cron_dir_shared_with": "",
                    "jobs_total": 0,
                    "jobs_enabled": 0,
                    "jobs_readable": True,
                    "ticker_present": False,
                    "ticker_age_seconds": -1,
                    "ticker_stale": False,
                    "reason": "no cron directory",
                }
            )
            continue
        record: dict[str, Any] = {
            "profile": profile,
            "cron_dir": _clip(str(resolved), 200),
            "cron_dir_shared_with": seen_cron_dirs.get(str(resolved), ""),
            "jobs_total": 0,
            "jobs_enabled": 0,
            "jobs_readable": True,
        }
        seen_cron_dirs.setdefault(str(resolved), profile)
        record.update(_read_ticker(resolved, now, stale_seconds))

        jobs_path = resolved / "jobs.json"
        if jobs_path.exists():
            try:
                document = json.loads(jobs_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                record["jobs_readable"] = False
                record["reason"] = _clip(f"{jobs_path}: {type(exc).__name__}", 160)
                profiles.append(record)
                continue
            raw_jobs = document.get("jobs") if isinstance(document, dict) else None
            if not isinstance(raw_jobs, list):
                record["jobs_readable"] = False
                record["reason"] = _clip(f"{jobs_path}: no jobs array", 160)
                profiles.append(record)
                continue
            skill_config = _load_profile_skill_config(entry) if raw_jobs else {}
            disabled = set(_str_list(skill_config.get("disabled")))

            def roots_for(workdir: str | None, _entry: Path = entry, _cfg: dict = skill_config):
                return _skill_roots(_entry, _cfg, workdir)

            for raw_job in raw_jobs:
                job = _read_job(raw_job, profile, resolved, roots_for, disabled, alias_cache, now)
                jobs.append(job)
                record["jobs_total"] += 1
                record["jobs_enabled"] += 1 if job.get("enabled") else 0
        profiles.append(record)
    return profiles, jobs, ""


# --------------------------------------------------------------------------- #
# assembly                                                                    #
# --------------------------------------------------------------------------- #


def _gateway_model(unit: str, host_units: list[str], units_known: set[str]) -> str:
    """Which gateway model a registry row's ``systemd.gateway_unit`` reflects.

    ``host``               no per-agent name, or it names the host gateway
    ``retired-per-agent``  names ``hermes-<agent>-gateway.service``, which
                           systemd has never loaded: a stale projection of the
                           retired model, served by the host gateway anyway
    ``per-agent-loaded``   names a per-agent unit systemd HAS loaded: it
                           competes with the host gateway for the host role
    ``other``              names some other unit systemd has loaded
    ``unknown``            names some other unit systemd does not know
    """
    if not unit or unit in host_units:
        return "host"
    if PER_AGENT_GATEWAY_RE.match(unit):
        return "per-agent-loaded" if unit in units_known else "retired-per-agent"
    return "other" if unit in units_known else "unknown"


def _agent_records(
    agents: dict[str, Any],
    profiles_dir: Path,
    unit_states: dict[str, str],
    units_known: set[str],
    host_units: list[str],
) -> list[dict[str, Any]]:
    records = []
    host = host_units[0] if host_units else ""
    for name, value in sorted(agents.items()):
        entry = value if isinstance(value, dict) else {}
        systemd = entry.get("systemd") if isinstance(entry.get("systemd"), dict) else {}
        profile_name = _clip(entry.get("profile_name"), 64)
        gateway_unit = _clip(systemd.get("gateway_unit"), 96)
        heartbeat_timer = _clip(systemd.get("heartbeat_timer"), 96)
        present = False
        if profile_name and "/" not in profile_name:
            try:
                present = (profiles_dir / profile_name).is_dir()
            except OSError:
                present = False
        model = _gateway_model(gateway_unit, host_units, units_known)
        served_by = host if model in {"host", "retired-per-agent"} else gateway_unit
        records.append(
            {
                "agent": _clip(name, 64),
                "profile_name": profile_name,
                "profile_dir_present": present,
                "gateway_unit": gateway_unit,
                "gateway_unit_known": bool(gateway_unit) and gateway_unit in units_known,
                "gateway_unit_active": unit_states.get(gateway_unit, "") == "active",
                "gateway_model": model,
                "served_by": served_by,
                "heartbeat_timer": heartbeat_timer,
                "heartbeat_timer_known": bool(heartbeat_timer) and heartbeat_timer in units_known,
            }
        )
    return records


def _link_candybars(
    candybars: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
) -> None:
    """Cross-check each candybar that names a Hermes job against the fleet.

    Candybar records ``success`` when ``hermes cron run`` exits 0. A runner
    aimed at a profile that no longer exists, or at a job whose skills do not
    resolve, can still exit 0 having done nothing useful -- the 2026-08-18
    shape. Mutates both lists in place: the candybar gets
    ``hermes_target_problem``, the job gets the candybar's name.
    """
    by_key = {f"{job['profile']}:{job['job_id']}": job for job in jobs if job["job_id"]}
    known_profiles = {profile["profile"] for profile in profiles}
    for candybar in candybars:
        target = candybar.get("hermes_target") or ""
        if not target:
            continue
        profile_name, _, job_id = target.partition(":")
        job = by_key.get(target)
        if profile_name not in known_profiles:
            candybar["hermes_target_problem"] = f"profile {profile_name} does not exist"
        elif job is None:
            candybar["hermes_target_problem"] = (
                f"job {job_id} is not in {profile_name}'s cron/jobs.json"
            )
        else:
            job["candybar"] = candybar.get("name") or ""
            problems = []
            if job["scheduler"] != "external":
                problems.append(
                    "job is not pinned scheduler=external (the Hermes ticker can fire it too)"
                    if job["pinned_enabled"]
                    else "job is not pinned scheduler=external"
                )
            if job["missing_skills"]:
                problems.append("skill(s) do not resolve: " + ", ".join(job["missing_skills"]))
            candybar["hermes_target_problem"] = "; ".join(problems)


def _render(observed: dict[str, Any], metrics: dict[str, Any], limit: int) -> list[str]:
    lines: list[str] = [
        f"observed at {observed['observed_at']} (fleet state is current, not reconstructed "
        "for the report date)",
    ]

    host = observed.get("host_gateway") or {}
    if host.get("unit"):
        state = (
            f"{host['load_state']}/{host['active_state']}/{host['sub_state']}"
            if host.get("load_state")
            else "unknown to systemd"
        )
        lines.append(
            f"gateway: {host['unit']} {state} -- the one host gateway; it serves "
            f"{metrics['agents_served_by_host_gateway']} of {metrics['agents_registered']} "
            "registered agents (there is no per-agent gateway unit)"
        )
    for unit in observed.get("per_agent_gateway_units") or []:
        lines.append(
            f"  CONFLICT {unit['unit']}: {unit['load_state']}/{unit['active_state']}/"
            f"{unit['sub_state']} -- a per-agent gateway unit beside the host gateway "
            "competes for the host role (2026-10-20 incident); retire it through flume and "
            "hand over with hermes-gateway-restart --reason"
        )

    lines.append(
        f"registry: {metrics['agents_registered']} agents, "
        f"{metrics['agent_profile_dirs_missing']} missing profile dir(s), "
        f"{metrics['registry_retired_gateway_rows']} row(s) naming a retired per-agent "
        f"gateway unit, {metrics['gateway_units_unknown']} naming an unknown unit"
    )
    retired = [agent for agent in observed["agents"] if agent["gateway_model"] == "retired-per-agent"]
    if retired:
        names = ", ".join(agent["agent"] for agent in retired[:12])
        more = f" and {len(retired) - 12} more" if len(retired) > 12 else ""
        lines.append(
            f"  {len(retired)} registry row(s) still carry systemd.gateway_unit = "
            "hermes-<agent>-gateway.service, a unit the single-gateway model never creates "
            f"({names}{more}). Stale projection, not an outage: these agents are served by "
            "the host gateway. Fix the writer (hermes-agent-template 80-registry.sh, flume "
            "handbook service_model), then reprovision."
        )
    for agent in observed["agents"]:
        problems = []
        if agent["profile_name"] and not agent["profile_dir_present"]:
            problems.append(f"profile dir {agent['profile_name']} absent")
        if agent["gateway_model"] == "unknown":
            problems.append(f"{agent['gateway_unit']} unknown to systemd")
        elif agent["gateway_model"] in {"per-agent-loaded", "other"} and not agent["gateway_unit_active"]:
            problems.append(f"{agent['gateway_unit']} not active")
        if agent["heartbeat_timer"] and not agent["heartbeat_timer_known"]:
            problems.append(f"{agent['heartbeat_timer']} unknown to systemd (retired heartbeat timer)")
        if problems:
            lines.append(f"  agent {agent['agent']}: " + "; ".join(problems))

    lines.append(
        f"systemd units: {metrics['units_total']} matching, {metrics['units_failed']} failed, "
        f"{metrics['units_not_found']} not-found"
    )
    for unit in observed["units"]:
        if unit["active_state"] == "failed" or unit["load_state"] == "not-found":
            lines.append(
                f"  unit {unit['unit']}: {unit['load_state']}/{unit['active_state']}/"
                f"{unit['sub_state']}"
            )

    lines.append(
        f"timers: {metrics['timers_total']} matching, {metrics['timers_active']} active, "
        f"{metrics['timers_failed']} failed, {metrics['timers_without_next_elapse']} with no "
        f"next elapse, {metrics['timers_never_triggered']} never triggered, "
        f"{metrics['timers_outside_candybar']} active outside Candybar's exception register"
    )
    for timer in observed["timers"]:
        flags = []
        if timer["active_state"] not in {"active", ""}:
            flags.append(timer["active_state"] or "unknown state")
        if timer["no_next_elapse"]:
            flags.append("no next elapse")
        if timer["never_triggered"]:
            flags.append("never triggered")
        if timer.get("policy_exempt") is True:
            flags.append("Candybar policy exception")
        elif timer.get("policy_exempt") is False and timer["active_state"] == "active":
            flags.append("second clock: not in candybar deploy/scheduling-policy.json")
        if flags:
            lines.append(
                f"  timer {timer['unit']}: {', '.join(flags)} "
                f"(last {timer['last_trigger_at'] or 'never'})"
            )

    lines.append(
        f"cron: {metrics['profiles_scanned']} profiles scanned "
        f"({metrics['profiles_without_cron_dir']} without a cron dir), "
        f"{metrics['profiles_with_cron_jobs']} with jobs, "
        f"{metrics['cron_jobs_total']} jobs: {metrics['cron_jobs_candybar']} pinned to Candybar, "
        f"{metrics['cron_jobs_enabled']} Hermes-native enabled (a second clock), "
        f"{metrics['cron_jobs_dormant']} dormant; "
        f"{metrics['profiles_with_stale_ticker']} stale ticker(s), "
        f"{metrics['duplicate_cron_dirs']} shared cron dir(s)"
    )
    for profile in observed["profiles"]:
        notes = []
        if not profile["jobs_readable"]:
            notes.append(f"jobs unreadable ({profile.get('reason', 'unknown')})")
        if profile["jobs_enabled"] and profile["ticker_stale"]:
            notes.append(
                "ticker absent"
                if not profile["ticker_present"]
                else f"ticker last moved {profile['ticker_age_seconds']}s ago"
            )
        if profile["cron_dir_shared_with"]:
            notes.append(f"shares its cron dir with {profile['cron_dir_shared_with']}")
        if notes:
            lines.append(f"  profile {profile['profile']}: " + "; ".join(notes))

    dormant: list[str] = []
    for job in observed["jobs"]:
        label = f"{job['profile']}/{job['name'] or job['job_id']}"
        if job["schedule_owner"] == "dormant":
            dormant.append(label)
            continue
        if job["schedule_owner"] == "candybar":
            # The Hermes ledger's next_run_at/last_status are not the source of
            # truth for a job whose schedule belongs to candybar; its run facts
            # appear in the candybar block below.
            note = (
                f"  job {label}: scheduler=external (candybar-managed"
                + (f" by {job['candybar']}" if job["candybar"] else "")
                + "; schedule and run facts in the candybar registry)"
            )
            if job["missing_skills"]:
                note += (
                    f"; skill(s) not installed for this profile: {', '.join(job['missing_skills'])}"
                    " -- a Candybar run executes the job without them"
                )
            lines.append(note)
            continue
        claim = job["last_status"] or "never run"
        note = (
            f"  job {label}: Hermes-native, enabled, schedule '{job['schedule'] or '?'}', "
            f"last_status='{claim}' (claim, {job['verification']}), "
            f"last run {job['last_run_at'] or 'never'}, next {job['next_run_at'] or 'none'}"
        )
        if job["missing_skills"]:
            note += f"; skill(s) not installed: {', '.join(job['missing_skills'])}"
        if job["next_run_in_past"]:
            note += "; next run is in the past"
        if job["last_error_present"]:
            note += f"; last_error recorded ({job['last_error_chars']} chars, not copied here)"
        lines.append(note)
    if dormant:
        lines.append(
            f"  {len(dormant)} dormant Hermes cron entr(ies) -- disabled, unpinned, scheduled by "
            f"nothing; their last_status is history, not a claim: {', '.join(dormant)}. Remove "
            "them or migrate them to Candybar."
        )

    if "candybars" in observed:
        lines.append(
            f"candybar: {metrics['candybars_total']} registered "
            f"({metrics['candybars_enabled']} enabled), "
            f"{metrics['candybars_last_run_failed']} last-run failure(s), "
            f"{metrics['candybars_hermes_target_broken']} Hermes runner target problem(s)"
        )
        healthy: list[str] = []
        for candybar in observed["candybars"]:
            # An enabled candybar whose last run succeeded and whose target is
            # sound is not news; it is counted on one line, not given its own.
            if (
                candybar["enabled"]
                and candybar["last_result"] == "success"
                and not candybar.get("hermes_target_problem")
            ):
                healthy.append(candybar["name"] or "?")
                continue
            flags = []
            if not candybar["enabled"]:
                flags.append("disabled")
            if candybar["last_result"] == "fail":
                flags.append(
                    f"last run failed ({candybar['last_trigger'] or '?'} "
                    f"{candybar['last_finished_at'] or '?'})"
                )
            elif candybar["last_result"] == "success":
                flags.append(
                    f"last run succeeded ({candybar['last_trigger'] or '?'} "
                    f"{candybar['last_finished_at'] or '?'})"
                )
            else:
                flags.append("no invocation recorded yet")
            if candybar.get("hermes_target_problem"):
                flags.append(
                    f"runs hermes {candybar['hermes_target']} but "
                    f"{candybar['hermes_target_problem']}"
                )
            lines.append(
                f"  candybar {candybar['name'] or '?'}: {', '.join(flags)} "
                f"('{candybar['schedule'] or '?'}' {candybar['timezone'] or 'UTC'})"
            )
        if healthy:
            lines.append(
                f"  {len(healthy)} enabled candybar(s) whose last run succeeded: "
                + ", ".join(sorted(healthy))
            )

    if len(lines) > limit:
        kept = lines[:limit]
        kept.append(f"detail truncated: showing {limit} of {len(lines)} lines")
        return kept
    return lines


def _collect(section_cfg: dict[str, Any], report_date: str) -> SectionResult:
    options = section_cfg.get("options") if isinstance(section_cfg, dict) else {}
    hermes_home = _path_option(options, "hermes_home", Path(DEFAULT_HERMES_HOME).expanduser())
    registry_path = _path_option(options, "registry_path", hermes_home / "agents-registry.yaml")
    profiles_dir = _path_option(options, "profiles_dir", hermes_home / "profiles")
    policy_path = _path_option(
        options, "scheduling_policy_path", Path(DEFAULT_SCHEDULING_POLICY).expanduser()
    )
    unit_prefix = str(_option(options, "unit_prefix", "hermes-"))
    host_option = _clip(str(_option(options, "host_gateway_unit", DEFAULT_HOST_GATEWAY_UNIT)), 96)
    stale_seconds = _int_option(
        options, "ticker_stale_seconds", DEFAULT_TICKER_STALE_SECONDS, low=30, high=86_400
    )
    timeout = _int_option(
        options, "systemctl_timeout_seconds", DEFAULT_COMMAND_TIMEOUT, low=1, high=120
    )
    limit = _int_option(
        options, "max_detail_lines", DEFAULT_MAX_DETAIL_LINES, low=10, high=2_000
    )
    candybar_url = _clip(str(_option(options, "candybar_api_url", DEFAULT_CANDYBAR_API_URL)), 200)
    http_timeout = _int_option(
        options, "candybar_http_timeout_seconds", DEFAULT_HTTP_TIMEOUT, low=1, high=60
    )

    now = _now()
    caveats: list[str] = []
    failures: dict[str, str] = {}
    source_ids = SOURCE_IDS + ((CANDYBAR_SOURCE_ID,) if candybar_url else ())

    agents, gateways, reason = _read_registry(registry_path)
    if reason:
        failures["agents-registry"] = reason
    host_units = _host_gateway_units(gateways, host_option)

    units, reason = _read_units(f"{unit_prefix}*", timeout)
    if reason:
        failures["systemd-units"] = reason

    timer_times, reason = _read_timers(unit_prefix, timeout)
    if reason:
        failures["systemd-timers"] = reason

    profiles, jobs, reason = _read_profiles(profiles_dir, now, stale_seconds)
    if reason:
        failures["hermes-profiles"] = reason

    candybars: list[dict[str, Any]] | None = None
    if candybar_url:
        candybars, reason = _read_candybars(candybar_url, http_timeout)
        if reason:
            failures[CANDYBAR_SOURCE_ID] = reason
        else:
            _link_candybars(candybars, jobs, profiles)

    # Optional, so never a source failure: without it timers are not classified.
    exemptions, policy_reason = _read_policy_exemptions(policy_path)
    policy_known = not policy_reason

    unit_states = {unit["unit"]: unit["active_state"] for unit in units}
    units_known = {unit["unit"] for unit in units if unit["load_state"] != "not-found"}
    timer_units = [unit for unit in units if unit["kind"] == "timer"]
    timers = [
        {
            **unit,
            **timer_times.get(
                unit["unit"],
                {
                    "last_trigger_at": None,
                    "next_elapse_at": None,
                    "never_triggered": True,
                    "no_next_elapse": True,
                },
            ),
            **({"policy_exempt": unit["unit"] in exemptions} if policy_known else {}),
        }
        for unit in timer_units
    ]
    if timer_units and not timer_times and "systemd-timers" not in failures:
        caveats.append("systemctl list-timers returned no hermes-* rows for known timer units")

    host_unit = host_units[0] if host_units else ""
    host_row = next((unit for unit in units if unit["unit"] == host_unit), None)
    host_gateway = {
        "unit": host_unit,
        "load_state": host_row["load_state"] if host_row else "",
        "active_state": host_row["active_state"] if host_row else "",
        "sub_state": host_row["sub_state"] if host_row else "",
    }
    host_active = bool(host_row) and host_row["active_state"] == "active"
    per_agent_units = [
        unit
        for unit in units
        if PER_AGENT_GATEWAY_RE.match(unit["unit"])
        and unit["unit"] not in host_units
        and unit["load_state"] != "not-found"
    ]

    agent_records = _agent_records(agents, profiles_dir, unit_states, units_known, host_units)
    profiles_with_jobs = [profile for profile in profiles if profile["jobs_total"] > 0]
    live_jobs = [job for job in jobs if job["schedule_owner"] != "dormant"]

    metrics: dict[str, Any] = {
        "agents_registered": len(agent_records),
        "agent_profile_dirs_missing": sum(
            1 for agent in agent_records if agent["profile_name"] and not agent["profile_dir_present"]
        ),
        "host_gateway_unit": host_unit,
        "host_gateway_active": host_active,
        "agents_served_by_host_gateway": sum(
            1 for agent in agent_records if agent["served_by"] == host_unit
        ),
        "agents_unserved": sum(
            1 for agent in agent_records if unit_states.get(agent["served_by"], "") != "active"
        ),
        "registry_retired_gateway_rows": sum(
            1 for agent in agent_records if agent["gateway_model"] == "retired-per-agent"
        ),
        "per_agent_gateway_units_loaded": len(per_agent_units),
        "gateway_units_unknown": sum(
            1 for agent in agent_records if agent["gateway_model"] == "unknown"
        ),
        "gateway_units_inactive": sum(
            1
            for agent in agent_records
            if agent["gateway_model"] in {"per-agent-loaded", "other"}
            and not agent["gateway_unit_active"]
        ),
        "units_total": len(units),
        "units_failed": sum(1 for unit in units if unit["active_state"] == "failed"),
        "units_not_found": sum(1 for unit in units if unit["load_state"] == "not-found"),
        "timers_total": len(timers),
        "timers_active": sum(1 for timer in timers if timer["active_state"] == "active"),
        "timers_failed": sum(1 for timer in timers if timer["active_state"] == "failed"),
        "timers_without_next_elapse": sum(1 for timer in timers if timer["no_next_elapse"]),
        "timers_never_triggered": sum(1 for timer in timers if timer["never_triggered"]),
        "timers_outside_candybar": sum(
            1
            for timer in timers
            if timer.get("policy_exempt") is False and timer["active_state"] == "active"
        ),
        "profiles_scanned": len(profiles),
        "profiles_without_cron_dir": sum(1 for profile in profiles if not profile["cron_dir"]),
        "profiles_with_cron_jobs": len(profiles_with_jobs),
        "profiles_unreadable_jobs": sum(1 for profile in profiles if not profile["jobs_readable"]),
        "profiles_with_stale_ticker": sum(
            1 for profile in profiles if profile["jobs_enabled"] and profile["ticker_stale"]
        ),
        "duplicate_cron_dirs": sum(1 for profile in profiles if profile["cron_dir_shared_with"]),
        "cron_jobs_total": len(jobs),
        "cron_jobs_enabled": sum(1 for job in jobs if job["schedule_owner"] == "hermes"),
        "cron_jobs_candybar": sum(1 for job in jobs if job["schedule_owner"] == "candybar"),
        "cron_jobs_dormant": sum(1 for job in jobs if job["schedule_owner"] == "dormant"),
        "cron_jobs_unreadable": sum(1 for job in jobs if job["verification"] == "unreadable"),
        # Only jobs something will actually run: a dormant entry's skills are moot.
        "jobs_with_missing_skill": sum(1 for job in live_jobs if job["missing_skills"]),
        "jobs_claiming_ok_unverified": sum(
            1 for job in jobs if job["verification"] == "unverified"
        ),
        "jobs_claiming_ok_contradicted": sum(
            1 for job in jobs if job["verification"] == "contradicted"
        ),
        "jobs_with_past_next_run": sum(1 for job in jobs if job["next_run_in_past"]),
        "sources_read": len(source_ids) - len(failures),
        "sources_failed": len(failures),
        "report_date": report_date,
    }
    if candybars is not None:
        metrics["candybars_total"] = len(candybars)
        metrics["candybars_enabled"] = sum(1 for cb in candybars if cb["enabled"])
        metrics["candybars_last_run_failed"] = sum(
            1 for cb in candybars if cb["last_result"] == "fail"
        )
        metrics["candybars_hermes_target_broken"] = sum(
            1 for cb in candybars if cb.get("hermes_target_problem")
        )

    # Structural field allowlist: assembled records are filtered again on the way
    # out, so a raw jobs.json field (a prompt, a base_url) cannot ride along.
    observed = allowlist(
        {
            "observed_at": _iso(now),
            "sources": [
                {"source": source, "ok": source not in failures, "reason": failures.get(source, "")}
                for source in source_ids
            ],
            "host_gateway": host_gateway,
            "per_agent_gateway_units": per_agent_units,
            "agents": agent_records,
            "units": units,
            "timers": timers,
            "profiles": profiles,
            "jobs": jobs,
            **({"candybars": candybars} if candybars is not None else {}),
        },
        FLEET_FIELDS,
        opaque_keys=frozenset(),
    )

    for source, message in sorted(failures.items()):
        caveats.append(f"source {source} unavailable: {_clip(message, 200)}")
    for profile in observed["profiles"]:
        if not profile["jobs_readable"]:
            caveats.append(
                f"profile {profile['profile']}: cron jobs unreadable "
                f"({profile.get('reason', 'unknown')})"
            )
    if "systemd-units" not in failures and host_unit and not host_active:
        caveats.append(
            f"host gateway {host_unit} is not active: every agent it serves "
            f"({metrics['agents_served_by_host_gateway']}) is unserved"
        )
    if per_agent_units:
        caveats.append(
            f"{len(per_agent_units)} per-agent gateway unit(s) loaded beside the host gateway "
            f"({', '.join(unit['unit'] for unit in per_agent_units[:5])}): a second gateway "
            "competes for the host role; retire it"
        )
    if metrics["registry_retired_gateway_rows"]:
        caveats.append(
            f"{metrics['registry_retired_gateway_rows']} registry row(s) name a retired per-agent "
            "gateway unit (stale projection of the pre-2026-10-11 model; the agents are served "
            "by the host gateway -- registry drift, not an outage)"
        )
    if metrics["cron_jobs_enabled"]:
        caveats.append(
            f"{metrics['cron_jobs_enabled']} Hermes-native cron job(s) are enabled and unpinned: "
            "a second clock beside Candybar"
        )
    if metrics["timers_outside_candybar"]:
        caveats.append(
            f"{metrics['timers_outside_candybar']} active hermes-* timer(s) are not in Candybar's "
            "exception register: a second clock"
        )
    if candybars is not None and metrics["candybars_hermes_target_broken"]:
        caveats.append(
            f"{metrics['candybars_hermes_target_broken']} candybar(s) run a Hermes job that is "
            "missing, unpinned, or missing skills; a 'success' there can be a run that did "
            "nothing"
        )
    if metrics["jobs_claiming_ok_unverified"]:
        caveats.append(
            f"{metrics['jobs_claiming_ok_unverified']} cron job(s) report last_status='ok' with no "
            "independent corroboration; last_status is a scheduler claim and is not treated as "
            "evidence of success"
        )
    if metrics["jobs_claiming_ok_contradicted"]:
        caveats.append(
            f"{metrics['jobs_claiming_ok_contradicted']} cron job(s) report last_status='ok' while "
            "an observable fact contradicts it"
        )

    if len(failures) == len(source_ids):
        return SectionResult(
            id=SECTION_ID,
            status="failed",
            reason="every fleet source was unreachable: "
            + "; ".join(f"{source}: {_clip(message, 120)}" for source, message in sorted(failures.items())),
            summary="Hermes fleet health could not be collected: no source was readable.",
            metrics=metrics,
            caveats=caveats,
            generated_at=now,
        )

    detail = _render(observed, metrics, limit)
    if "systemd-units" in failures:
        gateway_text = f"host gateway {host_unit or '?'} state unknown (systemd unreadable)"
    else:
        gateway_text = (
            f"host gateway {host_unit or '?'} {'active' if host_active else 'NOT active'} "
            f"serving {metrics['agents_served_by_host_gateway']}"
        )
    summary = (
        f"Hermes fleet: {metrics['agents_registered']} agents registered; {gateway_text}; "
        f"{metrics['per_agent_gateway_units_loaded']} per-agent gateway unit(s) loaded; "
        f"{metrics['registry_retired_gateway_rows']} registry row(s) still name a retired "
        f"per-agent unit. {metrics['timers_total']} timers ({metrics['timers_active']} active, "
        f"{metrics['timers_failed']} failed, {metrics['timers_outside_candybar']} outside "
        f"Candybar). {metrics['cron_jobs_total']} Hermes cron jobs across "
        f"{metrics['profiles_with_cron_jobs']} profiles: {metrics['cron_jobs_candybar']} "
        f"Candybar-run, {metrics['cron_jobs_enabled']} Hermes-native, "
        f"{metrics['cron_jobs_dormant']} dormant; {metrics['jobs_with_missing_skill']} live job(s) "
        f"reference a skill that does not resolve for its profile; "
        f"{metrics['profiles_with_stale_ticker']} profile(s) with a stale ticker."
    )
    if candybars is not None:
        summary += (
            f" Candybar: {metrics['candybars_total']} registered "
            f"({metrics['candybars_enabled']} enabled, "
            f"{metrics['candybars_last_run_failed']} last-run failed, "
            f"{metrics['candybars_hermes_target_broken']} with a broken Hermes target)."
        )

    partial_reasons: list[str] = []
    if failures:
        partial_reasons.append(
            "unread source(s): "
            + ", ".join(f"{source} ({_clip(message, 80)})" for source, message in sorted(failures.items()))
        )
    if metrics["profiles_unreadable_jobs"]:
        partial_reasons.append(
            f"{metrics['profiles_unreadable_jobs']} profile(s) had unreadable cron jobs"
        )
    if metrics["cron_jobs_unreadable"]:
        partial_reasons.append(
            f"{metrics['cron_jobs_unreadable']} cron job entr(ies) were malformed"
        )
    if partial_reasons:
        return SectionResult(
            id=SECTION_ID,
            status="partial",
            reason="; ".join(partial_reasons),
            summary=summary,
            metrics=metrics,
            detail=detail,
            caveats=caveats,
            generated_at=now,
        )

    return SectionResult(
        id=SECTION_ID,
        status="complete",
        summary=summary,
        metrics=metrics,
        detail=detail,
        caveats=caveats,
        generated_at=now,
    )


def collect(
    section_cfg: dict[str, Any],
    report_date: str | None = None,
    config: dict[str, Any] | None = None,
    *,
    date: str | None = None,
) -> SectionResult:
    """Collect Hermes fleet health. Never raises; failures become ``failed``.

    ``report_date`` may also arrive as the keyword ``date`` -- that is how
    ``reportctl collect`` invokes collectors today. ``config`` is accepted for
    contract parity; this collector reads only its own section options.
    """
    resolved_date = report_date or date or ""
    return run_collector(lambda cfg: _collect(cfg, resolved_date), section_cfg)


# --------------------------------------------------------------------------- #
# standalone entry point                                                      #
# --------------------------------------------------------------------------- #


def _section_from_config(path: str, section_id: str) -> dict[str, Any]:
    from reportctl_config import load_config

    config = load_config(Path(path))
    for section in config["sections"]:
        if section["id"] == section_id or section["collector"] == "fleet_health":
            return section
    raise ConfigError(f"no section using the fleet_health collector in {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="collectors.fleet_health",
        description="Collect Hermes fleet health and print the SectionArtifact JSON.",
    )
    parser.add_argument("--date", required=True, help="report date, YYYY-MM-DD")
    parser.add_argument("--config", help="operator config; the fleet_health section is used")
    parser.add_argument("--section-id", default=SECTION_ID)
    parser.add_argument("--run-id", help="reuse an existing run identifier")
    args = parser.parse_args(argv)

    run_id = args.run_id or f"fleet-health-{args.date}-{uuid.uuid4().hex[:8]}"
    section_cfg: dict[str, Any] = {
        "id": args.section_id,
        "collector": "fleet_health",
        "max_age_hours": DEFAULT_MAX_AGE_HOURS,
        "options": {},
    }
    result: SectionResult | None = None
    if args.config:
        try:
            section_cfg = _section_from_config(args.config, args.section_id)
        except (ConfigError, OSError) as exc:
            result = SectionResult(
                id=args.section_id,
                status="failed",
                reason=f"config unusable: {_clip(str(exc), 200)}",
                summary=f"{args.section_id}: configuration could not be loaded",
            )
    if result is None:
        result = collect(section_cfg, args.date, None)

    try:
        artifact = result.to_artifact(run_id, int(section_cfg.get("max_age_hours", DEFAULT_MAX_AGE_HOURS)))
    except ConfigError as exc:
        print(json.dumps({"error": f"artifact invalid: {exc}"}, indent=2), file=sys.stderr)
        return 4
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return 0 if artifact["status"] == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
