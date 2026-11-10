#!/usr/bin/env python3
"""env-op-resolve: resolve op:// references from a local interim secret store.

Implements the interim-store half of the delonet-dotenv two-file split for
hosts WITHOUT a 1Password service account (e.g. a peer machine that must never
hold a DeLoSecrets token). Repos keep their committed ``.env.op`` files
unchanged; instead of ``op run --env-file .env.op``, this tool resolves each
``op://`` reference against a per-host plaintext store:

  store   ~/.config/33god/secrets.env   (0600, outside any repo)
  refmap  ~/.config/33god/refmap.tsv    (op-ref <TAB> store-key, no values)

Later 1Password adoption is a cutover, not a re-architecture: import the store
into the vault and switch back to ``op run``.

Contract (fail closed everywhere):
  * Store keys are DERIVED deterministically from the op:// ref
    (see ``derive_key``). refmap.tsv must agree with the derivation; a row
    that disagrees, a duplicate ref, or a duplicate key aborts the run.
  * A .env.op entry whose ref is not in refmap.tsv aborts the run.
  * A ref whose store key has no value in secrets.env aborts the run.
  * Duplicate keys in .env.op or in the store abort the run.
  * Error messages name keys and refs only -- values are never logged.

Modes:
  render   .env.op -> .env (written atomically, mode 0600)
  exec     inject resolved vars into the environment and exec a command
           (file values override inherited environment, like `op run`)
  key      print the deterministic store key for one op:// ref (no values)

Only Python stdlib; compatible with /usr/bin/python3 >= 3.9 so it works under
launchd's minimal environment on macOS.
"""

import argparse
import os
import re
import sys

STORE_DEFAULT = "~/.config/33god/secrets.env"
REFMAP_DEFAULT = "~/.config/33god/refmap.tsv"

KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class FailClosed(Exception):
    """Resolution refused; message must never contain a secret value."""


def derive_key(ref):
    """op://Vault/Item[/Section]/Field -> OP_VAULT_ITEM_SECTION_FIELD.

    Deterministic: uppercase, every run of non-alphanumerics becomes one
    underscore. Collisions between distinct refs are detected by the refmap
    loader and fail closed.
    """
    if not ref.startswith("op://"):
        raise FailClosed("not an op:// ref: %r" % ref)
    body = ref[len("op://"):].strip("/")
    parts = [p for p in body.split("/") if p]
    if len(parts) < 3:
        raise FailClosed("ref has fewer than vault/item/field parts: %r" % ref)
    raw = "_".join(parts)
    key = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").upper()
    if not key:
        raise FailClosed("ref derives to an empty key: %r" % ref)
    return "OP_" + key


def _unescape_double_quoted(s, where):
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 1
            if i >= len(s):
                raise FailClosed("dangling backslash in quoted value (%s)" % where)
            e = s[i]
            out.append({"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}.get(e, e))
        else:
            out.append(c)
        i += 1
    return "".join(out)


def _parse_env_lines(text, where, allow_export):
    """Parse KEY=value lines. Returns list of (key, value) in file order.

    Values may be bare, 'single-quoted' (literal), or "double-quoted"
    (backslash escapes \\n \\r \\t \\" \\\\; may span lines until the closing
    quote). Everything after the first '=' belongs to the value.
    """
    items = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if allow_export and stripped.startswith("export "):
            stripped = stripped[len("export "):].lstrip()
        if "=" not in stripped:
            raise FailClosed("%s:%d: line has no '=': %r" % (where, i, stripped[:40]))
        key, _, value = stripped.partition("=")
        key = key.strip()
        if not KEY_RE.match(key):
            raise FailClosed("%s:%d: invalid key name: %r" % (where, i, key))
        value = value.strip()
        if value.startswith('"'):
            # double-quoted, possibly multiline
            buf = value[1:]
            while True:
                # find an unescaped closing quote
                j = 0
                closed = False
                while j < len(buf):
                    if buf[j] == "\\":
                        j += 2
                        continue
                    if buf[j] == '"':
                        closed = True
                        break
                    j += 1
                if closed:
                    trailing = buf[j + 1:].strip()
                    if trailing and not trailing.startswith("#"):
                        raise FailClosed(
                            "%s:%d: trailing characters after closing quote for key %s"
                            % (where, i, key)
                        )
                    value = _unescape_double_quoted(buf[:j], "%s key %s" % (where, key))
                    break
                if i >= len(lines):
                    raise FailClosed(
                        "%s: unterminated double-quoted value for key %s" % (where, key)
                    )
                buf += "\n" + lines[i]
                i += 1
        elif value.startswith("'"):
            if len(value) < 2 or not value.endswith("'"):
                raise FailClosed(
                    "%s:%d: unterminated single-quoted value for key %s" % (where, i, key)
                )
            value = value[1:-1]
        else:
            # bare value: strip trailing comment only if preceded by whitespace
            m = re.match(r"^(.*?)(\s+#.*)$", value)
            if m:
                value = m.group(1).rstrip()
        items.append((key, value))
    return items


def _no_dupes(items, where):
    seen = {}
    for key, _ in items:
        if key in seen:
            raise FailClosed("%s: duplicate key %s" % (where, key))
        seen[key] = True


def load_store(path):
    full = os.path.expanduser(path)
    if not os.path.exists(full):
        raise FailClosed("store not found: %s" % full)
    with open(full, "r", encoding="utf-8") as fh:
        items = _parse_env_lines(fh.read(), full, allow_export=False)
    _no_dupes(items, full)
    return dict(items)


def load_refmap(path):
    full = os.path.expanduser(path)
    if not os.path.exists(full):
        raise FailClosed("refmap not found: %s" % full)
    refmap = {}
    keys = {}
    with open(full, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh.read().split("\n"), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
                raise FailClosed("%s:%d: malformed refmap row (want: ref<TAB>key)" % (full, lineno))
            ref, key = parts[0].strip(), parts[1].strip()
            derived = derive_key(ref)
            if key != derived:
                raise FailClosed(
                    "%s:%d: refmap key %s disagrees with deterministic key %s for ref %r"
                    % (full, lineno, key, derived, ref)
                )
            if ref in refmap:
                raise FailClosed("%s:%d: duplicate ref %r" % (full, lineno, ref))
            if key in keys:
                raise FailClosed(
                    "%s:%d: store key %s maps two different refs (%r and %r)"
                    % (full, lineno, key, keys[key], ref)
                )
            refmap[ref] = key
            keys[key] = ref
    return refmap


def resolve(env_op_path, store, refmap):
    """Return ordered [(key, resolved_value)] for a .env.op file."""
    full = os.path.expanduser(env_op_path)
    if not os.path.exists(full):
        raise FailClosed("env file not found: %s" % full)
    with open(full, "r", encoding="utf-8") as fh:
        items = _parse_env_lines(fh.read(), full, allow_export=True)
    _no_dupes(items, full)
    resolved = []
    for key, value in items:
        if value.startswith("op://"):
            try:
                derive_key(value)
            except FailClosed:
                raise FailClosed("%s: key %s has a malformed op:// ref" % (full, key))
            if value not in refmap:
                raise FailClosed(
                    "%s: key %s references %r which is not in the refmap (refusing)"
                    % (full, key, value)
                )
            skey = refmap[value]
            if skey not in store:
                raise FailClosed(
                    "key %s: ref %r maps to store key %s which has no value in the store (refusing)"
                    % (key, value, skey)
                )
            resolved.append((key, store[skey]))
        else:
            if "op://" in value:
                raise FailClosed(
                    "%s: key %s embeds an op:// ref inside a literal value (refusing)"
                    % (full, key)
                )
            resolved.append((key, value))
    return resolved


def _escape_dotenv(value):
    out = []
    for c in value:
        if c == "\\":
            out.append("\\\\")
        elif c == '"':
            out.append('\\"')
        elif c == "\n":
            out.append("\\n")
        elif c == "\r":
            out.append("\\r")
        elif c == "\t":
            out.append("\\t")
        else:
            out.append(c)
    return "".join(out)


def cmd_render(args):
    store = load_store(args.store)
    refmap = load_refmap(args.refmap)
    resolved = resolve(args.env_op, store, refmap)
    out_path = os.path.expanduser(args.out)
    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    tmp = os.path.join(out_dir, ".%s.tmp.%d" % (os.path.basename(out_path), os.getpid()))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("# Rendered by env-op-resolve from %s -- do not commit, do not edit.\n"
                     % os.path.basename(os.path.expanduser(args.env_op)))
            for key, value in resolved:
                fh.write('%s="%s"\n' % (key, _escape_dotenv(value)))
        os.replace(tmp, out_path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    print("rendered %d var(s) -> %s (0600)" % (len(resolved), out_path))


def cmd_exec(args):
    store = load_store(args.store)
    refmap = load_refmap(args.refmap)
    resolved = resolve(args.env_file, store, refmap)
    env = dict(os.environ)
    for key, value in resolved:  # file wins over inherited environment
        env[key] = value
    if not args.command:
        raise FailClosed("exec mode requires a command after --")
    os.execvpe(args.command[0], args.command, env)


def cmd_key(args):
    print(derive_key(args.ref))


def main(argv):
    p = argparse.ArgumentParser(
        prog="env-op-resolve",
        description="Resolve op:// refs in .env.op files against a local interim store. "
                    "Fails closed; never prints secret values.",
    )
    p.add_argument("--store", default=os.environ.get("ENV_OP_STORE", STORE_DEFAULT),
                   help="path to the secrets store (default: %(default)s)")
    p.add_argument("--refmap", default=os.environ.get("ENV_OP_REFMAP", REFMAP_DEFAULT),
                   help="path to the ref->key mapping table (default: %(default)s)")
    sub = p.add_subparsers(dest="mode", required=True)

    pr = sub.add_parser("render", help="render .env.op to a 0600 .env file")
    pr.add_argument("env_op", help="input .env.op path")
    pr.add_argument("out", nargs="?", default=None,
                    help="output path (default: input path with the .op suffix removed)")
    pr.set_defaults(func=cmd_render)

    pe = sub.add_parser("exec", help="inject resolved vars and exec a command")
    pe.add_argument("--env-file", "-e", default=".env.op", help="env file (default: .env.op)")
    pe.add_argument("command", nargs=argparse.REMAINDER, help="-- command [args...]")
    pe.set_defaults(func=cmd_exec)

    pk = sub.add_parser("key", help="print the deterministic store key for an op:// ref")
    pk.add_argument("ref")
    pk.set_defaults(func=cmd_key)

    args = p.parse_args(argv)
    if args.mode == "render" and args.out is None:
        src = os.path.expanduser(args.env_op)
        args.out = src[:-3] if src.endswith(".op") else src + ".rendered"
    if args.mode == "exec" and args.command and args.command[0] == "--":
        args.command = args.command[1:]
    try:
        args.func(args)
    except FailClosed as exc:
        print("env-op-resolve: %s" % exc, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
