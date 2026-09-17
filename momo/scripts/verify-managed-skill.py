#!/usr/bin/env python3
"""Read-only complete installed Momo bundle parity receipt."""
import hashlib
import json
from pathlib import Path
import sys

def bundle(root):
    paths=sorted(p for p in root.rglob('*') if p.is_file() and p.suffix in {'.md','.py','.sh'} and '__pycache__' not in p.parts)
    data=''.join(f'{p.relative_to(root).as_posix()}\0{hashlib.sha256(p.read_bytes()).hexdigest()}\n' for p in paths)
    return hashlib.sha256(data.encode()).hexdigest()
canonical=Path(__file__).resolve().parents[1]
installed=Path(sys.argv[1]).resolve()
if installed.is_file(): installed=installed.parent
left,right=bundle(canonical),bundle(installed)
print(json.dumps({'version':2,'canonical':str(canonical),'installed':str(installed),'canonical_bundle_sha256':left,'installed_bundle_sha256':right,'matches':left==right}))
raise SystemExit(0 if left==right else 1)
