#!/usr/bin/env python3
"""Verify real NSUserDefaults/cfprefsd roundtrips, persistence and reader restart."""
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
        return target.read_bytes() if target.is_file() else b''

    def log(name):
        return extract('/private/var/tmp/' + name, name).decode(errors='replace')

    control = log('launchctl-control.log')
    writer_log = log('ipc-prefs-writer.log')
    summary = re.search(r'(?m)^PREFERENCES CONTROL PASS writer=(\d+) readers=(\d+),(\d+) regular=(\d+) system=(\d+)$', control)
    pids = list(map(int, summary.groups())) if summary else [-1] * 5
    writer, reader1, reader2, regular, system = pids
    if writer < 2:
        match = re.search(r'IDENTITY pid=(\d+)', writer_log)
        writer = int(match[1]) if match else -1
    probes = [(writer, writer_log)]
    probes.extend((pid, log(f'ipc-prefs-reader-{pid}.log')) for pid in (reader1, reader2))
    tags = ['prefs-writer-running', 'cfprefsd-0-before', 'cfprefsd-1-before',
            'prefs-reader-start-1', 'prefs-reader-exited-1',
            'prefs-reader-start-2', 'prefs-reader-exited-2', 'prefs-writer-exited',
            'cfprefsd-0-after', 'cfprefsd-1-after']
    cli = {tag: log(f'launchctl-{tag}.txt') for tag in tags}
    file_checks = {}
    for index, (path, expected) in enumerate(manifest['files'].items()):
        file_checks[path] = hashlib.sha256(extract(path, f'file-{index:03}')).hexdigest() == expected
    for path, expected in {
        '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
        '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
    }.items():
        file_checks[path] = hashlib.sha256(extract(path, Path(path).name)).hexdigest() == expected
    expected = {'device': 'DUCHAMP', 'soc': 6897, 'enabled': True}
    persisted = {}
    for index, path in enumerate(('/private/var/root/Library/Preferences/org.sweet.qemu.preferences.plist',
                                  '/Library/Preferences/org.sweet.qemu.preferences.plist')):
        raw = extract(path, f'preferences-{index}.plist')
        try:
            persisted[path] = plistlib.loads(raw)
        except (ValueError, plistlib.InvalidFileException):
            persisted[path] = None
    frames = sorted((root / 'run/frames').glob('*.txt'))
    screen = '\n'.join(p.read_text() for p in frames)
    if (root / 'run/fb.txt').exists():
        screen += '\n' + (root / 'run/fb.txt').read_text()

    def number(text, key):
        match = re.search(r'(?m)^\s*' + re.escape(key) + r' = (\d+)\s*$', text)
        return int(match[1]) if match else -1

    checks = {
        'cfprefsd_scenario': manifest['scenario'] == 'cfprefsd' and 'SCENARIO cfprefsd' in control,
        'runtime_dependency_audit': audit['passed'] and len(audit['files']) == len(manifest['syslogd_source']['files']),
        'observed_dynamic_preferences_dependency': all(path in audit['files'] for path in (
            '/System/Library/Frameworks/MobileCoreServices.framework/MobileCoreServices',
            '/System/Library/Frameworks/CoreServices.framework/CoreServices')),
        'all_installed_file_hashes_preserved': all(file_checks.values()),
        'unmodified_original_cfprefsd': audit['files'].get('/usr/sbin/cfprefsd', {}).get('sha256') ==
            '05e6c217284c2e4f669243fe24296f3ba9abb53a750c9d3860348b0b43c978e2',
        'foundation_and_corefoundation_pinned':
            audit['files'].get('/System/Library/Frameworks/Foundation.framework/Foundation', {}).get('sha256') ==
            '182a6fb6d6c51e8e1a70e9152c84cd9d1bd65d2a1f0bda21a4ebe1be446021f2' and
            audit['files'].get('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation', {}).get('sha256') ==
            '1bc84069d4292467b750c7aafb4c3114092cb9b5fa906d9c40e61504dc883878',
        'ram_root_128m': manifest['volume_bytes'] == 128 << 20 and
            (root / 'run/ramdisk-final.hfs').stat().st_size == 128 << 20,
        'three_distinct_probe_processes': min(writer, reader1, reader2) > 1 and len({writer, reader1, reader2}) == 3,
        'observer_original_launchd_child': bool(re.search(r'controller pid=\d+ ppid=1 uid=0 parent=/sbin/launchd', control)),
        'writer_sets_expected_values': 'PREFERENCES SET string=DUCHAMP integer=6897 bool=1' in writer_log,
        'reader_does_not_set_values': all('PREFERENCES SET' not in text for _, text in probes[1:]),
        'on_demand_original_daemon_selected': max(regular, system) > 1,
        'native_mach_services_preserved': {k for job in manifest['cfprefsd_jobs'].values() for k in job['MachServices']} ==
            {'com.apple.cfprefsd.daemon', 'com.apple.cfprefsd.daemon.system'},
        'cfprefsd_on_demand_without_keepalive': all(job['RunAtLoad'] is False and job['KeepAlive'] is False
            for job in manifest['cfprefsd_jobs'].values()),
        'reader_only_kickstarted': manifest['client_job']['RunAtLoad'] is False,
        'persisted_plist_exact_values': any(p == expected and type(p.get('soc')) is int and type(p.get('enabled')) is bool
            for p in persisted.values() if isinstance(p, dict)),
        'ten_real_launchctl_calls_succeed': re.findall(r'(?m)^BEGIN (\S+)$', control) == tags and
            re.findall(r'(?m)^CLI (\S+) status=0x00000000$', control) == tags,
        'writer_running_once': number(cli['prefs-writer-running'], 'pid') == writer and
            number(cli['prefs-writer-running'], 'runs') == 1 and 'state = running' in cli['prefs-writer-running'],
        'writer_exited_normally_without_restart': number(cli['prefs-writer-exited'], 'pid') == -1 and
            number(cli['prefs-writer-exited'], 'runs') == 1 and number(cli['prefs-writer-exited'], 'last exit code') == 0,
        'control_pass': summary is not None,
        'two_stopped_heartbeats': len(re.findall(r'heartbeat=\d+ preferences_stopped=1', control)) == 2,
        'no_probe_failure': all('FAIL' not in text and 'TIMEOUT' not in text and 'PREFERENCES ERROR' not in text
                                for text in [control, *[t for _, t in probes]]),
        'no_visible_panic': result['status'] == 'no_panic_observed' and
            all(term not in screen for term in ('SWEET EARLY PANIC:', 'panic(cpu ', 'Library not loaded:', 'Symbol not found:')),
        'framebuffer_decoded': result.get('unknown_glyphs') == 0,
        'expected_stop_marker': result.get('stop_marker') == 'SWEET launchctl: heartbeat=2 ',
    }
    for pid, text in probes:
        role = 'writer' if pid == writer else ('reader1' if pid == reader1 else 'reader2')
        checks[role + '_root_launchd_child'] = f'IDENTITY pid={pid} ppid=1 uid=0 parent=/sbin/launchd' in text
        checks[role + '_exact_readback'] = 'PREFERENCES READ string=DUCHAMP integer=6897 bool=1' in text
        checks[role + '_normal_exit'] = 'PREFERENCES NORMAL EXIT status=0' in text
        steps = [text.find(marker) for marker in ('PREFERENCES RUNTIME WARMUP domain=org.sweet.qemu.runtime-warmup unused=nil no_writes=1',
                  'PREFERENCES LIBRARIES PREPARED',
                  'PREFERENCES ISOLATED chroot=empty', 'PREFERENCES READ string=DUCHAMP',
                  'PREFERENCES ISOLATION VERIFIED')]
        checks[role + '_libraries_prepared_before_isolation'] = all(i >= 0 for i in steps) and steps == sorted(steps)
        checks[role + '_isolated_from_real_preferences'] = 'PREFERENCES ISOLATED chroot=empty cwd=/ direct_create=ENOENT paths=3' in text
        checks[role + '_direct_file_fallback_impossible'] = 'PREFERENCES ISOLATION VERIFIED direct_read=ENOENT paths=3' in text
    for cycle, pid in ((1, reader1), (2, reader2)):
        exited = cli[f'prefs-reader-exited-{cycle}']
        checks[f'reader{cycle}_new_launchd_pid'] = cli[f'prefs-reader-start-{cycle}'].strip() == str(pid)
        checks[f'reader{cycle}_normal_reaped_state'] = (number(exited, 'runs') == cycle and
            number(exited, 'pid') == -1 and number(exited, 'last exit code') == 0 and 'state = not running' in exited and
            f'PREFERENCES READER cycle={cycle} pid={pid} exit=0 ESRCH' in control)
    for index, pid in enumerate((regular, system)):
        before, after = cli[f'cfprefsd-{index}-before'], cli[f'cfprefsd-{index}-after']
        checks[f'daemon{index}_stable'] = ((pid > 1 and number(before, 'pid') == number(after, 'pid') == pid and
            number(before, 'runs') == number(after, 'runs') == 1 and 'state = running' in after) or
            (pid == 0 and number(before, 'pid') == number(after, 'pid') == -1 and
             number(before, 'runs') == number(after, 'runs') == 0))
    report = dict(passed=all(checks.values()), scenario='cfprefsd', checks=checks,
                  writer_pid=writer, reader_pids=[reader1, reader2], daemon_pids=[regular, system],
                  installed_file_checks=file_checks, persisted_preferences=persisted,
                  elapsed_host_seconds=result.get('elapsed_host_seconds'), sampled_frames=len(frames),
                  stop_marker=result.get('stop_marker'), framebuffer_is_sampled=True,
                  sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                          ('sweet-launchd-service', 'sweet-ipc-client', 'sweet-launchctl-control',
                           'root.hfs', 'payload.bin', 'run/ramdisk-final.hfs')})
    (root / 'run/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'installed_file_checks'}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
