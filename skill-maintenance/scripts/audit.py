#!/usr/bin/env python3
"""Read-only skill inventory; no skill text, credential values, or commands emitted."""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote
import yaml

SKIP = {'.git', 'node_modules', '__pycache__', 'references', 'reference', 'scripts', 'assets', 'tests'}


def unfenced(text):
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            mark = match.group(1)
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return '\n'.join(lines)


def inventory(root):
    root = Path(root).expanduser().absolute()
    entries, findings = [], []

    def walk(path, ancestors):
        try:
            stat = path.stat()
        except OSError:
            findings.append({'code': 'BROKEN_PATH', 'path': str(path)})
            return
        if not path.is_dir():
            return
        identity = (stat.st_dev, stat.st_ino)
        if identity in ancestors:
            findings.append({'code': 'DIRECTORY_CYCLE', 'path': str(path)})
            return
        entry = path / 'SKILL.md'
        if entry.is_file():
            read(entry)
            return
        try:
            children = sorted(path.iterdir())
        except OSError:
            findings.append({'code': 'UNREADABLE_DIRECTORY', 'path': str(path)})
            return
        for child in children:
            if child.name not in SKIP and (child.is_dir() or child.is_symlink()):
                walk(child, ancestors | {identity})

    def read(path):
        try:
            raw = path.read_bytes()
            text = raw.decode('utf-8-sig')
            match = re.match(r'\A---\s*\n(.*?)\n---(?:\s*\n|$)', text, re.S)
            meta = yaml.safe_load(match.group(1)) if match else None
            if not isinstance(meta, dict) or not isinstance(meta.get('name'), str) or not isinstance(meta.get('description'), str):
                raise ValueError('invalid metadata')
        except (OSError, UnicodeError, ValueError, yaml.YAMLError):
            findings.append({'code': 'INVALID_ENTRYPOINT', 'path': str(path)})
            return
        entries.append({'name': meta['name'], 'path': str(path), 'source': str(path.resolve()),
                        'sha256': hashlib.sha256(raw).hexdigest(), 'words': len(text.split()),
                        'description_words': len(meta['description'].split())})
        # Frontmatter and fenced code are data, not dependency declarations.
        prose = unfenced(text[match.end():])
        for target in re.findall(r'\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)', prose):
            target = unquote(target.strip('<>').split('#')[0])
            if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', target):
                continue
            if any(char in target for char in ('<', '>', '{', '}', '$', '*')):
                continue
            dest = Path(target).expanduser()
            if not dest.is_absolute():
                dest = path.parent / dest
            if not dest.exists():
                findings.append({'code': 'MISSING_LINK', 'path': str(path), 'target': target})

    walk(root, set())
    names = defaultdict(list)
    for entry in entries:
        names[entry['name']].append(entry['path'])
    for name, paths in sorted(names.items()):
        if len(paths) > 1:
            findings.append({'code': 'DUPLICATE_NAME', 'name': name, 'paths': paths})
    return {'root': str(root), 'entrypoints': len(entries),
            'words': sum(e['words'] for e in entries),
            'description_words': sum(e['description_words'] for e in entries),
            'entries': entries, 'findings': findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--check', action='store_true', help='exit 1 when structural findings exist')
    args = parser.parse_args()
    result = inventory(args.root)
    print(json.dumps(result, indent=2))
    return int(args.check and bool(result['findings']))


if __name__ == '__main__':
    sys.exit(main())
