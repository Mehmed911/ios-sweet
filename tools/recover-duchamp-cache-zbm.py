#!/usr/bin/env python3
"""Strictly decode the three unsupported cache components through read-only APFS."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[1]
COMPONENTS = {
    '42': ('dyld_shared_cache_arm64.42.dyldlinkedit', 333955072),
    '28': ('dyld_shared_cache_arm64.28.dyldlinkedit', 19906560),
    'symbols': ('dyld_shared_cache_arm64.symbols', 591855616),
}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--image', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    image, out = args.image.resolve(), args.output.resolve()
    if out.exists():
        raise SystemExit('preserve existing recovery output')
    if image.stat().st_size != 2726297600 or sha(image) != '2279bf443856fcb6a3f00b1fa06a32ba02a66fdf6ab6b12019462c7498aafdd3':
        raise SystemExit('requires exact matching acquired SystemOS image')
    source = REPO / 'work/tooling/apfs-fuse-systemos-v1'
    build = REPO / 'work/tooling/apfs-fuse-systemos-v1-build'
    out.mkdir(parents=True)
    command = ['g++', '-std=c++11', '-include', 'cstdint', '-I' + str(source),
        str(REPO / 'tools/read-systemos-zbm.cpp'), '-L' + str(build), '-lapfs', '-llzfse', '-lcrypto', '-lz', '-lbz2',
        '-o', str(out / 'read-systemos-zbm')]
    subprocess.run(command, check=True)
    files = {}
    for component, (name, size) in COMPONENTS.items():
        result = subprocess.run([str(out / 'read-systemos-zbm'), str(image), component, str(out / name)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        (out / (component + '.log')).write_text(result.stdout)
        print(result.stdout, end='', flush=True)
        if result.returncode or (out / name).stat().st_size != size:
            raise SystemExit('strict decompression failed: ' + name)
        files[name] = dict(bytes=size, sha256=sha(out / name))
    invalid = subprocess.run([str(out / 'read-systemos-zbm'), str(image), 'unsupported', str(out / 'must-not-exist')])
    if invalid.returncode != 2 or (out / 'must-not-exist').exists():
        raise SystemExit('unknown component rejection failed')
    report = dict(passed=True, files=files, image_sha256=sha(image), helper_source_sha256=sha(REPO / 'tools/read-systemos-zbm.cpp'),
        helper_sha256=sha(out / 'read-systemos-zbm'), apfs_commit=subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
        unknown_component_rejected=True, source_read_only=True, filesystem_mount_performed=False,
        phone_access=False, partition_write=False)
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Strict ZBM cache recovery: PASS components=3', flush=True)


if __name__ == '__main__':
    main()
