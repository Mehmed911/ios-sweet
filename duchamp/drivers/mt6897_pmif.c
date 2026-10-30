#include "mt6897_backends.h"
static int bad(struct mb_pmif *p,int result) { p->state=2; return result; }
static int wait_state(struct mb_pmif *p,unsigned expected) {
    uint64_t start=p->io.microseconds(p->io.context);
    for(unsigned i=0;i<1001;i++) {
        uint32_t value;
        if(p->io.read32(p->io.context,0,0x8a8,&value)) return MB_IO;
        if(((value>>1)&7)==expected) return 0;
        if(p->io.microseconds(p->io.context)-start>=10000) break;
        if(p->io.delay_us(p->io.context,10)) return MB_IO;
    }
    return MB_TIMEOUT;
}
int mb_pmif_bind(struct mb_pmif *p,const struct mb_io *io,uint32_t mask) {
    if(!p || !io || !io->authorise || !io->read32 || !io->write32 ||
       !io->barrier || !io->microseconds || !io->delay_us) return MB_ARGUMENT;
    if(p->state) return MB_STATE;
    if(mask) return MB_UNVERIFIED;
    p->io=*io; p->state=1; return 0;
}
int mb_pmif_transfer(struct mb_pmif *p,unsigned sid,uint32_t address,
                     void *bytes,size_t count,int write) {
    if(!p || !bytes || !count || count>4 || address>65535 || count>65536-address ||
       (sid!=4 && sid!=8) || (write!=0 && write!=1)) return MB_ARGUMENT;
    if(p->state!=1) return MB_STATE;
    if(p->io.authorise(p->io.context,MB_PMIF)!=1) return MB_UNVERIFIED;
    uint32_t init;
    if(p->io.read32(p->io.context,0,0,&init)) return bad(p,MB_IO);
    if(!(init&1)) return bad(p,MB_UNVERIFIED);
    int r=wait_state(p,0);
    if(r) return bad(p,r); /* Never clear somebody else's inherited reply. */
    uint32_t data=0;
    unsigned char *b=bytes;
    if(write) {
        for(size_t i=0;i<count;i++) data|=(uint32_t)b[i]<<(i*8);
        if(p->io.write32(p->io.context,0,0x884,data)) return bad(p,MB_IO);
    }
    uint32_t command=0xc0000000u|((uint32_t)write<<29)|(sid<<24)|
                     ((uint32_t)(count-1)<<16)|address;
    p->io.barrier(p->io.context);
    if(p->io.write32(p->io.context,0,0x880,command)) return bad(p,MB_IO);
    p->io.barrier(p->io.context);
    if(write) {
        r=wait_state(p,0);
        return r?bad(p,r):0; /* Posted write completion is NOT PMIC readback. */
    }
    if((r=wait_state(p,6))) return bad(p,r);
    if(p->io.read32(p->io.context,0,0x894,&data) ||
       p->io.write32(p->io.context,0,0x8a4,1)) return bad(p,MB_IO);
    p->io.barrier(p->io.context);
    if((r=wait_state(p,0))) return bad(p,r);
    for(size_t i=0;i<count;i++) b[i]=(unsigned char)(data>>(i*8));
    return 0;
}
