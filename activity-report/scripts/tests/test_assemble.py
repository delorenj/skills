import contextlib
import copy
import io
import json
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import __version__, assemble, contract, render  # noqa: E402
from ar.common import ConfigError, ContractError  # noqa: E402

FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "publish")


def read(name):
    with open(os.path.join(FX, name), encoding="utf-8") as fh:
        return fh.read()


def load(name):
    with open(os.path.join(FX, name), encoding="utf-8") as fh:
        return json.load(fh)


def build(audience, digest=None, raw=None, **kw):
    digest = digest or load(f"{audience}.digest.json")
    raw = raw or read(f"{audience}.raw.txt")
    title, body = render.split_raw(raw)
    blocks = render.parse(body)
    meta = {"project_name": digest["project"]["name"], "audience": audience, "window_start": digest["window"]["start"],
            "window_end": digest["window"]["end"], "tz": digest["project"]["timezone"], "run_id": digest["run_id"],
            "generated_at": digest["generated_at"], "duration_seconds": digest["window"]["duration_seconds"]}
    md = render.to_markdown(title, blocks)
    html = render.to_html(title, blocks, meta)
    params = {"model": "claude-opus-5", "dry_run": False}
    params.update(kw)
    return assemble.assemble(digest, raw, md, html, **params)


class Mapping(unittest.TestCase):
    def test_internal_event(self):
        data = build("internal")
        contract.validate_event(data)
        self.assertEqual(list(data), ["schema_version", "project", "audience", "window", "report", "tokens", "generator", "sources", "tickets"])
        self.assertEqual(data["project"], {"slug": "smoketest-project", "name": "Smoketest Project", "identifier": "SMK",
                                           "workspace": "automaticai", "board_id": "0b1c2d3e-4f50-4617-8899-aabbccddeeff",
                                           "repos": ["smoketest-project", "smoketest-mirror"]})
        self.assertEqual(data["window"], {"start": "2026-09-02T07:00:00Z", "end": "2026-09-03T07:00:00Z", "duration_seconds": 86400,
                                          "basis": "previous_report", "previous_event_id": "85bbe34e-1111-4222-8333-444455556666"})
        self.assertEqual(data["report"]["title"], "Invoice drafts land in the CRM; credential rotation started")
        self.assertTrue(data["report"]["raw"].startswith("## The day"))
        self.assertTrue(data["report"]["html"].startswith("<!doctype html>"))
        self.assertEqual(data["generator"], {"skill": "activity-report", "skill_version": __version__,
                                             "run_id": "4c1f2e8a-3b5d-4e6f-9a7b-1c2d3e4f5a6b", "model": "claude-opus-5", "dry_run": False})
        self.assertEqual(data["tokens"], {"total": 123456, "by_agent": {
            "claude": {"input": 100000, "output": 20000, "cache_read": 3000, "cache_write": 456, "total": 123456},
            "codex": None, "kimi": None}})
        git = data["sources"]["git"]
        self.assertEqual(list(git), ["smoketest-project"])  # state missing is dropped
        self.assertEqual(len(git["smoketest-project"]["commits"]), 4)
        self.assertEqual(git["smoketest-project"]["commits"][0], {"sha": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
                                                                  "subject": "feat(relay): draft invoice reaches the CRM",
                                                                  "author": "Jarad DeLorenzo", "at": "2026-09-02T13:40:00Z"})
        self.assertEqual(git["smoketest-project"]["branches"], ["main", "feat/invoice-draft"])
        self.assertEqual(data["sources"]["candystore"], {"sessions": 6, "tool_calls": 412, "by_cli": {"claude": 380, "codex": 32}})
        self.assertEqual(data["sources"]["board"], {"closed": ["SMK-214"], "opened": ["SMK-240"], "started": ["SMK-231"]})
        self.assertEqual(data["sources"]["hindsight"], {"bank": "smoketest-project", "facts": 2})
        self.assertEqual([t["key"] for t in data["tickets"]], ["SMK-214", "SMK-231", "SMK-240"])
        self.assertEqual(data["tickets"][2], {"key": "SMK-240", "title": "Voice line greets by name", "from_state": None,
                                              "to_state": "Backlog", "labels": [], "exposure": "unlabeled"})
        self.assertEqual(data["tickets"][0]["labels"], ["xp:external", "relay"])

    def test_external_event(self):
        data = build("external", model=None, dry_run=True)
        contract.validate_event(data)
        self.assertNotIn("sources", data)
        self.assertNotIn("tickets", data)
        self.assertIsNone(data["generator"]["model"])
        self.assertTrue(data["generator"]["dry_run"])

    def test_tokens_recomputed(self):
        d = load("internal.digest.json")
        d["tokens"]["total"] = 1
        d["tokens"]["by_agent"]["claude"]["total"] = 9
        d["tokens"]["by_agent"]["codex"] = {"input": 10, "output": 5}
        d["tokens"]["by_agent"]["hermes"] = {"input": 999}
        data = build("internal", digest=d)
        self.assertEqual(data["tokens"]["by_agent"]["claude"]["total"], 123456)
        self.assertEqual(data["tokens"]["by_agent"]["codex"], {"input": 10, "output": 5, "cache_read": 0, "cache_write": 0, "total": 15})
        self.assertEqual(data["tokens"]["total"], 123471)
        self.assertEqual(set(data["tokens"]["by_agent"]), {"claude", "codex", "kimi"})

    def test_truncation(self):
        d = load("internal.digest.json")
        repo = d["git"]["repos"][0]
        base = repo["commits"][0]
        repo["commits"] = [dict(base, sha=f"{i:040x}"[-40:].replace("0", "a", 1), subject="s" * 150, author="") for i in range(150)]
        for c in repo["commits"]:
            c["sha"] = ("%040x" % (0xabc123 + int(c["sha"].replace("a", "0", 1), 16)))
        repo["branches"] = [f"branch-{i}" for i in range(70)]
        d["board"]["tickets"] = [dict(d["board"]["tickets"][0], key=f"SMK-{i}", title="t" * 250, labels=[f"label-{j}" * 5 for j in range(10)])
                                 for i in range(230)]
        d["board"]["closed"] = [f"SMK-{i}" for i in range(230)] + ["bad key", {"key": "SMK-5"}]
        d["project"]["repos"] = [f"repo{i}" for i in range(12)]
        d["project"]["name"] = "n" * 200
        data = build("internal", digest=d, model="m" * 200)
        git = data["sources"]["git"]["smoketest-project"]
        self.assertEqual(len(git["commits"]), 100)
        self.assertTrue(git["truncated"])
        self.assertEqual(len(git["commits"][0]["subject"]), 120)
        self.assertEqual(git["commits"][0]["author"], "unknown")
        self.assertEqual(len(git["branches"]), 64)
        self.assertEqual(len(data["tickets"]), 200)
        self.assertEqual(len(data["tickets"][0]["title"]), 200)
        self.assertEqual(len(data["tickets"][0]["labels"]), 8)
        self.assertTrue(all(len(l) <= 40 for l in data["tickets"][0]["labels"]))
        self.assertEqual(len(data["sources"]["board"]["closed"]), 200)
        self.assertEqual(len(data["project"]["repos"]), 8)
        self.assertEqual(len(data["project"]["name"]), 120)
        self.assertEqual(len(data["generator"]["model"]), 120)

    def test_git_repos_capped_and_filtered(self):
        d = load("internal.digest.json")
        ok = d["git"]["repos"][0]
        d["git"]["repos"] = [dict(ok, name=f"r{i}") for i in range(10)] + [dict(ok, name="bad name")]
        data = build("internal", digest=d)
        self.assertEqual(len(data["sources"]["git"]), 8)
        self.assertNotIn("bad name", data["sources"]["git"])

    def test_by_cli_and_bank_fallbacks(self):
        d = load("internal.digest.json")
        d["candystore"]["by_cli"] = {"Claude Code": 1, "codex": 2, "kimi": "3", "": 4}
        d["hindsight"]["bank"] = "not valid!"
        d["hindsight"]["items"] = 7
        data = build("internal", digest=d)
        self.assertEqual(data["sources"]["candystore"]["by_cli"], {"codex": 2, "kimi": 3})
        self.assertEqual(data["sources"]["hindsight"], {"bank": "smoketest-project", "facts": 7})

    def test_absolute_path_in_digest_refused(self):
        d = load("internal.digest.json")
        d["git"]["repos"][0]["commits"][0]["subject"] = "notes in /home/x/y"
        with self.assertRaises(ContractError):
            build("internal", digest=d)

    def test_external_with_ticket_key_refused(self):
        with self.assertRaises(ContractError):
            build("external", raw=read("external-dirty.raw.txt"))

    def test_audience_required(self):
        d = load("internal.digest.json")
        d["audience"] = "client"
        with self.assertRaises(ConfigError):
            build("internal", digest=d)


class AssembleCmd(unittest.TestCase):
    def test_writes_event_next_to_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            digest = os.path.join(tmp, "2026-09-03T0300-internal.digest.json")
            with open(digest, "w", encoding="utf-8") as fh:
                json.dump(load("internal.digest.json"), fh)
            raw = os.path.join(FX, "internal.raw.txt")
            title, body = render.split_raw(read("internal.raw.txt"))
            blocks = render.parse(body)
            md, html = os.path.join(tmp, "x.md"), os.path.join(tmp, "x.html")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(render.to_markdown(title, blocks))
            with open(html, "w", encoding="utf-8") as fh:
                fh.write(render.to_html(title, blocks, {"project_name": "P", "audience": "internal", "window_start": "2026-09-02T07:00:00Z",
                                                        "window_end": "2026-09-03T07:00:00Z", "tz": "UTC", "run_id": "r"}))
            args = types.SimpleNamespace(digest=digest, raw=raw, md=md, html=html, out=None, model="claude-opus-5", dry_run=True,
                                         audience="internal", project="no-such-project-slug", json=True)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(assemble.assemble_cmd(args), 0)
            out = json.loads(buf.getvalue())
            self.assertEqual(out["event"], os.path.join(tmp, "2026-09-03T0300-internal.event.json"))
            with open(out["event"], encoding="utf-8") as fh:
                data = json.load(fh)
            contract.validate_event(data)
            self.assertTrue(data["generator"]["dry_run"])
            args.audience = "external"
            with self.assertRaises(ConfigError):
                assemble.assemble_cmd(args)


if __name__ == "__main__":
    unittest.main()
