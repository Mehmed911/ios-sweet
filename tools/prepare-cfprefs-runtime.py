#!/usr/bin/env python3
"""Merge pinned Foundation/daemon closures and the matching original cfprefsd."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import runpy
import shutil
import subprocess

CFPREFSD = '05e6c217284c2e4f669243fe24296f3ba9abb53a750c9d3860348b0b43c978e2'
DYNAMIC_PINS = {
    '/System/Library/Frameworks/MobileCoreServices.framework/MobileCoreServices':
        '1b78c1e4f3bc986e060e2a6d189172b0f34215c7dc4555ae3203547bc7266f77',
    '/System/Library/Frameworks/CoreServices.framework/CoreServices':
        '4a0a92937739cb822207a08fdb7b95206684433f32a6170efecf22187250896d',
}
JOBS = {
    'com.apple.cfprefsd.xpc.daemon.plist': '16aa60c1effb6b7e7775712582bf4572c56ca1a25d1aca322eb822b03a06189f',
    'com.apple.cfprefsd.xpc.daemon.system.plist': 'a34c6b85e29c1523d84597c81393e048c70274e5871c346d1969a7d413658f77',
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('foundation', 'daemons', 'apple', 'output'):
        ap.add_argument(key, type=Path)
    ap.add_argument('--dynamic-root', type=Path, required=True, help='matching original restore frameworks/libraries')
    ap.add_argument('--apfs', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit('refusing to overwrite an existing runtime')
    metadata = [json.loads((p.parent / 'source.json').read_text())
                for p in (args.foundation, args.daemons)]
    if metadata[0]['restore_apfs_sha256'] != metadata[1]['restore_apfs_sha256']:
        raise SystemExit('restore provenance mismatch')
    if hashlib.sha256(args.apfs.read_bytes()).hexdigest() != metadata[0]['restore_apfs_sha256']:
        raise SystemExit('requires pinned original restore APFS')
    sources = {}
    for base, info in zip((args.foundation, args.daemons), metadata):
        for guest, expected in {**info['files'], **info.get('resources', {})}.items():
            source = base / guest.lstrip('/')
            if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                raise SystemExit('source changed: ' + guest)
            if guest in sources and sources[guest].read_bytes() != source.read_bytes():
                raise SystemExit('closure conflict: ' + guest)
            sources[guest] = source
    binary = args.apple / 'usr/sbin/cfprefsd'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != CFPREFSD:
        raise SystemExit('requires pinned original 20F66 cfprefsd')
    sources['/usr/sbin/cfprefsd'] = binary
    # Observed CF-1977 initializeFSEvents dlopen target, absent from LC_LOAD_DYLIB.
    dynamic_entry = '/System/Library/Frameworks/MobileCoreServices.framework/MobileCoreServices'
    macho = runpy.run_path(str(Path(__file__).with_name('audit-darwin-runtime.py')))['macho']
    dynamic_files = {}
    todo = [dynamic_entry]
    while todo:
        guest = todo.pop()
        if guest in dynamic_files:
            continue
        source = sources.get(guest)
        if source is None:
            source = (args.dynamic_root / guest.lstrip('/')).resolve()
            if not source.is_relative_to(args.dynamic_root.resolve()) or not source.is_file():
                raise SystemExit('missing observed dynamic dependency: ' + guest)
        item = macho(source)
        if guest in DYNAMIC_PINS and item['sha256'] != DYNAMIC_PINS[guest]:
            raise SystemExit('observed dynamic framework changed: ' + guest)
        sources[guest] = source
        dynamic_files[guest] = item['sha256']
        if item['dylinker']:
            todo.append(item['dylinker'])
        for dep in item['dependencies']:
            if not dep['weak']:
                if not dep['path'].startswith('/'):
                    raise SystemExit('unresolved dynamic dependency: ' + dep['path'])
                todo.append(dep['path'])
    jobs = {}
    for name, expected in JOBS.items():
        data = (args.apple / 'System/Library/LaunchDaemons' / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise SystemExit('original job mismatch: ' + name)
        jobs[name] = dict(sha256=expected, original_job=plistlib.loads(data))
    runtime = args.output / 'runtime-root'
    runtime.mkdir(parents=True)
    for guest, source in sources.items():
        dest = runtime / guest.lstrip('/')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    info = dict(metadata[1])
    info.update(resources=metadata[0]['resources'],
                files={**metadata[0]['files'], **metadata[1]['files'], **dynamic_files, '/usr/sbin/cfprefsd': CFPREFSD},
                dynamic_preferences_entry=dynamic_entry,
                dynamic_preferences_files=dynamic_files,
                cfprefsd_source=dict(binary_sha256=CFPREFSD, original_jobs=jobs,
                                     source_version='CoreFoundation-1977',
                                     ipsw_member='096-04088-077.dmg',
                                     system_volume='SydneyF20F66.D22D221OS',
                                     note='Selective system-image extraction; not a whole-image signature verification.'))
    (args.output / 'source.json').write_text(json.dumps(info, indent=2) + '\n')
    subprocess.run(['python3', str(Path(__file__).with_name('audit-darwin-runtime.py')), str(runtime),
                    str(args.output / 'runtime-audit.json'), '--entry', '/bin/launchctl',
                    '--entry', '/System/Library/Frameworks/Foundation.framework/Foundation',
                    '--entry', '/usr/sbin/syslogd', '--entry', '/usr/sbin/notifyd',
                    '--entry', '/usr/sbin/cfprefsd', '--entry', dynamic_entry], check=True)


if __name__ == '__main__':
    main()
