/* Deterministic software-register tests, not MediaTek hardware emulation. */
#include "ufs_readonly.h"
#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *,unsigned) __attribute__((noreturn));
int printf(const char *,...);void *memcpy(void *,const void *,size_t);void *memset(void *,int,size_t);
#define assert(x) ((x)?(void)0:model_assert_fail(#x,__LINE__))
#else
#include <assert.h>
#include <stdio.h>
#include <string.h>
#endif
static unsigned checks;
#define CHECK(x) do{checks++;assert(x);}while(0)
struct model {uint32_t regs[64];unsigned reads,writes,dmas,commands,flags,clears;
    uint64_t tick;unsigned clock,stall_hce,stall_db,flag_clear_at;};
static struct model model;
static struct dufs_host host;
static _Alignas(16) uint8_t arena[0x60000];
static uint8_t destination[4096];
static uint32_t rd(void *c,uint32_t off){struct model *m=c;m->reads++;assert(off<256);return m->regs[off/4];}
static void wr(void *c,uint32_t off,uint32_t value){
    struct model *m=c;m->writes++;assert(off<256);
    if(off==0x34 && m->stall_hce)return;
    m->regs[off/4]=value;
    if(off==0x34 && !value)m->clears++;
    if(off==0x90)m->regs[0x20/4]|=1u<<10;
    if(off==0x58 && value==1){
        m->commands++;
        if(m->stall_db)return;
        uint8_t *cmd=arena+0x1000,*rsp=cmd+512;
        memset(rsp,0,512);memset(arena+8,0,4);
        rsp[0]=cmd[0]==0x16?0x36:cmd[0]==0?0x20:0x21;rsp[2]=cmd[2];rsp[3]=cmd[3];
        if(cmd[0]==0x16){
            rsp[12]=cmd[12];rsp[13]=cmd[13];
            if(cmd[12]==5){m->flags++;rsp[23]=!m->flag_clear_at || m->flags<m->flag_clear_at;}
        }
        m->regs[0x58/4]=0;m->regs[0x20/4]|=1;
    }
}
static int put(void *c,uint64_t bus,const void *p,size_t n){
    struct model *m=c;m->dmas++;assert(bus>=0x100000 && bus-0x100000<=sizeof(arena) && n<=sizeof(arena)-(bus-0x100000));
    memcpy(arena+(bus-0x100000),p,n);return 0;
}
static int get(void *c,uint64_t bus,void *p,size_t n){
    struct model *m=c;m->dmas++;assert(bus>=0x100000 && bus-0x100000<=sizeof(arena) && n<=sizeof(arena)-(bus-0x100000));
    memcpy(p,arena+(bus-0x100000),n);return 0;
}
static void barrier(void *c){(void)c;}
static uint64_t ticks(void *c){
    struct model *m=c;if(!m->clock)return m->tick;
    return m->clock==2?m->tick--:m->tick++;
}
static struct dufs_config config(unsigned limit,unsigned ms){
    return (struct dufs_config){.io={&model,rd,wr,put,get,barrier,ticks},
        .dma_begin=0x100000,.dma_end=0x160000,.list_dma=0x100000,
        .command_dma=0x101000,.data_dma=0x110000,.timeout_ms=ms,
        .exclusive_platform_ready=1,.poll_limit=limit};
}
static void reset(void){
    memset(&host,0,sizeof(host));memset(&model,0,sizeof(model));memset(arena,0,sizeof(arena));
    model.regs[0]=1u<<24;model.regs[2]=0x400;model.regs[0x30/4]=11;
    memset(destination,0xa5,sizeof(destination));
}
static unsigned io_count(void){return model.reads+model.writes+model.dmas;}
static void poisoned(unsigned cause){
    unsigned n=io_count();struct dufs_config c=config(64,3);uint64_t blocks=0;uint32_t size=0;
    CHECK(host.state==3 && dufs_timeout_cause(&host)==cause);
    CHECK(dufs_nop(&host)==DUFS_STATE && dufs_start(&host)==DUFS_STATE);
    CHECK(dufs_device_init(&host)==DUFS_STATE && dufs_capacity(&host,&blocks,&size)==DUFS_STATE);
    CHECK(dufs_read(&host,0,1,destination,sizeof(destination))==DUFS_STATE);
    CHECK(dufs_bind(&host,&c)==DUFS_STATE && io_count()==n && !model.clears);
    for(size_t i=0;i<sizeof(destination);i++)assert(destination[i]==0xa5);
}
int main(void){
    CHECK(dufs_timeout_cause(NULL)==DUFS_WAIT_NONE);
    for(unsigned mode=0;mode<2;mode++){
        reset();struct dufs_config c=config(mode?DUFS_MAX_POLLS+1:0,3);
        CHECK(dufs_bind(&host,&c)==DUFS_ARGUMENT && !io_count());
    }
    for(unsigned mode=0;mode<4;mode++){
        reset();struct dufs_config c=config(mode?64:8,3);
        model.stall_hce=1;model.clock=mode?mode==2?2:1:0;
        model.tick=mode==2?100:mode==3?UINT64_MAX-1:0;
        CHECK(dufs_bind(&host,&c)==0 && dufs_start(&host)==DUFS_TIMEOUT);
        CHECK(model.reads<16 && !model.dmas);
        if(!mode)CHECK(host.poll_remaining==0);
        poisoned(mode?DUFS_WAIT_DEADLINE:DUFS_WAIT_POLLS);
    }
    /* One budget spans the four startup waits; it is not reset per wait. */
    reset();struct dufs_config c=config(3,100);
    CHECK(dufs_bind(&host,&c)==0 && dufs_start(&host)==DUFS_TIMEOUT);
    CHECK(!model.dmas && host.poll_remaining==0);poisoned(DUFS_WAIT_POLLS);
    reset();c=config(4,100);
    CHECK(dufs_bind(&host,&c)==0 && dufs_start(&host)==0 && !host.poll_remaining);
    CHECK(dufs_nop(&host)==0 && host.poll_remaining==3); /* next API replenishes */
    /* Frozen-clock completion stall: leave DMA/host pinned, never reset it. */
    reset();c=config(8,100);CHECK(dufs_bind(&host,&c)==0 && dufs_start(&host)==0);
    host.device_ready=1;host.block_bytes=4096;host.blocks=8;model.stall_db=1;
    CHECK(dufs_read(&host,0,1,destination,sizeof(destination))==DUFS_TIMEOUT);
    CHECK(model.commands==1 && host.poll_remaining==0);poisoned(DUFS_WAIT_POLLS);
    /* Repeated successful READ_FLAG completions must consume one shared budget. */
    reset();c=config(9,100);CHECK(dufs_bind(&host,&c)==0 && dufs_start(&host)==0);
    CHECK(dufs_device_init(&host)==DUFS_TIMEOUT && !host.device_ready);
    CHECK(model.commands==9 && model.flags==8 && !host.poll_remaining);poisoned(DUFS_WAIT_POLLS);
    /* A flag clearing on the last allowed completion succeeds. */
    reset();c=config(5,100);model.flag_clear_at=4;
    CHECK(dufs_bind(&host,&c)==0 && dufs_start(&host)==0 && dufs_device_init(&host)==0);
    CHECK(model.commands==5 && model.flags==4 && host.device_ready && !host.poll_remaining);
    CHECK(dufs_nop(&host)==0 && host.poll_remaining==4 && dufs_timeout_cause(&host)==DUFS_WAIT_NONE);
    /* Deadline expiry remains distinct when the clock advances. */
    reset();c=config(64,3);model.clock=1;
    CHECK(dufs_bind(&host,&c)==0 && dufs_start(&host)==0 && dufs_device_init(&host)==DUFS_TIMEOUT);
    CHECK(model.flags>0 && model.flags<4);poisoned(DUFS_WAIT_DEADLINE);
    printf("%u bounded UFS polling checks passed\n",checks);return 0;
}
