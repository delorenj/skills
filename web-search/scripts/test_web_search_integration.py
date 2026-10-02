#!/usr/bin/env python3
"""Integration tests: the REAL cli-web-search binary behind the real egress proxy.

Local loopback origin servers stand in for the web, and the wrapper's resolver and address-classification hooks are
patched so that 'public.test' means 127.0.0.1 (allowed) and 'private.test' means 10.9.9.9 (refused). Everything else is
the production code path: environment, proxy wiring, redirects handled inside the real binary. Skipped when the binary
has not been installed (scripts/install.sh).
"""
import contextlib
import importlib.machinery
import importlib.util
import io
import os
import socketserver
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_loader = importlib.machinery.SourceFileLoader("web_search", os.path.join(HERE, "web-search"))
ws = importlib.util.module_from_spec(importlib.util.spec_from_loader("web_search", _loader))
_loader.exec_module(ws)


class Origin:
    def __init__(self):
        self.hits = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                outer.hits.append(self.path)
                if self.path == "/start":
                    self.send_response(302)
                    self.send_header("Location", f"http://private.test:{outer.port}/secret")
                elif self.path == "/hop-public":
                    self.send_response(302)
                    self.send_header("Location", f"http://public.test:{outer.port}/ok")
                elif self.path == "/chain":
                    self.send_response(302)
                    self.send_header("Location", f"http://public.test:{outer.port}/start")
                else:
                    body = b"<h1>Hello</h1><p>real binary through the proxy</p>" if self.path != "/secret" else b"SECRET"
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_header("Content-Length", "0")
                self.end_headers()

        class S(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        self.server = S(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def resolver_for(mapping, calls=None):
    def resolve(host, port, type=0):
        if calls is not None:
            calls.append(host)
        answer = mapping[host]
        answer = answer(len(calls)) if callable(answer) else answer
        return [(2, 1, 6, "", (a, port)) for a in answer]
    return resolve


@unittest.skipUnless(os.path.isfile(ws.BIN) and ws.read_marker().get("bin"), "real binary not installed")
class RealBinaryBehindProxy(unittest.TestCase):
    def setUp(self):
        self.origin = Origin()
        self.addCleanup(self.origin.close)
        self.calls = []
        self._saved = (ws._RESOLVER, ws._ALLOW)
        self.addCleanup(lambda: (setattr(ws, "_RESOLVER", self._saved[0]), setattr(ws, "_ALLOW", self._saved[1])))
        ws._ALLOW = lambda ip: ip == "127.0.0.1"
        self.use({"public.test": ["127.0.0.1"], "private.test": ["10.9.9.9"]})

    def use(self, mapping):
        ws._RESOLVER = resolver_for(mapping, self.calls)

    def fetch(self, path, *extra, host="public.test"):
        args = ws.build_parser().parse_args(["fetch", f"http://{host}:{self.origin.port}{path}", *extra])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ws.cmd_fetch(args)
        return code, out.getvalue()

    def test_real_binary_fetches_through_the_proxy_and_the_page_is_converted(self):
        code, out = self.fetch("/ok")
        self.assertEqual(code, 0)
        self.assertIn("# Hello", out)
        self.assertIn("real binary through the proxy", out)
        self.assertEqual(self.origin.hits, ["/ok"])

    def test_a_redirect_hop_to_a_public_host_is_followed(self):
        code, out = self.fetch("/hop-public")
        self.assertEqual(code, 0)
        self.assertIn("real binary through the proxy", out)
        self.assertEqual(self.origin.hits, ["/hop-public", "/ok"])

    def test_a_redirect_hop_into_private_space_is_refused_and_never_requested(self):
        for path in ("/start", "/chain"):
            self.origin.hits.clear()
            with self.assertRaises(ws.Fail) as ctx:
                self.fetch(path)
            self.assertEqual(ctx.exception.code, 4, path)
            self.assertIn("10.9.9.9", str(ctx.exception))
            self.assertNotIn("/secret", self.origin.hits)

    def test_backslash_and_other_parser_differential_urls_never_reach_the_child(self):
        for url in (f"http://public.test\\@127.0.0.1:{self.origin.port}/ok", f"http://127.0.0.1\\x.public.test:{self.origin.port}/ok"):
            args = ws.build_parser().parse_args(["fetch", url])
            with self.assertRaises(ws.Fail) as ctx:
                ws.cmd_fetch(args)
            self.assertEqual(ctx.exception.code, 4)
        self.assertEqual(self.origin.hits, [])

    def test_dns_rebinding_is_stopped_by_the_proxy_even_when_the_pre_check_passed(self):
        self.calls.clear()
        self.use({"rebind.test": lambda n: ["127.0.0.1"] if n == 1 else ["10.9.9.9"]})
        with self.assertRaises(ws.Fail) as ctx:
            self.fetch("/ok", host="rebind.test")
        self.assertEqual(ctx.exception.code, 4)
        self.assertEqual(self.origin.hits, [])
        self.assertGreaterEqual(len(self.calls), 2)

    def test_the_proxy_pins_the_answer_it_validated(self):
        self.calls.clear()
        self.use({"pin.test": lambda n: ["127.0.0.1"] if n <= 2 else ["10.9.9.9"]})
        code, out = self.fetch("/ok", host="pin.test")
        self.assertEqual(code, 0)
        self.assertIn("real binary through the proxy", out)
        self.assertEqual(self.origin.hits, ["/ok"])

    def test_inherited_proxy_settings_cannot_route_around_the_guard(self):
        saved = {k: os.environ.get(k) for k in ("HTTP_PROXY", "http_proxy", "NO_PROXY", "no_proxy", "ALL_PROXY")}
        self.addCleanup(lambda: [os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v) for k, v in saved.items()])
        os.environ.update({"HTTP_PROXY": "http://127.0.0.1:9", "http_proxy": "http://127.0.0.1:9", "ALL_PROXY": "http://127.0.0.1:9",
                           "NO_PROXY": "*", "no_proxy": "*"})
        code, out = self.fetch("/ok")
        self.assertEqual(code, 0)
        self.assertIn("real binary through the proxy", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
