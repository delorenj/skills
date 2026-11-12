"""ar-timeout.py: the timeout(1) stand-in run.sh uses when a host has neither timeout nor gtimeout."""
import os
import subprocess
import sys
import time
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ar-timeout.py")


def run(*args, **kw):
    start = time.monotonic()
    proc = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, timeout=30, **kw)
    return proc, time.monotonic() - start


class ArTimeout(unittest.TestCase):
    def test_passes_the_exit_status_through(self):
        self.assertEqual(run("5", "sh", "-c", "exit 7")[0].returncode, 7)
        self.assertEqual(run("5s", "true")[0].returncode, 0)
        self.assertEqual(run("1m", "true")[0].returncode, 0)

    def test_times_out_with_124(self):
        proc, took = run("1", "sleep", "20")
        self.assertEqual(proc.returncode, 124)
        self.assertLess(took, 10)

    def test_kill_after_escalates_to_sigkill_with_137(self):
        proc, took = run("--kill-after=1s", "1s", "sh", "-c", "trap '' TERM; sleep 20")
        self.assertEqual(proc.returncode, 137)
        self.assertLess(took, 15)

    def test_the_whole_process_group_is_signalled(self):
        marker = f"/tmp/ar-timeout-child-{os.getpid()}"
        proc, _ = run("1", "sh", "-c", f"sleep 30 & echo $! > {marker}; wait")
        self.assertEqual(proc.returncode, 124)
        with open(marker, encoding="utf-8") as fh:
            pid = int(fh.read())
        os.unlink(marker)
        time.sleep(0.5)
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_usage_errors_and_missing_commands(self):
        self.assertEqual(run()[0].returncode, 125)
        self.assertEqual(run("abc", "true")[0].returncode, 125)
        self.assertEqual(run("5", "ar-no-such-command-xyz")[0].returncode, 127)

    def test_stdout_is_untouched(self):
        proc, _ = run("5", "echo", "hello")
        self.assertEqual(proc.stdout, "hello\n")


if __name__ == "__main__":
    unittest.main()
