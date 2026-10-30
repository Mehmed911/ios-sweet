#!/usr/bin/env python3
"""Exercise the portable cores with QEMU UFS and CPU-owned framebuffer memory.

No phone backend, XNU kernel, physical device or host block device is used.
The UFS fixture is freshly generated and opened read-only by QEMU. qtest
drives the actual emulated DMA engine; no guest CPU or guest OS is running.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import tempfile
import time

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
                ('ready', C.c_uint8), ('lun', C.c_uint8)]


class Surface(C.Structure):
    _fields_ = [('pixels', PTR), ('bytes', SIZE), ('width', U32),
                ('height', U32), ('stride', U32)]


class Rect(C.Structure):
    _fields_ = [('x', U32), ('y', U32), ('width', U32), ('height', U32)]


class Qtest:
    def __init__(self, qemu, image, folder):
        self.folder = folder
        self.path = folder / 'qtest.sock'
        self.stderr = (folder / 'qemu.stderr').open('w')
        self.process = subprocess.Popen([
            qemu, '-machine', 'q35,accel=tcg,max-ram-below-4g=128M',
            '-m', '256M', '-nodefaults', '-display', 'none', '-S',
            '-qtest', f'unix:{self.path},server=on,wait=off',
            '-qtest-log', str(folder / 'qtest.log'),
            '-drive', f'if=none,id=lu0,file={image},format=raw,readonly=on',
            '-device', 'ufs,id=ufs0,addr=04.0,mcq=off',
            '-device', 'ufs-lu,drive=lu0,bus=ufs0,lun=0',
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
    lib.dufs_bind.argtypes = [PTR, C.POINTER(Config)]
    for name in ('dufs_start', 'dufs_nop', 'dufs_device_init'):
        getattr(lib, name).argtypes = [PTR]
    lib.dufs_capacity.argtypes = [PTR, C.POINTER(U64), C.POINTER(U32)]
    lib.dufs_read.argtypes = [PTR, U64, U32, PTR, SIZE]
    lib.dfb_validate.argtypes = [C.POINTER(Surface)]
    lib.dfb_fill.argtypes = [C.POINTER(Surface), Rect, U32]
    lib.dfb_blit.argtypes = [C.POINTER(Surface), U32, U32, C.POINTER(Surface), Rect]
    return lib


def ufs_checks(lib, q, base, original, fault):
    errors, checks, operations, cdbs = [], {}, [], []
    inject, timeout_arm = [None], [False]

    def rd(_, offset):
        operations.append(('r', offset))
        try:
            value = q.read(offset)
            return value | 1 if inject[0] == 'timeout' and offset == 0x58 else value
        except Exception as e:
            errors.append(str(e)); return 0xffffffff

    def wr(_, offset, value):
        operations.append(('w', offset, value))
        try:
            q.write(offset, value)
            if timeout_arm[0] and offset == 0x58:
                inject[0] = 'timeout'
        except Exception as e:
            errors.append(str(e))

    def put(_, address, data, length):
        try:
            raw = C.string_at(data, length)
            if address == base + 0x1000:
                cdbs.append({'transaction': raw[0], 'flags': raw[1],
                             'opcode': raw[16] if raw[0] == 1 else None,
                             'query': raw[12] if raw[0] == 0x16 else None})
            q.put(address, raw)
            return 0
        except Exception as e:
            errors.append(str(e)); return -1

    def get(_, address, data, length):
        try:
            raw = bytearray(q.get(address, length))
            if inject[0] == 'tag' and address == base + 0x1200:
                raw[3] ^= 0x80
            C.memmove(data, bytes(raw), length)
            return 0
        except Exception as e:
            errors.append(str(e)); return -1

    callbacks = [RD(rd), WR(wr), DMA(put), DMA(get), FENCE(lambda _: None),
                 TICK(lambda _: time.monotonic_ns() // 1_000_000)]
    cfg = Config(IO(None, *callbacks), base, base+0x100000,
                 base, base+0x1000, base+0x10000, 500, 1, 0)
    host = C.create_string_buffer(lib.dufs_host_size())
    cfg.ready = 0
    checks['unproven_platform_no_io'] = lib.dufs_bind(host, C.byref(cfg)) == -2 and not operations
    cfg.ready = 1
    for name, field, value in [('unaligned_list', 'list', base+1),
                              ('overlap', 'command', base),
                              ('outside_window', 'data', base+0x100000),
                              ('address_overflow', 'data', 0xfffffffffffffff0)]:
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
    # Software-injected faults are separate from successful emulation checks.
    # Tag fault alters a returned copy; timeout masks completion only AFTER
    # the doorbell write, so this exercises the bounded wait, not the busy gate.
    if fault == 'timeout':
        timeout_arm[0] = True
    else:
        inject[0] = fault
    before = len(operations)
    rc = lib.dufs_read(host, 0, 1, target, 4096)
    checks['injected_'+fault+'_rejected'] = rc == (-4 if fault == 'timeout' else -6)
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
    return dict(checks=checks, dma_base=hex(base), controller_version=hex(q.read(8)),
                pci_id=hex(q.pci_id), geometry=dict(blocks=count.value, block_bytes=size.value),
                reads=reads, packets=cdbs, injected_fault=fault, errors=errors)


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
    args = ap.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parent.parent
    sources = ['ufs_readonly.c', 'framebuffer.c']
    libpath = out / 'drivers.so'
    command = [args.cc, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-fPIC', '-shared',
               *(str(repo / 'duchamp/drivers' / s) for s in sources), '-o', str(libpath)]
    subprocess.run(command, check=True)
    guards = out/'guard-tests'
    subprocess.run([args.cc,'-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer',
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
    cases=[(0x100000,'tag',image,original),(0x100100000,'timeout',image,original)]
    if args.root_image:
        root=args.root_image.resolve()
        if not stat.S_ISREG(root.stat().st_mode):
            ap.error('--root-image must be a regular file')
        data=root.read_bytes()
        if len(data)<1024*1024 or len(data)%4096 or data[1024:1026] not in (b'H+',b'HX'):
            ap.error('--root-image must contain an aligned HFS+ volume')
        cases.append((0x100100000,'tag',root,data))
    for index, (base, fault, disk, contents) in enumerate(cases):
        folder = out / f'ufs-{index}'
        folder.mkdir()
        # Unix socket length is bounded; use a short temporary socket directory.
        with tempfile.TemporaryDirectory(prefix='sweet-ufs-') as name:
            q = None
            try:
                q = Qtest(args.qemu, disk, Path(name))
                item=ufs_checks(lib,q,base,contents,fault)
                item['image_sha256']=hashlib.sha256(contents).hexdigest()
                item['image_kind']='existing HFS+ (read only)' if disk!=image else 'generated fixture'
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
