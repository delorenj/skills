import contextlib
import io
import json
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import lint  # noqa: E402
from ar.common import ConfigError  # noqa: E402

FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "publish")


def read(name):
    with open(os.path.join(FX, name), encoding="utf-8") as fh:
        return fh.read()


def load(name):
    with open(os.path.join(FX, name), encoding="utf-8") as fh:
        return json.load(fh)


LINT_JSON = load("2026-09-03T0300-external.lint.json")
CLEAN = "# A fine title\n\n## What landed\nThe draft invoice path works end to end.\n"


def rules(findings, level=None):
    return [f.rule for f in findings if level is None or f.level == level]


class Always(unittest.TestCase):
    def test_clean_internal(self):
        findings = lint.lint(read("internal.raw.txt"), "internal", "SMK", {}, digest=load("internal.digest.json"))
        self.assertEqual(rules(findings, "error"), [])

    def test_title_line_missing(self):
        findings = lint.lint("No title\nbody", "internal", None, {})
        self.assertIn("title-line", rules(findings, "error"))

    def test_title_bounds(self):
        self.assertIn("title-length", rules(lint.lint("# " + "x" * 181 + "\nbody", "internal", None, {}), "error"))
        self.assertIn("title-length", rules(lint.lint("# x\nbody", "internal", None, {}), "error"))
        self.assertEqual(rules(lint.lint("# ok\nbody", "internal", None, {}), "error"), [])

    def test_body_bounds(self):
        self.assertIn("body-empty", rules(lint.lint("# T\n\n\n", "internal", None, {}), "error"))
        self.assertIn("body-length", rules(lint.lint("# T\n" + "y" * 5001, "internal", None, {}), "error"))
        self.assertEqual(rules(lint.lint("# Title\n" + "y" * 5000, "internal", None, {}), "error"), [])

    def test_placeholders(self):
        for text in ("TODO fix", "tktk", "XXX", "<placeholder>", "{{name}}", "Lorem Ipsum dolor"):
            findings = lint.lint(f"# T\nbody {text} here", "internal", None, {})
            self.assertIn("placeholder", rules(findings, "error"), text)
        self.assertEqual(rules(lint.lint("# Title\ntodos and maxxx", "internal", None, {}), "error"), [])

    def test_html_tag_warning(self):
        findings = lint.lint("# T\na <div>x</div> here", "internal", None, {})
        self.assertIn("html-tag", rules(findings, "warning"))
        self.assertNotIn("html-tag", rules(findings, "error"))

    def test_line_numbers(self):
        findings = lint.lint("# T\n\nfine\nTODO here", "internal", None, {})
        self.assertEqual([f.line for f in findings if f.rule == "placeholder"], [4])


class External(unittest.TestCase):
    def ext(self, body, identifier="SMK", config=None, lint_json=LINT_JSON, digest=None, title="A fine title"):
        return lint.lint(f"# {title}\n{body}", "external", identifier, config or {}, digest=digest, lint_json=lint_json)

    def test_ticket_key(self):
        self.assertIn("ticket-key", rules(self.ext("closed SMK-12 today"), "error"))
        self.assertIn("ticket-key", rules(self.ext("closed smk-12 today"), "error"))
        self.assertIn("ticket-key", rules(self.ext("x", title="SMK-9 done"), "error"))
        self.assertNotIn("ticket-key", rules(self.ext("closed ABC-12 today"), "error"))

    def test_extra_identifiers_and_lint_json_identifiers(self):
        self.assertIn("ticket-key", rules(self.ext("closed ABC-12", config={"extra_identifiers": ["ABC"]}), "error"))
        self.assertIn("ticket-key", rules(self.ext("closed XYZ-3", identifier=None, lint_json={"identifiers": ["XYZ"]}), "error"))

    def test_sha_and_hex_words(self):
        self.assertIn("sha", rules(self.ext("landed in a1b2c3d"), "error"))
        self.assertNotIn("sha", rules(self.ext("the defaced sign was effaced"), "error"))

    def test_abs_path(self):
        self.assertIn("abs-path", rules(self.ext("notes in /home/x/notes.md"), "error"))
        self.assertIn("abs-path", rules(self.ext("see /Users/x/y"), "error"))

    def test_vocabulary(self):
        for text, rule in (("the burndown is flat", "burndown"), ("burn down chart", "burndown"),
                           ("412 tool calls", "tool-calls"), ("one tool call", "tool-calls"),
                           ("in sprint 3", "sprint-number"), ("we refactored it", "refactor"),
                           ("a refactoring pass", "refactor"), ("Claude did it", "agent-name"),
                           ("via kimi", "agent-name"), ("Hermes ran", "agent-name")):
            self.assertIn(rule, rules(self.ext(text), "error"), text)
        self.assertNotIn("sprint-number", rules(self.ext("a sprint to the finish"), "error"))

    def test_banned_terms_whole_word_case_insensitive(self):
        cfg = {"banned_terms": ["GorillaDesk", "burn rate"]}
        self.assertIn("banned-term", rules(self.ext("in gorilladesk now", config=cfg), "error"))
        self.assertIn("banned-term", rules(self.ext("the Burn Rate is", config=cfg), "error"))
        self.assertNotIn("banned-term", rules(self.ext("gorilladesks", config=cfg), "error"))

    def test_denied_title_verbatim(self):
        self.assertIn("denied-title", rules(self.ext("we will ROTATE the  mirror capture credentials soon"), "error"))

    def test_denied_title_paraphrase(self):
        self.assertIn("denied-title", rules(self.ext("we rotate every mirror capture login and the credentials too"), "error"))
        self.assertNotIn("denied-title", rules(self.ext("the mirror keeps running; credentials are fine"), "error"))
        self.assertNotIn("denied-title", rules(self.ext("rotate the mirror\ncapture credentials"), "error"))

    def test_short_denied_title_only_verbatim(self):
        lj = {"identifiers": ["SMK"], "denied_titles": ["Fix login"], "surface_always": []}
        self.assertIn("denied-title", rules(self.ext("we fix login today", lint_json=lj), "error"))
        self.assertNotIn("denied-title", rules(self.ext("login is fixed", lint_json=lj), "error"))

    def test_surface_always_warning(self):
        findings = self.ext("a quiet week with nothing to report")
        self.assertIn("surface-always", rules(findings, "warning"))
        findings = self.ext("the draft invoice now lands in your CRM")
        self.assertNotIn("surface-always", rules(findings, "warning"))
        findings = self.ext("nothing", digest=load("external.digest.json"), lint_json=None)
        self.assertIn("surface-always", rules(findings, "warning"))

    def test_missing_context_warnings(self):
        findings = self.ext("fine text", identifier=None, lint_json=None)
        self.assertIn("no-identifier", rules(findings, "warning"))
        self.assertIn("no-lint-json", rules(findings, "warning"))
        findings = self.ext("fine text")
        self.assertNotIn("no-identifier", rules(findings, "warning"))
        self.assertNotIn("no-lint-json", rules(findings, "warning"))

    def test_internal_ignores_external_rules(self):
        findings = lint.lint("# Title\nSMK-1 a1b2c3d burndown by Claude in sprint 2, we refactored /home/x", "internal", "SMK", {}, lint_json=LINT_JSON)
        self.assertEqual(rules(findings, "error"), [])

    def test_fixture_external_clean(self):
        findings = lint.lint(read("external.raw.txt"), "external", "SMK", {}, digest=load("external.digest.json"), lint_json=LINT_JSON)
        self.assertEqual(findings, [], [f.as_dict() for f in findings])

    def test_fixture_external_dirty(self):
        findings = lint.lint(read("external-dirty.raw.txt"), "external", "SMK", {}, digest=load("external.digest.json"), lint_json=LINT_JSON)
        got = set(rules(findings, "error"))
        for rule in ("ticket-key", "sha", "abs-path", "burndown", "tool-calls", "sprint-number", "refactor", "agent-name", "denied-title"):
            self.assertIn(rule, got)
        self.assertTrue(all(f.line for f in findings if f.level == "error"))

    def test_errors_sort_first(self):
        findings = self.ext("a <b>tag</b> and SMK-1")
        self.assertEqual(findings[0].level, "error")


class LintCmd(unittest.TestCase):
    def run_cmd(self, **kw):
        args = types.SimpleNamespace(raw=None, digest=None, lint_json=None, warnings_as_errors=False, audience="external",
                                     project="no-such-project-slug", json=False)
        for k, v in kw.items():
            setattr(args, k, v)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = lint.lint_cmd(args)
        return rc, buf.getvalue()

    def test_dirty_refused_clean_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            digest = os.path.join(tmp, "2026-09-03T0300-external.digest.json")
            with open(digest, "w", encoding="utf-8") as fh:
                json.dump(load("external.digest.json"), fh)
            with open(os.path.join(tmp, "2026-09-03T0300-external.lint.json"), "w", encoding="utf-8") as fh:
                json.dump(LINT_JSON, fh)
            rc, out = self.run_cmd(raw=os.path.join(FX, "external-dirty.raw.txt"), digest=digest)
            self.assertEqual(rc, 3)
            self.assertIn("ticket-key", out)
            self.assertIn("lint: refused", out)
            rc, out = self.run_cmd(raw=os.path.join(FX, "external.raw.txt"), digest=digest)
            self.assertEqual(rc, 0, out)
            self.assertIn("lint: ok", out)
            rc, out = self.run_cmd(raw=os.path.join(FX, "external.raw.txt"), digest=digest, json=True)
            self.assertTrue(json.loads(out)["ok"])

    def test_missing_lint_json_is_a_config_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            digest = os.path.join(tmp, "2026-09-03T0300-external.digest.json")
            with open(digest, "w", encoding="utf-8") as fh:
                json.dump(load("external.digest.json"), fh)
            with self.assertRaises(ConfigError):
                self.run_cmd(raw=os.path.join(FX, "external.raw.txt"), digest=digest)
            with self.assertRaises(ConfigError):
                self.run_cmd(raw=os.path.join(FX, "external.raw.txt"), digest=digest, lint_json=os.path.join(tmp, "nope.json"))

    def test_warnings_as_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = os.path.join(tmp, "x.raw.txt")
            with open(raw, "w", encoding="utf-8") as fh:
                fh.write("# Title\nsome <i>tag</i>\n")
            rc, _ = self.run_cmd(raw=raw, audience="internal")
            self.assertEqual(rc, 0)
            rc, _ = self.run_cmd(raw=raw, audience="internal", warnings_as_errors=True)
            self.assertEqual(rc, 3)

    def test_digest_audience_mismatch(self):
        with self.assertRaises(ConfigError):
            self.run_cmd(raw=os.path.join(FX, "external.raw.txt"), digest=os.path.join(FX, "internal.digest.json"))


if __name__ == "__main__":
    unittest.main()
