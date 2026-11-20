/* SPDX-License-Identifier: 0BSD */
#include <assert.h>
#include <stdio.h>
#include "duchamp-virtio-pointer.h"
static unsigned n;
#define T(x) do{assert(x);n++;}while(0)
int main(void) {
    struct vp_state s;struct vp_report r;unsigned x,y;vp_init(&s,1);
    T(vp_event(&s,(struct vp_event){3,0,32767},&r)==0);
    T(vp_event(&s,(struct vp_event){3,1,0},&r)==0);
    T(vp_event(&s,(struct vp_event){1,0x110,1},&r)==0);
    T(vp_event(&s,(struct vp_event){0,0,0},&r)==1);
    T(r.sequence==1 && r.left==1 && r.x==32767 && r.y==0);
    T(vp_coordinates(&r,160,96,&x,&y) && x==159 && y==0);
    T(vp_event(&s,(struct vp_event){3,1,32767},&r)==0);
    T(vp_event(&s,(struct vp_event){1,0x110,0},&r)==0);
    T(vp_event(&s,(struct vp_event){0,0,0},&r)==1);
    T(r.sequence==2 && !r.left);
    T(vp_coordinates(&r,160,96,&x,&y) && y==95);
    T(vp_event(&s,(struct vp_event){3,0,32768},&r)==-1);
    T(vp_event(&s,(struct vp_event){0,0,0},&r)==-1);
    T(vp_event(&s,(struct vp_event){1,0x110,2},&r)==-1);
    T(vp_event(&s,(struct vp_event){0,0,0},&r)==-1);
    T(vp_event(&s,(struct vp_event){0,3,0},&r)==-1);
    T(vp_used(63,8,64));T(!vp_used(64,8,1));T(!vp_used(~0u,8,1));
    T(!vp_used(0,7,1));T(!vp_used(0,9,1));T(!vp_used(0,8,65));T(vp_used(0,8,0xffffu)==0);
    r.version=2;T(!vp_coordinates(&r,160,96,&x,&y));r.version=1;
    r.generation=0;T(!vp_coordinates(&r,160,96,&x,&y));r.generation=1;
    r.left=2;T(!vp_coordinates(&r,160,96,&x,&y));r.left=0;
    r.x=~0u;T(!vp_coordinates(&r,160,96,&x,&y));r.x=32767;
    T(!vp_coordinates(&r,0,96,&x,&y));T(!vp_coordinates(&r,5000,96,&x,&y));
    T(!vp_coordinates(&r,160,96,0,&y));
    r.flags=VP_FAULT;T(!vp_coordinates(&r,160,96,&x,&y));
    vp_init(&s,2);T(s.generation==2 && !s.left && !s.sequence);
    s.sequence=0xffffffffu;T(vp_event(&s,(struct vp_event){0,0,0},&r)==-1);
    printf("PASS %u VirtIO parser and bounds assertions\n",n);return 0;
}
