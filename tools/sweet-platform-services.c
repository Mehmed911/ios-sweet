/* QEMU batch: original process identities, persisted CLI diagnostics and a
 * bounded native LaunchServices reply witness. A Mach lookup is not a reply.
 */
#include "sweet-ipc.h"
extern int fork(void),dup2(int,int),waitpid(int,int *,int),execve(const char *,char *const [],char *const []);
extern int setuid(unsigned int),setgid(unsigned int),setenv(const char *,const char *,int);
extern char ***_NSGetEnviron(void);
extern void _exit(int) __attribute__((noreturn));
extern void sync(void);
extern char *strstr(const char *,const char *);
extern int mkdir(const char *,unsigned short),chown(const char *,unsigned int,unsigned int);
extern int proc_pidinfo(int,int,unsigned long long,void *,int);
extern _Bool _dyld_get_shared_cache_uuid(unsigned char[16]);
extern const void *_dyld_get_shared_cache_range(size_t *);
struct bsd_info {
    unsigned int flags,status,xstatus,pid,ppid,uid,gid,ruid,rgid,svuid,svgid,reserved;
    char comm[16],name[32];
    unsigned int nfiles,pgid,jobc,device,foreground;
    int nice;
    unsigned long long start_seconds,start_micros;
};
_Static_assert(sizeof(struct bsd_info)==136,"Darwin proc_bsdinfo");
static char output[65536];

static int command(const char *tag,const char *path,char *const args[],int mobile) {
    char file[192]; snprintf(file,sizeof(file),"/private/var/tmp/platform-%s.txt",tag);
    int fd=open(file,0x601,0644);
    if(fd<0) return -1;
    int pid=fork();
    if(pid<0) {close(fd);return -1;}
    if(!pid) {
        if(dup2(fd,1)<0 || dup2(fd,2)<0) _exit(126);
        if(fd>2) close(fd);
        if(ipc_trace>2) close(ipc_trace);
        if(mobile && (setgid(501) || setuid(501) || setenv("HOME","/var/mobile",1) ||
            setenv("__CF_USER_TEXT_ENCODING","0x1F5:0:0",1))) _exit(125);
        execve(path,args,*_NSGetEnviron()); _exit(127);
    }
    int status=-1,reaped=0;
    for(int i=0;i<20;i++) {
        int got=waitpid(pid,&status,1);
        if(got==pid) {reaped=1;break;}
        if(got<0 && *__error()!=4) break;
        sleep(1);
    }
    if(!reaped) {
        kill(pid,9);
        while(waitpid(pid,&status,0)<0 && *__error()==4) {}
    }
    fsync(fd);close(fd);
    ipc_note("PLATFORM COMMAND tag=%s status=0x%x timeout=%d",tag,status,!reaped);
    fd=open(file,0);
    if(fd<0) return -1;
    size_t at=0;
    while(at<sizeof(output)-1) {
        ssize_t n=read(fd,output+at,sizeof(output)-1-at);
        if(n<0 && *__error()==4) continue;
        if(n<0) {close(fd);return -1;}
        if(!n) break;
        at+=(size_t)n;
    }
    output[at]=0;close(fd);
    return reaped && status==0 && at<sizeof(output)-1?0:-1;
}
static int identity(int pid,const char *path,unsigned int uid,unsigned int gid) {
    struct bsd_info info={0};
    return proc_pidinfo(pid,3,0,&info,sizeof(info))==(int)sizeof(info) &&
        info.pid==(unsigned)pid && info.ppid==1 && info.uid==uid && info.gid==gid && ipc_path_matches(pid,path);
}
static int query(void) {
    int fresh=open("/private/var/tmp/platform-native-query.txt",0x601,0644);
    if(fresh<0)return 0;
    fsync(fresh);close(fresh);
    if(chown("/private/var/tmp/platform-native-query.txt",501,501))return 0;
    char *start[]={"launchctl","kickstart","-p","system/org.sweet.qemu.lsd-native",0};
    if(command("native-start","/bin/launchctl",start,0)) return 0;
    for(int i=0;i<20;i++) {
        int fd=open("/private/var/tmp/platform-native-query.txt",0);
        if(fd>=0) {
            ssize_t n=read(fd,output,sizeof(output)-1);close(fd);
            if(n>0) {
                output[n]=0;
                if(strstr(output,"LSD NATIVE QUERY RESULT")) {
                    if(strstr(output,"LSD NATIVE TRANSPORT PASS status="))
                        return strstr(output,"LSD NATIVE QUERY RESULT reply=1 error=0 status=")!=0;
                    if(strstr(output,"LSD NATIVE QUERY ERROR"))return 0;
                }
            }
        }
        sleep(1);
    }
    ipc_note("PLATFORM NATIVE QUERY TIMEOUT");
    return 0;
}
static int service(const char *label,const char *path,unsigned int uid,unsigned int gid,int index) {
    char target[128],tag[64]; snprintf(target,sizeof(target),"system/%s",label);
    snprintf(tag,sizeof(tag),"%d-start",index);
    char *start[]={"launchctl","kickstart","-p",target,0};
    int started=command(tag,"/bin/launchctl",start,0);
    ipc_note("PLATFORM START label=%s result=%d",label,started);
    int pid=-1;
    for(int i=0;i<5;i++) {
        snprintf(tag,sizeof(tag),"%d-print-%d",index,i);
        char *print[]={"launchctl","print",target,0};
        if(!command(tag,"/bin/launchctl",print,0)) {
            char *p=strstr(output,"pid = ");
            if(p) pid=(int)strtol(p+6,0,10);
            if(pid>1 && identity(pid,path,uid,gid)) break;
        }
        pid=-1;sleep(1);
    }
    if(pid<=1) {ipc_note("PLATFORM SERVICE FAIL label=%s step=identity",label);return -1;}
    for(int i=0;i<3;i++) {
        sleep(1);
        if(!identity(pid,path,uid,gid)) {ipc_note("PLATFORM SERVICE FAIL label=%s step=stability",label);return -1;}
    }
    ipc_note("PLATFORM SERVICE ALIVE label=%s pid=%d uid=%u gid=%u stable=3",label,pid,uid,gid);
    return pid;
}
int main(void) {
    if(ipc_identity("platform-services")) return 1;
    unsigned char uuid[16]={0};
    const unsigned char expected[16]={0xe5,0x42,0x0d,0xb3,0x30,0xd0,0x33,0xaa,0x8b,0x7e,0x05,0xb5,0x03,0x8b,0xb4,0x6d};
    if(!_dyld_get_shared_cache_uuid(uuid) || memcmp(uuid,expected,16)) {ipc_note("PLATFORM CACHE FAIL");return 1;}
    ipc_note("PLATFORM ORIGINAL CACHE VERIFIED");
    size_t cache_length=0;
    const void *cache_base=_dyld_get_shared_cache_range(&cache_length);
    ipc_note("PLATFORM CACHE RANGE base=%p bytes=%lu",cache_base,cache_length);
    const char *dirs[]={"/private/var/mobile","/private/var/mobile/Library","/private/var/mobile/Library/Caches",
        "/private/var/mobile/Library/Preferences","/private/var/mobile/Library/Logs"};
    for(unsigned int i=0;i<sizeof(dirs)/sizeof(*dirs);i++) {
        if((mkdir(dirs[i],0755) && *__error()!=17) || chown(dirs[i],501,501)) return 2;
    }
    int logd=service("com.apple.logd","/usr/libexec/logd",272,272,0);
    int mcm=service("com.apple.containermanagerd","/usr/libexec/containermanagerd",0,0,1);
    int lsd=service("com.apple.lsd","/usr/libexec/lsd",501,501,2);
    int native_reply=lsd>1?query():0;
    ipc_note("PLATFORM NATIVE REPLY verified=%d",native_reply);
    if(native_reply) {
        int saved=open("/private/var/tmp/platform-native-query-first.txt",0x601,0644);
        if(saved>=0){ipc_write_all(saved,output,strlen(output));fsync(saved);close(saved);}
    }
    int final_alive=logd>1 && mcm>1 && lsd>1 && identity(logd,"/usr/libexec/logd",272,272) &&
        identity(mcm,"/usr/libexec/containermanagerd",0,0) && identity(lsd,"/usr/libexec/lsd",501,501);
    ipc_note("PLATFORM FINAL PROVIDERS ALIVE=%d",final_alive);
    int pass=final_alive && native_reply;
    ipc_note("PLATFORM SERVICES RESULT logd=%d mcm=%d lsd=%d native_reply=%d",logd,mcm,lsd,native_reply);
    ipc_note("PLATFORM CORE SERVICES PASS=%d",pass);
#if SWEET_UI_PROBES
    if(pass) {
        int running=service("com.apple.runningboardd","/usr/libexec/runningboardd",0,0,3);
        int backboard=service("com.apple.backboardd","/usr/libexec/backboardd",501,501,4);
        ipc_note("PLATFORM UI PROBES runningboard=%d backboard=%d",running,backboard);
        pass=running>1 && backboard>1;
        for(int check=1;pass && check<=6;check++) {
            sleep(5);
            int a=identity(logd,"/usr/libexec/logd",272,272);
            int b=identity(mcm,"/usr/libexec/containermanagerd",0,0);
            int c=identity(lsd,"/usr/libexec/lsd",501,501);
            int d=identity(running,"/usr/libexec/runningboardd",0,0);
            int e=identity(backboard,"/usr/libexec/backboardd",501,501);
            pass=a && b && c && d && e;
            ipc_note("PLATFORM UI HEALTH check=%d stable=%d logd=%d mcm=%d lsd=%d rbs=%d bks=%d",check,pass,a,b,c,d,e);
        }
        int repeated=identity(lsd,"/usr/libexec/lsd",501,501)?query():0;
        ipc_note("PLATFORM NATIVE REPLY AFTER UI verified=%d",repeated);
        pass=pass && repeated;
    }
#endif
    sync();
    ipc_note("PLATFORM SERVICES DONE status=%d",pass?0:1);
    sync();
    for(;;) sleep(60);
}
