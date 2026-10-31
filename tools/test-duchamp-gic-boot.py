#!/usr/bin/env python3
"""ASan/UBSan + ARM64 model tests and actual QEMU GICR discovery/wake."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);a=ap.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent;src=repo/'duchamp/drivers'
    test=src/'test_duchamp_gic_boot.c';start=src/'test_mt6897_model_start.S';runtime=src/'test_mt6897_model_runtime.c'
    paths=[test,start,runtime,src/'duchamp_gic_boot.h',Path(__file__).resolve()]
    before={str(p.relative_to(repo)):sha(p) for p in paths};commands=[]
    def run(cmd,**kw):
        commands.append(cmd);(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        try:return subprocess.run(cmd,capture_output=True,text=True,check=True,**kw)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
            t=lambda s:s.decode(errors='replace') if isinstance(s,bytes) else s or ''
            (out/'failure.log').write_text(t(e.stdout)+t(e.stderr));raise
    native=out/'native'
    run(['clang','-std=c11','-Wall','-Wextra','-Werror','-O1','-g','-fsanitize=address,undefined',
        '-fno-sanitize-recover=all',str(test),'-o',str(native)])
    n=run([str(native)]);(out/'native.log').write_text(n.stdout+n.stderr)
    m=re.fullmatch(r'(\d+) bounded GIC bootstrap checks passed\n',n.stdout)
    if not m or n.stderr:raise ValueError('native checks failed')
    ld=out/'test.ld';ld.write_text('ENTRY(_start)\nSECTIONS { . = 0x40200000; .text : { *(.text.boot) *(.text*) }\n'
        '.rodata : { *(.rodata*) } .data : { *(.data*) } . = ALIGN(4096);\n'
        '.bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; }\n'
        '. += 0x40000; _stack_top = .; }\n')
    elf=out/'test.elf'
    run(['clang','-target','aarch64-none-elf','-std=c11','-O2','-ffreestanding','-fno-builtin',
        '-mgeneral-regs-only','-mstrict-align','-Wall','-Wextra','-Werror','-DMT6897_MODEL_FREESTANDING',
        '-nostdlib','-fuse-ld=lld','-Wl,-T,'+str(ld),str(test),str(start),str(runtime),'-o',str(elf)])
    arm=run(['qemu-system-aarch64','-M','virt,gic-version=3','-cpu','cortex-a76','-m','64M',
        '-nographic','-monitor','none','-nic','none','-semihosting-config','enable=on,target=native','-kernel',str(elf)],timeout=30)
    (out/'qemu.log').write_text(arm.stdout+arm.stderr)
    if n.stdout not in arm.stdout or '4 actual QEMU GICR checks passed' not in arm.stdout or 'MT6897 ARM64 MODEL PASS' not in arm.stdout:
        raise ValueError('ARM64 or actual GICR check failed')
    if before!={str(p.relative_to(repo)):sha(p) for p in paths}:raise ValueError('source changed')
    result={'passed':True,'native_checks':int(m[1]),'arm64_model_checks':int(m[1]),'actual_qemu_gicr_checks':4,
        'elf_sha256':sha(elf),'source_sha256':before,'scope':'portable models + actual QEMU GICR only; no MT6897/firmware/device access'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
