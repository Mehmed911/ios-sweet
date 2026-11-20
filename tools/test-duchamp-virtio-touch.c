/* SPDX-License-Identifier: 0BSD */
#include <assert.h>
#include <stdio.h>
#include "duchamp-virtio-touch.h"
static unsigned n;static struct mt_state s;static struct mt_report r;
#define T(x) do{assert(x);n++;}while(0)
static void ev(unsigned code,unsigned value){T(mt_event(&s,(struct vp_event){3,code,value},&r)==0);}
static void sync_event(void){T(mt_event(&s,(struct vp_event){0,0,0},&r)==1);T(mt_valid(&r));}
static void begin(unsigned slot,unsigned id,unsigned x,unsigned y){ev(0x2f,slot);ev(0x39,id);ev(0x35,x);ev(0x36,y);}
int main(void) {
    mt_init(&s,1);begin(0,1,0,32767);begin(10,10,16000,12000);sync_event();
    T(r.active==((1<<10)|1) && r.changed==r.active && r.contacts[0].id==1 && r.contacts[10].id==10);
    T(mt_axis(0,160)==0 && mt_axis(32767,160)==159 && mt_axis(32767,96)==95);
    ev(0x2f,0);ev(0x35,1000);sync_event();T(r.changed==1 && r.contacts[10].x==16000);
    ev(0x39,~0u);sync_event();T(r.active==(1<<10) && !r.contacts[0].active && r.contacts[0].id==1);
    begin(0,2,123,456);sync_event();T(r.contacts[0].id==2);
    ev(0x2f,11);sync_event();T(r.flags==(MT_REPORT|MT_CANCEL) && !r.active && r.changed==MT_MASK);
    begin(0,1,10,20);begin(1,1,30,40);sync_event();T(r.flags&MT_CANCEL);
    begin(0,1,32768,0);sync_event();T(r.flags&MT_CANCEL);
    ev(0x2f,0);ev(0x39,1);sync_event();T(r.flags&MT_CANCEL);
    begin(0,1,10,20);sync_event();T(r.active==1);
    T(mt_event(&s,(struct vp_event){0,3,0},&r)==0);sync_event();T(r.flags&MT_CANCEL);
    struct mt_report invalid=r;invalid.active=~0u;T(!mt_valid(&invalid));invalid=r;invalid.reserved=1;T(!mt_valid(&invalid));
    invalid=r;invalid.contacts[0].active=2;T(!mt_valid(&invalid));invalid=r;invalid.contacts[0].x=32768;T(!mt_valid(&invalid));
    s.frame.sequence=~0u;T(mt_event(&s,(struct vp_event){0,0,0},&r)==-1);
    printf("PASS %u multitouch parser assertions\n",n);return 0;
}
