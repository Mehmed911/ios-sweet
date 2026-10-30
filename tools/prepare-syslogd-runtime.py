#!/usr/bin/env python3
"""Add the pinned, unmodified iOS restore syslogd to a local launchctl closure."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import runpy
import shutil
import subprocess

SYSLOGD = '86838d9149bb898e3d39266fea884c6c92eeac1e6486c072b135a879c9eeaabe'
APFS = 'abf6d0281cffd6fdead38043e0a6291189164d2c06383218adcb95d8dc25efc8'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'libraries', 'apple', 'apfs', 'output'):
        ap.add_argument(name, type=Path)
    ap.add_argument('--notifyd-root', type=Path, help='matching system-image extraction, kept local')
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit('refusing to overwrite an existing runtime')
    if hashlib.sha256(args.apfs.read_bytes()).hexdigest() != APFS:
        raise SystemExit('requires the pinned 20F66 restore APFS')
    roots = [args.base.resolve(), args.apple.resolve(), args.libraries.resolve()]
    if args.notifyd_root:
        roots.append(args.notifyd_root.resolve())

    def locate(guest):
        if not guest.startswith('/'):
            raise SystemExit('unresolved dependency: ' + guest)
        for root in roots:
            path = (root / guest.lstrip('/')).resolve()
            if path.is_relative_to(root) and path.is_file():
                return path
        raise SystemExit('missing dependency: ' + guest)

    if hashlib.sha256(locate('/usr/sbin/syslogd').read_bytes()).hexdigest() != SYSLOGD:
        raise SystemExit('syslogd source mismatch')
    original_path = args.apple / 'System/Library/LaunchDaemons/com.apple.syslogd.plist'
    original = original_path.read_bytes()
    original_job = plistlib.loads(original)
    if (original_job.get('Label') != 'com.apple.syslogd' or original_job.get('Disabled') is not True
            or original_job.get('ProgramArguments') != ['/usr/sbin/syslogd']
            or original_job.get('MachServices') != {'com.apple.system.logger': True}
            or original_job.get('EnvironmentVariables') != {'ASL_DISABLE': '1'}):
        raise SystemExit('unexpected original syslogd job')
    macho = runpy.run_path(str(Path(__file__).with_name('audit-darwin-runtime.py')))['macho']
    todo, files = ['/usr/sbin/syslogd', '/bin/launchctl', '/usr/lib/dyld'], {}
    notifyd_source = None
    if args.notifyd_root:
        binary = locate('/usr/sbin/notifyd')
        job_bytes = (args.notifyd_root / 'System/Library/LaunchDaemons/com.apple.notifyd.plist').read_bytes()
        if (hashlib.sha256(binary.read_bytes()).hexdigest() !=
                '819c8ec6b3bee5cd2f1dcbe0b2b698418c411b4c126f2f97cbdae932c1972907'
                or hashlib.sha256(job_bytes).hexdigest() !=
                '627b24feb59a493a50f488bc62ec9e878c333757d4ddb7786a977650ed9b1a05'):
            raise SystemExit('requires the pinned system-image notifyd and job')
        notifyd_source = dict(original_job=plistlib.loads(job_bytes),
                              binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                              original_plist_sha256=hashlib.sha256(job_bytes).hexdigest(),
                              ipsw_member='096-04088-077.dmg', system_volume='SydneyF20F66.D22D221OS',
                              source_version='Libnotify-312',
                              source_reference='https://github.com/apple-oss-distributions/Libnotify/tree/885677be0379101ccf37b46f8da81dbc17d6d301')
        todo.append('/usr/sbin/notifyd')
    while todo:
        guest = todo.pop()
        if guest in files:
            continue
        path = locate(guest)
        item = macho(path)
        files[guest] = (path, item)
        if item['dylinker']:
            todo.append(item['dylinker'])
        for dep in item['dependencies']:
            if dep['weak']:
                continue
            target = dep['path']
            if target.startswith('@rpath/'):
                target = next((p.rstrip('/') + '/' + target[7:] for p in item['rpaths']
                               if p.startswith('/') and any((root / (p.rstrip('/') + '/' + target[7:]).lstrip('/')).is_file()
                                                            for root in roots)), target)
            todo.append(target)
    args.output.mkdir(parents=True)
    runtime = args.output / 'runtime-root'
    for guest, (source, item) in files.items():
        target = runtime / guest.lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (args.output / 'syslogd-original.plist').write_bytes(original)
    (args.output / 'source.json').write_text(json.dumps({
        'restore_apfs_sha256': APFS, 'syslogd_sha256': SYSLOGD,
        'original_plist_sha256': hashlib.sha256(original).hexdigest(), 'original_job': original_job,
        'notifyd_source': notifyd_source,
        'files': {guest: item['sha256'] for guest, (_, item) in files.items()},
        'source_reference': 'https://github.com/apple-oss-distributions/syslog/tree/69d8586e9a599c304e1b702a9c2830e2f78126d5',
        'note': 'Original Apple artifacts stay local; source reference informs ABI/config, not exact binary equivalence.',
    }, indent=2) + '\n')
    extra = ['--entry', '/usr/sbin/notifyd'] if args.notifyd_root else []
    subprocess.run(['python3', str(Path(__file__).with_name('audit-darwin-runtime.py')), str(runtime),
                    str(args.output / 'runtime-audit.json'), '--entry', '/usr/sbin/syslogd',
                    '--entry', '/bin/launchctl', *extra], check=True)


if __name__ == '__main__':
    main()
