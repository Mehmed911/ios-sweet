/* SPDX-License-Identifier: 0BSD */
#include "duchamp-darwin-iokit.h"
#include "duchamp-touch-wire.h"
extern dg_u32 bootstrap_port;
extern int bootstrap_look_up(dg_u32,const char *,dg_u32 *);
static int send_touch(dg_u32 remote,dg_u32 endpoint,unsigned op,struct mt_report r) {
    union {struct dt_message m;dg_u8 bytes[512];} q={0};dg_u32 port=mig_get_reply_port();
    q.m.h=(struct dg_head){19u|(21u<<8)|(op==DP_CONNECT?0x80000000u:0),sizeof(q.m),remote,port,0,DT_MSG};
    if(op==DP_CONNECT){q.m.count=1;q.m.endpoint=(struct dg_port){endpoint,0,0,20,0};}
    q.m.op=op;q.m.report=r;
    int rc=mach_msg(&q,1|2|0x100,sizeof(q.m),sizeof(q),port,3000,0);
    if(rc){mig_dealloc_reply_port(port);return rc;}
    if(q.m.h.id!=DT_MSG+100 || q.m.h.size!=sizeof(struct dp_reply) || q.m.h.bits&0x80000000u)return -1;
    return (int)dg_get32(q.bytes+24);
}
int main(void) {
    char name[48];snprintf(name,sizeof(name),"virtio-touch-%d",getpid());if(ipc_identity(name))return 1;ipc_role="virtio-touch";
    int fd=-1;dg_u32 remote=0,endpoint=0;unsigned failures=0;
    for(;;) {
        if(fd<0) {
            fd=open("/dev/duchamp-touch",4);
            if(fd<0){if(failures++>1000)return ipc_fail("touch device unavailable");usleep(10000);continue;}
            for(unsigned n=0;n<100;n++){if(!bootstrap_look_up(bootstrap_port,DP_SERVICE,&remote) && remote)break;usleep(100000);}
            if(!remote || mach_port_allocate(mach_task_self_,1,&endpoint))return ipc_fail("touch shell lookup");
        }
        struct mt_report r={0};ssize_t bytes=read(fd,&r,sizeof(r));
        if(bytes==(ssize_t)sizeof(r)) {
            if(!mt_valid(&r))return ipc_fail("invalid touch report");
            int rc=send_touch(remote,endpoint,r.flags==MT_CONNECTED?DP_CONNECT:DP_INPUT,r);
            if(!rc){ipc_note("DEVICE generation=%u seq=%u flags=%u active=0x%x changed=0x%x origin=virtio-multitouch",r.generation,r.sequence,r.flags,r.active,r.changed);continue;}
            ipc_note("RECONNECT status=0x%x",rc);
        }else if(bytes<0 && (*__error()==35 || *__error()==4)){usleep(5000);continue;}
        close(fd);fd=-1;mach_port_destroy(mach_task_self_,endpoint);mach_port_deallocate(mach_task_self_,remote);remote=endpoint=0;usleep(100000);
    }
}
