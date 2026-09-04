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
    def __init__(self, pages=None, recall=None, list_rc=0, recall_rc=0, retain_rc=0, get_rc=0, units=None, missing=False):
        self.pages = pages if pages is not None else [PAGE_1, PAGE_2, []]
        self.recall = recall if recall is not None else RECALL
        self.rcs = {"list": list_rc, "recall": recall_rc, "get": get_rc}
        # per successive retain call (the last value repeats); an int applies to every call
        self.retain_rcs = list(retain_rc) if isinstance(retain_rc, (list, tuple)) else [retain_rc]
        # memory_unit_count per successive `document get` (the last value repeats)
        self.units = list(units) if units is not None else [5]
        self.missing = missing
        self.calls: list[list[str]] = []

    @staticmethod
    def _next(seq):
        return seq.pop(0) if len(seq) > 1 else seq[0]

    def __call__(self, args, **kw):
        self.calls.append(list(args))
        if self.missing:
            raise FileNotFoundError(args[0])
        verb = args[2]
        rc = self._next(self.retain_rcs) if verb == "retain" else self.rcs[verb]
        if rc:
            return subprocess.CompletedProcess(args, rc, stdout="", stderr="error: bank exploded\n")
        if verb == "list":
            offset = int(args[args.index("-s") + 1])
            limit = int(args[args.index("-l") + 1])
            page = self.pages[offset // limit] if offset // limit < len(self.pages) else []
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps({"items": page, "limit": limit, "offset": offset, "total": 9}), stderr="")
        if verb == "recall":
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps(self.recall), stderr="")
        if verb == "get":
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps({"id": args[4], "memory_unit_count": self._next(self.units)}), stderr="")
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps({"success": True, "items_count": 1, "message": "Stored 1 memory units"}), stderr="")


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
    RAW = ("# First **draft** invoice landed\n## The window\n| Sessions | 97 (57 ended) |\n| Commits | 46 |\n"
           "## Timeline\n20:56 a24fd10 feat(surface): field proving\n02:12 draft **5444** read back\n"
           "## Still open\n- JIMB-169 held in review\n- nothing closed.\nPlain paragraph")
    WIN = {"start": "2026-09-02T00:35:54Z", "end": "2026-09-03T00:35:54Z"}   # 09-01 20:35 -> 09-02 20:35 New York

    def test_retain_text_is_prose_with_dated_timeline(self):
        text = hindsight.retain_text(project(), "external", self.RAW, self.WIN)
        self.assertEqual(text.split("\n\n"), [
            "Client-facing activity report for James Brennan (james-brennan), window ending 2026-09-03T00:35:54Z.",
            "First draft invoice landed.",
            "The window:",
            "Sessions: 97 (57 ended). Commits: 46.",
            "Timeline:",
            "On 2026-09-01 at 20:56, a24fd10 feat(surface): field proving. On 2026-09-02 at 02:12, draft 5444 read back.",
            "Still open:",
            "JIMB-169 held in review. nothing closed.",
            "Plain paragraph.",
        ])
        self.assertNotIn("|", text)
        self.assertNotIn("**", text)
        # a bare end value (no start) keeps the bare clock
        self.assertIn("At 09:00, x.", hindsight.retain_text(project(), "internal", "# T\n## Timeline\n09:00 x", "2026-09-03T00:00:00Z"))
        # text that is not a report goes through untouched
        self.assertEqual(hindsight.retain_text(project(), "internal", "just a note", self.WIN), "just a note")

    def test_timeline_dater(self):
        same_day = hindsight.timeline_dater(parse_iso("2026-09-02T13:00:00Z"), parse_iso("2026-09-02T22:00:00Z"), "America/New_York")
        self.assertEqual(same_day("10:15"), "2026-09-02")
        self.assertIsNone(same_day("nope"))
        across = hindsight.timeline_dater(parse_iso(self.WIN["start"]), parse_iso(self.WIN["end"]), "America/New_York")
        self.assertEqual(across("20:35"), "2026-09-01")
        self.assertEqual(across("23:59"), "2026-09-01")
        self.assertEqual(across("20:34"), "2026-09-02")
        self.assertEqual(across("00:00"), "2026-09-02")
        longer = hindsight.timeline_dater(parse_iso("2026-09-01T00:00:00Z"), parse_iso("2026-09-04T00:00:00Z"), "UTC")
        self.assertIsNone(longer("10:00"))
        self.assertIsNone(hindsight.timeline_dater(None, None, "UTC")("10:00"))

    def test_retain_arguments_and_verification(self):
        cli = FakeCli(units=[17])
        sleeps: list[int] = []
        with mock.patch.object(hindsight.subprocess, "run", cli):
            result = hindsight.retain(project(), "internal", "# Title\n\nBody", window(), "2026-09-03T0300", sleep=sleeps.append)
        prose = ("Internal activity report for James Brennan (james-brennan), window ending 2026-09-03T00:00:00Z."
                 "\n\nTitle.\n\nBody.")
        doc_id = "activity-report:james-brennan:internal:2026-09-03T0300"
        self.assertEqual(cli.calls, [
            ["hindsight", "memory", "retain", "james-brennan", prose, "--context", "activity-report:internal",
             "--doc-id", doc_id, "--timestamp", "2026-09-03T00:00:00Z"],
            ["hindsight", "document", "get", "james-brennan", doc_id, "-o", "json"],
        ])
        self.assertEqual(result, {"retained": True, "bank": "james-brennan", "doc_id": doc_id, "units": 17, "floor": 1,
                                  "attempts": 1, "reason": None})
        self.assertEqual(sleeps, [])
        # one document per window: no run id, no attempt suffix
        self.assertEqual(hindsight.doc_id_for(project(), "external", "L"), "activity-report:james-brennan:external:L")

    def test_retain_retries_the_same_id_on_zero_units(self):
        cli = FakeCli(units=[0, 0, 7])
        sleeps: list[int] = []
        with mock.patch.object(hindsight, "eprint"), mock.patch.object(hindsight.subprocess, "run", cli):
            result = hindsight.retain(project(), "internal", "# T\n\nB", window(), "L", sleep=sleeps.append)
        retains = [c for c in cli.calls if c[1] == "memory"]
        self.assertEqual(len(retains), 3)
        self.assertEqual({c[c.index("--doc-id") + 1] for c in retains}, {"activity-report:james-brennan:internal:L"})
        self.assertEqual(sleeps, [20, 40])
        self.assertEqual((result["retained"], result["units"], result["attempts"], result["reason"]), (True, 7, 3, None))

    def test_retain_floor_scales_with_the_text(self):
        self.assertEqual(hindsight.unit_floor("short note"), 1)
        long_report = "# Title\n\n" + " ".join(f"word{i}" for i in range(760))
        self.assertEqual(hindsight.unit_floor(hindsight.retain_text(project(), "internal", long_report, window())), 5)
        # 2 units from a day-long report is a failed extraction, not a quiet day: retried, then accepted at 6
        cli = FakeCli(units=[2, 6])
        sleeps: list[int] = []
        with mock.patch.object(hindsight, "eprint"), mock.patch.object(hindsight.subprocess, "run", cli):
            result = hindsight.retain(project(), "internal", long_report, window(), "L", sleep=sleeps.append)
        self.assertEqual((result["retained"], result["units"], result["floor"], result["attempts"]), (True, 6, 5, 2))
        self.assertEqual(sleeps, [20])

    def test_retain_gives_up_after_tries(self):
        cli = FakeCli(units=[0])
        sleeps: list[int] = []
        with mock.patch.object(hindsight, "eprint") as err, mock.patch.object(hindsight.subprocess, "run", cli):
            result = hindsight.retain(project(), "internal", "# T\n\nB", window(), "L", tries=2, sleep=sleeps.append)
        self.assertEqual(len([c for c in cli.calls if c[1] == "memory"]), 2)
        self.assertEqual(sleeps, [20])
        self.assertEqual((result["retained"], result["units"], result["attempts"]), (False, 0, 2))
        self.assertIn("0 units (floor 1) on try 2/2", result["reason"])
        self.assertIn("memory is not", err.call_args.args[0])
        # a failing CLI call is retried too
        cli = FakeCli(retain_rc=[2, 0], units=[4])
        with mock.patch.object(hindsight, "eprint"), mock.patch.object(hindsight.subprocess, "run", cli):
            result = hindsight.retain(project(), "internal", "# T\n\nB", window(), "L", sleep=lambda s: None)
        self.assertEqual((result["retained"], result["units"], result["attempts"]), (True, 4, 2))
        # an unreadable count is reported, not retried
        cli = FakeCli(get_rc=1)
        with mock.patch.object(hindsight, "eprint"), mock.patch.object(hindsight.subprocess, "run", cli):
            result = hindsight.retain(project(), "internal", "# T\n\nB", window(), "L", sleep=lambda s: None)
        self.assertEqual((result["retained"], result["units"], result["attempts"]), (False, None, 1))
        self.assertIn("could not be read", result["reason"])

    def test_retain_never_raises_and_respects_config(self):
        with mock.patch.object(hindsight, "eprint") as err:
            with mock.patch.object(hindsight.subprocess, "run", FakeCli(missing=True)):
                result = hindsight.retain(project(), "internal", "body", "2026-09-03T00:00:00Z", "L", sleep=lambda s: None)
            self.assertEqual((result["retained"], result["attempts"]), (False, 3))
            self.assertIn("is not on PATH", err.call_args.args[0])
            cli = FakeCli()
            with mock.patch.object(hindsight.subprocess, "run", cli):
                self.assertEqual(hindsight.retain(project(retain=False), "internal", "body", "2026-09-03T00:00:00Z", "L")["reason"],
                                 "hindsight.retain is false")
                self.assertEqual(hindsight.retain(project(), "internal", "   ", "2026-09-03T00:00:00Z", "L")["reason"],
                                 "empty report text")
                # the client-facing text is spin, not the record: not retained unless configured
                self.assertIn("not in hindsight.retain_audiences",
                              hindsight.retain(project(), "external", "body", "2026-09-03T00:00:00Z", "L")["reason"])
            self.assertEqual(cli.calls, [])
            with mock.patch.object(hindsight.subprocess, "run", cli):
                result = hindsight.retain(project(retain_audiences=["internal", "external"]), "external", "body",
                                          "2026-09-03T00:00:00Z", "L")
            self.assertTrue(result["retained"])
            self.assertEqual(cli.calls[0][cli.calls[0].index("--doc-id") + 1], "activity-report:james-brennan:external:L")

    def test_retain_cmd(self):
        tmp = tempfile.mkdtemp(prefix="ar-hs-")
        raw = os.path.join(tmp, "x.raw.txt")
        digest = os.path.join(tmp, "x.digest.json")
        with open(raw, "w", encoding="utf-8") as fh:
            fh.write("# Report\n\nline\n")
        with open(digest, "w", encoding="utf-8") as fh:
            json.dump({"audience": "internal", "label": "2026-09-03T0300",
                       "window": {"start": "2026-09-02T00:00:00Z", "end": "2026-09-03T00:00:00Z"},
                       "run_id": "9b6e3b86-5b5e-4040-bbbe-c8fb6d258575"}, fh)
        cli = FakeCli(units=[3])
        args = mock.Mock(project="james-brennan", audience="internal", raw=raw, digest=digest, json=True, tries=3)
        with mock.patch.object(hindsight, "load_project", return_value=project()), \
                mock.patch.object(hindsight.subprocess, "run", cli), mock.patch("sys.stdout") as out:
            self.assertEqual(hindsight.retain_cmd(args), 0)
        printed = json.loads("".join(c.args[0] for c in out.write.call_args_list))
        self.assertEqual(printed, {"retained": True, "bank": "james-brennan",
                                   "doc_id": "activity-report:james-brennan:internal:2026-09-03T0300",
                                   "units": 3, "floor": 1, "attempts": 1, "reason": None})
        self.assertTrue(cli.calls[0][4].endswith("\n\nReport.\n\nline."), cli.calls[0][4])
        self.assertNotIn("# Report", cli.calls[0][4])
        # an unverified retain exits 1 (the runner logs it as a warning; a hand repair sees it)
        with mock.patch.object(hindsight, "load_project", return_value=project()), mock.patch.object(hindsight, "eprint"), \
                mock.patch.object(hindsight.subprocess, "run", FakeCli(units=[0])), mock.patch("sys.stdout"), \
                mock.patch.object(hindsight.time, "sleep"):
            self.assertEqual(hindsight.retain_cmd(args), 1)
        args.audience = "external"
        with mock.patch.object(hindsight, "load_project", return_value=project()):
            with self.assertRaises(ConfigError):
                hindsight.retain_cmd(args)


if __name__ == "__main__":
    unittest.main()
