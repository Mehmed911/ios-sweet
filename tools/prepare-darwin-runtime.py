#!/usr/bin/env python3
"""Extract the small iOS 16.5 restore runtime from Apple's IPSW, not a full OS image.

Apple files stay local and must not be committed. Requires 7-Zip with APFS support.
The pinned IM4P contains an unencrypted APFS payload; this tool does not decrypt.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import remotezip


URL = ('https://updates.cdn-apple.com/2023SpringFCS/fullrestores/032-85130/'
       '6AB0D10A-8AF9-4F6C-8CF5-A1B315CABE88/'
       'iPhone10,3,iPhone10,6_16.5_20F66_Restore.ipsw')
MEMBER = '096-03566-084.dmg'
SHA256 = '8223b75c9399dfc8cf0971374527d710b69e29e8ef69722b98a82902199fcff5'
SELECTED = ['usr/lib/dyld', 'usr/lib/libSystem.B.dylib', 'usr/lib/system',
            'usr/lib/libobjc.A.dylib', 'usr/lib/libc++.1.dylib', 'usr/lib/libc++abi.dylib']


def tlv(data, off):
    tag, length = data[off:off + 2]
    pos = off + 2
    if length & 0x80:
        count = length & 0x7f
        if not 1 <= count <= 4:
            raise ValueError('unsupported DER length')
        length = int.from_bytes(data[pos:pos + count], 'big')
        pos += count
    end = pos + length
    if end > len(data):
        raise ValueError('truncated DER value')
    return tag, pos, end


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--img4', type=Path, help='reuse a local copy of the exact pinned ZIP member')
    ap.add_argument('--sevenzip', default='7z')
    args = ap.parse_args()
    runtime = args.output / 'runtime-root'
    if runtime.exists():
        raise SystemExit('refusing to overwrite an existing runtime-root')
    args.output.mkdir(parents=True, exist_ok=True)
    image = args.output / MEMBER
    if args.img4:
        if args.img4.resolve() != image.resolve():
            shutil.copyfile(args.img4, image)
    else:
        entry = next(e for e in remotezip.central_dir(URL) if e[0] == MEMBER)
        remotezip.extract(URL, entry, str(args.output))
    data = image.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        raise SystemExit(f'IM4P hash mismatch: {digest}')
    tag, start, end = tlv(data, 0)
    if tag != 0x30 or end != len(data):
        raise SystemExit('expected an IM4P DER sequence')
    parts, pos = [], start
    while pos < end:
        kind, begin, finish = tlv(data, pos)
        parts.append((kind, data[begin:finish]))
        pos = finish
    if len(parts) != 4 or parts[0] != (0x16, b'IM4P') or parts[1] != (0x16, b'rdsk') or parts[3][0] != 4:
        raise SystemExit('expected the pinned unencrypted rdsk IM4P layout')
    payload = parts[3][1]
    if payload[32:36] != b'NXSB':
        raise SystemExit('IM4P payload is not a plain APFS container')
    apfs = args.output / 'restore.apfs'
    apfs.write_bytes(payload)
    with (args.output / 'extract.log').open('w') as log:
        subprocess.run([args.sevenzip, 'x', '-y', '-o' + str(runtime), str(apfs), *SELECTED],
                       check=True, stdout=log, stderr=subprocess.STDOUT)
    report = args.output / 'runtime-audit.json'
    subprocess.run(['python3', str(Path(__file__).with_name('audit-darwin-runtime.py')),
                    str(runtime), str(report)], check=True)
    source = dict(ipsw=URL, member=MEMBER, sha256=digest,
                  apfs_sha256=hashlib.sha256(payload).hexdigest(),
                  note='Apple software extracted locally; not included in Git.')
    (args.output / 'source.json').write_text(json.dumps(source, indent=2) + '\n')
    print(f'runtime ready: {runtime}')


if __name__ == '__main__':
    main()
