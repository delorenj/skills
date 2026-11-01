#!/usr/bin/env python3
"""Check that required process environment variables are present and nonempty.

Name/count-only output: never emit environment values, even on error. This is
not an authentication, reference-resolution, or vault-permission probe.
"""

import os
import re
import sys

NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z", re.ASCII)


def main(arguments):
    if not arguments or any(not NAME.fullmatch(name) for name in arguments):
        print("usage: check-env.py NAME [NAME ...] (valid identifiers only)", file=sys.stderr)
        return 2
    names = set(arguments)
    missing_count = sum(not os.environ.get(name, "").strip() for name in names)
    if missing_count:
        print(f"environment check failed: {missing_count} of {len(names)} required names absent or empty", file=sys.stderr)
        return 1
    unresolved_count = sum("op://" in os.environ.get(name, "") for name in names)
    if unresolved_count:
        print(f"environment check failed: {unresolved_count} required names contain unresolved references", file=sys.stderr)
        return 1
    print(f"environment check passed: {len(names)} required names present")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
