import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import contract  # noqa: E402
from ar.common import ContractError  # noqa: E402

FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "publish")


def load(name):
    with open(os.path.join(FX, name), encoding="utf-8") as fh:
        return json.load(fh)


class A5Fixtures(unittest.TestCase):
    def test_internal_fixture_validates(self):
        contract.validate_event(load("a5-internal.event.json"))

    def test_external_fixture_validates(self):
        contract.validate_event(load("a5-external.event.json"))


class Mutations(unittest.TestCase):
    def setUp(self):
        self.internal = load("a5-internal.event.json")
        self.external = load("a5-external.event.json")

    def refuse(self, data, *needles):
        with self.assertRaises(ContractError) as ctx:
            contract.validate_event(data)
        msg = str(ctx.exception)
        for needle in needles:
            self.assertIn(needle, msg, msg)
        return msg

    def test_missing_required_names_the_field(self):
        d = copy.deepcopy(self.internal)
        del d["report"]["html"]
        self.refuse(d, "data.report", "html")

    def test_unknown_key_is_refused(self):
        d = copy.deepcopy(self.internal)
        d["report"]["extra"] = "x"
        self.refuse(d, "data.report", "additionalProperties")

    def test_schema_version_must_be_one(self):
        d = copy.deepcopy(self.internal)
        d["schema_version"] = 2
        self.refuse(d, "schema_version")

    def test_external_must_not_carry_sources_or_tickets(self):
        d = copy.deepcopy(self.external)
        d["sources"] = self.internal["sources"]
        self.refuse(d, "external", "sources")

    def test_internal_must_carry_both(self):
        d = copy.deepcopy(self.internal)
        del d["tickets"]
        self.refuse(d, "internal", "tickets")

    def test_external_ticket_key_in_raw(self):
        d = copy.deepcopy(self.external)
        d["report"]["raw"] += " see SMK-12"
        self.refuse(d, "data.report.raw", "ticket key", "SMK-12")

    def test_external_sha_in_markdown(self):
        d = copy.deepcopy(self.external)
        d["report"]["markdown"] += " at a1b2c3d"
        self.refuse(d, "data.report.markdown", "commit sha")

    def test_external_hex_word_is_not_a_sha(self):
        d = copy.deepcopy(self.external)
        d["report"]["raw"] += " the defaced label was effaced"
        contract.validate_event(d)

    def test_external_abs_path_in_title(self):
        d = copy.deepcopy(self.external)
        d["report"]["title"] = "Notes in /home/someone/x"
        self.refuse(d, "data.report.title", "absolute")

    def test_external_ticket_key_in_html(self):
        d = copy.deepcopy(self.external)
        d["report"]["html"] += "<p>SMK-7</p>"
        self.refuse(d, "data.report.html", "ticket key")

    def test_internal_may_name_tickets(self):
        d = copy.deepcopy(self.internal)
        d["report"]["raw"] += " SMK-12 a1b2c3d"
        contract.validate_event(d)

    def test_absolute_path_anywhere_in_data(self):
        d = copy.deepcopy(self.internal)
        repo = next(iter(d["sources"]["git"]))
        d["sources"]["git"][repo]["commits"][0]["subject"] = "fix /tmp/thing"
        self.refuse(d, "absolute filesystem path")

    def test_assert_no_paths_scans_keys(self):
        with self.assertRaises(ContractError):
            contract.assert_no_paths({"/etc/passwd": 1})
        contract.assert_no_paths({"ok": "https://x.test/home/y"})
        contract.assert_no_paths({"ok": "see a.b/tmp/x"})

    def test_window_arithmetic(self):
        d = copy.deepcopy(self.internal)
        d["window"]["duration_seconds"] += 1
        self.refuse(d, "duration_seconds", "end - start")

    def test_window_end_after_start(self):
        d = copy.deepcopy(self.internal)
        d["window"]["end"] = d["window"]["start"]
        self.refuse(d, "after")

    def test_cap_24h_requires_86400(self):
        d = copy.deepcopy(self.internal)
        d["window"]["basis"] = "cap_24h"
        d["window"]["previous_event_id"] = None
        d["window"]["start"] = "2026-09-02T07:00:00Z"
        d["window"]["end"] = "2026-09-02T09:00:00Z"
        d["window"]["duration_seconds"] = 7200
        self.refuse(d, "cap_24h")
        d["window"]["end"] = "2026-09-03T07:00:00Z"
        d["window"]["duration_seconds"] = 86400
        contract.validate_event(d)

    def test_previous_report_requires_previous_event_id(self):
        d = copy.deepcopy(self.internal)
        d["window"]["basis"] = "previous_report"
        d["window"]["previous_event_id"] = None
        self.refuse(d, "previous_event_id")

    def test_token_bucket_sum(self):
        d = copy.deepcopy(self.internal)
        agent = next(k for k, v in d["tokens"]["by_agent"].items() if v)
        d["tokens"]["by_agent"][agent]["total"] += 5
        self.refuse(d, f"by_agent.{agent}.total")

    def test_token_grand_total(self):
        d = copy.deepcopy(self.internal)
        d["tokens"]["total"] += 1
        self.refuse(d, "data.tokens.total")

    def test_html_must_be_a_document(self):
        d = copy.deepcopy(self.internal)
        d["report"]["html"] = "<p>fragment</p>"
        self.refuse(d, "doctype")

    def test_title_cap(self):
        d = copy.deepcopy(self.internal)
        d["report"]["title"] = "x" * 181
        self.refuse(d, "data.report.title", "180")

    def test_raw_cap(self):
        d = copy.deepcopy(self.internal)
        d["report"]["raw"] = "y" * 5001
        self.refuse(d, "data.report.raw", "5000")

    def test_generator_shapes(self):
        d = copy.deepcopy(self.internal)
        d["generator"]["skill_version"] = "1.0"
        self.refuse(d, "skill_version")
        d = copy.deepcopy(self.internal)
        d["generator"]["run_id"] = "not-a-uuid"
        self.refuse(d, "run_id")
        d = copy.deepcopy(self.internal)
        d["generator"]["dry_run"] = "yes"
        self.refuse(d, "dry_run")

    def test_agent_key_pattern(self):
        d = copy.deepcopy(self.internal)
        d["tokens"]["by_agent"]["Claude"] = None
        self.refuse(d, "by_agent")

    def test_commit_sha_lowercase(self):
        d = copy.deepcopy(self.internal)
        repo = next(iter(d["sources"]["git"]))
        d["sources"]["git"][repo]["commits"][0]["sha"] = "ABCDEF1"
        self.refuse(d, "sha")

    def test_ticket_list_unique(self):
        d = copy.deepcopy(self.internal)
        d["sources"]["board"]["closed"] = ["SMK-1", "SMK-1"]
        self.refuse(d, "board.closed", "duplicate")

    def test_ticket_exposure_enum(self):
        d = copy.deepcopy(self.internal)
        if not d["tickets"]:
            d["tickets"] = [{"key": "SMK-1", "title": "t", "from_state": None, "to_state": None, "labels": [], "exposure": "external"}]
        d["tickets"][0]["exposure"] = "secret"
        self.refuse(d, "exposure")

    def test_repos_required_and_capped(self):
        d = copy.deepcopy(self.internal)
        d["project"]["repos"] = []
        self.refuse(d, "repos")
        d["project"]["repos"] = [f"r{i}" for i in range(9)]
        self.refuse(d, "repos", "8")

    def test_bool_is_not_a_count(self):
        d = copy.deepcopy(self.internal)
        d["sources"]["candystore"]["sessions"] = True
        self.refuse(d, "sessions")

    def test_timestamp_format(self):
        d = copy.deepcopy(self.internal)
        d["window"]["start"] = "2026-09-02 07:00:00"
        self.refuse(d, "window.start")


class Regexes(unittest.TestCase):
    def test_sha_regex_needs_digit_and_letter(self):
        self.assertIsNone(contract._PROJECT_SHA.search("defaced effaced 1234567"))
        self.assertIsNotNone(contract._PROJECT_SHA.search("at a1b2c3d today"))
        self.assertIsNone(contract._PROJECT_SHA.search("color #a1b2c3d"))

    def test_abs_path_regex(self):
        self.assertIsNotNone(contract._PROJECT_ABS_PATH.search("in /home/x/y"))
        self.assertIsNone(contract._PROJECT_ABS_PATH.search("https://host/home/x"))
        self.assertIsNone(contract._PROJECT_ABS_PATH.search("a.b/tmp/x"))

    def test_external_markers_without_identifier(self):
        kinds = [what for _, what in contract.external_text_markers(None)]
        self.assertNotIn("a ticket key", kinds)
        kinds = [what for _, what in contract.external_text_markers("SMK")]
        self.assertEqual(kinds[0], "a ticket key")


if __name__ == "__main__":
    unittest.main()
