#!/usr/bin/env python3
"""Audit captured boot/module evidence offline. Never contacts a phone."""
import argparse,importlib.util,json,sys
from pathlib import Path
import duchamp_saved_ufs as saved

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path);ap.add_argument('--boot',type=Path,required=True)
    ap.add_argument('--vendor-boot',type=Path,required=True);ap.add_argument('--fdt',type=Path,required=True)
    ap.add_argument('--sources',type=Path,required=True);ap.add_argument('--firmware-dir',type=Path,required=True)
    a=ap.parse_args();out=a.output.resolve()
    if out.exists():ap.error('preserve existing output')
    repo=Path(__file__).resolve().parent.parent
    receipt=saved.sources(repo,a.sources)
    image,config=saved.boot_contents(a.boot);load={}
    modules=saved.selected_cpio(saved.vendor_contents(a.vendor_boot),load)
    raw=saved.pinned(a.fdt,saved.FDT_SHA)
    spec=importlib.util.spec_from_file_location('saved_fdt',repo/'tools/inspect-duchamp-hardware.py')
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    tree=mod.Fdt(raw);ufs=tree.nodes['/soc/ufshci@112b0000'];node=ufs;ancestry=[]
    while node:
        ancestry.append({'path':node.path,'iommus':node.cells('iommus'),'iommu_map':node.cells('iommu-map')})
        node=node.parent
    if any(e['iommus'] or e['iommu_map'] for e in ancestry) or ufs.parent.cells('dma-ranges')!=[0,0,0,0,16,0]:
        raise ValueError('saved DMA tree changed')
    fw=[]
    for name,expected in [('lk_a.bin','f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a'),
                          ('preloader_raw_a.bin','6e9b62813d4466b8143f6ddd2064e3c9cc177ab8a897aa0a586d636c3c526c99')]:
        data=saved.pinned(a.firmware_dir/name,expected)
        fw.append({'name':name,'sha256':saved.sha(data),'bytes':len(data),
                   'bl31_loader_markers':{s.decode():s in data for s in (b'BL31-reserved',b'[BL31] load failed')}})
    settings={}
    for line in config.decode().splitlines():
        if line.startswith('CONFIG_'):
            key,_,value=line.partition('=');settings[key]=value
        elif line.startswith('# CONFIG_') and line.endswith(' is not set'):settings[line[2:-11]]='n'
    keys=['CONFIG_IOMMU_DMA','CONFIG_IOMMU_DEFAULT_DMA_STRICT','CONFIG_IOMMU_DEFAULT_PASSTHROUGH',
          'CONFIG_SWIOTLB','CONFIG_XEN','CONFIG_ARM_SMMU','CONFIG_ARM_SMMU_V3','CONFIG_ARCH_DMA_ADDR_T_64BIT',
          'CONFIG_ZONE_DMA32','CONFIG_ARM64_4K_PAGES','CONFIG_ARM64_PA_BITS','CONFIG_DMA_OPS_BYPASS']
    selected={k:settings.get(k,'not_in_config') for k in keys}
    if selected['CONFIG_IOMMU_DMA']!='y' or selected['CONFIG_SWIOTLB']!='y' or selected['CONFIG_XEN']!='n':
        raise ValueError('captured kernel configuration differs')
    elf=saved.Elf(modules['ufs-mediatek-mod.ko']);fragments,proof=elf.fragments()
    out.mkdir(parents=True)
    (out/'kernel.config').write_bytes(config)
    for name,data in modules.items():(out/name).write_bytes(data)
    for name,data in fragments.items():(out/(name+'.bin')).write_bytes(data)
    result={'audit_complete':True,'kernel_release':saved.RELEASE,'kernel_stamp_commit':saved.GKI,
        'kernel_image_sha256':saved.sha(image),'config_sha256':saved.sha(config),'kernel_config':selected,
        'input_sha256':{'boot':saved.BOOT_SHA,'vendor_boot':saved.VENDOR_SHA,'fdt':saved.FDT_SHA},
        'modules':{n:{'sha256':saved.sha(b),'bytes':len(b),'modinfo':saved.Elf(b).modinfo()} for n,b in modules.items()},
        'module_load_recipe':load,
        'source_receipts':receipt,'saved_client_fragments':proof,'firmware_artifacts':fw,
        'ufs_ancestry':ancestry,'dma_window_bytes':1<<36,
        'compiled_ufs_mask_policy':'try streaming64 if effective CAP64; otherwise or streaming failure try32; coherent setter return ignored',
        'candidate':'direct DMA possibly using SWIOTLB, only if no existing/overridden DMA ops or IOMMU fwspec',
        'source_binary_equivalence_verified':False,'physical_dma_route_verified':False,
        'installed_firmware_contract_verified':False,'physical_backend_enabled':False,
        'missing':['runtime HCCAP and effective streaming/coherent masks','runtime dma_ops, fwspec, domain and SWIOTLB state',
                   'exact vendor module build correspondence (vermagic says maybe-dirty)',
                   'matched BL31 implementation/build config and UFS effect/return semantics','secure resource/PHY ownership'],
        'scope':'saved files + pinned source + static client analysis only; no device/module loading/firmware execution'}
    # Recheck saved sources at the end; never modify them.
    saved.pinned(a.boot,saved.BOOT_SHA);saved.pinned(a.vendor_boot,saved.VENDOR_SHA);saved.pinned(a.fdt,saved.FDT_SHA)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
