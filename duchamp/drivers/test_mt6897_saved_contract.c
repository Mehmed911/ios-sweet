/* QEMU/source fixture only. No physical MT6897 provider or real BL31. */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "mt6897_backends.h"
#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *,unsigned) __attribute__((noreturn));
int printf(const char *,...);
void *memset(void *,int,size_t);
void *memcpy(void *,const void *,size_t);
#define assert(v) ((v)?(void)0:model_assert_fail(#v,__LINE__))
#else
#include <assert.h>
#include <stdio.h>
#include <string.h>
#endif
static unsigned checks;
#define CHECK(x) do{checks++;assert(x);}while(0)
typedef uint64_t u64;
typedef uint64_t phys_addr_t;
typedef uint64_t dma_addr_t;
struct bus_dma_region {phys_addr_t cpu_start;dma_addr_t dma_start;u64 size,offset;};
struct dma_map_ops {unsigned fixture;};
struct iommu_ops {unsigned fixture;};
struct device {
    const struct bus_dma_region *dma_range_map;
    u64 *dma_mask,bus_dma_limit,coherent_dma_mask;
    const struct dma_map_ops *dma_ops;
    bool dma_coherent,force_bounce,bounce_active;
    unsigned fail_slots,support_calls,bounces,syncs,setup_calls,hooks;
    u64 mask_log[8];
};
struct ufs_hba {unsigned capabilities;struct device *dev;};
struct page {u64 physical;bool p2p;};
enum dma_data_direction {DMA_BIDIRECTIONAL=0,DMA_TO_DEVICE=1,DMA_FROM_DEVICE=2};
#define EIO 5
#define DMA_MAPPING_ERROR UINT64_MAX
#define DMA_BIT_MASK(n) (UINT64_MAX>>(64-(n)))
#define MASK_64_ADDRESSING_SUPPORT 0x01000000u
#define DMA_ATTR_SKIP_CPU_SYNC (1UL<<5)
#define CONFIG_ARCH_DMA_ADDR_T_64BIT 1
#define IS_ENABLED(n) (n)
#define likely(x) (x)
#define unlikely(x) (x)
#define __sme_set(x) (x)
#define __sme_clr(x) (x)
#define min(a,b) ((a)<(b)?(a):(b))
#define min_not_zero(a,b) (!(a)?(b):!(b)?(a):min(a,b))
#define PFN_PHYS(x) ((uint64_t)(x)<<12)
#define dev_WARN_ONCE(...) ((void)0)
#define ARCH_DMA_MINALIGN 128
#define panic(...) CHECK(false)
#define arch_dma_set_mask(d,m) ((void)0)
#define xen_setup_dma_ops(d) ((void)(d)) /* captured CONFIG_XEN=n */
static const struct dma_map_ops fixture_ops={1};
static const struct iommu_ops fixture_iommu={1};
static unsigned min_low_pfn;
static int cache_line_size_of_cpu(void){return 64;}
static void iommu_setup_dma_ops(struct device *d,u64 base,u64 end){
    CHECK(base==0 && end==(1ull<<36)-1);d->setup_calls++;d->dma_ops=&fixture_ops;
}
static void trace_android_rvh_iommu_setup_dma_ops(struct device *d,u64 base,u64 end){
    CHECK(base==0 && end==(1ull<<36)-1);d->hooks++;
}
static bool dma_supported(struct device *d,u64 mask){
    CHECK(d->support_calls<8);d->mask_log[d->support_calls]=mask;
    return !(d->fail_slots&(1u<<d->support_calls++));
}
static u64 page_to_phys(struct page *p){return p->physical;}
static bool is_swiotlb_force_bounce(struct device *d){return d->force_bounce;}
static bool is_swiotlb_active(struct device *d){return d->bounce_active;}
static bool is_pci_p2pdma_page(struct page *p){return p->p2p;}
static bool dev_is_dma_coherent(struct device *d){return d->dma_coherent;}
static struct device *sync_device;
static void arch_sync_dma_for_device(phys_addr_t p,size_t n,enum dma_data_direction dir){
    CHECK(p && n==4096 && dir==DMA_FROM_DEVICE);sync_device->syncs++;
}
static dma_addr_t swiotlb_map(struct device *d,phys_addr_t p,size_t n,
                              enum dma_data_direction dir,unsigned long attrs){
    (void)attrs;CHECK(p && n==4096 && dir==DMA_FROM_DEVICE);d->bounces++;return 0x10000000;
}
/* Unchanged function bodies extracted from exact, verified source Git blobs. */
#include "saved-reference.inc"

static struct bus_dma_region identity[]={{0,0,1ull<<36,0},{0,0,0,0}};
static void init_device(struct device *d,u64 *mask){
    memset(d,0,sizeof(*d));*mask=UINT64_MAX;d->dma_mask=mask;
    d->coherent_dma_mask=1;d->bus_dma_limit=(1ull<<36)-1;d->dma_range_map=identity;
}
static void source_tests(void){
    for(unsigned cap=0;cap<2;cap++)for(unsigned failures=0;failures<16;failures++){
        struct device d;u64 mask;init_device(&d,&mask);d.fail_slots=failures;
        struct ufs_hba h={cap?MASK_64_ADDRESSING_SUPPORT:0,&d};
        int r=ufshcd_set_dma_mask(&h);
        bool first_failed=failures&1,second_failed=failures&2;
        CHECK(r==((!cap&&first_failed)||(cap&&first_failed&&second_failed)?-EIO:0));
        CHECK(d.mask_log[0]==(cap?UINT64_MAX:0xffffffffull));
        if(cap&&first_failed)CHECK(d.mask_log[1]==0xffffffffull);
        if(!r)CHECK(mask==(cap&&!first_failed?UINT64_MAX:0xffffffffull));
        /* A coherent-mask setter error is ignored by this source helper. */
        if(!(failures&1) && (failures&2))CHECK(r==0 && d.coherent_dma_mask==1);
    }
    struct device d;u64 mask;init_device(&d,&mask);sync_device=&d;
    for(u64 p=0;p<(1ull<<36);p+=(1ull<<32)+4096){
        CHECK(phys_to_dma(&d,p)==p && dma_to_phys(&d,p)==p);
        CHECK(dma_capable(&d,p,4096,true));
    }
    CHECK(phys_to_dma(&d,1ull<<36)==DMA_MAPPING_ERROR);
    CHECK(!dma_capable(&d,DMA_MAPPING_ERROR,4096,true));
    CHECK(dma_capable(&d,(1ull<<36)-4096,4096,true));
    CHECK(!dma_capable(&d,(1ull<<36)-4096,8192,true));
    struct bus_dma_region shifted[]={{0x100000000ull,0x20000000,0x100000,0xe0000000ull},{0,0,0,0}};
    d.dma_range_map=shifted;
    CHECK(phys_to_dma(&d,0x100000123ull)==0x20000123 && dma_to_phys(&d,0x20000123)==0x100000123ull);
    CHECK(dma_to_phys(&d,0x10000000)==UINT64_MAX);
    d.dma_range_map=NULL;CHECK(phys_to_dma(&d,0x100002000ull)==0x100002000ull);
    d.dma_range_map=identity;
    struct page page={0x1c2830000ull,false};
    CHECK(dma_direct_map_page(&d,&page,0,4096,DMA_FROM_DEVICE,0)==page.physical);
    CHECK(d.syncs==1 && !d.bounces);
    *d.dma_mask=0xffffffffull;
    CHECK(dma_direct_map_page(&d,&page,0,4096,DMA_FROM_DEVICE,0)==DMA_MAPPING_ERROR);
    d.bounce_active=true;
    CHECK(dma_direct_map_page(&d,&page,0,4096,DMA_FROM_DEVICE,0)==0x10000000 && d.bounces==1);
    page.p2p=true;
    CHECK(dma_direct_map_page(&d,&page,0,4096,DMA_FROM_DEVICE,0)==DMA_MAPPING_ERROR);
    page.p2p=false;*d.dma_mask=UINT64_MAX;d.force_bounce=true;
    CHECK(dma_direct_map_page(&d,&page,0,4096,DMA_FROM_DEVICE,0)==0x10000000 && d.bounces==2);
    d.force_bounce=false;d.dma_coherent=true;
    CHECK(dma_direct_map_page(&d,&page,0,4096,DMA_FROM_DEVICE,0)==page.physical && d.syncs==1);
    d.dma_coherent=false;
    CHECK(dma_direct_map_page(&d,&page,0,4096,DMA_FROM_DEVICE,DMA_ATTR_SKIP_CPU_SYNC)==page.physical && d.syncs==1);
    arch_setup_dma_ops(&d,0,1ull<<36,NULL,false);
    CHECK(!d.dma_ops && !d.setup_calls && dma_map_direct(&d,NULL) && dma_alloc_direct(&d,NULL));
    arch_setup_dma_ops(&d,0,1ull<<36,&fixture_iommu,false);
    CHECK(d.dma_ops==&fixture_ops && d.setup_calls==1 && d.hooks==1);
    CHECK(!dma_map_direct(&d,d.dma_ops));
    arch_setup_dma_ops(&d,0,1ull<<36,NULL,false);
    CHECK(d.dma_ops==&fixture_ops); /* NULL IOMMU does not clear inherited DMA ops. */
}

#ifdef MT6897_MODEL_FREESTANDING
int fixture_dma_set_mask(struct device *d,u64 mask){return dma_set_mask(d,mask);}
int fixture_dma_set_coherent_mask(struct device *d,u64 mask){return dma_set_coherent_mask(d,mask);}
extern int saved_dma_mask(struct device *,unsigned);
extern void saved_mtcmos0(u64 *,unsigned),saved_mtcmos1(u64 *,unsigned);
extern void saved_refpre(u64 *,unsigned),saved_refpost(u64 *,unsigned);
_Alignas(16) volatile uint64_t test_smc_seen[8];
volatile uint32_t test_smc_count;
static void binary_dma_tests(void){
    for(unsigned cap=0;cap<2;cap++)for(unsigned fail=0;fail<16;fail++){
        struct device d,a;u64 m,n;init_device(&d,&m);init_device(&a,&n);d.fail_slots=a.fail_slots=fail;
        struct ufs_hba h={cap?MASK_64_ADDRESSING_SUPPORT:0,&a};
        int expected=ufshcd_set_dma_mask(&h);int actual=saved_dma_mask(&d,cap);
        CHECK(expected==actual && m==n && d.coherent_dma_mask==a.coherent_dma_mask);
        CHECK(d.support_calls==a.support_calls);
        for(unsigned j=0;j<d.support_calls;j++)CHECK(d.mask_log[j]==a.mask_log[j]);
    }
}
struct vector {void (*call)(u64 *,unsigned);u64 selector;unsigned on,stage;};
static const struct vector vectors[]={
    {saved_mtcmos0,512,0,0},{saved_mtcmos1,512,1,0},
    {saved_refpre,8,0,0},{saved_refpre,8,1,0},
    {saved_refpost,8,0,1},{saved_refpost,8,1,1}};
static int permit(void *c,const u64 q[8]){(void)c;(void)q;return 1;}
static int saved_conduit(void *c,const u64 q[8],u64 r[4]){
    const struct vector *v=c;CHECK(q[1]==v->selector && q[2]==v->on && q[3]==v->stage);
    v->call(r,v->on);return 0;
}
static int unverified(void *c,const u64 q[8],const u64 r[4]){(void)c;(void)q;(void)r;return 0;}
static void binary_smc_tests(void){
    for(unsigned i=0;i<6;i++){
        const struct vector *v=&vectors[i];struct {u64 a,r[4],b;} out={9,{0,0,0,0},10};
        v->call(out.r,v->on);
        u64 q[8]={0xc2000276u,v->selector,v->on,v->stage,0,0,0,0};
        for(unsigned j=0;j<8;j++)CHECK(test_smc_seen[j]==q[j]);
        CHECK(test_smc_count==i+1 && out.a==9 && out.b==10);
        CHECK(out.r[0]==0 && out.r[1]==0 && out.r[2]==v->on+13 && out.r[3]==0x1122334455667788ull);
    }
    for(unsigned i=0;i<6;i++){
        const struct vector *v=&vectors[i];struct mb_firmware f={0};
        struct mb_fw_ops o={(void *)v,permit,saved_conduit,unverified};u64 out[4]={9,8,7,6};
        u64 q[8]={0xc2000276u,v->selector,v->on,v->stage,0,0,0,0};
        CHECK(mb_firmware_bind(&f,&o)==0);
        CHECK(mb_firmware_ufs(&f,q,out)==MB_UNVERIFIED && f.state==2 && f.last_reply[0]==0);
        CHECK(out[0]==9 && out[1]==8 && out[2]==7 && out[3]==6);
        CHECK(test_smc_count==i+7);
        CHECK(mb_firmware_ufs(&f,q,out)==MB_STATE && test_smc_count==i+7);
    }
}
#endif
int main(void){
    source_tests();printf("%u source DMA contract checks passed\n",checks);
#ifdef MT6897_MODEL_FREESTANDING
    unsigned before=checks;binary_dma_tests();printf("%u saved DMA instruction checks passed\n",checks-before);
    before=checks;binary_smc_tests();printf("%u saved SMC instruction checks passed; 12 test-monitor calls\n",checks-before);
#endif
    return 0;
}
