#include "mt6897_backends.h"
int mb_firmware_bind(struct mb_firmware *f,const struct mb_fw_ops *o) {
    if(!f || !o || !o->authorise || !o->conduit || !o->verify_reply) return MB_ARGUMENT;
    if(f->state) return MB_STATE;
    f->ops=*o; f->state=1; return 0;
}
int mb_firmware_ufs(struct mb_firmware *f,const uint64_t q[8],uint64_t out[4]) {
    if(!f || !q || !out) return MB_ARGUMENT;
    if(f->state!=1) return MB_STATE;
    if(q[0]!=0xc2000276u || q[2]>1 || q[4] || q[5] || q[6] || q[7] ||
       !((q[1]==512 && !q[3]) || (q[1]==8 && q[3]<=1))) return MB_ARGUMENT;
    if(f->ops.authorise(f->ops.context,q)!=1) return MB_UNVERIFIED;
    uint64_t reply[4]={0,0,0,0};
    if(f->ops.conduit(f->ops.context,q,reply)) { f->state=2; return MB_IO; }
    for(unsigned i=0;i<4;i++) f->last_reply[i]=reply[i];
    /* a0==0 alone cannot prove a service took effect: the reference firmware
     * may compile MTCMOS handling out while returning zero. No guessing.
     */
    int verified=f->ops.verify_reply(f->ops.context,q,reply);
    if(verified!=1) { f->state=2; return verified<0?MB_IO:MB_UNVERIFIED; }
    for(unsigned i=0;i<4;i++) out[i]=reply[i];
    return 0;
}
