#!/usr/bin/env python3
"""Native sanitizer and ARM64 QEMU checks for operation-wide UFS poll budgets."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);a=ap.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent;src=repo/'duchamp/drivers'
    core=src/'ufs_readonly.c';test=src/'test_ufs_poll.c';start=src/'test_mt6897_model_start.S';runtime=src/'test_mt6897_model_runtime.c'
    inputs=[core,test,start,runtime,src/'ufs_readonly.h',Path(__file__).resolve()]
    before={str(p.relative_to(repo)):sha(p) for p in inputs};commands=[]
    def run(cmd,**kw):
        commands.append(cmd);(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        try:return subprocess.run(cmd,check=True,capture_output=True,text=True,**kw)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
            def text(s):return s.decode(errors='replace') if isinstance(s,bytes) else s or ''
            (out/'failure.log').write_text(text(e.stdout)+text(e.stderr));raise
    native=out/'native'
    run(['clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
         '-fno-sanitize-recover=all','-fno-omit-frame-pointer',str(core),str(test),'-o',str(native)])
    n=run([str(native)]);(out/'native.log').write_text(n.stdout+n.stderr)
    m=re.fullmatch(r'(\d+) bounded UFS polling checks passed\n',n.stdout)
    if not m or n.stderr:raise ValueError('native fixture/sanitizer failure')
    linker=out/'model.ld';linker.write_text('ENTRY(_start)\nSECTIONS { . = 0x40200000;\n'
        '.text : { *(.text.boot) *(.text*) } .rodata : { *(.rodata*) } .data : { *(.data*) }\n'
        '. = ALIGN(4096); .bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; }\n'
        '. += 0x40000; _stack_top = .; }\n')
    elf=out/'model.elf'
    run(['clang','-target','aarch64-none-elf','-std=c11','-O2','-ffreestanding','-fno-builtin',
         '-mgeneral-regs-only','-mstrict-align','-Wall','-Wextra','-Werror','-DMT6897_MODEL_FREESTANDING',
         '-nostdlib','-fuse-ld=lld','-Wl,-T,'+str(linker),str(core),str(test),str(start),str(runtime),'-o',str(elf)])
    arm=run(['qemu-system-aarch64','-M','virt','-cpu','cortex-a76','-smp','1','-m','64M','-nographic',
             '-monitor','none','-serial','stdio','-nic','none','-semihosting-config','enable=on,target=native',
             '-kernel',str(elf)],timeout=30)
    (out/'qemu.log').write_text(arm.stdout+arm.stderr)
    if n.stdout not in arm.stdout or 'MT6897 ARM64 MODEL PASS' not in arm.stdout:raise ValueError('ARM64 fixture failed')
    if before!={str(p.relative_to(repo)):sha(p) for p in inputs}:raise ValueError('test sources changed')
    result={'passed':True,'native_checks':int(m[1]),'arm64_checks':int(m[1]),'source_sha256':before,
            'elf_sha256':sha(elf),'test_sources_unchanged':True,
            'scope':'software register/DMA models on native + ARM64 QEMU; no physical hardware, XNU or actual UFS controller'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
