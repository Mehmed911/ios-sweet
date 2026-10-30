#include "mt6897_ufs_platform.h"
#include "mt6897_ufs_dma.h"
#ifdef MT6897_MODEL_FREESTANDING
#include <stddef.h>
void model_assert_fail(const char *,unsigned) __attribute__((noreturn));
void *memcpy(void *,const void *,size_t);
int memcmp(const void *,const void *,size_t);
int printf(const char *,...);
#define assert(v) ((v)?(void)0:model_assert_fail(#v,__LINE__))
#else
#include <assert.h>
#include <stdio.h>
#include <string.h>
#endif

static unsigned checks;
#define CHECK(v) do { checks++; assert(v); } while(0)
struct event { unsigned kind; uint64_t a,b,c; };
enum { E_SIP=1,E_WRITE,E_READ,E_BARRIER,E_DELAY,E_RESET };
struct power_model {
    struct event e[256];
    unsigned count,calls,fail_at,reads,ack_after;
    uint64_t tick;
    int permitted,frozen,ignored_request,fail_cleanup;
};
static int event(struct power_model *m,unsigned kind,uint64_t a,uint64_t b,uint64_t c) {
    assert(m->count<256);
    m->e[m->count++]=(struct event){kind,a,b,c};
    return ++m->calls==m->fail_at?-1:0;
}
static int pauth(void *v,uint32_t mask) { assert(mask==MP_REQUIRED); return ((struct power_model *)v)->permitted; }
static int psip(void *v,const struct mp_sip_request *r) {
    assert(r->x[0]==0xc2000276u);
    for(unsigned i=4;i<8;i++) assert(r->x[i]==0);
    int result=event(v,E_SIP,r->x[1],r->x[2],r->x[3]);
    if(((struct power_model *)v)->fail_cleanup && r->x[1]==8 && !r->x[2] && r->x[3]==1)
        return -1;
    return result;
}
static int pwrite(void *v,uint32_t offset,uint32_t value) {
    assert(offset==0x144 && value==1);
    return event(v,E_WRITE,offset,value,0);
}
static int pread(void *v,uint32_t offset,uint32_t *value) {
    struct power_model *m=v;
    assert(offset==0x144);
    int r=event(m,E_READ,offset,0,0);
    *value=m->ignored_request?0:(++m->reads>=m->ack_after?3:1);
    return r;
}
static void pbarrier(void *v) {
    struct power_model *m=v;
    assert(m->count<256);
    m->e[m->count++]=(struct event){E_BARRIER,0,0,0};
}
static uint64_t ptime(void *v) { return ((struct power_model *)v)->tick; }
static int pdelay(void *v,uint32_t us) {
    struct power_model *m=v;
    int r=event(m,E_DELAY,us,0,0);
    if(!m->frozen) m->tick+=us;
    return r;
}
static int preset(void *v,unsigned id,int asserted) {
    assert(id<=2 && (asserted==0 || asserted==1));
    return event(v,E_RESET,id,(unsigned)asserted,0);
}
static struct mp_ops pops(struct power_model *m) {
    return (struct mp_ops){m,pauth,psip,pread,pwrite,pbarrier,ptime,pdelay,preset};
}
static struct mp_profile profile(void) { return (struct mp_profile){1,1,0,MP_REQUIRED}; }
static void expect(struct power_model *m,unsigned i,unsigned k,uint64_t a,uint64_t b,uint64_t c) {
    CHECK(i<m->count);
    CHECK(m->e[i].kind==k && m->e[i].a==a && m->e[i].b==b && m->e[i].c==c);
}
static void power_tests(void) {
    for(unsigned id=0;id<3;id++) for(int a=0;a<=1;a++) {
        struct mp_reset_register r={0};
        CHECK(mp_reset_register(id,a,&r)==0);
        CHECK(r.bank==0x112bb000 && r.offset==(a?0x48u:0x4cu) && r.mask==(1u<<id));
    }
    struct mp_reset_register untouched={7,8,9};
    CHECK(mp_reset_register(3,1,&untouched)==MP_ARGUMENT && untouched.bank==7);
    CHECK(mp_reset_register(0,2,&untouched)==MP_ARGUMENT && untouched.offset==8);
    CHECK(mp_reset_register(0,1,NULL)==MP_ARGUMENT);
    struct power_model ok={.permitted=1,.ack_after=3};
    struct mp_power p={0}; struct mp_ops o=pops(&ok); struct mp_profile c=profile();
    CHECK(mp_bind(&p,&c,&o)==0 && !ok.count);
    CHECK(mp_prepare(&p)==0 && p.state==MP_PREPARED && p.step==MP_REF_POST);
    /* Expected events are fixed independently from the implementation:
     * no VA09 (absent in this DTB), no legacy PHY register/clock operations.
     */
    expect(&ok,0,E_SIP,512,0,0); expect(&ok,1,E_SIP,512,1,0);
    expect(&ok,2,E_SIP,8,1,0); expect(&ok,3,E_WRITE,0x144,1,0);
    expect(&ok,4,E_BARRIER,0,0,0); expect(&ok,5,E_READ,0x144,0,0);
    expect(&ok,6,E_DELAY,100,0,0); expect(&ok,7,E_READ,0x144,0,0);
    expect(&ok,8,E_DELAY,100,0,0); expect(&ok,9,E_READ,0x144,0,0);
    expect(&ok,10,E_DELAY,32,0,0); expect(&ok,11,E_SIP,8,1,1);
    CHECK(ok.count==12 && ok.tick==232);
    unsigned prepared_calls=ok.calls;
    CHECK(mp_reset_host(&p)==0 && p.state==MP_RESET_DONE);
    expect(&ok,12,E_RESET,2,1,0); expect(&ok,13,E_RESET,1,1,0);
    expect(&ok,14,E_RESET,0,1,0); expect(&ok,15,E_DELAY,100,0,0);
    expect(&ok,16,E_RESET,0,0,0); expect(&ok,17,E_RESET,1,0,0);
    expect(&ok,18,E_RESET,2,0,0); CHECK(ok.count==19);
    CHECK(mp_prepare(&p)==MP_STATE && mp_reset_host(&p)==MP_STATE && ok.count==19);

    for(unsigned bit=0;bit<7;bit++) {
        struct power_model m={.permitted=1,.ack_after=1}; struct mp_power x={0};
        struct mp_profile bad=profile(); bad.prerequisites&=~(1u<<bit);
        struct mp_ops ops=pops(&m);
        CHECK(mp_bind(&x,&bad,&ops)==MP_UNVERIFIED && !m.count);
    }
    for(unsigned kind=0;kind<3;kind++) {
        struct power_model m={.permitted=1}; struct mp_power x={0};
        struct mp_profile bad=profile(); struct mp_ops ops=pops(&m);
        if(kind==0) bad.mphy_version=0;
        if(kind==1) bad.rtff_mtcmos=0;
        if(kind==2) bad.va09_supported=1;
        CHECK(mp_bind(&x,&bad,&ops)==MP_UNVERIFIED && !m.count);
    }
    {
        struct power_model m={.ack_after=1}; struct mp_power x={0}; struct mp_ops ops=pops(&m);
        CHECK(mp_bind(&x,&c,&ops)==0);
        CHECK(mp_reset_host(&x)==MP_STATE && !m.count);
        CHECK(mp_prepare(&x)==MP_UNVERIFIED && !m.count && x.state==MP_BOUND);
        m.permitted=1; CHECK(mp_prepare(&x)==0);
        m.permitted=0; unsigned before=m.count;
        CHECK(mp_reset_host(&x)==MP_UNVERIFIED && m.count==before);
    }
    /* Every fallible operation in the successful prepare and reset trace. */
    for(unsigned at=1;at<=prepared_calls+7;at++) {
        struct power_model m={.permitted=1,.ack_after=3,.fail_at=at};
        struct mp_power x={0}; struct mp_ops ops=pops(&m);
        CHECK(mp_bind(&x,&c,&ops)==0);
        int r=mp_prepare(&x);
        if(at>prepared_calls) { CHECK(r==0); r=mp_reset_host(&x); }
        CHECK(r==MP_IO && x.state==MP_FAULTED && m.calls==at);
        unsigned before=m.count;
        CHECK(mp_prepare(&x)==MP_STATE && mp_reset_host(&x)==MP_STATE);
        CHECK(mp_bind(&x,&c,&ops)==MP_STATE && m.count==before);
    }
    /* Timeout with a progressing clock, frozen clock, and ignored write.
     * All must remain finite, notify REFCLK off/POST once, and latch failure.
     */
    for(unsigned mode=0;mode<3;mode++) {
        struct power_model m={.permitted=1,.ack_after=1000,.frozen=mode==1,.ignored_request=mode==2};
        struct mp_power x={0}; struct mp_ops ops=pops(&m);
        CHECK(mp_bind(&x,&c,&ops)==0);
        CHECK(mp_prepare(&x)==MP_TIMEOUT && x.state==MP_FAULTED);
        CHECK(m.count<80 && m.reads<=32);
        expect(&m,m.count-1,E_SIP,8,0,1);
        unsigned before=m.count;
        CHECK(mp_prepare(&x)==MP_STATE && m.count==before);
    }
    {
        struct power_model m={.permitted=1,.ack_after=1000,.fail_cleanup=1};
        struct mp_power x={0}; struct mp_ops ops=pops(&m);
        CHECK(mp_bind(&x,&c,&ops)==0);
        CHECK(mp_prepare(&x)==MP_IO && x.state==MP_FAULTED);
        expect(&m,m.count-1,E_SIP,8,0,1);
    }
    CHECK(mp_prepare(NULL)==MP_ARGUMENT && mp_reset_host(NULL)==MP_ARGUMENT);
}

_Alignas(4096) static unsigned char cpu_memory[8192];
struct dma_model {
    unsigned maps,unmaps,to_device,to_cpu,barriers,idles;
    int permitted,idle,fail_map,fail_device,fail_cpu,fail_unmap;
    uint64_t bus,cookie;
    unsigned char device_memory[8192];
};
static int dauth(void *v,const struct md_config *c) {
    assert(c->cpu==cpu_memory); return ((struct dma_model *)v)->permitted;
}
static int didle(void *v) { struct dma_model *m=v; m->idles++; return m->idle; }
static int dmap(void *v,uint64_t physical,uint64_t bytes,enum md_direction direction,uint64_t *bus,uint64_t *cookie) {
    struct dma_model *m=v; m->maps++;
    assert(physical==0x100000000ull && bytes==8192 && direction>=1 && direction<=3);
    *bus=m->bus; *cookie=m->cookie;
    return m->fail_map?-1:0;
}
static int dsync_device(void *v,void *cpu,uint64_t bytes,enum md_direction d) {
    struct dma_model *m=v; m->to_device++;
    assert(cpu==cpu_memory && bytes==8192 && m->idle==1);
    if(m->fail_device) return -1;
    if(d!=MD_FROM_DEVICE) memcpy(m->device_memory,cpu,(size_t)bytes);
    return 0;
}
static int dsync_cpu(void *v,void *cpu,uint64_t bytes,enum md_direction d) {
    struct dma_model *m=v; m->to_cpu++;
    assert(cpu==cpu_memory && bytes==8192 && m->idle==1);
    if(m->fail_cpu) return -1;
    if(d!=MD_TO_DEVICE) memcpy(cpu,m->device_memory,(size_t)bytes);
    return 0;
}
static void dbarrier(void *v) { ((struct dma_model *)v)->barriers++; }
static int dunmap(void *v,uint64_t cookie,uint64_t bus,uint64_t bytes,enum md_direction d) {
    struct dma_model *m=v; m->unmaps++;
    assert(cookie==m->cookie && bus==m->bus && bytes==8192 && m->idle==1 && d>=1 && d<=3);
    return m->fail_unmap?-1:0;
}
static struct md_ops dops(struct dma_model *m) {
    return (struct md_ops){m,dauth,didle,dmap,dsync_device,dsync_cpu,dbarrier,dunmap};
}
static struct md_config dconfig(void) {
    return (struct md_config){cpu_memory,0x100000000ull,8192,0x20000000,0x30000000,64,4096,32,
                             MD_VERIFIED_IOMMU,MD_BIDIRECTIONAL};
}
static struct dma_model dmodel(void) {
    return (struct dma_model){.permitted=1,.idle=1,.bus=0x20004000,.cookie=0x98765};
}
static void pinned(struct md_pool *p,struct dma_model *m) {
    unsigned before=m->maps+m->unmaps+m->to_cpu+m->to_device;
    CHECK(md_map(p)==MD_STATE && md_for_cpu(p)==MD_STATE && md_for_device(p)==MD_STATE);
    CHECK(md_release(p)==MD_STATE && before==m->maps+m->unmaps+m->to_cpu+m->to_device);
}
static void dma_tests(void) {
    for(int route=1;route<=2;route++) for(int direction=1;direction<=3;direction++) {
        struct dma_model m=dmodel(); struct md_ops o=dops(&m); struct md_config c=dconfig();
        c.route=(enum md_route)route; c.direction=(enum md_direction)direction;
        struct md_pool p={0};
        for(unsigned i=0;i<sizeof(cpu_memory);i++) cpu_memory[i]=(unsigned char)(i*7);
        CHECK(md_bind(&p,&c,&o)==0 && !m.maps);
        CHECK(md_map(&p)==0 && p.state==MD_CPU && p.device!=p.config.physical);
        CHECK(p.device==0x20004000 && p.cookie==0x98765 && m.maps==1);
        CHECK(md_for_device(&p)==0 && p.state==MD_DEVICE && m.to_device==1 && m.barriers==1);
        if(direction!=MD_FROM_DEVICE) CHECK(!memcmp(cpu_memory,m.device_memory,sizeof(cpu_memory)));
        m.idle=0; unsigned sync=m.to_cpu;
        CHECK(md_for_cpu(&p)==MD_BUSY && p.state==MD_DEVICE && m.to_cpu==sync);
        CHECK(md_release(&p)==MD_STATE && !m.unmaps);
        m.device_memory[33]=0x63; m.idle=1;
        CHECK(md_for_cpu(&p)==0 && p.state==MD_CPU && m.to_cpu==1 && m.barriers==2);
        if(direction!=MD_TO_DEVICE) CHECK(cpu_memory[33]==0x63);
        CHECK(md_release(&p)==0 && m.unmaps==1 && p.state==MD_RELEASED);
        CHECK(md_bind(&p,&c,&o)==MD_STATE);
    }
    for(unsigned mode=0;mode<14;mode++) {
        struct dma_model m=dmodel(); struct md_ops o=dops(&m); struct md_config c=dconfig();
        struct md_pool p={0}; int expected=MD_ARGUMENT;
        switch(mode) {
        case 0: c.cpu=NULL; break;
        case 1: c.bytes=0; break;
        case 2: c.bytes=8191; break;
        case 3: c.physical=UINT64_MAX-4095; break;
        case 4: c.physical++; break;
        case 5: c.cpu=cpu_memory+1; break;
        case 6: c.cache_line=63; break;
        case 7: c.alignment=32; break;
        case 8: c.address_bits=65; break;
        case 9: c.direction=0; break;
        case 10: c.device_end=c.device_begin; break;
        case 11: o.sync_cpu=NULL; break;
        case 12: c.route=MD_UNKNOWN; expected=MD_UNVERIFIED; break;
        default: c.cpu=(void *)(UINTPTR_MAX-63); break;
        }
        CHECK(md_bind(&p,&c,&o)==expected && !m.maps && !m.idles);
    }
    for(unsigned mode=0;mode<5;mode++) {
        struct dma_model m=dmodel(); struct md_ops o=dops(&m); struct md_config c=dconfig();
        struct md_pool p={0};
        if(mode==0) m.bus=0x1ffff000;       /* Below domain aperture */
        if(mode==1) m.bus=0x2ffff000;       /* Crosses aperture end */
        if(mode==2) m.bus++;               /* Misaligned mapping */
        if(mode==3) { m.bus=0xfffff000; c.device_end=0x200000000ull; } /* crosses 32-bit mask */
        if(mode==4) { m.bus=UINT64_MAX-4095; c.device_end=UINT64_MAX; c.address_bits=64; }
        CHECK(md_bind(&p,&c,&o)==0);
        CHECK(md_map(&p)==MD_RANGE && p.state==MD_POISONED && m.maps==1 && !m.unmaps);
        pinned(&p,&m);
    }
    for(unsigned mode=0;mode<4;mode++) {
        struct dma_model m=dmodel(); struct md_ops o=dops(&m); struct md_config c=dconfig();
        struct md_pool p={0};
        m.fail_map=mode==0; m.fail_device=mode==1; m.fail_cpu=mode==2; m.fail_unmap=mode==3;
        CHECK(md_bind(&p,&c,&o)==0);
        int r=md_map(&p);
        if(mode>=1) { CHECK(r==0); r=md_for_device(&p); }
        if(mode>=2) { CHECK(r==0); r=md_for_cpu(&p); }
        if(mode>=3) { CHECK(r==0); r=md_release(&p); }
        CHECK(r==MD_IO && p.state==MD_POISONED);
        CHECK(m.unmaps==(mode==3?1u:0u));
        pinned(&p,&m);
    }
    {
        struct dma_model m=dmodel(); struct md_ops o=dops(&m); struct md_config c=dconfig();
        struct md_pool p={0};
        CHECK(md_bind(&p,&c,&o)==0);
        m.permitted=0; CHECK(md_map(&p)==MD_UNVERIFIED && !m.idles && !m.maps);
        m.permitted=1; m.idle=0; CHECK(md_map(&p)==MD_BUSY && !m.maps);
        m.idle=1; CHECK(md_map(&p)==0); m.permitted=0;
        CHECK(md_for_device(&p)==MD_UNVERIFIED && !m.to_device);
        CHECK(md_release(&p)==MD_UNVERIFIED && !m.unmaps);
        m.permitted=1; CHECK(md_for_device(&p)==0); m.permitted=0;
        CHECK(md_for_cpu(&p)==MD_UNVERIFIED && p.state==MD_POISONED && !m.to_cpu);
        pinned(&p,&m);
    }
    {
        struct dma_model m=dmodel(); struct md_ops o=dops(&m); struct md_config c=dconfig();
        struct md_pool p={0}; CHECK(md_bind(&p,&c,&o)==0 && md_map(&p)==0);
        m.idle=0;
        CHECK(md_for_device(&p)==MD_BUSY && p.state==MD_CPU && !m.to_device);
        CHECK(md_release(&p)==MD_BUSY && !m.unmaps);
        m.idle=1; CHECK(md_for_device(&p)==0);
        CHECK(md_for_device(&p)==MD_STATE && m.to_device==1);
        CHECK(md_for_cpu(&p)==0 && md_release(&p)==0);
    }
    for(int state=0;state<2;state++) {
        struct dma_model m=dmodel(); struct md_ops o=dops(&m); struct md_config c=dconfig();
        struct md_pool p={0}; CHECK(md_bind(&p,&c,&o)==0 && md_map(&p)==0);
        if(state) CHECK(md_for_device(&p)==0);
        md_poison(&p); CHECK(p.state==MD_POISONED && !m.unmaps); pinned(&p,&m);
    }
    CHECK(md_bind(NULL,NULL,NULL)==MD_ARGUMENT && md_map(NULL)==MD_ARGUMENT);
    CHECK(md_for_device(NULL)==MD_ARGUMENT && md_for_cpu(NULL)==MD_ARGUMENT && md_release(NULL)==MD_ARGUMENT);
}
int main(void) {
    power_tests(); unsigned power=checks;
    dma_tests();
    printf("%u power-sequence checks, %u DMA-ownership checks passed; callbacks/models only\n",
           power,checks-power);
    return 0;
}
