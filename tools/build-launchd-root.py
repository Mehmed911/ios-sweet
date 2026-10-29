#!/usr/bin/env python3
"""Copy a tested dynamic RAM root and install original launchd plus one service."""
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
    for name in ('base', 'apple', 'bootstrap', 'service', 'hfsplus', 'output'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit('refusing to overwrite existing output')
    original = args.apple / 'sbin/launchd'
    proxy = args.apple / 'usr/libexec/xpcproxy'
    expected = {
        original: '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
        proxy: '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
        args.apple / 'private/etc/master.passwd':
            '63e2af613e38f5fc62aaea45cb9b57313470905cc42639639a92a925e65a7953',
        args.apple / 'private/etc/group':
            '8a7a3ac2dac006546cb233fbec2a458a7d1431631227dca090f1cb3e1f692458',
    }
    for file, digest in expected.items():
        if hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            raise SystemExit(f'original Apple file hash mismatch: {file}')
    shutil.copyfile(args.base, args.output)

    def run(*command):
        return subprocess.run([str(args.hfsplus.resolve()), str(args.output.resolve()),
                               *command], check=True, capture_output=True, text=True).stdout

    directories = ['/private', '/private/etc', '/private/var',
                   '/private/var/tmp', '/private/var/run', '/private/var/root',
                   '/private/var/mobile',
                   '/private/var/empty', '/private/var/log', '/private/var/db',
                   '/private/var/log/com.apple.xpc.launchd',
                   '/private/var/db/com.apple.xpc.launchd', '/private/var/db/launchd.db',
                   '/System', '/System/Library', '/System/Library/xpc',
                   '/System/Library/LaunchDaemons', '/System/Library/LaunchAgents',
                   '/System/Library/LaunchAngels', '/System/Library/NanoLaunchDaemons',
                   '/System/Library/NanoLaunchDaemonsAltAccount',
                   '/System/Library/DeveloperModeLaunchDaemons',
                   '/AppleInternal', '/AppleInternal/Library',
                   '/AppleInternal/Library/LaunchDaemons', '/AppleInternal/Library/LaunchAngels',
                   '/Library', '/Library/LaunchDaemons', '/Library/LaunchAgents',
                   '/usr/appleinternal', '/usr/appleinternal/sbin', '/usr/libexec']
    for directory in directories:
        run('mkdir', directory)
        run('chmod', '755', directory)
    for link, target in [('/var', '/private/var'), ('/tmp', '/private/var/tmp'),
                         ('/etc', '/private/etc')]:
        run('symlink', link, target)
    run('chmod', '1777', '/private/var/tmp')
    service = {
        'Label': 'org.sweet.qemu.c-service',
        'ProgramArguments': ['/sbin/sweet-launchd-service'],
        'RunAtLoad': True, 'KeepAlive': False,
        'UserName': 'root', 'GroupName': 'wheel', 'LimitLoadToSessionType': 'System',
        'StandardOutPath': '/dev/console', 'StandardErrorPath': '/dev/console',
    }
    with tempfile.TemporaryDirectory(prefix='sweet-launchd-root-') as scratch:
        temp = Path(scratch)
        job = temp / 'service.plist'
        job.write_bytes(plistlib.dumps(service))
        accounts = []
        for line in (args.apple / 'private/etc/master.passwd').read_text().splitlines():
            if not line or line.startswith('#'):
                continue
            fields = line.split(':')
            if len(fields) != 10:
                raise SystemExit('unexpected master.passwd field count')
            fields[1] = '*'  # Retain original IDs, lock all test-root passwords.
            accounts.append(fields)
        passwd = temp / 'passwd'
        passwd.write_text(''.join(':'.join(f[:4] + f[7:]) + '\n' for f in accounts))
        master = temp / 'master.passwd'
        master.write_text(''.join(':'.join(f) + '\n' for f in accounts))
        group = temp / 'group'
        group.write_bytes((args.apple / 'private/etc/group').read_bytes())
        files = {
            '/sbin/launchd': (original, '755'),
            '/usr/libexec/xpcproxy': (proxy, '755'),
            '/usr/appleinternal/sbin/launchd.sweet': (args.bootstrap, '755'),
            '/sbin/sweet-launchd-service': (args.service, '755'),
            '/System/Library/LaunchDaemons/org.sweet.qemu.c-service.plist': (job, '644'),
            '/private/etc/passwd': (passwd, '644'),
            '/private/etc/master.passwd': (master, '600'),
            '/private/etc/group': (group, '644'),
        }
        manifest = {}
        for guest, (host, mode) in files.items():
            run('add', str(host.resolve()), guest)
            run('chmod', mode, guest)
            extracted = temp / 'roundtrip'
            run('extract', guest, str(extracted))
            if extracted.read_bytes() != host.read_bytes():
                raise SystemExit(f'HFS roundtrip failed: {guest}')
            manifest[guest] = hashlib.sha256(host.read_bytes()).hexdigest()
        listing = run('ls', '/System/Library/LaunchDaemons')
        jobs = re.findall(r'^\d{6}\s+\d+\s+\d+\s+\d+\s+\S+\s+\S+\s+(.*)$',
                          listing, re.MULTILINE)
        if jobs != ['org.sweet.qemu.c-service.plist']:
            raise SystemExit(f'expected exactly one configured service, found {jobs}')
        (args.output.parent / 'launchd-root-manifest.json').write_text(
            json.dumps({'files': manifest, 'configuration': 'original embedded __TEXT,__config',
                        'service': service, 'service_files': jobs,
                        'base_sha256': hashlib.sha256(args.base.read_bytes()).hexdigest()},
                       indent=2) + '\n')
    print(f'{args.output}: original launchd, xpcproxy, bootstrap, one C service installed')


if __name__ == '__main__':
    main()
