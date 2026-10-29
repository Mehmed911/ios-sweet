#!/usr/bin/env python3
"""Copy the launchd RAM root and add pinned Procursus launchctl plus a test controller."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import tempfile


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('base', 'runtime', 'audit', 'service', 'controller', 'hfsplus', 'output'):
        ap.add_argument('--' + key, type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit('refusing to overwrite previous image')
    audit = json.loads(args.audit.read_text())
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
        for guest, expected in {
            '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
            '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
        }.items():
            run('extract', guest, str(temp / 'check'))
            if hashlib.sha256((temp / 'check').read_bytes()).hexdigest() != expected:
                raise SystemExit(f'base original executable mismatch: {guest}')
        job = temp / 'control.plist'
        job.write_bytes(plistlib.dumps(controller_job))
        files = {}
        for guest, metadata in audit['files'].items():
            if not (guest.startswith('/usr/lib/') or guest == '/bin/launchctl'):
                raise SystemExit(f'unexpected runtime path: {guest}')
            source = args.runtime / guest.lstrip('/')
            if hashlib.sha256(source.read_bytes()).hexdigest() != metadata['sha256']:
                raise SystemExit(f'audited runtime changed: {guest}')
            files[guest] = (source, '755')
        files.update({
            '/sbin/sweet-launchd-service': (args.service, '755'),
            '/sbin/sweet-launchctl-control': (args.controller, '755'),
            '/System/Library/LaunchDaemons/org.sweet.qemu.launchctl-control.plist': (job, '644'),
        })
        manifest = {}
        for guest, (source, mode) in files.items():
            run('add', str(source.resolve()), guest)
            run('chmod', mode, guest)
            run('extract', guest, str(temp / 'check'))
            data = source.read_bytes()
            if (temp / 'check').read_bytes() != data:
                raise SystemExit(f'HFS byte verification failed: {guest}')
            manifest[guest] = hashlib.sha256(data).hexdigest()
        expected_jobs = ['org.sweet.qemu.c-service.plist', 'org.sweet.qemu.launchctl-control.plist']
        if jobs() != expected_jobs:
            raise SystemExit('unexpected daemon job set')
        (args.output.parent / 'launchctl-root-manifest.json').write_text(json.dumps({
            'base_sha256': hashlib.sha256(args.base.read_bytes()).hexdigest(),
            'target_job_sha256': hashlib.sha256(target_data).hexdigest(),
            'files': manifest, 'jobs': expected_jobs, 'controller_job': controller_job,
        }, indent=2) + '\n')
    print(f'{args.output}: pinned Procursus launchctl, target and controller installed')


if __name__ == '__main__':
    main()
