#!/usr/bin/env python3
"""Execute three unchanged pinned parameter bodies in native/ARM64 fixtures."""
import argparse,json,re,subprocess
from pathlib import Path
import duchamp_boot_policy as policy
from duchamp_saved_ufs import sha

def function(text,name):
    m=re.search(r'^static\s+int\s+__init\s+'+name+r'\([^;{}]*\)\s*\{',text,re.M)
    if not m:raise ValueError('missing pinned function '+name)
    end=m.end();depth=1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[m.start():end]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path)
    ap.add_argument('--sources',type=Path,required=True);a=ap.parse_args()
    receipts=policy.sources(a.sources);out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    names=[('kernel/dma/swiotlb.c','setup_io_tlb_npages'),('arch/arm64/mm/init.c','early_disable_dma32'),
           ('arch/arm64/kvm/arm.c','early_kvm_mode_cfg')]
    reference=out/'policy-reference.inc'
    reference.write_text('\n\n'.join(function((a.sources/p).read_text(),n) for p,n in names)+'\n')
    repo=Path(__file__).resolve().parent.parent;src=repo/'duchamp/drivers'
    test=src/'test_boot_policy.c';runtime=src/'test_mt6897_model_runtime.c';start=src/'test_mt6897_model_start.S'
    inputs=[test,runtime,start,Path(__file__).resolve(),Path(policy.__file__),repo/'tools/duchamp_saved_ufs.py']
    before={str(p.relative_to(repo)):sha(p.read_bytes()) for p in inputs};commands=[]
    def run(cmd,**kw):
        commands.append(cmd);(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        try:return subprocess.run(cmd,check=True,capture_output=True,text=True,**kw)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
            t=lambda s:s.decode(errors='replace') if isinstance(s,bytes) else s or ''
            (out/'failure.log').write_text(t(e.stdout)+t(e.stderr));raise
    native=out/'native';flags=['-Wall','-Wextra','-Werror','-I'+str(out)]
    run(['clang','-std=c11','-O1','-g',*flags,'-fsanitize=address,undefined','-fno-sanitize-recover=all',str(test),'-o',str(native)])
    n=run([str(native)]);(out/'native.log').write_text(n.stdout+n.stderr)
    m=re.fullmatch(r'(\d+) saved boot-policy checks passed\n',n.stdout)
    if not m or n.stderr:raise ValueError('native check failed')
    linker=out/'policy.ld';linker.write_text('ENTRY(_start)\nSECTIONS { . = 0x40200000; .text : { *(.text.boot) *(.text*) }\n'
        '.rodata : { *(.rodata*) } .data : { *(.data*) } . = ALIGN(4096);\n'
        '.bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; }\n'
        '. += 0x40000; _stack_top = .; }\n')
    elf=out/'policy.elf'
    run(['clang','-target','aarch64-none-elf','-std=c11','-O2','-ffreestanding','-fno-builtin',
        '-mgeneral-regs-only','-mstrict-align',*flags,'-DMT6897_MODEL_FREESTANDING','-nostdlib','-fuse-ld=lld',
        '-Wl,-T,'+str(linker),str(test),str(start),str(runtime),'-o',str(elf)])
    arm=run(['qemu-system-aarch64','-M','virt','-cpu','cortex-a76','-m','64M','-nographic','-monitor','none',
             '-nic','none','-semihosting-config','enable=on,target=native','-kernel',str(elf)],timeout=30)
    (out/'qemu.log').write_text(arm.stdout+arm.stderr)
    if n.stdout not in arm.stdout or 'MT6897 ARM64 MODEL PASS' not in arm.stdout:raise ValueError('ARM64 check failed')
    if before!={str(p.relative_to(repo)):sha(p.read_bytes()) for p in inputs} or receipts!=policy.sources(a.sources):
        raise ValueError('source inputs changed')
    result={'passed':True,'native_checks':int(m[1]),'arm64_checks':int(m[1]),'source_functions':[n for _,n in names],
        'source_receipts':receipts,'source_sha256':before,'reference_sha256':sha(reference.read_bytes()),
        'elf_sha256':sha(elf.read_bytes()),'inputs_unchanged':True,
        'scope':'unchanged Linux parameter bodies, fixture globals/capabilities; no actual Linux/pKVM/SWIOTLB allocation or physical hardware'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
