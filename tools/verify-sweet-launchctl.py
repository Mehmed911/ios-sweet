#!/usr/bin/env python3
"""Validate launchctl stop/restart or bootout/bootstrap from the saved guest RAM root."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import subprocess


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--hfsplus', type=Path, required=True)
    ap.add_argument('--scenario', choices=('stop-restart', 'bootout-bootstrap'), default='stop-restart')
    args = ap.parse_args()
    root = args.output
    result = json.loads((root / 'run/result.json').read_text())
    manifest = json.loads((root / 'launchctl-root-manifest.json').read_text())
    guest = root / 'guest'
    guest.mkdir(exist_ok=True)
    reload_test = args.scenario == 'bootout-bootstrap'
    tags = (('print-before', 'bootout', 'print-missing', 'bootstrap', 'print-after') if reload_test
            else ('print-before', 'stop', 'print-stopped', 'restart', 'print-after'))

    def extract(path, target):
        # A failing HFS tool can return zero; never reuse an older extraction.
        target.unlink(missing_ok=True)
        subprocess.run([str(args.hfsplus.resolve()), str((root / 'run/ramdisk-final.hfs').resolve()),
                        'extract', path, str(target.resolve())], check=True, capture_output=True)
        return target.read_bytes() if target.exists() else b''

    names = {'trace': 'launchctl-control.log', 'ready': 'sweet-service.pid'}
    names.update({tag: f'launchctl-{tag}.txt' for tag in tags})
    data = {}
    for key, name in names.items():
        target = guest / name
        data[key] = extract('/private/var/tmp/' + name, target).decode(errors='replace')
    trace = data['trace']
    summary = re.search(r'CONTROL PASS old=(\d+) new=(\d+)', trace)
    before = re.search(r'BEFORE pid=(\d+) state=running', trace)
    after = re.search(r'AFTER pid=(\d+) state=running old=(\d+)', trace)
    old = int(summary[1]) if summary else int(before[1]) if before else -1
    new = int(summary[2]) if summary else int(after[1]) if after else -1
    frames = sorted((root / 'run/frames').glob('*.txt'))
    screen = '\n'.join(p.read_text() for p in frames)
    if (root / 'run/fb.txt').exists():
        screen += '\n' + (root / 'run/fb.txt').read_text()
    processes = set(int(pid) for pid in re.findall(
        r'SWEET launchd service: main pid=(\d+) ppid=1', screen))
    beats = set(re.findall(r'SWEET launchd service: heartbeat=(\d+) pid=(\d+) ppid=1', screen))

    def pid(text):
        found = re.search(r'(?m)^\s*pid = (\d+)\s*$', text)
        return int(found[1]) if found else 0

    originals = {}
    for path, expected in {
        '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
        '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
        '/bin/launchctl': '11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d',
    }.items():
        target = guest / Path(path).name
        originals[path] = hashlib.sha256(extract(path, target)).hexdigest() == expected
    statuses = [trace.find(f'CLI {tag} status=0x{(113 << 8) if tag == "print-missing" else 0:08x}')
                for tag in tags]
    checks = {
        'original_launchd_preserved': originals['/sbin/launchd'],
        'original_xpcproxy_preserved': originals['/usr/libexec/xpcproxy'],
        'pinned_procursus_launchctl_preserved': originals['/bin/launchctl'],
        'controller_is_root_child_of_launchd':
            bool(re.search(r'controller pid=\d+ ppid=1 uid=0 parent=/sbin/launchd', trace)),
        ('five_cli_expected_statuses' if reload_test else 'five_cli_commands_succeeded'):
            all(i >= 0 for i in statuses),
        'cli_commands_in_order': all(i >= 0 for i in statuses) and statuses == sorted(statuses),
        'print_before_running': old > 1 and pid(data['print-before']) == old
            and 'state = running' in data['print-before'],
        'old_pid_reaped': f'STOPPED pid={old} ESRCH' in trace,
        'different_positive_pids': old > 1 and new > 1 and old != new,
        'print_after_running': pid(data['print-after']) == new and 'state = running' in data['print-after'],
        'ready_file_matches_restart': data['ready'].strip() == str(new),
        'both_target_instances_observed': processes == {old, new},
        'target_sigterm_default_and_unmasked': set(int(p) for p in re.findall(
            r'TERM default mask=0x00000000 pid=(\d+)', screen)) == {old, new},
        'restarted_target_has_heartbeats': sum(int(p) == new for _, p in beats) >= 2,
        'controller_survives': len(re.findall(r'heartbeat=\d+ new_pid=' + str(new), trace)) >= 2,
        'control_pass': summary is not None,
        'no_control_failure': 'FAIL' not in trace and 'TIMEOUT' not in trace,
        'no_visible_panic': result['status'] == 'no_panic_observed'
            and 'SWEET EARLY PANIC:' not in screen and 'panic(cpu ' not in screen,
        'screen_decoded': result.get('unknown_glyphs') == 0,
    }
    if reload_test:
        job = extract('/System/Library/LaunchDaemons/org.sweet.qemu.c-service.plist',
                      guest / 'target.plist')
        try:
            properties = plistlib.loads(job)
        except (plistlib.InvalidFileException, ValueError):
            properties = {}
        checks.update({
            'bootout_bootstrap_scenario': 'SCENARIO bootout-bootstrap' in trace,
            'unregistered_gap_observed':
                'UNREGISTERED expected_exit=113 no pid after 5 seconds; plist readable' in trace,
            'print_missing_is_enoservice': data['print-missing'].strip() ==
                'Could not find service "org.sweet.qemu.c-service" in domain for system',
            'print_missing_has_no_pid': pid(data['print-missing']) == 0,
            'target_plist_preserved': hashlib.sha256(job).hexdigest() == manifest.get('target_job_sha256'),
            'target_is_runatload_not_keepalive': properties.get('Label') == 'org.sweet.qemu.c-service'
                and properties.get('RunAtLoad') is True and properties.get('KeepAlive') is False,
            'bootstrap_pass': f'BOOTSTRAP PASS old={old} new={new}' in trace,
            'exactly_five_cli_results': len(re.findall(r'(?m)^CLI \S+ status=', trace)) == 5,
        })
    else:
        checks.update({
            'stop_gap_observed': 'STOP GAP verified no pid after 5 seconds' in trace,
            'print_stopped_has_no_pid': pid(data['print-stopped']) == 0
                and 'org.sweet.qemu.c-service' in data['print-stopped'],
            'kickstart_reports_new_pid': data['restart'].strip() == str(new),
        })
    report = {'passed': all(checks.values()), 'scenario': args.scenario,
              'checks': checks, 'old_pid': old, 'new_pid': new,
              'launchctl_variant': 'Procursus FOSS 1:1.1.1, unchanged packaged binary',
              'elapsed_host_seconds': result.get('elapsed_host_seconds'),
              'stop_marker': result.get('stop_marker'),
              'sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                         for name in ('sweet-launchd-service', 'sweet-launchctl-control', 'root.hfs',
                                      'payload.bin', 'run/ramdisk-final.hfs')},
              'cli_output_sha256': {name: hashlib.sha256((guest / value).read_bytes()).hexdigest()
                                    if (guest / value).exists() else None
                                    for name, value in names.items()},
              'sampled_frames': len(frames), 'framebuffer_is_sampled': True}
    (root / 'run/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
