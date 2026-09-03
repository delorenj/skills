"""Plane: labels, states, issues, exposure, and the ensure-labels write.

Exposure is read from a ticket's CURRENT labels (a live GET per ticket, newest
first, capped by `board.max_live_fetches`), because the label a PM adds after
the fact is the decision that matters. When the live read is not possible the
event snapshot stands in and the digest says so. Without a key or with the
API down, the external digest withholds every ticket (the safe direction) and
the internal digest marks them unlabeled.

No key is ever written to disk. It is read at call time from an `op://`
reference (config, then the builtin per-workspace map) or from the
environment; the digest and the cache carry names and ids only.
"""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

from . import __version__
from .common import ConfigError, cache_dir, read_json, to_iso_z, utc_now, write_json
from .config import load_project

PLANE_BASE_URL = os.environ.get("PLANE_BASE_URL", "https://plane.delo.sh")
USER_AGENT = f"activity-report/{__version__} (+https://delo.sh)"
BUILTIN_KEY_REFS = {
    "automaticai": "op://DeLoSecrets/Plane/AutomaticAI API Token",
    "33god": "op://DeLoSecrets/Plane33God/api_key",
}
LABEL_SPECS = {
    "external": {"color": "#0e7c86", "description": "Surface in client-facing updates: progress and wins only"},
    "internal": {"color": "#586a7a", "description": "Never surface to the client"},
}
CACHE_TTL_SECONDS = 24 * 3600
TIMEOUT_SECONDS = 30
MAX_PAGES = 50
TICKET_CAP = 200
LABEL_CAP = 8
TITLE_CHARS = 200
EXCERPT_CHARS = 600
_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_TICKET_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,11}-[0-9]+$")
_TAG_RE = re.compile(r"<[^>]+>")


class BoardUnavailable(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


# -- key resolution -------------------------------------------------------------

def _op_read(ref: str) -> str | None:
    try:
        proc = subprocess.run(["op", "read", ref], capture_output=True, text=True, timeout=30, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    value = proc.stdout.strip()
    return value if proc.returncode == 0 and value else None


def resolve_api_key(project) -> tuple[str | None, str, list[str]]:
    """(key, where it came from, what was tried). Never logs or stores the value."""
    tried: list[str] = []
    board = project.config.get("board") or {}
    ref = board.get("api_key_ref")
    if ref:
        ref = str(ref)
        if ref.startswith("op://"):
            value = _op_read(ref)
            if value:
                return value, f"board.api_key_ref {ref}", tried
            tried.append(f"board.api_key_ref {ref} (op read failed)")
        elif ref.startswith("env:"):
            name = ref[len("env:"):]
            value = os.environ.get(name)
            if value:
                return value, f"env {name}", tried
            tried.append(f"env {name} (unset)")
        else:
            tried.append("board.api_key_ref is neither op://… nor env:NAME (a literal key is never read from config)")
    names = ["PLANE_API_KEY"]
    if project.workspace:
        names.append("PLANE_" + re.sub(r"[^A-Za-z0-9]+", "_", project.workspace).upper() + "_API_KEY")
    for name in names:
        value = os.environ.get(name)
        if value:
            return value, f"env {name}", tried
        tried.append(f"env {name} (unset)")
    builtin = BUILTIN_KEY_REFS.get((project.workspace or "").lower())
    if builtin:
        value = _op_read(builtin)
        if value:
            return value, f"builtin ref for workspace {project.workspace}", tried
        tried.append(f"builtin ref {builtin} (op read failed)")
    else:
        tried.append(f"no builtin ref for workspace {project.workspace!r}")
    return None, "none", tried


# -- client ---------------------------------------------------------------------

def _explain(status: int) -> str:
    return {
        401: "the key was rejected", 403: "forbidden (a missing User-Agent gets this too)",
        404: "not found (workspace slug or board id?)", 429: "rate limited",
    }.get(status, "")


class PlaneApi:
    def __init__(self, workspace: str, board_id: str, api_key: str, base_url: str = PLANE_BASE_URL,
                 timeout: int = TIMEOUT_SECONDS):
        self.workspace = workspace
        self.board_id = board_id
        self._key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _url(self, path: str, params: dict | None = None) -> str:
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace}/projects/{self.board_id}/{path.strip('/')}/"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def request(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"X-API-Key": self._key, "Accept": "application/json", "User-Agent": USER_AGENT}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self._url(path, params), data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            raise BoardUnavailable(f"Plane {method} {path}: HTTP {exc.code} {_explain(exc.code)}".rstrip(), exc.code) from exc
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise BoardUnavailable(f"Plane {method} {path}: {exc}") from exc
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise BoardUnavailable(f"Plane {method} {path}: non-JSON response") from exc
        return payload if isinstance(payload, dict) else {"results": payload}

    def paged(self, path: str) -> list[dict]:
        results: list[dict] = []
        cursor = None
        for _ in range(MAX_PAGES):
            params = {"per_page": 100}
            if cursor:
                params["cursor"] = cursor
            body = self.request("GET", path, params=params)
            batch = body.get("results")
            if isinstance(batch, list):
                results.extend(x for x in batch if isinstance(x, dict))
            if not body.get("next_page_results"):
                break
            cursor = body.get("next_cursor")
            if not cursor:
                break
        return results

    def labels(self) -> list[dict]:
        return self.paged("labels")

    def states(self) -> list[dict]:
        return self.paged("states")

    def issue(self, issue_id: str) -> dict:
        return self.request("GET", f"issues/{issue_id}")

    def create_label(self, name: str, color: str, description: str) -> dict:
        return self.request("POST", "labels", body={"name": name, "color": color, "description": description})


# -- cache ----------------------------------------------------------------------

def _cache_path(project, kind: str) -> str:
    return os.path.join(cache_dir("plane", project.workspace, project.board_id), f"{kind}.json")


def _write_cache(project, kind: str, items: list[dict]) -> None:
    write_json(_cache_path(project, kind), {"fetched_at": to_iso_z(utc_now()), "fetched_at_epoch": time.time(), "items": items})


def _cached(project, kind: str, fetch) -> tuple[list[dict], str | None]:
    """Items from the 24 h cache, else fetched and cached; a stale cache stands in when the fetch fails."""
    path = _cache_path(project, kind)
    cached = None
    try:
        cached = read_json(path)
    except (OSError, ValueError):
        cached = None
    if isinstance(cached, dict):
        try:
            age = time.time() - float(cached.get("fetched_at_epoch") or 0)
        except (TypeError, ValueError):
            age = CACHE_TTL_SECONDS + 1
        if age < CACHE_TTL_SECONDS and isinstance(cached.get("items"), list):
            return list(cached["items"]), None
    try:
        items = fetch()
    except BoardUnavailable as exc:
        if isinstance(cached, dict) and isinstance(cached.get("items"), list) and cached["items"]:
            return list(cached["items"]), f"Plane {kind} list failed ({exc}); using the cached {kind} from {cached.get('fetched_at')}"
        raise
    _write_cache(project, kind, items)
    return items, None


# -- enrichment -----------------------------------------------------------------

def _identifiers(project) -> list[str]:
    ids = [project.identifier] if project.identifier else []
    for extra in (project.config.get("lint") or {}).get("extra_identifiers") or []:
        if isinstance(extra, str) and extra and extra not in ids:
            ids.append(extra)
    return ids


def _label_names(values, label_by_id: dict) -> list[str]:
    names: list[str] = []
    for value in values or []:
        name = None
        if isinstance(value, dict):
            name = value.get("name") or label_by_id.get(value.get("id"))
        elif isinstance(value, str):
            name = label_by_id.get(value) if _UUID_RE.match(value) else value
            if name is None and _UUID_RE.match(value):
                continue
        if isinstance(name, str) and name and name not in names:
            names.append(name)
    return names


def _exposure(labels: list[str], external: str, internal: str) -> str:
    if internal in labels:
        return "internal"
    if external in labels:
        return "external"
    return "unlabeled"


def strip_html(text: str) -> str:
    text = re.sub(r"</(p|div|li|br|h[1-6]|tr)>", " ", text, flags=re.IGNORECASE)
    text = _TAG_RE.sub(" ", text)
    return " ".join(html.unescape(text).split())


def _excerpt(issue: dict | None, record: dict) -> str | None:
    text = None
    if issue and isinstance(issue.get("description_html"), str) and issue["description_html"].strip():
        text = strip_html(issue["description_html"])
    elif isinstance(record.get("description"), str) and record["description"].strip():
        text = " ".join(record["description"].split())
    return text[:EXCERPT_CHARS] if text else None


def _state_name(value, state_by_id: dict) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if _UUID_RE.match(value):
        entry = state_by_id.get(value)
        return entry.get("name") if isinstance(entry, dict) else None
    return value


def _ticket_url(project, ticket_id: str | None) -> str | None:
    if not (ticket_id and project.workspace and project.board_id):
        return None
    return f"{PLANE_BASE_URL}/{project.workspace}/projects/{project.board_id}/issues/{ticket_id}"


def enrich(project, ticket_events: list[dict], window, audience: str) -> tuple[dict, dict | None]:
    """(the digest "board" block, the lint.json dict for external or None)."""
    board_cfg = project.config.get("board") or {}
    labels_cfg = board_cfg.get("exposure_labels") or {}
    ext_label = labels_cfg.get("external") or "xp:external"
    int_label = labels_cfg.get("internal") or "xp:internal"
    max_live = int(board_cfg.get("max_live_fetches") or 0)
    caveats: list[str] = []
    block = {
        "provider": project.provider_type, "status": "ok", "labels_resolved": False,
        "exposure_labels": {"external": ext_label, "internal": int_label},
        "tickets": [], "opened": [], "closed": [], "started": [], "commented": [], "decisions": [],
        "caveats": caveats,
    }
    lint = {"identifiers": _identifiers(project), "denied_titles": [], "surface_always": []} if audience == "external" else None

    if (project.provider_type or "").lower() != "plane" or not project.board_id or not project.workspace:
        block["status"] = "unsupported"
        caveats.append(f"ticket provider {project.provider_type!r} (workspace {project.workspace!r}, board {project.board_id!r}) "
                       f"is not supported; {len(ticket_events)} ticket events in the window were not listed")
        return block, lint

    api: PlaneApi | None = None
    label_by_id: dict = {}
    state_by_id: dict = {}
    key, _source, tried = resolve_api_key(project)
    if key is None:
        block["status"] = "unavailable"
        caveats.append("Plane API key not found: " + "; ".join(tried))
    else:
        api = PlaneApi(project.workspace, project.board_id, key)
        try:
            labels, note_l = _cached(project, "labels", api.labels)
            states, note_s = _cached(project, "states", api.states)
        except BoardUnavailable as exc:
            block["status"] = "unavailable"
            caveats.append(f"Plane unavailable: {exc}")
            api = None
        else:
            for note in (note_l, note_s):
                if note:
                    caveats.append(note)
            label_by_id = {l["id"]: l.get("name") for l in labels if isinstance(l, dict) and l.get("id")}
            state_by_id = {s["id"]: {"name": s.get("name"), "group": s.get("group")} for s in states if isinstance(s, dict) and s.get("id")}
            block["labels_resolved"] = bool(label_by_id)
            missing = [n for n in (ext_label, int_label) if n not in label_by_id.values()]
            if missing:
                caveats.append(f"exposure label(s) {', '.join(missing)} do not exist on the board; "
                               "run `activity-report ensure-labels --confirm`")

    records = sorted(ticket_events, key=lambda r: r.get("last_seen") or "", reverse=True)
    live_budget = max_live if api else 0
    snapshot = unresolved = live_missing = 0
    live_errors: list[str] = []
    tickets: list[dict] = []
    flags = {"opened": [], "closed": [], "started": [], "commented": []}
    for rec in records:
        issue = None
        if live_budget > 0 and rec.get("ticket_id"):
            try:
                issue = api.issue(rec["ticket_id"])
                live_budget -= 1
            except BoardUnavailable as exc:
                if exc.status == 404:
                    live_missing += 1
                else:
                    live_errors.append(str(exc))
                    live_budget = 0
        key = rec.get("key")
        if not key and issue and project.identifier and issue.get("sequence_id") is not None:
            key = f"{project.identifier}-{issue['sequence_id']}"
        if not key or not _TICKET_KEY_RE.match(key):
            unresolved += 1
            continue
        title = (issue or {}).get("name") or rec.get("title") or key
        title = " ".join(str(title).split())[:TITLE_CHARS]
        if issue is not None:
            labels = _label_names(issue.get("labels"), label_by_id)
        else:
            labels = _label_names(rec.get("labels"), label_by_id)
            snapshot += 1
        labels = labels[:LABEL_CAP]
        if block["status"] == "ok":
            exposure = _exposure(labels, ext_label, int_label)
        else:
            exposure = "internal" if audience == "external" else "unlabeled"
        surface = None if audience == "internal" else ("always" if exposure == "external" else "judgment")
        transitions = rec.get("transitions") or []
        from_state = _state_name(transitions[0].get("from_state_id"), state_by_id) if transitions else None
        to_state = (transitions[-1].get("to_phase") if transitions else None) or rec.get("phase")
        ticket = {
            "key": key, "title": title, "from_state": from_state, "to_state": to_state,
            "event_kinds": list(rec.get("kinds") or []), "labels": labels, "exposure": exposure, "surface": surface,
            "description_excerpt": _excerpt(issue, rec) if (audience == "internal" or exposure == "external") else None,
            "url": _ticket_url(project, rec.get("ticket_id")),
            "first_seen": rec.get("first_seen"), "last_seen": rec.get("last_seen"),
        }
        if audience == "external":
            if exposure == "internal":
                lint["denied_titles"].append(title)
                continue
            if exposure == "external":
                lint["surface_always"].append({"key": key, "title": title})
        tickets.append(ticket)
        for flag in flags:
            if rec.get(flag):
                flags[flag].append(key)

    if len(tickets) > TICKET_CAP:
        caveats.append(f"tickets capped at {TICKET_CAP} of {len(tickets)}")
        kept = {t["key"] for t in tickets[:TICKET_CAP]}
        tickets = tickets[:TICKET_CAP]
        flags = {k: [x for x in v if x in kept] for k, v in flags.items()}
    if unresolved:
        caveats.append(f"{unresolved} ticket(s) had no resolvable key (comment-only events without a live read) and were dropped")
    if live_missing:
        caveats.append(f"{live_missing} ticket(s) answered 404 on the live read (deleted?); the event snapshot was used")
    if live_errors:
        caveats.append(f"live ticket reads stopped after an error: {live_errors[0]}")
    if snapshot and block["status"] == "ok":
        caveats.append(f"labels for {snapshot} ticket(s) come from the event snapshot, not a live read "
                       f"(board.max_live_fetches={max_live}); a label added since is not seen")
    if block["status"] != "ok" and records:
        if audience == "external":
            caveats.append(f"board {block['status']}: every ticket ({len(records)}) is withheld from the external digest")
        else:
            caveats.append(f"board {block['status']}: exposure is unlabeled for every ticket; labels were not verified")

    block["tickets"] = tickets
    block.update(flags)
    return block, lint


# -- ensure-labels ----------------------------------------------------------------

def ensure_labels(project, confirm: bool) -> dict:
    """Plan (and with confirm=True, create) the two exposure labels. Idempotent by name."""
    if (project.provider_type or "").lower() != "plane" or not project.board_id or not project.workspace:
        raise ConfigError(f"project {project.slug} has no Plane board (provider {project.provider_type!r})")
    labels_cfg = (project.config.get("board") or {}).get("exposure_labels") or {}
    key, source, tried = resolve_api_key(project)
    if key is None:
        raise ConfigError("Plane API key not found: " + "; ".join(tried))
    api = PlaneApi(project.workspace, project.board_id, key)
    try:
        existing = api.labels()
    except BoardUnavailable as exc:
        raise ConfigError(f"Plane unavailable: {exc}") from exc
    by_name = {l.get("name"): l for l in existing if isinstance(l, dict)}
    present, missing, created = [], [], []
    for role in ("external", "internal"):
        name = labels_cfg.get(role) or f"xp:{role}"
        spec = LABEL_SPECS[role]
        if name in by_name:
            found = by_name[name]
            present.append({"role": role, "name": name, "id": found.get("id"), "color": found.get("color")})
        else:
            missing.append({"role": role, "name": name, "color": spec["color"], "description": spec["description"]})
    if confirm:
        for spec in missing:
            try:
                made = api.create_label(spec["name"], spec["color"], spec["description"])
            except BoardUnavailable as exc:
                raise ConfigError(f"creating label {spec['name']} failed: {exc}") from exc
            created.append({"role": spec["role"], "name": spec["name"], "id": made.get("id"), "color": made.get("color") or spec["color"]})
        try:
            _write_cache(project, "labels", api.labels())
        except BoardUnavailable:
            pass
    return {"workspace": project.workspace, "board_id": project.board_id, "key_source": source,
            "present": present, "missing": missing, "created": created, "confirmed": confirm}


def ensure_labels_cmd(args) -> int:
    project = load_project(args.project)
    result = ensure_labels(project, bool(args.confirm))
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"board     {result['workspace']} {result['board_id']}  (key from {result['key_source']})")
    for label in result["present"]:
        print(f"present   {label['name']:<14} {label['color'] or ''}  id {label['id']}")
    for label in result["created"]:
        print(f"created   {label['name']:<14} {label['color']}  id {label['id']}")
    remaining = [m for m in result["missing"] if m["name"] not in {c["name"] for c in result["created"]}]
    for label in remaining:
        print(f"missing   {label['name']:<14} {label['color']}  \"{label['description']}\"")
    if remaining and not result["confirmed"]:
        print(f"plan      {len(remaining)} label(s) would be created; re-run with --confirm to write them")
    elif not remaining:
        print("plan      nothing to do; both labels exist")
    return 0
