#!/usr/bin/env python3
"""Deliver a published daily report to the places a human actually looks.

A report that only exists in ``_bmad-output`` is not delivered; it is filed.
This module fans one published generation out to four targets:

    vault     the Obsidian vault, as a dated note with frontmatter
    notebook  open-notebook at notebooklm.delo.sh, as a note in a dev journal
    email     the full report, rendered, to the operator
    slack     a digest -- executive brief plus anything degraded -- to a channel

Every target reports its own outcome. One failing target never blocks the
others and never turns a delivered report into an undelivered one: partial
delivery is reported as partial, which is the same honesty rule the rest of
this package runs on. The exit code says whether every ENABLED target
succeeded, so a scheduler cannot record success over a silent drop.

Reads the generation ``current.json`` names -- never a loose file on disk, and
never a generation that did not verify.

Stdlib only, except that Resend is reached over plain HTTPS.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

RESEND_ENDPOINT = "https://api.resend.com/emails"
#: Cloudflare fronts api.resend.com and rejects urllib's default
#: "Python-urllib/3.x" agent with a 403 (error 1010) before the request ever
#: reaches Resend. An explicit agent is required, not cosmetic.
USER_AGENT = "delonet-daily-report/2 (+https://delo.sh)"
RESEND_OP_REF = "op://DeLoSecrets/wulyiisb24eht3wknd6ynf2nyy/credential"
NOTEBOOK_CONTAINER = "open_notebook_core"
NOTEBOOK_PORT = 5055
HTTP_TIMEOUT = 30


@dataclass
class Delivery:
    """One target's outcome. ``ok`` is earned, never assumed."""

    target: str
    ok: bool = False
    skipped: bool = False
    detail: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        out = {"target": self.target, "ok": self.ok, "detail": self.detail}
        if self.skipped:
            out["skipped"] = True
        out.update(self.extra)
        return out


# --------------------------------------------------------------------------- io


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            **(headers or {}),
        },
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw) if raw.strip() else {}


def _request(url: str, method: str) -> None:
    req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT):
        return


def _get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def resend_api_key() -> str | None:
    """Environment first, then the vault. Never a literal in config.

    A cron run does not inherit the interactive shell, so ``RESEND_API_KEY``
    is usually absent there and the ``op`` read is the path that actually
    fires. Both are allowed; a key written into report.json is not.
    """
    key = os.environ.get("RESEND_API_KEY", "").strip()
    if key:
        return key
    try:
        out = subprocess.run(
            ["op", "read", RESEND_OP_REF],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


def notebook_base_url(configured: str | None = None) -> str | None:
    """Resolve the open-notebook API base.

    The API listens on 5055 inside the container and is NOT published to the
    host, so the container IP is the working route today. That IP changes when
    the container is recreated, hence the ordered fallback rather than a
    hardcoded address: an explicit config/env value, then a published host
    port if one ever appears, then ``docker inspect``.
    """
    for candidate in (configured, os.environ.get("DDR_NOTEBOOK_URL")):
        if candidate:
            return candidate.rstrip("/")
    for host in ("127.0.0.1", "localhost"):
        try:
            _get_json(f"http://{host}:{NOTEBOOK_PORT}/api/notebooks")
            return f"http://{host}:{NOTEBOOK_PORT}"
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            continue
    try:
        out = subprocess.run(
            ["docker", "inspect", NOTEBOOK_CONTAINER,
             "--format", "{{json .NetworkSettings.Networks}}"],
            capture_output=True, text=True, timeout=20,
        )
        if out.returncode == 0:
            for net in json.loads(out.stdout).values():
                ip = net.get("IPAddress")
                if ip:
                    return f"http://{ip}:{NOTEBOOK_PORT}"
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, AttributeError):
        pass
    return None


# ------------------------------------------------------------------- rendering


#: Collector sections, in the order a person wants to read them. The four core
#: sections (executive-brief, key-changes, ...) are prose ABOUT these, so the
#: digest reads the collectors directly and skips the prose -- otherwise every
#: fact arrives three times.
DIGEST_SECTION_IDS = ("dev-activity", "fleet-health", "pr-maintenance", "report-delivery")

#: Warnings are collected from this section only. It is the canonical place the
#: pipeline puts them; the same strings are repeated verbatim in the brief, the
#: key-changes list and each collector body, and scanning all of them produced a
#: digest that stated one problem seven times.
WARNING_SECTION_ID = "risks-watchlist"
WARNING_FLAGS = ("DEGRADED", "FAILED", "DISAGREEMENT", "missing skill")
DIGEST_LINE_CHARS = 200
MAX_WARNINGS = 8


def _one_line(text: str, limit: int = DIGEST_LINE_CHARS) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"


def _summary_of(section: dict[str, Any]) -> str:
    """First real sentence of a section body, minus pipeline markup."""
    for line in (section.get("body") or "").splitlines():
        text = line.strip()
        if not text or text.startswith(("**Status (authoritative)", "Metrics:", "Caveats:",
                                        "Detail:", "Narration follows")):
            continue
        return text
    return ""


def digest_lines(report: dict[str, Any], status: str) -> list[str]:
    """The short form: what happened, what needs attention, nothing else.

    A 32KB report pasted into a channel is not read. This is the part a person
    scanning Slack can act on, so it stays near fifteen lines and leads with
    the headline, not with prose.
    """
    date = report.get("report_date", "?")
    coverage = report.get("coverage") or {}
    degraded = coverage.get("degraded") or []
    complete = coverage.get("complete") or []
    by_id = {s.get("id"): s for s in report.get("sections", [])}

    lines = [
        f"*Daily Developer Report — {date}*  ·  status: *{status}*",
        f"{len(complete)} of {len(complete) + len(degraded)} sections complete"
        + (f" · degraded: {', '.join(degraded)}" if degraded else ""),
        "",
    ]

    for sid in DIGEST_SECTION_IDS:
        section = by_id.get(sid)
        if not section:
            continue
        mark = "⚠️" if sid in degraded else "•"
        summary = _summary_of(section)
        lines.append(f"{mark} *{section.get('title', sid)}* — {_one_line(summary)}")

    warnings: list[str] = []
    seen: set[str] = set()
    for line in ((by_id.get(WARNING_SECTION_ID) or {}).get("body") or "").splitlines():
        text = line.strip()
        if not text or not any(flag in text for flag in WARNING_FLAGS):
            continue
        # Collapse near-duplicates: the same fact is emitted with and without a
        # section-id prefix, so key on the tail rather than the whole line.
        key = _one_line(text.split(":", 1)[-1], 90).lower()
        if key in seen:
            continue
        seen.add(key)
        warnings.append(_one_line(text))

    if warnings:
        lines += ["", "*Needs attention:*"]
        lines += [f"  • {w}" for w in warnings[:MAX_WARNINGS]]
        if len(warnings) > MAX_WARNINGS:
            lines.append(f"  … and {len(warnings) - MAX_WARNINGS} more, in the full report")

    lines += ["", f"Full report: vault Journal/Dev-Reports/{date}.md · notebooklm.delo.sh"]
    return lines


def markdown_to_html(markdown: str) -> str:
    """A deliberately dumb renderer: preformatted text in a readable shell.

    The report is plain text with underlined headings, not rich markdown, and
    a real markdown library would be a dependency for no gain. Escaping is
    mandatory here regardless -- this text reaches an HTML mail client.
    """
    escaped = (markdown.replace("&", "&amp;")
                       .replace("<", "&lt;")
                       .replace(">", "&gt;"))
    return (
        '<div style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;'
        'font-size:13px;line-height:1.5;color:#1a1a1a;background:#fff;'
        'padding:16px;white-space:pre-wrap;word-wrap:break-word">'
        f"{escaped}</div>"
    )


def vault_note(markdown: str, report: dict[str, Any], status: str, run_id: str) -> str:
    """The vault copy, with frontmatter Obsidian and Dataview can query."""
    coverage = report.get("coverage") or {}
    degraded = coverage.get("degraded") or []
    front = [
        "---",
        f"date: {report.get('report_date', '')}",
        "type: dev-report",
        f"status: {status}",
        f"run_id: {run_id}",
        f"sections_complete: {len(coverage.get('complete') or [])}",
        f"sections_degraded: {len(degraded)}",
    ]
    if degraded:
        front.append("degraded:")
        front += [f"  - {d}" for d in degraded]
    front += ["generated_by: delonet-daily-report", "tags: [dev-journal, generated]", "---", ""]
    return "\n".join(front) + markdown


# --------------------------------------------------------------------- targets


def deliver_vault(cfg: dict[str, Any], markdown: str, report: dict[str, Any],
                  status: str, run_id: str, dry_run: bool) -> Delivery:
    d = Delivery("vault")
    root = Path(cfg["path"]).expanduser()
    target = root / f"{report.get('report_date')}.md"
    content = vault_note(markdown, report, status, run_id)
    if dry_run:
        d.ok, d.detail = True, f"would write {target} ({len(content)} bytes)"
        return d
    try:
        root.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".md.tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(target)
    except OSError as exc:
        d.detail = f"write failed: {exc}"
        return d
    d.ok, d.detail = True, f"wrote {target}"
    d.extra["path"] = str(target)

    if cfg.get("git_commit"):
        d.extra["git"] = _git_commit_vault(root, target, report.get("report_date", ""))
    return d


def _git_commit_vault(root: Path, target: Path, date: str) -> str:
    """Commit and push the vault note. Never fails the delivery.

    The note is on disk either way; git is how it reaches the operator's other
    machines. A push failure is worth reporting, not worth discarding a
    successful write over.
    """
    def git(*args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(root), *args],
                              capture_output=True, text=True, timeout=timeout)
    try:
        if git("rev-parse", "--git-dir").returncode != 0:
            return "not a git repository"
        if not git("status", "--porcelain", "--", str(target)).stdout.strip():
            return "no change to commit"
        if git("add", "--", str(target)).returncode != 0:
            return "git add failed"
        commit = git("commit", "-q", "-m", f"chore(dev-report): {date}")
        if commit.returncode != 0:
            return f"git commit failed: {commit.stderr.strip()[:160]}"
        push = git("push", timeout=180)
        return "committed and pushed" if push.returncode == 0 else \
            f"committed; push failed: {push.stderr.strip()[:160]}"
    except (OSError, subprocess.SubprocessError) as exc:
        return f"git error: {exc}"


def deliver_notebook(cfg: dict[str, Any], markdown: str, report: dict[str, Any],
                     status: str, dry_run: bool) -> Delivery:
    d = Delivery("notebook")
    base = notebook_base_url(cfg.get("base_url"))
    if not base:
        d.detail = "open-notebook API unreachable (tried config, env, localhost, docker inspect)"
        return d
    d.extra["base_url"] = base
    wanted = cfg.get("notebook_name", "Dev Journal")
    date = report.get("report_date", "?")

    if dry_run:
        d.ok, d.detail = True, f"would add note '{date}' to notebook '{wanted}' at {base}"
        return d
    try:
        notebooks = _get_json(f"{base}/api/notebooks")
        match = next((n for n in notebooks if n.get("name") == wanted), None)
        if match is None:
            match = _post_json(f"{base}/api/notebooks", {
                "name": wanted,
                "description": ("Nightly developer reports generated by "
                                "delonet-daily-report from the Candystore audit trail, "
                                "git history, Hermes fleet state and pr-crusher state."),
            })
            d.extra["created_notebook"] = True
        # Replace, never append. A nightly job gets re-run -- after a fix, after
        # a backfill -- and a notebook holding four notes for two days is worse
        # than one holding two, because neither copy is obviously the current one.
        title_prefix = f"Dev Report — {date} "
        existing = [
            n for n in _get_json(f"{base}/api/notes?notebook_id={match['id']}")
            if str(n.get("title", "")).startswith(title_prefix)
        ]
        note = _post_json(f"{base}/api/notes", {
            "title": f"{title_prefix}[{status}]",
            "content": markdown,
            "notebook_id": match["id"],
        })
        replaced = 0
        for stale in existing:
            try:
                _request(f"{base}/api/notes/{stale['id']}", "DELETE")
                replaced += 1
            except (urllib.error.URLError, OSError):
                pass  # a leftover duplicate is not worth failing a delivery over
        if replaced:
            d.extra["replaced_notes"] = replaced
    except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError, TypeError) as exc:
        d.detail = f"notebook API failed: {exc}"
        return d
    d.ok = True
    d.detail = f"added note to '{wanted}'"
    d.extra["note_id"] = note.get("id")
    d.extra["notebook_id"] = match.get("id")
    return d


def _send_resend(api_key: str, sender: str, to: list[str], subject: str,
                 *, html: str | None = None, text: str | None = None) -> tuple[bool, str]:
    payload: dict[str, Any] = {"from": sender, "to": to, "subject": subject}
    if html:
        payload["html"] = html
    if text:
        payload["text"] = text
    try:
        out = _post_json(RESEND_ENDPOINT, payload,
                         {"Authorization": f"Bearer {api_key}"})
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        return False, f"HTTP {exc.code}: {body}"
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        return False, f"send failed: {exc}"
    return True, f"id={out.get('id', '?')}"


def deliver_mail(target: str, cfg: dict[str, Any], markdown: str, report: dict[str, Any],
                 status: str, dry_run: bool) -> Delivery:
    d = Delivery(target)
    recipients = [r for r in (cfg.get("to") or []) if r]
    if not recipients:
        d.detail = "no recipients configured"
        return d
    date = report.get("report_date", "?")
    subject = cfg.get("subject_template", "Dev Journal — {date} [{status}]").format(
        date=date, status=status)

    if cfg.get("mode", "full") == "digest":
        text = "\n".join(digest_lines(report, status))
        html = None
    else:
        text = markdown
        html = markdown_to_html(markdown)

    if dry_run:
        d.ok = True
        d.detail = (f"would send {cfg.get('mode', 'full')} to {', '.join(recipients)} "
                    f"({len(text)} bytes)")
        return d

    api_key = resend_api_key()
    if not api_key:
        d.detail = "no Resend API key (RESEND_API_KEY unset and `op read` unavailable)"
        return d
    ok, detail = _send_resend(api_key, cfg.get("from", "dev-journal@delo.sh"),
                              recipients, subject, html=html, text=text)
    d.ok, d.detail = ok, detail
    d.extra["to"] = recipients
    return d


# ------------------------------------------------------------------ entrypoint


def distribute(config: dict[str, Any], date: str, markdown: str, report: dict[str, Any],
               status: str, run_id: str, *, only: list[str] | None = None,
               dry_run: bool = False) -> dict[str, Any]:
    """Fan one published generation out. Returns an honest per-target result."""
    dist = config.get("distribution") or {}
    results: list[Delivery] = []

    for name in ("vault", "notebook", "email", "slack"):
        cfg = dist.get(name) or {}
        if only and name not in only:
            results.append(Delivery(name, ok=True, skipped=True, detail="not selected"))
            continue
        if not cfg.get("enabled", False):
            results.append(Delivery(name, ok=True, skipped=True, detail="disabled in config"))
            continue
        if name == "vault":
            results.append(deliver_vault(cfg, markdown, report, status, run_id, dry_run))
        elif name == "notebook":
            results.append(deliver_notebook(cfg, markdown, report, status, dry_run))
        else:
            results.append(deliver_mail(name, cfg, markdown, report, status, dry_run))

    attempted = [r for r in results if not r.skipped]
    failed = [r.target for r in attempted if not r.ok]
    return {
        "date": date,
        "run_id": run_id,
        "report_status": status,
        "dry_run": dry_run,
        "deliveries": [r.as_dict() for r in results],
        "delivered": [r.target for r in attempted if r.ok],
        "failed": failed,
        # Enabled-but-unattempted is not success. Only a target that ran and
        # succeeded counts, which is what keeps this from becoming the kind of
        # cheerful lie the rest of the package exists to prevent.
        "ok": not failed and bool(attempted),
    }
