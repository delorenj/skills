"""Per-host overlay and secret resolution.

Everything a host owns -- gateway URL, token refs, destinations, output dirs -- lives
OUTSIDE the tracked tree, in two places:

  1. the process environment, which always wins;
  2. ``~/.config/33god/host.env`` (``$XDG_CONFIG_HOME/33god/host.env``, or the path in
     ``HOST_ENV_FILE``): a dotenv file of plain KEY=value lines. It is parsed here and
     never sourced, so it cannot execute anything. It holds names and ``op://``
     references, never secret values.

Secrets are resolved from an ``op://`` reference through one chain, selected by
``SECRET_RESOLVER`` (env or host.env):

  op       ``op read REF`` (a host with a 1Password service account)
  interim  ``env-op-resolve`` against the 0600 per-host store (a peer host that must
           never hold a vault token); the store is mapped by refmap.tsv
  auto     (default) ``op`` when the binary exists, then ``interim``

A ref written ``env:NAME`` reads that environment variable. Nothing here ever prints a
secret, and every error names the ref or the key, never a value.

This file is kept byte-identical in the activity-report and delonet-daily-report skills
and, as bin/jev_hostenv.py, in delorenj/agents tools/jev-clairic (each test suite checks
it against a sibling copy when one is checked out). Change all three.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

HOST_ENV_DEFAULT = "~/.config/33god/host.env"
KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RESOLVERS = ("auto", "op", "interim")


class HostEnvError(Exception):
    """host.env is malformed. The message names the file and line, never a value."""


class SecretError(Exception):
    """A secret could not be resolved. The message names the ref and what was tried."""


def host_env_path(env=None) -> str:
    env = os.environ if env is None else env
    explicit = (env.get("HOST_ENV_FILE") or "").strip()
    if explicit:
        return os.path.expanduser(explicit)
    xdg = (env.get("XDG_CONFIG_HOME") or "").strip()
    if xdg:
        return os.path.join(xdg, "33god", "host.env")
    return os.path.expanduser(HOST_ENV_DEFAULT)


def parse_env_text(text: str, where: str = "host.env") -> dict:
    """KEY=value lines; ``export`` prefix, blank lines and # comments allowed.

    Values are bare, 'single-quoted' (literal) or "double-quoted" (\\" and \\\\ escapes).
    A bare value loses a trailing `` # comment``. Nothing is expanded.
    """
    out: dict = {}
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, sep, value = line.partition("=")
        key = key.strip()
        if not sep or not KEY_RE.match(key):
            raise HostEnvError(f"{where}:{lineno}: expected KEY=value")
        value = value.strip()
        if value[:1] == '"':
            m = re.match(r'^"((?:[^"\\]|\\.)*)"\s*(?:#.*)?$', value)
            if not m:
                raise HostEnvError(f"{where}:{lineno}: unterminated double-quoted value for {key}")
            value = re.sub(r"\\(.)", r"\1", m.group(1))
        elif value[:1] == "'":
            m = re.match(r"^'([^']*)'\s*(?:#.*)?$", value)
            if not m:
                raise HostEnvError(f"{where}:{lineno}: unterminated single-quoted value for {key}")
            value = m.group(1)
        else:
            value = re.sub(r"\s+#.*$", "", value).strip()
        out[key] = value
    return out


def load_host_env(path: str | None = None, env=None) -> dict:
    """The host.env file as a dict; an absent or empty file is an empty dict."""
    path = path or host_env_path(env)
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise HostEnvError(f"{path}: unreadable ({exc.strerror or exc})") from exc
    return parse_env_text(text, path)


def host_value(key: str, default: str | None = None, env=None, host=None) -> str | None:
    """Environment first, then host.env, then ``default``. An empty value counts as unset."""
    env = os.environ if env is None else env
    value = (env.get(key) or "").strip()
    if value:
        return value
    host = load_host_env(env=env) if host is None else host
    value = (host.get(key) or "").strip()
    return value or default


def resolver_mode(env=None, host=None) -> str:
    mode = (host_value("SECRET_RESOLVER", "auto", env, host) or "auto").lower()
    if mode not in RESOLVERS:
        raise SecretError(f"SECRET_RESOLVER={mode!r} is not one of {', '.join(RESOLVERS)}")
    return mode


def _op_read(ref: str, timeout: int) -> str:
    exe = shutil.which("op")
    if not exe:
        raise SecretError("op: the 1Password CLI is not installed")
    try:
        proc = subprocess.run([exe, "read", ref], capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise SecretError(f"op: timed out after {timeout}s") from exc
    except OSError as exc:
        raise SecretError(f"op: {exc.strerror or exc}") from exc
    value = proc.stdout.strip()
    if proc.returncode != 0 or not value:
        raise SecretError("op: read failed" if proc.returncode else "op: returned an empty value")
    return value


def _interim_exe() -> str | None:
    found = shutil.which("env-op-resolve")
    if found:
        return found
    local = os.path.join(os.path.expanduser("~"), ".local", "bin", "env-op-resolve")
    return local if os.access(local, os.X_OK) else None


def _interim_read(ref: str, timeout: int) -> str:
    exe = _interim_exe()
    if not exe:
        raise SecretError("interim: env-op-resolve is not installed")
    quoted = ref.replace("\\", "\\\\").replace('"', '\\"')
    fd, tmp = tempfile.mkstemp(prefix=".ref-", suffix=".env.op")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(f'SECRET="{quoted}"\n')          # a ref only; the value never touches a file
        printer = "import os,sys; sys.stdout.write(os.environ['SECRET'])"
        try:
            proc = subprocess.run([exe, "exec", "--env-file", tmp, "--", sys.executable, "-c", printer],
                                  capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise SecretError(f"interim: timed out after {timeout}s") from exc
        except OSError as exc:
            raise SecretError(f"interim: {exc.strerror or exc}") from exc
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    value = proc.stdout.strip()
    if proc.returncode != 0 or not value:
        detail = (proc.stderr or "").strip().splitlines()
        # env-op-resolve names keys and refs only, so its last line is safe to show.
        raise SecretError("interim: " + (detail[-1][:200] if detail else "no value in the store"))
    return value


def resolve_secret(ref: str, env=None, host=None, timeout: int = 30) -> str:
    """The value behind ``ref``. Raises SecretError (never leaks a value) when none resolves."""
    env = os.environ if env is None else env
    ref = (ref or "").strip()
    if ref.startswith("env:"):
        name = ref[len("env:"):]
        value = (env.get(name) or "").strip()
        if not value:
            raise SecretError(f"{ref}: environment variable {name} is unset")
        return value
    if not ref.startswith("op://"):
        # Never echo the value: a literal secret pasted into a *_REF key is exactly this case.
        raise SecretError("the reference is not an op://… or env:NAME reference "
                          "(a literal secret is never read from config)")
    mode = resolver_mode(env, host)
    steps = {"op": ("op",), "interim": ("interim",), "auto": ("op", "interim")}[mode]
    tried = []
    for step in steps:
        try:
            return (_op_read if step == "op" else _interim_read)(ref, timeout)
        except SecretError as exc:
            if mode == "auto" and step == "op" and "not installed" in str(exc):
                continue                                # no op binary at all: not worth reporting
            tried.append(str(exc))
    raise SecretError(f"could not resolve {ref} (SECRET_RESOLVER={mode}): " + "; ".join(tried))
