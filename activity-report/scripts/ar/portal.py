"""The portal adapter: one `portal_project_updates` row per (project, window end, visibility).

Adapter `automatic-ai` (`config.portal.kind`), the AutomaticAI client portal's
D1 database. The portal reads the row directly and `visible_to_client` is the
whole boundary between what the client reads and what only the team reads, so
the write is followed by a read-back that asserts the flag.

Access is the Cloudflare GLOBAL key over the REST query endpoint (both scoped
tokens fail: one is IP-locked, the other has no D1 scope). The email and the
key are resolved from op:// references at call time (SECRET_RESOLVER) and never
written anywhere. The account, the database and both references belong to the
HOST, not this file: they come from the environment or ~/.config/33god/host.env,

  ACTIVITY_REPORT_PORTAL_CF_ACCOUNT      Cloudflare account id
  ACTIVITY_REPORT_PORTAL_D1_DATABASE     the portal's D1 database id
  ACTIVITY_REPORT_PORTAL_CF_EMAIL_REF    op:// ref of the account email
  ACTIVITY_REPORT_PORTAL_CF_KEY_REF      op:// ref of the global API key

and a host that declares none of them has no portal (a ConfigError, only reached
when a project's config names one).

`--dry-run` builds and prints the row and runs one read-only SELECT to prove
the access path. `portal: null` in the project config means this project has
no portal: print so and exit 0.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid

from . import __version__
from .common import (
    AUDIENCES, EXIT_OK, AcceptanceError, ConfigError, SourceUnavailable, parse_iso, read_json,
    to_iso_z, utc_now,
)
from .hostenv import HostEnvError, SecretError, host_value, resolve_secret
from .contract import UUID_RE

ADAPTER = "automatic-ai"
HOST_KEYS = {
    "account": "ACTIVITY_REPORT_PORTAL_CF_ACCOUNT",
    "database": "ACTIVITY_REPORT_PORTAL_D1_DATABASE",
    "email_ref": "ACTIVITY_REPORT_PORTAL_CF_EMAIL_REF",
    "key_ref": "ACTIVITY_REPORT_PORTAL_CF_KEY_REF",
}
# Cloudflare answers 403 (error 1010) to urllib's default agent on some paths.
USER_AGENT = f"activity-report/{__version__}"
# Same namespace as the daily-update publisher, so a re-run of a window
# overwrites its row instead of appending a second one.
NAMESPACE = uuid.UUID("6f9b1f1e-5d2a-4a3b-9c8d-1a2b3c4d5e6f")
KIND = "status"
TITLE_MIN, TITLE_MAX, BODY_MAX = 2, 180, 5000   # upsertUpdateInputSchema, never widened
TIMEOUT = 45

UPSERT_SQL = """
INSERT INTO portal_project_updates
    (id, project_id, kind, title, body, pinned, visible_to_client,
     occurred_at, created_at, updated_at)
VALUES (?1, ?2, ?3, ?4, ?5, 0, ?6, ?7, ?8, ?8)
ON CONFLICT(id) DO UPDATE SET
    kind = excluded.kind,
    title = excluded.title,
    body = excluded.body,
    visible_to_client = excluded.visible_to_client,
    occurred_at = excluded.occurred_at,
    updated_at = excluded.updated_at
"""
READ_SQL = "SELECT id, visible_to_client, length(body) AS n, title FROM portal_project_updates WHERE id = ?1"


def host_settings() -> dict:
    """This host's portal coordinates; ConfigError names every key that is unset."""
    try:
        values = {name: host_value(key) for name, key in HOST_KEYS.items()}
    except HostEnvError as exc:
        raise ConfigError(str(exc)) from exc
    missing = [HOST_KEYS[name] for name, value in values.items() if not value]
    if missing:
        raise ConfigError("this host has no portal: set " + ", ".join(missing)
                          + " in the environment or the host.env overlay")
    return values


def endpoint(settings: dict) -> str:
    return (f"https://api.cloudflare.com/client/v4/accounts/{settings['account']}"
            f"/d1/database/{settings['database']}/query")


def read_secret(ref: str) -> str:
    """The value behind an op:// ref (SECRET_RESOLVER: op, then the interim store)."""
    try:
        return resolve_secret(ref, timeout=60)
    except (SecretError, HostEnvError) as exc:
        raise ConfigError(str(exc)) from exc


def d1_query(sql: str, params: list) -> list[dict]:
    """POST one statement; return its rows. Credentials are resolved here, per call."""
    settings = host_settings()
    body = json.dumps({"sql": sql, "params": params}).encode("utf-8")
    req = urllib.request.Request(
        endpoint(settings), data=body, method="POST",
        headers={
            "X-Auth-Email": read_secret(settings["email_ref"]),
            "X-Auth-Key": read_secret(settings["key_ref"]),
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as err:
        raise ConfigError(f"D1 HTTP {err.code}: {err.read()[:400].decode(errors='replace')}") from err
    except (urllib.error.URLError, OSError) as err:
        raise SourceUnavailable(f"D1 endpoint unreachable: {err}") from err
    if not payload.get("success"):
        raise ConfigError(f"D1 refused the statement: {json.dumps(payload.get('errors'))[:400]}")
    result = payload.get("result") or []
    return list((result[0].get("results") if result else None) or [])


def visibility(audience: str) -> str:
    return "client" if audience == "external" else "internal"


def row_id(project_id: str, window_end: str, audience: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{project_id}:{window_end}:{visibility(audience)}"))


def portal_config(project) -> dict | None:
    portal = (getattr(project, "config", None) or {}).get("portal")
    if not portal:
        return None
    kind = portal.get("kind") or ADAPTER
    if kind != ADAPTER:
        raise ConfigError(f"activity_report.portal.kind {kind!r} is not supported; only {ADAPTER!r} is")
    project_id = str(portal.get("project_id") or "")
    if not UUID_RE.match(project_id):
        raise ConfigError("activity_report.portal.project_id must be the portal's project uuid")
    return {"kind": kind, "project_id": project_id}


def build_row(event_data: dict, project) -> dict:
    portal = portal_config(project)
    if portal is None:
        raise ConfigError("no portal configured")
    slug = (event_data.get("project") or {}).get("slug")
    if slug != project.slug:
        raise ConfigError(f"event is for project {slug!r}, portal target is {project.slug!r}")
    audience = event_data.get("audience")
    if audience not in AUDIENCES:
        raise ConfigError(f"event audience must be internal or external, got {audience!r}")
    report = event_data.get("report") or {}
    title = str(report.get("title") or "").strip()
    body = str(report.get("raw") or "").strip()
    if not TITLE_MIN <= len(title) <= TITLE_MAX:
        raise AcceptanceError(f"portal title must be {TITLE_MIN}..{TITLE_MAX} chars, got {len(title)}")
    if not body:
        raise AcceptanceError("portal body is empty")
    if len(body) > BODY_MAX:
        raise AcceptanceError(f"portal body is {len(body)} chars, cap is {BODY_MAX} (the admin console cannot edit past it)")
    window_end = to_iso_z(parse_iso(event_data["window"]["end"]))
    return {
        "id": row_id(portal["project_id"], window_end, audience),
        "project_id": portal["project_id"],
        "kind": KIND,
        "title": title,
        "body": body,
        "pinned": 0,
        "visible_to_client": 1 if audience == "external" else 0,
        "occurred_at": int(parse_iso(window_end).timestamp() * 1000),
    }


def _printable(row: dict) -> dict:
    return {k: (f"<{len(v)} chars, {len(v.splitlines())} lines>" if k == "body" else v) for k, v in row.items()}


def publish(event_data: dict, project, dry_run: bool) -> dict:
    if portal_config(project) is None:
        print("no portal configured")
        return {"skipped": "no portal configured"}
    row = build_row(event_data, project)
    if dry_run:
        print("[dry-run] portal_project_updates row (nothing written):")
        print(json.dumps(_printable(row), indent=2))
        existing = d1_query(READ_SQL, [row["id"]])
        state = f"row exists ({existing[0].get('n')} chars, visible_to_client={existing[0].get('visible_to_client')})" \
            if existing else "no row yet"
        print(f"[dry-run] read-only SELECT ok: {state} for id {row['id']}")
        return {"dry_run": True, "row": row, "existing": existing[0] if existing else None}

    now_ms = int(utc_now().timestamp() * 1000)
    d1_query(UPSERT_SQL, [row["id"], row["project_id"], row["kind"], row["title"], row["body"],
                          row["visible_to_client"], row["occurred_at"], now_ms])
    got = d1_query(READ_SQL, [row["id"]])
    if not got:
        raise AcceptanceError(f"wrote portal row {row['id']} but could not read it back")
    if int(got[0].get("visible_to_client", -1)) != row["visible_to_client"]:
        raise AcceptanceError(f"portal row {row['id']} has visible_to_client={got[0].get('visible_to_client')}, "
                              f"wanted {row['visible_to_client']}")
    print(f"published {event_data['audience']} update ({got[0].get('n')} chars) -> {row['id']} "
          f"visible_to_client={row['visible_to_client']}")
    return {"dry_run": False, "row": row, "verified": got[0]}


def portal_cmd(args) -> int:
    from .config import load_project
    project = load_project(getattr(args, "project", None))
    event_data = read_json(args.event)
    result = publish(event_data, project, bool(args.dry_run))
    if getattr(args, "json", False):
        print(json.dumps({k: (_printable(v) if k == "row" else v) for k, v in result.items()}, indent=2))
    return EXIT_OK
