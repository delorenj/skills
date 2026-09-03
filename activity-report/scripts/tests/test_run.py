"""run.sh end to end against fakes: a fake `activity-report` that records every
call and writes what each stage would, and a fake `claude` that writes the
raw.txt named in its prompt. No production test hooks; the script under test is
the real scripts/run.sh copied beside the fakes."""
import fcntl
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.dirname(SCRIPTS)
FX = os.path.join(SCRIPTS, "tests", "fixtures", "publish")
GRANT = "Read,Write,Edit,Glob,Grep,Skill,Bash(activity-report lint:*),Bash(git log:*),Bash(git show:*),Bash(git diff:*)"

FAKE_CLI = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, shutil, sys
    argv = sys.argv[1:]
    with open(os.environ["FAKE_LOG"], "a") as fh:
        fh.write(json.dumps(argv) + "\\n")
    fx, repo = os.environ["FAKE_FIXTURES"], os.environ["FAKE_REPO"]
    def opt(name):
        return argv[argv.index(name) + 1] if name in argv else None
    cmd = argv[0] if argv else ""
    if cmd == "resolve":
        portal = {"kind": "automatic-ai", "project_id": "9f1c1d4e-0a1b-4c2d-8e3f-000000000002"} if os.environ.get("FAKE_PORTAL") else None
        durable = os.environ.get("FAKE_DURABLE", "deliverables/activity") or None
        print(json.dumps({"project": {"slug": "smoketest-project", "name": "Smoketest Project", "identifier": "SMK",
              "repo_path": repo, "timezone": "America/New_York",
              "config": {"audiences": ["internal", "external"],
                         "compose": {"model": os.environ.get("FAKE_CONFIG_MODEL") or None, "timeout_minutes": 1},
                         "output": {"runtime_dir": "runtime/activity-report", "durable_html_dir": durable},
                         "portal": portal, "hindsight": {"retain": os.environ.get("FAKE_RETAIN", "1") == "1"}}},
              "scope": {}}))
    elif cmd == "collect":
        audience, out = opt("--audience"), opt("--out")
        rc = int(os.environ.get("FAKE_COLLECT_RC_" + audience.upper(), "0"))
        if rc:
            sys.exit(rc)
        with open(os.path.join(fx, audience + ".digest.json")) as fh:
            digest = json.load(fh)
        label = os.environ.get("FAKE_DIGEST_LABEL") or os.path.basename(out).split("-" + audience + ".digest.json")[0]
        digest["label"] = label
        digest["run_id"] = opt("--run-id")
        with open(out, "w") as fh:
            json.dump(digest, fh)
        if audience == "external":
            shutil.copy(os.path.join(fx, "2026-09-03T0300-external.lint.json"), os.path.join(os.path.dirname(out), label + "-external.lint.json"))
    elif cmd == "lint":
        sys.exit(int(os.environ.get("FAKE_LINT_RC", "0")))
    elif cmd == "render":
        open(opt("--md"), "w").write("# md\\n")
        open(opt("--html"), "w").write("<!doctype html>\\n<p>fake</p>\\n")
    elif cmd == "assemble":
        with open(opt("--out"), "w") as fh:
            json.dump({"fake": True, "model": opt("--model"), "dry_run": "--dry-run" in argv}, fh)
    elif cmd == "emit":
        with open(opt("--out"), "w") as fh:
            json.dump({"check": {"rc": 0}, "publish": None if "--dry-run" in argv else {"rc": 0}}, fh)
    elif cmd in ("verify", "portal", "retain"):
        sys.exit(int(os.environ.get("FAKE_" + cmd.upper() + "_RC", "0")))
    else:
        sys.exit(9)
""")

FAKE_CLAUDE = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, re, sys
    argv = sys.argv[1:]
    with open(os.environ["FAKE_LOG"], "a") as fh:
        fh.write(json.dumps(["claude"] + argv) + "\\n")
    prompt = argv[-1]
    m = re.search(r"Write exactly ONE file:\\n(\\S+)", prompt)
    if m and not os.environ.get("FAKE_CLAUDE_NO_RAW"):
        with open(m.group(1), "w") as fh:
            fh.write("# Fake title\\n\\n## The day\\n- something happened\\n")
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 3, "total_cost_usd": 0.12,
                      "stop_reason": "end_turn", "result": "ok",
                      "modelUsage": {"claude-opus-5[1m]": {"outputTokens": 500, "canonicalModel": "claude-opus-5"},
                                     "claude-haiku-4-5": {"outputTokens": 50, "canonicalModel": "claude-haiku-4-5-20251001"}}}))
    sys.exit(int(os.environ.get("FAKE_CLAUDE_RC", "0")))
""")


class Harness:
    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix="ar-run-")
        self.home = os.path.join(self.tmp, "home")
        self.repo = os.path.join(self.tmp, "repo")
        self.skill = os.path.join(self.tmp, "skill")
        self.state = os.path.join(self.tmp, "state")
        self.log = os.path.join(self.tmp, "calls.jsonl")
        for d in (os.path.join(self.home, ".local", "bin"), self.repo, os.path.join(self.skill, "scripts"), self.state):
            os.makedirs(d, exist_ok=True)
        shutil.copytree(os.path.join(SKILL, "templates"), os.path.join(self.skill, "templates"))
        shutil.copy(os.path.join(SCRIPTS, "run.sh"), os.path.join(self.skill, "scripts", "run.sh"))
        for path, body in ((os.path.join(self.skill, "scripts", "activity-report"), FAKE_CLI),
                           (os.path.join(self.home, ".local", "bin", "activity-report"), FAKE_CLI),
                           (os.path.join(self.home, ".local", "bin", "claude"), FAKE_CLAUDE)):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            os.chmod(path, 0o755)
        self.work = os.path.join(self.repo, "runtime", "activity-report", "smoketest-project")

    def run(self, *args, env=None):
        full_env = {k: v for k, v in os.environ.items() if not k.startswith("FAKE_") and k != "ACTIVITY_REPORT_DRY"}
        full_env.update({"HOME": self.home, "XDG_STATE_HOME": self.state, "FAKE_LOG": self.log, "FAKE_FIXTURES": FX,
                         "FAKE_REPO": self.repo, "FAKE_PORTAL": "1"})
        full_env.update(env or {})
        return subprocess.run(["bash", os.path.join(self.skill, "scripts", "run.sh"), *args], env=full_env,
                              capture_output=True, text=True, timeout=120)

    def calls(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def stages(self):
        return [c[0] + ("" if c[0] in ("resolve", "claude") else ":" + (c[c.index("--audience") + 1] if "--audience" in c else "-"))
                for c in self.calls()]

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class RunSh(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.addCleanup(self.h.close)

    def test_syntax(self):
        for script in ("run.sh", "install-timer.sh"):
            proc = subprocess.run(["bash", "-n", os.path.join(SCRIPTS, script)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_full_run_both_audiences(self):
        proc = self.h.run("--project", "smoketest-project")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        stages = self.h.stages()
        expected = ["resolve"]
        for a in ("internal", "external"):
            expected += [f"collect:{a}", "claude", f"lint:{a}", f"render:{a}", f"assemble:{a}", f"emit:-", f"verify:{a}", "portal:-", f"retain:{a}"]
        self.assertEqual(stages, expected)
        calls = self.h.calls()
        claude_calls = [c for c in calls if c[0] == "claude"]
        for c in claude_calls:
            self.assertEqual(c[c.index("--allowed-tools") + 1], GRANT)
            self.assertIn("--print", c)
            self.assertEqual(c[c.index("--output-format") + 1], "json")
            self.assertIn("Nobody is watching", c[c.index("--append-system-prompt") + 1])
            self.assertNotIn("--model", c)
        internal_raw = glob.glob(os.path.join(self.h.work, "*-internal.raw.txt"))
        self.assertEqual(len(internal_raw), 1)
        self.assertIn(internal_raw[0], claude_calls[1][-1])
        self.assertNotIn("{{", claude_calls[1][-1])
        self.assertIn("The previous update was titled: Invoice drafts reach the CRM", claude_calls[1][-1])
        assembles = [c for c in calls if c[0] == "assemble"]
        for c in assembles:
            self.assertEqual(c[c.index("--model") + 1], "claude-opus-5")
            self.assertNotIn("--dry-run", c)
        emits = [c for c in calls if c[0] == "emit"]
        self.assertTrue(all("--dry-run" not in c for c in emits))
        collects = [c for c in calls if c[0] == "collect"]
        run_ids = {c[c.index("--run-id") + 1] for c in collects}
        self.assertEqual(len(run_ids), 1)
        lints = [c for c in calls if c[0] == "lint"]
        self.assertIn("--lint-json", lints[1])
        self.assertTrue(lints[1][lints[1].index("--lint-json") + 1].endswith("-external.lint.json"))
        self.assertNotIn("--lint-json", lints[0])
        verifies = [c for c in calls if c[0] == "verify"]
        self.assertEqual(verifies[0][verifies[0].index("--run-id") + 1], run_ids.pop())
        for a in ("internal", "external"):
            self.assertEqual(len(glob.glob(os.path.join(self.h.repo, "deliverables", "activity", f"*-{a}.html"))), 1)
            logs = glob.glob(os.path.join(self.h.state, "activity-report", "smoketest-project", f"*-{a}.log"))
            self.assertEqual(len(logs), 1)
            with open(logs[0], encoding="utf-8") as fh:
                self.assertIn(f"===== {a} done =====", fh.read())
        self.assertEqual(len(glob.glob(os.path.join(self.h.work, "*-external.compose.json"))), 1)

    def test_dry_run_flag_and_env(self):
        for how in (("--dry-run",), ()):
            h = Harness()
            self.addCleanup(h.close)
            proc = h.run("--project", "smoketest-project", *how, env={} if how else {"ACTIVITY_REPORT_DRY": "1"})
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            stages = h.stages()
            self.assertNotIn("verify:internal", stages)
            self.assertNotIn("portal:-", stages)
            self.assertNotIn("retain:internal", stages)
            self.assertIn("emit:-", stages)
            assembles = [c for c in h.calls() if c[0] == "assemble"]
            self.assertTrue(all("--dry-run" in c for c in assembles))
            self.assertEqual(glob.glob(os.path.join(h.repo, "deliverables", "activity", "*.html")), [])

    def test_audience_flags_and_order(self):
        proc = self.h.run("--project", "smoketest-project", "--audience", "external")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        stages = self.h.stages()
        self.assertNotIn("collect:internal", stages)
        self.assertIn("collect:external", stages)
        claude = [c for c in self.h.calls() if c[0] == "claude"][0]
        self.assertIn("the complete account of the window: none.", claude[-1])

    def test_nothing_to_do_is_ok(self):
        proc = self.h.run("--project", "smoketest-project", env={"FAKE_COLLECT_RC_EXTERNAL": "4"})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        stages = self.h.stages()
        self.assertIn("retain:internal", stages)
        self.assertEqual(stages[-1], "collect:external")
        self.assertIn("nothing to do", proc.stdout)

    def test_lint_refusal_stops_the_audience(self):
        proc = self.h.run("--project", "smoketest-project", env={"FAKE_LINT_RC": "3"})
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        stages = self.h.stages()
        self.assertNotIn("render:internal", stages)
        self.assertNotIn("emit:-", stages)
        self.assertIn("collect:external", stages)
        self.assertIn("nothing emitted", proc.stdout)

    def test_compose_without_raw_is_exit_2(self):
        proc = self.h.run("--project", "smoketest-project", "--audience", "internal", env={"FAKE_CLAUDE_NO_RAW": "1"})
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertNotIn("lint:internal", self.h.stages())
        self.assertIn("wrote no", proc.stdout)
        self.assertEqual(len(glob.glob(os.path.join(self.h.work, "*-internal.digest.json"))), 1)

    def test_compose_failure_is_exit_2(self):
        proc = self.h.run("--project", "smoketest-project", "--audience", "internal", env={"FAKE_CLAUDE_RC": "1"})
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)

    def test_worst_code_wins(self):
        proc = self.h.run("--project", "smoketest-project", env={"FAKE_VERIFY_RC": "3", "FAKE_COLLECT_RC_EXTERNAL": "4"})
        self.assertEqual(proc.returncode, 3)

    def test_retain_failure_is_a_warning(self):
        proc = self.h.run("--project", "smoketest-project", "--audience", "internal", env={"FAKE_RETAIN_RC": "2"})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("warning: retain exited 2", proc.stdout)

    def test_no_portal_and_no_durable(self):
        proc = self.h.run("--project", "smoketest-project", "--audience", "internal", env={"FAKE_PORTAL": "", "FAKE_DURABLE": "", "FAKE_RETAIN": "0"})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        stages = self.h.stages()
        self.assertNotIn("portal:-", stages)
        self.assertNotIn("retain:internal", stages)
        self.assertIn("no portal configured", proc.stdout)

    def test_digest_label_wins(self):
        proc = self.h.run("--project", "smoketest-project", "--audience", "external", env={"FAKE_DIGEST_LABEL": "2026-09-03T0300"})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.h.work, "2026-09-03T0300-external.raw.txt")))
        lints = [c for c in self.h.calls() if c[0] == "lint"]
        self.assertEqual(lints[0][lints[0].index("--lint-json") + 1], os.path.join(self.h.work, "2026-09-03T0300-external.lint.json"))

    def test_lock(self):
        os.makedirs(self.h.work, exist_ok=True)
        fd = os.open(os.path.join(self.h.work, ".lock"), os.O_WRONLY | os.O_CREAT)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            proc = self.h.run("--project", "smoketest-project")
        finally:
            os.close(fd)
        self.assertEqual(proc.returncode, 5, proc.stdout + proc.stderr)
        self.assertEqual([s for s in self.h.stages() if s != "resolve"], [])

    def test_bad_arguments(self):
        self.assertEqual(self.h.run("--bogus").returncode, 2)
        self.assertEqual(self.h.run("--project", "smoketest-project", "--audience", "client").returncode, 2)
        self.assertEqual(self.h.run("--help").returncode, 0)

    def test_model_from_config_when_compose_json_lacks_it(self):
        proc = self.h.run("--project", "smoketest-project", "--audience", "internal", env={"FAKE_CONFIG_MODEL": "claude-sonnet-5"})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        claude = [c for c in self.h.calls() if c[0] == "claude"][0]
        self.assertEqual(claude[claude.index("--model") + 1], "claude-sonnet-5")
        assemble = [c for c in self.h.calls() if c[0] == "assemble"][0]
        self.assertEqual(assemble[assemble.index("--model") + 1], "claude-opus-5")


if __name__ == "__main__":
    unittest.main()
