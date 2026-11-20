/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_COMPOSITOR_WIRE_H
#define DUCHAMP_COMPOSITOR_WIRE_H
#include "duchamp-compositor-core.h"
#define DC_SERVICE "org.duchamp.qemu.compositor"
enum {DC_MSG=0x44504332,DC_VERSION=1};
enum {DC_REGISTER=1,DC_QUERY,DC_DIRTY,DC_SET_Z,DC_ACK,DC_EVENT,DC_FOCUS,DC_VIEW};
enum {DC_BLEND=1,DC_PATCHED,DC_RAISED,DC_RESTORED,DC_ONE_LEFT,DC_EMPTY};
enum {DC_CMD_NONE=0,DC_CMD_PATCH,DC_CMD_RAISE,DC_CMD_RESTORE};
struct dc_request {dg_u32 version,op,role,id,seq,x,y,w,h;int z;dg_u32 value,reserved;};
struct dc_answer {dg_u32 status,id,phase,command,base_id,epoch;};
struct __attribute__((packed,aligned(4))) dc_registration {
    struct dg_head h;dg_u32 count;struct dg_port surface,inbox;struct dc_request body;
};
struct dc_packet {struct dg_head h;struct dc_request body;};
struct dc_reply {struct dg_head h;struct dc_answer body;};
_Static_assert(sizeof(struct dc_request)==48,"compositor v1 request");
_Static_assert(sizeof(struct dc_registration)==100,"two transferred port rights");
_Static_assert(sizeof(struct dc_packet)==72,"simple compositor request");
_Static_assert(sizeof(struct dc_reply)==48,"compositor reply");
/* Only valid after a receive requesting MACH_RCV_TRAILER_AUDIT. The kernel,
 * not a client-supplied PID, appends the audit token after msgh_size. */
static inline int dc_audit_peer(const void *p,dg_u32 capacity,struct dc_owner *owner) {
    if(!p || !owner || capacity<24)return 0;
    dg_u32 size=dg_get32((const dg_u8 *)p+4);
    if(size<24 || size>capacity || size>0xfffffffcu)return 0;
    dg_u32 at=(size+3)&~3u;
    if(at>capacity || capacity-at<52)return 0;
    const dg_u8 *t=(const dg_u8 *)p+at;
    if(dg_get32(t)!=0 || dg_get32(t+4)<52 || dg_get32(t+4)>capacity-at)return 0;
    owner->pid=dg_get32(t+40);owner->birth=dg_get32(t+48);return 1;
}
#endif
