#!/usr/bin/env python3
"""Exercise source-pinned register programmers and raw SMC only in local models/QEMU."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def board_facts(path,expected,repo):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('saved Duchamp DTB provenance mismatch')
    spec=importlib.util.spec_from_file_location('backend_fdt',repo/'tools/inspect-duchamp-hardware.py')
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    tree=module.Fdt(raw)
    base='/soc/spmi@1cc04000'
    spmi=tree.nodes[base]
    if spmi.strings('compatible')!=['mediatek,mt6897-spmi'] or spmi.cells('spmi-dev-mask'):
        raise ValueError('SPMI compatible/route mask differs')
    rails=[]
    for leaf,parent,sid,compat,ramp,always,minimum,maximum in [
        ('pmic@4/regulators/vemc','pmic@4',4,'VEMC',680,True,1200000,3500000),
        ('mt6319@8/mt6319-8-regulator/8-vbuck3','mt6319@8',8,'vbuck3',256,False,300000,1193750)]:
        node=tree.nodes[base+'/'+leaf];pmic=tree.nodes[base+'/'+parent]
        if pmic.cells('reg')!=[sid,0] or node.strings('regulator-compatible')!=[compat]:
            raise ValueError('PMIC SID/rail binding differs')
        if node.scalar('regulator-enable-ramp-delay')!=ramp or ('regulator-always-on' in node.props)!=always:
            raise ValueError('rail ramp/always-on policy differs')
        if node.scalar('regulator-min-microvolt')!=minimum or node.scalar('regulator-max-microvolt')!=maximum:
            raise ValueError('rail constraints differ')
        rails.append({'path':node.path,'sid':sid,'pmic_compatible':pmic.strings('compatible'),
                      'provider_compatible':node.parent.strings('compatible'),
                      'ramp_us':ramp,'always_on':always,'minimum_uv':minimum,'maximum_uv':maximum})
    regs=tree.registers(spmi)
    if [(r['name'],r['physical_address'],r['bytes']) for r in regs]!=[
        ('pmif','0x1cc04000','0x8ff'),('spmimst','0x1cc01000','0x100'),
        ('pmif-p','0x1cc06000','0x8ff'),('spmimst-p','0x1cc00000','0x100')]:
        raise ValueError('SPMI resource translation differs')
    if rails[1]['provider_compatible']!=['mediatek,mt6315_8-regulator']:
        raise ValueError('MT6319 selected regulator ABI differs')
    ufs=tree.nodes['/soc/ufshci@112b0000']
    supply_names=['vcc-supply','vccq-supply']
    for prop,rail in zip(supply_names,rails):
        if tree.provider(ufs.scalar(prop)).path!=rail['path']:
            raise ValueError('UFS supply phandle differs')
    iommus=[]
    for name in ('/soc/iommu@1e802000','/soc/iommu@1e810000'):
        n=tree.nodes[name]
        iommus.append({'path':name,'compatible':n.strings('compatible'),'registers':tree.registers(n)})
    ancestry=[];node=ufs
    while node:
        ancestry.append({'path':node.path,'iommus':node.cells('iommus'),'iommu_map':node.cells('iommu-map')})
        node=node.parent
    return {'fdt_sha256':expected,'rails':rails,'spmi_registers':regs,'spmi_route_mask':0,
            'selected_iommus':iommus,'ufs_dma_ancestry':ancestry,
            'ufs_iommu_route_verified':False,'installed_firmware_verified':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path);ap.add_argument('--fdt',type=Path)
    ap.add_argument('--sources',type=Path)
    args=ap.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent;src=repo/'duchamp/drivers'
    catalog=src/'mt6897-backend-sources.json';manifest=json.loads(catalog.read_text())
    sources=[src/n for n in ('mt6897_pmif.c','mt6897_pmic.c','mt6897_firmware.c','mt6897_iommu.c')]
    test=src/'test_mt6897_backends.c';header=src/'mt6897_backends.h'
    raw=src/'mt6897_smc.S';start=src/'test_mt6897_secure_start.S';runtime=src/'test_mt6897_model_runtime.c'
    inputs=sources+[test,header,raw,start,runtime,catalog,Path(__file__).resolve()]
    before={str(p.relative_to(repo)):digest(p) for p in inputs}
    report={'passed':False,'scope':'native register/provider models + ARM64 EL1/EL3 raw SMC to a QEMU test monitor; no physical backend, installed firmware, PMIC/IOMMU hardware or XNU boot',
            'physical_backend_enabled':False,'source_manifest':manifest}
    commands=[]
    def run(command,**kw):
        commands.append(command);(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        try:
            return subprocess.run(command,check=True,**kw)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
            def text(v):return v.decode(errors='replace') if isinstance(v,bytes) else v or ''
            (out/'failed-command.log').write_text(text(error.stdout)+text(error.stderr))
            report['failure']=str(error);(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
            raise
    if args.fdt:
        report['saved_dtb']=board_facts(args.fdt,manifest['captured_fdt_sha256'],repo)
    if args.sources:
        receipts={}
        for entry in manifest['files']:
            p=args.sources/Path(entry['path']).name
            data=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            if blob!=entry['git_blob']:raise ValueError('upstream source changed: '+entry['path'])
            receipts[entry['path']]={'git_blob':blob,'sha256':digest(p)}
        report['upstream_source_receipts']=receipts
    binary=out/'native-test'
    run(['clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
         '-fno-omit-frame-pointer',*[str(p) for p in sources],str(test),'-o',str(binary)])
    native=run([str(binary)],capture_output=True,text=True)
    (out/'sanitizer.log').write_text(native.stdout+native.stderr)
    match=re.fullmatch(r'(\d+) PMIF, (\d+) PMIC, (\d+) firmware, (\d+) IOMMU checks passed; register/provider models\n',native.stdout)
    if not match:raise ValueError('unexpected native test output')
    report['native_checks']=dict(zip(['pmif','pmic','firmware','iommu'],map(int,match.groups())))
    report['sanitizers']='ASan + UBSan'
    objects={}
    for p in sources+[raw]:
        obj=out/(p.stem+'.o')
        run(['clang','-target','aarch64-none-elf','-O2','-ffreestanding','-fno-builtin','-mgeneral-regs-only',
             '-Wall','-Wextra','-Werror','-c',str(p),'-o',str(obj)])
        imports=run(['llvm-nm','--undefined-only',str(obj)],capture_output=True,text=True).stdout.strip()
        if imports:raise RuntimeError('unexpected standalone imports: '+imports)
        objects[obj.name]=digest(obj)
    linker=out/'secure.ld'
    linker.write_text('ENTRY(_start)\nSECTIONS { . = 0x40200000; .text : { *(.text.boot) *(.text*) }\n'
        '.rodata : { *(.rodata*) } .data : { *(.data*) } . = ALIGN(4096);\n'
        '.bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; }\n'
        '. += 0x80000; _stack_top = .; }\n')
    elf=out/'secure-model.elf'
    run(['clang','-target','aarch64-none-elf','-O2','-ffreestanding','-fno-builtin','-mgeneral-regs-only',
         '-mstrict-align','-Wall','-Wextra','-Werror','-DMT6897_MODEL_FREESTANDING','-nostdlib','-fuse-ld=lld',
         '-Wl,-T,'+str(linker),str(start),str(runtime),*[str(p) for p in sources],str(raw),str(test),'-o',str(elf)])
    arm=run(['qemu-system-aarch64','-M','virt,secure=on,virtualization=on','-cpu','cortex-a76',
         '-smp','1','-m','64M','-nographic','-monitor','none','-serial','stdio','-nic','none',
         '-semihosting-config','enable=on,target=native','-device','loader,file='+str(elf)+',cpu-num=0'],
         capture_output=True,text=True,timeout=30)
    (out/'arm64-secure.log').write_text(arm.stdout+arm.stderr)
    smc=re.search(r'(\d+) raw SMC EL1/EL3 checks passed; test monitor only',arm.stdout)
    if native.stdout not in arm.stdout or not smc or 'MT6897 ARM64 MODEL PASS' not in arm.stdout:
        raise RuntimeError('ARM64 secure fixture did not reproduce native checks and SMC roundtrip')
    after={str(p.relative_to(repo)):digest(p) for p in inputs}
    if before!=after:raise RuntimeError('test/production source changed during the run')
    report.update(passed=True,source_sha256=before,arm64_objects=objects,arm64_checks=report['native_checks'],
                  raw_smc_checks=int(smc[1]),arm64_elf_sha256=digest(elf),test_sources_unchanged=True)
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
