#!/usr/bin/env python3
"""Scaffold a side-effect-free enrichment pass and its YAML registry entry.

Invoke directly (no wrapper task); edit the generated files afterwards:
the scaffold only ever creates, never overwrites.
"""

from __future__ import annotations

import argparse
import json
import re
import stat
import sys
from pathlib import Path


# Parity with Wax `src/wax/pipelines.py` NAME_RE (^[a-z][a-z0-9-]*$), which
# also gates n8n import names: a scaffolded slug must start with a letter so
# it can always be named in a pipeline graph without renaming.
SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")

CAPABILITY_ORDER = ("document", "audio")


PASS_TEMPLATE = '''#!/usr/bin/env python3
"""{doc_description}

This executable is intentionally side-effect free. The host runner owns all
metadata writes, renames, state changes, and external links.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


RESULT_VERSION = 1


class EnrichmentError(RuntimeError):
    """Grounded failure carrying a lowercase/underscore reason code."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code


def document_body(text: str) -> str:
    """Remove a leading Markdown frontmatter block without parsing its values."""
    if not text.startswith("---"):
        return text
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "".join(lines[index + 1 :])
    return text


def enrich_document(body: str, *, document: Path, item_id: str = "") -> dict[str, Any]:
    """Return content-derived frontmatter proposals for any text document."""
    if not body.strip():
        raise EnrichmentError("empty_document", f"document has no body: {{document}}")
    # Implement this pass's grounded enrichment here. Do not mutate `document`
    # or call host services from this function.
    return {{}}


def build_result(document: Path, *, item_id: str = "") -> dict[str, Any]:
    try:
        text = document.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        # Codes are lowercase letters and underscores only: the runner's
        # ^reason_code=([a-z_]+)$ header rejects digits.
        raise EnrichmentError("undecodable", f"document is not UTF-8 text: {{document}}") from exc
    updates = enrich_document(document_body(text), document=document, item_id=item_id)
    if not isinstance(updates, dict):
        raise EnrichmentError("invalid_result", "enrich_document must return an object")
    return {{"wax_ep_version": RESULT_VERSION, "frontmatter": updates}}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("item_id", nargs="?", default="")
    return parser.parse_args()


def fail(code: str, detail: str, status: int) -> int:
    # The reason_code header must be the FIRST stderr line: the runner splits
    # it off (^reason_code=([a-z_]+)$) before classifying the failure.
    print(f"reason_code={{code}}", file=sys.stderr)
    print(detail, file=sys.stderr)
    return status


def main() -> int:
    args = parse_args()
    document = args.document.expanduser().resolve()
    if not document.is_file():
        return fail("not_a_file", f"not a document file: {{document}}", 2)
    try:
        result = build_result(document, item_id=args.item_id)
    except OSError as exc:
        return fail("unreadable_document", str(exc), 1)
    except EnrichmentError as exc:
        return fail(exc.code, str(exc), 1)
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def doc_description(description: str) -> str:
    """Escape an arbitrary description for the generated module docstring."""
    return description.replace("\\", "\\\\").replace('"', '\\"')


def registry_template(slug: str, description: str, host: str, capabilities: list[str]) -> str:
    if host == "wax":
        executable = f"{{component_root}}/config/passes.d/bin/{slug}"
        document = "{md_path}"
    else:
        executable = f"bin/{slug}"
        document = "{document_path}"
    # json.dumps output is a valid YAML double-quoted scalar: quotes,
    # backslashes, tabs and newlines all survive a registry round-trip.
    lines = [
        f"slug: {slug}",
        "version: 1",
        f"description: {json.dumps(description, ensure_ascii=False)}",
    ]
    if host == "wax":
        lines.append("capabilities: [" + ", ".join(capabilities) + "]")
    lines += [
        "enabled: false",
        "auto: false",
        "requires: []",
        "clobber: []",
        "timeout_s: 300",
        f'command: ["{executable}", "{document}", "{{item_id}}"]',
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "slug",
        help="pass identifier: starts with a letter, then lowercase letters, digits, hyphens",
    )
    parser.add_argument("--registry-dir", required=True, type=Path)
    parser.add_argument(
        "--host", choices=("generic", "wax"), default="generic",
        help="select registry placeholders; the executable stays document-neutral",
    )
    parser.add_argument(
        "--capability", action="append", choices=CAPABILITY_ORDER, metavar="CAP",
        help="wax only: declare an execution capability; repeat for both "
             "(document, audio). Default: document alone",
    )
    parser.add_argument(
        "--description", default="Derive grounded metadata from any text document",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.capability and args.host != "wax":
        print("--capability only applies to --host wax", file=sys.stderr)
        return 2
    if not SLUG_RE.fullmatch(args.slug):
        print(
            "slug must start with a letter and use only lowercase letters, "
            "digits, and hyphens (Wax pipeline name validation)",
            file=sys.stderr,
        )
        return 2

    # Deduplicate into the canonical declaration order.
    capabilities = [cap for cap in CAPABILITY_ORDER if cap in (args.capability or ["document"])]

    registry_dir = args.registry_dir.expanduser().resolve()
    manifest = registry_dir / f"{args.slug}.yaml"
    executable = registry_dir / "bin" / args.slug
    collisions = [path for path in (manifest, executable) if path.exists()]
    if collisions:
        print("refusing to overwrite: " + ", ".join(map(str, collisions)), file=sys.stderr)
        return 1

    executable.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        registry_template(args.slug, args.description, args.host, capabilities),
        encoding="utf-8",
    )
    executable.write_text(
        PASS_TEMPLATE.format(doc_description=doc_description(args.description)),
        encoding="utf-8",
    )
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(manifest)
    print(executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
