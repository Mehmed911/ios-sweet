#!/usr/bin/env python3
"""Audit pinned saved UFS client allocations/MCQ query; no device or code loading."""
import argparse,hashlib,importlib.util,json,struct
from pathlib import Path
import duchamp_saved_ufs as saved
spec=importlib.util.spec_from_file_location('fw_reference',Path(__file__).with_name('fetch-duchamp-firmware-reference.py'))
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
def inspect_client(elf):
    text=elf.section_data(elf.sections['.text'])
    query_words={0x1e54:0x52804ec0,0x1e74:0x72b84000,0x1e78:0x52808001,
                 0x1e84:0xf94027e8,0x1e8c:0xb5000068,0x1e90:0x32180042}
    for off,word in query_words.items():
        if saved.unpack(text,off,'<I')[0]!=word:raise ValueError('saved MCQ request/result instruction differs')
    elf.call(0x1e80,'__arm_smccc_smc')
    query=saved.span(text,0x1e54,0x44)
    if saved.sha(query)!='9fa2c04bc9124348dde1bb17b7bba48d317af41c42b7f04ced457a852b10644d':
        raise ValueError('saved MCQ fragment differs')
    alloc=[s for s in elf.symbols if s[0]=='ufshcd_memory_alloc']
    if len(alloc)!=1 or alloc[0][1:]!=(elf.sections['.text'],0x13198,0x154):raise ValueError('saved allocation function differs')
    for call,attrs in [(0x131d4,0x131cc),(0x13208,0x13200),(0x13248,0x1323c)]:
        elf.call(call,'dmam_alloc_attrs')
        if saved.unpack(text,attrs,'<I')[0]!=0xaa1f03e4:raise ValueError('allocation attrs no longer zero')
    for off,word in [(0x131e4,0x7200191f),(0x13218,0x7200251f),(0x13258,0x7200251f)]:
        if saved.unpack(text,off,'<I')[0]!=word:raise ValueError('allocation alignment check differs')
    return {'module_sha256':saved.UFS_SHA,'mcq_query':{'function_id':'0xc2000276','selector':1024,
        'argument_registers_2_through_7':0,'call_text_offset':'0x1e80','result_load':'a1 via stack result+8',
        'zero_a1_sets_disable_mcq_bit':'0x100','a0_checked_in_selected_result_block':False,
        'fragment_sha256':saved.sha(query)},
        'control_allocations':{'function_text_offset':'0x13198','function_bytes':0x154,
        'function_sha256':saved.sha(saved.span(text,0x13198,0x154)),
        'dmam_alloc_attrs_calls':['0x131d4','0x13208','0x13248'],'attrs':0,
        'alignment_bytes':[128,1024,1024]},'offsets_are_runtime_addresses':False}
def audit(module,source_dir,reference_dir,repo):
    receipts=saved.sources(repo,source_dir)
    data=saved.pinned(module,saved.UFS_SHA);client=inspect_client(saved.Elf(data))
    ref=reference.check((reference_dir/'ufs_ctrl.c').read_bytes())
    return {'audit_complete':True,'saved_client':client,'source_receipts':receipts,'comparison_reference':ref,
        'comparison_mcq_selector_supported':False,'comparison_mtcmos_zero_without_compiled_hook':True,
        'streaming_mask_proves_coherent_mask':False,'captured_window_proves_active_dma_route':False,
        'installed_firmware_contract_verified':False,'physical_dma_route_verified':False,'physical_backend_enabled':False,
        'missing':['matched installed monitor and build flags; per-service effect/return contract',
                   'exclusive physical resources and PHY state','runtime DMA ops/fwspec/domain and both effective masks',
                   'runtime controller HCCAP and cache ownership'],
        'scope':'pinned static module/source comparison only; no MMIO, SMC, DMA, module/image execution or phone access'}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path)
    ap.add_argument('--saved-audit',type=Path,required=True);ap.add_argument('--sources',type=Path,required=True)
    ap.add_argument('--reference',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():ap.error('preserve existing output')
    repo=Path(__file__).resolve().parent.parent
    result=audit(a.saved_audit/'ufs-mediatek-mod.ko',a.sources,a.reference,repo)
    prior=json.loads((a.saved_audit/'result.json').read_text())
    if not prior['audit_complete'] or prior['source_receipts']!=result['source_receipts']:raise ValueError('saved source audit differs')
    a.output.mkdir(parents=True,exist_ok=False);(a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
