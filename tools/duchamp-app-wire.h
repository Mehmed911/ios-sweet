/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_APP_WIRE_H
#define DUCHAMP_APP_WIRE_H
#include "duchamp-gui-wire.h"
#define AP_SERVICE "org.duchamp.qemu.applications"
enum {AP_MSG=0x44415031,AP_VERSION=1,AP_QUERY=1,AP_LAUNCH,AP_FOREGROUND,AP_BACKGROUND,AP_TERMINATE,AP_CRASH,AP_RESTART};
enum {AP_STOPPED=0,AP_BACKGROUND_STATE=1,AP_FOREGROUND_STATE=2,AP_PENDING=3,AP_FAILED=4,AP_STOPPING=5};
struct ap_body {dg_u32 version,op,id,pid,birth;};
struct ap_request {struct dg_head h;struct ap_body b;};
struct ap_reply {struct dg_head h;struct gw_identity b;};
static inline int ap_valid(const struct ap_request *p) {
    return p->h.id==AP_MSG && p->h.size==sizeof(*p) && !(p->h.bits&0x80000000u) &&
        p->b.version==AP_VERSION && p->b.op>=AP_QUERY && p->b.op<=AP_RESTART && p->b.id>=2 && p->b.id<=3;
}
#endif
