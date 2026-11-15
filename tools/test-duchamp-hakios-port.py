#!/usr/bin/env python3
"""Reproducible native/ARM64 offline checks and optional loader review container.

No ADB, fastboot, SMC or physical MMIO. QEMU slot/reset callbacks are models.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

REPO=Path(__file__).resolve().parent.parent
D=REPO/'duchamp/drivers'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--dtb',type=Path,required=True)
    ap.add_argument('--upstream',type=Path,help='Pinned main checker worktree with this device linked under devices/duchamp')
    ap.add_argument('--payload',type=Path,help='Existing SWEETXNU payload; preserved, not rebuilt by this tool')
    ap.add_argument('--boot-template',type=Path,help='Explicit offline QEMU-only Android-v4 header template')
    args=ap.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    commands=[]
    def run(cmd,name,timeout=90,env=None):
        cmd=[str(s) for s in cmd];commands.append(cmd)
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        p=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=timeout,env=env,cwd=REPO)
        (out/(name+'.log')).write_text(p.stdout+p.stderr)
        if p.returncode:raise RuntimeError(f'{name} failed; see {out/name}.log')
        return p.stdout
    run([sys.executable,REPO/'devices/duchamp/tools/hardware.py',args.dtb.resolve(),
         REPO/'devices/duchamp/hardware.json','--check'],'hardware')
    upstream_checked=False
    if args.upstream:
        up=args.upstream.resolve()
        head=run(['git','-C',up,'rev-parse','HEAD'],'upstream-head').strip()
        if head!='63fc2b4633bac3af8e57dadab9f5a8d4cb940438':raise ValueError('Upstream checker pin differs')
        if (up/'devices/duchamp').resolve()!=REPO/'devices/duchamp':raise ValueError('Device link differs')
        run([sys.executable,up/'tools/hakios-device.py','check','duchamp','mt6897'],'upstream-device')
        upstream_checked=True
    link=out/'model.ld';link.write_text('ENTRY(_start)\nSECTIONS { . = 0x40200000; .text : { *(.text.boot) *(.text*) } .rodata : { *(.rodata*) } .data : { *(.data*) } . = ALIGN(4096); .bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; } . += 0x40000; _stack_top = .; }\n')
    units={'inquiry':[D/'ufs_readonly.c',D/'test_ufs_inquiry.c'],
           'boot-choice':[REPO/'devices/duchamp/mtkloader/boot_choice.c',REPO/'devices/duchamp/mtkloader/test_boot_choice.c']}
    results={}
    for name,src in units.items():
        native=out/(name+'.native');elf=out/(name+'.elf')
        run(['clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
             '-fno-sanitize-recover=all',*src,'-o',native],name+'-native-build')
        text=run([native],name+'-native')
        run(['clang','--target=aarch64-none-elf','-std=c11','-O2','-ffreestanding','-fno-builtin',
             '-mgeneral-regs-only','-mstrict-align','-Wall','-Wextra','-Werror','-DMT6897_MODEL_FREESTANDING',
             '-nostdlib','-fuse-ld=lld','-Wl,-T,'+str(link),*src,D/'test_mt6897_model_start.S',
             D/'test_mt6897_model_runtime.c','-o',elf],name+'-arm-build')
        arm=run(['qemu-system-aarch64','-M','virt','-cpu','cortex-a76','-smp','1','-m','64M',
                 '-nographic','-monitor','none','-serial','stdio','-nic','none','-semihosting-config',
                 'enable=on,target=native','-kernel',elf],name+'-arm')
        if text not in arm or 'MT6897 ARM64 MODEL PASS' not in arm:raise ValueError(name+' ARM result differs')
        results[name]=dict(native=text.strip(),arm64_pass=True,elf_sha256=sha(elf))
    env=dict(os.environ,DUCHAMP_TARGET='qemu',SHIM_OUT=str(out/'preview'))
    for key in ('PAYLOAD','MATERIALIZE','READY','JUMP','RETURN','PHONE_CAPTURE','PHONE_LAYOUT','PHONE_CONTRACT','BOOT_ONCE','QEMU_BL31_RECEIVER','LK_RAM_TRANSPORT'):
        env.pop(key,None)
    run(['sh',REPO/'devices/duchamp/mtkloader/build.sh'],'preview-build',env=env)
    run([sys.executable,REPO/'duchamp/bootshim/test_boot_menu_qemu.py',out/'preview/Image',out/'menu-tests'],'menu',timeout=180)
    env.update(BOOT_ONCE='1', SHIM_OUT=str(out/'once-preview'))
    run(['sh',REPO/'devices/duchamp/mtkloader/build.sh'],'once-preview-build',env=env)
    candidate=None
    once_args=[]
    if bool(args.payload)!=bool(args.boot_template):raise ValueError('Supply payload and boot template together')
    if args.payload:
        payload=args.payload.resolve();template=args.boot_template.resolve()
        before={str(p):sha(p) for p in (payload,template)}
        env.update(PAYLOAD=str(payload),MATERIALIZE='1',READY='1',JUMP='1',SHIM_OUT=str(out/'with-xnu'))
        run(['sh',REPO/'devices/duchamp/mtkloader/build.sh'],'xnu-loader-build',env=env)
        once_args=['--with-xnu',out/'with-xnu/Image']
        candidate=out/'duchamp-qemu-review.img'
        run([sys.executable,REPO/'devices/duchamp/mtkloader/build_flashed.py','--stock-boot',template,
             '--loader',out/'with-xnu/Image','--output',candidate],'pack')
        if before!={str(p):sha(p) for p in (payload,template)}:raise ValueError('Inputs changed')
    run([sys.executable,REPO/'duchamp/bootshim/test_boot_once_qemu.py',out/'once-preview/Image',
         args.dtb.resolve(),out/'once-tests',*once_args],'boot-once',timeout=180)
    report=dict(passed=True,tests=results,upstream_checked=upstream_checked,
                menu_results=json.loads((out/'menu-tests/verification.json').read_text()),
                boot_once_results=json.loads((out/'once-tests/verification.json').read_text()),
                loader_sha256=sha(out/'preview/Image'),candidate_sha256=sha(candidate) if candidate else None,
                candidate_bytes=candidate.stat().st_size if candidate else None,
                scope='Offline software/boot-menu tests; physical storage/recovery/boot selection not validated',
                phone_access=False,flash=False,partition_write=False)
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
