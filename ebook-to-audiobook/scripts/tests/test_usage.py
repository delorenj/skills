import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
import usage
from abk_common import AbkError

PRICING = {"rates_usd_per_million": {"uncached_input_per_million": 2.0, "cache_read_per_million": 0.1,
                                     "cache_write_per_million": 2.5, "output_per_million": 10.0}}


def message(completed=True, **tokens):
    info = {"role": "assistant", "modelID": "m", "providerID": "p", "cost": 0,
            "tokens": {"input": 0, "output": 0, "reasoning": 0, "cache": {"read": 0, "write": 0}, **tokens}}
    if completed:
        info["time"] = {"completed": 1}
    return {"info": info}


class SummaryTests(unittest.TestCase):
    def test_incomplete_and_user_messages_excluded(self):
        data = {"info": {"id": "s"}, "messages": [
            message(input=10, output=2, total=12), message(completed=False, input=999),
            {"info": {"role": "user", "tokens": {"input": 5}}}]}
        s = usage.summarize_session(data)
        self.assertEqual((s["input_tokens"], s["completed_assistant_messages"], s["incomplete_assistant_messages_excluded"]), (10, 1, 1))

    def test_missing_fields_are_flagged_not_estimated(self):
        s = usage.summarize_session({"info": {"id": "s"}, "messages": [{"info": {"role": "assistant", "time": {"completed": 1}}}]})
        self.assertEqual((s["messages_missing_usage"], s["messages_missing_total_tokens"], s["messages_missing_cost"]), (1, 1, 1))


class DbTests(unittest.TestCase):
    def build_db(self, tmp):
        path = Path(tmp) / "o.db"
        conn = sqlite3.connect(path)
        conn.executescript(
            "create table session(id, parent_id, directory, title, time_created);"
            "create table message(id, session_id, time_created, data);")
        conn.executemany("insert into session values(?,?,?,?,?)", [
            ("main", None, "/d", "main", 1), ("kid", "main", "/d", "kid", 2), ("grandkid", "kid", "/d", "gk", 3),
            ("other", None, "/d", "other", 4)])
        for sid, n in (("main", 5), ("kid", 7), ("grandkid", 11), ("other", 1000)):
            conn.execute("insert into message values(?,?,?,?)", (f"m-{sid}", sid, 1, json.dumps(message(input=n)["info"])))
        conn.commit()
        conn.close()
        return path

    def test_children_are_discovered_transitively_and_unrelated_sessions_are_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self.build_db(tmp)
            self.assertEqual(usage.child_sessions(["main"], db), ["main", "kid", "grandkid"])
            data = usage.export_session_from_db("kid", db)
            self.assertEqual(usage.summarize_session(data)["parent_session_id"], "main")
            with self.assertRaises(AbkError):
                usage.export_session_from_db("missing", db)

    def test_capture_sums_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self.build_db(tmp)
            report = usage.capture(["main"], children=True, db_path=db,
                                   exporter=lambda sid: usage.export_session_from_db(sid, db))
            self.assertEqual(report["totals"]["input_tokens"], 5 + 7 + 11)
            self.assertEqual(len(report["sessions"]), 3)
            self.assertIsNone(report["actual_llm_charge_usd"])


class CostTests(unittest.TestCase):
    def test_pilot_numbers_reproduce(self):
        totals = {"input_tokens": 13_552_862, "cache_read_tokens": 3_530_240, "cache_write_tokens": 0, "output_tokens": 194_612}
        result = usage.api_equivalent(totals, PRICING)
        self.assertAlmostEqual(result["usd"], 29.404868, places=5)
        self.assertTrue(result["not_actual_charge"])

    def test_missing_inputs_yield_null_not_a_guess(self):
        self.assertIsNone(usage.api_equivalent({"input_tokens": 1}, PRICING)["usd"])
        self.assertIsNone(usage.api_equivalent({"input_tokens": 1, "cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": 0}, {})["usd"])

    def test_invalid_values_refused(self):
        with self.assertRaises(AbkError):
            usage.api_equivalent({"input_tokens": -1, "cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": 0}, PRICING)
        with self.assertRaises(AbkError):
            usage.electricity_scenario(10, 350, 150, 0.15)

    def test_energy_scenario_matches_pilot(self):
        e = usage.electricity_scenario(1460.767, 150, 350, 0.15)
        self.assertAlmostEqual(e["usd_low"], 0.0091298, places=5)
        self.assertAlmostEqual(e["usd_high"], 0.0213029, places=5)
        self.assertFalse(e["measured"])

    def test_record_appends_to_book(self):
        import book

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "b"
            book.init_book(root, "T")
            snap = Path(tmp) / "snap.json"
            snap.write_text(json.dumps({"totals": {"input_tokens": 1, "cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": 0},
                                        "sessions": [], "actual_llm_charge_usd": None}))
            pricing = Path(tmp) / "p.json"
            pricing.write_text(json.dumps(PRICING))
            self.assertEqual(usage.main(["record", "--book", str(root), "--chapter", "1", "--label", "build",
                                         "--snapshot", str(snap), "--pricing", str(pricing)]), 0)
            self.assertEqual(book.load(root)["usage"][0]["label"], "build")


if __name__ == "__main__":
    unittest.main()
