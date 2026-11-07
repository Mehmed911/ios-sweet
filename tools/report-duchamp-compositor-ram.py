#!/usr/bin/env python3
"""Read the pinned AppleCLCD layout from a stopped QEMU run, without guest writes."""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import struct

KERNEL_PIN = 'e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b'
FB_BASE = 0xfcc2f000
FB_GEOMETRY = (1220, 2712, 4992)
# Addresses and field offsets were verified against the pinned kernel's
# AppleCLCD constructor, start, swap, vsyncFired and present disassembly.
CLCD_VPTR = struct.pack('<Q', 0xfffffe00072a0ff0)
OBJECT_SIZE = 0x570
PAGE_SIZE = 0x4000
CPU_TTEP = 0xfffffe0007177928
CODE = (0xfffffe0007a4d608, 0xfffffe0007a4d930, 0xfffffe0007a4dc24, 0xfffffe0007a4dfec)


def uint(data, offset, size=4):
    return int.from_bytes(data[offset:offset + size], 'little')


def instances(ram, lo, hi):
    fd = ram.fileno()
    while lo < hi:
        try:
            lo = os.lseek(fd, lo, os.SEEK_DATA)
        except OSError as error:
            if error.errno == errno.ENXIO:
                return
            raise
        end = min(hi, os.lseek(fd, lo, os.SEEK_HOLE))
        while lo < end:
            data = os.pread(fd, min(8 << 20, end - lo), lo)
            if not data:
                raise ValueError('short RAM extent')
            pos = data.find(CLCD_VPTR)
            while pos != -1:
                offset = lo + pos
                # The field reads require the complete object within one XNU page.
                if offset % 8 == 0 and offset % 0x4000 <= 0x4000 - OBJECT_SIZE:
                    obj = os.pread(fd, OBJECT_SIZE, offset)
                    geometry = struct.unpack_from('<3I', obj, 0xa8)
                    if uint(obj, 0xa0, 8) == FB_BASE and geometry == FB_GEOMETRY:
                        yield offset, obj
                pos = data.find(CLCD_VPTR, pos + 1)
            lo += len(data)


def inspect(run, object_va=None):
    layout = json.loads((run / 'layout.json').read_text())
    result = json.loads((run / 'result.json').read_text())
    if layout['kernel_sha256'] != KERNEL_PIN or not layout['qemu_only'] or layout['physical_storage']:
        raise ValueError('expected pinned QEMU-only layout')
    if not (result.get('saved_framebuffer') or result.get('saved_guest_root')):
        raise ValueError('expected stopped QEMU capture')
    ram_base, phys_base, virt_base = (layout[k] for k in ('ram_base', 'phys_base', 'virt_base'))
    with (run / 'guest-ram.bin').open('rb') as ram, (run / 'kernel-only-payload.bin').open('rb') as payload:
        def read_pa(pa, size):
            if not ram_base <= pa <= ram_base + layout['ram_bytes'] - size:
                raise ValueError('physical RAM read outside QEMU layout')
            data = os.pread(ram.fileno(), size, pa - ram_base)
            if len(data) != size:
                raise ValueError('short physical RAM read')
            return data

        def pa_for_kernel_va(va):
            return phys_base + va - virt_base

        for address in CODE:
            pa = pa_for_kernel_va(address)
            seg = next(s for s in layout['segments'] if s[0] <= pa and pa + 32 <= s[0] + s[3])
            payload.seek(seg[2] + pa - seg[0])
            if read_pa(pa, 32) != payload.read(32):
                raise ValueError(f'kernel text mismatch at {address:#x}')
        raw = (run / 'fb.raw').read_bytes()
        if raw != read_pa(FB_BASE, FB_GEOMETRY[1] * FB_GEOMETRY[2]):
            raise ValueError('AppleCLCD scanout does not match the QMP framebuffer dump')
        if object_va is not None:
            # The AppleCLCD allocation can straddle noncontiguous physical pages.
            def translate(va):
                table = uint(read_pa(pa_for_kernel_va(CPU_TTEP), 8), 0, 8)
                for shift in (36, 25, 14):
                    entry = uint(read_pa(table + 8 * ((va >> shift) & 0x7ff), 8), 0, 8)
                    if not entry & 1:
                        raise ValueError('unmapped AppleCLCD virtual address')
                    table = entry & ((1 << 48) - PAGE_SIZE)
                    if shift == 14 or not entry & 2:
                        mask = (1 << shift) - 1
                        return (table & ~mask) | (va & mask)
                raise ValueError('incomplete virtual address translation')

            if object_va < 0xffff800000000000 or translate(CODE[-1]) != pa_for_kernel_va(CODE[-1]):
                raise ValueError('unexpected kernel virtual address or page table')
            pa = translate(object_va)
            head_size = min(OBJECT_SIZE, PAGE_SIZE - (object_va % PAGE_SIZE))
            obj = read_pa(pa, head_size)
            if head_size < OBJECT_SIZE:
                obj += read_pa(translate(object_va + head_size), OBJECT_SIZE - head_size)
            if (obj[:8] != CLCD_VPTR or uint(obj, 0xa0, 8) != FB_BASE
                    or struct.unpack_from('<3I', obj, 0xa8) != FB_GEOMETRY or not uint(obj, 0x564)):
                raise ValueError('virtual address does not identify the live AppleCLCD object')
            offset = pa - ram_base
        else:
            # Exclude the pinned kernel, RAM root and initial boot allocations.
            ranges = ((phys_base, layout['segments'][0][0]),
                      (layout['top'], phys_base + layout['mem_size']))
            found = [entry for lo, hi in ranges for entry in instances(ram, lo - ram_base, hi - ram_base)]
            if len(found) != 1:
                raise ValueError(f'expected one live-shaped AppleCLCD object, found {len(found)}. Supply --object-va from the QEMU trace')
            offset, obj = found[0]
        record = obj[0xf5:0x561]
        counters = {key: uint(read_pa(pa_for_kernel_va(va), size), 0, size) for key, va, size in (
            ('swap_count', 0xfffffe00081029d0, 8),
            ('layer_log_count', 0xfffffe00081029d8, 4),
            ('selector_mask', 0xfffffe00081029e0, 8))}
    return dict(kernel_sha256=KERNEL_PIN, code_sites_verified=len(CODE), counters=counters,
        framebuffer=dict(base=hex(FB_BASE), width=FB_GEOMETRY[0], height=FB_GEOMETRY[1],
                         stride=FB_GEOMETRY[2], sha256=hashlib.sha256(raw).hexdigest()),
        clcd=dict(object_pa=hex(offset + ram_base), pixel_va=hex(uint(obj, 0xc8, 8)),
                  logical_size=struct.unpack_from('<2I', obj, 0xb4),
                  vsync_count=uint(obj, 0x98, 8), dirty=bool(obj[0x561]),
                  flush_ticks=uint(obj, 0x564), power_off=bool(obj[0x568]), fade_step=uint(obj, 0x56c)),
        last_swap=dict(id=uint(record, 0x50), mask=hex(uint(record, 0x104)),
                       surface_ids=struct.unpack_from('<4I', record, 0x54),
                       source=[struct.unpack_from('<4i', record, 0x64 + 16 * i) for i in range(4)],
                       destination=[struct.unpack_from('<4i', record, 0xc4 + 16 * i) for i in range(4)],
                       sha256=hashlib.sha256(record).hexdigest()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--object-va', type=lambda address: int(address, 0), help='AppleCLCD VA from the QEMU trace')
    args = parser.parse_args()
    print(json.dumps(inspect(args.run, args.object_va), indent=2))


if __name__ == '__main__':
    main()
