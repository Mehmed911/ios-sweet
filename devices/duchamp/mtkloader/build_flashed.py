#!/usr/bin/env python3
"""Offline-only boot-container builder. The historical name does not flash.

Only accepts the emulator image produced by this device's build.sh. The fixed
QEMU entry address is checked before packaging: this is NOT a phone candidate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

REPO=Path(__file__).resolve().parents[3]
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('stock-boot','loader','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    manifest=a.output.with_suffix('.manifest.json')
    if a.output.exists() or manifest.exists():p.error('preserve existing output and manifest')
    raw=a.loader.read_bytes()
    if raw[56:60]!=b'ARM\x64' or struct.unpack_from('<Q',raw,8)[0]!=0:
        p.error('unsupported loader header')
    # Read the linked ELF symbol rather than guessing execution compatibility.
    elf=a.loader.parent/'duchamp-diagnostic.elf'
    if not elf.is_file():p.error('loader ELF is required')
    symbols={}
    for line in subprocess.check_output(['llvm-nm',str(elf)],text=True).splitlines():
        fields=line.split()
        if len(fields)==3:
            symbols[fields[2]]=int(fields[0],16)
    head=symbols.get('_head')
    if head!=0x40200000 or symbols.get('_end',0)-head!=len(raw):
        p.error('not the guarded QEMU entry or image size')
    with tempfile.TemporaryDirectory(prefix='duchamp-pack-') as directory:
        converted=Path(directory)/'Image'
        subprocess.run(['llvm-objcopy','-O','binary',str(elf),str(converted)],check=True)
        linked=converted.read_bytes()
        if len(linked)>len(raw) or not raw.startswith(linked) or any(raw[len(linked):]):
            p.error('loader bytes do not match the linked ELF')
    subprocess.run([sys.executable,str(REPO/'duchamp/bootshim/pack_boot.py'),
                    '--stock-boot',str(a.stock_boot),'--kernel',str(a.loader),
                    '--out',str(a.output),'--lz4-legacy'],check=True)
    container=a.output.read_bytes();template=a.stock_boot.read_bytes()
    kernel_bytes,=struct.unpack_from('<I',container,8)
    compressed=container[4096:4096+kernel_bytes]
    unpacked=subprocess.run(['lz4','-d','-c'],input=compressed,capture_output=True,check=True).stdout
    if unpacked!=raw or container[12:1584]!=template[12:1584]:
        p.error('container round-trip or preserved metadata differs')
    if len(container)!=((4096+kernel_bytes+4095)&~4095) or any(container[4096+kernel_bytes:]):
        p.error('unexpected container length or padding')
    report=dict(scope='QEMU-only offline Android-v4/LZ4 container',phone_flash_allowed=False,
                android_chainboot_verified=False,loader_sha256=hashlib.sha256(raw).hexdigest(),
                loader_roundtrip_verified=True,
                one_session_policy_linked='duchamp_take_xnu_request' in symbols,
                loader_matches_elf=True,
                image_bytes=a.output.stat().st_size,
                image_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest())
    with manifest.open('x') as stream:
        stream.write(json.dumps(report,indent=2)+'\n')
