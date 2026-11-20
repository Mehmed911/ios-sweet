/* SPDX-License-Identifier: 0BSD */
#include <assert.h>
#include <stdio.h>
#include "duchamp-iokit-contract.h"
int main(void) {
    dg_u64 scalar[16]={0}; dg_u8 bytes[4096]={0}; dg_u32 n=4096,c=16;
    unsigned passed=0;
#define CHECK(x) do {assert(x);passed++;} while(0)
    CHECK(!dg_object_valid(0)); CHECK(!dg_object_valid(0xffffffffu)); CHECK(dg_object_valid(0x103));
    CHECK(dg_method_request_valid(scalar,16,bytes,4096,bytes,&n,scalar,&c));
    CHECK(!dg_method_request_valid(0,1,0,0,0,0,0,0));
    CHECK(!dg_method_request_valid(0,0,0,1,0,0,0,0));
    CHECK(!dg_method_request_valid(0,0,0,0,0,&n,scalar,&c));
    CHECK(!dg_method_request_valid(0,0,0,0,bytes,&n,0,&c));
    CHECK(!dg_method_request_valid(scalar,17,bytes,4096,bytes,&n,scalar,&c));
    CHECK(!dg_method_request_valid(scalar,16,bytes,4097,bytes,&n,scalar,&c));
    n=4097;CHECK(!dg_method_request_valid(scalar,16,bytes,4096,bytes,&n,scalar,&c));
    n=4096;c=17;CHECK(!dg_method_request_valid(scalar,16,bytes,4096,bytes,&n,scalar,&c));
    n=0;c=0;CHECK(dg_method_request_valid(0,0,0,0,0,&n,0,&c));
    CHECK(dg_method_request_valid(0,0,0,0,0,0,0,0));
    printf("PASS %u/14 IOKit object and method-buffer contract cases\n",passed);
}
