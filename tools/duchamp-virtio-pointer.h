/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_VIRTIO_POINTER_H
#define DUCHAMP_VIRTIO_POINTER_H
/* Fixed little-endian VirtIO input events; no client pointers in this ABI. */
typedef unsigned int vp_u32;
typedef unsigned short vp_u16;
typedef unsigned long long vp_u64;
enum { VP_VERSION=1,VP_QUEUE=64,VP_ABS_MAX=32767,VP_CONNECTED=1,VP_REPORT=2,VP_FAULT=4 };
struct vp_event {vp_u16 type,code;vp_u32 value;};
struct vp_report {vp_u32 version,generation,sequence,flags,x,y,left,rejected;};
struct vp_state {vp_u32 x,y,left,sequence,generation,rejected,invalid;};
static inline void vp_init(struct vp_state *s,vp_u32 generation) {
    *s=(struct vp_state){.generation=generation};
}
static inline int vp_event(struct vp_state *s,struct vp_event e,struct vp_report *r) {
    if(e.type==3 && (e.code==0 || e.code==1)) {
        if(e.value>VP_ABS_MAX){s->invalid=1;s->rejected++;return -1;}
        if(e.code)s->y=e.value;else s->x=e.value;
    }else if(e.type==1 && e.code==0x110) {
        if(e.value>1){s->invalid=1;s->rejected++;return -1;}s->left=e.value;
    }else if(e.type==0 && e.code==0) {
        if(s->invalid){s->invalid=0;s->left=0;return -1;}
        if(s->sequence==0xffffffffu)return -1;
        *r=(struct vp_report){VP_VERSION,s->generation,++s->sequence,VP_REPORT,s->x,s->y,s->left,s->rejected};return 1;
    }else if(e.type==0 && e.code==3){s->invalid=1;s->left=0;s->rejected++;return -1;}
    return 0;
}
static inline int vp_coordinates(const struct vp_report *r,vp_u32 w,vp_u32 h,vp_u32 *x,vp_u32 *y) {
    if(!r || !x || !y || r->version!=VP_VERSION || !r->generation || r->x>VP_ABS_MAX || r->y>VP_ABS_MAX ||
       r->left>1 || !w || !h || w>4096 || h>4096 || (r->flags!=VP_CONNECTED && r->flags!=VP_REPORT))return 0;
    *x=(vp_u32)(((vp_u64)r->x*(w-1)+VP_ABS_MAX/2)/VP_ABS_MAX);
    *y=(vp_u32)(((vp_u64)r->y*(h-1)+VP_ABS_MAX/2)/VP_ABS_MAX);return 1;
}
static inline int vp_used(vp_u32 id,vp_u32 length,vp_u16 pending) {
    return id<VP_QUEUE && length==sizeof(struct vp_event) && pending<=VP_QUEUE;
}
#endif
