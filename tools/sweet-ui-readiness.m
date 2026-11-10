/* QEMU only. Use matching 20F66 native APIs; never set a readiness bit directly. */
#include "sweet-foundation-api.h"
extern void *dlopen(const char *,int), *dlsym(void *,const char *);
extern Class objc_getClass(const char *);
extern _Bool _dyld_get_shared_cache_uuid(unsigned char[16]);
@interface NSError : NSObject
- (long)code;
- (NSString *)description;
@end
@interface NSObject (SweetReadiness)
+ (id)defaultServiceDomainIndirect;
- (void)getServerStatusWithCompletionHandler:(void (^)(unsigned int))handler;
- (void)rebuildApplicationDatabasesForSystem:(BOOL)system internal:(BOOL)internal
    user:(BOOL)user completionHandler:(void (^)(BOOL,NSError *))handler;
+ (id)applicationProxyForIdentifier:(NSString *)identifier;
- (NSString *)bundleIdentifier;
- (id)bundleURL;
- (NSString *)path;
- (BOOL)isInstalled;
- (BOOL)isPlaceholder;
@end

typedef id (*factory_fn)(Class,id,_Bool,void (^)(NSError *));
static unsigned int status(void *core,int *witness) {
    __block int seen=0,failed=0;
    __block unsigned int value=0xffffffffu;
    factory_fn factory=(factory_fn)dlsym(core,"_LSDServiceGetXPCProxyForServiceClass");
    Class domain=objc_getClass("_LSDServiceDomain"), service=objc_getClass("_LSDReadService");
    if(!factory || !domain || !service){*witness=0;return value;}
    id proxy=factory(service,[domain defaultServiceDomainIndirect],1,^(NSError *error){
        failed=1;printf("REGISTRY STATUS ERROR %s\n",[[error description] UTF8String]);fflush(0);
    });
    [proxy getServerStatusWithCompletionHandler:^(unsigned int result){seen=1;value=result;}];
    *witness=seen && !failed;
    return value;
}
#if SWEET_VERIFY_SPRINGBOARD_RECORD || SWEET_REUSE_VERIFIED_APP_REGISTRY
static int application_ready(const char *bundle, const char *expected_path) {
    Class app_class=objc_getClass("LSApplicationProxy");
    id app=[app_class applicationProxyForIdentifier:[NSString stringWithUTF8String:bundle]];
    const char *identifier=[[app bundleIdentifier] UTF8String];
    const char *path=[[[app bundleURL] path] UTF8String];
    int installed=[app isInstalled],placeholder=[app isPlaceholder];
    printf("REGISTRY APP identifier=%s installed=%d placeholder=%d path=%s\n",
        identifier?identifier:"none",installed,placeholder,path?path:"none");fflush(0);
    return identifier && !strcmp(identifier,bundle) && path && !strcmp(path,expected_path) &&
        installed && !placeholder;
}
#endif
static int registry(void) {
    void *core=dlopen("/System/Library/Frameworks/CoreServices.framework/CoreServices",2);
    if(!core)return 2;
    factory_fn factory=(factory_fn)dlsym(core,"_LSDServiceGetXPCProxyForServiceClass");
    Class domain=objc_getClass("_LSDServiceDomain"),service=objc_getClass("_LSDModifyService");
    if(!factory || !domain || !service)return 3;
    int seen=0;unsigned int before=status(core,&seen);
    printf("REGISTRY BEFORE witnessed=%d status=%u\n",seen,before);fflush(0);
    if(!seen)return 4;
#if SWEET_REUSE_VERIFIED_APP_REGISTRY
    if((before&0x100) && !(before&0x200) &&
        application_ready("com.apple.springboard","/System/Library/CoreServices/SpringBoard.app") &&
        application_ready("com.apple.purplebuddy","/Applications/Setup.app")) {
        printf("REGISTRY EXISTING RECORDS PASS\n");fflush(0);
        return 0;
    }
#endif
    __block int replied=0,failed=0,rebuilt=0;
    __block long code=0;
    id proxy=factory(service,[domain defaultServiceDomainIndirect],1,^(NSError *error){
        failed=1;printf("REGISTRY REBUILD TRANSPORT ERROR %s\n",[[error description] UTF8String]);fflush(0);
    });
    printf("REGISTRY REBUILD REQUEST system=1 internal=0 user=1\n");fflush(0);
    [proxy rebuildApplicationDatabasesForSystem:1 internal:0 user:1 completionHandler:^(BOOL ok,NSError *error){
        replied=1;rebuilt=ok;code=error?[error code]:0;
        if(error)printf("REGISTRY REBUILD ERROR %s\n",[[error description] UTF8String]);
        fflush(0);
    }];
    printf("REGISTRY REBUILD RESULT callback=%d transport_error=%d rebuilt=%d code=%ld\n",replied,failed,rebuilt,code);fflush(0);
    int complete=0;
    for(int i=0;i<15;i++) {
        unsigned int value=status(core,&seen);
        complete=seen && (value&0x100) && !(value&0x200);
        printf("REGISTRY AFTER sample=%d witnessed=%d status=%u complete=%d\n",i,seen,value,complete);fflush(0);
        if(complete || !seen || failed || !replied || !rebuilt || code)break;
        sleep(1);
    }
    if(replied && !failed && rebuilt && !code && complete) {
#if SWEET_VERIFY_SPRINGBOARD_RECORD || SWEET_REUSE_VERIFIED_APP_REGISTRY
        if(!application_ready("com.apple.springboard","/System/Library/CoreServices/SpringBoard.app"))return 6;
        printf("REGISTRY APP RECORD PASS\n");fflush(0);
#endif
#if SWEET_REUSE_VERIFIED_APP_REGISTRY
        if(!application_ready("com.apple.purplebuddy","/Applications/Setup.app"))return 6;
#endif
        printf("REGISTRY NATIVE COMPLETE PASS\n");fflush(0);return 0;
    }
    return 5;
}
static int display(void) {
    void *bks=dlopen("/System/Library/PrivateFrameworks/BackBoardServices.framework/BackBoardServices",2);
    if(!bks)return 2;
    /* 20F66 disassembly: native port getter; MIG stub takes port, four float
     * pointers and two byte pointers, writes outputs only after reply validation.
     * The higher-level getter discards its return code, so use the MIG result.
     */
    typedef unsigned int (*port_fn)(void);
    typedef int (*query_fn)(unsigned int,float *,float *,float *,float *,unsigned char *,unsigned char *);
    port_fn get_port=(port_fn)dlsym(bks,"BKSDisplayServicesServerPort");
    query_fn query=(query_fn)dlsym(bks,"_BKSDisplayGetMainScreenInfo");
    if(!get_port || !query)return 3;
    unsigned int port=get_port();
    printf("DISPLAY NATIVE PORT value=%u\n",port);fflush(0);
    if(!port)return 4;
    int all=1;
    for(int i=0;i<2;i++) {
        float a=-1,b=-1,c=-1,d=-1;
        unsigned char e=255,f=255;
        int result=query(port,&a,&b,&c,&d,&e,&f);
        /* The fourth opaque scalar can be zero. Do not infer its meaning or
         * reject a validated native reply merely for that value. This checks
         * transport/output sanity, not rendering or physical panel geometry.
         */
        int valid=!result && a>0 && a<=16384 && b>0 && b<=16384 &&
            c>0 && c<=16384 && d>=0 && d<=16384 && e<=1 && f<=1;
        printf("DISPLAY NATIVE REPLY sample=%d kr=%d values=%.3f,%.3f,%.3f,%.3f flags=%u,%u valid=%d\n",
            i,result,(double)a,(double)b,(double)c,(double)d,e,f,valid);fflush(0);
        all=all && valid;
        if(i==0)sleep(1);
    }
    if(all){printf("DISPLAY NATIVE QUERY PASS\n");fflush(0);return 0;}
    return 5;
}
int main(int argc,char **argv) {
    NSAutoreleasePool *pool=[[NSAutoreleasePool alloc] init];
    unsigned char uuid[16]={0};
    const unsigned char expected[16]={0xe5,0x42,0x0d,0xb3,0x30,0xd0,0x33,0xaa,0x8b,0x7e,0x05,0xb5,0x03,0x8b,0xb4,0x6d};
    if(argc!=2 || getuid()!=501 || getppid()!=1 || !_dyld_get_shared_cache_uuid(uuid) || memcmp(uuid,expected,16))return 1;
    printf("READINESS IDENTITY mode=%s pid=%d ppid=1 uid=501 cache=20F66\n",argv[1],getpid());fflush(0);
    int result=!strcmp(argv[1],"registry")?registry():!strcmp(argv[1],"display")?display():9;
    printf("READINESS DONE kind=%s status=%d\n",argv[1],result);fflush(0);
    [pool drain];return result;
}
