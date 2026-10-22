#!/usr/bin/env python3
"""Offline tests for scripts/pa. Run: python3 <skill>/scripts/test_pa.py -v

The engine tests start FlowAgent locally (no sign-in, no network) and are skipped when node or
the engine is missing.
"""

import importlib.machinery
import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_loader = importlib.machinery.SourceFileLoader("pa", str(HERE / "pa"))
_spec = importlib.util.spec_from_loader("pa", _loader)
pa = importlib.util.module_from_spec(_spec)
_loader.exec_module(pa)
PATTERNS = HERE.parent / "references" / "patterns"


class ProfileTests(unittest.TestCase):
    def test_reads_known_keys_without_overriding(self):
        with tempfile.TemporaryDirectory() as d:
            prof = Path(d) / "profile.env"
            prof.write_text("# c\nPA_TENANT_ID=t-1\nexport PA_LOGIN_HINT='a@b'\nSECRET=x\nPA_CLOUD=already\n")
            saved = {k: os.environ.get(k) for k in ("PA_PROFILE", "PA_TENANT_ID", "PA_LOGIN_HINT", "SECRET", "PA_CLOUD")}
            try:
                for k in saved:
                    os.environ.pop(k, None)
                os.environ["PA_PROFILE"] = str(prof)
                os.environ["PA_CLOUD"] = "commercial"
                pa.load_profile()
                self.assertEqual(os.environ["PA_TENANT_ID"], "t-1")
                self.assertEqual(os.environ["PA_LOGIN_HINT"], "a@b")
                self.assertNotIn("SECRET", os.environ)
                self.assertEqual(os.environ["PA_CLOUD"], "commercial")
                self.assertEqual(pa.engine_env()["PA_DEFAULT_ENVIRONMENT"], "Default-t-1")
                self.assertEqual(pa.engine_env()["FLOWAGENT_TELEMETRY"], "0")
            finally:
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v


class HelperTests(unittest.TestCase):
    def test_render_prefers_structured_then_json_text(self):
        self.assertEqual(json.loads(pa.render_result({"structuredContent": {"a": 1}, "content": []})), {"a": 1})
        self.assertEqual(json.loads(pa.render_result({"content": [{"type": "text", "text": '{"b": 2}'}]})), {"b": 2})
        self.assertEqual(pa.render_result({"content": [{"type": "text", "text": "plain"}]}), "plain")

    def test_apply_kv_parses_json_values(self):
        self.assertEqual(pa.apply_kv({}, ["top=5", "name=Forum", 'deps={"g":1}', "wait=true"]),
                         {"top": 5, "name": "Forum", "deps": {"g": 1}, "wait": True})

    def test_resource_inference(self):
        self.assertEqual(pa._resource_for("https://api.flow.microsoft.com/x", None), pa.FLOW_RESOURCE)
        self.assertEqual(pa._resource_for("https://org1.crm.dynamics.com/api", None), "https://org1.crm.dynamics.com")
        self.assertEqual(pa._resource_for("https://graph.microsoft.com/v1.0/me", None), "https://graph.microsoft.com")
        with self.assertRaises(SystemExit):
            pa._resource_for("https://example.com/", None)

    def test_patterns_are_json(self):
        files = sorted(PATTERNS.glob("*.json"))
        self.assertGreaterEqual(len(files), 4)
        for f in files:
            json.loads(f.read_text())


@unittest.skipUnless(shutil.which("node") and pa.find_engine(required=False), "node or FlowAgent engine missing")
class EngineTests(unittest.TestCase):
    def setUp(self):
        self.eng = pa.Engine(pa.find_engine()[1], quiet=True, timeout=60)

    def tearDown(self):
        self.eng.close()

    def test_lists_tools(self):
        names = {t["name"] for t in self.eng.tools()}
        for needed in ("list_flows", "get_flow", "edit_flow", "create_flow", "validate_flow", "publish_flow"):
            self.assertIn(needed, names)

    def test_relay_patterns_validate(self):
        for name in ("teams-chat-to-email-relay.json", "teams-channel-to-email-relay.json"):
            doc = json.loads((PATTERNS / name).read_text())
            res = self.eng.call("validate_flow", {"definition": doc["definition"], "connectionRefs": doc["connectionReferences"]})
            self.assertTrue(json.loads(pa.render_result(res))["valid"], name)


if __name__ == "__main__":
    unittest.main()
