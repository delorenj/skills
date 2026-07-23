"""Shared secret detection, redaction, and URL policy."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

TOKEN_PATTERNS = [
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(
        r"(?i)\b(?:api[_ -]?key|token|secret|password|authorization)\s*[:=]\s*['\"]?[^\s'\"&,]{8,}"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
]


def contains_secret(value: Any) -> bool:
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in TOKEN_PATTERNS)
    if isinstance(value, dict):
        return any(contains_secret(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_secret(item) for item in value)
    return False


def redact_text(value: str) -> str:
    redacted = value
    for pattern in TOKEN_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    redacted = re.sub(r"(?i)(https?://)[^/@\s:]+:[^/@\s]+@", r"\1[REDACTED]@", redacted)
    redacted = re.sub(
        r"(?i)((?:token|secret|password|api.?key)=)[^&\s]+", r"\1[REDACTED]", redacted
    )
    return redacted


def is_safe_https_url(value: Any, *, allow_query: bool = False) -> bool:
    if not isinstance(value, str) or contains_secret(value):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and not parsed.username
        and not parsed.password
        and (allow_query or not parsed.query)
    )
