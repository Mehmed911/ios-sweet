/* SPDX-License-Identifier: 0BSD
 * Original 20F66 IOKit client; never publishes a GPU or changes device discovery.
 * The surface service tested here is not an IOAcceleratorES implementation.
 */
#include "sweet-foundation-api.h"
#include "duchamp-iokit-contract.h"
extern void *dlopen(const char *,int),*dlsym(void *,const char *);
extern unsigned int mach_task_self_;
extern _Bool _dyld_get_shared_cache_uuid(unsigned char[16]);
static int tests,failed;
static int check(const char *name,int ok) {
    tests++;failed+=!ok;
    printf("PROVIDER CHECK %s passed=%d\n",name,!!ok);fflush(0);return ok;
}
int main(void) {
    NSAutoreleasePool *pool=[[NSAutoreleasePool alloc] init];
    printf("PROVIDER IDENTITY pid=%d ppid=%d uid=%u\n",getpid(),getppid(),getuid());fflush(0);
    unsigned char uuid[16]={0};
    const unsigned char expected[16]={0xe5,0x42,0x0d,0xb3,0x30,0xd0,0x33,0xaa,0x8b,0x7e,0x05,0xb5,0x03,0x8b,0xb4,0x6d};
    if(!check("original-cache",_dyld_get_shared_cache_uuid(uuid) && !memcmp(uuid,expected,16)))return 2;
    if(!check("mobile-identity",getpid()>1 && getuid()==501))return 2;
    void *lib=dlopen("/System/Library/Frameworks/IOKit.framework/Versions/A/IOKit",2);
    if(!check("original-iokit",lib!=0))return 2;
    int (*mainport)(dg_u32,dg_u32 *)=dlsym(lib,"IOMasterPort");
    id (*matching)(const char *)=dlsym(lib,"IOServiceMatching");
    int (*getservices)(dg_u32,id,dg_u32 *)=dlsym(lib,"IOServiceGetMatchingServices");
    dg_u32 (*next)(dg_u32)=dlsym(lib,"IOIteratorNext");
    int (*release)(dg_u32)=dlsym(lib,"IOObjectRelease");
    int (*getclass)(dg_u32,char *)=dlsym(lib,"IOObjectGetClass");
    int (*getid)(dg_u32,dg_u64 *)=dlsym(lib,"IORegistryEntryGetRegistryEntryID");
    int (*openclient)(dg_u32,dg_u32,dg_u32,dg_u32 *)=dlsym(lib,"IOServiceOpen");
    int (*closeclient)(dg_u32)=dlsym(lib,"IOServiceClose");
    int (*method)(dg_u32,dg_u32,const dg_u64 *,dg_u32,const void *,size_t,
        dg_u64 *,dg_u32 *,void *,size_t *)=dlsym(lib,"IOConnectCallMethod");
    int (*map)(dg_u32,dg_u32,dg_u32,dg_u64 *,dg_u64 *,dg_u32)=dlsym(lib,"IOConnectMapMemory64");
    if(!check("public-symbols",mainport && matching && getservices && next && release && getclass &&
             getid && openclient && closeclient && method && map))return 2;
    dg_u32 master=0;int kr=mainport(0,&master);
    printf("PROVIDER MAIN kr=0x%x port=0x%x\n",kr,master);fflush(0);
    if(!check("main-port",kr==0 && dg_object_valid(master)))return 3;
    const char *names[]={"IOAcceleratorES","DuchampDeliberatelyAbsentGraphicsProvider","IOCoreSurfaceRoot"};
    dg_u32 surface=0;
    for(int i=0;i<3;i++) {
        id dict=matching(names[i]);
        if(!check(i==0?"accelerator-dictionary":i==1?"missing-dictionary":"surface-dictionary",dict!=0))return 3;
        NSString *value=[dict objectForKey:@"IOProviderClass"];
        const char *text=[value UTF8String];
        printf("PROVIDER DICTIONARY class=%s IOProviderClass=%s keys=%lu\n",names[i],text?text:"<null>",[dict count]);fflush(0);
        if(!check(i==0?"accelerator-class-key":i==1?"missing-class-key":"surface-class-key",text && !strcmp(text,names[i])))return 3;
        dg_u32 iter=0;kr=getservices(master,dict,&iter); /* consumes dict */
        dg_u32 service=dg_object_valid(iter)?next(iter):0;dg_u32 extra=0;
        if(dg_object_valid(iter)){extra=next(iter);release(iter);}
        printf("PROVIDER ENUM class=%s kr=0x%x iterator=0x%x first=0x%x extra=0x%x\n",names[i],kr,iter,service,extra);fflush(0);
        if(extra)release(extra);
        if(i<2) {
            check(i==0?"accelerator-absent":"missing-service-empty",kr==0 && !service);
            check(i==0?"zero-accelerator-rejected":"zero-missing-rejected",!dg_object_valid(service));
            /* No IOServiceOpen or user-client operation is attempted on zero. */
            if(service)release(service);
        } else {
            if(!check("real-surface-service",kr==0 && dg_object_valid(service)))return 3;
            surface=service;
        }
    }
    char cls[128]={0};dg_u64 registry=0;
    int class_kr=getclass(surface,cls),id_kr=getid(surface,&registry);
    printf("PROVIDER OBJECT port=0x%x class=%s class_kr=0x%x registry=%llu registry_kr=0x%x\n",
        surface,cls,class_kr,registry,id_kr);fflush(0);
    check("surface-object-identity",class_kr==0 && !strcmp(cls,"IOCoreSurfaceRoot") && id_kr==0 && registry!=0);
    dg_u32 connection=0;kr=openclient(surface,mach_task_self_,0,&connection);
    printf("PROVIDER OPEN service=0x%x type=0 kr=0x%x connection=0x%x owner_pid=%d\n",surface,kr,connection,getpid());fflush(0);
    if(!check("real-userclient-open",kr==0 && dg_object_valid(connection)))return 3;
    unsigned char limits[32];memset(limits,0xa5,sizeof(limits));size_t length=24;
    kr=method(connection,13,0,0,0,0,0,0,limits,&length);
    printf("PROVIDER METHOD selector=13 kr=0x%x bytes=%lu\n",kr,length);fflush(0);
    check("implemented-limits",kr==0 && length==24 && limits[22]==1 && limits[24]==0xa5);
    length=8;memset(limits,0xa5,sizeof(limits));
    kr=method(connection,13,0,0,0,0,0,0,limits,&length);
    printf("PROVIDER METHOD selector=13 short=1 kr=0x%x bytes=%lu\n",kr,length);fflush(0);
    check("short-output-rejected",kr!=0 && limits[8]==0xa5 && limits[31]==0xa5);
    kr=method(connection,0xffffffffu,0,0,0,0,0,0,0,0);
    printf("PROVIDER METHOD selector=4294967295 kr=0x%x\n",kr);fflush(0);
    check("unsupported-selector-error",(dg_u32)kr==0xe00002c7u);
    dg_u64 zero=0;length=sizeof(limits);memset(limits,0xa5,sizeof(limits));
    kr=method(connection,34,&zero,1,0,0,0,0,limits,&length);
    printf("PROVIDER METHOD selector=34 foreign_or_null_capability=0 kr=0x%x\n",kr);fflush(0);
    check("null-surface-capability-rejected",kr!=0);
    dg_u64 address=0,size=0;
    kr=map(connection,0xffffffffu,mach_task_self_,&address,&size,1);
    printf("PROVIDER MAP type=4294967295 kr=0x%x address=%llu bytes=%llu\n",kr,address,size);fflush(0);
    check("unsupported-memory-map",kr!=0 && address==0 && size==0);
    check("userclient-close",closeclient(connection)==0);
    check("service-release",release(surface)==0);
    check("null-and-dead-handles-rejected",!dg_object_valid(0) && !dg_object_valid(0xffffffffu));
    release(master);
    printf("PROVIDER DONE checks=%d failed=%d gpu_published=0 metal_compatibility=0 authentic_frame=0\n",tests,failed);fflush(0);
    [pool drain];return failed?1:0;
}
