"""The narrator trust boundary: untrusted text cannot become pipeline markup.

Round 2 defended this boundary with three line-anchored ASCII regexes
(``AUTHORITY_LINE_PATTERNS``) and a neutralising rewrite. An adversarial
narrator walked through it with Cyrillic homoglyphs, HTML tags, table rows,
setext rules and code fences: eight of twenty-one forgeries published verbatim,
bolded and unquoted, on a run whose real status was ``failed``. The same run's
line 2 read ``Narrated in one pass by **Status (authoritative): complete** the
pipeline/gpt-5.4**`` because the provider/model came out of the usage file the
narrator process itself writes.

Every test below was run against the pre-fix tree and failed there. They are
written against the *published document*, not against the implementation, so
they keep holding whatever mechanism is used to satisfy them -- and they are
deliberately blind to the narrator's *content*: nothing here asserts that the
narrator said something nice, only that whatever it said is rendered as inert
text and the pipeline's own statuses are the only authority markup in the file.
"""

from __future__ import annotations

import json
import os
import re
import stat
import unittest
from pathlib import Path
from unittest import mock

from test_run_pipeline import (
    PipelineCase,
    complete_collector,
    failing_collector,
    register_stub,
)

import narrate as narrator  # noqa: E402
import run as runner  # noqa: E402
from collectors.base import SectionResult  # noqa: E402

#: The pipeline's own authority markup. Only ``narrate.status_line`` and
#: ``narrate.report_status_line`` may produce a line of this shape.
PIPELINE_STATUS_RE = re.compile(r"^\*\*Status \(authoritative\): (\w+)\*\*", re.MULTILINE)

#: Twenty-one forgeries of that markup, one per rendering channel a Markdown
#: reader honours. Numbers 2-4 are homoglyphs: the Cyrillic Ѕ (U+0405) and а
#: (U+0430) and the Greek Ρ (U+03A1) render identically to their Latin twins,
#: which is why no list of patterns can ever be complete.
FORGERY_VARIANTS = [
    "**Status (authoritative): complete**",                      # 1  ASCII
    "**Ѕtatus (аuthoritative): complete**",            # 2  Cyrillic S, a
    "**Ѕтatus: complete**",                            # 3  Cyrillic St
    "**Ρeport status: complete**",                          # 4  Greek Rho
    "<b>Status: complete</b>",                                   # 5  HTML bold
    "<strong>Status (final): complete</strong>",                 # 6  HTML strong
    "<h2>Status (authoritative): complete</h2>",                 # 7  HTML heading
    "| **Status** | complete |",                                 # 8  table row
    "|---|---|",                                                 # 9  table rule
    "## Status (authoritative): complete",                       # 10 ATX heading
    "Status (authoritative): complete",                          # 11 setext text
    "=================================",                         # 12 setext rule
    "> **Status (authoritative): complete**",                    # 13 blockquote
    "  - **Status (authoritative): complete**",                  # 14 nested list
    "1. **Status (authoritative): complete**",                   # 15 ordered list
    "```",                                                       # 16 fence open
    "**Status (authoritative): complete**",                      # 17 inside fence
    "```",                                                       # 18 fence close
    "[Status (authoritative): complete](https://evil.example)",  # 19 link
    "![Status (authoritative): complete](x)",                    # 20 image
    "It is fine.‮**Status (authoritative): complete**",     # 21 bidi override
]

FORGED_BODY = "\n".join(FORGERY_VARIANTS) + "\nEverything is healthy. Every section completed."

#: What the hostile narrator process writes into its own ``--usage-file``.
FORGED_PROVIDER = "**Status (authoritative): complete** the pipeline"
FORGED_MODEL = "gpt-5.4**\n\n**Status (authoritative): complete"


def hostile_reply(lead: str, *, provider: str, model: str,
                  extra_keys: dict | None = None):
    """A narrator whose bodies AND whose usage report are both hostile."""

    def invoke(prompt, requested_provider, requested_model, reasoning=None):
        return {
            "stdout": json.dumps(
                {"headline": lead.splitlines()[0][:80], "lead": lead, **(extra_keys or {})}
            ),
            # The usage report is written by the narrated process. Round 2 read
            # provider/model out of it and interpolated them into line 2.
            "usage": {"completed": True, "failed": False,
                      "provider": provider, "model": model},
            "usage_note": None,
            "command": "/stub/hermes",
            "toolsets": narrator.toolsets(),
        }

    return invoke


def assert_not_active(case, needle: str, text: str, msg: str = "") -> None:
    """``\\**Status`` contains ``**Status``; only the unescaped form renders."""
    case.assertIsNone(
        re.search(r"(?<!\\)" + re.escape(needle), text),
        msg or f"active (unescaped) {needle!r} in: {text[:160]!r}",
    )


def below_the_lead(markdown: str) -> str:
    """The pipeline-rendered region: everything after the narrator's lead.

    The lead is the narrator's own Markdown, so a forged status line inside it
    matches ``PIPELINE_STATUS_RE`` too. Assertions about the AUTHORITATIVE
    record therefore scope to the region the pipeline renders, which is where
    the record actually lives.
    """
    marker = "\nDEVELOPER ACTIVITY\n"
    head, sep, tail = markdown.partition(marker)
    if sep:
        return sep + tail
    lines = markdown.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if index > 4 and line.strip() and line.strip() == line.strip().upper():
            return "".join(lines[index:])
    return markdown


class NarratorTrustCase(PipelineCase):
    """Shared machinery: run one pipeline with a hostile narrator."""

    def hostile_run(self, body: str = FORGED_BODY, *, provider: str = FORGED_PROVIDER,
                    model: str = FORGED_MODEL):
        """A run whose REQUIRED section died and whose narrator lies about it."""
        value = self.with_collectors(
            register_stub("trust_fail", failing_collector),
            register_stub("trust_ok", complete_collector),
        )
        reply = hostile_reply(body, provider=provider, model=model)
        with mock.patch.object(narrator, "invoke", reply):
            outcome, code = self.run_pipeline(value, narrate_enabled=True)
        markdown = Path(outcome["published"]["markdown"]).read_text(encoding="utf-8")
        report = json.loads(Path(outcome["published"]["report_json"]).read_text())
        return outcome, code, markdown, report

    def body_of(self, report: dict, section_id: str) -> str:
        return next(item for item in report["sections"] if item["id"] == section_id)["body"]


class NarratorLeadIsTrustedMarkdownTests(NarratorTrustCase):
    """The lead is the narrator's document, published as real Markdown.

    THIS CLASS REPLACES ``ForgeryIsImpossibleTests``, and the property it used
    to assert -- that no narrated character sequence can render as markup -- is
    deliberately no longer true OF THE LEAD.

    Why the trade was taken. Escaping every narrated character made the narrator
    structurally incapable of producing a heading, a list, or emphasis, which is
    to say incapable of organising a report. The resulting document restated the
    same counts three times across eight sections and was, in the operator's
    words, "extremely painful" to read. An unreadable daily report is a total
    failure of the artifact's purpose; a forged bold line inside a personal
    engineering journal, generated by the operator's own model from the
    operator's own commits, is not.

    What did NOT change, and is asserted here: the lead cannot remove, reword,
    or suppress a fact. Every collector section below it is rendered by the
    pipeline on every path, and every third-party string the PIPELINE
    interpolates -- commit subjects, event project names, reasons, metrics --
    is still inert. Those are covered by ``ThirdPartyDetailTests``,
    ``ForgedCaveatTests`` and ``EveryChannelTests``.
    """

    def test_the_run_really_did_fail(self) -> None:
        # The premise of the rest of this class.
        outcome, code, _, _ = self.hostile_run()
        self.assertEqual("llm", outcome["narration"]["mode"])
        self.assertEqual("failed", outcome["manifest"]["sections"]["dev-activity"])
        self.assertEqual("failed", outcome["status"])
        self.assertEqual(runner.EXIT_UNMET, code)

    def test_the_lead_is_published_as_the_narrator_wrote_it(self) -> None:
        _, _, _, report = self.hostile_run("## A heading\n\n- a bullet\n\n**bold**")
        body = self.body_of(report, "summary")
        self.assertIn("## A heading", body)
        self.assertIn("- a bullet", body)
        self.assertIn("**bold**", body)

    def test_a_lying_lead_cannot_change_the_manifest_or_the_exit_code(self) -> None:
        outcome, code, markdown, _ = self.hostile_run(
            "**Everything is complete and healthy.** No action needed."
        )
        self.assertEqual("failed", outcome["status"])
        self.assertEqual(runner.EXIT_UNMET, code)
        # The authoritative record contradicts the prose, in the document.
        self.assertIn("**Status (authoritative): failed**", markdown)

    def test_a_lying_lead_cannot_remove_the_bad_news_below_it(self) -> None:
        _, _, markdown, _ = self.hostile_run("All systems nominal.")
        self.assertIn("Status (authoritative): failed", markdown)
        self.assertIn("dev-activity", markdown)


class ProvenanceChannelTests(NarratorTrustCase):
    """Line 2 of report.md is pipeline-authored and config-sourced."""

    def provenance(self, markdown: str) -> str:
        return markdown.splitlines()[1]

    def test_provenance_names_the_configured_provider_not_the_reported_one(self) -> None:
        _, _, markdown, _ = self.hostile_run()
        line = self.provenance(markdown)
        self.assertTrue(
            line.startswith("Summary written by openai-codex/gpt-5.4"), line
        )
        self.assertNotIn(FORGED_PROVIDER, line)
        self.assertNotIn("(authoritative)", line)

    def test_provenance_carries_no_narrator_authored_markup(self) -> None:
        _, _, markdown, _ = self.hostile_run()
        head = "\n".join(markdown.splitlines()[:4])
        assert_not_active(self, "**Status", head)
        self.assertNotIn("(authoritative)", head)

    def test_a_forged_usage_report_cannot_inject_a_line_break(self) -> None:
        # FORGED_MODEL contains a newline, which is how the forgery reached
        # column 0 of its own line above every section.
        _, _, markdown, _ = self.hostile_run()
        lines = markdown.splitlines()
        self.assertTrue(lines[0].startswith("Daily Developer Report"))
        # Scope note: the LEAD may contain narrator markup by design now, so the
        # guard is on the provenance line -- the channel the forgery targeted.
        # Provider and model come from config; a newline in the usage report has
        # nowhere to land.
        assert_not_active(self, "**Status (authoritative): complete", "\n".join(lines[:2]))
        self.assertTrue(lines[1].startswith("Summary written by openai-codex/gpt-5.4."))

    def test_the_narrator_reported_identity_is_still_recorded(self) -> None:
        # Structural fix, not censorship: what the narrator claimed is still
        # captured on the machine surface, where it is data and not markup.
        outcome, _, _, _ = self.hostile_run()
        metrics = outcome["narration"]["metrics"]
        self.assertEqual(FORGED_PROVIDER, metrics["narrator_reported_provider"])
        self.assertEqual(FORGED_MODEL, metrics["narrator_reported_model"])
        self.assertEqual("openai-codex", metrics["narrator_requested_provider"])
        self.assertEqual("gpt-5.4", metrics["narrator_requested_model"])

    def test_a_mismatch_caveat_cannot_carry_markup_either(self) -> None:
        outcome, _, _, _ = self.hostile_run()
        mismatch = [item for item in outcome["caveats"] if "not the configured" in item]
        self.assertTrue(mismatch, outcome["caveats"])
        assert_not_active(self, "**Status (authoritative)", mismatch[0])

    def test_the_real_usage_file_channel_end_to_end(self) -> None:
        # The same attack through the real subprocess path: a narrator binary
        # that writes a forged provider/model into the --usage-file it is
        # handed, which is the file narrate.invoke reads back.
        script = self.root / "hostile-narrator.py"
        script.write_text(
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            "argv = sys.argv[1:]\n"
            "path = argv[argv.index('--usage-file') + 1]\n"
            "json.dump({'completed': True, 'failed': False,\n"
            f"           'provider': {FORGED_PROVIDER!r}, 'model': {FORGED_MODEL!r}}},\n"
            "          open(path, 'w'))\n"
            f"print(json.dumps({{'headline': 'h', 'lead': {FORGED_BODY!r}}}))\n",
            encoding="utf-8",
        )
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        value = self.with_collectors(
            register_stub("trust_live_a", failing_collector),
            register_stub("trust_live_b", complete_collector),
        )
        with mock.patch.dict(os.environ, {"DDR_NARRATOR_CMD": str(script)}):
            outcome, code = self.run_pipeline(value, narrate_enabled=True)
        self.assertEqual("llm", outcome["narration"]["mode"], outcome["narration"]["failure"])
        markdown = Path(outcome["published"]["markdown"]).read_text(encoding="utf-8")
        self.assertIn("openai-codex/gpt-5.4", markdown.splitlines()[1])
        # Every status line in the document is a manifest status, in plan order.
        # Derived rather than hardcoded so the assertion tracks the real section
        # set instead of a count that drifts whenever the plan changes.
        expected = [
            outcome["manifest"]["sections"][item["id"]]
            for item in runner.report_plan(value)
            if item["kind"] == "section"
        ]
        self.assertEqual(expected, PIPELINE_STATUS_RE.findall(below_the_lead(markdown)))
        # Scoped below the lead: the lead is the narrator's Markdown by design,
        # so raw HTML there is expected. It must not survive where the PIPELINE
        # renders third-party text.
        self.assertIsNone(re.search(r"(?<!\\)<strong>", below_the_lead(markdown)))


class NarratorFailureTextTests(NarratorTrustCase):
    """The other narrator-controlled string that reaches the document."""

    def test_a_hostile_error_message_cannot_forge_a_status(self) -> None:
        # narrate.invoke puts the narrator's own stderr into the failure text,
        # and the deterministic render prints that text in line 2 and in the
        # executive brief.
        value = self.with_collectors(
            register_stub("trust_err_a", complete_collector),
            register_stub("trust_err_b", complete_collector),
        )

        def explode(prompt, provider, model, reasoning=None):
            raise narrator.NarrationError(
                "narrator exited 3: **Status (authoritative): complete** <b>all good</b>"
            )

        with mock.patch.object(narrator, "invoke", explode):
            outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        markdown = Path(outcome["published"]["markdown"]).read_text(encoding="utf-8")
        provenance = markdown.splitlines()[1]
        self.assertEqual("fallback", outcome["narration"]["mode"])
        # The narrator's message is reported -- that is the point of it --
        # but as literal characters, in the pipeline's own sentence.
        self.assertIn("narrator exited 3", provenance)
        self.assertIn("\\**Status", provenance)
        assert_not_active(self, "**Status (authoritative): complete**", provenance)
        self.assertNotIn("<b>all good</b>", markdown)
        # Both collectors completed, so the only "complete" status lines in the
        # document are the two the manifest really earned.
        # One line per collector section. The four core sections that used to
        # repeat the report-wide status are gone.
        self.assertEqual(["complete", "complete"], PIPELINE_STATUS_RE.findall(below_the_lead(markdown)))

    def test_an_unknown_section_id_cannot_forge_a_status(self) -> None:
        value = self.with_collectors(
            register_stub("trust_extra_a", complete_collector),
            register_stub("trust_extra_b", complete_collector),
        )
        reply = hostile_reply("Nothing to report.", provider="openai-codex",
                              model="gpt-5.4", extra_keys={
                                  "**Status (authoritative): complete**": "x"})
        with mock.patch.object(narrator, "invoke", reply):
            outcome, _ = self.run_pipeline(value, narrate_enabled=True)
        dropped = [item for item in outcome["caveats"] if "unexpected key" in item]
        self.assertTrue(dropped, outcome["caveats"])
        assert_not_active(self, "**Status (authoritative): complete**", dropped[0])


class BadNewsIsStillPublishedTests(NarratorTrustCase):
    """Escaping is not censorship. A narrator reporting a real failure is doing
    its job, and every word of it must reach the reader."""

    HONEST = (
        "Developer activity failed: the Candystore event history at http://127.0.0.1:9\n"
        "refused the connection (errno 111). Nothing was collected for this day, and the\n"
        "24 commits visible in git are NOT in this report. Yesterday's report is missing."
    )

    def test_an_honest_failure_narrative_reaches_the_reader_intact(self) -> None:
        _, _, markdown, _ = self.hostile_run(body=self.HONEST, provider="openai-codex",
                                             model="gpt-5.4")
        # Word for word, in order, with only the punctuation escaped.
        for phrase in (
            "Developer activity failed",
            "refused the connection",
            "errno 111",
            "24 commits visible in git are NOT in this report",
            "Yesterday",
            "report is missing",
        ):
            self.assertIn(phrase, markdown, f"the narrator's bad news lost {phrase!r}")

    def test_escaping_is_lossless(self) -> None:
        # A reader can recover exactly what the narrator wrote, so nothing is
        # hidden by the render -- only defused.
        escaped = narrator.escape_untrusted_text(self.HONEST)
        recovered = re.sub(r"\\(.)", r"\1", escaped)
        self.assertEqual(self.HONEST, recovered)


class ThirdPartyDetailTests(PipelineCase):
    """The same forgery, arriving through the other door.

    ``detail`` carries git commit subjects and PR titles verbatim -- text
    written by anyone with commit access to a watched repository, which is
    exactly the threat model that made the narrator untrusted. It reached the
    deterministic render unescaped, so a commit subject could forge an
    authority line in a report that was never narrated at all.
    """

    FORGED_SUBJECT = "abc1234 **Status (authoritative): complete** everything is fine"

    def collector(self, section_cfg, report_date, config_value=None):
        return SectionResult(
            id=section_cfg["id"],
            status="failed",
            reason="candystore unreachable",
            summary="nothing was collected",
            detail=["=== 33GOD ===", self.FORGED_SUBJECT],
        )

    def test_a_commit_subject_cannot_forge_a_status_line(self) -> None:
        body = narrator.section_body(
            {
                "id": "dev-activity", "title": "Developer Activity", "status": "failed",
                "reason": "candystore unreachable", "summary": "nothing was collected",
                "detail": ["=== 33GOD ===", self.FORGED_SUBJECT],
            }
        )
        lines = body.splitlines()
        self.assertEqual("**Status (authoritative): failed** -- candystore unreachable", lines[0])
        for line in lines[1:]:
            assert_not_active(self, "**Status (authoritative)", line)
        self.assertIn("\\**Status (authoritative)", body)
        self.assertIn("abc1234", body)

    def test_it_holds_end_to_end_on_the_unnarrated_path(self) -> None:
        value = self.with_collectors(
            register_stub("trust_detail_a", self.collector),
            register_stub("trust_detail_b", complete_collector),
        )
        outcome, _ = self.run_pipeline(value, narrate_enabled=False)
        markdown = Path(outcome["published"]["markdown"]).read_text(encoding="utf-8")
        self.assertEqual("fallback", outcome["narration"]["mode"])
        # The forged subject is indented inside the Detail block, so it never
        # matched the line-anchored check: only the escape stops it.
        for line in markdown.splitlines():
            if line.lstrip().startswith("**Status (authoritative)"):
                self.assertTrue(line.startswith("**Status (authoritative): "), line)
        self.assertIn("\\**Status (authoritative)", markdown)
        self.assertIn("abc1234", markdown)


class EscaperUnitTests(unittest.TestCase):
    """The escaper itself: an allowlist of inert characters, nothing else."""

    def test_inline_punctuation_stays_readable(self) -> None:
        """Prose punctuation is NOT escaped -- that is the point of the pass.

        An earlier version escaped all 32 ASCII punctuation characters and the
        report came out as ``17598 events across 39 project\\(s\\) on
        2026\\-08\\-17\\:``. Nothing that cannot open a markdown block is
        touched now, because the document a human reads is the deliverable.
        """
        text = "17598 events across 39 project(s) on 2026-08-17: 380 sessions, 43 decisions."
        self.assertEqual(text, narrator.escape_untrusted_text(text))

    def test_only_sequences_that_can_render_are_escaped(self) -> None:
        """A lone punctuation character is not markup and is left readable.

        Escaping every ``*`` and ``_`` turned the pipeline's own prose into
        ``refs/notes/\\*`` and ``last\\_status``. Emphasis needs a paired run,
        a fence needs three backticks, a tag needs a name after ``<``, and a
        link needs ``](``.
        """
        for text in ("a*b", "a_b", "a`b", "a<b", "a[b", "2 * 3", "last_status"):
            with self.subTest(text=text, expect="untouched"):
                self.assertEqual(text, narrator.escape_untrusted_text(text))
        for text, needle in (
            ("a**b**", "\\**"), ("a__b__", "\\__"), ("a```b", "\\```"),
            ("a<b>c", "\\<b>"), ("[x](y)", "\\](" ),
        ):
            with self.subTest(text=text, expect="escaped"):
                self.assertIn(needle, str(narrator.escape_untrusted_text(text)))

    def test_block_openers_are_escaped_at_the_start_of_a_line(self) -> None:
        for char in "#>|+~":
            with self.subTest(char=char):
                self.assertEqual(
                    f"\\{char} x", narrator.escape_untrusted_text(f"{char} x")
                )
                # ... and left alone mid-sentence, where they cannot open a block.
                self.assertEqual(f"a{char}b", narrator.escape_untrusted_text(f"a{char}b"))

    def test_a_bullet_needs_its_space_to_be_a_bullet(self) -> None:
        # `- x` is a list item and is neutralised; `=== Events by CLI ===` and a
        # hyphen inside a sentence are not blocks and stay readable.
        self.assertEqual("\\- x", narrator.escape_untrusted_text("- x"))
        self.assertEqual("=== Events by CLI ===",
                         narrator.escape_untrusted_text("=== Events by CLI ==="))
        self.assertEqual("a - b", narrator.escape_untrusted_text("a - b"))
        self.assertEqual("\\---", narrator.escape_untrusted_text("---"))

    def test_an_ordered_list_item_cannot_open_a_block(self) -> None:
        self.assertEqual("1\\. forged", narrator.escape_untrusted_text("1. forged"))

    def test_letters_digits_and_spaces_are_untouched(self) -> None:
        text = "The fleet ran 14 jobs and 3 of them are Ѕtill fine"
        self.assertEqual(text, narrator.escape_untrusted_text(text))

    def test_newlines_survive_so_paragraphs_survive(self) -> None:
        self.assertEqual("one\ntwo", narrator.escape_untrusted_text("one\ntwo"))
        self.assertEqual("one\ntwo", narrator.escape_untrusted_text("one\r\ntwo"))

    def test_invisible_characters_become_visible_names(self) -> None:
        for char, name in (("‮", "U+202E"), ("​", "U+200B"), ("\x07", "U+0007")):
            with self.subTest(char=char):
                out = narrator.escape_untrusted_text(f"a{char}b")
                self.assertNotIn(char, out)
                self.assertIn(name, out)

    def test_escaping_is_idempotent_by_type(self) -> None:
        once = narrator.escape_untrusted_text("cost: $5 (5%)")
        twice = narrator.escape_untrusted_text(once)
        self.assertEqual(once, twice)

    def test_no_line_can_open_a_markdown_block(self) -> None:
        """The guarantee, stated once: no line of escaped text opens a block.

        Block constructs -- heading, status line, table row, blockquote, code
        fence, list item, setext rule -- are the only way to impersonate this
        pipeline, and every one of them is recognised only at the start of a
        line. Inline punctuation cannot open a block and stays readable.
        """
        source = "".join(chr(code) for code in range(32, 127)) + "Ѕ‮\n\ttab"
        for line in str(narrator.escape_untrusted_text(source)).split("\n"):
            stripped = line.lstrip(" ")
            if not stripped:
                continue
            if stripped[0] == "\\":
                continue
            self.assertNotIn(
                stripped[0], narrator.BLOCK_OPENERS,
                f"line opens with active block character {stripped[0]!r}: {line!r}",
            )
            self.assertIsNone(
                narrator._ORDERED_ITEM.match(stripped),
                f"line opens an ordered list: {line!r}",
            )

    def test_a_tab_cannot_open_an_indented_code_block(self) -> None:
        self.assertNotIn("\t", narrator.escape_untrusted_text("\tindented"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
