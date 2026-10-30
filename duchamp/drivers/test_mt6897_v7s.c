#include "mt6897_v7s.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
extern uint32_t oracle_page(uint64_t,int);
extern uint32_t oracle_link(uint64_t);
extern uint32_t oracle_ttbr(uint64_t);
extern uint64_t oracle_decode(uint32_t,int);
static unsigned checks;
#define CHECK(v) do { checks++; assert(v); } while(0)
static uint32_t root[MV7_L1_ENTRIES+2],pool[1024+2];
struct sync_model {unsigned calls,barriers,fail;uint64_t pa[2];size_t n[2];};
static int sync_fn(void *v,uint64_t pa,size_t n){
    struct sync_model *s=v;assert(s->calls<2);s->pa[s->calls]=pa;s->n[s->calls]=n;
    return ++s->calls==s->fail?-1:0;
}
static void barrier(void *v){((struct sync_model *)v)->barriers++;}
static void init(struct mv7_table *t,uint64_t rp,uint64_t pp,unsigned n){
    root[0]=root[MV7_L1_ENTRIES+1]=0x12345678;pool[0]=pool[1025]=0x87654321;
    CHECK(mv7_init(t,root+1,rp,pool+1,pp,n)==0);
}
static void guards(void){
    CHECK(root[0]==0x12345678 && root[MV7_L1_ENTRIES+1]==0x12345678);
    CHECK(pool[0]==0x87654321 && pool[1025]==0x87654321);
}
static uint64_t hash(void) {
    uint64_t h=1469598103934665603ull;
    for(unsigned i=0;i<MV7_L1_ENTRIES+2;i++)h=(h^root[i])*1099511628211ull;
    for(unsigned i=0;i<1026;i++)h=(h^pool[i])*1099511628211ull;
    return h;
}
int main(void){
    for(unsigned rh=0;rh<8;rh++)for(unsigned ph=0;ph<8;ph++)for(int cache=0;cache<2;cache++){
        uint64_t rp=((uint64_t)rh<<32)|0x40000,pp=((uint64_t)ph<<32)|0x80000;
        uint64_t physical=((uint64_t)((rh+ph)&7)<<32)|0x23456000;
        struct mv7_table t={0};init(&t,rp,pp,4);
        CHECK(mv7_map(&t,0xfffff000ull,physical,8192,cache)==0 && t.used==2);
        CHECK(root[1+4095]==oracle_link(pp));
        CHECK(root[1+4096]==oracle_link(pp+1024));
        CHECK(pool[1+255]==oracle_page(physical,cache));
        CHECK(pool[1+256]==oracle_page(physical+4096,cache));
        CHECK(oracle_decode(root[1+4096],1)==pp+1024);
        CHECK(oracle_decode(pool[1+256],2)==physical+4096);
        for(unsigned off=0;off<8192;off+=113){
            uint64_t pa=0;CHECK(mv7_translate(&t,0xfffff000ull+off,&pa)==0 && pa==physical+off);
        }
        uint64_t before=hash();
        CHECK(mv7_map(&t,0xffffe000ull,physical,8192,cache)==MV7_OVERLAP && hash()==before);
        CHECK(mv7_map(&t,0,physical,0,cache)==MV7_ARGUMENT && hash()==before);
        struct sync_model sm={0};struct mv7_sync s={&sm,sync_fn,barrier};uint32_t ttbr=0;
        CHECK(mv7_seal(&t,&s,&ttbr)==0 && ttbr==oracle_ttbr(rp) && t.state==2);
        CHECK(sm.calls==2 && sm.barriers==2 && sm.pa[0]==pp && sm.n[0]==2048 &&
              sm.pa[1]==rp && sm.n[1]==65536);
        CHECK(mv7_map(&t,0,physical,4096,0)==MV7_STATE);
        CHECK(mv7_seal(&t,&s,&ttbr)==MV7_STATE);
        guards();
    }
    for(unsigned h=0;h<7;h++){
        struct mv7_table t={0};init(&t,0x100040000ull,0x200080000ull,4);
        uint64_t pa=((uint64_t)h<<32)|0xfffff000ull,out=0;
        CHECK(mv7_map(&t,(1ull<<34)-8192,pa,8192,0)==0);
        CHECK(mv7_translate(&t,(1ull<<34)-1,&out)==0 && out==pa+8191);
        CHECK(pool[1+254]==oracle_page(pa,0) && pool[1+255]==oracle_page(pa+4096,0));
    }
    for(unsigned mode=0;mode<8;mode++){
        struct mv7_table t={0};init(&t,0x40000,0x80000,1);uint64_t before=hash();
        int r;
        if(mode==0)r=mv7_map(&t,(1ull<<34)-4096,0,8192,0);
        else if(mode==1)r=mv7_map(&t,0,(1ull<<35)-4096,8192,0);
        else if(mode==2)r=mv7_map(&t,1,0,4096,0);
        else if(mode==3)r=mv7_map(&t,0,1,4096,0);
        else if(mode==4)r=mv7_map(&t,0,0,4096,2);
        else if(mode==5)r=mv7_map(&t,0,0,4097,0);
        else if(mode==6)r=mv7_map(&t,0xfffff000ull,0,8192,0);
        else r=mv7_map(&t,UINT64_MAX-4095,0,4096,0);
        CHECK(r==(mode==2||mode==3||mode==4||mode==5?MV7_ARGUMENT:mode==6?MV7_CAPACITY:MV7_RANGE));
        CHECK(hash()==before && !t.used && t.state==1);guards();
    }
    for(unsigned at=1;at<=2;at++){
        struct mv7_table t={0};init(&t,0x40000,0x80000,4);
        CHECK(mv7_map(&t,0,0x100000,4096,0)==0);
        struct sync_model sm={.fail=at};struct mv7_sync s={&sm,sync_fn,barrier};uint32_t out=0xdeadbeef;
        CHECK(mv7_seal(&t,&s,&out)==MV7_SYNC && t.state==3 && out==0xdeadbeef && sm.calls==at);
        CHECK(mv7_map(&t,0,0,4096,0)==MV7_STATE);
    }
    {
        struct mv7_table t={0};init(&t,0x40000,0x80000,4);
        uint64_t p=17;CHECK(mv7_translate(&t,0,&p)==MV7_RANGE && p==17);
        root[1]=1;CHECK(mv7_map(&t,0,0,4096,0)==MV7_CORRUPT && t.state==3);
    }
    {
        struct mv7_table t={0};
        CHECK(mv7_init(&t,root+1,0x40000,root+2,0x80000,4)==MV7_RANGE);
        CHECK(mv7_init(&t,root+1,0x40000,pool+1,0x40000,4)==MV7_RANGE);
        CHECK(mv7_init(&t,root+1,0x40001,pool+1,0x80000,4)==MV7_ARGUMENT);
        CHECK(mv7_init(&t,root+1,(1ull<<35),pool+1,0x80000,4)==MV7_RANGE);
        CHECK(!t.state);
    }
    printf("%u ARM_V7S table checks passed against pinned Android reference encoders\n",checks);
    return 0;
}
