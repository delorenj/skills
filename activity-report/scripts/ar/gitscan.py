"""Commits across every ref and linked worktree of each configured root.

Per root: `git log --all` (stash and notes excluded) plus `git log HEAD` in
every linked worktree, unioned by sha. Rebase replays (same author date and
subject under a new sha) collapse to one commit, preferring the copy on the
default branch. Commits are filtered on committer date against [start, end)
client-side because git's --since/--until are inclusive at the edges.
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import timedelta

from .common import parse_iso, to_iso_z

EXCLUDED_REF_GLOBS = ("refs/stash", "refs/notes/*")
SEP = "\x1f"
RECORD = "\x1e"
LOG_FORMAT = SEP.join(("%H", "%h", "%cI", "%aI", "%an", "%s"))
COMMIT_CAP = 100
BRANCH_CAP = 64
REPO_CAP = 8
SUBJECT_CHARS = 120
AUTHOR_CHARS = 80
MAX_REF_PROBES = 300
GIT_TIMEOUT = 120
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_REMOTE_RE = re.compile(r"^refs/remotes/[^/]+/")


class GitFailed(Exception):
    pass


def _git(cwd: str, *args: str, timeout: int = GIT_TIMEOUT) -> str:
    try:
        proc = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, errors="replace",
                              timeout=timeout, check=False)
    except FileNotFoundError as exc:
        raise GitFailed("git is not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitFailed(f"git {args[0]} timed out after {timeout}s in {cwd}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        raise GitFailed(f"git {' '.join(args[:2])} failed in {cwd}: {detail[0][:200] if detail else 'no output'}")
    return proc.stdout


def _git_ok(cwd: str, *args: str) -> str | None:
    try:
        return _git(cwd, *args)
    except GitFailed:
        return None


def _ref_exists(cwd: str, ref: str) -> bool:
    return _git_ok(cwd, "rev-parse", "-q", "--verify", ref + "^{commit}") is not None


def _default_branch(root: str) -> str:
    ref = _git_ok(root, "symbolic-ref", "-q", "refs/remotes/origin/HEAD")
    if ref and ref.strip().startswith("refs/remotes/origin/"):
        return ref.strip()[len("refs/remotes/origin/"):]
    for candidate in ("main", "master"):
        if _ref_exists(root, f"refs/heads/{candidate}"):
            return candidate
    return "main"


def _range_args(start, end) -> list[str]:
    # git's --until is inclusive at second resolution; the window is half-open [start, end).
    return [f"--since={to_iso_z(start)}", f"--until={to_iso_z(end - timedelta(seconds=1))}"]


def _log(cwd: str, revs: list[str], start, end) -> list[dict]:
    out = _git(cwd, "log", "--no-merges", *_range_args(start, end), f"--format={LOG_FORMAT}", *revs)
    commits = []
    for line in out.split("\n"):   # not splitlines(): it treats \x1e as a line break
        parts = line.split(SEP)
        if len(parts) != 6:
            continue
        sha, short, committed, authored, author, subject = parts
        try:
            at = parse_iso(committed)
        except ValueError:
            continue
        if not (start <= at < end):
            continue
        commits.append({"sha": sha, "short": short, "at": at, "authored": authored, "author": author, "subject": subject})
    return commits


def _numstat(cwd: str, revs: list[str], start, end) -> dict[str, list]:
    """sha -> [set(paths), insertions, deletions] for the commits git lists under revs."""
    out = _git(cwd, "log", "--no-merges", *_range_args(start, end), f"--format={RECORD}%H", "--numstat", *revs)
    stats: dict[str, list] = {}
    current = None
    for line in out.split("\n"):   # not splitlines(): it treats \x1e as a line break
        if line.startswith(RECORD):
            current = line[1:].strip()
            stats.setdefault(current, [set(), 0, 0])
            continue
        if not current or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, path = parts[0], parts[1], "\t".join(parts[2:])
        rec = stats[current]
        rec[0].add(path)
        if added.isdigit():
            rec[1] += int(added)
        if deleted.isdigit():
            rec[2] += int(deleted)
    return stats


def _default_shas(root: str, default: str, start, end) -> set[str]:
    shas: set[str] = set()
    for ref in (f"refs/heads/{default}", f"refs/remotes/origin/{default}"):
        if not _ref_exists(root, ref):
            continue
        out = _git_ok(root, "rev-list", "--no-merges", *_range_args(start, end), ref)
        if out:
            shas.update(out.split())
    return shas


def _short_ref(refname: str) -> str:
    if refname.startswith("refs/heads/"):
        return refname[len("refs/heads/"):]
    return _REMOTE_RE.sub("", refname)


def _branches(root: str, start, end, default: str, caveats: list[str], name: str) -> list[str]:
    out = _git_ok(root, "for-each-ref", "--sort=-committerdate",
                  "--format=%(refname)%09%(committerdate:iso-strict)%09%(objecttype)", "refs/heads", "refs/remotes")
    found: dict[str, int] = {}
    probes = 0
    for line in (out or "").splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        refname, date, objtype = parts
        if objtype != "commit" or refname.endswith("/HEAD"):
            continue
        try:
            tip = parse_iso(date)
        except ValueError:
            continue
        if tip < start:
            break
        probes += 1
        if probes > MAX_REF_PROBES:
            caveats.append(f"repo {name}: more than {MAX_REF_PROBES} refs updated in the window; branch list is partial")
            break
        count = _git_ok(root, "rev-list", "--no-merges", *_range_args(start, end), "--count", refname)
        n = int(count.strip()) if count and count.strip().isdigit() else 0
        if n <= 0:
            continue
        short = _short_ref(refname)
        found[short] = max(found.get(short, 0), n)
    names = sorted(found, key=lambda b: (b != default, -found[b], b))
    if len(names) > BRANCH_CAP:
        caveats.append(f"repo {name}: branches capped at {BRANCH_CAP} of {len(names)}")
        names = names[:BRANCH_CAP]
    return names


def _worktrees(root: str) -> list[dict]:
    out = _git_ok(root, "worktree", "list", "--porcelain")
    entries: list[dict] = []
    current: dict | None = None
    for line in (out or "").splitlines():
        if line.startswith("worktree "):
            current = {"path": os.path.normpath(line[len("worktree "):].strip()), "head": None, "branch": None}
            entries.append(current)
        elif current is not None and line.startswith("HEAD "):
            current["head"] = line[len("HEAD "):].strip()
        elif current is not None and line.startswith("branch "):
            branch = line[len("branch "):].strip()
            current["branch"] = branch[len("refs/heads/"):] if branch.startswith("refs/heads/") else branch
        elif current is not None and line.strip() == "detached":
            current["branch"] = None
    return [e for e in entries if e["path"] != os.path.normpath(root)]


def _is_checkout(path: str) -> bool:
    dot_git = os.path.join(path, ".git")
    return os.path.isdir(dot_git) or os.path.isfile(dot_git)


def _uncommitted(path: str) -> int:
    out = _git_ok(path, "status", "--porcelain", "--ignore-submodules=dirty", "-z")
    if out is None:
        return 0
    tokens = out.split("\0")
    i = n = 0
    while i < len(tokens):
        entry = tokens[i]
        if not entry:
            i += 1
            continue
        n += 1
        status = entry[:2]
        i += 2 if ("R" in status or "C" in status) else 1
    return n


def _empty(name: str, state: str) -> dict:
    return {
        "name": name, "state": state, "default_branch": None,
        "commit_count": 0, "on_default": 0, "off_default": 0, "replays": 0, "truncated": False,
        "commits": [], "branches": [], "worktrees": [],
        "uncommitted_files": 0, "files_changed": 0, "insertions": 0, "deletions": 0,
    }


def _scan_root(root: str, name: str, scope, window, caveats: list[str]) -> dict:
    start, end = window.start, window.end
    default = _default_branch(root)
    default_shas = _default_shas(root, default, start, end)
    all_revs = [f"--exclude={glob}" for glob in EXCLUDED_REF_GLOBS] + ["--all"]
    commits: dict[str, dict] = {c["sha"]: c for c in _log(root, all_revs, start, end)}

    worktrees = [wt for wt in _worktrees(root) if os.path.isdir(wt["path"])]
    known = {wt["path"] for wt in worktrees}
    for extra in scope.worktrees:
        if extra.startswith(root + os.sep) and extra not in known and _is_checkout(extra):
            worktrees.append({"path": extra, "head": None, "branch": None})
            known.add(extra)
    worktree_blocks = []
    wt_stats: dict[str, list] = {}
    for wt in worktrees:
        path = wt["path"]
        try:
            for c in _log(path, ["HEAD"], start, end):
                commits.setdefault(c["sha"], c)
            head = _git_ok(path, "rev-parse", "--short", "HEAD")
            if wt["branch"] is None:
                branch = _git_ok(path, "symbolic-ref", "-q", "--short", "HEAD")
                wt["branch"] = branch.strip() if branch else None
            worktree_blocks.append({"path": path, "branch": wt["branch"], "head": (head or wt["head"] or "")[:12].strip() or None,
                                    "uncommitted_files": _uncommitted(path)})
            wt_stats.update(_numstat(path, ["HEAD"], start, end))
        except GitFailed as exc:
            caveats.append(f"repo {name}: worktree {os.path.basename(path)} skipped: {exc}")

    groups: dict[tuple, list[dict]] = {}
    for c in commits.values():
        groups.setdefault((c["authored"], c["subject"]), []).append(c)
    kept: list[dict] = []
    replays = 0
    for group in groups.values():
        if len(group) > 1:
            group.sort(key=lambda c: (c["sha"] in default_shas, c["at"], c["sha"]), reverse=True)
            replays += len(group) - 1
        kept.append(group[0])
    kept.sort(key=lambda c: (c["at"], c["sha"]), reverse=True)

    stats = _numstat(root, all_revs, start, end)
    stats.update({sha: rec for sha, rec in wt_stats.items() if sha not in stats})
    files: set[str] = set()
    insertions = deletions = 0
    for c in kept:
        rec = stats.get(c["sha"])
        if rec:
            files |= rec[0]
            insertions += rec[1]
            deletions += rec[2]

    on_default = sum(1 for c in kept if c["sha"] in default_shas)
    truncated = len(kept) > COMMIT_CAP
    if truncated:
        caveats.append(f"repo {name}: commits capped at {COMMIT_CAP} of {len(kept)}")
    shown = [{
        "sha": c["sha"], "short": c["short"], "at": to_iso_z(c["at"]),
        "author": c["author"][:AUTHOR_CHARS], "subject": c["subject"][:SUBJECT_CHARS],
        "on_default": c["sha"] in default_shas,
    } for c in kept[:COMMIT_CAP]]
    return {
        "name": name, "state": "ok", "default_branch": default,
        "commit_count": len(kept), "on_default": on_default, "off_default": len(kept) - on_default,
        "replays": replays, "truncated": truncated, "commits": shown,
        "branches": _branches(root, start, end, default, caveats, name),
        "worktrees": worktree_blocks,
        "uncommitted_files": _uncommitted(root),
        "files_changed": len(files), "insertions": insertions, "deletions": deletions,
    }


def scan(project, scope, window) -> dict:
    """The digest "git" block (plus a caveats list digest.py hoists)."""
    caveats: list[str] = []
    repos: list[dict] = []
    roots = [os.path.normpath(r) for r in project.roots]
    if len(roots) > REPO_CAP:
        caveats.append(f"{len(roots)} repo roots configured; only the first {REPO_CAP} are scanned")
        roots = roots[:REPO_CAP]
    seen_names: set[str] = set()
    for root in roots:
        name = os.path.basename(root.rstrip(os.sep)) or root
        if not _NAME_RE.match(name):
            cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "repo"
            caveats.append(f"repo name {name!r} is not a valid repo name; recorded as {cleaned!r}")
            name = cleaned
        if name in seen_names:
            caveats.append(f"repo name {name!r} appears twice among the roots; the second is skipped")
            continue
        seen_names.add(name)
        if root in scope.missing or not _is_checkout(root):
            repos.append(_empty(name, "missing"))
            caveats.append(f"repo {name}: {root} is not a git checkout")
            continue
        try:
            repos.append(_scan_root(root, name, scope, window, caveats))
        except GitFailed as exc:
            repos.append(_empty(name, "failed"))
            caveats.append(f"repo {name}: {exc}")
    return {"commit_count": sum(r["commit_count"] for r in repos), "repos": repos, "caveats": caveats}
