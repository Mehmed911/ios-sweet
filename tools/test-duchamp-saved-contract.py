#!/usr/bin/env python3
"""Source oracles + isolated saved UFS instructions in a local QEMU EL1/EL3 fixture."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
import duchamp_saved_ufs as saved

def function(text,name):
    m=re.search(r'^[A-Za-z_][^\n;{}]*\b'+name+r'\([^;{}]*?\)\s*\{',text,re.M)
    if not m:raise ValueError('missing source function '+name)
    end=m.end();depth=1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[m.start():end]

def assembly(fragments):
    out=['.text','.p2align 2']
    prologue=['stp x29,x30,[sp,#-64]!','stp x19,x20,[sp,#16]','stp x22,x23,[sp,#32]',
              'stp x24,x25,[sp,#48]','sub sp,sp,#96']
    epilogue=['add sp,sp,#96','ldp x19,x20,[sp,#16]','ldp x22,x23,[sp,#32]',
              'ldp x24,x25,[sp,#48]','ldp x29,x30,[sp],#64','ret']
    for name,*_ in saved.SMC_BLOCKS:
        out+=['.global saved_'+name,'saved_'+name+':',*prologue,'mov x19,x0','mov w20,w1',
              'add x22,sp,#32','add x29,sp,#72']
        out+=['.inst 0x%08x'%v for v in struct.unpack('<%dI'%(len(fragments[name])//4),fragments[name])]
        out+=['bl __arm_smccc_smc','ldp x0,x1,[sp,#32]','ldp x2,x3,[sp,#48]',
              'stp x0,x1,[x19]','stp x2,x3,[x19,#16]',*epilogue]
    out+=['.global saved_dma_mask','saved_dma_mask:',*prologue,'str x0,[sp,#64]',
          'mov x19,sp','mov w10,w1']
    replacements={0x12a44:'bl fixture_dma_set_mask',0x12a48:'cbz w0,.Ldma64',
        0x12a58:'bl fixture_dma_set_mask',0x12a5c:'cbnz w0,.Ldma_return',
        0x12a68:'.Ldma_coherent:\nbl fixture_dma_set_coherent_mask'}
    for i,v in enumerate(struct.unpack('<%dI'%(len(fragments['dma'])//4),fragments['dma'])):
        out.append(replacements.get(0x12a34+i*4,'.inst 0x%08x'%v))
    # Boundary: stop before the original ufshcd_memory_alloc() call. The
    # original stream ignores the coherent setter's return and continues.
    out+=['mov w0,wzr','b .Ldma_return','.Ldma64:']
    for i,v in enumerate(struct.unpack('<3I',fragments['dma64'])):
        out.append('b .Ldma_coherent' if i==2 else '.inst 0x%08x'%v)
    out+=['.Ldma_return:',*epilogue,
          '.global __arm_smccc_smc','__arm_smccc_smc:',
          'stp x29,x30,[sp,#-32]!','str x19,[sp,#16]','ldr x19,[sp,#32]',
          'smc #0','stp x0,x1,[x19]','stp x2,x3,[x19,#16]',
          'ldr x19,[sp,#16]','ldp x29,x30,[sp],#32','ret']
    return '\n'.join(out)+'\n'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path);ap.add_argument('--audit',type=Path,required=True)
    ap.add_argument('--sources',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent
    audit=json.loads((a.audit/'result.json').read_text())
    receipts=saved.sources(repo,a.sources)
    if receipts!=audit['source_receipts'] or not audit['audit_complete'] or audit['physical_backend_enabled']:
        raise ValueError('audit/source profile mismatch')
    module=saved.pinned(a.audit/'ufs-mediatek-mod.ko',saved.UFS_SHA)
    fragments,proof=saved.Elf(module).fragments()
    if proof!=audit['saved_client_fragments']:raise ValueError('saved fragment manifest changed')
    selections=[
        ('include/linux/dma-direct.h',['translate_phys_to_dma','translate_dma_to_phys','phys_to_dma_unencrypted',
                                      'phys_to_dma','dma_to_phys','dma_capable']),
        ('kernel/dma/mapping.c',['dma_set_mask','dma_set_coherent_mask','dma_go_direct','dma_alloc_direct','dma_map_direct']),
        ('include/linux/dma-mapping.h',['dma_set_mask_and_coherent']),
        ('drivers/ufs/core/ufshcd.c',['ufshcd_set_dma_mask']),
        ('kernel/dma/direct.h',['dma_direct_map_page']),
        ('arch/arm64/mm/dma-mapping.c',['arch_setup_dma_ops'])]
    extracted=[];names=[]
    for path,functions in selections:
        text=(a.sources/path).read_text()
        for name in functions:extracted.append(function(text,name));names.append(name)
    reference=out/'saved-reference.inc';reference.write_text('\n\n'.join(extracted)+'\n')
    client=out/'saved-client.S';client.write_text(assembly(fragments))
    test=repo/'duchamp/drivers/test_mt6897_saved_contract.c'
    firmware=repo/'duchamp/drivers/mt6897_firmware.c'
    start=repo/'duchamp/drivers/test_mt6897_secure_start.S'
    runtime=repo/'duchamp/drivers/test_mt6897_model_runtime.c'
    tracked=[test,firmware,start,runtime,Path(__file__).resolve(),repo/'tools/duchamp_saved_ufs.py',
             repo/'tools/audit-duchamp-saved-ufs.py',repo/'duchamp/drivers/mt6897-contract-sources.json',
             repo/'duchamp/drivers/mt6897_backends.h']
    before={str(p.relative_to(repo)):saved.sha(p.read_bytes()) for p in tracked}
    commands=[]
    def run(cmd,**kw):
        commands.append(cmd);(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        try:return subprocess.run(cmd,check=True,capture_output=True,text=True,**kw)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
            def text(s):return s.decode(errors='replace') if isinstance(s,bytes) else s or ''
            (out/'failed-command.log').write_text(text(e.stdout)+text(e.stderr));raise
    warnings=['-Wall','-Wextra','-Werror','-Wno-unused-parameter','-Wno-unused-function']
    native=out/'native-test'
    run(['clang','-std=c11','-O1','-g',*warnings,'-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer',
         '-I'+str(out),str(test),str(firmware),'-o',str(native)])
    n=run([str(native)]);(out/'native.log').write_text(n.stdout+n.stderr)
    m=re.fullmatch(r'(\d+) source DMA contract checks passed\n',n.stdout)
    if not m:raise ValueError('unexpected native test output')
    source_count=int(m[1])
    linker=out/'fixture.ld'
    linker.write_text('ENTRY(_start)\nSECTIONS { . = 0x40200000; .text : { *(.text.boot) *(.text*) }\n'
        '.rodata : { *(.rodata*) } .data : { *(.data*) } . = ALIGN(4096);\n'
        '.bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; }\n'
        '. += 0x80000; _stack_top = .; }\n')
    elf=out/'saved-contract.elf'
    run(['clang','-target','aarch64-none-elf','-O2','-ffreestanding','-fno-builtin','-mgeneral-regs-only',
         '-mstrict-align',*warnings,'-DMT6897_MODEL_FREESTANDING','-nostdlib','-fuse-ld=lld',
         '-Wl,-T,'+str(linker),'-I'+str(out),str(test),str(firmware),str(start),str(runtime),str(client),'-o',str(elf)])
    arm=run(['qemu-system-aarch64','-M','virt,secure=on,virtualization=on','-cpu','cortex-a76','-smp','1',
             '-m','64M','-nographic','-monitor','none','-serial','stdio','-nic','none',
             '-semihosting-config','enable=on,target=native','-device','loader,file='+str(elf)+',cpu-num=0'],timeout=30)
    (out/'qemu.log').write_text(arm.stdout+arm.stderr)
    matches=re.search(r'(\d+) saved DMA instruction checks passed\n(\d+) saved SMC instruction checks passed; 12 test-monitor calls',arm.stdout)
    if n.stdout not in arm.stdout or not matches or 'MT6897 ARM64 MODEL PASS' not in arm.stdout:
        raise ValueError('ARM64 source/binary/SMC test failed')
    if before!={str(p.relative_to(repo)):saved.sha(p.read_bytes()) for p in tracked}:raise ValueError('sources changed during tests')
    if saved.sources(repo,a.sources)!=receipts:raise ValueError('upstream inputs changed during tests')
    saved.pinned(a.audit/'ufs-mediatek-mod.ko',saved.UFS_SHA)
    result={'passed':True,'native_source_checks':source_count,'arm64_source_checks':source_count,
        'arm64_saved_dma_checks':int(matches[1]),'arm64_saved_smc_checks':int(matches[2]),'raw_smc_calls':12,
        'source_functions':names,'reference_sha256':saved.sha(reference.read_bytes()),
        'client_fixture_sha256':saved.sha(client.read_bytes()),'elf_sha256':saved.sha(elf.read_bytes()),
        'source_sha256':before,'source_receipts':receipts,'saved_module_sha256':saved.UFS_SHA,
        'saved_fragments':proof,'test_sources_unchanged':True,'physical_backend_enabled':False,
        'installed_firmware_contract_verified':False,'physical_dma_route_verified':False,
        'scope':'unchanged source bodies with kernel/DMA/SWIOTLB fixture callbacks; isolated saved client instructions with relocated external calls/exit branches; actual SMC to a QEMU test monitor, not installed BL31 or physical UFS'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
