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
    ap.add_argument('--hfsplus', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit('refusing to overwrite existing output image')
    audit = json.loads(args.audit.read_text())
    if not audit['passed']:
        raise SystemExit('runtime dependency audit must pass first')
    shutil.copyfile(args.base, args.output)
    def run(*command):
        subprocess.run([str(args.hfsplus.resolve()), str(args.output.resolve()), *command],
                       check=True, stdout=subprocess.DEVNULL)
    created = {'/', '/sbin'}
    files = {**{path: args.runtime / path.lstrip('/') for path in audit['files']},
             '/sbin/launchd': args.init, '/sbin/c-runtime-test': args.program}
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
