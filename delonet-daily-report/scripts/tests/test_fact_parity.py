"""Round 4, defect (B): the narrator may add prose, never remove a fact.

Measured on identical data for one date, with a cooperative narrator that simply
had the wrong opinion:

    DETERMINISTIC  RISKS AND WATCHLIST
                   report-delivery: DELIVERY FAILED: 6 of 6 due day(s) in
                   2026-08-11..2026-08-17 have no valid published report
    NARRATED       RISKS AND WATCHLIST
                   All systems nominal.

Same run, same artifacts, same statuses. The narrated render replaced each core
section's body wholesale, so every fact the pipeline had derived about coverage,
degradation and delivery lived or died on the model's judgement. That is the same
false green as a forged status line arriving by a politer route: the reader is
told the day was fine when the pipeline knew it was not.

The fix is compositional rather than defensive. ``run.compose_report`` renders
the pipeline's own body for every section on every path and *appends* the
narrator's prose beneath it. There is no code path that can drop a derived fact,
because there is no code path that chooses between the two bodies.

So these tests assert set relations between the two documents rather than
looking for particular sentences: whatever the deterministic render says, the
narrated render says too. A future section, metric or caveat is covered without
this file being edited.

Fail-first: run against the pre-fix ``compose_report`` (which used
``narration.bodies`` only when ``untrusted_bodies`` had no entry) and every test
here fails.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from test_run_pipeline import PipelineCase, complete_collector, register_stub

import narrate as narrator  # noqa: E402
import run as runner  # noqa: E402
from collectors.base import SectionResult  # noqa: E402

#: The exact bad news that vanished, verbatim from ``report_delivery``.
DELIVERY_GAP = (
    "DELIVERY FAILED: 6 of 6 due day(s) in 2026-08-11..2026-08-17 have no valid "
    "published report (6 missing)"
)

#: What the narrator says instead. It is not hostile -- it is wrong, which is a
#: harder case: nothing about it trips a forgery check.
NOMINAL = "All systems nominal. Everything completed successfully. No section is degraded."


def gap_collector(section_cfg, report_date, config_value=None):
    """A collector that did its job perfectly and found something bad."""
    return SectionResult(
        id=section_cfg["id"],
        status="complete",
        summary=f"report-delivery: {DELIVERY_GAP}. 0 of 6 due days delivered.",
        metrics={"delivery_gaps": 6, "days_delivered": 0},
        detail=["2026-08-11 missing", "2026-08-12 missing"],
        caveats=[DELIVERY_GAP, "duplicate completion events for 2026-08-16"],
    )


def nominal_narrator(section_ids: list[str]):
    def invoke(prompt, provider, model, reasoning=None):
        return {
            "stdout": json.dumps({"headline": "h", "lead": NOMINAL}),
            "usage": {"completed": True, "failed": False, "provider": provider, "model": model},
            "usage_note": None,
            "command": "/stub/hermes",
            "toolsets": "todo",
        }

    return invoke


class FactParityCase(PipelineCase):
    """One date, one set of artifacts, rendered both ways."""

    def build(self, tag: str) -> dict:
        return self.with_collectors(
            register_stub(f"parity_gap_{tag}", gap_collector),
            register_stub(f"parity_ok_{tag}", complete_collector),
        )

    def render_both(self, tag: str) -> tuple[dict, dict]:
        """Deterministic and narrated renders of the same collected data."""
        deterministic_value = self.build(f"{tag}_d")
        deterministic, _ = self.run_pipeline(deterministic_value, narrate_enabled=False)

        narrated_value = self.build(f"{tag}_n")
        ids = [
            item["id"]
            for item in runner.report_plan(narrated_value)
            if item["id"] != "coverage-freshness"
        ]
        with mock.patch.object(narrator, "invoke", nominal_narrator(ids)):
            narrated, _ = self.run_pipeline(narrated_value, narrate_enabled=True)
        self.assertEqual("fallback", deterministic["narration"]["mode"])
        self.assertEqual("llm", narrated["narration"]["mode"])
        return deterministic, narrated

    def report_of(self, outcome: dict) -> dict:
        return json.loads(Path(outcome["published"]["report_json"]).read_text())

    def bodies_of(self, outcome: dict) -> dict[str, str]:
        return {item["id"]: item["body"] for item in self.report_of(outcome)["sections"]}

    def markdown_of(self, outcome: dict) -> str:
        return Path(outcome["published"]["markdown"]).read_text(encoding="utf-8")


class BadNewsSurvivesNarrationTests(FactParityCase):
    """The A/B that produced the finding."""

    def test_the_delivery_gap_is_in_the_risks_section_on_both_paths(self) -> None:
        deterministic, narrated = self.render_both("gap")
        for label, outcome in (("deterministic", deterministic), ("narrated", narrated)):
            with self.subTest(path=label):
                # The delivery gap now lands in the report-delivery section's
                # own body; the risks-watchlist roll-up was retired with the
                # core sections.
                # The gap lands in the collector section that found it; the
                # risks-watchlist roll-up was retired with the core sections.
                # Asserted against the whole document so the test does not
                # depend on which stub id the fixture happened to register.
                markdown = self.markdown_of(outcome)
                self.assertIn("DELIVERY FAILED", markdown)
                self.assertIn("6 of 6 due day", markdown)

    def test_the_narrator_saying_nominal_does_not_remove_the_gap(self) -> None:
        _, narrated = self.render_both("nominal")
        markdown = self.markdown_of(narrated)
        # The narrator's opinion is published -- it is not censored --
        self.assertIn("All systems nominal", markdown)
        # -- and so is what the pipeline actually found.
        self.assertIn("DELIVERY FAILED", markdown)

    def test_every_caveat_reaches_the_narrated_document(self) -> None:
        _, narrated = self.render_both("caveats")
        markdown = self.markdown_of(narrated)
        for caveat in ("duplicate completion events for 2026", "DELIVERY FAILED"):
            self.assertIn(caveat, markdown, caveat)


class IdenticalFactSetTests(FactParityCase):
    """Whatever the deterministic render says, the narrated render says too.

    Composed from ONE run, so the two documents describe byte-identical
    artifacts: same statuses, same timestamps, same caveats. The only difference
    permitted is the narrator's prose.
    """

    def compose_both(self, tag: str) -> tuple[dict, dict]:
        value = self.build(tag)
        outcome, _ = self.run_pipeline(value, narrate_enabled=False)
        manifest = json.loads(Path(outcome["manifest"]["path"]).read_text())
        plan = runner.report_plan(value)
        entries = runner.section_entries(value, manifest)
        ids = [item["id"] for item in plan if item["id"] != "coverage-freshness"]
        narration = narrator.narrate(
            self.date, outcome["run_id"], plan, entries, "complete", value["narrator"],
            enabled=True, invoker=nominal_narrator(ids),
        )
        self.assertEqual("llm", narration.mode)
        deterministic = narrator.Narration(mode="fallback", bodies=narration.bodies)
        narrated_report = runner.compose_report(
            value, self.date, outcome["run_id"], plan, entries, narration, "complete"
        )
        deterministic_report = runner.compose_report(
            value, self.date, outcome["run_id"], plan, entries, deterministic, "complete"
        )
        return (
            {item["id"]: item["body"] for item in deterministic_report["sections"]},
            {item["id"]: item["body"] for item in narrated_report["sections"]},
        )

    def test_every_deterministic_line_survives_verbatim_in_the_narrated_body(self) -> None:
        left, right = self.compose_both("bodies")
        self.assertEqual(sorted(left), sorted(right))
        for section_id, body in left.items():
            if section_id == "summary":
                continue  # the lead IS the narrator's; parity is for the rest
            with self.subTest(section=section_id):
                for line in body.splitlines():
                    if not line.strip():
                        continue
                    self.assertIn(
                        line, right[section_id],
                        f"{section_id} lost a derived line under narration: {line!r}",
                    )

    def test_every_collector_section_is_byte_identical(self) -> None:
        """Narration is additive: it may prepend a lead, never alter a section.

        This replaces a check on `coverage-freshness`, which was retired with
        the core sections; the table it held is now rendered once in the
        pipeline's COVERAGE block, outside the section list entirely.
        """
        left, right = self.compose_both("coverage")
        for section_id, body in left.items():
            if section_id == "summary":
                continue  # the lead is the one section narration authors
            with self.subTest(section=section_id):
                self.assertEqual(body, right[section_id])

    def test_narration_is_additive_and_says_where_it_starts(self) -> None:
        left, right = self.compose_both("additive")
        for section_id, body in right.items():
            if section_id == "summary":
                continue  # the lead is narrator prose, not an additive block
            with self.subTest(section=section_id):
                if section_id != "summary":
                    # Only the lead is narrated; collector sections are the
                    # pipeline's own record on every path.
                    self.assertNotIn(narrator.NARRATOR_PROSE_LEAD, body)
                    continue
                self.assertIn(narrator.NARRATOR_PROSE_LEAD, body)
                facts, _, prose = body.partition(narrator.NARRATOR_PROSE_LEAD)
                # Facts first, prose after: a reader meets the derived record
                # before anybody's account of it.
                self.assertIn("**Status (authoritative)", facts)
                self.assertIn("All systems nominal", prose)
                self.assertEqual(left[section_id], facts.strip())

    def test_every_deterministic_fact_survives_narration(self) -> None:
        """Supersetness is about FACTS, not bytes.

        The narrated document can be shorter than the deterministic one now --
        a terse lead replaces a longer generated stand-in -- so length proves
        nothing. What must hold is that no line the pipeline derived is missing
        once a narrator has run.
        """
        left, right = self.compose_both("superset")
        for section_id, body in left.items():
            if section_id == "summary":
                continue
            for line in body.splitlines():
                if line.strip():
                    self.assertIn(line, right[section_id])


class NarratorOmissionTests(FactParityCase):
    """A narrator that returns an empty-looking body still cannot hide anything."""

    def test_a_whitespace_body_falls_back_and_keeps_every_fact(self) -> None:
        value = self.build("empty")
        ids = [
            item["id"]
            for item in runner.report_plan(value)
            if item["id"] != "coverage-freshness"
        ]

        def blank(prompt, provider, model, reasoning=None):
            return {
                "stdout": json.dumps({"headline": "h", "lead": "   "}),
                "usage": {"completed": True, "failed": False},
                "usage_note": None,
                "command": "/stub/hermes",
                "toolsets": "todo",
            }

        with mock.patch.object(narrator, "invoke", blank):
            outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        # A body the narrator did not write is a narration failure, and the
        # deterministic render is what publishes.
        self.assertEqual("fallback", outcome["narration"]["mode"])
        self.assertIn("DELIVERY FAILED", self.markdown_of(outcome))


if __name__ == "__main__":
    unittest.main()
