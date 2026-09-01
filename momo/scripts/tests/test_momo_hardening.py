#!/usr/bin/env python3
"""Regression tests for the six Momo hardening tickets (33GPM-3 through 33GPM-8).

Run: python3 momo/skill/scripts/tests/test_momo_hardening.py
"""
import json
import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[4]  # 33GOD root
LIB = ROOT / "momo" / "skill" / "scripts" / "lib"
SCRIPTS = ROOT / "momo" / "skill" / "scripts"

sys.path.insert(0, str(LIB))

from momo_lane_gate import GateResult, LaneGate

TRELLO_SPEC = importlib.util.spec_from_file_location(
    "momo_trello_provider",
    SCRIPTS / "providers" / "trello.py",
)
assert TRELLO_SPEC is not None and TRELLO_SPEC.loader is not None
trello_provider = importlib.util.module_from_spec(TRELLO_SPEC)
TRELLO_SPEC.loader.exec_module(trello_provider)

MOMO_CONFIG_SPEC = importlib.util.spec_from_file_location(
    "momo_config_script",
    SCRIPTS / "momo-config.py",
)
assert MOMO_CONFIG_SPEC is not None and MOMO_CONFIG_SPEC.loader is not None
momo_config = importlib.util.module_from_spec(MOMO_CONFIG_SPEC)
MOMO_CONFIG_SPEC.loader.exec_module(momo_config)


def run_cli(script: str, *args, cwd=None, env=None):
    """Run a momo CLI script and return (rc, stdout, stderr)."""
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=cwd or str(ROOT),
        capture_output=True, text=True, timeout=15, env=e,
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


class TestHandback(unittest.TestCase):
    """33GPM-3: Structured worker hand-back with heartbeat and retry policy."""

    def setUp(self):
        self.spool = tempfile.mkdtemp(prefix="momo-hb-test-")

    def tearDown(self):
        shutil.rmtree(self.spool, ignore_errors=True)

    def test_init_creates_bundle(self):
        rc, out, err = run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "init", "--agent-id", "worker-1")
        self.assertEqual(rc, 0, err)
        bundle_path = pathlib.Path(self.spool) / "T-1.handback.json"
        self.assertTrue(bundle_path.exists())
        data = json.loads(bundle_path.read_text())
        self.assertEqual(data["issue"], "T-1")
        self.assertEqual(data["worker"]["agent_id"], "worker-1")
        self.assertIn("heartbeat", data)
        self.assertIn("checks", data)

    def test_heartbeat_updates_timestamp(self):
        run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "init", "--agent-id", "w")
        rc, out, err = run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "heartbeat")
        self.assertEqual(rc, 0, err)
        bundle = json.loads((pathlib.Path(self.spool) / "T-1.handback.json").read_text())
        self.assertNotEqual(bundle["heartbeat"]["started_at"], bundle["heartbeat"]["last_seen_at"])

    def test_finalize_and_validate(self):
        run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "init", "--agent-id", "w")
        rc, out, err = run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "finalize", "--status", "DONE", "--summary", "all pass", "--tests")
        self.assertEqual(rc, 0, err)
        rc, out, err = run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "validate")
        self.assertEqual(rc, 0, err)
        self.assertIn("VALID", out)

    def test_validate_fails_on_missing_bundle(self):
        rc, out, err = run_cli("momo-worker-handback.py", "--issue", "NOPE", "--spool", self.spool, "validate")
        self.assertNotEqual(rc, 0)


class TestFindingsLedger(unittest.TestCase):
    """33GPM-6: Stable findings ledger."""

    def setUp(self):
        self.findings_dir = ROOT / "_bmad-output" / "implementation-artifacts" / "findings"
        self.findings_dir.mkdir(parents=True, exist_ok=True)
        # Clean test artifacts
        for f in self.findings_dir.glob("TESTFINDINGS*"):
            f.unlink()

    def tearDown(self):
        for f in self.findings_dir.glob("TESTFINDINGS*"):
            f.unlink()

    def test_add_and_show(self):
        rc, out, err = run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-1", "add", "--severity", "high", "--category", "security", "--description", "test finding")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out, "F001")

    def test_resolve_with_dash_id(self):
        run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-1", "add", "--severity", "high", "--category", "bug", "--description", "test")
        rc, out, err = run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-1", "resolve", "--id", "F-001")
        self.assertEqual(rc, 0, err)
        rc, out, err = run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-1", "show")
        data = json.loads(out)
        self.assertEqual(data["findings"][0]["state"], "resolved")

    def test_stable_ids(self):
        for i in range(3):
            run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-2", "add", "--severity", "low", "--category", "style", "--description", f"finding {i}")
        rc, out, err = run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-2", "show")
        data = json.loads(out)
        ids = [f["id"] for f in data["findings"]]
        self.assertEqual(ids, ["F001", "F002", "F003"])

    def tearDown2(self):
        for f in self.findings_dir.glob("TESTFINDINGS*"):
            f.unlink()


class TestTreeLock(unittest.TestCase):
    """33GPM-8: Lock working tree against background auto-commits."""

    def setUp(self):
        self.lock_dir = ROOT / ".momo"
        # Clean any test locks
        for f in self.lock_dir.glob("tree.lock*"):
            f.unlink()

    def tearDown(self):
        for f in self.lock_dir.glob("tree.lock*"):
            f.unlink()

    def test_acquire_status_release(self):
        rc, out, err = run_cli("momo-tree-lock.py", "acquire", "--owner", "test-owner")
        self.assertEqual(rc, 0, err)
        self.assertIn("ACQUIRED", out)

        rc, out, err = run_cli("momo-tree-lock.py", "status")
        self.assertEqual(rc, 0, err)
        data = json.loads(out)
        self.assertTrue(data["locked"])
        self.assertEqual(data["owner"], "test-owner")

        rc, out, err = run_cli("momo-tree-lock.py", "release", "--owner", "test-owner")
        self.assertEqual(rc, 0, err)
        self.assertIn("RELEASED", out)

    def test_guard_blocks_when_locked(self):
        run_cli("momo-tree-lock.py", "acquire", "--owner", "session-1")
        rc, out, err = run_cli("momo-tree-lock.py", "guard")
        self.assertNotEqual(rc, 0, err)
        self.assertIn("GUARD_FAIL", err)

    def test_guard_passes_when_unlocked(self):
        rc, out, err = run_cli("momo-tree-lock.py", "guard")
        self.assertEqual(rc, 0, err)


class TestReporter(unittest.TestCase):
    """33GPM-5: Reporting discipline and deduplication."""

    def test_dry_run_produces_json(self):
        rc, out, err = run_cli("momo-reporter.py", "--issue", "T-1", "--event", "impl-complete", "--delta", "all done", "--state", "review", "--dry-run")
        self.assertEqual(rc, 0, err)
        data = json.loads(out)
        self.assertTrue(data["skipped"])
        self.assertIn("hash", data)
        self.assertIn("body", data)


class TestLaneGate(unittest.TestCase):
    """33GPM-7: Gated lane transitions."""

    def make_gate(self, temp: str) -> LaneGate:
        root = pathlib.Path(temp)
        script = (
            root
            / "agents"
            / "hermes"
            / "pm"
            / ".scripts"
            / "sentinel"
            / "bin"
            / "issue-autonomous-review.sh"
        )
        script.parent.mkdir(parents=True)
        script.touch()
        gate = LaneGate(root, "T-1")
        gate.gate_tree_lock = mock.Mock(
            return_value=GateResult("tree_lock", True, "pass")
        )
        gate.gate_close = mock.Mock(
            return_value=GateResult("close_gate", True, "pass")
        )
        return gate

    def traced_gate(
        self,
        temp: str,
        *,
        tree_passed: bool = True,
        close_passed: bool = True,
        review_passed: bool = True,
    ):
        gate = self.make_gate(temp)
        calls = []
        gate.gate_tree_lock = mock.Mock(
            side_effect=lambda: (
                calls.append("tree")
                or GateResult("tree_lock", tree_passed, "tree result")
            )
        )
        gate.gate_close = mock.Mock(
            side_effect=lambda: (
                calls.append("close")
                or GateResult("close_gate", close_passed, "close result")
            )
        )
        gate.gate_autonomous_review = mock.Mock(
            side_effect=lambda *_args, **_kwargs: (
                calls.append("review")
                or GateResult(
                    "autonomous_review",
                    review_passed,
                    "review result",
                )
            )
        )
        gate.transition = mock.Mock(
            side_effect=lambda target: (
                calls.append(f"transition:{target}")
                or subprocess.CompletedProcess(
                    [],
                    0,
                    stdout='{"ok":true}',
                    stderr="",
                )
            )
        )
        return gate, calls

    def test_tree_failure_short_circuits_every_downstream_action(self):
        for target in ("completed", "in_review"):
            with self.subTest(target=target), tempfile.TemporaryDirectory(
                prefix="momo-lane-test-"
            ) as temp:
                gate, calls = self.traced_gate(temp, tree_passed=False)

                result = gate.run(target)

                self.assertFalse(result["allowed"])
                self.assertEqual(calls, ["tree"])
                self.assertEqual(
                    [item["gate"] for item in result["gates"]],
                    ["tree_lock"],
                )
                gate.gate_close.assert_not_called()
                gate.gate_autonomous_review.assert_not_called()
                gate.transition.assert_not_called()

    def test_close_failure_short_circuits_review_and_transition(self):
        for target in ("completed", "in_review"):
            with self.subTest(target=target), tempfile.TemporaryDirectory(
                prefix="momo-lane-test-"
            ) as temp:
                gate, calls = self.traced_gate(temp, close_passed=False)

                result = gate.run(target)

                self.assertFalse(result["allowed"])
                self.assertEqual(calls, ["tree", "close"])
                self.assertEqual(
                    [item["gate"] for item in result["gates"]],
                    ["tree_lock", "close_gate"],
                )
                gate.gate_autonomous_review.assert_not_called()
                gate.transition.assert_not_called()

    def test_review_failure_short_circuits_completed_transition(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate, calls = self.traced_gate(temp, review_passed=False)

            result = gate.run("completed")

            self.assertFalse(result["allowed"])
            self.assertEqual(calls, ["tree", "close", "review"])
            gate.gate_autonomous_review.assert_called_once_with(None, close=True)
            gate.transition.assert_not_called()

    def test_success_paths_preserve_exact_chain_order(self):
        expected = {
            "completed": ["tree", "close", "review"],
            "in_review": ["tree", "close", "transition:in_review"],
        }
        for target, expected_calls in expected.items():
            with self.subTest(target=target), tempfile.TemporaryDirectory(
                prefix="momo-lane-test-"
            ) as temp:
                gate, calls = self.traced_gate(temp)

                result = gate.run(target)

                self.assertTrue(result["allowed"])
                self.assertEqual(calls, expected_calls)

    def test_gate_blocks_without_evidence(self):
        rc, out, err = run_cli("momo-lane-gate.py", "--issue", "NONEXISTENT-1", "--target", "completed", "--no-review")
        self.assertNotEqual(rc, 0)
        data = json.loads(out)
        self.assertFalse(data["allowed"])

    def test_gate_blocks_without_review(self):
        rc, out, err = run_cli("momo-lane-gate.py", "--issue", "NONEXISTENT-2", "--target", "in_review", "--no-review")
        self.assertNotEqual(rc, 0)
        # gate prints JSON to stdout even on failure
        data = json.loads(out)
        self.assertFalse(data["allowed"])

    def test_completed_review_is_single_close_authority(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate = self.make_gate(temp)
            review = pathlib.Path(temp) / "T-1.review.md"
            gate._run = mock.Mock(
                return_value=subprocess.CompletedProcess(
                    [], 0, stdout="AUTONOMOUS REVIEW: ACCEPTED\n", stderr=""
                )
            )
            gate.transition = mock.Mock()

            result = gate.run("completed", review_file=review)

            self.assertTrue(result["allowed"])
            self.assertEqual(result["transition_authority"], "autonomous_review")
            gate._run.assert_called_once_with(
                [
                    str(gate.sentinel_bin / "issue-autonomous-review.sh"),
                    "T-1",
                    str(review),
                    "--close",
                ]
            )
            gate.transition.assert_not_called()
            self.assertNotIn("stays in the review lane", json.dumps(result).lower())

    def test_completed_transition_failure_is_not_accepted_or_retried(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate = self.make_gate(temp)
            gate._run = mock.Mock(
                return_value=subprocess.CompletedProcess(
                    [], 1, stdout="", stderr="adapter transition failed"
                )
            )
            gate.transition = mock.Mock()

            result = gate.run("completed")

            self.assertFalse(result["allowed"])
            self.assertIn("adapter transition failed", json.dumps(result))
            self.assertNotIn("accepted", json.dumps(result).lower())
            gate.transition.assert_not_called()
            gate._run.assert_called_once()

    def test_completed_comment_failure_remains_explicit(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate = self.make_gate(temp)
            gate._run = mock.Mock(
                return_value=subprocess.CompletedProcess(
                    [],
                    1,
                    stdout="AUTONOMOUS REVIEW: ACCEPTED\n",
                    stderr="required acceptance comment failed",
                )
            )
            gate.transition = mock.Mock()

            result = gate.run("completed")

            rendered = json.dumps(result).lower()
            self.assertFalse(result["allowed"])
            self.assertIn("required acceptance comment failed", rendered)
            self.assertNotIn("autonomous review: accepted", rendered)
            self.assertNotIn("stays in the review lane", rendered)
            gate.transition.assert_not_called()

    def test_review_lane_reports_success_only_after_transition(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate = self.make_gate(temp)
            gate.transition = mock.Mock(
                return_value=subprocess.CompletedProcess(
                    [], 0, stdout='{"ok":true}', stderr=""
                )
            )

            result = gate.run("in_review")

            self.assertTrue(result["allowed"])
            gate.transition.assert_called_once_with("in_review")
            self.assertNotIn("accepted", json.dumps(result).lower())

    def test_review_lane_transition_failure_has_no_acceptance(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate = self.make_gate(temp)
            gate.transition = mock.Mock(
                return_value=subprocess.CompletedProcess(
                    [], 1, stdout="", stderr="transition failed"
                )
            )

            result = gate.run("in_review")

            self.assertFalse(result["allowed"])
            self.assertIn("transition failed", result["adapter_error"])
            self.assertNotIn("accepted", json.dumps(result).lower())


def trello_board_card(
    card_id="card-1",
    board="board-1",
    id_short=42,
    short_link="abc123",
):
    return {
        "id": card_id,
        "idBoard": board,
        "idShort": id_short,
        "shortLink": short_link,
    }


class FakeTrello:
    def __init__(self, lists, card_gets, put_response, post_response=None, cards=None):
        self.lists = lists
        self.card_gets = list(card_gets)
        self.put_response = put_response
        self.post_response = post_response
        self.cards = cards
        self.calls = []

    def get(self, path, extra=None):
        self.calls.append(("GET", path, extra))
        if path.startswith("boards/"):
            if path.endswith("/cards") and self.cards is not None:
                return self.cards
            return self.lists
        if path.startswith("cards/") and self.card_gets:
            return self.card_gets.pop(0)
        raise AssertionError(f"unexpected GET {path}")

    def put(self, path, extra=None):
        self.calls.append(("PUT", path, extra))
        return self.put_response

    def post(self, path, extra=None):
        self.calls.append(("POST", path, extra))
        return self.post_response


class TestTrelloCardResolution(unittest.TestCase):
    def resolve(self, fake, reference="card-1", identifier="MOMO"):
        return trello_provider.resolve_card_id(
            fake,
            "board-1",
            reference,
            identifier,
        )

    def assert_resolution_error(self, fake, reference, expected):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            self.resolve(fake, reference)
        self.assertIn(expected, stderr.getvalue())
        self.assertFalse(any(call[0] in {"PUT", "POST"} for call in fake.calls))

    def test_native_shortlink_idshort_and_project_key_resolve_uniquely(self):
        cases = (
            ("card-1", trello_board_card()),
            ("ABC123", trello_board_card()),
            ("42", trello_board_card()),
            ("42", trello_board_card(id_short="42")),
            ("momo-42", trello_board_card()),
        )
        for reference, card in cases:
            with self.subTest(reference=reference, id_short=card["idShort"]):
                fake = FakeTrello([], [], {}, cards=[card])

                self.assertEqual(self.resolve(fake, reference), "card-1")
                self.assertEqual(fake.calls, [(
                    "GET",
                    "boards/board-1/cards",
                    {"fields": "id,idBoard,idShort,shortLink"},
                )])

    def test_blank_reference_fails_before_network(self):
        for reference in ("", " ", " card-1", "card-1 "):
            with self.subTest(reference=reference):
                fake = FakeTrello([], [], {}, cards=[trello_board_card()])

                self.assert_resolution_error(fake, reference, "non-blank exact")
                self.assertEqual(fake.calls, [])

    def test_blank_optional_identifier_adds_no_project_alias(self):
        for identifier in (None, "", " "):
            with self.subTest(identifier=identifier):
                fake = FakeTrello([], [], {}, cards=[trello_board_card()])

                self.assertEqual(
                    self.resolve(fake, "abc123", identifier=identifier),
                    "card-1",
                )
                self.assertEqual([call[0] for call in fake.calls], ["GET"])

    def test_non_string_or_padded_nonblank_identifier_is_config_invalid(self):
        for identifier in (42, True, ["MOMO"], " MOMO "):
            with self.subTest(identifier=identifier):
                fake = FakeTrello([], [], {}, cards=[trello_board_card()])
                stderr = io.StringIO()

                with (
                    contextlib.redirect_stderr(stderr),
                    self.assertRaises(SystemExit),
                ):
                    self.resolve(fake, "abc123", identifier=identifier)

                self.assertIn("configured ticket-provider identifier", stderr.getvalue())
                self.assertEqual(fake.calls, [])

    def test_no_match_fails_after_board_read_only_lookup(self):
        fake = FakeTrello([], [], {}, cards=[trello_board_card()])

        self.assert_resolution_error(fake, "external-card", "not on configured board")

        self.assertEqual([call[0] for call in fake.calls], ["GET"])

    def test_duplicate_casefold_alias_fails_closed(self):
        fake = FakeTrello(
            [],
            [],
            {},
            cards=[
                trello_board_card(
                    card_id="card-1",
                    id_short=42,
                    short_link="same-key",
                ),
                trello_board_card(
                    card_id="card-2",
                    id_short=43,
                    short_link="SAME-KEY",
                ),
            ],
        )

        self.assert_resolution_error(fake, "same-key", "duplicate card alias")

        self.assertEqual([call[0] for call in fake.calls], ["GET"])

    def test_duplicate_idshort_and_project_key_aliases_fail_closed(self):
        fake = FakeTrello(
            [],
            [],
            {},
            cards=[
                trello_board_card(
                    card_id="card-1",
                    id_short=42,
                    short_link="key-one",
                ),
                trello_board_card(
                    card_id="card-2",
                    id_short="42",
                    short_link="key-two",
                ),
            ],
        )

        self.assert_resolution_error(fake, "MOMO-42", "duplicate card alias")

        self.assertEqual([call[0] for call in fake.calls], ["GET"])

    def test_empty_alias_or_native_id_fails_closed(self):
        malformed_cards = (
            {**trello_board_card(), "id": ""},
            {**trello_board_card(), "idShort": ""},
            {**trello_board_card(), "idShort": " "},
            {**trello_board_card(), "shortLink": ""},
            {**trello_board_card(), "shortLink": " "},
        )
        for card in malformed_cards:
            with self.subTest(card=card):
                fake = FakeTrello([], [], {}, cards=[card])

                self.assert_resolution_error(fake, "card-1", "card")
                self.assertEqual([call[0] for call in fake.calls], ["GET"])

    def test_malformed_board_cards_response_fails_closed(self):
        for cards in ({}, [None]):
            with self.subTest(cards=cards):
                fake = FakeTrello([], [], {}, cards=cards)

                self.assert_resolution_error(fake, "card-1", "board cards response")
                self.assertEqual([call[0] for call in fake.calls], ["GET"])

    def test_external_board_card_fails_after_read_only_lookup(self):
        fake = FakeTrello(
            [],
            [],
            {},
            cards=[trello_board_card(board="board-2")],
        )

        self.assert_resolution_error(fake, "card-1", "external board")

        self.assertEqual([call[0] for call in fake.calls], ["GET"])

    def test_missing_or_malformed_board_identity_fails_after_read_only_lookup(self):
        for board_value in (None, "", 123):
            with self.subTest(board_value=board_value):
                card = trello_board_card()
                if board_value is None:
                    card.pop("idBoard")
                else:
                    card["idBoard"] = board_value
                fake = FakeTrello([], [], {}, cards=[card])

                self.assert_resolution_error(fake, "card-1", "valid idBoard")
                self.assertEqual([call[0] for call in fake.calls], ["GET"])


class TestTrelloTransition(unittest.TestCase):
    def transition(self, fake, card_ref="card-1", target="completed", config=None):
        config = config or {}
        if fake.cards is None:
            fake.cards = [trello_board_card()]
        return trello_provider.transition_card(
            fake,
            "board-1",
            card_ref,
            target,
            config,
            trello_provider.lane_map(config),
            "MOMO",
        )

    def successful_fake(self):
        return FakeTrello(
            [{"id": "list-done", "name": "Done"}],
            [
                {
                    **trello_board_card(),
                    "idList": "list-old",
                },
                {
                    **trello_board_card(),
                    "idList": "list-done",
                },
            ],
            {
                "id": "card-1",
                "idBoard": "board-1",
                "idList": "list-done",
            },
            cards=[trello_board_card()],
        )

    def assert_transition_error(self, fake, expected):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            self.transition(fake)
        self.assertIn(expected, stderr.getvalue())

    def test_duplicate_exact_or_casefold_lane_is_rejected_without_put(self):
        for names in (("Done", "Done"), ("Done", "done")):
            with self.subTest(names=names):
                fake = FakeTrello(
                    [
                        {"id": "list-1", "name": names[0]},
                        {"id": "list-2", "name": names[1]},
                    ],
                    [{
                        **trello_board_card(),
                        "idList": "list-old",
                    }],
                    {},
                )

                self.assert_transition_error(fake, "duplicate live lanes")

                self.assertFalse(any(call[0] == "PUT" for call in fake.calls))

    def assert_transition_scope_error(self, card, expected):
        fake = FakeTrello(
            [{"id": "list-done", "name": "Done"}],
            [card],
            {},
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            self.transition(fake)

        self.assertIn(expected, stderr.getvalue())
        self.assertEqual([call[0] for call in fake.calls], ["GET", "GET"])
        self.assertEqual(fake.calls[1], (
            "GET",
            "cards/card-1",
            {"fields": "id,idBoard,idList,shortLink,idShort"},
        ))

    def test_transition_rejects_wrong_board_before_put(self):
        self.assert_transition_scope_error(
            {"id": "card-1", "idBoard": "board-2", "idList": "list-old"},
            "different board",
        )

    def test_transition_rejects_missing_or_malformed_board_before_put(self):
        for card in (
            {"id": "card-1", "idList": "list-old"},
            {"id": "card-1", "idBoard": 123, "idList": "list-old"},
            {"id": "card-1", "idBoard": "", "idList": "list-old"},
        ):
            with self.subTest(card=card):
                self.assert_transition_scope_error(card, "valid idBoard")

    def test_transition_rejects_wrong_or_malformed_native_id_before_put(self):
        for card in (
            {"id": "card-2", "idBoard": "board-1", "idList": "list-old"},
            {"id": 123, "idBoard": "board-1", "idList": "list-old"},
            {"idBoard": "board-1", "idList": "list-old"},
        ):
            with self.subTest(card=card):
                expected = (
                    "different card"
                    if card.get("id") == "card-2"
                    else "without an id"
                )
                self.assert_transition_scope_error(card, expected)

    def test_external_board_card_fails_before_transition_write(self):
        fake = self.successful_fake()
        fake.cards = [trello_board_card(board="external-board")]

        self.assert_transition_error(fake, "external board")

        self.assertEqual([call[0] for call in fake.calls], ["GET"])
        self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 0)

    def test_globally_addressable_external_reference_is_not_transitionable(self):
        fake = self.successful_fake()

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            self.transition(fake, card_ref="external-card-id")

        self.assertIn("not on configured board", stderr.getvalue())
        self.assertEqual([call[0] for call in fake.calls], ["GET"])
        self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 0)

    def test_normalized_write_target_must_belong_to_requested_state(self):
        config = {
            "lanes": {"completed": ["Done"]},
            "write_targets": {"completed": "Archive"},
        }
        valid_lm = trello_provider.lane_map({
            "lanes": {"completed": ["Done"]},
        })
        fake = self.successful_fake()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            trello_provider.transition_card(
                fake,
                "board-1",
                "card-1",
                "completed",
                config,
                valid_lm,
                "MOMO",
            )

        self.assertIn("must name exactly one lane", stderr.getvalue())
        self.assertEqual(fake.calls, [])
        self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 0)

    def test_malformed_present_lane_config_never_falls_back_or_puts(self):
        invalid_configs = (
            {"lanes": {"completed": []}},
            {"lanes": {"completed": "Done"}},
            {"lanes": {"completed": [""]}},
            {"write_targets": None},
            {"write_targets": []},
            {"write_targets": {"completed": ""}},
        )
        for config in invalid_configs:
            with self.subTest(config=config):
                fake = self.successful_fake()
                stderr = io.StringIO()

                with (
                    contextlib.redirect_stderr(stderr),
                    self.assertRaises(SystemExit),
                ):
                    self.transition(fake, config=config)

                self.assertIn("invalid lane config", stderr.getvalue())
                self.assertEqual(fake.calls, [])
                self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 0)

    def test_cross_state_lane_overlap_fails_before_cancelled_put(self):
        config = {
            "lanes": {
                "completed": ["Terminal"],
                "cancelled": ["terminal"],
            },
            "write_targets": {"cancelled": "terminal"},
        }
        fake = self.successful_fake()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            self.transition(fake, target="cancelled", config=config)

        self.assertIn("belongs to both", stderr.getvalue())
        self.assertEqual(fake.calls, [])
        self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 0)

    def test_supplied_lane_map_cannot_diverge_from_config(self):
        config = {"lanes": {"completed": ["Done"]}}
        divergent_lm = trello_provider.lane_map({
            "lanes": {"completed": ["Archive"]},
        })
        fake = self.successful_fake()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            trello_provider.transition_card(
                fake,
                "board-1",
                "card-1",
                "completed",
                config,
                divergent_lm,
                "MOMO",
            )

        self.assertIn("does not match", stderr.getvalue())
        self.assertEqual(fake.calls, [])
        self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 0)

    def test_wrong_put_response_fails_before_readback(self):
        wrong_responses = (
            {},
            {
                "id": "different-card",
                "idBoard": "board-1",
                "idList": "list-done",
            },
            {
                "id": "card-1",
                "idBoard": "board-1",
                "idList": "different-list",
            },
        )
        for response in wrong_responses:
            with self.subTest(response=response):
                fake = FakeTrello(
                    [{"id": "list-done", "name": "Done"}],
                    [
                        {
                            "id": "card-1",
                            "idBoard": "board-1",
                            "idShort": 42,
                            "idList": "list-old",
                        },
                        {
                            "id": "card-1",
                            "idBoard": "board-1",
                            "idShort": 42,
                            "idList": "list-done",
                        },
                    ],
                    response,
                )

                self.assert_transition_error(fake, "PUT response")

                self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)
                self.assertEqual(len(fake.card_gets), 1)

    def test_wrong_or_missing_board_in_put_response_fails_without_readback(self):
        for board_fields in ({}, {"idBoard": "external-board"}):
            with self.subTest(board_fields=board_fields):
                fake = self.successful_fake()
                fake.put_response = {
                    "id": "card-1",
                    "idList": "list-done",
                    **board_fields,
                }

                self.assert_transition_error(fake, "PUT response")

                self.assertEqual(
                    [call[0] for call in fake.calls],
                    ["GET", "GET", "GET", "PUT"],
                )
                self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)
                self.assertEqual(len(fake.card_gets), 1)

    def test_wrong_or_missing_readback_fails_without_ok(self):
        wrong_readbacks = (
            {},
            {
                "id": "different-card",
                "idBoard": "board-1",
                "idShort": 42,
                "idList": "list-done",
            },
            {
                "id": "card-1",
                "idBoard": "board-1",
                "idShort": 42,
                "idList": "different-list",
            },
        )
        for readback in wrong_readbacks:
            with self.subTest(readback=readback):
                fake = FakeTrello(
                    [{"id": "list-done", "name": "Done"}],
                    [
                        {
                            "id": "card-1",
                            "idBoard": "board-1",
                            "idShort": 42,
                            "idList": "list-old",
                        },
                        readback,
                    ],
                    {
                        "id": "card-1",
                        "idBoard": "board-1",
                        "idList": "list-done",
                    },
                )

                self.assert_transition_error(fake, "GET readback")

                self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)

    def test_wrong_or_missing_board_in_readback_fails_without_reput(self):
        for board_fields in ({}, {"idBoard": "external-board"}):
            with self.subTest(board_fields=board_fields):
                fake = self.successful_fake()
                fake.card_gets[-1] = {
                    "id": "card-1",
                    "idList": "list-done",
                    **board_fields,
                }

                self.assert_transition_error(fake, "GET readback")

                self.assertEqual(
                    [call[0] for call in fake.calls],
                    ["GET", "GET", "GET", "PUT", "GET"],
                )
                self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)

    def test_exact_transition_puts_once_and_reads_back_same_card(self):
        fake = FakeTrello(
            [{"id": "list-done", "name": "Done"}],
            [
                {
                    "id": "card-1",
                    "idBoard": "board-1",
                    "idShort": 42,
                    "shortLink": "abc123",
                    "idList": "list-old",
                },
                {
                    "id": "card-1",
                    "idBoard": "board-1",
                    "idShort": 42,
                    "shortLink": "abc123",
                    "idList": "list-done",
                },
            ],
            {
                "id": "card-1",
                "idBoard": "board-1",
                "idList": "list-done",
            },
        )

        result = self.transition(fake)

        self.assertEqual(
            result,
            {
                "ok": True,
                "card": "card-1",
                "requested_card": "card-1",
                "target": "completed",
                "moved_to": "Done",
                "state": "completed",
            },
        )
        self.assertEqual(
            [call[:2] for call in fake.calls],
            [
                ("GET", "boards/board-1/cards"),
                ("GET", "cards/card-1"),
                ("GET", "boards/board-1/lists"),
                ("PUT", "cards/card-1"),
                ("GET", "cards/card-1"),
            ],
        )
        self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)
        self.assertEqual(
            fake.calls[1][2],
            {"fields": "id,idBoard,idList,shortLink,idShort"},
        )

    def test_lane_gate_style_human_key_and_trello_aliases_use_native_card(self):
        for reference in ("MOMO-42", "momo-42", "ABC123", "42"):
            with self.subTest(reference=reference):
                fake = self.successful_fake()

                result = self.transition(fake, card_ref=reference)

                self.assertTrue(result["ok"])
                self.assertEqual(result["card"], "card-1")
                self.assertEqual(result["requested_card"], reference)
                self.assertEqual(
                    [call[:2] for call in fake.calls],
                    [
                        ("GET", "boards/board-1/cards"),
                        ("GET", "cards/card-1"),
                        ("GET", "boards/board-1/lists"),
                        ("PUT", "cards/card-1"),
                        ("GET", "cards/card-1"),
                    ],
                )
                self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)

    def test_casefold_write_target_returns_canonical_lane_and_state(self):
        config = {
            "lanes": {"completed": ["Archive"]},
            "write_targets": {"completed": "archive"},
        }
        fake = FakeTrello(
            [{"id": "list-archive", "name": "ARCHIVE"}],
            [
                {**trello_board_card(), "idList": "list-old"},
                {**trello_board_card(), "idList": "list-archive"},
            ],
            {
                "id": "card-1",
                "idBoard": "board-1",
                "idList": "list-archive",
            },
            cards=[trello_board_card()],
        )

        result = self.transition(fake, target="completed", config=config)

        self.assertTrue(result["ok"])
        self.assertEqual(result["target"], "completed")
        self.assertEqual(result["moved_to"], "ARCHIVE")
        self.assertEqual(result["state"], "completed")
        self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)

    def test_literal_unmapped_lane_may_classify_as_other(self):
        fake = FakeTrello(
            [{"id": "list-archive", "name": "Archive"}],
            [
                {**trello_board_card(), "idList": "list-old"},
                {**trello_board_card(), "idList": "list-archive"},
            ],
            {
                "id": "card-1",
                "idBoard": "board-1",
                "idList": "list-archive",
            },
            cards=[trello_board_card()],
        )

        result = self.transition(fake, target="Archive")

        self.assertTrue(result["ok"])
        self.assertEqual(result["target"], "Archive")
        self.assertEqual(result["moved_to"], "Archive")
        self.assertEqual(result["state"], "other")
        self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)

    def test_cli_blank_identifier_allows_board_scoped_shortlink_transition(self):
        with tempfile.TemporaryDirectory(prefix="momo-trello-transition-") as temp:
            root = pathlib.Path(temp)
            (root / ".project.json").write_text(json.dumps({
                "ticket_provider": {
                    "type": "trello",
                    "board_id": "board-1",
                    "identifier": "",
                },
            }))
            fake = self.successful_fake()
            stdout = io.StringIO()
            argv = [
                "trello.py",
                "--root",
                str(root),
                "transition",
                "abc123",
                "completed",
            ]

            with (
                mock.patch.object(trello_provider.sys, "argv", argv),
                mock.patch.object(
                    trello_provider,
                    "creds",
                    return_value=("key", "token"),
                ),
                mock.patch.object(trello_provider, "Trello", return_value=fake),
                contextlib.redirect_stdout(stdout),
            ):
                self.assertEqual(trello_provider.main(), 0)

            result = json.loads(stdout.getvalue())
            self.assertTrue(result["ok"])
            self.assertEqual(result["card"], "card-1")
            self.assertEqual(result["requested_card"], "abc123")
            self.assertEqual(
                [call[:2] for call in fake.calls],
                [
                    ("GET", "boards/board-1/cards"),
                    ("GET", "cards/card-1"),
                    ("GET", "boards/board-1/lists"),
                    ("PUT", "cards/card-1"),
                    ("GET", "cards/card-1"),
                ],
            )
            self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)

    def test_default_cancelled_transition_uses_normalized_lane(self):
        fake = FakeTrello(
            [{"id": "list-cancelled", "name": "Cancelled"}],
            [
                {
                    "id": "card-1",
                    "idBoard": "board-1",
                    "idShort": 42,
                    "idList": "list-old",
                },
                {
                    "id": "card-1",
                    "idBoard": "board-1",
                    "idShort": 42,
                    "idList": "list-cancelled",
                },
            ],
            {
                "id": "card-1",
                "idBoard": "board-1",
                "idList": "list-cancelled",
            },
        )

        result = self.transition(fake, target="cancelled")

        self.assertEqual(result["state"], "cancelled")
        self.assertEqual(result["moved_to"], "Cancelled")
        self.assertEqual(fake.calls[3], (
            "PUT",
            "cards/card-1",
            {"idList": "list-cancelled"},
        ))

    def test_custom_cancelled_transition_honors_write_mapping(self):
        config = {
            "lanes": {"cancelled": ["Abandoned"]},
            "write_targets": {"cancelled": "Abandoned"},
        }
        fake = FakeTrello(
            [{"id": "list-abandoned", "name": "Abandoned"}],
            [
                {
                    "id": "card-1",
                    "idBoard": "board-1",
                    "idShort": 42,
                    "idList": "list-old",
                },
                {
                    "id": "card-1",
                    "idBoard": "board-1",
                    "idShort": 42,
                    "idList": "list-abandoned",
                },
            ],
            {
                "id": "card-1",
                "idBoard": "board-1",
                "idList": "list-abandoned",
            },
        )

        result = self.transition(
            fake,
            target="cancelled",
            config=config,
        )

        self.assertEqual(result["state"], "cancelled")
        self.assertEqual(result["moved_to"], "Abandoned")
        self.assertEqual(fake.calls[3][2], {"idList": "list-abandoned"})


class TestTrelloComment(unittest.TestCase):
    CARD = {
        "id": "card-1",
        "idBoard": "board-1",
        "idShort": 42,
        "shortLink": "abc123",
    }

    def comment(self, response, card_ref="card-1", cards=None):
        if cards is None:
            cards = [trello_board_card()]
        fake = FakeTrello(
            [],
            [dict(self.CARD)],
            {},
            post_response=response,
            cards=cards,
        )
        result = trello_provider.comment_card(
            fake,
            "board-1",
            card_ref,
            "Finished closeout",
            "MOMO",
        )
        return result, fake

    def assert_comment_error(self, response, expected):
        fake = FakeTrello(
            [],
            [dict(self.CARD)],
            {},
            post_response=response,
            cards=[trello_board_card()],
        )
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            trello_provider.comment_card(
                fake,
                "board-1",
                "card-1",
                "Finished closeout",
                "MOMO",
            )
        self.assertIn(expected, stderr.getvalue())
        self.assertEqual(sum(call[0] == "POST" for call in fake.calls), 1)

    def assert_comment_scope_error(self, card, expected):
        fake = FakeTrello(
            [],
            [card],
            {},
            post_response={"id": "action-1"},
            cards=[trello_board_card()],
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            trello_provider.comment_card(
                fake,
                "board-1",
                "card-1",
                "Finished closeout",
                "MOMO",
            )

        self.assertIn(expected, stderr.getvalue())
        self.assertEqual(
            fake.calls,
            [
                (
                    "GET",
                    "boards/board-1/cards",
                    {"fields": "id,idBoard,idShort,shortLink"},
                ),
                (
                    "GET",
                    "cards/card-1",
                    {"fields": "id,idBoard,shortLink,idShort"},
                ),
            ],
        )

    def test_comment_rejects_wrong_board_before_post(self):
        self.assert_comment_scope_error(
            {"id": "card-1", "idBoard": "board-2"},
            "different board",
        )

    def test_external_board_card_fails_before_comment_write(self):
        fake = FakeTrello(
            [],
            [dict(self.CARD)],
            {},
            post_response={"id": "action-1"},
            cards=[trello_board_card(board="external-board")],
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            trello_provider.comment_card(
                fake,
                "board-1",
                "card-1",
                "Finished closeout",
                "MOMO",
            )

        self.assertIn("external board", stderr.getvalue())
        self.assertEqual([call[0] for call in fake.calls], ["GET"])
        self.assertEqual(sum(call[0] == "POST" for call in fake.calls), 0)

    def test_globally_addressable_external_reference_is_not_commentable(self):
        fake = FakeTrello(
            [],
            [dict(self.CARD)],
            {},
            post_response={"id": "action-1"},
            cards=[trello_board_card()],
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            trello_provider.comment_card(
                fake,
                "board-1",
                "external-card-id",
                "Finished closeout",
                "MOMO",
            )

        self.assertIn("not on configured board", stderr.getvalue())
        self.assertEqual([call[0] for call in fake.calls], ["GET"])
        self.assertEqual(sum(call[0] == "POST" for call in fake.calls), 0)

    def test_comment_rejects_missing_or_malformed_board_before_post(self):
        for card in (
            {"id": "card-1"},
            {"id": "card-1", "idBoard": 123},
            {"id": "card-1", "idBoard": ""},
        ):
            with self.subTest(card=card):
                self.assert_comment_scope_error(card, "valid idBoard")

    def test_comment_rejects_wrong_or_malformed_native_id_before_post(self):
        for card in (
            {"id": "card-2", "idBoard": "board-1"},
            {"id": 123, "idBoard": "board-1"},
            {"idBoard": "board-1"},
        ):
            with self.subTest(card=card):
                expected = (
                    "different card"
                    if card.get("id") == "card-2"
                    else "without an id"
                )
                self.assert_comment_scope_error(card, expected)

    def test_comment_rejects_empty_malformed_or_missing_id_response(self):
        invalid = (
            (None, "action object"),
            ([], "action object"),
            ({}, "no action id"),
            ({"comment": {"id": "action-1"}}, "no action id"),
            ({"id": ""}, "no action id"),
            ({"id": 123}, "no action id"),
            ({"id": "action-1", "type": "updateCard"}, "action type"),
            ({"id": "action-1", "data": "wrong"}, "data envelope"),
            ({"id": "action-1", "data": {"card": {}}}, "no identity"),
        )
        for response, expected in invalid:
            with self.subTest(response=response):
                self.assert_comment_error(response, expected)

    def test_comment_rejects_wrong_exposed_card(self):
        wrong_cards = (
            {"id": "action-1", "idCard": "card-2"},
            {"id": "action-1", "card": {"id": "card-2"}},
            {"id": "action-1", "data": {"card": {"id": "card-2"}}},
            {
                "id": "action-1",
                "data": {"card": {"id": "card-2", "idShort": 42}},
            },
        )
        for response in wrong_cards:
            with self.subTest(response=response):
                self.assert_comment_error(response, "different card")

    def test_comment_returns_only_proven_action_id(self):
        response = {
            "id": "action-1",
            "type": "commentCard",
            "data": {"card": {"id": "card-1", "idShort": 42}},
        }

        result, fake = self.comment(response)

        self.assertEqual(result, "action-1")
        self.assertEqual(
            [call[:2] for call in fake.calls],
            [
                ("GET", "boards/board-1/cards"),
                ("GET", "cards/card-1"),
                ("POST", "cards/card-1/actions/comments"),
            ],
        )
        self.assertEqual(
            fake.calls[1][2],
            {"fields": "id,idBoard,shortLink,idShort"},
        )

    def test_lane_gate_style_human_key_comments_on_resolved_native_card(self):
        response = {
            "id": "action-1",
            "type": "commentCard",
            "data": {"card": {"id": "card-1"}},
        }

        result, fake = self.comment(response, card_ref="MOMO-42")

        self.assertEqual(result, "action-1")
        self.assertEqual(
            [call[:2] for call in fake.calls],
            [
                ("GET", "boards/board-1/cards"),
                ("GET", "cards/card-1"),
                ("POST", "cards/card-1/actions/comments"),
            ],
        )

    def test_comment_rejects_id_only_response_without_card_identity(self):
        self.assert_comment_error(
            {"id": "action-1"},
            "exposed no card identity",
        )

    def test_comment_cli_prints_nothing_until_response_is_proven(self):
        with tempfile.TemporaryDirectory(prefix="momo-trello-comment-") as temp:
            root = pathlib.Path(temp)
            (root / ".project.json").write_text(json.dumps({
                "ticket_provider": {
                    "type": "trello",
                    "board_id": "board-1",
                    "identifier": "MOMO",
                },
            }))
            fake = FakeTrello(
                [],
                [dict(self.CARD)],
                {},
                post_response={},
                cards=[trello_board_card()],
            )
            stdout = io.StringIO()
            stderr = io.StringIO()
            argv = [
                "trello.py",
                "--root",
                str(root),
                "comment",
                "MOMO-42",
                "Finished closeout",
            ]
            with (
                mock.patch.object(trello_provider.sys, "argv", argv),
                mock.patch.object(
                    trello_provider,
                    "creds",
                    return_value=("key", "token"),
                ),
                mock.patch.object(trello_provider, "Trello", return_value=fake),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
                self.assertRaises(SystemExit),
            ):
                trello_provider.main()

            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("no action id", stderr.getvalue())


class TestTrelloCancelledClassification(unittest.TestCase):
    def run_list_issues(self, config):
        with tempfile.TemporaryDirectory(prefix="momo-trello-list-") as temp:
            root = pathlib.Path(temp)
            (root / ".project.json").write_text(json.dumps({
                "ticket_provider": {"type": "trello", "board_id": "board-1"},
            }))
            if config:
                momo = root / ".momo"
                momo.mkdir()
                (momo / "config.json").write_text(json.dumps(config))

            lane = "Abandoned" if config else "Cancelled"
            fake = FakeTrello(
                [{"id": "list-cancelled", "name": lane}],
                [],
                {},
                cards=[{
                    "id": "card-1",
                    "name": "Cancelled work",
                    "idList": "list-cancelled",
                    "shortLink": "abc123",
                }],
            )
            stdout = io.StringIO()
            argv = ["trello.py", "--root", str(root), "list_issues"]
            with (
                mock.patch.object(trello_provider.sys, "argv", argv),
                mock.patch.object(trello_provider, "creds", return_value=("key", "token")),
                mock.patch.object(trello_provider, "Trello", return_value=fake),
                contextlib.redirect_stdout(stdout),
            ):
                self.assertEqual(trello_provider.main(), 0)
            return json.loads(stdout.getvalue())

    def test_list_issues_classifies_default_cancelled_lane(self):
        rows = self.run_list_issues({})

        self.assertEqual(rows[0]["state"], "cancelled")
        self.assertEqual(rows[0]["state_type"], "cancelled")

    def test_list_issues_classifies_custom_cancelled_lane(self):
        rows = self.run_list_issues({
            "lanes": {"cancelled": ["Abandoned"]},
            "write_targets": {"cancelled": "Abandoned"},
        })

        self.assertEqual(rows[0]["state"], "cancelled")
        self.assertEqual(rows[0]["list"], "Abandoned")


class TestEvidenceCapture(unittest.TestCase):
    """33GPM-4: Automate evidence capture."""

    def test_requires_handback(self):
        rc, out, err = run_cli("momo-evidence-capture.py", "--issue", "NOHANDBACK-1", "--pytest-cmd", "echo", "--ruff-cmd", "echo")
        self.assertNotEqual(rc, 0)
        self.assertIn("no handback bundle", err)


class TestMomoConfig(unittest.TestCase):
    def run_set(self, root, lanes, write_targets=None, notes=None):
        args = [
            "set",
            "--root",
            str(root),
            "--lanes",
            lanes,
        ]
        if write_targets is not None:
            args.extend(["--write-targets", write_targets])
        if notes is not None:
            args.extend(["--notes", notes])
        return run_cli("momo-config.py", *args)

    def test_set_writes_only_validated_lane_schema(self):
        with tempfile.TemporaryDirectory(prefix="momo-config-test-") as temp:
            root = pathlib.Path(temp)

            rc, _out, err = self.run_set(
                root,
                json.dumps({
                    "completed": ["Archive"],
                    "cancelled": ["Abandoned"],
                }),
                json.dumps({
                    "completed": "archive",
                    "cancelled": "Abandoned",
                }),
                json.dumps({"Archive": "accepted work"}),
            )

            self.assertEqual(rc, 0, err)
            config = json.loads((root / ".momo" / "config.json").read_text())
            self.assertEqual(config["lanes"]["completed"], ["Archive"])
            self.assertEqual(config["lanes"]["cancelled"], ["Abandoned"])
            self.assertEqual(config["write_targets"]["completed"], "archive")

    def test_set_rejects_invalid_lane_shapes_without_writing(self):
        invalid_lanes = (
            "[]",
            json.dumps({"completed": []}),
            json.dumps({"completed": "Done"}),
            json.dumps({"completed": [""]}),
            json.dumps({"completed": ["Done", "done"]}),
            json.dumps({"completed": ["Terminal"], "cancelled": ["terminal"]}),
            json.dumps({"unknown": ["Mystery"]}),
        )
        for lanes in invalid_lanes:
            with self.subTest(lanes=lanes), tempfile.TemporaryDirectory(
                prefix="momo-config-test-"
            ) as temp:
                root = pathlib.Path(temp)

                rc, _out, err = self.run_set(root, lanes)

                self.assertNotEqual(rc, 0)
                self.assertIn("invalid configuration", err)
                self.assertFalse((root / ".momo" / "config.json").exists())

    def test_set_rejects_invalid_write_targets_without_writing(self):
        invalid_targets = (
            "{",
            "[]",
            json.dumps({"unknown": "Done"}),
            json.dumps({"completed": ""}),
            json.dumps({"completed": 123}),
            json.dumps({"completed": "Archive"}),
        )
        lanes = json.dumps({"completed": ["Done"]})
        for write_targets in invalid_targets:
            with self.subTest(write_targets=write_targets), tempfile.TemporaryDirectory(
                prefix="momo-config-test-"
            ) as temp:
                root = pathlib.Path(temp)

                rc, _out, err = self.run_set(root, lanes, write_targets)

                self.assertNotEqual(rc, 0)
                self.assertIn("invalid configuration", err)
                self.assertFalse((root / ".momo" / "config.json").exists())

    def test_detect_classifies_custom_cancelled_lane_casefold_consistently(self):
        lane_config = {
            "lanes": {"cancelled": ["Abandoned"]},
            "write_targets": {"cancelled": "Abandoned"},
        }
        info = {
            "board_name": "Test board",
            "board_id": "board-1",
            "config_present": True,
            "list_map": trello_provider.lane_map(lane_config),
            "board_lists": [
                "BACKLOG",
                "to do",
                "IN PROGRESS",
                "review",
                "DONE",
                "ABANDONED",
            ],
        }
        stdout = io.StringIO()

        with (
            mock.patch.object(momo_config, "provider_resolve", return_value=info),
            contextlib.redirect_stdout(stdout),
        ):
            self.assertEqual(momo_config.cmd_detect("/unused"), 0)

        result = json.loads(stdout.getvalue())
        self.assertEqual(result["unmapped_lanes"], [])
        self.assertEqual(result["states_with_missing_lane"], {})
        self.assertTrue(result["is_standard"])


class TestConfigDrift(unittest.TestCase):
    """Verify the current 33GOD project identifier does not drift."""

    def test_project_json_identifier(self):
        data = json.loads((ROOT / ".project.json").read_text())
        self.assertEqual(data["ticket_provider"]["identifier"], "33GOD")

    def test_role_yaml_identifier(self):
        text = (ROOT / "agents" / "hermes" / "pm" / "role.yaml").read_text()
        self.assertIn("33GOD", text)
        # Check the identifier line specifically, not the word "PROJECT" in comments
        for line in text.splitlines():
            if line.strip().startswith("identifier:"):
                self.assertIn("33GOD", line)
                self.assertNotIn("PROJ\"", line)
                break
        else:
            self.fail("no identifier: line found in role.yaml")


class TestBoardCredentialPreflight(unittest.TestCase):
    """JIMB-207: The wrapper recognizes provider-owned fleet credentials."""

    def test_fleet_op_reference_suppresses_false_missing_key_warning(self):
        with tempfile.TemporaryDirectory(prefix="momo-board-test-") as temp:
            root = pathlib.Path(temp) / "repo"
            role = root / "agents" / "hermes" / "pm"
            adapter = role / ".scripts" / "lib" / "ticket-provider.sh"
            adapter.parent.mkdir(parents=True)
            (root / ".project.json").write_text(json.dumps({
                "ticket_provider": {"type": "plane", "workspace": "test.space-name"},
                "agents": {"test-pm": {"role_dir": "agents/hermes/pm"}},
            }))
            adapter.write_text('tp() { printf \'{"provider":"plane"}\\n\'; }\n')

            marker = pathlib.Path(temp) / "must-not-exist"
            fleet_env = pathlib.Path(temp) / "fleet.env"
            fleet_env.write_text("\n".join([
                f"UNRELATED=$(touch {marker})",
                "PLANE_TEST_SPACE_NAME_API_KEY=op://Example/Plane/apiKey",
            ]) + "\n")
            env = os.environ.copy()
            env.pop("PLANE_API_KEY", None)
            env.pop("PLANE_TEST_SPACE_NAME_API_KEY", None)
            env["HERMES_FLEET_ENV"] = str(fleet_env)

            result = subprocess.run(
                ["bash", str(SCRIPTS / "momo-board.sh"), "--root", str(root), "resolve"],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                timeout=15,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("momo-board: WARN", result.stderr)
            self.assertNotIn("op://", result.stdout + result.stderr)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
