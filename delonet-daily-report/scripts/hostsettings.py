#!/usr/bin/env python3
"""This skill's view of the per-host overlay (see hostenv.py for the file and the chain).

Values a host owns -- where the mirror lives, who sends the mail, which Resend key,
the config path -- are read here, from the environment first and then
``~/.config/33god/host.env``. Failures surface as ConfigError, which reportctl turns
into exit 2 with a JSON error, never a traceback.

Also a tiny CLI for shell wrappers (scripts/nightly.sh), which must not parse dotenv:

    python3 hostsettings.py get KEY [DEFAULT]     print the value, or DEFAULT; exit 1 if neither

Keys this skill reads:

    DDR_CONFIG            the report.json path (default ~/.config/delonet-daily-report/report.json)
    DDR_MIRROR_DIR        git-tracked mirror of each published report; unset = no mirror
    DDR_DIGEST_FOOTER     last line of the Slack digest; {date} is substituted
    DDR_MAIL_FROM         sender for email/slack when a target has no ``from``
    RESEND_API_KEY        the Resend key itself (wins), or
    RESEND_API_KEY_REF    op:// or env: reference to it, resolved by SECRET_RESOLVER
    SECRET_RESOLVER       auto (default) | op | interim
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hostenv import HostEnvError, SecretError, host_value, resolve_secret  # noqa: E402
from reportctl_contracts import ConfigError  # noqa: E402

DEFAULT_CONFIG = "~/.config/delonet-daily-report/report.json"


def setting(key: str, default: str | None = None) -> str | None:
    """Environment, then host.env, then ``default``; an empty value counts as unset."""
    try:
        return host_value(key, default)
    except HostEnvError as exc:
        raise ConfigError(str(exc)) from exc


def secret(ref: str) -> str:
    """The value behind an op:// or env: reference; ConfigError names the ref, never a value."""
    try:
        return resolve_secret(ref)
    except (SecretError, HostEnvError) as exc:
        raise ConfigError(str(exc)) from exc


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3) or argv[0] != "get":
        print("usage: hostsettings.py get KEY [DEFAULT]", file=sys.stderr)
        return 2
    try:
        value = setting(argv[1], argv[2] if len(argv) == 3 else None)
    except ConfigError as exc:
        print(f"hostsettings: {exc}", file=sys.stderr)
        return 2
    if value is None:
        return 1
    print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
