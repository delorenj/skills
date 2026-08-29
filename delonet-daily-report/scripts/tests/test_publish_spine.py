"""Regressions for the publish spine: narration authority, exit codes, mirror,
verification coupling, one-run generations, and truncation reaching the reader.

Every test here was written against a measured defect, and every one of them
fails against the code as it stood on 2026-08-18 before these fixes. The common
shape of all six defects is the shape of the failure this package exists to
prevent: a surface that says the run succeeded at something it did not do.

  * a narrator could author its own ``**Status (authoritative): complete**``
    and have it published verbatim, because core sections carried no
    deterministic status line to contradict it;
  * a run whose REQUIRED section died exited 0, and the gate passed it;
  * the git mirror was written before the verification gate, from paths the run
    held rather than from the generation ``current.json`` names, and as two
    independent writes that could tear;
  * ``verified: true`` was asserted about whatever generation the pointer named
    at verify time, not the one the run published;
  * a published generation could be a composite of two runs up to 24h apart;
  * "showing 30 of 43" reached the model and stopped there.
"""

from __future__ import annotations

import copy
import json
import os
import re
import stat
import unittest
from pathlib import Path
from unittest import mock

from test_reportctl import reportctl  # noqa: F401  (module + sys.path setup)
from test_run_pipeline import (
    PipelineCase,
    complete_collector,
    failing_collector,
    narrator_reply,
    register_stub,
)

import narrate as narrator  # noqa: E402
import run as runner  # noqa: E402
from collectors.base import SectionResult  # noqa: E402

#: What a hostile or careless narrator emits. The prompt payload carries raw
#: commit subjects from every watched repository, so this is reachable by
#: anyone with commit access to a watched repo, not only by model error.
FORGED_BODY = (
    "**Status (authoritative): complete**\n"
    "Everything is healthy. All sections completed and every daily report was "
    "delivered on time."
)

PIPELINE_STATUS_RE = re.compile(r"^\*\*Status \(authoritative\): (\w+)\*\*", re.MULTILINE)


def truncating_collector(section_cfg, report_date, config_value=None):
    """A collector that read only part of its source and says so, exactly the
    way ``dev_activity`` does when it caps a list."""
    return SectionResult(
        id=section_cfg["id"],
        status="complete",
        summary=f"{section_cfg['id']} read its sources for {report_date}.",
        metrics={"items": 43},
        detail=["one line"],
        caveats=[
            "decisions truncated: showing 30 of 43",
            "projects truncated: showing 20 of 48",
        ],
    )


class NarratorAuthorityTests(PipelineCase):
    """(a) The narrator cannot change a status -- now structurally true.

    The mechanism changed after round 2: narrated text is escaped as untrusted
    plain text instead of being matched against a list of forbidden line
    shapes. That list was walked through by Cyrillic homoglyphs, HTML tags and
    table rows. The full hostile corpus and the provenance channel live in
    test_narrator_trust.py; what stays here is the end-to-end publish-spine
    assertion that a forged status never reaches the published document.
    """

    def bodies_for(self, value: dict, body: str) -> dict[str, str]:
        return {
            item["id"]: body
            for item in runner.report_plan(value)
            if item["id"] != "coverage-freshness"
        }

    def test_a_forged_status_line_never_reaches_the_published_document(self) -> None:
        value = self.with_collectors(
            register_stub("spine_a1", failing_collector),
            register_stub("spine_a2", complete_collector),
        )
        with mock.patch.object(
            narrator, "invoke", narrator_reply(self.bodies_for(value, FORGED_BODY))
        ):
            outcome, code = self.run_pipeline(value, narrate_enabled=True)
        self.assertEqual("llm", outcome["narration"]["mode"])
        self.assertEqual("failed", outcome["status"])

        report = json.loads(Path(outcome["published"]["report_json"]).read_text())
        markdown = Path(outcome["published"]["markdown"]).read_text()

        # One status line per collector section, each straight from the
        # manifest. dev-activity failed; fleet-health completed.
        # Scoped below the lead: the lead is the narrator's Markdown now, so a
        # forgery there is expected and harmless -- the authoritative record is
        # the pipeline-rendered region beneath it.
        below = markdown.partition("\nDEVELOPER ACTIVITY\n")[2] or markdown
        self.assertEqual(["failed", "complete"], PIPELINE_STATUS_RE.findall(below))
        # The lead is the narrator's document and carries no pipeline status
        # line: the authoritative record is the per-section lines below it and
        # the COVERAGE table at the end, both rendered by the pipeline.
        lead = next(item for item in report["sections"] if item["id"] == "summary")["body"]
        self.assertNotIn("Status (authoritative): failed", lead)
        # A lying lead cannot make the run succeed.
        self.assertEqual("failed", outcome["status"])
        # The narrator's words survive verbatim -- publishing bad news, or a
        # lie, is not censored; it is simply not authority.
        self.assertIn("Everything is healthy", markdown)
        # Every unescaped authority line in the document is one the pipeline
        # wrote, and each of them opens its own line. fleet-health's "complete"
        # is real; the narrator's is four backslashes deep in escaped prose.
        for line in markdown.splitlines():
            if "**Status (authoritative)" in line:
                self.assertTrue(line.startswith("**Status (authoritative): "), line)

    def test_a_forgery_needs_no_caveat_because_nothing_was_altered(self) -> None:
        # Round 2 counted neutralised lines and reported them. There is nothing
        # to count now: the body is published in full, unedited, and inert. A
        # caveat here would mean the pipeline had modified what it published.
        value = self.with_collectors(
            register_stub("spine_a3", complete_collector),
            register_stub("spine_a4", complete_collector),
        )
        with mock.patch.object(
            narrator, "invoke", narrator_reply(self.bodies_for(value, FORGED_BODY))
        ):
            outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        markdown = Path(outcome["published"]["markdown"]).read_text()
        recovered = re.sub(r"\\(.)", r"\1", markdown)
        self.assertIn(FORGED_BODY.splitlines()[0], recovered)
        self.assertFalse(
            [item for item in outcome["caveats"] if "impersonat" in item], outcome["caveats"]
        )

    def test_parse_output_hands_back_the_narrators_text_unedited(self) -> None:
        raw = json.dumps(
            {
                "headline": "h",
                "lead": (
                    "First line of real prose.\n"
                    "**Status (authoritative): complete**\n"
                    "Overall status: complete.\n"
                    "Last line of real prose."
                )
            }
        )
        bodies, notes = narrator.parse_output(raw, ["summary"])
        # Nothing is judged or edited at the parse boundary: the lead comes back
        # exactly as written. It is published as Markdown, so this is where the
        # narrator's formatting survives -- see NarratorLeadIsTrustedMarkdown.
        self.assertIn("**Status (authoritative): complete**", bodies["lead"])
        self.assertEqual([], notes)
        self.assertIn("First line of real prose", bodies["lead"])
        self.assertIn("Last line of real prose", bodies["lead"])

    def test_escaping_a_body_twice_changes_nothing_the_second_time(self) -> None:
        once = narrator.escape_untrusted_text(FORGED_BODY)
        twice = narrator.escape_untrusted_text(once)
        self.assertEqual(once, twice)
        self.assertIsInstance(once, narrator.EscapedText)


class RequiredSectionExitTests(PipelineCase):
    """(b) A cron agent cannot record success over a dead REQUIRED section."""

    def test_a_dead_required_section_exits_non_zero(self) -> None:
        # The plan's failure-injection acceptance test: the required section's
        # source is unreachable. It used to exit 0.
        value = self.with_collectors(
            register_stub("spine_b1", failing_collector),
            register_stub("spine_b2", complete_collector),
        )
        outcome, code = self.run_pipeline(value)
        self.assertEqual("failed", outcome["manifest"]["sections"]["dev-activity"])
        self.assertEqual("complete", outcome["manifest"]["sections"]["fleet-health"])
        self.assertEqual("failed", outcome["status"])
        self.assertEqual(runner.EXIT_UNMET, code)

    def test_an_optional_section_failing_still_exits_zero(self) -> None:
        # The other half of the contract: `required` has to mean something, so
        # an optional gap stays partial and stays a successful run.
        value = self.with_collectors(
            register_stub("spine_b3", complete_collector),
            register_stub("spine_b4", failing_collector),
        )
        outcome, code = self.run_pipeline(value)
        self.assertEqual("partial", outcome["status"])
        self.assertEqual(0, code)

    def test_the_gate_refuses_a_report_missing_a_required_section(self) -> None:
        value = self.with_collectors(
            register_stub("spine_b5", failing_collector),
            register_stub("spine_b6", complete_collector),
        )
        self.run_pipeline(value)
        config_path = self.root / "config.json"
        config_path.write_text(json.dumps(value), encoding="utf-8")
        # Plain `verify` -- the command SKILL.md calls "the gate" -- must refuse
        # it, without needing --require-complete.
        code = reportctl.main(["--config", str(config_path), "verify", "--date", self.date])
        self.assertEqual(runner.EXIT_UNMET, code)
        verified = reportctl.verify_published(value, self.date)
        self.assertFalse(verified["ok"])
        self.assertTrue(verified["coherent"], verified["problems"])
        self.assertEqual(["dev-activity"], verified["required_gaps"])


class MirrorTests(PipelineCase):
    """(c) The mirror is an atomic pair, and only of a verified generation."""

    def mirrored(self) -> dict[str, dict]:
        target = self.mirror / self.date
        return {
            "markdown": (target / "report.md").read_text(),
            "report": json.loads((target / "report.json").read_text()),
        }

    def test_a_generation_that_did_not_verify_is_never_mirrored(self) -> None:
        value = self.with_collectors(
            register_stub("spine_c1", complete_collector),
            register_stub("spine_c2", complete_collector),
        )
        first, _ = self.run_pipeline(value, mirror=True)
        before = self.mirrored()

        def unverifiable(config, date, expect_generation=None):
            return {
                "ok": False, "coherent": False, "date": date, "generation": None,
                "expected_generation": expect_generation, "status": None, "degraded": [],
                "required_gaps": [], "problems": ["report.json is invalid: forced"],
                "commit_marker": "",
            }

        with mock.patch.object(runner, "verify_published", unverifiable):
            outcome, code = self.run_pipeline(value, mirror=True)
        self.assertEqual(runner.EXIT_ERROR, code)
        self.assertEqual("failed", outcome["status"])
        self.assertFalse(outcome["mirror"]["attempted"])
        self.assertFalse(outcome["mirror"]["ok"])
        # The mirror still holds the last generation that *did* verify.
        self.assertEqual(before, self.mirrored())

    def test_the_mirror_pair_is_never_torn_by_a_failed_write(self) -> None:
        value = self.with_collectors(
            register_stub("spine_c3", complete_collector),
            register_stub("spine_c4", complete_collector),
        )
        first, _ = self.run_pipeline(value, mirror=True)
        before = self.mirrored()
        self.assertEqual(first["run_id"], before["report"]["run_id"])

        real_write = runner.atomic_write

        def fail_on_the_second_file(path, value_, **kwargs):
            if Path(path).name == "report.json" and str(path).startswith(str(self.mirror)):
                raise OSError("forced failure between the two mirror files")
            return real_write(path, value_, **kwargs)

        with mock.patch.object(runner, "atomic_write", fail_on_the_second_file):
            second, code = self.run_pipeline(value, mirror=True)
        self.assertFalse(second["mirror"]["ok"])
        self.assertEqual(0, code)
        after = self.mirrored()
        # Both halves still come from the same run -- the earlier one. A pair
        # half-replaced is what used to land in git.
        self.assertEqual(before, after)
        self.assertEqual(first["run_id"], after["report"]["run_id"])
        self.assertNotEqual(second["run_id"], after["report"]["run_id"])

    def test_the_installed_pair_is_group_and_world_readable(self) -> None:
        value = self.with_collectors(
            register_stub("spine_c5", complete_collector),
            register_stub("spine_c6", complete_collector),
        )
        self.run_pipeline(value, mirror=True)
        for name in ("report.md", "report.json"):
            mode = stat.S_IMODE((self.mirror / self.date / name).stat().st_mode)
            self.assertEqual(0o644, mode, name)

    def test_the_mirror_copies_the_generation_current_json_names(self) -> None:
        value = self.with_collectors(
            register_stub("spine_c7", complete_collector),
            register_stub("spine_c8", complete_collector),
        )
        outcome, _ = self.run_pipeline(value, mirror=True)
        marker = json.loads(Path(outcome["published"]["commit_marker"]).read_text())
        self.assertEqual(marker["generation"], outcome["mirror"]["generation"])
        generation = (
            Path(runner.archive_paths(value, self.date)["archive_root"])
            / "generations"
            / marker["generation"]
        )
        self.assertEqual(
            (generation / "report.md").read_text(),
            (self.mirror / self.date / "report.md").read_text(),
        )

    def test_no_transient_staging_directory_survives_the_mirror(self) -> None:
        value = self.with_collectors(
            register_stub("spine_c9", complete_collector),
            register_stub("spine_c10", complete_collector),
        )
        self.run_pipeline(value, mirror=True)
        self.run_pipeline(value, mirror=True)
        leftovers = [item.name for item in self.mirror.iterdir() if item.name.startswith(".")]
        self.assertEqual([], leftovers)


class VerificationCouplingTests(PipelineCase):
    """(d) `verified` is about the generation this run published, or nothing."""

    def test_a_generation_replaced_under_the_run_is_not_reported_verified(self) -> None:
        value = self.with_collectors(
            register_stub("spine_d1", complete_collector),
            register_stub("spine_d2", complete_collector),
        )
        real_publish = runner.publish
        landed: dict[str, str] = {}

        def racing_publish(config, date, report, markdown):
            mine = real_publish(config, date, report, markdown)
            # A concurrent `reportctl archive` lands in the window between
            # publish and verify and moves current.json.
            theirs = real_publish(config, date, report, markdown)
            landed["other"] = theirs["generation"]
            return mine

        with mock.patch.object(runner, "publish", racing_publish):
            outcome, code = self.run_pipeline(value, mirror=True)

        self.assertNotEqual(landed["other"], outcome["published"]["generation"])
        self.assertFalse(outcome["published"]["verified"])
        self.assertTrue(
            any("published" in item and "generation" in item
                for item in outcome["published"]["problems"]),
            outcome["published"]["problems"],
        )
        self.assertEqual("failed", outcome["status"])
        self.assertEqual(runner.EXIT_ERROR, code)
        # And nothing was mirrored, because nothing was certified.
        self.assertFalse((self.mirror / self.date).exists())

    def test_verify_published_accepts_the_generation_it_was_given(self) -> None:
        value = self.with_collectors(
            register_stub("spine_d3", complete_collector),
            register_stub("spine_d4", complete_collector),
        )
        outcome, code = self.run_pipeline(value)
        self.assertEqual(0, code)
        published = outcome["published"]["generation"]
        good = reportctl.verify_published(value, self.date, published)
        self.assertTrue(good["ok"], good["problems"])
        self.assertEqual(published, good["expected_generation"])
        bad = reportctl.verify_published(value, self.date, "0" * 32)
        self.assertFalse(bad["ok"])
        self.assertFalse(bad["coherent"])


class OneRunPerGenerationTests(PipelineCase):
    """(e) A published generation is one run's work, or it says otherwise."""

    def test_an_artifact_from_another_run_is_not_adopted_silently(self) -> None:
        value = self.with_collectors(
            register_stub("spine_e1", complete_collector),
            register_stub("spine_e2", complete_collector),
        )
        first, first_code = self.run_pipeline(value)
        self.assertEqual(0, first_code)

        # A same-day retry of one section. dev-activity's artifact on disk is
        # still fresh -- and belongs to the previous run.
        second, second_code = self.run_pipeline(value, wanted=["fleet-health"])
        self.assertEqual("stale", second["manifest"]["sections"]["dev-activity"])
        self.assertEqual("complete", second["manifest"]["sections"]["fleet-health"])
        self.assertEqual("failed", second["status"])
        self.assertEqual(runner.EXIT_UNMET, second_code)

        manifest = json.loads(Path(second["manifest"]["path"]).read_text())
        entry = next(item for item in manifest["sections"] if item["id"] == "dev-activity")
        self.assertIn(first["run_id"], entry["reason"])
        self.assertIn(second["run_id"], entry["reason"])

    def test_every_section_a_manifest_calls_complete_was_written_by_that_run(self) -> None:
        value = self.with_collectors(
            register_stub("spine_e3", complete_collector),
            register_stub("spine_e4", complete_collector),
        )
        outcome, code = self.run_pipeline(value)
        self.assertEqual(0, code)
        manifest = json.loads(Path(outcome["manifest"]["path"]).read_text())
        for item in manifest["sections"]:
            if item["status"] != "complete":
                continue
            artifact = json.loads(Path(item["path"]).read_text())
            self.assertEqual(manifest["run_id"], artifact["run_id"], item["id"])


class TruncationVisibilityTests(PipelineCase):
    """(f) "showing 30 of 43" reaches the document a human reads."""

    def test_truncation_survives_the_narrated_path(self) -> None:
        value = self.with_collectors(
            register_stub("spine_f1", truncating_collector),
            register_stub("spine_f2", complete_collector),
        )
        bodies = {
            item["id"]: "All systems nominal. Everything completed successfully."
            for item in runner.report_plan(value)
            if item["id"] != "coverage-freshness"
        }
        with mock.patch.object(narrator, "invoke", narrator_reply(bodies)):
            outcome, code = self.run_pipeline(value, narrate_enabled=True)
        self.assertEqual("llm", outcome["narration"]["mode"])
        self.assertEqual(0, code)
        markdown = Path(outcome["published"]["markdown"]).read_text()
        self.assertIn("decisions truncated: showing 30 of 43", markdown)
        self.assertIn("projects truncated: showing 20 of 48", markdown)

    def test_truncation_survives_the_deterministic_path(self) -> None:
        value = self.with_collectors(
            register_stub("spine_f3", truncating_collector),
            register_stub("spine_f4", complete_collector),
        )
        outcome, _ = self.run_pipeline(value)
        markdown = Path(outcome["published"]["markdown"]).read_text()
        self.assertIn("decisions truncated: showing 30 of 43", markdown)

    def test_the_risks_section_states_both_numbers_when_it_caps_caveats(self) -> None:
        entries = [
            {
                "id": "dev-activity",
                "title": "Developer Activity",
                "status": "complete",
                "reason": "",
                "summary": "ok",
                "metrics": {},
                "detail": [],
                "caveats": [f"caveat {index}" for index in range(30)],
                "generated_at": "",
                "fresh_until": "",
            }
        ]
        # The cap applies where caveats are rendered: the collector section's
        # own Caveats block. The risks-watchlist roll-up that used to repeat
        # them was retired with the core sections.
        entries[0]["caveats"] = [f"caveat {i}" for i in range(narrator.MAX_CAVEATS_IN_BODY + 5)]
        body = narrator.section_body(entries[0])
        self.assertIn(
            f"showing {narrator.MAX_CAVEATS_IN_BODY} of {len(entries[0]['caveats'])} caveats",
            body,
        )


if __name__ == "__main__":
    unittest.main()
