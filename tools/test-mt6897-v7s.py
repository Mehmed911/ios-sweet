#!/usr/bin/env python3
"""Compare offline MTK V7S tables to encoding functions extracted from pinned source."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
SOURCE_BLOB='08ec39111e608f6405a5777889d6ac2eda561506'
def function(text,name):
    m=re.search(r'^static [^;{}]+\b'+name+r'\([^;]*?\)\s*\{',text,re.M|re.S)
    if not m: raise ValueError('missing upstream function '+name)
    start=m.start();i=m.end();depth=1
    while depth:
        if text[i]=='{':depth+=1
        if text[i]=='}':depth-=1
        i+=1
    return text[start:i]
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path)
    ap.add_argument('--reference',type=Path,required=True);args=ap.parse_args()
    raw=args.reference.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if blob!=SOURCE_BLOB:ap.error('reference differs from pinned Git blob')
    text=raw.decode();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent;src=repo/'duchamp/drivers'
    macros=text[text.index('#define ARM_V7S_ADDR_BITS'):text.index('#ifdef CONFIG_ZONE_DMA32')]
    names=['arm_v7s_is_mtk_enabled','to_mtk_iopte','paddr_to_iopte','iopte_to_paddr',
           'arm_v7s_prot_to_pte','arm_v7s_install_table']
    extracted='\n'.join(function(text,n) for n in names)
    shim='''#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
typedef uint32_t u32;typedef uint32_t arm_v7s_iopte;typedef uint64_t phys_addr_t;
#define BIT(n) (1u<<(n))
#define BIT_ULL(n) (1ull<<(n))
#define IS_ENABLED(n) 1
#define CONFIG_PHYS_ADDR_T_64BIT 1
#define IO_PGTABLE_QUIRK_ARM_NS 1u
#define IO_PGTABLE_QUIRK_NO_PERMS 2u
#define IO_PGTABLE_QUIRK_ARM_MTK_EXT 8u
#define IO_PGTABLE_QUIRK_ARM_MTK_TTBR_EXT 16u
#define IOMMU_MMIO 16u
#define IOMMU_PRIV 32u
#define IOMMU_WRITE 2u
#define IOMMU_NOEXEC 8u
#define IOMMU_CACHE 4u
struct io_pgtable_cfg {unsigned quirks,ias,oas;};
static bool arm_v7s_pte_is_cont(arm_v7s_iopte p,int lvl){(void)p;(void)lvl;return false;}
#define virt_to_phys(p) ((uint64_t)(uintptr_t)(p))
#define dma_wmb() ((void)0)
static uint32_t fixture_cmp(uint32_t *p,uint32_t old,uint32_t n){uint32_t v=*p;if(v==old)*p=n;return v;}
#define cmpxchg_relaxed(p,o,n) fixture_cmp(p,o,n)
#define __arm_v7s_pte_sync(p,n,c) ((void)0)
'''
    tail='''
static struct io_pgtable_cfg cfg={1|2|8|16,34,35};
uint32_t oracle_page(uint64_t pa,int cache){return paddr_to_iopte(pa,2,&cfg)|arm_v7s_prot_to_pte(cache?IOMMU_CACHE:0,2,&cfg);}
uint32_t oracle_link(uint64_t pa){uint32_t entry=0;arm_v7s_install_table((uint32_t *)(uintptr_t)pa,&entry,0,&cfg);return entry;}
uint64_t oracle_decode(uint32_t entry,int lvl){return iopte_to_paddr(entry,lvl,&cfg);}
uint32_t oracle_ttbr(uint64_t paddr){return (uint32_t)(paddr|(uint32_t)(paddr>>32));}
'''
    if 'cfg->arm_v7s_cfg.ttbr = paddr | upper_32_bits(paddr);' not in text:
        raise ValueError('upstream TTBR rule changed')
    oracle=out/'reference.c';oracle.write_text(shim+macros+extracted+tail)
    binary=out/'test'
    command=['clang','-std=gnu11','-O1','-g','-Wall','-Wextra','-Werror',
             '-Wno-unused-parameter','-fsanitize=address,undefined','-fno-omit-frame-pointer',
             str(src/'mt6897_v7s.c'),str(src/'test_mt6897_v7s.c'),str(oracle),'-o',str(binary)]
    subprocess.run(command,check=True)
    r=subprocess.run([str(binary)],check=True,capture_output=True,text=True)
    (out/'sanitizer.log').write_text(r.stdout+r.stderr)
    count=int(re.fullmatch(r'(\d+) ARM_V7S table checks passed against pinned Android reference encoders\n',r.stdout)[1])
    report={'passed':True,'checks':count,'reference_commit':'498f91c17b0822a09aede17d26a63bf8c6813725',
            'reference_blob':blob,'reference_sha256':hashlib.sha256(raw).hexdigest(),
            'extracted_functions':names,'oracle_stubs':'allocator/cache/atomic helper fixtures; encoders unchanged',
            'oracle_sha256':hashlib.sha256(oracle.read_bytes()).hexdigest(),
            'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [src/'mt6897_v7s.c',src/'mt6897_v7s.h',src/'test_mt6897_v7s.c',Path(__file__).resolve()]},
            'scope':'native ASan/UBSan software tables/oracle; no hardware walker, XNU or firmware execution'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
