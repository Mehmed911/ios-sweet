/* SPDX-License-Identifier: 0BSD
 * QEMU diagnostic client of the original public IOSurface API. No Metal
 * replacement, framebuffer submission, or SpringBoard ownership claim.
 */
#include "sweet-foundation-api.h"
extern void *dlopen(const char *,int), *dlsym(void *,const char *);
extern _Bool _dyld_get_shared_cache_uuid(unsigned char[16]);
extern unsigned int mach_task_self_,mach_port_deallocate(unsigned int,unsigned int);
@interface NSNumber (SurfaceValues)
+ (id)numberWithUnsignedLongLong:(unsigned long long)value;
@end
typedef void *Surface;
typedef unsigned int u32;
static int total,failed;
static int check(const char *name,int ok) {
    total++;failed+=!ok;
    printf("SURFACE CHECK %s passed=%d\n",name,!!ok);fflush(0);return ok;
}
int main(void) {
    printf("SURFACE DIAGNOSTIC pid=%d ppid=%d uid=%u\n",getpid(),getppid(),getuid());fflush(0);
    NSAutoreleasePool *pool=[[NSAutoreleasePool alloc] init];
    unsigned char uuid[16]={0};
    const unsigned char expected[16]={0xe5,0x42,0x0d,0xb3,0x30,0xd0,0x33,0xaa,0x8b,0x7e,0x05,0xb5,0x03,0x8b,0xb4,0x6d};
    if(!check("original-cache",_dyld_get_shared_cache_uuid(uuid) && !memcmp(uuid,expected,16)))return 2;
    if(!check("mobile-identity",getpid()>1 && getuid()==501))return 2;
    void *lib=dlopen("/System/Library/Frameworks/IOSurface.framework/IOSurface",2);
    if(!check("original-library",lib!=0))return 2;
    Surface (*create)(const void *)=dlsym(lib,"IOSurfaceCreate");
    u32 (*getid)(Surface)=dlsym(lib,"IOSurfaceGetID");
    size_t (*width)(Surface)=dlsym(lib,"IOSurfaceGetWidth");
    size_t (*height)(Surface)=dlsym(lib,"IOSurfaceGetHeight");
    size_t (*row)(Surface)=dlsym(lib,"IOSurfaceGetBytesPerRow");
    size_t (*size)(Surface)=dlsym(lib,"IOSurfaceGetAllocSize");
    u32 (*format)(Surface)=dlsym(lib,"IOSurfaceGetPixelFormat");
    void *(*base)(Surface)=dlsym(lib,"IOSurfaceGetBaseAddress");
    u32 (*lock)(Surface,u32,u32 *)=dlsym(lib,"IOSurfaceLock");
    u32 (*unlock)(Surface,u32,u32 *)=dlsym(lib,"IOSurfaceUnlock");
    u32 (*port)(Surface)=dlsym(lib,"IOSurfaceCreateMachPort");
    Surface (*fromport)(u32)=dlsym(lib,"IOSurfaceLookupFromMachPort");
    Surface (*lookup)(u32)=dlsym(lib,"IOSurfaceLookup");
    void (*release)(const void *)=dlsym(lib,"CFRelease");
    if(!release)release=dlsym((void *)-2L,"CFRelease");
    if(!check("public-symbols",create && getid && width && height && row && size && format &&
            base && lock && unlock && port && fromport && lookup && release))return 2;
    const char *names[]={"kIOSurfaceWidth","kIOSurfaceHeight","kIOSurfaceBytesPerElement",
        "kIOSurfaceBytesPerRow","kIOSurfaceAllocSize","kIOSurfacePixelFormat"};
    id keys[6],values[6];unsigned long long numbers[]={64,32,4,256,8192,0x42475241};
    for(int i=0;i<6;i++) {
        id *key=dlsym(lib,names[i]);
        if(!check(names[i],key && *key))return 2;
        keys[i]=*key;values[i]=[NSNumber numberWithUnsignedLongLong:numbers[i]];
    }
    Surface s=create([NSDictionary dictionaryWithObjects:values forKeys:keys count:6]);
    if(!check("create",s!=0))return 3;
    u32 sid=getid(s);size_t stride=row(s),allocation=size(s);
    printf("SURFACE OBJECT id=%u width=%lu height=%lu stride=%lu allocation=%lu format=0x%x\n",
        sid,width(s),height(s),stride,allocation,format(s));fflush(0);
    int bounded=sid>1 && width(s)==64 && height(s)==32 && stride>=256 && stride<=16384 &&
        allocation>=stride*32 && allocation<=1<<20 && format(s)==0x42475241;
    if(!check("layout-and-bounds",bounded)){release(s);return 3;}
    u32 seed=0,kr=lock(s,0,&seed);
    printf("SURFACE LOCK result=0x%x seed=%u\n",kr,seed);fflush(0);
    if(!check("lock",kr==0)){release(s);return 3;}
    unsigned char *bytes=base(s);
    if(!check("mapping",bytes!=0)){unlock(s,0,&seed);release(s);return 3;}
    for(size_t y=0;y<32;y++)for(size_t x=0;x<256;x++)bytes[y*stride+x]=(unsigned char)((x*19+y*5+7)&255);
    kr=unlock(s,0,&seed);check("unlock",kr==0);
    u32 right=port(s);check("mach-port",right && right!=0xffffffffu);
    printf("SURFACE PORT id=%u name=0x%x\n",sid,right);fflush(0);
    Surface alias=right?fromport(right):0;
    if(check("lookup-from-mach-port",alias!=0)) {
        check("alias-identity",getid(alias)==sid && width(alias)==64 && height(alias)==32);
        unsigned char *other=base(alias);int matches=other && row(alias)==stride && size(alias)==allocation;
        for(size_t y=0;matches && y<32;y++)for(size_t x=0;x<256;x++)
            if(other[y*stride+x]!=(unsigned char)((x*19+y*5+7)&255)){matches=0;break;}
        check("actual-shared-bytes",matches);
        release(s);s=0;
        check("retained-alias",getid(alias)==sid && base(alias)!=0);
        release(alias);
    }
    if(s)release(s);
    if(right && right!=0xffffffffu)check("port-deallocate",mach_port_deallocate(mach_task_self_,right)==0);
    Surface absent=lookup(0xffffffffu);check("invalid-id-rejected",absent==0);if(absent)release(absent);
    absent=fromport(0);check("null-port-rejected",absent==0);if(absent)release(absent);
    values[0]=[NSNumber numberWithUnsignedLongLong:0];
    absent=create([NSDictionary dictionaryWithObjects:values forKeys:keys count:6]);
    /* Zero-width buffers with an explicit allocation are accepted by this
     * port. Record the behavior; do not invent an Apple compatibility rule. */
    printf("SURFACE OBSERVATION zero-width accepted=%d width=%lu allocation=%lu\n",
        absent!=0,absent?width(absent):0,absent?size(absent):0);fflush(0);
    if(absent)release(absent);
    /* Actual source limit: SWEET_SURFACE_MAX_DIM == 16384. */
    values[0]=[NSNumber numberWithUnsignedLongLong:16385];
    absent=create([NSDictionary dictionaryWithObjects:values forKeys:keys count:6]);
    check("over-width-rejected",absent==0);if(absent)release(absent);
    printf("SURFACE DONE checks=%d failed=%d cross_process=0 metal_compatibility=0\n",total,failed);fflush(0);
    [pool drain];return failed?1:0;
}
