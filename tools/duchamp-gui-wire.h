/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_GUI_WIRE_H
#define DUCHAMP_GUI_WIRE_H
#include "duchamp-compositor-wire.h"
#define GW_SERVICE "org.duchamp.qemu.window-manager"
#define GW_COMPOSITOR "org.duchamp.qemu.gui-compositor"
enum { GW_MSG=0x44574731,GW_VERSION=1,GW_CREATE=1,GW_PAINT,GW_GEOMETRY,GW_FOCUS,GW_DESTROY,GW_QUERY,GW_POINTER,GW_EVENT };
enum {GW_TOUCH=9,GW_INFO,GW_FOREGROUND,GW_BACKGROUND,GW_TOUCH_EVENT,GW_TERMINATE,GW_CRASH,GW_LIFECYCLE_EVENT};
struct gw_body {dg_u32 version,op,id,x,y,w,h,value,seq,bytes;};
struct __attribute__((packed,aligned(4))) gw_request {
    struct dg_head h;dg_u32 count;struct dg_port inbox;struct gw_body b;dg_u32 pixels[DC_PIXELS];
};
struct gw_result {dg_u32 status,id,pid,focus,active,events,down,x,y,w,h,epoch;};
struct gw_reply {struct dg_head h;struct gw_result b;};
struct gw_identity {dg_u32 status,id,pid,birth,state,visible,contacts,touch_events,cancelled;};
struct gw_identity_reply {struct dg_head h;struct gw_identity b;};
#define GW_FIXED ((dg_u32)__builtin_offsetof(struct gw_request,pixels))
static inline int gw_valid(const struct gw_request *r,dg_u32 capacity) {
    if(capacity<GW_FIXED || r->h.size<GW_FIXED || r->h.size>capacity || r->h.id!=GW_MSG ||
       r->b.version!=GW_VERSION || r->b.op<GW_CREATE || r->b.op>GW_CRASH || r->b.op==GW_EVENT || r->b.op==GW_TOUCH_EVENT)return 0;
    int paint=r->b.op==GW_CREATE || r->b.op==GW_PAINT;
    if(r->b.bytes!=(paint?DC_PIXELS*4u:0) || r->h.size!=GW_FIXED+r->b.bytes)return 0;
    if(r->b.op==GW_CREATE)return (r->h.bits&0x80000000u) && r->count==1 && !r->inbox.type && r->inbox.disposition==17 && r->inbox.name;
    return !(r->h.bits&0x80000000u) && !r->count && !r->inbox.name;
}
#endif
