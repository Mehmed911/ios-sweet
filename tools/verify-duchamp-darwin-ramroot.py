#!/usr/bin/env python3
"""Verify the offline Duchamp HFS+ userspace test from payload and guest evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy
import struct

import adt
from mkpayload import CMDLINE, SEG_TABLE, parse_macho

RAM_ROOT_SIZE = 32 * 1024 * 1024


def check_ramdisk(payload, root):
    if len(payload) < SEG_TABLE:
        raise ValueError('truncated payload header')
    magic, version, count = struct.unpack_from('<8sII', payload)
    virt, _, adt_offset, adt_size, end, phys, memory = struct.unpack_from('<7Q', payload, 0x10)
    table_end = SEG_TABLE + count * 32
    if (magic, version) != (b'SWEETXNU', 1) or not count:
        raise ValueError('invalid payload header')
    if not table_end <= adt_offset < adt_offset + adt_size <= len(payload):
        raise ValueError('invalid payload table or ADT extent')
    va, size, offset, length = struct.unpack_from('<4Q', payload, table_end - 32)
    if not (virt <= va < end == va + size <= virt + memory):
        raise ValueError('RAM disk escapes the payload RAM window')
    if not table_end <= offset <= offset + length <= adt_offset:
        raise ValueError('invalid RAM disk file extent')
    if size != RAM_ROOT_SIZE or length != size or len(root) != size:
        raise ValueError('RAM root is not exactly 32 MiB')
    if memoryview(payload)[offset:offset + length] != root or root[1024:1026] != b'H+':
        raise ValueError('payload RAM disk bytes or HFS+ signature mismatch')
    boot_args = payload[CMDLINE:SEG_TABLE].split(b'\0', 1)[0].decode().split()
    for key, value in (('rd', 'md0'), ('rootrw', '0')):
        if [arg for arg in boot_args if arg.split('=', 1)[0] == key] != [f'{key}={value}']:
            raise ValueError('expected a read-only md0 root')
    tree, consumed = adt.parse(payload[adt_offset:adt_offset + adt_size])
    for name in ('chosen', 'memory-map'):
        nodes = [child for child in tree.children if child.name == name]
        if len(nodes) != 1:
            raise ValueError(f'missing or ambiguous ADT node {name}')
        tree = nodes[0]
    pa = phys + va - virt
    properties = [(flags, data) for name, flags, data in tree.props if name == 'RAMDisk']
    if consumed != adt_size or properties != [(0, struct.pack('<QQ', pa, size))]:
        raise ValueError('ADT RAMDisk does not name the embedded RAM root')
    return {'pa': f'{pa:#x}', 'size': size}


def check_execution(console, result, fixture_size):
    dynamic = set(re.findall(r'RAMROOT USER: dynamic pid=(\d+) ppid=(\d+) images=(\d+) libSystem=(\d+)', console))
    main_pid, parent, loaded_images, libsystem = map(int, next(iter(dynamic))) if len(dynamic) == 1 else (0, 0, 0, 0)
    child = set(re.findall(r'RAMROOT USER: static child pid=(\d+) exit=42 wait=2a00', console))
    child_pid = int(next(iter(child))) if len(child) == 1 else 0
    checks = {
        'hfs_root_mounted_read_only': (
            'QEMU RAM ROOT MOUNTED' in console and 'RAMROOT USER: HFS root readonly source=' in console),
        'devfs_console_ready': 'DEVFS CONSOLE READY' in console and 'PID1 CONSOLE OPEN OK' in console,
        'pid1_started_exec': 'SWEET dynamic init: starting C program via execve' in console,
        'dyld_libsystem_and_distinct_pid': main_pid > 1 and parent == 1 and loaded_images >= 2 and libsystem == 1,
        'hfs_directory_entries': 'RAMROOT USER: HFS directory fixture static and init present' in console,
        'hfs_read_eof_private_vm_and_invalid_mapping': (
            f'RAMROOT USER: HFS bytes={fixture_size} EOF private VM and EINVAL verified' in console),
        'hfs_lookup_and_write_errors': 'RAMROOT USER: ENOTDIR=20 ENOENT=2 EROFS=30 verified' in console,
        'real_mach_send_receive': 'RAMROOT USER: Mach loopback id=391 payload=44554348' in console,
        'static_child_exec_and_wait': (child_pid > 1 and child_pid != main_pid and
                                      'RAMROOT STATIC: entered LC_UNIXTHREAD child' in console),
        'dynamic_exit_zero_verified_by_pid1': (main_pid > 1 and f'RAMROOT USER: PASS dynamic pid={main_pid}\n' in console and
                                              'SWEET dynamic init: C child exit 0 verified' in console),
        'pid1_survived': 'SWEET dynamic init: still alive' in console,
        'no_visible_panic_or_loader_failure': (
            result.get('status') == 'no_panic_observed' and result.get('unknown_glyphs') == 0
            and not any(marker in console for marker in ('RAMROOT USER: FAIL', 'TEST FAILED', 'SWEET EARLY PANIC:',
                                                        'DEVFS MOUNT FAILED',
                                                        'panic(cpu ', 'Library not loaded:', 'Symbol not found:'))),
    }
    return checks, {'pid1': parent, 'dynamic_pid': main_pid, 'loaded_images': loaded_images,
                    'static_pid': child_pid, 'static_exit': 42 if checks['static_child_exec_and_wait'] else None,
                    'dynamic_exit': 0 if checks['dynamic_exit_zero_verified_by_pid1'] else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    out = parser.parse_args().output
    run = out / 'run'
    sources = [run / 'serial.txt', *sorted((run / 'frames').glob('*.txt')), run / 'fb.txt']
    console = '\n'.join(path.read_text(errors='replace') for path in sources)
    result = json.loads((run / 'result.json').read_text())
    audit = json.loads((out / 'runtime-audit.json').read_text())
    fixture_size = (out / 'ramroot-fixture.txt').stat().st_size
    checks, processes = check_execution(console, result, fixture_size)

    root = (out / 'root.hfs').read_bytes()
    payload = (out / 'payload.bin').read_bytes()
    layout = check_ramdisk(payload, root)
    macho = runpy.run_path(str(Path(__file__).with_name('audit-darwin-runtime.py')))['macho']
    dynamic = macho(out / 'c-runtime-test')
    static = macho(out / 'ramroot-static')
    init = macho(out / 'launchd')
    checks.update(
        standalone_runtime_files=bool(audit['passed']),
        dynamic_macho=(dynamic['filetype'] == 2 and dynamic['dylinker'] == '/usr/lib/dyld'
                       and dynamic['main_entry'] is not None and dynamic['code_signature']
                       and any(item['path'] == '/usr/lib/libSystem.B.dylib' for item in dynamic['dependencies'])),
        static_macho=all(info['filetype'] == 2 and info['dylinker'] is None and not info['dependencies']
                         and info['main_entry'] is None and info['code_signature']
                         and parse_macho((out / name).read_bytes())['entry'] is not None
                         for name, info in (('ramroot-static', static), ('launchd', init))),
        ramdisk_unchanged_in_guest=root == (run / 'ramdisk-final.hfs').read_bytes(),
        payload_rebuilt_identically=payload == (out / 'payload.rebuild.bin').read_bytes(),
    )
    report = {
        'passed': all(checks.values()), 'checks': checks, 'processes': processes,
        'ramdisk': layout, 'elapsed_host_seconds': result['elapsed_host_seconds'],
        'root_sha256': hashlib.sha256(root).hexdigest(),
        'payload_sha256': hashlib.sha256(payload).hexdigest(),
        'static_macho_sha256': static['sha256'], 'dynamic_macho_sha256': dynamic['sha256'],
        'standalone_runtime_files': len(audit['files']),
        'guest_evidence': [str(path.relative_to(out)) for path in sources],
    }
    (run / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
