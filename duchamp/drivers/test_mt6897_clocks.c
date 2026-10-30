#include "mt6897_ufs_clocks.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned checks;
#define CHECK(v) do { checks++; assert(v); } while(0)
struct model {
    uint32_t status[2],last_offset,last_mask;
    unsigned reads,writes,barriers;
    uint64_t tick;
    int permitted,stall,read_error,write_error;
};
static int authorise(void *v,unsigned b,unsigned id) { (void)b;(void)id;return ((struct model *)v)->permitted; }
static int read32(void *v,unsigned b,uint32_t off,uint32_t *value) {
    struct model *m=v; m->reads++;
    assert(b<2 && off==4);
    if(m->read_error) return -1;
    *value=m->status[b]; return 0;
}
static int write32(void *v,unsigned b,uint32_t off,uint32_t mask) {
    struct model *m=v; m->writes++; m->last_offset=off; m->last_mask=mask;
    assert(b<2 && (off==8 || off==12));
    if(m->write_error) return -1;
    if(!m->stall) { if(off==8) m->status[b]|=mask; else m->status[b]&=~mask; }
    return 0;
}
static void barrier(void *v) { ((struct model *)v)->barriers++; }
static uint64_t ticks(void *v) { return ++((struct model *)v)->tick; }
static struct mufs_clock_ops ops(struct model *m) {
    return (struct mufs_clock_ops){m,authorise,read32,write32,barrier,ticks};
}
int main(void) {
    CHECK(mufs_clock_bank_address(0)==0x112b8000ull);
    CHECK(mufs_clock_bank_address(1)==0x112bb000ull);
    CHECK(mufs_clock_bank_address(2)==0);
    for(unsigned bank=0;bank<2;bank++) for(unsigned id=0;id<(bank?2u:4u);id++) {
        struct model m={.status={0xa5a5ffff,0x5a5affff}};
        struct mufs_clocks c={0}; struct mufs_clock_ops o=ops(&m);
        int enabled=123;
        CHECK(mufs_clocks_bind(&c,&o,5)==0);
        CHECK(mufs_clock_set(&c,bank,id,1)==MUFS_UNVERIFIED);
        CHECK(mufs_clock_status(&c,bank,id,&enabled)==MUFS_UNVERIFIED && enabled==123);
        CHECK(!m.reads && !m.writes);
        m.permitted=1; uint32_t before=m.status[bank];
        CHECK(mufs_clock_set(&c,bank,id,1)==0);
        CHECK(m.writes==1 && m.last_offset==12 && m.last_mask==(1u<<id));
        CHECK(m.status[bank]==(before&~(1u<<id)) && m.barriers==1);
        CHECK(mufs_clock_status(&c,bank,id,&enabled)==0 && enabled==1);
        CHECK(mufs_clock_set(&c,bank,id,1)==0 && m.writes==1);
        CHECK(mufs_clock_set(&c,bank,id,0)==0);
        CHECK(m.writes==2 && m.last_offset==8 && m.status[bank]==before);
        CHECK(mufs_clock_status(&c,bank,id,&enabled)==0 && !enabled);
        CHECK(mufs_clock_set(&c,bank,id,0)==0 && m.writes==2);
        unsigned accesses=m.reads+m.writes;
        CHECK(mufs_clock_set(&c,bank,32,1)==MUFS_ARGUMENT);
        CHECK(mufs_clock_set(&c,9,0,1)==MUFS_ARGUMENT);
        CHECK(mufs_clock_set(&c,bank,id,2)==MUFS_ARGUMENT);
        CHECK(accesses==m.reads+m.writes);
    }
    for(int mode=0;mode<3;mode++) {
        struct model m={.status={0xffffffff,0xffffffff},.permitted=1};
        m.stall=mode==0; m.read_error=mode==1; m.write_error=mode==2;
        struct mufs_clocks c={0}; struct mufs_clock_ops o=ops(&m);
        CHECK(mufs_clocks_bind(&c,&o,5)==0);
        CHECK(mufs_clock_set(&c,0,0,1)==(mode?MUFS_IO:MUFS_TIMEOUT));
        CHECK(m.writes==(mode==1?0u:1u) && m.reads<12);
        unsigned accesses=m.reads+m.writes;
        CHECK(mufs_clock_set(&c,0,0,1)==MUFS_FAULTED);
        CHECK(mufs_clocks_bind(&c,&o,5)==MUFS_FAULTED);
        CHECK(accesses==m.reads+m.writes);
    }
    printf("%u MT6897 leaf-clock model checks passed; no hardware access\n",checks);
    return 0;
}
