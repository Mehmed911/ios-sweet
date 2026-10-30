#!/usr/bin/env python3
"""Copy the launchd RAM root and add pinned Procursus launchctl plus a test controller."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import struct
import subprocess
import tempfile


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('base', 'runtime', 'audit', 'service', 'controller', 'hfsplus', 'output'):
        ap.add_argument('--' + key, type=Path, required=True)
    ap.add_argument('--scenario', choices=('stop-restart', 'bootout-bootstrap', 'keepalive', 'ipc', 'xpc', 'foundation', 'foundation-xpc', 'foundation-xpc-batch', 'syslogd', 'notifyd', 'cfprefsd', 'cfprefs-batch'),
                    default='stop-restart')
    ap.add_argument('--client', type=Path)
    ap.add_argument('--runtime-source', type=Path)
    args = ap.parse_args()
    batch = args.scenario == 'foundation-xpc-batch'
    prefs_batch = args.scenario == 'cfprefs-batch'
    cfprefs = args.scenario in ('cfprefsd', 'cfprefs-batch')
    syslogd = args.scenario in ('syslogd', 'notifyd', 'cfprefsd', 'cfprefs-batch')
    notifyd = args.scenario in ('notifyd', 'cfprefsd', 'cfprefs-batch')
    foundation_scenario = args.scenario in ('foundation', 'foundation-xpc', 'foundation-xpc-batch', 'cfprefsd', 'cfprefs-batch')
    native_xpc = args.scenario in ('xpc', 'foundation-xpc', 'foundation-xpc-batch')
    client_scenario = args.scenario in ('ipc', 'xpc', 'foundation-xpc', 'foundation-xpc-batch', 'syslogd', 'notifyd', 'cfprefsd', 'cfprefs-batch')
    if client_scenario and args.client is None:
        ap.error('IPC scenarios require --client')
    if args.output.exists():
        raise SystemExit('refusing to overwrite previous image')
    audit = json.loads(args.audit.read_text())
    syslogd_source, syslogd_job = None, None
    notifyd_job = None
    prefs_jobs = {}
    if syslogd:
        if args.runtime_source is None:
            raise SystemExit('syslogd requires --runtime-source')
        syslogd_source = json.loads(args.runtime_source.read_text())
        if (audit['files'].get('/usr/sbin/syslogd', {}).get('sha256') !=
                '86838d9149bb898e3d39266fea884c6c92eeac1e6486c072b135a879c9eeaabe'):
            raise SystemExit('requires the pinned original syslogd')
        syslogd_job = dict(syslogd_source['original_job'])
        syslogd_job.update(Disabled=False, RunAtLoad=True, KeepAlive=False,
                          UserName='root', GroupName='wheel', LimitLoadToSessionType='System',
                          StandardOutPath='/dev/console', StandardErrorPath='/dev/console',
                          ProgramArguments=['/usr/sbin/syslogd', '-d', '/private/var/tmp/syslogd-debug.log',
                                            '-config', 'iphone', '-klog_in', '0', '-udp_in', '0',
                                            '-bsd_out', '0', '-remote', '0', '-launchd_in', '0', '-m', '0'])
        if notifyd:
            if audit['files'].get('/usr/sbin/notifyd', {}).get('sha256') != (
                    '819c8ec6b3bee5cd2f1dcbe0b2b698418c411b4c126f2f97cbdae932c1972907'):
                raise SystemExit('requires the pinned original notifyd')
            notifyd_job = dict(syslogd_source['notifyd_source']['original_job'])
            notifyd_job.update(RunAtLoad=True, KeepAlive=False, UserName='root', GroupName='wheel',
                               StandardOutPath='/dev/console', StandardErrorPath='/dev/console',
                               ProgramArguments=['/usr/sbin/notifyd', '-d', '-log_file',
                                                 '/private/var/tmp/notifyd-debug.log', '-shm_pages', '0'])
    if cfprefs:
        if audit['files'].get('/usr/sbin/cfprefsd', {}).get('sha256') != (
                '05e6c217284c2e4f669243fe24296f3ba9abb53a750c9d3860348b0b43c978e2'):
            raise SystemExit('requires the pinned original cfprefsd')
        for name, source in syslogd_source['cfprefsd_source']['original_jobs'].items():
            entry = dict(source['original_job'])
            # Enable both original native endpoints on demand in the test System
            # session; record which one the unmodified CoreFoundation selects.
            entry.update(Disabled=False, RunAtLoad=False, KeepAlive=False,
                         UserName='root', GroupName='wheel', LimitLoadToSessionType='System',
                         StandardOutPath='/dev/console', StandardErrorPath='/dev/console')
            prefs_jobs[name] = entry
    if not audit['passed'] or '/bin/launchctl' not in audit['files']:
        raise SystemExit('launchctl and required libraries must pass the dependency audit')
    if audit['files']['/bin/launchctl']['sha256'] != (
            '11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d'):
        raise SystemExit('requires the pinned Procursus launchctl binary')
    shutil.copyfile(args.base, args.output)

    def run(*cmd):
        return subprocess.run([str(args.hfsplus.resolve()), str(args.output.resolve()), *cmd],
                              check=True, capture_output=True, text=True).stdout

    def jobs():
        listing = run('ls', '/System/Library/LaunchDaemons')
        return re.findall(r'^\d{6}\s+\d+\s+\d+\s+\d+\s+\S+\s+\S+\s+(.*)$',
                          listing, re.MULTILINE)

    if foundation_scenario:
        foundation = '/System/Library/Frameworks/Foundation.framework/Foundation'
        if (audit['files'].get(foundation, {}).get('sha256') !=
                '182a6fb6d6c51e8e1a70e9152c84cd9d1bd65d2a1f0bda21a4ebe1be446021f2'):
            raise SystemExit('requires the pinned Foundation closure')
        if args.runtime_source is None:
            raise SystemExit('Foundation requires --runtime-source')
        run('grow', str(128 << 20))
        with args.output.open('rb') as image:
            image.seek(1024)
            header = image.read(512)
        block_size, blocks = struct.unpack_from('>II', header, 40)
        if header[:2] != b'H+' or blocks * block_size != 128 << 20 or args.output.stat().st_size != 128 << 20:
            raise SystemExit('HFS growth did not produce the expected 128 MiB volume')

    if jobs() != ['org.sweet.qemu.c-service.plist']:
        raise SystemExit('base must have exactly the existing target job')
    controller_job = {
        'Label': 'org.sweet.qemu.launchctl-control',
        'ProgramArguments': ['/sbin/sweet-launchctl-control'],
        'UserName': 'root', 'GroupName': 'wheel', 'LimitLoadToSessionType': 'System',
        'RunAtLoad': True, 'KeepAlive': False,
        'StandardOutPath': '/dev/console', 'StandardErrorPath': '/dev/console',
    }
    if 'No such file or directory' in run('ls', '/bin'):
        run('mkdir', '/bin')
        run('chmod', '755', '/bin')
    with tempfile.TemporaryDirectory(prefix='sweet-launchctl-') as scratch:
        temp = Path(scratch)
        target_job = '/System/Library/LaunchDaemons/org.sweet.qemu.c-service.plist'
        run('extract', target_job, str(temp / 'target.plist'))
        target_data = (temp / 'target.plist').read_bytes()
        properties = plistlib.loads(target_data)
        if (properties.get('Label') != 'org.sweet.qemu.c-service'
                or properties.get('RunAtLoad') is not True
                or properties.get('KeepAlive') is not False):
            raise SystemExit('target must be the RunAtLoad, non-KeepAlive diagnostic service')
        installed_target_data = target_data
        if syslogd:
            properties['ProgramArguments'] = ['/sbin/sweet-launchd-service', '1']
            properties['EnvironmentVariables'] = {'ASL_DISABLE': '0'}
            installed_target_data = plistlib.dumps(properties)
            (temp / 'syslogd-probe.plist').write_bytes(installed_target_data)
            (temp / 'syslogd.plist').write_bytes(plistlib.dumps(syslogd_job))
            if notifyd:
                (temp / 'notifyd.plist').write_bytes(plistlib.dumps(notifyd_job))
        if args.scenario == 'keepalive':
            properties['KeepAlive'] = True
            installed_target_data = plistlib.dumps(properties)
            (temp / 'keepalive.plist').write_bytes(installed_target_data)
        if native_xpc:
            properties['RunAtLoad'] = False
            properties['MachServices'] = {'org.sweet.qemu.mach-service': True}
            installed_target_data = plistlib.dumps(properties)
            (temp / 'xpc.plist').write_bytes(installed_target_data)
        if cfprefs:
            properties['ProgramArguments'] = ['/sbin/sweet-launchd-service']
            properties['EnvironmentVariables'] = {'HOME': '/var/root', 'ASL_DISABLE': '0'}
            installed_target_data = plistlib.dumps(properties)
            (temp / 'syslogd-probe.plist').write_bytes(installed_target_data)
            for name, entry in prefs_jobs.items():
                (temp / name).write_bytes(plistlib.dumps(entry))
            for name in ('/private/var/root', '/private/var/root/Library',
                         '/private/var/root/Library/Preferences', '/Library', '/Library/Preferences',
                         '/private/var/tmp/preferences-empty-root'):
                if 'No such file or directory' in run('ls', name):
                    run('mkdir', name)
                    run('chmod', '755', name)
        for guest, expected in {
            '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
            '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
        }.items():
            run('extract', guest, str(temp / 'check'))
            if hashlib.sha256((temp / 'check').read_bytes()).hexdigest() != expected:
                raise SystemExit(f'base original executable mismatch: {guest}')
        job = temp / 'control.plist'
        job.write_bytes(plistlib.dumps(controller_job))
        client_job = None
        batch_client_jobs = []
        prefs_batch_jobs = []
        if prefs_batch:
            for number in (1, 2):
                entry = dict(plistlib.loads(target_data), Label=f'org.sweet.qemu.prefs-reader{number}',
                             ProgramArguments=['/sbin/sweet-ipc-client', str(number)],
                             RunAtLoad=True, KeepAlive=False,
                             EnvironmentVariables={'HOME': '/var/root', 'ASL_DISABLE': '0'})
                prefs_batch_jobs.append(entry)
                (temp / f'prefs-reader{number}.plist').write_bytes(plistlib.dumps(entry))
        elif batch:
            for number in (1, 2):
                entry = dict(plistlib.loads(target_data), Label=f'org.sweet.qemu.ipc-client{number}',
                             ProgramArguments=['/sbin/sweet-ipc-client', str(number)])
                batch_client_jobs.append(entry)
                (temp / f'client{number}.plist').write_bytes(plistlib.dumps(entry))
        elif client_scenario:
            client_job = dict(plistlib.loads(target_data), Label='org.sweet.qemu.ipc-client',
                              ProgramArguments=['/sbin/sweet-ipc-client'])
            if syslogd:
                client_job.update(ProgramArguments=['/sbin/sweet-ipc-client', '2'],
                                  EnvironmentVariables={'ASL_DISABLE': '0'})
            if cfprefs:
                client_job.update(RunAtLoad=False, ProgramArguments=['/sbin/sweet-ipc-client'],
                                  EnvironmentVariables={'HOME': '/var/root', 'ASL_DISABLE': '0'})
            (temp / 'client.plist').write_bytes(plistlib.dumps(client_job))
        files = {}
        for guest, metadata in audit['files'].items():
            framework = foundation_scenario and guest.startswith(
                ('/System/Library/Frameworks/', '/System/Library/PrivateFrameworks/'))
            if not (guest.startswith('/usr/lib/') or guest == '/bin/launchctl' or framework
                    or (syslogd and guest == '/usr/sbin/syslogd')
                    or (notifyd and guest == '/usr/sbin/notifyd')
                    or (cfprefs and guest == '/usr/sbin/cfprefsd')):
                raise SystemExit(f'unexpected runtime path: {guest}')
            source = args.runtime / guest.lstrip('/')
            if hashlib.sha256(source.read_bytes()).hexdigest() != metadata['sha256']:
                raise SystemExit(f'audited runtime changed: {guest}')
            files[guest] = (source, '755')
        if foundation_scenario:
            resources = json.loads(args.runtime_source.read_text())['resources']
            for guest, digest in resources.items():
                if not guest.startswith(('/System/Library/Frameworks/', '/System/Library/PrivateFrameworks/')):
                    raise SystemExit('unexpected Foundation resource: ' + guest)
                source = args.runtime / guest.lstrip('/')
                if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                    raise SystemExit('Foundation resource changed: ' + guest)
                files[guest] = (source, '644')
        files.update({
            '/sbin/sweet-launchd-service': (args.service, '755'),
            '/sbin/sweet-launchctl-control': (args.controller, '755'),
            '/System/Library/LaunchDaemons/org.sweet.qemu.launchctl-control.plist': (job, '644'),
        })
        if args.scenario == 'keepalive':
            files[target_job] = (temp / 'keepalive.plist', '644')
        if native_xpc:
            files[target_job] = (temp / 'xpc.plist', '644')
        if syslogd:
            files[target_job] = (temp / 'syslogd-probe.plist', '644')
            files['/System/Library/LaunchDaemons/com.apple.syslogd.plist'] = (temp / 'syslogd.plist', '644')
            files['/private/etc/asl.conf'] = (Path(__file__).resolve().parent.parent / 'duchamp/syslogd-asl.conf', '644')
            if 'No such file or directory' in run('ls', '/private/etc/asl'):
                run('mkdir', '/private/etc/asl')
                run('chmod', '755', '/private/etc/asl')
        if notifyd:
            files['/System/Library/LaunchDaemons/com.apple.notifyd.plist'] = (temp / 'notifyd.plist', '644')
        if cfprefs:
            for name in prefs_jobs:
                files['/System/Library/LaunchDaemons/' + name] = (temp / name, '644')
        if client_scenario:
            files['/sbin/sweet-ipc-client'] = (args.client, '755')
        if prefs_batch:
            for number in (1, 2):
                files[f'/System/Library/LaunchDaemons/org.sweet.qemu.prefs-reader{number}.plist'] = (temp / f'prefs-reader{number}.plist', '644')
        elif batch:
            for number in (1, 2):
                files[f'/System/Library/LaunchDaemons/org.sweet.qemu.ipc-client{number}.plist'] = (temp / f'client{number}.plist', '644')
        elif client_scenario:
            files['/System/Library/LaunchDaemons/org.sweet.qemu.ipc-client.plist'] = (temp / 'client.plist', '644')
        manifest = {}
        directories = {'/'}
        for guest, (source, mode) in files.items():
            for parent in reversed(Path(guest).parents):
                name = parent.as_posix()
                if name not in directories:
                    if 'No such file or directory' in run('ls', name):
                        run('mkdir', name)
                        run('chmod', '755', name)
                    directories.add(name)
            run('add', str(source.resolve()), guest)
            run('chmod', mode, guest)
            (temp / 'check').unlink(missing_ok=True)
            run('extract', guest, str(temp / 'check'))
            data = source.read_bytes()
            if (temp / 'check').read_bytes() != data:
                raise SystemExit(f'HFS byte verification failed: {guest}')
            manifest[guest] = hashlib.sha256(data).hexdigest()
        expected_jobs = ['org.sweet.qemu.c-service.plist', 'org.sweet.qemu.launchctl-control.plist']
        if prefs_batch:
            expected_jobs[1:1] = ['org.sweet.qemu.prefs-reader1.plist', 'org.sweet.qemu.prefs-reader2.plist']
        elif batch:
            expected_jobs[1:1] = ['org.sweet.qemu.ipc-client1.plist', 'org.sweet.qemu.ipc-client2.plist']
        elif client_scenario:
            expected_jobs.insert(1, 'org.sweet.qemu.ipc-client.plist')
        if syslogd:
            expected_jobs.insert(0, 'com.apple.syslogd.plist')
        if notifyd:
            expected_jobs.insert(0, 'com.apple.notifyd.plist')
        if cfprefs:
            expected_jobs = sorted(expected_jobs + list(prefs_jobs))
        if jobs() != expected_jobs:
            raise SystemExit('unexpected daemon job set')
        (args.output.parent / 'launchctl-root-manifest.json').write_text(json.dumps({
            'base_sha256': hashlib.sha256(args.base.read_bytes()).hexdigest(),
            'base_target_job_sha256': hashlib.sha256(target_data).hexdigest(),
            'base_target_job': plistlib.loads(target_data),
            'target_job_sha256': hashlib.sha256(installed_target_data).hexdigest(),
            'scenario': args.scenario,
            'client_job': client_job,
            'batch_client_jobs': batch_client_jobs,
            'prefs_batch_jobs': prefs_batch_jobs,
            'syslogd_source': syslogd_source, 'syslogd_job': syslogd_job,
            'notifyd_job': notifyd_job,
            'cfprefsd_jobs': prefs_jobs,
            'volume_bytes': args.output.stat().st_size,
            'files': manifest, 'jobs': expected_jobs, 'controller_job': controller_job,
        }, indent=2) + '\n')
    print(f'{args.output}: pinned Procursus launchctl, target and controller installed')


if __name__ == '__main__':
    main()
