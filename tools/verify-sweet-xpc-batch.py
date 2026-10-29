#!/usr/bin/env python3
"""Verify the saved two-client, two-generation Foundation/XPC QEMU fixture."""
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
    manifest = json.loads((root / 'launchctl-root-manifest.json').read_text())
    result = json.loads((root / 'run/result.json').read_text())
    guest = root / 'guest'
    guest.mkdir(exist_ok=True)

    def extract(path, name):
        target = guest / name
        target.unlink(missing_ok=True)
        subprocess.run([str(args.hfsplus.resolve()), str((root / 'run/ramdisk-final.hfs').resolve()),
                        'extract', path, str(target.resolve())], capture_output=True, check=True)
        return target.read_bytes() if target.exists() else b''

    installed = {path: hashlib.sha256(extract(path, f'installed-{index:03}')).hexdigest() == digest
                 for index, (path, digest) in enumerate(manifest['files'].items())}
    originals = {path: hashlib.sha256(extract(path, Path(path).name)).hexdigest() == digest for path, digest in {
        '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
        '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
    }.items()}
    names = ['launchctl-control.log'] + [f'ipc-batch-{role}{number}.log'
               for role in ('server', 'client') for number in (1, 2)]
    tags = ['batch-dormant-1', 'batch-running-1', 'batch-stop-1', 'batch-dormant-2',
            'batch-running-2', 'batch-stop-2', 'batch-dormant-3',
            'batch-client-1-exited', 'batch-client-2-exited']
    names += [f'launchctl-{tag}.txt' for tag in tags]
    raw = {name: extract('/private/var/tmp/' + name, name) for name in names}
    text = {name: value.decode(errors='replace') for name, value in raw.items()}
    trace = text['launchctl-control.log']
    summary = re.search(r'(?m)^BATCH CONTROL PASS servers=(\d+),(\d+) clients=(\d+),(\d+) valid=12 rejected=24$', trace)
    servers = [int(summary[i]) for i in (1, 2)] if summary else [-1, -1]
    clients = [int(summary[i]) for i in (3, 4)] if summary else [-1, -1]
    identity = re.search(r'controller pid=(\d+) ppid=1 uid=0 parent=/sbin/launchd', trace)
    observer = int(identity[1]) if identity else -1

    def integer(source, key):
        match = re.search(r'(?m)^\s*' + re.escape(key) + r' = (\d+)\s*$', source)
        return int(match[1]) if match else -1

    def state(tag, pid, runs):
        source = text[f'launchctl-{tag}.txt']
        return (integer(source, 'pid') == pid and integer(source, 'runs') == runs and
                ('state = running' in source if pid > 0 else 'state = not running' in source) and
                (pid > 0 or runs == 0 or integer(source, 'last exit code') == 0))

    job_names = ['org.sweet.qemu.c-service.plist', 'org.sweet.qemu.ipc-client1.plist',
                 'org.sweet.qemu.ipc-client2.plist', 'org.sweet.qemu.launchctl-control.plist']
    listing = subprocess.run([str(args.hfsplus.resolve()), str((root / 'run/ramdisk-final.hfs').resolve()),
                              'ls', '/System/Library/LaunchDaemons'], capture_output=True, check=True).stdout.decode()
    (guest / 'job-listing.txt').write_text(listing)
    found_jobs = re.findall(r'^\d{6}\s+\d+\s+\d+\s+\d+\s+\S+\s+\S+\s+(.*)$', listing, re.MULTILINE)
    jobs = []
    for name in job_names:
        data = extract('/System/Library/LaunchDaemons/' + name, name)
        try:
            jobs.append(plistlib.loads(data))
        except (ValueError, plistlib.InvalidFileException):
            jobs.append({})
    expected_server = dict(manifest['base_target_job'], RunAtLoad=False,
                           MachServices={'org.sweet.qemu.mach-service': True})
    audit = json.loads((root / 'runtime-audit.json').read_text())
    with (root / 'run/ramdisk-final.hfs').open('rb') as image:
        image.seek(1024)
        header = image.read(512)
    size, blocks = struct.unpack_from('>II', header, 40)
    frames = sorted((root / 'run/frames').glob('*.txt'))
    screen = '\n'.join(path.read_text() for path in frames)
    if (root / 'run/fb.txt').exists():
        screen += (root / 'run/fb.txt').read_text()
    checks = {
        'batch_scenario': manifest.get('scenario') == 'foundation-xpc-batch' and 'SCENARIO foundation-xpc-batch' in trace,
        'control_pass': summary is not None,
        'observer_identity': observer > 1,
        'two_distinct_server_generations_two_distinct_clients': min(servers + clients) > 1 and
            len(set(servers + clients + [observer])) == 5,
        'all_installed_hashes_match': bool(installed) and all(installed.values()),
        'original_launchd_xpcproxy_preserved': all(originals.values()),
        'pinned_foundation_runtime': audit['passed'] and len(audit['files']) == 82 and
            audit['files'].get('/System/Library/Frameworks/Foundation.framework/Foundation', {}).get('sha256') ==
            '182a6fb6d6c51e8e1a70e9152c84cd9d1bd65d2a1f0bda21a4ebe1be446021f2',
        'pinned_foss_launchctl': manifest['files'].get('/bin/launchctl') ==
            '11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d',
        'ram_root_128m': header[:2] == b'H+' and size * blocks == manifest.get('volume_bytes') ==
            (root / 'run/ramdisk-final.hfs').stat().st_size == 128 << 20,
        'exactly_four_jobs': found_jobs == job_names == manifest['jobs'],
        'server_policy_unchanged_except_on_demand': jobs[0] == expected_server,
        'client_jobs_match_manifest': jobs[1:3] == manifest.get('batch_client_jobs'),
        'client_arguments_and_policy': all(jobs[i].get('ProgramArguments') == ['/sbin/sweet-ipc-client', str(i)] and
            jobs[i].get('RunAtLoad') is True and jobs[i].get('KeepAlive') is False and
            'MachServices' not in jobs[i] for i in (1, 2)),
        'observer_job_matches': jobs[3] == manifest['controller_job'],
        'all_jobs_without_keepalive': all(job.get('KeepAlive') is False for job in jobs),
        'exact_cli_sequence_no_start': re.findall(r'(?m)^BEGIN (\S+)$', trace) == tags,
        'nine_cli_commands_exit_zero': re.findall(r'(?m)^CLI (\S+) status=0x00000000$', trace) == tags,
        'initial_server_dormant': state('batch-dormant-1', -1, 0),
        'first_instance_running_once': state('batch-running-1', servers[0], 1),
        'first_instance_exit_zero': state('batch-dormant-2', -1, 1),
        'second_instance_running_twice': state('batch-running-2', servers[1], 2),
        'second_instance_exit_zero': state('batch-dormant-3', -1, 2),
        'mach_registration_survives_both_exits': all('org.sweet.qemu.mach-service' in
            text[f'launchctl-batch-dormant-{i}.txt'] for i in (1, 2, 3)),
        'client1_exit_zero_runs_one': state('batch-client-1-exited', -1, 1),
        'client2_exit_zero_runs_one': state('batch-client-2-exited', -1, 1),
        'stopped_state_survives_two_heartbeats': re.findall(r'(?m)^heartbeat=(\d+) batch_stopped=1$', trace) == ['1', '2'],
        'no_diagnostic_failure': all('FAIL' not in log and 'TIMEOUT' not in log for log in text.values()),
        'no_visible_panic': result['status'] == 'no_panic_observed' and
            'SWEET EARLY PANIC:' not in screen and 'panic(cpu ' not in screen,
        'framebuffer_decoded': result.get('unknown_glyphs') == 0,
    }
    statuses = [0, 1, 0, 2, 3, 4, 5, 6, 0]
    json_hashes = {}
    json_ok, json_equal = True, True
    for generation, server in enumerate(servers, 1):
        log = text[f'ipc-batch-server{generation}.log']
        checks[f'server{generation}_root_launchd_child'] = f'IDENTITY pid={server} ppid=1 uid=0 parent=/sbin/launchd' in log
        checks[f'server{generation}_two_authenticated_clients'] = sorted(re.findall(
            r'(?m)^BATCH HELLO generation=(\d+) id=(\d+) client=(\d+) server=(\d+) active=[12]$', log)) == [
            (str(generation), str(i), str(clients[i - 1]), str(server)) for i in (1, 2)]
        checks[f'server{generation}_two_connections_closed'] = len(re.findall(
            r'(?m)^BATCH CLOSED generation=' + str(generation) + r' id=[12] client=\d+ steps=9 active=[01]$', log)) == 2
        checks[f'server{generation}_normal_exit'] = (
            f'BATCH SERVER EXIT generation={generation} server={server} status=0 accepted=2 closed=2 valid=6 rejected=12' in log)
        checks[f'server{generation}_reaped'] = f'BATCH SERVER REAPED generation={generation} server={server} ESRCH' in trace
        for kind, token in (('begin', b'begin\n'), ('close', b'close\n'), ('closed', b'closed\n')):
            name = f'batch-g{generation}-c0-{kind}'
            checks[f'g{generation}_{kind}_gate'] = extract('/private/var/tmp/' + name, name) == token
        for client_id, client in enumerate(clients, 1):
            client_log = text[f'ipc-batch-client{client_id}.log']
            expected = [(str(generation), str(client_id), str(client), str(step),
                         str(generation * 100 + client_id * 10 + step), str(status), str(server))
                        for step, status in enumerate(statuses, 1)]
            pattern = (r'(?m)^BATCH REQUEST generation=(\d+) id=(\d+) client=(\d+) step=(\d+) seq=(\d+) '
                       r'status=(\d+) server=(\d+) active=2$')
            actual = [row for row in re.findall(pattern, log) if row[1] == str(client_id)]
            checks[f'g{generation}_c{client_id}_server_all_requests'] = actual == expected
            actual = re.findall(pattern.replace('BATCH REQUEST', 'BATCH REPLY'), client_log)
            checks[f'g{generation}_c{client_id}_client_all_responses'] = [row for row in actual if row[0] == str(generation)] == expected
            checks[f'g{generation}_c{client_id}_connection_and_round_complete'] = (
                f'BATCH CONNECTED generation={generation} id={client_id} client={client} server={server}' in client_log and
                f'BATCH ROUND DONE generation={generation} id={client_id} client={client} server={server} valid=3 rejected=6' in client_log)
            for kind in ('connected', 'done'):
                name = f'batch-g{generation}-c{client_id}-{kind}'
                checks[f'g{generation}_c{client_id}_{kind}_token'] = extract('/private/var/tmp/' + name, name) == f'{server}\n'.encode()
            seqs = [generation * 100 + client_id * 10 + step for step in (1, 3, 9)]
            for role, source in (('REQUEST', client_log), ('SERVER', log), ('CLIENT', client_log)):
                found = [int(seq) for seq in re.findall(
                    r'(?m)^FOUNDATION XPC ' + role + r' POOL drained seq=(\d+)$', source) if int(seq) in seqs]
                checks[f'g{generation}_c{client_id}_{role.lower()}_pools'] = found == seqs
            for seq in seqs:
                contents = {}
                for role in ('request', 'server-reply', 'client-reply'):
                    name = f'foundation-xpc-{role}-{seq}.json'
                    contents[role] = extract('/private/var/tmp/' + name, name)
                    json_hashes[name] = hashlib.sha256(contents[role]).hexdigest()
                    expected_json = ({'device': 'duchamp', 'seq': seq, 'value': 0x10203000 + seq} if role == 'request' else
                                     {'device': 'DUCHAMP', 'soc': 6897, 'seq': seq, 'value': (0x10203000 + seq) ^ 0x5a5a5a5a})
                    try:
                        json_ok &= json.loads(contents[role]) == expected_json
                    except (ValueError, UnicodeError):
                        json_ok = False
                json_equal &= contents['server-reply'] == contents['client-reply'] != b''
    for client_id, client in enumerate(clients, 1):
        log = text[f'ipc-batch-client{client_id}.log']
        checks[f'client{client_id}_root_launchd_child'] = f'IDENTITY pid={client} ppid=1 uid=0 parent=/sbin/launchd' in log
        checks[f'client{client_id}_normal_exit'] = f'BATCH CLIENT EXIT id={client_id} client={client} status=0 rounds=2 valid=6 rejected=12' in log
    checks['all_36_foundation_json_files_decoded'] = bool(json_ok) and len(json_hashes) == 36
    checks['all_12_reply_pairs_identical'] = bool(json_equal)
    report = {'passed': all(checks.values()), 'checks': checks, 'server_pids': servers, 'client_pids': clients,
              'observer_pid': observer, 'elapsed_host_seconds': result.get('elapsed_host_seconds'),
              'sampled_frames': len(frames), 'stop_marker': result.get('stop_marker'),
              'installed_file_checks': installed, 'original_file_checks': originals,
              'foundation_json_sha256': json_hashes,
              'sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                         ('sweet-launchd-service', 'sweet-ipc-client', 'sweet-launchctl-control',
                          'root.hfs', 'payload.bin', 'run/ramdisk-final.hfs')}}
    (root / 'run/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
