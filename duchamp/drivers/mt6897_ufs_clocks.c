#include "mt6897_ufs_clocks.h"
/* Independent implementation from the pinned clk-mt6897-peri.c/binding facts:
 * IDs equal bits (AO 0..3, PDN 0..1); status=4, disable/set=8, enable/clear=12.
 * A cleared status bit means enabled. See QEMU-UFS-XNU.md for source pins.
 */
static int valid(unsigned bank,unsigned id) { return bank<2 && id<(bank==MUFS_AO?4u:2u); }
uint64_t mufs_clock_bank_address(unsigned bank) {
    return bank==MUFS_AO?0x112b8000ull:bank==MUFS_PDN?0x112bb000ull:0;
}
static int fault(struct mufs_clocks *c,int result) { c->state=2; return result; }
static int access(struct mufs_clocks *c,unsigned bank,unsigned id) {
    if(!c || !valid(bank,id)) return MUFS_ARGUMENT;
    if(c->state!=1) return MUFS_FAULTED;
    return c->ops.authorise(c->ops.context,bank,id)==1?MUFS_OK:MUFS_UNVERIFIED;
}
int mufs_clocks_bind(struct mufs_clocks *c,const struct mufs_clock_ops *ops,uint32_t timeout) {
    if(!c || !ops || !timeout || timeout>100000 || !ops->authorise || !ops->read32 ||
       !ops->write32 || !ops->barrier || !ops->microseconds) return MUFS_ARGUMENT;
    if(c->state) return MUFS_FAULTED;
    c->ops=*ops; c->timeout_us=timeout; c->state=1; return 0;
}
int mufs_clock_status(struct mufs_clocks *c,unsigned bank,unsigned id,int *enabled) {
    if(!enabled) return MUFS_ARGUMENT;
    int r=access(c,bank,id); if(r) return r;
    uint32_t value;
    if(c->ops.read32(c->ops.context,bank,4,&value)) return fault(c,MUFS_IO);
    *enabled=(value&(1u<<id))==0; return 0;
}
int mufs_clock_set(struct mufs_clocks *c,unsigned bank,unsigned id,int enable) {
    if(enable!=0 && enable!=1) return MUFS_ARGUMENT;
    int r=access(c,bank,id); if(r) return r;
    uint32_t value,mask=1u<<id;
    if(c->ops.read32(c->ops.context,bank,4,&value)) return fault(c,MUFS_IO);
    if(((value&mask)==0)==enable) return 0;
    if(c->ops.write32(c->ops.context,bank,enable?12:8,mask)) return fault(c,MUFS_IO);
    c->ops.barrier(c->ops.context);
    uint64_t start=c->ops.microseconds(c->ops.context);
    do {
        if(c->ops.read32(c->ops.context,bank,4,&value)) return fault(c,MUFS_IO);
        if(((value&mask)==0)==enable) return 0;
    } while(c->ops.microseconds(c->ops.context)-start<c->timeout_us);
    return fault(c,MUFS_TIMEOUT);
}
