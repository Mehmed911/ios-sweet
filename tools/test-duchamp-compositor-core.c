/* SPDX-License-Identifier: 0BSD */
#include <assert.h>
#include <stdio.h>
#include "duchamp-compositor-core.h"
#include "duchamp-compositor-wire.h"
static struct dc_scene scene;
static dg_u32 red[DC_PIXELS],blue[DC_PIXELS];
static unsigned passed;
#define CHECK(x) do {assert(x);passed++;} while(0)
int main(void) {
    struct dc_owner a={10,1},b={11,2},reuse={10,2};struct dc_route route;
    dc_init(&scene);CHECK(scene.frames[scene.front][0]==0xff102030);
    CHECK(dc_bounds(64,32,256,8192));CHECK(!dc_bounds(64,32,256,8191));
    CHECK(!dc_bounds(64,32,~0ull-3,~0ull));CHECK(!dc_bounds(0,32,256,8192));
    CHECK(!dc_bounds(65,1,260,260));CHECK(!dc_bounds(64,32,255,8192));
    CHECK(dc_add(&scene,a,1,64,32,0,0,0)==DC_OK);
    CHECK(dc_add(&scene,b,2,32,16,16,8,1)==DC_OK);
    CHECK(dc_add(&scene,a,1,1,1,0,0,0)==DC_INVALID);
    CHECK(dc_add(&scene,a,3,64,32,1,0,0)==DC_INVALID);
    for(unsigned i=0;i<DC_PIXELS;i++){red[i]=0xffff0000;blue[i]=0x800000ff;}
    CHECK(dc_commit(&scene,a,1,1,red,256,sizeof(red),(struct dc_rect){0,0,64,32})==DC_OK);
    CHECK(dc_commit(&scene,b,2,1,blue,128,2048,(struct dc_rect){0,0,32,16})==DC_OK);
    CHECK(dc_commit(&scene,b,1,2,blue,256,8192,(struct dc_rect){0,0,64,32})==DC_OWNER);
    CHECK(dc_commit(&scene,reuse,1,2,blue,256,8192,(struct dc_rect){0,0,64,32})==DC_OWNER);
    CHECK(dc_commit(&scene,b,2,1,blue,128,2048,(struct dc_rect){0,0,32,16})==DC_STALE);
    CHECK(dc_commit(&scene,b,2,2,blue,128,2048,(struct dc_rect){31,0,2,16})==DC_INVALID);
    unsigned front=scene.front;CHECK(dc_render(&scene)==DC_PIXELS && scene.front!=front);
    CHECK(scene.frames[scene.front][0]==0xffff0000);
    CHECK(scene.frames[scene.front][8*DC_W+16]==0xff7f0080);
    dg_u32 old[DC_PIXELS];memcpy(old,scene.frames[scene.front],sizeof(old));
    for(unsigned i=0;i<16*32;i++)blue[i]=0x8000ff00;
    CHECK(dc_commit(&scene,b,2,2,blue,128,2048,(struct dc_rect){0,0,8,8})==DC_OK);
    CHECK(dc_render(&scene)==64);
    unsigned unchanged=0;for(unsigned y=0;y<DC_H;y++)for(unsigned x=0;x<DC_W;x++)
        if(!(x>=16 && x<24 && y>=8 && y<16))unchanged+=old[y*DC_W+x]==scene.frames[scene.front][y*DC_W+x];
    CHECK(unchanged==DC_PIXELS-64);CHECK(scene.frames[scene.front][8*DC_W+16]==0xff7f8000);
    CHECK(dc_z(&scene,b,1,2)==DC_OWNER);CHECK(dc_z(&scene,a,1,2)==DC_OK);
    dc_render(&scene);CHECK(scene.frames[scene.front][8*DC_W+16]==0xffff0000);
    CHECK(dc_focus(&scene,b,1)==DC_OWNER);CHECK(dc_focus(&scene,b,2)==DC_OK);
    CHECK(dc_input(&scene,1,&route) && route.id==2 && route.owner.pid==11);
    CHECK(dc_focus(&scene,a,1)==DC_OK);
    CHECK(!dc_input(&scene,1,&route));
    CHECK(dc_input(&scene,0,&route) && route.id==2);
    CHECK(!dc_input(&scene,0,&route));
    CHECK(dc_remove(&scene,b)==1);dc_render(&scene);
    CHECK(scene.focus==1 && scene.layers[1].active==0 && scene.layers[1].pixels[0]==0);
    CHECK(dc_input(&scene,1,&route) && route.id==1);
    CHECK(dc_remove(&scene,a)==1 && scene.capture==0 && scene.focus==0);
    dc_render(&scene);CHECK(scene.frames[scene.front][0]==0xff102030);
    CHECK(dc_render(&scene)==0);
    unsigned char packet[128]={0};struct dc_owner audit={0};
    dg_put32(packet+4,72);dg_put32(packet+72+4,52);
    dg_put32(packet+72+40,27);dg_put32(packet+72+48,8);
    CHECK(dc_audit_peer(packet,sizeof(packet),&audit) && audit.pid==27 && audit.birth==8);
    CHECK(!dc_audit_peer(packet,123,&audit));CHECK(!dc_audit_peer(0,sizeof(packet),&audit));
    dg_put32(packet+72,1);CHECK(!dc_audit_peer(packet,sizeof(packet),&audit));dg_put32(packet+72,0);
    dg_put32(packet+72+4,8);CHECK(!dc_audit_peer(packet,sizeof(packet),&audit));dg_put32(packet+72+4,52);
    dg_put32(packet+4,129);CHECK(!dc_audit_peer(packet,sizeof(packet),&audit));
    dg_put32(packet+4,0xffffffffu);CHECK(!dc_audit_peer(packet,sizeof(packet),&audit));
    dg_put32(packet+4,127);CHECK(!dc_audit_peer(packet,127,&audit));
    printf("PASS %u compositor assertions\n",passed);return 0;
}
