#include "duchamp_gic_boot.h"
#include <stddef.h>
#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *,unsigned) __attribute__((noreturn));
int printf(const char *,...);void *memset(void *,int,unsigned long);
#define assert(x) ((x)?(void)0:model_assert_fail(#x,__LINE__))
#else
#include <assert.h>
#include <stdio.h>
#include <string.h>
#endif
static unsigned checks;
#define CHECK(x) do{checks++;assert(x);}while(0)
struct model {uint64_t offset[8],typer[8],seen[8],tick;unsigned count,reads64,reads32,writes,
    barriers,clock,clear_at,fail_read,fail_write,ignore_write,ids;uint32_t waker,written,pidr;};
static struct model m;
static int read64(void *ctx,uint64_t off,uint64_t *value) {
    struct model *x=ctx;CHECK(x->reads64<8);x->seen[x->reads64++]=off;
    if(x->fail_read)return -1;
    for(unsigned i=0;i<x->count;i++)if(x->offset[i]+8==off){*value=x->typer[i];return 0;}
    return -1;
}
static int read32(void *ctx,uint64_t off,uint32_t *value) {
    struct model *x=ctx;
    if(off==0xffe8){x->ids++;*value=x->pidr;return 0;}
    CHECK(off==0x14);x->reads32++;
    if(x->fail_read && x->reads32==x->fail_read)return -1;
    if(x->clear_at && x->reads32>=x->clear_at)x->waker&=~4u;
    *value=x->waker;return 0;
}
static int write32(void *ctx,uint64_t off,uint32_t value) {
    struct model *x=ctx;CHECK(off==0x14);x->writes++;x->written=value;
    if(x->fail_write)return -1;
    if(!x->ignore_write)x->waker=value;
    return 0;
}
static uint64_t now(void *ctx){struct model *x=ctx;uint64_t t=x->tick;if(x->clock)x->tick+=x->clock==2?UINT64_MAX:1;return t;}
static void barrier(void *ctx){((struct model *)ctx)->barriers++;}
static struct dgic_io io={&m,read32,read64,write32,now,barrier};
static void reset(void){memset(&m,0,sizeof(m));m.pidr=0x3b;}
static uint64_t type(uint64_t mpidr,unsigned flags){return (uint64_t)dgic_affinity(mpidr)<<32|flags;}
static void scans(void) {
    CHECK(dgic_regions_valid(0,0xc400000,0x40000,0xc440000,0x200000));
    CHECK(dgic_regions_valid(0x1000000,0xb400000,0x40000,0xb440000,0x200000));
    CHECK(!dgic_regions_valid(UINT64_MAX,1,0x10000,0x20000,0x20000));
    CHECK(!dgic_regions_valid(0,0xc400001,0x40000,0xc440000,0x200000));
    CHECK(!dgic_regions_valid(0,0xc400000,0x50000,0xc440000,0x200000));
    CHECK(!dgic_regions_valid(0,0xc400000,0x40000,0xc440000,0x10000));
    CHECK(!dgic_regions_valid(0,0xc400000,0x40000,0xc440000,UINT64_MAX));
    CHECK(dgic_affinity(UINT64_C(0x2a00030042))==0x2a030042u);
    uint64_t found=0xdead;
    reset();m.count=3;
    for(unsigned i=0;i<3;i++){m.offset[i]=i*0x20000;m.typer[i]=type(i<<8,i==2?16:0);}
    CHECK(dgic_find(&io,0x60000,0,0x200,8,&found)==0 && found==0x40000 && m.reads64==3);
    reset();m.count=2;m.offset[1]=0x40000;m.typer[0]=type(1,2);m.typer[1]=type(0,16);
    CHECK(dgic_find(&io,0x60000,0,0,8,&found)==0 && found==0x40000 && m.seen[1]==0x40008);
    reset();m.count=2;m.offset[1]=0x20000;m.typer[0]=type(0x30042,0);m.typer[1]=type(UINT64_C(0x2a00030042),16);
    CHECK(dgic_find(&io,0x40000,0,UINT64_C(0x2a00030042),8,&found)==0 && found==0x20000);
    reset();m.count=2;m.offset[1]=0x80000;m.typer[0]=type(1,0);m.typer[1]=type(0,16);
    CHECK(dgic_find(&io,0xa0000,0x80000,0,8,&found)==0 && found==0x80000);
    for(unsigned mode=0;mode<7;mode++) {
        reset();found=0xdead;m.count=2;m.offset[1]=0x20000;m.typer[0]=type(1,0);m.typer[1]=type(0,16);
        if(mode==0)m.typer[0]|=16;
        if(mode==1)m.fail_read=1;
        if(mode==2)m.typer[0]|=2;
        int r=dgic_find(&io,mode==3?0x10001:mode==4?0x20000:0x40000,mode==2?0x20000:0,0,mode==5?1:mode==6?0:8,&found);
        CHECK(r==(mode==0||mode==4?DGIC_NOT_FOUND:mode==1?DGIC_IO:mode==5?DGIC_LIMIT:mode==6?DGIC_ARGUMENT:DGIC_RANGE));
        CHECK(found==0xdead && m.reads64<=1);
    }
    reset();m.count=1;m.typer[0]=type(0,2);
    CHECK(dgic_find(&io,0x20000,0,0,8,&found)==DGIC_RANGE);
    CHECK(dgic_find(NULL,0x20000,0,0,8,&found)==DGIC_ARGUMENT);
    CHECK(dgic_find(&io,0x20000,0,0,DGIC_MAX_FRAMES+1,&found)==DGIC_ARGUMENT);
    reset();m.count=1;m.typer[0]=type(0,16);m.pidr=0;
    CHECK(dgic_find(&io,0x20000,0,0,8,&found)==DGIC_ID && !m.reads64 && !m.writes);
    m.pidr=0x40;
    CHECK(dgic_find(&io,0x20000,0,0,8,&found)==0 && found==0);
}
static void wakes(void) {
    struct dgic_wake_result d;
    reset();m.waker=0x80;
    CHECK(dgic_wake(&io,0x20000,0,100,8,&d)==0 && d.reads==1 && !d.writes && !m.barriers);
    reset();m.waker=0x86;m.clear_at=3;
    CHECK(dgic_wake(&io,0x20000,0,100,8,&d)==0);
    CHECK(d.initial==0x86 && d.last==0x80 && d.reads==3 && d.writes==1 && m.written==0x84 && m.barriers==1);
    reset();m.waker=0x82;
    CHECK(dgic_wake(&io,0x20000,0,100,8,&d)==0 && d.reads==2 && m.written==0x80);
    reset();m.waker=4;m.clear_at=2;
    CHECK(dgic_wake(&io,0x20000,0,100,8,&d)==0 && !d.writes && !m.barriers);
    for(unsigned mode=0;mode<5;mode++) {
        reset();m.waker=6;m.clock=mode==1||mode==3?1:mode==2?2:0;
        m.tick=mode==3?UINT64_MAX-1:mode==2?100:0;
        if(mode==4){m.waker=2;m.ignore_write=1;}
        CHECK(dgic_wake(&io,0x20000,0,3,8,&d)==DGIC_TIMEOUT);
        CHECK(d.timeout_cause==((mode>0&&mode<4)?DGIC_WAIT_CLOCK:DGIC_WAIT_POLLS));
        CHECK(d.reads<=8 && d.writes==1 && m.barriers==1);
    }
    reset();m.waker=6;
    CHECK(dgic_wake(&io,0x20000,0,0,3,&d)==DGIC_TIMEOUT && d.timeout_cause==DGIC_WAIT_POLLS && d.reads==3);
    for(unsigned failure=1;failure<4;failure++) {
        reset();m.waker=6;
        if(failure==1)m.fail_write=1;else m.fail_read=failure==2?1:2;
        CHECK(dgic_wake(&io,0x20000,0,100,8,&d)==DGIC_IO);
        CHECK(d.reads<3 && d.writes<=1 && m.barriers==(failure==3?1u:0u));
    }
    reset();
    CHECK(dgic_wake(&io,0x20000,0,100,0,&d)==DGIC_ARGUMENT);
    CHECK(dgic_wake(&io,0x20000,0,100,DGIC_MAX_POLLS+1,&d)==DGIC_ARGUMENT);
    CHECK(dgic_wake(&io,0x20000,1,100,8,&d)==DGIC_RANGE);
    CHECK(dgic_wake(&io,0x20000,0x20000,100,8,&d)==DGIC_RANGE);
    CHECK(dgic_wake(&io,0x20000,0,UINT64_MAX,8,&d)==DGIC_ARGUMENT);
    CHECK(!m.reads32 && !m.writes && !m.barriers);
}
#ifdef MT6897_MODEL_FREESTANDING
static int actual32(void *c,uint64_t o,uint32_t *v){(void)c;*v=*(volatile uint32_t *)(UINT64_C(0x80a0000)+o);return 0;}
static int actual64(void *c,uint64_t o,uint64_t *v){(void)c;*v=*(volatile uint64_t *)(UINT64_C(0x80a0000)+o);return 0;}
static int actual_write(void *c,uint64_t o,uint32_t v){(void)c;*(volatile uint32_t *)(UINT64_C(0x80a0000)+o)=v;return 0;}
static uint64_t actual_ns(void *c){(void)c;uint64_t t;__asm__ volatile("mrs %0,cntvct_el0":"=r"(t));return t*16;}
static void actual_barrier(void *c){(void)c;__asm__ volatile("dsb sy":::"memory");}
static void actual_gic(void) {
    struct dgic_io real={0,actual32,actual64,actual_write,actual_ns,actual_barrier};
    uint64_t mpidr,found=0xdead;__asm__ volatile("mrs %0,mpidr_el1":"=r"(mpidr));
    CHECK(dgic_find(&real,0x20000,0,mpidr,8,&found)==0 && found==0);
    struct dgic_wake_result d;
    CHECK(dgic_wake(&real,0x20000,found,1000000000,1000,&d)==0);
    CHECK(!(d.last&6) && d.writes<=1 && d.reads<=1000);
    CHECK(dgic_wake(&real,0x20000,found,1000000000,1000,&d)==0 && !d.writes);
    printf("4 actual QEMU GICR checks passed\n");
}
#endif
int main(void){scans();wakes();printf("%u bounded GIC bootstrap checks passed\n",checks);
#ifdef MT6897_MODEL_FREESTANDING
    actual_gic();
#endif
    return 0;
}
