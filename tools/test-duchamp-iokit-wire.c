/* SPDX-License-Identifier: 0BSD */
#include <assert.h>
#include <stdio.h>
#include "duchamp-iokit-wire.h"
static unsigned char queue[256] __attribute__((aligned(8)));
static void event(unsigned at,unsigned down) {
    unsigned char *p=queue+12+at;
    dg_put32(p,60);p+=4;dg_put64(p,100+down);dg_put64(p+8,7);dg_put32(p+24,1);
    p+=28;dg_put32(p,32);dg_put32(p+4,3);dg_u16 page=12,key=0x40;
    memcpy(p+16,&page,2);memcpy(p+18,&key,2);dg_put32(p+20,down);
}
static void reset(void) {memset(queue,0,sizeof(queue));dg_put32(queue,128);}
int main(void) {
    struct dg_event e;unsigned passed=0;
    reset();event(0,1);event(64,0);dg_put32(queue+8,128);
    assert(dg_queue_pop(queue,140,&e)==1 && e.type==3 && e.down==1 && e.sender==7);passed++;
    assert(dg_queue_pop(queue,140,&e)==1 && e.down==0);passed++;
    assert(dg_queue_pop(queue,140,&e)==0);passed++;
    reset();dg_put32(queue,200);assert(dg_queue_pop(queue,140,&e)==-1);passed++;
    reset();dg_put32(queue+4,129);assert(dg_queue_pop(queue,140,&e)==-1);passed++;
    reset();dg_put32(queue+8,129);assert(dg_queue_pop(queue,140,&e)==-1);passed++;
    reset();event(0,1);dg_put32(queue+8,64);dg_put32(queue+12,4);
    assert(dg_queue_pop(queue,140,&e)==-1);passed++;
    reset();event(0,1);dg_put32(queue+8,64);dg_put32(queue+16+28,100);
    assert(dg_queue_pop(queue,140,&e)==-1);passed++;
    reset();event(0,1);dg_put32(queue+4,128);dg_put32(queue+8,64);
    assert(dg_queue_pop(queue,140,&e)==1 && e.down==1);passed++;
    reset();assert(dg_queue_pop(queue,8,&e)==-1);passed++;
    printf("PASS %u/10 IOSharedDataQueue bounds and ordering parser cases\n",passed);
    return 0;
}
