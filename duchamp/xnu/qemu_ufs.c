/* BSD read/completion adapter for the opt-in QEMU UFS fixture.
 * No MediaTek power sequence or physical phone backend is implemented here.
 */
#if defined(ARM64_BOARD_CONFIG_SWEET)
#include <sys/param.h>
#include <sys/systm.h>
#include <sys/buf.h>
#include <sys/conf.h>
#include <sys/disk.h>
#include <sys/errno.h>
#include <sys/proc.h>
#include <sys/uio.h>
#include <miscfs/devfs/devfs.h>
#include <kern/locks.h>
#include <kern/clock.h>
#include <machine/machine_routines.h>
#include <arm/caches_internal.h>
#include <vm/pmap.h>
#include <vm/vm_kern.h>
#include <pexpert/pexpert.h>
#include <pexpert/device_tree.h>
#include "ufs_readonly.h"

extern vm_offset_t ml_io_map(vm_offset_t, vm_size_t);
extern ppnum_t pmap_find_phys(pmap_t, addr64_t);
int duchamp_qemu_ufs_rootdev(dev_t *);

#define QU_DMA_BYTES 0x60000u
#define QU_BAR 0x10000000ull
#define QU_ECAM 0x3f000000ull
#define QU_PCI_ID 0x00131b36u
static struct {
    struct dufs_host host;
    vm_offset_t regs, dma;
    uint64_t dma_pa, bytes, requests;
    uint32_t physical_bytes, sector_bytes;
    dev_t device;
    int bmajor,cmajor,attempted,ready;
    uint8_t bounce[DUFS_MAX_TRANSFER];
} qu;
static LCK_GRP_DECLARE(qu_group,"duchamp_qemu_ufs");
static LCK_MTX_DECLARE(qu_lock,&qu_group);

static uint32_t qu_read32(void *ctx,uint32_t offset) {
    (void)ctx;
    return *(volatile uint32_t *)(qu.regs+offset);
}
static void qu_write32(void *ctx,uint32_t offset,uint32_t value) {
    (void)ctx;
    *(volatile uint32_t *)(qu.regs+offset)=value;
}
static int qu_dma_valid(uint64_t address,size_t bytes) {
    return address>=qu.dma_pa && address-qu.dma_pa<=QU_DMA_BYTES &&
        bytes<=QU_DMA_BYTES-(address-qu.dma_pa);
}
static int qu_dma_write(void *ctx,uint64_t address,const void *data,size_t bytes) {
    (void)ctx;
    if(!qu_dma_valid(address,bytes)) return -1;
    memcpy((void *)(qu.dma+(address-qu.dma_pa)),data,bytes);
    clean_dcache64((addr64_t)address,(unsigned)bytes,TRUE);
    return 0;
}
static int qu_dma_read(void *ctx,uint64_t address,void *data,size_t bytes) {
    (void)ctx;
    if(!qu_dma_valid(address,bytes)) return -1;
    flush_dcache64((addr64_t)address,(unsigned)bytes,TRUE);
    memcpy(data,(void *)(qu.dma+(address-qu.dma_pa)),bytes);
    return 0;
}
static void qu_barrier(void *ctx) {
    (void)ctx;
    __asm__ volatile("dsb sy; isb" ::: "memory");
}
static uint64_t qu_milliseconds(void *ctx) {
    (void)ctx;
    uint64_t ns;
    absolutetime_to_nanoseconds(mach_absolute_time(),&ns);
    return ns/1000000ull;
}
static int qu_error(int result) {
    return result==DUFS_TIMEOUT?ETIMEDOUT:result==DUFS_ARGUMENT?EINVAL:EIO;
}
static int qu_profile(void) {
    uint32_t enabled=0;
    if(!PE_parse_boot_argn("sweet-qemu-ufs",&enabled,sizeof(enabled)) || enabled!=1) return ENXIO;
    uint64_t midr;
    __asm__ volatile("mrs %0, midr_el1" : "=r"(midr));
    /* MT6897's cores are not Cortex-A76. Refuse before ANY PCI/MMIO mapping.
     * This is an accident-prevention gate, not hardware authentication.
     */
    if((midr>>24)!=0x41 || ((midr>>4)&0xfff)!=0xd0b) return ENXIO;
    DTEntry chosen,node;
    const void *value;
    unsigned size;
    static const char firmware[]="duchamp-qemu-ufs-fixture-v1";
    static const char compatible[]="qemu,ufs-test-only";
    if(SecureDTLookupEntry(NULL,"/chosen",&chosen)!=kSuccess ||
       SecureDTGetProperty(chosen,"firmware-version",&value,&size)!=kSuccess ||
       size!=sizeof(firmware) || memcmp(value,firmware,size)) return ENXIO;
    if(SecureDTLookupEntry(NULL,"/duchamp-qemu-ufs",&node)!=kSuccess ||
       SecureDTGetProperty(node,"compatible",&value,&size)!=kSuccess ||
       size!=sizeof(compatible) || memcmp(value,compatible,size)) return ENXIO;
    uint64_t reg[2],ecam[2];
    if(SecureDTGetProperty(node,"reg",&value,&size)!=kSuccess || size!=sizeof(reg)) return ENXIO;
    memcpy(reg,value,sizeof(reg));
    if(SecureDTGetProperty(node,"ecam",&value,&size)!=kSuccess || size!=sizeof(ecam)) return ENXIO;
    memcpy(ecam,value,sizeof(ecam));
    if(reg[0]!=QU_BAR || reg[1]!=0x1000 || ecam[0]!=QU_ECAM || ecam[1]!=0x1000000) return ENXIO;
    return 0;
}
static int qu_open(dev_t device,int flags,__unused int type,__unused struct proc *p) {
    if(!qu.ready || minor(device)!=0) return ENXIO;
    return flags&FWRITE?EROFS:0;
}
static int qu_close(__unused dev_t dev,__unused int flags,__unused int type,__unused struct proc *p) { return 0; }
static void qu_strategy(buf_t bp) {
    int error=0,mapped=0;
    caddr_t address=NULL;
    uint32_t count=buf_count(bp);
    buf_setresid(bp,count);
    if(!(buf_flags(bp)&B_READ)) { error=EROFS; goto done; }
    /* Only mapped kernel buffer-cache I/O belongs here. Raw user I/O uses
     * uiomove below; buf_map(B_PHYS) can return a user address under PAN.
     */
    if(buf_flags(bp)&B_PHYS) { error=EINVAL; goto done; }
    if(!qu.ready || minor(buf_device(bp))!=0) { error=ENXIO; goto done; }
    lck_mtx_lock(&qu_lock);
    int64_t block=buf_blkno(bp);
    if(block<0 || (uint64_t)block>UINT64_MAX/qu.sector_bytes) { error=EINVAL; goto unlock; }
    uint64_t offset=(uint64_t)block*qu.sector_bytes;
    if(offset>qu.bytes || count>qu.bytes-offset) { error=EINVAL; goto unlock; }
    if(!count) goto unlock;
    if(buf_map(bp,&address)) { error=EIO; goto unlock; }
    mapped=1;
    for(uint32_t done=0;done<count;) {
        uint64_t position=offset+done;
        uint32_t skip=(uint32_t)(position%qu.physical_bytes);
        uint32_t take=MIN(count-done,DUFS_MAX_TRANSFER-skip);
        uint32_t blocks=(skip+take+qu.physical_bytes-1)/qu.physical_bytes;
        int result=dufs_read(&qu.host,position/qu.physical_bytes,blocks,
                             qu.bounce,(size_t)blocks*qu.physical_bytes);
        if(result) { error=qu_error(result); break; }
        memcpy(address+done,qu.bounce+skip,take);
        done+=take; buf_setresid(bp,count-done);
        if(++qu.requests<=4) printf("DUCHAMP QUFS READ request=%llu bytes=%u\n",
                                    (unsigned long long)qu.requests,take);
    }
unlock:
    if(mapped) buf_unmap(bp);
    lck_mtx_unlock(&qu_lock);
done:
    if(error) buf_seterror(bp,error);
    buf_biodone(bp);
}
static int qu_ioctl(__unused dev_t dev,u_long command,caddr_t data,__unused int flags,
                    __unused struct proc *p) {
    if(!qu.ready) return ENXIO;
    int error=0;
    lck_mtx_lock(&qu_lock);
    switch(command) {
    case DKIOCGETBLOCKSIZE: *(uint32_t *)data=qu.sector_bytes; break;
    case DKIOCGETPHYSICALBLOCKSIZE: *(uint32_t *)data=qu.physical_bytes; break;
    case DKIOCGETBLOCKCOUNT: *(uint64_t *)data=qu.bytes/qu.sector_bytes; break;
    case DKIOCSETBLOCKSIZE: {
        uint32_t size=*(uint32_t *)data;
        if(size<DEV_BSIZE || size>qu.physical_bytes || (size&(size-1))) error=EINVAL;
        else qu.sector_bytes=size;
        break;
    }
    case DKIOCISWRITABLE: *(uint32_t *)data=0; break;
    case DKIOCSYNCHRONIZE:
    case DKIOCSYNCHRONIZECACHE: break;
    case DKIOCGETMAXBLOCKCOUNTREAD: *(uint64_t *)data=DUFS_MAX_TRANSFER/qu.sector_bytes; break;
    case DKIOCGETMAXBLOCKCOUNTWRITE: *(uint64_t *)data=0; break;
    case DKIOCGETMAXSEGMENTCOUNTREAD:
    case DKIOCGETMAXSEGMENTCOUNTWRITE: *(uint64_t *)data=1; break;
    default: error=ENOTTY;
    }
    lck_mtx_unlock(&qu_lock);
    return error;
}
static int qu_psize(__unused dev_t dev) {
    return qu.ready?(int)MIN(qu.bytes/qu.sector_bytes,INT_MAX):-1;
}
static int qu_read(dev_t dev,struct uio *uio,__unused int flags) {
    if(!qu.ready || minor(dev)!=0) return ENXIO;
    if(uio_offset(uio)<0 || uio_resid(uio)<0) return EINVAL;
    if(!uio_resid(uio)) return 0;
    vm_offset_t scratch=0;
    if(kmem_alloc(kernel_map,&scratch,PAGE_SIZE,KMA_DATA,VM_KERN_MEMORY_IOKIT)!=KERN_SUCCESS)
        return ENOMEM;
    int error=0;
    while(uio_resid(uio)>0) {
        uint64_t position=(uint64_t)uio_offset(uio);
        if(position>=qu.bytes) break;
        uint32_t skip=(uint32_t)(position%qu.physical_bytes);
        uint32_t take=(uint32_t)MIN((uint64_t)uio_resid(uio),(uint64_t)PAGE_SIZE-skip);
        take=(uint32_t)MIN((uint64_t)take,qu.bytes-position);
        uint32_t blocks=(skip+take+qu.physical_bytes-1)/qu.physical_bytes;
        lck_mtx_lock(&qu_lock);
        int result=dufs_read(&qu.host,position/qu.physical_bytes,blocks,
                             (void *)scratch,(size_t)blocks*qu.physical_bytes);
        lck_mtx_unlock(&qu_lock);
        if(result) { error=qu_error(result); break; }
        /* Private CPU buffer: copyout may fault/re-enter VFS, so hold no
         * controller lock across uiomove. It is never a DMA target.
         */
        error=uiomove((void *)(scratch+skip),(int)take,uio);
        if(error) break;
    }
    kmem_free(kernel_map,scratch,PAGE_SIZE);
    return error;
}
static int qu_write(__unused dev_t dev,__unused struct uio *uio,__unused int flags) { return EROFS; }
static const struct bdevsw qu_bdevsw={
    .d_open=qu_open,.d_close=qu_close,.d_strategy=qu_strategy,.d_ioctl=qu_ioctl,
    .d_dump=eno_dump,.d_psize=qu_psize,.d_type=D_DISK
};
static const struct cdevsw qu_cdevsw={
    .d_open=qu_open,.d_close=qu_close,.d_read=qu_read,.d_write=qu_write,.d_ioctl=qu_ioctl,
    .d_stop=eno_stop,.d_reset=eno_reset,.d_ttys=NULL,.d_select=eno_select,.d_mmap=eno_mmap,
    .d_strategy=eno_strat,.d_reserved_1=eno_getc,.d_reserved_2=eno_putc,.d_type=D_DISK
};
int duchamp_qemu_ufs_rootdev(dev_t *device) {
    if(!device) return EINVAL;
    if(qu.ready) { *device=qu.device; return 0; }
    if(qu.attempted) return ENXIO;
    qu.attempted=1;
    int error=qu_profile();
    if(error) { printf("DUCHAMP QUFS PROFILE REJECTED\n"); return error; }
    printf("DUCHAMP QUFS PROFILE VERIFIED\n");
    vm_offset_t config=ml_io_map(QU_ECAM+(4u<<15),0x1000);
    if(!config) return ENOMEM;
    volatile uint32_t *pci=(void *)config;
    if(pci[0]!=QU_PCI_ID || pci[2]>>16!=0x0109 || (pci[1]&7)) return ENXIO;
    uint32_t type=pci[4]&15;
    if(type!=0 && type!=4) return ENXIO;
    pci[4]=(uint32_t)QU_BAR;
    if(type==4) pci[5]=0;
    *(volatile uint16_t *)(config+4)=6;
    qu_barrier(NULL);
    if((pci[4]&~15u)!=QU_BAR) return EIO;
    qu.regs=ml_io_map(QU_BAR,0x1000);
    if(!qu.regs) return ENOMEM;
    if(kmem_alloc_contig(kernel_map,&qu.dma,QU_DMA_BYTES,PAGE_MASK,0,0,
        KMA_DATA|KMA_ZERO|KMA_PERMANENT,VM_KERN_MEMORY_IOKIT)!=KERN_SUCCESS) return ENOMEM;
    ppnum_t first=pmap_find_phys(kernel_pmap,(addr64_t)qu.dma);
    if(!first) return ENOMEM;
    qu.dma_pa=ptoa_64(first);
    for(vm_size_t offset=0;offset<QU_DMA_BYTES;offset+=PAGE_SIZE)
        if(ptoa_64(pmap_find_phys(kernel_pmap,(addr64_t)qu.dma+offset))!=qu.dma_pa+offset) return EIO;
    struct dufs_config setup={
        .io={NULL,qu_read32,qu_write32,qu_dma_write,qu_dma_read,qu_barrier,qu_milliseconds},
        .dma_begin=qu.dma_pa,.dma_end=qu.dma_pa+QU_DMA_BYTES,
        .list_dma=qu.dma_pa,.command_dma=qu.dma_pa+0x1000,.data_dma=qu.dma_pa+0x10000,
        .timeout_ms=3000,.exclusive_platform_ready=1,.lun=0
    };
    int result=dufs_bind(&qu.host,&setup);
    if(!result) result=dufs_start(&qu.host);
    if(!result) result=dufs_nop(&qu.host);
    if(!result) result=dufs_device_init(&qu.host);
    uint64_t blocks=0;
    if(!result) result=dufs_capacity(&qu.host,&blocks,&qu.physical_bytes);
    if(result) { printf("DUCHAMP QUFS ATTACH FAILED result=%d\n",result); return qu_error(result); }
    if(qu.physical_bytes!=4096 || blocks>UINT64_MAX/qu.physical_bytes) return ENXIO;
    qu.bytes=blocks*qu.physical_bytes; qu.sector_bytes=DEV_BSIZE;
    qu.bmajor=bdevsw_add(-1,&qu_bdevsw);
    if(qu.bmajor<0) return ENXIO;
    qu.cmajor=cdevsw_add_with_bdev(-1,&qu_cdevsw,qu.bmajor);
    if(qu.cmajor<0) return ENXIO;
    qu.device=makedev(qu.bmajor,0);
    devfs_make_node(qu.device,DEVFS_BLOCK,UID_ROOT,GID_OPERATOR,0440,"qufs0");
    devfs_make_node(makedev(qu.cmajor,0),DEVFS_CHAR,UID_ROOT,GID_OPERATOR,0440,"rqufs0");
    qu.ready=1;
    printf("DUCHAMP QUFS READY blocks=%llu blocksize=%u dma=0x%llx readonly=1\n",
           (unsigned long long)blocks,qu.physical_bytes,(unsigned long long)qu.dma_pa);
    *device=qu.device;
    return 0;
}
#endif
