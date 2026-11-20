/* SPDX-License-Identifier: 0BSD */
#include <assert.h>
#include <stdio.h>
#include "duchamp-window-core.h"
#include "duchamp-gui-wire.h"
static unsigned n;
#define T(x) do{assert(x);n++;}while(0)
static struct dw_manager m;
static struct dc_scene s;
static struct gw_request packet;
static dg_u32 pixels[DC_PIXELS];
int main(void) {
    struct dc_owner a={10,1},b={11,2},reused={10,3};dg_u32 target;
    dw_init(&m);
    T(dw_create(&m,a,1,(struct dc_rect){0,0,DC_W,DC_H})==DC_OK);
    T(dw_create(&m,a,2,(struct dc_rect){12,16,70,44})==DC_OK);
    T(dw_create(&m,b,3,(struct dc_rect){60,28,72,44})==DC_OK);
    T(dw_create(&m,a,2,(struct dc_rect){0,0,24,20})==DC_INVALID);
    T(dw_geometry(&m,b,2,(struct dc_rect){1,1,24,20})==DC_OWNER);
    T(dw_geometry(&m,reused,2,(struct dc_rect){1,1,24,20})==DC_OWNER);
    T(dw_geometry(&m,a,2,(struct dc_rect){~0u,0,24,20})==DC_INVALID);
    T(dw_geometry(&m,a,2,(struct dc_rect){0,0,~0u,20})==DC_INVALID);
    T(dw_geometry(&m,a,2,(struct dc_rect){0,0,23,20})==DC_INVALID);
    T(dw_focus(&m,b,2)==DC_OWNER);T(dw_focus(&m,reused,2)==DC_OWNER);
    T(dw_pointer(&m,24,38,1,&target)==DC_OK && target==2 && m.focus==2);
    T(dw_pointer(&m,140,90,0,&target)==DC_OK && target==2 && m.capture==0);
    T(m.windows[1].events==2 && !m.windows[1].down);
    T(dw_pointer(&m,20,19,1,&target)==DC_OK && target==2);
    T(dw_pointer(&m,34,25,1,&target)==DC_OK && target==2);
    T(dw_pointer(&m,34,25,0,&target)==DC_OK && m.windows[1].rect.x==26 && m.windows[1].rect.y==22);
    T(dw_pointer(&m,94,64,1,&target)==DC_OK && m.mode==2);
    T(dw_pointer(&m,104,70,1,&target)==DC_OK);
    T(dw_pointer(&m,104,70,0,&target)==DC_OK && m.windows[1].rect.w==80 && m.windows[1].rect.h==50);
    T(dw_pointer(&m,DC_W,0,0,&target)==DC_INVALID);T(dw_pointer(&m,0,DC_H,0,&target)==DC_INVALID);
    T(dw_pointer(&m,0,0,2,&target)==DC_INVALID);T(dw_pointer(&m,0,0,1,0)==DC_INVALID);
    T(dw_destroy(&m,b,2)==DC_OWNER);T(dw_destroy(&m,reused,2)==DC_OWNER);
    T(dw_pointer(&m,34,25,1,&target)==DC_OK);
    T(dw_destroy(&m,a,2)==DC_OK && m.capture==0 && m.focus==3 && !m.pressed);
    T(dw_destroy(&m,a,2)==DC_INVALID);
    T(dw_pointer(&m,34,25,0,&target)==DC_OK && !target);
    dc_init(&s);T(dc_add(&s,a,7,DC_W,DC_H,0,0,0)==DC_OK);
    for(unsigned i=0;i<DC_PIXELS;i++)pixels[i]=0xff335577;
    T(dc_commit(&s,a,7,1,pixels,DC_W*4,sizeof(pixels),(struct dc_rect){0,0,DC_W,DC_H})==DC_OK);
    T(dc_view(&s,b,7,(struct dc_rect){5,5,24,20})==DC_OWNER);
    T(dc_view(&s,reused,7,(struct dc_rect){5,5,24,20})==DC_OWNER);
    T(dc_view(&s,a,7,(struct dc_rect){~0u,0,24,20})==DC_INVALID);
    T(dc_view(&s,a,7,(struct dc_rect){5,5,24,20})==DC_OK);dc_render(&s);
    T(s.frames[s.front][5*DC_W+5]==0xff335577 && s.frames[s.front][0]==0xff102030);
    T(dc_view(&s,a,7,(struct dc_rect){6,6,26,21})==DC_OK);dc_render(&s);
    T(s.frames[s.front][5*DC_W+5]==0xff102030 && s.frames[s.front][6*DC_W+6]==0xff335577);
    T(dc_commit(&s,a,7,2,pixels,DC_W*4,sizeof(pixels),(struct dc_rect){DC_W-1,DC_H-1,1,1})==DC_OK);
    T(dc_render(&s)==0);T(dc_remove_id(&s,b,7)==DC_OWNER);
    T(dc_remove_id(&s,a,7)==DC_OK);T(dc_remove_id(&s,a,7)==DC_INVALID);
    packet.h.id=GW_MSG;packet.h.size=GW_FIXED;packet.b=(struct gw_body){.version=GW_VERSION,.op=GW_QUERY};
    T(gw_valid(&packet,sizeof(packet)));packet.h.size--;
    T(!gw_valid(&packet,sizeof(packet)));packet.h.size=GW_FIXED;packet.b.bytes=~0u;
    T(!gw_valid(&packet,sizeof(packet)));packet.b.bytes=0;packet.b.op=GW_CREATE;
    T(!gw_valid(&packet,sizeof(packet)));packet.h.bits=0x80000000;packet.h.size=sizeof(packet);
    packet.count=1;packet.inbox=(struct dg_port){30,0,0,17,0};packet.b.bytes=DC_PIXELS*4;
    T(gw_valid(&packet,sizeof(packet)));packet.inbox.disposition=19;T(!gw_valid(&packet,sizeof(packet)));
    packet.inbox.disposition=17;T(!gw_valid(&packet,sizeof(packet)-1));
    dw_pixels(&m,1,pixels);T(pixels[0]==0xff102030);dw_cursor(&m,pixels);
    T(pixels[m.pointer_y*DC_W+m.pointer_x]==0xfff3f5f7);
    printf("PASS %u window and GUI wire assertions\n",n);return 0;
}
