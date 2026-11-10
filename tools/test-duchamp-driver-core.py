#!/usr/bin/env python3
"""Exercise the portable cores with QEMU UFS and CPU-owned framebuffer memory.

No phone backend, XNU kernel, physical device or host block device is used.
The UFS fixture is freshly generated and opened read-only by QEMU. qtest
drives the actual emulated DMA engine; no guest CPU or guest OS is running.
Known-block mode embeds one block of a pinned local backup in an isolated,
temporary sparse LUN and publishes only digests and test results.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import struct
import subprocess
import tempfile
import time
import uuid
import zlib

U32, U64, PTR, SIZE = C.c_uint32, C.c_uint64, C.c_void_p, C.c_size_t
RD = C.CFUNCTYPE(U32, PTR, U32)
WR = C.CFUNCTYPE(None, PTR, U32, U32)
DMA = C.CFUNCTYPE(C.c_int, PTR, U64, PTR, SIZE)
FENCE = C.CFUNCTYPE(None, PTR)
TICK = C.CFUNCTYPE(U64, PTR)


class IO(C.Structure):
    _fields_ = [('ctx', PTR), ('read', RD), ('write', WR), ('put', DMA),
                ('get', DMA), ('barrier', FENCE), ('ticks', TICK)]


class Config(C.Structure):
    _fields_ = [('io', IO), ('begin', U64), ('end', U64), ('list', U64),
                ('command', U64), ('data', U64), ('timeout', U32),
                ('ready', C.c_uint8), ('lun', C.c_uint8),
                ('descriptor_bits', C.c_uint8), ('data_bits', C.c_uint8), ('poll_limit', U32)]


class Partition(C.Structure):
    _fields_ = [('first_block', U64), ('blocks', U64)]


class GptScratch(C.Structure):
    _fields_ = [('block', C.c_uint8 * 4096), ('primary', C.c_uint8 * 16384),
                ('backup', C.c_uint8 * 16384)]


HFS_TYPE = uuid.UUID('48465300-0000-11aa-aa11-00306543ecac').bytes_le
ROOT_GUID = uuid.UUID('a1f31536-d200-4eb6-b196-530f8768ea63').bytes_le
NEIGHBOR_GUID = uuid.UUID('6d726bf3-22e1-4684-8312-76a36453d8d5').bytes_le


def gpt_fixture(original, sector, fault=None, root=None):
    image = bytearray(original)
    root_offset = 1024 * 1024
    root_bytes = len(root) if root else 2 * 1024 * 1024
    if root:
        image.extend(bytes(root_bytes))
        image[root_offset:root_offset + root_bytes] = root
    image[:512] = bytes(512)
    last_lba = len(image) // sector - 1
    image[450] = 0xee
    struct.pack_into('<II', image, 454, 1, last_lba)
    image[510:512] = b'\x55\xaa'
    if fault == 'hybrid_mbr':
        image[466] = 0x83
    table_bytes = 128 * 128
    backup_lba = last_lba - table_bytes // sector
    first_usable = 2 + table_bytes // sector
    last_usable = backup_lba - 1
    root_first = root_offset // sector
    root_last = (root_offset + root_bytes) // sector - 1
    if not root:
        image[root_offset + 1024:root_offset + 1028] = (
            b'H+\x00\x04' if fault != 'bad_hfs_header' else b'\x00' * 4)
    table = bytearray(table_bytes)
    struct.pack_into('<16s16sQQ', table, 0,
                     NEIGHBOR_GUID if fault == 'wrong_type' else HFS_TYPE, ROOT_GUID,
                     root_first + (fault == 'unaligned'), root_last)
    struct.pack_into('<16s16sQQ', table, 128, HFS_TYPE,
                     ROOT_GUID if fault == 'duplicate' else NEIGHBOR_GUID,
                     root_last if fault == 'overlap' else root_last + 1,
                     root_last + (1024 * 1024) // sector)
    table[56:70] = 'iosroot'.encode('utf-16-le')
    table[184:198] = 'iosroot'.encode('utf-16-le')
    for own, alternate, entries in ((1, last_lba, 2), (last_lba, 1, backup_lba)):
        header = bytearray(sector)
        data = table[:]
        if own == last_lba and fault == 'conflict':
            data[56] ^= 1
        table_lba = first_usable if own == 1 and fault == 'metadata_overlap' else entries
        struct.pack_into('<8sIIIIQQQQ16sQIII', header, 0, b'EFI PART', 0x10000,
                         92, 0, 0, own, alternate, first_usable, last_usable,
                         NEIGHBOR_GUID, table_lba, 128, 128, zlib.crc32(data))
        struct.pack_into('<I', header, 16, zlib.crc32(header[:92]))
        if own == 1 and fault == 'header_crc':
            header[16] ^= 1
        if own == last_lba and fault == 'table_crc':
            data[56] ^= 1
        image[own * sector:(own + 1) * sector] = header
        image[entries * sector:entries * sector + table_bytes] = data
    return bytes(image)


def gpt_checks(lib, host, original, sector, fault, expected_blocks, operations):
    scratch = GptScratch()
    partition = Partition(0x1111, 0x2222)
    guid = C.create_string_buffer(ROOT_GUID)
    result = lib.dufs_gpt_find_hfs(host, sector, guid, C.byref(scratch), C.byref(partition))
    if fault:
        return {'gpt_' + fault + '_rejected': result == -8,
                'gpt_failed_selection_untouched': (partition.first_block, partition.blocks) ==
                (0x1111, 0x2222)}

    first, blocks = 256, expected_blocks
    checks = {'gpt_partition_exact': result == 0 and
              (partition.first_block, partition.blocks) == (first, blocks)}
    storage = C.create_string_buffer(8192)
    for relative in (0, blocks - 1):
        offset = (first + relative) * 4096
        rc = lib.dufs_partition_read(host, C.byref(partition), relative, 1, storage, 4096)
        checks[f'gpt_read_{relative}'] = rc == 0 and storage.raw[:4096] == original[offset:offset + 4096]

    before, saved = len(operations), storage.raw
    rc = lib.dufs_partition_read(host, C.byref(partition), blocks - 1, 2, storage, 8192)
    checks['gpt_reject_read_past_end_no_io'] = rc == -1 and len(operations) == before and storage.raw == saved
    rc = lib.dufs_partition_read(host, C.byref(partition), 0xffffffffffffffff, 1, storage, 4096)
    checks['gpt_reject_read_overflow_no_io'] = rc == -1 and len(operations) == before

    missing = C.create_string_buffer(bytes(range(16)))
    rc = lib.dufs_gpt_find_hfs(host, sector, missing, C.byref(scratch), C.byref(partition))
    checks['gpt_reject_unknown_guid'] = rc == -9 and (partition.first_block, partition.blocks) == (first, blocks)
    rc = lib.dufs_gpt_find_hfs(host, 4096 if sector == 512 else 512, guid,
                              C.byref(scratch), C.byref(partition))
    checks['gpt_reject_wrong_sector_size'] = rc == -8
    return checks


class Surface(C.Structure):
    _fields_ = [('pixels', PTR), ('bytes', SIZE), ('width', U32),
                ('height', U32), ('stride', U32)]


class Rect(C.Structure):
    _fields_ = [('x', U32), ('y', U32), ('width', U32), ('height', U32)]


class Qtest:
    def __init__(self, qemu, image, folder, *, lun=0, keep_trace=True):
        self.folder = folder
        self.path = folder / 'qtest.sock'
        self.stderr = (folder / 'qemu.stderr').open('w')
        self.process = subprocess.Popen([
            qemu, '-machine', 'q35,accel=tcg,max-ram-below-4g=128M',
            '-m', '256M', '-nodefaults', '-display', 'none', '-S',
            '-qtest', f'unix:{self.path},server=on,wait=off',
            '-qtest-log', str(folder / 'qtest.log') if keep_trace else os.devnull,
            '-drive', f'if=none,id=lu0,file={image},format=raw,readonly=on',
            '-device', 'ufs,id=ufs0,addr=04.0,mcq=off',
            '-device', f'ufs-lu,drive=lu0,bus=ufs0,lun={lun}',
        ], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=self.stderr)
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.settimeout(5)
        deadline = time.monotonic() + 5
        while True:
            try:
                self.socket.connect(str(self.path))
                break
            except (FileNotFoundError, ConnectionRefusedError):
                if self.process.poll() is not None or time.monotonic() > deadline:
                    self.close()
                    raise RuntimeError((folder / 'qemu.stderr').read_text())
                time.sleep(.02)
        self.stream = self.socket.makefile('rb')
        try:
            self.configure_pci()
        except BaseException:
            self.close()
            raise

    def configure_pci(self):
        # PCI configuration mechanism #1, in this isolated x86 QEMU test only.
        assert self.cfgread(0) not in (0, 0xffffffff)
        assert self.cfgread(8) >> 16 == 0x0109
        self.pci_id = self.cfgread(0)
        self.cfgwrite(0x10, 0xffffffff)
        self.bar_mask = self.cfgread(0x10)
        assert self.bar_mask & 1 == 0  # memory BAR; implementation may use 32 bits
        self.bar = 0x10000000
        self.cfgwrite(0x10, self.bar)
        if self.bar_mask & 6 == 4:
            self.cfgwrite(0x14, 0)
        self.command('outl 0xcf8 0x80002004')
        self.command('outw 0xcfc 6')  # memory + bus mastering
        assert self.cfgread(0x10) & ~15 == self.bar

    def command(self, command):
        self.socket.sendall((command + '\n').encode())
        while True:
            line = self.stream.readline().decode().strip()
            if line.startswith(('IRQ ', 'IRQ_INTERCEPT')):
                continue
            if not line.startswith('OK'):
                raise RuntimeError(f'qtest {command[:80]}: {line}')
            return line[2:].strip()

    def cfgread(self, offset):
        self.command(f'outl 0xcf8 {0x80002000 + offset:#x}')
        return int(self.command('inl 0xcfc'), 0)

    def cfgwrite(self, offset, value):
        self.command(f'outl 0xcf8 {0x80002000 + offset:#x}')
        self.command(f'outl 0xcfc {value:#x}')

    def read(self, offset):
        return int(self.command(f'readl {self.bar + offset:#x}'), 0)

    def write(self, offset, value):
        self.command(f'writel {self.bar + offset:#x} {value:#x}')

    def put(self, address, data):
        self.command(f'write {address:#x} {len(data):#x} 0x{data.hex()}')

    def get(self, address, length):
        text = self.command(f'read {address:#x} {length:#x}')
        value = bytes.fromhex(text.removeprefix('0x'))
        assert len(value) == length
        return value

    def close(self):
        if hasattr(self, 'stream'):
            self.stream.close()
        self.socket.close()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.stderr.close()


def configure_library(path):
    lib = C.CDLL(str(path))
    lib.dufs_host_size.restype = SIZE
    lib.dufs_timeout_cause.argtypes = [PTR]
    lib.dufs_timeout_cause.restype = U32
    lib.dufs_bind.argtypes = [PTR, C.POINTER(Config)]
    for name in ('dufs_start', 'dufs_nop', 'dufs_device_init'):
        getattr(lib, name).argtypes = [PTR]
    lib.dufs_capacity.argtypes = [PTR, C.POINTER(U64), C.POINTER(U32)]
    lib.dufs_read.argtypes = [PTR, U64, U32, PTR, SIZE]
    lib.dufs_gpt_find_hfs.argtypes = [PTR, U32, PTR, C.POINTER(GptScratch), C.POINTER(Partition)]
    lib.dufs_partition_read.argtypes = [PTR, C.POINTER(Partition), U64, U32, PTR, SIZE]
    lib.dfb_validate.argtypes = [C.POINTER(Surface)]
    lib.dfb_fill.argtypes = [C.POINTER(Surface), Rect, U32]
    lib.dfb_blit.argtypes = [C.POINTER(Surface), U32, U32, C.POINTER(Surface), Rect]
    return lib


def ufs_checks(lib, q, base, original, fault, data_base=None, descriptor_bits=64, data_bits=64,
               gpt=None, known_block=None):
    errors, checks, operations, cdbs = [], {}, [], []
    busy_register = None
    inject, timeout_arm = [None], [False]

    def rd(_, offset):
        operations.append(('r', offset))
        if offset == busy_register:
            return 1
        try:
            value = q.read(offset)
            return value | 1 if inject[0] in ('timeout','frozen') and offset == 0x58 else value
        except Exception as e:
            errors.append(str(e)); return 0xffffffff

    def wr(_, offset, value):
        operations.append(('w', offset, value))
        try:
            q.write(offset, value)
            if timeout_arm[0] and offset == 0x58:
                inject[0] = fault
        except Exception as e:
            errors.append(str(e))

    def put(_, address, data, length):
        operations.append(('dma-write', address, length))
        try:
            raw = C.string_at(data, length)
            if address == base + 0x1000:
                cdbs.append({'transaction': raw[0], 'flags': raw[1],
                             'opcode': raw[16] if raw[0] == 1 else None,
                             'query': raw[12] if raw[0] == 0x16 else None})
                if known_block is not None and cdbs[-1]['opcode'] == 0x88:
                    cdbs[-1].update(lun=raw[2], lba=int.from_bytes(raw[18:26], 'big'),
                                     blocks=int.from_bytes(raw[26:30], 'big'))
            q.put(address, raw)
            return 0
        except Exception as e:
            errors.append(str(e)); return -1

    def get(_, address, data, length):
        operations.append(('dma-read', address, length))
        try:
            raw = bytearray(q.get(address, length))
            if inject[0] == 'tag' and address == base + 0x1200:
                raw[3] ^= 0x80
            C.memmove(data, bytes(raw), length)
            return 0
        except Exception as e:
            errors.append(str(e)); return -1

    def fence(_):
        operations.append(('barrier',))

    def tick(_):
        operations.append(('clock',))
        return 1 if inject[0] == 'frozen' else time.monotonic_ns() // 1_000_000

    callbacks = [RD(rd), WR(wr), DMA(put), DMA(get), FENCE(fence), TICK(tick)]
    data_base=base+0x10000 if data_base is None else data_base
    cfg = Config(IO(None, *callbacks), min(base,data_base), max(base+0x100000,data_base+0x40000),
                 base, base+0x1000, data_base, 500, 1, 0, descriptor_bits, data_bits,
                 64 if fault=='frozen' else 1000000)
    host = C.create_string_buffer(lib.dufs_host_size())
    if known_block is not None:
        cfg.lun = known_block['lun']
    cfg.ready = 0
    checks['unproven_platform_no_io'] = lib.dufs_bind(host, C.byref(cfg)) == -2 and not operations
    cfg.ready = 1
    if known_block is not None:
        for name, register in [('transfer_doorbell', 0x58),
                               ('task_doorbell', 0x78), ('task_run', 0x80)]:
            busy_register = register
            blocked_host = C.create_string_buffer(lib.dufs_host_size())
            before = len(operations)
            refused = (lib.dufs_bind(blocked_host, C.byref(cfg)) == 0 and
                       lib.dufs_start(blocked_host) == -3)
            new_operations = operations[before:]
            checks[f'{name}_blocked_before_write_or_dma'] = (
                refused and ('r', register) in new_operations and
                all(op[0] == 'r' for op in new_operations))
        busy_register = None
        return read_known_block(lib, host, cfg, checks, cdbs, errors, known_block)

    for name, field, value in [('unaligned_list', 'list', base+1),
                              ('overlap', 'command', base),
                              ('outside_window', 'data', cfg.end),
                              ('address_overflow', 'data', 0xfffffffffffffff0),
                              ('unknown_descriptor_limit','descriptor_bits',0),
                              ('unknown_payload_limit','data_bits',0),
                              ('invalid_descriptor_limit','descriptor_bits',65),
                              ('invalid_payload_limit','data_bits',65),
                              ('descriptor_limit_too_small','descriptor_bits',1),
                              ('payload_limit_too_small','data_bits',1)]:
        previous = getattr(cfg, field); setattr(cfg, field, value)
        checks[name+'_no_io'] = lib.dufs_bind(host, C.byref(cfg)) == -1 and not operations
        setattr(cfg, field, previous)
    checks['bind'] = lib.dufs_bind(host, C.byref(cfg)) == 0
    checks['no_rebind'] = lib.dufs_bind(host, C.byref(cfg)) == -3 and not operations
    checks['start'] = lib.dufs_start(host) == 0
    checks['nop'] = lib.dufs_nop(host) == 0
    count, size = U64(), U32()
    checks['capacity_before_device_init_rejected'] = lib.dufs_capacity(host, C.byref(count), C.byref(size)) == -3
    checks['device_init'] = lib.dufs_device_init(host) == 0
    checks['capacity'] = lib.dufs_capacity(host, C.byref(count), C.byref(size)) == 0
    checks['exact_geometry'] = size.value == 4096 and count.value*size.value == len(original)
    reads = []
    for lba, blocks in [(0, 1), (1, 2), (127, 3), (count.value-1, 1), (193, 64)]:
        n = blocks*size.value
        storage = C.create_string_buffer(b'\xa5'*(n+32), n+32)
        rc = lib.dufs_read(host, lba, blocks, C.addressof(storage)+16, n)
        actual = storage.raw[16:-16]
        passed = rc == 0 and actual == original[lba*size.value:(lba+blocks)*size.value]
        canaries = storage.raw[:16] == b'\xa5'*16 and storage.raw[-16:] == b'\xa5'*16
        checks[f'read_{lba}_{blocks}'] = passed and canaries
        reads.append(dict(lba=lba, blocks=blocks, result=rc,
                          sha256=hashlib.sha256(actual).hexdigest(), canaries=canaries))
    target = C.create_string_buffer(b'\xcc'*4096, 4096)
    for name, lba, blocks, n in [('past_end', count.value, 1, 4096),
                               ('overflow_lba', 0xffffffffffffffff, 1, 4096),
                               ('zero_blocks', 0, 0, 0), ('wrong_length', 0, 1, 4095),
                               ('over_max_transfer', 0, 65, 65*4096)]:
        before = len(operations)
        checks[name+'_no_io'] = lib.dufs_read(host, lba, blocks, target, n) == -1 and len(operations) == before
    if gpt:
        checks.update(gpt_checks(lib, host, original, *gpt, operations))
    # Software-injected faults are separate from successful emulation checks.
    # Tag fault alters a returned copy; timeout masks completion only AFTER
    # the doorbell write, so this exercises the bounded wait, not the busy gate.
    if fault in ('timeout','frozen'):
        timeout_arm[0] = True
    else:
        inject[0] = fault
    before = len(operations)
    rc = lib.dufs_read(host, 0, 1, target, 4096)
    checks['injected_'+fault+'_rejected'] = rc == (-4 if fault in ('timeout','frozen') else -6)
    if fault in ('timeout','frozen'):
        checks['timeout_reason_matches'] = lib.dufs_timeout_cause(host)==(2 if fault=='frozen' else 1)
    checks['failed_read_destination_unchanged'] = target.raw == b'\xcc'*4096
    after = len(operations)
    checks['poisoned_host_no_further_io'] = lib.dufs_read(host, 0, 1, target, 4096) == -3 and len(operations) == after
    checks['poisoned_host_no_rebind'] = lib.dufs_bind(host, C.byref(cfg)) == -3
    checks['fault_ran_transport'] = after > before
    checks['callbacks_clean'] = not errors
    checks['only_read_scsi'] = all(c['opcode'] in (0x9e, 0x88) and c['flags'] == 0x40
                                  for c in cdbs if c['transaction'] == 1)
    checks['no_task_abort_or_implicit_reset'] = not any(op[0]=='w' and
        (op[1] == 0x5c or op[1] == 0x34 and op[2] == 0) for op in operations)
    return dict(checks=checks, dma_base=hex(base), data_dma_base=hex(data_base),
                descriptor_address_bits=descriptor_bits,data_address_bits=data_bits,controller_version=hex(q.read(8)),
                pci_id=hex(q.pci_id), geometry=dict(blocks=count.value, block_bytes=size.value),
                reads=reads, packets=cdbs, injected_fault=fault, errors=errors)


def read_known_block(lib, host, cfg, checks, packets, errors, target):
    blocks, size = U64(), U32()
    checks['emulated_controller_initialized'] = (
        lib.dufs_bind(host, C.byref(cfg)) == 0 and lib.dufs_start(host) == 0 and
        lib.dufs_nop(host) == 0 and lib.dufs_device_init(host) == 0 and
        lib.dufs_capacity(host, C.byref(blocks), C.byref(size)) == 0)
    checks['exact_geometry'] = (
        blocks.value == target['lba'] + 2 and size.value == target['bytes'])
    guard = b'\xa5' * 16
    destination = guard + bytes(target['bytes']) + guard
    storage = C.create_string_buffer(destination, len(destination))
    first_packet = len(packets)
    rc = None
    if checks['emulated_controller_initialized'] and checks['exact_geometry']:
        rc = lib.dufs_read(host, target['lba'], 1, C.addressof(storage) + len(guard),
                           target['bytes'])
    data_end = len(guard) + target['bytes']
    digest = hashlib.sha256(storage.raw[len(guard):data_end]).hexdigest() if rc == 0 else None
    matches_android = digest == target['android_sha256']
    reads = packets[first_packet:]
    checks['exact_single_read_command'] = reads == [{
        'transaction': 1, 'flags': 0x40, 'opcode': 0x88, 'query': None,
        'lun': target['lun'], 'lba': target['lba'], 'blocks': 1,
    }]
    checks['only_read_scsi'] = all(
        cmd['opcode'] in (0x9e, 0x88) and cmd['flags'] == 0x40
        for cmd in packets if cmd['transaction'] == 1)
    checks['read_exact_fixture_block'] = rc == 0 and digest == target['fixture_sha256']
    checks['expected_android_digest_verdict'] = matches_android == target['expect_match']
    checks['destination_guards_preserved'] = (
        storage.raw[:len(guard)] == guard and
        storage.raw[data_end:] == guard)
    checks['callbacks_clean'] = not errors
    return dict(checks=checks, command=reads, returned_sha256=digest,
                matched_android=matches_android, read_result=rc)


def run_known_block(lib, qemu, out, reference, backup):
    reference_fields = {
        'os': 'Android', 'product': 'duchamp', 'soc': 'mt6897',
        'partition': 'vendor_boot_a', 'linux_scsi_lun': 2, 'linux_lba': 276480,
        'linux_logical_block_bytes': 4096, 'byte_offset': 1132462080,
        'block_sha256': '065f2cf024655ce86cd67efd58901ded708c34cf2e721778b6b3de67f5382fd6',
        'saved_vendor_boot_sha256': 'd1d1887eba4f7b4920fc4292de5cf4e9aa6e7ce474a6b45ffeb4141434743e49',
    }
    if not reference.is_file() or not backup.is_file():
        raise ValueError('reference and backup must be regular files')
    metadata = json.loads(reference.read_text())
    if (not isinstance(metadata, dict) or
            any(metadata.get(key) != value for key, value in reference_fields.items()) or
            not all(metadata.get(key) is True for key in
                    ('matched_live_partition', 'matched_second_lba_read', 'matched_saved_partition'))):
        raise ValueError('Android reference differs from the pinned observation')
    block_bytes = reference_fields['linux_logical_block_bytes']
    expected_digest = reference_fields['block_sha256']
    backup_digest = reference_fields['saved_vendor_boot_sha256']
    with backup.open('rb') as source:
        if (not stat.S_ISREG(os.fstat(source.fileno()).st_mode) or
                hashlib.file_digest(source, 'sha256').hexdigest() != backup_digest):
            raise ValueError('saved vendor_boot_a backup hash differs')
        source.seek(0)
        block = source.read(block_bytes)
    if len(block) != block_bytes or hashlib.sha256(block).hexdigest() != expected_digest:
        raise ValueError('saved block hash differs from Android reference')

    lun, lba = reference_fields['linux_scsi_lun'], reference_fields['linux_lba']
    report = dict(scope='QEMU UFS qtest only; no XNU guest or physical device',
                  qemu=subprocess.check_output([qemu, '--version'], text=True).splitlines()[0],
                  lun=lun, lba=lba, block_bytes=block_bytes, android_sha256=expected_digest,
                  saved_backup_sha256=backup_digest, physical_backend_enabled=False,
                  physical_ufs_read_performed=False, raw_data_in_report=False, cases={})
    for label, contents in [('match', block),
                            ('one_byte_changed', bytes([block[0] ^ 1]) + block[1:])]:
        with tempfile.TemporaryDirectory(prefix='dufs-known-') as name:
            folder = Path(name)
            image = folder / 'virtual-lun.raw'
            with image.open('wb') as disk:
                disk.truncate((lba + 2) * block_bytes)
                disk.seek(lba * block_bytes)
                disk.write(contents)
            target = dict(lun=lun, lba=lba, bytes=block_bytes, android_sha256=expected_digest,
                          fixture_sha256=hashlib.sha256(contents).hexdigest(),
                          expect_match=(label == 'match'))
            q = Qtest(qemu, image, folder, lun=lun, keep_trace=False)
            try:
                item = ufs_checks(lib, q, 0x100000, None, None, known_block=target)
            finally:
                q.close()
            with image.open('rb') as disk:
                disk.seek(lba * block_bytes)
                item['checks']['fixture_block_unchanged'] = disk.read(block_bytes) == contents
            report['cases'][label] = item

    with backup.open('rb') as source:
        report['backup_unchanged'] = hashlib.file_digest(source, 'sha256').hexdigest() == backup_digest
    checks = [value for case in report['cases'].values() for value in case['checks'].values()]
    checks.append(report['backup_unchanged'])
    report.update(checks=len(checks), checks_passed=sum(checks), passed=all(checks))
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


def framebuffer_checks(lib):
    width, height, stride, guard = 1220, 2712, 4992, 64
    n = stride*height
    memory = C.create_string_buffer(b'\xa5'*(n+2*guard), n+2*guard)
    surface = Surface(C.addressof(memory)+guard, n, width, height, stride)
    tile = C.create_string_buffer(bytes(range(64)), 64)
    source = Surface(C.addressof(tile), 64, 4, 4, 16)
    checks = {'duchamp_geometry': lib.dfb_validate(C.byref(surface)) == 0}
    r = Rect(0, 0, width, height)
    checks['full_fill'] = lib.dfb_fill(C.byref(surface), r, 0xff123456) == 0
    checks['bottom_right_blit'] = lib.dfb_blit(C.byref(surface), width-4, height-4,
                                              C.byref(source), Rect(0, 0, 4, 4)) == 0
    raw = memory.raw
    checks['outer_canaries'] = raw[:guard] == b'\xa5'*guard and raw[-guard:] == b'\xa5'*guard
    checks['all_row_padding_untouched'] = all(raw[guard+y*stride+width*4:guard+(y+1)*stride] ==
                                              b'\xa5'*(stride-width*4) for y in range(height))
    checks['exact_fill_and_blit_pixels'] = all(
        raw[guard+y*stride+x*4:guard+y*stride+x*4+4] ==
        (tile.raw[(y-height+4)*16+(x-width+4)*4:(y-height+4)*16+(x-width+4)*4+4]
         if y>=height-4 and x>=width-4 else b'\x56\x34\x12\xff')
        for y in range(height) for x in range(width))
    digest = hashlib.sha256(raw).hexdigest()
    for name, rect in [('x_overflow', Rect(0xffffffff, 0, 2, 1)),
                       ('past_bottom', Rect(0, height-1, 1, 2)), ('empty', Rect(0, 0, 0, 1))]:
        checks[name+'_no_write'] = lib.dfb_fill(C.byref(surface), rect, 0) == -1 and hashlib.sha256(memory.raw).hexdigest() == digest
    checks['alias_rejected_no_write'] = lib.dfb_blit(C.byref(surface), 1, 1, C.byref(surface), Rect(0, 0, 4, 4)) == -1 and hashlib.sha256(memory.raw).hexdigest() == digest
    short = Surface(C.addressof(memory)+guard, n-1, width, height, stride)
    checks['short_surface_no_write'] = lib.dfb_fill(C.byref(short), r, 0) == -1 and hashlib.sha256(memory.raw).hexdigest() == digest
    return dict(checks=checks, width=width, height=height, stride=stride, sha256=digest,
                scope='CPU-owned host memory; no GPU, scanout, XNU mapping or phone test')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--qemu', default='qemu-system-x86_64')
    ap.add_argument('--cc', default='clang')
    ap.add_argument('--cross-cc', default='clang')
    ap.add_argument('--root-image',type=Path,help='optional existing regular HFS+ image, opened read-only')
    ap.add_argument('--gpt', action='store_true', help='also test GPT-wrapped virtual UFS disks')
    ap.add_argument('--known-block', nargs=2, type=Path, metavar=('REFERENCE_JSON', 'SAVED_VENDOR_BOOT'),
                    help='run only the pinned Android block check on a temporary read-only QEMU LUN')
    args = ap.parse_args()
    if args.known_block and (args.gpt or args.root_image):
        ap.error('--known-block cannot be combined with --gpt or --root-image')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parent.parent
    sources = ['ufs_readonly.c', 'ufs_gpt.c', 'framebuffer.c']
    libpath = out / 'drivers.so'
    command = [args.cc, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-fPIC', '-shared',
               *(str(repo / 'duchamp/drivers' / s) for s in sources), '-o', str(libpath)]
    subprocess.run(command, check=True)
    if args.known_block:
        return run_known_block(configure_library(libpath), args.qemu, out, *args.known_block)
    guards = out/'guard-tests'
    subprocess.run([args.cc,'-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer',
                    str(repo/'duchamp/drivers/test_guards.c'),
                    *(str(repo/'duchamp/drivers'/s) for s in sources),'-o',str(guards)],check=True)
    guard_run=subprocess.run([str(guards)],check=True,capture_output=True,text=True)
    (out/'sanitizer.log').write_text(guard_run.stdout+guard_run.stderr)
    cross_objects=[]
    for source in sources:
        dest=out/(source+'.arm64.o')
        subprocess.run([args.cross_cc,'-target','aarch64-none-elf','-std=c11','-O2',
                        '-ffreestanding','-fno-builtin','-mgeneral-regs-only',
                        '-Wall','-Wextra','-Werror','-c',str(repo/'duchamp/drivers'/source),
                        '-o',str(dest)],check=True)
        cross_objects.append({'file':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    lib = configure_library(libpath)
    original = b''.join(hashlib.sha256(i.to_bytes(8, 'big')).digest()*128 for i in range(4096))
    image = out / 'read-only-fixture.raw'
    image.write_bytes(original)
    digest = hashlib.sha256(original).hexdigest()
    result = {'scope': 'Host cores + actual QEMU UFS DMA; no guest OS or physical device',
              'qemu': subprocess.check_output([args.qemu, '--version'], text=True).splitlines()[0],
              'compiler': subprocess.check_output([args.cc, '--version'], text=True).splitlines()[0],
              'native_sanitizer_checks':guard_run.stdout.strip(),
              'cross_compile_only':cross_objects,
              'source_hashes': {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (repo/'duchamp/drivers').glob('*.[ch]')}, 'ufs': []}
    cases=[(0x100000,'tag',image,original,None,64,64,None),
           (0x100100000,'timeout',image,original,None,64,64,None),
           (0x100100000,'frozen',image,original,None,64,64,None),
           (0x100000,'tag',image,original,0x100110000,32,64,None),
           (0x100100000,'tag',image,original,0x110000,64,32,None)]
    root_data = None
    if args.root_image:
        root=args.root_image.resolve()
        if not stat.S_ISREG(root.stat().st_mode):
            ap.error('--root-image must be a regular file')
        root_data = root.read_bytes()
        if len(root_data)<1024*1024 or len(root_data)%4096 or root_data[1024:1026] not in (b'H+',b'HX'):
            ap.error('--root-image must contain an aligned HFS+ volume')
        cases.append((0x100100000,'tag',root,root_data,None,64,64,None))
    if args.gpt:
        layouts = [(512, None), (4096, None)]
        layouts.extend((512, fault) for fault in (
            'header_crc', 'table_crc', 'conflict', 'overlap', 'duplicate',
            'metadata_overlap', 'unaligned', 'wrong_type', 'bad_hfs_header', 'hybrid_mbr'))
        for sector, fault in layouts:
            disk = out / f'gpt-{sector}-{fault or "valid"}.raw'
            contents = gpt_fixture(original, sector, fault)
            disk.write_bytes(contents)
            cases.append((0x100000, 'tag', disk, contents, None, 64, 64, (sector, fault, 512)))
        if root_data:
            disk = out / 'gpt-512-real-hfs.raw'
            contents = gpt_fixture(original, 512, root=root_data)
            disk.write_bytes(contents)
            cases.append((0x100100000, 'tag', disk, contents, None, 64, 64,
                          (512, None, len(root_data) // 4096)))
    for index, (base, fault, disk, contents, data_base, descriptor_bits, data_bits, gpt) in enumerate(cases):
        folder = out / f'ufs-{index}'
        folder.mkdir()
        # Unix socket length is bounded; use a short temporary socket directory.
        with tempfile.TemporaryDirectory(prefix='sweet-ufs-') as name:
            q = None
            try:
                q = Qtest(args.qemu, disk, Path(name))
                item=ufs_checks(lib,q,base,contents,fault,data_base,descriptor_bits,data_bits,gpt)
                item['image_sha256']=hashlib.sha256(contents).hexdigest()
                item['image_kind'] = 'generated GPT fixture' if gpt else (
                    'existing HFS+ (read only)' if disk != image else 'generated fixture')
                if gpt:
                    item['gpt_sector_bytes'], item['gpt_fault'], expected_blocks = gpt
                    if item['gpt_fault'] is None:
                        item['gpt_expected_partition_blocks'] = expected_blocks
                item['image_unchanged']=disk.read_bytes()==contents
                item['checks']['image_unchanged']=item['image_unchanged']
                result['ufs'].append(item)
            finally:
                if q is not None:
                    q.close()
                for leaf in ('qtest.log', 'qemu.stderr'):
                    if (Path(name)/leaf).exists():
                        shutil.copyfile(Path(name)/leaf, folder/leaf)
    result['fixture_sha256'] = digest
    result['fixture_unchanged'] = hashlib.sha256(image.read_bytes()).hexdigest() == digest
    result['framebuffer'] = framebuffer_checks(lib)
    groups = [r['checks'] for r in result['ufs']] + [result['framebuffer']['checks']]
    result['checks'] = sum(len(g) for g in groups) + 1
    result['passed'] = result['fixture_unchanged'] and all(all(g.values()) for g in groups)
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
