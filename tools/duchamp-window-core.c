/* SPDX-License-Identifier: 0BSD */
#include "duchamp-window-core.h"
static int owner_eq(struct dc_owner a,struct dc_owner b){return a.pid==b.pid && a.birth==b.birth;}
static int bounds(struct dc_rect r) {
    return r.w>=DW_MIN_W && r.h>=DW_MIN_H && r.x<DC_W && r.y<DC_H && r.w<=DC_W-r.x && r.h<=DC_H-r.y;
}
static struct dw_window *window(struct dw_manager *m,dg_u32 id){return id && id<=DW_WINDOWS && m->windows[id-1].active?&m->windows[id-1]:0;}
void dw_init(struct dw_manager *m){memset(m,0,sizeof(*m));}
int dw_create(struct dw_manager *m,struct dc_owner o,dg_u32 id,struct dc_rect r) {
    if(!id || id>DW_WINDOWS || o.pid<=1 || window(m,id) || !bounds(r))return DC_INVALID;
    if(id==1 && (r.x || r.y || r.w!=DC_W || r.h!=DC_H))return DC_INVALID;
    m->windows[id-1]=(struct dw_window){.owner=o,.rect=r,.id=id,.active=1,.visible=1,.z=id==1?-6:(int)id};
    if(id>1)m->focus=id;return DC_OK;
}
int dw_geometry(struct dw_manager *m,struct dc_owner o,dg_u32 id,struct dc_rect r) {
    struct dw_window *w=window(m,id);if(!w || id==1 || !bounds(r))return DC_INVALID;
    if(!owner_eq(w->owner,o))return DC_OWNER;
    w->rect=r;return DC_OK;
}
int dw_focus(struct dw_manager *m,struct dc_owner o,dg_u32 id) {
    struct dw_window *w=window(m,id);if(!w || id==1)return DC_INVALID;
    if(!owner_eq(w->owner,o))return DC_OWNER;
    for(unsigned i=1;i<DW_WINDOWS;i++)if(m->windows[i].active)m->windows[i].z=2;
    w->z=3;w->visible=1;m->focus=id;return DC_OK;
}
static void restore_focus(struct dw_manager *m) {
    struct dw_window *best=0;
    for(unsigned i=1;i<DW_WINDOWS;i++)if(m->windows[i].active && m->windows[i].visible &&
        (!best || m->windows[i].z>best->z || (m->windows[i].z==best->z && m->windows[i].id>best->id)))best=&m->windows[i];
    m->focus=best?best->id:0;
}
int dw_background(struct dw_manager *m,struct dc_owner o,dg_u32 id) {
    struct dw_window *w=window(m,id);if(!w || id==1)return DC_INVALID;
    if(!owner_eq(w->owner,o))return DC_OWNER;
    w->visible=0;if(m->capture==id){m->capture=0;m->pressed=0;m->mode=0;}
    for(unsigned i=0;i<MT_SLOTS;i++)if(m->contacts[i].active && m->contacts[i].target==id){m->contacts[i].target=0;w->cancelled++;}
    w->contacts=0;if(m->focus==id)restore_focus(m);return DC_OK;
}
int dw_destroy(struct dw_manager *m,struct dc_owner o,dg_u32 id) {
    struct dw_window *w=window(m,id);if(!w)return DC_INVALID;
    if(!owner_eq(w->owner,o))return DC_OWNER;
    for(unsigned i=0;i<MT_SLOTS;i++)if(m->contacts[i].active && m->contacts[i].target==id)m->contacts[i].target=0;
    memset(w,0,sizeof(*w));if(m->capture==id){m->capture=0;m->pressed=0;m->mode=0;}
    if(m->focus==id)restore_focus(m);
    return DC_OK;
}
int dw_pointer(struct dw_manager *m,dg_u32 x,dg_u32 y,dg_u32 down,dg_u32 *target) {
    if(x>=DC_W || y>=DC_H || down>1 || !target)return DC_INVALID;
    *target=0;m->pointer_x=x;m->pointer_y=y;
    if(down && !m->pressed) {
        struct dw_window *best=0;
        for(unsigned i=1;i<DW_WINDOWS;i++) {
            struct dw_window *w=&m->windows[i];struct dc_rect r=w->rect;
            if(w->active && w->visible && x>=r.x && y>=r.y && x-r.x<r.w && y-r.y<r.h && (!best || w->z>best->z || (w->z==best->z && w->id>best->id)))best=w;
        }
        m->capture=best?best->id:0;m->pressed=1;m->origin_x=x;m->origin_y=y;
        if(best) {
            dw_focus(m,best->owner,best->id);m->original=best->rect;
            m->mode=x-best->rect.x>=best->rect.w-5 && y-best->rect.y>=best->rect.h-5?2:y-best->rect.y<DW_TITLE?1:0;
        }
    }
    struct dw_window *w=window(m,m->capture);
    if(w) {
        struct dc_rect r=m->original;
        int dx=(int)x-(int)m->origin_x,dy=(int)y-(int)m->origin_y;
        if(m->mode==1) {
            int nx=(int)r.x+dx,ny=(int)r.y+dy;
            if(nx<0)nx=0;if(ny<10)ny=10;
            if(nx>DC_W-(int)r.w)nx=DC_W-r.w;if(ny>DC_H-16-(int)r.h)ny=DC_H-16-r.h;
            if(ny<0)ny=0;r.x=(dg_u32)nx;r.y=(dg_u32)ny;w->rect=r;
        }else if(m->mode==2) {
            int nw=(int)r.w+dx,nh=(int)r.h+dy;
            if(nw<DW_MIN_W)nw=DW_MIN_W;if(nh<DW_MIN_H)nh=DW_MIN_H;
            if(nw>DC_W-(int)r.x)nw=DC_W-r.x;if(nh>DC_H-16-(int)r.y)nh=DC_H-16-r.y;
            if(nh<DW_MIN_H)nh=DW_MIN_H;r.w=(dg_u32)nw;r.h=(dg_u32)nh;w->rect=r;
        }
        w->events++;w->down=down;*target=w->id;
    }
    if(!down){m->pressed=0;m->capture=0;m->mode=0;}
    return DC_OK;
}
/* phase: up0, down1, move2, cancel3. Capture is per contact, not global. */
int dw_touch(struct dw_manager *m,dg_u32 slot,dg_u32 id,dg_u32 x,dg_u32 y,dg_u32 phase,dg_u32 *target) {
    if(slot>=MT_SLOTS || id>MT_ID_MAX || x>=DC_W || y>=DC_H || phase>3 || !target)return DC_INVALID;
    struct dw_contact *c=&m->contacts[slot];*target=0;
    if(phase==1) {
        if(c->active)return DC_STALE;
        for(unsigned i=0;i<MT_SLOTS;i++)if(m->contacts[i].active && m->contacts[i].id==id)return DC_STALE;
        struct dw_window *best=0;
        for(unsigned i=1;i<DW_WINDOWS;i++) {
            struct dw_window *w=&m->windows[i];struct dc_rect r=w->rect;
            if(w->active && w->visible && x>=r.x && y>=r.y && x-r.x<r.w && y-r.y<r.h &&
               (!best || w->z>best->z || (w->z==best->z && w->id>best->id)))best=w;
        }
        *c=(struct dw_contact){.active=1,.id=id,.target=best?best->id:0,.origin_x=x,.origin_y=y};
        if(best) {
            dw_focus(m,best->owner,best->id);c->original=best->rect;best->contacts++;
            c->mode=x-best->rect.x>=best->rect.w-5 && y-best->rect.y>=best->rect.h-5?2:y-best->rect.y<DW_TITLE?1:0;
            for(unsigned i=0;i<MT_SLOTS;i++)if(i!=slot && m->contacts[i].active && m->contacts[i].target==best->id && m->contacts[i].mode)c->mode=0;
        }
    }else if(!c->active || c->id!=id)return DC_STALE;
    c->x=x;c->y=y;m->pointer_x=x;m->pointer_y=y;
    struct dw_window *w=window(m,c->target);
    if(w) {
        if(phase==2 && c->mode) {
            struct dc_rect r=c->original;int dx=(int)x-(int)c->origin_x,dy=(int)y-(int)c->origin_y;
            if(c->mode==1) {
                int nx=(int)r.x+dx,ny=(int)r.y+dy;
                if(nx<0)nx=0;if(ny<10)ny=10;
                if(nx>DC_W-(int)r.w)nx=DC_W-r.w;if(ny>DC_H-16-(int)r.h)ny=DC_H-16-r.h;
                if(ny<0)ny=0;r.x=(dg_u32)nx;r.y=(dg_u32)ny;
            }else {
                int nw=(int)r.w+dx,nh=(int)r.h+dy;
                if(nw<DW_MIN_W)nw=DW_MIN_W;if(nh<DW_MIN_H)nh=DW_MIN_H;
                if(nw>DC_W-(int)r.x)nw=DC_W-r.x;if(nh>DC_H-16-(int)r.y)nh=DC_H-16-r.y;
                if(nh<DW_MIN_H)nh=DW_MIN_H;r.w=(dg_u32)nw;r.h=(dg_u32)nh;
            }w->rect=r;
        }
        w->touch_events++;if(phase==3)w->cancelled++;*target=w->id;
        if((phase==0 || phase==3) && w->contacts)w->contacts--;
    }
    if(phase==0 || phase==3)*c=(struct dw_contact){0};return DC_OK;
}
void dw_pixels(const struct dw_manager *m,dg_u32 id,dg_u32 *p) {
    const struct dw_window *w=&m->windows[id-1];
    memset(p,0,DC_PIXELS*4);
    for(dg_u32 y=0;y<w->rect.h;y++)for(dg_u32 x=0;x<w->rect.w;x++) {
        dg_u32 c;
        if(id==1) {
            c=0xff183040;
            if(y<10)c=0xff102030;
            if(y>=DC_H-16)c=0xff102030;
            if(y>=DC_H-12 && y<DC_H-4 && ((x>=12 && x<38)||(x>=48 && x<74)))c=x<40?0xffe28a50:0xff589cdb;
            if(y>=3 && y<6 && x>=6 && x<50 && (x%5)<3)c=0xffd5e4ed;
        }else {
            c=id==2?0xffe28a50:0xff589cdb;
            if(y<DW_TITLE)c=m->focus==id?0xffe8edf0:0xff7a8a98;
            if(x==0 || y==0 || x==w->rect.w-1 || y==w->rect.h-1)c=0xff26323c;
            if(y>=3 && y<6 && x>=5 && x<25 && (x%5)<3)c=0xff26323c;
            if(y>=DW_TITLE+4 && y<DW_TITLE+8 && x>=6 && x<w->rect.w-6)c=0xfff5e9dc;
            if(x>=w->rect.w-5 && y>=w->rect.h-5)c=0xff26323c;
        }
        p[y*DC_W+x]=c;
    }
}
void dw_cursor(const struct dw_manager *m,dg_u32 *p) {
    memset(p,0,DC_PIXELS*4);
    unsigned held=m->pressed;for(unsigned i=0;i<MT_SLOTS;i++)held|=m->contacts[i].active;
    for(unsigned y=0;y<5 && m->pointer_y+y<DC_H;y++)for(unsigned x=0;x<4 && m->pointer_x+x<DC_W;x++)
        if(x<=y/2)p[(m->pointer_y+y)*DC_W+m->pointer_x+x]=held?0xffffdd55:0xfff3f5f7;
}
