from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNTIME = SKILL_ROOT / "scripts" / "hook-runtime.py"
FANOUT = SKILL_ROOT / "scripts" / "hooks-fanout.py"
DIRTY = ".codegraph/codegraph-voyage.dirty"


def run_runtime(role: str, cwd: Path, payload: dict, env: dict[str, str] | None = None):
    environment = os.environ.copy()
    environment.pop("CODEGRAPH_VOYAGE_HOOK_PROVIDER", None)
    environment.pop("VOYAGE_API_KEY", None)
    if env:
        environment.update(env)
    return subprocess.run(
        [sys.executable, str(RUNTIME), role], cwd=cwd, input=json.dumps(payload),
        text=True, capture_output=True, env=environment, check=False,
    )


def make_project(root: Path, *, exit_code: int = 0) -> Path:
    (root / ".codegraph").mkdir(parents=True)
    (root / ".codegraph/codegraph.db").write_bytes(b"db")
    package = root / "tools/codegraph_voyage"
    package.mkdir(parents=True)
    (root / "tools/__init__.py").write_text("")
    (package / "__init__.py").write_text("")
    (package / "__main__.py").write_text(
        "import json, os, pathlib, sys\n"
        "path = pathlib.Path('.codegraph/mock-calls.jsonl')\n"
        "with path.open('a') as f: f.write(json.dumps({'args': sys.argv[1:], 'key_in_env': 'VOYAGE_API_KEY' in os.environ}) + '\\n')\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    return root


def calls(root: Path) -> list[dict]:
    path = root / ".codegraph/mock-calls.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def load_fanout():
    spec = importlib.util.spec_from_file_location("codegraph_hooks_fanout", FANOUT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_noop_outside_codegraph_project(tmp_path: Path):
    result = run_runtime("post_tool", tmp_path, {"cwd": str(tmp_path), "tool_name": "write_file"})
    assert result.returncode == 0
    assert list(tmp_path.iterdir()) == []


def test_mutation_marks_dirty_and_read_only_does_not(tmp_path: Path):
    root = make_project(tmp_path)
    result = run_runtime("post_tool", root, {"cwd": str(root), "toolName": "functions.write_file"})
    assert result.returncode == 0
    assert (root / DIRTY).is_file()
    (root / DIRTY).unlink()
    nested = run_runtime(
        "post_tool", root, {"context": {"projectRoot": str(root)}, "tool": {"name": "apply_patch"}}
    )
    assert nested.returncode == 0
    assert (root / DIRTY).is_file()
    (root / DIRTY).unlink()
    result = run_runtime("post_tool", root, {"project_path": str(root), "tool": {"name": "read_file"}})
    assert result.returncode == 0
    assert not (root / DIRTY).exists()


def test_session_end_coalesces_and_clears_only_after_success(tmp_path: Path):
    root = make_project(tmp_path)
    (root / DIRTY).write_text("dirty")
    first = run_runtime("session_end", root, {"cwd": str(root)})
    second = run_runtime("session_end", root, {"cwd": str(root)})
    assert first.returncode == second.returncode == 0
    assert not (root / DIRTY).exists()
    assert [call["args"] for call in calls(root)] == [["index", "--provider", "fake"]]


def test_provider_defaults_fake_and_voyage_needs_explicit_opt_in(tmp_path: Path):
    root = make_project(tmp_path)
    (root / DIRTY).write_text("dirty")
    run_runtime("session_end", root, {"cwd": str(root)})
    assert calls(root)[-1] == {"args": ["index", "--provider", "fake"], "key_in_env": False}

    (root / DIRTY).write_text("dirty")
    (root / ".agents").mkdir()
    (root / ".agents/local.json").write_text(
        json.dumps({"codegraph_voyage": {"hook_provider": "voyage"}})
    )
    secret = "hook-" + "secret-" + "value"
    run_runtime("session_end", root, {"cwd": str(root)}, {"VOYAGE_API_KEY": secret})
    assert calls(root)[-1] == {"args": ["index", "--provider", "voyage"], "key_in_env": True}
    assert all(secret not in " ".join(call["args"]) for call in calls(root))
    all_skill_bytes = b"".join(
        path.read_bytes() for path in SKILL_ROOT.rglob("*") if path.is_file() and "__pycache__" not in path.parts
    )
    assert secret.encode() not in all_skill_bytes


def test_failed_index_retains_dirty_and_exits_success(tmp_path: Path):
    root = make_project(tmp_path, exit_code=7)
    (root / DIRTY).write_text("dirty")
    result = run_runtime("session_end", root, {"cwd": str(root)})
    assert result.returncode == 0
    assert (root / DIRTY).exists()
    assert (root / ".codegraph/codegraph-voyage-hooks.log").is_file()


def test_render_deterministic_and_check_detects_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = load_fanout()
    generated = tmp_path / "generated"
    monkeypatch.setattr(module, "GENERATED", generated)
    assert module.render() == 0
    first = {path.name: path.read_bytes() for path in generated.iterdir()}
    stats = {path.name: path.stat().st_ino for path in generated.iterdir()}
    assert module.render() == 0
    assert first == {path.name: path.read_bytes() for path in generated.iterdir()}
    assert stats == {path.name: path.stat().st_ino for path in generated.iterdir()}
    assert module.check(None) == 0
    target = generated / "claude.settings.json"
    target.write_text("{}\n")
    assert module.check(None) == 1


def test_install_uninstall_preserve_sibling_hooks(tmp_path: Path):
    foreign = {"type": "command", "command": "foreign-command", "timeout": 9}
    claude = tmp_path / ".claude/settings.json"
    claude.parent.mkdir()
    claude.write_text(json.dumps({"theme": "dark", "hooks": {"Stop": [{"hooks": [foreign]}]}}))
    hermes = tmp_path / ".hermes/hooks.json"
    hermes.parent.mkdir()
    hermes.write_text(json.dumps({"hooks": {"on_session_end": [{"command": "foreign-hermes"}]}}))

    install = subprocess.run(
        [sys.executable, str(FANOUT), "install", "--project-root", str(tmp_path)],
        text=True, capture_output=True, check=False,
    )
    assert install.returncode == 0, install.stderr
    installed = json.loads(claude.read_text())
    assert installed["theme"] == "dark"
    assert foreign in installed["hooks"]["Stop"][0]["hooks"]
    assert claude.with_name("settings.json.bak").exists()
    backup_mtime = claude.with_name("settings.json.bak").stat().st_mtime_ns
    again = subprocess.run(
        [sys.executable, str(FANOUT), "install", "--project-root", str(tmp_path)],
        text=True, capture_output=True, check=False,
    )
    assert again.returncode == 0 and "up to date" in again.stdout
    assert claude.with_name("settings.json.bak").stat().st_mtime_ns == backup_mtime

    uninstall = subprocess.run(
        [sys.executable, str(FANOUT), "uninstall", "--project-root", str(tmp_path)],
        text=True, capture_output=True, check=False,
    )
    assert uninstall.returncode == 0, uninstall.stderr
    final = json.loads(claude.read_text())
    assert final["theme"] == "dark"
    assert final["hooks"]["Stop"][0]["hooks"] == [foreign]
    assert json.loads(hermes.read_text())["hooks"]["on_session_end"] == [{"command": "foreign-hermes"}]


def test_unsafe_symlink_causes_zero_mutation(tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel").write_text("unchanged")
    (tmp_path / ".claude").symlink_to(outside, target_is_directory=True)
    before = {str(path.relative_to(tmp_path)): (path.read_bytes() if path.is_file() else None)
              for path in tmp_path.rglob("*") if not path.is_symlink()}
    result = subprocess.run(
        [sys.executable, str(FANOUT), "install", "--project-root", str(tmp_path)],
        text=True, capture_output=True, check=False,
    )
    after = {str(path.relative_to(tmp_path)): (path.read_bytes() if path.is_file() else None)
             for path in tmp_path.rglob("*") if not path.is_symlink()}
    assert result.returncode == 2
    assert before == after
    assert not (tmp_path / ".codex").exists()
    assert not (tmp_path / ".hermes").exists()
