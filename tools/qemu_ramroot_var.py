#!/usr/bin/env python3
"""Package a source-built SWEET kernel and two HFS+ RAMDisks for QEMU."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

import adt
import duchamp_xnu_link
import mkpayload

REPO = Path(__file__).resolve().parents[1]
BOOT_ARGS = ('debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress '
             'rd=md0 rootrw=0 sweet_console_fb=1 duchamp_timer_irq_ack=1 '
             'unentitled_ios_sim_launch=1 launchdsuffix=sweet launchd_log_serial=1 '
             'duchamp_dual_ramdisk=1')
IMAGE_SIZE = 32 * 1024 * 1024
PROP = 'DuchampDataRAMDisk'
PAGE = mkpayload.PAGE
SEGMENT = struct.Struct('<4Q')


def check(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def memory_map(tree):
    for name in ('chosen', 'memory-map'):
        nodes = [node for node in tree.children if node.name == name]
        check(len(nodes) == 1, f'missing or ambiguous ADT node {name}')
        tree = nodes[0]
    return tree


def valid_size(size):
    return 1024**2 <= size <= 64 * 1024**2 and size % PAGE == 0


def verify(payload, missing_device=False, diagnostic_hid=False):
    check(len(payload) >= mkpayload.SEG_TABLE, 'truncated payload header')
    magic, version, count = struct.unpack_from('<8sII', payload)
    virt, _, offset, size, end, phys, memory = struct.unpack_from('<7Q', payload, 16)
    header_end = mkpayload.SEG_TABLE + count * SEGMENT.size
    check((magic, version) == (b'SWEETXNU', 1) and 3 <= count <= 32,
          'unexpected dual-HFS layout')
    check(header_end <= offset and 0 < size <= len(payload) - offset, 'invalid ADT bytes')
    boot_args = BOOT_ARGS + (' sweethidtest=5' if diagnostic_hid else '')
    check(payload[mkpayload.CMDLINE:mkpayload.SEG_TABLE] ==
          boot_args.encode().ljust(mkpayload.BOOT_LINE_LENGTH, b'\0'), 'incorrect QEMU boot arguments')
    check(virt <= end and (virt | end | phys | memory) % PAGE == 0
          and 0 < memory < (1 << 64) - phys
          and ((end - virt + size + PAGE - 1) & -PAGE) + PAGE <= memory,
          'invalid boot-data RAM window')
    ranges = list(SEGMENT.iter_unpack(payload[mkpayload.SEG_TABLE:header_end]))
    root, var = ranges[-2:]
    layout = {}
    for label, (va, span, file, length) in zip(('root', 'var'), (root, var)):
        check(valid_size(span) and span == length and va % PAGE == 0
              and virt <= va <= end - span and header_end <= file <= offset - length
              and payload[file+1024:file+1026] in (b'H+', b'HX'), f'invalid {label} segment')
        layout[label] = {'pa': va - virt + phys, 'bytes': span,
                         'sha256': digest(memoryview(payload)[file:file+length])}
    check(root[0] + root[1] == var[0] and root[2] + root[3] == var[2] and
          var[2] + var[3] == offset and var[0] + var[1] == end, 'invalid reservation boundaries')
    last_file = header_end
    for va, span, file, length in ranges[:-2]:
        check(virt <= va and 0 < span <= root[0] - va and last_file <= file and
              length <= span and file + length <= root[2], 'kernel segment overlaps volumes')
        last_file = file + length
    tree, consumed = adt.parse(payload[offset:offset + size])
    check(consumed == size and not any(n.name in ('duchamp-qemu-ufs', 'sweet-ufs') for n in tree.children)
          and mkpayload.adt_dram(payload[offset:offset + size]) == (phys, memory),
          'invalid or storage-enabled ADT')
    props = memory_map(tree).props
    for name, label, absent in (('RAMDisk', 'root', False), (PROP, 'var', missing_device)):
        region = layout[label]
        expected = [] if absent else [(0, struct.pack('<QQ', region['pa'], region['bytes']))]
        check([(flags, value) for key, flags, value in props if key == name] == expected,
              f'invalid {name} declaration')
    return layout


def require_source_kernel(path):
    return duchamp_xnu_link.verify(path.read_bytes())


def build(kernel, base_adt, root, var, missing_device=False, diagnostic_hid=False):
    check(valid_size(root.stat().st_size), 'invalid root image size')
    image = var.read_bytes()
    check(valid_size(len(image)), 'invalid var image size')
    boot_args = BOOT_ARGS + (' sweethidtest=5' if diagnostic_hid else '')
    data, _ = mkpayload.build(kernel, base_adt, boot_args, root)
    count, = struct.unpack_from('<I', data, 12)
    virt, _, old_adt, adt_size, end, phys, _ = struct.unpack_from('<7Q', data, 16)
    old_segments = mkpayload.SEG_TABLE + count * SEGMENT.size
    tree, _ = adt.parse(data[old_adt:old_adt + adt_size])
    props = memory_map(tree).props
    check(not any(key == PROP for key, _, _ in props), 'base ADT already declares md1')
    if not missing_device:
        props.append((PROP, 0, struct.pack('<QQ', end - virt + phys, len(image))))
    new_adt = adt.serialize(tree)

    result = bytearray(data[:mkpayload.SEG_TABLE])
    struct.pack_into('<I', result, 12, count + 1)
    struct.pack_into('<3Q', result, 0x20, old_adt + SEGMENT.size + len(image),
                     len(new_adt), end + len(image))
    for va, span, file, length in SEGMENT.iter_unpack(data[mkpayload.SEG_TABLE:old_segments]):
        result += SEGMENT.pack(va, span, file + SEGMENT.size, length)
    result += SEGMENT.pack(end, len(image), old_adt + SEGMENT.size, len(image))
    result += data[old_segments:old_adt]
    result += image
    result += new_adt
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('kernel', 'adt', 'root', 'var', 'output'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--missing-device', action='store_true', help='QEMU negative test without md1')
    parser.add_argument('--diagnostic-hid', action='store_true', help='QEMU-only built-in HID button timer')
    args = parser.parse_args()
    kernel_report = require_source_kernel(args.kernel)
    payload = build(args.kernel, args.adt, args.root, args.var, args.missing_device, args.diagnostic_hid)
    check(digest(args.kernel.read_bytes()) == kernel_report['sha256'], 'kernel changed during packaging')
    layout = verify(payload, args.missing_device, args.diagnostic_hid)
    offset, size = struct.unpack_from('<QQ', payload, 0x20)
    boot_adt = payload[offset:offset+size]
    report = dict(layout=layout, payload_sha256=digest(payload), payload_bytes=len(payload),
                  kernel_sha256=kernel_report['sha256'], kernel_entry=kernel_report['entry'],
                  kernel_dual_ramdisk_registration=kernel_report['dual_ramdisk_registration'],
                  base_adt_sha256=digest(args.adt.read_bytes()), adt_sha256=digest(boot_adt),
                  missing_device=args.missing_device, diagnostic_hid=args.diagnostic_hid, qemu_only=True)
    args.output.mkdir()
    (args.output / 'payload.bin').write_bytes(payload)
    (args.output / 'ramdisks.adt').write_bytes(boot_adt)
    (args.output / 'layout.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
