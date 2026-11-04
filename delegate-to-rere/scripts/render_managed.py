#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Render one managed instruction block into existing, user-owned files."""

import argparse
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

BEGIN = b"<!-- delegate-to-rere:start -->"
END = b"<!-- delegate-to-rere:end -->"
BEGIN_LINE = re.compile(rb"(?m)^" + re.escape(BEGIN) + rb"\r?\n")
END_LINE = re.compile(rb"(?m)^" + re.escape(END) + rb"(?:\r?\n|$)")


class InvalidInput(Exception):
    pass


def owned_regular(path: Path) -> os.stat_result:
    try:
        info = path.stat()
        parent = path.parent.stat()
    except OSError as exc:
        raise InvalidInput(f"{path}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
        raise InvalidInput(f"{path}: must be an existing regular file owned by this user")
    if parent.st_uid != os.geteuid() or not os.access(path.parent, os.W_OK | os.X_OK):
        raise InvalidInput(f"{path}: parent directory must be owned and writable by this user")
    return info


def render(original: bytes, source: bytes) -> bytes:
    starts = list(BEGIN_LINE.finditer(original))
    ends = list(END_LINE.finditer(original))
    if original.count(BEGIN) != len(starts) or original.count(END) != len(ends):
        raise InvalidInput("markers must occupy their own complete lines")
    if len(starts) != len(ends) or len(starts) > 1:
        raise InvalidInput("duplicate or unmatched markers")
    if starts and starts[0].start() >= ends[0].start():
        raise InvalidInput("end marker precedes start marker")

    newline = b"\r\n" if b"\r\n" in original and b"\n" not in original.replace(b"\r\n", b"") else b"\n"
    normalized = source.replace(b"\r\n", b"\n")
    block = BEGIN + newline + normalized.replace(b"\n", newline) + END + newline
    if starts:
        return original[:starts[0].start()] + block + original[ends[0].end():]
    separator = b"" if not original or original.endswith(b"\n") else newline
    return original + separator + block


def install(path: Path, content: bytes, mode: int) -> None:
    fd, name = tempfile.mkstemp(prefix=".delegate-to-rere-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            os.fchmod(output.fileno(), stat.S_IMODE(mode))
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def run(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="plain UTF-8 policy text")
    parser.add_argument("--target", required=True, action="append", type=Path, help="existing file; repeat as needed")
    parser.add_argument("--apply", action="store_true", help="write changed files; without it only check for drift")
    args = parser.parse_args(argv)
    try:
        source_path = args.source.resolve(strict=True)
        owned_regular(source_path)
        source = source_path.read_bytes()
        source.decode("utf-8")
        if not source.strip() or BEGIN in source or END in source:
            raise InvalidInput("source must be nonempty plain text without managed markers")
        if b"\r" in source.replace(b"\r\n", b""):
            raise InvalidInput("source has unsupported newline encoding")
        source = source.rstrip(b"\r\n") + b"\n"
        plans = []
        seen = set()
        for target in args.target:
            path = target.resolve(strict=True)
            if path in seen:
                raise InvalidInput(f"duplicate target: {path}")
            seen.add(path)
            info = owned_regular(path)
            original = path.read_bytes()
            original.decode("utf-8")
            updated = render(original, source)
            plans.append((path, info, original, updated))
        for path, info, original, updated in plans:
            if updated == original:
                print(f"unchanged: {path}")
            elif not args.apply:
                print(f"drift: {path}")
            else:
                current = path.stat()
                if (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) != (
                    info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
                ):
                    raise InvalidInput(f"target changed since preflight: {path}")
                install(path, updated, info.st_mode)
                print(f"updated: {path}")
        return 0 if args.apply or all(old == new for _, _, old, new in plans) else 1
    except (InvalidInput, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(run())
