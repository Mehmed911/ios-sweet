#include "duchamp_psci_boot.h"
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
struct model { unsigned auth_calls,conduit_calls;int authorised,io,status;
    struct dpsci_request last_auth,last_call; };
static int auth(void *context,const struct dpsci_request *request) {
    struct model *m=context;m->auth_calls++;m->last_auth=*request;
    return m->authorised;
}
static int conduit(void *context,const struct dpsci_request *request,int32_t *status) {
    struct model *m=context;m->conduit_calls++;m->last_call=*request;
    *status=m->status;return m->io;
}
static void reset(struct model *m) { memset(m,0,sizeof(*m));m->authorised=1; }
static void arguments(void) {
    struct model m;reset(&m);struct dpsci_ops ops={&m,auth,conduit};
    struct dpsci_request q={0x100,0x1c0100000,1};int32_t status=123;
    CHECK(dpsci_cpu_on(0,&q,&status)==DPSCI_ARGUMENT);
    CHECK(dpsci_cpu_on(&ops,0,&status)==DPSCI_ARGUMENT);
    CHECK(dpsci_cpu_on(&ops,&q,0)==DPSCI_ARGUMENT);
    struct dpsci_ops missing=ops;missing.authorise=0;
    CHECK(dpsci_cpu_on(&missing,&q,&status)==DPSCI_ARGUMENT);
    missing=ops;missing.conduit=0;
    CHECK(dpsci_cpu_on(&missing,&q,&status)==DPSCI_ARGUMENT);
    const struct dpsci_request bad[]={
        {0,0x1c0100000,0},{0x100,0,1},{0x100,0x1c0100001,1},
        {0x100,0x1c0100000,0},{0x800,0x1c0100000,8},
        {0x200,0x1c0100000,1},{0x101,0x1c0100000,1},
        {UINT64_C(0x100000100),0x1c0100000,1}
    };
    for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);i++) {
        CHECK(dpsci_cpu_on(&ops,&bad[i],&status)==DPSCI_ARGUMENT);
        CHECK(status==123 && !m.auth_calls && !m.conduit_calls);
    }
}
static void authorization(void) {
    struct model m;reset(&m);m.authorised=0;
    struct dpsci_ops ops={&m,auth,conduit};
    struct dpsci_request q={0x300,0x1c0100000,3};int32_t status=77;
    CHECK(dpsci_cpu_on(&ops,&q,&status)==DPSCI_UNVERIFIED);
    CHECK(m.auth_calls==1 && !m.conduit_calls && status==77);
    CHECK(m.last_auth.target==q.target && m.last_auth.entry==q.entry &&
          m.last_auth.context==q.context);
}
static void transport(void) {
    for(unsigned cpu=1;cpu<8;cpu++) {
        struct model m;reset(&m);m.status=cpu==1?0:cpu==2?-1:-3;
        struct dpsci_ops ops={&m,auth,conduit};
        struct dpsci_request q={(uint64_t)cpu<<8,0x1c0100000,cpu};
        int32_t status=99;
        CHECK(dpsci_cpu_on(&ops,&q,&status)==DPSCI_OK);
        CHECK(m.auth_calls==1 && m.conduit_calls==1 && status==m.status);
        CHECK(m.last_call.target==q.target && m.last_call.entry==q.entry &&
              m.last_call.context==q.context);
    }
    struct model m;reset(&m);m.io=1;m.status=0;
    struct dpsci_ops ops={&m,auth,conduit};
    struct dpsci_request q={0x700,0x1c0100000,7};int32_t status=55;
    CHECK(dpsci_cpu_on(&ops,&q,&status)==DPSCI_IO);
    CHECK(m.auth_calls==1 && m.conduit_calls==1 && status==55);
}
int main(void) {
    arguments();authorization();transport();
    printf("%u bounded PSCI CPU_ON checks passed\n",checks);
    return 0;
}
