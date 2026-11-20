/* SPDX-License-Identifier: 0BSD */
/* Read real VirtIO input queue reports via the QEMU-only XNU cdev. */
#include "duchamp-darwin-iokit.h"
#include "duchamp-pointer-wire.h"
extern dg_u32 bootstrap_port;
extern int bootstrap_look_up(dg_u32,const char *,dg_u32 *);
static int send(dg_u32 remote,dg_u32 endpoint,unsigned op,struct vp_report r) {
    union {struct dp_message m;dg_u8 bytes[256];} q={0};
    dg_u32 reply=mig_get_reply_port();
    q.m.h=(struct dg_head){19u|(21u<<8)|(op==DP_CONNECT?0x80000000u:0),sizeof(q.m),remote,reply,0,DP_MSG};
    if(op==DP_CONNECT){q.m.count=1;q.m.endpoint=(struct dg_port){endpoint,0,0,20,0};}
    q.m.op=op;q.m.report=r;
    int rc=mach_msg(&q,1|2|0x100,sizeof(q.m),sizeof(q),reply,1000,0);
    if(rc){mig_dealloc_reply_port(reply);return rc;}
    if(q.m.h.id!=DP_MSG+100 || q.m.h.size!=sizeof(struct dp_reply) || q.m.h.bits&0x80000000u)return -1;
    return (int)dg_get32(q.bytes+24);
}
int main(void) {
    char role[48];snprintf(role,sizeof(role),"virtio-pointer-%d",getpid());
    if(ipc_identity(role))return 1;ipc_role="virtio-pointer";
    dg_u32 remote=0,endpoint=0;int fd=-1;unsigned count=0;
    for(;;) {
        if(fd<0) {
            fd=open("/dev/duchamp-pointer",4); /* O_RDONLY|O_NONBLOCK */
            if(fd<0){if(count++>1000)return ipc_fail("input node unavailable");usleep(10000);continue;}
            remote=0;
            for(unsigned i=0;i<100;i++){if(!bootstrap_look_up(bootstrap_port,DP_SERVICE,&remote) && remote)break;usleep(100000);}
            if(!remote || mach_port_allocate(mach_task_self_,1,&endpoint))return ipc_fail("shell input lookup");
            ipc_note("OPEN fd=%d shell=%u origin=virtio-mmio",fd,remote);
        }
        struct vp_report r={0};ssize_t size=read(fd,&r,sizeof(r));
        if(size==(ssize_t)sizeof(r)) {
            dg_u32 x,y;if(!vp_coordinates(&r,DC_W,DC_H,&x,&y))return ipc_fail("invalid input report");
            unsigned op=r.flags==VP_CONNECTED?DP_CONNECT:DP_INPUT;
            int rc=send(remote,endpoint,op,r);
            if(rc){ipc_note("RECONNECT rc=0x%x generation=%u",rc,r.generation);close(fd);fd=-1;mach_port_destroy(mach_task_self_,endpoint);mach_port_deallocate(mach_task_self_,remote);usleep(100000);continue;}
            ipc_note("DEVICE generation=%u seq=%u flags=%u raw=%u,%u screen=%u,%u left=%u",r.generation,r.sequence,r.flags,r.x,r.y,x,y,r.left);
            if(op==DP_CONNECT) {
                int witness=open("/private/var/tmp/virtio-pointer-generation",0x601,0600);char text[64];
                int bytes=snprintf(text,sizeof(text),"%u\n",r.generation);
                if(witness<0 || bytes<1 || ipc_write_all(witness,text,(size_t)bytes) || fsync(witness) || close(witness))return ipc_fail("generation witness");
            }
        }else if(size<0 && (*__error()==35 || *__error()==4))usleep(5000);
        else {ipc_note("DEVICE DISCONNECTED bytes=%ld errno=%d",size,*__error());close(fd);fd=-1;mach_port_destroy(mach_task_self_,endpoint);mach_port_deallocate(mach_task_self_,remote);usleep(100000);}
    }
}
