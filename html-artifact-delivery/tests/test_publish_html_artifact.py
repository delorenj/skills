"""Run: python3 -m unittest discover -s tests -v   (from the skill directory)."""
import contextlib
import errno
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import publish_html_artifact as pha  # noqa: E402

SAMPLE = HERE.parent / "assets" / "sample-bundle"
SESSION = "11111111-2222-4333-8444-555555555555"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run(argv, env=None, runner=None, fetch=None):
    out = io.StringIO()
    def no_runner(*a, **k):
        raise AssertionError("subprocess must not run")
    def no_fetch(*a, **k):
        raise AssertionError("network must not be used")
    code = pha.main(argv, env=env or {}, runner=runner or no_runner, fetch=fetch or no_fetch, out=out)
    return code, json.loads(out.getvalue())


def base_args(bundle, *extra):
    return ["--bundle", str(bundle), "--project", "demo", "--artifact", "report",
            "--bb-session-id", SESSION, *extra]


class Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class FakeRemote:
    """Records mc calls; stores uploaded bytes so fetch can serve them."""
    def __init__(self, existing=(), ls_error=None, cp_fail_on=None):
        self.calls, self.store, self.existing = [], {}, list(existing)
        self.ls_error, self.cp_fail_on = ls_error, cp_fail_on

    def runner(self, cmd, **kw):
        self.calls.append(cmd)
        assert kw.get("timeout"), "timeout must be bounded"
        if cmd[1] == "ls":
            if self.ls_error:
                return Proc(1, json.dumps({"status": "error", "error": {"message": "Unable to list folder.",
                            "cause": {"error": {"Code": self.ls_error, "Message": "Access Denied. secret_key=abc"}}}}),
                            "mc: <ERROR> AKIA" "ABCDEFGHIJKLMNOP leaked")
            return Proc(0, "\n".join(json.dumps({"status": "success", "key": k}) for k in self.existing))
        if cmd[1] == "cp":
            local, target = cmd[-2], cmd[-1]
            if self.cp_fail_on and target.endswith(self.cp_fail_on):
                return Proc(1, json.dumps({"status": "error", "error": {"message": "upload failed"}}), "raw stderr")
            attr = cmd[cmd.index("--attr") + 1]
            ctype = attr.split(";")[0].split("=", 1)[1]
            key = target.split("/", 2)[2]
            self.store[key] = (ctype, Path(local).read_bytes())
            return Proc(0, json.dumps({"status": "success"}))
        raise AssertionError(cmd)

    def fetch(self, url, timeout):
        key = url.split("/projects/", 1)[1]
        key = __import__("urllib.parse").parse.unquote(key)
        if key not in self.store:
            return 404, "application/xml", b""
        ctype, body = self.store[key]
        return 200, ctype + "; charset=utf-8" if ctype.startswith("text/") else ctype, body


class SessionTests(unittest.TestCase):
    def test_uuid_passthrough(self):
        self.assertEqual(pha.map_bb_session("codex", SESSION.upper()), SESSION)

    def test_hermes_native_maps_to_live_bloodbank_id(self):
        self.assertEqual(pha.map_bb_session("hermes", "20261017_134801_419ca7"),
                         "db31c489-fbe6-5aa0-933e-b775364c3136")

    def test_uuid5_formula(self):
        self.assertEqual(pha.map_bb_session("claude", "abc"),
                         str(uuid.uuid5(uuid.NAMESPACE_URL, "bloodbank:claude:abc")))

    def test_env_derivation_and_provenance(self):
        s = pha.resolve_session(None, None, None, {"HERMES_SESSION_ID": "20261017_134801_419ca7"})
        self.assertEqual(s["bb_session_id"], "db31c489-fbe6-5aa0-933e-b775364c3136")
        self.assertEqual((s["harness"], s["source"]), ("hermes", "env:HERMES_SESSION_ID"))

    def test_codex_consistent_env_vars(self):
        s = pha.resolve_session(None, None, None, {"CODEX_THREAD_ID": SESSION, "CODEX_SESSION_ID": SESSION})
        self.assertEqual(s["bb_session_id"], SESSION)

    def test_missing(self):
        with self.assertRaises(pha.Failure) as c:
            pha.resolve_session(None, None, None, {})
        self.assertEqual(c.exception.kind, "session_missing")
        with self.assertRaises(pha.Failure) as c:
            pha.resolve_session(None, "claude", None, {})
        self.assertEqual(c.exception.kind, "session_missing")

    def test_ambiguous(self):
        cases = [
            (None, None, None, {"CODEX_THREAD_ID": "a", "HERMES_SESSION_ID": "b"}),
            (None, None, None, {"CODEX_THREAD_ID": "a", "CODEX_SESSION_ID": "b"}),
            (SESSION, "codex", "x", {}),
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(pha.Failure) as c:
                pha.resolve_session(*case)
            self.assertEqual(c.exception.kind, "session_ambiguous")

    def test_invalid(self):
        for case in [("not-a-uuid", None, None), (None, None, "x"), (None, "Bad Name", "x")]:
            with self.subTest(case=case), self.assertRaises(pha.Failure):
                pha.resolve_session(*case, {})

    def test_explicit_harness_wins_over_other_env(self):
        s = pha.resolve_session(None, "claude", "abc", {"CODEX_THREAD_ID": SESSION})
        self.assertEqual(s["harness"], "claude")


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def git(self, *args, cwd):
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                       env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
                            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t"})

    def test_slug_preferred_over_id(self):
        write(self.tmp / ".project.json", json.dumps({"project_slug": "alpha", "project_id": "zz"}))
        self.assertEqual(pha.resolve_project(None, str(self.tmp))["slug"], "alpha")

    def test_project_id_fallback(self):
        write(self.tmp / ".project.json", json.dumps({"project_id": "beta", "ticket_provider": {"identifier": "BETA"}}))
        self.assertEqual(pha.resolve_project(None, str(self.tmp))["slug"], "beta")

    def test_linked_worktree_uses_main_worktree_metadata(self):
        main = self.tmp / "main-repo"
        main.mkdir()
        self.git("init", "-q", "-b", "main", cwd=main)
        write(main / ".project.json", json.dumps({"project_slug": "gamma"}))
        self.git("add", ".", cwd=main)
        self.git("commit", "-qm", "init", cwd=main)
        wt = self.tmp / "feature-branch-name"
        self.git("worktree", "add", "-q", "-b", "feature-x", str(wt), cwd=main)
        (wt / ".project.json").unlink()  # metadata only in main worktree
        sub = wt / "docs"
        sub.mkdir()
        got = pha.resolve_project(None, str(sub))
        self.assertEqual(got["slug"], "gamma")
        self.assertEqual(Path(got["main_worktree"]), main.resolve())

    def test_conflicting_worktree_metadata_is_ambiguous(self):
        main = self.tmp / "m"
        main.mkdir()
        self.git("init", "-q", "-b", "main", cwd=main)
        write(main / ".project.json", json.dumps({"project_slug": "one"}))
        self.git("add", ".", cwd=main)
        self.git("commit", "-qm", "init", cwd=main)
        wt = self.tmp / "w"
        self.git("worktree", "add", "-q", "-b", "b", str(wt), cwd=main)
        write(wt / ".project.json", json.dumps({"project_slug": "two"}))
        with self.assertRaises(pha.Failure) as c:
            pha.resolve_project(None, str(wt))
        self.assertEqual(c.exception.kind, "project_ambiguous")

    def test_missing_and_disagreeing(self):
        with self.assertRaises(pha.Failure) as c:
            pha.resolve_project(None, str(self.tmp))
        self.assertEqual(c.exception.kind, "project_missing")
        write(self.tmp / ".project.json", json.dumps({"project_slug": "alpha"}))
        with self.assertRaises(pha.Failure) as c:
            pha.resolve_project("other", str(self.tmp))
        self.assertEqual(c.exception.kind, "project_ambiguous")

    def test_explicit_project(self):
        self.assertEqual(pha.resolve_project("delta", None)["slug"], "delta")
        with self.assertRaises(pha.Failure):
            pha.resolve_project("../x", None)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.b = Path(tempfile.mkdtemp())
        write(self.b / "index.html", '<link rel="stylesheet" href="a/s.css"><script src="a/app.js"></script>')
        write(self.b / "a/s.css", "body{background:url('../img/x.svg')}")
        write(self.b / "a/app.js", "import './m.mjs';")
        write(self.b / "a/m.mjs", "export const x = 1;")
        write(self.b / "img/x.svg", "<svg xmlns='http://www.w3.org/2000/svg'/>")

    def errors(self):
        code, doc = run(base_args(self.b))
        return code, doc

    def test_nested_assets_and_mime(self):
        code, doc = self.errors()
        self.assertEqual(code, 0, doc)
        types = {f["path"]: f["content_type"] for f in doc["files"]}
        self.assertEqual(types, {"index.html": "text/html", "a/s.css": "text/css", "a/app.js": "text/javascript",
                                 "a/m.mjs": "text/javascript", "img/x.svg": "image/svg+xml"})
        self.assertEqual(doc["entry_url"], f"https://s3.delo.sh/projects/demo/{SESSION}/report/index.html")

    def test_missing_asset(self):
        (self.b / "img/x.svg").unlink()
        code, doc = self.errors()
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertTrue(any("missing local asset" in e for e in doc["errors"]))

    def test_traversal_root_relative_file_localhost(self):
        write(self.b / "index.html", "\n".join([
            '<img src="../../etc/passwd">', '<img src="/abs.png">', '<img src="file:///tmp/x.png">',
            '<script src="http://localhost:3000/app.js"></script>', '<img src="https://192.168.1.5/x.png">',
            '<a href="sub/">dir</a>']))
        (self.b / "sub").mkdir()
        write(self.b / "sub/index.html", "<p>x</p>")
        code, doc = self.errors()
        self.assertEqual(code, pha.EXIT_INVALID)
        text = "\n".join(doc["errors"])
        for needle in ("escapes the bundle", "root-relative", "file: URL", "private/localhost", "directory"):
            self.assertIn(needle, text)
        self.assertEqual(text.count("private/localhost"), 2)

    def test_symlinks_rejected(self):
        os.symlink(self.b / "a/s.css", self.b / "link.css")
        os.symlink(self.b / "a", self.b / "linkdir")
        code, doc = self.errors()
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertTrue(any("symlink rejected" in e for e in doc["errors"]))
        self.assertTrue(any("symlinked directory" in e for e in doc["errors"]))

    def test_secret_files_rejected_without_reading_values(self):
        for name in (".env", ".env.local", "credentials.json", "server.pem", ".git/config"):
            write(self.b / name, "x")
        write(self.b / "a/key.txt", "-----BEGIN " "OPENSSH PRIVATE KEY-----\nzzz\n")
        code, doc = self.errors()
        self.assertEqual(code, pha.EXIT_INVALID)
        text = "\n".join(doc["errors"])
        for needle in (".env", ".env.local", "credentials.json", "server.pem", ".git", "private key material"):
            self.assertIn(needle, text)
        self.assertNotIn("zzz", json.dumps(doc))
        self.assertNotIn(".git/config", [f["path"] for f in doc["files"]])

    def test_external_cdn_listed_in_dry_run(self):
        write(self.b / "index.html", '<script src="https://cdn.example.com/lib.js"></script><a href="https://x.org">x</a>')
        code, doc = self.errors()
        self.assertEqual(code, 0)
        self.assertEqual([r["url"] for r in doc["external_resources"]], ["https://cdn.example.com/lib.js"])
        self.assertFalse(doc["publishable"])
        self.assertIn("localize", doc["next"])

    def test_unresolved_required_resources_block_publish(self):
        cases = {
            "external": '<link rel="stylesheet" href="https://cdn.example.com/x.css">',
            "bare-module": '<script type="module">import "lodash";</script>',
            "templated": '<img src="{{ asset }}/x.png">',
            "templated-js": '<script type="module">import "./${name}.mjs";</script>',
        }
        for name, html in cases.items():
            with self.subTest(name=name):
                write(self.b / "index.html", html)
                remote = FakeRemote()
                code, doc = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
                self.assertEqual(code, pha.EXIT_INVALID, doc)
                self.assertEqual(doc["failure"]["kind"], "unresolved_dependencies")
                self.assertEqual(remote.calls, [])
                self.assertFalse(doc["ok"])

    def test_plain_external_hyperlinks_do_not_block_publish(self):
        write(self.b / "index.html", '<link rel="stylesheet" href="a/s.css"><script src="a/app.js"></script>'
              '<a href="https://example.org/docs">docs</a><a href="http://example.org">x</a>'
              '<link rel="canonical" href="https://example.org/r">')
        remote = FakeRemote()
        code, doc = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, 0, doc)
        self.assertEqual(doc["external_resources"] + doc["unresolved"], [])

    def test_symlink_ancestor_of_bundle_rejected(self):
        link = Path(tempfile.mkdtemp()) / "alias"
        os.symlink(self.b, link)
        for bundle in (link, link / "a"):
            with self.subTest(bundle=bundle):
                code, doc = run(["--bundle", str(bundle), "--entry", "index.html" if bundle == link else "x.html",
                                 "--project", "demo", "--artifact", "report", "--bb-session-id", SESSION])
                self.assertEqual(code, pha.EXIT_INVALID)
                self.assertEqual(doc["failure"]["kind"], "bundle_invalid")
                self.assertIn("symlink", doc["failure"]["message"])

    def test_entry_and_artifact_validation(self):
        for argv in (["--entry", "../x.html"], ["--entry", "a/app.js"]):
            with self.subTest(argv=argv):
                code, doc = run(base_args(self.b, *argv))
                self.assertEqual(code, pha.EXIT_INVALID)
        code, doc = run(["--bundle", str(self.b), "--project", "demo", "--artifact", "../x", "--bb-session-id", SESSION])
        self.assertEqual(doc["failure"]["kind"], "artifact_invalid")
        code, doc = run(base_args(self.b, "--entry", "index.html\n"))
        self.assertEqual(code, pha.EXIT_INVALID)

    def test_trailing_newline_and_malformed_names_rejected(self):
        for flag, value, kind in (("--artifact", "report\n", "artifact_invalid"),
                                  ("--artifact", "a/b", "artifact_invalid"),
                                  ("--project", "demo\n", "project_invalid"),
                                  ("--project", "de mo", "project_invalid")):
            with self.subTest(flag=flag, value=value):
                argv = ["--bundle", str(self.b), "--project", "demo", "--artifact", "report",
                        "--bb-session-id", SESSION]
                argv[argv.index(flag) + 1] = value
                code, doc = run(argv)
                self.assertEqual((code, doc["failure"]["kind"]), (pha.EXIT_INVALID, kind))
        with self.assertRaises(pha.Failure):
            pha.resolve_session(None, "codex\n", "x", {})
        write(self.b / ".pj/.project.json", json.dumps({"project_slug": "ev\nil"}))
        with self.assertRaises(pha.Failure) as c:
            pha.resolve_project(None, str(self.b / ".pj"))
        self.assertEqual(c.exception.kind, "project_invalid")

    def test_repo_root_bundle_rejected(self):
        write(self.b / ".project.json", "{}")
        code, doc = self.errors()
        self.assertEqual(code, pha.EXIT_INVALID)


class RemoteValidationTests(unittest.TestCase):
    def test_bucket_and_base_url_are_not_overridable(self):
        for flag in ("--bucket", "--base-url"):
            with self.subTest(flag=flag), self.assertRaises(SystemExit), \
                    contextlib.redirect_stderr(io.StringIO()):
                pha.parse_args(["--bundle", ".", "--artifact", "a", flag, "x"])

    def test_alias_validation(self):
        for alias in ("delo/other", "delo\n", "", "-x", "a b", "https://k:s@h", "../delo"):
            with self.subTest(alias=alias):
                code, doc = run(base_args(SAMPLE, f"--alias={alias}"))
                self.assertEqual((code, doc["failure"]["kind"]), (pha.EXIT_INVALID, "remote_invalid"))
                self.assertNotIn("files", doc)
        code, doc = run(base_args(SAMPLE, "--alias", "delo-2"))
        self.assertEqual(code, 0, doc)
        self.assertTrue(doc["files"][0]["target"].startswith("delo-2/projects/demo/"))

    def test_base_url_validator(self):
        self.assertEqual(pha.validate_remote("delo", "projects", "https://s3.delo.sh/"), "https://s3.delo.sh")
        for url in ("http://s3.delo.sh", "https://user:pw@s3.delo.sh", "https://s3.delo.sh?x=1",
                    "https://s3.delo.sh#f", "https://s3.delo.sh/p", "ftp://s3.delo.sh", "https://",
                    "https://s3.delo.sh\n", "//s3.delo.sh"):
            with self.subTest(url=url), self.assertRaises(pha.Failure):
                pha.validate_remote("delo", "projects", url)
        for bucket in ("Projects", "pro/jects", "projects\n", "p"):
            with self.subTest(bucket=bucket), self.assertRaises(pha.Failure):
                pha.validate_remote("delo", bucket, "https://s3.delo.sh")


class SampleAndDryRunTests(unittest.TestCase):
    def test_sample_bundle_plans_cleanly_offline(self):
        before = {p: p.stat().st_mtime_ns for p in SAMPLE.rglob("*")}
        code, doc = run(base_args(SAMPLE, "--dry-run"))
        self.assertEqual(code, 0, doc)
        self.assertEqual(doc["mode"], "plan")
        self.assertEqual(doc["errors"] + doc["warnings"] + doc["external_resources"] + doc["unresolved"], [])
        self.assertTrue(doc["publishable"])
        self.assertEqual(sorted(f["path"] for f in doc["files"]),
                         ["assets/css/style.css", "assets/img/badge.svg", "assets/js/app.js", "index.html"])
        self.assertEqual(before, {p: p.stat().st_mtime_ns for p in SAMPLE.rglob("*")})

    def test_sample_js_checks_css_and_image(self):
        js = (SAMPLE / "assets/js/app.js").read_text()
        css = (SAMPLE / "assets/css/style.css").read_text()
        html = (SAMPLE / "index.html").read_text()
        self.assertIn("--css-loaded", js)
        self.assertIn("--css-loaded: yes", css)
        self.assertIn("naturalWidth", js)
        for marker in ('id="css-status"', 'id="img-status"', 'id="js-status"', 'src="assets/img/badge.svg"',
                       '<link rel="icon" href="assets/img/badge.svg"'):
            self.assertIn(marker, html)


class PublishTests(unittest.TestCase):
    def test_successful_publish(self):
        remote = FakeRemote()
        code, doc = run(base_args(SAMPLE, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, 0, doc)
        self.assertTrue(doc["ok"])
        self.assertEqual(remote.calls[0][:4], ["mc", "ls", "--json", "--recursive"])
        cps = [c for c in remote.calls if c[1] == "cp"]
        self.assertEqual(len(cps), 4)
        for c in cps:
            self.assertTrue(c[c.index("--attr") + 1].endswith(";Cache-Control=no-cache, no-transform"))
            self.assertTrue(c[-1].startswith(f"delo/projects/demo/{SESSION}/report/"))
            self.assertNotIn("--remove", c)
        self.assertTrue(all(v["ok"] for v in doc["verification"]))
        self.assertEqual(remote.store[f"demo/{SESSION}/report/assets/img/badge.svg"][0], "image/svg+xml")

    def test_collision_fails_closed_without_upload(self):
        remote = FakeRemote(existing=["index.html"])
        code, doc = run(base_args(SAMPLE, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, pha.EXIT_COLLISION)
        self.assertEqual(doc["failure"]["kind"], "collision")
        self.assertFalse(any(c[1] == "cp" for c in remote.calls))

    def test_auth_failure_redacted(self):
        remote = FakeRemote(ls_error="AccessDenied")
        code, doc = run(base_args(SAMPLE, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, pha.EXIT_REMOTE)
        self.assertEqual(doc["failure"]["mc_code"], "AccessDenied")
        dumped = json.dumps(doc)
        self.assertNotIn("AKIA" "ABCDEFGHIJKLMNOP", dumped)
        self.assertNotIn("secret_key=abc", dumped)
        self.assertNotIn("raw stderr", dumped)

    def test_partial_upload_failure(self):
        remote = FakeRemote(cp_fail_on="assets/js/app.js")
        code, doc = run(base_args(SAMPLE, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, pha.EXIT_UPLOAD)
        self.assertFalse(doc["ok"])
        self.assertEqual(doc["failure"]["failed"], "assets/js/app.js")
        self.assertIn("retry", doc["failure"])
        self.assertNotIn("raw stderr", json.dumps(doc))

    def test_remote_mismatch_fails(self):
        remote = FakeRemote()
        def tampered(url, timeout):
            status, ctype, body = remote.fetch(url, timeout)
            return (status, ctype, body + b"x") if url.endswith(".css") else (status, ctype, body)
        code, doc = run(base_args(SAMPLE, "--publish"), runner=remote.runner, fetch=tampered)
        self.assertEqual(code, pha.EXIT_VERIFY)
        bad = [v for v in doc["verification"] if not v["ok"]]
        self.assertEqual([(v["path"], v["problem"]) for v in bad], [("assets/css/style.css", "sha256 mismatch")])

    def test_injected_html_beacon_still_fails_strict_sha(self):
        remote = FakeRemote()
        def beacon(url, timeout):
            status, ctype, body = remote.fetch(url, timeout)
            if url.endswith(".html"):
                body = body.replace(b"</body>", b"<script src='/cdn-cgi/beacon.min.js'></script></body>")
            return status, ctype, body
        code, doc = run(base_args(SAMPLE, "--publish"), runner=remote.runner, fetch=beacon)
        self.assertEqual(code, pha.EXIT_VERIFY)
        self.assertEqual([v["path"] for v in doc["verification"] if not v["ok"]], ["index.html"])

    def test_empty_file_verifies(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<link rel="stylesheet" href="empty.css">')
        write(b / "empty.css", "")
        remote = FakeRemote()
        code, doc = run(base_args(b, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, 0, doc)
        empty = next(v for v in doc["verification"] if v["path"] == "empty.css")
        self.assertTrue(empty["ok"] and empty["sha256_match"])
        self.assertEqual(next(f for f in doc["files"] if f["path"] == "empty.css")["sha256"],
                         hashlib.sha256(b"").hexdigest())
        # A non-200 empty body never counts as a digest match.
        code, doc = run(["--bundle", str(b), "--project", "demo", "--artifact", "r2", "--bb-session-id", SESSION,
                         "--publish"], runner=FakeRemote().runner, fetch=lambda u, t: (404, "text/css", b""))
        self.assertEqual(code, pha.EXIT_VERIFY)
        self.assertFalse(any(v["sha256_match"] for v in doc["verification"]))

    def test_malformed_preflight_output_fails_closed(self):
        for stdout in ("not json", '{"status":"success"}', "[1,2]"):
            with self.subTest(stdout=stdout):
                calls = []
                def runner(cmd, **kw):
                    calls.append(cmd)
                    return Proc(0, stdout)
                code, doc = run(base_args(SAMPLE, "--publish"), runner=runner)
                self.assertEqual((code, doc["failure"]["kind"]), (pha.EXIT_REMOTE, "preflight_malformed"))
                self.assertEqual([c[1] for c in calls], ["ls"])

    def test_wrong_mime_and_404_fail(self):
        remote = FakeRemote()
        def wrong(url, timeout):
            if url.endswith(".svg"):
                return 200, "application/octet-stream", remote.store[url.split("/projects/", 1)[1]][1]
            if url.endswith(".js"):
                return 403, "application/xml", b""
            return remote.fetch(url, timeout)
        code, doc = run(base_args(SAMPLE, "--publish"), runner=remote.runner, fetch=wrong)
        self.assertEqual(code, pha.EXIT_VERIFY)
        problems = {v["path"]: v.get("problem") for v in doc["verification"] if not v["ok"]}
        self.assertEqual(set(problems), {"assets/img/badge.svg", "assets/js/app.js"})

    def test_timeout_is_reported(self):
        def slow(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, kw["timeout"])
        code, doc = run(base_args(SAMPLE, "--publish", "--timeout", "5"), runner=slow)
        self.assertEqual(code, pha.EXIT_REMOTE)
        self.assertEqual(doc["failure"]["kind"], "timeout")


class RegressionSKRILL30Tests(unittest.TestCase):
    """Regressions from the SKRILL-30 quality review: credential guards,
    partial-upload accounting, validated-byte uploads, parser false positives,
    standalone SVG dependencies and the delivered flag."""

    def setUp(self):
        self.b = Path(tempfile.mkdtemp())
        write(self.b / "index.html", '<link rel="stylesheet" href="s.css">')
        write(self.b / "s.css", "body{}")

    def test_credential_files_rejected(self):
        for name in (".s3cfg", ".pgpass", "secrets.toml", "secrets.yaml"):
            with self.subTest(name=name):
                write(self.b / name, "[s3]\naccess_key=1\nsecret_key=2\n")
                code, doc = run(base_args(self.b))
                self.assertEqual(code, pha.EXIT_INVALID, name)
                self.assertTrue(any(name in e for e in doc["errors"]), (name, doc["errors"]))
                self.assertFalse(doc["publishable"])
                self.assertNotIn("access_key", json.dumps(doc))
                (self.b / name).unlink()

    def test_pgp_private_key_block_detected(self):
        write(self.b / "key.asc", "-----BEGIN " "PGP PRIVATE KEY BLOCK-----\nzzz\n")
        code, doc = run(base_args(self.b))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertTrue(any("private key material" in e for e in doc["errors"]))

    def test_source_and_dotfiles_warned_not_blocked(self):
        write(self.b / "app.js.map", '{"sourcesContent":"x"}')
        write(self.b / "src/main.ts", "export const a=1")
        write(self.b / ".DS_Store", "junk")
        code, doc = run(base_args(self.b))
        self.assertEqual(code, 0, doc["errors"])
        warnings = "\n".join(doc["warnings"])
        for needle in ("app.js.map", "src/main.ts", ".DS_Store", "will be public"):
            self.assertIn(needle, warnings)
        self.assertEqual(len(doc["warnings"]), 3, doc["warnings"])

    def test_timeout_mid_upload_reports_partial_accounting(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<link rel="stylesheet" href="s.css"><script src="a.js"></script>')
        write(b / "s.css", "body{}")
        write(b / "a.js", "1;")
        remote = FakeRemote()
        orig = remote.runner
        def flaky(cmd, **kw):
            if cmd[1] == "cp" and cmd[-1].endswith("/s.css"):
                raise subprocess.TimeoutExpired(cmd, kw["timeout"])
            return orig(cmd, **kw)
        code, doc = run(base_args(b, "--publish"), runner=flaky, fetch=remote.fetch)
        self.assertEqual(code, pha.EXIT_UPLOAD)
        f = doc["failure"]
        self.assertEqual((f["kind"], f["cause"]), ("upload_failed", "timeout"))
        self.assertEqual(f["uploaded"], ["a.js", "index.html"])
        self.assertEqual(f["failed"], "s.css")
        self.assertEqual(f["not_attempted"], [])
        self.assertIn("retry", f)
        self.assertFalse(doc["ok"])
        self.assertFalse(doc["delivered"])

    def test_mc_missing_mid_upload_reports_partial_accounting(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<link rel="stylesheet" href="s.css"><script src="a.js"></script>')
        write(b / "s.css", "body{}")
        write(b / "a.js", "1;")
        remote = FakeRemote()
        orig = remote.runner
        def vanishing(cmd, **kw):
            if cmd[1] == "cp" and cmd[-1].endswith("/s.css"):
                raise FileNotFoundError("mc")
            return orig(cmd, **kw)
        code, doc = run(base_args(b, "--publish"), runner=vanishing, fetch=remote.fetch)
        self.assertEqual(code, pha.EXIT_UPLOAD)
        f = doc["failure"]
        self.assertEqual((f["kind"], f["cause"]), ("upload_failed", "mc_missing"))
        self.assertEqual(f["uploaded"], ["a.js", "index.html"])
        self.assertEqual(f["failed"], "s.css")
        self.assertEqual(f["not_attempted"], [])

    def test_upload_uses_validated_snapshot_not_live_paths(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<link rel="stylesheet" href="s.css">')
        write(b / "s.css", "body{}")
        secret_dir = Path(tempfile.mkdtemp())
        secret = secret_dir / "TOPSECRET"
        secret.write_text("TOPSECRET")
        remote = FakeRemote()
        orig = remote.runner
        def swapping(cmd, **kw):
            if cmd[1] == "cp":  # swap live sources after validation, before their upload
                if (b / "s.css").exists() and not (b / "s.css").is_symlink():
                    (b / "s.css").unlink()
                    os.symlink(secret, b / "s.css")
            return orig(cmd, **kw)
        code, doc = run(base_args(b, "--publish"), runner=swapping, fetch=remote.fetch)
        self.assertEqual(code, 0, doc)
        self.assertEqual(remote.store[f"demo/{SESSION}/report/s.css"][1], b"body{}")
        self.assertNotIn("TOPSECRET", json.dumps({k: v[1].decode("latin-1") for k, v in remote.store.items()}))

    def test_snapshot_detects_post_validation_change(self):
        args = pha.parse_args(base_args(self.b))
        plan = pha.build_plan(args, {})
        write(self.b / "s.css", "changed after plan")
        with self.assertRaises(pha.Failure) as c:
            pha._snapshot(plan)
        self.assertEqual(c.exception.kind, "bundle_changed")

    @unittest.skipIf(os.geteuid() == 0, "root bypasses mode 000")
    def test_unreadable_file_gets_json_receipt(self):
        p = self.b / "hidden.css"
        write(p, "x")
        p.chmod(0)
        try:
            code, doc = run(base_args(self.b))
        finally:
            p.chmod(0o644)
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertTrue(any("unreadable file" in e for e in doc["errors"]))

    def test_js_keyword_array_is_raw_candidate_waivable_only_exactly(self):
        # Raw scanning reads the closing quote after "import" as an opener and
        # reports ',' (recovery B: no lexical exclusion). The quote after "from"
        # opens a literal that never closes before the line break; t_00a2629f
        # keeps its bounded raw text '];' instead of dropping it. Both block until waived.
        write(self.b / "app.js", 'var kw=["import","export","from"];\nimport "./s.css";')
        write(self.b / "index.html", '<script src="app.js"></script>')
        code, doc = run(base_args(self.b))
        self.assertEqual(code, 0, doc)
        self.assertEqual([r["ref"] for r in doc["unresolved"]], [",", "];"])
        self.assertFalse(doc["publishable"])
        code, doc = run(base_args(self.b, "--accept-js-candidate", "app.js:,"))
        self.assertEqual(code, 0, doc)
        self.assertEqual([r["ref"] for r in doc["unresolved"]], ["];"])
        self.assertFalse(doc["publishable"])
        code, doc = run(base_args(self.b, "--accept-js-candidate", "app.js:,", "--accept-js-candidate", "app.js:];"))
        self.assertEqual(code, 0, doc)
        self.assertEqual(doc["unresolved"], [])
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "app.js", "specifier": ","},
                                                         {"file": "app.js", "specifier": "];"}])
        self.assertTrue(doc["publishable"])

    def test_non_js_script_blocks_not_scanned_as_js(self):
        write(self.b / "index.html",
              '<script type="application/json">{"op":"import","target":"x"}</script>'
              '<script type="importmap">{"imports":{"a":"./a.js"}}</script>'
              '<script type="text/template">import "{{ x }}";</script>')
        code, doc = run(base_args(self.b))
        self.assertEqual(code, 0, doc)
        self.assertEqual(doc["errors"] + doc["unresolved"], [])

    def test_srcset_data_uri_no_false_missing(self):
        write(self.b / "index.html", '<img srcset="data:image/png;base64,AAAA 1x, b.png 2x" src="b.png">')
        write(self.b / "b.png", "png")
        code, doc = run(base_args(self.b))
        self.assertEqual(code, 0, doc)
        self.assertEqual(doc["errors"], [])
        self.assertEqual(doc["warnings"], [])

    def test_standalone_svg_dependencies_scanned(self):
        write(self.b / "index.html", '<object data="pic.svg"></object>')
        write(self.b / "pic.svg",
              '<svg xmlns="http://www.w3.org/2000/svg"><image href="missing.png"/></svg>')
        code, doc = run(base_args(self.b))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertTrue(any("missing local asset" in e and "missing.png" in e for e in doc["errors"]))

    def test_svg_xml_stylesheet_scanned(self):
        write(self.b / "index.html", '<img src="pic.svg">')
        write(self.b / "pic.svg", '<?xml-stylesheet href="nope.css"?><svg xmlns="http://www.w3.org/2000/svg"/>')
        code, doc = run(base_args(self.b))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertTrue(any("missing local asset" in e and "nope.css" in e for e in doc["errors"]))

    def test_delivered_flag_false_for_plan_and_failures_true_for_verified_publish(self):
        code, doc = run(base_args(self.b))
        self.assertTrue(doc["ok"])
        self.assertFalse(doc["delivered"])
        remote = FakeRemote(cp_fail_on="/s.css")
        code, doc = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, pha.EXIT_UPLOAD)
        self.assertFalse(doc["delivered"])
        remote = FakeRemote()
        code, doc = run(base_args(self.b, "--artifact", "v2", "--publish"),
                        runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, 0)
        self.assertTrue(doc["delivered"])
        self.assertTrue(all(v["ok"] for v in doc["verification"]))


class RegressionQualityRereviewTests(unittest.TestCase):
    """Regressions from the independent quality re-review (Q1-Q5): scan-to-read
    symlink races, subprocess OS-error partial receipts, srcset tokenization,
    unreadable subtrees, and failed-snapshot cleanup."""

    def setUp(self):
        self.b = Path(tempfile.mkdtemp())

    def test_q1_symlink_swap_between_enumeration_and_read_fails_closed(self):
        # Interleave exactly at the validated open: right after the scanner
        # opens a.png (before any bytes are read), replace the name with a
        # symlink to a file outside the bundle. The scanner must read the
        # already-open validated inode, and publication must never carry the
        # outside bytes.
        write(self.b / "index.html", '<img src="a.png">')
        write(self.b / "a.png", "initial in-bundle bytes")
        outside_dir = Path(tempfile.mkdtemp())
        outside = outside_dir / "synthetic-outside.txt"
        outside.write_text("SYNTHETIC_OUTSIDE_BOUNDARY")
        remote = FakeRemote()
        original_open = os.open
        swapped = []
        def swapping_open(path, flags, *args, **kwargs):
            fd = original_open(path, flags, *args, **kwargs)
            if kwargs.get("dir_fd") is not None and Path(path).name == "a.png" and not swapped:
                swapped.append(True)
                (self.b / "a.png").unlink()
                os.symlink(outside, self.b / "a.png")
            return fd
        with patch.object(os, "open", swapping_open):
            code, doc = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertTrue(swapped, "interleaving never fired; test is not exercising the race")
        self.assertEqual(code, pha.EXIT_INVALID, doc)
        self.assertFalse(doc["delivered"])
        self.assertTrue(any("changed during scan" in e and "a.png" in e for e in doc["errors"]), doc["errors"])
        self.assertEqual(remote.store, {})  # nothing uploaded, in particular no outside bytes
        self.assertEqual(remote.calls, [])
        self.assertNotIn("SYNTHETIC_OUTSIDE_BOUNDARY", json.dumps(doc))

    def test_q1_scan_reads_bytes_from_validated_handles(self):
        # The scan must never re-resolve a path to read content: patch
        # Path.read_bytes to leak if it is ever used on bundle files.
        write(self.b / "index.html", '<link rel="stylesheet" href="s.css">')
        write(self.b / "s.css", "body{}")
        def exploding_read(self_path):
            raise AssertionError(f"path-based read used: {self_path}")
        with patch.object(Path, "read_bytes", exploding_read):
            code, doc = run(base_args(self.b))
        self.assertEqual(code, 0, doc)
        self.assertTrue(doc["publishable"])

    def test_q2_permission_error_mid_upload_reports_partial_accounting(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<link rel="stylesheet" href="s.css"><script src="z.js"></script>')
        write(b / "s.css", "body{}")
        write(b / "z.js", "1;")
        remote = FakeRemote()
        orig = remote.runner
        def denied(cmd, **kw):
            if cmd[1] == "cp" and cmd[-1].endswith("/s.css"):
                raise PermissionError(errno.EACCES, "Permission denied", "mc")
            return orig(cmd, **kw)
        code, doc = run(base_args(b, "--publish"), runner=denied, fetch=remote.fetch)
        self.assertEqual(code, pha.EXIT_UPLOAD, doc)
        f = doc["failure"]
        self.assertEqual(f["kind"], "upload_failed")
        self.assertEqual(f["cause"], "os_error")
        self.assertEqual(f["uploaded"], ["index.html"])
        self.assertEqual(f["failed"], "s.css")
        self.assertEqual(f["not_attempted"], ["z.js"])
        self.assertIn("retry", f)
        self.assertFalse(doc["ok"] or doc["delivered"])
        self.assertEqual(sorted(remote.store), [f"demo/{SESSION}/report/index.html"])

    def test_q2_runner_oserror_bypassing_run_still_accounted(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<link rel="stylesheet" href="s.css">')
        write(b / "s.css", "body{}")
        remote = FakeRemote()
        orig = remote.runner
        def raw_oserror(cmd, **kw):
            if cmd[1] == "cp" and cmd[-1].endswith("/s.css"):
                raise OSError(errno.EAGAIN, "Resource temporarily unavailable")
            return orig(cmd, **kw)
        code, doc = run(base_args(b, "--publish"), runner=raw_oserror, fetch=remote.fetch)
        self.assertEqual(code, pha.EXIT_UPLOAD, doc)
        self.assertEqual(doc["failure"]["uploaded"], ["index.html"])
        self.assertEqual(doc["failure"]["failed"], "s.css")
        self.assertEqual(doc["failure"]["not_attempted"], [])

    def test_q3_srcset_second_candidate_without_space_is_required(self):
        write(self.b / "index.html", '<img srcset="data:image/png;base64,AAAA 1x,missing.png 2x">')
        code, doc = run(base_args(self.b))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertTrue(any("missing local asset" in e and "missing.png" in e for e in doc["errors"]))

    def test_q3_srcset_second_candidate_present_publishes(self):
        write(self.b / "index.html",
              '<img srcset="data:image/png;base64,AAAA 1x,missing.png 2x" src="missing.png">')
        write(self.b / "missing.png", "png")
        remote = FakeRemote()
        code, doc = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, 0, doc)
        self.assertEqual(doc["errors"], [])
        self.assertEqual(sorted(f["path"] for f in doc["files"]), ["index.html", "missing.png"])

    def test_q3_srcset_tokenization_cases(self):
        self.assertEqual(pha._srcset_candidates("a.png 1x, b.png 2x"), ["a.png", "b.png"])
        self.assertEqual(pha._srcset_candidates("a.png 1x,b.png 2x"), ["a.png", "b.png"])
        self.assertEqual(pha._srcset_candidates("data:image/png;base64,AAAA 1x, b.png 2x"),
                         ["data:image/png;base64,AAAA", "b.png"])
        self.assertEqual(pha._srcset_candidates("data:image/png;base64,AAAA 1x,b.png 2x"),
                         ["data:image/png;base64,AAAA", "b.png"])
        self.assertEqual(pha._srcset_candidates("data:image/png;base64,AAAA"), ["data:image/png;base64,AAAA"])
        self.assertEqual(pha._srcset_candidates("  "), [])
        self.assertEqual(pha._srcset_candidates("a.png"), ["a.png"])

    @unittest.skipIf(os.geteuid() == 0, "root bypasses mode 000")
    def test_q4_unreadable_subdirectory_fails_closed(self):
        write(self.b / "index.html", "<p>hello</p>")
        write(self.b / "nested/extra.html", "<p>second page</p>")
        (self.b / "nested").chmod(0)
        remote = FakeRemote()
        try:
            code, doc = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
        finally:
            (self.b / "nested").chmod(0o700)
        self.assertEqual(code, pha.EXIT_INVALID, doc)
        self.assertEqual(doc["failure"]["kind"], "walk_failed")
        self.assertIn("nested", doc["failure"]["message"])
        self.assertEqual(remote.calls, [])  # no upload may happen
        self.assertNotIn("files", doc)

    def test_q5_failed_snapshot_leaves_no_partial_copy(self):
        write(self.b / "index.html", '<link rel="stylesheet" href="s.css">')
        write(self.b / "s.css", "body{}")
        remote = FakeRemote()
        original_mkdtemp = tempfile.mkdtemp
        original_snapshot = pha._snapshot
        created = []
        def tracking_mkdtemp(*args, **kwargs):
            path = original_mkdtemp(*args, **kwargs)
            created.append(Path(path))
            return path
        def mutating_snapshot(plan):
            write(self.b / "s.css", "SYNTHETIC_UNVALIDATED_BYTES")
            return original_snapshot(plan)
        with patch.object(tempfile, "mkdtemp", tracking_mkdtemp), \
             patch.object(pha, "_snapshot", mutating_snapshot):
            code, doc = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, pha.EXIT_INVALID, doc)
        self.assertEqual(doc["failure"]["kind"], "bundle_changed")
        self.assertEqual(remote.calls, [])
        leftover = [p for p in created if p.exists()]
        self.assertEqual(leftover, [], f"snapshot directories leaked: {leftover}")

    def test_q5_snapshot_failure_inside_cleanup_is_removed(self):
        # Mutation during the copy loop itself (mid-snapshot) must also clean up.
        write(self.b / "index.html", '<link rel="stylesheet" href="n/x.css">')
        write(self.b / "n/x.css", "body{}")
        original_mkdtemp = tempfile.mkdtemp
        created = []
        def tracking_mkdtemp(*args, **kwargs):
            path = original_mkdtemp(*args, **kwargs)
            created.append(Path(path))
            return path
        real_open_rel_dir = pha._open_rel_dir
        seen = []
        def mutating_open(base_fd, rel_dir):
            fd = real_open_rel_dir(base_fd, rel_dir)
            if rel_dir.parts and not seen:
                seen.append(True)
                write(self.b / "n/x.css", "SYNTHETIC_UNVALIDATED_BYTES")
            return fd
        remote = FakeRemote()
        with patch.object(tempfile, "mkdtemp", tracking_mkdtemp), \
             patch.object(pha, "_open_rel_dir", mutating_open):
            code, doc = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, pha.EXIT_INVALID, doc)
        self.assertEqual(doc["failure"]["kind"], "bundle_changed")
        self.assertTrue(seen)
        self.assertEqual([p for p in created if p.exists()], [])



# Exact diagnostic text shipped in React's development build (lazy()).
REACT_LAZY_WARNING = (
    "lazy: Expected the result of a dynamic import() call. Instead received: %s\n\n"
    "Your code should look like: \n"
    "  const MyComponent = lazy(() => import('./MyComponent'))\n\n"
    "Did you accidentally put curly braces around the import?"
)


def js_single(text):
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"


def js_double(text):
    return json.dumps(text)


def js_template(text):
    return "`" + text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${") + "`"


SCRIPT = HERE.parent / "scripts/publish_html_artifact.py"
SPECS = {"missing": ("./absent.js", "./absent.js"),
         "bare": ("missing-package", "missing-package"),
         "templated": ("./${name}.js", "./${name}.js")}

# Every shape from the three review rounds (t_ec1c3ed4, t_ec1c3ed4-r2,
# t_36dd3a80) plus spread/spaced/comment-separated forms. SPEC is the literal.
HISTORICAL_SHAPES = {
    # round 1: contextual identifiers, members, numbers, for-await
    "contextual-of": "const of=6; of / import(SPEC) / 2;",
    "member-return": "const obj={return:6}; obj.return / import(SPEC) / 2;",
    "member-new": "const r=stats.new/stats.total;import(SPEC);const q=r/2;",
    "optional-member": "obj?.return / import(SPEC) / 2;",
    "number-dot": "x=1./import(SPEC)/2",
    "for-await": "async function f(){for await (const x of y) /'/.test(x); import(SPEC)}",
    # round 2: quote/backtick/comment-bearing regex bodies
    "await-quote": "async function f(){await /'/; import(SPEC);}",
    "yield-quote": "function* f(){yield /'/; import(SPEC);}",
    "await-backtick": "async function f(){await /`/; import(SPEC);}",
    "for-of-quote": "for (const c of /'/[Symbol.split](\"a'b\")) ; import(SPEC)",
    "for-of-escaped": r"for (const c of /\/\//.exec('x//y') ?? []) ; import(SPEC)",
    "for-of-comment": "for (const c of /[/*]/.exec('*') ?? []) ;\nimport(SPEC);",
    "default-regex": "export default /'/; import(SPEC)",
    "class-expression": "const x=class {} / import(SPEC) / 2;",
    "static-after-quote-regex": "async function f(){await /'/;}\nimport importedModule from SPEC;",
    "reexport-after-quote-regex": "function* f(){yield /'/;}\nexport * from SPEC;",
    # round 3: from bindings, nested blocks, spread, extends, for heads
    "binding-from": "import {from} from SPEC;",
    "default-from": "import from from SPEC;",
    "alias-from": "import {x as from} from SPEC;",
    "namespace-from": "import * as from from SPEC;",
    "default-and-from": "import from, { a } from SPEC;",
    "export-from": "export {from} from SPEC;",
    "export-as-from": "export {x as from} from SPEC;",
    "arrow-nested-block": "const f = () => { {} /'/.test(\"'\"); import(SPEC); \"'\" }",
    "fnexpr-nested-block": "(function(){ {} /'/.test(\"'\"); import(SPEC); \"'\" })()",
    "static-block": "class A { static { {} /'/.test(\"'\"); import(SPEC); \"'\" } }",
    "spread-array": "const mods = [...import(SPEC)]",
    "spread-call": "f(...import(SPEC))",
    "spread-object": "const o = ({...import(SPEC)})",
    "spread-regex": "const m = [.../'/.exec(\"'\")]; import x from SPEC; \"'\"",
    "extends-regex": "class A extends /'/.constructor {}; import x from SPEC; \"'\"",
    "for-fn-head": "for (;function(){} / '/';) {} import x from SPEC; \"'\"",
    "for-obj-head": "for (;{} / '/';) {} import x from SPEC; \"'\"",
    # spaced and comment-separated literal imports
    "spaced-dynamic": "import (SPEC)",
    "spread-spaced": "f(... import ( SPEC ))",
    "newline-dynamic": "import\n(\n  SPEC\n)",
    "block-comment-dynamic": "import/*a*/(/*b*/SPEC/*c*/)",
    "line-comment-dynamic": "import // why\n( // because\nSPEC)",
    "comment-side-effect": "import/**/SPEC",
    "line-comment-side-effect": "import // note\nSPEC;",
    "comment-reexport": "export/**/*/**/from/**/SPEC",
    "comment-static": "import x /* a */ from // b\nSPEC",
    "minified-static": "import{a as b}from SPEC;",
}


def shape_js(shape, literal):
    return HISTORICAL_SHAPES[shape].replace("SPEC", json.dumps(literal))


class RawJsScannerTests(unittest.TestCase):
    """Raw candidate discovery (recovery B): no lexer, no lexical exclusions.
    Import-shaped text in strings, comments and regexes is reported on purpose;
    a human waives an inspected false positive with --accept-js-candidate."""

    def refs(self, js):
        out = list(pha._js_refs(js, "unit"))
        for item in out:
            self.assertIsInstance(item, tuple)
            self.assertEqual(item[1:], ("module", "unit"))
        return [spec for spec, _, _ in out]

    def test_no_lexer_machinery_remains(self):
        for name in ("_js_code_offsets", "_js_candidate", "_js_template_end", "MAX_JS_STATES",
                     "MAX_TEMPLATE_DEPTH", "_JS_KEYWORDS", "_JS_EVENTS"):
            self.assertFalse(hasattr(pha, name), name)

    def test_every_historical_shape_reports_its_specifier(self):
        for shape in HISTORICAL_SHAPES:
            for kind, (literal, spec) in SPECS.items():
                with self.subTest(shape=shape, kind=kind):
                    self.assertIn(spec, self.refs(shape_js(shape, literal)))

    def test_react_lazy_warning_is_reported_raw_in_strings_and_comments(self):
        forms = {
            "double": (f"console.error({js_double(REACT_LAZY_WARNING)}, x);", ["./MyComponent"]),
            "template": (f"console.error({js_template(REACT_LAZY_WARNING)});", ["./MyComponent"]),
            "template-interp": ("console.error(`" + REACT_LAZY_WARNING.replace("%s", "${typeof x}") + "`);",
                                ["./MyComponent"]),
            "concat": ("console.error('lazy: ' + \"const MyComponent = lazy(() => import('./MyComponent'))\");",
                       ["./MyComponent"]),
            "line-comments": ("\n".join("// " + l for l in REACT_LAZY_WARNING.splitlines()) + "\nvar a = 1;",
                              ["./MyComponent"]),
            "block-comment": ("/* " + REACT_LAZY_WARNING + " */ var a = 1;", ["./MyComponent"]),
            # an escaped quote is not a quote: no literal follows import(
            "single-escaped": (f"console.error({js_single(REACT_LAZY_WARNING)}, x);", []),
        }
        for name, (js, want) in forms.items():
            with self.subTest(form=name):
                self.assertEqual(self.refs(js), want)

    def test_strings_comments_and_regexes_are_reported_not_excluded(self):
        cases = {
            "var s = 'import \"./nope.js\"';": ["./nope.js"],
            'var s = "import x from \'./nope.js\'";': ["./nope.js"],
            "var s = `export * from './nope.js'`;": ["./nope.js"],
            "var s = `import('./nope.js')`;": ["./nope.js"],
            "// import './nope.js'\nvar a;": ["./nope.js"],
            "/* import x from './nope.js' */": ["./nope.js"],
            "/* multi\nline import('./nope.js')\n*/": ["./nope.js"],
            "var r = /import \"\\.\\/nope.js\"/g;": ["\\.\\/nope.js"],
            "a.import('./member.js'); a?.import('./opt.js');": ["./member.js", "./opt.js"],
        }
        for js, want in cases.items():
            with self.subTest(js=js):
                self.assertEqual(self.refs(js), want)

    def test_real_imports_kept_in_source_order_beside_false_positives(self):
        js = (f"const w = {js_double(REACT_LAZY_WARNING)};\n"
              "import def, { a as b } from './static.mjs';\n"
              "import * as ns from \"./ns.mjs\";\n"
              "import './side.mjs';\n"
              "export * from './reexport.mjs';\n"
              "export { c as d } from \"./named.mjs\";\n"
              "const lazyMod = () => import('./dynamic.mjs');\n"
              "const tmplMod = () => import(`./plain-template.mjs`);\n")
        self.assertEqual(self.refs(js), ["./MyComponent", "./static.mjs", "./ns.mjs", "./side.mjs",
                                         "./reexport.mjs", "./named.mjs", "./dynamic.mjs", "./plain-template.mjs"])
        js = ('import{a as b}from"./a.mjs";export*from\'./b.mjs\';import"./c.mjs";'
              '/*import\'./nope2.js\'*/export{q}from"./d.mjs";const f=()=>import("./e.mjs");'
              "var r=/['\"/]/g;import'./f.mjs'")
        self.assertEqual(self.refs(js), ["./a.mjs", "./b.mjs", "./c.mjs", "./nope2.js", "./d.mjs",
                                         "./e.mjs", "./f.mjs"])

    def test_non_import_words_and_shapes_are_not_candidates(self):
        for js in ("const o = { import: './nope.js', export: \"./nope2.js\" };",
                   "myimport('./nope.js'); import_('./nope.js'); $import('./nope.js'); importer('./x.js')",
                   "const u = import.meta.url; import();",
                   "export const from = './nope.js';",
                   "export { a, b }\nfrom('./nope.js');",
                   "const m = import(name); const n = import(base + './x.js');",
                   "fromage './nope.js'; reimport './nope.js'"):
            with self.subTest(js=js):
                self.assertEqual(self.refs(js), [])

    def test_templated_specifiers_keep_interpolation_and_stay_unresolved(self):
        self.assertEqual(self.refs("import(`./${name}.mjs`);"), ["./${name}.mjs"])
        self.assertEqual(self.refs("import(`./a${`b${c}`}.mjs`);"), ["./a${"])
        self.assertEqual(self.refs("import React from 'react'; import('lodash');"), ["react", "lodash"])

    def test_unclosed_and_overlong_literals(self):
        # Cut short by EOF or a line break: uncertain, so the bounded raw text is
        # still a candidate (t_00a2629f: never silently omitted).
        self.assertEqual(self.refs("import('./u.js"), ["./u.js"])
        self.assertEqual(self.refs("import './line\nbreak.js'"), ["./line"])
        self.assertEqual(self.refs('var kw=["import","export","from"];\nfrom: "from",\n'), [",", "];", ","])
        # Passes are independent: a later match inside an open comment is still raw text.
        self.assertEqual(self.refs("x; import /* never closed import('./c.js')"), ["./c.js"])
        # A closing quote read as an opener is a raw false positive, reported on purpose.
        self.assertEqual(self.refs('m = " passed from " + name + ".";'), ["+ name +"])
        long = "import('./" + "a" * (pha.MAX_JS_SPECIFIER + 10) + "')"
        self.assertEqual(self.refs(long), ["./" + "a" * (pha.MAX_JS_SPECIFIER - 2)])

    def test_escaped_specifiers_stay_raw(self):
        self.assertEqual(self.refs(r"import('.\/x.js'); import '\u002e/y.js'"), [r".\/x.js", r"\u002e/y.js"])

    def test_adversarial_sizes_are_bounded(self):
        for js in ("x=/[" * 50_000 + '\nimport("missing-package");',
                   "x=" + "a.in/[" * 50_000 + "0" + "]" * 50_000 + ';import("missing-package");',
                   'const x="import(\'ghost\')";' * 50_000 + 'import("missing-package");',
                   "`${" * 5_000 + "}`" * 5_000 + 'import("missing-package");'):
            with self.subTest(size=len(js)):
                start = time.perf_counter()
                self.assertIn("missing-package", self.refs(js))
                self.assertLess(time.perf_counter() - start, 2.0)

    def test_quadratic_comment_input_fails_closed_not_partial(self):
        js = '"' + "import//" * 40_000 + '"\nimport("missing-package")'
        with self.assertRaises(pha.Failure) as c:
            self.refs(js)
        self.assertEqual(c.exception.kind, "bundle_invalid")


class RawJsScannerCliTests(unittest.TestCase):
    """Real offline CLI plans: every historical shape blocks without flags."""

    def setUp(self):
        self.b = Path(tempfile.mkdtemp())
        write(self.b / "index.html", '<script type="module" src="app.js"></script>')

    def assert_blocks(self, doc, kind, spec):
        self.assertFalse(doc["publishable"], doc)
        self.assertFalse(doc["delivered"], doc)
        self.assertEqual(doc["accepted_js_candidates"], [])
        if kind == "missing":
            self.assertTrue(any(spec in e for e in doc["errors"]), doc)
        else:
            self.assertIn(spec, [r["ref"] for r in doc["unresolved"]], doc)

    def test_every_historical_shape_blocks_in_process_cli(self):
        for shape in HISTORICAL_SHAPES:
            for kind, (literal, spec) in SPECS.items():
                with self.subTest(shape=shape, kind=kind):
                    write(self.b / "app.js", shape_js(shape, literal))
                    code, doc = run(base_args(self.b))
                    self.assertEqual(code, pha.EXIT_INVALID if kind == "missing" else 0, doc)
                    self.assert_blocks(doc, kind, spec)
                    remote = FakeRemote()
                    code, published = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
                    self.assertEqual(code, pha.EXIT_INVALID, published)
                    self.assertEqual(remote.calls, [])

    def test_review_shapes_block_through_subprocess_cli(self):
        self.assertEqual(len(HISTORICAL_SHAPES), 43)
        for shape in HISTORICAL_SHAPES:
            for kind, (literal, spec) in SPECS.items():
                with self.subTest(shape=shape, kind=kind):
                    write(self.b / "app.js", shape_js(shape, literal))
                    proc = subprocess.run([sys.executable, str(SCRIPT), *base_args(self.b)],
                                          capture_output=True, text=True, timeout=10)
                    doc = json.loads(proc.stdout)
                    self.assertEqual(proc.returncode, pha.EXIT_INVALID if kind == "missing" else 0, doc)
                    self.assert_blocks(doc, kind, spec)

    def test_inline_scripts_in_html_and_svg_are_scanned(self):
        write(self.b / "index.html", '<script type="module">import(\'./gone.js\')</script><img src="p.svg">')
        write(self.b / "p.svg", '<svg xmlns="http://www.w3.org/2000/svg"><script>import("lodash")</script></svg>')
        code, doc = run(base_args(self.b))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertTrue(any("./gone.js" in e and e.startswith("index.html inline script") for e in doc["errors"]))
        self.assertEqual([(r["referrer"], r["ref"]) for r in doc["unresolved"]], [("p.svg", "lodash")])

    def test_quadratic_comment_input_rejects_bundle(self):
        write(self.b / "app.js", '"' + "import//" * 40_000 + '"\nimport("missing-package")')
        code, doc = run(base_args(self.b))
        self.assertEqual((code, doc["failure"]["kind"]), (pha.EXIT_INVALID, "bundle_invalid"))
        self.assertFalse(doc["ok"] or doc["delivered"])


class AcceptJsCandidateTests(unittest.TestCase):
    """--accept-js-candidate FILE:SPECIFIER: exact, file-scoped, JS-only waivers."""

    REACT = "_vendor/react.js:./MyComponent"

    def setUp(self):
        self.b = Path(tempfile.mkdtemp())
        write(self.b / "index.html", '<script type="module" src="_vendor/react.js"></script>')
        write(self.b / "_vendor/react.js",
              f"export const w = {js_double(REACT_LAZY_WARNING)};\n"
              f"/* {REACT_LAZY_WARNING} */\nexport const t = {js_template(REACT_LAZY_WARNING)};\n")

    def plan(self, *accept):
        args = []
        for value in accept:
            args += ["--accept-js-candidate", value]
        return run(base_args(self.b, *args))

    def test_react_warning_blocks_by_default_and_exact_acceptance_publishes(self):
        code, doc = self.plan()
        self.assertEqual(code, pha.EXIT_INVALID, doc)
        self.assertEqual(doc["failure"]["kind"], "bundle_invalid")
        self.assertEqual(sum("./MyComponent" in e for e in doc["errors"]), 3, doc["errors"])
        self.assertEqual(doc["accepted_js_candidates"], [])
        code, doc = self.plan(self.REACT)
        self.assertEqual(code, 0, doc)
        self.assertTrue(doc["publishable"])
        self.assertEqual(doc["errors"] + doc["unresolved"], [])
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "_vendor/react.js", "specifier": "./MyComponent"}])
        remote = FakeRemote()
        code, doc = run(base_args(self.b, "--publish", "--accept-js-candidate", self.REACT),
                        runner=remote.runner, fetch=remote.fetch)
        self.assertEqual(code, 0, doc)
        self.assertTrue(doc["delivered"])
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "_vendor/react.js", "specifier": "./MyComponent"}])
        code, doc = run(base_args(self.b, "--artifact", "v2", "--publish"),
                        runner=FakeRemote().runner, fetch=FakeRemote().fetch)
        self.assertEqual((code, doc["accepted_js_candidates"]), (pha.EXIT_INVALID, []))

    def test_other_missing_in_same_file_still_blocks(self):
        with open(self.b / "_vendor/react.js", "a") as fh:
            fh.write("import './gone.js'; import('lodash');\n")
        code, doc = self.plan(self.REACT)
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertTrue(any("./gone.js" in e for e in doc["errors"]))
        self.assertFalse(any("MyComponent" in e for e in doc["errors"]))
        self.assertEqual([r["ref"] for r in doc["unresolved"]], ["lodash"])
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "_vendor/react.js", "specifier": "./MyComponent"}])

    def test_same_specifier_in_another_file_still_blocks(self):
        write(self.b / "index.html", '<script type="module" src="_vendor/react.js"></script>'
                                     '<script type="module" src="app.js"></script>')
        write(self.b / "app.js", "import('./MyComponent');")
        code, doc = self.plan(self.REACT)
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertEqual([e for e in doc["errors"] if "MyComponent" in e],
                         ["app.js js import: missing local asset './MyComponent' (resolved 'MyComponent')"])

    def test_html_and_css_references_are_never_waived(self):
        write(self.b / "index.html", '<script type="module" src="_vendor/react.js"></script>'
                                     '<img src="./MyComponent"><link rel="stylesheet" href="s.css">'
                                     '<script type="module">import("./MyComponent")</script>')
        write(self.b / "s.css", "body{background:url(./MyComponent)}")
        code, doc = self.plan(self.REACT, "index.html:./MyComponent", "s.css:./MyComponent")
        self.assertEqual(code, pha.EXIT_INVALID)
        errors = "\n".join(doc["errors"])
        self.assertIn("index.html <img src>: missing local asset './MyComponent'", errors)
        self.assertIn("s.css css: missing local asset './MyComponent'", errors)
        self.assertNotIn("index.html inline script", errors)
        self.assertIn("unused --accept-js-candidate s.css:./MyComponent", errors)
        self.assertEqual(doc["accepted_js_candidates"],
                         [{"file": "_vendor/react.js", "specifier": "./MyComponent"},
                          {"file": "index.html", "specifier": "./MyComponent"}])

    def test_near_matches_are_unused_and_refused(self):
        for value in ("_vendor/react.js:./MyComponent.js", "_vendor/react.js:MyComponent",
                      "_vendor/react.js:./MyComponent ", "_vendor/react.js:./My", "_vendor/react.js:*",
                      "_vendor/React.js:./MyComponent", "react.js:./MyComponent", "_vendor/*:./MyComponent",
                      "_vendor/react.js:./mycomponent"):
            with self.subTest(value=value):
                code, doc = self.plan(value)
                self.assertEqual((code, doc["failure"]["kind"]), (pha.EXIT_INVALID, "bundle_invalid"))
                self.assertIn(f"unused --accept-js-candidate {value}", "\n".join(doc["errors"]))
                self.assertEqual(doc["accepted_js_candidates"], [])

    def test_unused_acceptance_beside_used_one_is_refused_but_reports_used(self):
        code, doc = self.plan(self.REACT, "_vendor/react.js:./ghost.js")
        self.assertEqual((code, doc["failure"]["kind"]), (pha.EXIT_INVALID, "bundle_invalid"))
        self.assertFalse(doc["publishable"])
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "_vendor/react.js", "specifier": "./MyComponent"}])
        self.assertEqual([e for e in doc["errors"] if "unused" in e],
                         ["unused --accept-js-candidate _vendor/react.js:./ghost.js: no JS candidate './ghost.js' "
                          "was emitted for '_vendor/react.js'; acceptances must match an emitted candidate exactly"])

    def test_malformed_acceptances_are_invalid_input(self):
        for value in ("", "nocolon", ":./x", "_vendor/react.js:", "/_vendor/react.js:./MyComponent",
                      "./_vendor/react.js:./MyComponent", "_vendor/./react.js:./MyComponent",
                      "_vendor/../_vendor/react.js:./MyComponent", "_vendor//react.js:./MyComponent",
                      "_vendor/:./MyComponent", "_vendor\\react.js:./MyComponent", "..:./x", ".:./x",
                      "_vendor/react\x01.js:./x", "_vendor/react\x7f.js:./x", "_vendor/react.js\n:./x"):
            with self.subTest(value=value):
                code, doc = self.plan(value)
                self.assertEqual((code, doc["failure"]["kind"]), (pha.EXIT_INVALID, "acceptance_invalid"))
                self.assertNotIn("files", doc)
                self.assertFalse(doc["ok"] or doc["delivered"])
        with self.assertRaises(pha.Failure):
            pha.parse_acceptances(["a.js"])
        self.assertEqual(pha.parse_acceptances(["a/b.js:x:y", "a/b.js:x:y"]), {("a/b.js", "x:y")})

    def test_duplicate_acceptances_dedup_deterministically(self):
        code, doc = self.plan(self.REACT, self.REACT, self.REACT)
        self.assertEqual(code, 0, doc)
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "_vendor/react.js", "specifier": "./MyComponent"}])

    def test_specifier_containing_colon_splits_at_first_colon(self):
        write(self.b / "app.js", 'import "virtual:thing"; import("data:text/javascript,1");')
        write(self.b / "index.html", '<script type="module" src="app.js"></script>')
        code, doc = self.plan()
        self.assertEqual([r["ref"] for r in doc["unresolved"]], ["virtual:thing"])
        code, doc = self.plan("app.js:virtual:thing", self.REACT)
        self.assertEqual(code, 0, doc)
        self.assertTrue(doc["publishable"])
        self.assertEqual(doc["accepted_js_candidates"],
                         [{"file": "_vendor/react.js", "specifier": "./MyComponent"},
                          {"file": "app.js", "specifier": "virtual:thing"}])

    def test_inline_identities_are_the_containing_file(self):
        write(self.b / "index.html", "<script>import('./ghost.js')</script>")
        write(self.b / "sub/page.html", "<script type='module'>import('./ghost.js')</script>")
        write(self.b / "p.svg", '<svg xmlns="http://www.w3.org/2000/svg"><script>import("./ghost.js")</script></svg>')
        write(self.b / "m.mjs", "import('./ghost.js')")
        accepts = ["index.html:./ghost.js", "sub/page.html:./ghost.js", "p.svg:./ghost.js", "m.mjs:./ghost.js",
                   self.REACT]
        code, doc = self.plan(*accepts)
        self.assertEqual(code, 0, doc)
        self.assertEqual([(a["file"], a["specifier"]) for a in doc["accepted_js_candidates"]],
                         sorted(tuple(a.split(":", 1)) for a in accepts))
        code, doc = self.plan(*accepts[1:])
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertEqual([e for e in doc["errors"] if "ghost" in e],
                         ["index.html inline script: missing local asset './ghost.js' (resolved 'ghost.js')"])
        code, doc = self.plan("page.html:./ghost.js", *accepts[2:])
        self.assertTrue(any("unused --accept-js-candidate page.html:./ghost.js" in e for e in doc["errors"]))

    def test_pair_acceptance_covers_every_occurrence_including_real_imports(self):
        # Documented scope: one pair waives ALL occurrences in that file, so a
        # real import that shares the pair is waived too. Inspect every one.
        write(self.b / "app.js", "const s = \"import('./x.js')\"; import('./x.js');")
        write(self.b / "index.html", '<script type="module" src="app.js"></script>')
        code, doc = self.plan()
        self.assertEqual(sum("./x.js" in e for e in doc["errors"]), 2)
        code, doc = self.plan("app.js:./x.js", self.REACT)
        self.assertEqual(code, 0, doc)
        self.assertTrue(doc["publishable"])

    def test_security_checks_cannot_be_waived(self):
        write(self.b / ".env", "TOKEN=1")
        write(self.b / "id.js", "-----BEGIN " "OPENSSH PRIVATE KEY-----\nzzz\nimport('./MyComponent')")
        os.symlink(self.b / "_vendor/react.js", self.b / "link.js")
        code, doc = self.plan(self.REACT, "id.js:./MyComponent", "link.js:./MyComponent", ".env:./x")
        self.assertEqual(code, pha.EXIT_INVALID)
        errors = "\n".join(doc["errors"])
        for needle in ("dangerous file rejected: .env", "private key material detected in id.js",
                       "symlink rejected: link.js", "unused --accept-js-candidate link.js:./MyComponent",
                       "unused --accept-js-candidate .env:./x"):
            self.assertIn(needle, errors)
        self.assertNotIn("zzz", json.dumps(doc))
        self.assertEqual(doc["accepted_js_candidates"],
                         [{"file": "_vendor/react.js", "specifier": "./MyComponent"},
                          {"file": "id.js", "specifier": "./MyComponent"}])

    def test_every_post_plan_receipt_carries_accepted_candidates(self):
        want = [{"file": "_vendor/react.js", "specifier": "./MyComponent"}]
        accept = ["--accept-js-candidate", self.REACT]
        write(self.b / "s.css", "body{}")
        write(self.b / "index.html", '<script type="module" src="_vendor/react.js"></script>'
                                     '<link rel="stylesheet" href="s.css">')
        cases = {}
        cases["collision"] = (FakeRemote(existing=["index.html"]), None, pha.EXIT_COLLISION)
        cases["preflight_failed"] = (FakeRemote(ls_error="AccessDenied"), None, pha.EXIT_REMOTE)
        cases["upload_failed"] = (FakeRemote(cp_fail_on="/s.css"), None, pha.EXIT_UPLOAD)
        verify_remote = FakeRemote()
        cases["verify_failed"] = (verify_remote, lambda u, t: (404, "text/html", b""), pha.EXIT_VERIFY)
        for kind, (remote, fetch, exit_code) in cases.items():
            with self.subTest(kind=kind):
                code, doc = run(base_args(self.b, "--publish", *accept), runner=remote.runner,
                                fetch=fetch or remote.fetch)
                self.assertEqual((code, doc["failure"]["kind"]), (exit_code, kind), doc)
                self.assertEqual(doc["accepted_js_candidates"], want)
                self.assertFalse(doc["delivered"])
                if kind == "upload_failed":
                    self.assertEqual(doc["failure"]["uploaded"], ["_vendor/react.js", "index.html"])
                    self.assertEqual(doc["failure"]["failed"], "s.css")
        def slow(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, kw["timeout"])
        code, doc = run(base_args(self.b, "--publish", *accept), runner=slow)
        self.assertEqual((code, doc["failure"]["kind"], doc["accepted_js_candidates"]), (pha.EXIT_REMOTE, "timeout", want))
        original_snapshot = pha._snapshot
        def mutating_snapshot(plan):
            write(self.b / "s.css", "changed")
            return original_snapshot(plan)
        with patch.object(pha, "_snapshot", mutating_snapshot):
            code, doc = run(base_args(self.b, "--publish", *accept), runner=FakeRemote().runner)
        self.assertEqual((code, doc["failure"]["kind"], doc["accepted_js_candidates"]),
                         (pha.EXIT_INVALID, "bundle_changed", want))
        write(self.b / "s.css", "body{}")
        write(self.b / "extra.js", "import('lodash')")
        write(self.b / "index.html", '<script type="module" src="_vendor/react.js"></script>'
                                     '<script type="module" src="extra.js"></script>')
        code, doc = run(base_args(self.b, "--publish", *accept), runner=FakeRemote().runner)
        self.assertEqual((code, doc["failure"]["kind"], doc["accepted_js_candidates"]),
                         (pha.EXIT_INVALID, "unresolved_dependencies", want))
        code, doc = run(base_args(self.b, *accept))
        self.assertEqual((code, doc["ok"], doc["accepted_js_candidates"]), (0, True, want))
        self.assertFalse(doc["publishable"])

    def test_subprocess_cli_round_trip(self):
        argv = [sys.executable, str(SCRIPT), *base_args(self.b)]
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, pha.EXIT_INVALID)
        self.assertEqual(json.loads(proc.stdout)["accepted_js_candidates"], [])
        proc = subprocess.run(argv + ["--accept-js-candidate", self.REACT], capture_output=True, text=True, timeout=10)
        doc = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, 0, doc)
        self.assertTrue(doc["publishable"])
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "_vendor/react.js", "specifier": "./MyComponent"}])


def subprocess_plan(bundle, *extra):
    proc = subprocess.run([sys.executable, str(SCRIPT), *base_args(bundle, *extra)],
                          capture_output=True, text=True, timeout=10)
    return proc.returncode, json.loads(proc.stdout)


def accept_args(*pairs):
    return [a for p in pairs for a in ("--accept-js-candidate", p)]


class HistoricalRealImportRegressionTests(unittest.TestCase):
    """Restored historical scanner regressions (before t_effe42d4, test file
    lines 890-1388). Expected raw candidates are hardcoded, never derived from
    the scanner under test. Lexer-only state assertions are obsolete; their
    source fixtures and real imports survive here."""

    def refs(self, js):
        return [spec for spec, _, _ in pha._js_refs(js, "unit")]

    def assert_cases(self, cases):
        for name, (js, want) in cases.items():
            with self.subTest(case=name):
                self.assertEqual(self.refs(js), want)

    # original test_followup_quoted_module_export_names (lines 1051-1063)
    def test_quoted_module_export_names_raw_outputs(self):
        self.assert_cases({
            "import-quoted-name": ("import {\"name\" as x} from './real.js';", ["./real.js"]),
            "export-as-quoted": ("export {x as \"name\"} from './real.js';", ["./real.js"]),
            "export-quoted-both": ("export {'a b' as 'c d', \"e\"} from \"./q.js\";", ["./q.js"]),
            "export-star-as-quoted": ("export * as \"ns\" from './s.js';", ["./s.js"]),
            "minified": ('import{"a"as b}from"./m.js";export{b as"c"}from"./n.js"', ["./m.js", "./n.js"]),
            "quoted-name-content-not-scanned": ("import {\"./nope.js\" as y} from './k.js';", ["./k.js"]),
            # The closing quote of "from" opens a raw literal that runs to EOF:
            # its bounded raw text is kept (t_00a2629f), beside the real import.
            "quoted-from-lookalike": ("import {\"from\" as y} from './z.js';", ["as y} from './z.js';", "./z.js"]),
            # A double-quoted specifier after a quoted "from" name: the closing
            # quote of "from" opens a raw false candidate. Reported on purpose.
            "quoted-from-lookalike-double": ("import {\"from\" as y} from \"./z.js\";", ["as y} from", "./z.js"]),
            "quoted-from-lookalike-chain": ("import {\"from\" as y} from './z.js'; import \"./w.js\";",
                                            ["as y} from './z.js'; import", "./z.js", "./w.js"]),
            "export-as-quoted-from-double": ("export {x as \"from\"} from \"./z.js\";", ["} from", "./z.js"]),
            "export-quoted-from": ("export {\"from\"} from './z.js';", ["} from './z.js';", "./z.js"]),
        })

    def test_quoted_from_lookalike_cli_blocks_until_real_import_resolves(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<script type="module" src="app.js"></script>')
        write(b / "app.js", "import {\"from\" as y} from \"./z.js\";")
        code, doc = subprocess_plan(b)
        self.assertEqual(code, pha.EXIT_INVALID, doc)
        self.assertEqual(doc["errors"], ["app.js js import: missing local asset './z.js' (resolved 'z.js')"])
        self.assertEqual([r["ref"] for r in doc["unresolved"]], ["as y} from"])
        code, doc = subprocess_plan(b, *accept_args("app.js:as y} from"))
        self.assertEqual(code, pha.EXIT_INVALID, doc)
        self.assertFalse(doc["publishable"])
        self.assertEqual(doc["errors"], ["app.js js import: missing local asset './z.js' (resolved 'z.js')"])
        self.assertEqual(doc["unresolved"], [])
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "app.js", "specifier": "as y} from"}])
        write(b / "z.js", "export const y = 1;")
        code, doc = subprocess_plan(b)
        self.assertEqual((code, doc["publishable"]), (0, False), doc)
        code, doc = subprocess_plan(b, *accept_args("app.js:as y} from"))
        self.assertEqual((code, doc["publishable"]), (0, True), doc)

    # original test_template_interpolation_is_code_with_nested_templates_and_brace_balance
    # and test_template_object_division_and_escaped_interpolation_boundaries
    def test_nested_and_escaped_template_interpolation_raw_outputs(self):
        self.assert_cases({
            "nested-brace-balance": (
                'const s = `outer ${ { a: `inner ${ "}" + \'`\' } import "./nope.js"`, b: {c: 1} }.a } '
                'tail import "./nope2.js"`; import "./real.mjs";', ["./nope.js", "./nope2.js", "./real.mjs"]),
            "import-in-interp": ("const s = `x ${await import('./in-interp.mjs')} y ${`z ${ {k: 1}.k }`} "
                                 "import './nope.js'`;", ["./in-interp.mjs", "./nope.js"]),
            "escaped-interp": ("const s = `\\${import('./escaped.js')}`; import './after.mjs';",
                               ["./escaped.js", "./after.mjs"]),
            "object-division-in-interp": ("`${ {} / import('missing-package') / 2 }`", ["missing-package"]),
            "escape-before-interp": ("`\\a${import('missing-package')}`", ["missing-package"]),
            "template-in-object-in-interp": ("`${ {a:`${import('missing-package')}`} }`", ["missing-package"]),
            "escaped-interp-ghost": ("`\\${import('ghost')}`", ["ghost"]),
            "nested-templated-specifier": ("import(`./${`x${y}`}.mjs`);", ["./${"]),
            "templated-specifier": ("import(`./${name}.mjs`);", ["./${name}.mjs"]),
        })

    def test_nested_template_mixture_cli_accepts_only_false_candidates(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<script type="module" src="app.js"></script>')
        write(b / "app.js", 'const s = `outer ${ { a: `inner ${ "}" + \'`\' } import "./nope.js"`, b: {c: 1} }.a } '
                            'tail import "./nope2.js"`; import "./real.mjs"; import(`./${`x${y}`}.mjs`);')
        real = ["app.js js import: missing local asset './real.mjs' (resolved 'real.mjs')"]
        code, doc = subprocess_plan(b)
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertEqual(doc["errors"], ["app.js js import: missing local asset './nope.js' (resolved 'nope.js')",
                                         "app.js js import: missing local asset './nope2.js' (resolved 'nope2.js')",
                                         *real])
        self.assertEqual([r["ref"] for r in doc["unresolved"]], ["./${"])
        code, doc = subprocess_plan(b, *accept_args("app.js:./nope.js", "app.js:./nope2.js"))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertEqual(doc["errors"], real)
        self.assertEqual([r["ref"] for r in doc["unresolved"]], ["./${"])
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "app.js", "specifier": "./nope.js"},
                                                         {"file": "app.js", "specifier": "./nope2.js"}])
        self.assertFalse(doc["publishable"])

    # original test_string_escape_boundaries
    def test_string_escape_boundaries_raw_outputs(self):
        self.assert_cases({
            "escaped-single-quote": ("var s = 'it\\'s import \"./nope.js\"'; import './real.mjs';",
                                     ["./nope.js", "./real.mjs"]),
            "escaped-double-quote": ('var s = "say \\"import(\'./nope.js\')\\""; import "./real.mjs";',
                                     ["./nope.js", "./real.mjs"]),
            "escaped-backslash-ends-string": ('var s = "a\\\\"; import "./real.mjs";', ["./real.mjs"]),
            "escaped-backtick": ("var s = `\\`import './nope.js'\\``; import './real.mjs';",
                                 ["./nope.js", "./real.mjs"]),
        })

    # original test_followup_every_js_line_terminator_ends_line_comment and
    # test_followup_escaped_line_continuations_stay_inside_strings
    def test_line_terminators_and_escaped_continuations_raw_outputs(self):
        for name, term in {"LF": "\n", "CR": "\r", "CRLF": "\r\n", "LS": "\u2028", "PS": "\u2029"}.items():
            with self.subTest(terminator=name):
                self.assertEqual(self.refs(f'// comment{term}import("./missing.js")'), ["./missing.js"])
                self.assertEqual(self.refs(f"var s = 'a\\{term}import(\"./nope.js\")'; import './real.mjs';"),
                                 ["./nope.js", "./real.mjs"])
        self.assertEqual(self.refs("var s = 'raw \u2028 import(\"./nope.js\") \u2029'; import './real.mjs';"),
                         ["./nope.js", "./real.mjs"])

    def test_line_terminator_cli_blocks_and_accepts_only_string_candidate(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<script type="module" src="app.js"></script>')
        for name, term in {"LF": "\n", "CR": "\r", "CRLF": "\r\n", "LS": "\u2028", "PS": "\u2029"}.items():
            with self.subTest(terminator=name):
                (b / "app.js").write_bytes((f'// comment{term}import("./missing.js");'
                                            f"var s = 'a\\{term}import(\"./nope.js\")';").encode())
                code, doc = subprocess_plan(b)
                self.assertEqual(code, pha.EXIT_INVALID)
                self.assertEqual(sorted(doc["errors"]),
                                 ["app.js js import: missing local asset './missing.js' (resolved 'missing.js')",
                                  "app.js js import: missing local asset './nope.js' (resolved 'nope.js')"])
                code, doc = subprocess_plan(b, *accept_args("app.js:./nope.js"))
                self.assertEqual(code, pha.EXIT_INVALID)
                self.assertEqual(doc["errors"],
                                 ["app.js js import: missing local asset './missing.js' (resolved 'missing.js')"])
                self.assertEqual(doc["accepted_js_candidates"], [{"file": "app.js", "specifier": "./nope.js"}])

    # original test_regex_versus_division, test_followup_slash_after_object_and_function_expressions_is_division,
    # test_followup_regex_after_control_paren
    def test_regex_division_and_control_paren_raw_outputs(self):
        self.assert_cases({
            "division-around-import": ("x = a / b; import './real.mjs'; y = c / d;", ["./real.mjs"]),
            "postfix-division": ("x = y++ / 2; import './real.mjs'; z = 1 / 2;", ["./real.mjs"]),
            "paren-division": ("x = (a) / 2; import './real.mjs'; z = (b) / 3;", ["./real.mjs"]),
            "regex-with-quotes": ("var r = /['\"]/; import './real.mjs';", ["./real.mjs"]),
            "regex-class-slash": ("var r = /[/'`]/g; import './real.mjs';", ["./real.mjs"]),
            "regex-after-paren": ("if (/'/.test(s)) {} import './real.mjs';", ["./real.mjs"]),
            "regex-after-return": ("function f(s){return /import '.\\/nope.js'/.test(s)} import './real.mjs';",
                                   [".\\/nope.js", "./real.mjs"]),
            "regex-escaped-slash": ("var r = /a\\/'b/; import './real.mjs';", ["./real.mjs"]),
            "object-literal": ('const x = {} / import("./missing.js") / 2', ["./missing.js"]),
            "nested-object": ("const x = {a: {b: 1}} / import('./o.js') / 2", ["./o.js"]),
            "object-in-call": ("f({k: 1} / import('./c.js') / 2)", ["./c.js"]),
            "function-expression": ("x = function () {} / import('./f.js') / 2", ["./f.js"]),
            "named-function-expression": ("x = function g(a) { return a } / import('./g.js') / 2", ["./g.js"]),
            "block-then-regex": ("{} /import('.\\/nope.js')/g; import './real.mjs';", [".\\/nope.js", "./real.mjs"]),
            "function-declaration-then-regex": ("function f() {}\n/import('.\\/nope.js')/.test(s); import './real.mjs';",
                                                [".\\/nope.js", "./real.mjs"]),
            "arrow-body-then-regex": ("const f = () => {}\n/import('.\\/nope.js')/.test(s); import './r.mjs';",
                                      [".\\/nope.js", "./r.mjs"]),
            "if-block-then-regex": ("if (a) {} /import('.\\/nope.js')/.test(s); import './i.mjs';",
                                    [".\\/nope.js", "./i.mjs"]),
            "if": ('if (ok) /import("ghost")/.test(x); import("./real.js")', ["ghost", "./real.js"]),
            "while": ("while (a(b)) /import('ghost')/.exec(x); import('./w.js')", ["ghost", "./w.js"]),
            "for": ("for (;;) /import('ghost')/.exec(x); import('./f.js')", ["ghost", "./f.js"]),
            "with": ("with (o) /import('ghost')/.exec(x); import('./h.js')", ["ghost", "./h.js"]),
            "else-if": ("if (a) b(); else if (c) /import('ghost')/.exec(x); import('./e.js')", ["ghost", "./e.js"]),
            "call-paren-division": ("x = f(a) / import('./div.js') / 2", ["./div.js"]),
            "member-if-is-call": ("obj.if(a) / import('./m.js') / 2", ["./m.js"]),
            "optional-member-while": ("obj?.while(a) / import('./o.js') / 2", ["./o.js"]),
        })

    # original test_keyword_properties_and_identifier_boundaries + import-text-in-strings cases
    def test_keyword_properties_and_lexical_fixtures_raw_outputs(self):
        self.assert_cases({
            "member-import": ("a.import('./nope.js');", ["./nope.js"]),
            "optional-member-import": ("a?.import('./nope.js');", ["./nope.js"]),
            "member-export-from": ("lib.export * from './nope.js';", ["./nope.js"]),
            "keyword-keys": ("const o = { import: './nope.js', export: \"./nope2.js\" };", []),
            "identifier-boundaries": ("myimport('./nope.js'); import_('./nope.js'); $import('./nope.js');", []),
            "import-meta": ("const u = import.meta.url;", []),
            "export-const-from": ("export const from = './nope.js';", []),
            "from-call": ("export { a, b }\nfrom('./nope.js');", []),
            "keyword-array": ('var kw=["import","export","from"];', [",", "];"]),
            "concat-full": ("console.error('lazy: Expected the result of a dynamic import() call. ' + "
                            "'Instead received: %s\\n\\nYour code should look like: \\n  ' + "
                            "\"const MyComponent = lazy(() => import('./MyComponent'))\\n\\n\" + "
                            "'Did you accidentally put curly braces around the import?', moduleObject);",
                            ["./MyComponent"]),
        })

    LEXICAL_FIXTURES = {
        "single-string": ("var s = 'import \"./nope.js\"';", ["./nope.js"]),
        "double-string": ('var s = "import x from \'./nope.js\'";', ["./nope.js"]),
        "template-reexport": ("var s = `export * from './nope.js'`;", ["./nope.js"]),
        "template-dynamic": ("var s = `import('./nope.js')`;", ["./nope.js"]),
        "line-comment": ("// import './nope.js'\nvar a;", ["./nope.js"]),
        "block-comment": ("/* import x from './nope.js' */", ["./nope.js"]),
        "multiline-comment": ("/* multi\nline import('./nope.js')\n*/", ["./nope.js"]),
        "regex": ("var r = /import \"\\.\\/nope.js\"/g;", ["\\.\\/nope.js"]),
        "member-import": ("a.import('./nope.js'); a?.import('./nope2.js');", ["./nope.js", "./nope2.js"]),
        "member-export-from": ("lib.export * from './nope.js';", ["./nope.js"]),
        "keyword-array": ('var kw=["import","export","from"];', [",", "];"]),
        "escaped-interp-ghost": ("`\\${import('ghost')}`", ["ghost"]),
        "regex-after-await": ("async function f(){await /import('ghost')/}", ["ghost"]),
    }

    def test_lexical_exclusion_fixtures_need_explicit_exact_acceptance(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<script type="module" src="app.js"></script>')
        for name, (js, want) in self.LEXICAL_FIXTURES.items():
            with self.subTest(case=name):
                self.assertEqual(self.refs(js), want)
                write(b / "app.js", js)
                code, doc = run(base_args(b))
                self.assertFalse(doc["publishable"], doc)
                self.assertEqual(doc["accepted_js_candidates"], [])
                code, doc = run(base_args(b, *accept_args(*[f"app.js:{s}" for s in want])))
                self.assertEqual(code, 0, doc)
                self.assertTrue(doc["publishable"], doc)
                self.assertEqual(doc["errors"] + doc["unresolved"], [])
                self.assertEqual(doc["accepted_js_candidates"],
                                 [{"file": "app.js", "specifier": s} for s in sorted(want)])

    def test_real_imports_beside_single_quoted_warning_raw_outputs(self):
        js = (f"const w = {js_double(REACT_LAZY_WARNING)};\n"
              "import def, { a as b } from './static.mjs';\n"
              "import * as ns from \"./ns.mjs\";\n"
              "import './side.mjs';\n"
              "export * from './reexport.mjs';\n"
              "export { c as d } from \"./named.mjs\";\n"
              f"const e = {js_single(REACT_LAZY_WARNING)};\n"
              "const lazyMod = () => import('./dynamic.mjs');\n"
              "const tmplMod = () => import(`./plain-template.mjs`);\n")
        self.assertEqual(self.refs(js), ["./MyComponent", "./static.mjs", "./ns.mjs", "./side.mjs",
                                         "./reexport.mjs", "./named.mjs", "./dynamic.mjs", "./plain-template.mjs"])

    # original test_minified_one_line_mixture: full fixture, now with acceptance
    MINIFIED = ('import{a as b}from"./a.mjs";const e=' + js_double(REACT_LAZY_WARNING) +
                ";export*from'./b.mjs';var t=`x${y}import('./nope.js')`;import\"./c.mjs\";"
                "/*import'./nope2.js'*/export{q}from\"./d.mjs\";const f=()=>import(\"./e.mjs\");"
                "var r=/['\"/]/g;import'./f.mjs'")

    def test_minified_one_line_mixture_raw_and_acceptance(self):
        self.assertEqual(self.refs(self.MINIFIED), ["./a.mjs", "./MyComponent", "./b.mjs", "./nope.js", "./c.mjs",
                                                    "./nope2.js", "./d.mjs", "./e.mjs", "./f.mjs"])
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<script type="module" src="app.js"></script>')
        write(b / "app.js", self.MINIFIED)
        real = [f"app.js js import: missing local asset './{n}.mjs' (resolved '{n}.mjs')" for n in "abcdef"]
        code, doc = subprocess_plan(b)
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertEqual(len(doc["errors"]), 9, doc["errors"])
        false = ("app.js:./MyComponent", "app.js:./nope.js", "app.js:./nope2.js")
        code, doc = subprocess_plan(b, *accept_args(*false))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertEqual(doc["errors"], real)
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "app.js", "specifier": "./MyComponent"},
                                                         {"file": "app.js", "specifier": "./nope.js"},
                                                         {"file": "app.js", "specifier": "./nope2.js"}])
        for n in "abcdef":
            write(b / f"{n}.mjs", "export const q = 1;")
        code, doc = subprocess_plan(b, *accept_args(*false))
        self.assertEqual((code, doc["publishable"], doc["errors"]), (0, True, []))

    # original JsScannerRepairTests
    REPAIR_CASES = {
        "contextual-of": "const of=6; of / IMPORT / 2;",
        "member-return": "const obj={return:6}; obj.return / IMPORT / 2;",
        "member-new": "const r=stats.new/stats.total;IMPORT;const q=r/2;",
        "optional-member": "obj?.return / IMPORT / 2;",
        "number-dot": "x=1./IMPORT/2",
        "for-await": "async function f(){for await (const x of y) /'/.test(x); IMPORT}",
    }
    REPAIR_SPECS = {"missing": ("'./absent.js'", "./absent.js"),
                    "bare": ('"missing-package"', "missing-package"),
                    "templated": ("`./${name}.js`", "./${name}.js")}

    def test_repair_probes_exact_tuples(self):
        for name, pattern in self.REPAIR_CASES.items():
            for kind, (literal, spec) in self.REPAIR_SPECS.items():
                with self.subTest(case=name, kind=kind):
                    js = pattern.replace("IMPORT", f"import({literal})")
                    self.assertEqual(list(pha._js_refs(js, "repair")), [(spec, "module", "repair")])

    def test_repair_probes_fail_closed_through_subprocess_cli(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<script type="module" src="app.js"></script>')
        for name, pattern in self.REPAIR_CASES.items():
            for kind, (literal, spec) in self.REPAIR_SPECS.items():
                with self.subTest(case=name, kind=kind):
                    write(b / "app.js", pattern.replace("IMPORT", f"import({literal})"))
                    code, doc = subprocess_plan(b)
                    self.assertFalse(doc["publishable"] or doc["delivered"], doc)
                    self.assertEqual(code, pha.EXIT_INVALID if kind == "missing" else 0, doc)
                    if kind == "missing":
                        self.assertTrue(any(spec in e for e in doc["errors"]), doc)
                    else:
                        self.assertEqual([r["ref"] for r in doc["unresolved"]], [spec], doc)
                    remote = FakeRemote()
                    code, published = run(base_args(b, "--publish"), runner=remote.runner, fetch=remote.fetch)
                    self.assertEqual(code, pha.EXIT_INVALID, published)
                    self.assertEqual(remote.calls, [])

    def test_keyword_members_contextual_numeric_and_ambiguous_slashes(self):
        want = [("missing-package", "module", "repair")]
        for word in "return typeof instanceof in of new delete void throw case do else yield await".split():
            for member in (".", "?."):
                with self.subTest(word=word, member=member):
                    js = f"obj{member}/* member */{word} / import('missing-package') / 2"
                    self.assertEqual(list(pha._js_refs(js, "repair")), want)
        for expr in ("of", "await", "yield", "async", "1.", "1.0", ".5", "1.e2", "1e-2", "0xff", "0b11", "0o17",
                     "12n", "1_000.5", "obj.in", "identifier", "f()", "(x)", "a[0]", "x++", "x--", "obj.return"):
            with self.subTest(expr=expr):
                self.assertEqual(list(pha._js_refs(f"{expr} / import('missing-package') / 2", "repair")), want)
        self.assertEqual(list(pha._js_refs("async function f(){await /import('ghost')/}", "repair")),
                         [("ghost", "module", "repair")])

    def test_expression_prefix_regexes_are_raw_candidates_beside_real_import(self):
        for prefix in ("", "(", ",", "=", ":", "[", "!", "&", "|", "?", "{", ";", "+", "-", "*", "%", "<", ">",
                       "~", "^", "=>", "return ", "typeof ", "instanceof ", "in ", "delete ", "void ",
                       "throw ", "new ", "case ", "do ", "else "):
            with self.subTest(prefix=prefix):
                self.assertEqual(list(pha._js_refs(prefix + "/import('ghost')/; import('./real.js')", "repair")),
                                 [("ghost", "module", "repair"), ("./real.js", "module", "repair")])

    def test_failed_regex_candidates_have_linear_work_and_recover_import(self):
        class CountedText(str):
            reads = 0

            def __getitem__(self, key):
                self.reads += 1
                return super().__getitem__(key)

        for prefix in ("x=/[" * 50_000, "x=" + "a.in/[" * 30_000 + "0" + "]" * 30_000):
            js = CountedText(prefix + ";\nimport './real.js'")
            with self.subTest(bytes=len(js)):
                started = time.monotonic()
                self.assertEqual(list(pha._js_refs(js, "repair")), [("./real.js", "module", "repair")])
                self.assertLess(time.monotonic() - started, 8.0)
                self.assertLess(js.reads, 30 * len(js))

    def test_unterminated_regex_fallback_blocks_subprocess_cli(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<script src="app.js"></script>')
        write(b / "app.js", "x=/[" * 50_000 + ";\nimport('missing-package')")
        code, doc = subprocess_plan(b)
        self.assertEqual(code, 0, doc)
        self.assertFalse(doc["publishable"] or doc["delivered"], doc)
        self.assertEqual([r["ref"] for r in doc["unresolved"]], ["missing-package"])

    # obsolete lexer-state tests (state cap, union/merge, cap rollback): fixtures kept
    def test_former_lexer_state_fixtures_raw_outputs(self):
        self.assert_cases({
            "state-cap-template": ("`${await /x/;}`; const s = \"import('ghost')\"; import('./real.js');",
                                   ["ghost", "./real.js"]),
            "union": ("await /import('division')/; import('after');", ["division", "after"]),
            "merge": ("await /x/;" * 1000 + '"import(\'not-code\')"; import("after");', ["not-code", "after"]),
            "cap-rollback": ("const s=\"import('before')\"; await /x/; const t=\"import('after')\"; import('real');",
                             ["before", "after", "real"]),
        })

    def test_unterminated_regions_keep_real_imports_through_subprocess_cli(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<script src="app.js"></script>')
        for prefix in ("/*", "'", '"', "`", "/[", "await /'", "`${await /'"):
            js = prefix + '\nimport("missing-package"); import("./${name}.js");'
            with self.subTest(prefix=prefix):
                self.assertEqual(self.refs(js), ["missing-package", "./${name}.js"])
                write(b / "app.js", js)
                code, doc = subprocess_plan(b)
                self.assertFalse(doc["publishable"])
                self.assertEqual([r["ref"] for r in doc["unresolved"]], ["missing-package", "./${name}.js"])

    def test_statement_boundaries_through_subprocess_cli(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<script src="app.js"></script>')
        for prefix in ("a++\n", "try{}catch{}\n", "foo: {}\n", "async function f(){}\n",
                       "if(0){}else function f(){}\n"):
            for spec in ("./absent.js", "missing-package", "./${name}.js"):
                js = prefix + f"/'/.source; import({json.dumps(spec)}); q='z'"
                with self.subTest(prefix=prefix, spec=spec):
                    self.assertEqual(list(pha._js_refs(js, "asi")), [(spec, "module", "asi")])
                    write(b / "app.js", js)
                    code, doc = subprocess_plan(b)
                    self.assertFalse(doc["publishable"])

    def test_reviewer_adversarial_sizes_are_subsecond(self):
        for js, want in (("x=/[" * 50_000 + '\nimport("missing-package");', ["missing-package"]),
                         ("x=" + "a.in/[" * 50_000 + "0" + "]" * 50_000 + ';import("missing-package");',
                          ["missing-package"]),
                         ('const x="import(\'ghost\')";' * 50_000 + 'import("missing-package");',
                          ["ghost"] * 50_000 + ["missing-package"])):
            with self.subTest(size=len(js)):
                start = time.perf_counter()
                self.assertEqual(self.refs(js), want)
                self.assertLess(time.perf_counter() - start, 1.0)


# Original JsForkingLexerTests five-form matrix: 17 prefixes x 3 specs x 5
# forms + 12 divisions = 267 cases, every one through the real offline CLI.
MATRIX_PREFIXES = {
    "of": "const of=6; const x=of / 2;",
    "member": "const x=obj.return / 2;",
    "member-new": "const r=stats.new/stats.total;",
    "optional": "const x=obj?.return / 2;",
    "trailing-dot": "const x=1./2;",
    "for-await": "async function f(){for await(const x of y) /'/.test(x);}",
    "await-quote": "async function f(){await /'/;}",
    "yield-quote": "function* f(){yield /'/;}",
    "await-backtick": "async function f(){await /`/;}",
    "yield-backtick": "function* f(){yield /`/;}",
    "default": "export default /'/;",
    "for-of-quote": "for(const c of /'/[Symbol.split](\"a'b\")) ;",
    "for-of-escaped-slash": r"for(const c of /\/\//.exec('x//y') ?? []) ;",
    "for-of-comment": "for(const c of /[/*]/.exec('*') ?? []) ;\n",
    "await-comment": "async function f(){await /[/*]/;}\n",
    "await-line-comment": "async function f(){await /[//]/;}\n",
    "class": "const x=class{} / 2;",
}
MATRIX_SPECS = ("./absent.js", "missing-package", "./${name}.js")
MATRIX_DIVISIONS = ("const x=class{}", "const of=6; of", "obj.return", "1.")


def matrix_cases():
    for name, prefix in MATRIX_PREFIXES.items():
        for spec in MATRIX_SPECS:
            literal = json.dumps(spec)
            for form, clause in (("dynamic", f"import({literal});"), ("side-effect", f"import {literal};"),
                                 ("static", f"import importedModule from {literal};"),
                                 ("reexport", f"export * from {literal};"), ("template", f"import(`{spec}`);")):
                yield f"{name}/{spec}/{form}", prefix + clause, spec
    for prefix in MATRIX_DIVISIONS:
        for spec in MATRIX_SPECS:
            yield f"division:{prefix}/{spec}", prefix + f" / import(`{spec}`) / 2;", spec


class FiveFormMatrixTests(unittest.TestCase):

    def test_matrix_has_all_267_cases(self):
        cases = list(matrix_cases())
        self.assertEqual(len(cases), 267)
        self.assertEqual(len({name for name, _, _ in cases}), 267)

    def test_every_matrix_case_scanner_exact(self):
        for name, js, spec in matrix_cases():
            with self.subTest(case=name):
                self.assertEqual(list(pha._js_refs(js, "round3")), [(spec, "module", "round3")])

    def test_every_matrix_case_blocks_through_subprocess_offline_cli(self):
        b = Path(tempfile.mkdtemp())
        write(b / "index.html", '<script type="module" src="app.js"></script>')
        ran = 0
        for name, js, spec in matrix_cases():
            with self.subTest(case=name):
                write(b / "app.js", js)
                code, doc = subprocess_plan(b)
                ran += 1
                self.assertFalse(doc["publishable"], doc)
                self.assertFalse(doc["delivered"], doc)
                self.assertEqual(doc["accepted_js_candidates"], [])
                if spec == "./absent.js":
                    self.assertEqual(code, pha.EXIT_INVALID, doc)
                    self.assertEqual(doc["errors"],
                                     ["app.js js import: missing local asset './absent.js' (resolved 'absent.js')"])
                    self.assertEqual(doc["unresolved"], [])
                else:
                    self.assertEqual(code, 0, doc)
                    self.assertEqual(doc["errors"], [])
                    self.assertEqual([r["ref"] for r in doc["unresolved"]], [spec])
        self.assertEqual(ran, 267)


class HistoricalBundleCliTests(unittest.TestCase):
    """Original JsImportScannerBundleTests, adapted to raw candidates + acceptance."""

    def setUp(self):
        self.b = Path(tempfile.mkdtemp())
        write(self.b / "index.html", '<script type="module" src="app.js"></script>')
        write(self.b / "real.mjs", "export const x = 1;")

    def test_react_dev_bundle_blocks_until_exact_acceptance(self):
        write(self.b / "app.js",
              f"import {{x}} from './real.mjs';\nconsole.error({js_double(REACT_LAZY_WARNING)}, m);\n"
              f"console.error({js_single(REACT_LAZY_WARNING)}, m);\n"
              f"/* {REACT_LAZY_WARNING} */\nconst w = {js_template(REACT_LAZY_WARNING)};\n")
        write(self.b / "index.html",
              '<script type="module" src="app.js"></script>'
              f'<script type="module">console.error({js_single(REACT_LAZY_WARNING)});</script>')
        code, doc = run(base_args(self.b))
        self.assertEqual(code, pha.EXIT_INVALID, doc)
        self.assertEqual(doc["errors"], ["app.js js import: missing local asset './MyComponent' "
                                         "(resolved 'MyComponent')"] * 3)
        code, doc = run(base_args(self.b, *accept_args("app.js:./MyComponent")))
        self.assertEqual(code, 0, doc)
        self.assertEqual(doc["errors"] + doc["unresolved"], [])
        self.assertTrue(doc["publishable"])
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "app.js", "specifier": "./MyComponent"}])

    def test_real_missing_import_beside_warning_still_errors_with_acceptance(self):
        write(self.b / "app.js", f"const w = {js_double(REACT_LAZY_WARNING)};\nimport './gone.mjs';")
        code, doc = run(base_args(self.b))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertTrue(any("./gone.mjs" in e for e in doc["errors"]))
        code, doc = run(base_args(self.b, *accept_args("app.js:./MyComponent")))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertEqual(doc["errors"], ["app.js js import: missing local asset './gone.mjs' (resolved 'gone.mjs')"])
        write(self.b / "app.js", f"const w = {js_single(REACT_LAZY_WARNING)};\nconst m = () => import(`./gone2.mjs`);")
        code, doc = run(base_args(self.b))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertEqual(doc["errors"], ["app.js js import: missing local asset './gone2.mjs' (resolved 'gone2.mjs')"])

    def test_missing_dynamic_import_after_object_and_cr_comment_errors(self):
        write(self.b / "app.js", 'const x = {} / import("./missing.js") / 2;\n// c\rimport("./gone-cr.js")')
        code, doc = run(base_args(self.b))
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertEqual(doc["errors"],
                         ["app.js js import: missing local asset './missing.js' (resolved 'missing.js')",
                          "app.js js import: missing local asset './gone-cr.js' (resolved 'gone-cr.js')"])

    def test_templated_and_bare_imports_block_publish(self):
        cases = {
            "templated-backtick": ("const m = import(`./${name}.mjs`);", "./${name}.mjs"),
            "nested-templated-backtick": ("const m = import(`./${`x${y}`}.mjs`);", "./${"),
            "bare-static": ("import React from 'react';", "react"),
            "bare-dynamic": ("const m = import('lodash');", "lodash"),
        }
        for name, (js, ref) in cases.items():
            with self.subTest(case=name):
                write(self.b / "app.js", js)
                remote = FakeRemote()
                code, doc = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
                self.assertEqual(code, pha.EXIT_INVALID, doc)
                self.assertEqual(doc["failure"]["kind"], "unresolved_dependencies")
                self.assertEqual([r["ref"] for r in doc["unresolved"]], [ref])
                self.assertEqual(remote.calls, [])


# t_00a2629f: a backslash followed by a line terminator inside a quoted module
# specifier is a JS LineContinuation. Escaped CRLF is ONE continuation; before
# the repair the reader skipped backslash+CR, then dropped the candidate at LF
# and the CLI reported publishable=true. All 24 CRLF variants (4 forms x 3 deps
# x 2 quotes) are Node-valid; LF/CR/LS/PS continuations are controls. Raw text
# is kept (never decoded), so the backslash or ${ still blocks publication.
CONTINUATION_FORMS = {"side-effect": "import Q;", "binding": "import value from Q;",
                      "reexport": "export * from Q;", "dynamic": "import(Q);"}
CONTINUATION_DEPS = ("./gone.js", "missing-package", "./${name}.js")
CONTINUATION_TERMS = {"CRLF": "\r\n", "LF": "\n", "CR": "\r", "LS": "\u2028", "PS": "\u2029"}


def continuation_cases(term_name):
    term = CONTINUATION_TERMS[term_name]
    for form, clause in CONTINUATION_FORMS.items():
        for dep in CONTINUATION_DEPS:
            for quote in ("'", '"'):
                raw = dep[:4] + "\\" + term + dep[4:]
                yield f"{term_name}/{form}/{dep}/{quote}", clause.replace("Q", quote + raw + quote), dep, raw


class EscapedLineContinuationTests(unittest.TestCase):

    def setUp(self):
        self.b = Path(tempfile.mkdtemp())
        (self.b / "index.html").write_bytes(b'<script type="module" src="app.js"></script>')

    def assert_refused(self, code, doc, dep, raw, where="app.js js import"):
        self.assertFalse(doc["publishable"], doc)
        self.assertFalse(doc["delivered"], doc)
        self.assertEqual(doc["accepted_js_candidates"], [])
        if "${" in dep:
            self.assertEqual(code, 0, doc)
            self.assertEqual(doc["errors"], [])
            self.assertEqual([(r["origin"], r["ref"]) for r in doc["unresolved"]], [(where.split(" ", 1)[1], raw)])
        else:
            self.assertEqual(code, pha.EXIT_INVALID, doc)
            self.assertEqual(doc["errors"], [f"{where}: backslash in reference {raw!r}"])
            self.assertEqual(doc["unresolved"], [])

    def test_case_matrix_has_24_crlf_variants_and_96_controls(self):
        self.assertEqual(len(list(continuation_cases("CRLF"))), 24)
        self.assertEqual(sum(len(list(continuation_cases(t))) for t in ("LF", "CR", "LS", "PS")), 96)
        self.assertEqual(len({n for t in CONTINUATION_TERMS for n, _, _, _ in continuation_cases(t)}), 120)

    def test_escaped_crlf_scanner_keeps_raw_specifier(self):
        for name, js, dep, raw in continuation_cases("CRLF"):
            with self.subTest(case=name):
                self.assertIn("\\\r\n", js)
                self.assertEqual(list(pha._js_refs(js, "crlf")), [(raw, "module", "crlf")])

    def test_escaped_lf_cr_ls_ps_scanner_controls_keep_raw_specifier(self):
        for term in ("LF", "CR", "LS", "PS"):
            for name, js, dep, raw in continuation_cases(term):
                with self.subTest(case=name):
                    self.assertEqual(list(pha._js_refs(js, "ctl")), [(raw, "module", "ctl")])

    def test_escaped_crlf_blocks_through_subprocess_offline_cli(self):
        ran = 0
        for name, js, dep, raw in continuation_cases("CRLF"):
            with self.subTest(case=name):
                (self.b / "app.js").write_bytes(js.encode())
                self.assertIn(b"\\\r\n", (self.b / "app.js").read_bytes())
                code, doc = subprocess_plan(self.b)
                self.assert_refused(code, doc, dep, raw)
                remote = FakeRemote()
                code, published = run(base_args(self.b, "--publish"), runner=remote.runner, fetch=remote.fetch)
                kind = "unresolved_dependencies" if "${" in dep else "bundle_invalid"
                self.assertEqual((code, published["failure"]["kind"]), (pha.EXIT_INVALID, kind))
                self.assertEqual(remote.calls, [])
                ran += 1
        self.assertEqual(ran, 24)

    def test_escaped_lf_cr_ls_ps_controls_block_through_subprocess_offline_cli(self):
        ran = 0
        for term in ("LF", "CR", "LS", "PS"):
            for name, js, dep, raw in continuation_cases(term):
                with self.subTest(case=name):
                    (self.b / "app.js").write_bytes(js.encode())
                    self.assert_refused(*subprocess_plan(self.b), dep, raw)
                    ran += 1
        self.assertEqual(ran, 96)

    def test_inline_module_script_crlf_identity_is_containing_file(self):
        (self.b / "app.js").write_bytes(b"export const ok = 1;")
        ran = 0
        for name, js, dep, raw in continuation_cases("CRLF"):
            with self.subTest(case=name):
                (self.b / "index.html").write_bytes(
                    ('<script type="module" src="app.js"></script>\r\n<script type="module">\r\n'
                     + js + '\r\n</script>\r\n').encode())
                code, doc = subprocess_plan(self.b)
                self.assert_refused(code, doc, dep, raw, where="index.html inline script")
                if "${" in dep:
                    self.assertEqual([r["referrer"] for r in doc["unresolved"]], ["index.html"])
                ran += 1
        self.assertEqual(ran, 24)

    def test_raw_ls_ps_inside_specifier_close_normally(self):
        for term in ("\u2028", "\u2029"):
            with self.subTest(term=repr(term)):
                spec = f"./go{term}ne.js"
                js = f"import '{spec}';"
                self.assertEqual(list(pha._js_refs(js, "raw")), [(spec, "module", "raw")])
                (self.b / "app.js").write_bytes(js.encode())
                code, doc = subprocess_plan(self.b)
                self.assertEqual(code, pha.EXIT_INVALID, doc)
                self.assertFalse(doc["publishable"])
                self.assertEqual(doc["errors"], [f"app.js js import: missing local asset {spec!r} "
                                                 f"(resolved {spec[2:]!r})"])


class UnclosedLiteralFallbackTests(unittest.TestCase):
    """Once an opening quote is recognised the reader always yields bounded raw
    text. A literal that never closed (EOF, raw line break, MAX_JS_SPECIFIER,
    dangling escape) is uncertain: it is never silently publishable."""

    LONG = "a" * (pha.MAX_JS_SPECIFIER + 10)
    AT_LIMIT = "./" + "a" * (pha.MAX_JS_SPECIFIER - 2)
    # name: (js, scanner candidates, CLI errors, CLI unresolved refs)
    CASES = {
        "eof-missing": ("import './gone.js", ["./gone.js"],
                        ["app.js js import: missing local asset './gone.js' (resolved 'gone.js')"], []),
        "lf-cut": ("import './gone\n.js';", ["./gone"],
                   ["app.js js import: missing local asset './gone' (resolved 'gone')"], []),
        "cr-cut": ('import "./gone\r.js";', ["./gone"],
                   ["app.js js import: missing local asset './gone' (resolved 'gone')"], []),
        "crlf-cut-unescaped": ("export * from './gone\r\n.js';", ["./gone"],
                               ["app.js js import: missing local asset './gone' (resolved 'gone')"], []),
        "eof-bare": ("import('missing-package", ["missing-package"], [], ["missing-package"]),
        "eof-template": ("import(`./${name}.js", ["./${name}.js"], [], ["./${name}.js"]),
        "dangling-escape": ("import './gone\\", ["./gone\\"],
                            ["app.js js import: backslash in reference './gone\\\\'"], []),
        "dangling-escape-before-cr": ("import './gone\\\r", ["./gone\\"],
                                      ["app.js js import: backslash in reference './gone\\\\'"], []),
        "empty-lf": ("import '\nexport const x = 1;", [""], [], [""]),
        "empty-eof": ('import("', [""], [], [""]),
        "whitespace-only": ("import x from '  \r\n", [""], [], [""]),
        "existing-prefix": ("import './real.js\n", ["./real.js"], [], ["./real.js"]),
        "fragment-prefix": ("import x from '#frag\n", ["#frag"], [], ["#frag"]),
        "data-prefix-eof": ("import 'data:text/javascript,1", ["data:text/javascript,1"], [],
                            ["data:text/javascript,1"]),
        "limit-data": ("import 'data:text/javascript," + LONG + "'",
                       [("data:text/javascript," + LONG)[:pha.MAX_JS_SPECIFIER]], [],
                       [("data:text/javascript," + LONG)[:pha.MAX_JS_SPECIFIER]]),
        "limit-at-eof": ("import('" + AT_LIMIT, [AT_LIMIT],
                         [f"app.js js import: missing local asset {AT_LIMIT!r} (resolved {AT_LIMIT[2:]!r})"], []),
    }

    def setUp(self):
        self.b = Path(tempfile.mkdtemp())
        (self.b / "index.html").write_bytes(b'<script type="module" src="app.js"></script>')
        (self.b / "real.js").write_bytes(b"export const x = 1;")

    def test_reader_never_returns_none(self):
        closed = ("''", "'a'", "'./a\\\r\nb.js'")
        for text in ("'", "'abc", "'a\nb'", "'a\rb'", "'a\\", "'a\\\r", "`a${", "'" + self.LONG + "'", *closed):
            with self.subTest(text=text[:20]):
                raw = pha._js_literal(text, 0, [10 ** 9])
                self.assertIsInstance(raw, str)
                self.assertLessEqual(len(raw), pha.MAX_JS_SPECIFIER)
                self.assertEqual(isinstance(raw, pha._OpenJsLiteral), text not in closed)
        self.assertEqual(pha._js_literal("'./a\\\r\nb.js'", 0, [10 ** 9]), "./a\\\r\nb.js")

    def test_unclosed_reads_spend_budget_and_exhausted_budget_refuses(self):
        budget = [100]
        pha._js_literal("'abcdef\n", 0, budget)
        self.assertEqual(budget, [100 - 7])
        with self.assertRaises(pha.Failure) as c:
            pha._js_literal("'" + "a" * 50 + "\n", 0, [10])
        self.assertEqual(c.exception.kind, "bundle_invalid")

    def test_scanner_emits_bounded_raw_candidates(self):
        for name, (js, want, _, _) in self.CASES.items():
            with self.subTest(case=name):
                self.assertEqual(list(pha._js_refs(js, "fb")), [(w, "module", "fb") for w in want])

    def test_cli_never_publishes_unclosed_candidates_without_flags(self):
        for name, (js, _, errors, unresolved) in self.CASES.items():
            with self.subTest(case=name):
                (self.b / "app.js").write_bytes(js.encode())
                code, doc = subprocess_plan(self.b)
                self.assertFalse(doc["publishable"] or doc["delivered"], doc)
                self.assertEqual(code, pha.EXIT_INVALID if errors else 0, doc)
                self.assertEqual(doc["errors"], errors)
                self.assertEqual([r["ref"] for r in doc["unresolved"]], unresolved)
                self.assertEqual(doc["accepted_js_candidates"], [])

    def test_unclosed_resolving_prefix_is_waivable_only_exactly(self):
        (self.b / "app.js").write_bytes(b"import './real.js\n")
        code, doc = subprocess_plan(self.b)
        self.assertEqual((code, doc["publishable"]), (0, False), doc)
        self.assertIn("not closed", doc["unresolved"][0]["reason"])
        code, doc = subprocess_plan(self.b, *accept_args("app.js:./real.js "))
        self.assertEqual(code, pha.EXIT_INVALID, doc)
        self.assertFalse(doc["publishable"])
        code, doc = subprocess_plan(self.b, *accept_args("app.js:./real.js"))
        self.assertEqual((code, doc["publishable"], doc["errors"], doc["unresolved"]), (0, True, [], []), doc)
        self.assertEqual(doc["accepted_js_candidates"], [{"file": "app.js", "specifier": "./real.js"}])

    def test_unclosed_empty_candidate_cannot_be_waived(self):
        (self.b / "app.js").write_bytes(b"import '\n")
        code, doc = subprocess_plan(self.b)
        self.assertEqual((code, doc["publishable"], [r["ref"] for r in doc["unresolved"]]), (0, False, [""]), doc)
        code, doc = subprocess_plan(self.b, *accept_args("app.js:"))
        self.assertEqual((code, doc["failure"]["kind"]), (pha.EXIT_INVALID, "acceptance_invalid"))

    def test_closed_literal_next_to_unclosed_one_keeps_both(self):
        js = "import './real.js'; import './gone.js'; import('ghost\n"
        self.assertEqual([s for s, _, _ in pha._js_refs(js, "fb")], ["./real.js", "./gone.js", "ghost"])
        (self.b / "app.js").write_bytes(js.encode())
        code, doc = subprocess_plan(self.b)
        self.assertEqual(code, pha.EXIT_INVALID)
        self.assertEqual(doc["errors"], ["app.js js import: missing local asset './gone.js' (resolved 'gone.js')"])
        self.assertEqual([r["ref"] for r in doc["unresolved"]], ["ghost"])


REAL_REACT_BUNDLE = Path("/home/delorenj/code/gruvato/.design-sync/.cache/review-publish")


@unittest.skipUnless((REAL_REACT_BUNDLE / "_vendor/react.js").is_file(), "local React review bundle absent")
class RealReactBundleTests(unittest.TestCase):
    """Read-only offline plan of the real React review bundle (never published)."""

    def test_real_bundle_blocks_by_default_and_publishes_only_with_exact_acceptances(self):
        before = {p: p.stat().st_mtime_ns for p in REAL_REACT_BUNDLE.rglob("*")}
        code, doc = run(base_args(REAL_REACT_BUNDLE))
        self.assertEqual(code, pha.EXIT_INVALID, doc.get("failure"))
        self.assertTrue(any(e.startswith("_vendor/react.js js import: missing local asset './MyComponent'")
                            for e in doc["errors"]), doc["errors"])
        # Raw scanning also reports the closing-quote false positive in React's
        # 'passed a child from " + componentName2 + "."' warning; each needs its own waiver.
        # The inventory may grow (t_00a2629f keeps unclosed raw text such as the
        # ',' after `from: "from"`), so it is derived from this plan, not frozen.
        refs = [r["ref"] for r in doc["unresolved"]]
        self.assertIn("+ componentName2 +", refs)
        self.assertEqual(len(refs), len(set(refs)))
        code, doc = run(base_args(REAL_REACT_BUNDLE, "--accept-js-candidate", "_vendor/react.js:./MyComponent"))
        self.assertEqual(code, 0, doc.get("errors"))
        self.assertFalse(doc["publishable"])
        self.assertEqual([r["ref"] for r in doc["unresolved"]], refs)
        accepts = ["_vendor/react.js:./MyComponent", *[f"_vendor/react.js:{r}" for r in refs]]
        code, doc = run(base_args(REAL_REACT_BUNDLE, *[a for v in accepts for a in ("--accept-js-candidate", v)]))
        self.assertEqual(code, 0, doc.get("errors"))
        self.assertTrue(doc["publishable"], (doc["errors"], doc["unresolved"]))
        self.assertEqual(doc["accepted_js_candidates"],
                         [{"file": "_vendor/react.js", "specifier": s} for s in sorted({"./MyComponent", *refs})])
        self.assertEqual(before, {p: p.stat().st_mtime_ns for p in REAL_REACT_BUNDLE.rglob("*")})


if __name__ == "__main__":
    unittest.main()
