#include "boot_choice.h"
#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *,unsigned) __attribute__((noreturn));
int printf(const char *,...);void *memset(void *,int,size_t);int memcmp(const void *,const void *,size_t);
#define assert(x) ((x)?(void)0:model_assert_fail(#x,__LINE__))
#else
#include <assert.h>
#include <stdio.h>
#include <string.h>
#endif
static unsigned checks;
#define CHECK(x) do{checks++;assert(x);}while(0)
static unsigned char ring[128],copy[128];
static const struct duchamp_boot_choice_access ready={1,1,1,1,1};
static void le(unsigned char *p,unsigned v){for(unsigned i=0;i<4;i++)p[i]=(unsigned char)(v>>(8*i));}
static void setup(unsigned end,unsigned size){memset(ring,0,sizeof(ring));le(ring,0x43474244);le(ring+4,end);le(ring+8,size);}
static void request(unsigned start){const char *s="\nDUCHAMP:BOOT-XNU-ONCE\n";for(unsigned i=0;s[i];i++)ring[12+(start+i)%116]=(unsigned char)s[i];}
int main(void){
    setup(0,0);CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==0);
    for(unsigned i=0;i<5;i++){
        struct duchamp_boot_choice_access a=ready;
        if(i==0)a.readable=0;if(i==1)a.writable=0;if(i==2)a.retained=0;
        if(i==3)a.cache_publication_ready=0;if(i==4)a.android_fallback_ready=0;
        CHECK(duchamp_take_xnu_request((void *)(uintptr_t)1,sizeof(ring),&a)==0);
    }
    CHECK(duchamp_take_xnu_request(ring,sizeof(ring),NULL)==0);
    CHECK(duchamp_take_xnu_request(NULL,128,&ready)==-1);
    CHECK(duchamp_take_xnu_request(ring,8,&ready)==-1);
    CHECK(duchamp_take_xnu_request(ring,65537,&ready)==-1);
    setup(116,116);CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==-1);
    setup(0,117);CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==-1);
    setup(30,29);CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==-1);
    setup(0,0);request(50);CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==0); /* stale bytes */
    setup(24,24);request(0);CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==1);
    CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==0);
    for(unsigned start=0;start<116;start++){
        setup(start,116);request(start);
        CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==1);
        CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==0);
    }
    setup(60,60);request(0);request(30);
    CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==1);
    CHECK(duchamp_take_xnu_request(ring,sizeof(ring),&ready)==0);
    for(unsigned i=0;i<128;i++)copy[i]=ring[i];
    CHECK(duchamp_take_xnu_request(ring,sizeof(ring),NULL)==0 && !memcmp(ring,copy,sizeof(ring)));
    printf("%u one-session boot policy checks passed\n",checks);return 0;
}
