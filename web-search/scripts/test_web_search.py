#!/usr/bin/env python3
"""Tests for the web-search wrapper. Run: python3 scripts/test_web_search.py

A fake cli-web-search binary stands in for the real one (selected with WEB_SEARCH_TEST_BIN), so no network and no
real keys are used. The fake reports its own argv and environment back through a result snippet, which lets the
tests prove what the wrapper hands the child. test_web_search_integration.py covers the real binary behind the proxy.
"""
import base64
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unicodedata
import unittest
from unittest import mock

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
WS_PATH = os.path.join(HERE, "web-search")
sys.path.insert(0, HERE)
_loader = importlib.machinery.SourceFileLoader("web_search", WS_PATH)
ws = importlib.util.module_from_spec(importlib.util.spec_from_loader("web_search", _loader))
_loader.exec_module(ws)



def fake_key(prefix, seed, length=41):
    """Deterministic, non-repeating, runtime-generated stand-in for a key, so no key-shaped literal sits in source."""
    return (prefix + hashlib.sha256(seed.encode()).hexdigest() * 2)[:length]


SECRET_T = fake_key("tvly-", "tavily-test")
SECRET_B = fake_key("BSA", "brave-test", 31)

FAKE = textwrap.dedent('''\
    #!/usr/bin/env python3
    import base64, json, os, sys, time
    a = sys.argv[1:]
    if a[:1] == ["--version"]:
        print("cli-web-search 0.1.0"); sys.exit(0)
    key = (os.environ.get("CLI_WEB_SEARCH_TAVILY_API_KEY") or "") + (os.environ.get("CLI_WEB_SEARCH_BRAVE_API_KEY") or "")
    report = json.dumps({"argv": a, "env": sorted(os.environ), "rust_log": os.environ.get("RUST_LOG"),
                         "http_proxy": os.environ.get("HTTP_PROXY"), "no_proxy": os.environ.get("NO_PROXY"),
                         "home": os.environ.get("HOME"), "xdg": os.environ.get("XDG_CONFIG_HOME")})
    if a[:1] == ["fetch"]:
        url = a[1]
        if url.endswith("/abort"):
            sys.exit(134)
        if url.endswith("/leak"):
            print(key); print(key, file=sys.stderr); sys.exit(1)
        ctype, body, title = "text/html; charset=utf-8", "<h1>Hi</h1><p>hello <a href='/x'>link</a></p>", "T"
        if url.endswith("/env"):
            ctype, body = "application/json", report
        elif url.endswith("/binary"):
            ctype, body = "application/pdf", "%PDF-binary"
        elif url.endswith("/long"):
            ctype, body = "text/plain", "x" * 500
        elif url.endswith("/plain"):
            ctype, body = "text/plain", "From: John Doe <jdoe@example.org>\\n    indented\\n"
        elif url.endswith("/hostile"):
            ctype, body, title = "text/plain", "ok\\U000e0049\\U000e0047\\u202eevil\\u200b\\x1b[31m\\n\\n\\n\\n\\nend", "T" * 5000
        print(json.dumps({"url": url, "final_url": url, "status": 200, "content_type": ctype, "content": body,
                          "content_length": len(body), "title": title}))
        sys.exit(0)
    prov = a[a.index("-p") + 1] if "-p" in a else "?"
    q = a[-1]
    if "SLEEP" in q:
        open(q.split()[-1], "w").write(str(os.getpid())); time.sleep(60); sys.exit(0)
    if "LEAK" in q:
        print(key); print("Error: " + key, file=sys.stderr); sys.exit(1)
    if "ECHOB64" in q:
        print(base64.b64encode(key.encode()).decode()); sys.exit(0)
    if "ECHOREV" in q:
        print("oops " + key[::-1], file=sys.stderr); sys.exit(1)
    if "ECHOPREFIX" in q:
        print("Error: bad key " + key[:14], file=sys.stderr); sys.exit(1)
    if "HUGE" in q:
        sys.stdout.write("x" * (70 << 20)); sys.exit(0)
    if "ABORT" in q:
        sys.exit(134)
    if "FAILALL" in q or ("FAILTAVILY" in q and prov == "tavily") or ("FAILBRAVE" in q and prov == "brave"):
        print("Error: API error from " + prov + ": HTTP 429 Too Many Requests", file=sys.stderr); sys.exit(1)
    snippet = "snip " * 200 if "LONGSNIP" in q else report
    results = [] if ("EMPTYTAVILY" in q and prov == "tavily") else [
        {"title": "T\\u202eitle <strong>bold</strong> &quot;q&quot; " + prov, "url": "https://example.org/" + prov,
         "snippet": snippet, "position": 1, "source": "example.org", "published_date": "1 day ago"},
        {"title": "bad scheme", "url": "javascript:alert(1)", "snippet": "x", "position": 2}]
    if "HOSTILE" in q:
        results[0]["title"] = "ti\\U000e0041tle\\u2060" + "T" * 900
        results[0]["snippet"] = "snip\\u2028line\\U000e0049\\U000e0047 " + "z" * 6000
        results[0]["url"] = "https://example.org/" + "u" * 900
    print(json.dumps({"query": q, "provider": prov, "timestamp": "t", "total_results": len(results),
                      "search_time_ms": 1, "results": results}))
''')


def child_report(data):
    return json.loads(data["results"][0]["snippet"])


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="ws-test-")
        cls.fake = os.path.join(cls.tmp.name, "cli-web-search")
        with open(cls.fake, "w") as fh:
            fh.write(FAKE)
        os.chmod(cls.fake, 0o755)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def env(self, ambient=True, extra=None):
        env = {"PATH": "/usr/bin:/bin", "HOME": self.tmp.name, "WEB_SEARCH_TEST_BIN": self.fake,
               "AWS_SECRET_ACCESS_KEY": "must-not-reach-child", "CARGO_REGISTRY_TOKEN": "must-not-reach-child",
               "HTTPS_PROXY": "http://user:pw@corp-proxy.invalid:3128", "NO_PROXY": "127.0.0.1,localhost"}
        if ambient:
            env.update({"TAVILY_API_KEY": SECRET_T, "BRAVE_API_KEY": SECRET_B})
        env.update(extra or {})
        return env

    def run_ws(self, *args, ambient=True, extra_env=None, timeout=60):
        return subprocess.run([sys.executable, WS_PATH, *args], env=self.env(ambient, extra_env), capture_output=True,
                              text=True, timeout=timeout)

    def search_json(self, *args, **kw):
        r = self.run_ws("search", *args, "--json", **kw)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)


class ChildHygiene(Base):
    def test_search_child_env_is_scrubbed_and_gets_only_one_key(self):
        report = child_report(self.search_json("hello world", "-p", "tavily", "--snippet-chars", "0"))
        allowed = {"PATH", "HOME", "LANG", "RUST_LOG", "NO_COLOR", "XDG_CONFIG_HOME", "XDG_CACHE_HOME",
                   "CLI_WEB_SEARCH_TAVILY_API_KEY", "LC_CTYPE", "HTTPS_PROXY", "NO_PROXY"}
        self.assertLessEqual(set(report["env"]), allowed)
        self.assertIn("CLI_WEB_SEARCH_TAVILY_API_KEY", report["env"])
        self.assertNotIn("CLI_WEB_SEARCH_BRAVE_API_KEY", report["env"])
        self.assertEqual(report["rust_log"], "off")
        self.assertTrue(report["home"].startswith(tempfile.gettempdir()) or "web-search-" in report["home"])
        self.assertEqual(report["home"], report["xdg"])

    def test_fetch_child_is_forced_through_the_egress_proxy_and_cannot_bypass_it(self):
        r = self.run_ws("fetch", "http://8.8.8.8/env", "--max-chars", "0")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        start = next(i for i, l in enumerate(lines) if l.startswith("<<<BEGIN")) + 1
        end = next(i for i, l in enumerate(lines) if l.startswith("<<<END"))
        report = json.loads("\n".join(lines[start:end]))
        self.assertTrue(report["http_proxy"].startswith("http://127.0.0.1:"))
        self.assertEqual(report["no_proxy"], "")
        self.assertEqual(report["argv"][report["argv"].index("-f") + 1], "html")
        self.assertNotIn("corp-proxy", json.dumps(report))

    def test_keys_never_appear_in_argv_or_output(self):
        r = self.run_ws("search", "hello", "-p", "both", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        for secret in (SECRET_T, SECRET_B):
            self.assertNotIn(secret, r.stdout + r.stderr)

    def test_leaked_exact_key_is_redacted(self):
        for args in (("search", "LEAK", "-p", "tavily"), ("fetch", "http://8.8.8.8/leak")):
            r = self.run_ws(*args)
            self.assertNotEqual(r.returncode, 0)
            for secret in (SECRET_T, SECRET_B):
                self.assertNotIn(secret, r.stdout + r.stderr, args)

    def test_transformed_key_echoes_suppress_the_child_output(self):
        for marker in ("ECHOB64", "ECHOREV", "ECHOPREFIX"):
            r = self.run_ws("search", marker, "-p", "tavily")
            self.assertNotEqual(r.returncode, 0, marker)
            blob = r.stdout + r.stderr
            self.assertNotIn(SECRET_T, blob)
            self.assertNotIn(SECRET_T[::-1], blob)
            self.assertNotIn(SECRET_T[:14], blob)
            self.assertNotIn(base64.b64encode(SECRET_T.encode()).decode()[:20], blob, marker)

    def test_doctor_reports_lengths_not_values(self):
        r = self.run_ws("doctor")
        for secret in (SECRET_T, SECRET_B):
            self.assertNotIn(secret, r.stdout + r.stderr)
        self.assertIn(f"({len(SECRET_T)} chars)", r.stdout)

    def test_oversized_child_output_is_stopped_at_the_cap(self):
        r = self.run_ws("search", "HUGE", "-p", "brave", timeout=120)
        self.assertEqual(r.returncode, 5, r.stderr)
        self.assertIn("MiB", r.stderr)

    def test_sigterm_kills_the_child_and_never_orphans_it(self):
        pidfile = os.path.join(self.tmp.name, "child.pid")
        proc = subprocess.Popen([sys.executable, WS_PATH, "search", f"SLEEP {pidfile}", "-p", "brave"], env=self.env(),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for _ in range(100):
            if os.path.exists(pidfile) and open(pidfile).read():
                break
            time.sleep(0.05)
        child = int(open(pidfile).read())
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)
        for _ in range(100):
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            os.kill(child, signal.SIGKILL)
            self.fail("child survived the wrapper")

    def test_a_hard_data_limit_below_the_cap_does_not_break_the_wrapper(self):
        r = subprocess.run(["bash", "-c", f"ulimit -Hd 1500000; exec {sys.executable} {WS_PATH} search hello -p tavily"],
                           env=self.env(), capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_broken_pipe_is_quiet(self):
        r = subprocess.run(f"{sys.executable} {WS_PATH} search LONGSNIP -p tavily -n 20 --snippet-chars 0 | head -c1",
                           shell=True, env=self.env(), capture_output=True, text=True, timeout=60)
        self.assertNotIn("Exception ignored", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


class KeyResolution(Base):
    def test_op_is_not_called_without_a_service_account_token(self):
        env = {k: v for k, v in os.environ.items() if k not in ("OP_SERVICE_ACCOUNT_TOKEN", "OP_CONNECT_TOKEN")}
        env["TAVILY_API_KEY"] = SECRET_T
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(ws.subprocess, "run", side_effect=AssertionError("op must not be called")):
            self.assertEqual(ws.resolve_key("tavily"), (SECRET_T, "env:TAVILY_API_KEY"))

    def test_op_value_wins_and_failure_falls_back_to_env_with_a_restricted_op_environment(self):
        ok = mock.Mock(returncode=0, stdout=SECRET_B + "\n", stderr="")
        bad = mock.Mock(returncode=1, stdout="", stderr="[ERROR] item not found\nmore")
        env = {"OP_SERVICE_ACCOUNT_TOKEN": "x", "BRAVE_API_KEY": "from-env", "ANTHROPIC_AUTH_TOKEN": "decoy",
               "PATH": "/usr/bin", "HOME": "/h"}
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(ws.subprocess, "run", return_value=ok) as run:
                self.assertEqual(ws.resolve_key("brave"), (SECRET_B, "1password"))
                passed = run.call_args.kwargs["env"]
                self.assertNotIn("ANTHROPIC_AUTH_TOKEN", passed)
                self.assertNotIn("BRAVE_API_KEY", passed)
                self.assertIn("OP_SERVICE_ACCOUNT_TOKEN", passed)
            with mock.patch.object(ws.subprocess, "run", return_value=bad):
                self.assertEqual(ws.resolve_key("brave"), ("from-env", "env:BRAVE_API_KEY"))

    def test_no_key_anywhere_exits_3_and_says_what_to_do(self):
        r = self.run_ws("search", "hello", ambient=False)
        self.assertEqual(r.returncode, 3)
        self.assertIn("no tavily API key", r.stderr)
        self.assertIn("web-search doctor", r.stderr)


class SearchFlow(Base):
    def test_default_subcommand_is_search_and_compact_output(self):
        r = self.run_ws("rust", "2026", "edition")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith('web-search: "rust 2026 edition" via tavily (1 result,'), r.stdout[:80])
        self.assertEqual(r.stdout.splitlines()[1], ws.BANNER)
        self.assertNotIn("<strong>", r.stdout)
        self.assertNotIn("&quot;", r.stdout)
        self.assertIn('"q"', r.stdout)
        self.assertNotIn("javascript:", r.stdout)

    def test_json_contract_is_sanitised_flagged_untrusted_and_honours_snippet_chars(self):
        data = self.search_json("HOSTILE", "-p", "tavily", "--snippet-chars", "100")
        self.assertIs(data["untrusted"], True)
        self.assertEqual(data["notice"], ws.BANNER)
        item = data["results"][0]
        self.assertLessEqual(len(item["snippet"]), 101)
        self.assertLessEqual(len(item["title"]), 301)
        self.assertLessEqual(len(item["url"]), 501)
        blob = json.dumps(data, ensure_ascii=False)
        for bad in ("\U000e0041", "\U000e0049", "⁠", " ", "‮"):
            self.assertNotIn(bad, blob)
        self.assertEqual(len(data["results"]), 1)

    def test_failover_to_second_provider_and_attempts_recorded_without_duplicate_labels(self):
        data = self.search_json("FAILTAVILY")
        self.assertEqual(data["provider"], "brave")
        self.assertEqual(data["attempts"][0]["provider"], "tavily")
        self.assertEqual(data["attempts"][0]["error"], "tavily: HTTP 429 Too Many Requests")
        r = self.run_ws("search", "FAILTAVILY")
        self.assertIn("note: tavily: HTTP 429 Too Many Requests", r.stderr)
        self.assertNotIn("tavily: tavily", r.stderr)

    def test_empty_results_fall_through_to_next_provider(self):
        data = self.search_json("EMPTYTAVILY")
        self.assertEqual(data["provider"], "brave")
        self.assertTrue(any(a.get("note") == "returned no results" for a in data["attempts"]))

    def test_date_range_and_safe_search_prefer_brave(self):
        for flag, value in (("--date-range", "week"), ("--safe-search", "strict")):
            data = self.search_json("news", flag, value, "--snippet-chars", "0")
            self.assertEqual(data["provider"], "brave", flag)
            self.assertIn(value, child_report(data)["argv"])

    def test_a_dropped_filter_is_stated_on_stdout_when_tavily_answers(self):
        r = self.run_ws("search", "FAILBRAVE news", "--date-range", "week")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("via tavily", r.stdout)
        self.assertIn("date filter NOT applied", r.stdout)
        data = self.search_json("FAILBRAVE news", "--safe-search", "strict")
        self.assertIn("safe-search NOT applied: Tavily ignores --safe-search", data["caveats"])

    def test_both_runs_both_providers(self):
        data = self.search_json("x", "-p", "both")
        self.assertEqual(set(data["results_by_provider"]), {"tavily", "brave"})

    def test_single_provider_has_no_fallback_and_reports_a_single_failure(self):
        r = self.run_ws("search", "FAILTAVILY", "-p", "tavily")
        self.assertEqual(r.returncode, 1)
        self.assertIn("search failed: tavily: HTTP 429", r.stderr)
        self.assertNotIn("all providers failed", r.stderr)

    def test_all_providers_failing_exits_1_with_both_reasons(self):
        r = self.run_ws("search", "FAILALL")
        self.assertEqual(r.returncode, 1)
        self.assertIn("all providers failed", r.stderr)
        self.assertIn("tavily", r.stderr)
        self.assertIn("brave", r.stderr)

    def test_cli_abort_maps_to_exit_5(self):
        self.assertEqual(self.run_ws("search", "ABORT", "-p", "brave").returncode, 5)

    def test_site_filter_is_validated_and_applied(self):
        self.assertEqual(self.run_ws("search", "x", "--site", "a.com OR evil").returncode, 2)
        data = self.search_json("x", "--site", "a.com", "--site", "b.org")
        self.assertEqual(data["query"], "x (site:a.com OR site:b.org)")

    def test_argument_validation(self):
        for args in (("-n", "0"), ("-n", "21"), ("-n", "-3"), ("-n", "abc"), ("--timeout", "0"), ("--timeout", "-5"),
                     ("--timeout", "99999999999999"), ("--snippet-chars", "-5")):
            r = self.run_ws("search", "x", *args)
            self.assertEqual(r.returncode, 2, args)
            self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(self.run_ws("fetch", "http://8.8.8.8/", "--max-chars", "-5").returncode, 2)
        self.assertEqual(self.run_ws("search", "x", "-n", "20").returncode, 0)

    def test_empty_whitespace_and_oversized_queries_are_usage_errors(self):
        for query in ("", "   "):
            self.assertEqual(self.run_ws("search", query).returncode, 2)
        self.assertEqual(self.run_ws("search", "", "--site", "docs.rs").returncode, 2)
        long = self.run_ws("search", "w " * 300)
        self.assertEqual(long.returncode, 2)
        self.assertIn("distinctive part", long.stderr)

    def test_odd_queries_arrive_as_one_argv_element(self):
        for query in ('say "hi" `id` $(id) | ls; echo', "emoji 🙂 rtl", "line1\nline2"):
            report = child_report(self.search_json(query, "-p", "tavily", "--snippet-chars", "0"))
            self.assertEqual(report["argv"][-2:], ["--", query])

    def test_leading_dash_query_needs_double_dash(self):
        self.assertEqual(self.run_ws("search", "--", "-rust").returncode, 0)
        self.assertEqual(self.run_ws("-rust").returncode, 2)


class FetchFlow(Base):
    def test_html_is_converted_fenced_and_marked_untrusted(self):
        r = self.run_ws("fetch", "http://8.8.8.8/ok")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], ws.BANNER)
        self.assertTrue(lines[1].startswith("# fetched: http://8.8.8.8/ok (status 200, text/html"))
        begin = next(l for l in lines if l.startswith("<<<BEGIN UNTRUSTED CONTENT "))
        end = next(l for l in lines if l.startswith("<<<END UNTRUSTED CONTENT "))
        self.assertEqual(begin.split()[-1], end.split()[-1])
        self.assertIn("# Hi", r.stdout)
        self.assertIn("[link](http://8.8.8.8/x)", r.stdout)

    def test_fence_ids_are_random_per_call(self):
        ids = {next(l for l in self.run_ws("fetch", "http://8.8.8.8/ok").stdout.splitlines()
                    if l.startswith("<<<BEGIN")).split()[-1] for _ in range(3)}
        self.assertEqual(len(ids), 3)

    def test_plain_text_bodies_are_not_run_through_the_html_stripper(self):
        r = self.run_ws("fetch", "http://8.8.8.8/plain")
        self.assertIn("From: John Doe <jdoe@example.org>", r.stdout)
        self.assertIn("    indented", r.stdout)

    def test_hostile_body_and_title_are_sanitised_and_bounded(self):
        data = json.loads(self.run_ws("fetch", "http://8.8.8.8/hostile", "--json").stdout)
        self.assertIs(data["untrusted"], True)
        self.assertLessEqual(len(data["title"]), 301)
        blob = json.dumps(data, ensure_ascii=False)
        for bad in ("\U000e0049", "‮", "​", "\x1b"):
            self.assertNotIn(bad, blob)
        self.assertNotIn("\n\n\n", data["content"])
        text = self.run_ws("fetch", "http://8.8.8.8/hostile").stdout
        self.assertLess(len(text), 3000)
        self.assertEqual(text.splitlines()[0], ws.BANNER)

    def test_non_text_bodies_are_not_shown(self):
        r = self.run_ws("fetch", "http://8.8.8.8/binary")
        self.assertIn("body not shown", r.stdout)
        self.assertNotIn("%PDF", r.stdout)

    def test_truncation_and_abort(self):
        data = json.loads(self.run_ws("fetch", "http://8.8.8.8/long", "--max-chars", "50", "--json").stdout)
        self.assertTrue(data["truncated"])
        self.assertLessEqual(len(data["content"]), 50 + len("\n…[truncated]"))
        self.assertEqual(self.run_ws("fetch", "http://8.8.8.8/abort").returncode, 5)

    def test_raw_html_format_skips_conversion(self):
        r = self.run_ws("fetch", "http://8.8.8.8/ok", "--format", "html")
        self.assertIn("<h1>Hi</h1>", r.stdout)


class UrlNormalisation(unittest.TestCase):
    def test_hostile_urls_are_refused_before_anything_runs(self):
        for url in ("http://192.168.1.12\\x.8.8.8.8.nip.io/admin", "http://example.com\\@127.0.0.1/", "http://a b/",
                    "http://a\tb/", "http://a\nb/", "http://example.com/\x00", "file:///etc/passwd", "ftp://example.com/",
                    "gopher://example.com/", "javascript:alert(1)", "http://user:pw@example.com/", "http://@/", "",
                    "http://example.com:abc/", "http://[::1/", "http://example.com:99999/", "mailto:a@b.c"):
            with self.assertRaises(ws.Fail, msg=url) as ctx:
                ws.normalize_url(url)
            self.assertEqual(ctx.exception.code, 4, url)

    def test_urls_are_reserialised_as_plain_ascii(self):
        self.assertEqual(ws.normalize_url("HTTP://Example.COM./a b".replace(" ", "%20")), "http://example.com/a%20b")
        self.assertEqual(ws.normalize_url("https://münchen.de/straße?q=ü#frag"), "https://xn--mnchen-3ya.de/stra%C3%9Fe?q=%C3%BC")
        self.assertEqual(ws.normalize_url("http://example.com"), "http://example.com/")
        self.assertEqual(ws.normalize_url("http://[2606:4700::1111]:8080/x"), "http://[2606:4700::1111]:8080/x")
        self.assertEqual(ws.normalize_url("http://example.com/a%2Fb?x=1&y=%7E"), "http://example.com/a%2Fb?x=1&y=%7E")


class SsrfPreCheck(unittest.TestCase):
    def check(self, url, addrs=None):
        infos = [(0, 0, 0, "", (a, 0)) for a in (addrs or [])]
        with mock.patch.object(ws, "_RESOLVER", return_value=infos):
            return ws.check_public(url)

    def test_public_addresses_pass(self):
        self.check("https://example.com/x", ["93.184.216.34"])
        self.check("http://[2606:4700::1111]/", ["2606:4700::1111"])
        self.check("http://8.8.8.8/", ["8.8.8.8"])

    def test_non_public_addresses_are_refused(self):
        for addr in ("127.0.0.1", "10.1.2.3", "172.16.0.9", "192.168.0.1", "169.254.169.254", "100.64.0.1", "0.0.0.0",
                     "::1", "fe80::1", "fc00::1", "::ffff:127.0.0.1", "224.0.0.1", "64:ff9b::7f00:1", "::127.0.0.1",
                     "2002:7f00:1::", "fec0::1"):
            with self.assertRaises(ws.Fail, msg=addr) as ctx:
                self.check("https://some.example.com/", [addr])
            self.assertEqual(ctx.exception.code, 4, addr)

    def test_one_private_answer_among_public_ones_is_refused(self):
        with self.assertRaises(ws.Fail):
            self.check("https://rebind.example.com/", ["93.184.216.34", "10.0.0.5"])

    def test_names_and_numeric_forms_are_refused_without_resolving(self):
        with mock.patch.object(ws, "_RESOLVER", side_effect=AssertionError("must not resolve")):
            for url in ("http://localhost/", "http://printer.local/", "http://x.internal/", "http://nas.lan/",
                        "http://box.burro-salmon.ts.net/", "http://intranet/", "http://127.1/", "http://2130706433/",
                        "http://0x7f.1/", "http://127.0X.0.1/", "http://0177.0.0.1/", "http://1.2.3.0x/"):
                with self.assertRaises(ws.Fail, msg=url) as ctx:
                    ws.check_public(url)
                self.assertEqual(ctx.exception.code, 4, url)

    def test_unresolvable_host_is_a_plain_failure_not_a_refusal(self):
        with mock.patch.object(ws, "_RESOLVER", side_effect=ws.socket.gaierror(-2, "Name or service not known")):
            with self.assertRaises(ws.Fail) as ctx:
                ws.check_public("https://nope.example.com/")
        self.assertEqual(ctx.exception.code, 1)

    def test_invalid_label_lengths_do_not_traceback(self):
        r = subprocess.run([sys.executable, WS_PATH, "fetch", "http://a..b.com/"], capture_output=True, text=True,
                           env={"PATH": "/usr/bin:/bin", "WEB_SEARCH_TEST_BIN": "/bin/true"})
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn(r.returncode, (1, 4))


class Sanitiser(unittest.TestCase):
    def test_no_invisible_or_control_character_survives(self):
        keep = {"\n", "\t"}
        offenders = []
        for cp in range(0x110000):
            ch = chr(cp)
            if ch in keep or unicodedata.category(ch) not in ("Cc", "Cf", "Cs", "Co", "Zl", "Zp"):
                continue
            if ws.clean_block(f"a{ch}b") not in ("ab", "a\nb"):
                offenders.append(hex(cp))
        self.assertEqual(offenders, [])

    def test_known_smuggling_characters_are_removed(self):
        for ch in ("\U000e0041", "\U000e0001", "️", "⁠", "­", "؜", "᠎", "͏", "ㅤ",
                   "\U000e0100", "‮", "​", "﻿", "\x00", "\x1b", " ", "\u0085"):
            self.assertNotIn(ch, ws.clean(f"a{ch}b"), repr(ch))
            self.assertNotIn(ch, ws.clean_block(f"a{ch}b"), repr(ch))

    def test_clean_collapses_whitespace_and_caps_length(self):
        self.assertEqual(ws.clean("  a \n\t b  "), "a b")
        self.assertEqual(ws.clean("x" * 10, 4), "xxxx…")
        self.assertEqual(ws.clean_block("a\r\n\r\n\r\n\r\nb  \nc"), "a\n\nb\nc")

    def test_provider_markup_and_entities_are_unwrapped(self):
        self.assertEqual(ws.clean(ws.strip_markup("Chipset <strong>xHCI</strong> &quot;x&quot; &#x27;y&#x27; a &lt; b")),
                         "Chipset xHCI \"x\" 'y' a < b")


class Integrity(unittest.TestCase):
    def test_binary_must_match_the_recorded_digest(self):
        with tempfile.TemporaryDirectory() as d:
            binary, marker = os.path.join(d, "cli-web-search"), os.path.join(d, "installed")
            with open(binary, "w") as fh:
                fh.write("#!/bin/sh\necho hi\n")
            os.chmod(binary, 0o755)
            with mock.patch.object(ws, "TEST_BIN", None), mock.patch.object(ws, "BIN", binary), \
                    mock.patch.object(ws, "MARKER", marker):
                with self.assertRaises(ws.Fail) as ctx:
                    ws.verify_binary()
                self.assertEqual(ctx.exception.code, 3)
                with open(marker, "w") as fh:
                    fh.write(f"sha=x patch=y bin={ws.sha256_of(binary)}\n")
                self.assertEqual(ws.verify_binary(), binary)
                with open(binary, "a") as fh:
                    fh.write("# tampered\n")
                with self.assertRaises(ws.Fail) as ctx:
                    ws.verify_binary()
                self.assertIn("refusing to hand it API keys", str(ctx.exception))
                os.unlink(binary)
                with self.assertRaises(ws.Fail) as ctx:
                    ws.verify_binary()
                self.assertIn("not found", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
