#!/usr/bin/env python3
"""Read-only installed Momo source parity receipt."""
import hashlib
import json
from pathlib import Path
import sys
canonical=Path(__file__).resolve().parents[1]/'SKILL.md'
installed=Path(sys.argv[1]).resolve()
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a,b=digest(canonical),digest(installed)
print(json.dumps({'version':2,'canonical':str(canonical),'installed':str(installed),'canonical_sha256':a,'installed_sha256':b,'matches':a==b}))
raise SystemExit(0 if a==b else 1)
