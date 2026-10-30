#include "ufs_readonly.h"
#include "framebuffer.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks;
#define CHECK(v) do { ++checks; assert(v); } while(0)
struct model { uint32_t regs[64]; unsigned reads,writes,dmas; uint64_t tick; int stall; };
static uint32_t read32(void *v,uint32_t off) {
    struct model *m=v; ++m->reads;
    return m->regs[off/4];
}
static void write32(void *v,uint32_t off,uint32_t value) {
    struct model *m=v; ++m->writes;
    if(off==0x34 && m->stall) return;
    m->regs[off/4]=value;
    if(off==0x90) m->regs[0x20/4]|=1u<<10;
}
static int put(void *v,uint64_t bus,const void *p,size_t n) {
    struct model *m=v; (void)bus; (void)p; (void)n; ++m->dmas; return -1;
}
static int get(void *v,uint64_t bus,void *p,size_t n) {
    struct model *m=v; (void)bus; (void)p; (void)n; ++m->dmas; return -1;
}
static void fence(void *v) { (void)v; }
static uint64_t ticks(void *v) { return ++((struct model *)v)->tick; }
static void check_poison(struct dufs_host *h,struct dufs_config *c,struct model *m) {
    unsigned before=m->reads+m->writes+m->dmas;
    char target[4096]; memset(target,0xa5,sizeof(target));
    CHECK(dufs_nop(h)==DUFS_STATE);
    CHECK(dufs_start(h)==DUFS_STATE);
    CHECK(dufs_bind(h,c)==DUFS_STATE);
    CHECK(dufs_read(h,0,1,target,sizeof(target))==DUFS_STATE);
    CHECK(before==m->reads+m->writes+m->dmas);
    for(size_t i=0;i<sizeof(target);i++) assert((unsigned char)target[i]==0xa5);
}
int main(void) {
    for(int mode=0;mode<5;mode++) {
        struct model m={0}; m.regs[0]=1u<<24; m.regs[8/4]=0x400; m.regs[0x30/4]=11;
        struct dufs_config c={.io={&m,read32,write32,put,get,fence,ticks},
            .dma_begin=0x100000,.dma_end=0x200000,.list_dma=0x100000,
            .command_dma=0x101000,.data_dma=0x110000,.timeout_ms=5,
            .exclusive_platform_ready=1,.poll_limit=64};
        struct dufs_host *h=calloc(1,sizeof(*h)); CHECK(h!=NULL);
        if(mode==0) m.regs[0x34/4]=1; /* inherited live controller: no takeover */
        if(mode==1) m.stall=1;
        if(mode==2) m.regs[8/4]=0xffffffff;
        if(mode==3) { m.regs[0]=0; c.dma_end+=0x100000000ULL;
            c.list_dma+=0x100000000ULL; c.command_dma+=0x100000000ULL;
            c.data_dma+=0x100000000ULL; c.dma_begin+=0x100000000ULL; }
        /* Alias-safe configuration copy, even when supplied in host storage. */
        h->config=c;
        CHECK(dufs_bind(h,&h->config)==0);
        CHECK(h->config.io.context==&m && h->config.list_dma==c.list_dma);
        int result=dufs_start(h);
        CHECK(result==(mode==1?DUFS_TIMEOUT:mode==3?DUFS_ARGUMENT:mode==4?DUFS_DMA:DUFS_STATE));
        if(mode==0 || mode==2 || mode==3) CHECK(m.writes==0 && m.dmas==0);
        if(mode==1) CHECK(m.reads<20 && m.dmas==0);
        check_poison(h,&c,&m); free(h);
    }
    uint8_t pixels[256]; memset(pixels,0xa5,sizeof(pixels));
    struct dfb_surface good={pixels,sizeof(pixels),4,4,32};
    CHECK(dfb_validate(&good)==0);
    CHECK(dfb_fill(&good,(struct dfb_rect){3,3,1,1},0x12345678)==0);
    CHECK(pixels[108]==0x78 && pixels[111]==0x12 && pixels[112]==0xa5);
    uint8_t previous[256]; memcpy(previous,pixels,sizeof(pixels));
    struct dfb_surface invalid[]={
        {NULL,256,4,4,32},{pixels,0,4,4,32},{pixels,256,0,4,32},
        {pixels,256,4,0,32},{pixels,256,4,4,0},{pixels,256,4,4,15},
        {pixels,256,UINT32_MAX,4,32},{(void *)(UINTPTR_MAX-16),256,4,4,32}};
    for(size_t i=0;i<sizeof(invalid)/sizeof(*invalid);i++) {
        CHECK(dfb_validate(&invalid[i])==-1);
        CHECK(dfb_fill(&invalid[i],(struct dfb_rect){0,0,1,1},0)==-1);
        CHECK(memcmp(previous,pixels,sizeof(pixels))==0);
    }
    CHECK(dfb_blit(&good,0,0,&good,(struct dfb_rect){0,0,1,1})==-1);
    CHECK(memcmp(previous,pixels,sizeof(pixels))==0);
    printf("%u native guard checks passed (ASan/UBSan run by harness)\n",checks);
    return 0;
}
