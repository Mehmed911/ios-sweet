#!/usr/bin/env python3
"""Validate launchd peers over Unix sockets or native XPC and their orderly exits."""
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
    ap.add_argument('--transport', choices=('unix', 'xpc', 'foundation-xpc'), default='unix')
    ap.add_argument('--report', type=Path, help='write a separate recheck report without replacing the original')
    args = ap.parse_args()
    root = args.output
    result = json.loads((root / 'run/result.json').read_text())
    manifest = json.loads((root / 'launchctl-root-manifest.json').read_text())
    with_foundation = args.transport == 'foundation-xpc'
    native_xpc = args.transport in ('xpc', 'foundation-xpc')
    scenario = 'foundation-xpc' if with_foundation else 'xpc' if native_xpc else 'ipc'
    prefix = 'XPC ' if native_xpc else ''
    guest = root / 'guest'
    guest.mkdir(exist_ok=True)

    def run(*cmd):
        return subprocess.run([str(args.hfsplus.resolve()), str((root / 'run/ramdisk-final.hfs').resolve()),
                               *cmd], check=True, capture_output=True).stdout

    def extract(path, name):
        target = guest / name
        target.unlink(missing_ok=True)
        run('extract', path, str(target.resolve()))
        return target.read_bytes() if target.exists() else b''

    tags = ('print-server', 'print-client', 'print-client-exited', 'stop-server', 'print-server-exited')
    if native_xpc:
        tags = ('print-server-dormant',) + tags
    names = {'trace': 'launchctl-control.log', 'server': 'ipc-server.log', 'client': 'ipc-client.log',
             'server-pid': 'ipc-server.pid', 'client-pid': 'ipc-client.pid', 'release': 'ipc-client.exit'}
    names.update({tag: f'launchctl-{tag}.txt' for tag in tags})
    if native_xpc:
        names.update(begin='xpc-client.begin', done='xpc-client.done')
    raw = {key: extract('/private/var/tmp/' + name, name) for key, name in names.items()}
    data = {key: value.decode(errors='replace') for key, value in raw.items()}
    trace, server_log, client_log = data['trace'], data['server'], data['client']
    summary = re.search(r'(?m)^IPC CONTROL PASS server=(\d+) client=(\d+)$', trace)
    ready = re.search(r'(?m)^IPC READY server=(\d+) client=(\d+)$', trace)
    identity = re.search(r'controller pid=(\d+) ppid=1 uid=0 parent=/sbin/launchd', trace)
    values = summary or ready
    server, client = (int(values[1]), int(values[2])) if values else (-1, -1)
    controller = int(identity[1]) if identity else -1

    def integer(text, key):
        found = re.search(r'(?m)^\s*' + re.escape(key) + r' = (\d+)\s*$', text)
        return int(found[1]) if found else -1

    def running(tag, pid):
        return integer(data[tag], 'pid') == pid and 'state = running' in data[tag] and integer(data[tag], 'runs') == 1

    def exited(tag):
        return (integer(data[tag], 'pid') == -1 and 'state = not running' in data[tag]
                and integer(data[tag], 'runs') == 1 and integer(data[tag], 'last exit code') == 0)

    hashes = {}
    for path, expected in {
        '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
        '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
        '/bin/launchctl': '11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d',
        **{path: manifest['files'][path] for path in
           ('/sbin/sweet-launchd-service', '/sbin/sweet-ipc-client', '/sbin/sweet-launchctl-control')},
    }.items():
        hashes[path] = hashlib.sha256(extract(path, Path(path).name)).hexdigest() == expected

    jobs = {}
    for role, label in (('server', 'c-service'), ('client', 'ipc-client'), ('controller', 'launchctl-control')):
        content = extract('/System/Library/LaunchDaemons/org.sweet.qemu.' + label + '.plist', role + '.plist')
        try:
            job = plistlib.loads(content)
        except (ValueError, plistlib.InvalidFileException):
            job = {}
        jobs[role] = job if isinstance(job, dict) else {}
        if role == 'server':
            server_plist_hash = hashlib.sha256(content).hexdigest()
    listing = run('ls', '/private/var/tmp').decode(errors='replace')
    (guest / 'tmp-listing.txt').write_text(listing)
    job_listing = run('ls', '/System/Library/LaunchDaemons').decode(errors='replace')
    (guest / 'job-listing.txt').write_text(job_listing)
    job_names = re.findall(r'^\d{6}\s+\d+\s+\d+\s+\d+\s+\S+\s+\S+\s+(.*)$', job_listing, re.MULTILINE)
    statuses = [trace.find(f'CLI {tag} status=0x00000000') for tag in tags]
    exchanges = r'(?m)^' + prefix + r'EXCHANGE seq=(\d+) request=0x([0-9a-f]+) response=0x([0-9a-f]+) server=(\d+) client=(\d+)$'
    expected = [(str(seq), f'{0x10203000 + seq:08x}', f'{(0x10203000 + seq) ^ 0x5a5a5a5a:08x}',
                 str(server), str(client)) for seq in (1, 2, 3)]
    frames = sorted((root / 'run/frames').glob('*.txt'))
    screen = '\n'.join(p.read_text() for p in frames)
    if (root / 'run/fb.txt').exists():
        screen += '\n' + (root / 'run/fb.txt').read_text()
    checks = {
        'ipc_scenario': manifest.get('scenario') == scenario and 'SCENARIO ' + scenario in trace,
        **{'preserved_' + Path(path).name.replace('.', '_'): matched for path, matched in hashes.items()},
        'exactly_three_launchd_jobs': job_names == [
            'org.sweet.qemu.c-service.plist', 'org.sweet.qemu.ipc-client.plist', 'org.sweet.qemu.launchctl-control.plist'],
        'all_jobs_without_keepalive': all(j.get('KeepAlive') is False for j in jobs.values()),
        'job_launch_policy_matches': jobs['server'].get('RunAtLoad') is (not native_xpc)
            and all(jobs[role].get('RunAtLoad') is True for role in ('client', 'controller')),
        'client_job_matches_manifest': jobs['client'] == manifest.get('client_job'),
        'controller_job_matches_manifest': jobs['controller'] == manifest['controller_job'],
        'three_distinct_root_launchd_children': min(server, client, controller) > 1
            and len({server, client, controller}) == 3 and identity is not None
            and f'IDENTITY pid={server} ppid=1 uid=0 parent=/sbin/launchd' in server_log
            and f'IDENTITY pid={client} ppid=1 uid=0 parent=/sbin/launchd' in client_log,
        'all_cli_exit_zero': all(i >= 0 for i in statuses),
        'cli_order_and_no_manual_start': re.findall(r'(?m)^BEGIN (\S+)$', trace) == list(tags)
            and len(re.findall(r'(?m)^CLI \S+ status=', trace)) == len(tags) and statuses == sorted(statuses),
        'server_running_once': running('print-server', server),
        'client_running_once': running('print-client', client),
        'server_peer_pid_verified': prefix + f'PEER client={client} server={server} verified='
            + ('xpc_connection_get_pid' if native_xpc else 'LOCAL_PEERPID') in server_log,
        'client_peer_pid_verified': prefix + f'PEER client={client} server={server} verified='
            + ('xpc_connection_get_pid' if native_xpc else 'LOCAL_PEERPID') in client_log,
        'server_received_and_replied_three_frames': re.findall(exchanges, server_log) == expected,
        'client_validated_three_replies': re.findall(exchanges, client_log) == expected,
        'server_saw_peer_close': ('XPC PEER CLOSED messages=3' if native_xpc else f'PEER EOF client={client} messages=3') in server_log,
        'client_waited_after_exchange': prefix + f'READY client={client} server={server} messages=3 waiting_for_release=1' in client_log,
        'client_release_was_exact': raw['release'] == b'exit\n' and f'IPC CLIENT RELEASED pid={client}' in trace,
        'client_returned_normally': ('XPC NORMAL EXIT status=0 messages=3 connection_cancelled=1' if native_xpc
                                    else 'NORMAL EXIT status=0 messages=3 socket_closed=1') in client_log,
        'client_reaped': f'IPC CLIENT REAPED pid={client} ESRCH' in trace,
        'client_launchd_exit_zero_no_restart': exited('print-client-exited'),
        'server_installed_term_handler': 'TERM handler installed mask=0x00000000' in server_log,
        'server_cleaned_up_and_returned':
            ('XPC GRACEFUL EXIT status=0 signal=15 messages=3 peer_closed=1 connections_cancelled=1' if native_xpc
             else 'GRACEFUL EXIT status=0 signal=15 messages=3 peer_closed=1 socket_removed=1') in server_log,
        'server_reaped': f'IPC SERVER REAPED pid={server} ESRCH' in trace,
        'server_launchd_exit_zero_no_restart': exited('print-server-exited'),
        'socket_absent_in_saved_root': 'sweet-ipc.sock' not in listing
            and 'ipc-server.log' in listing and 'ipc-client.log' in listing,
        'pid_files_match_both_services': data['server-pid'].strip() == str(server) and data['client-pid'].strip() == str(client),
        'control_pass': summary is not None,
        'stopped_state_survives': len(re.findall(r'heartbeat=\d+ ipc_stopped=1 server=' + str(server)
            + ' client=' + str(client), trace)) >= 2,
        'no_diagnostic_failure': all('FAIL' not in log and 'TIMEOUT' not in log for log in (trace, server_log, client_log)),
        'no_visible_panic': result['status'] == 'no_panic_observed'
            and 'SWEET EARLY PANIC:' not in screen and 'panic(cpu ' not in screen,
        'screen_decoded': result.get('unknown_glyphs') == 0,
    }
    if native_xpc:
        expected_job = dict(manifest['base_target_job'], RunAtLoad=False,
                            MachServices={'org.sweet.qemu.mach-service': True})
        checks.update({
            'server_machservice_configured': jobs['server'] == expected_job
                and server_plist_hash == manifest['target_job_sha256'],
            'only_server_advertises_machservice': all('MachServices' not in jobs[role] for role in ('client', 'controller')),
            'on_demand_server_initially_dormant': integer(data['print-server-dormant'], 'pid') == -1
                and integer(data['print-server-dormant'], 'runs') == 0
                and 'org.sweet.qemu.mach-service' in data['print-server-dormant']
                and 'XPC DORMANT verified runs=0 no pid' in trace,
            'on_demand_gate_tokens': raw['begin'] == b'begin\n' and raw['done'] == b'done\n',
            'broker_registration_survives_exit': 'org.sweet.qemu.mach-service' in data['print-server-exited'],
        })
    else:
        checks['server_job_unchanged'] = jobs['server'] == manifest['base_target_job'] \
            and server_plist_hash == manifest['base_target_job_sha256'] == manifest['target_job_sha256']
    foundation_files = {}
    installed_checks = {}
    if with_foundation:
        for index, (path, expected_hash) in enumerate(manifest['files'].items()):
            installed_checks[path] = hashlib.sha256(extract(path, f'installed-{index:03}')).hexdigest() == expected_hash
        for seq in (1, 2, 3):
            for role in ('request', 'server-reply', 'client-reply'):
                name = f'foundation-xpc-{role}-{seq}.json'
                foundation_files[role, seq] = extract('/private/var/tmp/' + name, name)
        decoded = {}
        for key, content in foundation_files.items():
            try:
                decoded[key] = json.loads(content)
            except (ValueError, UnicodeError):
                decoded[key] = None
        with (root / 'run/ramdisk-final.hfs').open('rb') as image:
            image.seek(1024)
            header = image.read(512)
        block_size, blocks = struct.unpack_from('>II', header, 40)
        audit = json.loads((root / 'runtime-audit.json').read_text())
        checks.update({
            'foundation_dependency_closure': audit['passed'] and len(audit['files']) == 82,
            'all_installed_foundation_bytes_preserved': all(installed_checks.values()),
            'original_foundation_pinned': audit['files'].get('/System/Library/Frameworks/Foundation.framework/Foundation', {}).get('sha256') ==
                '182a6fb6d6c51e8e1a70e9152c84cd9d1bd65d2a1f0bda21a4ebe1be446021f2',
            'grown_ram_volume_128m': manifest.get('volume_bytes') == 128 << 20 and header[:2] == b'H+'
                and block_size * blocks == 128 << 20 and (root / 'run/ramdisk-final.hfs').stat().st_size == 128 << 20,
            'three_foundation_requests_received': all(decoded['request', seq] ==
                {'device': 'duchamp', 'seq': seq, 'value': 0x10203000 + seq} for seq in (1, 2, 3)),
            'three_foundation_server_replies': all(decoded['server-reply', seq] ==
                {'device': 'DUCHAMP', 'soc': 6897, 'seq': seq, 'value': (0x10203000 + seq) ^ 0x5a5a5a5a} for seq in (1, 2, 3)),
            'three_foundation_client_replies': all(decoded['client-reply', seq] == decoded['server-reply', seq]
                and decoded['client-reply', seq] is not None for seq in (1, 2, 3)),
            'xpc_json_bytes_match_end_to_end': all(foundation_files['server-reply', seq] ==
                foundation_files['client-reply', seq] != b'' for seq in (1, 2, 3)),
            'client_request_pools_drained': re.findall(r'(?m)^FOUNDATION XPC REQUEST POOL drained seq=(\d+)$', client_log) == ['1', '2', '3'],
            'server_callback_pools_drained': re.findall(r'(?m)^FOUNDATION XPC SERVER POOL drained seq=(\d+)$', server_log) == ['1', '2', '3'],
            'client_reply_pools_drained': re.findall(r'(?m)^FOUNDATION XPC CLIENT POOL drained seq=(\d+)$', client_log) == ['1', '2', '3'],
            'server_json_lengths_match_saved_files': re.findall(
                r'(?m)^FOUNDATION XPC SERVER seq=(\d+) request_bytes=(\d+) reply_bytes=(\d+)$', server_log) ==
                [(str(seq), str(len(foundation_files['request', seq])), str(len(foundation_files['server-reply', seq]))) for seq in (1, 2, 3)],
            'client_json_lengths_match_saved_files': re.findall(
                r'(?m)^FOUNDATION XPC CLIENT VALIDATED seq=(\d+) bytes=(\d+)$', client_log) ==
                [(str(seq), str(len(foundation_files['client-reply', seq]))) for seq in (1, 2, 3)],
        })
    report = {'passed': all(checks.values()), 'scenario': scenario, 'checks': checks,
              'server_pid': server, 'client_pid': client, 'controller_pid': controller,
              'ipc_method': ('Apple libxpc MachServices, on-demand activation, three dictionary request/replies' if native_xpc
                             else 'AF_UNIX SOCK_STREAM, LOCAL_PEERPID, three 32-byte request/reply frames'),
              'launchctl_variant': 'Procursus FOSS 1:1.1.1, unchanged packaged binary',
              'elapsed_host_seconds': result.get('elapsed_host_seconds'), 'stop_marker': result.get('stop_marker'),
              'sampled_frames': len(frames), 'framebuffer_is_sampled': True,
              'sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                         ('sweet-launchd-service', 'sweet-ipc-client', 'sweet-launchctl-control',
                          'root.hfs', 'payload.bin', 'run/ramdisk-final.hfs')},
              'guest_file_sha256': {key: hashlib.sha256(value).hexdigest() for key, value in raw.items()}}
    if with_foundation:
        report.update(installed_file_checks=installed_checks,
                      foundation_json_sha256={f'{role}-{seq}': hashlib.sha256(value).hexdigest()
                                             for (role, seq), value in foundation_files.items()})
        report['ipc_method'] = 'Original Foundation JSON/NSData over native Apple libxpc MachServices'
    (args.report or root / 'run/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
