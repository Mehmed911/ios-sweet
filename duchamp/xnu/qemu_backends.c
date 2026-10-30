/* Opt-in in-kernel selftest: all peripheral callbacks below use private RAM.
 * The only real platform operations are XNU allocation/cache/clock/locking
 * and the read-only diagnostic devfs device. No physical MMIO or SMC call.
 */
#if defined(ARM64_BOARD_CONFIG_SWEET)
#include <sys/param.h>
#include <sys/systm.h>
#include <sys/conf.h>
#include <sys/errno.h>
#include <sys/proc.h>
#include <sys/uio.h>
#include <miscfs/devfs/devfs.h>
#include <kern/locks.h>
#include <kern/clock.h>
#include <arm/caches_internal.h>
#include <vm/pmap.h>
#include <vm/vm_kern.h>
#include <pexpert/pexpert.h>
#include <pexpert/device_tree.h>
#include <arm64/sweet_early.h>
#include "mt6897_backends.h"
#include "mt6897_ufs_dma.h"
#include "mt6897_ufs_platform.h"
#include "mt6897_ufs_clocks.h"
#include "mt6897_v7s.h"

extern ppnum_t pmap_find_phys(pmap_t,addr64_t);
int duchamp_qemu_backends_prepare(void);
static LCK_GRP_DECLARE(qbt_group,"duchamp_qemu_backends");
static LCK_MTX_DECLARE(qbt_lock,&qbt_group);
static const char receipt[]="DUCHAMP XNU BACKENDS PASS tables=1 mmu=1 pmic=1 fw_verified=0 physical=0\n";
static int ready,attempted;
struct peripheral_model {
    unsigned role,state,locked,fw_calls,confirmed,accesses;
    uint32_t write_data,read_data,ttbr,done;
    uint8_t reg[2][0x2000];
};
static struct peripheral_model peripheral,mmu;
static struct mv7_table tables;
static vm_offset_t root_va,pool_va,data_va;
static uint64_t root_pa,pool_pa,data_pa;

static int contiguous(vm_offset_t *va,uint64_t *pa,vm_size_t bytes,vm_size_t mask) {
    /* mask aligns the VA; pnum_mask separately aligns physical page numbers. */
    if(kmem_alloc_contig(kernel_map,va,bytes,mask,atop_64((1ull<<35)-1),atop_64(mask),
                        KMA_DATA|KMA_ZERO|KMA_PERMANENT,
                        VM_KERN_MEMORY_IOKIT)!=KERN_SUCCESS) return ENOMEM;
    *pa=ptoa_64(pmap_find_phys(kernel_pmap,(addr64_t)*va));
    if(!*pa || (*pa&mask) || *pa>=(1ull<<35) || bytes>(1ull<<35)-*pa) return EIO;
    for(vm_size_t off=0;off<bytes;off+=PAGE_SIZE)
        if(ptoa_64(pmap_find_phys(kernel_pmap,(addr64_t)*va+off))!=*pa+off) return EIO;
    return 0;
}
static int sync_table(void *ctx,uint64_t pa,size_t n) {
    (void)ctx;
    if(!((pa==root_pa && n==MV7_L1_BYTES) || (pa==pool_pa && n<=PAGE_SIZE))) return -1;
    clean_dcache64(pa,(unsigned)n,TRUE); return 0;
}
static void ordered(void *ctx) { (void)ctx;__asm__ volatile("dsb sy; isb" ::: "memory"); }
static uint64_t micros(void *ctx) {
    (void)ctx;uint64_t ns;absolutetime_to_nanoseconds(mach_absolute_time(),&ns);return ns/1000;
}
static int pause_us(void *ctx,uint32_t us) { (void)ctx;if(us>10000)return -1;delay(us);return 0; }
static int auth(void *ctx,unsigned resource) {
    struct peripheral_model *m=ctx;
    return resource==(m->role?MB_DISP_IOMMU:MB_PMIF);
}
static int read_model(void *ctx,unsigned bank,uint32_t off,uint32_t *v) {
    struct peripheral_model *m=ctx;m->accesses++;
    if(bank)return -1;
    if(m->role) {
        if(off==0)*v=m->ttbr;
        else if(off==0x110)*v=8;
        else if(off==0x12c)*v=m->done;
        else return -1;
    } else {
        if(off==0)*v=1;
        else if(off==0x8a8)*v=m->state<<1;
        else if(off==0x894)*v=m->read_data;
        else return -1;
    }
    return 0;
}
static int write_model(void *ctx,unsigned bank,uint32_t off,uint32_t v) {
    struct peripheral_model *m=ctx;m->accesses++;
    if(bank)return -1;
    if(m->role) {
        if(off==0)m->ttbr=v;
        else if(off==0x20){if(v!=1 && v!=2)return -1;m->done=1;}
        else if(off==0x12c){if(v)return -1;m->done=0;}
        else if(off!=0x2c && off!=0x24 && off!=0x28)return -1;
        return 0;
    }
    if(off==0x884)m->write_data=v;
    else if(off==0x8a4){if(v!=1)return -1;m->state=0;}
    else if(off==0x880) {
        unsigned sid=(v>>24)&15,n=((v>>16)&3)+1,a=v&65535,w=(v>>29)&1;
        if(v>>30!=3 || (sid!=4 && sid!=8) || a+n>0x2000 || m->state)return -1;
        unsigned i=sid==4?0:1;
        if(w) {
            for(unsigned j=0;j<n;j++) {
                uint8_t b=(uint8_t)(m->write_data>>(j*8));
                if(!i && a+j==0x1b40 && (m->reg[0][0x39e]!=0x9c || m->reg[0][0x39f]!=0x9c))return -1;
                if(i && a+j==0x1441)m->reg[1][0x1440]|=b;
                else m->reg[i][a+j]=b;
            }
        } else {
            m->read_data=0;
            for(unsigned j=0;j<n;j++)m->read_data|=(uint32_t)m->reg[i][a+j]<<(j*8);
            m->state=6;
        }
    } else return -1;
    return 0;
}
struct pmic_link {struct mb_pmif bus;struct peripheral_model *model;};
static int rail_auth(void *ctx,unsigned rail,int w){(void)ctx;return rail<=1 && w==1;}
static int rail_lock(void *ctx){struct pmic_link *l=ctx;lck_mtx_lock(&qbt_lock);l->model->locked=1;return 0;}
static void rail_unlock(void *ctx){struct pmic_link *l=ctx;l->model->locked=0;lck_mtx_unlock(&qbt_lock);}
static int rail_read(void *ctx,unsigned sid,uint16_t a,void *data,size_t n){
    struct pmic_link *l=ctx;if(!l->model->locked)return -1;return mb_pmif_transfer(&l->bus,sid,a,data,n,0);
}
static int rail_write(void *ctx,unsigned sid,uint16_t a,const void *data,size_t n){
    struct pmic_link *l=ctx;if(!l->model->locked)return -1;return mb_pmif_transfer(&l->bus,sid,a,(void *)data,n,1);
}
static int fw_auth(void *ctx,const uint64_t q[8]){(void)ctx;(void)q;return 1;}
static int fw_call(void *ctx,const uint64_t q[8],uint64_t r[4]){
    (void)q;struct peripheral_model *m=ctx;m->fw_calls++;r[0]=0;return 0;
}
static int fw_check(void *ctx,const uint64_t q[8],const uint64_t r[4]){
    (void)q;(void)r;return ((struct peripheral_model *)ctx)->confirmed?1:0;
}
static int deny_power(void *ctx,uint32_t mask){(void)ctx;(void)mask;return 0;}
static int deny_clock(void *ctx,unsigned bank,unsigned id){(void)ctx;(void)bank;(void)id;return 0;}
static int unreachable_sip(void *ctx,const struct mp_sip_request *q){(void)q;((struct peripheral_model *)ctx)->accesses++;return -1;}
static int unreachable_read(void *ctx,uint32_t o,uint32_t *v){(void)o;(void)v;((struct peripheral_model *)ctx)->accesses++;return -1;}
static int unreachable_write(void *ctx,uint32_t o,uint32_t v){(void)o;(void)v;((struct peripheral_model *)ctx)->accesses++;return -1;}
static int unreachable_reset(void *ctx,unsigned id,int a){(void)id;(void)a;((struct peripheral_model *)ctx)->accesses++;return -1;}
static int deny_dma(void *ctx,const struct md_config *c){(void)ctx;(void)c;return 0;}
static int unreachable_idle(void *ctx){((struct peripheral_model *)ctx)->accesses++;return 0;}
static int unreachable_map(void *ctx,uint64_t p,uint64_t n,enum md_direction d,uint64_t *a,uint64_t *c){
    (void)p;(void)n;(void)d;(void)a;(void)c;((struct peripheral_model *)ctx)->accesses++;return -1;
}
static int unreachable_sync(void *ctx,void *p,uint64_t n,enum md_direction d){
    (void)p;(void)n;(void)d;((struct peripheral_model *)ctx)->accesses++;return -1;
}
static int unreachable_unmap(void *ctx,uint64_t c,uint64_t a,uint64_t n,enum md_direction d){
    (void)c;(void)a;(void)n;(void)d;((struct peripheral_model *)ctx)->accesses++;return -1;
}
static int profile(void) {
    uint64_t midr;__asm__ volatile("mrs %0,midr_el1":"=r"(midr));
    if((midr>>24)!=0x41 || ((midr>>4)&0xfff)!=0xd0b)return ENXIO;
    DTEntry n;const void *v;unsigned size;
    static const char f[]="duchamp-qemu-ufs-fixture-v1",c[]="qemu,ufs-test-only";
    if(SecureDTLookupEntry(NULL,"/chosen",&n)!=kSuccess ||
       SecureDTGetProperty(n,"firmware-version",&v,&size)!=kSuccess ||
       size!=sizeof(f) || memcmp(v,f,size))return ENXIO;
    if(SecureDTLookupEntry(NULL,"/duchamp-qemu-ufs",&n)!=kSuccess ||
       SecureDTGetProperty(n,"compatible",&v,&size)!=kSuccess ||
       size!=sizeof(c) || memcmp(v,c,size))return ENXIO;
    return 0;
}
static int diagnostic_open(__unused dev_t d,int f,__unused int t,__unused struct proc *p){
    return !ready?ENXIO:f&FWRITE?EROFS:0;
}
static int diagnostic_close(__unused dev_t d,__unused int f,__unused int t,__unused struct proc *p){return 0;}
static int diagnostic_read(__unused dev_t d,struct uio *uio,__unused int f){
    if(!ready)return ENXIO;
    off_t off=uio_offset(uio);
    if(off<0 || uio_resid(uio)<0)return EINVAL;
    if((uint64_t)off>=sizeof(receipt)-1)return 0;
    int n=(int)MIN((uint64_t)uio_resid(uio),sizeof(receipt)-1-(uint64_t)off);
    return uiomove((void *)(receipt+off),n,uio);
}
static const struct cdevsw diagnostic={
    .d_open=diagnostic_open,.d_close=diagnostic_close,.d_read=diagnostic_read,.d_write=eno_rdwrt,
    .d_ioctl=eno_ioctl,.d_stop=eno_stop,.d_reset=eno_reset,.d_ttys=NULL,.d_select=eno_select,
    .d_mmap=eno_mmap,.d_strategy=eno_strat,.d_reserved_1=eno_getc,.d_reserved_2=eno_putc,.d_type=D_TTY
};
int duchamp_qemu_backends_prepare(void) {
    uint32_t enabled=0;
    if(!PE_parse_boot_argn("sweet-qemu-backends",&enabled,sizeof(enabled)) || !enabled)return 0;
    if(enabled!=1 || profile())return ENXIO;
    if(ready)return 0;
    if(attempted)return EIO;
    attempted=1;
    sweet_early_mark(196,"QEMU XNU BACKENDS SELFTEST ENTERED");
    if(contiguous(&root_va,&root_pa,MV7_L1_BYTES,MV7_L1_BYTES-1) ||
       contiguous(&pool_va,&pool_pa,PAGE_SIZE,PAGE_MASK) ||
       contiguous(&data_va,&data_pa,PAGE_SIZE,PAGE_MASK))return ENOMEM;
    if(mv7_init(&tables,(void *)root_va,root_pa,(void *)pool_va,pool_pa,PAGE_SIZE/1024) ||
       mv7_map(&tables,0xfffff000ull,data_pa,8192,0))return EIO;
    uint64_t translated=0;
    if(mv7_translate(&tables,0x100000071ull,&translated) || translated!=data_pa+4096+113 ||
       mv7_map(&tables,0xfffff000ull,data_pa,4096,0)!=MV7_OVERLAP)return EIO;
    struct mv7_sync sync={NULL,sync_table,ordered};uint32_t ttbr=0;
    if(mv7_seal(&tables,&sync,&ttbr) || ttbr!=((uint32_t)root_pa|(uint32_t)(root_pa>>32)) ||
       mv7_map(&tables,0,0,4096,0)!=MV7_STATE)return EIO;
    sweet_early_mark(196,"QEMU XNU TABLES CACHE PASS");

    mmu.role=1;
    struct mb_io io={&mmu,auth,read_model,write_model,ordered,micros,pause_us};
    struct mb_iommu m={0},ufs={0};unsigned accesses=mmu.accesses;
    if(mb_iommu_bind(&ufs,&io,MB_CLIENT_UNVERIFIED_UFS,0,1ull<<34)!=MB_UNVERIFIED ||
       mmu.accesses!=accesses || mb_iommu_bind(&m,&io,MB_CLIENT_DISP,0,1ull<<34) ||
       mb_iommu_install(&m,ttbr,1) || mb_iommu_invalidate(&m,0xfffff000ull,8192))return EIO;
    sweet_early_mark(196,"QEMU XNU IOMMU MODEL PASS UFS REFUSED");

    struct pmic_link link={.model=&peripheral};struct mb_pmic pmic={0};
    io=(struct mb_io){&peripheral,auth,read_model,write_model,ordered,micros,pause_us};
    struct mb_pmic_ops ops={&link,rail_auth,rail_lock,rail_unlock,rail_read,rail_write,pause_us};
    peripheral.reg[0][0x36]=1;peripheral.reg[0][0x1b40]=0xa5;peripheral.reg[0][0x1c23]=0xa0;
    peripheral.reg[1][0x1440]=0x81;
    if(mb_pmif_bind(&link.bus,&io,0) || mb_pmic_bind(&pmic,&ops) ||
       mb_pmic_voltage(&pmic,MB_VEMC,3000000) || mb_pmic_enable(&pmic,MB_VEMC) ||
       mb_pmic_voltage(&pmic,MB_VBUCK3,300000) || mb_pmic_enable(&pmic,MB_VBUCK3) ||
       peripheral.reg[0][0x1b40]!=0xb5 || peripheral.reg[0][0x1c23]!=0xa1 ||
       peripheral.reg[1][0x144d]!=48 || peripheral.reg[1][0x1440]!=0x85 ||
       peripheral.reg[0][0x39e] || peripheral.reg[0][0x39f] || peripheral.locked)return EIO;
    sweet_early_mark(196,"QEMU XNU PMIF PMIC LOCKING PASS");

    struct mb_firmware fw={0};struct mb_fw_ops fo={&peripheral,fw_auth,fw_call,fw_check};
    uint64_t q[8]={0xc2000276u,512,0,0,0,0,0,0},reply[4]={7,8,9,10};
    if(mb_firmware_bind(&fw,&fo) || mb_firmware_ufs(&fw,q,reply)!=MB_UNVERIFIED ||
       peripheral.fw_calls!=1 || reply[0]!=7 || fw.state!=2)return EIO;
    sweet_early_mark(196,"QEMU XNU FIRMWARE CONTRACT UNVERIFIED REFUSED");
    accesses=peripheral.accesses;
    struct mp_power power={0};struct mp_profile pp={1,1,0,MP_REQUIRED};
    struct mp_ops pop={&peripheral,deny_power,unreachable_sip,unreachable_read,unreachable_write,
                      ordered,micros,pause_us,unreachable_reset};
    struct mufs_clocks clocks={0};
    struct mufs_clock_ops cop={&peripheral,deny_clock,read_model,write_model,ordered,micros};
    struct md_pool dma={0};
    struct md_config dc={(void *)data_va,data_pa,PAGE_SIZE,0,1ull<<35,64,PAGE_SIZE,35,MD_UNKNOWN,MD_BIDIRECTIONAL};
    struct md_ops dop={&peripheral,deny_dma,unreachable_idle,unreachable_map,unreachable_sync,
                      unreachable_sync,ordered,unreachable_unmap};
    if(mp_bind(&power,&pp,&pop) || mp_prepare(&power)!=MP_UNVERIFIED ||
       mufs_clocks_bind(&clocks,&cop,1000) || mufs_clock_set(&clocks,0,0,1)!=MUFS_UNVERIFIED ||
       md_bind(&dma,&dc,&dop)!=MD_UNVERIFIED || peripheral.accesses!=accesses)return EIO;
    sweet_early_mark(196,"QEMU XNU PHYSICAL PROVIDERS DEFAULT CLOSED");
    int major=cdevsw_add(-1,&diagnostic);
    if(major<0 || !devfs_make_node(makedev(major,0),DEVFS_CHAR,UID_ROOT,GID_WHEEL,0440,"mbtest"))return ENXIO;
    ready=1;
    sweet_early_mark(196,"QEMU XNU BACKENDS SELFTEST PASS");
    return 0;
}
#endif
