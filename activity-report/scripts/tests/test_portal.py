import contextlib
import io
import json
import os
import sys
import types
import unittest
import uuid
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import portal  # noqa: E402
from ar.common import AcceptanceError, ConfigError  # noqa: E402

FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "publish")
PROJECT_ID = "9f1c1d4e-0a1b-4c2d-8e3f-000000000002"


def load(name):
    with open(os.path.join(FX, name), encoding="utf-8") as fh:
        return json.load(fh)


def project(portal_cfg="default"):
    if portal_cfg == "default":
        portal_cfg = {"kind": "automatic-ai", "project_id": PROJECT_ID}
    return types.SimpleNamespace(slug="smoketest-project", config={"portal": portal_cfg})


class RowDerivation(unittest.TestCase):
    def test_row_id_formula(self):
        end = "2026-09-03T07:00:00Z"
        self.assertEqual(portal.row_id(PROJECT_ID, end, "external"),
                         str(uuid.uuid5(uuid.UUID("6f9b1f1e-5d2a-4a3b-9c8d-1a2b3c4d5e6f"), f"{PROJECT_ID}:{end}:client")))
        self.assertEqual(portal.row_id(PROJECT_ID, end, "internal"),
                         str(uuid.uuid5(portal.NAMESPACE, f"{PROJECT_ID}:{end}:internal")))
        self.assertNotEqual(portal.row_id(PROJECT_ID, end, "external"), portal.row_id(PROJECT_ID, end, "internal"))

    def test_build_row_external(self):
        data = load("a5-external.event.json")
        row = portal.build_row(data, project())
        end = data["window"]["end"]
        self.assertEqual(row["id"], portal.row_id(PROJECT_ID, end, "external"))
        self.assertEqual(row["project_id"], PROJECT_ID)
        self.assertEqual(row["kind"], "status")
        self.assertEqual(row["title"], data["report"]["title"].strip())
        self.assertEqual(row["body"], data["report"]["raw"].strip())
        self.assertEqual(row["pinned"], 0)
        self.assertEqual(row["visible_to_client"], 1)
        self.assertEqual(row["occurred_at"], int(portal.parse_iso(end).timestamp() * 1000))
        self.assertEqual(list(row), ["id", "project_id", "kind", "title", "body", "pinned", "visible_to_client", "occurred_at"])

    def test_build_row_internal(self):
        row = portal.build_row(load("a5-internal.event.json"), project())
        self.assertEqual(row["visible_to_client"], 0)

    def test_bounds(self):
        data = load("a5-external.event.json")
        data["report"]["title"] = "x"
        with self.assertRaises(AcceptanceError):
            portal.build_row(data, project())
        data = load("a5-external.event.json")
        data["report"]["raw"] = "y" * 5001
        with self.assertRaises(AcceptanceError):
            portal.build_row(data, project())

    def test_config_checks(self):
        data = load("a5-external.event.json")
        with self.assertRaises(ConfigError):
            portal.build_row(data, project({"kind": "other", "project_id": PROJECT_ID}))
        with self.assertRaises(ConfigError):
            portal.build_row(data, project({"project_id": "not-a-uuid"}))
        with self.assertRaises(ConfigError):
            portal.build_row(data, types.SimpleNamespace(slug="another", config={"portal": {"project_id": PROJECT_ID}}))
        self.assertEqual(portal.portal_config(project({"project_id": PROJECT_ID}))["kind"], "automatic-ai")


class Publish(unittest.TestCase):
    def test_no_portal(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = portal.publish(load("a5-external.event.json"), project(None), dry_run=False)
        self.assertEqual(result, {"skipped": "no portal configured"})
        self.assertIn("no portal configured", buf.getvalue())

    def test_dry_run_reads_only(self):
        calls = []

        def fake_d1(sql, params):
            calls.append((sql.strip().split()[0].upper(), params))
            return []
        buf = io.StringIO()
        with mock.patch.object(portal, "d1_query", side_effect=fake_d1), contextlib.redirect_stdout(buf):
            result = portal.publish(load("a5-external.event.json"), project(), dry_run=True)
        self.assertEqual([c[0] for c in calls], ["SELECT"])
        self.assertEqual(calls[0][1], [result["row"]["id"]])
        self.assertTrue(result["dry_run"])
        self.assertIsNone(result["existing"])
        self.assertIn("nothing written", buf.getvalue())
        self.assertNotIn(result["row"]["body"], buf.getvalue())

    def test_publish_upserts_then_reads_back(self):
        calls = []

        def fake_d1(sql, params):
            calls.append((sql.strip().split()[0].upper(), params))
            if sql.strip().upper().startswith("SELECT"):
                return [{"id": params[0], "visible_to_client": 1, "n": 42, "title": "t"}]
            return []
        buf = io.StringIO()
        with mock.patch.object(portal, "d1_query", side_effect=fake_d1), contextlib.redirect_stdout(buf):
            result = portal.publish(load("a5-external.event.json"), project(), dry_run=False)
        self.assertEqual([c[0] for c in calls], ["INSERT", "SELECT"])
        row = result["row"]
        params = calls[0][1]
        self.assertEqual(params[:7], [row["id"], PROJECT_ID, "status", row["title"], row["body"], 1, row["occurred_at"]])
        self.assertIsInstance(params[7], int)
        self.assertIn("ON CONFLICT(id) DO UPDATE", portal.UPSERT_SQL)
        self.assertIn("published external update", buf.getvalue())

    def test_visibility_mismatch_is_refused(self):
        def fake_d1(sql, params):
            if sql.strip().upper().startswith("SELECT"):
                return [{"id": params[0], "visible_to_client": 0, "n": 1, "title": "t"}]
            return []
        with mock.patch.object(portal, "d1_query", side_effect=fake_d1), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(AcceptanceError):
                portal.publish(load("a5-external.event.json"), project(), dry_run=False)

    def test_missing_row_after_write(self):
        with mock.patch.object(portal, "d1_query", return_value=[]), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(AcceptanceError):
                portal.publish(load("a5-internal.event.json"), project(), dry_run=False)


class D1(unittest.TestCase):
    def test_request_shape(self):
        captured = {}

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["headers"] = {k.lower(): v for k, v in req.header_items()}
            captured["body"] = json.loads(req.data.decode())
            return Resp(json.dumps({"success": True, "result": [{"results": [{"id": "x"}]}]}).encode())
        with mock.patch.object(portal, "op_read", side_effect=lambda ref: "secret-for-" + ref.rsplit("/", 1)[1]), \
                mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            rows = portal.d1_query("SELECT 1 WHERE ?1", ["a"])
        self.assertEqual(rows, [{"id": "x"}])
        self.assertEqual(captured["url"], portal.ENDPOINT)
        self.assertEqual(captured["headers"]["x-auth-email"], "secret-for-username")
        self.assertEqual(captured["headers"]["x-auth-key"], "secret-for-globalAPIToken")
        self.assertTrue(captured["headers"]["user-agent"].startswith("activity-report/"))
        self.assertEqual(captured["body"], {"sql": "SELECT 1 WHERE ?1", "params": ["a"]})

    def test_refusal(self):
        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        with mock.patch.object(portal, "op_read", return_value="x"), \
                mock.patch("urllib.request.urlopen", return_value=Resp(json.dumps({"success": False, "errors": [{"code": 7}]}).encode())):
            with self.assertRaises(ConfigError):
                portal.d1_query("SELECT 1", [])

    def test_op_read_failure(self):
        proc = types.SimpleNamespace(returncode=1, stdout="", stderr="no item")
        with mock.patch("subprocess.run", return_value=proc):
            with self.assertRaises(ConfigError):
                portal.op_read("op://DeLoSecrets/x/y")

    def test_no_secret_literals_in_module(self):
        with open(portal.__file__, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("op://DeLoSecrets/Cloudflare/globalAPIToken", source)
        self.assertNotIn("X-Auth-Key\": \"", source.replace("op_read", ""))


if __name__ == "__main__":
    unittest.main()
