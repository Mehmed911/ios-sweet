#include "mt6897_backends.h"
static int fault(struct mb_iommu *m,int error) { m->state=3; return error; }
static int allowed(struct mb_iommu *m) {
    unsigned resource=m->client==MB_CLIENT_DISP?MB_DISP_IOMMU:MB_MDP_IOMMU;
    return m->io.authorise(m->io.context,resource)==1?0:MB_UNVERIFIED;
}
static int rd(struct mb_iommu *m,uint32_t off,uint32_t *v) {
    return m->io.read32(m->io.context,m->client-1,off,v)?MB_IO:0;
}
static int wr(struct mb_iommu *m,uint32_t off,uint32_t v) {
    return m->io.write32(m->io.context,m->client-1,off,v)?MB_IO:0;
}
static int done(struct mb_iommu *m) {
    uint64_t start=m->io.microseconds(m->io.context);
    for(unsigned i=0;i<101;i++) {
        uint32_t v; int r=rd(m,0x12c,&v);
        if(r) return r;
        if(v) { if((r=wr(m,0x12c,0))) return r; m->io.barrier(m->io.context); return 0; }
        if(m->io.microseconds(m->io.context)-start>=1000) break;
        if(m->io.delay_us(m->io.context,10)) return MB_IO;
    }
    return MB_TIMEOUT; /* No fallback reset/flush-all or table reclamation. */
}
static int clean_status(struct mb_iommu *m) {
    uint32_t ctrl,status; int r=rd(m,0x110,&ctrl);
    if(r) return r;
    if(!(ctrl&8)) return MB_UNVERIFIED; /* Existing domain must have TLB_SYNC_EN. */
    if((r=rd(m,0x12c,&status))) return r;
    return status?MB_BUSY:0; /* Do not mistake stale completion for our own. */
}
int mb_iommu_bind(struct mb_iommu *m,const struct mb_io *o,unsigned client,uint64_t b,uint64_t e) {
    if(!m || !o || !o->authorise || !o->read32 || !o->write32 || !o->barrier ||
       !o->microseconds || !o->delay_us || b>=e || e>(1ull<<34) || (b&4095) || (e&4095)) return MB_ARGUMENT;
    if(m->state) return MB_STATE;
    /* The source/DTB binds display/MDP to these M4Us. It does NOT bind UFS.
     * Refuse UFS before authorization, mapping or ANY register access.
     */
    if(client!=MB_CLIENT_DISP && client!=MB_CLIENT_MDP) return MB_UNVERIFIED;
    m->io=*o; m->client=client; m->iova_begin=b; m->iova_end=e; m->state=1;
    return 0;
}
int mb_iommu_install(struct mb_iommu *m,uint32_t ttbr,int table_authorised) {
    if(!m || !ttbr) return MB_ARGUMENT;
    if(m->state!=1) return MB_STATE;
    if(table_authorised!=1) return MB_UNVERIFIED;
    int r=allowed(m); if(r) return r;
    uint32_t old;
    if((r=rd(m,0,&old))) return fault(m,r);
    if(old) return MB_BUSY; /* Never overwrite an inherited/live table. */
    if((r=clean_status(m))) return r==MB_IO?fault(m,r):r;
    m->io.barrier(m->io.context); /* Provider has already synchronized tables. */
    if((r=wr(m,0,ttbr))) return fault(m,r);
    if((r=rd(m,0,&old))) return fault(m,r);
    if(old!=ttbr) return fault(m,MB_IO);
    if((r=wr(m,0x2c,3)) || (r=wr(m,0x20,2))) return fault(m,r);
    m->io.barrier(m->io.context);
    if((r=done(m))) return fault(m,r);
    m->state=2; return 0;
}
int mb_iommu_invalidate(struct mb_iommu *m,uint64_t a,uint64_t n) {
    if(!m || !n || (a&4095) || (n&4095)) return MB_ARGUMENT;
    if(m->state!=2) return MB_STATE;
    if(a<m->iova_begin || a>=m->iova_end || n>m->iova_end-a) return MB_RANGE;
    int r=allowed(m); if(r) return fault(m,r);
    if((r=clean_status(m))) return fault(m,r);
    uint64_t last=a+n-1;
    uint32_t first=(uint32_t)(a&0xfffff000u)|(uint32_t)(a>>32);
    uint32_t end=(uint32_t)(last&0xfffff000u)|(uint32_t)(last>>32);
    if((r=wr(m,0x2c,3)) || (r=wr(m,0x24,first)) || (r=wr(m,0x28,end)) ||
       (r=wr(m,0x20,1))) return fault(m,r);
    m->io.barrier(m->io.context);
    if((r=done(m))) return fault(m,r);
    return 0;
}
