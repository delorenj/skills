"""Validating egress proxy for the fetch child.

The upstream binary parses URLs and resolves DNS on its own, so any check the wrapper does first races with it
(backslash and numeric-host parser differences, redirect hops, DNS rebinding). Running the child behind this proxy
moves the decision to the one place that sees what it will really connect to: every request, redirect hop and CONNECT
arrives here with the host already normalised by the child's URL parser. Each host is resolved once, refused unless
every answer is a public address, and the upstream connection is made to that exact address, so a second lookup
never happens and a flipping nameserver has nothing to flip.
"""
import ipaddress
import select
import socket
import socketserver
import threading
import time
from urllib.parse import urlsplit

_V4_DENY = [ipaddress.ip_network(n) for n in (
    "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12", "192.0.0.0/24",
    "192.0.2.0/24", "192.88.99.0/24", "192.168.0.0/16", "198.18.0.0/15", "198.51.100.0/24", "203.0.113.0/24",
    "224.0.0.0/4", "240.0.0.0/4")]
_V6_DENY = [ipaddress.ip_network(n) for n in (
    "::/96", "::ffff:0:0/96", "64:ff9b::/96", "64:ff9b:1::/48", "100::/64", "2001::/32", "2001:db8::/32",
    "2002::/16", "fc00::/7", "fe80::/10", "fec0::/10", "ff00::/8")]

MAX_HEAD = 64 * 1024
IDLE_SECONDS = 60.0
CONNECT_SECONDS = 10.0
TUNNEL_SECONDS = 300.0
_HOP_BY_HOP = {"proxy-connection", "connection", "keep-alive", "proxy-authorization", "te", "trailer",
               "transfer-encoding", "upgrade", "host"}


class Refused(Exception):
    """The target resolves to something that is not a public address."""


class Unresolvable(Exception):
    """The target could not be resolved at all (a plain failure, not a security refusal)."""


class BadRequest(Exception):
    pass


def is_public(text):
    """True only for globally routable unicast addresses. The explicit deny lists keep the answer stable across
    Python versions and cover IPv6 transition ranges that embed IPv4 (NAT64, 6to4, IPv4-compatible, SIIT)."""
    try:
        ip = ipaddress.ip_address(str(text).split("%", 1)[0])
    except ValueError:
        return False
    deny = _V4_DENY if ip.version == 4 else _V6_DENY
    return ip.is_global and not ip.is_multicast and not any(ip in net for net in deny)


def resolve_public(host, port, resolver=socket.getaddrinfo, allow=is_public):
    """Resolve once and return the answers, refusing unless there is at least one and every one is public."""
    try:
        infos = resolver(host, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError, OSError) as exc:
        raise Unresolvable(f"cannot resolve {host}: {getattr(exc, 'strerror', None) or exc}")
    addrs = []
    for info in infos:
        if info[4][0] not in addrs:
            addrs.append(info[4][0])
    if not addrs:
        raise Unresolvable(f"{host} has no addresses")
    bad = [a for a in addrs if not allow(a)]
    if bad:
        raise Refused(f"{host} resolves to non-public address {', '.join(bad)}")
    return addrs


def _split_hostport(target):
    if target.startswith("["):
        host, _, rest = target[1:].partition("]")
        port = rest.lstrip(":")
    else:
        host, _, port = target.rpartition(":")
    if not host or not port.isdigit() or not 0 < int(port) < 65536:
        raise BadRequest(f"bad CONNECT target {target!r}")
    return host, int(port)


def _read_head(sock):
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            raise BadRequest("connection closed before the request head ended")
        buf += chunk
        if len(buf) > MAX_HEAD:
            raise BadRequest("request head too large")
    head, _, rest = buf.partition(b"\r\n\r\n")
    return head, rest


def _connect(addrs, port):
    last = None
    for addr in addrs:
        try:
            return socket.create_connection((addr, port), timeout=CONNECT_SECONDS)
        except OSError as exc:
            last = exc
    raise last or OSError("no address to connect to")


def _splice(a, b):
    deadline = time.monotonic() + TUNNEL_SECONDS
    a.settimeout(IDLE_SECONDS)
    b.settimeout(IDLE_SECONDS)
    while time.monotonic() < deadline:
        ready, _, _ = select.select([a, b], [], [], IDLE_SECONDS)
        if not ready:
            return
        for src in ready:
            data = src.recv(65536)
            if not data:
                return
            (b if src is a else a).sendall(data)


def _respond(sock, status, reason, body=""):
    payload = body.encode("utf-8", "replace")
    sock.sendall(f"HTTP/1.1 {status} {reason}\r\nContent-Type: text/plain\r\nContent-Length: {len(payload)}\r\n"
                 f"Connection: close\r\n\r\n".encode("ascii") + payload)


class _Handler(socketserver.BaseRequestHandler):
    def handle(self):
        owner = self.server.owner
        client = self.request
        upstream = None
        try:
            client.settimeout(IDLE_SECONDS)
            head, rest = _read_head(client)
            lines = head.split(b"\r\n")
            try:
                method, target, version = lines[0].decode("ascii").split(" ")
            except (UnicodeError, ValueError):
                raise BadRequest("malformed request line")
            if not version.startswith("HTTP/1."):
                raise BadRequest("unsupported HTTP version")
            if method == "CONNECT":
                host, port = _split_hostport(target)
            elif method == "GET":
                try:
                    parts = urlsplit(target)
                    target_port = parts.port
                except ValueError:
                    raise BadRequest("malformed target URL")
                if parts.scheme != "http" or not parts.hostname:
                    raise BadRequest("only absolute http:// GET targets are proxied")
                host, port = parts.hostname, target_port or 80
            else:
                _respond(client, 405, "Method Not Allowed", "only GET and CONNECT are proxied")
                return
            owner.log.append((method, host, port))
            try:
                addrs = resolve_public(host, port, owner.resolver, owner.allow)
            except Unresolvable as exc:
                _respond(client, 502, "Bad Gateway", str(exc))
                return
            except Refused as exc:
                owner.refusals.append(str(exc))
                _respond(client, 403, "Forbidden", f"egress guard: {exc}")
                return
            upstream = _connect(addrs, port)
            if method == "CONNECT":
                client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                if rest:
                    upstream.sendall(rest)
                _splice(client, upstream)
                return
            path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
            headers = []
            for raw in lines[1:]:
                name, sep, value = raw.decode("latin-1").partition(":")
                if sep and name.strip().lower() not in _HOP_BY_HOP:
                    headers.append(f"{name.strip()}: {value.strip()}")
            netloc = parts.hostname if ":" not in parts.hostname else f"[{parts.hostname}]"
            headers = [f"Host: {netloc}" + (f":{target_port}" if target_port else "")] + headers + ["Connection: close"]
            upstream.sendall(f"GET {path} HTTP/1.1\r\n".encode("ascii", "replace")
                             + "\r\n".join(headers).encode("latin-1", "replace") + b"\r\n\r\n")
            upstream.settimeout(IDLE_SECONDS)
            while True:
                data = upstream.recv(65536)
                if not data:
                    break
                client.sendall(data)
        except BadRequest as exc:
            try:
                _respond(client, 400, "Bad Request", str(exc))
            except OSError:
                pass
        except OSError as exc:
            try:
                _respond(client, 502, "Bad Gateway", f"upstream error: {exc.__class__.__name__}")
            except OSError:
                pass
        except Exception as exc:
            owner.errors.append(repr(exc))
            try:
                _respond(client, 502, "Bad Gateway", "internal proxy error")
            except OSError:
                pass
        finally:
            if upstream is not None:
                upstream.close()


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class EgressProxy:
    """Loopback-only proxy on an ephemeral port. The socket is bound and listening as soon as the object exists,
    but nothing is served until start(): spawn the child first, then start(), so the fork happens before any
    thread exists. `refusals` lists every request it refused; `errors` any unexpected handler failure."""

    def __init__(self, resolver=socket.getaddrinfo, allow=is_public):
        self.resolver = resolver
        self.allow = allow
        self.refusals = []
        self.errors = []
        self.log = []
        self._server = _Server(("127.0.0.1", 0), _Handler)
        self._server.owner = self
        self._thread = None

    @property
    def url(self):
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def start(self):
        self._thread = threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self._thread.start()
        return self

    def close(self):
        if self._thread is not None:
            self._server.shutdown()
        self._server.server_close()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.close()
