#!/usr/bin/env python3
"""Inventory a standalone arm64 dyld/libSystem dependency closure, without executing it."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def macho(path):
    data = path.read_bytes()
    if len(data) < 32:
        raise ValueError('too short for Mach-O')
    magic, cpu, sub, kind, count, size, flags, _ = struct.unpack_from('<8I', data)
    if magic != 0xfeedfacf or cpu != 0x100000c or (sub & 0xffffff) != 0:
        raise ValueError('requires a thin plain-arm64 Mach-O')
    if 32 + size > len(data):
        raise ValueError('truncated load commands')
    result = dict(cpu='arm64', subtype=sub, filetype=kind, flags=flags,
                  size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                  dependencies=[], code_signature=False, platform=None,
                  dylinker=None, main_entry=None)
    off = 32
    for _ in range(count):
        cmd, length = struct.unpack_from('<II', data, off)
        if length < 8 or off + length > 32 + size:
            raise ValueError('invalid load command')
        if cmd in (0xc, 0x80000018, 0x8000001f, 0x80000023):
            nameoff, = struct.unpack_from('<I', data, off + 8)
            name = data[off + nameoff:off + length].split(b'\0')[0].decode()
            result['dependencies'].append(dict(path=name, weak=cmd == 0x80000018))
        elif cmd == 0x1d:
            sigoff, sigsize = struct.unpack_from('<II', data, off + 8)
            result['code_signature'] = bool(sigsize and sigoff + sigsize <= len(data))
        elif cmd == 0x32:
            result['platform'], result['minos'], _sdk = struct.unpack_from('<III', data, off + 8)
        elif cmd == 0xe:
            nameoff, = struct.unpack_from('<I', data, off + 8)
            result['dylinker'] = data[off + nameoff:off + length].split(b'\0')[0].decode()
        elif cmd == 0x80000028:
            result['main_entry'], = struct.unpack_from('<Q', data, off + 8)
        off += length
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root', type=Path)
    ap.add_argument('report', type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    todo = ['/usr/lib/dyld', '/usr/lib/libSystem.B.dylib']
    files, missing, invalid = {}, set(), {}
    while todo:
        guest = todo.pop()
        if guest in files or guest in missing or guest in invalid:
            continue
        path = (root / guest.lstrip('/')).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            missing.add(guest)
            continue
        try:
            item = macho(path)
        except (ValueError, struct.error, UnicodeError) as error:
            invalid[guest] = str(error)
            continue
        files[guest] = item
        for dependency in item['dependencies']:
            if not dependency['weak']:
                todo.append(dependency['path'])
    report = dict(passed=not missing and not invalid, files=files,
                  missing=sorted(missing), invalid=invalid,
                  signature_note='Signature load-command presence only; runtime verification is separate.')
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], files=len(files),
                         total_bytes=sum(f['size'] for f in files.values()),
                         missing=report['missing'], invalid=invalid), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
