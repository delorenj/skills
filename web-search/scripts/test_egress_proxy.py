#!/usr/bin/env python3
"""Tests for the egress proxy. Run: python3 scripts/test_egress_proxy.py (no network, loopback sockets only)."""
import os
import socket
import socketserver
import sys
import threading
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import egress_proxy as ep  # noqa: E402


def fake_resolver(mapping):
    """Resolver stub: name -> list of addresses (or an exception to raise)."""
    calls = []

    def resolve(host, port, type=0):
        calls.append(host)
        answer = mapping[host]
        if isinstance(answer, Exception):
            raise answer
        return [(2, 1, 6, "", (a, port)) for a in answer]

    resolve.calls = calls
    return resolve


class Origin:
    """Loopback origin that records raw requests and answers with a canned response."""

    def __init__(self, response=b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 5\r\nConnection: close\r\n\r\nhello"):
        self.requests = []
        outer = self

        class H(socketserver.BaseRequestHandler):
            def handle(self):
                data = b""
                while b"\r\n\r\n" not in data:
                    chunk = self.request.recv(4096)
                    if not chunk:
                        return
                    data += chunk
                outer.requests.append(data)
                self.request.sendall(response)

        class S(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        self.server = S(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class EchoOrigin(Origin):
    def __init__(self):
        outer = self

        class H(socketserver.BaseRequestHandler):
            def handle(self):
                while True:
                    data = self.request.recv(4096)
                    if not data:
                        return
                    self.request.sendall(data.upper())

        class S(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        self.requests = []
        self.server = S(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()


def talk(proxy, payload, read_until_close=True, extra=b""):
    host, port = "127.0.0.1", int(proxy.url.rsplit(":", 1)[1])
    with socket.create_connection((host, port), timeout=5) as s:
        s.sendall(payload)
        out = b""
        while True:
            try:
                chunk = s.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            out += chunk
            if not read_until_close:
                break
        return out


class IsPublic(unittest.TestCase):
    def test_public_addresses(self):
        for addr in ("8.8.8.8", "93.184.216.34", "1.1.1.1", "2606:4700:4700::1111", "2a00:1450:4001:81c::200e"):
            self.assertTrue(ep.is_public(addr), addr)

    def test_non_public_addresses(self):
        for addr in ("127.0.0.1", "127.255.255.254", "0.0.0.0", "10.0.0.1", "172.16.5.5", "172.31.255.255",
                     "192.168.0.1", "169.254.169.254", "100.64.0.1", "100.66.29.76", "100.127.255.255", "192.0.0.8",
                     "192.0.2.1", "198.18.0.1", "198.51.100.7", "203.0.113.9", "224.0.0.1", "239.255.255.250",
                     "240.0.0.1", "255.255.255.255", "::1", "::", "::127.0.0.1", "::7f00:1", "::ffff:127.0.0.1",
                     "::ffff:8.8.8.8", "64:ff9b::7f00:1", "64:ff9b::a9fe:a9fe", "64:ff9b:1::1", "2002:7f00:1::",
                     "2001::1", "2001:db8::1", "fe80::1", "fe80::1%eth0", "fc00::1", "fd12:3456::1", "fec0::1",
                     "ff02::1", "100::1", "not-an-ip", ""):
            self.assertFalse(ep.is_public(addr), addr)


class ResolvePublic(unittest.TestCase):
    def test_non_public_mixed_answers_are_refused(self):
        with self.assertRaises(ep.Refused):
            ep.resolve_public("x", 80, fake_resolver({"x": ["8.8.8.8", "10.0.0.5"]}), ep.is_public)

    def test_resolution_failures_are_unresolvable_not_refusals(self):
        for answer in ([], socket.gaierror(-2, "Name or service not known"), UnicodeError("label too long")):
            with self.assertRaises(ep.Unresolvable):
                ep.resolve_public("x", 80, fake_resolver({"x": answer}), ep.is_public)

    def test_deduplicates_answers(self):
        self.assertEqual(ep.resolve_public("x", 80, fake_resolver({"x": ["8.8.8.8", "8.8.8.8"]}), ep.is_public), ["8.8.8.8"])


class ProxyBehaviour(unittest.TestCase):
    def setUp(self):
        self.origin = Origin()
        self.addCleanup(self.origin.close)

    def proxy(self, mapping, allow=lambda ip: ip == "127.0.0.1"):
        resolver = fake_resolver(mapping)
        p = ep.EgressProxy(resolver=resolver, allow=allow)
        p.resolver_stub = resolver
        return p

    def get(self, p, host, headers=b""):
        req = (f"GET http://{host}:{self.origin.port}/a/b?x=1 HTTP/1.1\r\nHost: {host}:{self.origin.port}\r\n"
               f"User-Agent: t/1\r\nAccept: */*\r\n").encode() + headers + b"\r\n"
        return talk(p, req)

    def test_get_is_forwarded_in_origin_form_without_hop_by_hop_headers(self):
        with self.proxy({"public.test": ["127.0.0.1"]}) as p:
            out = self.get(p, "public.test", b"Proxy-Connection: keep-alive\r\nProxy-Authorization: Basic eDp5\r\nKeep-Alive: 5\r\n")
        self.assertTrue(out.startswith(b"HTTP/1.1 200 OK"), out[:80])
        self.assertTrue(out.endswith(b"hello"))
        seen = self.origin.requests[0].decode("latin-1")
        self.assertTrue(seen.startswith("GET /a/b?x=1 HTTP/1.1\r\n"), seen)
        self.assertIn(f"Host: public.test:{self.origin.port}", seen)
        self.assertIn("User-Agent: t/1", seen)
        self.assertIn("Connection: close", seen)
        for banned in ("Proxy-Connection", "Proxy-Authorization", "Keep-Alive"):
            self.assertNotIn(banned, seen)
        self.assertEqual(p.refusals, [])

    def test_private_resolution_is_refused_with_403_and_recorded(self):
        with self.proxy({"internal.test": ["10.0.0.5"]}) as p:
            out = self.get(p, "internal.test")
        self.assertTrue(out.startswith(b"HTTP/1.1 403"), out[:60])
        self.assertIn(b"egress guard", out)
        self.assertEqual(self.origin.requests, [])
        self.assertEqual(len(p.refusals), 1)
        self.assertIn("10.0.0.5", p.refusals[0])

    def test_dns_rebinding_cannot_flip_because_the_answer_is_pinned_and_never_re_resolved(self):
        answers = iter([["127.0.0.1"], ["10.0.0.5"], ["10.0.0.5"]])
        calls = []

        def flipping(host, port, type=0):
            calls.append(host)
            return [(2, 1, 6, "", (a, port)) for a in next(answers)]

        with ep.EgressProxy(resolver=flipping, allow=lambda ip: ip == "127.0.0.1") as p:
            out = self.get(p, "rebind.test")
        self.assertTrue(out.startswith(b"HTTP/1.1 200"), out[:60])
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(self.origin.requests), 1)

    def test_every_request_is_resolved_independently_so_a_hostile_later_answer_is_refused(self):
        answers = iter([["127.0.0.1"], ["10.0.0.5"]])

        def flipping(host, port, type=0):
            return [(2, 1, 6, "", (a, port)) for a in next(answers)]

        with ep.EgressProxy(resolver=flipping, allow=lambda ip: ip == "127.0.0.1") as p:
            first, second = self.get(p, "rebind.test"), self.get(p, "rebind.test")
        self.assertTrue(first.startswith(b"HTTP/1.1 200"))
        self.assertTrue(second.startswith(b"HTTP/1.1 403"))

    def test_ip_literals_and_odd_forms_go_through_the_same_check(self):
        with ep.EgressProxy(allow=ep.is_public) as p:
            for host in ("127.0.0.1", "169.254.169.254", "192.168.1.12", "[::1]", "100.66.29.76"):
                out = talk(p, f"GET http://{host}:{self.origin.port}/ HTTP/1.1\r\nHost: x\r\n\r\n".encode())
                self.assertTrue(out.startswith(b"HTTP/1.1 403"), (host, out[:60]))
        self.assertEqual(self.origin.requests, [])
        self.assertEqual(len(p.refusals), 5)
        self.assertEqual(p.errors, [])

    def test_userinfo_in_the_target_is_not_forwarded(self):
        with self.proxy({"public.test": ["127.0.0.1"]}) as p:
            talk(p, f"GET http://user:pw@public.test:{self.origin.port}/ HTTP/1.1\r\nHost: x\r\n\r\n".encode())
        seen = self.origin.requests[0].decode("latin-1")
        self.assertNotIn("user", seen.lower().replace("user-agent", ""))
        self.assertIn(f"Host: public.test:{self.origin.port}", seen)

    def test_malformed_and_unsupported_requests(self):
        with self.proxy({"public.test": ["127.0.0.1"]}) as p:
            cases = {
                b"POST http://public.test/ HTTP/1.1\r\n\r\n": b"405",
                b"HEAD http://public.test/ HTTP/1.1\r\n\r\n": b"405",
                b"GARBAGE\r\n\r\n": b"400",
                b"GET https://public.test/ HTTP/1.1\r\n\r\n": b"400",
                b"GET /relative HTTP/1.1\r\n\r\n": b"400",
                b"GET http://public.test/ HTTP/2.0\r\n\r\n": b"400",
                b"CONNECT public.test HTTP/1.1\r\n\r\n": b"400",
                b"CONNECT public.test:99999 HTTP/1.1\r\n\r\n": b"400",
                b"GET http://public.test:abc/ HTTP/1.1\r\n\r\n": b"400",
                b"GET http://public.test/ HTTP/1.1\r\n" + b"X: " + b"a" * 70000 + b"\r\n\r\n": b"400",
            }
            for payload, status in cases.items():
                out = talk(p, payload)
                self.assertIn(status, out[:20], (payload[:40], out[:40]))
        self.assertEqual(self.origin.requests, [])

    def test_connect_tunnel_relays_bytes_and_refuses_private_targets(self):
        echo = EchoOrigin()
        self.addCleanup(echo.close)
        with self.proxy({"public.test": ["127.0.0.1"], "internal.test": ["192.168.1.12"]}) as p:
            host, port = "127.0.0.1", int(p.url.rsplit(":", 1)[1])
            with socket.create_connection((host, port), timeout=5) as s:
                s.sendall(f"CONNECT public.test:{echo.port} HTTP/1.1\r\nHost: public.test\r\n\r\n".encode())
                reply = s.recv(4096)
                self.assertTrue(reply.startswith(b"HTTP/1.1 200"), reply)
                s.sendall(b"hello tunnel")
                self.assertEqual(s.recv(4096), b"HELLO TUNNEL")
            out = talk(p, f"CONNECT internal.test:{echo.port} HTTP/1.1\r\n\r\n".encode())
            self.assertTrue(out.startswith(b"HTTP/1.1 403"), out[:60])
        with ep.EgressProxy() as real:
            out = talk(real, b"CONNECT [::1]:443 HTTP/1.1\r\n\r\n")
            self.assertTrue(out.startswith(b"HTTP/1.1 403"), out[:60])
        self.assertEqual(len(p.refusals), 1)
        self.assertEqual(len(real.refusals), 1)

    def test_upstream_failure_is_a_502_not_a_hang(self):
        dead = socket.socket()
        dead.bind(("127.0.0.1", 0))
        port = dead.getsockname()[1]
        dead.close()
        with self.proxy({"public.test": ["127.0.0.1"], "gone.test": socket.gaierror(-2, "Name or service not known")}) as p:
            out = talk(p, f"GET http://public.test:{port}/ HTTP/1.1\r\nHost: x\r\n\r\n".encode())
            unresolved = talk(p, b"GET http://gone.test/ HTTP/1.1\r\nHost: x\r\n\r\n")
        self.assertTrue(out.startswith(b"HTTP/1.1 502"), out[:60])
        self.assertTrue(unresolved.startswith(b"HTTP/1.1 502"), unresolved[:60])
        self.assertEqual(p.refusals, [])

    def test_unexpected_resolver_errors_become_a_502_not_a_silent_close(self):
        def boom(host, port, type=0):
            raise RuntimeError("resolver exploded")

        with ep.EgressProxy(resolver=boom) as p:
            out = talk(p, b"GET http://x.test/ HTTP/1.1\r\nHost: x\r\n\r\n")
        self.assertTrue(out.startswith(b"HTTP/1.1 502"), out[:60])
        self.assertEqual(len(p.errors), 1)

    def test_concurrent_requests(self):
        results = []
        with self.proxy({"public.test": ["127.0.0.1"]}) as p:
            def go():
                results.append(self.get(p, "public.test").startswith(b"HTTP/1.1 200"))
            threads = [threading.Thread(target=go) for _ in range(12)]
            [t.start() for t in threads]
            [t.join(15) for t in threads]
        self.assertEqual(results, [True] * 12)

    def test_listens_on_loopback_only_and_closes_on_exit(self):
        with ep.EgressProxy() as p:
            self.assertTrue(p.url.startswith("http://127.0.0.1:"))
            port = int(p.url.rsplit(":", 1)[1])
            self.assertEqual(p._server.server_address[0], "127.0.0.1")
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.1", port), timeout=1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
