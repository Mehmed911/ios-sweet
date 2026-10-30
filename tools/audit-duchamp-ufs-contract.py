#!/usr/bin/env python3
"""Offline source/DTB/firmware-artifact audit. Never contacts a device."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
FDT='9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29'
GKI='498f91c17b0822a09aede17d26a63bf8c6813725'
SOURCES={
    'of-device.c':('drivers/of/device.c','91d92bfe57359d9bfa7a361718ef571e04539d53'),
    'of_iommu.c':('drivers/iommu/of_iommu.c','3ad1461dc94fa0d47daafa619035d5fb7ee917a4'),
    'arm64-dma-mapping.c':('arch/arm64/mm/dma-mapping.c','f011f4c2c968e6ed87c2f75b55d6d50be24f4ace')}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path);ap.add_argument('--fdt',type=Path,required=True)
    ap.add_argument('--gki-sources',type=Path,required=True);ap.add_argument('--firmware-dir',type=Path)
    args=ap.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent
    if digest(args.fdt)!=FDT:ap.error('not the captured Duchamp DTB')
    spec=importlib.util.spec_from_file_location('route_fdt',repo/'tools/inspect-duchamp-hardware.py')
    hw=importlib.util.module_from_spec(spec);sys.modules[spec.name]=hw;spec.loader.exec_module(hw)
    tree=hw.Fdt(args.fdt.read_bytes());ufs=tree.nodes['/soc/ufshci@112b0000']
    soc=ufs.parent;root=soc.parent
    if soc.scalar('#address-cells')!=2 or soc.scalar('#size-cells')!=2 or root.scalar('#address-cells')!=2:
        raise ValueError('unsupported DMA address-cell shape')
    ranges=soc.cells('dma-ranges')
    if ranges!=[0,0,0,0,16,0]:raise ValueError('captured ancestor DMA window changed')
    parents=[];node=ufs
    while node:
        parents.append({'path':node.path,'iommus':node.cells('iommus'),'iommu_map':node.cells('iommu-map')})
        node=node.parent
    if any(n['iommus'] or n['iommu_map'] for n in parents):
        raise ValueError('new IOMMU routing evidence requires a fresh audit')
    receipts={}
    required={
      'of-device.c':['of_iommu_configure(dev, np, id)','arch_setup_dma_ops(dev, dma_start, size, iommu, coherent)'],
      'of_iommu.c':['dev_iommu_fwspec_get(dev)','of_iommu_configure_device(master_np, dev, id)'],
      'arm64-dma-mapping.c':['if (iommu)','iommu_setup_dma_ops(dev, dma_base, dma_base + size - 1)',
                             'trace_android_rvh_iommu_setup_dma_ops','xen_setup_dma_ops(dev)']}
    for name,anchors in required.items():
        p=args.gki_sources/name;data=p.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if blob!=SOURCES[name][1]:raise ValueError('source Git blob mismatch: '+name)
        text=data.decode('utf-8')
        if not all(x in text for x in anchors):raise ValueError('source anchor changed: '+name)
        receipts[name]=digest(p)
    firmware=[]
    if args.firmware_dir:
        for name,kind,expected in [
          ('lk_a.bin','LK bootloader','f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a'),
          ('preloader_raw_a.bin','preloader','6e9b62813d4466b8143f6ddd2064e3c9cc177ab8a897aa0a586d636c3c526c99')]:
            p=args.firmware_dir/name
            if not p.is_file():raise ValueError('expected saved artifact missing: '+name)
            actual=digest(p)
            if actual!=expected:raise ValueError('saved artifact provenance mismatch: '+name)
            firmware.append({'name':name,'role':kind,'bytes':p.stat().st_size,'sha256':actual,
                             'secure_monitor_contract_evidence':False})
    result={'audit_complete':True,'scope':'offline declared-source candidate only; no device, MMIO, DMA, image execution or firmware invocation',
      'fdt_sha256':FDT,'source_profile_commit':GKI,'source_sha256':receipts,
      'source_git_blobs':{n:{'path':p,'blob':b} for n,(p,b) in SOURCES.items()},
      'declared_dma_window':{'device_base':0,'cpu_base':0,'bytes':1<<36},
      'ufs_ancestry':parents,'source_candidate':'bus-window/direct DMA if no pre-existing fwspec or runtime override',
      'candidate_preconditions':['the supplied kernel source profile matches the installed GKI',
        'no pre-existing iommu_fwspec overrides the absent DT property',
        'no runtime vendor/hypervisor/Xen or secure-ownership override changes the DMA path',
        'effective controller address mask and noncoherent cache/ownership contract verified separately'],
      'physical_dma_route_verified':False,'display_mdp_iommu_for_ufs_authorised':False,
      'firmware_artifacts':firmware,'installed_firmware_contract_verified':False,
      'firmware_missing':['matched BL31/secure-monitor implementation and build configuration',
                          'per-UFS-service return and effect semantics','secure resource/PHY ownership attestation'],
      'physical_backend_enabled':False}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
