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
    ap.add_argument('--notifyd', action='store_true', help='also verify notify/cancel and ASL remote-filter integration')
    ap.add_argument('--report', type=Path, help='separate report for a saved-guest recheck')
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
    original_pins = {
        '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
        '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
        '/usr/sbin/syslogd': SYSLOGD,
    }
    if args.notifyd:
        original_pins['/usr/sbin/notifyd'] = '819c8ec6b3bee5cd2f1dcbe0b2b698418c411b4c126f2f97cbdae932c1972907'
    originals = {path: hashlib.sha256(extract(path, Path(path).name)).hexdigest() == digest
                 for path, digest in original_pins.items()}
    names = ['launchctl-control.log', 'syslogd-debug.log', 'ipc-asl1.log', 'ipc-asl2.log',
             'asl-probes.begin', 'asl-probes.exit', 'asl-probe1.pid', 'asl-probe2.pid',
             'asl-probe1.done', 'asl-probe2.done']
    tags = ['syslogd-before', 'syslogd-probe1-exited', 'syslogd-probe2-exited', 'syslogd-after']
    if args.notifyd:
        tags.insert(1, 'notifyd-before')
        tags.append('notifyd-after')
        names.append('notifyd-debug.log')
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
    if args.notifyd:
        expected_jobs.insert(0, 'com.apple.notifyd.plist')
    frames = sorted((root / 'run/frames').glob('*.txt'))
    screen = '\n'.join(path.read_text() for path in frames)
    checks = {
        'syslogd_scenario': manifest.get('scenario') == ('notifyd' if args.notifyd else 'syslogd') and
            ('SCENARIO notifyd' if args.notifyd else 'SCENARIO syslogd') in trace,
        'control_pass': summary is not None,
        'four_distinct_processes': min(server, one, two, observer) > 1 and len({server, one, two, observer}) == 4,
        'dependency_closure': audit['passed'] and audit['files'].get('/usr/sbin/syslogd', {}).get('sha256') == SYSLOGD,
        'all_installed_hashes_match': bool(installed) and all(installed.values()),
        'original_executables_preserved': all(originals.values()),
        'pinned_foss_launchctl': manifest['files'].get('/bin/launchctl') ==
            '11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d',
        'exact_job_set': found_jobs == expected_jobs == manifest['jobs'],
        'syslogd_job_matches_manifest': jobs.get('com.apple.syslogd.plist') == manifest.get('syslogd_job'),
        'original_disabled_job_documented': manifest['syslogd_source']['original_job'].get('Disabled') is True and
            manifest['syslogd_source']['original_job'].get('EnvironmentVariables') == {'ASL_DISABLE': '1'},
        'syslogd_enabled_without_keepalive': jobs.get('com.apple.syslogd.plist', {}).get('Disabled') is False and
            jobs.get('com.apple.syslogd.plist', {}).get('KeepAlive') is False,
        'machservice_name_preserved': jobs.get('com.apple.syslogd.plist', {}).get('MachServices') ==
            {'com.apple.system.logger': True},
        'all_cli_commands_exit_zero': re.findall(r'(?m)^CLI (\S+) status=0x00000000$', trace) == tags,
        'cli_prints_only': re.findall(r'(?m)^BEGIN (\S+)$', trace) == tags,
        'syslogd_pidfile': raw['syslog.pid'].strip() == str(server).encode(),
        'debug_reached_mach_server_and_work_queue': 'starting mach service' in debug and 'starting work queue' in debug,
        'begin_exit_gates': raw['asl-probes.begin'] == b'begin\n' and raw['asl-probes.exit'] == b'exit\n',
        'two_server_heartbeats': re.findall(r'(?m)^heartbeat=(\d+) syslogd_running=1 server=' +
            str(server) + r' probes_stopped=1$', trace) == ['1', '2'],
        'no_diagnostic_failure': all(data[name] and 'FAIL' not in data[name] and 'TIMEOUT' not in data[name]
                                     and 'NOTIFY ERROR' not in data[name]
                                     for name in ('launchctl-control.log', 'ipc-asl1.log', 'ipc-asl2.log')),
        'no_visible_panic': result['status'] == 'no_panic_observed' and 'SWEET EARLY PANIC:' not in screen and 'panic(cpu ' not in screen,
        'framebuffer_decoded': result.get('unknown_glyphs') == 0,
    }
    for tag in ('syslogd-before', 'syslogd-after'):
        text = data[f'launchctl-{tag}.txt']
        checks[tag + '_running_once_same_pid'] = integer(text, 'pid') == server and integer(text, 'runs') == 1 and 'state = running' in text
    notification_server = -1
    if args.notifyd:
        match = re.search(r'(?m)^NOTIFYD CONTROL PASS server=(\d+) syslogd=' + str(server) +
                          ' clients=' + str(one) + ',' + str(two) + '$', trace)
        notification_server = int(match[1]) if match else -1
        for tag in ('notifyd-before', 'notifyd-after'):
            text = data[f'launchctl-{tag}.txt']
            checks[tag + '_running_once_same_pid'] = integer(text, 'pid') == notification_server and integer(text, 'runs') == 1 and 'state = running' in text
        checks.update({
            'notifyd_control_pass': match is not None,
            'five_distinct_processes': min(notification_server, server, one, two, observer) > 1 and
                len({notification_server, server, one, two, observer}) == 5,
            'original_notifyd_job_and_ipc_mode': jobs.get('com.apple.notifyd.plist') == manifest.get('notifyd_job') and
                jobs.get('com.apple.notifyd.plist', {}).get('ProgramArguments') ==
                ['/usr/sbin/notifyd', '-d', '-log_file', '/private/var/tmp/notifyd-debug.log', '-shm_pages', '0'],
            'notifyd_service_and_publisher_preserved': jobs.get('com.apple.notifyd.plist', {}).get('MachServices') ==
                {'com.apple.system.notification_center': True} and
                jobs.get('com.apple.notifyd.plist', {}).get('PublishesEvents') == 'com.apple.notifyd.matching',
            'notifyd_debug_identity': f'notifyd start PID {notification_server}' in data['notifyd-debug.log'],
            'remote_master_set_through_notifyd': f'ASL REMOTE MASTER state=0x300ff notifyd={notification_server}' in trace,
            'remote_master_restored_and_token_cancelled': 'ASL REMOTE MASTER restored=0 token_cancelled=1' in trace,
        })
        for kind, number in [('ready', 1), ('ready', 2), ('begin', 0), ('received1', 1),
                             ('received1', 2), ('received2', 2), ('done', 1), ('done', 2)]:
            name = f'notify-{kind}-{number}'
            checks[name + '_gate'] = extract('/private/var/tmp/' + name, name) == b'done\n'
        first, second = data['ipc-asl1.log'], data['ipc-asl2.log']
        checks['two_native_posts_by_first_probe'] = re.findall(
            r'(?m)^NOTIFY POSTED phase=(\d) state=0x([0-9a-f]+)$', first) == [
                ('1', '1020304050607001'), ('2', '1020304050607002')] and 'NOTIFY POSTED' not in second
        checks['cancelled_first_token_stayed_invalid_after_second_post'] = (
            'NOTIFY CANCELLED id=1 valid=0 check_status=2' in first and
            'NOTIFY CANCEL HOLDS id=1 phase=2 valid=0 check_status=2' in first and
            'NOTIFY RECEIVED id=1 phase=2' not in first)
        for number in (1, 2):
            log = data[f'ipc-asl{number}.log']
            checks[f'notify_probe{number}_plain_registration'] = bool(re.search(
                rf'(?m)^NOTIFY REGISTER RESULT id={number} api=plain status=0 token=\d+$', log))
            checks[f'notify_probe{number}_initial_state_zero'] = (
                f'NOTIFY INITIAL STATE id={number} status=0 state=0x0000000000000000' in log)
            checks[f'notify_probe{number}_initial_dirty_cleared'] = bool(re.search(
                rf'(?m)^NOTIFY REGISTERED id={number} token=\d+ initial_state=0 initial_changed=1 quiet=0$', log))
            expected = [('1', '1020304050607001')] + ([('2', '1020304050607002')] if number == 2 else [])
            checks[f'notify_probe{number}_received_expected_states'] = re.findall(
                rf'(?m)^NOTIFY RECEIVED id={number} phase=(\d) state=0x([0-9a-f]+) changed=1$', log) == expected
            checks[f'notify_probe{number}_cancelled_and_completed'] = (
                f'NOTIFY CANCELLED id={number} valid=0 check_status=2' in log and f'NOTIFY PROBE PASS id={number}' in log)
    records = [dict(re.findall(r'\[([^\s\]]+) ([^\]]*)\]', line)) for line in output.splitlines() if line]
    messages_ok = len(records) == 6
    expected_tokens = []
    for number, pid in enumerate((one, two), 1):
        log = data[f'ipc-asl{number}.log']
        checks[f'probe{number}_root_child'] = f'IDENTITY pid={pid} ppid=1 uid=0 parent=/sbin/launchd' in log
        checks[f'probe{number}_legacy_asl_connection'] = bool(re.search(
            rf'(?m)^ASL CONNECTED id={number} pid={pid} port=0x[1-9a-f][0-9a-f]* options=' +
            ('0x20000000' if args.notifyd else '0x20000004') + '$', log))
        sent = re.findall(rf'(?m)^ASL SENT id={number} seq=(\d+) pid={pid} status=0 eval=0x([0-9a-f]+)$', log)
        checks[f'probe{number}_sent_three_native_asl_messages'] = [row[0] for row in sent] == ['1', '2', '3'] and all(
            int(row[1], 16) & 0x20000 and not int(row[1], 16) & (0x40000 | 0x80000 | 0x100000) for row in sent)
        if args.notifyd:
            checks[f'probe{number}_asl_remote_filter_applied'] = len(sent) == 3 and all(int(row[1], 16) & 0x200000 for row in sent)
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
              'notifyd_pid': notification_server,
              'observer_pid': observer, 'record_count': len(records), 'records': records,
              'elapsed_host_seconds': result.get('elapsed_host_seconds'), 'sampled_frames': len(frames),
              'stop_marker': result.get('stop_marker'), 'installed_file_checks': installed, 'original_file_checks': originals,
              'sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                         ('sweet-launchd-service', 'sweet-ipc-client', 'sweet-launchctl-control',
                          'root.hfs', 'payload.bin', 'run/ramdisk-final.hfs')},
              'guest_file_sha256': {name: hashlib.sha256(content).hexdigest() for name, content in raw.items()}}
    (args.report or root / 'run/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
