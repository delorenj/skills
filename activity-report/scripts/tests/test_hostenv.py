"""The per-host overlay and the secret chain: parsing, precedence, and what never leaks."""
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import hostenv  # noqa: E402
from ar.host import gateway_settings  # noqa: E402
from ar.common import ConfigError  # noqa: E402

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = "op://Vault/Some Item/field"


class Parse(unittest.TestCase):
    def test_forms(self):
        text = textwrap.dedent("""\
            # a comment
            PLAIN=value
            export EXPORTED=yes
            SPACED = padded value   # trailing comment
            DQ="a \\"quoted\\" value # not a comment"
            SQ='literal $HOME \\n'
            EMPTY=
            URL=https://example.test/a#frag
            """)
        got = hostenv.parse_env_text(text)
        self.assertEqual(got["PLAIN"], "value")
        self.assertEqual(got["EXPORTED"], "yes")
        self.assertEqual(got["SPACED"], "padded value")
        self.assertEqual(got["DQ"], 'a "quoted" value # not a comment')
        self.assertEqual(got["SQ"], "literal $HOME \\n")      # never expanded, never sourced
        self.assertEqual(got["EMPTY"], "")
        self.assertEqual(got["URL"], "https://example.test/a#frag")   # '#' needs whitespace before it to start a comment

    def test_malformed_lines_name_the_line_and_never_the_value(self):
        for bad in ("no equals sign here", "1BAD=x", 'OPEN="never closed SECRETVALUE'):
            with self.assertRaises(hostenv.HostEnvError) as ctx:
                hostenv.parse_env_text("OK=1\n" + bad + "\n", "host.env")
            self.assertIn("host.env:2", str(ctx.exception))
            self.assertNotIn("SECRETVALUE", str(ctx.exception))

    def test_a_command_substitution_is_just_text(self):
        marker = os.path.join(tempfile.gettempdir(), "ar-hostenv-should-not-exist")
        got = hostenv.parse_env_text(f"X=$(touch {marker})\nY=`touch {marker}`\n")
        self.assertFalse(os.path.exists(marker))
        self.assertTrue(got["X"].startswith("$("))


class Precedence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ar-hostenv-")
        self.path = os.path.join(self.tmp, "host.env")
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("A=from-file\nB=from-file\nSECRET_RESOLVER=interim\n")
        self.env = {"HOST_ENV_FILE": self.path, "A": "from-env", "B": ""}

    def test_env_wins_and_an_empty_value_is_unset(self):
        self.assertEqual(hostenv.host_value("A", env=self.env), "from-env")
        self.assertEqual(hostenv.host_value("B", env=self.env), "from-file")
        self.assertEqual(hostenv.host_value("C", "dflt", env=self.env), "dflt")
        self.assertIsNone(hostenv.host_value("C", env=self.env))

    def test_absent_file_is_empty(self):
        self.assertEqual(hostenv.load_host_env(env={"HOST_ENV_FILE": os.path.join(self.tmp, "none")}), {})

    def test_path_resolution(self):
        self.assertEqual(hostenv.host_env_path({"HOST_ENV_FILE": "~/x.env"}), os.path.expanduser("~/x.env"))
        self.assertEqual(hostenv.host_env_path({"XDG_CONFIG_HOME": "/cfg"}), "/cfg/33god/host.env")
        self.assertEqual(hostenv.host_env_path({}), os.path.expanduser("~/.config/33god/host.env"))

    def test_gateway_settings_and_a_bad_resolver(self):
        got = gateway_settings(env=dict(self.env, ACTIVITY_REPORT_GATEWAY_URL="https://g.test"))
        self.assertEqual(got["gateway_url"], "https://g.test")
        self.assertIsNone(got["gateway_route"])
        self.assertEqual(got["resolver"], "interim")
        with self.assertRaises(ConfigError):
            gateway_settings(env=dict(self.env, SECRET_RESOLVER="vault"))


class Secrets(unittest.TestCase):
    """op is a fake on PATH; env-op-resolve is the REAL resolver against a scratch store."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ar-secret-")
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        self.op_log = os.path.join(self.tmp, "op.log")
        self.write_op(0, "from-op")
        self.base = {"PATH": self.bin + os.pathsep + "/usr/bin:/bin", "HOME": self.tmp, "HOST_ENV_FILE": os.path.join(self.tmp, "none"),
                     "OP_LOG": self.op_log}

    def write_op(self, rc, value):
        path = os.path.join(self.bin, "op")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f'#!/bin/sh\necho "$@" >> "$OP_LOG"\n[ {rc} -eq 0 ] && printf %s "{value}"\nexit {rc}\n')
        os.chmod(path, 0o755)

    def install_resolver(self):
        """The real env-op-resolve, if this checkout sits beside the delonet-dotenv skill; else a faithful stand-in."""
        sibling = os.path.join(os.path.dirname(os.path.dirname(SCRIPTS)), "delonet-dotenv", "scripts", "env-op-resolve.py")
        target = os.path.join(self.bin, "env-op-resolve")
        if os.path.exists(sibling):
            with open(sibling, encoding="utf-8") as src, open(target, "w", encoding="utf-8") as dst:
                dst.write(src.read())
            os.chmod(target, 0o755)
            return True
        return False

    def seed_store(self, value="from-store"):
        cfg = os.path.join(self.tmp, ".config", "33god")
        os.makedirs(cfg, exist_ok=True)
        key = "OP_VAULT_SOME_ITEM_FIELD"
        with open(os.path.join(cfg, "secrets.env"), "w", encoding="utf-8") as fh:
            fh.write(f"{key}={value}\n")
        os.chmod(os.path.join(cfg, "secrets.env"), 0o600)
        with open(os.path.join(cfg, "refmap.tsv"), "w", encoding="utf-8") as fh:
            fh.write(f"{REF}\t{key}\n")

    def test_env_ref(self):
        self.assertEqual(hostenv.resolve_secret("env:TOK", env={"TOK": " v "}), "v")
        with self.assertRaises(hostenv.SecretError) as ctx:
            hostenv.resolve_secret("env:NOPE", env={})
        self.assertIn("NOPE", str(ctx.exception))

    def test_a_literal_is_refused_and_not_echoed_back(self):
        with self.assertRaises(hostenv.SecretError) as ctx:
            hostenv.resolve_secret("sk-live-abcdef", env={})
        # strict: the first cut echoed it as `'sk-live-abcdef': not an op://...` and this test
        # stripped the quoted form before looking, so it passed over the leak.
        self.assertNotIn("sk-live-abcdef", str(ctx.exception))

    def test_op_mode(self):
        with mock.patch.dict(os.environ, self.base, clear=True):
            self.assertEqual(hostenv.resolve_secret(REF, env=dict(os.environ, SECRET_RESOLVER="op")), "from-op")
        with open(self.op_log, encoding="utf-8") as fh:
            self.assertEqual(fh.read().strip(), f"read {REF}")

    def test_auto_falls_back_to_the_interim_store_when_op_fails(self):
        if not self.install_resolver():
            self.skipTest("delonet-dotenv skill not checked out beside this skill")
        self.write_op(1, "")
        self.seed_store()
        with mock.patch.dict(os.environ, self.base, clear=True):
            self.assertEqual(hostenv.resolve_secret(REF), "from-store")

    def test_interim_mode_never_calls_op(self):
        if not self.install_resolver():
            self.skipTest("delonet-dotenv skill not checked out beside this skill")
        self.seed_store()
        with mock.patch.dict(os.environ, dict(self.base, SECRET_RESOLVER="interim"), clear=True):
            self.assertEqual(hostenv.resolve_secret(REF), "from-store")
        self.assertFalse(os.path.exists(self.op_log))

    def test_interim_fails_closed_naming_the_ref_not_a_value(self):
        if not self.install_resolver():
            self.skipTest("delonet-dotenv skill not checked out beside this skill")
        self.seed_store(value="TOPSECRETVALUE")
        other = "op://Vault/Other/field"
        with mock.patch.dict(os.environ, dict(self.base, SECRET_RESOLVER="interim"), clear=True):
            with self.assertRaises(hostenv.SecretError) as ctx:
                hostenv.resolve_secret(other)
        self.assertIn(other, str(ctx.exception))
        self.assertNotIn("TOPSECRETVALUE", str(ctx.exception))

    def test_interim_leaves_no_ref_file_behind(self):
        if not self.install_resolver():
            self.skipTest("delonet-dotenv skill not checked out beside this skill")
        self.seed_store()
        tmpdir = os.path.join(self.tmp, "t")
        os.makedirs(tmpdir)
        with mock.patch.dict(os.environ, dict(self.base, SECRET_RESOLVER="interim", TMPDIR=tmpdir), clear=True):
            hostenv.resolve_secret(REF)
        self.assertEqual(os.listdir(tmpdir), [])

    def test_no_resolver_anywhere_is_an_error_that_lists_what_was_tried(self):
        with mock.patch.dict(os.environ, {"PATH": "/nonexistent", "HOME": self.tmp, "HOST_ENV_FILE": os.path.join(self.tmp, "none")}, clear=True):
            with self.assertRaises(hostenv.SecretError) as ctx:
                hostenv.resolve_secret(REF)
        self.assertIn("SECRET_RESOLVER=auto", str(ctx.exception))
        self.assertIn("interim", str(ctx.exception))

    def test_cli_secret_read_prints_only_the_value(self):
        env = dict(self.base, SECRET_RESOLVER="op")
        proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, "activity-report"), "secret", "read", "--ref", REF],
                              env=env, capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "from-op\n", ""))
        self.write_op(1, "")
        proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, "activity-report"), "secret", "read", "--ref", REF],
                              env=env, capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (2, ""))
        self.assertIn(REF, proc.stderr)


class Mirror(unittest.TestCase):
    def test_identical_to_the_sibling_skill_copy(self):
        sibling = os.path.join(os.path.dirname(os.path.dirname(SCRIPTS)), "delonet-daily-report", "scripts", "hostenv.py")
        if not os.path.exists(sibling):
            self.skipTest("delonet-daily-report not checked out beside this skill")
        with open(sibling, "rb") as a, open(os.path.join(SCRIPTS, "ar", "hostenv.py"), "rb") as b:
            self.assertEqual(a.read(), b.read(), "hostenv.py must stay byte-identical in both skills")


if __name__ == "__main__":
    unittest.main()
