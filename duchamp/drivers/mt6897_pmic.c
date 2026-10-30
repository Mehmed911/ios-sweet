#include "mt6897_backends.h"
static const uint32_t vemc_uv[]={1200000,1300000,1500000,1700000,1800000,2000000,
    2500000,2600000,2700000,2800000,2900000,3000000,3100000,3300000,3400000,3500000};
static int begin(struct mb_pmic *p,unsigned rail,int write) {
    if(!p || rail>MB_VBUCK3) return MB_ARGUMENT;
    if(p->state!=1) return MB_STATE;
    if(p->ops.authorise(p->ops.context,rail,write)!=1) return MB_UNVERIFIED;
    if(p->ops.lock(p->ops.context)) { p->state=2; return MB_IO; }
    return 0;
}
static int end(struct mb_pmic *p,int r) {
    p->ops.unlock(p->ops.context);
    if(r) p->state=2;
    return r;
}
static int read8(struct mb_pmic *p,unsigned sid,uint16_t a,uint8_t *v) {
    return p->ops.read(p->ops.context,sid,a,v,1)?MB_IO:0;
}
static int write8(struct mb_pmic *p,unsigned sid,uint16_t a,uint8_t v) {
    return p->ops.write(p->ops.context,sid,a,&v,1)?MB_IO:0;
}
int mb_pmic_bind(struct mb_pmic *p,const struct mb_pmic_ops *o) {
    if(!p || !o || !o->authorise || !o->lock || !o->unlock ||
       !o->read || !o->write || !o->delay_us) return MB_ARGUMENT;
    if(p->state) return MB_STATE;
    p->ops=*o; p->state=1; return 0;
}
int mb_pmic_voltage(struct mb_pmic *p,unsigned rail,uint32_t uv) {
    unsigned selector=16;
    if(rail==MB_VEMC) {
        for(unsigned i=0;i<16;i++) if(vemc_uv[i]==uv) selector=i;
        if(selector==16) return MB_RANGE;
    } else if(rail==MB_VBUCK3) {
        /* The matched driver advertises n_voltages=0xbf: selector 0xbf is
         * outside that count, despite the inclusive linear-range endpoint.
         */
        if(uv<300000 || uv%6250 || uv/6250>=0xbf) return MB_RANGE;
        selector=uv/6250;
    } else return MB_ARGUMENT;
    int r=begin(p,rail,1);
    if(r) return r;
    unsigned sid=rail==MB_VEMC?4:8;
    uint16_t reg=rail==MB_VEMC?0x1b40:0x144d;
    uint8_t old,mask=0xff,value=(uint8_t)selector;
    if(rail==MB_VEMC) {
        uint8_t trap;
        if((r=read8(p,4,0x36,&trap))) return end(p,r);
        if(trap>1) return end(p,MB_UNVERIFIED);
        mask=(uint8_t)(0xfu<<(trap*4)); value=(uint8_t)(selector<<(trap*4));
    }
    if((r=read8(p,sid,reg,&old))) return end(p,r);
    uint8_t next=(uint8_t)((old&~mask)|value);
    if(next==old) return end(p,0);
    if(rail==MB_VEMC) {
        const uint8_t key[2]={0x9c,0x9c},zero[2]={0,0};
        /* Once unlock is attempted, always attempt to relock, including a
         * partially failed key write. Never change another protected rail.
         */
        r=p->ops.write(p->ops.context,4,0x39e,key,2)?MB_IO:0;
        if(!r) r=write8(p,4,reg,next);
        int locked=p->ops.write(p->ops.context,4,0x39e,zero,2);
        if(locked) r=MB_IO;
    } else r=write8(p,8,reg,next);
    if(!r) {
        uint8_t actual;
        r=read8(p,sid,reg,&actual);
        if(!r && (actual&mask)!=value) r=MB_IO;
    }
    return end(p,r);
}
int mb_pmic_enable(struct mb_pmic *p,unsigned rail) {
    int r=begin(p,rail,1);
    if(r) return r;
    unsigned sid=rail==MB_VEMC?4:8;
    uint16_t reg=rail==MB_VEMC?0x1c23:0x1440;
    uint8_t mask=rail==MB_VEMC?1:4,old;
    if((r=read8(p,sid,reg,&old))) return end(p,r);
    if(!(old&mask)) {
        r=write8(p,sid,rail==MB_VEMC?reg:(uint16_t)(reg+1),
                 rail==MB_VEMC?(uint8_t)(old|mask):mask);
        if(!r && p->ops.delay_us(p->ops.context,rail==MB_VEMC?680:256)) r=MB_IO;
    }
    if(!r) {
        uint8_t actual;
        r=read8(p,sid,reg,&actual);
        if(!r && !(actual&mask)) r=MB_IO;
    }
    return end(p,r);
}
