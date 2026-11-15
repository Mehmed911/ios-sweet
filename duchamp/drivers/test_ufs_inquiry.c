/* Reuse the bounded transport model, including its complete regression suite.
 * The identification bytes are synthetic, not a physical UFS observation.
 */
#include "ufs_readonly.h"
#ifdef MT6897_MODEL_FREESTANDING
int memcmp(const void *,const void *,size_t);
#endif
#define main poll_regression_main
#include "test_ufs_poll.c"
#undef main
static unsigned fault, inquiry_commands;
static void inquiry_write(void *c,uint32_t off,uint32_t value) {
    unsigned inquiry=off==0x58 && value==1 && arena[0x1000]==1 && arena[0x1010]==0x12;
    if(inquiry) {
        inquiry_commands++;
        const uint8_t expected[16]={0x12,0,0,0,36};
        assert(!memcmp(arena+0x1010,expected,16));
    }
    wr(c,off,value);
    if(!inquiry)return;
    uint8_t *data=arena+0x10000;
    data[0]=0;data[2]=6;data[3]=2;data[4]=31;
    memcpy(data+8,"SYNTHETC",8);memcpy(data+16,"READONLY MODEL  ",16);memcpy(data+32,"0001",4);
    if(fault==1)data[0]=0x20; /* unconnected LU */
    if(fault==2)data[0]=5; /* unsupported optical device */
    if(fault==3)data[3]=0;
    if(fault==4)data[4]=30;
    if(fault==5)memset(data,0,36); /* detects the community no-transfer pattern */
    if(fault==6)arena[0x1203]^=1; /* wrong UPIU tag */
}
int main(void) {
    assert(poll_regression_main()==0);
    struct dufs_inquiry out,original;
    memset(&original,0xa5,sizeof(original));
    for(fault=0;fault<=6;fault++) {
        reset();inquiry_commands=0;
        struct dufs_config c=config(16,100);c.io.write32=inquiry_write;
        CHECK(dufs_bind(&host,&c)==0 && dufs_start(&host)==0);
        out=original;unsigned before=io_count();
        CHECK(dufs_inquiry(&host,&out)==DUFS_STATE && io_count()==before);
        model.flag_clear_at=1;CHECK(dufs_device_init(&host)==0);
        before=io_count();CHECK(dufs_inquiry(&host,NULL)==DUFS_ARGUMENT && io_count()==before);
        int result=dufs_inquiry(&host,&out);CHECK(inquiry_commands==1);
        if(!fault) {
            CHECK(result==0 && out.version==6 && !memcmp(out.vendor,"SYNTHETC",8));
            CHECK(!memcmp(out.product,"READONLY MODEL  ",16) && !memcmp(out.revision,"0001",4));
        } else {
            CHECK(result==DUFS_RESPONSE && host.state==3 && !memcmp(&out,&original,sizeof(out)));
            before=io_count();CHECK(dufs_inquiry(&host,&out)==DUFS_STATE && io_count()==before);
        }
    }
    reset();struct dufs_config c=config(16,100);c.exclusive_platform_ready=0;
    CHECK(dufs_bind(&host,&c)==DUFS_PLATFORM && !io_count());
    CHECK(dufs_inquiry(&host,&out)==DUFS_STATE && !io_count());
    CHECK(dufs_inquiry(NULL,&out)==DUFS_ARGUMENT);
    printf("%u bounded UFS inquiry checks passed\n",checks);
    return 0;
}
