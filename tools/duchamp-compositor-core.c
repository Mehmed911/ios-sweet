/* SPDX-License-Identifier: 0BSD */
/* Single-threaded scene state. All pixels belong to the compositor. */
#include "duchamp-compositor-core.h"
static int same(struct dc_owner a,struct dc_owner b) {return a.pid==b.pid && a.birth==b.birth;}
static struct dc_layer *find(struct dc_scene *s,dg_u32 id) {
    for(unsigned i=0;i<DC_LAYERS;i++)if(s->layers[i].active && s->layers[i].id==id)return &s->layers[i];
    return 0;
}
static int rect(struct dc_rect r,dg_u32 w,dg_u32 h) {
    return r.w && r.h && r.x<w && r.y<h && r.w<=w-r.x && r.h<=h-r.y;
}
static void damage(struct dc_scene *s,struct dc_rect r) {
    struct dc_rect *d=&s->dirty;
    if(!d->w){*d=r;return;}
    dg_u32 x=d->x<r.x?d->x:r.x,y=d->y<r.y?d->y:r.y;
    dg_u32 endx=d->x+d->w>r.x+r.w?d->x+d->w:r.x+r.w;
    dg_u32 endy=d->y+d->h>r.y+r.h?d->y+d->h:r.y+r.h;
    *d=(struct dc_rect){x,y,endx-x,endy-y};
}
static dg_u32 top(struct dc_scene *s) {
    struct dc_layer *best=0;
    for(unsigned i=0;i<DC_LAYERS;i++) {
        struct dc_layer *l=&s->layers[i];
        if(l->active && (!best || l->z>best->z || (l->z==best->z && l->id>best->id)))best=l;
    }
    return best?best->id:0;
}
void dc_init(struct dc_scene *s) {
    memset(s,0,sizeof(*s));s->dirty=(struct dc_rect){0,0,DC_W,DC_H};
    dc_render(s);
}
int dc_bounds(dg_u32 w,dg_u32 h,dg_u64 stride,dg_u64 bytes) {
    if(!w || w>DC_W || !h || h>DC_H || (stride&3) || stride<(dg_u64)w*4 || bytes<(dg_u64)w*4)return 0;
    /* Division avoids (height-1)*stride overflow, even for adversarial metadata. */
    return h==1 || stride<=(bytes-(dg_u64)w*4)/(h-1);
}
int dc_add(struct dc_scene *s,struct dc_owner owner,dg_u32 id,dg_u32 w,dg_u32 h,dg_u32 x,dg_u32 y,int z) {
    struct dc_rect r={x,y,w,h};
    if(owner.pid<=1 || !id || find(s,id) || !rect(r,DC_W,DC_H) || z< -8 || z>8)return DC_INVALID;
    for(unsigned i=0;i<DC_LAYERS;i++)if(!s->layers[i].active) {
        struct dc_layer *l=&s->layers[i];memset(l,0,sizeof(*l));
        l->owner=owner;l->id=id;l->w=w;l->h=h;l->capacity_w=w;l->capacity_h=h;l->x=x;l->y=y;l->z=z;l->active=1;
        damage(s,r);s->focus=top(s);return DC_OK;
    }
    return DC_FULL;
}
int dc_commit(struct dc_scene *s,struct dc_owner owner,dg_u32 id,dg_u32 seq,const void *pixels,dg_u64 stride,dg_u64 bytes,struct dc_rect r) {
    struct dc_layer *l=find(s,id);
    if(!l)return DC_INVALID;
    if(!same(owner,l->owner))return DC_OWNER;
    if(!seq || seq<=l->seq)return DC_STALE;
    if(!pixels || !dc_bounds(l->capacity_w,l->capacity_h,stride,bytes) || !rect(r,l->capacity_w,l->capacity_h))return DC_INVALID;
    /* Snapshot only the committed rectangle; never retain a client's pointer. */
    for(dg_u32 y=r.y;y<r.y+r.h;y++)
        memcpy(l->pixels+y*l->capacity_w+r.x,(const dg_u8 *)pixels+(dg_u64)y*stride+r.x*4,r.w*4);
    l->seq=seq;
    if(r.x<l->w && r.y<l->h) {
        if(r.w>l->w-r.x)r.w=l->w-r.x;
        if(r.h>l->h-r.y)r.h=l->h-r.y;
        r.x+=l->x;r.y+=l->y;damage(s,r);
    }
    return DC_OK;
}
int dc_z(struct dc_scene *s,struct dc_owner owner,dg_u32 id,int z) {
    struct dc_layer *l=find(s,id);if(!l || z< -8 || z>8)return DC_INVALID;
    if(!same(owner,l->owner))return DC_OWNER;
    l->z=z;damage(s,(struct dc_rect){l->x,l->y,l->w,l->h});return DC_OK;
}
int dc_focus(struct dc_scene *s,struct dc_owner owner,dg_u32 id) {
    struct dc_layer *l=find(s,id);if(!l)return DC_INVALID;
    if(!same(owner,l->owner))return DC_OWNER;
    s->focus=id;return DC_OK;
}
int dc_view(struct dc_scene *s,struct dc_owner owner,dg_u32 id,struct dc_rect r) {
    struct dc_layer *l=find(s,id);if(!l)return DC_INVALID;
    if(!same(owner,l->owner))return DC_OWNER;
    if(!rect(r,DC_W,DC_H) || r.w>l->capacity_w || r.h>l->capacity_h)return DC_INVALID;
    damage(s,(struct dc_rect){l->x,l->y,l->w,l->h});
    l->x=r.x;l->y=r.y;l->w=r.w;l->h=r.h;damage(s,r);return DC_OK;
}
int dc_remove_id(struct dc_scene *s,struct dc_owner owner,dg_u32 id) {
    struct dc_layer *l=find(s,id);if(!l)return DC_INVALID;
    if(!same(owner,l->owner))return DC_OWNER;
    damage(s,(struct dc_rect){l->x,l->y,l->w,l->h});
    if(s->capture==id)s->capture=0;
    memset(l,0,sizeof(*l));if(s->focus==id)s->focus=top(s);return DC_OK;
}
int dc_input(struct dc_scene *s,dg_u32 down,struct dc_route *r) {
    if(down>1 || (down && s->capture) || (!down && !s->capture))return 0;
    struct dc_layer *l=find(s,down?s->focus:s->capture);
    if(!l)return 0;
    s->capture=down?l->id:0;*r=(struct dc_route){l->owner,l->id,down};return 1;
}
unsigned dc_remove(struct dc_scene *s,struct dc_owner owner) {
    unsigned n=0;
    for(unsigned i=0;i<DC_LAYERS;i++) {
        struct dc_layer *l=&s->layers[i];
        if(l->active && same(owner,l->owner)) {
            damage(s,(struct dc_rect){l->x,l->y,l->w,l->h});
            if(s->capture==l->id)s->capture=0;
            memset(l,0,sizeof(*l));n++;
        }
    }
    if(!find(s,s->focus))s->focus=top(s);
    return n;
}
static dg_u32 over(dg_u32 dst,dg_u32 src) {
    unsigned a=src>>24;dg_u32 out=0xff000000u;
    for(unsigned shift=0;shift<24;shift+=8) {
        unsigned c=(((src>>shift)&255)*a+((dst>>shift)&255)*(255-a)+127)/255;
        out|=c<<shift;
    }
    return out;
}
unsigned dc_render(struct dc_scene *s) {
    struct dc_rect d=s->dirty;if(!d.w)return 0;
    unsigned order[DC_LAYERS],n=0;
    for(unsigned i=0;i<DC_LAYERS;i++)if(s->layers[i].active) {
        unsigned at=n;
        while(at && (s->layers[order[at-1]].z>s->layers[i].z ||
              (s->layers[order[at-1]].z==s->layers[i].z && s->layers[order[at-1]].id>s->layers[i].id))) {
            order[at]=order[at-1];at--;
        }
        order[at]=i;n++;
    }
    unsigned back=s->front^1;memcpy(s->frames[back],s->frames[s->front],sizeof(s->frames[0]));
    for(dg_u32 y=d.y;y<d.y+d.h;y++)for(dg_u32 x=d.x;x<d.x+d.w;x++) {
        dg_u32 color=0xff102030;
        for(unsigned i=0;i<n;i++) {
            struct dc_layer *l=&s->layers[order[i]];
            if(x>=l->x && x-l->x<l->w && y>=l->y && y-l->y<l->h)
                color=over(color,l->pixels[(y-l->y)*l->capacity_w+x-l->x]);
        }
        s->frames[back][y*DC_W+x]=color;
    }
    s->front=back;s->epoch++;s->dirty=(struct dc_rect){0};return d.w*d.h;
}
