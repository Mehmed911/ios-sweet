#!/usr/bin/env python3
"""Run a pinned comparison UFS handler with MTCMOS built in/out, native + EL3."""
import argparse,hashlib,importlib.util,json,re,subprocess
from pathlib import Path
spec=importlib.util.spec_from_file_location('fw_reference',Path(__file__).with_name('fetch-duchamp-firmware-reference.py'))
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def function(text):
    start=text.index('static u_register_t ufs_knl_ctrl(');body=text.index('{',start);end=body+1;depth=1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[start:end]
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path)
    ap.add_argument('--source',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():ap.error('preserve existing output')
    src=a.source/'ufs_ctrl.c';data=src.read_bytes();receipt=reference.check(data);text=data.decode()
    defines=re.findall(r'^#define UFS_MTK_SIP_[^\n]+',text,re.M)
    if len(defines)!=9:raise ValueError('comparison selector set changed')
    repo=Path(__file__).resolve().parent.parent;drivers=repo/'duchamp/drivers'
    names=['test_mt6897_fw_effect.c','mt6897_firmware.c','mt6897_backends.h','mt6897_smc.S',
           'test_mt6897_secure_start.S','test_mt6897_model_runtime.c']
    tracked=[drivers/n for n in names]+[Path(__file__).resolve(),Path(reference.__file__)]
    before={str(p.relative_to(repo)):sha(p) for p in tracked}
    a.output.mkdir(parents=True,exist_ok=False)
    inc=a.output/'firmware-reference.inc';inc.write_text('\n'.join(defines)+'\n'+function(text)+'\n')
    start=(drivers/'test_mt6897_secure_start.S').read_text()
    begin=start.index('secure_trap:\n');end=start.index('secure_fault:\n',begin)
    # An explicitly synthetic monitor adapter invokes the unchanged C handler.
    monitor='''secure_trap:
    mrs x9, esr_el3
    lsr x9, x9, #26
    cmp x9, #0x17
    b.ne secure_fault
    sub sp,sp,#96
    stp x0,x1,[sp]
    stp x2,x3,[sp,#16]
    stp x4,x5,[sp,#32]
    stp x6,x7,[sp,#48]
    stp x29,x30,[sp,#64]
    mov x0,sp
    bl model_ref_monitor
    ldp x0,x1,[sp]
    ldp x2,x3,[sp,#16]
    ldp x29,x30,[sp,#64]
    add sp,sp,#96
    eret
'''
    assembly=a.output/'monitor.S';assembly.write_text(start[:begin]+monitor+start[end:])
    linker=a.output/'model.ld';linker.write_text('ENTRY(_start)\nSECTIONS { . = 0x40200000;\n'
        '.text : { *(.text.boot) *(.text*) } .rodata : { *(.rodata*) } .data : { *(.data*) }\n'
        '. = ALIGN(4096); .bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; }\n'
        '. += 0x80000; _stack_top = .; }\n')
    commands=[]
    def run(cmd,**kw):
        commands.append(cmd);(a.output/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        try:return subprocess.run(cmd,check=True,capture_output=True,text=True,**kw)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
            t=lambda x:x.decode(errors='replace') if isinstance(x,bytes) else x or ''
            (a.output/'failure.log').write_text(t(e.stdout)+t(e.stderr));raise
    reports=[];warnings=['-Wall','-Wextra','-Werror','-Wno-unused-parameter','-Wno-unused-function']
    for enabled in [0,1]:
        flags=['-DCONFIG_MTK_MTCMOS=1'] if enabled else []
        native=a.output/('native-'+str(enabled));common=[*warnings,*flags,'-I'+str(a.output.resolve())]
        run(['clang','-std=c11','-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*common,
             str(drivers/'test_mt6897_fw_effect.c'),str(drivers/'mt6897_firmware.c'),'-o',str(native)])
        n=run([str(native.resolve())]);(a.output/('native-'+str(enabled)+'.log')).write_text(n.stdout+n.stderr)
        m=re.fullmatch(r'(\d+) reference firmware checks passed; (\d+) fixture calls\n',n.stdout)
        if not m or n.stderr:raise ValueError('native handler test failed')
        elf=a.output/('firmware-'+str(enabled)+'.elf')
        run(['clang','-target','aarch64-none-elf','-O2','-ffreestanding','-fno-builtin','-mgeneral-regs-only','-mstrict-align',
             '-DMT6897_MODEL_FREESTANDING',*common,'-nostdlib','-fuse-ld=lld','-Wl,-T,'+str(linker),
             str(drivers/'test_mt6897_fw_effect.c'),str(drivers/'mt6897_firmware.c'),str(drivers/'mt6897_smc.S'),
             str(assembly),str(drivers/'test_mt6897_model_runtime.c'),'-o',str(elf)])
        q=run(['qemu-system-aarch64','-M','virt,secure=on,virtualization=on','-cpu','cortex-a76','-smp','1','-m','64M',
               '-nographic','-monitor','none','-nic','none','-semihosting-config','enable=on,target=native',
               '-device','loader,file='+str(elf)+',cpu-num=0'],timeout=30)
        (a.output/('qemu-'+str(enabled)+'.log')).write_text(q.stdout+q.stderr)
        if n.stdout not in q.stdout or 'MT6897 ARM64 MODEL PASS' not in q.stdout:raise ValueError('EL3 handler test failed')
        reports.append({'mtcmos_compiled':bool(enabled),'native_checks':int(m[1]),'arm64_checks':int(m[1]),
                        'actual_fixture_smc_calls':int(m[2]),'elf_sha256':sha(elf)})
    if before!={str(p.relative_to(repo)):sha(p) for p in tracked} or src.read_bytes()!=data:raise ValueError('inputs changed')
    result={'passed':True,'reference_source':receipt,'handler_sha256':hashlib.sha256(function(text).encode()).hexdigest(),
        'variants':reports,'source_sha256':before,'physical_backend_enabled':False,'installed_firmware_contract_verified':False,
        'scope':'unchanged comparison handler, fixture power hooks and explicit EL3 adapter; no phone BL31, hardware effect, DMA or partition access'}
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
