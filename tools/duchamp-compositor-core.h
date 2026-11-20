/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_COMPOSITOR_CORE_H
#define DUCHAMP_COMPOSITOR_CORE_H
#include "duchamp-iokit-wire.h"
#ifndef DC_CANVAS_W
#define DC_CANVAS_W 64
#define DC_CANVAS_H 32
#endif
enum { DC_W=DC_CANVAS_W, DC_H=DC_CANVAS_H, DC_PIXELS=DC_W*DC_H, DC_LAYERS=4 };
enum { DC_OK=0, DC_INVALID=1, DC_OWNER=2, DC_STALE=3, DC_FULL=4 };
struct dc_owner {dg_u32 pid,birth;};
struct dc_rect {dg_u32 x,y,w,h;};
struct dc_layer {
    struct dc_owner owner;
    dg_u32 id,w,h,x,y,seq,active,capacity_w,capacity_h;
    int z;
    dg_u32 pixels[DC_PIXELS];
};
struct dc_scene {
    struct dc_layer layers[DC_LAYERS];
    dg_u32 frames[2][DC_PIXELS],front,epoch,focus,capture;
    struct dc_rect dirty;
};
struct dc_route {struct dc_owner owner;dg_u32 id,down;};
void dc_init(struct dc_scene *s);
int dc_bounds(dg_u32 w,dg_u32 h,dg_u64 stride,dg_u64 bytes);
int dc_add(struct dc_scene *,struct dc_owner,dg_u32 id,dg_u32 w,dg_u32 h,dg_u32 x,dg_u32 y,int z);
int dc_commit(struct dc_scene *,struct dc_owner,dg_u32 id,dg_u32 seq,const void *,dg_u64 stride,dg_u64 bytes,struct dc_rect);
int dc_z(struct dc_scene *,struct dc_owner,dg_u32 id,int z);
int dc_focus(struct dc_scene *,struct dc_owner,dg_u32 id);
int dc_view(struct dc_scene *,struct dc_owner,dg_u32 id,struct dc_rect);
int dc_remove_id(struct dc_scene *,struct dc_owner,dg_u32 id);
int dc_input(struct dc_scene *,dg_u32 down,struct dc_route *);
unsigned dc_remove(struct dc_scene *,struct dc_owner);
unsigned dc_render(struct dc_scene *);
#endif
