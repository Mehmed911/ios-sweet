/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_POINTER_WIRE_H
#define DUCHAMP_POINTER_WIRE_H
#include "duchamp-gui-wire.h"
#include "duchamp-virtio-pointer.h"
#define DP_SERVICE "org.duchamp.qemu.gui-shell.input"
enum { DP_MSG=0x44565031,DP_CONNECT=1,DP_INPUT };
struct __attribute__((packed,aligned(4))) dp_message {
    struct dg_head h;dg_u32 count;struct dg_port endpoint;dg_u32 op;struct vp_report report;
};
struct dp_reply {struct dg_head h;dg_u32 status;};
#endif
