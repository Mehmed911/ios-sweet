#!/usr/bin/env python3
"""Populate a fresh copy of a diagnostic HFS image using an explicit hfsplus tool."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--runtime', type=Path, required=True)
    ap.add_argument('--audit', type=Path, required=True)
    ap.add_argument('--init', type=Path, required=True)
    ap.add_argument('--program', type=Path, required=True)
    ap.add_argument('--install', nargs=2, action='append', default=[], metavar=('GUEST', 'HOST'),
                    help='install and verify an additional file in the copied root')
    ap.add_argument('--devfs-mountpoint', action='store_true',
                    help='ensure /dev already exists before a read-only boot')
    ap.add_argument('--hfsplus', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit('refusing to overwrite existing output image')
    audit = json.loads(args.audit.read_text())
    if not audit['passed']:
        raise SystemExit('runtime dependency audit must pass first')
    files = {**{path: args.runtime / path.lstrip('/') for path in audit['files']},
             '/sbin/launchd': args.init, '/sbin/c-runtime-test': args.program}
    for guest, host in args.install:
        path = Path(guest)
        if not guest.startswith('/') or path.as_posix() != guest or '..' in path.parts or guest == '/':
            ap.error(f'expected a normalized absolute guest file path, got {guest!r}')
        if guest in files:
            ap.error(f'guest file already planned for installation: {guest}')
        files[guest] = Path(host)
    shutil.copyfile(args.base, args.output)
    volume = [str(args.hfsplus.resolve()), str(args.output.resolve())]
    def run(*command):
        subprocess.run([*volume, *command], check=True, stdout=subprocess.DEVNULL)
    created = {'/', '/sbin'}
    if args.devfs_mountpoint:
        def dev_exists():
            listing = subprocess.check_output([*volume, 'ls', '/'], text=True)
            return any(parts[0].startswith('04') and parts[-1] == 'dev'
                       for line in listing.splitlines() if (parts := line.split()))
        if not dev_exists():
            run('mkdir', '/dev')
        if not dev_exists():
            raise SystemExit('missing /dev directory in the copied root')
        created.add('/dev')
    with tempfile.TemporaryDirectory(prefix='sweet-hfs-') as scratch:
        extracted = Path(scratch) / 'roundtrip'
        for guest, host in sorted(files.items()):
            path = Path(guest)
            for parent in reversed(path.parents):
                name = parent.as_posix()
                if name not in created:
                    run('mkdir', name)
                    created.add(name)
            run('add', str(host.resolve()), guest)
            run('chmod', '755', guest)
            run('extract', guest, str(extracted))
            if extracted.read_bytes() != host.read_bytes():
                raise SystemExit(f'HFS roundtrip verification failed for {guest}')
    print(f'{args.output}: installed {len(files)} files into a copied HFS RAM root')


if __name__ == '__main__':
    main()
