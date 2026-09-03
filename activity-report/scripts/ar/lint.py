"""Refuse a raw.txt before anything downstream sees it.

Runs on the text the agent wrote, in the agent's loop (`activity-report lint`
is in its tool grant), so a refusal costs one more turn instead of a failed
emit at 03:00. It is at least as strict as the Bloodbank validator on text
(the same sha and path regexes, the same ticket-key shape) and stricter for
the external audience: the old publish script's markers (burndown, tool-call
counts) plus sprint numbers, "refactor", agent names, configured banned terms
and the titles of internal-only tickets from `<label>-external.lint.json`.

Findings carry a level, a rule name, an excerpt and a line. Exit 3 on any
error; `--warnings-as-errors` promotes warnings.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass

from .common import (
    AGENT_NAMES, AUDIENCES, EXIT_ACCEPTANCE, EXIT_OK, AcceptanceError, ConfigError,
    SkillError, read_json,
)
from .contract import CAPS, NO_ABSOLUTE_PATH_RE, _PROJECT_ABS_PATH, _PROJECT_SHA
from .render import split_raw

TITLE_LIMIT = CAPS["title"]      # 180, portal upsertUpdateInputSchema and the schema agree
TITLE_MIN = 2                    # portal: title.trim().min(2)
BODY_LIMIT = CAPS["raw"]         # 5000, the portal bound; never widen

PLACEHOLDER_WORD_RE = re.compile(r"\b(TODO|TKTK|XXX)\b", re.I)
PLACEHOLDER_SUBSTRINGS = ("<placeholder>", "{{", "lorem ipsum")
HTML_TAG_RE = re.compile(r"<[A-Za-z][^<>]*>")

# A title paraphrase counts when this many consecutive distinctive title
# tokens (at least DISTINCTIVE_MIN_LEN chars, not a stopword) appear in order
# on one line. Tunable; titles with fewer distinctive tokens are only caught
# verbatim.
DISTINCTIVE_MIN_LEN = 5
DISTINCTIVE_RUN = 3
STOPWORDS = frozenset("""
about above across after again against along already although always among another anyone
anything around because before being below between could doing during either every everything
first further having might neither never nothing often other others rather really shall should
since still their there these thing things those though through toward towards under until
using where whether which while whose without within would
""".split())

EXTERNAL_RULES: tuple[tuple[str, re.Pattern, str], ...] = (
    ("sha", _PROJECT_SHA, "a commit sha"),
    ("abs-path", _PROJECT_ABS_PATH, "an absolute filesystem path"),
    ("abs-path", NO_ABSOLUTE_PATH_RE, "an absolute filesystem path"),
    ("burndown", re.compile(r"\bburn ?down\b", re.I), "burndown language"),
    ("tool-calls", re.compile(r"\btool calls?\b", re.I), "an agent tool-call count"),
    ("sprint-number", re.compile(r"\bsprint \d+\b", re.I), "a sprint number"),
    ("refactor", re.compile(r"\bwe refactored\b|\brefactor(ed|ing)?\b", re.I), "\"refactor\" (say what changed for the reader)"),
    ("agent-name", re.compile(r"\b(" + "|".join(re.escape(n) for n in AGENT_NAMES) + r")\b", re.I), "an agent name"),
)


@dataclass
class Finding:
    level: str          # "error" | "warning"
    rule: str
    excerpt: str
    line: int | None = None

    def as_dict(self) -> dict:
        return asdict(self)


# -- helpers -------------------------------------------------------------------

def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _distinctive(text: str, min_len: int = DISTINCTIVE_MIN_LEN) -> list[str]:
    return [t for t in _tokens(text) if len(t) >= min_len and t not in STOPWORDS]


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _excerpt(line: str, start: int, end: int, context: int = 32) -> str:
    lo, hi = max(0, start - context), min(len(line), end + context)
    return ("…" if lo else "") + line[lo:hi] + ("…" if hi < len(line) else "")


def _in_order(needles: list[str], haystack: list[str]) -> bool:
    pos = 0
    for needle in needles:
        try:
            pos = haystack.index(needle, pos) + 1
        except ValueError:
            return False
    return True


def _title_paraphrased(title: str, line_tokens: list[str]) -> bool:
    run = _distinctive(title)
    if len(run) < DISTINCTIVE_RUN:
        return False
    return any(_in_order(run[i:i + DISTINCTIVE_RUN], line_tokens) for i in range(len(run) - DISTINCTIVE_RUN + 1))


# -- the linter ----------------------------------------------------------------

def lint(raw_text: str, audience: str, project_identifier: str | None, config_lint: dict | None,
         digest: dict | None = None, lint_json: dict | None = None) -> list[Finding]:
    if audience not in AUDIENCES:
        raise ConfigError(f"audience must be internal or external, got {audience!r}")
    config_lint = config_lint or {}
    findings: list[Finding] = []
    text = raw_text.lstrip("﻿").replace("\r\n", "\n")
    lines = text.split("\n")

    try:
        title, body = split_raw(text)
    except AcceptanceError as exc:
        findings.append(Finding("error", "title-line", str(exc), 1))
        title, body = "", text.strip()

    if title and len(title) < TITLE_MIN:
        findings.append(Finding("error", "title-length", f"title is {len(title)} chars, the portal needs {TITLE_MIN}", 1))
    if len(title) > TITLE_LIMIT:
        findings.append(Finding("error", "title-length", f"title is {len(title)} chars, cap is {TITLE_LIMIT}", 1))
    if not body:
        findings.append(Finding("error", "body-empty", "body is empty (line 1 is the title; the update goes below it)", None))
    if len(body) > BODY_LIMIT:
        findings.append(Finding(
            "error", "body-length",
            f"body is {len(body)} chars, cap is {BODY_LIMIT}. Cut the least load-bearing detail; the cap is the portal's and is never raised",
            None))

    # Per-line rules, so every finding names a line.
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        hit = PLACEHOLDER_WORD_RE.search(line)
        if hit:
            findings.append(Finding("error", "placeholder", _excerpt(line, hit.start(), hit.end()), number))
        low = line.lower()
        for token in PLACEHOLDER_SUBSTRINGS:
            at = low.find(token)
            if at != -1:
                findings.append(Finding("error", "placeholder", _excerpt(line, at, at + len(token)), number))
        if number > 1:
            tag = HTML_TAG_RE.search(line)
            if tag:
                findings.append(Finding("warning", "html-tag",
                                        f"{_excerpt(line, tag.start(), tag.end())} (the portal renders tags literally)", number))

    # -- external-only: nothing internal may reach the client -----------------
    identifiers: list[str] = []
    for candidate in [project_identifier, *(config_lint.get("extra_identifiers") or []),
                      *((lint_json or {}).get("identifiers") or []),
                      ((digest or {}).get("project") or {}).get("identifier")]:
        if isinstance(candidate, str) and candidate and candidate not in identifiers:
            identifiers.append(candidate)

    if audience == "external":
        rules: list[tuple[str, re.Pattern, str]] = [
            ("ticket-key", re.compile(r"\b" + re.escape(ident) + r"-\d+\b", re.I), f"a {ident} ticket key")
            for ident in identifiers
        ]
        rules += list(EXTERNAL_RULES)
        for term in config_lint.get("banned_terms") or []:
            if isinstance(term, str) and term.strip():
                rules.append(("banned-term", re.compile(r"(?<!\w)" + re.escape(term.strip()) + r"(?!\w)", re.I),
                              f"the banned term {term.strip()!r}"))
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            seen_rules: set[str] = set()
            for rule, pattern, what in rules:
                if rule in seen_rules and rule != "ticket-key":
                    continue
                hit = pattern.search(line)
                if hit:
                    seen_rules.add(rule)
                    findings.append(Finding("error", rule, f"{what}: {_excerpt(line, hit.start(), hit.end())}", number))
        if not identifiers:
            findings.append(Finding("warning", "no-identifier",
                                    "no project identifier known; ticket keys were not checked", None))
        if lint_json is None:
            findings.append(Finding("warning", "no-lint-json",
                                    "no <label>-external.lint.json; internal-only ticket titles were not checked", None))
        else:
            denied = [d for d in (lint_json.get("denied_titles") or []) if isinstance(d, str) and d.strip()]
            for denied_title in denied:
                needle = _norm(denied_title)
                for number, line in enumerate(lines, start=1):
                    if not line.strip():
                        continue
                    if len(needle) >= 2 and needle in _norm(line):
                        findings.append(Finding("error", "denied-title",
                                                f"names an internal-only ticket verbatim ({denied_title!r})", number))
                    elif _title_paraphrased(denied_title, _tokens(line)):
                        findings.append(Finding("error", "denied-title",
                                                f"paraphrases an internal-only ticket ({denied_title!r}): {_excerpt(line, 0, len(line))}",
                                                number))

    # -- surface_always: the tickets the reader must hear about ----------------
    wanted: dict[str, str] = {}
    for item in (lint_json or {}).get("surface_always") or []:
        if isinstance(item, dict) and item.get("key"):
            wanted[str(item["key"])] = str(item.get("title") or "")
    for ticket in ((digest or {}).get("board") or {}).get("tickets") or []:
        if isinstance(ticket, dict) and ticket.get("surface") == "always" and ticket.get("key"):
            wanted.setdefault(str(ticket["key"]), str(ticket.get("title") or ""))
    haystack = f"{title}\n{body}"
    hay_tokens = set(_tokens(haystack))
    for key, ticket_title in wanted.items():
        if key in haystack:
            continue
        run = _distinctive(ticket_title) or _distinctive(ticket_title, 3)
        if not run:
            continue
        if not any(t in hay_tokens for t in run):
            findings.append(Finding("warning", "surface-always",
                                    f"{key} ({ticket_title!r}) must be surfaced and nothing in the text mentions it", None))

    order = {"error": 0, "warning": 1}
    findings.sort(key=lambda f: (order[f.level], f.line if f.line is not None else 10 ** 6))
    return findings


# -- command -------------------------------------------------------------------

def _load_lint_json(args, digest: dict | None) -> dict | None:
    if args.lint_json:
        if not os.path.exists(args.lint_json):
            raise ConfigError(f"--lint-json {args.lint_json} does not exist (collect --audience external writes it)")
        return read_json(args.lint_json)
    if args.audience != "external" or not args.digest:
        return None
    label = (digest or {}).get("label")
    candidate = os.path.join(os.path.dirname(os.path.abspath(args.digest)), f"{label}-external.lint.json")
    if not os.path.exists(candidate):
        raise ConfigError(
            f"external lint needs {candidate} (collect --audience external writes it, "
            "even when nothing is denied); pass --lint-json to point elsewhere")
    return read_json(candidate)


def lint_cmd(args) -> int:
    with open(args.raw, encoding="utf-8") as fh:
        raw_text = fh.read()
    digest = read_json(args.digest) if args.digest else None
    if digest and digest.get("audience") not in (None, args.audience):
        raise ConfigError(f"digest {args.digest} is for audience {digest.get('audience')!r}, "
                          f"lint asked for {args.audience!r}")
    lint_json = _load_lint_json(args, digest)

    identifier = ((digest or {}).get("project") or {}).get("identifier")
    config_lint: dict | None = None
    try:
        from .config import load_project
        project = load_project(getattr(args, "project", None))
        config_lint = dict((project.config or {}).get("lint") or {})
        identifier = identifier or project.identifier
    except SkillError:
        from .config import DEFAULTS
        config_lint = dict(DEFAULTS.get("lint") or {})

    findings = lint(raw_text, args.audience, identifier, config_lint, digest=digest, lint_json=lint_json)
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    failed = bool(errors) or (bool(warnings) and getattr(args, "warnings_as_errors", False))

    if getattr(args, "json", False):
        print(json.dumps({"audience": args.audience, "ok": not failed, "errors": len(errors),
                          "warnings": len(warnings), "findings": [f.as_dict() for f in findings]}, indent=2))
    else:
        for f in findings:
            where = f"line {f.line}" if f.line is not None else ""
            print(f"{f.level:<8} {f.rule:<15} {where:<9} {f.excerpt}")
        verdict = "refused" if failed else "ok"
        print(f"lint: {verdict} ({args.audience}, {len(errors)} error{'s' if len(errors) != 1 else ''}, "
              f"{len(warnings)} warning{'s' if len(warnings) != 1 else ''})")
    return EXIT_ACCEPTANCE if failed else EXIT_OK
