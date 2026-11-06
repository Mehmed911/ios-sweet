#!/usr/bin/env python3
"""Inspect locally available UI-service Mach-O closures without running them."""
import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import runpy
import struct

MACHO = runpy.run_path(str(Path(__file__).with_name('audit-darwin-runtime.py')))['macho']
ENTRIES = [
    '/System/Library/CoreServices/SpringBoard.app/SpringBoard',
    '/usr/libexec/backboardd', '/usr/libexec/runningboardd',
    '/System/Library/Frameworks/UIKit.framework/UIKit',
    '/System/Library/PrivateFrameworks/UIKitCore.framework/UIKitCore',
    '/System/Library/Frameworks/QuartzCore.framework/QuartzCore',
    '/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics',
    '/System/Library/Frameworks/IOSurface.framework/IOSurface',
    '/System/Library/PrivateFrameworks/IOMobileFramebuffer.framework/IOMobileFramebuffer',
    '/System/Library/PrivateFrameworks/MiniDisplay.framework/MiniDisplay',
    '/usr/sbin/cfprefsd', '/usr/sbin/notifyd', '/usr/sbin/syslogd',
]


def locate(roots, guest):
    if not guest.startswith('/') or '..' in guest.split('/'):
        return None, 'unresolved or unsafe guest path', []
    matches = []
    for root in roots:
        candidate = (root / guest.lstrip('/')).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            matches.append(candidate)
    if not matches:
        return None, 'not present in the inspected local roots', []
    hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in matches}
    if len(hashes) != 1:
        return None, 'conflicting bytes across local roots', [str(path) for path in matches]
    return matches[0], None, [str(path) for path in matches]


def audit_entry(roots, entry):
    files, missing, invalid, weak = {}, [], {}, []
    todo = [entry, '/usr/lib/dyld', '/usr/lib/libSystem.B.dylib']
    visited = set()
    while todo:
        guest = todo.pop()
        if guest in visited:
            continue
        visited.add(guest)
        source, error, providers = locate(roots, guest)
        if source is None:
            if error == 'not present in the inspected local roots':
                missing.append(guest)
            else:
                invalid[guest] = dict(error=error, providers=providers)
            continue
        try:
            item = MACHO(source)
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            invalid[guest] = dict(error=str(error), providers=providers)
            continue
        item['source'] = str(source)
        files[guest] = item
        if item['dylinker']:
            todo.append(item['dylinker'])
        for dependency in item['dependencies']:
            target = dependency['path']
            if dependency['weak']:
                weak.append(dict(importer=guest, path=target))
                continue
            if target.startswith('@loader_path/'):
                target = posixpath.normpath(posixpath.dirname(guest) + '/' + target[13:])
            elif target.startswith('@executable_path/'):
                target = posixpath.normpath(posixpath.dirname(entry) + '/' + target[17:])
            elif target.startswith('@rpath/'):
                candidates = [base.rstrip('/') + '/' + target[7:]
                              for base in item['rpaths'] if base.startswith('/')]
                # Inherited loader-chain rpaths are not guessed by this audit.
                target = next((path for path in candidates if locate(roots, path)[0]), target)
            dependency['resolved_path'] = target
            todo.append(target)
    return dict(entry=entry, complete=not missing and not invalid,
                entry_present=entry in files, files=files, missing=sorted(missing),
                invalid=invalid, weak_imports_not_followed=weak,
                binary_count=len(files), total_bytes=sum(item['size'] for item in files.values()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', action='append', required=True, type=Path)
    parser.add_argument('--entry', action='append')
    parser.add_argument('--require', action='append', default=[])
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('preserve existing report')
    roots = [path.resolve(strict=True) for path in args.root]
    if not all(path.is_dir() for path in roots):
        parser.error('each root must be a directory')
    entries = list(dict.fromkeys([*(args.entry or ENTRIES), *args.require]))
    results = {entry: audit_entry(roots, entry) for entry in entries}
    passed = all(results[entry]['complete'] for entry in args.require)
    report = dict(required_entries_complete=passed, roots=[str(root) for root in roots], entries=results,
        scope={'phone_access': False, 'execution': False, 'entire_system_inventory': False,
               'weak_and_dynamic_imports_proven': False, 'signature_authentication': False,
               'service_protocols_or_hardware_proven': False},
        note='Missing means absent from the inspected roots only. LC_LOAD_DYLIB closure is not runtime compatibility. Unresolved inherited rpaths remain invalid.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    for entry, result in results.items():
        print(json.dumps(dict(entry=entry, complete=result['complete'], binary_count=result['binary_count'],
                              total_bytes=result['total_bytes'], missing=result['missing'], invalid=result['invalid'])))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
