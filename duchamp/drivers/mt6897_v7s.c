#include "mt6897_v7s.h"
static uint32_t extended(uint64_t p) {
    return (uint32_t)((p>>23)&0x200u)|(uint32_t)((p>>29)&0x10u)|(uint32_t)((p>>29)&0x20u);
}
static uint64_t decoded(uint32_t p,uint32_t mask) {
    return (p&mask)|((uint64_t)(p&0x200u)<<23)|((uint64_t)(p&0x10u)<<29)|((uint64_t)(p&0x20u)<<29);
}
static int overlaps(uint64_t a,uint64_t n,uint64_t b,uint64_t k) {
    return a<b+k && b<a+n;
}
static int slot(const struct mv7_table *t,uint32_t entry,uint32_t *index) {
    if((entry&3u)!=1u) return MV7_CORRUPT;
    uint64_t pa=decoded(entry,0xfffffc00u);
    if(pa<t->pool_pa || (pa-t->pool_pa)%1024 || (pa-t->pool_pa)/1024>=t->used) return MV7_CORRUPT;
    uint32_t i=(uint32_t)((pa-t->pool_pa)/1024);
    uint32_t expected=(uint32_t)pa|extended(pa)|9u;
    if(entry!=expected) return MV7_CORRUPT;
    *index=i; return 0;
}
int mv7_init(struct mv7_table *t,void *root,uint64_t rpa,void *pool,uint64_t ppa,uint32_t capacity) {
    uint64_t bytes=(uint64_t)capacity*1024;
    if(!t || !root || !pool || !capacity || capacity>MV7_L1_ENTRIES ||
       (uintptr_t)root%4 || (uintptr_t)pool%4 || !rpa || rpa%65536 || ppa%1024)
        return MV7_ARGUMENT;
    if(t->state) return MV7_STATE;
    if(rpa>=(1ull<<35) || MV7_L1_BYTES>(1ull<<35)-rpa ||
       ppa>=(1ull<<35) || bytes>(1ull<<35)-ppa ||
       (uintptr_t)root>UINTPTR_MAX-MV7_L1_BYTES || (uintptr_t)pool>UINTPTR_MAX-bytes ||
       overlaps(rpa,MV7_L1_BYTES,ppa,bytes) ||
       overlaps((uintptr_t)root,MV7_L1_BYTES,(uintptr_t)pool,bytes)) return MV7_RANGE;
    t->root=root;t->root_pa=rpa;t->pool=pool;t->pool_pa=ppa;t->capacity=capacity;t->used=0;
    for(unsigned i=0;i<MV7_L1_ENTRIES;i++)t->root[i]=0;
    for(uint64_t i=0;i<bytes/4;i++)t->pool[i]=0;
    t->state=1;return 0;
}
int mv7_map(struct mv7_table *t,uint64_t a,uint64_t p,uint64_t n,int cacheable) {
    if(!t || !n || (a&4095) || (p&4095) || (n&4095) || (cacheable!=0 && cacheable!=1))
        return MV7_ARGUMENT;
    if(t->state!=1)return MV7_STATE;
    if(a>=(1ull<<34) || n>(1ull<<34)-a || p>=(1ull<<35) || n>(1ull<<35)-p)return MV7_RANGE;
    uint32_t need=0,last=UINT32_MAX;
    /* Preflight the complete operation before changing any table bytes. */
    for(uint64_t off=0;off<n;off+=4096) {
        uint32_t l1=(uint32_t)((a+off)>>20),l2=(uint32_t)(((a+off)>>12)&255);
        if(!t->root[l1]) {if(last!=l1) {need++;last=l1;}}
        else {
            uint32_t i;int r=slot(t,t->root[l1],&i);
            if(r){t->state=3;return r;}
            if(t->pool[i*256+l2])return MV7_OVERLAP;
        }
    }
    if(need>t->capacity-t->used)return MV7_CAPACITY;
    for(uint64_t off=0;off<n;off+=4096) {
        uint32_t l1=(uint32_t)((a+off)>>20),l2=(uint32_t)(((a+off)>>12)&255),i;
        if(!t->root[l1]) {
            i=t->used++;
            uint64_t pa=t->pool_pa+(uint64_t)i*1024;
            t->root[l1]=(uint32_t)pa|extended(pa)|9u;
        } else { int r=slot(t,t->root[l1],&i);if(r){t->state=3;return r;} }
        uint64_t pa=p+off;
        t->pool[i*256+l2]=(uint32_t)(pa&0xfffff000u)|extended(pa)|0xc42u|(cacheable?12u:0u);
    }
    return 0;
}
int mv7_translate(const struct mv7_table *t,uint64_t a,uint64_t *p) {
    if(!t || !p)return MV7_ARGUMENT;
    if(t->state!=1 && t->state!=2)return MV7_STATE;
    if(a>=(1ull<<34))return MV7_RANGE;
    uint32_t entry=t->root[a>>20];
    if(!entry)return MV7_RANGE;
    uint32_t i;int r=slot(t,entry,&i);if(r)return r;
    entry=t->pool[i*256+((a>>12)&255)];
    if((entry&3u)!=2u)return entry?MV7_CORRUPT:MV7_RANGE;
    *p=decoded(entry,0xfffff000u)|(a&4095);
    return 0;
}
int mv7_seal(struct mv7_table *t,const struct mv7_sync *s,uint32_t *ttbr) {
    if(!t || !s || !s->table || !s->barrier || !ttbr)return MV7_ARGUMENT;
    if(t->state!=1)return MV7_STATE;
    if(t->used && s->table(s->context,t->pool_pa,(size_t)t->used*1024)) {t->state=3;return MV7_SYNC;}
    s->barrier(s->context);
    if(s->table(s->context,t->root_pa,MV7_L1_BYTES)) {t->state=3;return MV7_SYNC;}
    s->barrier(s->context);
    *ttbr=(uint32_t)t->root_pa|(uint32_t)(t->root_pa>>32);
    t->state=2;return 0;
}
