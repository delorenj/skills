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

What is treated as evidence
---------------------------
* does the referenced skill actually resolve to a ``SKILL.md`` under
  ``~/.hermes/skills`` (a broken symlink resolves to nothing -- this is the exact
  shape of the 2026-08-18 failure);
* does the profile directory named by the registry exist;
* does the systemd unit named by the registry exist, and is it active;
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
import sys
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
        "verification",
        "output_files",
        "output_latest_at",
    }
)

#: The four sources this section needs. ``complete`` requires all four.
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


def _read_registry(path: Path) -> tuple[dict[str, Any], str]:
    """Return ``(agents, reason)``; a non-empty reason means the source failed."""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - PyYAML ships with the fleet
        return {}, f"PyYAML unavailable: {exc}"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, f"cannot read {path}: {exc.strerror or exc}"
    try:
        document = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return {}, f"cannot parse {path}: {type(exc).__name__}"
    if not isinstance(document, dict):
        return {}, f"{path} is not a YAML mapping"
    agents = document.get("agents")
    if not isinstance(agents, dict):
        return {}, f"{path} has no agents mapping"
    return agents, ""


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


def _resolve_skill(skills_dir: Path, name: str) -> bool:
    """True only when ``name`` resolves to a real skill (a readable SKILL.md).

    ``is_file`` follows symlinks, so a dangling ``~/.hermes/skills/<name>`` link
    -- precisely the 2026-08-18 failure -- resolves to False.
    """
    if not name or "/" in name or name in {".", ".."}:
        return False
    try:
        if (skills_dir / name / "SKILL.md").is_file():
            return True
        children = sorted(entry for entry in skills_dir.iterdir() if entry.is_dir())
    except OSError:
        return False
    for category in children:
        try:
            if (category / name / "SKILL.md").is_file():
                return True
        except OSError:
            continue
    return False


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
        "verification": "not-claimed",
        "output_files": 0,
        "output_latest_at": None,
    }


def _read_job(
    job: Any, profile: str, cron_dir: Path, skills_dir: Path, now: dt.datetime
) -> dict[str, Any]:
    if not isinstance(job, dict):
        record = _empty_job(profile)
        record["name"] = "<malformed job entry>"
        record["verification"] = "unreadable"
        return record
    job_id = _clip(job.get("id"), 64)
    skills = _job_skills(job)
    missing = [name for name in skills if not _resolve_skill(skills_dir, name)]
    next_run = _parse_dt(job.get("next_run_at"))
    last_run = _parse_dt(job.get("last_run_at"))
    enabled = job.get("enabled") is True
    last_status = _clip(job.get("last_status"), 32)
    last_error = job.get("last_error")
    error_present = isinstance(last_error, str) and bool(last_error.strip())
    schedule = job.get("schedule")
    schedule_expr = ""
    if isinstance(schedule, dict):
        schedule_expr = _clip(schedule.get("expr") or schedule.get("display"), 64)
    if not schedule_expr:
        schedule_expr = _clip(job.get("schedule_display"), 64)

    # last_status is a claim. It is only ever downgraded here, never trusted.
    if last_status != "ok" or last_run is None:
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
    profiles_dir: Path, skills_dir: Path, now: dt.datetime, stale_seconds: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    try:
        entries = sorted(entry for entry in profiles_dir.iterdir())
    except OSError as exc:
        return [], [], f"cannot list {profiles_dir}: {exc.strerror or exc}"

    profiles: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    seen_cron_dirs: dict[str, str] = {}
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
            for raw_job in raw_jobs:
                job = _read_job(raw_job, profile, resolved, skills_dir, now)
                jobs.append(job)
                record["jobs_total"] += 1
                record["jobs_enabled"] += 1 if job.get("enabled") else 0
        profiles.append(record)
    return profiles, jobs, ""


# --------------------------------------------------------------------------- #
# assembly                                                                    #
# --------------------------------------------------------------------------- #


def _agent_records(
    agents: dict[str, Any], profiles_dir: Path, unit_states: dict[str, str], units_known: set[str]
) -> list[dict[str, Any]]:
    records = []
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
        records.append(
            {
                "agent": _clip(name, 64),
                "profile_name": profile_name,
                "profile_dir_present": present,
                "gateway_unit": gateway_unit,
                "gateway_unit_known": bool(gateway_unit) and gateway_unit in units_known,
                "gateway_unit_active": unit_states.get(gateway_unit, "") == "active",
                "heartbeat_timer": heartbeat_timer,
                "heartbeat_timer_known": bool(heartbeat_timer) and heartbeat_timer in units_known,
            }
        )
    return records


def _render(observed: dict[str, Any], metrics: dict[str, Any], limit: int) -> list[str]:
    lines: list[str] = [
        f"observed at {observed['observed_at']} (fleet state is current, not reconstructed "
        "for the report date)",
        f"registry: {metrics['agents_registered']} agents, "
        f"{metrics['agent_profile_dirs_missing']} missing profile dir(s), "
        f"{metrics['gateway_units_unknown']} gateway unit(s) unknown to systemd, "
        f"{metrics['gateway_units_inactive']} not active",
    ]
    for agent in observed["agents"]:
        problems = []
        if agent["profile_name"] and not agent["profile_dir_present"]:
            problems.append(f"profile dir {agent['profile_name']} absent")
        if agent["gateway_unit"] and not agent["gateway_unit_known"]:
            problems.append(f"{agent['gateway_unit']} unknown to systemd")
        elif agent["gateway_unit"] and not agent["gateway_unit_active"]:
            problems.append(f"{agent['gateway_unit']} not active")
        if agent["heartbeat_timer"] and not agent["heartbeat_timer_known"]:
            problems.append(f"{agent['heartbeat_timer']} unknown to systemd")
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
        f"next elapse, {metrics['timers_never_triggered']} never triggered"
    )
    for timer in observed["timers"]:
        flags = []
        if timer["active_state"] not in {"active", ""}:
            flags.append(timer["active_state"] or "unknown state")
        if timer["no_next_elapse"]:
            flags.append("no next elapse")
        if timer["never_triggered"]:
            flags.append("never triggered")
        if flags:
            lines.append(
                f"  timer {timer['unit']}: {', '.join(flags)} "
                f"(last {timer['last_trigger_at'] or 'never'})"
            )

    lines.append(
        f"cron: {metrics['profiles_scanned']} profiles scanned "
        f"({metrics['profiles_without_cron_dir']} without a cron dir), "
        f"{metrics['profiles_with_cron_jobs']} with jobs, "
        f"{metrics['cron_jobs_total']} jobs ({metrics['cron_jobs_enabled']} enabled), "
        f"{metrics['profiles_with_stale_ticker']} stale ticker(s), "
        f"{metrics['duplicate_cron_dirs']} shared cron dir(s)"
    )
    for profile in observed["profiles"]:
        notes = []
        if not profile["jobs_readable"]:
            notes.append(f"jobs unreadable ({profile.get('reason', 'unknown')})")
        if profile["jobs_total"] and profile["ticker_stale"]:
            notes.append(
                "ticker absent"
                if not profile["ticker_present"]
                else f"ticker last moved {profile['ticker_age_seconds']}s ago"
            )
        if profile["cron_dir_shared_with"]:
            notes.append(f"shares its cron dir with {profile['cron_dir_shared_with']}")
        if notes:
            lines.append(f"  profile {profile['profile']}: " + "; ".join(notes))

    for job in observed["jobs"]:
        claim = job["last_status"] or "never run"
        note = (
            f"  job {job['profile']}/{job['name'] or job['job_id']}: "
            f"{'enabled' if job['enabled'] else 'disabled'}, schedule '{job['schedule'] or '?'}', "
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
    skills_dir = _path_option(options, "skills_dir", hermes_home / "skills")
    unit_prefix = str(_option(options, "unit_prefix", "hermes-"))
    stale_seconds = _int_option(
        options, "ticker_stale_seconds", DEFAULT_TICKER_STALE_SECONDS, low=30, high=86_400
    )
    timeout = _int_option(
        options, "systemctl_timeout_seconds", DEFAULT_COMMAND_TIMEOUT, low=1, high=120
    )
    limit = _int_option(
        options, "max_detail_lines", DEFAULT_MAX_DETAIL_LINES, low=10, high=2_000
    )

    now = _now()
    caveats: list[str] = []
    failures: dict[str, str] = {}

    agents, reason = _read_registry(registry_path)
    if reason:
        failures["agents-registry"] = reason

    units, reason = _read_units(f"{unit_prefix}*", timeout)
    if reason:
        failures["systemd-units"] = reason

    timer_times, reason = _read_timers(unit_prefix, timeout)
    if reason:
        failures["systemd-timers"] = reason

    profiles, jobs, reason = _read_profiles(profiles_dir, skills_dir, now, stale_seconds)
    if reason:
        failures["hermes-profiles"] = reason

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
        }
        for unit in timer_units
    ]
    if timer_units and not timer_times and "systemd-timers" not in failures:
        caveats.append("systemctl list-timers returned no hermes-* rows for known timer units")

    agent_records = _agent_records(agents, profiles_dir, unit_states, units_known)
    profiles_with_jobs = [profile for profile in profiles if profile["jobs_total"] > 0]

    metrics: dict[str, Any] = {
        "agents_registered": len(agent_records),
        "agent_profile_dirs_missing": sum(
            1 for agent in agent_records if agent["profile_name"] and not agent["profile_dir_present"]
        ),
        "gateway_units_unknown": sum(
            1 for agent in agent_records if agent["gateway_unit"] and not agent["gateway_unit_known"]
        ),
        "gateway_units_inactive": sum(
            1
            for agent in agent_records
            if agent["gateway_unit"] and agent["gateway_unit_known"] and not agent["gateway_unit_active"]
        ),
        "units_total": len(units),
        "units_failed": sum(1 for unit in units if unit["active_state"] == "failed"),
        "units_not_found": sum(1 for unit in units if unit["load_state"] == "not-found"),
        "timers_total": len(timers),
        "timers_active": sum(1 for timer in timers if timer["active_state"] == "active"),
        "timers_failed": sum(1 for timer in timers if timer["active_state"] == "failed"),
        "timers_without_next_elapse": sum(1 for timer in timers if timer["no_next_elapse"]),
        "timers_never_triggered": sum(1 for timer in timers if timer["never_triggered"]),
        "profiles_scanned": len(profiles),
        "profiles_without_cron_dir": sum(1 for profile in profiles if not profile["cron_dir"]),
        "profiles_with_cron_jobs": len(profiles_with_jobs),
        "profiles_unreadable_jobs": sum(1 for profile in profiles if not profile["jobs_readable"]),
        "profiles_with_stale_ticker": sum(
            1 for profile in profiles_with_jobs if profile["ticker_stale"]
        ),
        "duplicate_cron_dirs": sum(1 for profile in profiles if profile["cron_dir_shared_with"]),
        "cron_jobs_total": len(jobs),
        "cron_jobs_enabled": sum(1 for job in jobs if job["enabled"]),
        "cron_jobs_unreadable": sum(1 for job in jobs if job["verification"] == "unreadable"),
        "jobs_with_missing_skill": sum(1 for job in jobs if job["missing_skills"]),
        "jobs_claiming_ok_unverified": sum(
            1 for job in jobs if job["verification"] == "unverified"
        ),
        "jobs_claiming_ok_contradicted": sum(
            1 for job in jobs if job["verification"] == "contradicted"
        ),
        "jobs_with_past_next_run": sum(1 for job in jobs if job["next_run_in_past"]),
        "sources_read": len(SOURCE_IDS) - len(failures),
        "sources_failed": len(failures),
        "report_date": report_date,
    }

    # Structural field allowlist: assembled records are filtered again on the way
    # out, so a raw jobs.json field (a prompt, a base_url) cannot ride along.
    observed = allowlist(
        {
            "observed_at": _iso(now),
            "sources": [
                {"source": source, "ok": source not in failures, "reason": failures.get(source, "")}
                for source in SOURCE_IDS
            ],
            "agents": agent_records,
            "units": units,
            "timers": timers,
            "profiles": profiles,
            "jobs": jobs,
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

    if len(failures) == len(SOURCE_IDS):
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
    summary = (
        f"Hermes fleet: {metrics['agents_registered']} agents registered; "
        f"{metrics['timers_total']} timers ({metrics['timers_active']} active, "
        f"{metrics['timers_failed']} failed); {metrics['cron_jobs_total']} cron jobs across "
        f"{metrics['profiles_with_cron_jobs']} profiles ({metrics['cron_jobs_enabled']} enabled); "
        f"{metrics['jobs_with_missing_skill']} job(s) reference a missing skill; "
        f"{metrics['profiles_with_stale_ticker']} profile(s) with a stale ticker; "
        f"{metrics['gateway_units_inactive'] + metrics['gateway_units_unknown']} gateway unit(s) "
        f"not running."
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
