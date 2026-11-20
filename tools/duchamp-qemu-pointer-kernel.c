/* SPDX-License-Identifier: 0BSD */
/* QEMU virt, modern VirtIO-MMIO input only. Never a physical MT6897 driver. */
#include <sys/param.h>
#include <sys/systm.h>
#include <sys/conf.h>
#include <sys/errno.h>
#include <sys/proc.h>
#include <sys/uio.h>
#include <miscfs/devfs/devfs.h>
#include <kern/locks.h>
#include <kern/clock.h>
#include <vm/pmap.h>
#include <vm/vm_kern.h>
#include <pexpert/pexpert.h>
#include <pexpert/device_tree.h>
#include "duchamp-virtio-touch.h"
extern ppnum_t pmap_find_phys(pmap_t,addr64_t);
extern vm_offset_t ml_io_map(vm_offset_t,vm_size_t);
int duchamp_qemu_pointer_register(void);
struct vp_desc {uint64_t address;uint32_t length;uint16_t flags,next;};
struct vp_used_element {uint32_t id,length;};
struct vp_memory {
    struct vp_desc descriptors[VP_QUEUE];
    uint16_t avail_flags,avail_index,avail[VP_QUEUE],used_event;
    uint32_t padding;
    uint16_t used_flags,used_index;
    struct vp_used_element used[VP_QUEUE];
    uint16_t avail_event;
    struct vp_event events[VP_QUEUE];
};
static LCK_GRP_DECLARE(vp_group,"duchamp_qemu_pointer");
static LCK_MTX_DECLARE(vp_lock,&vp_group);
struct vp_context {
    struct vp_memory *queue;vm_offset_t registers,allocation;uint64_t allocation_pa;
    struct vp_state state;struct mt_state touch;uint16_t used_index;
    uint32_t generation;int enabled,opened,connected_pending,touch_device;
};
static struct vp_context devices[2];
static uint32_t vr(struct vp_context *c,uint32_t offset) {
    uint32_t value=*(volatile uint32_t *)(c->registers+offset);__asm__ volatile("dmb oshld" ::: "memory");return value;
}
static void vw(struct vp_context *c,uint32_t offset,uint32_t value) {
    __asm__ volatile("dmb oshst" ::: "memory");*(volatile uint32_t *)(c->registers+offset)=value;__asm__ volatile("dsb osh" ::: "memory");
}
static void address(struct vp_context *c,uint32_t offset,uint64_t pa){vw(c,offset,(uint32_t)pa);vw(c,offset+4,(uint32_t)(pa>>32));}
static int stop(struct vp_context *c) {
    vw(c,0x70,0);
    for(unsigned i=0;i<1000;i++){if(!vr(c,0x70))return 0;delay(1);}return ETIMEDOUT;
}
static int initialize(struct vp_context *c) {
    if(!c->registers)c->registers=ml_io_map(c->touch_device?0x0a003c00:0x0a003e00,0x200);
    if(!c->registers || vr(c,0)!=0x74726976 || vr(c,4)!=2 || vr(c,8)!=18 || vr(c,12)!=0x554d4551)return ENXIO;
    if(stop(c))return EIO;
    if(!c->allocation) {
        if(kmem_alloc_contig(kernel_map,&c->allocation,PAGE_SIZE,PAGE_MASK,0,0,
            KMA_DATA|KMA_ZERO|KMA_PERMANENT,VM_KERN_MEMORY_IOKIT)!=KERN_SUCCESS)return ENOMEM;
        c->allocation_pa=ptoa_64(pmap_find_phys(kernel_pmap,(addr64_t)c->allocation));
        if(!c->allocation_pa || (c->allocation_pa&PAGE_MASK) || sizeof(struct vp_memory)>PAGE_SIZE)return EIO;
        c->queue=(void *)c->allocation;
    }
    bzero(c->queue,PAGE_SIZE);c->used_index=0;
    vw(c,0x70,1);vw(c,0x70,3);vw(c,0x14,1);
    if(!(vr(c,0x10)&1))return ENOTSUP; /* VIRTIO_F_VERSION_1, bit 32 */
    vw(c,0x24,0);vw(c,0x20,0);vw(c,0x24,1);vw(c,0x20,1);
    vw(c,0x70,11);if(!(vr(c,0x70)&8))return EIO;
    vw(c,0x30,0);if(vr(c,0x34)<VP_QUEUE || vr(c,0x44))return EIO;
    vw(c,0x38,VP_QUEUE);
    for(unsigned i=0;i<VP_QUEUE;i++) {
        c->queue->descriptors[i]=(struct vp_desc){c->allocation_pa+__builtin_offsetof(struct vp_memory,events)+i*sizeof(struct vp_event),sizeof(struct vp_event),2,0};
        c->queue->avail[i]=(uint16_t)i;
    }
    c->queue->avail_flags=1;c->queue->avail_index=VP_QUEUE;
    address(c,0x80,c->allocation_pa);address(c,0x90,c->allocation_pa+__builtin_offsetof(struct vp_memory,avail_flags));
    address(c,0xa0,c->allocation_pa+__builtin_offsetof(struct vp_memory,used_flags));
    __asm__ volatile("dsb sy" ::: "memory");vw(c,0x44,1);vw(c,0x70,15);vw(c,0x50,0);
    if(++c->generation==0)return EIO;
    vp_init(&c->state,c->generation);mt_init(&c->touch,c->generation);c->connected_pending=1;
    printf("DUCHAMP QEMU INPUT READY kind=%s generation=%u queue=%u dma=qemu-coherent page=0x%llx\n",c->touch_device?"multitouch":"pointer",c->generation,VP_QUEUE,c->allocation_pa);
    return 0;
}
static int vp_open(__unused dev_t d,int flags,__unused int type,__unused struct proc *p) {
    if(minor(d)>1)return ENXIO;struct vp_context *c=&devices[minor(d)];
    lck_mtx_lock(&vp_lock);int error=!c->enabled?ENXIO:flags&FWRITE?EROFS:c->opened?EBUSY:initialize(c);
    if(!error)c->opened=1;lck_mtx_unlock(&vp_lock);return error;
}
static int vp_close(__unused dev_t d,__unused int flags,__unused int type,__unused struct proc *p) {
    if(minor(d)>1)return ENXIO;struct vp_context *c=&devices[minor(d)];
    lck_mtx_lock(&vp_lock);int error=c->registers?stop(c):0;c->opened=0;lck_mtx_unlock(&vp_lock);return error;
}
static int vp_read(__unused dev_t d,struct uio *uio,__unused int flags) {
    if(minor(d)>1)return ENXIO;struct vp_context *c=&devices[minor(d)];
    size_t bytes=c->touch_device?sizeof(struct mt_report):sizeof(struct vp_report);
    if(uio_resid(uio)!=bytes)return EINVAL;
    union {struct vp_report pointer;struct mt_report touch;} report={0};int error=EWOULDBLOCK;int complete=0;
    lck_mtx_lock(&vp_lock);
    if(!c->opened){error=ENXIO;goto done;}
    if(c->connected_pending) {
        c->connected_pending=0;
        if(c->touch_device)report.touch=(struct mt_report){.version=MT_VERSION,.generation=c->generation,.flags=MT_CONNECTED};
        else report.pointer=(struct vp_report){VP_VERSION,c->generation,0,VP_CONNECTED,0,0,0,0};
        complete=1;goto done;
    }
    if(vr(c,0x70)!=15){error=ENXIO;goto done;}
    for(unsigned count=0;count<VP_QUEUE;count++) {
        uint16_t current=__atomic_load_n(&c->queue->used_index,__ATOMIC_ACQUIRE);
        uint16_t pending=(uint16_t)(current-c->used_index);if(!pending)break;
        struct vp_used_element e=c->queue->used[c->used_index%VP_QUEUE];
        if(!vp_used(e.id,e.length,pending)){error=EIO;vw(c,0x70,128);goto done;}
        struct vp_event event=c->queue->events[e.id];c->used_index++;
        uint16_t at=c->queue->avail_index;c->queue->avail[at%VP_QUEUE]=(uint16_t)e.id;
        __atomic_store_n(&c->queue->avail_index,(uint16_t)(at+1),__ATOMIC_RELEASE);vw(c,0x50,0);
        int parsed=c->touch_device?mt_event(&c->touch,event,&report.touch):vp_event(&c->state,event,&report.pointer);
        if(parsed<0){error=EIO;goto done;}
        if(parsed>0){complete=1;break;}
    }
    {uint32_t irq=vr(c,0x60);if(irq)vw(c,0x64,irq&3);}
done:
    lck_mtx_unlock(&vp_lock);
    return complete?uiomove((void *)&report,bytes,uio):error;
}
static const struct cdevsw vp_device={
    .d_open=vp_open,.d_close=vp_close,.d_read=vp_read,.d_write=eno_rdwrt,.d_ioctl=eno_ioctl,
    .d_stop=eno_stop,.d_reset=eno_reset,.d_ttys=NULL,.d_select=eno_select,.d_mmap=eno_mmap,
    .d_strategy=eno_strat,.d_reserved_1=eno_getc,.d_reserved_2=eno_putc,.d_type=D_TTY
};
int duchamp_qemu_pointer_register(void) {
    uint32_t flag=0,size;uint64_t midr;DTEntry node;const void *p;
    if(!PE_parse_boot_argn("duchamp_qemu_pointer",&flag,sizeof(flag)))return 0;
    __asm__ volatile("mrs %0,midr_el1":"=r"(midr));
    if(flag!=1 || (midr>>24)!=0x41 || ((midr>>4)&0xfff)!=0xd0b)return ENXIO;
    for(unsigned i=0;i<2;i++) {
        const char *arg=i?"duchamp_qemu_multitouch":"duchamp_qemu_pointer";
        const char *path=i?"/duchamp-qemu-multitouch":"/duchamp-qemu-pointer";
        const char *compatible=i?"qemu,duchamp-virtio-multitouch-v1":"qemu,duchamp-virtio-pointer-v1";
        uint64_t address=i?0x0a003c00:0x0a003e00;flag=0;
        if(!PE_parse_boot_argn(arg,&flag,sizeof(flag)))continue;
        if(flag!=1 || SecureDTLookupEntry(NULL,path,&node)!=kSuccess ||
           SecureDTGetProperty(node,"compatible",&p,&size)!=kSuccess || size!=strlen(compatible)+1 || memcmp(p,compatible,size) ||
           SecureDTGetProperty(node,"reg",&p,&size)!=kSuccess || size!=16 ||
           ((const uint64_t *)p)[0]!=address || ((const uint64_t *)p)[1]!=0x200)return ENXIO;
        devices[i].enabled=1;devices[i].touch_device=(int)i;
    }
    static int registered;if(registered)return 0;int major=cdevsw_add(-1,&vp_device);
    if(major<0)return ENXIO;
    for(unsigned i=0;i<2;i++)if(devices[i].enabled && !devfs_make_node(makedev(major,i),DEVFS_CHAR,UID_ROOT,GID_WHEEL,0600,
            i?"duchamp-touch":"duchamp-pointer"))return ENXIO;
    registered=1;printf("DUCHAMP QEMU INPUT REGISTERED pointer=%d touch=%d physical_access=0\n",devices[0].enabled,devices[1].enabled);return 0;
}
