"""The run orchestration: collect, aggregate, narrate, publish, emit, mirror.

Four steps, in this order, and every one of them ends by writing down what
actually happened rather than what was supposed to happen.

COLLECT
    Every enabled section is dispatched through ``collectors.base.run_collector``,
    so a collector that raises becomes a ``failed`` artifact and the run
    continues. Each artifact is written to ``<artifact_dir>/<date>/sections/<id>.json``.

MANIFEST
    Expected sections are enumerated **from config**, never by listing the
    sections directory. This is the single most important rule in the package:
    the predecessor design enumerated files, so a section that was never written
    silently disappeared and the report looked complete. Each expected section
    resolves to complete / partial / missing / invalid / stale / failed by
    reading the file back off disk -- a section that failed to write is caught
    here, not assumed away.

NARRATE
    One LLM call over the manifest plus the artifacts, field-allowlisted and
    capped. The narrator writes prose; it cannot change a status. On any failure
    the deterministic render runs and the report degrades to ``partial``.

PUBLISH
    ``archive_report`` stages a full generation, fsyncs it, and renames it into
    ``generations/<id>``. It is then *verified while nothing points at it*, and
    ``current.json`` is swapped only if that proof passes. A crash at any point
    leaves ``current.json`` pointing at the previous good generation, and so does
    a run whose report this package will not stand behind: the failed generation
    stays on disk, unreferenced, for debugging, and the run reports its own
    failure (failed status, non-zero exit, the gate's reasons in its caveats).
    Ordering the swap before the proof made a bad re-run a one-way door out of a
    good day -- see ``reportctl_archive.publish_gated_generation``. Afterwards the
    report is mirrored into the git-tracked
    ``_bmad-output/daily-journals/<date>/`` and one Bloodbank event is emitted
    whose statuses are derived from the manifest.

Status derivation, which is the whole point of the merge:

    complete  <=>  every enabled section is complete
    failed    <=>  no section reached complete, OR a REQUIRED section did not
    partial   <=>  otherwise (only optional sections are degraded)

A non-required section that fails degrades the report to ``partial`` but never
to ``failed``. Exit code is 0 for complete and partial, non-zero for failed, so
a cron agent cannot record success over a dead run -- and because a required
gap is ``failed``, it cannot record success over a run that lost the very
source it was configured to require, either. That was measurable: with
Candystore down, the required ``dev-activity`` section died and the run still
exited 0.
"""

from __future__ import annotations

import datetime as dt
import importlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import narrate as narrator  # noqa: E402
from collectors.base import SectionResult, run_collector  # noqa: E402
from reportctl_archive import (  # noqa: E402
    archive_report,
    artifact_health,
    derive_status,
    required_gaps,
    section_path,
    verify_generation,
    verify_published,
)
from reportctl_config import load_json  # noqa: E402
from reportctl_contracts import (  # noqa: E402
    ConfigError,
    active_section_ids,
    required_section_ids,
    validate_daily_report,
    validate_run_manifest,
    validate_section_artifact,
)
from reportctl_runtime import (  # noqa: E402
    archive_paths,
    atomic_write,
    atomic_write_text,
    file_lock,
    fsync_dir,
)

EXIT_OK = 0
EXIT_ERROR = 2
EXIT_UNMET = 3

LEAD_SECTION_ID = "summary"
REPORT_TITLE = "Daily Developer Report"
MAX_REASON_CHARS = 500

#: The git-tracked mirror. Only the current generation's report.md and
#: report.json are copied; generation history stays in the archive.
DEFAULT_MIRROR_DIR = Path("/home/delorenj/code/33GOD/_bmad-output/daily-journals")

DAPR_DEFAULT_PORT = "3504"
DAPR_PUBSUB = "bloodbank-pubsub"
EVENT_SOURCE = "urn:33god:service:delonet-daily-report"
EVENT_PRODUCER = "delonet-daily-report"
EVENT_TIMEOUT_SECONDS = 10

ARTIFACT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
#: Characters a failure summary may contain. The Bloodbank schema rejects
#: absolute paths and credential shapes in this field; excluding "/" and every
#: other punctuation mark structurally is a stronger guarantee than trying to
#: detect them, and it is built by construction rather than by filtering.
SAFE_SUMMARY_RE = re.compile(r"^[A-Za-z0-9 ,.;:()'\-]{1,500}$")
SAFE_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def iso(moment: dt.datetime) -> str:
    return moment.astimezone(dt.UTC).isoformat().replace("+00:00", "Z")


def new_run_id(date: str) -> str:
    return f"ddr-{date}-{uuid.uuid4().hex[:8]}"


def clip(value: Any, limit: int = MAX_REASON_CHARS) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... (clipped from {len(text)} characters)"


def mirror_dir() -> Path:
    override = os.environ.get("DDR_MIRROR_DIR")
    return Path(override).expanduser() if override else DEFAULT_MIRROR_DIR


# --------------------------------------------------------------------------- #
# 1. collect
# --------------------------------------------------------------------------- #


def selected_sections(config: dict[str, Any], wanted: list[str]) -> list[dict[str, Any]]:
    enabled = [section for section in config["sections"] if section["enabled"]]
    if not wanted:
        return enabled
    known = {section["id"] for section in config["sections"]}
    unknown = sorted(set(wanted) - known)
    if unknown:
        raise ConfigError(f"unknown section id(s): {', '.join(unknown)}")
    disabled = sorted(set(wanted) - {section["id"] for section in enabled})
    if disabled:
        raise ConfigError(f"section(s) are disabled in config: {', '.join(disabled)}")
    return [section for section in enabled if section["id"] in set(wanted)]


def collector_callable(section: dict[str, Any], date: str, config: dict[str, Any]):
    """Import and call one collector. Positional call, because that is the one
    calling convention every shipped collector accepts."""
    module_name = f"collectors.{section['collector']}"

    def call(section_cfg: dict[str, Any]) -> SectionResult:
        module = importlib.import_module(module_name)
        entry = getattr(module, "collect", None)
        if not callable(entry):
            raise ConfigError(f"{module_name} does not define collect(section, date, config)")
        return entry(section_cfg, date, config)

    return call


def collect_sections(
    config: dict[str, Any], date: str, wanted: list[str], run_id: str
) -> list[dict[str, Any]]:
    """Run the selected collectors and write their artifacts. Never raises for
    a collector's sake: a crash becomes a ``failed`` artifact on disk."""
    archive_paths(config, date)
    entries: list[dict[str, Any]] = []
    for section in selected_sections(config, wanted):
        result = run_collector(collector_callable(section, date, config), section)
        path = Path(section_path(config, section["id"], date))
        entry: dict[str, Any] = {
            "id": section["id"],
            "required": section["required"],
            "collector": section["collector"],
        }
        try:
            artifact = result.to_artifact(run_id, section["max_age_hours"])
            atomic_write(path, artifact)
            entry.update(
                {
                    "status": artifact["status"],
                    "reason": artifact.get("reason", ""),
                    "path": str(path),
                }
            )
        except ConfigError as exc:
            entry.update({"status": "invalid", "reason": str(exc), "path": None})
        entries.append(entry)
    return entries


# --------------------------------------------------------------------------- #
# 2. manifest
# --------------------------------------------------------------------------- #


def build_manifest(
    config: dict[str, Any], date: str, run_id: str, started_at: dt.datetime
) -> dict[str, Any]:
    """Enumerate expected sections FROM CONFIG and resolve each one from disk."""
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "report_date": date,
        "started_at": iso(started_at),
        "completed_at": iso(now_utc()),
        "sections": [],
    }
    # run_id is passed so an artifact left behind by another run is reported as
    # such instead of being adopted: a published generation must be one run's
    # work, not a composite of whatever was still fresh on disk.
    for health in artifact_health(config, date, run_id):
        entry: dict[str, Any] = {
            "id": health["id"],
            "status": health["status"],
            "path": health["path"] or None,
        }
        reason = clip(health.get("reason") or "")
        if reason:
            entry["reason"] = reason
        manifest["sections"].append(entry)
    validate_run_manifest(manifest, config)
    atomic_write(Path(archive_paths(config, date)["manifest"]), manifest)
    return manifest


def report_plan(config: dict[str, Any]) -> list[dict[str, Any]]:
    """One narrator-written lead, then each enabled collector as reference.

    The four "core sections" this replaces -- executive-brief, key-changes,
    risks-watchlist, coverage-freshness -- were inherited wholesale from the
    predecessor's external-news design and were vestigial here. Measured on a
    real report: they were 30% of the file and their content was the collector
    summaries, printed verbatim, twice, above the collectors that printed them
    a third time.

    ``config["core_sections"]`` is still accepted and still validated; it is no
    longer projected into the document.
    """
    plan = [{"id": LEAD_SECTION_ID, "title": "Summary", "kind": "lead"}]
    plan += [
        {"id": section["id"], "title": section["title"], "kind": "section"}
        for section in config["sections"]
        if section["enabled"]
    ]
    return plan

def section_entries(
    config: dict[str, Any], manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    """Manifest status plus artifact content, per enabled section.

    The manifest status wins. When the artifact is absent or unreadable the
    entry says exactly that instead of leaving a blank the narrator could fill
    with something optimistic.
    """
    titles = {section["id"]: section["title"] for section in config["sections"]}
    entries: list[dict[str, Any]] = []
    for item in manifest["sections"]:
        section_id = item["id"]
        artifact: dict[str, Any] | None = None
        load_error = ""
        path = item.get("path")
        if path:
            try:
                artifact = validate_section_artifact(load_json(Path(path)), section_id)
            except (ConfigError, ValueError, AttributeError) as exc:
                artifact, load_error = None, clip(exc, 200)
        if artifact is None:
            summary = (
                f"No usable artifact for {section_id}: {load_error}"
                if load_error
                else f"No artifact was written for {section_id} during this run."
            )
        else:
            summary = artifact["summary"]
        entries.append(
            {
                "id": section_id,
                "title": titles.get(section_id, section_id),
                "status": item["status"],
                "reason": item.get("reason", "") or (load_error if artifact is None else ""),
                "summary": summary,
                "metrics": (artifact or {}).get("metrics", {}),
                "detail": (artifact or {}).get("detail", []),
                "caveats": (artifact or {}).get("caveats", []),
                "generated_at": (artifact or {}).get("generated_at", ""),
                "fresh_until": (artifact or {}).get("fresh_until", ""),
            }
        )
    return entries


# --------------------------------------------------------------------------- #
# 3. compose
# --------------------------------------------------------------------------- #


def _id_status(section_id: str, status: str) -> str:
    """``<id> (<status>)``, both proven inert before they are exempted."""
    return narrator.render(
        "{id} ({status})",
        id=narrator.certified(section_id, narrator.CERTIFIED_ID),
        status=narrator.certified_status(status),
    )


def coverage_summary(
    config: dict[str, Any], entries: list[dict[str, Any]], overall: str
) -> str:
    """The COVERAGE block, rendered through the same chokepoint as everything else.

    Section ids come from the operator's config and statuses from the manifest,
    so both are certified rather than trusted: a value that does not match its
    pattern is escaped and shows up as the literal text it is.
    """
    complete = [entry["id"] for entry in entries if entry["status"] == "complete"]
    degraded = [entry for entry in entries if entry["status"] != "complete"]
    required = required_section_ids(config)
    lines = [
        narrator.render(
            "{complete} of {total} enabled sections completed.",
            complete=len(complete),
            total=len(entries),
        )
    ]
    if degraded:
        listed = ", ".join(_id_status(item["id"], item["status"]) for item in degraded)
        lines.append(
            narrator.render("Degraded: {listed}.", listed=narrator.Literal(listed))
        )
    else:
        lines.append(narrator.render("No section is degraded."))
    # The per-section table with generated/fresh-until timestamps. It used to
    # live in the `coverage-freshness` core section; retiring those sections
    # would have dropped it from the document, so it lands here -- once, at the
    # end, where the authoritative record belongs.
    lines += ["", narrator.coverage_table(entries)]
    statuses = {entry["id"]: entry["status"] for entry in entries}
    listed = ", ".join(
        _id_status(item, statuses.get(item, "absent")) for item in required
    )
    lines.append(narrator.render("Required: {listed}.", listed=narrator.Literal(listed)))
    lines.append(
        narrator.render(
            "Overall status {overall} is derived from the run manifest above, not asserted.",
            overall=narrator.certified_status(overall),
        )
    )
    return "\n".join(lines)


def compose_report(
    config: dict[str, Any],
    date: str,
    run_id: str,
    plan: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    narration: narrator.Narration,
    overall: str,
) -> dict[str, Any]:
    """Assemble the document: a lead a human reads, then reference material.

    THE FACT SET IS STILL THE SAME ON BOTH PATHS, which is the invariant that
    matters. Every collector section is rendered by the pipeline -- status,
    summary, caveats, detail -- narrated or not, so the narrator can add
    interpretation above but cannot remove, reword, or bury a fact. What changed
    is only *arrangement*: the lead is the narrator's, the reference below it is
    the pipeline's, and each fact appears once instead of three times.

    The lead is published as real Markdown rather than escaped plain text. That
    is a deliberate, narrowed trade. Forgery mattered when eight sections each
    carried a ``Status (authoritative)`` line and a forged ninth was
    indistinguishable; now the authoritative record is ONE pipeline-rendered
    table in a section of its own, and prose above it cannot impersonate a table
    it sits beside. Third-party strings the pipeline interpolates -- commit
    subjects, event project names -- are still escaped wherever the pipeline
    renders them.
    """
    by_id = {entry["id"]: entry for entry in entries}
    sections = []
    for item in plan:
        if item["kind"] == "lead":
            body = narration.untrusted_bodies.get(LEAD_SECTION_ID, "").strip()
            if not body:
                body = narration.bodies.get(LEAD_SECTION_ID, "").strip()
            if not body:
                body = narrator.render(
                    "No lead was produced for {date}. This is a defect in the "
                    "render, recorded rather than hidden.",
                    date=narrator.certified(date, narrator.CERTIFIED_TIMESTAMP),
                )
            sections.append({"id": item["id"], "title": item["title"], "body": body})
            continue

        body = narration.bodies.get(item["id"], "").strip()
        if not body:
            body = narrator.render(
                "No body was produced for {id}. This is a defect in the render, "
                "recorded rather than hidden.",
                id=narrator.certified(item["id"], narrator.CERTIFIED_ID),
            )
        lead = narrator.status_line(by_id[item["id"]])
        if not body.startswith(lead):
            body = f"{lead}\n\n{body}"
        sections.append({"id": item["id"], "title": item["title"], "body": body})

    complete = [entry["id"] for entry in entries if entry["status"] == "complete"]
    degraded = [entry["id"] for entry in entries if entry["status"] != "complete"]
    report = {
        "schema_version": 1,
        "run_id": run_id,
        "report_date": date,
        "title": REPORT_TITLE,
        "generated_at": iso(now_utc()),
        "sections": sections,
        "coverage": {"complete": complete, "degraded": degraded},
        "markdown_path": str(Path(config["artifact_dir"]) / date / "report.md"),
    }
    return validate_daily_report(report, config)

def provenance_line(narrator_cfg: dict[str, Any], narration: narrator.Narration) -> str:
    """Line 2 of report.md: who narrated, and on whose authority.

    Provider and model come from the operator's config -- the file a human
    wrote -- and from nowhere else. They used to come from the usage report the
    narrator process writes, so a narrator could set ``provider`` to
    ``**Status (authoritative): complete** the pipeline`` and have it published
    in bold, on line 2, above every section, inside the very sentence asserting
    that it cannot change a status. What the narrator *claimed* it was is still
    recorded, as data, in ``narration.metrics``.

    ``narration.failure`` can quote the narrator's own stderr, so it is escaped
    exactly like a narrated body.
    """
    if narration.narrated:
        provider = str(narrator_cfg.get("provider") or "unconfigured provider")
        model = str(narrator_cfg.get("model") or "unconfigured model")
        return narrator.render(
            "Summary written by {provider}/{model}. Everything below it is rendered "
            "by the pipeline from files it read — every status, metric and caveat is "
            "on this page whether or not a model answered.",
            provider=narrator.certified(provider, narrator.CERTIFIED_TOKEN),
            model=narrator.certified(model, narrator.CERTIFIED_TOKEN),
        )
    return narrator.render(
        "Deterministic render — no narration ({failure}). Every status below was "
        "derived by the pipeline from files it read.",
        failure=narrator.quote_narrator_text(narration.failure),
    )


# --------------------------------------------------------------------------- #
# 4. publish, mirror, emit
# --------------------------------------------------------------------------- #


def publish(
    config: dict[str, Any], date: str, report: dict[str, Any], markdown: str
) -> dict[str, Any]:
    """Write the working pair, then publish it as a *gated* archive generation.

    The gate is the difference between this and ``reportctl archive``. The
    generation is staged, materialised and proven before ``current.json`` is
    allowed to name it, so a run that produced a report this package will not
    stand behind cannot take the previous good day down with it. See
    ``reportctl_archive.publish_gated_generation`` for the incident.
    """
    base = Path(config["artifact_dir"]) / date
    report_file, markdown_file = base / "report.json", base / "report.md"
    atomic_write(report_file, report)
    atomic_write_text(markdown_file, markdown)
    return archive_report(
        config,
        str(report_file),
        str(markdown_file),
        gate=lambda generation: verify_generation(config, date, generation),
    )


#: The two files the mirror owns. Nothing else in the day directory is ours.
MIRROR_FILES = ("report.json", "report.md")
#: ``atomic_write`` stages through ``tempfile.mkstemp(prefix=f".{name}.")``,
#: which appends exactly eight characters from ``[A-Za-z0-9_]``. A SIGKILL
#: mid-write leaves one of those behind, so the next run sweeps them -- and only
#: them. The pattern is narrow on purpose: it matches what this function
#: provably wrote and nothing an operator, git, or another tool would ever put
#: in a daily-journal directory.
MIRROR_TEMP_RE = re.compile(r"^\.report\.(?:json|md)\.[A-Za-z0-9_]{8}$")


def _sweep_mirror_temps(target: Path) -> None:
    """Delete this function's own leftover temp files. Never raises.

    Called on entry (repairing a previous run that was killed mid-write) and
    again in a ``finally`` (so a handled failure leaves nothing). It removes
    regular files only, and only ones matching the mkstemp name this module
    produces -- a directory, a symlink, a dotfile like ``.gitkeep``, or any file
    the mirror did not write is left exactly as found.
    """
    try:
        entries = list(target.iterdir())
    except OSError:
        return
    for item in entries:
        if not MIRROR_TEMP_RE.fullmatch(item.name):
            continue
        try:
            if item.is_file() and not item.is_symlink():
                item.unlink()
        except OSError:
            pass


def mirror_generation(date: str, verified: dict[str, Any]) -> dict[str, Any]:
    """Install the verified generation's report pair into the git-tracked mirror.

    The mirror is ``_bmad-output/daily-journals/<date>/`` inside the 33GOD
    working tree. That is somebody else's directory: it is version-controlled,
    humans commit into it by hand, and on 2026-08-17 it held ``journal.txt``
    (17811 bytes) and ``report_event.json`` (1766 bytes) that this pipeline
    never wrote. So this function behaves like a well-behaved writer in a shared
    directory rather than like an owner of it.

    Four rules, each of them a defect that was measured before it was fixed.

    *The source is the generation ``current.json`` names.* It used to be the
    paths ``publish()`` returned, so a ``reportctl archive`` landing in the
    meantime left the archive saying one report was current while git got a
    different one.

    *Only a verified generation is mirrored.* The mirror used to be written
    before the verification gate, so a run that exited as ``failed`` still left
    a document in git claiming ``partial``, with nothing in the mirrored pair
    recording the failure. This is the one artifact a human actually reads; it
    is the last place a false green may appear.

    *Both files are written IN PLACE, and nothing else is touched.* The previous
    attempt to make the pair atomic staged a whole new day directory and swapped
    it in by renaming directories. That bought atomicity with data loss: the
    swap replaced the entire directory, so ``journal.txt`` and
    ``report_event.json`` -- files nobody here wrote -- were deleted on every
    successful run; a SIGKILL between the two renames left no day directory at
    all; and a SIGKILL during staging stranded a ``.stage-<uuid>`` corpse
    holding a mode-0600 half-written report in a git-tracked tree, forever.
    So: ``mkdir(exist_ok=True)`` on the destination and two ``atomic_write``
    calls into it. The day directory is never created as a replacement, never
    renamed, never removed; no file outside :data:`MIRROR_FILES` is read,
    written, or unlinked.

    *A torn pair is accepted here, deliberately, and reported.* If the second
    write fails the mirror holds a new ``report.json`` beside an older
    ``report.md``. That is the right trade in THIS directory and it is not to be
    "fixed" back into a directory swap: the archive is the source of truth, git
    shows the diff, the tear is named in ``outcome["error"]`` and in the run's
    caveats, and the next run overwrites both files. Losing a hand-committed
    journal is not repairable by any of those things. The order is fixed --
    ``report.json`` first, then ``report.md`` -- so the tear always has the same
    shape: the machine-readable half, the only one carrying a ``run_id``, is the
    fresh one, which is what makes a tear detectable at all.

    Debris: temp files are swept on entry and in a ``finally``, so a killed run
    is repaired by the next one and a handled failure leaves nothing. Two
    concurrent mirrors of the same date would fight over those temps; they
    already fight over the destination, and the loser fails loudly rather than
    silently, which is the outcome this package prefers.
    """
    base = mirror_dir()
    target = base / date
    outcome: dict[str, Any] = {
        "attempted": True,
        "ok": False,
        "dir": str(target),
        "generation": None,
        "reason": None,
        "error": None,
    }
    generation = verified.get("generation")
    if not verified.get("ok") or not generation:
        outcome["attempted"] = False
        outcome["reason"] = "generation_unverified"
        outcome["error"] = (
            "not mirrored: the published generation did not pass verification "
            + ("(" + "; ".join(verified.get("problems", [])[:3]) + ")" if verified.get("problems")
               else "")
        ).strip()
        return outcome
    source = Path(generation)
    outcome["generation"] = source.name
    installed: list[str] = []
    try:
        markdown = (source / "report.md").read_text(encoding="utf-8")
        report = json.loads((source / "report.json").read_text(encoding="utf-8"))
        target.mkdir(parents=True, exist_ok=True)
        _sweep_mirror_temps(target)
        # atomic_write goes through mkstemp, which creates 0600, and os.replace
        # installs that inode over the old file -- so the mode has to be set on
        # every write, and immediately, not in a loop after both writes. The
        # earlier version chmodded only after both succeeded and left report.md
        # world-unreadable whenever the second write failed.
        atomic_write(target / "report.json", report)
        (target / "report.json").chmod(0o644)
        installed.append("report.json")
        atomic_write_text(target / "report.md", markdown)
        (target / "report.md").chmod(0o644)
        installed.append("report.md")
        fsync_dir(target)
        outcome["ok"] = True
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        outcome["reason"] = "mirror_failed"
        if installed:
            missing = [name for name in MIRROR_FILES if name not in installed]
            outcome["error"] = clip(
                f"mirror pair is torn: {', '.join(installed)} now holds generation "
                f"{source.name} and {', '.join(missing)} does not; the archive is "
                f"authoritative and the next run repairs it ({exc})",
                200,
            )
        else:
            outcome["error"] = clip(exc, 200)
    finally:
        _sweep_mirror_temps(target)
    return outcome


def _artifact_id(candidate: str, fallback: str) -> str:
    return candidate if ARTIFACT_ID_RE.fullmatch(candidate) else fallback


def _safe_summary(text: str, fallback: str) -> str:
    collapsed = " ".join(str(text).split())[:500]
    return collapsed if SAFE_SUMMARY_RE.fullmatch(collapsed) else fallback


def _envelope(event_type: str, date: str, data: dict[str, Any], narration_model: Any) -> dict[str, Any]:
    moment = now_utc()
    action = event_type.rsplit(".", 1)[-1]
    return {
        "specversion": "1.0",
        "id": str(uuid.uuid4()),
        "source": EVENT_SOURCE,
        "type": event_type,
        "subject": f"bloodbank.evt.reporting.report.{action}",
        "time": iso(moment),
        "datacontenttype": "application/json",
        "dataschema": f"apicurio://holyfields/{event_type}/versions/1",
        "correlationid": str(uuid.uuid4()),
        "causationid": None,
        "producer": EVENT_PRODUCER,
        "service": EVENT_PRODUCER,
        "domain": "reporting",
        "kind": "event",
        "schemaref": f"{event_type}.v1",
        "actor": {
            "type": "service",
            "agent_id": "bloodbank.service.delonet-daily-report",
            "cli": "reportctl",
            "provider": None,
            "model": narration_model if isinstance(narration_model, str) else None,
        },
        "ordering_key": f"report:delonet-daily-report:{date}",
        "data": data,
    }


#: The pseudo-section that carries a narration failure into the Bloodbank
#: envelope. See ``completed_event``.
NARRATION_COMPONENT_ID = "report-narration"


def completed_event(
    run_id: str,
    date: str,
    started_at: dt.datetime,
    entries: list[dict[str, Any]],
    published: dict[str, Any],
    generation: str,
    delivery: dict[str, Any],
    narration: narrator.Narration,
    report_status: str,
) -> dict[str, Any]:
    """The report.completed envelope, with every status derived, never assumed.

    The predecessor hardcoded ``outcome.status="complete"`` and four ``"complete"``
    sections on every run. Here ``outcome.status`` is exactly the status of the
    report that was published: ``complete`` only when every enabled section
    completed *and* the report was narrated. The per-section map is read off the
    manifest entries, so a section that is missing, invalid, stale, partial, or
    failed is published as ``degraded``.

    One wrinkle, handled explicitly rather than papered over. The v1 schema makes
    ``outcome.status`` a pure function of the sections map: ``partial`` is only
    valid when at least one section is ``degraded``. So a run whose sections all
    completed but whose narrator died -- published as ``partial`` -- has no
    section to point at. Rather than emit ``complete`` over a report that says
    ``partial``, the degraded narration is named as its own component,
    ``report-narration``. It is not a configured section and never collides with
    one (a real section of that id keeps its own status). The alternative was an
    envelope that claims more than the artifact it describes, which is the exact
    defect this rewrite exists to remove.
    """
    sections = {
        entry["id"]: ("complete" if entry["status"] == "complete" else "degraded")
        for entry in entries
    }
    status = "complete" if report_status == "complete" else "partial"
    if status == "partial" and all(value == "complete" for value in sections.values()):
        sections.setdefault(NARRATION_COMPONENT_ID, "degraded")
    data = {
        "schema_version": 1,
        "run_id": run_id,
        "report_date": date,
        "started_at": iso(started_at),
        "completed_at": iso(now_utc()),
        "outcome": {"status": status, "sections": sections},
        "artifacts": {
            "report_artifact_id": _artifact_id(f"{run_id}:report.json", run_id),
            "markdown_artifact_id": _artifact_id(f"{run_id}:report.md", run_id),
            "commit_marker_id": _artifact_id(f"{date}:{generation}", run_id),
        },
        "delivery": delivery,
    }
    return _envelope(
        "bloodbank.reporting.report.completed",
        date,
        data,
        narration.metrics.get("narrator_reported_model"),
    )


def failed_event(
    run_id: str,
    date: str,
    started_at: dt.datetime,
    phase: str,
    code: str,
    summary: str,
    delivery: dict[str, Any],
    narration: narrator.Narration,
) -> dict[str, Any]:
    data = {
        "schema_version": 1,
        "run_id": run_id,
        "report_date": date,
        "started_at": iso(started_at),
        "failed_at": iso(now_utc()),
        "failure": {
            "phase": phase,
            "code": code if SAFE_CODE_RE.fullmatch(code) else "run_failed",
            "summary": _safe_summary(
                summary, "The daily report run did not succeed. See the run manifest."
            ),
            "retryable": True,
            "redacted": True,
        },
        "delivery": delivery,
    }
    return _envelope(
        "bloodbank.reporting.report.failed",
        date,
        data,
        narration.metrics.get("narrator_reported_model"),
    )


def emit_event(envelope: dict[str, Any]) -> dict[str, Any]:
    """POST one envelope to the local Dapr sidecar. Never raises."""
    port = os.environ.get("DAPR_HTTP_PORT", DAPR_DEFAULT_PORT)
    topic = envelope["subject"]
    url = f"http://127.0.0.1:{port}/v1.0/publish/{DAPR_PUBSUB}/{topic}"
    payload = json.dumps(envelope).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/cloudevents+json",
            "Content-Length": str(len(payload)),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=EVENT_TIMEOUT_SECONDS) as response:
            ok = response.status in {200, 204}
            return {"published": ok, "url": url, "status_code": response.status,
                    "error": None if ok else f"unexpected status {response.status}"}
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"published": False, "url": url, "status_code": None, "error": clip(exc, 200)}


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #


def run_report(
    config: dict[str, Any],
    date: str,
    *,
    run_id: str | None = None,
    wanted: list[str] | None = None,
    narrate_enabled: bool = True,
    emit: bool = True,
    mirror: bool = True,
) -> tuple[dict[str, Any], int]:
    started_at = now_utc()
    run_id = run_id or new_run_id(date)
    paths = archive_paths(config, date)
    lock_path = Path(config["artifact_dir"]) / date / ".run.lock"

    with file_lock(lock_path):
        collected = collect_sections(config, date, wanted or [], run_id)
        manifest = build_manifest(config, date, run_id, started_at)
        statuses = {item["id"]: item["status"] for item in manifest["sections"]}
        overall = derive_status(config, statuses)

        plan = report_plan(config)
        entries = section_entries(config, manifest)
        narration = narrator.narrate(
            date,
            run_id,
            plan,
            entries,
            overall,
            config["narrator"],
            enabled=narrate_enabled and bool(config["narrator"].get("enabled", False)),
        )
        caveats = list(narration.caveats)
        # A report that could not be narrated is not a complete report.
        report_status = overall
        if not narration.narrated and overall == "complete":
            report_status = "partial"
            # The deterministic bodies were built before that was known, so the
            # brief would otherwise state the section coverage as the report's
            # overall status. Re-render them against the status the document is
            # actually published with: one report, one status, stated once.
            narration.bodies = narrator.fallback_bodies(
                plan, entries, report_status, narration.failure
            )

        coverage_text = coverage_summary(config, entries, report_status)
        report = compose_report(config, date, run_id, plan, entries, narration, report_status)
        markdown, render_caveats = narrator.render_markdown(
            report,
            provenance=provenance_line(config["narrator"], narration),
            coverage_text=coverage_text,
            overall_status=report_status,
        )
        caveats.extend(render_caveats)

        outcome: dict[str, Any] = {
            "date": date,
            "run_id": run_id,
            "started_at": iso(started_at),
            "collected": collected,
            "manifest": {"path": paths["manifest"], "sections": statuses},
            "section_status": overall,
            "status": report_status,
            "narration": {
                "mode": narration.mode,
                "failure": narration.failure,
                "metrics": narration.metrics,
            },
            "caveats": caveats,
            "published": None,
            "mirror": None,
            "event": None,
        }

        try:
            published = publish(config, date, report, markdown)
        except (ConfigError, OSError) as exc:
            outcome["publish_error"] = clip(exc, 300)
            outcome["status"] = "failed"
            outcome["caveats"].append(f"publish failed: {outcome['publish_error']}")
            envelope = failed_event(
                run_id, date, started_at, "archive", "archive_publish_failed",
                f"The daily report for {date} was composed but could not be archived. "
                f"Sections complete: {sum(1 for v in statuses.values() if v == 'complete')} "
                f"of {len(statuses)}.",
                {"status": "not_attempted", "channel": None,
                 "destination_alias": None, "attempts": 0},
                narration,
            )
            outcome["event"] = _finish_event(config, date, envelope, emit)
            return outcome, EXIT_ERROR

        # The generation was staged, proven, and only then allowed to become
        # current -- ``publish`` passes the gate. So there are three outcomes
        # here, and they are different facts:
        #
        #   staged["current"] is True   the gate accepted it and current.json
        #                               now names it;
        #   False, coherent             the artifact is fine but the run it
        #                               records is `failed`, so the pointer was
        #                               deliberately left where it was;
        #   False, not coherent         the artifact itself did not read back.
        #
        # Verification is then bound to the generation this run published. It
        # used to resolve whatever current.json pointed at by the time it ran,
        # so a concurrent `reportctl archive` could make a run report
        # `verified: true` about a generation it had never written.
        gate = published.get("gate") or {}
        if published.get("current"):
            verified = verify_published(config, date, expect_generation=published["generation"])
        else:
            verified = dict(gate) or {
                "ok": False,
                "coherent": False,
                "generation": str(Path(published["markdown"]).parent),
                "problems": ["the publication gate returned no verdict"],
            }
            outcome["caveats"].append(
                "current.json was not moved: this run's generation "
                f"{published['generation']} did not pass the publication gate ("
                + "; ".join(verified["problems"][:3])
                + f"), and generation {published['previous_generation']} already "
                f"published for {date} does. The verified report stands; this run's "
                "generation is retained, unreferenced, for debugging."
            )
        outcome["published"] = {
            "generation": published["generation"],
            "markdown": published["markdown"],
            "report_json": published["report_json"],
            "commit_marker": published["commit_marker"],
            # `verified` is about the artifact: this exact generation reads back
            # coherently. `accepted` is about the run: the report it holds is not
            # a failed one. `current` is about the archive: whether current.json
            # was allowed to name it.
            "verified": verified["coherent"],
            "accepted": verified["ok"],
            "current": bool(published.get("current")),
            "previous_generation": published.get("previous_generation"),
            "problems": verified["problems"],
        }

        if not verified["coherent"]:
            outcome["status"] = "failed"
            outcome["mirror"] = {
                "attempted": False, "ok": False, "dir": str(mirror_dir() / date),
                "generation": None, "reason": "generation_unverified",
                "error": "not mirrored: the published generation did not verify",
            }
            outcome["caveats"].append(
                "published generation did not verify: " + "; ".join(verified["problems"][:5])
            )
            envelope = failed_event(
                run_id, date, started_at, "validation", "published_report_invalid",
                f"The daily report for {date} was archived but the published generation "
                "did not verify.",
                {"status": "not_attempted", "channel": None,
                 "destination_alias": None, "attempts": 0},
                narration,
            )
            outcome["event"] = _finish_event(config, date, envelope, emit)
            return outcome, EXIT_ERROR

        # The mirror comes AFTER the gate and reads the generation current.json
        # names, so the git-tracked copy is never a document the pipeline itself
        # refused to certify.
        mirrored = (
            mirror_generation(date, verified)
            if mirror
            else {"attempted": False, "ok": False, "dir": str(mirror_dir() / date),
                  "generation": None, "reason": "mirror_disabled",
                  "error": "mirror skipped by request"}
        )
        outcome["mirror"] = mirrored
        if mirror and not mirrored["ok"]:
            verb = "failed" if mirrored.get("attempted") else "skipped"
            outcome["caveats"].append(f"mirror {verb}: {mirrored['error']}")

        delivery = _delivery_block(mirrored)
        if overall == "failed":
            complete_count = sum(1 for value in statuses.values() if value == "complete")
            gaps = required_gaps(config, statuses)
            if complete_count == 0:
                phase, code = "investigation", "no_section_completed"
                summary = (
                    f"No section completed for {date}. Sections complete: {complete_count} of "
                    f"{len(statuses)}. Degraded: "
                    + ", ".join(sorted(sid for sid, st in statuses.items() if st != "complete"))
                    + "."
                )
            else:
                phase, code = "aggregation", "required_section_incomplete"
                summary = (
                    f"The daily report for {date} did not meet its required coverage. "
                    f"Sections complete: {complete_count} of {len(statuses)}. Required "
                    "section(s) that did not complete: " + ", ".join(gaps) + "."
                )
            envelope = failed_event(
                run_id, date, started_at, phase, code, summary,
                _failed_delivery_block(mirrored),
                narration,
            )
        else:
            envelope = completed_event(
                run_id, date, started_at, entries, published,
                outcome["published"]["generation"], delivery, narration,
                outcome["status"],
            )
        outcome["event"] = _finish_event(config, date, envelope, emit)

    exit_code = EXIT_UNMET if outcome["status"] == "failed" else EXIT_OK
    return outcome, exit_code


def _delivery_block(mirrored: dict[str, Any]) -> dict[str, Any]:
    if mirrored.get("ok"):
        return {
            "status": "delivered",
            "channel": "file",
            "destination_alias": "daily-journals",
            "attempts": 1,
            "delivered_at": iso(now_utc()),
        }
    reason = str(mirrored.get("reason") or "")
    if not SAFE_CODE_RE.fullmatch(reason):
        reason = "mirror_failed" if mirrored.get("attempted") else "mirror_disabled"
    return {
        "status": "skipped",
        "channel": "file",
        "destination_alias": "daily-journals",
        "attempts": 0,
        "delivered_at": None,
        "reason": reason,
    }


def _failed_delivery_block(mirrored: dict[str, Any]) -> dict[str, Any]:
    if mirrored.get("attempted") and not mirrored.get("ok"):
        return {
            "status": "failed",
            "channel": "file",
            "destination_alias": "daily-journals",
            "attempts": 1,
        }
    return {"status": "not_attempted", "channel": None, "destination_alias": None, "attempts": 0}


def _finish_event(
    config: dict[str, Any], date: str, envelope: dict[str, Any], emit: bool
) -> dict[str, Any]:
    """Record the envelope on disk always; publish it only when asked."""
    record: dict[str, Any] = {
        "type": envelope["type"],
        "outcome_status": envelope["data"].get("outcome", {}).get("status"),
        "emitted": False,
        "path": str(Path(config["artifact_dir"]) / date / "report-event.json"),
    }
    try:
        atomic_write(Path(record["path"]), envelope)
    except OSError as exc:
        record["write_error"] = clip(exc, 200)
    if not emit:
        record["skipped"] = "emission skipped by request (--no-emit)"
        return record
    published = emit_event(envelope)
    record["emitted"] = published["published"]
    record["url"] = published["url"]
    record["status_code"] = published["status_code"]
    if published["error"]:
        record["error"] = published["error"]
    return record


def command_run(config: dict[str, Any], args: Any) -> tuple[dict[str, Any], int]:
    return run_report(
        config,
        args.date,
        run_id=getattr(args, "run_id", None),
        wanted=list(getattr(args, "section", []) or []),
        narrate_enabled=not getattr(args, "no_narrate", False),
        emit=not getattr(args, "no_emit", False),
        mirror=not getattr(args, "no_mirror", False),
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    from reportctl_cli import default_date
    from reportctl_config import load_config

    parser = argparse.ArgumentParser(prog="run.py", description="Run one daily report")
    parser.add_argument("--config", required=True)
    parser.add_argument("--date", default=default_date())
    parser.add_argument("--run-id")
    parser.add_argument("--section", action="append", default=[])
    parser.add_argument("--no-narrate", action="store_true")
    parser.add_argument("--no-emit", action="store_true")
    parser.add_argument("--no-mirror", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = load_config(Path(args.config).expanduser())
        outcome, code = command_run(config, args)
    except (ConfigError, OSError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return EXIT_ERROR
    print(json.dumps(outcome, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
