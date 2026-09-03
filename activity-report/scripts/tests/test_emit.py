import contextlib
import io
import json
import os
import sys
import tempfile
import textwrap
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import emit  # noqa: E402
from ar.common import AcceptanceError, ConfigError, ContractError  # noqa: E402

FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "publish")

FAKE_EMITTER = textwrap.dedent("""\
    import json, os, sys
    rec = {"argv": sys.argv[1:], "stdin": sys.stdin.read()}
    with open(os.environ["FAKE_EMIT_LOG"], "a") as fh:
        fh.write(json.dumps(rec) + "\\n")
    if "--check" in sys.argv:
        print("PASS bloodbank.project.activity.recorded")
        print("bb-emit: --check, nothing published", file=sys.stderr)
        sys.exit(int(os.environ.get("FAKE_CHECK_RC", "0")))
    print("bb-emit: published bloodbank.project.activity.recorded -> bloodbank.evt.project.activity.recorded (corr=4c1f2e8a)", file=sys.stderr)
    sys.exit(int(os.environ.get("FAKE_PUBLISH_RC", "0")))
""")


def load(name):
    with open(os.path.join(FX, name), encoding="utf-8") as fh:
        return json.load(fh)


class FakeBloodbank:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(self.tmp.name, "bin"))
        self.path = os.path.join(self.tmp.name, "bin", "bb-emit")
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(FAKE_EMITTER)
        self.log = os.path.join(self.tmp.name, "calls.jsonl")
        self.env = mock.patch.dict(os.environ, {"BLOODBANK_ROOT": self.tmp.name, "FAKE_EMIT_LOG": self.log,
                                                "FAKE_CHECK_RC": "0", "FAKE_PUBLISH_RC": "0"})
        self.env.start()

    def calls(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def close(self):
        self.env.stop()
        self.tmp.cleanup()


class Args(unittest.TestCase):
    def test_check_and_publish_argv(self):
        data = load("a5-internal.event.json")
        common = ["--type", "bloodbank.project.activity.recorded", "--source", "urn:33god:skill:activity-report",
                  "--producer", "activity-report", "--service", "activity-report", "--actor-type", "service",
                  "--actor-id", "bloodbank.skill.activity-report", "--correlation", data["generator"]["run_id"],
                  "--ordering-key", "project:" + data["project"]["slug"]]
        self.assertEqual(emit.emit_args(data, check=True), ["--check"] + common)
        self.assertEqual(emit.emit_args(data, check=False), common + ["--strict"])


class FindEmitter(unittest.TestCase):
    def test_order(self):
        fake = FakeBloodbank()
        try:
            self.assertEqual(emit.find_emitter()[1], fake.path)
        finally:
            fake.close()
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"BLOODBANK_ROOT": os.path.join(tmp, "none")}), \
                    mock.patch.object(emit, "DEFAULT_BLOODBANK", os.path.join(tmp, "none2")), \
                    mock.patch("shutil.which", return_value=None):
                with self.assertRaises(ConfigError):
                    emit.find_emitter()
            with mock.patch.dict(os.environ, {"BLOODBANK_ROOT": os.path.join(tmp, "none")}), \
                    mock.patch.object(emit, "DEFAULT_BLOODBANK", os.path.join(tmp, "none2")), \
                    mock.patch("shutil.which", return_value="/usr/bin/bb"):
                self.assertEqual(emit.find_emitter(), ["/usr/bin/bb", "emit"])


class Emit(unittest.TestCase):
    def setUp(self):
        self.fake = FakeBloodbank()
        self.addCleanup(self.fake.close)
        self.data = load("a5-internal.event.json")

    def test_dry_run_checks_only(self):
        record = emit.emit(self.data, dry_run=True)
        calls = self.fake.calls()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["argv"][0], "--check")
        self.assertEqual(json.loads(calls[0]["stdin"]), self.data)
        self.assertEqual(record["check"]["rc"], 0)
        self.assertIn("PASS", record["check"]["stdout"])
        self.assertIsNone(record["publish"])
        self.assertTrue(record["dry_run"])
        self.assertEqual(record["ordering_key"], "project:" + self.data["project"]["slug"])

    def test_publish_after_check(self):
        record = emit.emit(self.data, dry_run=False)
        calls = self.fake.calls()
        self.assertEqual(len(calls), 2)
        self.assertNotIn("--check", calls[1]["argv"])
        self.assertEqual(calls[1]["argv"][-1], "--strict")
        self.assertEqual(record["publish"]["rc"], 0)
        self.assertIn("published", record["publish"]["stderr"])

    def test_check_failure(self):
        os.environ["FAKE_CHECK_RC"] = "1"
        with self.assertRaises(AcceptanceError) as ctx:
            emit.emit(self.data, dry_run=False)
        self.assertEqual(len(self.fake.calls()), 1)
        self.assertEqual(ctx.exception.record["check"]["rc"], 1)
        self.assertIsNone(ctx.exception.record["publish"])

    def test_publish_failure(self):
        os.environ["FAKE_PUBLISH_RC"] = "1"
        with self.assertRaises(AcceptanceError) as ctx:
            emit.emit(self.data, dry_run=False)
        self.assertEqual(ctx.exception.record["publish"]["rc"], 1)

    def test_invalid_event_never_runs_emitter(self):
        bad = dict(self.data)
        bad["audience"] = "client"
        with self.assertRaises(ContractError):
            emit.emit(bad, dry_run=True)
        self.assertEqual(self.fake.calls(), [])


class EmitCmd(unittest.TestCase):
    def setUp(self):
        self.fake = FakeBloodbank()
        self.addCleanup(self.fake.close)

    def test_record_written_default_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            event = os.path.join(tmp, "2026-09-03T0300-internal.event.json")
            with open(event, "w", encoding="utf-8") as fh:
                json.dump(load("a5-internal.event.json"), fh)
            args = types.SimpleNamespace(event=event, dry_run=True, out=None, json=False, project=None)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(emit.emit_cmd(args), 0)
            record_path = os.path.join(tmp, "2026-09-03T0300-internal.emit.json")
            self.assertTrue(os.path.exists(record_path))
            self.assertIn("publish: skipped", buf.getvalue())
            os.environ["FAKE_CHECK_RC"] = "2"
            args.out = os.path.join(tmp, "custom.emit.json")
            with self.assertRaises(AcceptanceError):
                emit.emit_cmd(args)
            with open(args.out, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["check"]["rc"], 2)


if __name__ == "__main__":
    unittest.main()
