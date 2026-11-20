/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_VIRTIO_TOUCH_H
#define DUCHAMP_VIRTIO_TOUCH_H
#include "duchamp-virtio-pointer.h"
/* QEMU10.2.1 advertises slots/tracking IDs 0..0xa, inclusive. */
enum { MT_VERSION=2,MT_SLOTS=11,MT_MASK=(1u<<MT_SLOTS)-1,MT_ID_MAX=10,
       MT_CONNECTED=1,MT_REPORT=2,MT_CANCEL=4 };
struct mt_contact {vp_u32 id,x,y,active;};
struct mt_report {vp_u32 version,generation,sequence,flags,changed,active,rejected,reserved;
    struct mt_contact contacts[MT_SLOTS];};
struct mt_state {struct mt_report frame;vp_u32 slot,invalid,xy[MT_SLOTS];};
static inline void mt_init(struct mt_state *s,vp_u32 generation) {
    *s=(struct mt_state){.frame={.version=MT_VERSION,.generation=generation,.flags=MT_REPORT}};
}
static inline int mt_valid(const struct mt_report *r) {
    if(r->version!=MT_VERSION || !r->generation || r->reserved ||
       (r->flags!=MT_CONNECTED && r->flags!=MT_REPORT && r->flags!=(MT_REPORT|MT_CANCEL)) ||
       ((r->active|r->changed)&~MT_MASK))return 0;
    if(r->flags==MT_CONNECTED && (r->sequence || r->active || r->changed))return 0;
    if((r->flags&MT_CANCEL) && r->active)return 0;
    for(unsigned i=0;i<MT_SLOTS;i++) {
        const struct mt_contact *c=&r->contacts[i];
        if(c->id>MT_ID_MAX || c->active>1 || c->active!=((r->active>>i)&1) || c->x>VP_ABS_MAX || c->y>VP_ABS_MAX)return 0;
        for(unsigned j=0;j<i;j++)if(c->active && r->contacts[j].active && c->id==r->contacts[j].id)return 0;
    }
    return 1;
}
static inline int mt_event(struct mt_state *s,struct vp_event e,struct mt_report *r) {
    if(e.type==0 && e.code==0) {
        if(s->frame.sequence==0xffffffffu)return -1;
        for(unsigned i=0;i<MT_SLOTS;i++)if(s->frame.contacts[i].active && s->xy[i]!=3)s->invalid=1;
        if(s->invalid) {
            vp_u32 gen=s->frame.generation,seq=s->frame.sequence,rejected=s->frame.rejected;
            mt_init(s,gen);s->frame.sequence=seq;s->frame.rejected=rejected;
            s->frame.changed=MT_MASK;s->frame.flags=MT_REPORT|MT_CANCEL;
        }
        s->frame.sequence++;*r=s->frame;s->frame.changed=0;s->frame.flags=MT_REPORT;return 1;
    }
    if(e.type==0 && e.code==3){s->invalid=1;s->frame.rejected++;return 0;}
    if(e.type!=3)return 0; /* BTN_TOUCH is redundant with per-slot tracking IDs. */
    if(e.code==0x2f) {
        if(e.value>=MT_SLOTS){s->invalid=1;s->frame.rejected++;return 0;}
        s->slot=e.value;return 0;
    }
    if(s->invalid)return 0;
    struct mt_contact *c=&s->frame.contacts[s->slot];vp_u32 bit=1u<<s->slot;
    if(e.code==0x39) {
        if(e.value==0xffffffffu) {
            if(!c->active)goto invalid;
            c->active=0;s->frame.active&=~bit;
        }else {
            if(e.value>MT_ID_MAX || (c->active && c->id!=e.value))goto invalid;
            for(unsigned i=0;i<MT_SLOTS;i++)if(i!=s->slot && s->frame.contacts[i].active && s->frame.contacts[i].id==e.value)goto invalid;
            if(!c->active){*c=(struct mt_contact){.id=e.value,.active=1};s->xy[s->slot]=0;}
            s->frame.active|=bit;
        }
        s->frame.changed|=bit;
    }else if(e.code==0x35 || e.code==0x36) {
        if(!c->active || e.value>VP_ABS_MAX)goto invalid;
        if(e.code==0x35){c->x=e.value;s->xy[s->slot]|=1;}else{c->y=e.value;s->xy[s->slot]|=2;}
        s->frame.changed|=bit;
    }
    return 0;
invalid:s->invalid=1;s->frame.rejected++;return 0;
}
static inline int mt_follows(const struct mt_report *old,const struct mt_report *r) {
    if(!mt_valid(r) || r->flags==MT_CONNECTED || r->generation!=old->generation ||
       old->sequence==0xffffffffu || r->sequence!=old->sequence+1)return 0;
    if(r->flags&MT_CANCEL)return 1;
    for(unsigned i=0;i<MT_SLOTS;i++) {
        struct mt_contact a=old->contacts[i],b=r->contacts[i];
        if(!(r->changed&(1u<<i))) {
            if(a.id!=b.id || a.x!=b.x || a.y!=b.y || a.active!=b.active)return 0;
        }else if((a.active && a.id!=b.id) || (!a.active && !b.active))return 0;
    }
    return 1;
}
static inline vp_u32 mt_axis(vp_u32 raw,vp_u32 dimension) {
    return (vp_u32)(((vp_u64)raw*(dimension-1)+VP_ABS_MAX/2)/VP_ABS_MAX);
}
#endif
