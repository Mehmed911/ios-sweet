#include "mt6897_ufs_platform.h"

int mp_reset_register(unsigned id,int asserted,struct mp_reset_register *r) {
    if(!r || id>MP_HCI || (asserted!=0 && asserted!=1)) return MP_ARGUMENT;
    r->bank=0x112bb000ull; r->offset=asserted?0x48:0x4c; r->mask=1u<<id;
    return MP_OK;
}
static int fail(struct mp_power *p,int result) {
    p->state=MP_FAULTED;
    return result;
}
static int permitted(struct mp_power *p) {
    if(p->profile.prerequisites!=MP_REQUIRED ||
       p->ops.authorise(p->ops.context,MP_REQUIRED)!=1) return MP_UNVERIFIED;
    return MP_OK;
}
static int sip(struct mp_power *p,uint32_t selector,uint64_t value,uint64_t stage) {
    struct mp_sip_request r={{MP_SIP_UFS,selector,value,stage,0,0,0,0}};
    return p->ops.sip(p->ops.context,&r)?MP_IO:MP_OK;
}
int mp_bind(struct mp_power *p,const struct mp_profile *profile,const struct mp_ops *ops) {
    if(!p || !profile || !ops || !ops->authorise || !ops->sip ||
       !ops->hci_read32 || !ops->hci_write32 || !ops->barrier ||
       !ops->microseconds || !ops->delay_us || !ops->reset) return MP_ARGUMENT;
    if(p->state!=MP_NEW) return MP_STATE;
    /* Only the captured Duchamp policy. A different DTB/version is a new port. */
    if(profile->mphy_version!=1 || profile->rtff_mtcmos!=1 ||
       profile->va09_supported!=0 || profile->prerequisites!=MP_REQUIRED)
        return MP_UNVERIFIED;
    p->profile=*profile; p->ops=*ops; p->state=MP_BOUND;
    return MP_OK;
}
int mp_prepare(struct mp_power *p) {
    if(!p) return MP_ARGUMENT;
    if(p->state!=MP_BOUND) return MP_STATE;
    int result=permitted(p);
    if(result) return result; /* No hardware operation has happened. */
    p->state=MP_PREPARING;
    /* phy-mtk-ufs.c power_on returns immediately for mphy-ver=1.
     * Deliberately no PHY register access or old unipro/mp clock lookup.
     */
    p->step=MP_PHY_DELEGATED;
    if((result=sip(p,MP_SIP_MTCMOS,0,0))) return fail(p,result);
    p->step=MP_RTFF_RESTORED; /* false is restore, NOT a power-off request. */
    if((result=sip(p,MP_SIP_MTCMOS,1,0))) return fail(p,result);
    p->step=MP_MTCMOS_ON;
    if((result=sip(p,MP_SIP_REFCLK,1,0))) return fail(p,result);
    p->step=MP_REF_PRE;
    if(p->ops.hci_write32(p->ops.context,MP_REFCLK_OFFSET,1)) return fail(p,MP_IO);
    p->ops.barrier(p->ops.context);
    p->step=MP_REF_REQUEST;
    uint64_t start=p->ops.microseconds(p->ops.context);
    int ack=0;
    /* A second finite bound also handles a broken/non-progressing timer.
     * Require both requested state and ACK, not 0==0 after an ignored write.
     */
    for(unsigned poll=0;poll<32;poll++) {
        uint32_t value;
        if(p->ops.hci_read32(p->ops.context,MP_REFCLK_OFFSET,&value)) return fail(p,MP_IO);
        if((value&3u)==3u) { ack=1; break; }
        if(p->ops.microseconds(p->ops.context)-start>=MP_REF_TIMEOUT_US) break;
        if(p->ops.delay_us(p->ops.context,100)) return fail(p,MP_IO);
    }
    if(!ack) {
        /* Documented clock-on timeout notification. State remains UNKNOWN;
         * do not write RELEASE, power down shared resources or free DMA.
         */
        result=sip(p,MP_SIP_REFCLK,0,1);
        return fail(p,result?result:MP_TIMEOUT);
    }
    p->step=MP_REF_ACK;
    if(p->ops.delay_us(p->ops.context,MP_REF_SETTLE_US)) return fail(p,MP_IO);
    p->step=MP_REF_SETTLED;
    if((result=sip(p,MP_SIP_REFCLK,1,1))) return fail(p,result);
    p->step=MP_REF_POST; p->state=MP_PREPARED;
    return MP_OK;
}
int mp_reset_host(struct mp_power *p) {
    static const unsigned order[]={MP_HCI,MP_CRYPTO,MP_UNIPRO,MP_UNIPRO,MP_CRYPTO,MP_HCI};
    if(!p) return MP_ARGUMENT;
    if(p->state!=MP_PREPARED) return MP_STATE;
    int result=permitted(p);
    if(result) return result;
    for(unsigned i=0;i<6;i++) {
        if(i==3 && p->ops.delay_us(p->ops.context,100)) return fail(p,MP_IO);
        if(p->ops.reset(p->ops.context,order[i],i<3)) return fail(p,MP_IO);
    }
    p->state=MP_RESET_DONE;
    return MP_OK;
}
