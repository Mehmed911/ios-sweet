/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_COMPOSITOR_IOKIT_H
#define DUCHAMP_COMPOSITOR_IOKIT_H
#include "duchamp-darwin-iokit.h"
#include "duchamp-compositor-core.h"
struct di_surface {dg_u32 id,w,h,stride,bytes;dg_u32 *pixels;};
static inline int di_description(const dg_u8 *d,struct di_surface *s) {
    *s=(struct di_surface){dg_get32(d+24),dg_get32(d+32),dg_get32(d+36),dg_get32(d+40),dg_get32(d+28),
        (void *)(unsigned long)dg_get64(d)};
    /* The kernel rounds allocations to its VM page size (16 KiB here).
     * The logical 8 KiB canvas is still bounded separately by dc_bounds. */
    return !s->id || !s->pixels || s->bytes>65536 || dg_get32(d+48)!=0x42475241 ||
           !dc_bounds(s->w,s->h,s->stride,s->bytes)?-1:0;
}
static inline int di_create(dg_u32 connection,dg_u32 w,dg_u32 h,struct di_surface *s) {
    char xml[512];
    int n=snprintf(xml,sizeof(xml),"<dict><key>IOSurfaceWidth</key><integer>%u</integer>"
        "<key>IOSurfaceHeight</key><integer>%u</integer><key>IOSurfaceBytesPerElement</key><integer>4</integer>"
        "<key>IOSurfaceBytesPerRow</key><integer>%u</integer><key>IOSurfaceAllocSize</key><integer>%u</integer>"
        "<key>IOSurfacePixelFormat</key><integer>1111970369</integer></dict>",w,h,w*4,w*h*4);
    if(n<0 || (unsigned)n>=sizeof(xml))return -1;
    dg_u8 d[0xa68];dg_u32 count=sizeof(d);
    int rc=method(connection,0,0,0,xml,(dg_u32)n+1,d,&count,0,0);
    return rc?rc:count==sizeof(d)?di_description(d,s):-1;
}
static inline int di_import(dg_u32 connection,dg_u32 port,struct di_surface *s) {
    dg_u64 in=port;dg_u8 d[0xa68];dg_u32 count=sizeof(d);
    int rc=method(connection,34,&in,1,0,0,d,&count,0,0);
    return rc?rc:count==sizeof(d)?di_description(d,s):-1;
}
static inline int di_close(dg_u32 connection) {
    memset(message,0,sizeof(message));
    int rc=rpc(connection,2816,24,0);
    if(!rc)rc=dg_get32(message+4)==36?(int)dg_get32(message+32):-1;
    mach_port_deallocate(mach_task_self_,connection);return rc;
}
static inline int di_present(dg_u32 fb,struct di_surface *surface,const dg_u32 *pixels,dg_u64 *swap) {
    memcpy(surface->pixels,pixels,DC_PIXELS*4);__atomic_thread_fence(__ATOMIC_SEQ_CST);
    dg_u32 count=1;int rc=method(fb,4,0,0,0,0,0,0,swap,&count);
    if(rc || count!=1 || !*swap)return -1;
    dg_u8 record[0x46c]={0};dg_put32(record+0x50,(dg_u32)*swap);dg_put32(record+0x54,surface->id);
    dg_put32(record+0x64+8,DC_W);dg_put32(record+0x64+12,DC_H);
    dg_put32(record+0xc4,320);dg_put32(record+0xc4+4,1664);
    dg_put32(record+0xc4+8,DC_W);dg_put32(record+0xc4+12,DC_H);dg_put32(record+0x104,1);
    return method(fb,5,0,0,record,sizeof(record),0,0,0,0);
}
#endif
