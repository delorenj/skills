#!/usr/bin/env python3
"""Plan or publish a static HTML artifact bundle to the DeLoNET projects bucket.

Layout: https://s3.delo.sh/projects/{project-slug}/{bb-session-id}/{artifact}/{relative-path}

Default mode is an offline plan (no subprocess, no network, no writes).
--publish uploads the validated bytes from a private snapshot (a file swapped
or rewritten after validation fails instead of publishing unvalidated bytes)
with the existing `mc` alias, then verifies every object over anonymous HTTPS.
Publishing refuses bundles whose required resources are not all local files.
Stdlib only. Output is one JSON document on stdout.
"""
from __future__ import annotations

import argparse
import contextlib
import errno
import hashlib
import http.client
import ipaddress
import json
import os
import re
import shutil
import socket
import ssl
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import NoReturn

DEFAULT_ALIAS = "delo"
BUCKET = "projects"            # fixed by the delivery contract; not configurable
BASE_URL = "https://s3.delo.sh"  # fixed by the delivery contract; not configurable
# no-transform stops the Cloudflare proxy in front of s3.delo.sh from rewriting
# responses (it injected its analytics beacon into HTML, so served bytes no
# longer matched the uploaded SHA-256). Verification stays byte-exact; the fix
# is to stop the rewrite, never to normalize the body.
CACHE_CONTROL = "no-cache, no-transform"
MAX_FILES = 2000
MAX_DEPTH = 64              # bundle subdirectory nesting bound
MAX_READ_BYTES = 512 << 20  # single-file read bound (512 MiB)

EXIT_OK, EXIT_UNEXPECTED, EXIT_INVALID, EXIT_COLLISION, EXIT_REMOTE, EXIT_UPLOAD, EXIT_VERIFY = 0, 1, 2, 3, 4, 5, 6

# Always used with fullmatch: `$` with match() would accept a trailing newline.
SLUG_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
HARNESS_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
ALIAS_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
BUCKET_RE = re.compile(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]")

# Known CLI environment variables carrying the harness-native session id.
HARNESS_ENV = {
    "codex": ("CODEX_THREAD_ID", "CODEX_SESSION_ID"),
    "hermes": ("HERMES_SESSION_ID",),
    "claude": ("CLAUDE_SESSION_ID", "CLAUDE_CODE_SESSION_ID"),
}

MIME = {
    ".html": "text/html", ".htm": "text/html", ".css": "text/css",
    ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json",
    ".map": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
    ".avif": "image/avif", ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2",
    ".ttf": "font/ttf", ".otf": "font/otf", ".wasm": "application/wasm", ".txt": "text/plain",
    ".md": "text/markdown", ".csv": "text/csv", ".xml": "application/xml", ".pdf": "application/pdf",
    ".mp4": "video/mp4", ".webm": "video/webm", ".mp3": "audio/mpeg", ".wav": "audio/wav",
    ".webmanifest": "application/manifest+json",
}

DANGEROUS_NAMES = {
    ".git", ".env", ".envrc", ".npmrc", ".netrc", ".pypirc", ".ssh", ".aws", ".mc", ".gnupg",
    ".docker", ".kube", ".htpasswd", ".s3cfg", ".pgpass", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
    "credentials", "credentials.json", "secrets.json", "secrets.yaml", "secrets.yml",
    ".git-credentials", "known_hosts", "authorized_keys",
}
DANGEROUS_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".kdbx", ".tfstate", ".env")
PRIVATE_KEY_MARK = b"-----BEGIN"
# Covers PKCS#1/8, RSA, EC, OPENSSH, ENCRYPTED and PGP ("PRIVATE KEY BLOCK-----") armor.
PRIVATE_KEY_RE = re.compile(rb"-----BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----")

SKIP_SCHEMES = ("data:", "blob:", "mailto:", "tel:", "javascript:", "about:", "sms:")
# Only these <script type> values are JavaScript; JSON import maps, templates,
# application/json blocks etc. are data, not code, and must not be scanned as JS.
JS_SCRIPT_TYPES = {"", "module", "text/javascript", "application/javascript",
                   "application/x-javascript", "text/ecmascript", "application/ecmascript"}
XML_STYLESHEET_RE = re.compile(r"<\?xml-stylesheet[^>]*?href=[\"']([^\"']+)[\"']", re.I)
NON_RESOURCE_RELS = {"preconnect", "dns-prefetch", "canonical", "alternate", "author", "license",
                     "help", "search", "next", "prev", "me", "external"}
PRIVATE_HOST_SUFFIXES = (".localhost", ".local", ".lan", ".internal", ".home.arpa", ".ts.net")


class Failure(Exception):
    def __init__(self, code: int, kind: str, message: str, **extra):
        super().__init__(message)
        self.code, self.kind, self.message, self.extra = code, kind, message, extra


# ---------------------------------------------------------------- identity

def map_bb_session(harness: str, native_id: str) -> str:
    """Mirror bloodbank agent-hooks BaseClient.get_correlation_id."""
    try:
        return str(uuid.UUID(native_id))
    except (ValueError, AttributeError):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"bloodbank:{harness}:{native_id}"))


def resolve_session(bb_session_id, harness, native_id, env) -> dict:
    if bb_session_id:
        if harness or native_id:
            raise Failure(EXIT_INVALID, "session_ambiguous",
                          "use --bb-session-id or --harness/--native-session-id, not both")
        try:
            value = str(uuid.UUID(bb_session_id))
        except ValueError:
            raise Failure(EXIT_INVALID, "session_invalid", "--bb-session-id must be a UUID")
        return {"bb_session_id": value, "source": "explicit:--bb-session-id"}
    if native_id and not harness:
        raise Failure(EXIT_INVALID, "session_invalid", "--native-session-id requires --harness")
    if harness:
        if not HARNESS_RE.fullmatch(harness):
            raise Failure(EXIT_INVALID, "session_invalid", "invalid --harness name")
        source = "explicit:--native-session-id"
        if not native_id:
            native_id, source = _env_native(harness, env)
            if not native_id:
                raise Failure(EXIT_INVALID, "session_missing",
                              f"no native session id for harness {harness!r}; pass --native-session-id")
    else:
        found = {}
        for name in HARNESS_ENV:
            value, src = _env_native(name, env)
            if value:
                found[name] = (value, src)
        if not found:
            raise Failure(EXIT_INVALID, "session_missing",
                          "no session identity: pass --bb-session-id or --harness and --native-session-id")
        if len(found) > 1:
            raise Failure(EXIT_INVALID, "session_ambiguous",
                          "multiple harness session ids in environment; pass --harness explicitly",
                          harnesses=sorted(found))
        harness, (native_id, source) = next(iter(found.items()))
    native_id = native_id.strip()
    if not native_id:
        raise Failure(EXIT_INVALID, "session_missing", "empty native session id")
    return {"bb_session_id": map_bb_session(harness, native_id), "harness": harness,
            "native_session_id": native_id, "source": source,
            "mapping": "uuid-passthrough" if _is_uuid(native_id)
            else f"uuid5(NAMESPACE_URL, 'bloodbank:{harness}:<native>')"}


def _env_native(harness, env):
    values = {var: env[var].strip() for var in HARNESS_ENV.get(harness, ()) if env.get(var, "").strip()}
    if not values:
        return None, None
    if len(set(values.values())) > 1:
        raise Failure(EXIT_INVALID, "session_ambiguous",
                      f"conflicting {harness} session ids in environment", variables=sorted(values))
    var = sorted(values)[0]
    return values[var], f"env:{var}"


def _is_uuid(value):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def _git_main_worktree(start: Path):
    """Find the main worktree for start without running git. Returns (toplevel, main) or (None, None)."""
    for candidate in [start, *start.parents]:
        dotgit = candidate / ".git"
        if dotgit.is_dir():
            return candidate, candidate
        if dotgit.is_file():
            try:
                text = dotgit.read_text(errors="replace").strip()
            except OSError:
                raise Failure(EXIT_INVALID, "project_ambiguous", f"unreadable .git file at {candidate}")
            if not text.startswith("gitdir:"):
                raise Failure(EXIT_INVALID, "project_ambiguous", f"unreadable .git file at {candidate}")
            gitdir = Path(text[len("gitdir:"):].strip())
            if not gitdir.is_absolute():
                gitdir = (candidate / gitdir).resolve()
            commondir = gitdir / "commondir"
            if not commondir.is_file():
                return candidate, candidate  # submodule or plain gitfile: its own main worktree
            try:
                common_text = commondir.read_text().strip()
            except OSError:
                raise Failure(EXIT_INVALID, "project_ambiguous", f"unreadable commondir at {gitdir}")
            common = Path(common_text)
            if not common.is_absolute():
                common = (gitdir / common).resolve()
            if common.name == ".git":
                return candidate, common.parent
            config = common / "config"
            if config.is_file():
                try:
                    config_text = config.read_text(errors="replace")
                except OSError:
                    raise Failure(EXIT_INVALID, "project_ambiguous", f"unreadable config at {common}")
                match = re.search(r"^\s*worktree\s*=\s*(.+)$", config_text, re.M)
                if match:
                    main = Path(match.group(1).strip())
                    return candidate, (main if main.is_absolute() else (common / main)).resolve()
            raise Failure(EXIT_INVALID, "project_ambiguous",
                          f"cannot determine main worktree for {candidate}; pass --project")
    return None, None


def _read_project_json(path: Path):
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        raise Failure(EXIT_INVALID, "project_invalid", f"unreadable {path}")
    for field in ("project_slug", "project_id"):
        value = data.get(field) if isinstance(data, dict) else None
        if isinstance(value, str) and value.strip():
            return value.strip(), field
    return None


def resolve_project(project, project_root) -> dict:
    if project and not SLUG_RE.fullmatch(project):
        raise Failure(EXIT_INVALID, "project_invalid", "invalid --project slug")
    if project and not project_root:
        return {"slug": project, "source": "explicit:--project"}
    root = Path(project_root or os.getcwd()).expanduser().resolve()
    if not root.is_dir():
        raise Failure(EXIT_INVALID, "project_invalid", f"project root is not a directory: {root}")
    toplevel, main = _git_main_worktree(root)
    places = [p for p in dict.fromkeys([main, toplevel, root]) if p is not None]
    found = {}
    for place in places:
        hit = _read_project_json(place / ".project.json")
        if hit:
            found[str(place)] = hit
    if not found:
        if project:
            return {"slug": project, "source": "explicit:--project", "project_root": str(root)}
        raise Failure(EXIT_INVALID, "project_missing",
                      "no .project.json project_slug/project_id found; pass --project")
    slugs = {v[0] for v in found.values()}
    if len(slugs) > 1:
        raise Failure(EXIT_INVALID, "project_ambiguous", "conflicting .project.json identities",
                      candidates={k: v[0] for k, v in found.items()})
    slug = slugs.pop()
    if project and project != slug:
        raise Failure(EXIT_INVALID, "project_ambiguous",
                      f"--project {project!r} disagrees with .project.json {slug!r}")
    if not SLUG_RE.fullmatch(slug):
        raise Failure(EXIT_INVALID, "project_invalid", f".project.json identity {slug!r} is not a safe slug")
    origin = next(iter(found))
    return {"slug": slug, "source": f"{origin}/.project.json:{found[origin][1]}",
            "project_root": str(root), "main_worktree": str(main) if main else None}


# ---------------------------------------------------------------- bundle scan

def _srcset_candidates(value: str):
    """Tokenize a srcset into candidate URLs via URL/descriptor states.

    A comma ends a candidate only once the URL is complete: inside a URL a
    comma is kept (data: URIs contain commas, so 'data:...;base64,AAAA' is one
    URL), and once whitespace started the descriptor the next comma separates
    candidates even with no space after it ('...1x,missing.png 2x'). This is
    real tokenization, not a global `data:` test with a comma-plus-space split.
    """
    urls, url, in_descriptors = [], [], False
    for ch in value:
        if ch == ",":
            if not in_descriptors and url and "".join(url).lower().startswith("data:"):
                url.append(ch)  # comma inside a data: URL body, before descriptors
                continue
            if url:
                urls.append("".join(url))
                url = []
            in_descriptors = False
        elif ch.isspace():
            if url:
                urls.append("".join(url))
                url = []
                in_descriptors = True  # descriptors are skipped until the next comma
        elif not in_descriptors:
            url.append(ch)
    if url:
        urls.append("".join(url))
    return [u for u in urls if u]


class _RefParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []  # (value, kind, origin)
        self.inline_css = []
        self.inline_js = []
        self.base = False
        self._capture = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "base" and a.get("href"):
            self.base = True
        nav = tag in ("a", "area", "form")
        if tag == "link":
            rels = set(a.get("rel", "").lower().split())
            nav = bool(rels) and rels <= NON_RESOURCE_RELS
            if rels & {"preconnect", "dns-prefetch"}:
                return
        kind = "navigation" if nav else "resource"
        for attr in ("src", "href", "poster", "data", "xlink:href", "action"):
            if attr in a and not (attr == "action" and tag != "form"):
                self.refs.append((a[attr], kind, f"<{tag} {attr}>"))
        for attr in ("srcset", "imagesrcset"):
            for url in _srcset_candidates(a.get(attr, "")):
                self.refs.append((url, "resource", f"<{tag} {attr}>"))
        if "style" in a:
            self.inline_css.append(a["style"])
        if tag == "meta" and a.get("http-equiv", "").lower() == "refresh":
            m = re.search(r"url\s*=\s*['\"]?([^'\";]+)", a.get("content", ""), re.I)
            if m:
                self.refs.append((m.group(1), "navigation", "<meta refresh>"))
        if tag == "style":
            self._capture = self.inline_css
        elif tag == "script" and "src" not in a:
            stype = a.get("type", "").strip().lower()
            if stype in JS_SCRIPT_TYPES:  # JSON import maps / templates are not code
                self._capture = self.inline_js

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self._capture = None

    def handle_pi(self, data):
        # Standalone SVG/XML: <?xml-stylesheet href="..."?>
        m = XML_STYLESHEET_RE.match("<?" + data + "?>")
        if m:
            self.refs.append((m.group(1), "resource", "<?xml-stylesheet?>"))

    def handle_data(self, data):
        if self._capture is not None:
            self._capture.append(data)


CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I | re.S)
CSS_IMPORT_RE = re.compile(r"@import\s+(['\"])(.*?)\1", re.I)
# JS module discovery is deliberately RAW: independent passes over the whole
# text with no lexer, parser, vendor list, or string/comment/regex exclusion.
# Import-shaped text inside strings, comments and regex literals IS reported
# (React's development build ships import('./MyComponent') inside a warning
# string). A human inspects every such occurrence and waives a false positive
# only with an exact --accept-js-candidate FILE:SPECIFIER. The passes are:
#   import <gap> 'x' | "x"                  side-effect import
#   import <gap> ( <gap> 'x' | "x" | `x`    literal dynamic import, including
#                                           ...import('x') and import ('x')
#   from <gap> 'x' | "x"                    static import / re-export, whatever
#                                           the binding names (even `from`)
# <gap> is whitespace plus // and /* */ comments. A literal still open after
# A backslash before a line terminator is a LineContinuation: escaped CRLF is
# consumed as ONE continuation, escaped LF/CR/LS/PS as one character each; the
# raw text (backslash included) is kept and never decoded, so it still blocks.
# Once an opening quote is recognised the reader never drops the candidate: a
# literal that does not close (end of text, raw line break in '/", dangling
# escape, or MAX_JS_SPECIFIER characters) yields its bounded raw text marked
# _OpenJsLiteral, and scan_bundle refuses it as unresolved unless the normal
# reference check already blocks it or an exact --accept-js-candidate waives
# it. A template specifier stops at its first backtick and keeps `${`, so it
# stays unresolved.
# Not seen: computed import(expr), escaped keywords, and anything only a full
# ECMAScript parser could find; escaped specifiers are kept raw. Work is
# bounded; an exhausted budget rejects the bundle instead of a partial scan.
MAX_JS_SPECIFIER = 4096
_JS_IMPORT_WORD = re.compile(r"(?<![\w$])import(?![\w$])")
_JS_FROM_WORD = re.compile(r"(?<![\w$])from(?![\w$])")
_JS_LINE_END_RE = re.compile(r"[\n\r\u2028\u2029]")


class _OpenJsLiteral(str):
    """Bounded raw text of a JS literal that never closed (uncertain candidate)."""


def _css_refs(text, origin):
    for m in CSS_URL_RE.finditer(text):
        yield m.group(2).strip(), "resource", origin
    for m in CSS_IMPORT_RE.finditer(text):
        yield m.group(2).strip(), "resource", origin


def _js_spend(budget, amount):
    budget[0] -= amount
    if budget[0] < 0:
        raise Failure(EXIT_INVALID, "bundle_invalid",
                      "JS import candidate work budget exhausted; cannot scan imports")


def _js_gap(text, i, budget):
    """Skip whitespace and comments; an unterminated comment runs to the end."""
    n, start = len(text), i
    while i < n:
        if text[i].isspace() or text[i] == "\ufeff":
            i += 1
        elif text.startswith("//", i):
            m = _JS_LINE_END_RE.search(text, i + 2)
            i = m.start() if m else n
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            break
    _js_spend(budget, i - start)
    return i


def _js_literal(text, i, budget):
    """Raw text of the literal opened at text[i]; never None. Text of a literal
    that does not close within MAX_JS_SPECIFIER is returned as _OpenJsLiteral."""
    quote, j = text[i], i + 1
    end = min(len(text), j + MAX_JS_SPECIFIER)
    while j < end:
        c = text[j]
        if c == "\\":
            j += 3 if text.startswith("\r\n", j + 1) else 2  # escaped CRLF is one continuation
        elif c == quote:
            _js_spend(budget, j - i)
            return text[i + 1:j]
        elif quote != "`" and c in "\n\r":
            break
        else:
            j += 1
    j = min(j, end)
    _js_spend(budget, j - i)
    return _OpenJsLiteral(text[i + 1:j])


def _js_refs(text, origin):
    """Raw JS module candidates as (specifier, 'module', origin) in source order."""
    budget = [8 * len(text) + 65536]
    n, found = len(text), {}
    for match in _JS_IMPORT_WORD.finditer(text):
        i = _js_gap(text, match.end(), budget)
        if i < n and text[i] == "(":
            i = _js_gap(text, i + 1, budget)
            if i < n and text[i] in "'\"`" and i not in found:
                found[i] = _js_literal(text, i, budget)
        elif i < n and text[i] in "'\"" and i not in found:
            found[i] = _js_literal(text, i, budget)
    for match in _JS_FROM_WORD.finditer(text):
        i = _js_gap(text, match.end(), budget)
        if i < n and text[i] in "'\"" and i not in found:
            found[i] = _js_literal(text, i, budget)
    for i in sorted(found):
        spec = found[i].strip()
        yield (_OpenJsLiteral(spec) if isinstance(found[i], _OpenJsLiteral) else spec), "module", origin


def parse_acceptances(values) -> set:
    """Exact FILE:SPECIFIER waivers, split at the FIRST colon. No normalization."""
    pairs = set()
    for value in values or ():
        file, sep, spec = value.partition(":")
        parts = file.split("/")
        if (not sep or not file or not spec or file.startswith("/") or "\\" in file or ":" in file
                or any(ord(c) < 32 or ord(c) == 127 for c in file)
                or any(part in ("", ".", "..") for part in parts)):
            raise Failure(EXIT_INVALID, "acceptance_invalid",
                          f"--accept-js-candidate {value!r} must be FILE:SPECIFIER with FILE a canonical "
                          "bundle-relative POSIX path (no leading /, empty, . or .. segments, backslash, "
                          "colon or control characters) and a non-empty exact SPECIFIER")
        pairs.add((file, spec))
    return pairs


def _host_is_private(host: str) -> bool:
    host = (host or "").strip("[]").lower()
    if not host or host == "localhost" or host.endswith(PRIVATE_HOST_SUFFIXES):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_reserved


def _check_ref(value, kind, origin, referrer: PurePosixPath, files: set, report: dict):
    raw = value.strip()
    where = f"{referrer} {origin}"
    if not raw or raw.startswith("#") or raw.lower().startswith(SKIP_SCHEMES):
        return
    if "${" in raw or "{{" in raw or "{%" in raw:
        if kind != "navigation":
            report["unresolved"].append({"referrer": str(referrer), "origin": origin, "ref": raw,
                                         "reason": "templated reference; render it to a concrete local path"})
        else:
            report["warnings"].append(f"{where}: templated link {raw!r} not statically verifiable")
        return
    lowered = raw.lower()
    if lowered.startswith("file:"):
        report["errors"].append(f"{where}: file: URL {raw!r} will not resolve publicly")
        return
    if "\\" in raw:
        report["errors"].append(f"{where}: backslash in reference {raw!r}")
        return
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme or raw.startswith("//"):
        if parsed.scheme not in ("http", "https", ""):
            if kind != "navigation":
                report["unresolved"].append({"referrer": str(referrer), "origin": origin, "ref": raw,
                                             "reason": "unhandled URL scheme"})
            return
        if _host_is_private(parsed.hostname or ""):
            report["errors"].append(f"{where}: private/localhost URL {raw!r} is not publicly reachable")
            return
        if kind == "navigation":
            return
        if parsed.scheme == "http":
            report["errors"].append(f"{where}: insecure http resource {raw!r} is blocked as mixed content")
            return
        report["external_resources"].append({"referrer": str(referrer), "origin": origin, "url": raw})
        return
    if raw.startswith("/"):
        report["errors"].append(f"{where}: root-relative reference {raw!r} resolves outside the artifact prefix")
        return
    if kind == "module" and not raw.startswith(("./", "../")):
        report["unresolved"].append({"referrer": str(referrer), "origin": origin, "ref": raw,
                                     "reason": "bare module specifier; bundle it (import maps are not resolved)"})
        return
    path = urllib.parse.unquote(parsed.path)
    if not path:
        return
    parts = []
    for part in (referrer.parent / path).parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                report["errors"].append(f"{where}: reference {raw!r} escapes the bundle")
                return
            parts.pop()
        else:
            parts.append(part)
    target = "/".join(parts)
    if path.endswith("/") or (target and target not in files and any(f.startswith(target + "/") for f in files)):
        report["errors"].append(f"{where}: {raw!r} is a directory; S3 serves no directory index, link the file")
        return
    if target not in files:
        report["errors"].append(f"{where}: missing local asset {raw!r} (resolved {target!r})")


def _dangerous(name: str) -> bool:
    lower = name.lower()
    return (lower in DANGEROUS_NAMES or lower.startswith(".env") or lower.endswith(DANGEROUS_SUFFIXES)
            or lower.startswith("credentials") or lower.startswith("secrets."))


def _errcode(exc: OSError) -> str:
    """Stable errno name for receipts (OSError.errno may be None)."""
    if exc.errno is None:
        return type(exc).__name__
    return errno.errorcode.get(exc.errno, str(exc.errno))


def _read_all(fd: int) -> bytes:
    """Read a whole file from an already-open descriptor (no path re-resolve)."""
    chunks, total = [], 0
    while True:
        chunk = os.read(fd, 1 << 20)
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > MAX_READ_BYTES:
            raise OSError(errno.EFBIG, "file exceeds the read limit")
    return b"".join(chunks)


def _collect_files(root_fd: int, report: dict) -> dict:
    """Depth-first, fd-relative traversal binding validation to open handles.

    Every file and directory is opened relative to its parent directory
    descriptor with O_NOFOLLOW and validated with fstat stat.S_ISREG before
    any bytes are read, so a name swapped to a symlink after enumeration
    fails with ELOOP instead of reading outside the bundle. Bytes are read
    from the validated descriptors only; paths are never reopened.
    """
    handles = {}

    def fail_closed(exc: OSError, rel_dir: str) -> NoReturn:
        if exc.errno in (errno.EACCES, errno.EPERM):
            detail = "permission denied"
        elif exc.errno == errno.ELOOP:
            detail = "symlink cycle"
        elif exc.errno == errno.ENOENT:
            detail = "vanished during scan"
        else:
            detail = exc.strerror or _errcode(exc)
        raise Failure(EXIT_INVALID, "walk_failed",
                      f"cannot enumerate {rel_dir or '.'}: {detail} ({_errcode(exc)})")

    def walk(dir_fd: int, rel_dir: str, depth: int):
        if depth > MAX_DEPTH:
            raise Failure(EXIT_INVALID, "walk_failed", f"bundle nested deeper than {MAX_DEPTH} levels at {rel_dir}")
        try:
            names = sorted(os.listdir(dir_fd))
        except OSError as exc:
            fail_closed(exc, rel_dir)
        for name in names:
            rel = f"{rel_dir}/{name}" if rel_dir else name
            try:
                if any(ord(c) < 32 for c in rel):
                    report["errors"].append(f"control character in file name rejected: {rel!r}")
                    continue
                st = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
            except FileNotFoundError:
                continue  # raced away between listdir and stat: nothing to validate
            except OSError as exc:
                fail_closed(exc, rel_dir)
            if stat.S_ISLNK(st.st_mode):
                try:
                    target = os.stat(name, dir_fd=dir_fd)  # classify only; never opened
                except OSError:
                    target = None
                if target is not None and stat.S_ISDIR(target.st_mode):
                    report["errors"].append(f"symlinked directory rejected: {rel}")
                else:
                    report["errors"].append(f"symlink rejected: {rel}")
                continue
            if stat.S_ISDIR(st.st_mode):
                if _dangerous(name):
                    report["errors"].append(f"dangerous directory rejected: {rel}")
                    continue
                try:
                    sub_fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=dir_fd)
                except OSError as exc:
                    fail_closed(exc, rel)
                try:
                    walk(sub_fd, rel, depth + 1)
                finally:
                    os.close(sub_fd)
                continue
            if not stat.S_ISREG(st.st_mode):
                report["errors"].append(f"non-regular file rejected: {rel}")
                continue
            if _dangerous(name):
                report["errors"].append(f"dangerous file rejected: {rel}")
                continue
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
            except FileNotFoundError:
                continue  # raced away: never validated, never read
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    report["errors"].append(f"symlink rejected: {rel}")
                elif exc.errno in (errno.EACCES, errno.EPERM):
                    # Per-file unreadability is recorded and blocks publishing,
                    # but does not hide the rest of the bundle's receipts.
                    report["errors"].append(f"unreadable file rejected: {rel} ({type(exc).__name__})")
                else:
                    fail_closed(exc, rel_dir)
                continue
            try:
                opened_st = os.fstat(fd)
            except OSError as exc:
                os.close(fd)
                fail_closed(exc, rel_dir)
            if (opened_st.st_nlink < 1
                    or (opened_st.st_ino, opened_st.st_dev, opened_st.st_mode) != (st.st_ino, st.st_dev, st.st_mode)):
                # The name was replaced/unlinked between enumeration and the
                # validated open: the handle no longer matches what was listed.
                os.close(fd)
                report["errors"].append(f"changed during scan rejected: {rel}")
                continue
            if not stat.S_ISREG(opened_st.st_mode):
                os.close(fd)
                report["errors"].append(f"non-regular file rejected: {rel}")
                continue
            handles[rel] = fd

    walk(root_fd, "", 0)
    return handles


def scan_bundle(bundle: Path, entry: str, accepted=frozenset()) -> dict:
    report = {"errors": [], "warnings": [], "external_resources": [], "unresolved": [], "files": [],
              "accepted_js_candidates": []}
    used = set()
    absolute = bundle.absolute()
    linked = [str(p) for p in (absolute, *absolute.parents) if p.is_symlink()]
    if linked:
        raise Failure(EXIT_INVALID, "bundle_invalid",
                      f"--bundle path must not traverse symlinks (pass the real path): {linked[0]}")
    if not bundle.is_dir():
        raise Failure(EXIT_INVALID, "bundle_invalid", f"--bundle must be a real directory: {bundle}")
    bundle = bundle.resolve()
    if (bundle / ".git").exists() or (bundle / ".project.json").exists():
        report["errors"].append("bundle looks like a repository root; stage the artifact in its own directory")
    entry_path = PurePosixPath(entry)
    if any(ord(c) < 32 for c in entry) or entry_path.is_absolute() or ".." in entry_path.parts or entry_path.suffix.lower() not in (".html", ".htm"):
        raise Failure(EXIT_INVALID, "entry_invalid", "--entry must be a relative .html path inside the bundle")
    # Open the bundle root without following symlinks; every child is reached
    # through this (and nested) directory descriptors, never by re-walking a
    # path that could have been swapped between enumeration and reading.
    try:
        root_fd = _open_bundle_root(bundle)
    except OSError as exc:
        raise Failure(EXIT_INVALID, "walk_failed",
                      f"cannot open bundle root: {exc.strerror or _errcode(exc)} ({_errcode(exc)})")
    try:
        handles = _collect_files(root_fd, report)
    finally:
        os.close(root_fd)
    files = sorted(handles)
    if len(files) > MAX_FILES:
        raise Failure(EXIT_INVALID, "bundle_too_large", f"bundle has {len(files)} files (max {MAX_FILES})")
    fileset = set(files)
    if entry_path.as_posix() not in fileset:
        report["errors"].append(f"entry {entry!r} not found in bundle")
    for rel in files:
        fd = handles.pop(rel)
        try:
            data = _read_all(fd)
        except OSError as exc:
            report["errors"].append(f"unreadable file rejected: {rel} ({type(exc).__name__})")
            continue
        finally:
            os.close(fd)
        if PRIVATE_KEY_MARK in data and PRIVATE_KEY_RE.search(data):
            report["errors"].append(f"private key material detected in {rel}")
        suffix = PurePosixPath(rel).suffix.lower()
        name = PurePosixPath(rel).name
        if name.startswith("."):
            report["warnings"].append(f"{rel}: dotfile will be public")
        elif suffix in (".map", ".ts", ".tsx", ".jsx"):
            report["warnings"].append(f"{rel}: {suffix} source/source-map will be public")
        report["files"].append({"path": rel, "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                "content_type": MIME.get(suffix, "application/octet-stream")})
        referrer = PurePosixPath(rel)
        text = data.decode("utf-8", errors="replace")
        refs, js_refs = [], []  # JS candidates stay separate: a waiver never covers HTML/CSS refs
        if suffix in (".html", ".htm", ".svg"):
            parser = _RefParser()
            parser.feed(text)
            parser.close()
            if parser.base:
                report["errors"].append(f"{rel}: <base href> is not supported; use relative paths")
            refs.extend(parser.refs)
            for css in parser.inline_css:
                refs.extend(_css_refs(css, "inline css"))
            for js in parser.inline_js:
                js_refs.extend(_js_refs(js, "inline script"))
        elif suffix == ".css":
            refs.extend(_css_refs(text, "css"))
        elif suffix in (".js", ".mjs"):
            js_refs.extend(_js_refs(text, "js import"))
        for value, kind, origin in refs:
            _check_ref(value, kind, origin, referrer, fileset, report)
        for value, kind, origin in js_refs:
            if (rel, value) in accepted:
                used.add((rel, value))
                continue
            blocked = len(report["errors"]) + len(report["unresolved"]) + len(report["external_resources"])
            _check_ref(value, kind, origin, referrer, fileset, report)
            if isinstance(value, _OpenJsLiteral) and blocked == (
                    len(report["errors"]) + len(report["unresolved"]) + len(report["external_resources"])):
                # Uncertain raw text (even empty, '#', data: or a resolving
                # prefix) must never pass silently.
                report["unresolved"].append({"referrer": rel, "origin": origin, "ref": str(value),
                                             "reason": "JS literal not closed (end of text, line break, "
                                                       "dangling escape or length cap); raw text kept for review"})
    report["accepted_js_candidates"] = [{"file": f, "specifier": s} for f, s in sorted(used)]
    for f, s in sorted(set(accepted) - used):
        report["errors"].append(f"unused --accept-js-candidate {f}:{s}: no JS candidate {s!r} was emitted "
                                f"for {f!r}; acceptances must match an emitted candidate exactly")
    return report


# ---------------------------------------------------------------- plan

def validate_remote(alias: str, bucket: str, base_url: str) -> str:
    """Reject anything that could smuggle a path, credential, or insecure origin into targets/URLs."""
    if not isinstance(alias, str) or not ALIAS_RE.fullmatch(alias):
        raise Failure(EXIT_INVALID, "remote_invalid", "--alias must be a plain mc alias name ([A-Za-z0-9_-])")
    if not isinstance(bucket, str) or not BUCKET_RE.fullmatch(bucket):
        raise Failure(EXIT_INVALID, "remote_invalid", "bucket name is invalid")
    if not isinstance(base_url, str) or any(ord(c) < 33 for c in base_url):
        raise Failure(EXIT_INVALID, "remote_invalid", "base URL is invalid")
    parsed = urllib.parse.urlsplit(base_url)
    if (parsed.scheme != "https" or not parsed.hostname or "@" in parsed.netloc or parsed.query
            or parsed.fragment or "?" in base_url or "#" in base_url or parsed.path not in ("", "/")):
        raise Failure(EXIT_INVALID, "remote_invalid",
                      "base URL must be https://host with no credentials, path, query, or fragment")
    return base_url.rstrip("/")


def build_plan(args, env) -> dict:
    base = validate_remote(args.alias, BUCKET, BASE_URL)
    if not SLUG_RE.fullmatch(args.artifact or ""):
        raise Failure(EXIT_INVALID, "artifact_invalid", "--artifact must be a safe name ([A-Za-z0-9._-])")
    project = resolve_project(args.project, args.project_root)
    session = resolve_session(args.bb_session_id, args.harness, args.native_session_id, env)
    accepted = parse_acceptances(getattr(args, "accept_js_candidate", None))
    bundle = Path(args.bundle).expanduser()
    report = scan_bundle(bundle, args.entry, accepted)
    prefix = f"{project['slug']}/{session['bb_session_id']}/{args.artifact}/"
    for item in report["files"]:
        key = prefix + item["path"]
        item["key"] = key
        item["target"] = f"{args.alias}/{BUCKET}/{key}"
        item["url"] = f"{base}/{BUCKET}/{urllib.parse.quote(key)}"
    return {
        "mode": "publish" if args.publish else "plan",
        "entry_url": f"{base}/{BUCKET}/{urllib.parse.quote(prefix + PurePosixPath(args.entry).as_posix())}",
        "prefix_url": f"{base}/{BUCKET}/{urllib.parse.quote(prefix)}",
        "remote": {"alias": args.alias, "bucket": BUCKET, "prefix": prefix},
        "bundle": str(bundle.resolve()),
        "entry": PurePosixPath(args.entry).as_posix(),
        "provenance": {"project": project, "session": session, "artifact": args.artifact},
        "files": report["files"],
        "external_resources": report["external_resources"],
        "unresolved": report["unresolved"],
        "accepted_js_candidates": report["accepted_js_candidates"],
        "publishable": not (report["errors"] or report["external_resources"] or report["unresolved"]),
        "warnings": report["warnings"],
        "errors": report["errors"],
        "limits": [
            "static discovery only: runtime fetch()/dynamic imports/JS-built URLs are not followed",
            "JS module discovery is raw text matching: import-shaped strings/comments/regexes are reported, "
            "computed import(expr) is not; waive only inspected false positives with --accept-js-candidate",
            "publish complete build output and verify the entry URL in a browser for dynamic JS",
        ],
    }


# ---------------------------------------------------------------- remote

SECRETISH_RE = re.compile(
    r"(?i)((?:access|secret|session)[_-]?key[^\s]*|signature=[^\s&]+|credential=[^\s&]+|"
    r"[A-Za-z0-9+/]{32,}={0,2}|AKIA[0-9A-Z]{16}|https?://[^/\s:@]+:[^/\s@]+@)")


def redact(text: str) -> str:
    return SECRETISH_RE.sub("[redacted]", str(text))[:300]


def _mc_error(stdout: str, stderr: str) -> dict:
    for line in (stdout + "\n" + stderr).splitlines():
        try:
            doc = json.loads(line)
        except ValueError:
            continue
        if isinstance(doc, dict) and doc.get("status") == "error":
            err = doc.get("error") or {}
            cause = (err.get("cause") or {}).get("error") or {}
            return {"code": cause.get("Code") or "mc_error",
                    "message": redact(cause.get("Message") or err.get("message") or "mc failed")}
    return {"code": "mc_error", "message": "mc failed without a JSON error (stderr suppressed)"}


def _run(runner, cmd, timeout):
    try:
        return runner(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise Failure(EXIT_REMOTE, "timeout", f"mc {cmd[1]} timed out after {timeout}s")
    except FileNotFoundError:
        raise Failure(EXIT_REMOTE, "mc_missing", "mc executable not found")
    except OSError as exc:
        # PermissionError, EAGAIN (process/table exhaustion), ENOMEM, ...: every
        # OS-level failure to spawn/read the subprocess is a normalized remote
        # failure, never an escape from partial-upload accounting.
        raise Failure(EXIT_REMOTE, "os_error",
                      f"mc {cmd[1]} could not run: {type(exc).__name__}: {redact(str(exc))}",
                      os_errno=exc.errno)


def preflight(plan, runner, timeout):
    remote = plan["remote"]
    target = f"{remote['alias']}/{remote['bucket']}/{remote['prefix']}"
    proc = _run(runner, ["mc", "ls", "--json", "--recursive", target], timeout)
    if proc.returncode != 0:
        err = _mc_error(proc.stdout or "", proc.stderr or "")
        raise Failure(EXIT_REMOTE, "preflight_failed", err["message"], mc_code=err["code"])
    existing = []
    for line in (proc.stdout or "").splitlines():
        if not line.strip():
            continue
        try:
            doc = json.loads(line)
        except ValueError:
            doc = None
        if isinstance(doc, dict) and doc.get("status") == "error":
            err = _mc_error(proc.stdout or "", "")
            raise Failure(EXIT_REMOTE, "preflight_failed", err["message"], mc_code=err["code"])
        if not (isinstance(doc, dict) and isinstance(doc.get("key"), str) and doc["key"]):
            # Unreadable listing must not be mistaken for an empty prefix.
            raise Failure(EXIT_REMOTE, "preflight_malformed",
                          "mc ls returned output that is not a recognizable object listing")
        existing.append(doc["key"])
    if existing:
        raise Failure(EXIT_COLLISION, "collision",
                      "objects already exist under the artifact prefix; choose a new --artifact",
                      existing_count=len(existing), existing_sample=existing[:10])


def _open_bundle_root(path) -> int:
    """Open the (already resolved) bundle root via a descriptor chain from /.

    Every component is opened with O_NOFOLLOW, so not only files inside the
    bundle but the directory chain to the bundle itself cannot be swapped to
    a symlink between the path checks and the traversal.
    """
    fd = os.open(os.sep, os.O_RDONLY | os.O_DIRECTORY)
    for part in PurePosixPath(str(path)).parts[1:]:
        prev = fd
        try:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=prev)
        except OSError:
            os.close(prev)
            raise
        os.close(prev)
    return fd


def _open_rel_dir(base_fd: int, rel_dir: PurePosixPath):
    """Open a nested bundle subdirectory through a descriptor chain.

    Returns the deepest directory fd, or None when rel_dir is the bundle root
    (the caller keeps using base_fd). Intermediate descriptors are closed.
    Symlinked components fail with ELOOP instead of escaping the bundle.
    """
    fd, opened = base_fd, None
    for part in rel_dir.parts:
        fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        if opened is not None:
            os.close(opened)
        opened = fd
    return opened


def _snapshot(plan, bundle_root=None) -> Path:
    """Materialize the validated bytes in a private dir (0700) before upload.

    mc cp re-reads the source path, so a file swapped to a symlink (or rewritten
    by a build watcher) between scan and upload could publish bytes that were
    never validated. The source is re-opened without following symlinks,
    relative to the bundle root descriptor, and re-hashed against the plan;
    either the exact validated bytes are copied, or nothing is. The snapshot
    directory is removed on every failure path inside this function, so a
    failed attempt never leaves a partial copy on disk.
    """
    root = Path(bundle_root if bundle_root is not None else plan["bundle"])
    snap = Path(tempfile.mkdtemp(prefix="html-artifact-delivery-"))
    try:
        os.chmod(snap, 0o700)
        try:
            bundle_fd = _open_bundle_root(root)
        except OSError as exc:
            raise Failure(EXIT_INVALID, "bundle_changed",
                          f"bundle could not be re-opened after validation "
                          f"({_errcode(exc)}); re-run the plan")
        try:
            for item in plan["files"]:
                rel, pure = item["path"], PurePosixPath(item["path"])
                try:
                    parent_fd = _open_rel_dir(bundle_fd, pure.parent)
                except OSError as exc:
                    raise Failure(EXIT_INVALID, "bundle_changed",
                                  f"{rel} could not be re-read after validation "
                                  f"({_errcode(exc)}); re-run the plan")
                try:
                    try:
                        src_fd = os.open(pure.name, os.O_RDONLY | os.O_NOFOLLOW,
                                         dir_fd=parent_fd if parent_fd is not None else bundle_fd)
                    except OSError as exc:
                        raise Failure(EXIT_INVALID, "bundle_changed",
                                      f"{rel} could not be re-read after validation "
                                      f"({_errcode(exc)}); re-run the plan")
                    try:
                        data = _read_all(src_fd)
                    finally:
                        os.close(src_fd)
                finally:
                    if parent_fd is not None:
                        os.close(parent_fd)
                if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                    raise Failure(EXIT_INVALID, "bundle_changed",
                                  f"{rel} changed after validation; re-run the plan")
                dest = snap / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
        finally:
            os.close(bundle_fd)
        return snap
    except BaseException:
        shutil.rmtree(snap, ignore_errors=True)
        raise


def upload(plan, runner, timeout, snapshot=None):
    """Upload every planned object. Any mid-loop failure (mc error, timeout,
    missing binary, or any other OS error from the runner) is re-raised with
    full uploaded/failed/not_attempted accounting so a partial publish is
    always reported."""
    root = snapshot if snapshot is not None else Path(plan["bundle"])
    uploaded = []
    try:
        for item in plan["files"]:
            attr = f"Content-Type={item['content_type']};Cache-Control={CACHE_CONTROL}"
            local = str(root / item["path"])
            proc = _run(runner, ["mc", "cp", "--json", "--attr", attr, local, item["target"]], timeout)
            if proc.returncode != 0 or '"status":"error"' in (proc.stdout or "").replace(" ", ""):
                err = _mc_error(proc.stdout or "", proc.stderr or "")
                raise Failure(EXIT_UPLOAD, "upload_failed",
                              f"upload failed for {item['path']}: {err['message']}", mc_code=err["code"])
            uploaded.append(item["path"])
    except Failure as exc:
        failed = plan["files"][len(uploaded)]["path"]
        not_attempted = [f["path"] for f in plan["files"][len(uploaded) + 1:]]
        extra = {"cause": exc.kind, "uploaded": uploaded, "failed": failed,
                 "not_attempted": not_attempted}
        if exc.extra.get("mc_code"):
            extra["mc_code"] = exc.extra["mc_code"]
        raise Failure(EXIT_UPLOAD, "upload_failed", f"upload failed for {failed}: {exc.message}", **extra)
    except OSError as exc:
        # A runner that bypasses _run's normalization still gets accounting.
        failed = plan["files"][len(uploaded)]["path"]
        not_attempted = [f["path"] for f in plan["files"][len(uploaded) + 1:]]
        raise Failure(EXIT_UPLOAD, "upload_failed",
                      f"upload failed for {failed}: {type(exc).__name__}: {redact(str(exc))}",
                      cause="os_error", uploaded=uploaded, failed=failed,
                      not_attempted=not_attempted)
    return uploaded


def public_address(host, timeout):
    """The host's address in public DNS (Cloudflare DoH), or None.

    The publishing machine pins s3.delo.sh to loopback in /etc/hosts, which
    would make verification check the origin instead of the public edge a
    viewer gets (tunnel up, no body rewrite)."""
    query = urllib.parse.urlencode({"name": host, "type": "A"})
    req = urllib.request.Request(f"https://1.1.1.1/dns-query?{query}", headers={"Accept": "application/dns-json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            answers = json.load(resp).get("Answer") or []
    except (OSError, ValueError):
        return None
    return next((a["data"] for a in answers if a.get("type") == 1), None)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS to a fixed address, with SNI and certificate checks for the URL's host."""

    def __init__(self, host, address, **kwargs):
        super().__init__(host, **kwargs)
        self._address = address

    def connect(self):
        sock = socket.create_connection((self._address, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def default_fetch(url, timeout):
    """Anonymous GET through the public edge: no credentials, no cookies.

    Returns (status, content_type, body)."""
    headers = {"User-Agent": "html-artifact-delivery/1", "Cache-Control": "no-cache"}
    parts = urllib.parse.urlsplit(url)
    address = public_address(parts.hostname, timeout) if parts.scheme == "https" else None
    if address is None:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.headers.get("Content-Type", ""), resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers.get("Content-Type", "") if exc.headers else "", b""
    conn = _PinnedHTTPSConnection(parts.hostname, address, port=parts.port, timeout=timeout,
                                  context=ssl.create_default_context())
    try:
        path = parts.path or "/"
        conn.request("GET", f"{path}?{parts.query}" if parts.query else path, headers=headers)
        resp = conn.getresponse()
        body = resp.read()
        return resp.status, resp.getheader("Content-Type", ""), body if resp.status == 200 else b""
    finally:
        conn.close()


def verify(plan, fetch, timeout):
    results, failures = [], []
    for item in plan["files"]:
        try:
            status, ctype, body = fetch(item["url"], timeout)
        except Exception as exc:  # network errors become a recorded failure
            status, ctype, body = None, "", None
            problem = f"request failed: {type(exc).__name__}"
        else:
            problem = None
        got_type = (ctype or "").split(";")[0].strip().lower()
        # An empty 200 body is real content (zero-byte CSS); hash it like any other.
        digest = hashlib.sha256(body).hexdigest() if status == 200 and isinstance(body, bytes) else None
        if problem is None:
            if status != 200:
                problem = f"HTTP {status}"
            elif got_type != item["content_type"]:
                problem = f"content-type {got_type!r} != {item['content_type']!r}"
            elif digest != item["sha256"]:
                problem = "sha256 mismatch"
        result = {"path": item["path"], "url": item["url"], "status": status, "content_type": got_type,
                  "sha256_match": digest == item["sha256"], "ok": problem is None}
        if problem:
            result["problem"] = problem
            failures.append(result)
        results.append(result)
    return results, failures


# ---------------------------------------------------------------- cli

def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="offline plan (default)")
    mode.add_argument("--publish", action="store_true", help="upload with mc and verify over HTTPS")
    p.add_argument("--bundle", required=True, help="explicit staging directory (never a whole repo)")
    p.add_argument("--entry", default="index.html", help="entry HTML path relative to --bundle")
    p.add_argument("--artifact", required=True, help="artifact subfolder; use a new name per version")
    p.add_argument("--project", help="explicit project slug")
    p.add_argument("--project-root", help="project path (worktrees resolve to the main worktree)")
    p.add_argument("--bb-session-id", help="Bloodbank session UUID")
    p.add_argument("--harness", help="agent harness name, e.g. codex, claude, hermes")
    p.add_argument("--native-session-id", help="harness-native session id")
    p.add_argument("--alias", default=DEFAULT_ALIAS, help="existing mc alias name (bucket and URL are fixed)")
    p.add_argument("--timeout", type=float, default=60.0, help="per-command / per-request seconds")
    p.add_argument("--accept-js-candidate", action="append", default=[], metavar="FILE:SPECIFIER",
                   help="repeatable: waive one inspected false-positive JS candidate, exactly as emitted, in "
                        "one bundle-relative file (all its occurrences there); unused waivers are refused")
    return p.parse_args(argv)


def main(argv=None, env=None, runner=subprocess.run, fetch=default_fetch, out=sys.stdout) -> int:
    args = parse_args(argv)
    env = os.environ if env is None else env
    timeout = max(1.0, min(args.timeout, 600.0))
    plan = None
    snapshot = None
    try:
        plan = build_plan(args, env)
        if plan["errors"]:
            raise Failure(EXIT_INVALID, "bundle_invalid", f"{len(plan['errors'])} validation error(s)")
        if not args.publish:
            plan["ok"] = True
            plan["delivered"] = False
            plan["next"] = ("re-run with --publish to upload and verify" if plan["publishable"] else
                            "localize/bundle every external_resources and unresolved entry before --publish")
            _emit(out, plan)
            return EXIT_OK
        if not plan["publishable"]:
            raise Failure(EXIT_INVALID, "unresolved_dependencies",
                          f"{len(plan['external_resources'])} external and {len(plan['unresolved'])} unresolved "
                          "required resource(s); localize or bundle them before publishing")
        snapshot = _snapshot(plan)  # pin uploads to the validated bytes
        try:
            preflight(plan, runner, timeout)
            plan["uploaded"] = upload(plan, runner, timeout, snapshot)
            plan["verification"], failures = verify(plan, fetch, timeout)
            if failures:
                raise Failure(EXIT_VERIFY, "verify_failed",
                              f"{len(failures)} of {len(plan['files'])} object(s) failed public verification")
        finally:
            with contextlib.suppress(OSError):
                shutil.rmtree(snapshot, ignore_errors=True)
        plan["ok"] = True
        plan["delivered"] = True
        _emit(out, plan)
        return EXIT_OK
    except subprocess.TimeoutExpired as exc:  # a runner bypassing _run still gets JSON
        doc = plan or {"mode": "publish" if args.publish else "plan"}
        doc["ok"] = False
        doc["delivered"] = False
        doc["failure"] = {"kind": "timeout", "message": f"command timed out: {exc.cmd}",
                          "exit_code": EXIT_REMOTE}
        _emit(out, doc)
        return EXIT_REMOTE
    except Failure as exc:
        doc = plan or {"mode": "publish" if args.publish else "plan"}
        doc["ok"] = False
        doc["delivered"] = False
        doc["failure"] = {"kind": exc.kind, "message": exc.message, "exit_code": exc.code, **exc.extra}
        if exc.code in (EXIT_UPLOAD, EXIT_VERIFY):
            doc["failure"]["retry"] = ("objects may be partially uploaded and are not deleted; "
                                       "publish again with a new --artifact")
        _emit(out, doc)
        return exc.code
    except OSError as exc:  # unreadable paths etc. keep the JSON output contract
        doc = plan or {"mode": "publish" if args.publish else "plan"}
        doc["ok"] = False
        doc["delivered"] = False
        doc["failure"] = {"kind": "os_error", "message": f"{type(exc).__name__}: {exc}", "exit_code": EXIT_UNEXPECTED}
        _emit(out, doc)
        return EXIT_UNEXPECTED


def _emit(out, doc):
    out.write(json.dumps(doc, indent=2, sort_keys=False) + "\n")
    out.flush()


if __name__ == "__main__":
    sys.exit(main())
