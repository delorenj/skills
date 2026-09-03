"""systemd user timer per project: template units plus a per-project drop-in.

`assets/systemd/activity-report@.service` and `.timer` are copied verbatim to
`~/.config/systemd/user/`; the project's time and zone go in
`activity-report@<slug>.timer.d/schedule.conf`, which resets OnCalendar and
sets it again. `install-timer` is the only place that enables anything.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess

from .common import EXIT_OK, ConfigError, write_text

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
ASSETS_SYSTEMD = os.path.join(SKILL_ROOT, "assets", "systemd")
UNITS = ("activity-report@.service", "activity-report@.timer")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def systemd_user_dir() -> str:
    root = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(root, "systemd", "user")


def timer_name(slug: str) -> str:
    return f"activity-report@{slug}.timer"


def service_name(slug: str) -> str:
    return f"activity-report@{slug}.service"


def dropin_path(slug: str, user_dir: str | None = None) -> str:
    return os.path.join(user_dir or systemd_user_dir(), f"{timer_name(slug)}.d", "schedule.conf")


def render_dropin(project) -> str:
    at = ((project.config or {}).get("schedule") or {}).get("at")
    if not isinstance(at, str) or not _TIME_RE.match(at):
        raise ConfigError(f"activity_report.schedule.at must be HH:MM, got {at!r}")
    tz = project.tz
    if not tz or any(ch.isspace() for ch in tz):
        raise ConfigError(f"activity_report.timezone {tz!r} cannot go in OnCalendar")
    return f"[Timer]\nOnCalendar=\nOnCalendar=*-*-* {at}:00 {tz}\n"


def _read(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _put(path: str, content: str) -> bool:
    """Write only when absent or different. Returns True when written."""
    if _read(path) == content:
        return False
    write_text(path, content)
    os.chmod(path, 0o644)
    return True


def install_units(user_dir: str) -> list[str]:
    changed = []
    for unit in UNITS:
        template = _read(os.path.join(ASSETS_SYSTEMD, unit))
        if template is None:
            raise ConfigError(f"template unit missing: {os.path.join(ASSETS_SYSTEMD, unit)}")
        if _put(os.path.join(user_dir, unit), template):
            changed.append(unit)
    return changed


def _systemctl(*args: str) -> subprocess.CompletedProcess:
    if not shutil.which("systemctl"):
        raise ConfigError("systemctl not found; this host does not run systemd")
    return subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True, check=False)


def _linger_enabled() -> bool | None:
    if not shutil.which("loginctl"):
        return None
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    proc = subprocess.run(["loginctl", "show-user", user, "--property=Linger"],
                          capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return None
    return "Linger=yes" in proc.stdout


def install_timer_cmd(args) -> int:
    from .config import load_project
    project = load_project(getattr(args, "project", None))
    shim = os.path.join(os.path.expanduser("~"), ".local", "bin", "activity-report")
    if not os.path.exists(shim):
        raise ConfigError(f"{shim} is missing; run `activity-report init` first "
                          "(the unit's ExecStart is %h/.local/bin/activity-report)")
    user_dir = systemd_user_dir()
    os.makedirs(user_dir, exist_ok=True)
    changed = install_units(user_dir)
    dropin = dropin_path(project.slug, user_dir)
    dropin_changed = _put(dropin, render_dropin(project))
    timer = timer_name(project.slug)

    reload = _systemctl("daemon-reload")
    if reload.returncode != 0:
        raise ConfigError(f"systemctl --user daemon-reload failed: {reload.stderr.strip()}")
    enable = _systemctl("enable", "--now", timer)
    if enable.returncode != 0:
        raise ConfigError(f"systemctl --user enable --now {timer} failed: {enable.stderr.strip()}")
    linger = _linger_enabled()
    listing = _systemctl("list-timers", timer, "--no-pager", "--all")

    result = {
        "timer": timer, "units_written": changed, "dropin": dropin, "dropin_written": dropin_changed,
        "schedule": render_dropin(project).strip().splitlines()[-1].split("=", 1)[1],
        "linger": linger, "list_timers": listing.stdout,
    }
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
        return EXIT_OK
    for unit in changed:
        print(f"installed {os.path.join(user_dir, unit)}")
    print(f"{'wrote' if dropin_changed else 'unchanged'} {dropin} ({result['schedule']})")
    print(f"enabled {timer}")
    if linger is False:
        print("note: lingering is off for this user, so the timer sleeps when you log out; "
              "run `sudo loginctl enable-linger $USER` once")
    print(listing.stdout.rstrip())
    return EXIT_OK


def timer_status_cmd(args) -> int:
    from .config import load_project
    project = load_project(getattr(args, "project", None))
    timer, service = timer_name(project.slug), service_name(project.slug)
    user_dir = systemd_user_dir()
    installed = os.path.isfile(os.path.join(user_dir, "activity-report@.timer"))
    dropin = _read(dropin_path(project.slug, user_dir))
    listing = _systemctl("list-timers", timer, "--no-pager", "--all")
    journal = None
    if shutil.which("journalctl"):
        journal = subprocess.run(["journalctl", "--user", "-u", service, "-n", "20", "--no-pager"],
                                 capture_output=True, text=True, check=False).stdout
    result = {
        "timer": timer, "service": service, "installed": installed, "enabled": dropin is not None,
        "dropin": dropin, "expected_dropin": render_dropin(project),
        "list_timers": listing.stdout, "journal": journal,
    }
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
        return EXIT_OK
    if not installed:
        print(f"{timer}: not installed (template units missing from {user_dir}); "
              f"run `activity-report install-timer --project {project.slug}`")
    elif dropin is None:
        print(f"{timer}: template units present but no drop-in for {project.slug}; "
              f"run `activity-report install-timer --project {project.slug}`")
    else:
        print(f"{timer}: drop-in {dropin.strip().splitlines()[-1]}")
        if dropin != render_dropin(project):
            print(f"  note: config says {render_dropin(project).strip().splitlines()[-1]}; re-run install-timer")
    print(listing.stdout.rstrip() or listing.stderr.rstrip())
    if journal:
        print(f"--- last 20 journal lines for {service} ---")
        print(journal.rstrip())
    return EXIT_OK
