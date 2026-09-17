#!/usr/bin/env python3
"""Check named environment entries without disclosing credential values."""
import os
import sys


def main(names):
    if not names or any(not name.isidentifier() for name in names):
        print("Usage: check-env.py REQUIRED_NAME [REQUIRED_NAME ...]", file=sys.stderr)
        return 2
    missing = [name for name in names if not os.environ.get(name) or "op://" in os.environ[name]]
    if missing:
        print("Missing or unresolved: " + ", ".join(missing), file=sys.stderr)
        return 1
    print("Required environment entries are resolved and nonempty.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
