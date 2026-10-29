#!/usr/bin/env python3
"""Add pinned Procursus launchctl and libiosexec to a copy of the Apple restore runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

PACKAGES = {
    'launchctl': (
        'pool/main/iphoneos-arm64/1700/launchctl/launchctl_1:1.1.1_iphoneos-arm.deb',
        'fcfbc9c7ab24d612379f40f10637de4e059ed39a0817e6628a99ab26ceea62d5'),
    'libiosexec1': (
        'pool/main/iphoneos-arm64/1700/libiosexec/libiosexec1_1.3.1_iphoneos-arm.deb',
        '2e00e300f34f11bec7aeb04f2484a165e075094329344e8ec900834c03a82b9b'),
}
FILES = {
    'usr/bin/launchctl': ('bin/launchctl',
        '11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d'),
    'usr/lib/libiosexec.1.dylib': ('usr/lib/libiosexec.1.dylib',
        '9d8f0b10be02f9829854e11dc4a86f70dbfd0f0322f3a3a996716e4d38214391'),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('base_runtime', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--package-cache', type=Path)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit('refusing to overwrite existing runtime')
    args.output.mkdir(parents=True)
    unpacked = args.output / 'packages'
    provenance = {}
    for name, (member, expected) in PACKAGES.items():
        archive = args.output / (name + '.deb')
        cached = args.package_cache / (name + '.deb') if args.package_cache else None
        if cached and cached.exists():
            shutil.copyfile(cached, archive)
        else:
            subprocess.run(['curl', '-fsL', '--retry', '2', '--max-time', '120',
                            '-o', str(archive), 'https://apt.procurs.us/' + member], check=True)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise SystemExit(f'package SHA-256 mismatch: {name}')
        subprocess.run(['dpkg-deb', '-x', str(archive), str(unpacked)], check=True)
        provenance[name] = {'url': 'https://apt.procurs.us/' + member, 'sha256': expected}
    runtime = args.output / 'runtime-root'
    shutil.copytree(args.base_runtime, runtime)
    for source, (destination, expected) in FILES.items():
        data = (unpacked / source).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise SystemExit(f'executable/library SHA-256 mismatch: {source}')
        target = runtime / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (args.output / 'source.json').write_text(json.dumps({
        'launchctl': 'Procursus FOSS 1:1.1.1; not an Apple-supplied binary',
        'source': 'https://github.com/ProcursusTeam/launchctl/tree/v1.1.1',
        'packages': provenance,
    }, indent=2) + '\n')
    subprocess.run(['python3', str(Path(__file__).with_name('audit-darwin-runtime.py')),
                    str(runtime), str(args.output / 'runtime-audit.json'),
                    '--entry', '/bin/launchctl'], check=True)
    print(f'runtime ready: {runtime}')


if __name__ == '__main__':
    main()
