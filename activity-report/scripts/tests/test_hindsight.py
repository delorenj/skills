"""Hindsight list/recall/retain with the CLI mocked; colour only, never fatal."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import hindsight  # noqa: E402
from ar.common import ConfigError, parse_iso  # noqa: E402
from ar.config import DEFAULTS, Project, deep_merge  # noqa: E402
from ar.window import Window  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "collect")


def fixture(name: str):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return json.load(fh)


LIST_ITEM = fixture("hindsight_list.json")["items"][0]
RECALL = fixture("hindsight_recall.json")
QUERY = "what changed for James Brennan between 2026-09-02T00:00:00Z and 2026-09-03T00:00:00Z: wins, blockers, decisions"


def window() -> Window:
    return Window(start=parse_iso("2026-09-02T00:00:00Z"), end=parse_iso("2026-09-03T00:00:00Z"), basis="explicit",
                  previous_event_id=None, previous=None, caveats=[])


def project(**cfg) -> Project:
    config = deep_merge(DEFAULTS, {"hindsight": {"bank": "james-brennan", **cfg}})
    return Project(slug="james-brennan", name="James Brennan", identifier="JIMB", workspace="automaticai", board_id=None,
                   provider_type="plane", repo_path="/tmp/james-brennan", extra_repo_paths=[], config=config,
                   tz="America/New_York", project_json_path="/tmp/james-brennan/.project.json")


def item(date: str, text: str, **over) -> dict:
    out = copy.deepcopy(LIST_ITEM)
    out.update({"date": date, "text": text, "invalidated_at": None, "context": "session-summary", "fact_type": "world"})
    out.update(over)
    return out


PAGE_1 = [item("2026-09-02T20:00:00+00:00", "  Newest \n fact "),
          item("2026-09-02T19:00:00+00:00", "Yesterday's report body", context="activity-report:internal"),
          item("2026-09-02T18:00:00+00:00", "Retracted", invalidated_at="2026-09-02T18:30:00+00:00")]
PAGE_2 = [item("2026-09-02T08:00:00+00:00", "x" * 700, fact_type="experience"),
          item("2026-09-01T23:00:00+00:00", "Before the window"),
          item("2026-09-01T22:00:00+00:00", "Older still")]


class FakeCli:
    def __init__(self, pages=None, recall=None, list_rc=0, recall_rc=0, retain_rc=0, missing=False):
        self.pages = pages if pages is not None else [PAGE_1, PAGE_2, []]
        self.recall = recall if recall is not None else RECALL
        self.rcs = {"list": list_rc, "recall": recall_rc, "retain": retain_rc}
        self.missing = missing
        self.calls: list[list[str]] = []

    def __call__(self, args, **kw):
        self.calls.append(list(args))
        if self.missing:
            raise FileNotFoundError(args[0])
        verb = args[2]
        rc = self.rcs[verb]
        if rc:
            return subprocess.CompletedProcess(args, rc, stdout="", stderr="error: bank exploded\n")
        if verb == "list":
            offset = int(args[args.index("-s") + 1])
            limit = int(args[args.index("-l") + 1])
            page = self.pages[offset // limit] if offset // limit < len(self.pages) else []
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps({"items": page, "limit": limit, "offset": offset, "total": 9}), stderr="")
        if verb == "recall":
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps(self.recall), stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="stored\n", stderr="")


class CollectTests(unittest.TestCase):
    def collect(self, cli: FakeCli, proj=None):
        with mock.patch.object(hindsight, "LIST_PAGE", 3), mock.patch.object(hindsight.subprocess, "run", cli):
            return hindsight.collect(proj or project(), window())

    def test_list_filters_and_stops_early(self):
        cli = FakeCli()
        block = self.collect(cli)
        self.assertEqual((block["bank"], block["status"], block["caveats"]), ("james-brennan", "ok", []))
        self.assertEqual(block["items"], [
            {"at": "2026-09-02T20:00:00Z", "fact_type": "world", "text": "Newest fact"},
            {"at": "2026-09-02T08:00:00Z", "fact_type": "experience", "text": "x" * 500},
        ])
        lists = [c for c in cli.calls if c[2] == "list"]
        self.assertEqual(lists, [["hindsight", "memory", "list", "james-brennan", "-o", "json", "-l", "3", "-s", "0"],
                                 ["hindsight", "memory", "list", "james-brennan", "-o", "json", "-l", "3", "-s", "3"]])
        recall = [c for c in cli.calls if c[2] == "recall"]
        self.assertEqual(recall, [["hindsight", "memory", "recall", "james-brennan", QUERY, "-o", "json",
                                   "--budget", "high", "--max-tokens", "2048"]])
        self.assertEqual(block["recall"]["query"], QUERY)
        expected = []
        for r in RECALL["results"]:
            text = " ".join(r["text"].split())[:500]
            if text not in expected:
                expected.append(text)
        self.assertEqual(block["recall"]["items"], expected[:20])
        self.assertLessEqual(len(block["recall"]["items"]), 20)

    def test_list_failure_is_a_caveat_not_a_stop(self):
        block = self.collect(FakeCli(list_rc=1))
        self.assertEqual((block["status"], block["items"]), ("ok", []))
        self.assertTrue(block["recall"]["items"])
        self.assertEqual(block["caveats"], ["hindsight list failed: hindsight memory list exited 1: error: bank exploded"])

    def test_everything_failing_is_unavailable(self):
        block = self.collect(FakeCli(list_rc=1, recall_rc=2))
        self.assertEqual(block["status"], "unavailable")
        self.assertEqual(len(block["caveats"]), 2)
        block = self.collect(FakeCli(missing=True))
        self.assertEqual(block["status"], "unavailable")
        self.assertTrue(all("is not on PATH" in c for c in block["caveats"]))

    def test_non_json_output(self):
        cli = FakeCli()
        cli.recall = None
        with mock.patch.object(hindsight, "LIST_PAGE", 3), mock.patch.object(hindsight.subprocess, "run", cli):
            with mock.patch.object(hindsight, "_json", side_effect=hindsight.HindsightFailed("hindsight returned non-JSON output")):
                block = hindsight.collect(project(), window())
        self.assertEqual(block["status"], "unavailable")
        self.assertTrue(all("non-JSON" in c for c in block["caveats"]))

    def test_disabled_by_config(self):
        cli = FakeCli()
        block = self.collect(cli, project(recall=False))
        self.assertEqual((block["status"], block["items"], block["recall"]["items"]), ("disabled", [], []))
        self.assertEqual(cli.calls, [])

    def test_bank_refusal(self):
        cli = FakeCli()
        with mock.patch.object(hindsight, "hindsight_bank", side_effect=ConfigError("refusing implicit Hindsight bank")):
            with mock.patch.object(hindsight.subprocess, "run", cli):
                block = hindsight.collect(project(), window())
        self.assertEqual((block["bank"], block["status"]), (None, "unavailable"))
        self.assertIn("refusing", block["caveats"][0])
        self.assertEqual(cli.calls, [])


class RetainTests(unittest.TestCase):
    def test_retain_arguments(self):
        cli = FakeCli()
        with mock.patch.object(hindsight.subprocess, "run", cli):
            ok = hindsight.retain(project(), "internal", "# Title\n\nBody", window().end, "2026-09-03T0300")
        self.assertTrue(ok)
        self.assertEqual(cli.calls, [["hindsight", "memory", "retain", "james-brennan", "# Title\n\nBody",
                                      "--context", "activity-report:internal",
                                      "--doc-id", "activity-report:james-brennan:internal:2026-09-03T0300",
                                      "--timestamp", "2026-09-03T00:00:00Z"]])

    def test_retain_never_raises(self):
        with mock.patch.object(hindsight, "eprint") as err:
            with mock.patch.object(hindsight.subprocess, "run", FakeCli(retain_rc=2)):
                self.assertFalse(hindsight.retain(project(), "external", "body", "2026-09-03T00:00:00Z", "L"))
            self.assertIn("retain failed (warning)", err.call_args.args[0])
            with mock.patch.object(hindsight.subprocess, "run", FakeCli(missing=True)):
                self.assertFalse(hindsight.retain(project(), "external", "body", "2026-09-03T00:00:00Z", "L"))
            cli = FakeCli()
            with mock.patch.object(hindsight.subprocess, "run", cli):
                self.assertFalse(hindsight.retain(project(retain=False), "internal", "body", "2026-09-03T00:00:00Z", "L"))
                self.assertFalse(hindsight.retain(project(), "internal", "   ", "2026-09-03T00:00:00Z", "L"))
            self.assertEqual(cli.calls, [])

    def test_retain_cmd(self):
        tmp = tempfile.mkdtemp(prefix="ar-hs-")
        raw = os.path.join(tmp, "x.raw.txt")
        digest = os.path.join(tmp, "x.digest.json")
        with open(raw, "w", encoding="utf-8") as fh:
            fh.write("# Report\n\nline\n")
        with open(digest, "w", encoding="utf-8") as fh:
            json.dump({"audience": "internal", "label": "2026-09-03T0300", "window": {"end": "2026-09-03T00:00:00Z"}}, fh)
        cli = FakeCli()
        args = mock.Mock(project="james-brennan", audience="internal", raw=raw, digest=digest, json=True)
        with mock.patch.object(hindsight, "load_project", return_value=project()), \
                mock.patch.object(hindsight.subprocess, "run", cli), mock.patch("sys.stdout") as out:
            self.assertEqual(hindsight.retain_cmd(args), 0)
        printed = json.loads("".join(c.args[0] for c in out.write.call_args_list))
        self.assertEqual(printed, {"retained": True, "bank": "james-brennan", "doc_id": "activity-report:james-brennan:internal:2026-09-03T0300"})
        self.assertEqual(cli.calls[0][4], "# Report\n\nline\n")
        args.audience = "external"
        with mock.patch.object(hindsight, "load_project", return_value=project()):
            with self.assertRaises(ConfigError):
                hindsight.retain_cmd(args)


if __name__ == "__main__":
    unittest.main()
