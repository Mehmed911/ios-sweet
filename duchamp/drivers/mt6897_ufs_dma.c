#include "mt6897_ufs_dma.h"

static int pow2(uint64_t n) { return n && !(n&(n-1)); }
static int poison(struct md_pool *p,int error) { p->state=MD_POISONED; return error; }
static int authorised(struct md_pool *p) {
    return p->ops.authorise(p->ops.context,&p->config)==1?MD_OK:MD_UNVERIFIED;
}
int md_bind(struct md_pool *p,const struct md_config *c,const struct md_ops *o) {
    if(!p || !c || !o || !c->cpu || !c->bytes || c->bytes>SIZE_MAX ||
       c->physical>UINT64_MAX-c->bytes || (uintptr_t)c->cpu>UINTPTR_MAX-c->bytes ||
       !pow2(c->cache_line) || c->cache_line<16 || c->cache_line>4096 ||
       !pow2(c->alignment) || c->alignment<c->cache_line ||
       c->physical%c->alignment || (uintptr_t)c->cpu%c->cache_line ||
       c->bytes%c->alignment || c->device_begin>=c->device_end ||
       !c->address_bits || c->address_bits>64 ||
       c->direction<MD_TO_DEVICE || c->direction>MD_BIDIRECTIONAL ||
       !o->authorise || !o->idle || !o->map || !o->sync_device || !o->sync_cpu ||
       !o->barrier || !o->unmap) return MD_ARGUMENT;
    if(p->state!=MD_NEW) return MD_STATE;
    if(c->route!=MD_VERIFIED_BUS_WINDOW && c->route!=MD_VERIFIED_IOMMU) return MD_UNVERIFIED;
    /* Reserving a bus window does not establish that physical == DMA. The
     * mapper must return an explicitly validated device address in both modes.
     */
    p->config=*c; p->ops=*o; p->state=MD_BOUND;
    return MD_OK;
}
int md_map(struct md_pool *p) {
    if(!p) return MD_ARGUMENT;
    if(p->state!=MD_BOUND) return MD_STATE;
    int r=authorised(p);
    if(r) return r;
    if(p->ops.idle(p->ops.context)!=1) return MD_BUSY;
    if(p->ops.map(p->ops.context,p->config.physical,p->config.bytes,p->config.direction,
                  &p->device,&p->cookie)) return poison(p,MD_IO);
    const struct md_config *c=&p->config;
    uint64_t d=p->device;
    if(d<c->device_begin || d>=c->device_end || c->bytes>c->device_end-d ||
       d%c->alignment || d>UINT64_MAX-(c->bytes-1) ||
       (c->address_bits<64 && ((d+c->bytes-1)>>c->address_bits)))
        return poison(p,MD_RANGE);
    p->state=MD_CPU;
    return MD_OK;
}
int md_for_device(struct md_pool *p) {
    if(!p) return MD_ARGUMENT;
    if(p->state!=MD_CPU) return MD_STATE;
    int r=authorised(p);
    if(r) return r;
    if(p->ops.idle(p->ops.context)!=1) return MD_BUSY;
    if(p->ops.sync_device(p->ops.context,p->config.cpu,p->config.bytes,p->config.direction))
        return poison(p,MD_IO);
    p->ops.barrier(p->ops.context);
    p->state=MD_DEVICE;
    return MD_OK;
}
int md_for_cpu(struct md_pool *p) {
    if(!p) return MD_ARGUMENT;
    if(p->state!=MD_DEVICE) return MD_STATE;
    int r=authorised(p);
    if(r) return poison(p,r); /* Ownership changed while DMA may be live. */
    if(p->ops.idle(p->ops.context)!=1) return MD_BUSY;
    p->ops.barrier(p->ops.context);
    if(p->ops.sync_cpu(p->ops.context,p->config.cpu,p->config.bytes,p->config.direction))
        return poison(p,MD_IO);
    p->state=MD_CPU;
    return MD_OK;
}
int md_release(struct md_pool *p) {
    if(!p) return MD_ARGUMENT;
    if(p->state!=MD_CPU) return MD_STATE;
    int r=authorised(p);
    if(r) return r;
    if(p->ops.idle(p->ops.context)!=1) return MD_BUSY;
    if(p->ops.unmap(p->ops.context,p->cookie,p->device,p->config.bytes,p->config.direction))
        return poison(p,MD_IO);
    p->device=0; p->cookie=0; p->state=MD_RELEASED;
    return MD_OK;
}
void md_poison(struct md_pool *p) {
    if(p && p->state!=MD_NEW && p->state!=MD_RELEASED) p->state=MD_POISONED;
}
