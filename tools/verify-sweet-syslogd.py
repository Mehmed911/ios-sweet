#!/usr/bin/env python3
"""Verify real ASL receipt/file output by the unmodified iOS restore syslogd."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import subprocess

SYSLOGD = '86838d9149bb898e3d39266fea884c6c92eeac1e6486c072b135a879c9eeaabe'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--hfsplus', type=Path, required=True)
    args = ap.parse_args()
    root = args.output
    manifest = json.loads((root / 'launchctl-root-manifest.json').read_text())
    result = json.loads((root / 'run/result.json').read_text())
    audit = json.loads((root / 'runtime-audit.json').read_text())
    guest = root / 'guest'
    guest.mkdir(exist_ok=True)

    def extract(path, name):
        target = guest / name
        target.unlink(missing_ok=True)
        subprocess.run([str(args.hfsplus.resolve()), str((root / 'run/ramdisk-final.hfs').resolve()),
                        'extract', path, str(target.resolve())], check=True, capture_output=True)
        return target.read_bytes() if target.exists() else b''

    installed = {path: hashlib.sha256(extract(path, f'installed-{i:03}')).hexdigest() == digest
                 for i, (path, digest) in enumerate(manifest['files'].items())}
    originals = {path: hashlib.sha256(extract(path, Path(path).name)).hexdigest() == digest for path, digest in {
        '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
        '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
        '/usr/sbin/syslogd': SYSLOGD,
    }.items()}
    names = ['launchctl-control.log', 'syslogd-debug.log', 'ipc-asl1.log', 'ipc-asl2.log',
             'asl-probes.begin', 'asl-probes.exit', 'asl-probe1.pid', 'asl-probe2.pid',
             'asl-probe1.done', 'asl-probe2.done']
    tags = ['syslogd-before', 'syslogd-probe1-exited', 'syslogd-probe2-exited', 'syslogd-after']
    names += [f'launchctl-{tag}.txt' for tag in tags]
    raw = {name: extract('/private/var/tmp/' + name, name) for name in names}
    raw['output'] = extract('/private/var/log/sweet-asl.log', 'sweet-asl.log')
    raw['syslog.pid'] = extract('/private/var/run/syslog.pid', 'syslog.pid')
    data = {name: content.decode(errors='replace') for name, content in raw.items()}
    trace, debug, output = data['launchctl-control.log'], data['syslogd-debug.log'], data['output']
    summary = re.search(r'(?m)^SYSLOGD CONTROL PASS server=(\d+) clients=(\d+),(\d+) messages=6$', trace)
    server, one, two = [int(summary[i]) for i in (1, 2, 3)] if summary else [-1, -1, -1]
    identity = re.search(r'controller pid=(\d+) ppid=1 uid=0 parent=/sbin/launchd', trace)
    observer = int(identity[1]) if identity else -1

    def integer(text, key):
        match = re.search(r'(?m)^\s*' + re.escape(key) + r' = (\d+)\s*$', text)
        return int(match[1]) if match else -1

    jobs = {}
    for name in manifest['jobs']:
        try:
            jobs[name] = plistlib.loads(extract('/System/Library/LaunchDaemons/' + name, name))
        except (ValueError, plistlib.InvalidFileException):
            jobs[name] = {}
    listing = subprocess.run([str(args.hfsplus.resolve()), str((root / 'run/ramdisk-final.hfs').resolve()),
                              'ls', '/System/Library/LaunchDaemons'], check=True, capture_output=True).stdout.decode()
    (guest / 'job-listing.txt').write_text(listing)
    found_jobs = re.findall(r'^\d{6}\s+\d+\s+\d+\s+\d+\s+\S+\s+\S+\s+(.*)$', listing, re.MULTILINE)
    expected_jobs = ['com.apple.syslogd.plist', 'org.sweet.qemu.c-service.plist',
                     'org.sweet.qemu.ipc-client.plist', 'org.sweet.qemu.launchctl-control.plist']
    frames = sorted((root / 'run/frames').glob('*.txt'))
    screen = '\n'.join(path.read_text() for path in frames)
    checks = {
        'syslogd_scenario': manifest.get('scenario') == 'syslogd' and 'SCENARIO syslogd' in trace,
        'control_pass': summary is not None,
        'four_distinct_processes': min(server, one, two, observer) > 1 and len({server, one, two, observer}) == 4,
        'dependency_closure': audit['passed'] and audit['files'].get('/usr/sbin/syslogd', {}).get('sha256') == SYSLOGD,
        'all_installed_hashes_match': bool(installed) and all(installed.values()),
        'original_executables_preserved': all(originals.values()),
        'pinned_foss_launchctl': manifest['files'].get('/bin/launchctl') ==
            '11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d',
        'exactly_four_jobs': found_jobs == expected_jobs == manifest['jobs'],
        'syslogd_job_matches_manifest': jobs.get('com.apple.syslogd.plist') == manifest.get('syslogd_job'),
        'original_disabled_job_documented': manifest['syslogd_source']['original_job'].get('Disabled') is True and
            manifest['syslogd_source']['original_job'].get('EnvironmentVariables') == {'ASL_DISABLE': '1'},
        'syslogd_enabled_without_keepalive': jobs.get('com.apple.syslogd.plist', {}).get('Disabled') is False and
            jobs.get('com.apple.syslogd.plist', {}).get('KeepAlive') is False,
        'machservice_name_preserved': jobs.get('com.apple.syslogd.plist', {}).get('MachServices') ==
            {'com.apple.system.logger': True},
        'four_cli_commands_exit_zero': re.findall(r'(?m)^CLI (\S+) status=0x00000000$', trace) == tags,
        'cli_prints_only': re.findall(r'(?m)^BEGIN (\S+)$', trace) == tags,
        'syslogd_pidfile': raw['syslog.pid'].strip() == str(server).encode(),
        'debug_reached_mach_server_and_work_queue': 'starting mach service' in debug and 'starting work queue' in debug,
        'begin_exit_gates': raw['asl-probes.begin'] == b'begin\n' and raw['asl-probes.exit'] == b'exit\n',
        'two_server_heartbeats': re.findall(r'(?m)^heartbeat=(\d+) syslogd_running=1 server=' +
            str(server) + r' probes_stopped=1$', trace) == ['1', '2'],
        'no_diagnostic_failure': all('FAIL' not in data[name] and 'TIMEOUT' not in data[name]
                                     for name in ('launchctl-control.log', 'ipc-asl1.log', 'ipc-asl2.log')),
        'no_visible_panic': result['status'] == 'no_panic_observed' and 'SWEET EARLY PANIC:' not in screen and 'panic(cpu ' not in screen,
        'framebuffer_decoded': result.get('unknown_glyphs') == 0,
    }
    for tag in ('syslogd-before', 'syslogd-after'):
        text = data[f'launchctl-{tag}.txt']
        checks[tag + '_running_once_same_pid'] = integer(text, 'pid') == server and integer(text, 'runs') == 1 and 'state = running' in text
    records = [dict(re.findall(r'\[([^\s\]]+) ([^\]]*)\]', line)) for line in output.splitlines() if line]
    messages_ok = len(records) == 6
    expected_tokens = []
    for number, pid in enumerate((one, two), 1):
        log = data[f'ipc-asl{number}.log']
        checks[f'probe{number}_root_child'] = f'IDENTITY pid={pid} ppid=1 uid=0 parent=/sbin/launchd' in log
        checks[f'probe{number}_legacy_asl_connection'] = bool(re.search(
            rf'(?m)^ASL CONNECTED id={number} pid={pid} port=0x[1-9a-f][0-9a-f]* options=0x20000004$', log))
        sent = re.findall(rf'(?m)^ASL SENT id={number} seq=(\d+) pid={pid} status=0 eval=0x([0-9a-f]+)$', log)
        checks[f'probe{number}_sent_three_native_asl_messages'] = [row[0] for row in sent] == ['1', '2', '3'] and all(
            int(row[1], 16) & 0x20000 and not int(row[1], 16) & (0x40000 | 0x80000 | 0x100000) for row in sent)
        checks[f'probe{number}_normal_exit_marker'] = f'ASL PROBE EXIT id={number} pid={pid} status=0 messages=3' in log
        state = data[f'launchctl-syslogd-probe{number}-exited.txt']
        checks[f'probe{number}_exit_zero_runs_one'] = integer(state, 'pid') == -1 and integer(state, 'runs') == 1 and integer(state, 'last exit code') == 0 and 'state = not running' in state
        checks[f'probe{number}_pid_done_tokens'] = raw[f'asl-probe{number}.pid'] == raw[f'asl-probe{number}.done'] == f'{pid}\n'.encode()
        for seq in (1, 2, 3):
            token = f'SWEET_SYSLOGD_C{number}_S{seq}_20F66'
            expected_tokens.append(token)
            matches = [record for record in records if record.get('Message') == token]
            expected = {'Message': token, 'Sender': f'sweet-asl{number}', 'Facility': 'local0',
                        'SweetFixture': 'syslogd-qemu', 'SweetClient': str(number), 'SweetSequence': str(seq),
                        'PID': str(pid), 'UID': '0', 'GID': '0', 'Level': '5'}
            checks[f'probe{number}_seq{seq}_received_with_credentials'] = len(matches) == 1 and all(
                matches[0].get(key) == value for key, value in expected.items())
            messages_ok &= checks[f'probe{number}_seq{seq}_received_with_credentials']
    checks['exactly_six_raw_asl_records'] = bool(messages_ok)
    debug_receipts = re.findall(r'__asl_server_message: ([^\n]*)', debug)
    checks['original_daemon_mig_receipt_for_each_message'] = all(
        sum(token in line for line in debug_receipts) == 1 for token in expected_tokens)
    report = {'passed': all(checks.values()), 'checks': checks, 'syslogd_pid': server, 'probe_pids': [one, two],
              'observer_pid': observer, 'record_count': len(records), 'records': records,
              'elapsed_host_seconds': result.get('elapsed_host_seconds'), 'sampled_frames': len(frames),
              'stop_marker': result.get('stop_marker'), 'installed_file_checks': installed, 'original_file_checks': originals,
              'sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                         ('sweet-launchd-service', 'sweet-ipc-client', 'sweet-launchctl-control',
                          'root.hfs', 'payload.bin', 'run/ramdisk-final.hfs')},
              'guest_file_sha256': {name: hashlib.sha256(content).hexdigest() for name, content in raw.items()}}
    (root / 'run/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
