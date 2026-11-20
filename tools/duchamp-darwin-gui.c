/* SPDX-License-Identifier: 0BSD */
/* QEMU-only native Darwin experiment. No Apple private display protocol. */
#include "duchamp-compositor-iokit.h"
#include "duchamp-window-core.h"
#include "duchamp-gui-wire.h"
#include "duchamp-pointer-wire.h"
#include "duchamp-app-wire.h"
#include "duchamp-touch-wire.h"
extern void abort(void) __attribute__((noreturn));
extern dg_u32 bootstrap_port;
extern int bootstrap_check_in(dg_u32,const char *,dg_u32 *),bootstrap_look_up(dg_u32,const char *,dg_u32 *);
extern int mach_port_request_notification(dg_u32,dg_u32,int,dg_u32,dg_u32,int,dg_u32 *);
extern void mach_msg_destroy(void *);
extern int fork(void),waitpid(int,int *,int),execve(const char *,char *const *,char *const *);
extern char ***_NSGetEnviron(void);
extern void _exit(int) __attribute__((noreturn));
static int ap_rpc(dg_u32,unsigned,unsigned,struct dc_owner,struct gw_identity *);
static void drop(dg_u32 p){if(p)mach_port_deallocate(mach_task_self_,p);}
static int failure(const char *what,int rc){ipc_note("FAIL %s rc=0x%x",what,rc);return 1;}
static dg_u32 lookup(const char *name) {
    dg_u32 p=0;for(unsigned i=0;i<100;i++){if(!bootstrap_look_up(bootstrap_port,name,&p) && p)return p;usleep(100000);}return 0;
}
static int dc_rpc(dg_u32 remote,struct dc_request b,dg_u32 port,dg_u32 inbox,struct dc_answer *a) {
    union {struct dc_registration r;struct dc_packet p;dg_u8 bytes[256];} m={0};
    dg_u32 reply=mig_get_reply_port(),size=b.op==DC_REGISTER?sizeof(m.r):sizeof(m.p);
    m.p.h=(struct dg_head){19u|(21u<<8)|(b.op==DC_REGISTER?0x80000000u:0),size,remote,reply,0,DC_MSG};
    if(b.op==DC_REGISTER){m.r.count=2;m.r.surface=(struct dg_port){port,0,0,19,0};m.r.inbox=(struct dg_port){inbox,0,0,20,0};m.r.body=b;}
    else m.p.body=b;
    int rc=mach_msg(&m,1|2|0x100,size,sizeof(m),reply,3000,0);
    if(rc){mig_dealloc_reply_port(reply);return rc;}
    if(m.p.h.id!=DC_MSG+100 || m.p.h.size!=sizeof(struct dc_reply) || (m.p.h.bits&0x80000000u))return -1;
    memcpy(a,m.bytes+24,sizeof(*a));return 0;
}
struct backend {struct dc_owner owner;dg_u32 connection,inbox;struct di_surface s;};
static struct backend imported[DC_LAYERS];
static struct dc_scene composition;
static int compositor(void) {
    if(ipc_identity("gui-compositor"))return 1;
    dg_u32 master=0,service=0;if(host_get_io_main(mach_host_self(),&master))return failure("master",-1);
    dg_u32 root=match(master,"IOCoreSurfaceRoot"),f=match(master,"AppleCLCD"),fb=open_client(f,0),connection=open_client(root,0);
    struct di_surface frames[2];
    if(!root || !fb || !connection || di_create(connection,DC_W,DC_H,&frames[0]) || di_create(connection,DC_W,DC_H,&frames[1]) ||
       bootstrap_check_in(bootstrap_port,GW_COMPOSITOR,&service))return failure("compositor startup",-1);
    dc_init(&composition);ipc_note("READY pid=%d size=%ux%u",getpid(),DC_W,DC_H);
    for(;;) {
        union {struct dc_registration r;struct dc_packet p;dg_u8 bytes[512];} m={0};
        int rc=mach_msg(&m,2|0x100|(3u<<24),0,sizeof(m),service,50,0);
        if(!rc) {
            struct dc_owner owner={0};if(!dc_audit_peer(&m,sizeof(m),&owner))return failure("audit",-1);
            if(m.p.h.id==72 && m.p.h.size==36 && !owner.pid && !(m.p.h.bits&0x80000000u)) {
                dg_u32 name=dg_get32(m.bytes+32);
                for(unsigned i=0;i<DC_LAYERS;i++)if(imported[i].inbox==name) {
                    struct backend *p=&imported[i];dg_u32 id=p->s.id;
                    if(dc_remove_id(&composition,p->owner,id) || di_close(p->connection))return failure("cleanup",-1);
                    drop(name);drop(name);memset(p,0,sizeof(*p));ipc_note("CLEANUP surface=%u kernel_dead_name=1",id);break;
                }
            }else {
                int complex=(m.p.h.bits&0x80000000u)!=0;struct dc_request b=complex?m.r.body:m.p.body;
                int status=DC_INVALID,slot=-1;
                int valid=owner.pid>1 && ipc_path_matches(owner.pid,"/sbin/duchamp-window-manager") && m.p.h.id==DC_MSG &&
                    b.version==DC_VERSION && !b.reserved && ((complex && m.p.h.size==sizeof(m.r) && b.op==DC_REGISTER &&
                    m.r.count==2 && !m.r.surface.type && !m.r.inbox.type && m.r.surface.disposition==17 && m.r.inbox.disposition==17) ||
                    (!complex && m.p.h.size==sizeof(m.p) && b.op!=DC_REGISTER));
                for(unsigned i=0;i<DC_LAYERS;i++)if(imported[i].s.id==b.id && imported[i].owner.pid)slot=(int)i;
                if(valid && b.op==DC_REGISTER && b.role>=1 && b.role<=DC_LAYERS && !imported[b.role-1].owner.pid) {
                    struct backend p={.owner=owner,.connection=open_client(root,0),.inbox=m.r.inbox.name};dg_u32 old=0;
                    if(p.connection && !di_import(p.connection,m.r.surface.name,&p.s) && p.s.id==b.id && p.s.w==DC_W && p.s.h==DC_H &&
                       !dc_add(&composition,owner,p.s.id,DC_W,DC_H,0,0,b.z) &&
                       !dc_view(&composition,owner,p.s.id,(struct dc_rect){b.x,b.y,b.w,b.h}) &&
                       !dc_commit(&composition,owner,p.s.id,1,p.s.pixels,p.s.stride,p.s.bytes,(struct dc_rect){0,0,DC_W,DC_H}) &&
                       !mach_port_request_notification(mach_task_self_,p.inbox,72,1,service,21,&old)) {
                        drop(old);imported[b.role-1]=p;status=DC_OK;ipc_note("REGISTER owner=%u role=%u surface=%u",owner.pid,b.role,p.s.id);
                    }else {dc_remove_id(&composition,owner,p.s.id);if(p.connection)di_close(p.connection);drop(p.inbox);}
                    drop(m.r.surface.name);
                }else if(valid && slot>=0) {
                    struct backend *p=&imported[slot];
                    if(b.op==DC_VIEW)status=dc_view(&composition,owner,b.id,(struct dc_rect){b.x,b.y,b.w,b.h});
                    if(b.op==DC_SET_Z)status=dc_z(&composition,owner,b.id,b.z);
                    if(b.op==DC_DIRTY)status=dc_commit(&composition,owner,b.id,b.seq,p->s.pixels,p->s.stride,p->s.bytes,(struct dc_rect){b.x,b.y,b.w,b.h});
                }
                if(complex && !(valid && b.op==DC_REGISTER && b.role>=1 && b.role<=DC_LAYERS && status==DC_OK)) {
                    /* A rejected valid registration has already released its received rights. */
                    if(!valid || b.op!=DC_REGISTER || b.role<1 || b.role>DC_LAYERS || imported[b.role-1].owner.pid) {
                        dg_u32 reply=m.p.h.remote;m.p.h.remote=0;mach_msg_destroy(&m);m.p.h.remote=reply;
                    }
                }
                struct dc_reply r={{18,sizeof(r),m.p.h.remote,0,0,DC_MSG+100},{.status=status,.id=b.id,.epoch=composition.epoch}};
                if(r.h.remote && mach_msg(&r,1|0x10,sizeof(r),0,0,1000,0))return failure("reply",-1);
            }
        }else if(rc!=0x10004003)return failure("receive",rc);
        unsigned changed=dc_render(&composition);
        dg_u64 swap=0;if(di_present(fb,&frames[composition.front],composition.frames[composition.front],&swap))return failure("present",-1);
        if(changed)ipc_note("PRESENT surface=%u swap=%llu epoch=%u",frames[composition.front].id,swap,composition.epoch);
    }
}
struct managed {
    struct dc_owner owner;dg_u32 inbox,connection,event_port,seq,paint_seq;
    struct di_surface surface;dg_u32 pixels[DC_PIXELS];
};
static struct managed managed[DC_LAYERS];
static struct dw_manager windows;
static int applications_mode;
static dg_u32 compositor_port,root_service,wm_service,wm_epoch;
static int backend_open(unsigned index) {
    struct managed *p=&managed[index];p->connection=open_client(root_service,0);
    if(!p->connection || di_create(p->connection,DC_W,DC_H,&p->surface) || mach_port_allocate(mach_task_self_,1,&p->event_port))return -1;
    dg_u64 in=p->surface.id,out=0;dg_u32 count=1;
    if(method(p->connection,35,&in,1,0,0,0,0,&out,&count) || count!=1 || !out || out>0xffffffffu)return -1;
    struct dc_answer a;struct dc_request b={.version=DC_VERSION,.op=DC_REGISTER,.role=index+1,.id=p->surface.id,
        .w=DC_W,.h=DC_H,.z=index==3?8:index==0?-6:2};
    int rc=dc_rpc(compositor_port,b,(dg_u32)out,p->event_port,&a);drop((dg_u32)out);p->seq=1;
    return rc?rc:(int)a.status;
}
static int backend_close(unsigned i) {
    struct managed *p=&managed[i];
    if(p->event_port)mach_port_destroy(mach_task_self_,p->event_port);
    if(p->connection && di_close(p->connection))return -1;
    p->event_port=p->connection=0;return 0;
}
static int update(void) {
    for(unsigned i=0;i<DC_LAYERS;i++) {
        struct managed *p=&managed[i];if(i<3 && !windows.windows[i].active)continue;
        if(!p->connection && backend_open(i))return -1;
        struct dc_rect r={0,0,DC_W,DC_H};int z=8;
        if(i==3)dw_cursor(&windows,p->surface.pixels);
        else {
            struct dw_window *w=&windows.windows[i];r=w->rect;z=w->z;
            if(w->visible)memcpy(p->surface.pixels,p->pixels,DC_PIXELS*4);
            else {memset(p->surface.pixels,0,DC_PIXELS*4);z=-8;}
            if(i && w->visible) {
                static dg_u32 decorations[DC_PIXELS];dw_pixels(&windows,i+1,decorations);
                for(unsigned y=0;y<r.h;y++)for(unsigned x=0;x<r.w;x++)
                    if(y<DW_TITLE || !x || x==r.w-1 || y==r.h-1 || (x>=r.w-5 && y>=r.h-5))
                        p->surface.pixels[y*DC_W+x]=decorations[y*DC_W+x];
            }
        }
        __atomic_thread_fence(__ATOMIC_SEQ_CST);struct dc_answer a;
        struct dc_request b={.version=DC_VERSION,.op=DC_VIEW,.id=p->surface.id,.x=r.x,.y=r.y,.w=r.w,.h=r.h};
        if(dc_rpc(compositor_port,b,0,0,&a) || a.status)return -1;
        b.op=DC_SET_Z;b.z=z;if(dc_rpc(compositor_port,b,0,0,&a) || a.status)return -1;
        b.op=DC_DIRTY;b.seq=++p->seq;b.x=b.y=0;b.w=DC_W;b.h=DC_H;
        if(dc_rpc(compositor_port,b,0,0,&a) || a.status)return -1;
    }
    wm_epoch++;return 0;
}
static int forget(unsigned i) {
    struct managed *p=&managed[i];dg_u32 pid=p->owner.pid;
    if(dw_destroy(&windows,p->owner,i+1) || backend_close(i))return -1;
    memset(p,0,sizeof(*p));ipc_note("CLIENT CLEANUP id=%u pid=%u",i+1,pid);return update();
}
static int touch_deliver(dg_u32 target,dg_u32 slot,dg_u32 id,dg_u32 x,dg_u32 y,dg_u32 phase) {
    dg_u8 bytes[GW_FIXED]={0};struct gw_request *event=(void *)bytes;
    event->h=(struct dg_head){19,GW_FIXED,managed[target-1].inbox,0,0,GW_MSG};
    event->b=(struct gw_body){.version=GW_VERSION,.op=GW_TOUCH_EVENT,.id=target,.x=x,.y=y,
        .w=slot,.h=id,.seq=windows.windows[target-1].touch_events,.value=phase};
    int rc=mach_msg(event,1|0x10,GW_FIXED,0,0,1000,0);
    return rc && rc!=0x10000003?DC_INVALID:DC_OK;
}
static int manager(void) {
    if(ipc_identity("gui-wm"))return 1;
    dg_u32 master=0;if(host_get_io_main(mach_host_self(),&master))return failure("master",-1);
    root_service=match(master,"IOCoreSurfaceRoot");compositor_port=lookup(GW_COMPOSITOR);
    if(!root_service || !compositor_port || bootstrap_check_in(bootstrap_port,GW_SERVICE,&wm_service))return failure("WM startup",-1);
    dw_init(&windows);if(update())return failure("initial cursor",-1);
    ipc_note("READY pid=%d compositor=%u canvas=%ux%u",getpid(),compositor_port,DC_W,DC_H);
    for(;;) {
        static union {struct gw_request r;dg_u8 bytes[sizeof(struct gw_request)+128];} m;
        memset(&m,0,sizeof(m));int rc=mach_msg(&m,2|0x100|(3u<<24),0,sizeof(m),wm_service,100,0);
        if(rc==0x10004003)continue;if(rc)return failure("WM receive",rc);
        struct dc_owner owner={0};if(!dc_audit_peer(&m,sizeof(m),&owner))return failure("WM audit",-1);
        if(m.r.h.id==71 && m.r.h.size==24 && !owner.pid && !(m.r.h.bits&0x80000000u))continue;
        if(m.r.h.id==72 && m.r.h.size==36 && !owner.pid && !(m.r.h.bits&0x80000000u)) {
            dg_u32 name=dg_get32(m.bytes+32);
            for(unsigned i=0;i<3;i++)if(managed[i].inbox==name && managed[i].owner.pid) {
                drop(name);drop(name);if(forget(i))return failure("dead client",-1);break;
            }
            continue;
        }
        struct gw_body b=m.r.b;int valid=gw_valid(&m.r,sizeof(m)) && owner.pid>1,status=DC_INVALID,changed=0;
        unsigned i=b.id-1;struct managed *p=i<3?&managed[i]:0;
        int shell=owner.pid>1 && ipc_path_matches(owner.pid,"/sbin/duchamp-gui-shell");
        int apps=owner.pid>1 && ipc_path_matches(owner.pid,"/sbin/duchamp-app-manager");
        if(valid && b.op==GW_CREATE && p && !p->owner.pid && (b.id!=1 || shell) && b.seq==1) {
            struct dc_rect r={b.x,b.y,b.w,b.h};
            status=applications_mode && b.id>1 && !ipc_path_matches(owner.pid,b.id==2?"/sbin/duchamp-app-red":"/sbin/duchamp-app-blue")?DC_OWNER:dw_create(&windows,owner,b.id,r);
            dg_u32 old=0;
            if(!status && mach_port_request_notification(mach_task_self_,m.r.inbox.name,72,1,wm_service,21,&old)) {
                dw_destroy(&windows,owner,b.id);status=DC_INVALID;
            }
            if(!status) {
                drop(old);p->owner=owner;p->inbox=m.r.inbox.name;p->paint_seq=1;
                memcpy(p->pixels,m.r.pixels,DC_PIXELS*4);changed=1;
                ipc_note("CREATE id=%u pid=%u birth=%u rect=%u,%u,%u,%u",b.id,owner.pid,owner.birth,b.x,b.y,b.w,b.h);
            }
        }else if(valid && b.op==GW_POINTER) {
            if(shell){dg_u32 target=0;status=dw_pointer(&windows,b.x,b.y,b.value,&target);changed=!status;
                if(!status) {
                    ipc_note("INPUT x=%u y=%u down=%u target=%u capture=%u",b.x,b.y,b.value,target,windows.capture);
                    if(target) {
                        dg_u8 bytes[GW_FIXED]={0};struct gw_request *event=(void *)bytes;
                        event->h=(struct dg_head){19,GW_FIXED,managed[target-1].inbox,0,0,GW_MSG};
                        event->b=(struct gw_body){.version=GW_VERSION,.op=GW_EVENT,.id=target,.x=b.x,.y=b.y,
                            .seq=windows.windows[target-1].events,.value=b.value};
                        int sent=mach_msg(event,1|0x10,GW_FIXED,0,0,1000,0);
                        if(sent && sent!=0x10000003)status=DC_INVALID;
                    }
                }
            }else status=DC_OWNER;
        }else if(valid && b.op==GW_TOUCH) {
            if(shell && applications_mode) {
                dg_u32 target=0;status=dw_touch(&windows,b.id-1,b.seq,b.x,b.y,b.value,&target);changed=!status;
                if(!status){ipc_note("TOUCH slot=%u contact=%u phase=%u target=%u x=%u y=%u",b.id-1,b.seq,b.value,target,b.x,b.y);
                    if(target)status=touch_deliver(target,b.id-1,b.seq,b.x,b.y,b.value);}
            }else status=DC_OWNER;
        }else if(valid && (b.op==GW_FOREGROUND || b.op==GW_BACKGROUND)) {
            status=DC_OWNER;
            if(apps && p && p->owner.pid) {
                /* Bind lifecycle controls to the exact current PID version. */
                if(b.w!=p->owner.pid || b.h!=p->owner.birth)status=DC_STALE;
                else if(b.op==GW_FOREGROUND)status=dw_focus(&windows,p->owner,b.id);
                else {
                    for(unsigned k=0;k<MT_SLOTS;k++)if(windows.contacts[k].active && windows.contacts[k].target==b.id) {
                        struct dw_contact *c=&windows.contacts[k];windows.windows[i].touch_events++;
                        if(touch_deliver(b.id,k,c->id,c->x,c->y,3))return failure("background cancel",-1);
                    }
                    status=dw_background(&windows,p->owner,b.id);
                }changed=!status;
            }
        }else if(valid && (b.op==GW_TERMINATE || b.op==GW_CRASH)) {
            status=DC_OWNER;
            if(apps && applications_mode && p && p->owner.pid) {
                if(b.w!=p->owner.pid || b.h!=p->owner.birth)status=DC_STALE;
                else {
                    dg_u8 bytes[GW_FIXED]={0};struct gw_request *event=(void *)bytes;
                    event->h=(struct dg_head){19,GW_FIXED,p->inbox,0,0,GW_MSG};
                    event->b=(struct gw_body){.version=GW_VERSION,.op=GW_LIFECYCLE_EVENT,.id=b.id,.value=b.op==GW_CRASH};
                    status=mach_msg(event,1|0x10,GW_FIXED,0,0,1000,0)?DC_INVALID:DC_OK;
                    ipc_note("APP EXIT REQUEST id=%u pid=%u birth=%u crash=%u",b.id,p->owner.pid,p->owner.birth,b.op==GW_CRASH);
                }
            }
        }else if(valid && b.op==GW_INFO) {
            status=(shell || apps || (p && p->owner.pid==owner.pid && p->owner.birth==owner.birth))?DC_OK:DC_OWNER;
        }else if(valid && b.op==GW_QUERY)status=DC_OK;
        else if(valid && p && p->owner.pid) {
            if(p->owner.pid!=owner.pid || p->owner.birth!=owner.birth)status=DC_OWNER;
            else if(b.op==GW_GEOMETRY){status=dw_geometry(&windows,owner,b.id,(struct dc_rect){b.x,b.y,b.w,b.h});changed=!status;}
            else if(b.op==GW_FOCUS){status=dw_focus(&windows,owner,b.id);changed=!status;}
            else if(b.op==GW_PAINT) {
                if(!b.seq || b.seq<=p->paint_seq)status=DC_STALE;
                else {memcpy(p->pixels,m.r.pixels,DC_PIXELS*4);p->paint_seq=b.seq;status=DC_OK;changed=1;}
            }
            else if(b.op==GW_DESTROY) {
                dg_u32 old=0;
                if(!mach_port_request_notification(mach_task_self_,p->inbox,72,0,0,21,&old)) {
                    drop(old);drop(p->inbox);status=forget(i)?DC_INVALID:DC_OK;
                }
            }
        }
        if((m.r.h.bits&0x80000000u) && !(valid && b.op==GW_CREATE && status==DC_OK)) {
            dg_u32 reply=m.r.h.remote;m.r.h.remote=0;mach_msg_destroy(&m);m.r.h.remote=reply;
        }
        if(changed && update())return failure("WM presentation",-1);
        struct gw_result a={.status=(dg_u32)status,.id=b.id,.pid=(dg_u32)getpid(),.focus=windows.focus,.epoch=wm_epoch};
        if(p && windows.windows[i].active) {
            struct dw_window *w=&windows.windows[i];a.active=1;a.events=w->events;a.down=w->down;
            a.x=w->rect.x;a.y=w->rect.y;a.w=w->rect.w;a.h=w->rect.h;
        }
        if(status)ipc_note("DENIED op=%u id=%u pid=%u status=%d",b.op,b.id,owner.pid,status);
        if(valid && b.op==GW_INFO) {
            struct gw_identity info={.status=(dg_u32)status,.id=b.id};
            if(!status && p && windows.windows[i].active){struct dw_window *w=&windows.windows[i];
                info.pid=p->owner.pid;info.birth=p->owner.birth;info.state=windows.focus==b.id?2:1;
                info.visible=w->visible;info.contacts=w->contacts;info.touch_events=w->touch_events;info.cancelled=w->cancelled;}
            struct gw_identity_reply reply={{18,sizeof(reply),m.r.h.remote,0,0,GW_MSG+101},info};
            if(reply.h.remote && mach_msg(&reply,1|0x10,sizeof(reply),0,0,1000,0))return failure("identity reply",-1);
            continue;
        }
        struct gw_reply reply={{18,sizeof(reply),m.r.h.remote,0,0,GW_MSG+100},a};
        if(reply.h.remote && mach_msg(&reply,1|0x10,sizeof(reply),0,0,1000,0))return failure("WM reply",-1);
    }
}
static int gw_rpc(dg_u32 remote,struct gw_body b,dg_u32 inbox,const dg_u32 *pixels,struct gw_result *a) {
    static union {struct gw_request r;dg_u8 bytes[sizeof(struct gw_request)+128];} m;
    memset(&m,0,sizeof(m));dg_u32 reply=mig_get_reply_port();b.version=GW_VERSION;
    b.bytes=pixels?DC_PIXELS*4:0;dg_u32 size=GW_FIXED+b.bytes;
    m.r.h=(struct dg_head){19u|(21u<<8)|(b.op==GW_CREATE?0x80000000u:0),size,remote,reply,0,GW_MSG};
    m.r.b=b;if(b.op==GW_CREATE){m.r.count=1;m.r.inbox=(struct dg_port){inbox,0,0,20,0};}
    if(pixels)memcpy(m.r.pixels,pixels,DC_PIXELS*4);
    int rc=mach_msg(&m,1|2|0x100,size,sizeof(m),reply,3000,0);
    if(rc){mig_dealloc_reply_port(reply);return rc;}
    if(m.r.h.id!=GW_MSG+100 || m.r.h.size!=sizeof(struct gw_reply) || (m.r.h.bits&0x80000000u))return -1;
    memcpy(a,m.bytes+24,sizeof(*a));return 0;
}
static dg_u32 client_pixels[DC_PIXELS];
static int gw_info(dg_u32 remote,unsigned id,struct gw_identity *a) {
    union {struct gw_request r;struct gw_identity_reply reply;dg_u8 bytes[256];} m={0};
    dg_u32 port=mig_get_reply_port();m.r.h=(struct dg_head){19u|(21u<<8),GW_FIXED,remote,port,0,GW_MSG};
    m.r.b=(struct gw_body){.version=GW_VERSION,.op=GW_INFO,.id=id};
    int rc=mach_msg(&m,1|2|0x100,GW_FIXED,sizeof(m),port,3000,0);
    if(rc){mig_dealloc_reply_port(port);return rc;}
    if(m.reply.h.id!=GW_MSG+101 || m.reply.h.size!=sizeof(m.reply) || m.reply.h.bits&0x80000000u)return -1;
    *a=m.reply.b;return (int)a->status;
}
static void paint(unsigned id) {
    struct dw_manager m;dw_init(&m);dw_create(&m,(struct dc_owner){2,1},id,(struct dc_rect){0,0,DC_W,DC_H});
    dw_pixels(&m,id,client_pixels);
    if(id==1 && applications_mode)for(unsigned y=DC_H-12;y<DC_H-4;y++)for(unsigned x=86;x<150;x++)
        if(x<104 || (x>=108 && x<126) || x>=130)client_pixels[y*DC_W+x]=x<104?0xff86ac75:x<126?0xffc86a6a:0xffad8bcd;
}
static int connect_client(unsigned id,dg_u32 *remote,dg_u32 *inbox,struct gw_result *a) {
    *remote=lookup(GW_SERVICE);if(!*remote)return -1;
    if(!*inbox && mach_port_allocate(mach_task_self_,1,inbox))return -1;
    paint(id);struct dc_rect r=id==1?(struct dc_rect){0,0,DC_W,DC_H}:id==2?(struct dc_rect){12,16,70,44}:(struct dc_rect){60,28,72,44};
    return gw_rpc(*remote,(struct gw_body){.op=GW_CREATE,.id=id,.x=r.x,.y=r.y,.w=r.w,.h=r.h,.seq=1},*inbox,client_pixels,a) || a->status?-1:0;
}
static int app(unsigned id) {
    char role[48];snprintf(role,sizeof(role),"app-%s-%d",id==2?"red":"blue",getpid());
    if(ipc_identity(applications_mode?role:id==2?"gui-red":"gui-blue"))return 1;
    ipc_role=id==2?"gui-red":"gui-blue";
    dg_u32 remote=0,inbox=0;struct gw_result a;
    if(connect_client(id,&remote,&inbox,&a))return failure("app create",-1);
    ipc_note("WINDOW id=%u manager=%u",id,a.pid);dg_u32 events=0,touches=0,manager_pid=a.pid,last_state=~0u;
    if(applications_mode){struct gw_identity denied;struct gw_result invalid;dg_u32 apps=lookup(AP_SERVICE);
        if(!apps || ap_rpc(apps,AP_TERMINATE,id==2?3:2,(struct dc_owner){0},&denied)!=DC_OWNER ||
           gw_info(remote,id==2?3:2,&denied)!=DC_OWNER ||
           gw_rpc(remote,(struct gw_body){.op=GW_TOUCH,.id=1,.seq=1,.value=1},0,0,&invalid) || invalid.status!=DC_OWNER)
            return failure("application isolation",-1);
        drop(apps);ipc_note("PASS APP_ISOLATION no_lifecycle_authority=1 no_touch_injection=1");}
    for(;;) {
        dg_u8 received[GW_FIXED+128]={0};struct gw_request *event=(void *)received;
        int rc=mach_msg(received,2|0x100|(3u<<24),0,sizeof(received),inbox,100,0);
        if(!rc) {
            struct dc_owner sender={0};
            if(!dc_audit_peer(event,sizeof(received),&sender) || event->h.size!=GW_FIXED || event->h.id!=GW_MSG ||
               (event->h.bits&0x80000000u) || event->b.version!=GW_VERSION || (event->b.op!=GW_EVENT && event->b.op!=GW_TOUCH_EVENT && event->b.op!=GW_LIFECYCLE_EVENT) || event->b.id!=id ||
               event->b.bytes || event->b.value>(event->b.op==GW_EVENT?1u:3u) || !ipc_path_matches(sender.pid,"/sbin/duchamp-window-manager"))return failure("input sender or record",-1);
            if(sender.pid==manager_pid) {
                if(event->b.op==GW_LIFECYCLE_EVENT && applications_mode){ipc_note("APP EXIT id=%u crash=%u",id,event->b.value);if(event->b.value)abort();_exit(0);}
                if(event->b.op==GW_EVENT) {
                    if(event->b.seq!=events+1)return failure("input ordering",-1);
                    events++;ipc_note("DELIVER id=%u seq=%u down=%u x=%u y=%u manager=%u",id,events,event->b.value,event->b.x,event->b.y,manager_pid);
                }else {
                    if(event->b.seq!=touches+1 || event->b.w>=MT_SLOTS || event->b.h>MT_ID_MAX)return failure("touch ordering",-1);
                    touches++;ipc_note("TOUCH DELIVER id=%u seq=%u slot=%u contact=%u phase=%u x=%u y=%u manager=%u",id,touches,event->b.w,event->b.h,event->b.value,event->b.x,event->b.y,manager_pid);
                }
            }
        }else if(rc!=0x10004003)return failure("app event receive",rc);
        if(gw_rpc(remote,(struct gw_body){.op=GW_QUERY,.id=id},0,0,&a) || !a.active) {
            drop(remote);if(connect_client(id,&remote,&inbox,&a))continue;
            manager_pid=a.pid;ipc_note("RECONNECTED id=%u manager=%u",id,a.pid);events=touches=0;
        }
        if(applications_mode){struct gw_identity info;if(!gw_info(remote,id,&info) && info.state!=last_state){
            ipc_note("APP STATE id=%u pid=%u birth=%u state=%u visible=%u",id,info.pid,info.birth,info.state,info.visible);last_state=info.state;}}
    }
}
static int launch(const char *action,const char *name) {
    char path[128];snprintf(path,sizeof(path),"system/org.duchamp.qemu.%s",name);
    char *args[]={"launchctl",(char *)action,"-k",path,0};
    int child=fork();if(child<0)return -1;
    if(!child){execve("/bin/launchctl",args,*_NSGetEnviron());_exit(127);}
    int status=0;for(unsigned n=0;n<40;n++) {int r=waitpid(child,&status,1);if(r==child){ipc_note("LAUNCH %s %s status=%d",action,name,status);return status? -1:0;}usleep(100000);}
    kill(child,9);waitpid(child,&status,0);return -1;
}
static int query_wait(dg_u32 remote,unsigned id,int active,struct gw_result *a) {
    for(unsigned n=0;n<100;n++) {
        if(!gw_rpc(remote,(struct gw_body){.op=GW_QUERY,.id=id},0,0,a) && a->active==(dg_u32)active)return 0;
        usleep(100000);
    }
    return -1;
}
static int pointer(dg_u32 remote,unsigned x,unsigned y,unsigned down) {
    struct gw_result a;return gw_rpc(remote,(struct gw_body){.op=GW_POINTER,.x=x,.y=y,.value=down},0,0,&a) || a.status?-1:0;
}
static void frame(unsigned phase){ipc_note("FRAME phase=%u hold=8s",phase);sleep(8);}
static int shell(int selftest) {
    if(ipc_identity("gui-shell"))return 1;
    dg_u32 remote=0,inbox=0;struct gw_result a;
    if(connect_client(1,&remote,&inbox,&a))return failure("desktop create",-1);
    if(!selftest)for(;;)sleep(1);
    /* This explicit QEMU test driver supplies pointer coordinates through Mach
     * IPC. It is not claimed as an IOHID touchscreen or a physical mouse. */
    frame(1);
    if(pointer(remote,24,88,1) || launch("kickstart","gui-red") || pointer(remote,24,88,0) || query_wait(remote,2,1,&a) ||
       pointer(remote,60,88,1) || launch("kickstart","gui-blue") || pointer(remote,60,88,0) || query_wait(remote,3,1,&a) ||
       pointer(remote,0,0,0))return failure("launcher",-1);
    frame(2);
    if(pointer(remote,24,38,1) || pointer(remote,24,38,0))return failure("content click",-1);
    if(gw_rpc(remote,(struct gw_body){.op=GW_QUERY,.id=2},0,0,&a) || a.focus!=2 || a.events!=2 || a.down)return failure("hit focus",-1);
    ipc_note("PASS focus_and_release id=2 events=%u",a.events);frame(3);
    if(pointer(remote,20,19,1) || pointer(remote,34,25,1) || pointer(remote,34,25,0))return failure("drag",-1);
    if(gw_rpc(remote,(struct gw_body){.op=GW_QUERY,.id=2},0,0,&a) || a.x!=26 || a.y!=22)return failure("moved geometry",-1);
    ipc_note("PASS move rect=%u,%u,%u,%u",a.x,a.y,a.w,a.h);frame(4);
    if(pointer(remote,94,64,1) || pointer(remote,104,70,1) || pointer(remote,104,70,0))return failure("resize",-1);
    if(gw_rpc(remote,(struct gw_body){.op=GW_QUERY,.id=2},0,0,&a) || a.w!=80 || a.h!=50)return failure("resized geometry",-1);
    ipc_note("PASS resize rect=%u,%u,%u,%u",a.x,a.y,a.w,a.h);frame(5);
    if(gw_rpc(remote,(struct gw_body){.op=GW_GEOMETRY,.id=2,.x=0,.y=0,.w=24,.h=20},0,0,&a) || a.status!=DC_OWNER)return failure("foreign geometry",-1);
    if(gw_rpc(remote,(struct gw_body){.op=GW_PAINT,.id=1,.seq=1},0,client_pixels,&a) || a.status!=DC_STALE)return failure("replayed submission",-1);
    if(pointer(remote,~0u,0,1)!=-1)return failure("out of bounds pointer",-1);
    ipc_note("PASS ownership_replay_bounds");
    /* Ordinary client exit closes its endpoint; actual kernel notification
     * removes the window, without a fabricated client death message. */
    char *stopargs[]={"launchctl","bootout","system/org.duchamp.qemu.gui-blue",0};
    int child=fork();if(child<0)return failure("bootout fork",-1);
    if(!child){execve("/bin/launchctl",stopargs,*_NSGetEnviron());_exit(127);}
    int status=0;if(waitpid(child,&status,0)!=child || status || query_wait(remote,3,0,&a))return failure("client cleanup",-1);
    ipc_note("PASS process_cleanup id=3");frame(6);
    dg_u32 old=a.pid;
    /* Retain the first server's evidence before ipc_identity truncates its
     * per-role runtime log during the explicit restart test. */
    int source=open("/private/var/tmp/ipc-gui-wm.log",0),saved=open("/private/var/tmp/ipc-gui-wm-before.log",0x601,0600);
    if(source<0 || saved<0)return failure("save WM trace",-1);
    char chunk[2048];ssize_t bytes;
    while((bytes=read(source,chunk,sizeof(chunk)))>0)if(ipc_write_all(saved,chunk,(size_t)bytes))return failure("copy WM trace",-1);
    if(bytes<0 || close(source) || fsync(saved) || close(saved))return failure("flush WM trace",-1);
    if(launch("kickstart","gui-wm"))return failure("WM restart",-1);
    drop(remote);remote=0;int reconnected=0;
    for(unsigned n=0;n<30;n++) {
        if(!connect_client(1,&remote,&inbox,&a) && a.pid!=old){reconnected=1;break;}
        drop(remote);remote=0;sleep(1);
    }
    if(!reconnected || query_wait(remote,2,1,&a))return failure("restart reconnect",-1);
    ipc_note("PASS service_restart old=%u new=%u desktop_reconnected=1",old,a.pid);frame(7);
    int fd=open("/private/var/tmp/gui-done",0x601,0600);
    if(fd<0 || ipc_write_all(fd,"PASS\n",5) || fsync(fd) || close(fd))return failure("GUI witness",-1);
    ipc_note("PASS GUI_COMPLETE manager=%u dyld_images=%u",a.pid,_dyld_image_count());
    for(;;)sleep(1);
}
/* Custom application service lives in a separate launchd process. */
#include "duchamp-app-service.inc"
struct touch_connection {dg_u32 endpoint,generation,sequence,last_app;struct dc_owner producer;struct mt_report previous;};
static int cancel_touch(dg_u32 remote,struct touch_connection *c) {
    unsigned count=0;
    for(unsigned i=0;i<MT_SLOTS;i++)if(c->previous.contacts[i].active) {
        struct mt_contact p=c->previous.contacts[i];struct gw_result a;
        if(gw_rpc(remote,(struct gw_body){.op=GW_TOUCH,.id=i+1,.seq=p.id,.x=mt_axis(p.x,DC_W),.y=mt_axis(p.y,DC_H),.value=3},0,0,&a) || a.status)return -1;
        count++;
    }
    memset(&c->previous,0,sizeof(c->previous));ipc_note("TOUCH CANCEL generation=%u count=%u",c->generation,count);return 0;
}
static int touch_message(struct dt_message *m,struct dc_owner sender,dg_u32 remote,dg_u32 applications,dg_u32 input,struct touch_connection *c) {
    struct mt_report r=m->report;int complex=(m->h.bits&0x80000000u)!=0;
    int valid=m->h.size==sizeof(*m) && mt_valid(&r) && ipc_path_matches(sender.pid,"/sbin/duchamp-touch-input");
    if(valid && m->op==DP_CONNECT && complex && m->count==1 && !m->endpoint.type && m->endpoint.disposition==17 &&
       m->endpoint.name && !c->endpoint && r.flags==MT_CONNECTED && r.generation>c->generation) {
        dg_u32 old=0;
        if(mach_port_request_notification(mach_task_self_,m->endpoint.name,72,1,input,21,&old))return DC_INVALID;
        drop(old);c->endpoint=m->endpoint.name;c->generation=r.generation;c->sequence=0;c->producer=sender;c->previous=r;
        ipc_note("TOUCH CONNECT pid=%u birth=%u generation=%u",sender.pid,sender.birth,r.generation);return DC_OK;
    }
    if(!valid || complex || m->op!=DP_INPUT || m->count || m->endpoint.name || !c->endpoint ||
       sender.pid!=c->producer.pid || sender.birth!=c->producer.birth || r.generation!=c->generation ||
       c->sequence==~0u || r.sequence!=c->sequence+1 || !mt_follows(&c->previous,&r))return DC_STALE;
    if(r.flags&MT_CANCEL){if(cancel_touch(remote,c))return DC_INVALID;}
    else for(unsigned i=0;i<MT_SLOTS;i++)if(r.changed&(1u<<i)) {
        struct mt_contact before=c->previous.contacts[i],p=r.contacts[i];struct gw_result a;
        unsigned phase=p.active?(before.active?2:1):0;
        if((before.active && before.id!=p.id) || (!before.active && !p.active))return DC_INVALID;
        dg_u32 x=mt_axis(p.x,DC_W),y=mt_axis(p.y,DC_H);
        if(gw_rpc(remote,(struct gw_body){.op=GW_TOUCH,.id=i+1,.seq=p.id,.x=x,.y=y,.value=phase},0,0,&a) || a.status)return DC_INVALID;
        c->previous.contacts[i]=p; /* A later RPC failure must cancel applied contacts too. */
        ipc_note("TOUCH INPUT generation=%u seq=%u slot=%u contact=%u phase=%u x=%u y=%u origin=virtio",r.generation,r.sequence,i,p.id,phase,x,y);
        if(phase==1 && y>=DC_H-12 && y<DC_H-4) {
            unsigned id=x>=12 && x<38?2:x>=48 && x<74?3:0;
            if(id){c->last_app=id;if(app_nowait(applications,AP_LAUNCH,id))return DC_INVALID;}
            else {
                struct gw_result focused;if(gw_rpc(remote,(struct gw_body){.op=GW_QUERY,.id=1},0,0,&focused))return DC_INVALID;
                id=focused.focus?focused.focus:c->last_app;
                if(id>=2 && id<=3) {
                    c->last_app=id;
                    if(x>=86 && x<104){if(app_nowait(applications,AP_BACKGROUND,id))return DC_INVALID;}
                    if(x>=108 && x<126){if(app_nowait(applications,AP_TERMINATE,id))return DC_INVALID;}
                    if(x>=130 && x<150){struct gw_identity owner;
                        if(ap_rpc(applications,AP_QUERY,id,(struct dc_owner){0},&owner))return DC_INVALID;
                        if(app_nowait(applications,owner.pid?AP_RESTART:AP_LAUNCH,id))return DC_INVALID;}
                }
            }
        }
    }
    c->previous=r;c->sequence=r.sequence;return DC_OK;
}
static int live_shell(int app_mode) {
    if(ipc_identity("gui-shell"))return 1;
    dg_u32 remote=0,inbox=0,input=0,endpoint=0,last_generation=0,last_sequence=0,x=0,y=0,down=0;
    struct dc_owner producer={0};struct gw_result a;
    applications_mode=app_mode;struct touch_connection touch={0};dg_u32 applications=0;
    if(connect_client(1,&remote,&inbox,&a) || bootstrap_check_in(bootstrap_port,DP_SERVICE,&input))return failure("live shell startup",-1);
    if(app_mode && !(applications=lookup(AP_SERVICE)))return failure("application service lookup",-1);
    ipc_note("LIVE READY manager=%u input_service=%u",a.pid,input);
    for(;;) {
        union {struct dp_message m;struct dt_message touch;dg_u8 bytes[512];} q={0};
        int rc=mach_msg(&q,2|0x100|(3u<<24),0,sizeof(q),input,100,0);
        if(rc==0x10004003)continue;if(rc)return failure("live receive",rc);
        struct dc_owner sender={0};if(!dc_audit_peer(&q,sizeof(q),&sender))return failure("live audit",-1);
        if(q.m.h.id==72 && q.m.h.size==36 && !sender.pid && !(q.m.h.bits&0x80000000u)) {
            dg_u32 name=dg_get32(q.bytes+32);
            if(app_mode && touch.endpoint && name==touch.endpoint) {
                if(cancel_touch(remote,&touch))return failure("touch disconnect",-1);
                drop(name);drop(name);touch.endpoint=0;touch.producer=(struct dc_owner){0};
                ipc_note("TOUCH DISCONNECT generation=%u",touch.generation);continue;
            }
            if(endpoint && name==endpoint) {
                if(down && pointer(remote,x,y,0))return failure("disconnect release",-1);
                ipc_note("LIVE DISCONNECT generation=%u forced_release=%u",last_generation,down);
                down=0;drop(name);drop(name);endpoint=0;producer=(struct dc_owner){0};
            }
            continue;
        }
        if(q.m.h.id==71 && q.m.h.size==24 && !sender.pid)continue;
        if(app_mode && q.m.h.id==DT_MSG) {
            int status=touch_message(&q.touch,sender,remote,applications,input,&touch);
            if((q.touch.h.bits&0x80000000u) && status){dg_u32 reply=q.touch.h.remote;q.touch.h.remote=0;mach_msg_destroy(&q);q.touch.h.remote=reply;}
            if(status)ipc_note("TOUCH REJECT pid=%u status=%d",sender.pid,status);
            struct dp_reply reply={{18,sizeof(reply),q.touch.h.remote,0,0,DT_MSG+100},(dg_u32)status};
            if(reply.h.remote && mach_msg(&reply,1|0x10,sizeof(reply),0,0,1000,0))return failure("touch reply",-1);
            continue;
        }
        struct vp_report r=q.m.report;dg_u32 nx=0,ny=0;int status=DC_INVALID;
        int valid=q.m.h.id==DP_MSG && q.m.h.size==sizeof(q.m) && vp_coordinates(&r,DC_W,DC_H,&nx,&ny) &&
            ipc_path_matches(sender.pid,"/sbin/duchamp-pointer-input");
        int complex=(q.m.h.bits&0x80000000u)!=0;
        if(valid && q.m.op==DP_CONNECT && complex && q.m.count==1 && q.m.endpoint.disposition==17 &&
           !q.m.endpoint.type && q.m.endpoint.name && !endpoint && r.flags==VP_CONNECTED && !r.sequence && !r.left &&
           r.generation>last_generation) {
            dg_u32 old=0;
            if(!mach_port_request_notification(mach_task_self_,q.m.endpoint.name,72,1,input,21,&old)) {
                drop(old);endpoint=q.m.endpoint.name;producer=sender;last_generation=r.generation;last_sequence=0;status=DC_OK;
                ipc_note("LIVE CONNECT pid=%u birth=%u generation=%u",sender.pid,sender.birth,r.generation);
            }
        }else if(valid && q.m.op==DP_INPUT && !complex && !q.m.count && !q.m.endpoint.name && endpoint &&
                 sender.pid==producer.pid && sender.birth==producer.birth && r.generation==last_generation &&
                 r.flags==VP_REPORT && r.sequence==last_sequence+1 && last_sequence!=0xffffffffu) {
            if(!pointer(remote,nx,ny,r.left)) {
                status=DC_OK;last_sequence=r.sequence;
                ipc_note("LIVE INPUT generation=%u seq=%u pos=%u,%u left=%u origin=virtio",r.generation,r.sequence,nx,ny,r.left);
                if(r.left && !down && ny>=DC_H-12 && ny<DC_H-4 && ((nx>=12 && nx<38)||(nx>=48 && nx<74))) {
                    unsigned id=nx<40?2:3;
                    if(gw_rpc(remote,(struct gw_body){.op=GW_QUERY,.id=id},0,0,&a))return failure("launcher query",-1);
                    if(app_mode?app_nowait(applications,AP_LAUNCH,id):(!a.active && launch("kickstart",id==2?"gui-red":"gui-blue")))return failure("live launcher",-1);
                    ipc_note("LIVE LAUNCH id=%u already_active=%u",id,a.active);
                }
                x=nx;y=ny;down=r.left;
            }
        }
        if(complex && !(valid && q.m.op==DP_CONNECT && status==DC_OK)) {
            dg_u32 reply=q.m.h.remote;q.m.h.remote=0;mach_msg_destroy(&q);q.m.h.remote=reply;
        }
        if(status)ipc_note("LIVE REJECT pid=%u op=%u generation=%u seq=%u",sender.pid,q.m.op,r.generation,r.sequence);
        struct dp_reply reply={{18,sizeof(reply),q.m.h.remote,0,0,DP_MSG+100},(dg_u32)status};
        if(reply.h.remote && mach_msg(&reply,1|0x10,sizeof(reply),0,0,1000,0))return failure("live reply",-1);
    }
}
static int live_observer(void) {
    if(ipc_identity("gui-live-observer"))return 1;
    dg_u32 remote=lookup(GW_SERVICE);if(!remote)return failure("observer lookup",-1);
    struct gw_result a,b;unsigned phase=0;dg_u32 held_events=0;
    for(unsigned tick=0;tick<3000;tick++) {
        if(gw_rpc(remote,(struct gw_body){.op=GW_QUERY,.id=2},0,0,&a) ||
           gw_rpc(remote,(struct gw_body){.op=GW_QUERY,.id=3},0,0,&b))return failure("observer query",-1);
        unsigned before=phase;
        if(phase==0 && a.active && b.active && a.focus==3)phase=1;
        else if(phase==1 && a.focus==2 && a.events>=2 && !a.down)phase=2;
        else if(phase==2 && a.x==26 && a.y==22 && a.w==70 && a.h==44 && !a.down)phase=3;
        else if(phase==3 && a.w==80 && a.h==50 && !a.down)phase=4;
        else if(phase==4 && a.down) {
            held_events=a.events;
            if(launch("kickstart","gui-input"))return failure("input restart",-1);
            phase=5;
        }else if(phase==5 && a.events>held_events && !a.down) {
            char generation[32]={0};int fd=open("/private/var/tmp/virtio-pointer-generation",0);
            if(fd>=0){ssize_t n=read(fd,generation,sizeof(generation)-1);close(fd);if(n>0 && strtol(generation,0,10)>=2)phase=6;}
        }else if(phase==6 && b.focus==3 && b.events>=2 && !b.down) {
            if(a.x!=26 || a.y!=22 || a.w!=80 || a.h!=50)return failure("geometry after reconnect",-1);
            sleep(8); /* Preserve the completed state for the passive observer. */
            int fd=open("/private/var/tmp/live-input-done",0x601,0600);
            if(fd<0 || ipc_write_all(fd,"PASS\n",5) || fsync(fd) || close(fd))return failure("live result",-1);
            ipc_note("PASS LIVE_INPUT_COMPLETE phases=7 manager=%u red_events=%u blue_events=%u",a.pid,a.events,b.events);
            for(;;)sleep(1);
        }
        if(phase!=before)ipc_note("OBSERVED phase=%u focus=%u red=%u,%u,%u,%u down=%u events=%u",phase,a.focus,a.x,a.y,a.w,a.h,a.down,a.events);
        usleep(100000);
    }
    return failure("live input deadline",-1);
}
#include "duchamp-app-observer.inc"
int main(int argc,char **argv) {
    if(argc<2)return 2;
    if(!strcmp(argv[1],"compositor"))return compositor();
    if(!strcmp(argv[1],"manager")){applications_mode=argc==3 && !strcmp(argv[2],"--apps");return manager();}
    if(!strcmp(argv[1],"shell"))return argc==3 && (!strcmp(argv[2],"--live") || !strcmp(argv[2],"--apps"))?live_shell(!strcmp(argv[2],"--apps")):shell(argc==3 && !strcmp(argv[2],"--selftest"));
    if(!strcmp(argv[1],"red")){applications_mode=argc==3 && !strcmp(argv[2],"--apps");return app(2);}
    if(!strcmp(argv[1],"blue")){applications_mode=argc==3 && !strcmp(argv[2],"--apps");return app(3);}
    if(!strcmp(argv[1],"applications"))return app_manager();
    if(!strcmp(argv[1],"app-observer"))return app_observer();
    if(!strcmp(argv[1],"live-observer"))return live_observer();
    return 2;
}
