/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_TOUCH_WIRE_H
#define DUCHAMP_TOUCH_WIRE_H
#include "duchamp-pointer-wire.h"
#include "duchamp-virtio-touch.h"
enum {DT_MSG=0x44545032};
struct __attribute__((packed,aligned(4))) dt_message {
    struct dg_head h;dg_u32 count;struct dg_port endpoint;dg_u32 op;struct mt_report report;
};
#endif
