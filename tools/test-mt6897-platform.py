#!/usr/bin/env python3
"""Test MT6897 power/DMA sequencing locally; never discovers or accesses a phone."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_fdt(path, expected, repo):
    spec=importlib.util.spec_from_file_location('mt6897_saved_fdt',repo/'tools/inspect-duchamp-hardware.py')
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('saved-DTB provenance differs from the captured Duchamp tree')
    tree=module.Fdt(raw)
    ufs=tree.nodes['/soc/ufshci@112b0000']
    phy=tree.nodes['/soc/ufsphy@112a0000']
    if tree.registers(ufs)[0]['physical_address']!='0x112b0000' or tree.registers(phy)[0]['physical_address']!='0x112a0000':
        raise ValueError('captured physical register translation changed')
    phys=tree.references(ufs,'phys','#phy-cells')
    if len(phys)!=1 or phys[0]['provider']!=phy.path or phys[0]['args']:
        raise ValueError('unexpected PHY binding')
    if phy.scalar('mphy-ver')!=1 or 'mediatek,ufs-rtff-mtcmos' not in ufs.props or 'mediatek,ufs-support-va09' in ufs.props:
        raise ValueError('power policy differs from the implemented version-1 subset')
    resets=tree.references(ufs,'resets','#reset-cells','reset-names')
    expected_names=['unipro_rst','crypto_rst','hci_rst']
    if [r['name'] for r in resets]!=expected_names or [r['args'] for r in resets]!=[[0],[1],[2]]:
        raise ValueError('reset IDs/order differ')
    provider='/syscon@112bb000/reset-controller'
    if any(r['provider']!=provider for r in resets):
        raise ValueError('unexpected reset provider')
    reset_cells=tree.nodes[provider].cells('ti,reset-bits')
    expected_cells=[v for i in range(3) for v in (0x48,i,0x4c,i,0,0,0x1c)]
    if reset_cells!=expected_cells:
        raise ValueError('reset register tuples differ')
    ancestry=[]
    node=ufs
    while node:
        ancestry.append({'path':node.path,
            'dma_ranges':node.cells('dma-ranges') if 'dma-ranges' in node.props else None,
            'iommus':node.cells('iommus') if 'iommus' in node.props else None,
            'iommu_map':node.cells('iommu-map') if 'iommu-map' in node.props else None,
            'dma_coherent':'dma-coherent' in node.props})
        node=node.parent
    return {'fdt_sha256':expected,'mphy_version':1,'rtff_mtcmos':True,'va09_supported':False,
            'reset_ids':expected_names,'reset_register_cells':reset_cells,
            'reset_status_supported':False,'dma_ancestry':ancestry,
            'physical_dma_route_verified':False,'physical_firmware_contract_verified':False}


def source_receipts(directory, manifest):
    receipts={}
    for entry in manifest['vendor']['files']:
        path=directory/Path(entry['path']).name
        raw=path.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob!=entry['git_blob']:
            raise ValueError('pinned upstream Git blob mismatch: '+entry['path'])
        receipts[entry['path']]={'git_blob':blob,'sha256':hashlib.sha256(raw).hexdigest()}
    return receipts


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path)
    ap.add_argument('--fdt',type=Path,help='existing saved DTB only; optional, never acquired from hardware')
    ap.add_argument('--sources',type=Path,help='optional previously downloaded exact vendor source files')
    args=ap.parse_args()
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent
    src=repo/'duchamp/drivers'
    manifest_path=src/'mt6897-platform-sources.json'
    manifest=json.loads(manifest_path.read_text())
    report={'passed':False,'scope':'native and ARM64 QEMU power/DMA callback models; no physical backend or XNU execution',
            'physical_backend_enabled':False,'source_manifest':manifest}
    if args.fdt:
        report['saved_dtb']=inspect_fdt(args.fdt,manifest['captured_fdt_sha256'],repo)
    if args.sources:
        report['upstream_source_receipts']=source_receipts(args.sources,manifest)
    paths=[src/n for n in ('mt6897_ufs_platform.c','mt6897_ufs_platform.h',
            'mt6897_ufs_dma.c','mt6897_ufs_dma.h','test_mt6897_platform.c')]
    test=out/'test'
    commands=[]
    def run(command,**kw):
        commands.append(command)
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        try:
            return subprocess.run(command,check=True,**kw)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
            def decoded(value):
                return value.decode(errors='replace') if isinstance(value,bytes) else value or ''
            (out/'failed-command.log').write_text(decoded(error.stdout)+decoded(error.stderr))
            report['failure']=str(error)
            (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
            raise
    run(['clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
         '-fno-omit-frame-pointer',str(paths[0]),str(paths[2]),str(paths[4]),'-o',str(test)])
    result=run([str(test)],capture_output=True,text=True)
    (out/'sanitizer.log').write_text(result.stdout+result.stderr)
    match=re.fullmatch(r'(\d+) power-sequence checks, (\d+) DMA-ownership checks passed; callbacks/models only\n',result.stdout)
    if not match:
        raise RuntimeError('unexpected test output')
    report['power_checks']=int(match[1])
    report['dma_checks']=int(match[2])
    report['sanitizers']='ASan + UBSan'
    objects={}
    for path in (paths[0],paths[2]):
        obj=out/(path.stem+'.arm64.o')
        run(['clang','-target','aarch64-none-elf','-std=c11','-O2','-ffreestanding','-fno-builtin',
             '-mgeneral-regs-only','-Wall','-Wextra','-Werror','-c',str(path),'-o',str(obj)])
        imports=run(['llvm-nm','--undefined-only',str(obj)],capture_output=True,text=True).stdout.strip()
        if imports:
            raise RuntimeError('freestanding imports: '+imports)
        objects[obj.name]=sha(obj)
    report['arm64_objects']=objects
    # The standalone MMU-off fixture needs strict-alignment code generation.
    # Its byte-wise runtime supplies libc primitives lowered by that mode;
    # the separate normal-RAM objects above have no undefined imports.
    runtime=src/'test_mt6897_model_runtime.c'
    start=src/'test_mt6897_model_start.S'
    linker=out/'model.ld'
    linker.write_text('ENTRY(_start)\nSECTIONS { . = 0x40200000;\n'
        ' .text : { *(.text.boot) *(.text*) }\n .rodata : { *(.rodata*) }\n'
        ' .data : { *(.data*) }\n . = ALIGN(4096);\n'
        ' .bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; }\n'
        ' . += 0x40000; _stack_top = .;\n}\n')
    elf=out/'model.arm64.elf'
    run(['clang','-target','aarch64-none-elf','-std=c11','-O2','-ffreestanding','-fno-builtin',
         '-mgeneral-regs-only','-mstrict-align','-Wall','-Wextra','-Werror','-DMT6897_MODEL_FREESTANDING',
         '-nostdlib','-fuse-ld=lld','-Wl,-T,'+str(linker),str(start),str(runtime),
         str(paths[0]),str(paths[2]),str(paths[4]),'-o',str(elf)])
    arm=run(['qemu-system-aarch64','-M','virt','-cpu','cortex-a76','-smp','1','-m','64M',
             '-nographic','-monitor','none','-serial','stdio','-nic','none',
             '-semihosting-config','enable=on,target=native','-kernel',str(elf)],
            capture_output=True,text=True,timeout=30)
    (out/'arm64-model.log').write_text(arm.stdout+arm.stderr)
    if result.stdout not in arm.stdout or 'MT6897 ARM64 MODEL PASS' not in arm.stdout:
        raise RuntimeError('ARM64 model did not reproduce the native checks')
    report['arm64_model']={'passed':True,'elf_sha256':sha(elf),'same_checks_as_native':True,
                          'scope':'actual ARM64 CPU execution of register/DMA models; strict alignment, MMU/cache off, no MediaTek peripheral emulation'}
    paths += [runtime,start]
    report['source_sha256']={str(p.relative_to(repo)):sha(p) for p in paths+[manifest_path,Path(__file__).resolve()]}
    if args.fdt:
        report['source_sha256']['tools/inspect-duchamp-hardware.py']=sha(repo/'tools/inspect-duchamp-hardware.py')
    report['passed']=True
    (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
