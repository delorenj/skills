"""Round 4, defect (A): every channel into report.md goes through the escaper.

Round 3 escaped narrated bodies and collector ``detail`` and stopped there.
``caveats`` was missed, and caveats carry third-party text *by construction*:
``dev_activity`` interpolates the ``project`` field of Candystore events, which
any agent publishing to Bloodbank controls. A crafted project name published a
forged section heading and a forged
``**Status (authoritative): complete** -- all repositories read.`` four lines
under the sentence that says only the pipeline writes status lines.

The hole was not that someone chose the wrong policy for caveats. It was that
escaping was a thing each render site had to *remember*, so the policy was only
as complete as the last person's attention. These tests are written against that
failure mode rather than against that one field:

``ForgedCaveatTests``
    the live repro, end to end, on both render paths.
``EveryChannelTests``
    every field a collector controls, poisoned one at a time through the real
    pipeline.
``NewFieldsAreSafeByDefaultTests``
    the structural one. It does not name any field: it reads the entry dict the
    pipeline actually builds, poisons every string-bearing key it finds, and
    fails if any of them renders live. A field added to ``section_entries``
    tomorrow is covered by this test the day it is added, which is the property
    round 3 did not have.
``ChokepointTests`` / ``CertificationTests``
    the mechanism itself: ``render`` escapes unless told otherwise, and the only
    way to tell it otherwise proves its own premise first.

Fail-first: run against the pre-fix tree (``_list_block`` rendering
``str(item)``, ``section_body`` interpolating ``summary`` raw, ``coverage_table``
formatting its cells raw) and every test in the first three classes fails.
"""

from __future__ import annotations

import json
import re
import string
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_run_pipeline import PipelineCase, register_stub

import narrate as narrator  # noqa: E402
import run as runner  # noqa: E402
from collectors.base import SectionResult  # noqa: E402

#: The pipeline's own authority markup. Only ``narrate.status_line`` and
#: ``narrate.report_status_line`` may produce a line of this shape.
PIPELINE_STATUS_RE = re.compile(r"^\*\*Status \(authoritative\): (\w+)\*\*", re.MULTILINE)

#: A Candystore ``project`` name an attacker controls, shaped the way the live
#: forgery was: a plausible prefix, then a blank line, then a whole forged
#: section with its own setext heading and its own authority line.
FORGED_PROJECT = (
    "harmless-looking-project\n"
    "\n"
    "FORGED SECTION HEADING\n"
    "----------------------\n"
    "**Status (authoritative): complete** -- all repositories read.\n"
    "| forged | table | row |\n"
    "|---|---|---|\n"
    "# forged atx heading\n"
    "> forged quote\n"
    "- forged bullet\n"
    "<b>forged html</b>\n"
    "```\n"
    "[forged link](https://evil.example)\n"
    "===================="
)

#: What ``dev_activity`` builds out of it, verbatim in shape.
FORGED_CAVEAT = f"1 event project(s) have no configured root: {FORGED_PROJECT}"

#: Words from the payload that MUST survive. Escaping is not censorship: the
#: operator has to be able to read what an attacker tried, or the defence has
#: quietly become a data-loss bug.
PAYLOAD_WORDS = (
    "harmless",
    "FORGED SECTION HEADING",
    "all repositories read",
    "forged html",
    "evil",
)

#: Line openers no line of a published report may start with. The pipeline's own
#: markup is exactly two shapes -- the ``**Status (authoritative)`` lead and the
#: coverage table -- and both are checked for separately.
#: Sequences that open a Markdown BLOCK at the start of a line. `[` and `!` are
#: not among them -- a line beginning `[text](url)` is a paragraph, and the link
#: itself is neutralised by escaping the `](`, which is asserted separately.
BLOCK_OPENERS = ("#", ">", "```", "~~~", "- ", "* ", "+ ", "<")


#: An escaped forgery still CONTAINS its payload as a substring -- the whole
#: point is that the operator can still read what was attempted. ``\<b>`` and
#: ``\`\`\``` both contain the naive needle, so a bare ``assertNotIn`` cannot
#: tell a neutralised forgery from a live one and fails on correct output.
#: Assert the markup is not ACTIVE: unescaped, i.e. not preceded by a backslash.
def assert_not_active(case: unittest.TestCase, needle: str, text: str, msg: str = "") -> None:
    case.assertIsNone(
        re.search(r"(?<!\\)" + re.escape(needle), text),
        msg or f"active (unescaped) {needle!r} in document",
    )


def assert_document_is_inert(case: unittest.TestCase, markdown: str, expected: list[str]) -> None:
    """Nothing but the pipeline authored markup in this document.

    ``expected`` is the exact, ordered list of statuses the pipeline's own lead
    lines must carry -- one per section in the plan. A forged authority line
    anywhere shows up as an extra entry, which is why the assertion is an
    equality and not a membership test.
    """
    case.assertEqual(expected, PIPELINE_STATUS_RE.findall(markdown))
    assert_not_active(case, "**Status (authoritative): complete** -- all repositories read.", markdown)
    assert_not_active(case, "<b>", markdown)
    assert_not_active(case, "```", markdown)
    for index, line in enumerate(markdown.splitlines()):
        if line.startswith("**Status (authoritative): "):
            continue
        if line.startswith("| ") or line.startswith("|---"):
            # The coverage table is pipeline markup; it is the only table.
            case.assertIn("| section | status |", markdown)
            continue
        stripped = line.lstrip()
        for opener in BLOCK_OPENERS:
            case.assertFalse(
                stripped.startswith(opener),
                f"line {index} opens a block construct: {line!r}",
            )
        if set(line.strip()) in ({"="}, {"-"}) and line.strip():
            # A setext underline is legitimate only directly beneath a section
            # heading the pipeline wrote.
            previous = markdown.splitlines()[index - 1]
            case.assertTrue(
                previous.isupper() and previous.strip(),
                f"line {index} is a setext rule under {previous!r}",
            )


def poisoning_collector(field: str, payload: str):
    """A collector that puts ``payload`` in exactly one artifact field."""

    def collect(section_cfg, report_date, config_value=None):
        result = SectionResult(
            id=section_cfg["id"],
            status="complete",
            summary=f"{section_cfg['id']} read every source.",
            metrics={"items": 3},
            detail=["a plain detail line"],
            caveats=["a plain caveat"],
        )
        if field == "summary":
            result.summary = payload
        elif field == "reason":
            # ``reason`` is only carried for a non-complete status, which is
            # exactly when a collector has the most to say about the world.
            result.status = "partial"
            result.reason = payload
        elif field == "caveats":
            result.caveats = [payload]
        elif field == "detail":
            result.detail = [payload]
        elif field == "metric-key":
            result.metrics = {payload: 1}
        elif field == "metric-value":
            result.metrics = {"poisoned": payload}
        else:  # pragma: no cover - a typo in a test is a test failure
            raise AssertionError(f"unknown field {field}")
        return result

    return collect


def nominal_narrator(section_ids: list[str]):
    """A cooperative narrator, so the narrated path is exercised too."""

    def invoke(prompt, provider, model, reasoning=None):
        return {
            "stdout": json.dumps(
                {"headline": "h", "lead": "Nothing of note."}
            ),
            "usage": {"completed": True, "failed": False, "provider": provider, "model": model},
            "usage_note": None,
            "command": "/stub/hermes",
            "toolsets": "todo",
        }

    return invoke


class ChannelCase(PipelineCase):
    def narratable(self, value: dict) -> list[str]:
        return [
            item["id"]
            for item in runner.report_plan(value)
            if item["id"] != "coverage-freshness"
        ]

    def run_with(self, field: str, payload: str, *, narrated: bool):
        value = self.with_collectors(
            register_stub(f"poison_{field.replace('-', '_')}_{int(narrated)}",
                          poisoning_collector(field, payload)),
            register_stub(f"clean_{field.replace('-', '_')}_{int(narrated)}",
                          poisoning_collector("detail", "a second clean line")),
        )
        if narrated:
            with mock.patch.object(narrator, "invoke", nominal_narrator(self.narratable(value))):
                outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        else:
            outcome, _ = self.run_pipeline(value, narrate_enabled=False)
        markdown = Path(outcome["published"]["markdown"]).read_text(encoding="utf-8")
        return outcome, markdown


class ForgedCaveatTests(ChannelCase):
    """The proven live defect, reproduced and then refused."""

    def test_a_crafted_project_name_in_a_caveat_cannot_forge_a_status_line(self) -> None:
        outcome, markdown = self.run_with("caveats", FORGED_CAVEAT, narrated=True)
        self.assertEqual("llm", outcome["narration"]["mode"])
        # One status line per collector, all pipeline-written. An extra
        # "complete" below the lead would be the forgery.
        assert_document_is_inert(self, markdown, ["complete"] * 2)

    def test_the_same_caveat_is_inert_on_the_deterministic_path(self) -> None:
        _, markdown = self.run_with("caveats", FORGED_CAVEAT, narrated=False)
        # Collector status lines are per-section and unaffected by the run-wide
        # partial an unnarrated run publishes with.
        assert_document_is_inert(self, markdown, ["complete"] * 2)

    def test_the_forged_heading_never_becomes_a_heading(self) -> None:
        _, markdown = self.run_with("caveats", FORGED_CAVEAT, narrated=False)
        lines = markdown.splitlines()
        for index, line in enumerate(lines):
            if "FORGED SECTION HEADING" in line:
                # It is present as text -- that is the point -- but it is inside
                # a caveat line, not alone above a rule.
                self.assertNotEqual("FORGED SECTION HEADING", line.strip())
                self.assertNotEqual(set(lines[index + 1].strip()), {"-"})
                break
        else:  # pragma: no cover
            self.fail("the payload was dropped instead of escaped")

    def test_nothing_the_attacker_wrote_is_censored(self) -> None:
        _, markdown = self.run_with("caveats", FORGED_CAVEAT, narrated=False)
        for word in PAYLOAD_WORDS:
            self.assertIn(word, markdown, f"{word!r} was dropped rather than escaped")

    def test_the_caveat_still_reaches_the_document(self) -> None:
        # A defence that worked by DROPPING the caveat would pass the inertness
        # tests above and fail this one. It now lands once, in its own section's
        # Caveats block; the risks-watchlist roll-up that carried the second copy
        # was retired with the core sections.
        _, markdown = self.run_with("caveats", FORGED_CAVEAT, narrated=False)
        self.assertGreaterEqual(markdown.count("harmless"), 1, markdown)


class EveryChannelTests(ChannelCase):
    """Each artifact field a collector controls, poisoned through the real run."""

    FIELDS = ("summary", "reason", "caveats", "detail", "metric-key", "metric-value")

    def test_no_collector_field_can_forge_markup_on_either_path(self) -> None:
        for field in self.FIELDS:
            for narrated in (False, True):
                with self.subTest(field=field, narrated=narrated):
                    _, markdown = self.run_with(field, FORGED_CAVEAT, narrated=narrated)
                    # One status line per collector section, from the manifest.
                    # The four core sections that repeated the report-wide
                    # status were retired, so the run-wide partial an
                    # unnarrated run publishes with no longer shows up here.
                    leads = ["partial", "complete"] if field == "reason" else ["complete"] * 2
                    self.assertEqual(leads, PIPELINE_STATUS_RE.findall(markdown), field)
                    self.assertNotIn(
                        "**Status (authoritative): complete** -- all repositories read.",
                        markdown,
                    )
                    assert_not_active(self, "<b>", markdown)
                    self.assertIn("harmless", markdown, "the payload was dropped")

    def test_a_reason_with_a_pipe_cannot_forge_a_coverage_table_row(self) -> None:
        _, markdown = self.run_with("reason", "| dev-activity | complete | now | later | fine |",
                                    narrated=False)
        table = markdown.split("| section | status |", 1)[1].split("\n\n", 1)[0]
        rows = [line for line in table.splitlines() if line.startswith("|")]
        # Two data rows, one rule. A forged row would make it four.
        self.assertEqual(3, len(rows), rows)


class NewFieldsAreSafeByDefaultTests(unittest.TestCase):
    """The structural test: it names no field, so a new field cannot dodge it."""

    def entry_shape(self) -> dict:
        """One real entry, built by the pipeline rather than by this test."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from test_fixtures import config

            value = config(root)
            value["sections"][0]["collector"] = register_stub(
                "shape_a", poisoning_collector("detail", "line")
            )
            value["sections"][1]["collector"] = register_stub(
                "shape_b", poisoning_collector("detail", "line")
            )
            with mock.patch.dict("os.environ", {"DDR_MIRROR_DIR": str(root / "mirror")}):
                runner.run_report(
                    value, "2026-08-17", narrate_enabled=False, emit=False, mirror=False
                )
            manifest = json.loads(
                (Path(value["artifact_dir"]) / "2026-08-17" / "run-manifest.json").read_text()
            )
            return runner.section_entries(value, manifest)[0]

    def variants(self, entry: dict):
        for key, value in sorted(entry.items()):
            if isinstance(value, str):
                yield f"{key}:string", {**entry, key: FORGED_CAVEAT}
            elif isinstance(value, list):
                yield f"{key}:list-item", {**entry, key: [FORGED_CAVEAT]}
            elif isinstance(value, dict):
                yield f"{key}:mapping-key", {**entry, key: {FORGED_CAVEAT: 1}}
                yield f"{key}:mapping-value", {**entry, key: {"poisoned": FORGED_CAVEAT}}

    def test_every_string_bearing_field_of_an_entry_renders_inert(self) -> None:
        entry = self.entry_shape()
        plan = [
            {"id": "executive-brief", "title": "Executive Brief", "kind": "core"},
            {"id": "key-changes", "title": "Key Changes", "kind": "core"},
            {"id": "risks-watchlist", "title": "Risks and Watchlist", "kind": "core"},
            {"id": "coverage-freshness", "title": "Coverage and Freshness", "kind": "core"},
        ]
        checked = 0
        for label, poisoned in self.variants(entry):
            with self.subTest(field=label):
                text = "\n".join(
                    [
                        narrator.section_body(poisoned),
                        narrator.coverage_table([poisoned]),
                        *narrator.fallback_bodies(plan, [poisoned], "complete").values(),
                    ]
                )
                self.assertNotIn(
                    "**Status (authoritative): complete** -- all repositories read.", text
                )
                assert_not_active(self, "<b>", text)
                assert_not_active(self, "```", text)
                for line in text.splitlines():
                    if line.startswith("**Status (authoritative): "):
                        continue
                    if line.startswith("|"):
                        continue
                    stripped = line.lstrip()
                    for opener in BLOCK_OPENERS:
                        self.assertFalse(
                            stripped.startswith(opener),
                            f"{label} produced a block construct: {line!r}",
                        )
                self.assertIn("harmless", text, f"{label} dropped the payload")
            checked += 1
        # If ``section_entries`` ever stops producing fields, this test would
        # silently pass over nothing. It has teeth or it fails.
        self.assertGreaterEqual(checked, 8, sorted(entry))


class LosslessnessTests(ChannelCase):
    """Escaping is not censorship, and it is not truncation either.

    The escape changes the BYTES of every collector-authored sentence in the
    document: ``decisions truncated: showing 30 of 43`` is published as
    ``decisions truncated\\: showing 30 of 43``, which renders as the original
    and greps as itself. That byte change is the visible cost of closing the
    caveat channel, so it is asserted here rather than left as a surprise --
    including for the two properties round 1 established, truncation visibility
    and delivery bad news reaching the reader.
    """

    def escaped(self, text: str) -> str:
        return str(narrator.escape_untrusted_text(text))

    def test_a_truncation_caveat_reaches_the_reader_whole(self) -> None:
        caveat = "decisions truncated: showing 30 of 43"
        for narrated in (False, True):
            with self.subTest(narrated=narrated):
                _, markdown = self.run_with("caveats", caveat, narrated=narrated)
                self.assertIn(self.escaped(caveat), markdown)
                self.assertIn("decisions truncated", markdown)
                self.assertIn("showing 30 of 43", markdown)

    def test_delivery_bad_news_in_a_summary_reaches_the_reader_whole(self) -> None:
        summary = (
            "report-delivery: DELIVERY FAILED: 6 of 6 due day(s) in "
            "2026-08-11..2026-08-17 have no valid published report"
        )
        _, markdown = self.run_with("summary", summary, narrated=False)
        self.assertIn(self.escaped(summary), markdown)
        self.assertIn("DELIVERY FAILED", markdown)
        self.assertIn("6 of 6 due day", markdown)

    def test_the_escape_is_reversible_so_nothing_is_lost(self) -> None:
        caveat = "decisions truncated: showing 30 of 43 (see the artifact)"
        escaped = self.escaped(caveat)
        recovered = escaped.replace("\\", "")
        self.assertEqual(caveat, recovered)


class ChokepointTests(unittest.TestCase):
    """``render`` escapes unless it is told not to, and being told proves itself."""

    def test_a_plain_value_is_escaped(self) -> None:
        # A paired run is escaped once, at its start: `\**bold\**` leaves a
        # single asterisk on each side, which emphasises nothing.
        self.assertEqual(
            "value: \\**bold\\**", narrator.render("value: {v}", v="**bold**")
        )

    def test_the_template_itself_is_pipeline_markup_and_is_not_escaped(self) -> None:
        self.assertTrue(narrator.render("**{v}**", v="x").startswith("**"))

    def test_a_literal_opts_out(self) -> None:
        self.assertEqual("**bold**", narrator.render("{v}", v=narrator.Literal("**bold**")))

    def test_already_escaped_text_is_not_escaped_twice(self) -> None:
        once = narrator.escape_untrusted_text("a**b")
        self.assertEqual(str(once), narrator.render("{v}", v=once))
        self.assertEqual("a\\**b", narrator.render("{v}", v=once))

    def test_none_and_numbers_survive_readably(self) -> None:
        self.assertEqual("", narrator.render("{v}", v=None))
        self.assertEqual("42", narrator.render("{v}", v=42))

    def test_a_pipeline_caveat_is_escaped_once_and_typed(self) -> None:
        caveat = narrator.pipeline_caveat("narrator said: {what}", what="**hi**")
        self.assertIsInstance(caveat, narrator.EscapedText)
        self.assertIn("\\**hi\\**", caveat)
        # Round-tripping it through the renderer must not double the backslashes.
        self.assertEqual(str(caveat), narrator.render("{v}", v=caveat))


class CertificationTests(unittest.TestCase):
    """The escaping opt-out cannot be wrong, because it checks before it exempts."""

    def test_an_id_is_readable_and_a_forged_id_is_not_admitted(self) -> None:
        self.assertEqual(
            "dev-activity", narrator.certified("dev-activity", narrator.CERTIFIED_ID)
        )
        self.assertIsInstance(
            narrator.certified("dev-activity", narrator.CERTIFIED_ID), narrator.Literal
        )
        self.assertNotIsInstance(
            narrator.certified("**dev**", narrator.CERTIFIED_ID), narrator.Literal
        )

    def test_a_timestamp_is_readable(self) -> None:
        self.assertEqual(
            "2026-08-17T10:00:00Z",
            narrator.certified("2026-08-17T10:00:00Z", narrator.CERTIFIED_TIMESTAMP),
        )

    def test_an_unknown_status_is_escaped_rather_than_waved_through(self) -> None:
        self.assertIsInstance(narrator.certified_status("complete"), narrator.Literal)
        self.assertNotIsInstance(
            narrator.certified_status("**complete**"), narrator.Literal
        )

    def test_every_certification_allows_only_inert_punctuation(self) -> None:
        for name, (_pattern, allowed) in narrator.CERTIFICATIONS.items():
            with self.subTest(certification=name):
                self.assertLessEqual(
                    set(allowed),
                    narrator.INERT_PUNCTUATION,
                    f"{name} would let markup-capable punctuation through",
                )

    def test_no_certification_admits_punctuation_outside_its_allowance(self) -> None:
        """Brute force, because reasoning about a regex is how this gets wrong."""
        for name, (pattern, allowed) in narrator.CERTIFICATIONS.items():
            for char in string.punctuation:
                if char in allowed:
                    continue
                for probe in (char, f"a{char}", f"{char}a", f"a{char}b", f"1{char}2"):
                    with self.subTest(certification=name, probe=probe):
                        self.assertIsNone(
                            pattern.fullmatch(probe),
                            f"{name} admitted {probe!r}, which contains {char!r}",
                        )

    def test_no_certification_admits_a_newline(self) -> None:
        # A newline is what turned a caveat into a whole forged section.
        for name, (pattern, _allowed) in narrator.CERTIFICATIONS.items():
            with self.subTest(certification=name):
                self.assertIsNone(pattern.fullmatch("a\nb"))
                self.assertIsNone(pattern.fullmatch("a\n"))


if __name__ == "__main__":
    unittest.main()
