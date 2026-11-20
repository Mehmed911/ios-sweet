/* SPDX-License-Identifier: 0BSD */
/* Isolated, bounded userspace compositor protocol, not an Apple graphics API. */
#include "duchamp-compositor-iokit.h"
#include "duchamp-compositor-wire.h"
extern dg_u32 bootstrap_port;
extern int bootstrap_check_in(dg_u32,const char *,dg_u32 *),bootstrap_look_up(dg_u32,const char *,dg_u32 *);
extern int mach_port_request_notification(dg_u32,dg_u32,int,dg_u32,dg_u32,int,dg_u32 *);
extern int gettimeofday(struct ipc_timeval *,void *);
extern void _exit(int) __attribute__((noreturn));
static dg_u64 now(void) {
    struct ipc_timeval t={0};if(gettimeofday(&t,0) || t.seconds<0 || t.micros<0 || t.micros>=1000000)return 0;
    return (dg_u64)t.seconds*1000000+(unsigned)t.micros;
}
static int error(const char *step,int rc) {ipc_note("FAIL %s rc=0x%x",step,rc);return 1;}
static void drop(dg_u32 p) {if(p)mach_port_deallocate(mach_task_self_,p);}
static int call(dg_u32 service,struct dc_request b,dg_u32 surface,dg_u32 inbox,struct dc_answer *answer) {
    union {struct dc_registration reg;struct dc_packet simple;dg_u8 bytes[512];} p={0};
    dg_u32 reply=mig_get_reply_port();if(!reply)return -1;
    dg_u32 size;
    if(b.op==DC_REGISTER) {
        size=sizeof(p.reg);p.reg.count=2;p.reg.surface=(struct dg_port){surface,0,0,19,0};
        p.reg.inbox=(struct dg_port){inbox,0,0,20,0};p.reg.body=b;
    }else {size=sizeof(p.simple);p.simple.body=b;}
    p.simple.h=(struct dg_head){19u|(21u<<8)|(b.op==DC_REGISTER?0x80000000u:0),size,service,reply,0,DC_MSG};
    int rc=mach_msg(p.bytes,1|2|0x100,size,sizeof(p),reply,3000,0);
    if(rc){mig_dealloc_reply_port(reply);return rc;}
    if(p.simple.h.id!=DC_MSG+100 || p.simple.h.size!=sizeof(struct dc_reply) || (p.simple.h.bits&0x80000000u))return -2;
    memcpy(answer,p.bytes+24,sizeof(*answer));return 0;
}
static int answer(dg_u32 port,struct dc_answer b) {
    struct dc_reply p={{18,sizeof(p),port,0,0,DC_MSG+100},b};
    return mach_msg(&p,1|0x10,sizeof(p),0,0,1000,0);
}
struct peer {
    struct dc_owner owner;dg_u32 role,connection,inbox,events,acked;
    struct di_surface surface;
};
static struct dc_scene scene;
static struct peer peers[2];
static struct di_surface output[2];
static dg_u32 fb,root_service,service,phase,death_count,denials[3],pending_kill;
static int selftest;
static dg_u64 phase_time,last_swap;
static void phase_set(dg_u32 p) {phase=p;phase_time=now();}
static int published_phase;
static int present(void) {
    dc_render(&scene);
    if(di_present(fb,&output[scene.front],scene.frames[scene.front],&last_swap))return -1;
    if(selftest && published_phase!=(int)phase) {
        published_phase=(int)phase;
        ipc_note("PHASE %u front=%u epoch=%u output_surface=%u swap=%llu",phase,scene.front,scene.epoch,output[scene.front].id,last_swap);
    }
    return 0;
}
static struct peer *by_owner(struct dc_owner owner) {
    for(unsigned i=0;i<2;i++)if(peers[i].owner.pid==owner.pid && peers[i].owner.birth==owner.birth)return &peers[i];
    return 0;
}
static int register_peer(struct dc_registration *p,struct dc_owner owner) {
    struct dc_request *b=&p->body;int rc=DC_INVALID;
    if(b->role<1 || b->role>2 || owner.pid<=1 || by_owner(owner) || peers[b->role-1].owner.pid)goto rejected;
    dg_u32 connection=open_client(root_service,0);if(!connection)goto rejected;
    struct di_surface s;
    rc=di_import(connection,p->surface.name,&s);
    if(rc || s.id!=b->id || s.w!=b->w || s.h!=b->h || b->x>DC_W || b->y>DC_H) {
        di_close(connection);rc=DC_INVALID;goto rejected;
    }
    rc=dc_add(&scene,owner,s.id,s.w,s.h,b->x,b->y,b->z);
    if(!rc)rc=dc_commit(&scene,owner,s.id,1,s.pixels,s.stride,s.bytes,(struct dc_rect){0,0,s.w,s.h});
    if(rc){dc_remove(&scene,owner);di_close(connection);goto rejected;}
    dg_u32 old=0;
    if(mach_port_request_notification(mach_task_self_,p->inbox.name,72,1,service,21,&old)) {
        dc_remove(&scene,owner);di_close(connection);rc=DC_INVALID;goto rejected;
    }
    drop(old);
    peers[b->role-1]=(struct peer){owner,b->role,connection,p->inbox.name,0,0,s};
    ipc_note("REGISTER role=%u pid=%u birth=%u surface=%u bytes=%u stride=%u",b->role,owner.pid,owner.birth,s.id,s.bytes,s.stride);
    drop(p->surface.name);return DC_OK;
rejected:
    drop(p->surface.name);drop(p->inbox.name);ipc_note("REJECT register pid=%u rc=%d",owner.pid,rc);return rc;
}
static int remove_dead(dg_u32 port,struct dc_owner producer) {
    if(producer.pid)return error("non-kernel death notification",-1);
    for(unsigned i=0;i<2;i++)if(peers[i].owner.pid && peers[i].inbox==port) {
        struct peer *p=&peers[i];dg_u32 id=p->surface.id;
        unsigned removed=dc_remove(&scene,p->owner);
        if(removed!=1 || di_close(p->connection))return error("client mapping cleanup",-1);
        drop(port);drop(port); /* received dead-name notification adds one user ref */
        dg_u32 temporary=open_client(root_service,0);if(!temporary)return error("cleanup lookup open",-1);
        dg_u8 d[0xa68];dg_u32 bytes=sizeof(d);dg_u64 in=id;
        int rc=method(temporary,4,&in,1,0,0,d,&bytes,0,0);int close_rc=di_close(temporary);
        if(rc!=(int)0xe00002f0u || close_rc)return error("released surface still accessible",rc);
        ipc_note("DEAD role=%u pid=%u kernel_notification=1 closed=1 lookup=0x%x events=%u acked=%u",p->role,p->owner.pid,rc,p->events,p->acked);
        if(selftest && (p->events!=2 || p->acked!=2))return error("dead client input incomplete",-1);
        memset(p,0,sizeof(*p));death_count++;
        if(selftest)phase_set(death_count==1?DC_ONE_LEFT:DC_EMPTY);return 0;
    }
    return error("unregistered death port",-1);
}
static int input(struct dg_event e) {
    if(e.type!=3 || e.usage_page!=12 || e.usage!=0x40 || e.down>1)return error("unexpected HID record",-1);
    if(selftest && !((phase==DC_RESTORED || phase==DC_ONE_LEFT) && now()-phase_time>=8000000))return 0;
    struct dc_route r;
    if(!dc_input(&scene,e.down,&r))return 0;
    struct peer *p=by_owner(r.owner);
    if(!p || p->surface.id!=r.id || p->events==(selftest?2u:0xffffffffu))return error("input target",-1);
    struct dc_packet packet={0};packet.h=(struct dg_head){19,sizeof(packet),p->inbox,0,0,DC_MSG};
    packet.body=(struct dc_request){.version=DC_VERSION,.op=DC_EVENT,.id=r.id,.seq=++p->events,.value=e.down};
    int rc=mach_msg(&packet,1|0x10,sizeof(packet),0,0,1000,0);if(rc)return error("input delivery",rc);
    ipc_note("ROUTE role=%u pid=%u id=%u seq=%u down=%u",p->role,p->owner.pid,r.id,p->events,e.down);
    if(selftest && e.down && phase==DC_RESTORED) {
        if(dc_focus(&scene,peers[0].owner,peers[0].surface.id))return error("focus switch",-1);
        ipc_note("FOCUS changed_to_red_while_pressed=1 capture=%u",scene.capture);
    }
    return 0;
}
static int server(void) {
    if(ipc_identity(selftest?"compositor":"compositor-service"))return 1;
    dg_u32 master=0;if(host_get_io_main(mach_host_self(),&master))return error("IOMainPort",-1);
    root_service=match(master,"IOCoreSurfaceRoot");dg_u32 f=match(master,"AppleCLCD"),h=match(master,"SweetHIDButtons");
    if(!root_service || !f || !h)return error("IOKit match",-1);
    fb=open_client(f,0);dg_u32 surfaces=open_client(root_service,0),hid=open_client(h,0x65737563);
    if(!fb || !surfaces || !hid)return error("IOKit clients",-1);
    if(di_create(surfaces,DC_W,DC_H,&output[0]) || di_create(surfaces,DC_W,DC_H,&output[1]))return error("front/back allocation",-1);
    void *queue=0;dg_u64 queue_bytes=0;
    if(map_queue(hid,&queue,&queue_bytes))return error("HID map",-1);
    dg_u64 options=0;if(method(hid,0,&options,1,0,0,0,0,0,0))return error("HID open",-1);
    if(bootstrap_check_in(bootstrap_port,DC_SERVICE,&service) || !service)return error("launchd Mach check-in",-1);
    dc_init(&scene);dg_u64 started=now();ipc_note("READY pid=%d service=%s front=%u back=%u",getpid(),DC_SERVICE,output[0].id,output[1].id);
    while(!selftest || now()-started<150000000) {
        union {struct dc_registration reg;struct dc_packet packet;dg_u8 bytes[512];} m={0};
        int rc=mach_msg(m.bytes,2|0x100|(3u<<24),0,sizeof(m),service,100,0);
        if(!rc) {
            struct dc_owner owner={0};
            if(!dc_audit_peer(&m,sizeof(m),&owner))return error("missing audit trailer",-1);
            if(m.packet.h.id==72 && m.packet.h.size==36 && !(m.packet.h.bits&0x80000000u)) {
                if(remove_dead(dg_get32(m.bytes+32),owner))return 1;
            }else {
                int complex=(m.packet.h.bits&0x80000000u)!=0;
                struct dc_request b=complex?m.reg.body:m.packet.body;
                int valid=m.packet.h.id==DC_MSG && owner.pid>1 && b.version==DC_VERSION && !b.reserved &&
                    ((complex && m.packet.h.size==sizeof(m.reg) && m.reg.count==2 && !m.reg.surface.type && !m.reg.inbox.type &&
                      m.reg.surface.disposition==17 && m.reg.inbox.disposition==17 && b.op==DC_REGISTER) ||
                     (!complex && m.packet.h.size==sizeof(m.packet) && b.op!=DC_REGISTER));
                if(!valid)return error("malformed request",-1);
                int status=DC_INVALID;struct peer *p=by_owner(owner);
                if(b.op==DC_REGISTER)status=register_peer(&m.reg,owner);
                else if(p) {
                    if(b.op==DC_QUERY)status=DC_OK;
                    else if(b.op==DC_DIRTY) {
                        status=dc_commit(&scene,owner,b.id,b.seq,p->surface.pixels,p->surface.stride,p->surface.bytes,(struct dc_rect){b.x,b.y,b.w,b.h});
                        if(!status && phase==DC_BLEND)phase_set(DC_PATCHED);
                        if(status==DC_OWNER)denials[0]++;if(status==DC_INVALID)denials[1]++;if(status==DC_STALE)denials[2]++;
                    }else if(b.op==DC_SET_Z) {
                        status=dc_z(&scene,owner,b.id,b.z);
                        if(!status && phase==DC_PATCHED && b.z==2)phase_set(DC_RAISED);
                        else if(!status && phase==DC_RAISED && b.z==0) {
                            if(dc_focus(&scene,peers[1].owner,peers[1].surface.id))return error("overlay focus",-1);
                            phase_set(DC_RESTORED);
                        }
                    }else if(b.op==DC_FOCUS)status=dc_focus(&scene,owner,b.id);
                    else if(b.op==DC_ACK && b.id==p->surface.id && b.seq==p->acked+1 && b.seq<=p->events && b.value==(b.seq&1)) {
                        p->acked++;status=DC_OK;
                        if(selftest && p->role==2 && p->acked==2)pending_kill=p->owner.pid;
                    }
                }
                if(selftest && !phase && peers[0].owner.pid && peers[1].owner.pid)phase_set(DC_BLEND);
                dg_u32 command=0;
                if(selftest && p && now()-phase_time>=8000000) {
                    if(phase==DC_BLEND && p->role==2)command=DC_CMD_PATCH;
                    if(phase==DC_PATCHED && p->role==1)command=DC_CMD_RAISE;
                    if(phase==DC_RAISED && p->role==1)command=DC_CMD_RESTORE;
                }
                struct peer *actual=by_owner(owner);
                struct dc_answer reply={status,actual?actual->surface.id:0,phase,command,peers[0].surface.id,scene.epoch};
                if(answer(m.packet.h.remote,reply))return error("RPC reply",-1);
            }
        }else if(rc!=0x10004003)return error("Mach receive",rc);
        if(pending_kill) {
            ipc_note("TERMINATE overlay pid=%u signal=9 after_release_ack=1",pending_kill);
            if(kill((int)pending_kill,9))return error("kill test client",-1);pending_kill=0;
        }
        struct dg_event event;int got;
        while((got=dg_queue_pop(queue,queue_bytes,&event))>0)if(input(event))return 1;
        if(got<0)return error("HID bounds",got);
        if((!selftest || phase) && present())return error("frame presentation",-1);
        if(selftest && phase==DC_EMPTY && now()-phase_time>=8000000) {
            if(death_count!=2 || scene.focus || scene.capture || !denials[0] || !denials[1] || !denials[2])return error("final invariants",-1);
            ipc_note("PASS cleanup=%u owner_denials=%u rect_denials=%u replay_denials=%u epoch=%u",death_count,denials[0],denials[1],denials[2],scene.epoch);
            int fd=open("/private/var/tmp/compositor-done",0x601,0600);
            if(fd<0 || ipc_write_all(fd,"PASS\n",5) || fsync(fd) || close(fd))return error("done witness",-1);
            /* Stay launchd-managed until the test controller bootouts the job. */
            for(;;)usleep(100000);
        }
    }
    return error("compositor deadline",-1);
}
static int client(dg_u32 role,int early_exit) {
    const char *identity=early_exit?(role==1?"comp-early-red":"comp-early-overlay"):(role==1?"comp-red":"comp-overlay");
    if(ipc_identity(identity))return 1;
    dg_u32 master=0,remote=0;
    if(host_get_io_main(mach_host_self(),&master))return error("client IOMainPort",-1);
    dg_u32 root=match(master,"IOCoreSurfaceRoot"),connection=open_client(root,0),inbox=0;
    struct di_surface s;dg_u32 w=role==1?64:32,h=role==1?32:16;
    if(!connection || di_create(connection,w,h,&s) || mach_port_allocate(mach_task_self_,1,&inbox))return error("client surface",-1);
    dg_u32 portcount=1;dg_u64 in=s.id,out=0;
    if(method(connection,35,&in,1,0,0,0,0,&out,&portcount) || portcount!=1 || !out || out>0xffffffffu)return error("surface capability",-1);
    for(unsigned y=0;y<h;y++)for(unsigned x=0;x<w;x++)s.pixels[y*(s.stride/4)+x]=role==1?0xffff0000:0x800000ff;
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
    for(int tries=0;tries<30;tries++) {if(!bootstrap_look_up(bootstrap_port,DC_SERVICE,&remote) && remote)break;sleep(1);}
    if(!remote)return error("Mach service lookup",-1);
    struct dc_request b={.version=DC_VERSION,.op=DC_REGISTER,.role=role,.id=s.id,.seq=1,
        .x=role==1?0:16,.y=role==1?0:8,.w=w,.h=h,.z=role==1?0:1};
    struct dc_answer a;
    if(role==2) {
        struct dc_request invalid=b;invalid.w++;
        if(call(remote,invalid,(dg_u32)out,inbox,&a) || a.status!=DC_INVALID)return error("invalid shared geometry accepted",-1);
        ipc_note("SHARED BOUNDS rejection=1");
    }
    if(call(remote,b,(dg_u32)out,inbox,&a) || a.status || a.id!=s.id)return error("client registration",-1);
    if(early_exit) {drop((dg_u32)out);ipc_note("EARLY EXIT role=%u no_input=1",role);return 0;}
    drop((dg_u32)out);unsigned received=0,patched=0,raised=0,restored=0;dg_u64 started=now();
    while(now()-started<140000000) {
        union {struct dc_packet packet;dg_u8 bytes[256];} event={0};
        int rc=mach_msg(event.bytes,2|0x100,0,sizeof(event),inbox,100,0);
        if(!rc) {
            struct dc_request e=event.packet.body;
            if(event.packet.h.id!=DC_MSG || event.packet.h.size!=sizeof(event.packet) || (event.packet.h.bits&0x80000000u) ||
               e.version!=DC_VERSION || e.op!=DC_EVENT || e.id!=s.id || e.seq!=received+1 || e.value!=(received==0))return error("focused event validation",-1);
            received++;ipc_note("EVENT role=%u pid=%d id=%u seq=%u down=%u",role,getpid(),e.id,e.seq,e.value);
            b=(struct dc_request){.version=DC_VERSION,.op=DC_ACK,.id=s.id,.seq=e.seq,.value=e.value};
            if(call(remote,b,0,0,&a) || a.status)return error("event acknowledgment",-1);
            if(role==1 && received==2){ipc_note("EXIT red status=0 events=2");return 0;}
        }else if(rc!=0x10004003)return error("client input receive",rc);
        b=(struct dc_request){.version=DC_VERSION,.op=DC_QUERY};
        if(call(remote,b,0,0,&a) || a.status)return error("phase query",-1);
        if(role==2 && a.command==DC_CMD_PATCH && !patched) {
            b=(struct dc_request){.version=DC_VERSION,.op=DC_FOCUS,.id=a.base_id};
            if(call(remote,b,0,0,&a) || a.status!=DC_OWNER)return error("foreign focus accepted",-1);
            b.id=s.id;
            if(call(remote,b,0,0,&a) || a.status)return error("own focus rejected",-1);
            ipc_note("FOCUS RPC owner_verified=1");
            b=(struct dc_request){.version=DC_VERSION,.op=DC_DIRTY,.id=a.base_id,.seq=2,.w=1,.h=1};
            if(call(remote,b,0,0,&a) || a.status!=DC_OWNER)return error("foreign surface accepted",-1);
            b=(struct dc_request){.version=DC_VERSION,.op=DC_DIRTY,.id=s.id,.seq=2,.x=w-1,.w=2,.h=1};
            if(call(remote,b,0,0,&a) || a.status!=DC_INVALID)return error("invalid rectangle accepted",-1);
            b=(struct dc_request){.version=DC_VERSION,.op=DC_DIRTY,.id=s.id,.seq=1,.w=1,.h=1};
            if(call(remote,b,0,0,&a) || a.status!=DC_STALE)return error("replay accepted",-1);
            /* Modify the entire shared image, but commit only 8x8. Outside
             * that rectangle must retain the compositor's prior blue copy. */
            for(unsigned y=0;y<h;y++)for(unsigned x=0;x<w;x++)s.pixels[y*(s.stride/4)+x]=0x8000ff00;
            __atomic_thread_fence(__ATOMIC_SEQ_CST);
            b=(struct dc_request){.version=DC_VERSION,.op=DC_DIRTY,.id=s.id,.seq=2,.w=8,.h=8};
            if(call(remote,b,0,0,&a) || a.status)return error("dirty submit",-1);
            patched=1;ipc_note("DIRTY 8x8 committed foreign=denied bounds=denied replay=denied");
        }
        if(role==1 && ((a.command==DC_CMD_RAISE && !raised) || (a.command==DC_CMD_RESTORE && !restored))) {
            int z=a.command==DC_CMD_RAISE?2:0;
            b=(struct dc_request){.version=DC_VERSION,.op=DC_SET_Z,.id=s.id,.z=z};
            if(call(remote,b,0,0,&a) || a.status)return error("z order submit",-1);
            if(z==2)raised=1;else restored=1;ipc_note("Z_ORDER role=1 z=%d",z);
        }
    }
    return error("client deadline",-1);
}
int main(int argc,char **argv) {
    if(argc==1)return server();
    if(argc==2 && !strcmp(argv[1],"--selftest")){selftest=1;return server();}
    if(argc==2 && !strcmp(argv[1],"red"))return client(1,0);
    if(argc==2 && !strcmp(argv[1],"overlay"))return client(2,0);
    if(argc==2 && !strcmp(argv[1],"red-exit"))return client(1,1);
    if(argc==2 && !strcmp(argv[1],"overlay-exit"))return client(2,1);
    return 2;
}
