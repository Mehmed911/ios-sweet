/* SPDX-License-Identifier: 0BSD */
/* Original-service execution observer. No framework or Mach-service emulation. */
#include "sweet-ipc.h"
extern int fork(void),waitpid(int,int *,int),execve(const char *,char *const *,char *const *);
extern int setuid(unsigned),setgid(unsigned),dup2(int,int),pipe(int *),fcntl(int,int,...);
extern void _exit(int) __attribute__((noreturn));
extern void sync(void);
extern int usleep(unsigned);
extern _Bool _dyld_get_shared_cache_uuid(unsigned char[16]);
extern const void *_dyld_get_shared_cache_range(size_t *);
extern _Bool _dyld_shared_cache_contains_path(const char *);
extern unsigned _dyld_image_count(void);

static int observe(const char *name,const char *path) {
    char log[160];snprintf(log,sizeof(log),"/private/var/tmp/apple-%s-loader.log",name);
    int fd=open(log,0x601,0600),statuspipe[2];
    if(fd<0 || pipe(statuspipe))return ipc_fail("loader output");
    if(fcntl(statuspipe[1],2,1)<0)return ipc_fail("exec close-on-exec");
    ipc_note("PRE EXEC name=%s",name);
    int child=fork();if(child<0)return ipc_fail("fork");
    if(!child) {
        close(statuspipe[0]);int error=0;
        if(dup2(fd,1)<0 || dup2(fd,2)<0 || setgid(501) || setuid(501))error=*__error();
        close(fd);
        if(!error){
            char *args[]={(char *)path,0};
            char *env[]={"PATH=/usr/bin:/bin:/usr/sbin:/sbin","HOME=/private/var/mobile",
                "DYLD_PRINT_TO_STDERR=1","DYLD_PRINT_LIBRARIES=1","DYLD_PRINT_INITIALIZERS=1",0};
            execve(path,args,env);error=*__error();
        }
        ipc_write_all(statuspipe[1],&error,sizeof(error));_exit(125);
    }
    close(statuspipe[1]);close(fd);
    int status=0,done=0,timed=0;
    for(unsigned n=0;n<600;n++) {
        int r=waitpid(child,&status,1);
        if(r==child){done=1;break;}if(r<0)return ipc_fail("waitpid");usleep(100000);
    }
    if(!done){timed=1;kill(child,15);usleep(200000);if(waitpid(child,&status,1)!=child){kill(child,9);if(waitpid(child,&status,0)!=child)return ipc_fail("timeout reap");}}
    int error=0;ssize_t n=read(statuspipe[0],&error,sizeof(error));close(statuspipe[0]);
    if(n!=0 && n!=sizeof(error))return ipc_fail("exec status read");
    ipc_note("APPLE EXEC name=%s pid=%d target_uid=501 exec_errno=%d accepted=%d wait_status=%d signal=%d exit_bits=%d timeout=%d",
        name,child,error,n==0,status,status&127,(status>>8)&255,timed);
    return 0;
}

int main(void) {
    if(ipc_identity("ios20f66"))return 1;
    const unsigned char expected[16]={0xe5,0x42,0x0d,0xb3,0x30,0xd0,0x33,0xaa,0x8b,0x7e,0x05,0xb5,0x03,0x8b,0xb4,0x6d};
    unsigned char uuid[16]={0};size_t bytes=0;
    const void *base=_dyld_get_shared_cache_range(&bytes);
    if(!_dyld_get_shared_cache_uuid(uuid) || memcmp(uuid,expected,16) || !base || !bytes)
        return ipc_fail("matching shared cache not mapped");
    ipc_note("CACHE UUID=E5420DB330D033AA8B7E05B5038BB46D base=%p bytes=%lu images=%u",base,bytes,_dyld_image_count());
    const char *paths[]={"/System/Library/PrivateFrameworks/StudyLog.framework/StudyLog",
        "/System/Library/PrivateFrameworks/SpringBoard.framework/SpringBoard"};
    for(unsigned i=0;i<2;i++){
        if(!_dyld_shared_cache_contains_path(paths[i]))return ipc_fail("framework absent from live cache");
        ipc_note("CACHE PATH index=%u present=1",i);
    }
    if(observe("backboardd","/usr/libexec/backboardd") ||
        observe("SpringBoard","/System/Library/CoreServices/SpringBoard.app/SpringBoard"))return 1;
    ipc_note("COMPLETE runtime_success_not_assumed=1");sync();return 0;
}
