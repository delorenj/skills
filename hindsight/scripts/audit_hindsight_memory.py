#!/usr/bin/env python3
import json
import sys
from pathlib import Path

CFG = Path('/home/delorenj/.openclaw/openclaw.json')

REQUIRED_BOOLS = [
    'autoRecall',
    'autoCapture',
    'captureDirectIntent',
    'captureToolErrors',
]


def fail(msg: str):
    print(f'FAIL: {msg}')
    return False


def ok(msg: str):
    print(f'OK: {msg}')
    return True


def main() -> int:
    if not CFG.exists():
        print(f'FAIL: config not found: {CFG}')
        return 2

    cfg = json.loads(CFG.read_text())
    entries = (cfg.get('plugins') or {}).get('entries') or {}
    hm = entries.get('hindsight-memory')
    if not isinstance(hm, dict):
        print('FAIL: plugins.entries.hindsight-memory missing')
        return 2

    passed = True

    enabled = hm.get('enabled', True)
    passed &= ok('hindsight-memory plugin enabled') if enabled else fail('hindsight-memory plugin disabled')

    conf = hm.get('config') or {}

    default_bank = conf.get('defaultBank')
    if isinstance(default_bank, str) and default_bank.strip():
        passed &= ok(f'defaultBank set: {default_bank}')
    else:
        passed &= fail('defaultBank missing/empty')

    for k in REQUIRED_BOOLS:
        v = conf.get(k)
        if v is True:
            passed &= ok(f'{k}=true')
        else:
            passed &= fail(f'{k} must be true (got {v!r})')

    agent_routes = conf.get('agentRoutes')
    if isinstance(agent_routes, dict) and len(agent_routes) > 0:
        passed &= ok(f'agentRoutes configured ({len(agent_routes)} routes)')
    else:
        passed &= fail('agentRoutes missing or empty')

    global_recall = conf.get('globalRecallBanks')
    if isinstance(global_recall, list) and len(global_recall) > 0:
        passed &= ok(f'globalRecallBanks configured ({len(global_recall)})')
    else:
        passed &= fail('globalRecallBanks missing/empty')

    if passed:
        print('PASS: Hindsight memory governance is compliant.')
        return 0
    print('FAIL: Hindsight memory governance not compliant.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
