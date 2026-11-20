/* SPDX-License-Identifier: 0BSD */
static int ap_rpc(dg_u32 remote,unsigned op,unsigned id,struct dc_owner expected,struct gw_identity *result) {
    union {struct ap_request request;struct ap_reply reply;dg_u8 bytes[256];} m={0};
    dg_u32 port=mig_get_reply_port();m.request.h=(struct dg_head){19u|(21u<<8),sizeof(m.request),remote,port,0,AP_MSG};
    m.request.b=(struct ap_body){AP_VERSION,op,id,expected.pid,expected.birth};
    int rc=mach_msg(&m,1|2|0x100,sizeof(m.request),sizeof(m),port,8000,0);
    if(rc){mig_dealloc_reply_port(port);return rc;}
    if(m.reply.h.id!=AP_MSG+100 || m.reply.h.size!=sizeof(m.reply) || m.reply.h.bits&0x80000000u)return -1;
    *result=m.reply.b;return (int)result->status;
}
static int app_nowait(dg_u32 applications,unsigned op,unsigned id) {
    struct gw_identity a;if(ap_rpc(applications,AP_QUERY,id,(struct dc_owner){0},&a))return -1;
    return ap_rpc(applications,op,id,(struct dc_owner){a.pid,a.birth},&a);
}
/* Diagnostic callers may wait. Input handling uses app_nowait so launchd's
 * scheduling/throttling cannot hold a contact acknowledgement hostage. */
static int app_action(dg_u32 applications,unsigned op,unsigned id) {
    struct gw_identity a;if(ap_rpc(applications,AP_QUERY,id,(struct dc_owner){0},&a))return -1;
    int rc=ap_rpc(applications,op,id,(struct dc_owner){a.pid,a.birth},&a);if(rc)return rc;
    if(op!=AP_LAUNCH && op!=AP_RESTART && op!=AP_TERMINATE && op!=AP_CRASH)return 0;
    for(unsigned n=0;n<300;n++) {
        if(ap_rpc(applications,AP_QUERY,id,(struct dc_owner){0},&a))return -1;
        if(op==AP_TERMINATE || op==AP_CRASH){if(!a.pid && a.state==AP_STOPPED)return 0;}
        else if(a.pid && a.state<=AP_FOREGROUND_STATE)return 0;
        if(a.state==AP_FAILED)return -1;usleep(100000);
    }
    return -1;
}
struct app_pending {int child,submitted,launching,stopping,error;struct dc_owner old;};
static int app_start_child(unsigned id) {
    int child=fork();if(child)return child;
    char *args[]={"launchctl","kickstart","-k",id==2?"system/org.duchamp.qemu.gui-red":"system/org.duchamp.qemu.gui-blue",0};
    execve("/bin/launchctl",args,*_NSGetEnviron());_exit(127);
}
static int app_progress(dg_u32 manager,struct app_pending *p,unsigned id,struct gw_identity *a) {
    if(gw_info(manager,id,a))return -1;
    if(p->child){int status=0,done=waitpid(p->child,&status,1);if(done==p->child){
        ipc_note("LAUNCH RECEIPT app=%u utility=%d wait_status=%d",id,p->child,status);p->child=0;
        if(status){p->error=DC_INVALID;p->launching=0;}}
        else if(done<0){p->error=DC_INVALID;p->child=0;p->launching=0;}}
    if(p->stopping && (!a->pid || a->pid!=p->old.pid || a->birth!=p->old.birth))p->stopping=0;
    if(p->launching && !p->stopping) {
        if(a->pid){p->launching=p->submitted=0;p->error=0;ipc_note("READY app=%u status=0 pid=%u version=%u state=%u visible=%u",id,a->pid,a->birth,a->state,a->visible);}
        else if(!p->submitted && !p->child){p->child=app_start_child(id);if(p->child<0){p->error=DC_INVALID;p->launching=0;}
            else {p->submitted=1;ipc_note("LAUNCH QUEUED app=%u utility=%d",id,p->child);}}
    }
    if(p->stopping)a->state=AP_STOPPING;
    else if(p->launching)a->state=AP_PENDING;
    else if(p->error && !a->pid)a->state=AP_FAILED;
    return 0;
}
static int app_manager(void) {
    if(ipc_identity("applications"))return 1;
    dg_u32 manager=lookup(GW_SERVICE),service=0;struct app_pending pending[2]={{0}};
    if(!manager || bootstrap_check_in(bootstrap_port,AP_SERVICE,&service))return failure("application manager startup",-1);
    ipc_note("READY fixed_catalog=2 images=arm64-macho execution=launchd async_launch=1");
    for(;;) {
        for(unsigned i=0;i<2;i++)if(pending[i].child || pending[i].launching || pending[i].stopping){struct gw_identity a;
            if(app_progress(manager,&pending[i],i+2,&a))return failure("application progress",-1);}
        union {struct ap_request request;dg_u8 bytes[256];} m={0};
        int rc=mach_msg(&m,2|0x100|(3u<<24),0,sizeof(m),service,100,0);
        if(rc==0x10004003)continue;if(rc)return failure("applications receive",rc);
        struct dc_owner caller={0};if(!dc_audit_peer(&m,sizeof(m),&caller))return failure("applications audit",-1);
        struct ap_body b=m.request.b;struct gw_identity result={.status=DC_INVALID,.id=b.id};
        int valid=ap_valid(&m.request),authorized=ipc_path_matches(caller.pid,"/sbin/duchamp-gui-shell") ||
            ipc_path_matches(caller.pid,"/sbin/duchamp-app-observer");
        if(valid && !authorized)result.status=DC_OWNER;
        else if(valid) {
            struct app_pending *p=&pending[b.id-2];int status=app_progress(manager,p,b.id,&result);
            if(!status && b.op!=AP_QUERY) {
                int stop=b.op==AP_TERMINATE || b.op==AP_CRASH || b.op==AP_RESTART;
                if(b.op==AP_RESTART && !result.pid && !b.pid && !b.birth){p->launching=1;p->error=0;}
                else if(b.op!=AP_LAUNCH && (!result.pid || result.pid!=b.pid || result.birth!=b.birth))status=DC_STALE;
                else if(stop && p->stopping){p->launching=b.op==AP_RESTART;p->error=0;}
                else if(stop) {
                    struct gw_result a;
                    status=gw_rpc(manager,(struct gw_body){.op=b.op==AP_CRASH?GW_CRASH:GW_TERMINATE,.id=b.id,.w=result.pid,.h=result.birth},0,0,&a);
                    if(!status)status=(int)a.status;
                    if(!status){p->old=(struct dc_owner){result.pid,result.birth};p->stopping=1;p->launching=b.op==AP_RESTART;p->submitted=0;p->error=0;}
                }else if(b.op==AP_LAUNCH && (!result.pid || p->stopping)) {
                    p->launching=1;p->error=0; /* repeated launch requests coalesce */
                }else {
                    struct gw_result a;
                    status=gw_rpc(manager,(struct gw_body){.op=b.op==AP_BACKGROUND?GW_BACKGROUND:GW_FOREGROUND,.id=b.id,.w=result.pid,.h=result.birth},0,0,&a);
                    if(!status)status=(int)a.status;
                }
                if(!status)status=app_progress(manager,p,b.id,&result);
            }
            result.status=(dg_u32)status;
        }
        if(m.request.h.bits&0x80000000u){dg_u32 reply=m.request.h.remote;m.request.h.remote=0;mach_msg_destroy(&m);m.request.h.remote=reply;}
        ipc_note("REQUEST caller=%u birth=%u op=%u app=%u status=%u pid=%u version=%u state=%u visible=%u",caller.pid,caller.birth,b.op,b.id,result.status,result.pid,result.birth,result.state,result.visible);
        struct ap_reply reply={{18,sizeof(reply),m.request.h.remote,0,0,AP_MSG+100},result};
        if(reply.h.remote && mach_msg(&reply,1|0x10,sizeof(reply),0,0,1000,0))return failure("applications reply",-1);
    }
}
