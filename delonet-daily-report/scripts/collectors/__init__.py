"""Deterministic local collectors for the DeLoNET Daily Report.

Every collector module in this package must expose::

    def collect(section: dict, *, date: str, config: dict) -> SectionResult

``section`` is the validated config entry (id, title, collector, required,
enabled, max_age_hours, options). Collectors read local sources only -- git,
localhost HTTP, and files under the user's home. They never fabricate a status:
if a source is unreachable the collector returns ``status="failed"`` with a
reason, and the run degrades around it.
"""
