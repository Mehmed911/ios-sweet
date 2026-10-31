#include "duchamp_timer_boot.h"
#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *,unsigned) __attribute__((noreturn));
int printf(const char *,...);
#define assert(x) ((x)?(void)0:model_assert_fail(#x,__LINE__))
#else
#include <assert.h>
#include <stdio.h>
#endif

static unsigned checks;
#define CHECK(x) do{checks++;assert(x);}while(0)

int main(void) {
    CHECK(dtimer_frequency_check(0,UINT64_C(13000000))==DTIMER_ARGUMENT);
    CHECK(dtimer_frequency_check(13000000,0)==DTIMER_ARGUMENT);
    CHECK(dtimer_frequency_check(1,UINT64_C(0x100000000))==DTIMER_ARGUMENT);
    CHECK(dtimer_frequency_check(UINT32_MAX,UINT64_MAX)==DTIMER_ARGUMENT);

    static const uint32_t valid[]={1,13000000,19200000,24000000,62500000,UINT32_MAX};
    for(unsigned i=0;i<sizeof(valid)/sizeof(valid[0]);i++) {
        CHECK(dtimer_frequency_check(valid[i],valid[i])==DTIMER_OK);
    }

    CHECK(dtimer_frequency_check(13000000,62500000)==DTIMER_FREQUENCY_MISMATCH);
    CHECK(dtimer_frequency_check(62500000,13000000)==DTIMER_FREQUENCY_MISMATCH);
    CHECK(dtimer_frequency_check(13000000,12999999)==DTIMER_FREQUENCY_MISMATCH);
    CHECK(dtimer_frequency_check(13000000,13000001)==DTIMER_FREQUENCY_MISMATCH);
    CHECK(dtimer_frequency_check(UINT32_MAX,UINT32_MAX-1)==DTIMER_FREQUENCY_MISMATCH);

    printf("%u bounded CNTFRQ checks passed\n",checks);
    return 0;
}
