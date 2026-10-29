#!/usr/bin/env python3
"""Build a standalone Foundation closure from the pinned local iOS restore extraction."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess

FOUNDATION = '/System/Library/Frameworks/Foundation.framework/Foundation'
PINS = {
    FOUNDATION: '182a6fb6d6c51e8e1a70e9152c84cd9d1bd65d2a1f0bda21a4ebe1be446021f2',
    '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation':
        '1bc84069d4292467b750c7aafb4c3114092cb9b5fa906d9c40e61504dc883878',
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'apple', 'apfs', 'output'):
        ap.add_argument(name, type=Path)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit('refusing to overwrite an existing runtime')
    if hashlib.sha256(args.apfs.read_bytes()).hexdigest() != (
            'abf6d0281cffd6fdead38043e0a6291189164d2c06383218adcb95d8dc25efc8'):
        raise SystemExit('requires the pinned iOS 16.5 20F66 restore APFS')
    roots = [args.base.resolve(), args.apple.resolve()]

    def locate(guest):
        if not guest.startswith('/'):
            raise ValueError('unresolved dependency: ' + guest)
        for root in roots:
            path = (root / guest.lstrip('/')).resolve()
            if not path.is_relative_to(root):
                raise ValueError('dependency escapes extraction: ' + guest)
            if path.is_file():
                return path
        raise ValueError('missing dependency: ' + guest)

    for path, digest in PINS.items():
        if hashlib.sha256(locate(path).read_bytes()).hexdigest() != digest:
            raise SystemExit('Foundation source mismatch: ' + path)
    macho = runpy.run_path(str(Path(__file__).with_name('audit-darwin-runtime.py')))['macho']
    todo = [FOUNDATION, '/usr/lib/dyld', '/usr/lib/libSystem.B.dylib', '/bin/launchctl']
    files = {}
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
                candidates = [r.rstrip('/') + '/' + target[7:] for r in item['rpaths'] if r.startswith('/')]
                for candidate in candidates:
                    try:
                        locate(candidate)
                    except ValueError:
                        continue
                    target = candidate
                    break
            todo.append(target)
    args.output.mkdir(parents=True)
    runtime = args.output / 'runtime-root'
    shutil.copytree(args.base, runtime)
    provenance = {}
    for guest, (source, item) in files.items():
        target = runtime / guest.lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != source.read_bytes():
                raise SystemExit('base dependency differs: ' + guest)
        else:
            shutil.copyfile(source, target)
        provenance[guest] = item['sha256']
    resources = {}
    bundles = set()
    for guest in files:
        parts = Path(guest).parts
        for index, part in enumerate(parts):
            if part.endswith('.framework'):
                bundles.add('/' + '/'.join(parts[1:index + 1]))
                break
    for bundle in sorted(bundles):
        source_root = args.apple.resolve() / bundle.lstrip('/')
        for source in sorted(source_root.rglob('*')):
            if not source.is_file() or source.is_symlink():
                continue
            guest = '/' + source.relative_to(args.apple.resolve()).as_posix()
            if guest in files:
                continue
            data = source.read_bytes()
            if data[:4] in (b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe'):
                continue
            target = runtime / guest.lstrip('/')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            resources[guest] = hashlib.sha256(data).hexdigest()
    (args.output / 'source.json').write_text(json.dumps({
        'restore_apfs_sha256': 'abf6d0281cffd6fdead38043e0a6291189164d2c06383218adcb95d8dc25efc8',
        'entry': FOUNDATION, 'files': provenance, 'resources': resources,
        'note': 'Locally extracted Apple files; exclude from Git. Strong dependency closure only.',
    }, indent=2) + '\n')
    subprocess.run(['python3', str(Path(__file__).with_name('audit-darwin-runtime.py')),
                    str(runtime), str(args.output / 'runtime-audit.json'), '--entry', FOUNDATION,
                    '--entry', '/bin/launchctl'], check=True)
    print(f'Foundation runtime: {len(files)} binaries, {len(resources)} resource files')


if __name__ == '__main__':
    main()
