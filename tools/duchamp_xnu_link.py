#!/usr/bin/env python3
"""Verify the linked SWEET kernel format consumed by the Duchamp loader."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

ARM64_EXECUTE = (0xFEEDFACF, 0x100000C, 0, 2)
TEXT_BASE = 0xFFFFFE0007004000
PAGE = 0x4000
LC_SEGMENT_64, LC_SYMTAB, LC_DYSYMTAB, LC_UNIXTHREAD = (0x19, 2, 11, 5)
LC_BUILD_VERSION, LC_MAIN = (0x32, 0x80000028)
DYLD_DEPENDENCIES = {0xC, 0xE, 0x20, 0x80000018, 0x8000001F, 0x80000023}
BOOT_SEGMENTS = ('__TEXT', '__DATA_CONST', '__TEXT_EXEC', '__KLD', '__LASTDATA_CONST',
                 '__KLDDATA', '__DATA', '__BOOTDATA', '__LINKINFO', '__LINKEDIT')


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def name(raw):
    return raw.split(b'\0', 1)[0].decode('ascii')


def load_commands(blob, count, end):
    offset = 32
    for _ in range(count):
        check(offset + 8 <= end, 'truncated Mach-O load command')
        cmd, size = struct.unpack_from('<II', blob, offset)
        check(size >= 8 and size % 8 == 0 and size <= end - offset, 'invalid Mach-O load command size')
        yield cmd, blob[offset:offset + size]
        offset += size
    check(offset == end, 'Mach-O load command count or size mismatch')


def parse_segment(raw, file_size):
    check(len(raw) >= 72, 'truncated LC_SEGMENT_64')
    seg, addr, span, offset, size, maximum, initial, count, _ = struct.unpack_from('<16s4Q4I', raw, 8)
    check(len(raw) == 72 + count * 80 and offset + size <= file_size and addr + span < 1 << 64,
          'invalid Mach-O segment extents')
    names = [name(raw[i:i+16]) for i in range(72, len(raw), 80)]
    return dict(name=name(seg), vmaddr=addr, vmsize=span, fileoff=offset, filesize=size,
                maxprot=maximum, initprot=initial, sections=names)


def symbols(blob, raw):
    check(len(raw) == 24, 'invalid LC_SYMTAB')
    offset, count, strings, size = struct.unpack_from('<4I', raw, 8)
    check(offset + count * 16 <= len(blob) and strings + size <= len(blob), 'invalid symbol table bounds')
    wanted = {b'__start', b'_duchamp_dual_ramdisk_init'}
    found = {}
    for index, kind, section, _, value in struct.iter_unpack('<IBBHQ', blob[offset:offset+count*16]):
        if kind & 0xE0 or kind & 0x0E != 0x0E:
            continue
        check(index < size, 'symbol name outside string table')
        end = blob.find(b'\0', strings + index, strings + size)
        check(end != -1, 'unterminated symbol name')
        symbol = blob[strings+index:end]
        if symbol in wanted:
            check(symbol not in found, 'duplicate kernel entry symbol')
            found[symbol] = (section, value)
    return found


def verify(blob, reference=False):
    check(len(blob) >= 32, 'truncated Mach-O header')
    magic, cpu, subtype, filetype, count, size, flags, _ = struct.unpack_from('<8I', blob)
    check((magic, cpu, subtype, filetype) == ARM64_EXECUTE, 'expected plain ARM64 MH_EXECUTE')
    check(32 + size <= len(blob) and flags & 1, 'expected complete Mach-O with MH_NOUNDEFS')
    commands = list(load_commands(blob, count, 32 + size))
    ids = [cmd for cmd, _ in commands]
    check(not DYLD_DEPENDENCIES.intersection(ids) and LC_MAIN not in ids, 'kernel has a userspace loader entry')

    def required(cmd, label):
        matches = [raw for kind, raw in commands if kind == cmd]
        check(len(matches) == 1, f'expected one {label}')
        return matches[0]

    raw = required(LC_UNIXTHREAD, 'LC_UNIXTHREAD')
    check(len(raw) == 288 and struct.unpack_from('<II', raw, 8) == (6, 68), 'invalid ARM_THREAD_STATE64')
    pc, = struct.unpack_from('<Q', raw, 272)
    dynsym = required(LC_DYSYMTAB, 'LC_DYSYMTAB')
    check(len(dynsym) == 80 and struct.unpack_from('<I', dynsym, 28)[0] == 0, 'undefined kernel symbols')
    build = required(LC_BUILD_VERSION, 'LC_BUILD_VERSION')
    check(len(build) >= 24, 'truncated LC_BUILD_VERSION')
    platform, minimum, sdk, tools = struct.unpack_from('<4I', build, 8)
    check(platform == 1 and len(build) == 24 + tools * 8, 'invalid macOS build version')

    segments = [parse_segment(raw, len(blob)) for cmd, raw in commands if cmd == LC_SEGMENT_64]
    by_name = {seg['name']: seg for seg in segments}
    check(len(segments) == len(by_name) and all(key in by_name for key in BOOT_SEGMENTS),
          'missing or ambiguous kernel segments')
    text = segments[0]
    check((text['name'], text['vmaddr'], text['fileoff'], text['initprot']) == ('__TEXT', TEXT_BASE, 0, 1)
          and text['filesize'] >= 32 + size, 'incorrect kernel header mapping')
    active = sorted((seg for seg in segments if seg['vmsize']), key=lambda seg: seg['vmaddr'])
    previous = TEXT_BASE
    for seg in active:
        check(seg['vmaddr'] >= previous and seg['vmaddr'] % PAGE == 0 and seg['filesize'] <= seg['vmsize'],
              'overlapping, unaligned, or oversized kernel segment')
        previous = seg['vmaddr'] + seg['vmsize']
    check(tuple(seg['name'] for seg in active if seg['name'] in BOOT_SEGMENTS) == BOOT_SEGMENTS,
          'unexpected kernel boot segment order')
    code = by_name['__TEXT_EXEC']
    check(code['initprot'] == 5 and by_name['__DATA_CONST']['initprot'] == 1
          and by_name['__DATA']['initprot'] == 3 and '__text' in code['sections'],
          'unexpected executable or data protections')

    found = symbols(blob, required(LC_SYMTAB, 'LC_SYMTAB'))
    sections = [(seg['name'], section) for seg in segments for section in seg['sections']]

    def code_symbol(symbol):
        index, addr = found.get(symbol, (0, 0))
        check(0 < index <= len(sections) and sections[index-1] == ('__TEXT_EXEC', '__text')
              and code['vmaddr'] <= addr < code['vmaddr'] + code['filesize'],
              f'{symbol.decode()} is missing or outside file-backed kernel text')
        return addr

    check(pc == code_symbol(b'__start'), 'entry PC differs from __start')
    registration = None if reference else code_symbol(b'_duchamp_dual_ramdisk_init')
    return dict(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob), reference_only=reference,
                entry=hex(pc), dual_ramdisk_registration=hex(registration) if registration else None,
                load_commands=[hex(cmd) for cmd in ids], segments=segments,
                build_version=dict(minimum=minimum, sdk=sdk, tools=list(struct.iter_unpack('<2I', build[24:]))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kernel', type=Path)
    parser.add_argument('--reference-only', action='store_true', help='inspect the legacy kernel as a reference')
    args = parser.parse_args()
    try:
        report = verify(args.kernel.read_bytes(), args.reference_only)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Kernel link verification failed: {error}\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
