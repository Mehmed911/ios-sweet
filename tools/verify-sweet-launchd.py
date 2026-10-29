#!/usr/bin/env python3
"""Require a C service with parent PID 1 after exec of the original Apple launchd."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    root = args.output
    result = json.loads((root / 'run/result.json').read_text())
    manifest = json.loads((root / 'launchd-root-manifest.json').read_text())
    screen_path = root / 'run/fb.txt'
    snapshots = sorted((root / 'run/frames').glob('*.txt'))
    screen = '\n'.join(p.read_text() for p in snapshots)
    screen += '\n' + (screen_path.read_text() if screen_path.exists() else '')
    main_line = re.search(r'SWEET launchd service: main pid=(\d+) ppid=(\d+)', screen)
    processes = set(re.findall(r'SWEET launchd service: main pid=(\d+) ppid=(\d+)', screen))
    uids = set(re.findall(r'SWEET launchd service: uid=(\d+) euid=(\d+)', screen))
    heartbeats = list(dict.fromkeys(re.findall(
        r'SWEET launchd service: heartbeat=(\d+) pid=(\d+) ppid=(\d+)', screen)))
    checks = {
        'original_launchd_installed': manifest['files'].get('/sbin/launchd') ==
            '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
        'original_xpcproxy_installed': manifest['files'].get('/usr/libexec/xpcproxy') ==
            '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
        'one_service_configured': manifest['service']['Label'] == 'org.sweet.qemu.c-service'
            and manifest.get('service_files') == ['org.sweet.qemu.c-service.plist'],
        'system_service_configured': manifest['service'].get('UserName') == 'root'
            and manifest['service'].get('LimitLoadToSessionType') == 'System',
        'bootstrap_pid1_exec': 'SWEET launchd bootstrap: PID 1 exec original /sbin/launchd' in screen,
        'original_launchd_announced': 'hello from launchd.1' in screen,
        'no_bootstrap_exec_failure': 'TEST FAILED' not in screen and 'exec errno hex:' not in screen,
        'service_is_child_of_pid1': bool(main_line) and int(main_line[1]) > 1 and main_line[2] == '1',
        'single_service_process': len(processes) == 1,
        'kernel_reports_original_parent_path':
            'SWEET launchd service: parent_path=/sbin/launchd' in screen,
        'service_is_root': uids == {('0', '0')},
        'service_ram_file': 'SWEET launchd service: RAM file verified' in screen,
        'persistent_service': bool(main_line) and len(heartbeats) >= 2 and
            all(pid == main_line[1] and parent == '1' for _, pid, parent in heartbeats) and
            all(int(b[0]) > int(a[0]) for a, b in zip(heartbeats, heartbeats[1:])),
        'no_visible_panic': result['status'] == 'no_panic_observed' and
            'SWEET EARLY PANIC:' not in screen and 'panic(cpu ' not in screen,
        'screen_decoded': result.get('unknown_glyphs') == 0,
    }
    report = {
        'passed': all(checks.values()), 'checks': checks,
        'sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                   for name in ('bootstrap', 'service', 'root.hfs', 'payload.bin')},
        'snapshot_series_only': True, 'sampled_frames': len(snapshots),
    }
    (root / 'run/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
