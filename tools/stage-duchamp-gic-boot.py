#!/usr/bin/env python3
"""Stage bounded Duchamp GICR scan/wake into already-patched XNU. No device API."""
import argparse,hashlib,json,re
from pathlib import Path

MARKER='DUCHAMP BOUNDED GICR BOOT V1'
def once(text,old,new):
    if text.count(old)!=1:raise ValueError('unexpected or changed GIC source anchor')
    return text.replace(old,new,1)

def transform(text):
    text=once(text,'#include <arm64/sweet_early.h>\n',
        '#include <arm64/sweet_early.h>\n#if defined(DUCHAMP)\n#include "duchamp_gic_boot.h"\n#endif\n')
    start=text.index('static vm_offset_t\nfind_gicr_pe_base()\n{');body=start+len('static vm_offset_t\nfind_gicr_pe_base()\n{')
    end=body;depth=1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    original=text[start:end]
    adapters='''#if defined(DUCHAMP)
/* DUCHAMP BOUNDED GICR BOOT V1 */
static int duchamp_gic_read32(void *ctx,uint64_t off,uint32_t *value) {
    (void)ctx;*value=_gic_read32(gicr_base+off);return 0;
}
static int duchamp_gic_read64(void *ctx,uint64_t off,uint64_t *value) {
    (void)ctx;*value=_gic_read64(gicr_base+off);return 0;
}
static int duchamp_gic_write32(void *ctx,uint64_t off,uint32_t value) {
    (void)ctx;_gic_write32(gicr_base+off,value);return 0;
}
static uint64_t duchamp_gic_nanoseconds(void *ctx) {
    (void)ctx;uint64_t ns;absolutetime_to_nanoseconds(mach_absolute_time(),&ns);return ns;
}
static void duchamp_gic_barrier(void *ctx) {
    (void)ctx;__asm__ volatile("dsb sy" ::: "memory");
}
static const struct dgic_io duchamp_gic_io={NULL,duchamp_gic_read32,duchamp_gic_read64,
    duchamp_gic_write32,duchamp_gic_nanoseconds,duchamp_gic_barrier};
#endif
'''
    replacement='''static vm_offset_t
find_gicr_pe_base()
{
#if defined(DUCHAMP)
    uint64_t off=0;
    int result=dgic_find(&duchamp_gic_io,gicr_size,0,__builtin_arm_rsr64("MPIDR_EL1"),DGIC_MAX_FRAMES,&off);
    if(result)panic("DUCHAMP GICR scan failed %d size=%llu",result,(unsigned long long)gicr_size);
    return gicr_base+off;
#else
'''+original[original.index('{')+1:-1]+'''#endif
}'''
    text=once(text,original,adapters+replacement)
    old='''\t\tif (gicd_size_prop == 0 || gicr_size_prop == 0 ||
\t\t    gicd_base_prop > UINT64_MAX - soc_base_phys ||
\t\t    gicr_base_prop > UINT64_MAX - soc_base_phys) {'''
    text=once(text,old,'''\t\tif (prop_size != 4*sizeof(uint64_t) ||
            !dgic_regions_valid(soc_base_phys,gicd_base_prop,gicd_size_prop,gicr_base_prop,gicr_size_prop)) {''')
    start=text.index('\t// Mark this PE to be awake\n');end=text.index('#if defined(SWEET)\n\t/*',start)
    old=text[start:end]
    new='''#if defined(DUCHAMP)
    struct dgic_wake_result wake={0};
    int wake_status=dgic_wake(&duchamp_gic_io,gicr_size,gicr_pe_base-gicr_base,
        os_atomic_load(&gicr_wake_timeout_ns,relaxed),DGIC_MAX_POLLS,&wake);
    if(wake_status)panic("DUCHAMP GICR wake failed %d cause=%u reads=%u WAKER=0x%x",
        wake_status,wake.timeout_cause,wake.reads,wake.last);
#else
'''+old+'#endif /* DUCHAMP */\n\n'
    return once(text,old,new)

def stage(root):
    repo=Path(__file__).resolve().parent.parent
    source=repo/'duchamp/drivers/duchamp_gic_boot.h';target=root/'pexpert/arm/duchamp_gic_boot.h'
    receipt=root/'pexpert/arm/duchamp_gic_boot.json'
    path=root/'pexpert/arm/pe_fiq.c';old=path.read_text()
    cpu=root/'iokit/Kernel/arm/SweetCPU.cpp';config=root/'iokit/KernelConfigTables.cpp'
    old_cpu=cpu.read_text();old_config=config.read_text()
    if MARKER in old:
        if old.count(MARKER)!=1 or not target.exists() or target.read_bytes()!=source.read_bytes() or not receipt.is_file():
            raise ValueError('partial or changed bounded-GIC staging')
        metadata=json.loads(receipt.read_text())
        if metadata!={'pe_fiq_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'cpu_sha256':hashlib.sha256(cpu.read_bytes()).hexdigest(),
                      'config_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),
                      'header_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}:
            raise ValueError('changed staged GIC source')
        return {'already_staged':True,'header_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    if target.exists() or receipt.exists():raise ValueError('preserve existing GIC header/receipt')
    new=transform(old) # Validate all anchors before touching either file.
    match='    "     \'IONameMatch\'     = \'qcom,kryo470\';"'
    bindings='''#if defined(DUCHAMP)
    /* DUCHAMP CPU BINDINGS V1: architected boot CPU, not a Qualcomm driver. */
    "     'IONameMatch'     = ('qcom,kryo470', 'arm,cortex-a510', 'arm,cortex-a715', 'arm,cortex-a76');"
#else
'''+match+'''\n#endif'''
    new_config=once(old_config,match,bindings)
    name='\tcpuName = OSSymbol::withCStringNoCopy("Kryo 470");'
    new_cpu=once(old_cpu,name,'''#if defined(DUCHAMP)
    /* DUCHAMP CPU BINDINGS V1: only the validated boot CPU is registered. */
    cpuName = OSSymbol::withCStringNoCopy("ARM64 bootstrap CPU");
#else
'''+name+'''\n#endif''')
    target.write_bytes(source.read_bytes());path.write_text(new);cpu.write_text(new_cpu);config.write_text(new_config)
    receipt.write_text(json.dumps({'pe_fiq_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'cpu_sha256':hashlib.sha256(cpu.read_bytes()).hexdigest(),
        'config_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),
        'header_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},indent=2)+'\n')
    return {'already_staged':False,'header_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('xnu',type=Path);a=ap.parse_args()
    print(json.dumps(stage(a.xnu.resolve()),indent=2))
