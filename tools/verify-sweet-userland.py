#!/usr/bin/env python3
"""Require observed exec, intentional exit, wait4, restart, and heartbeats.

A non-panic framebuffer is not a userspace success condition. This validator
checks the complete diagnostic scenario and records hashes of its inputs.
The framebuffer is a circular snapshot, not a complete serial log.
"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    for name in ('kernel', 'init', 'worker', 'root', 'payload'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = json.loads((args.run / 'result.json').read_text())
    screen = (args.run / 'fb.txt').read_text()
    # Rotate the circular rows to the PID 1 startup message for sequence checks.
    marker = '*** SWEET userspace: init running as PID 1 ***'
    start = screen.find(marker)
    ordered = screen[start:] + screen[:start] if start >= 0 else screen
    started = 'SWEET worker: exec successful, child PID verified'
    restart = 'SWEET init: restarting worker in stay mode'
    heartbeat = 'SWEET worker: still alive'
    tail = ordered.split(restart, 1)[-1] if restart in ordered else ''
    checks = {
        'snapshot_decoded': result.get('unknown_glyphs') == 0,
        'no_visible_panic': result.get('status') == 'no_panic_observed',
        'pid1_started': start >= 0,
        'worker_installed': 'SWEET init: worker file installed' in screen,
        'two_exec_entries': screen.count(started) == 2,
        'intentional_exit': 'SWEET worker: intentional exit 42' in screen,
        'wait4_reaped': 'SWEET init: wait4 reaped worker, status hex:' in screen,
        'correct_wait_status': '00002a00' in screen,
        'worker_restarted': restart in screen,
        'restarted_worker_entered': started in tail,
        'restarted_worker_heartbeats': tail.count(heartbeat) >= 2,
        'parent_heartbeats': screen.count('SWEET init: still alive') >= 3,
        'no_test_failure': 'TEST FAILED' not in screen and 'execve failed' not in screen,
    }
    hashes = {name: hashlib.sha256(getattr(args, name).read_bytes()).hexdigest()
              for name in ('kernel', 'init', 'worker', 'root', 'payload')}
    report = {'passed': all(checks.values()), 'checks': checks,
              'sha256': hashes, 'framebuffer_snapshot_only': True}
    (args.run / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
