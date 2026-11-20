/* SPDX-License-Identifier: 0BSD */
/* Host-only failure transport: prove invalid requests never reach Mach IPC.
 * No successful hardware or IOKit operation is synthesized here. */
#include <assert.h>
#include "duchamp-darwin-iokit.h"
dg_u32 mach_task_self_=0x203;
static unsigned calls,allocations,deallocations;
dg_u32 mig_get_reply_port(void) {allocations++;return 0x103;}
void mig_dealloc_reply_port(dg_u32 p) {assert(p==0x103);deallocations++;}
int mach_msg2_internal(void *m,dg_u64 a,dg_u64 b,dg_u64 c,dg_u64 d,dg_u64 e,dg_u64 f,dg_u64 g) {
    (void)m;(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;
    calls++;return 0x10000003; /* deliberately fail all transported requests */
}
int main(void) {
    ipc_role="contract-test";
    dg_u32 n=16,c=1;dg_u64 scalar=0,size=0;void *address=0;unsigned passed=0;
#define REJECT(x) do {unsigned a=allocations;assert(x);assert(calls==0 && allocations==a);passed++;} while(0)
    REJECT(open_client(0,0)==0);
    REJECT(open_client(0xffffffffu,0)==0);
    REJECT(match(0,"IOAcceleratorES")==0);
    REJECT(match(0x303,0)==0);
    REJECT(method(0,0,0,0,0,0,0,0,0,0)!=0);
    REJECT(method(0x303,0,0,1,0,0,0,0,0,0)!=0);
    REJECT(method(0x303,0,0,0,0,1,0,0,0,0)!=0);
    REJECT(method(0x303,0,0,0,0,0,0,&n,0,0)!=0);
    REJECT(method(0x303,0,0,0,0,0,0,0,0,&c)!=0);
    REJECT(map_queue(0x303,0,&size)!=0);
    REJECT(map_queue(0x303,&address,0)!=0);
    REJECT(rpc(0,2865,64,0)!=0);
    REJECT(rpc(0x303,2865,8193,0)!=0);
    /* A well-formed request actually reaches the failure-only transport and
     * retains its error, rather than becoming success or leaking a reply. */
    assert(method(0x303,0,&scalar,1,0,0,0,0,0,0)==0x10000003);
    assert(calls==1 && allocations==1 && deallocations==1);passed++;
    printf("PASS %u/14 transport rejection and reply cleanup cases\n",passed);
}
