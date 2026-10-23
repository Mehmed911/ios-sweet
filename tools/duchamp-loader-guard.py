#!/usr/bin/env python3
"""Validate a Duchamp SWEETXNU load plan without copying or executing it."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ALIGN = 0x2000000
PAGE = 0x4000
MAX_FDT = 2 * 1024 * 1024
MAX_SEGMENTS = 32


def checked_end(start, size, label):
    end = start + size
    if size < 0 or end > 1 << 64:
        raise ValueError(f'{label} overflows')
    return end


def overlaps(first_start, first_size, second_start, second_size):
    first_end = checked_end(first_start, first_size, 'range')
    second_end = checked_end(second_start, second_size, 'range')
    return first_size > 0 and second_size > 0 and first_start < second_end and second_start < first_end


def parse_range(value):
    try:
        start_text, size_text = value.split(':', 1)
        start, size = int(start_text, 0), int(size_text, 0)
    except (ValueError, TypeError) as error:
        raise argparse.ArgumentTypeError('range must be START:SIZE') from error
    try:
        checked_end(start, size, 'range')
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    if size == 0:
        raise argparse.ArgumentTypeError('range size must be non-zero')
    return start, size


def parse_fdt(blob):
    if len(blob) < 40:
        raise ValueError('short FDT')
    magic, total, struct_offset, strings_offset, reserve_offset, version, _, _, strings_size, struct_size = \
        struct.unpack_from('>10I', blob)
    if magic != 0xd00dfeed or version != 17 or not 40 <= total <= min(len(blob), MAX_FDT):
        raise ValueError('invalid FDT header')
    if (struct_offset < 40 or struct_offset % 4 or struct_offset + struct_size > total or
            strings_offset < 40 or strings_offset + strings_size > total or
            reserve_offset < 40 or reserve_offset % 8):
        raise ValueError('invalid FDT offsets')
    position, structure_end = struct_offset, struct_offset + struct_size
    stack, nodes, ended = [], {}, False
    while position + 4 <= structure_end:
        token = struct.unpack_from('>I', blob, position)[0]
        position += 4
        if token == 1:
            terminator = blob.find(b'\0', position, structure_end)
            if terminator < 0 or len(stack) >= 64:
                raise ValueError('invalid FDT node')
            name = blob[position:terminator].decode('ascii')
            position = (terminator + 4) & ~3
            if '/' in name or (not stack and name):
                raise ValueError('invalid FDT node name')
            stack.append(name)
            path = '/'.join(stack) or '/'
            if path in nodes or len(nodes) >= 8192:
                raise ValueError('duplicate or excessive FDT nodes')
            nodes[path] = {}
        elif token == 2:
            if not stack:
                raise ValueError('unbalanced FDT')
            stack.pop()
        elif token == 3:
            if not stack or position + 8 > structure_end:
                raise ValueError('invalid FDT property')
            size, name_offset = struct.unpack_from('>II', blob, position)
            position += 8
            if position + size > structure_end or name_offset >= strings_size:
                raise ValueError('invalid FDT property bounds')
            terminator = blob.find(b'\0', strings_offset + name_offset, strings_offset + strings_size)
            if terminator < 0:
                raise ValueError('invalid FDT property name')
            name = blob[strings_offset + name_offset:terminator].decode('ascii')
            node = nodes['/'.join(stack) or '/']
            if name in node:
                raise ValueError('duplicate FDT property')
            node[name] = blob[position:position + size]
            position = (position + size + 3) & ~3
        elif token == 4:
            continue
        elif token == 9:
            if stack:
                raise ValueError('unbalanced FDT end')
            ended = True
            break
        else:
            raise ValueError('unknown FDT token')
    if not ended:
        raise ValueError('missing FDT end')
    reservations = []
    for position in range(reserve_offset, total - 15, 16):
        start, size = struct.unpack_from('>QQ', blob, position)
        if start == 0 and size == 0:
            break
        checked_end(start, size, 'FDT reservation')
        if size == 0:
            raise ValueError('empty FDT reservation')
        reservations.append(('memreserve', start, size))
    else:
        raise ValueError('missing FDT reservation terminator')
    return nodes, reservations


def cells_2_2(value, label):
    if not value or len(value) % 16:
        raise ValueError(f'invalid {label}')
    return [struct.unpack_from('>QQ', value, offset) for offset in range(0, len(value), 16)]


def fdt_ranges(nodes, reservations):
    if b'mediatek,MT6897' not in nodes.get('/', {}).get('compatible', b'').split(b'\0'):
        raise ValueError('FDT is not MT6897')
    for path in ('/', '/reserved-memory'):
        node = nodes.get(path)
        if node is None:
            raise ValueError(f'missing {path}')
        for name in ('#address-cells', '#size-cells'):
            if node.get(name) != struct.pack('>I', 2):
                raise ValueError(f'unsupported cells in {path}')
    if nodes['/reserved-memory'].get('ranges', b''):
        raise ValueError('translated reserved-memory is unsupported')
    memory = []
    for path, properties in nodes.items():
        if path == '/memory' or path.startswith('/memory@'):
            memory.extend(cells_2_2(properties.get('reg'), f'{path}/reg'))
    if not memory:
        raise ValueError('FDT has no memory ranges')
    fixed = list(reservations)
    dynamic = []
    for path, properties in nodes.items():
        if not path.startswith('/reserved-memory/') or path.count('/') != 2:
            continue
        if 'reg' in properties:
            fixed.extend((path, start, size) for start, size in cells_2_2(properties['reg'], f'{path}/reg'))
        elif 'size' in properties:
            if len(properties['size']) != 8:
                raise ValueError(f'invalid {path}/size')
            requested = struct.unpack('>Q', properties['size'])[0]
            if requested == 0:
                raise ValueError(f'empty dynamic reservation {path}')
            allowed = cells_2_2(properties['alloc-ranges'], f'{path}/alloc-ranges') if 'alloc-ranges' in properties else memory
            dynamic.append((path, requested, allowed))
        else:
            raise ValueError(f'{path} has no reservation description')
    return memory, fixed, dynamic


def parse_payload(blob):
    if len(blob) < 0x2a8 or blob[:8] != b'SWEETXNU':
        raise ValueError('invalid SWEETXNU header')
    version, segment_count = struct.unpack_from('<II', blob, 8)
    if version != 1 or not 1 <= segment_count <= MAX_SEGMENTS or len(blob) < 0x2a8 + segment_count * 32:
        raise ValueError('invalid SWEETXNU version or segment count')
    virt_base, entry, adt_offset, adt_size, kernel_end, phys_base, memory_size = struct.unpack_from('<7Q', blob, 0x10)
    if not memory_size or (phys_base | memory_size | virt_base) & (ALIGN - 1):
        raise ValueError('payload memory window is not 32 MiB aligned')
    checked_end(phys_base, memory_size, 'payload memory window')
    if not virt_base <= kernel_end <= checked_end(virt_base, memory_size, 'virtual memory window') or kernel_end & (PAGE - 1):
        raise ValueError('invalid kernel end')
    if not adt_size or adt_size > MAX_FDT or adt_offset < 0x2a8 + segment_count * 32 or adt_offset + adt_size > len(blob):
        raise ValueError('invalid payload ADT')
    greatest_end, entry_mapped, file_ranges, virtual_ranges = virt_base, False, [], []
    for index in range(segment_count):
        virtual, virtual_size, file_offset, file_size = struct.unpack_from('<4Q', blob, 0x2a8 + index * 32)
        if not virtual_size or virtual & (PAGE - 1) or file_size > virtual_size:
            raise ValueError(f'invalid segment {index}')
        virtual_end = checked_end(virtual, virtual_size, f'segment {index}')
        if virtual < virt_base or virtual_end > kernel_end or file_offset < 0x2a8 + segment_count * 32 or file_offset + file_size > len(blob):
            raise ValueError(f'segment {index} is outside payload bounds')
        if any(overlaps(virtual, virtual_size, start, size) for start, size in virtual_ranges):
            raise ValueError('overlapping virtual segments')
        if any(overlaps(file_offset, file_size, start, size) for start, size in file_ranges):
            raise ValueError('overlapping segment files')
        if overlaps(file_offset, file_size, adt_offset, adt_size):
            raise ValueError('segment overlaps payload ADT')
        virtual_ranges.append((virtual, virtual_size))
        file_ranges.append((file_offset, file_size))
        entry_mapped |= virtual <= entry and entry + 4 <= virtual + file_size
        greatest_end = max(greatest_end, virtual_end)
    if not entry_mapped or entry & 3 or (greatest_end + PAGE - 1) & ~(PAGE - 1) != kernel_end:
        raise ValueError('invalid payload entry or kernel extent')
    adt = phys_base + kernel_end - virt_base
    boot_args = (adt + adt_size + PAGE - 1) & ~(PAGE - 1)
    top = checked_end(boot_args, PAGE, 'boot_args')
    if top > phys_base + memory_size:
        raise ValueError('payload metadata exceeds memory window')
    return {
        'phys_base': phys_base, 'memory_size': memory_size,
        'entry': phys_base + entry - virt_base, 'adt': adt,
        'adt_size': adt_size, 'boot_args': boot_args, 'top': top,
    }


def validate_plan(fdt_blob, payload_blob, occupied):
    nodes, reservations = parse_fdt(fdt_blob)
    memory, fixed, dynamic = fdt_ranges(nodes, reservations)
    plan = parse_payload(payload_blob)
    base, size = plan['phys_base'], plan['memory_size']
    if not any(start <= base and base + size <= start + length for start, length in memory):
        raise ValueError('payload window is outside live RAM')
    conflicts = [(name, start, length) for name, start, length in fixed if overlaps(base, size, start, length)]
    if conflicts:
        raise ValueError(f'payload overlaps fixed reservation {conflicts[0][0]}')
    for name, _, allowed in dynamic:
        if any(overlaps(base, size, start, length) for start, length in allowed):
            raise ValueError(f'payload intersects dynamic allocation range {name}')
    for name, start, length in occupied:
        if overlaps(base, size, start, length):
            raise ValueError(f'payload overlaps occupied range {name}')
    return {
        'decision': 'plan-valid-no-copy-performed',
        'payload': {key: hex(value) for key, value in plan.items()},
        'fixed_reservations_checked': len(fixed),
        'dynamic_reservations_checked': len(dynamic),
        'occupied_ranges_checked': len(occupied),
        'phone_accessed': False,
        'copy_performed': False,
        'jump_performed': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fdt', type=Path, required=True, help='live FDT captured for the same boot')
    parser.add_argument('--payload', type=Path, required=True, help='SWEETXNU v1 payload')
    parser.add_argument('--occupied', action='append', default=[], type=parse_range,
                        help='loader/DTB/stack range as START:SIZE; repeat for every occupied range')
    parser.add_argument('--output', type=Path, help='optional JSON result path')
    arguments = parser.parse_args()
    fdt_blob = arguments.fdt.read_bytes()
    payload_blob = arguments.payload.read_bytes()
    occupied = [(f'occupied-{index}', start, size) for index, (start, size) in enumerate(arguments.occupied)]
    try:
        result = validate_plan(fdt_blob, payload_blob, occupied)
    except ValueError as error:
        result = {
            'decision': 'rejected-no-copy-performed',
            'reason': str(error),
            'phone_accessed': False,
            'copy_performed': False,
            'jump_performed': False,
        }
        result.update({
            'fdt_sha256': hashlib.sha256(fdt_blob).hexdigest(),
            'payload_sha256': hashlib.sha256(payload_blob).hexdigest(),
        })
        encoded = json.dumps(result, indent=2) + '\n'
        if arguments.output:
            arguments.output.write_text(encoded, encoding='utf-8')
        print(encoded, end='', file=sys.stderr)
        return 2
    result.update({
        'fdt_sha256': hashlib.sha256(fdt_blob).hexdigest(),
        'payload_sha256': hashlib.sha256(payload_blob).hexdigest(),
    })
    encoded = json.dumps(result, indent=2) + '\n'
    if arguments.output:
        arguments.output.write_text(encoded, encoding='utf-8')
    print(encoded, end='')


if __name__ == '__main__':
    sys.exit(main())
