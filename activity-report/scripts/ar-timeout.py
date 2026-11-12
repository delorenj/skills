#!/usr/bin/env python3
"""timeout(1) for hosts that lack it: ``ar-timeout.py [--kill-after=DUR] DURATION COMMAND [ARG...]``.

run.sh uses GNU ``timeout`` or ``gtimeout`` when one is on PATH and this file when neither
is (a stock macOS, or a launchd job whose PATH skips Homebrew). Same contract as GNU:

  * DURATION and --kill-after take s (default), m, h or d suffixes;
  * the command runs in its own process group, so its children are signalled too;
  * at the deadline the group gets SIGTERM, and SIGKILL after --kill-after;
  * exit 124 when the command timed out (137 when it needed the SIGKILL),
    125 for a usage error, 126/127 when the command cannot be run,
    otherwise the command's own exit status (128+N when it died of signal N).

Standard library only; runs on /usr/bin/python3 3.9.
"""
import os
import signal
import subprocess
import sys
import time

UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_duration(text):
    text = text.strip()
    scale = 1
    if text and text[-1] in UNITS:
        scale, text = UNITS[text[-1]], text[:-1]
    value = float(text)
    if value < 0:
        raise ValueError("negative duration")
    return value * scale


def main(argv):
    kill_after = None
    args = list(argv)
    while args and args[0].startswith("-") and args[0] != "--":
        flag = args.pop(0)
        if flag.startswith("--kill-after="):
            kill_after_text = flag.split("=", 1)[1]
        elif flag in ("-k", "--kill-after") and args:
            kill_after_text = args.pop(0)
        else:
            sys.stderr.write("ar-timeout: unknown option %s\n" % flag)
            return 125
        try:
            kill_after = parse_duration(kill_after_text)
        except ValueError:
            sys.stderr.write("ar-timeout: invalid --kill-after %r\n" % kill_after_text)
            return 125
    if args and args[0] == "--":
        args.pop(0)
    if len(args) < 2:
        sys.stderr.write("usage: ar-timeout.py [--kill-after=DUR] DURATION COMMAND [ARG...]\n")
        return 125
    try:
        limit = parse_duration(args[0])
    except ValueError:
        sys.stderr.write("ar-timeout: invalid duration %r\n" % args[0])
        return 125
    try:
        child = subprocess.Popen(args[1:], start_new_session=True)
    except FileNotFoundError:
        sys.stderr.write("ar-timeout: %s: command not found\n" % args[1])
        return 127
    except OSError as exc:
        sys.stderr.write("ar-timeout: %s: %s\n" % (args[1], exc.strerror or exc))
        return 126

    def forward(signum, _frame):
        try:
            os.killpg(child.pid, signum)
        except OSError:
            pass

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, forward)

    deadline = time.monotonic() + limit if limit > 0 else None
    timed_out = False
    killed = False
    kill_deadline = None
    while True:
        rc = child.poll()
        if rc is not None:
            break
        now = time.monotonic()
        if deadline is not None and not timed_out and now >= deadline:
            timed_out = True
            forward(signal.SIGTERM, None)
            if kill_after is not None:
                kill_deadline = now + kill_after
        if kill_deadline is not None and not killed and now >= kill_deadline:
            killed = True
            forward(signal.SIGKILL, None)
        time.sleep(0.05)
    if timed_out:
        return 137 if killed else 124
    return rc if rc >= 0 else 128 - rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
