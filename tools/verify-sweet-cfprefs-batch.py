#!/usr/bin/env python3
"""Check live isolated preference clients, explicit notifyd signals and restart recovery."""
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
    ap.add_argument('--report', type=Path)
    ap.add_argument('--kernel-sha256', default='82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9',
                    help='explicit expected kernel pin; legacy fixture pin remains the default')
    args = ap.parse_args()
    root = args.output
    result = json.loads((root / 'run/result.json').read_text())
    manifest = json.loads((root / 'launchctl-root-manifest.json').read_text())
    audit = json.loads((root / 'runtime-audit.json').read_text())
    inputs = json.loads((root / 'inputs.json').read_text())
    guest = root / 'guest'
    guest.mkdir(exist_ok=True)
    image = root / 'run/ramdisk-final.hfs'

    def hfs(*cmd):
        return subprocess.run([str(args.hfsplus.resolve()), str(image.resolve()), *cmd],
                              check=True, capture_output=True).stdout

    def extract(path, name):
        dest = guest / name
        dest.unlink(missing_ok=True)
        hfs('extract', path, str(dest.resolve()))
        return dest.read_bytes() if dest.is_file() else b''

    def log(name):
        return extract('/private/var/tmp/' + name, name).decode(errors='replace')

    def number(text, key):
        match = re.search(r'(?m)^\s*' + re.escape(key) + r' = (\d+)\s*$', text)
        return int(match[1]) if match else -1

    control = log('launchctl-control.log')
    summary = re.search(r'(?m)^BATCH CONTROL PASS writer=(\d+) first_reader1=(\d+) reader1=(\d+) reader2=(\d+) old_daemon=(\d+) daemon=(\d+) notifyd=(\d+)$', control)
    pids = list(map(int, summary.groups())) if summary else [-1] * 7
    writer, first, reader1, reader2, old_daemon, daemon, notifyd = pids
    if summary is None:
        live = re.search(r'BATCH LIVE writer=(\d+) reader1=(\d+) reader2=(\d+)', control)
        if live:
            writer, first, reader2 = map(int, live.groups())
        restart = re.search(r'BATCH READER RESTART old=(\d+) new=(\d+)', control)
        if restart:
            reader1 = int(restart[2])
        daemon_restart = re.search(r'BATCH DAEMON RESTART old=(\d+) new=(\d+)', control)
        if daemon_restart:
            old_daemon, daemon = map(int, daemon_restart.groups())
    roles = {'writer': (0, writer, [1, 2, 3, 4]), 'reader1_first': (1, first, [1, 2]),
             'reader1_restarted': (1, reader1, [3, 4]), 'reader2_live': (2, reader2, [1, 2, 3, 4])}
    logs = {role: log(f'ipc-prefs-batch-{kind}-{pid}.log') for role, (kind, pid, _) in roles.items()}
    # Preserve every discovered probe log even if a crash prevented CONTROL PASS.
    listing = hfs('ls', '/private/var/tmp').decode(errors='replace')
    for name in re.findall(r'ipc-prefs-batch-\d+-\d+\.log', listing):
        log(name)
    tags = ['batch-daemon-before', 'batch-notify-before', 'batch-daemon-restart',
            'batch-reader1-first-exit', 'batch-reader1-restart', 'batch-writer-final',
            'batch-reader1-final', 'batch-reader2-final', 'batch-daemon-final', 'batch-notify-final']
    cli = {tag: log(f'launchctl-{tag}.txt') for tag in tags}
    installed = {}
    for index, (path, expected) in enumerate(manifest['files'].items()):
        installed[path] = hashlib.sha256(extract(path, f'file-{index:03}')).hexdigest() == expected
    for path, expected in {
        '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
        '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
    }.items():
        installed[path] = hashlib.sha256(extract(path, Path(path).name)).hexdigest() == expected
    raw = extract('/private/var/root/Library/Preferences/org.sweet.qemu.preferences.batch.plist', 'batch-preferences.plist')
    try:
        saved = plistlib.loads(raw)
    except (ValueError, plistlib.InvalidFileException):
        saved = None
    frames = sorted((root / 'run/frames').glob('*.txt'))
    screen = '\n'.join(p.read_text() for p in frames)
    if (root / 'run/fb.txt').exists():
        screen += '\n' + (root / 'run/fb.txt').read_text()
    metadata = {f'{kind}-{ident}': log(f'prefs-batch-{kind}-{ident}')
                for kind, ident in [('ack', 1), ('ack', 2), ('completed', 0), ('control', 0)]}
    jail = hfs('ls', '/private/var/tmp/preferences-empty-root').decode(errors='replace')
    (guest / 'jail-listing.txt').write_text(jail)
    expected_pins = {
        '/usr/sbin/cfprefsd': '05e6c217284c2e4f669243fe24296f3ba9abb53a750c9d3860348b0b43c978e2',
        '/usr/sbin/notifyd': '819c8ec6b3bee5cd2f1dcbe0b2b698418c411b4c126f2f97cbdae932c1972907',
        '/System/Library/Frameworks/Foundation.framework/Foundation':
            '182a6fb6d6c51e8e1a70e9152c84cd9d1bd65d2a1f0bda21a4ebe1be446021f2',
        '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation':
            '1bc84069d4292467b750c7aafb4c3114092cb9b5fa906d9c40e61504dc883878',
        '/System/Library/Frameworks/MobileCoreServices.framework/MobileCoreServices':
            '1b78c1e4f3bc986e060e2a6d189172b0f34215c7dc4555ae3203547bc7266f77',
        '/System/Library/Frameworks/CoreServices.framework/CoreServices':
            '4a0a92937739cb822207a08fdb7b95206684433f32a6170efecf22187250896d',
    }
    checks = {
        'batch_scenario': manifest['scenario'] == 'cfprefs-batch' and inputs['mode'] == 'batch'
            and 'SCENARIO cfprefs-batch' in control,
        'runtime_dependency_audit': audit['passed'] and len(audit['files']) == 92,
        'pinned_apple_binaries': all(audit['files'].get(path, {}).get('sha256') == digest for path, digest in expected_pins.items()),
        'all_installed_hashes_preserved': all(installed.values()),
        'unchanged_kernel': inputs['input_hashes']['kernel'] == args.kernel_sha256,
        'fresh_original_base': inputs['input_hashes']['base'] == '491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f',
        'source_snapshot_intact': all(hashlib.sha256((root / 'test-sources' / name).read_bytes()).hexdigest() == digest
            for name, digest in inputs['compiled_source_snapshot'].items()),
        'ram_root_128m': manifest['volume_bytes'] == 128 << 20 and image.stat().st_size == 128 << 20,
        'four_distinct_client_instances': min(writer, first, reader1, reader2) > 1 and len({writer, first, reader1, reader2}) == 4,
        'observer_root_launchd_child': bool(re.search(r'controller pid=\d+ ppid=1 uid=0 parent=/sbin/launchd', control)),
        'two_runatload_reader_jobs': len(manifest['prefs_batch_jobs']) == 2 and all(
            job['RunAtLoad'] is True and job['KeepAlive'] is False for job in manifest['prefs_batch_jobs']),
        'cfprefsd_remains_on_demand': all(job['RunAtLoad'] is False and job['KeepAlive'] is False
                                        for job in manifest['cfprefsd_jobs'].values()),
        'ten_real_cli_calls_succeed': re.findall(r'(?m)^BEGIN (\S+)$', control) == tags and
            re.findall(r'(?m)^CLI (\S+) status=0x00000000$', control) == tags,
        'four_completed_phases': re.findall(r'(?m)^BATCH PHASE COMPLETE step=(\d+)$', control) == ['1', '2', '3', '4'],
        'initial_clients_simultaneously_live': f'BATCH LIVE writer={writer} reader1={first} reader2={reader2}' in control,
        'daemon_restarted_to_new_pid': min(old_daemon, daemon) > 1 and old_daemon != daemon and
            cli['batch-daemon-restart'].strip() == str(daemon) and
            f'BATCH DAEMON RESTART old={old_daemon} new={daemon} old_reaped=1' in control,
        'daemon_exec_wait_completed': f'BATCH DAEMON EXEC READY pid={daemon} path=/usr/sbin/cfprefsd' in control,
        'first_reader_orderly_exit': number(cli['batch-reader1-first-exit'], 'runs') == 1 and
            number(cli['batch-reader1-first-exit'], 'last exit code') == 0 and
            'state = not running' in cli['batch-reader1-first-exit'],
        'reader_restarted_to_new_pid': cli['batch-reader1-restart'].strip() == str(reader1) and
            f'BATCH READER RESTART old={first} new={reader1} ready=1' in control,
        'daemon_before_pid_runs': number(cli['batch-daemon-before'], 'pid') == old_daemon and
            number(cli['batch-daemon-before'], 'runs') == 1,
        'daemon_final_pid_runs': number(cli['batch-daemon-final'], 'pid') == daemon and
            number(cli['batch-daemon-final'], 'runs') == 2 and 'state = running' in cli['batch-daemon-final'],
        'notifyd_stayed_same_pid_once': number(cli['batch-notify-before'], 'pid') ==
            number(cli['batch-notify-final'], 'pid') == notifyd and notifyd > 1 and
            number(cli['batch-notify-before'], 'runs') == number(cli['batch-notify-final'], 'runs') == 1,
        'only_writer_sets_three_generations': re.findall(r'(?m)^BATCH SET step=(\d+) generation=(\d+)$',
            logs['writer']) == [('1', '1'), ('2', '2'), ('4', '3')],
        'recovery_phase_has_no_setters': 'BATCH RECOVERY READ ONLY generation=2 no_setters=1' in logs['writer'],
        'explicit_notification_posts_four_steps': re.findall(
            r'(?m)^BATCH NOTIFY POSTED step=(\d+) state=(\d+) explicit_after_save=1$', logs['writer']) ==
            [(str(step), str(step)) for step in range(1, 5)],
        'writer_received_both_acknowledgements': re.findall(r'(?m)^BATCH BOTH READERS ACK step=(\d+)$',
            logs['writer']) == ['1', '2', '3', '4'],
        'saved_final_exact_values_types': saved == {'device': 'DUCHAMP-RECOVERED', 'soc': 6897, 'enabled': True, 'generation': 3}
            and type(saved.get('enabled')) is bool and type(saved.get('soc')) is int and type(saved.get('generation')) is int,
        'coordination_files_carry_only_steps': all(value == '4\n' for value in metadata.values()),
        'chroot_stayed_empty': 'No such file' not in jail and not re.search(r'(?m)^\d{6}\s', jail),
        'control_pass': summary is not None,
        'at_least_two_stopped_heartbeats': re.findall(r'(?m)^heartbeat=(\d+) preferences_batch_stopped=1$', control)[:2] == ['1', '2'],
        'no_failure_or_timeout': all(not re.search(r'FAIL|TIMEOUT|PREFERENCES BATCH ERROR', text)
                                   for text in [control, *logs.values()]),
        'no_visible_panic_or_crash': result['status'] == 'no_panic_observed' and not any(
            term in screen for term in ('SWEET EARLY PANIC:', 'panic(cpu ', 'exited due to SIGSEGV',
                                        'Library not loaded:', 'Symbol not found:')),
        'decoded_framebuffer': result.get('unknown_glyphs') == 0,
        'expected_success_stop': result.get('stop_marker') == 'SWEET launchctl: heartbeat=2 ',
    }
    values = {1: ('DUCHAMP', 6897, 1, 1), 2: ('DUCHAMP-LIVE', 8300, 0, 2),
              3: ('DUCHAMP-LIVE', 8300, 0, 2), 4: ('DUCHAMP-RECOVERED', 6897, 1, 3)}
    for role, (kind, pid, steps) in roles.items():
        text = logs[role]
        initial = 2 if role == 'reader1_restarted' else 0
        checks[role + '_identity'] = f'IDENTITY pid={pid} ppid=1 uid=0 parent=/sbin/launchd' in text
        checks[role + '_expected_initial_step'] = f'BATCH READY id={kind} pid={pid} initial_step={initial}' in text
        warm = text.find('BATCH WARMUP independent_domain=1 no_fixture_access=1')
        isolated = text.find('BATCH ISOLATED chroot=empty cwd=/ direct_create=ENOENT paths=3')
        first_read = text.find('BATCH VALUES')
        checks[role + '_isolated_after_warmup'] = 0 <= warm < isolated < first_read
        got = re.findall(r'(?m)^BATCH VALUES step=(\d+) generation=(\d+) device=(\S+) soc=(\d+) enabled=(\d+) refresh=synchronize direct_read=ENOENT$', text)
        wanted = [(str(step), str(values[step][3]), values[step][0], str(values[step][1]), str(values[step][2])) for step in steps]
        checks[role + '_exact_phase_values'] = got == wanted
        checks[role + '_normal_exit'] = f'BATCH NORMAL EXIT id={kind} status=0' in text
        checks[role + '_notification_cleanup'] = 'BATCH TOKEN CANCELLED valid=0 check_status=2' in text
        if kind:
            checks[role + '_no_setters'] = 'BATCH SET' not in text
            checks[role + '_real_notify_sequence'] = re.findall(
                r'(?m)^BATCH NOTIFY RECEIVED step=(\d+) state=(\d+)$', text) == [(str(s), str(s)) for s in steps]
            checks[role + '_ack_sequence'] = re.findall(r'(?m)^BATCH ACK id=' + str(kind) + r' step=(\d+)$',
                                                       text) == [str(s) for s in steps]
    for tag, runs in [('batch-writer-final', 1), ('batch-reader1-final', 2), ('batch-reader2-final', 1)]:
        checks[tag + '_normal_reaped'] = (number(cli[tag], 'runs') == runs and
            number(cli[tag], 'last exit code') == 0 and number(cli[tag], 'pid') == -1 and 'state = not running' in cli[tag])
    order = [control.find(marker) for marker in ('BATCH PHASE COMPLETE step=1', 'BATCH PHASE COMPLETE step=2',
              'BATCH DAEMON RESTART', 'BATCH READER RESTART', 'BATCH PHASE COMPLETE step=3', 'BATCH PHASE COMPLETE step=4')]
    checks['restart_recovery_in_order'] = all(pos >= 0 for pos in order) and order == sorted(order)
    report = dict(passed=all(checks.values()), scenario='cfprefs-batch', checks=checks,
                  writer_pid=writer, first_reader1_pid=first, reader1_pid=reader1, reader2_pid=reader2,
                  old_daemon_pid=old_daemon, daemon_pid=daemon, notifyd_pid=notifyd,
                  installed_file_checks=installed, saved_preferences=saved, inputs=inputs,
                  elapsed_host_seconds=result.get('elapsed_host_seconds'), sampled_frames=len(frames),
                  stop_marker=result.get('stop_marker'), framebuffer_is_sampled=True,
                  notification_semantics='Explicit program post after synchronize; no automatic CFPreferences notification claim.',
                  sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                          ('sweet-launchd-service', 'sweet-ipc-client', 'sweet-launchctl-control',
                           'root.hfs', 'payload.bin', 'run/ramdisk-final.hfs')})
    dest = args.report or root / 'run/verification.json'
    dest.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key not in ('installed_file_checks', 'inputs')}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
