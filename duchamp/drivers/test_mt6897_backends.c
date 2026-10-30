#include "mt6897_backends.h"
#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *,unsigned) __attribute__((noreturn));
int printf(const char *,...);
void *memcpy(void *,const void *,size_t);
#define assert(v) ((v)?(void)0:model_assert_fail(#v,__LINE__))
#else
#include <assert.h>
#include <stdio.h>
#include <string.h>
#endif
static unsigned checks;
#define CHECK(v) do { checks++; assert(v); } while(0)
struct bus {
    unsigned state,calls,fail_at,commands,clears,auth_calls;
    uint32_t wdata,rdata,last_command;
    uint64_t tick;
    int permitted,stall,frozen,init,ignore_write,locked;
    unsigned lock_calls,unlock_calls;
    uint8_t reg[2][65536];
};
static struct bus bm;
static unsigned slot(unsigned sid) { assert(sid==4 || sid==8); return sid==4?0:1; }
static int step(struct bus *b) { return ++b->calls==b->fail_at?-1:0; }
static int bauth(void *v,unsigned r) { struct bus *b=v; assert(r==MB_PMIF);b->auth_calls++;return b->permitted; }
static int bread(void *v,unsigned bank,uint32_t off,uint32_t *value) {
    struct bus *b=v; assert(bank==0); if(step(b)) return -1;
    if(off==0) *value=(unsigned)b->init;
    else if(off==0x8a8) *value=b->state<<1;
    else { assert(off==0x894); *value=b->rdata; }
    return 0;
}
static int bwrite(void *v,unsigned bank,uint32_t off,uint32_t value) {
    struct bus *b=v; assert(bank==0); if(step(b)) return -1;
    if(off==0x884) b->wdata=value;
    else if(off==0x8a4) { assert(value==1);b->clears++;b->state=0; }
    else {
        assert(off==0x880 && (value>>30)==3);
        unsigned sid=(value>>24)&15,bytes=((value>>16)&3)+1,a=value&65535;
        assert(a+bytes<=65536 && b->state==0);
        unsigned index=slot(sid),write=(value>>29)&1;
        b->last_command=value; b->commands++;
        if(b->stall) { b->state=2;return 0; }
        if(write) {
            for(unsigned i=0;i<bytes;i++) if(!b->ignore_write) {
                uint8_t x=(uint8_t)(b->wdata>>(i*8));
                if(sid==4 && a+i==0x1b40)
                    assert(b->reg[0][0x39e]==0x9c && b->reg[0][0x39f]==0x9c);
                if(sid==8 && a+i==0x1441) b->reg[index][0x1440]|=x;
                else b->reg[index][a+i]=x;
            }
            b->state=0;
        } else {
            b->rdata=0;
            for(unsigned i=0;i<bytes;i++) b->rdata|=(uint32_t)b->reg[index][a+i]<<(i*8);
            b->state=6;
        }
    }
    return 0;
}
static void barrier(void *v) { (void)v; }
static uint64_t btime(void *v) { return ((struct bus *)v)->tick; }
static int bdelay(void *v,uint32_t n) { struct bus *b=v; if(step(b)) return -1; if(!b->frozen)b->tick+=n;return 0; }
static struct mb_io bio(struct bus *b) { return (struct mb_io){b,bauth,bread,bwrite,barrier,btime,bdelay}; }
static void fresh_bus(void) {
    for(unsigned i=0;i<2;i++) for(unsigned j=0;j<65536;j++) bm.reg[i][j]=0;
    bm.state=0;bm.calls=0;bm.fail_at=0;bm.commands=0;bm.clears=0;bm.auth_calls=0;
    bm.tick=0;bm.permitted=1;bm.init=1;bm.stall=0;bm.frozen=0;bm.ignore_write=0;
    bm.locked=0;bm.lock_calls=0;bm.unlock_calls=0;
}
static void bus_tests(void) {
    for(unsigned n=1;n<=4;n++) {
        fresh_bus();struct mb_pmif p={0};struct mb_io io=bio(&bm);
        CHECK(mb_pmif_bind(&p,&io,0)==0 && !bm.calls);
        uint8_t write[4]={0x12,0x34,0x56,0x78},read[6]={0xa5,0,0,0,0,0x5a};
        CHECK(mb_pmif_transfer(&p,4,0x39e,write,n,1)==0);
        CHECK(bm.last_command==(0xe400039eu|((n-1)<<16)));
        CHECK(mb_pmif_transfer(&p,4,0x39e,read+1,n,0)==0);
        for(unsigned i=0;i<n;i++) CHECK(read[i+1]==write[i]);
        CHECK(read[0]==0xa5 && read[5]==0x5a && bm.clears==1);
    }
    for(unsigned mode=0;mode<7;mode++) {
        fresh_bus();struct mb_pmif p={0};struct mb_io io=bio(&bm);uint8_t value=0x96;
        CHECK(mb_pmif_bind(&p,&io,0)==0);
        int result;
        if(mode==0) result=mb_pmif_transfer(&p,3,0,&value,1,0);
        else if(mode==1) result=mb_pmif_transfer(&p,4,65535,&value,2,0);
        else if(mode==2) result=mb_pmif_transfer(&p,4,0,&value,0,0);
        else if(mode==3) result=mb_pmif_transfer(&p,4,0,&value,5,0);
        else if(mode==4) result=mb_pmif_transfer(&p,4,0,&value,1,2);
        else if(mode==5) { bm.permitted=0;result=mb_pmif_transfer(&p,4,0,&value,1,0); }
        else { struct mb_pmif x={0}; result=mb_pmif_bind(&x,&io,1); }
        CHECK(result==(mode<5?MB_ARGUMENT:MB_UNVERIFIED));
        CHECK(!bm.calls && !bm.commands && value==0x96);
    }
    struct mb_io io;uint8_t x=0;
    for(int write=0;write<=1;write++) {
        fresh_bus();struct mb_pmif ok={0};io=bio(&bm);
        CHECK(mb_pmif_bind(&ok,&io,0)==0 && mb_pmif_transfer(&ok,8,0x144d,&x,1,write)==0);
        unsigned operations=bm.calls;
        for(unsigned at=1;at<=operations;at++) {
            fresh_bus();bm.fail_at=at;struct mb_pmif p={0};io=bio(&bm);uint8_t out=0xa5;
            CHECK(mb_pmif_bind(&p,&io,0)==0);
            CHECK(mb_pmif_transfer(&p,8,0x144d,&out,1,write)==MB_IO && p.state==2 && out==0xa5);
            unsigned before=bm.calls;CHECK(mb_pmif_transfer(&p,8,0,&out,1,0)==MB_STATE && before==bm.calls);
        }
    }
    for(unsigned mode=0;mode<4;mode++) {
        fresh_bus();bm.frozen=mode==0;bm.stall=mode<2;bm.state=mode==2?6:0;bm.init=mode==3?0:1;
        struct mb_pmif p={0};io=bio(&bm);x=0x66;CHECK(mb_pmif_bind(&p,&io,0)==0);
        CHECK(mb_pmif_transfer(&p,4,0,&x,1,0)==(mode==3?MB_UNVERIFIED:MB_TIMEOUT));
        CHECK(p.state==2 && x==0x66 && bm.calls<2100);
        CHECK(bm.clears==0); /* No inherited reply stolen. */
    }
}
struct pmic_context { struct mb_pmif link; int permit,fail_key,fail_selector,fail_relock; unsigned key_attempts,relocks; };
static int pa(void *v,unsigned rail,int write) { struct pmic_context *c=v;assert(rail<2 && write==1);return c->permit; }
static int plock(void *v) { (void)v;assert(!bm.locked);bm.locked=1;bm.lock_calls++;return 0; }
static void punlock(void *v) { (void)v;assert(bm.locked);bm.locked=0;bm.unlock_calls++; }
static int pr(void *v,unsigned sid,uint16_t a,void *buf,size_t n) {
    struct pmic_context *c=v;assert(bm.locked);return mb_pmif_transfer(&c->link,sid,a,buf,n,0);
}
static int pw(void *v,unsigned sid,uint16_t a,const void *buf,size_t n) {
    struct pmic_context *c=v;const uint8_t *bytes=buf;assert(bm.locked);
    if(a==0x39e && n==2) {
        if(bytes[0]) { c->key_attempts++; if(c->fail_key) return -1; }
        else { c->relocks++; if(c->fail_relock) return -1; }
    }
    if(a==0x1b40 && c->fail_selector) return -1;
    return mb_pmif_transfer(&c->link,sid,a,(void *)buf,n,1);
}
static int pd(void *v,uint32_t us) { (void)v;return bdelay(&bm,us); }
static struct mb_pmic_ops po(struct pmic_context *c) { return (struct mb_pmic_ops){c,pa,plock,punlock,pr,pw,pd}; }
static void pmic_setup(struct pmic_context *c,struct mb_pmic *p) {
    fresh_bus();c->permit=1;struct mb_io io=bio(&bm);struct mb_pmic_ops o=po(c);
    CHECK(mb_pmif_bind(&c->link,&io,0)==0 && mb_pmic_bind(p,&o)==0);
}
static void pmic_tests(void) {
    for(unsigned trap=0;trap<2;trap++) {
        struct pmic_context c={0};struct mb_pmic p={0};pmic_setup(&c,&p);
        bm.reg[0][0x36]=(uint8_t)trap;bm.reg[0][0x1b40]=0xa5;bm.reg[0][0x1b4b]=0x77;
        CHECK(mb_pmic_voltage(&p,MB_VEMC,3000000)==0);
        CHECK(bm.reg[0][0x1b40]==(trap?0xb5:0xab));
        CHECK(bm.reg[0][0x1b4b]==0x77 && !bm.reg[0][0x39e] && !bm.reg[0][0x39f]);
        CHECK(c.key_attempts==1 && c.relocks==1 && !bm.locked && bm.lock_calls==bm.unlock_calls);
        unsigned before=bm.commands;CHECK(mb_pmic_voltage(&p,MB_VEMC,3000000)==0);
        CHECK(bm.commands==before+2 && c.key_attempts==1);
        CHECK(mb_pmic_voltage(&p,MB_VEMC,3100001)==MB_RANGE);
    }
    for(unsigned mode=0;mode<4;mode++) {
        struct pmic_context c={0};struct mb_pmic p={0};pmic_setup(&c,&p);
        c.fail_key=mode==0;c.fail_selector=mode==1;c.fail_relock=mode==2;
        if(mode==3) bm.reg[0][0x36]=3;
        CHECK(mb_pmic_voltage(&p,MB_VEMC,3000000)==(mode==3?MB_UNVERIFIED:MB_IO));
        CHECK(p.state==2 && !bm.locked && bm.lock_calls==bm.unlock_calls);
        CHECK(mode==3?!c.key_attempts:c.relocks==1);
        unsigned before=bm.commands;CHECK(mb_pmic_enable(&p,0)==MB_STATE && before==bm.commands);
    }
    {
        struct pmic_context c={0};struct mb_pmic p={0};pmic_setup(&c,&p);
        CHECK(mb_pmic_voltage(&p,MB_VBUCK3,300000)==0 && bm.reg[1][0x144d]==48);
        CHECK(mb_pmic_voltage(&p,MB_VBUCK3,1187500)==0 && bm.reg[1][0x144d]==190);
        unsigned before=bm.commands;
        CHECK(mb_pmic_voltage(&p,MB_VBUCK3,1193750)==MB_RANGE && bm.commands==before);
        CHECK(mb_pmic_voltage(&p,MB_VBUCK3,300001)==MB_RANGE && bm.commands==before);
        bm.reg[0][0x1c23]=0xa0;bm.reg[1][0x1440]=0x81;
        CHECK(mb_pmic_enable(&p,MB_VEMC)==0 && bm.reg[0][0x1c23]==0xa1 && bm.tick==680);
        CHECK(mb_pmic_enable(&p,MB_VBUCK3)==0 && bm.reg[1][0x1440]==0x85 && bm.tick==936);
        CHECK(mb_pmic_enable(&p,MB_VBUCK3)==0 && bm.tick==936);
        c.permit=0;before=bm.commands;
        CHECK(mb_pmic_voltage(&p,0,3000000)==MB_UNVERIFIED && bm.commands==before);
    }
    {
        struct pmic_context c={0};struct mb_pmic p={0};pmic_setup(&c,&p);bm.ignore_write=1;
        CHECK(mb_pmic_enable(&p,MB_VEMC)==MB_IO && p.state==2 && !bm.locked);
    }
    struct pmic_context good={0};struct mb_pmic gp={0};pmic_setup(&good,&gp);
    CHECK(mb_pmic_voltage(&gp,MB_VEMC,3000000)==0);
    unsigned operations=bm.calls;
    for(unsigned at=1;at<=operations;at++) {
        struct pmic_context c={0};struct mb_pmic p={0};pmic_setup(&c,&p);bm.fail_at=at;
        CHECK(mb_pmic_voltage(&p,MB_VEMC,3000000)==MB_IO && p.state==2);
        CHECK(!bm.locked && bm.lock_calls==bm.unlock_calls);
        CHECK(bm.calls==at); /* Transport poisoning refuses relock I/O; the
                            * PMIC driver still attempts it through pw(). */
    }
}
struct firmware_model { unsigned calls; int permit,confirm,error; };
static int fa(void *v,const uint64_t q[8]) { (void)q;return ((struct firmware_model *)v)->permit; }
static int fc(void *v,const uint64_t q[8],uint64_t reply[4]) {
    struct firmware_model *f=v; f->calls++;
    reply[0]=0;reply[1]=q[1];reply[2]=q[2];reply[3]=0x8877665544332211ull;
    return f->error;
}
static int fv(void *v,const uint64_t q[8],const uint64_t reply[4]) {
    (void)q;assert(reply[0]==0);return ((struct firmware_model *)v)->confirm;
}
static void firmware_tests(void) {
    for(unsigned mode=0;mode<5;mode++) {
        struct firmware_model m={.permit=mode!=0,.confirm=mode==1?1:mode==4?-1:0,.error=mode==3};
        struct mb_fw_ops o={&m,fa,fc,fv};struct mb_firmware f={0};
        uint64_t q[8]={0xc2000276u,512,0,0,0,0,0,0},r[4]={7,8,9,10};
        CHECK(mb_firmware_bind(&f,&o)==0);
        CHECK(mb_firmware_ufs(&f,q,r)==(mode==0||mode==2?MB_UNVERIFIED:mode==1?0:MB_IO));
        CHECK(m.calls==(mode==0?0u:1u));
        if(mode==1) CHECK(r[3]==0x8877665544332211ull);
        else CHECK(r[0]==7 && r[3]==10);
        if(mode>=2) CHECK(f.state==2 && mb_firmware_ufs(&f,q,r)==MB_STATE && m.calls==1);
    }
    for(unsigned index=0;index<8;index++) {
        struct firmware_model m={.permit=1,.confirm=1};struct mb_fw_ops o={&m,fa,fc,fv};struct mb_firmware f={0};
        uint64_t q[8]={0xc2000276u,512,0,0,0,0,0,0},r[4]={0};
        CHECK(mb_firmware_bind(&f,&o)==0);q[index]=index==2?2:123;
        CHECK(mb_firmware_ufs(&f,q,r)==MB_ARGUMENT && !m.calls);
    }
}
struct mm_model { unsigned calls,fail_at,writes;uint32_t ttbr,ctrl,status,start,end,command;uint64_t time;int permit,stall,frozen; };
static int ma(void *v,unsigned r) { assert(r==MB_DISP_IOMMU || r==MB_MDP_IOMMU);return ((struct mm_model *)v)->permit; }
static int mr(void *v,unsigned bank,uint32_t off,uint32_t *out) {
    struct mm_model *m=v;assert(bank<2);if(++m->calls==m->fail_at)return -1;
    if(off==0)*out=m->ttbr;else if(off==0x110)*out=m->ctrl;else{assert(off==0x12c);*out=m->status;}return 0;
}
static int mw(void *v,unsigned bank,uint32_t off,uint32_t value) {
    struct mm_model *m=v;assert(bank<2);if(++m->calls==m->fail_at)return -1;
    m->writes++;
    if(off==0)m->ttbr=value;
    else if(off==0x2c)assert(value==3);
    else if(off==0x24)m->start=value;
    else if(off==0x28)m->end=value;
    else if(off==0x20){assert(value==1 || value==2);m->command=value;if(!m->stall)m->status=1;}
    else{assert(off==0x12c && value==0);m->status=0;}
    return 0;
}
static uint64_t mt(void *v){return ((struct mm_model *)v)->time;}
static int md(void *v,uint32_t n){struct mm_model *m=v;if(++m->calls==m->fail_at)return -1;if(!m->frozen)m->time+=n;return 0;}
static struct mb_io mio(struct mm_model *m){return(struct mb_io){m,ma,mr,mw,barrier,mt,md};}
static void iommu_tests(void) {
    unsigned total=0;
    for(unsigned client=1;client<=2;client++) {
        struct mm_model mm={.permit=1,.ctrl=8};struct mb_io io=mio(&mm);struct mb_iommu m={0};
        CHECK(mb_iommu_bind(&m,&io,client,0,1ull<<34)==0);
        CHECK(mb_iommu_install(&m,0x12340000,0)==MB_UNVERIFIED && !mm.calls);
        CHECK(mb_iommu_install(&m,0x12340000,1)==0 && m.state==2 && mm.ttbr==0x12340000);
        total=mm.calls;
        CHECK(mb_iommu_invalidate(&m,0x200010000ull,8192)==0);
        CHECK(mm.start==0x10002 && mm.end==0x11002 && mm.command==1 && !mm.status);
        unsigned before=mm.calls;
        CHECK(mb_iommu_invalidate(&m,(1ull<<34)-4096,8192)==MB_RANGE && before==mm.calls);
        CHECK(mb_iommu_invalidate(&m,1,4096)==MB_ARGUMENT && before==mm.calls);
    }
    {
        struct mm_model mm={.permit=1,.ctrl=8};struct mb_io io=mio(&mm);struct mb_iommu m={0};
        CHECK(mb_iommu_bind(&m,&io,MB_CLIENT_UNVERIFIED_UFS,0,1ull<<34)==MB_UNVERIFIED);
        CHECK(!mm.calls && !mm.writes && !m.state);
    }
    for(unsigned at=1;at<=total;at++) {
        struct mm_model mm={.permit=1,.ctrl=8,.fail_at=at};struct mb_io io=mio(&mm);struct mb_iommu m={0};
        CHECK(mb_iommu_bind(&m,&io,1,0,1ull<<34)==0);
        CHECK(mb_iommu_install(&m,0x12340000,1)==MB_IO);
        CHECK(mm.calls==at && m.state==3); /* No follow-up after an I/O error. */
    }
    for(unsigned mode=0;mode<5;mode++) {
        struct mm_model mm={.permit=mode!=0,.ctrl=mode==1?0:8,.ttbr=mode==2?1:0,
            .status=mode==3?1:0,.stall=mode==4,.frozen=1};
        struct mb_io io=mio(&mm);struct mb_iommu m={0};
        CHECK(mb_iommu_bind(&m,&io,1,0,1ull<<34)==0);
        int r=mb_iommu_install(&m,0x12340000,1);
        CHECK(r==(mode<2?MB_UNVERIFIED:mode<4?MB_BUSY:MB_TIMEOUT));
        CHECK(mm.calls<210 && (mode==4 || !mm.writes));
        if(mode==4) {unsigned before=mm.calls;CHECK(m.state==3 && mb_iommu_invalidate(&m,0,4096)==MB_STATE && mm.calls==before);}
    }
    struct mm_model good={.permit=1,.ctrl=8};struct mb_io gio=mio(&good);struct mb_iommu gm={0};
    CHECK(mb_iommu_bind(&gm,&gio,1,0,1ull<<34)==0 && mb_iommu_install(&gm,0x12340000,1)==0);
    unsigned first=good.calls;CHECK(mb_iommu_invalidate(&gm,0x100000000ull,4096)==0);
    unsigned range_calls=good.calls-first;
    for(unsigned at=1;at<=range_calls;at++) {
        struct mm_model mm={.permit=1,.ctrl=8};struct mb_io io=mio(&mm);struct mb_iommu m={0};
        CHECK(mb_iommu_bind(&m,&io,1,0,1ull<<34)==0 && mb_iommu_install(&m,0x12340000,1)==0);
        mm.fail_at=mm.calls+at;
        CHECK(mb_iommu_invalidate(&m,0x100000000ull,4096)==MB_IO && m.state==3);
        CHECK(mm.calls==mm.fail_at);
    }
    {
        struct mm_model mm={.permit=1,.ctrl=8};struct mb_io io=mio(&mm);struct mb_iommu m={0};
        CHECK(mb_iommu_bind(&m,&io,1,0,1ull<<34)==0 && mb_iommu_install(&m,0x12340000,1)==0);
        mm.permit=0;unsigned before=mm.calls;
        CHECK(mb_iommu_invalidate(&m,0,4096)==MB_UNVERIFIED && m.state==3 && mm.calls==before);
    }
}
#ifdef MT6897_MODEL_FREESTANDING
_Alignas(16) volatile uint64_t test_smc_seen[8];
volatile uint32_t test_smc_count;
static int raw_conduit(void *ctx,const uint64_t q[8],uint64_t r[4]) { (void)ctx;mb_smc_raw(q,r);return 0; }
static int raw_verify(void *ctx,const uint64_t q[8],const uint64_t r[4]) {
    (void)ctx;return !r[0] && r[1]==q[7] && r[2]==q[2]+13 && r[3]==0x1122334455667788ull;
}
static void smc_instruction_tests(void) {
    uint64_t q[8]={0xc2000276u,512,7,3,4,5,6,0x8877665544332211ull};
    struct {uint64_t before,r[4],after;} result={9,{0,0,0,0},10};
    mb_smc_raw(q,result.r);
    for(unsigned i=0;i<8;i++) CHECK(test_smc_seen[i]==q[i]);
    CHECK(test_smc_count==1 && result.before==9 && result.after==10);
    CHECK(result.r[0]==0 && result.r[1]==q[7] && result.r[2]==20 && result.r[3]==0x1122334455667788ull);
    struct firmware_model auth={.permit=1};
    struct mb_fw_ops o={&auth,fa,raw_conduit,raw_verify};struct mb_firmware f={0};
    q[2]=1;q[3]=0;for(unsigned i=4;i<8;i++)q[i]=0;
    CHECK(mb_firmware_bind(&f,&o)==0 && mb_firmware_ufs(&f,q,result.r)==0);
    CHECK(test_smc_count==2 && result.r[2]==14);
}
#endif
int main(void) {
    bus_tests();unsigned a=checks;
    pmic_tests();unsigned b=checks-a;
    firmware_tests();unsigned c=checks-a-b;
    iommu_tests();unsigned d=checks-a-b-c;
    printf("%u PMIF, %u PMIC, %u firmware, %u IOMMU checks passed; register/provider models\n",a,b,c,d);
#ifdef MT6897_MODEL_FREESTANDING
    unsigned before=checks;smc_instruction_tests();
    printf("%u raw SMC EL1/EL3 checks passed; test monitor only\n",checks-before);
#endif
    return 0;
}
