#!/usr/bin/env python3
"""Check original Foundation/Objective-C execution and normal launchd exit in QEMU."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import struct
import subprocess


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--hfsplus', type=Path, required=True)
    args = ap.parse_args()
    root = args.output
    result = json.loads((root / 'run/result.json').read_text())
    manifest = json.loads((root / 'launchctl-root-manifest.json').read_text())
    audit = json.loads((root / 'runtime-audit.json').read_text())
    guest = root / 'guest'
    guest.mkdir(exist_ok=True)

    def extract(path, name):
        target = guest / name
        target.unlink(missing_ok=True)
        subprocess.run([str(args.hfsplus.resolve()), str((root / 'run/ramdisk-final.hfs').resolve()),
                        'extract', path, str(target.resolve())], check=True, capture_output=True)
        return target.read_bytes() if target.exists() else b''

    names = ('launchctl-control.log', 'ipc-foundation.log', 'sweet-service.pid', 'ipc-client.exit',
             'foundation-result.json', 'launchctl-print-foundation-running.txt', 'launchctl-print-foundation-exited.txt')
    data = {name: extract('/private/var/tmp/' + name, name).decode(errors='replace') for name in names}
    trace, log = data['launchctl-control.log'], data['ipc-foundation.log']
    summary = re.search(r'(?m)^FOUNDATION CONTROL PASS pid=(\d+)$', trace)
    ready = re.search(r'FOUNDATION READY pid=(\d+)', log)
    found = summary or ready
    pid = int(found[1]) if found else -1
    try:
        artifact = json.loads(data['foundation-result.json'])
    except ValueError:
        artifact = None
    file_checks = {}
    for index, (path, expected) in enumerate(manifest['files'].items()):
        content = extract(path, f'file-{index:03}')
        file_checks[path] = hashlib.sha256(content).hexdigest() == expected
    for path, expected in {
        '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
        '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
    }.items():
        file_checks[path] = hashlib.sha256(extract(path, Path(path).name)).hexdigest() == expected
    profile = extract('/System/Library/LaunchDaemons/org.sweet.qemu.c-service.plist', 'target.plist')
    try:
        job = plistlib.loads(profile)
    except (plistlib.InvalidFileException, ValueError):
        job = {}
    job = job if isinstance(job, dict) else {}
    frames = sorted((root / 'run/frames').glob('*.txt'))
    screen = '\n'.join(p.read_text() for p in frames)
    if (root / 'run/fb.txt').exists():
        screen += '\n' + (root / 'run/fb.txt').read_text()
    tags = ('print-foundation-running', 'print-foundation-exited')
    positions = [trace.find(f'CLI {tag} status=0x00000000') for tag in tags]
    running = data['launchctl-print-foundation-running.txt']
    exited = data['launchctl-print-foundation-exited.txt']

    def integer(text, key):
        found = re.search(r'(?m)^\s*' + re.escape(key) + r' = (\d+)\s*$', text)
        return int(found[1]) if found else -1

    with (root / 'run/ramdisk-final.hfs').open('rb') as image:
        image.seek(1024)
        header = image.read(512)
    block_size, blocks = struct.unpack_from('>II', header, 40)
    markers = ('FOUNDATION ENTERED', 'FOUNDATION POOL ready',
               'FOUNDATION STRING uppercase=DUCHAMP length=7 unicode_units=5',
               'FOUNDATION DICTIONARY count=2 soc=6897', 'FOUNDATION JSON roundtrip bytes=',
               'FOUNDATION FILE roundtrip bytes=', 'FOUNDATION EXCEPTION caught=SweetProbe',
               'FOUNDATION POOL drained', f'FOUNDATION READY pid={pid}', 'FOUNDATION NORMAL EXIT status=0')
    steps = [log.find(marker) for marker in markers]
    checks = {
        'foundation_scenario': manifest.get('scenario') == 'foundation' and 'SCENARIO foundation' in trace,
        'dependency_audit_passed': audit['passed'] and len(audit['files']) == 82,
        'all_installed_bytes_preserved': all(file_checks.values()),
        'original_foundation_pinned': audit['files'].get('/System/Library/Frameworks/Foundation.framework/Foundation', {}).get('sha256') ==
            '182a6fb6d6c51e8e1a70e9152c84cd9d1bd65d2a1f0bda21a4ebe1be446021f2',
        'original_corefoundation_pinned': audit['files'].get('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation', {}).get('sha256') ==
            '1bc84069d4292467b750c7aafb4c3114092cb9b5fa906d9c40e61504dc883878',
        'grown_ram_volume_128m': manifest.get('volume_bytes') == 128 << 20 and header[:2] == b'H+'
            and blocks * block_size == 128 << 20 and (root / 'run/ramdisk-final.hfs').stat().st_size == 128 << 20,
        'exactly_target_and_observer_jobs': manifest['jobs'] == ['org.sweet.qemu.c-service.plist', 'org.sweet.qemu.launchctl-control.plist'],
        'target_profile_unchanged': job == manifest['base_target_job']
            and hashlib.sha256(profile).hexdigest() == manifest['target_job_sha256'],
        'target_runatload_without_keepalive': job.get('RunAtLoad') is True and job.get('KeepAlive') is False,
        'root_child_of_original_launchd': pid > 1 and f'IDENTITY pid={pid} ppid=1 uid=0 parent=/sbin/launchd' in log,
        'observer_root_child': bool(re.search(r'controller pid=\d+ ppid=1 uid=0 parent=/sbin/launchd', trace)),
        'all_foundation_steps_observed': all(i >= 0 for i in steps),
        'foundation_steps_in_order': all(i >= 0 for i in steps) and steps == sorted(steps),
        'json_file_matches_expected': artifact == {'device': 'DUCHAMP', 'soc': 6897},
        'matching_json_file_lengths': re.findall(r'FOUNDATION JSON roundtrip bytes=(\d+)', log) ==
            re.findall(r'FOUNDATION FILE roundtrip bytes=(\d+)', log) != [],
        'two_cli_exit_zero': all(i >= 0 for i in positions),
        'only_expected_cli_calls': re.findall(r'(?m)^BEGIN (\S+)$', trace) == list(tags)
            and len(re.findall(r'(?m)^CLI \S+ status=', trace)) == 2,
        'target_running_once': integer(running, 'pid') == pid and integer(running, 'runs') == 1 and 'state = running' in running,
        'release_file_exact': data['ipc-client.exit'] == 'exit\n',
        'target_reaped': f'FOUNDATION REAPED pid={pid} ESRCH' in trace,
        'normal_exit_without_restart': 'state = not running' in exited and integer(exited, 'pid') == -1
            and integer(exited, 'runs') == 1 and integer(exited, 'last exit code') == 0,
        'control_pass': summary is not None,
        'stopped_state_survives': len(re.findall(r'heartbeat=\d+ foundation_stopped=1 pid=' + str(pid), trace)) >= 2,
        'no_diagnostic_failure': all('FAIL' not in text and 'TIMEOUT' not in text for text in (trace, log)),
        'no_visible_panic': result['status'] == 'no_panic_observed' and 'SWEET EARLY PANIC:' not in screen and 'panic(cpu ' not in screen,
        'screen_decoded': result.get('unknown_glyphs') == 0,
    }
    report = {'passed': all(checks.values()), 'scenario': 'foundation', 'checks': checks,
              'foundation_pid': pid, 'installed_file_checks': file_checks,
              'elapsed_host_seconds': result.get('elapsed_host_seconds'), 'stop_marker': result.get('stop_marker'),
              'sampled_frames': len(frames), 'framebuffer_is_sampled': True,
              'sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                         ('sweet-launchd-service', 'sweet-launchctl-control', 'root.hfs', 'payload.bin', 'run/ramdisk-final.hfs')}}
    (root / 'run/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
