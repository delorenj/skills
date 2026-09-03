import contextlib
import io
import os
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import schedule  # noqa: E402
from ar.common import ConfigError  # noqa: E402


def project(at="03:30", tz="America/New_York", slug="james-brennan"):
    return types.SimpleNamespace(slug=slug, tz=tz, config={"schedule": {"at": at}})


class Dropin(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(schedule.render_dropin(project()), "[Timer]\nOnCalendar=\nOnCalendar=*-*-* 03:30:00 America/New_York\n")

    def test_bad_time(self):
        for at in ("3:30", "25:00", "", None):
            with self.assertRaises(ConfigError):
                schedule.render_dropin(project(at=at))

    def test_names(self):
        self.assertEqual(schedule.timer_name("x"), "activity-report@x.timer")
        self.assertEqual(schedule.service_name("x"), "activity-report@x.service")
        self.assertEqual(schedule.dropin_path("x", "/u"), "/u/activity-report@x.timer.d/schedule.conf")


class Templates(unittest.TestCase):
    def test_units_exist_and_carry_the_plan(self):
        with open(os.path.join(schedule.ASSETS_SYSTEMD, "activity-report@.service"), encoding="utf-8") as fh:
            service = fh.read()
        with open(os.path.join(schedule.ASSETS_SYSTEMD, "activity-report@.timer"), encoding="utf-8") as fh:
            timer = fh.read()
        for line in ("Type=oneshot", "ExecStart=%h/.local/bin/activity-report run --project %i", "TimeoutStartSec=90min",
                     "Nice=10", "IOSchedulingClass=idle", "WantedBy=default.target", "After=network-online.target",
                     "Environment=PATH=%h/.local/bin:%h/.local/share/mise/shims:/usr/local/bin:/usr/bin:/bin"):
            self.assertIn(line, service, line)
        for line in ("OnCalendar=*-*-* 03:00:00 America/New_York", "Persistent=true", "AccuracySec=1min",
                     "Unit=activity-report@%i.service", "WantedBy=timers.target"):
            self.assertIn(line, timer, line)

    def test_install_units_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sorted(schedule.install_units(tmp)), sorted(schedule.UNITS))
            self.assertEqual(schedule.install_units(tmp), [])
            with open(os.path.join(tmp, "activity-report@.timer"), "a", encoding="utf-8") as fh:
                fh.write("# drift\n")
            self.assertEqual(schedule.install_units(tmp), ["activity-report@.timer"])
            self.assertEqual(oct(os.stat(os.path.join(tmp, "activity-report@.timer")).st_mode & 0o777), "0o644")


class InstallTimer(unittest.TestCase):
    def run_install(self, home, cfg, shim=True):
        if shim:
            os.makedirs(os.path.join(home, ".local", "bin"), exist_ok=True)
            with open(os.path.join(home, ".local", "bin", "activity-report"), "w", encoding="utf-8") as fh:
                fh.write("#!/bin/sh\n")
        calls = []

        def fake_systemctl(*args):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, stdout="NEXT LEFT LAST PASSED UNIT ACTIVATES\n", stderr="")
        buf = io.StringIO()
        with mock.patch.dict(os.environ, {"HOME": home, "XDG_CONFIG_HOME": cfg}), \
                mock.patch.object(schedule, "_systemctl", side_effect=fake_systemctl), \
                mock.patch.object(schedule, "_linger_enabled", return_value=True), \
                mock.patch("ar.config.load_project", return_value=project()), \
                contextlib.redirect_stdout(buf):
            rc = schedule.install_timer_cmd(types.SimpleNamespace(project="james-brennan", json=False))
        return rc, calls, buf.getvalue()

    def test_installs_dropin_and_enables(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as cfg:
            rc, calls, out = self.run_install(home, cfg)
            self.assertEqual(rc, 0)
            user_dir = os.path.join(cfg, "systemd", "user")
            self.assertTrue(os.path.exists(os.path.join(user_dir, "activity-report@.service")))
            with open(os.path.join(user_dir, "activity-report@james-brennan.timer.d", "schedule.conf"), encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "[Timer]\nOnCalendar=\nOnCalendar=*-*-* 03:30:00 America/New_York\n")
            self.assertEqual(calls[0], ("daemon-reload",))
            self.assertEqual(calls[1], ("enable", "--now", "activity-report@james-brennan.timer"))
            self.assertEqual(calls[2][:2], ("list-timers", "activity-report@james-brennan.timer"))
            self.assertIn("enabled activity-report@james-brennan.timer", out)

    def test_requires_shim(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as cfg:
            with self.assertRaises(ConfigError):
                self.run_install(home, cfg, shim=False)


class TimerStatus(unittest.TestCase):
    def test_not_installed(self):
        with tempfile.TemporaryDirectory() as cfg:
            buf = io.StringIO()
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": cfg}), \
                    mock.patch.object(schedule, "_systemctl", return_value=subprocess.CompletedProcess([], 0, stdout="", stderr="")), \
                    mock.patch("shutil.which", return_value=None), \
                    mock.patch("ar.config.load_project", return_value=project()), \
                    contextlib.redirect_stdout(buf):
                rc = schedule.timer_status_cmd(types.SimpleNamespace(project="james-brennan", json=False))
            self.assertEqual(rc, 0)
            self.assertIn("not installed", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
