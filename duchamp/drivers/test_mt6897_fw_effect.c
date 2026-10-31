/* Execute a pinned comparison handler. This is not the phone's BL31. */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "mt6897_backends.h"
#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *,unsigned) __attribute__((noreturn));
int printf(const char *,...);
#define assert(v) ((v)?(void)0:model_assert_fail(#v,__LINE__))
#else
#include <assert.h>
#include <stdio.h>
#endif
typedef uintptr_t u_register_t;
struct smccc_res {uint64_t a0,a1,a2,a3;};
static unsigned checks,mtcmos_calls,ref_calls,monitor_calls;
static uint64_t ref_on,ref_stage;
#define CHECK(v) do{checks++;assert(v);}while(0)
#define BIT(n) (1u<<(n))
#define WARN(...) ((void)0)
static void ufs_mphy_va09_cg_ctrl(bool v){(void)v;assert(0);}
static void ufs_device_reset_ctrl(bool v){(void)v;assert(0);}
static void ufs_crypto_hie_init(void){assert(0);}
static void ufs_ref_clk_status(uint64_t on,uint64_t stage){ref_calls++;ref_on=on;ref_stage=stage;}
static void ufs_sram_pwr_ctrl(uint64_t v){(void)v;assert(0);}
static void ufs_get_vcc_info(struct smccc_res *r){(void)r;assert(0);}
static void ufs_device_pwr_ctrl(uint64_t a,uint64_t b){(void)a;(void)b;assert(0);}
static void ufs_mphy_ctrl(uint64_t v){(void)v;assert(0);}
static void ufs_mtcmos_ctrl(bool on){(void)on;mtcmos_calls++;}
/* Definitions and unchanged ufs_knl_ctrl() body from the verified Git blob. */
#include "firmware-reference.inc"

void model_ref_monitor(uint64_t q[8]){
    monitor_calls++;struct smccc_res r={0,0,0,0};
    uint64_t ret=UINT64_MAX;
    if(q[0]==0xc2000276u)ret=ufs_knl_ctrl(q[1],q[2],q[3],q[4],NULL,&r);
    q[0]=ret;q[1]=r.a1;q[2]=r.a2;q[3]=r.a3;
}
static void invoke(const uint64_t q[8],uint64_t out[4]){
#ifdef MT6897_MODEL_FREESTANDING
    mb_smc_raw(q,out);
#else
    uint64_t copy[8];for(unsigned i=0;i<8;i++)copy[i]=q[i];model_ref_monitor(copy);
    for(unsigned i=0;i<4;i++)out[i]=copy[i];
#endif
}
static int permit(void *c,const uint64_t q[8]){(void)c;(void)q;return 1;}
static int conduit(void *c,const uint64_t q[8],uint64_t r[4]){(void)c;invoke(q,r);return 0;}
static int unverified(void *c,const uint64_t q[8],const uint64_t r[4]){(void)c;(void)q;(void)r;return 0;}
int main(void){
    for(unsigned on=0;on<2;on++){
        uint64_t q[8]={0xc2000276u,512,on,0,0,0,0,0},r[4]={9,8,7,6};
        unsigned old=mtcmos_calls;invoke(q,r);
        CHECK(r[0]==0 && r[1]==0 && r[2]==0 && r[3]==0);
#ifdef CONFIG_MTK_MTCMOS
        CHECK(mtcmos_calls==old+1);
#else
        CHECK(mtcmos_calls==old); /* zero result even though no hook ran */
#endif
    }
    for(unsigned on=0;on<2;on++)for(unsigned stage=0;stage<2;stage++){
        uint64_t q[8]={0xc2000276u,8,on,stage,0,0,0,0},r[4];unsigned old=ref_calls;
        invoke(q,r);CHECK(r[0]==0 && r[1]==0 && r[2]==0 && r[3]==0);
        CHECK(ref_calls==old+1 && ref_on==on && ref_stage==stage);
    }
    for(unsigned i=0;i<2;i++){
        /* Vendor header's MCQ query and combined selectors are unsupported in
         * this comparison handler. It is not a complete MT6897 monitor ABI. */
        uint64_t q[8]={0xc2000276u,i?520:1024,0,0,0,0,0,0},r[4];
        unsigned old=mtcmos_calls+ref_calls;invoke(q,r);
        CHECK(r[0]==UINT64_MAX && mtcmos_calls+ref_calls==old);
    }
    for(unsigned i=0;i<6;i++){
        uint64_t q[8]={0xc2000276u,i<2?512:8,i<2?i:(i-2)/2,i<2?0:(i-2)%2,0,0,0,0};
        uint64_t out[4]={9,8,7,6};struct mb_firmware fw={0};
        struct mb_fw_ops ops={NULL,permit,conduit,unverified};unsigned calls=monitor_calls;
        CHECK(mb_firmware_bind(&fw,&ops)==0);
        CHECK(mb_firmware_ufs(&fw,q,out)==MB_UNVERIFIED && fw.state==2 && fw.last_reply[0]==0);
        CHECK(out[0]==9 && out[1]==8 && out[2]==7 && out[3]==6);
        CHECK(monitor_calls==calls+1);
        CHECK(mb_firmware_ufs(&fw,q,out)==MB_STATE && monitor_calls==calls+1);
    }
    CHECK(monitor_calls==14);
    printf("%u reference firmware checks passed; %u fixture calls\n",checks,monitor_calls);
    return 0;
}
