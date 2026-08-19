#!/usr/bin/python3 -I
"""Fail-open SessionStart bridge to the fixed PJangler user installation."""

from __future__ import annotations

import grp
import os
import pwd
import signal
import stat
import subprocess
import sys
from pathlib import Path

DISPLAY_EVENT = "SessionStart"
HOOK_EVENT = "session-start"
REQUEST_LIMIT_BYTES = 1_048_576
STREAM_LIMIT_BYTES = REQUEST_LIMIT_BYTES + 1
CHILD_TIMEOUT_SECONDS = 2.25
NODE_BINARY = Path("/usr/bin/node")
AUTH_VARIABLE = "OPEN_NOTEBOOK_PASSWORD"


class LauncherError(RuntimeError):
    """A bounded launcher-validation failure."""


def fail_open(reason: str) -> int:
    print(f"project-notebook: {DISPLAY_EVENT} {reason}", file=sys.stderr)
    return 0


def canonical_identity() -> pwd.struct_passwd:
    entry = pwd.getpwuid(os.geteuid())
    if entry.pw_uid != os.geteuid():
        raise LauncherError("skipped; canonical user identity is invalid")
    home = Path(entry.pw_dir)
    if not home.is_absolute() or home == Path("/") or ".." in home.parts:
        raise LauncherError("skipped; canonical user home is invalid")
    return entry


def private_primary_group(entry: pwd.struct_passwd) -> bool:
    try:
        group = grp.getgrgid(entry.pw_gid)
        primary_users = {
            candidate.pw_name for candidate in pwd.getpwall() if candidate.pw_gid == entry.pw_gid
        }
    except (KeyError, OSError):
        return False
    if entry.pw_name not in primary_users:
        return False
    writers = primary_users | set(group.gr_mem)
    return writers <= {entry.pw_name}


def path_components(path: Path) -> list[Path]:
    if not path.is_absolute() or path == Path("/"):
        raise LauncherError("skipped; trusted path is invalid")
    components: list[Path] = []
    current = Path("/")
    for component in path.parts[1:]:
        if component in ("", ".", ".."):
            raise LauncherError("skipped; trusted path is invalid")
        current /= component
        components.append(current)
    return components


def reject_symlink_components(path: Path) -> None:
    for component in path_components(path):
        try:
            information = component.lstat()
        except OSError as exc:
            raise LauncherError("skipped; trusted path is unavailable") from exc
        if stat.S_ISLNK(information.st_mode):
            raise LauncherError("skipped; trusted path contains a symlink")


def validate_owned_component(
    path: Path,
    entry: pwd.struct_passwd,
    *,
    directory: bool,
    private_group: bool,
) -> None:
    try:
        information = path.lstat()
    except OSError as exc:
        raise LauncherError("skipped; trusted path is unavailable") from exc
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    if stat.S_ISLNK(information.st_mode) or not expected_type(information.st_mode):
        raise LauncherError("skipped; trusted path has an unsafe type")
    if information.st_uid != entry.pw_uid or information.st_gid != entry.pw_gid:
        raise LauncherError("skipped; trusted path ownership is unsafe")
    mode = stat.S_IMODE(information.st_mode)
    special = stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX
    if mode & (special | stat.S_IWOTH):
        raise LauncherError("skipped; trusted path permissions are unsafe")
    if mode & stat.S_IWGRP and not private_group:
        raise LauncherError("skipped; trusted path group is not private")
    if not directory and not mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        raise LauncherError("skipped; trusted pj is not executable")


def validate_owned_tree(
    home: Path,
    target: Path,
    entry: pwd.struct_passwd,
    *,
    final_directory: bool,
    private_group: bool,
) -> None:
    try:
        relative = target.relative_to(home)
    except ValueError as exc:
        raise LauncherError("skipped; resolved pj is outside canonical home") from exc
    reject_symlink_components(target)
    validate_owned_component(home, entry, directory=True, private_group=private_group)
    current = home
    for index, component in enumerate(relative.parts):
        current /= component
        validate_owned_component(
            current,
            entry,
            directory=final_directory or index < len(relative.parts) - 1,
            private_group=private_group,
        )


def validate_node_binary() -> None:
    try:
        information = NODE_BINARY.lstat()
    except OSError as exc:
        raise LauncherError("skipped; fixed node runtime is unavailable") from exc
    mode = stat.S_IMODE(information.st_mode)
    special = stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX
    if (
        stat.S_ISLNK(information.st_mode)
        or not stat.S_ISREG(information.st_mode)
        or information.st_uid != 0
        or mode & (special | stat.S_IWGRP | stat.S_IWOTH)
        or not mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    ):
        raise LauncherError("skipped; fixed node runtime is unsafe")


def resolve_launcher(entry: pwd.struct_passwd) -> Path:
    home = Path(entry.pw_dir)
    launcher = home / ".local" / "bin" / "pj"
    private_group = private_primary_group(entry)
    reject_symlink_components(launcher.parent)
    validate_owned_tree(
        home,
        launcher.parent,
        entry,
        final_directory=True,
        private_group=private_group,
    )
    try:
        resolved = launcher.resolve(strict=True)
    except OSError as exc:
        raise LauncherError("skipped; trusted pj launcher cannot be resolved") from exc
    validate_owned_tree(
        home,
        resolved,
        entry,
        final_directory=False,
        private_group=private_group,
    )
    return resolved


def sanitized_environment(entry: pwd.struct_passwd) -> dict[str, str]:
    environment = {
        "HOME": entry.pw_dir,
        "USER": entry.pw_name,
        "LOGNAME": entry.pw_name,
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    authentication = os.environ.get(AUTH_VARIABLE)
    if authentication is not None:
        environment[AUTH_VARIABLE] = authentication
    return environment


def invoke(entry: pwd.struct_passwd, launcher: Path, payload: bytes) -> int:
    process = subprocess.Popen(
        [str(NODE_BINARY), str(launcher), "notebook", "hook", HOOK_EVENT],
        stdin=subprocess.PIPE,
        env=sanitized_environment(entry),
        close_fds=True,
        start_new_session=True,
    )
    try:
        process.communicate(payload, timeout=CHILD_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        return fail_open("timed out; run pj notebook audit")
    if process.returncode != 0:
        return fail_open("failed open; run pj notebook audit")
    return 0


def main() -> int:
    entry = canonical_identity()
    validate_node_binary()
    launcher = resolve_launcher(entry)
    payload = sys.stdin.buffer.read(STREAM_LIMIT_BYTES)
    if len(payload) > REQUEST_LIMIT_BYTES:
        return fail_open("skipped; hook payload exceeds 1048576 bytes")
    return invoke(entry, launcher, payload)


if __name__ == "__main__":
    try:
        result = main()
    except LauncherError as exc:
        result = fail_open(str(exc))
    except Exception:
        result = fail_open("failed open; run pj notebook audit")
    raise SystemExit(result)
