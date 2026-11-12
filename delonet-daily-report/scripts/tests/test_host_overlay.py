"""Genericization (W9-1): nothing a host owns lives in this skill's tracked files.

Each test pins one value to the overlay (environment, then ~/.config/33god/host.env)
or to a portable replacement: the mirror, the Resend key, the sender, the digest
footer, the s3 target, `~` in the config, and the nightly wrapper on a BSD userland.
"""
from __future__ import annotations

import copy
import json
import os
import re
import runpy
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from test_run_pipeline import PipelineCase, complete_collector, register_stub
from test_fixtures import config

import distribute  # noqa: E402
import hostsettings  # noqa: E402
import run as runner  # noqa: E402
from reportctl_config import validate_config  # noqa: E402
from reportctl_contracts import ConfigError  # noqa: E402

SCRIPTS = Path(__file__).resolve().parents[1]
SKILL = SCRIPTS.parent


def clean_env(**extra):
    """The environment with every host-overlay key removed, plus ``extra``."""
    base = {k: v for k, v in os.environ.items()
            if k not in ("DDR_MIRROR_DIR", "DDR_DIGEST_FOOTER", "DDR_MAIL_FROM", "DDR_CONFIG", "RESEND_API_KEY",
                         "RESEND_API_KEY_REF", "SECRET_RESOLVER", "HOST_ENV_FILE", "XDG_CONFIG_HOME")}
    base.update(extra)
    return base


class HostFile(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ddr-host-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.host_env = self.tmp / "host.env"

    def write(self, text):
        self.host_env.write_text(textwrap.dedent(text), encoding="utf-8")

    def env(self, **extra):
        return mock.patch.dict(os.environ, clean_env(HOST_ENV_FILE=str(self.host_env), **extra), clear=True)


class MirrorDir(HostFile):
    def test_no_default_means_no_mirror(self):
        with self.env():
            self.assertIsNone(runner.mirror_dir())
            self.assertIsNone(runner.mirror_target_text("2026-11-11"))

    def test_host_env_names_the_mirror(self):
        self.write('DDR_MIRROR_DIR="~/mirror dir"\n')
        with self.env():
            self.assertEqual(runner.mirror_dir(), Path("~/mirror dir").expanduser())
            self.assertEqual(runner.mirror_target_text("2026-11-11"), str(Path("~/mirror dir").expanduser() / "2026-11-11"))

    def test_environment_beats_the_file_even_to_disable_it(self):
        self.write("DDR_MIRROR_DIR=/from/file\n")
        with self.env(DDR_MIRROR_DIR="disabled"):
            self.assertIsNone(runner.mirror_dir())
        with self.env(DDR_MIRROR_DIR="/from/env"):
            self.assertEqual(runner.mirror_dir(), Path("/from/env"))

    def test_a_malformed_host_file_is_a_config_error_not_a_traceback(self):
        self.write("this is not dotenv\n")
        with self.env():
            with self.assertRaises(ConfigError):
                runner.mirror_dir()


class NoMirrorRuns(PipelineCase):
    """The latent bug: `str(mirror_dir() / date)` raised TypeError when a host has no mirror."""

    def setUp(self):
        super().setUp()
        self._env.stop()   # PipelineCase pins DDR_MIRROR_DIR; these runs have none
        self._none = mock.patch.dict(os.environ, clean_env(HOST_ENV_FILE=str(self.root / "absent.env")), clear=True)
        self._none.start()

    def tearDown(self):
        self._none.stop()
        self._env.start()
        super().tearDown()

    def two_ok(self):
        value = copy.deepcopy(self.value)
        value["sections"][0]["collector"] = register_stub("hov_a", complete_collector)
        value["sections"][1]["collector"] = register_stub("hov_b", complete_collector)
        return value

    def test_no_mirror_requested_on_a_host_without_one(self):
        outcome, code = self.run_pipeline(self.two_ok(), mirror=False)
        self.assertEqual(code, 0)
        self.assertIsNone(outcome["mirror"]["dir"])
        self.assertEqual(outcome["mirror"]["reason"], "mirror_disabled")

    def test_mirror_requested_but_the_host_has_none(self):
        outcome, code = self.run_pipeline(self.two_ok(), mirror=True)
        self.assertEqual(code, 0)
        self.assertIsNone(outcome["mirror"]["dir"])
        self.assertTrue(outcome["mirror"]["ok"])

    def test_an_unverified_generation_on_a_host_without_a_mirror_is_still_a_failed_run_not_a_crash(self):
        value = self.two_ok()
        with mock.patch.object(runner, "verify_published", return_value={
                "coherent": False, "ok": False, "problems": ["forced"], "generation": None, "generation_id": None}):
            outcome, code = self.run_pipeline(value)
        self.assertEqual(outcome["status"], "failed")
        self.assertIsNone(outcome["mirror"]["dir"])
        self.assertNotEqual(code, 0)


class HomeRelativeConfig(unittest.TestCase):
    def test_tilde_paths_become_absolute_and_absolute_paths_are_untouched(self):
        value = config(Path(tempfile.gettempdir()) / "ddr-x")
        value["artifact_dir"] = "~/state/ddr/artifacts"
        value["archive_dir"] = "~/state/ddr/archive"
        value["project_roots"] = ["~/code/a", "/opt/other"]
        out = validate_config(value)
        home = str(Path.home())
        self.assertEqual(out["artifact_dir"], home + "/state/ddr/artifacts")
        self.assertEqual(out["archive_dir"], home + "/state/ddr/archive")
        self.assertEqual(out["project_roots"], [home + "/code/a", "/opt/other"])

    def test_relative_paths_are_still_refused(self):
        for key, bad in (("artifact_dir", "relative/dir"), ("archive_dir", "also/relative")):
            value = config(Path(tempfile.gettempdir()) / "ddr-x")
            value[key] = bad
            with self.assertRaises(ConfigError):
                validate_config(value)
        value = config(Path(tempfile.gettempdir()) / "ddr-x")
        value["project_roots"] = ["rel/root"]
        with self.assertRaises(ConfigError):
            validate_config(value)

    def test_duplicates_are_caught_after_expansion(self):
        value = config(Path(tempfile.gettempdir()) / "ddr-x")
        value["project_roots"] = ["~/code/a", str(Path.home() / "code" / "a")]
        with self.assertRaises(ConfigError):
            validate_config(value)


class Delivery(HostFile):
    def mail_cfg(self, **over):
        cfg = {"enabled": True, "to": ["me@example.test"], "mode": "digest", "subject_template": "S {date} {status}"}
        cfg.update(over)
        return cfg

    def report(self):
        return {"report_date": "2026-11-11", "sections": [], "coverage": {"complete": [], "degraded": []}}

    def test_the_resend_key_comes_from_the_environment_first(self):
        self.write("RESEND_API_KEY_REF=env:SOME_VAR\n")
        with self.env(RESEND_API_KEY="re_direct", SOME_VAR="via-ref"):
            self.assertEqual(distribute.resend_api_key(), ("re_direct", ""))

    def test_the_resend_key_resolves_through_the_hosts_reference(self):
        self.write("RESEND_API_KEY_REF=env:SOME_VAR\n")
        with self.env(SOME_VAR="via-ref"):
            self.assertEqual(distribute.resend_api_key(), ("via-ref", ""))

    def test_no_key_anywhere_names_the_settings_and_never_a_value(self):
        with self.env():
            key, why = distribute.resend_api_key()
        self.assertIsNone(key)
        self.assertIn("RESEND_API_KEY_REF", why)

    def test_an_unresolvable_reference_names_the_ref(self):
        self.write("RESEND_API_KEY_REF=op://Vault/Item/credential\nSECRET_RESOLVER=interim\n")
        with self.env(PATH="/nonexistent", HOME=str(self.tmp)):
            key, why = distribute.resend_api_key()
        self.assertIsNone(key)
        self.assertIn("op://Vault/Item/credential", why)

    def test_a_target_without_a_sender_or_host_default_does_not_send(self):
        with self.env(RESEND_API_KEY="re_x"):
            d = distribute.deliver_mail("email", self.mail_cfg(), "md", self.report(), "complete", dry_run=False)
        self.assertFalse(d.ok)
        self.assertIn("DDR_MAIL_FROM", d.detail)

    def test_the_host_sender_is_used_when_the_target_has_none(self):
        self.write("DDR_MAIL_FROM=journal@host.test\n")
        sent = {}
        with self.env(RESEND_API_KEY="re_x"), mock.patch.object(
                distribute, "_send_resend", side_effect=lambda key, sender, to, subject, html=None, text=None: sent.update(sender=sender) or (True, "id=1")):
            d = distribute.deliver_mail("email", self.mail_cfg(), "md", self.report(), "complete", dry_run=False)
        self.assertTrue(d.ok)
        self.assertEqual(sent["sender"], "journal@host.test")

    def test_a_configured_sender_beats_the_host_default(self):
        self.write("DDR_MAIL_FROM=journal@host.test\n")
        sent = {}
        with self.env(RESEND_API_KEY="re_x"), mock.patch.object(
                distribute, "_send_resend", side_effect=lambda key, sender, to, subject, html=None, text=None: sent.update(sender=sender) or (True, "id=1")):
            distribute.deliver_mail("email", self.mail_cfg(**{"from": "cfg@x.test"}), "md", self.report(), "complete", dry_run=False)
        self.assertEqual(sent["sender"], "cfg@x.test")

    def test_the_digest_footer_is_the_hosts_and_defaults_to_neutral(self):
        with self.env():
            self.assertEqual(distribute.digest_lines(self.report(), "complete")[-1], "Full report: 2026-11-11")
        self.write('DDR_DIGEST_FOOTER="Read it at vault/{date}.md · there"\n')
        with self.env():
            self.assertEqual(distribute.digest_lines(self.report(), "complete")[-1], "Read it at vault/2026-11-11.md · there")

    def test_s3_without_a_target_is_a_failed_delivery_not_someone_elses_bucket(self):
        d = distribute.deliver_s3({}, "2026-11-11", "md", self.report(), "complete", "run-1", dry_run=False)
        self.assertFalse(d.ok)
        self.assertIn("distribution.s3.target", d.detail)

    def test_no_host_owned_literals_in_the_module(self):
        source = (SCRIPTS / "distribute.py").read_text(encoding="utf-8")
        for literal in ("delo.sh", "DeLoSecrets", "notebooklm", "wulyiisb24eht3wknd6ynf2nyy"):
            self.assertNotIn(literal, source)
        source = (SCRIPTS / "run.py").read_text(encoding="utf-8")
        self.assertNotIn("/home/delorenj", source)


class SiblingCopy(unittest.TestCase):
    def test_hostenv_is_byte_identical_to_the_activity_report_copy(self):
        sibling = SKILL.parent / "activity-report" / "scripts" / "ar" / "hostenv.py"
        if not sibling.exists():
            self.skipTest("activity-report not checked out beside this skill")
        self.assertEqual(sibling.read_bytes(), (SCRIPTS / "hostenv.py").read_bytes(),
                         "hostenv.py must stay byte-identical in both skills")


class PythonGuard(unittest.TestCase):
    def test_an_old_python_gets_a_sentence_not_an_attribute_error(self):
        old = (3, 9, 6, "final", 0)
        with mock.patch.object(sys, "version_info", old), self.assertRaises(SystemExit) as ctx, \
                mock.patch.object(sys, "stderr") as err:
            runpy.run_path(str(SCRIPTS / "reportctl"), run_name="not_main")
        self.assertEqual(ctx.exception.code, 2)
        written = "".join(call.args[0] for call in err.write.call_args_list)
        self.assertIn("needs Python 3.11", written)


class HostSettingsCli(HostFile):
    def run_cli(self, *args, env=None):
        return subprocess.run([sys.executable, str(SCRIPTS / "hostsettings.py"), *args], capture_output=True, text=True,
                              env=env or clean_env(HOST_ENV_FILE=str(self.host_env)))

    def test_get(self):
        self.write('A="two words"\nB=\n')
        self.assertEqual(self.run_cli("get", "A").stdout, "two words\n")
        self.assertEqual(self.run_cli("get", "B", "dflt").stdout, "dflt\n")
        proc = self.run_cli("get", "NOPE")
        self.assertEqual((proc.returncode, proc.stdout), (1, ""))
        self.assertEqual(self.run_cli("get").returncode, 2)

    def test_a_malformed_file_exits_2(self):
        self.write("garbage\n")
        proc = self.run_cli("get", "A")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("host.env", proc.stderr + str(self.host_env))


# --------------------------------------------------------------------------- nightly.sh

FAKE_REPORTCTL = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, sys
    argv = sys.argv[1:]
    state = os.environ["FAKE_STATE"]
    with open(os.path.join(state, "calls.log"), "a") as fh:
        fh.write(json.dumps(argv) + " mirror=" + os.environ.get("DDR_MIRROR_DIR", "<unset>") + "\\n")
    cmd = argv[2]
    def flag(name): return os.path.exists(os.path.join(state, name))
    def count(name):
        path = os.path.join(state, name)
        n = int(open(path).read()) if os.path.exists(path) else 0
        open(path, "w").write(str(n + 1))
        return n
    if cmd == "verify":
        # verified from the start, or only after a run that produced it
        ok = flag("verified") or (flag("ran") and not flag("run-fails-to-publish"))
        print(json.dumps({"ok": ok}))
        sys.exit(0 if ok else 3)
    if cmd == "run":
        open(os.path.join(state, "ran"), "w").write("1")
        sys.exit(int(open(os.path.join(state, "run-rc")).read()) if flag("run-rc") else 0)
    if cmd == "distribute":
        sys.exit(int(open(os.path.join(state, "dist-rc")).read()) if flag("dist-rc") else 0)
    sys.exit(9)
""")


class NightlyScript(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ddr-nightly-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        self.skill = self.tmp / "skill" / "scripts"
        self.state = self.tmp / "state"
        for d in (self.home / ".local" / "bin", self.skill, self.state):
            d.mkdir(parents=True)
        for name in ("nightly.sh", "hostsettings.py", "hostenv.py", "reportctl_contracts.py"):
            shutil.copy(SCRIPTS / name, self.skill / name)
        (self.skill / "reportctl").write_text(FAKE_REPORTCTL, encoding="utf-8")
        (self.skill / "reportctl").chmod(0o755)
        self.config = self.tmp / "report.json"
        self.config.write_text(json.dumps({"timezone": "Asia/Tokyo"}), encoding="utf-8")
        # macOS stand-in: a date that refuses GNU -d, first on PATH
        self.date_log = self.tmp / "date.log"
        bin_dir = self.home / ".local" / "bin"
        (bin_dir / "date").write_text(
            '#!/bin/bash\necho "$*" >> "%s"\nfor a in "$@"; do case "$a" in -d|--date|--date=*) echo "date: illegal option -- $a" >&2; exit 1;; esac; done\nexec /bin/date "$@"\n' % self.date_log,
            encoding="utf-8")
        (bin_dir / "date").chmod(0o755)

    def run_script(self, *args, flags=(), **env):
        for name in flags:
            if isinstance(name, tuple):
                (self.state / name[0]).write_text(str(name[1]))
            else:
                (self.state / name).write_text("1")
        full = clean_env(HOME=str(self.home), FAKE_STATE=str(self.state), DDR_CONFIG=str(self.config),
                         HOST_ENV_FILE=str(self.tmp / "absent.env"), PATH=f"{self.home}/.local/bin:" + os.environ["PATH"], **env)
        return subprocess.run(["bash", str(self.skill / "nightly.sh"), *args], env=full, capture_output=True, text=True, timeout=60)

    def calls(self):
        path = self.state / "calls.log"
        return [line for line in path.read_text().splitlines()] if path.exists() else []

    def cmds(self):
        return [json.loads(line.split(" mirror=")[0])[2] for line in self.calls()]

    def test_yesterday_is_in_the_configs_timezone_without_date_d(self):
        proc = self.run_script(flags=("verified",))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        import datetime as dt
        from zoneinfo import ZoneInfo
        expected = (dt.datetime.now(ZoneInfo("Asia/Tokyo")).date() - dt.timedelta(days=1)).isoformat()
        self.assertIn(f"Dev Journal {expected}: run=0 distribute=0", proc.stdout)
        self.assertNotIn("illegal option", proc.stdout + proc.stderr)
        self.assertFalse(self.date_log.exists() and re.search(r"(^|\s)-d", self.date_log.read_text()))

    def test_date_flag_pins_the_day(self):
        proc = self.run_script("nightly", "--date", "2026-01-02", flags=("verified",))
        self.assertIn("Dev Journal 2026-01-02: run=0 distribute=0", proc.stdout)
        self.assertTrue(all(json.loads(line.split(" mirror=")[0])[4] == "2026-01-02" for line in self.calls()))

    def test_scheduled_runs_never_write_the_git_tracked_mirror(self):
        self.run_script(flags=("verified",), DDR_MIRROR_DIR="/somewhere/tracked")
        self.assertTrue(all(line.endswith("mirror=disabled") for line in self.calls()))

    def test_nightly_verified_report_is_only_distributed(self):
        proc = self.run_script("nightly", flags=("verified",))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(self.cmds(), ["verify", "distribute"])

    def test_nightly_runs_when_unverified_then_distributes(self):
        proc = self.run_script("nightly")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(self.cmds(), ["verify", "run", "verify", "distribute"])

    def test_nightly_a_partial_run_that_verifies_is_a_success_even_if_run_exited_nonzero(self):
        proc = self.run_script("nightly", flags=(("run-rc", 3),))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("run=0", proc.stdout)

    def test_nightly_a_run_that_never_publishes_fails_even_if_it_exited_zero(self):
        proc = self.run_script("nightly", flags=("run-fails-to-publish",))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("run=1", proc.stdout)

    def test_nightly_a_failed_distribution_fails_the_job(self):
        proc = self.run_script("nightly", flags=("verified", ("dist-rc", 3)))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("distribute=3", proc.stdout)

    def test_ensure_verified_redelivers_best_effort_and_succeeds(self):
        proc = self.run_script("ensure", flags=("verified", ("dist-rc", 3)))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(self.cmds(), ["verify", "distribute"])

    def test_ensure_generates_then_delivers(self):
        proc = self.run_script("ensure")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(self.cmds(), ["verify", "run", "verify", "distribute"])

    def test_ensure_fails_when_the_run_still_leaves_nothing_verified(self):
        proc = self.run_script("ensure", flags=("run-fails-to-publish", ("run-rc", 3)))
        self.assertEqual(proc.returncode, 3)
        proc = self.run_script("ensure", flags=(("run-rc", 0),))
        self.assertEqual(proc.returncode, 1)

    def test_bad_arguments_and_missing_config(self):
        self.assertEqual(self.run_script("--bogus").returncode, 2)
        self.assertEqual(self.run_script("--date").returncode, 2)
        self.config.unlink()
        proc = self.run_script()
        self.assertEqual(proc.returncode, 2)
        self.assertIn("DDR_CONFIG", proc.stderr)

    def test_the_config_path_can_come_from_host_env(self):
        host = self.tmp / "host.env"
        host.write_text(f'DDR_CONFIG="{self.config}"\n', encoding="utf-8")
        env = clean_env(HOME=str(self.home), FAKE_STATE=str(self.state), HOST_ENV_FILE=str(host))
        (self.state / "verified").write_text("1")
        proc = subprocess.run(["bash", str(self.skill / "nightly.sh"), "--date", "2026-01-02"], env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_runs_through_a_symlink(self):
        link = self.home / ".local" / "bin" / "ddr-nightly"
        link.symlink_to(self.skill / "nightly.sh")
        (self.state / "verified").write_text("1")
        env = clean_env(HOME=str(self.home), FAKE_STATE=str(self.state), DDR_CONFIG=str(self.config), HOST_ENV_FILE=str(self.tmp / "none"))
        proc = subprocess.run(["bash", str(link), "--date", "2026-01-02"], env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_syntax_under_bash_3_2_features_only(self):
        body = (SCRIPTS / "nightly.sh").read_text(encoding="utf-8")
        for banned in ("declare -A", "mapfile", "readarray", "${var,,}", "date -d", "readlink -f", "timeout ", "flock", "sed -i", "jq "):
            self.assertNotIn(banned, body)
        self.assertEqual(subprocess.run(["bash", "-n", str(SCRIPTS / "nightly.sh")]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
