/* SPDX-License-Identifier: 0BSD */
/* Passive QEMU API/exec admission observations, not a graphical service shim. */
#include "duchamp-darwin-iokit.h"
extern int fork(void),waitpid(int,int *,int),execve(const char *,char *const *,char *const *);
extern int setuid(unsigned),setgid(unsigned),dup2(int,int),pipe(int *),fcntl(int,int,...);
extern void _exit(int) __attribute__((noreturn));
extern void sync(void);
extern char ***_NSGetEnviron(void);
extern _Bool _dyld_get_shared_cache_uuid(unsigned char[16]);
extern const void *_dyld_get_shared_cache_range(size_t *);

static int observe(const char *name,const char *path) {
    char log[160];snprintf(log,sizeof(log),"/private/var/tmp/apple-%s-loader.log",name);
    int fd=open(log,0x601,0600),statuspipe[2];
    if(fd<0 || pipe(statuspipe))return ipc_fail("loader output");
    if(fcntl(statuspipe[1],2,1)<0)return ipc_fail("exec status close-on-exec");
    int child=fork();if(child<0)return ipc_fail("fork");
    if(!child) {
        close(statuspipe[0]);
        int error=0;
        if(dup2(fd,1)<0 || dup2(fd,2)<0 || setgid(501) || setuid(501))error=*__error();
        close(fd);
        if(!error){char *args[]={(char *)path,0};execve(path,args,*_NSGetEnviron());error=*__error();}
        ipc_write_all(statuspipe[1],&error,sizeof(error));_exit(125);
    }
    close(statuspipe[1]);close(fd);
    int status=0,done=0,timed=0;
    for(unsigned n=0;n<300;n++) {
        int r=waitpid(child,&status,1);
        if(r==child){done=1;break;}if(r<0)return ipc_fail("waitpid");usleep(100000);
    }
    if(!done){timed=1;kill(child,15);usleep(200000);if(waitpid(child,&status,1)!=child){kill(child,9);if(waitpid(child,&status,0)!=child)return ipc_fail("timeout reap");}}
    int error=0;ssize_t n=read(statuspipe[0],&error,sizeof(error));close(statuspipe[0]);
    if(n!=0 && n!=sizeof(error))return ipc_fail("exec status read");
    ipc_note("APPLE EXEC name=%s pid=%d target_uid=501 exec_errno=%d accepted=%d wait_status=%d signal=%d exit=%d timeout=%d",
        name,child,error,n==0,status,status&127,(status>>8)&255,timed);
    /* The observation is not success: a dyld failure or an exec rejection is
     * recorded as a dependency blocker, never as a running graphical service. */
    return 0;
}

int main(void) {
    if(ipc_identity("ios-admission"))return 1;
    unsigned char uuid[16]={0};size_t size=0;
    int present=_dyld_get_shared_cache_uuid(uuid);const void *base=_dyld_get_shared_cache_range(&size);
    ipc_note("DYLD images=%u cache_present=%d base=%p bytes=%lu",_dyld_image_count(),present,base,size);
    dg_u32 master=0;if(host_get_io_main(mach_host_self(),&master) || !master)return ipc_fail("IOMainPort");
    const char *providers[]={"IOCoreSurfaceRoot","IOMobileFramebuffer","AppleCLCD","SweetHIDButtons","SweetHIDTouch","IOHIDSystem","IOAccelerator"};
    dg_u32 surface=0,fb=0;
    for(unsigned i=0;i<sizeof(providers)/sizeof(providers[0]);i++) {
        dg_u32 p=match(master,providers[i]);ipc_note("PROVIDER name=%s matched=%u",providers[i],p!=0);
        if(i==0)surface=p;else if(i==2)fb=p;else if(p)mach_port_deallocate(mach_task_self_,p);
    }
    if(!surface || !fb)return ipc_fail("baseline display providers");
    dg_u32 client=open_client(surface,0),framebuffer=open_client(fb,0);
    if(!client || !framebuffer)return ipc_fail("baseline clients");
    dg_u8 limits[24]={0};dg_u32 bytes=sizeof(limits);
    int rc=method(client,13,0,0,0,0,limits,&bytes,0,0);
    if(rc || bytes!=24 || limits[22]!=1)return ipc_fail("surface limits");
    dg_u64 display[2]={0};dg_u32 count=2;rc=method(framebuffer,8,0,0,0,0,0,0,display,&count);
    if(rc || count!=2 || !display[0] || !display[1])return ipc_fail("display query");
    ipc_note("CAPABILITY surface_limits_version=%u row_mask=%u display=%llux%llu scope=existing-project-subset",
        limits[22],dg_get32(limits+4),display[0],display[1]);
    if(observe("backboardd","/usr/libexec/backboardd") ||
       observe("SpringBoard","/System/Library/CoreServices/SpringBoard.app/SpringBoard"))return 1;
    ipc_note("OBSERVED services_running_not_proven=1 no_fake_service_replies=1");
    sync();
    for(unsigned i=1;i<=3;i++){sleep(1);ipc_note("HEARTBEAT %u",i);sync();}
    ipc_note("COMPLETE");sync();return 0;
}
