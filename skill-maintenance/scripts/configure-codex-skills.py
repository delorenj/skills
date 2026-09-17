#!/usr/bin/env python3
"""Apply explicit path exclusions through Codex's own skill configuration API."""
from collections import Counter
import argparse
import json
import selectors
import subprocess
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--verify', action='store_true', help='reload discovery and check exclusions')
    parser.add_argument('--cwd', default=str(Path.cwd()))
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text())
    paths = policy.get('disabled_paths', [])
    if policy.get('version') != 1 or not isinstance(paths, list) or not all(
        isinstance(p, str) and Path(p).is_absolute() and Path(p).name == 'SKILL.md'
        for p in paths
    ):
        parser.error('Expected version 1 and absolute SKILL.md disabled_paths')
    paths = sorted(set(paths))
    if not args.apply and not args.verify:
        print(json.dumps({'action': 'disable', 'paths': paths, 'apply': False}, indent=2))
        return
    proc = subprocess.Popen(['codex', 'app-server'], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True, bufsize=1)
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ)

    def call(number, method, params):
        proc.stdin.write(json.dumps({'id': number, 'method': method, 'params': params}) + '\n')
        proc.stdin.flush()
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if not selector.select(1):
                continue
            line = proc.stdout.readline()
            if not line:
                raise RuntimeError('Codex app-server closed the connection')
            response = json.loads(line)
            if response.get('id') == number:
                if 'error' in response:
                    raise RuntimeError(f'{method} failed; inspect the installed protocol')
                return response['result']
        raise TimeoutError(method)

    try:
        call(1, 'initialize', {'clientInfo': {'name': 'skill-maintenance', 'version': '1'}})
        proc.stdin.write('{"method":"initialized"}\n')
        proc.stdin.flush()
        number = 2
        if args.apply:
            for path in paths:
                call(number, 'skills/config/write', {'path': path, 'enabled': False})
                number += 1
            print(json.dumps({'disabled_paths': len(paths), 'owner': 'codex skills/config/write'}))
        if args.verify:
            result = call(number, 'skills/list', {'cwds': [str(Path(args.cwd).resolve())], 'forceReload': True})
            discovered = [skill for entry in result['data'] for skill in entry['skills']]
            errors = [error for entry in result['data'] for error in entry['errors']]
            regressions = [skill['path'] for skill in discovered if skill['path'] in paths and skill['enabled']]
            active = [skill for skill in discovered if skill['enabled'] and not skill.get('pluginId')]
            duplicates = {name: count for name, count in Counter(skill['name'] for skill in active).items() if count > 1}
            print(json.dumps({'active_nonplugin': len(active), 'duplicate_active_names': duplicates,
                              'excluded_but_enabled': regressions, 'parser_errors': len(errors),
                              'scope': str(Path(args.cwd).resolve())}, indent=2))
            if errors or regressions or duplicates:
                raise SystemExit(1)
    finally:
        selector.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


if __name__ == '__main__':
    main()
