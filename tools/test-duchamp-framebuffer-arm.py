#!/usr/bin/env python3
"""Run the actual ARM64 software raster core on guest RAM; never a GPU/phone test."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    src=Path(__file__).resolve().parent.parent/'duchamp/drivers'
    elf=out/'framebuffer.elf'
    subprocess.run(['clang','-target','aarch64-none-elf','-O2','-ffreestanding',
                    '-fno-builtin','-fno-stack-protector','-mgeneral-regs-only',
                    '-Wall','-Wextra','-Werror','-nostdlib','-fuse-ld=lld',
                    '-Wl,-T,'+str(src/'test_framebuffer_arm.ld'),
                    str(src/'test_framebuffer_arm.S'),str(src/'test_framebuffer_arm.c'),
                    str(src/'framebuffer.c'),'-o',str(elf)],check=True)
    qemu='qemu-system-aarch64'
    with tempfile.TemporaryDirectory(prefix='sweet-arm-fb-') as temp:
        qmp=Path(temp)/'qmp.sock'
        serial=out/'serial.txt'
        stderr=(out/'qemu.stderr').open('w')
        process=subprocess.Popen([qemu,'-machine','virt,virtualization=off,secure=off',
            '-cpu','cortex-a76','-m','4G','-smp','1','-nodefaults','-display','none',
            '-serial','file:'+str(serial),'-qmp',f'unix:{qmp},server=on,wait=off',
            '-device',f'loader,file={elf},cpu-num=0'],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=stderr)
        sock=socket.socket(socket.AF_UNIX); sock.settimeout(5)
        try:
            deadline=time.monotonic()+20
            while True:
                text=serial.read_text(errors='replace') if serial.exists() else ''
                if 'ARM FB FAIL' in text:
                    raise RuntimeError(text)
                if 'ARM FB PASS' in text:
                    break
                if process.poll() is not None or time.monotonic()>deadline:
                    raise RuntimeError('ARM framebuffer did not complete: '+text)
                time.sleep(.05)
            sock.connect(str(qmp)); stream=sock.makefile('rb')
            def response():
                while True:
                    line=stream.readline()
                    if not line: raise RuntimeError('QMP disconnected')
                    value=json.loads(line)
                    if 'return' in value or 'error' in value or 'QMP' in value:
                        return value
            assert 'QMP' in response()
            def command(name,arguments=None):
                sock.sendall((json.dumps({'execute':name,'arguments':arguments or {}})+'\n').encode())
                result=response()
                if 'error' in result: raise RuntimeError(str(result))
                return result['return']
            command('qmp_capabilities'); command('stop')
            dump=out/'framebuffer.bin'; n=4992*2712
            result=command('human-monitor-command',{'command-line':
                f'pmemsave {0xfcc2f000-64:#x} {n+128:#x} {json.dumps(str(dump))}'})
            if result.strip(): raise RuntimeError(result)
            raw=dump.read_bytes()
            expected=bytearray(b'\xa5'*(n+128))
            for row in range(2712):
                expected[64+row*4992:64+row*4992+1220*4]=b'\x56\x34\x12\xff'*1220
            tile=bytes(range(64))
            for row in range(4):
                offset=64+(2712-4+row)*4992+(1220-4)*4
                expected[offset:offset+16]=tile[row*16:row*16+16]
            checks={'el1_mmu_caches_off':'ARM FB PASS EL1 MMU/cache off' in text,
                    'exact_size':len(raw)==n+128,'every_pixel_padding_and_guard':raw==expected}
            report={'passed':all(checks.values()),'checks':checks,'sha256':hashlib.sha256(raw).hexdigest(),
                    'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),
                    'qemu':subprocess.check_output([qemu,'--version'],text=True).splitlines()[0],
                    'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in [src/'framebuffer.c',src/'framebuffer.h',src/'test_framebuffer_arm.c',
                                  src/'test_framebuffer_arm.S',src/'test_framebuffer_arm.ld']},
                    'scope':'ARM64 code executed on guest RAM at Duchamp framebuffer geometry; no GPU/DSI/scanout, XNU or phone'}
            (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps(report,indent=2))
            return 0 if report['passed'] else 1
        finally:
            sock.close()
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=5)
            stderr.close()


if __name__=='__main__':
    raise SystemExit(main())
