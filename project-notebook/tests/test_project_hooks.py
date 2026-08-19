from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import pwd
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "project-hooks.py"
MASTER_PATH = SKILL_ROOT / "hooks" / "hooks.master.json"
FRAGMENT_PATH = SKILL_ROOT / "hooks" / "claude.settings.json"
OWNER_PREFIX = "PJ_HOOK_OWNER=project-notebook.v1 "
START_COMMAND = (
    "PJ_HOOK_OWNER=project-notebook.v1 "
    '"$HOME/.agents/skills/project-notebook/hooks/session-start.sh"'
)
END_COMMAND = (
    'PJ_HOOK_OWNER=project-notebook.v1 "$HOME/.agents/skills/project-notebook/hooks/session-end.sh"'
)


def _load_projector():
    spec = importlib.util.spec_from_file_location("project_notebook_hooks_tested", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load projector")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PROJECTOR = _load_projector()


class ProjectHooksTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.claude = self.root / ".claude"
        self.claude.mkdir(mode=0o700)
        self.target = self.claude / "settings.json"
        self.state_home = self.root / "state"
        self.master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))

    def run_projector(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *arguments],
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )

    def write_json(self, value: dict, *, compact: bool = False) -> bytes:
        if compact:
            raw = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode()
        else:
            raw = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
        self.target.write_bytes(raw)
        return raw

    def mutation_arguments(self, command: str) -> list[str]:
        return [
            command,
            "--master",
            str(MASTER_PATH),
            "--fragment",
            str(FRAGMENT_PATH),
            "--target",
            str(self.target),
            "--state-home",
            str(self.state_home),
        ]

    def canonical_hook(self, event: str) -> dict:
        return copy.deepcopy(self.master["hooks"][event][0]["hooks"][0])

    def make_fake_pj(
        self, *, name: str = "trusted-home", exit_code: int = 0, hang: bool = False
    ) -> tuple[Path, Path]:
        fake_home = self.root / name
        local = fake_home / ".local"
        binary_directory = local / "bin"
        fake_home.mkdir(mode=0o700)
        local.mkdir(mode=0o700)
        binary_directory.mkdir(mode=0o700)
        resolved_directory = fake_home / "apps" / "pjangler" / "dist"
        resolved_directory.mkdir(parents=True, mode=0o770)
        for directory in (
            fake_home / "apps",
            fake_home / "apps" / "pjangler",
            resolved_directory,
        ):
            directory.chmod(0o770)
        resolved_binary = resolved_directory / "pj-real"
        resolved_binary.write_text(
            "const chunks = [];\n"
            "process.stdin.on('data', (chunk) => chunks.push(chunk));\n"
            "process.stdin.on('end', () => {\n"
            "  const report = {\n"
            "    argv: process.argv.slice(2),\n"
            "    bytes: Buffer.concat(chunks).length,\n"
            "    env: {\n"
            "      HOME: process.env.HOME,\n"
            "      USER: process.env.USER,\n"
            "      LOGNAME: process.env.LOGNAME,\n"
            "      PATH: process.env.PATH,\n"
            "      LANG: process.env.LANG,\n"
            "      LC_ALL: process.env.LC_ALL,\n"
            "      BASH_ENV: process.env.BASH_ENV ?? null,\n"
            "      NODE_OPTIONS: process.env.NODE_OPTIONS ?? null,\n"
            "      NODE_PATH: process.env.NODE_PATH ?? null,\n"
            "      authPresent: Object.hasOwn(process.env, 'OPEN_NOTEBOOK_PASSWORD'),\n"
            "    },\n"
            "  };\n"
            "  console.log(`trusted-pj ${JSON.stringify(report)}`);\n"
            + ("  setInterval(() => {}, 10000);\n" if hang else f"  process.exit({exit_code});\n")
            + "});\n",
            encoding="utf-8",
        )
        resolved_binary.chmod(0o770)
        launcher = binary_directory / "pj"
        launcher.symlink_to(resolved_binary)
        return fake_home, resolved_binary

    def snapshot_tree(self, root: Path) -> dict[str, tuple[str, int, bytes | str]]:
        snapshot: dict[str, tuple[str, int, bytes | str]] = {}
        for path in sorted([root, *root.rglob("*")]):
            relative = "." if path == root else str(path.relative_to(root))
            mode = stat.S_IMODE(path.lstat().st_mode)
            if path.is_symlink():
                snapshot[relative] = ("symlink", mode, os.readlink(path))
            elif path.is_dir():
                snapshot[relative] = ("directory", mode, b"")
            else:
                snapshot[relative] = ("file", mode, path.read_bytes())
        return snapshot

    def run_wrapper(
        self,
        wrapper: str,
        fake_home: Path,
        payload: bytes,
        *,
        path_prefix: Path | None = None,
        extra_environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        instrumented_directory = self.root / "instrumented-wrappers"
        instrumented_directory.mkdir(mode=0o700, exist_ok=True)
        source = (SKILL_ROOT / "hooks" / wrapper).read_text(encoding="utf-8")
        identity = pwd.getpwuid(os.getuid())
        original_lookup = "entry = pwd.getpwuid(os.geteuid())"
        replacement_lookup = (
            "entry = pwd.struct_passwd(("
            f"{identity.pw_name!r}, 'x', {identity.pw_uid}, {identity.pw_gid}, '', "
            f"{str(fake_home)!r}, {identity.pw_shell!r}))"
        )
        self.assertIn(original_lookup, source)
        instrumented = instrumented_directory / wrapper
        instrumented.write_text(
            source.replace(original_lookup, replacement_lookup, 1), encoding="utf-8"
        )
        instrumented.chmod(0o700)
        environment = os.environ.copy()
        environment["HOME"] = str(self.root / "attacker-controlled-home")
        environment["USER"] = "attacker-user"
        environment["LOGNAME"] = "attacker-logname"
        environment["PATH"] = (
            f"{path_prefix}:/usr/bin:/bin" if path_prefix is not None else "/usr/bin:/bin"
        )
        if extra_environment:
            environment.update(extra_environment)
        return subprocess.run(
            [str(instrumented)],
            input=payload,
            capture_output=True,
            check=False,
            env=environment,
        )

    def test_master_fragment_and_wrappers_are_exact(self) -> None:
        self.assertEqual(MASTER_PATH.read_bytes(), FRAGMENT_PATH.read_bytes())
        self.assertEqual(list(self.master["hooks"]), ["SessionStart", "SessionEnd"])
        self.assertNotIn("Stop", self.master["hooks"])
        self.assertEqual(self.canonical_hook("SessionStart")["command"], START_COMMAND)
        self.assertEqual(self.canonical_hook("SessionStart")["timeout"], 3)
        self.assertEqual(self.canonical_hook("SessionEnd")["command"], END_COMMAND)
        self.assertEqual(self.canonical_hook("SessionEnd")["timeout"], 1)

        start_wrapper = (SKILL_ROOT / "hooks" / "session-start.sh").read_text()
        end_wrapper = (SKILL_ROOT / "hooks" / "session-end.sh").read_text()
        self.assertTrue(start_wrapper.startswith("#!/usr/bin/python3 -I\n"))
        self.assertTrue(end_wrapper.startswith("#!/usr/bin/python3 -I\n"))
        self.assertIn('HOOK_EVENT = "session-start"', start_wrapper)
        self.assertIn('HOOK_EVENT = "session-close"', end_wrapper)
        self.assertIn("REQUEST_LIMIT_BYTES = 1_048_576", start_wrapper + end_wrapper)
        self.assertIn("STREAM_LIMIT_BYTES = REQUEST_LIMIT_BYTES + 1", start_wrapper + end_wrapper)
        self.assertIn("len(payload) > REQUEST_LIMIT_BYTES", start_wrapper + end_wrapper)
        self.assertIn('NODE_BINARY = Path("/usr/bin/node")', start_wrapper + end_wrapper)
        self.assertIn("pwd.getpwuid(os.geteuid())", start_wrapper + end_wrapper)
        self.assertNotIn("#!/bin/bash", start_wrapper + end_wrapper)
        self.assertNotIn("--payload-file", start_wrapper + end_wrapper)
        self.assertNotIn("mktemp", start_wrapper + end_wrapper)
        self.assertNotIn("XDG_STATE_HOME", start_wrapper + end_wrapper)
        self.assertNotIn("notebook hook Stop", start_wrapper + end_wrapper)

    def test_wrappers_stream_bounded_stdin_to_only_the_fixed_trusted_binary(self) -> None:
        fake_home, _ = self.make_fake_pj()
        self.assertTrue((fake_home / ".local" / "bin" / "pj").is_symlink())
        malicious_directory = self.root / "malicious-path"
        malicious_directory.mkdir(mode=0o700)
        malicious = malicious_directory / "pj"
        malicious.write_text(
            "#!/usr/bin/python3 -I\nraise SystemExit('MALICIOUS')\n", encoding="utf-8"
        )
        malicious.chmod(0o700)
        malicious_node = malicious_directory / "node"
        malicious_node.write_text(
            "#!/usr/bin/python3 -I\nraise SystemExit('MALICIOUS NODE')\n",
            encoding="utf-8",
        )
        malicious_node.chmod(0o700)
        bash_marker = self.root / "bash-env-executed"
        bash_environment = self.root / "bash-environment"
        bash_environment.write_text(f"/usr/bin/touch {bash_marker}\n", encoding="utf-8")
        node_marker = self.root / "node-options-executed"
        node_preload = self.root / "node-preload.js"
        node_preload.write_text(
            f"require('fs').writeFileSync({str(node_marker)!r}, 'executed');\n",
            encoding="utf-8",
        )
        malicious_modules = self.root / "malicious-node-path"
        malicious_modules.mkdir(mode=0o700)
        injected_environment = {
            "BASH_ENV": str(bash_environment),
            "NODE_OPTIONS": f"--require={node_preload}",
            "NODE_PATH": str(malicious_modules),
            "OPEN_NOTEBOOK_PASSWORD": "test-only-placeholder",
        }
        before = self.snapshot_tree(fake_home)
        payload = b"x" * 1048576

        start = self.run_wrapper(
            "session-start.sh",
            fake_home,
            payload,
            path_prefix=malicious_directory,
            extra_environment=injected_environment,
        )
        self.assertEqual(start.returncode, 0, start.stderr.decode())
        start_report = json.loads(start.stdout.decode().removeprefix("trusted-pj "))
        self.assertEqual(start_report["argv"], ["notebook", "hook", "session-start"])
        self.assertEqual(start_report["bytes"], 1048576)
        identity = pwd.getpwuid(os.getuid())
        self.assertEqual(
            start_report["env"],
            {
                "HOME": str(fake_home),
                "USER": identity.pw_name,
                "LOGNAME": identity.pw_name,
                "PATH": "/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "BASH_ENV": None,
                "NODE_OPTIONS": None,
                "NODE_PATH": None,
                "authPresent": True,
            },
        )
        self.assertNotIn(b"MALICIOUS", start.stdout + start.stderr)
        self.assertFalse(bash_marker.exists())
        self.assertFalse(node_marker.exists())
        self.assertFalse((self.root / "attacker-controlled-home").exists())
        self.assertEqual(self.snapshot_tree(fake_home), before)

        end = self.run_wrapper(
            "session-end.sh",
            fake_home,
            payload,
            path_prefix=malicious_directory,
            extra_environment=injected_environment,
        )
        self.assertEqual(end.returncode, 0, end.stderr.decode())
        end_report = json.loads(end.stdout.decode().removeprefix("trusted-pj "))
        self.assertEqual(end_report["argv"], ["notebook", "hook", "session-close"])
        self.assertEqual(end_report["bytes"], 1048576)
        self.assertEqual(end_report["env"], start_report["env"])
        self.assertNotIn(b"MALICIOUS", end.stdout + end.stderr)
        self.assertFalse(bash_marker.exists())
        self.assertFalse(node_marker.exists())
        self.assertEqual(self.snapshot_tree(fake_home), before)

        oversize_payload = b"x" * (1048576 + 8192)
        for wrapper in ("session-start.sh", "session-end.sh"):
            with self.subTest(wrapper=wrapper):
                oversize = self.run_wrapper(
                    wrapper,
                    fake_home,
                    oversize_payload,
                    path_prefix=malicious_directory,
                    extra_environment=injected_environment,
                )
                self.assertEqual(oversize.returncode, 0)
                self.assertEqual(oversize.stdout, b"")
                self.assertIn(b"payload exceeds 1048576 bytes", oversize.stderr)
                self.assertFalse(bash_marker.exists())
                self.assertFalse(node_marker.exists())
                self.assertEqual(self.snapshot_tree(fake_home), before)

    def test_wrappers_fail_open_without_creating_state(self) -> None:
        missing_home = self.root / "missing-pj-home"
        missing_home.mkdir(mode=0o700)
        before_missing = self.snapshot_tree(missing_home)
        skipped = self.run_wrapper(
            "session-start.sh",
            missing_home,
            b'{"disabled":true}',
        )
        self.assertEqual(skipped.returncode, 0)
        self.assertIn(b"skipped; trusted path is unavailable", skipped.stderr)
        self.assertEqual(self.snapshot_tree(missing_home), before_missing)

        fake_home, binary = self.make_fake_pj(name="failed-home", exit_code=42)
        before_failure = self.snapshot_tree(fake_home)
        failed = self.run_wrapper(
            "session-end.sh",
            fake_home,
            b'{"capture":false}',
        )
        self.assertEqual(failed.returncode, 0)
        self.assertIn(b"failed open", failed.stderr)
        self.assertEqual(self.snapshot_tree(fake_home), before_failure)

        binary.chmod(0o772)
        before_unsafe = self.snapshot_tree(fake_home)
        unsafe = self.run_wrapper(
            "session-start.sh",
            fake_home,
            b"ignored",
        )
        self.assertEqual(unsafe.returncode, 0)
        self.assertIn(b"permissions are unsafe", unsafe.stderr)
        self.assertNotIn(b"trusted-pj", unsafe.stdout)
        self.assertEqual(self.snapshot_tree(fake_home), before_unsafe)

        timeout_home, _ = self.make_fake_pj(name="timeout-home", hang=True)
        before_timeout = self.snapshot_tree(timeout_home)
        started = time.monotonic()
        timed_out = self.run_wrapper("session-end.sh", timeout_home, b'{"policy":"disabled"}')
        elapsed = time.monotonic() - started
        self.assertEqual(timed_out.returncode, 0)
        self.assertIn(b"timed out", timed_out.stderr)
        self.assertLess(elapsed, 2.0)
        self.assertEqual(self.snapshot_tree(timeout_home), before_timeout)

    def test_render_is_deterministic_and_second_render_changes_zero_bytes(self) -> None:
        rendered = self.root / "generated.json"
        first = self.run_projector(
            "render", "--master", str(MASTER_PATH), "--fragment", str(rendered)
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        first_bytes = rendered.read_bytes()
        self.assertEqual(first_bytes, FRAGMENT_PATH.read_bytes())
        first_stat = rendered.stat()

        second = self.run_projector(
            "render", "--master", str(MASTER_PATH), "--fragment", str(rendered)
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("up to date", second.stdout)
        self.assertEqual(rendered.read_bytes(), first_bytes)
        self.assertEqual(rendered.stat().st_ino, first_stat.st_ino)

    def test_check_is_pure_and_reports_all_required_finding_kinds(self) -> None:
        stale = self.canonical_hook("SessionStart")
        stale["timeout"] = 9
        value = {
            "theme": "dark",
            "hooks": {
                "SessionStart": [
                    {"hooks": [stale, self.canonical_hook("SessionStart")]},
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": OWNER_PREFIX
                                + '"$HOME/.agents/skills/project-notebook/hooks/unknown.sh"',
                                "timeout": 1,
                            }
                        ]
                    },
                ],
                "SessionEnd": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": START_COMMAND,
                                "timeout": 3,
                            }
                        ]
                    }
                ],
                "Stop": [{"hooks": [{"type": "command", "command": "foreign-stop"}]}],
            },
        }
        before = self.write_json(value, compact=True)
        result = self.run_projector(
            "check",
            "--master",
            str(MASTER_PATH),
            "--fragment",
            str(FRAGMENT_PATH),
            "--target",
            str(self.target),
            "--json",
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        kinds = {finding["kind"] for finding in report["findings"]}
        self.assertTrue({"missing", "duplicate", "stale", "foreign-conflict"} <= kinds)
        self.assertEqual(self.target.read_bytes(), before)
        self.assertFalse(self.state_home.exists(), "pure check created recovery state")

    def test_install_preserves_foreign_objects_order_and_is_byte_idempotent(self) -> None:
        stale = self.canonical_hook("SessionStart")
        stale["timeout"] = 11
        stale["owned_extra"] = "discard"
        stop = [{"matcher": "foreign", "hooks": [{"type": "command", "command": "foreign-stop"}]}]
        value = {
            "theme": "dark",
            "foreign_top": {"nested": [1, 2, 3]},
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "startup",
                        "condition": {"mode": "interactive"},
                        "hooks": [
                            {"type": "command", "command": "foreign-before", "timeout": 7},
                            stale,
                            {"type": "command", "command": "foreign-after", "extra": True},
                        ],
                        "group_extra": "preserve",
                    },
                    {"hooks": [self.canonical_hook("SessionStart")]},
                    {
                        "matcher": "preserve-empty-group",
                        "hooks": [self.canonical_hook("SessionStart")],
                        "extra": {"preserve": True},
                    },
                    {
                        "label": "tail",
                        "hooks": [{"type": "command", "command": "foreign-tail"}],
                    },
                ],
                "Stop": stop,
                "Notification": [{"hooks": [{"type": "command", "command": "foreign-notify"}]}],
            },
        }
        before = self.write_json(value, compact=True)

        first = self.run_projector(*self.mutation_arguments("install"))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("changed", first.stdout)
        installed = json.loads(self.target.read_text())

        self.assertEqual(installed["theme"], value["theme"])
        self.assertEqual(installed["foreign_top"], value["foreign_top"])
        self.assertEqual(installed["hooks"]["Stop"], stop)
        self.assertEqual(installed["hooks"]["Notification"], value["hooks"]["Notification"])
        groups = installed["hooks"]["SessionStart"]
        self.assertEqual(
            [group.get("matcher") for group in groups], ["startup", "preserve-empty-group", None]
        )
        self.assertEqual(groups[0]["condition"], {"mode": "interactive"})
        self.assertEqual(groups[0]["group_extra"], "preserve")
        self.assertEqual(groups[0]["hooks"][0], value["hooks"]["SessionStart"][0]["hooks"][0])
        self.assertEqual(groups[0]["hooks"][1], self.canonical_hook("SessionStart"))
        self.assertEqual(groups[0]["hooks"][2], value["hooks"]["SessionStart"][0]["hooks"][2])
        self.assertEqual(groups[1]["hooks"], [])
        self.assertEqual(groups[1]["extra"], {"preserve": True})
        self.assertEqual(groups[2]["label"], "tail")
        self.assertEqual(installed["hooks"]["SessionEnd"], self.master["hooks"]["SessionEnd"])

        snapshot = (
            self.state_home
            / "pjangler"
            / "notebook"
            / "v1"
            / "hook-install"
            / "snapshots"
            / f"{hashlib.sha256(before).hexdigest()}.json"
        )
        self.assertEqual(snapshot.read_bytes(), before)
        self.assertEqual(stat.S_IMODE(snapshot.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o600)
        first_bytes = self.target.read_bytes()
        first_inode = self.target.stat().st_ino
        snapshots_before = sorted(snapshot.parent.iterdir())

        second = self.run_projector(*self.mutation_arguments("install"))
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("up to date", second.stdout)
        self.assertEqual(self.target.read_bytes(), first_bytes)
        self.assertEqual(self.target.stat().st_ino, first_inode)
        self.assertEqual(sorted(snapshot.parent.iterdir()), snapshots_before)

        clean = self.run_projector(
            "check",
            "--master",
            str(MASTER_PATH),
            "--fragment",
            str(FRAGMENT_PATH),
            "--target",
            str(self.target),
        )
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)

    def test_install_rereads_target_after_acquiring_lock(self) -> None:
        self.write_json({"foreign": "preflight"})
        late_value = {"foreign": "changed-between-preflight-and-lock", "late": [1, 2]}
        original_read_target = PROJECTOR._read_target
        original_read_target_at = PROJECTOR._read_target_at
        path_calls = 0
        descriptor_calls = 0

        def mutate_after_preflight(path: Path):
            nonlocal path_calls
            result = original_read_target(path)
            if path == self.target:
                path_calls += 1
                if path_calls == 1:
                    self.target.write_text(json.dumps(late_value), encoding="utf-8")
            return result

        def count_descriptor_read(parent_fd: int, name: str):
            nonlocal descriptor_calls
            descriptor_calls += 1
            return original_read_target_at(parent_fd, name)

        with (
            mock.patch.object(PROJECTOR, "_read_target", side_effect=mutate_after_preflight),
            mock.patch.object(PROJECTOR, "_read_target_at", side_effect=count_descriptor_read),
        ):
            changed = PROJECTOR._mutate(
                "install", MASTER_PATH, FRAGMENT_PATH, self.target, self.state_home
            )
        self.assertTrue(changed)
        installed = json.loads(self.target.read_text())
        self.assertEqual(installed["foreign"], late_value["foreign"])
        self.assertEqual(installed["late"], late_value["late"])
        self.assertEqual(path_calls, 1)
        self.assertGreaterEqual(descriptor_calls, 4)

    def test_descriptor_relative_replace_survives_ancestor_symlink_swap(self) -> None:
        self.write_json({"foreign": "pinned-parent"}, compact=True)
        outside = self.root / "outside"
        outside.mkdir(mode=0o700)
        outside_target = outside / "settings.json"
        outside_bytes = b'{"outside":"must-not-change"}\n'
        outside_target.write_bytes(outside_bytes)
        pinned_parent = self.root / "pinned-claude-parent"
        original_replace = os.replace
        swapped = False

        def swap_parent_then_replace(
            source: str,
            destination: str,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
        ) -> None:
            nonlocal swapped
            if destination == self.target.name and not swapped:
                self.claude.rename(pinned_parent)
                self.claude.symlink_to(outside, target_is_directory=True)
                swapped = True
            original_replace(
                source,
                destination,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )

        with mock.patch.object(PROJECTOR.os, "replace", side_effect=swap_parent_then_replace):
            changed = PROJECTOR._mutate(
                "install", MASTER_PATH, FRAGMENT_PATH, self.target, self.state_home
            )

        self.assertTrue(changed)
        self.assertTrue(swapped)
        self.assertTrue(self.claude.is_symlink())
        self.assertEqual(outside_target.read_bytes(), outside_bytes)
        self.assertEqual(sorted(path.name for path in outside.iterdir()), ["settings.json"])
        installed = json.loads((pinned_parent / "settings.json").read_text())
        self.assertEqual(installed["foreign"], "pinned-parent")
        self.assertEqual(installed["hooks"], self.master["hooks"])
        self.assertEqual(
            [path.name for path in pinned_parent.iterdir() if path.name.startswith(".")],
            [],
        )

    def test_uninstall_removes_only_recognized_same_event_hooks(self) -> None:
        unknown = {
            "type": "command",
            "command": OWNER_PREFIX + '"$HOME/.agents/skills/project-notebook/hooks/custom.sh"',
            "timeout": 5,
        }
        prefix_similar = {
            "type": "command",
            "command": f"echo {START_COMMAND}",
            "timeout": 5,
        }
        mismatched = {"type": "command", "command": END_COMMAND, "timeout": 1}
        value = {
            "hooks": {
                "SessionStart": [
                    {"hooks": [self.canonical_hook("SessionStart")]},
                    {
                        "matcher": "keep-container",
                        "hooks": [self.canonical_hook("SessionStart")],
                        "condition": "foreign-extra",
                    },
                    {"hooks": [unknown]},
                    {"hooks": [prefix_similar]},
                ],
                "SessionEnd": [{"hooks": [self.canonical_hook("SessionEnd")]}],
                "Stop": [{"matcher": "stop", "hooks": [mismatched]}],
            },
            "other": {"untouched": True},
        }
        self.write_json(value)
        first = self.run_projector(*self.mutation_arguments("uninstall"))
        self.assertEqual(first.returncode, 0, first.stderr)
        uninstalled = json.loads(self.target.read_text())
        self.assertNotIn("SessionEnd", uninstalled["hooks"])
        self.assertEqual(uninstalled["other"], value["other"])
        self.assertEqual(uninstalled["hooks"]["Stop"], value["hooks"]["Stop"])
        remaining = uninstalled["hooks"]["SessionStart"]
        self.assertEqual(remaining[0]["matcher"], "keep-container")
        self.assertEqual(remaining[0]["condition"], "foreign-extra")
        self.assertEqual(remaining[0]["hooks"], [])
        self.assertEqual(remaining[1]["hooks"], [unknown])
        self.assertEqual(remaining[2]["hooks"], [prefix_similar])

        before_second = self.target.read_bytes()
        inode = self.target.stat().st_ino
        second = self.run_projector(*self.mutation_arguments("uninstall"))
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.target.read_bytes(), before_second)
        self.assertEqual(self.target.stat().st_ino, inode)

    def test_invalid_or_symlink_target_is_rejected_before_state_mutation(self) -> None:
        invalid = b'{"hooks": '
        self.target.write_bytes(invalid)
        result = self.run_projector(*self.mutation_arguments("install"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.target.read_bytes(), invalid)
        self.assertFalse(self.state_home.exists())

        self.target.unlink()
        real_target = self.root / "real-settings.json"
        real_target.write_text("{}\n", encoding="utf-8")
        self.target.symlink_to(real_target)
        result = self.run_projector(*self.mutation_arguments("install"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(real_target.read_text(), "{}\n")
        self.assertFalse(self.state_home.exists())

    def test_explicit_null_hook_containers_are_bounded_validation_errors(self) -> None:
        cases = (
            {"theme": "dark", "hooks": None},
            {"hooks": {"SessionStart": [{"matcher": "x", "hooks": None}]}},
        )
        for index, value in enumerate(cases):
            with self.subTest(index=index):
                before = self.write_json(value, compact=True)
                state_home = self.root / f"null-state-{index}"
                result = self.run_projector(
                    "install",
                    "--master",
                    str(MASTER_PATH),
                    "--fragment",
                    str(FRAGMENT_PATH),
                    "--target",
                    str(self.target),
                    "--state-home",
                    str(state_home),
                )
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("must be", result.stderr)
                self.assertEqual(self.target.read_bytes(), before)
                self.assertFalse(state_home.exists())

    def test_all_projector_paths_reject_ancestor_symlinks_before_mutation(self) -> None:
        real_target_parent = self.root / "real-target-parent"
        real_target_parent.mkdir(mode=0o700)
        linked_target_parent = self.root / "linked-target-parent"
        linked_target_parent.symlink_to(real_target_parent, target_is_directory=True)
        linked_target = linked_target_parent / "missing-tail" / "settings.json"
        target_state = self.root / "target-symlink-state"
        target_result = self.run_projector(
            "install",
            "--master",
            str(MASTER_PATH),
            "--fragment",
            str(FRAGMENT_PATH),
            "--target",
            str(linked_target),
            "--state-home",
            str(target_state),
        )
        self.assertEqual(target_result.returncode, 2)
        self.assertNotIn("Traceback", target_result.stderr)
        self.assertFalse((real_target_parent / "missing-tail").exists())
        self.assertFalse(target_state.exists())

        self.write_json({"foreign": "preserve"}, compact=True)
        target_before = self.target.read_bytes()
        real_state = self.root / "real-state"
        real_state.mkdir(mode=0o700)
        linked_state = self.root / "linked-state"
        linked_state.symlink_to(real_state, target_is_directory=True)
        state_result = self.run_projector(
            "install",
            "--master",
            str(MASTER_PATH),
            "--fragment",
            str(FRAGMENT_PATH),
            "--target",
            str(self.target),
            "--state-home",
            str(linked_state / "missing-tail"),
        )
        self.assertEqual(state_result.returncode, 2)
        self.assertNotIn("Traceback", state_result.stderr)
        self.assertEqual(self.target.read_bytes(), target_before)
        self.assertEqual(list(real_state.iterdir()), [])

        linked_assets = self.root / "linked-assets"
        linked_assets.symlink_to(SKILL_ROOT / "hooks", target_is_directory=True)
        fragment_state = self.root / "fragment-symlink-state"
        fragment_result = self.run_projector(
            "install",
            "--master",
            str(MASTER_PATH),
            "--fragment",
            str(linked_assets / "claude.settings.json"),
            "--target",
            str(self.target),
            "--state-home",
            str(fragment_state),
        )
        self.assertEqual(fragment_result.returncode, 2)
        self.assertNotIn("Traceback", fragment_result.stderr)
        self.assertEqual(self.target.read_bytes(), target_before)
        self.assertFalse(fragment_state.exists())

        def make_hook_install(state_home: Path) -> Path:
            current = state_home
            current.mkdir(mode=0o700)
            for name in ("pjangler", "notebook", "v1", "hook-install"):
                current = current / name
                current.mkdir(mode=0o700)
            return current

        external_lock = self.root / "external-lock"
        external_lock.write_text("foreign", encoding="utf-8")
        lock_state = self.root / "lock-symlink-state"
        lock_install = make_hook_install(lock_state)
        (lock_install / "snapshots").mkdir(mode=0o700)
        (lock_install / "lock").symlink_to(external_lock)
        lock_result = self.run_projector(
            "install",
            "--master",
            str(MASTER_PATH),
            "--fragment",
            str(FRAGMENT_PATH),
            "--target",
            str(self.target),
            "--state-home",
            str(lock_state),
        )
        self.assertEqual(lock_result.returncode, 2)
        self.assertNotIn("Traceback", lock_result.stderr)
        self.assertEqual(external_lock.read_text(), "foreign")
        self.assertEqual(self.target.read_bytes(), target_before)

        snapshot_state = self.root / "snapshot-symlink-state"
        snapshot_install = make_hook_install(snapshot_state)
        external_snapshots = self.root / "external-snapshots"
        external_snapshots.mkdir(mode=0o700)
        (snapshot_install / "snapshots").symlink_to(external_snapshots, target_is_directory=True)
        snapshot_result = self.run_projector(
            "install",
            "--master",
            str(MASTER_PATH),
            "--fragment",
            str(FRAGMENT_PATH),
            "--target",
            str(self.target),
            "--state-home",
            str(snapshot_state),
        )
        self.assertEqual(snapshot_result.returncode, 2)
        self.assertNotIn("Traceback", snapshot_result.stderr)
        self.assertFalse((snapshot_install / "lock").exists())
        self.assertEqual(list(external_snapshots.iterdir()), [])
        self.assertEqual(self.target.read_bytes(), target_before)

    def test_absent_target_gets_recoverable_empty_object_snapshot(self) -> None:
        self.claude.rmdir()
        result = self.run_projector(*self.mutation_arguments("install"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.claude.is_dir())
        self.assertEqual(stat.S_IMODE(self.claude.stat().st_mode), 0o700)
        empty_digest = hashlib.sha256(b"{}\n").hexdigest()
        snapshot = (
            self.state_home
            / "pjangler"
            / "notebook"
            / "v1"
            / "hook-install"
            / "snapshots"
            / f"{empty_digest}.json"
        )
        self.assertEqual(snapshot.read_bytes(), b"{}\n")
        self.assertEqual(json.loads(self.target.read_text()), self.master)


if __name__ == "__main__":
    unittest.main()
