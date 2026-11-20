/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_WINDOW_CORE_H
#define DUCHAMP_WINDOW_CORE_H
#include "duchamp-compositor-core.h"
#include "duchamp-virtio-touch.h"
enum { DW_WINDOWS=3, DW_TITLE=9, DW_MIN_W=24, DW_MIN_H=20 };
struct dw_window {struct dc_owner owner;struct dc_rect rect;dg_u32 id,active,events,down,seq,visible,touch_events,contacts,cancelled;int z;};
struct dw_contact {dg_u32 active,id,target,x,y,mode,origin_x,origin_y;struct dc_rect original;};
struct dw_manager {
    struct dw_window windows[DW_WINDOWS];
    dg_u32 focus,capture,pointer_x,pointer_y,pressed,mode,origin_x,origin_y;
    struct dc_rect original;
    struct dw_contact contacts[MT_SLOTS];
};
void dw_init(struct dw_manager *);
int dw_create(struct dw_manager *,struct dc_owner,dg_u32,struct dc_rect);
int dw_geometry(struct dw_manager *,struct dc_owner,dg_u32,struct dc_rect);
int dw_focus(struct dw_manager *,struct dc_owner,dg_u32);
int dw_destroy(struct dw_manager *,struct dc_owner,dg_u32);
int dw_pointer(struct dw_manager *,dg_u32 x,dg_u32 y,dg_u32 down,dg_u32 *target);
int dw_background(struct dw_manager *,struct dc_owner,dg_u32);
int dw_touch(struct dw_manager *,dg_u32 slot,dg_u32 id,dg_u32 x,dg_u32 y,dg_u32 phase,dg_u32 *target);
void dw_pixels(const struct dw_manager *,dg_u32 id,dg_u32 *pixels);
void dw_cursor(const struct dw_manager *,dg_u32 *pixels);
#endif
