#!/usr/bin/env python3
"""
agent_efficiency.py

Typer CLI for managing a layered multi-agent coding stack:
Claude Code, OpenAI Codex, Kimi Code CLI, and Nous Hermes Agent.

Principles:
- dry-run by default
- cheap scouts for exploration/log/docs work
- premium agents for decisions/final synthesis
- minimal MCP surface area
- usage metrics drive iteration
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

try:
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()

HOME = Path.home()
DEFAULT_STATE_DIR = HOME / ".agent-token-efficiency"
DEFAULT_REPORT_DIR = DEFAULT_STATE_DIR / "reports"
SKILL_ROOT = Path(__file__).resolve().parents[1]

SUPPORTED_AGENTS = ["claude", "codex", "kimi", "hermes"]


@dataclass
class CommandResult:
    command: list[str]
    cwd: str | None
    returncode: int
    stdout: str
    stderr: str


@dataclass
class AgentPathSet:
    name: str
    executable: str | None
    home: Path
    config_files: list[Path]
    agents_dir: Path | None = None
    skills_dir: Path | None = None
    mcp_file: Path | None = None


@dataclass
class ProviderQuota:
    name: str
    model: str
    enabled: bool
    rpm: float | None = None
    daily_requests: int | None = None
    tpm: int | None = None
    notes: str = ""
    source_url: str = ""
    cost_tier: str = "unknown"
    quality_tier: str = "unknown"


def now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def mkdir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return default


def write_text(path: Path, text: str, apply: bool = False) -> None:
    if not apply:
        console.print(f"[yellow]dry-run[/yellow] would write {path}")
        preview = text[:1800]
        console.print(Syntax(preview, "markdown" if path.suffix.lower() in {'.md'} else "text"))
        if len(text) > len(preview):
            console.print("[dim]...preview truncated...[/dim]")
        return
    mkdir(path.parent)
    path.write_text(text, encoding="utf-8")
    console.print(f"[green]wrote[/green] {path}")


def copy_path(src: Path, dst: Path, apply: bool = False) -> None:
    if not src.exists():
        raise typer.BadParameter(f"source does not exist: {src}")
    if not apply:
        console.print(f"[yellow]dry-run[/yellow] would copy {src} -> {dst}")
        return
    mkdir(dst.parent)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    console.print(f"[green]copied[/green] {src} -> {dst}")


def run_cmd(
    command: list[str],
    cwd: Path | None = None,
    timeout: int = 30,
    allow_fail: bool = True,
) -> CommandResult:
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        result = CommandResult(
            command=command,
            cwd=str(cwd) if cwd else None,
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )
        if proc.returncode != 0 and not allow_fail:
            raise RuntimeError(f"command failed: {' '.join(command)}\n{proc.stderr}")
        return result
    except FileNotFoundError as exc:
        return CommandResult(command, str(cwd) if cwd else None, 127, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        return CommandResult(command, str(cwd) if cwd else None, 124, exc.stdout or "", exc.stderr or "timeout")


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def agent_paths() -> dict[str, AgentPathSet]:
    return {
        "claude": AgentPathSet(
            name="claude",
            executable=which("claude"),
            home=HOME / ".claude",
            config_files=[HOME / ".claude" / "settings.json", HOME / ".claude" / "CLAUDE.md"],
            agents_dir=HOME / ".claude" / "agents",
            skills_dir=HOME / ".claude" / "skills",
        ),
        "codex": AgentPathSet(
            name="codex",
            executable=which("codex"),
            home=HOME / ".codex",
            config_files=[HOME / ".codex" / "config.toml", HOME / ".codex" / "AGENTS.md"],
            agents_dir=HOME / ".codex" / "agents",
            skills_dir=HOME / ".codex" / "skills",
        ),
        "kimi": AgentPathSet(
            name="kimi",
            executable=which("kimi"),
            home=HOME / ".kimi",
            config_files=[HOME / ".kimi" / "config.toml", HOME / ".kimi" / "mcp.json"],
            agents_dir=HOME / ".kimi" / "agents",
            skills_dir=HOME / ".kimi" / "skills",
            mcp_file=HOME / ".kimi" / "mcp.json",
        ),
        "hermes": AgentPathSet(
            name="hermes",
            executable=which("hermes"),
            home=HOME / ".hermes",
            config_files=[HOME / ".hermes" / "config.yaml", HOME / ".hermes" / ".env"],
            agents_dir=None,
            skills_dir=HOME / ".hermes" / "skills",
        ),
    }


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"expected YAML mapping in {path}")
    return data


def save_yaml(path: Path, data: dict[str, Any], apply: bool = False) -> None:
    text = yaml.safe_dump(data, sort_keys=False, width=120)
    write_text(path, text, apply=apply)


def merge_markdown(path: Path, section_title: str, body: str, apply: bool = False) -> None:
    existing = read_text(path)
    marker = f"<!-- agent-token-efficiency:{section_title} -->"
    block = f"\n{marker}\n## {section_title}\n\n{body.strip()}\n"
    if marker in existing:
        pattern = re.compile(rf"\n?{re.escape(marker)}\n## {re.escape(section_title)}\n.*?(?=\n<!-- agent-token-efficiency:|\Z)", re.S)
        updated = pattern.sub(block, existing)
    else:
        updated = existing.rstrip() + "\n" + block if existing.strip() else block.lstrip()
    write_text(path, updated, apply=apply)


def append_toml_section(path: Path, section_name: str, toml_body: str, apply: bool = False) -> None:
    existing = read_text(path)
    marker = f"# agent-token-efficiency:{section_name}"
    block = f"\n{marker}\n{toml_body.strip()}\n"
    if marker in existing:
        pattern = re.compile(rf"\n?{re.escape(marker)}\n.*?(?=\n# agent-token-efficiency:|\Z)", re.S)
        updated = pattern.sub(block, existing)
    else:
        updated = existing.rstrip() + "\n" + block if existing.strip() else block.lstrip()
    write_text(path, updated, apply=apply)


def command_exists_table() -> Table:
    table = Table(title="Agent CLI availability")
    table.add_column("Agent")
    table.add_column("Executable")
    table.add_column("Version probe")
    for name, paths in agent_paths().items():
        exe = paths.executable or "missing"
        version = "not found"
        if paths.executable:
            result = run_cmd([paths.executable, "--version"], timeout=10)
            version = result.stdout or result.stderr or f"exit {result.returncode}"
        table.add_row(name, exe, version[:120])
    return table


@app.command()
def doctor(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show config files and path status."),
) -> None:
    """Check installed agent CLIs, expected config paths, and helper tools."""
    console.print(command_exists_table())

    helpers = ["npx", "node", "npm", "rg", "git", "ccusage"]
    table = Table(title="Helper tool availability")
    table.add_column("Tool")
    table.add_column("Path")
    for h in helpers:
        table.add_row(h, which(h) or "missing")
    console.print(table)

    if verbose:
        path_table = Table(title="Config paths")
        path_table.add_column("Agent")
        path_table.add_column("Path")
        path_table.add_column("Exists")
        for name, paths in agent_paths().items():
            for p in paths.config_files:
                path_table.add_row(name, str(p), "yes" if p.exists() else "no")
            for p in [paths.agents_dir, paths.skills_dir, paths.mcp_file]:
                if p:
                    path_table.add_row(name, str(p), "yes" if p.exists() else "no")
        console.print(path_table)


def inspect_unknown(target: Path, docs_url: str | None = None) -> dict[str, Any]:
    target = target.expanduser().resolve()
    is_repo = (target / ".git").exists() if target.is_dir() else False
    executable = str(target) if target.is_file() and os.access(target, os.X_OK) else None
    name = target.name

    data: dict[str, Any] = {
        "target": str(target),
        "name": name,
        "is_dir": target.is_dir(),
        "is_file": target.is_file(),
        "is_repo": is_repo,
        "docs_url": docs_url,
        "detected_files": [],
        "commands": [],
        "capability_hints": [],
        "docs_hints": [],
    }

    if target.is_dir():
        patterns = [
            "README*", "docs/**", "package.json", "pyproject.toml", "Cargo.toml",
            "*.toml", "*.yaml", "*.yml", "*.json", "AGENTS.md", "CLAUDE.md",
            ".*rc", "config/**", "settings/**",
        ]
        files: list[str] = []
        for pat in patterns:
            files.extend([str(p.relative_to(target)) for p in target.glob(pat) if p.is_file()][:50])
        data["detected_files"] = sorted(set(files))[:200]

        if is_repo:
            remote = run_cmd(["git", "config", "--get", "remote.origin.url"], cwd=target)
            if remote.stdout:
                data["docs_hints"].append(f"git remote: {remote.stdout}")

        for candidate in ["README.md", "README", "docs/index.md", "docs/configuration.md"]:
            p = target / candidate
            if p.exists():
                snippet = read_text(p)[:4000]
                data["docs_hints"].append(f"{candidate}:\n{snippet}")

    if executable:
        for args in [["--version"], ["version"], ["--help"], ["help"], ["config", "--help"], ["mcp", "--help"], ["agents", "--help"], ["skills", "--help"]]:
            res = run_cmd([executable, *args], timeout=15)
            data["commands"].append(asdict(res))
    elif target.is_dir():
        for bin_name in [name, "bin/" + name, "dist/" + name]:
            p = target / bin_name
            if p.exists() and os.access(p, os.X_OK):
                for args in [["--version"], ["--help"], ["mcp", "--help"], ["skills", "--help"]]:
                    res = run_cmd([str(p), *args], timeout=15)
                    data["commands"].append(asdict(res))

    corpus = "\n".join(
        [json.dumps(data.get("detected_files", [])), *data.get("docs_hints", [])]
        + [c.get("stdout", "") + c.get("stderr", "") for c in data.get("commands", [])]
    ).lower()

    hints = []
    for label, needles in {
        "mcp_tools": ["mcp", "model context protocol", "tools"],
        "skills": ["skill", "skills", "prompt templates"],
        "custom_agents": ["agent", "subagent", "worker"],
        "profiles": ["profile", "profiles", "model", "reasoning", "thinking"],
        "config_file": ["config", "settings", "toml", "yaml", "json"],
        "compaction": ["compact", "summar", "context", "truncate"],
        "approval_sandbox": ["approval", "sandbox", "permission", "yolo", "auto-approve"],
        "usage_metrics": ["usage", "token", "cost", "quota", "rate limit"],
    }.items():
        if any(n in corpus for n in needles):
            hints.append(label)
    data["capability_hints"] = hints
    return data


def optimization_report(inspection: dict[str, Any]) -> str:
    name = inspection.get("name", "unknown-agent")
    hints = set(inspection.get("capability_hints", []))

    strategies = []
    if "custom_agents" in hints or "skills" in hints:
        strategies.append("Create cheap read-only scout, docs researcher, and log summarizer workers.")
    else:
        strategies.append("If native agents/skills are absent, emulate cheap workers with shell aliases and reusable prompt files.")

    if "mcp_tools" in hints:
        strategies.append("Install only Context7 plus one semantic code-search MCP. Keep all other MCPs disabled until a task needs them.")
    else:
        strategies.append("Prefer CLI-native docs/search commands or add an MCP bridge only if the agent supports external tools.")

    if "profiles" in hints:
        strategies.append("Add deep/cheap profiles: premium model/high reasoning for orchestration, cheap/minimal reasoning for scouting.")
    else:
        strategies.append("Add wrapper scripts/aliases for deep vs cheap modes if profiles are not supported.")

    if "compaction" in hints:
        strategies.append("Configure auto-compaction around 70–85% of context, and manual compact/clear when switching unrelated tasks.")
    else:
        strategies.append("Add prompt discipline: summarize logs and file scans before feeding them back to the premium agent.")

    if "approval_sandbox" in hints:
        strategies.append("Keep mutation approvals on-request; never enable global YOLO/AFK mode.")

    if "usage_metrics" not in hints:
        strategies.append("Add ccusage or wrapper-level token/cost logging because optimization without meters is cosplay.")

    raw = json.dumps(inspection, indent=2)[:12000]
    return f"""# Unknown Agent Token-Efficiency Report: {name}

Generated: {datetime.now(timezone.utc).isoformat()}

## Target

`{inspection.get('target')}`

Docs URL: {inspection.get('docs_url') or 'not provided'}

## Detected capability hints

{chr(10).join(f'- {h}' for h in inspection.get('capability_hints', [])) or '- none detected'}

## Strategy transfer map

The known supported stack has these reusable optimization layers:

| Layer | Claude | Codex | Kimi | Hermes | Unknown-agent transfer |
|---|---|---|---|---|---|
| Cheap explorer | Explore/Haiku subagent | read-only custom agent | explore / custom YAML agent | cheap auxiliary model | create scout worker or prompt wrapper |
| Current docs | Context7 MCP | Context7 MCP | Context7 MCP | web/model provider tools | install docs tool only if low overhead |
| Profiles | model/effort/session discipline | TOML profiles | config/default thinking | provider routing/fallback | deep vs cheap launch modes |
| Compaction | /compact, /clear | auto compact + /compact | loop control/context reserve | compression auxiliary | summarize before feeding main model |
| Usage metrics | ccusage | ccusage | ccusage if supported | ccusage/provider logs | add usage probe/wrapper |

## Recommended changes

{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(strategies))}

## Generic files to add if this is a repository

- `AGENTS.md` with token-discipline rules.
- `.agent-efficiency/strategy.md` with agent-specific findings.
- `.agent-efficiency/scout.prompt.md` for a cheap read-only scout.
- `.agent-efficiency/log-summarizer.prompt.md` for compressing logs.
- `.agent-efficiency/docs-researcher.prompt.md` for current docs.

## Raw inspection excerpt

```json
{raw}
```
"""


@app.command("optimize-unknown")
def optimize_unknown(
    target: Path = typer.Argument(..., help="Path to unsupported agent executable or repository."),
    docs_url: Optional[str] = typer.Option(None, "--docs-url", help="Optional docs URL for the unknown agent."),
    out: Path = typer.Option(DEFAULT_REPORT_DIR, "--out", help="Output directory for reports."),
    apply: bool = typer.Option(False, "--apply", help="Apply safe generic files when target is a repository."),
) -> None:
    """Research an unsupported agent and apply transferable token-saving strategies."""
    inspection = inspect_unknown(target, docs_url=docs_url)
    report = optimization_report(inspection)
    mkdir(out)
    report_path = out / f"unknown-{inspection.get('name','agent')}-{now_slug()}.md"
    write_text(report_path, report, apply=True)

    if apply and Path(inspection["target"]).is_dir():
        repo = Path(inspection["target"])
        agent_rules = read_text(SKILL_ROOT / "assets" / "templates" / "AGENTS.md")
        merge_markdown(repo / "AGENTS.md", "Agent Token Efficiency", agent_rules, apply=True)
        mkdir(repo / ".agent-efficiency")
        (repo / ".agent-efficiency" / "strategy.md").write_text(report, encoding="utf-8")
        for prompt in ["scout.prompt.md", "log-summarizer.prompt.md", "docs-researcher.prompt.md"]:
            src = SKILL_ROOT / "assets" / "templates" / prompt
            if src.exists():
                shutil.copy2(src, repo / ".agent-efficiency" / prompt)
        console.print(f"[green]applied generic optimization files to[/green] {repo}")
    elif not apply:
        console.print("[yellow]dry-run[/yellow] inspection only. Add --apply to write generic repo files.")

    console.print(f"[bold]Report:[/bold] {report_path}")


def load_mcp_definition(source: Path) -> dict[str, Any]:
    data = json.loads(read_text(source))
    if "name" not in data:
        raise typer.BadParameter("MCP definition must include name")
    return data


def codex_mcp_toml(mcp: dict[str, Any]) -> str:
    name = mcp["name"]
    command = mcp.get("command", "npx")
    args = mcp.get("args", [])
    enabled = bool(mcp.get("enabled_by_default", True))
    args_toml = ", ".join(json.dumps(a) for a in args)
    return f"""[mcp_servers.{name}]
command = {json.dumps(command)}
args = [{args_toml}]
enabled = {str(enabled).lower()}
"""


def kimi_mcp_json(existing: dict[str, Any], mcp: dict[str, Any]) -> dict[str, Any]:
    servers = existing.setdefault("mcpServers", {})
    name = mcp["name"]
    servers[name] = {
        "command": mcp.get("command", "npx"),
        "args": mcp.get("args", []),
    }
    if mcp.get("env"):
        servers[name]["env"] = mcp["env"]
    return existing


def apply_mcp(mcp: dict[str, Any], targets: list[str], apply: bool = False) -> None:
    paths = agent_paths()
    for target in targets:
        if target == "codex":
            append_toml_section(paths[target].home / "config.toml", f"mcp-{mcp['name']}", codex_mcp_toml(mcp), apply=apply)
        elif target == "kimi":
            existing = load_yaml(paths[target].mcp_file) if paths[target].mcp_file and paths[target].mcp_file.exists() else {}
            # mcp.json is JSON, but YAML parser can read JSON. Write JSON for Kimi.
            updated = kimi_mcp_json(existing, mcp)
            text = json.dumps(updated, indent=2) + "\n"
            write_text(paths[target].mcp_file or (paths[target].home / "mcp.json"), text, apply=apply)
        elif target == "claude":
            cmd = f"claude mcp add {mcp['name']} -- {mcp.get('command','npx')} {' '.join(mcp.get('args', []))}"
            marker_body = f"Recommended MCP install command:\n\n```bash\n{cmd}\n```"
            merge_markdown(paths[target].home / "CLAUDE.md", f"MCP {mcp['name']}", marker_body, apply=apply)
            if apply and paths[target].executable:
                console.print(f"[cyan]not auto-running Claude MCP command; review first:[/cyan] {cmd}")
        elif target == "hermes":
            body = f"""# MCP {mcp['name']}

Hermes MCP servers may be managed through `hermes tools` or config. Review this definition before enabling:

```json
{json.dumps(mcp, indent=2)}
```
"""
            write_text(paths[target].home / "mcp" / f"{mcp['name']}.md", body, apply=apply)


def normalize_targets(target: str) -> list[str]:
    if target == "all":
        return SUPPORTED_AGENTS
    parts = [p.strip().lower() for p in target.split(",") if p.strip()]
    unknown = [p for p in parts if p not in SUPPORTED_AGENTS]
    if unknown:
        raise typer.BadParameter(f"unknown targets: {unknown}. supported: {SUPPORTED_AGENTS}")
    return parts


@app.command("propagate-update")
def propagate_update(
    kind: Literal["mcp", "skill", "profile", "agent", "instruction", "config"] = typer.Option(..., "--kind"),
    name: str = typer.Option(..., "--name"),
    source: Path = typer.Option(..., "--source", exists=True, help="File or directory containing the update."),
    target: str = typer.Option("all", "--target", help="all or comma-separated agent names."),
    apply: bool = typer.Option(False, "--apply", help="Actually mutate files. Dry-run is default."),
) -> None:
    """Apply a new MCP/tool/skill/profile/agent/instruction/config update across supported CLIs."""
    targets = normalize_targets(target)
    paths = agent_paths()

    if kind == "mcp":
        mcp = load_mcp_definition(source)
        apply_mcp(mcp, targets, apply=apply)
        return

    if kind == "skill":
        for t in targets:
            skills_dir = paths[t].skills_dir
            if not skills_dir:
                console.print(f"[yellow]skip[/yellow] {t}: no known skills dir")
                continue
            dst = skills_dir / name
            copy_path(source, dst, apply=apply)
        return

    if kind == "agent":
        for t in targets:
            agents_dir = paths[t].agents_dir
            if not agents_dir:
                console.print(f"[yellow]skip[/yellow] {t}: no known agents dir")
                continue
            suffix = source.suffix or ".txt"
            dst = agents_dir / f"{name}{suffix}" if source.is_file() else agents_dir / name
            copy_path(source, dst, apply=apply)
        return

    if kind == "instruction":
        text = read_text(source)
        for t in targets:
            if t == "codex":
                merge_markdown(paths[t].home / "AGENTS.md", name, text, apply=apply)
            elif t == "claude":
                merge_markdown(paths[t].home / "CLAUDE.md", name, text, apply=apply)
            elif t == "kimi":
                merge_markdown(paths[t].home / "AGENTS.md", name, text, apply=apply)
            elif t == "hermes":
                merge_markdown(paths[t].home / "AGENTS.md", name, text, apply=apply)
        return

    if kind == "profile":
        for t in targets:
            if t == "codex":
                dst = paths[t].home / f"{name}.config.toml"
            elif t == "kimi":
                dst = paths[t].home / "profiles" / f"{name}.toml"
            elif t == "hermes":
                dst = paths[t].home / f"config.{name}.yaml"
            else:
                dst = paths[t].home / "profiles" / f"{name}.md"
            copy_path(source, dst, apply=apply)
        return

    if kind == "config":
        for t in targets:
            dst = paths[t].home / source.name
            copy_path(source, dst, apply=apply)
        return


def call_ccusage() -> dict[str, Any]:
    candidates = [
        ["ccusage", "daily", "--json"],
        ["ccusage", "blocks", "--json"],
        ["ccusage", "daily"],
    ]
    results = []
    for cmd in candidates:
        if not which(cmd[0]):
            continue
        res = run_cmd(cmd, timeout=30)
        results.append(asdict(res))
        if res.returncode == 0 and res.stdout:
            try:
                return {"json": json.loads(res.stdout), "raw_results": results}
            except Exception:
                return {"text": res.stdout, "raw_results": results}
    return {"error": "ccusage not found or produced no output", "raw_results": results}


def parse_providers(path: Path) -> list[ProviderQuota]:
    data = load_yaml(path)
    providers = []
    for item in data.get("providers", []):
        providers.append(ProviderQuota(**item))
    return providers


def fetch_provider_notes(providers: list[ProviderQuota], max_chars: int = 2500) -> dict[str, str]:
    notes: dict[str, str] = {}
    if requests is None:
        return {"error": "requests is not installed"}
    for p in providers:
        if not p.source_url:
            continue
        try:
            resp = requests.get(p.source_url, timeout=12, headers={"User-Agent": "agent-efficiency/0.1"})
            text = re.sub(r"\s+", " ", resp.text)
            notes[p.name] = text[:max_chars]
        except Exception as exc:
            notes[p.name] = f"fetch failed: {exc}"
    return notes


def calculate_rotation(
    providers: list[ProviderQuota], desired_rpm: float, desired_daily_requests: int
) -> dict[str, Any]:
    enabled = [p for p in providers if p.enabled]
    known_rpm = sum(p.rpm or 0 for p in enabled)
    known_daily = sum(p.daily_requests or 0 for p in enabled)
    daily_need_from_rpm = int(desired_rpm * 60 * 24)
    effective_daily_need = max(desired_daily_requests, daily_need_from_rpm)

    plan = []
    remaining = effective_daily_need
    for p in sorted(enabled, key=lambda x: ((x.cost_tier != "free"), -(x.daily_requests or 10**9), -(x.rpm or 0))):
        cap = p.daily_requests if p.daily_requests is not None else max(0, int((p.rpm or 0) * 60 * 24)) or None
        if cap is None:
            allocation = "unknown; use as overflow only until verified"
            allocated = 0
        else:
            allocated = min(remaining, cap)
            remaining -= allocated
            allocation = allocated
        interval = None
        if p.rpm:
            interval = round(60.0 / p.rpm, 2)
        plan.append({
            "provider": p.name,
            "model": p.model,
            "allocation_daily_requests": allocation,
            "rpm": p.rpm,
            "min_interval_seconds": interval,
            "notes": p.notes,
            "source_url": p.source_url,
        })

    return {
        "desired_rpm": desired_rpm,
        "desired_daily_requests": desired_daily_requests,
        "effective_daily_need": effective_daily_need,
        "known_total_rpm": known_rpm,
        "known_total_daily_requests": known_daily,
        "rpm_ok": known_rpm >= desired_rpm if known_rpm else False,
        "daily_ok": known_daily >= effective_daily_need if known_daily else False,
        "uncovered_daily_requests": max(0, remaining),
        "plan": plan,
        "warnings": [
            "Do not use account multiplication or throwaway accounts to evade provider limits.",
            "Unknown quotas must be manually verified before inclusion in continuous rotation.",
            "Free provider limits can be best-effort and may fail during peak global demand.",
        ],
    }


def usage_improvement_notes(usage: dict[str, Any], providers: list[ProviderQuota], rotation: dict[str, Any]) -> str:
    raw = json.dumps(usage, indent=2)[:8000]
    provider_lines = []
    for p in providers:
        provider_lines.append(f"- {p.name} / {p.model}: enabled={p.enabled}, rpm={p.rpm}, daily={p.daily_requests}, tier={p.cost_tier}, notes={p.notes}")

    suggestions = [
        "Route repo exploration, call-site mapping, docs lookup, and log summarization to cheap scout agents before invoking premium models.",
        "Disable unused MCP servers; keep Context7 and one code-search MCP as defaults only.",
        "Use deep profiles only for architecture, ambiguous debugging, and final synthesis.",
        "Compact/clear between unrelated workstreams and preserve only files changed, tests run, decisions, and unresolved risks.",
        "If 429s appear, reduce concurrent worker fan-out before adding more providers.",
    ]
    if not rotation.get("daily_ok"):
        suggestions.append("Desired daily request volume exceeds known free/throttled capacity; add a paid overflow provider or lower request rate.")
    if not rotation.get("rpm_ok"):
        suggestions.append("Desired RPM exceeds known provider capacity; increase inter-request delay or use Hermes/OpenRouter paid overflow routing.")

    return f"""# Agent Token Usage Analysis

Generated: {datetime.now(timezone.utc).isoformat()}

## Provider assumptions

{chr(10).join(provider_lines) or '- no providers configured'}

## Rotation calculation

```json
{json.dumps(rotation, indent=2)}
```

## Suggested improvements

{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(suggestions))}

## Raw usage excerpt

```json
{raw}
```
"""


@app.command("analyze-usage")
def analyze_usage(
    providers: Path = typer.Option(SKILL_ROOT / "assets" / "configs" / "providers.yml", "--providers", help="Provider quota config."),
    desired_rpm: float = typer.Option(2.0, "--desired-rpm", help="Desired sustained requests per minute for cheap/rotation providers."),
    desired_daily_requests: int = typer.Option(250, "--desired-daily-requests", help="Desired daily cheap/rotation request volume."),
    out: Path = typer.Option(DEFAULT_REPORT_DIR, "--out", help="Output directory for analysis report."),
    allow_web: bool = typer.Option(False, "--allow-web", help="Fetch provider docs snippets for refreshed notes."),
) -> None:
    """Analyze usage metrics and calculate provider rotation/fallback strategy."""
    qs = parse_providers(providers)
    web_notes = fetch_provider_notes(qs) if allow_web else {}
    usage = call_ccusage()
    if web_notes:
        usage["provider_doc_snippets"] = web_notes
    rotation = calculate_rotation(qs, desired_rpm=desired_rpm, desired_daily_requests=desired_daily_requests)
    report = usage_improvement_notes(usage, qs, rotation)
    mkdir(out)
    report_path = out / f"usage-analysis-{now_slug()}.md"
    write_text(report_path, report, apply=True)

    console.print(Panel.fit("Usage analysis complete", style="green"))
    console.print(f"[bold]Report:[/bold] {report_path}")
    table = Table(title="Rotation summary")
    table.add_column("Provider")
    table.add_column("Daily allocation")
    table.add_column("RPM")
    table.add_column("Interval")
    for row in rotation["plan"]:
        table.add_row(
            row["provider"],
            str(row["allocation_daily_requests"]),
            str(row["rpm"]),
            str(row["min_interval_seconds"]),
        )
    console.print(table)


@app.command("install-bundle")
def install_bundle(
    target: str = typer.Option("all", "--target", help="all or comma-separated agent names."),
    apply: bool = typer.Option(False, "--apply", help="Actually install files. Dry-run is default."),
) -> None:
    """Install bundled agents, MCP definitions, profiles, and shared instructions into supported CLI config dirs."""
    targets = normalize_targets(target)
    paths = agent_paths()

    for t in targets:
        p = paths[t]
        mkdir(p.home) if apply else console.print(f"[yellow]dry-run[/yellow] would ensure {p.home}")

    # Instructions
    instr = SKILL_ROOT / "assets" / "templates" / "AGENTS.md"
    propagate_args = [
        ("instruction", "Agent Token Efficiency", instr),
    ]
    for _, name, src in propagate_args:
        text = read_text(src)
        for t in targets:
            if t == "claude":
                merge_markdown(paths[t].home / "CLAUDE.md", name, text, apply=apply)
            else:
                merge_markdown(paths[t].home / "AGENTS.md", name, text, apply=apply)

    # Skills
    for t in targets:
        if paths[t].skills_dir:
            copy_path(SKILL_ROOT, paths[t].skills_dir / "agent-token-efficiency", apply=apply)

    # Agents
    agent_assets = {
        "claude": SKILL_ROOT / "assets" / "agents" / "claude",
        "codex": SKILL_ROOT / "assets" / "agents" / "codex",
        "kimi": SKILL_ROOT / "assets" / "agents" / "kimi",
    }
    for t, srcdir in agent_assets.items():
        if t in targets and srcdir.exists() and paths[t].agents_dir:
            for src in srcdir.iterdir():
                dst = paths[t].agents_dir / src.name
                copy_path(src, dst, apply=apply)

    # MCPs
    for mcp_file in (SKILL_ROOT / "assets" / "mcp").glob("*.json"):
        try:
            mcp_def = load_mcp_definition(mcp_file)
            if mcp_def.get("enabled_by_default") is False:
                console.print(f"[yellow]skip[/yellow] optional MCP {mcp_def['name']} (enable explicitly with propagate-update)")
                continue
            apply_mcp(mcp_def, targets, apply=apply)
        except Exception as exc:
            console.print(f"[red]failed MCP {mcp_file.name}:[/red] {exc}")

    console.print("[green]bundle install workflow complete[/green]" if apply else "[yellow]dry-run complete; add --apply to install[/yellow]")


@app.command("smoke")
def smoke(
    repo: Optional[Path] = typer.Option(None, "--repo", help="Optional repo path to check for AGENTS.md and git status."),
) -> None:
    """Run lightweight smoke checks after install."""
    doctor(verbose=False)
    if repo:
        repo = repo.expanduser().resolve()
        console.print(f"[bold]Repo:[/bold] {repo}")
        console.print(f"AGENTS.md: {'yes' if (repo / 'AGENTS.md').exists() else 'no'}")
        git_status = run_cmd(["git", "status", "--short"], cwd=repo)
        console.print("Git status:")
        console.print(git_status.stdout or "clean / not a git repo / no output")


if __name__ == "__main__":
    app()
