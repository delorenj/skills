"""`activity-report host-config` and `activity-report secret read`: what run.sh needs from
the per-host overlay (see hostenv.py), kept in Python so the parsing exists once.

Nothing here has a default for a gateway, a route or a token ref: those belong to a host,
and a host that has not declared them cannot compose. run.sh turns the missing keys into
one FATAL line that names them.
"""
from __future__ import annotations

import json

from .common import ConfigError, eprint
from .hostenv import (HostEnvError, SecretError, host_env_path, host_value, load_host_env,
                      resolve_secret, resolver_mode)

GATEWAY_KEYS = {
    "gateway_url": "ACTIVITY_REPORT_GATEWAY_URL",
    "gateway_route": "ACTIVITY_REPORT_GATEWAY_ROUTE",
    "gateway_token_ref": "ACTIVITY_REPORT_GATEWAY_TOKEN_REF",
}


def gateway_settings(env=None) -> dict:
    """The compose gateway for this host; each unset key is None."""
    try:
        host = load_host_env(env=env)
        out = {name: host_value(key, None, env, host) for name, key in GATEWAY_KEYS.items()}
        out["resolver"] = resolver_mode(env, host)
    except (HostEnvError, SecretError) as exc:
        raise ConfigError(str(exc)) from exc
    out["host_env"] = host_env_path(env)
    return out


def host_config_cmd(args) -> int:
    settings = gateway_settings()
    if args.json:
        print(json.dumps(settings, indent=2))
        return 0
    for name in GATEWAY_KEYS:
        print(f"{name:18} {settings[name] or '-'}")
    print(f"{'resolver':18} {settings['resolver']}")
    print(f"{'host_env':18} {settings['host_env']}")
    return 0


def secret_read_cmd(args) -> int:
    """Print the secret behind --ref on stdout. Errors go to stderr and name the ref only."""
    try:
        value = resolve_secret(args.ref)
    except (SecretError, HostEnvError) as exc:
        eprint(f"activity-report: {exc}")
        return 2
    print(value)
    return 0
