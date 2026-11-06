/* Read-only native status query through the original CoreServices proxy.
 * The private factory ABI and registered domain/status selectors were
 * recovered from the matching 20F66 CoreServices, not invented wire messages.
 */
#include "sweet-foundation-api.h"
extern void *dlopen(const char *,int), *dlsym(void *,const char *);
extern Class objc_getClass(const char *);
extern _Bool _dyld_get_shared_cache_uuid(unsigned char[16]);
@interface NSDate : NSObject
+ (id)dateWithTimeIntervalSince1970:(double)seconds;
@end
@interface NSTimeZone : NSObject
+ (id)timeZoneForSecondsFromGMT:(long)seconds;
@end
@interface NSISO8601DateFormatter : NSObject
- (void)setTimeZone:(NSTimeZone *)zone;
- (NSString *)stringFromDate:(NSDate *)date;
@end
@interface NSError : NSObject
- (NSString *)localizedDescription;
- (NSString *)description;
@end
@interface NSObject (SweetLSServiceDomain)
+ (id)defaultServiceDomainIndirect;
- (void)getServerStatusWithCompletionHandler:(void (^)(unsigned int))handler;
@end

int main(void) {
    NSAutoreleasePool *pool=[[NSAutoreleasePool alloc] init];
    unsigned char uuid[16]={0};
    const unsigned char expected[16]={0xe5,0x42,0x0d,0xb3,0x30,0xd0,0x33,0xaa,0x8b,0x7e,0x05,0xb5,0x03,0x8b,0xb4,0x6d};
    printf("LSD NATIVE QUERY ENTERED pid=%d ppid=%d uid=%u\n",getpid(),getppid(),getuid()); fflush(0);
    if (getuid()!=501 || getppid()!=1 || !_dyld_get_shared_cache_uuid(uuid) || memcmp(uuid,expected,16)) return 2;
    NSISO8601DateFormatter *formatter=[[NSISO8601DateFormatter alloc] init];
    [formatter setTimeZone:[NSTimeZone timeZoneForSecondsFromGMT:0]];
    NSString *formatted=[formatter stringFromDate:[NSDate dateWithTimeIntervalSince1970:0]];
    const char *iso=[formatted UTF8String];
    if (!iso || strcmp(iso,"1970-01-01T00:00:00Z")) return 8;
    printf("LSD NATIVE ICU ISO8601 PASS %s\n",iso); fflush(0);
    void *handle=dlopen("/System/Library/Frameworks/CoreServices.framework/CoreServices",2);
    if (!handle) return 3;
    typedef id (*factory_fn)(Class,id,_Bool,void (^)(NSError *));
    factory_fn factory=(factory_fn)dlsym(handle,"_LSDServiceGetXPCProxyForServiceClass");
    Class domain_class=objc_getClass("_LSDServiceDomain");
    Class read_class=objc_getClass("_LSDReadService");
    if (!factory || !domain_class || !read_class) return 4;
    __block int reply_seen=0, error_seen=0;
    __block unsigned int status=0xffffffffu;
    id domain=[domain_class defaultServiceDomainIndirect];
    if (!domain) return 5;
    printf("LSD NATIVE QUERY FACTORY READY\n"); fflush(0);
    id proxy=factory(read_class,domain,1,^(NSError *error) {
        error_seen=1;
        const char *message=[[error description] UTF8String];
        printf("LSD NATIVE QUERY ERROR %s\n",message?message:"no-description"); fflush(0);
    });
    if (!proxy) return 6;
    [proxy getServerStatusWithCompletionHandler:^(unsigned int value) {
        reply_seen=1; status=value;
        printf("LSD NATIVE STATUS REPLY status=%u\n",value); fflush(0);
    }];
    printf("LSD NATIVE QUERY RESULT reply=%d error=%d status=%u\n",reply_seen,error_seen,status); fflush(0);
    /* This is _LSDatabaseGetSessionStatus, an unsigned bitfield, not OSStatus.
     * Matching 20F66 code sets 0x100 for isSeeded and 0x200 when seeding is
     * incomplete. A successful transport reply must not be required to be 0.
     * The old wrapper alone could return its default 0 without a reply; use
     * it only as a cross-check AFTER the separately witnessed callback.
     */
    typedef unsigned int (*status_fn)(void);
    status_fn get_status=(status_fn)dlsym(handle,"_LSGetStatus");
    if (!get_status || !reply_seen || error_seen) return 7;
    unsigned int wrapper=get_status();
    printf("LSD NATIVE WRAPPER status=%u matches=%d\n",wrapper,wrapper==status); fflush(0);
    printf("LSD NATIVE DATABASE seeded=%u seeding_complete=%u\n",!!(status&0x100),
        !!(status&0x100) && !(status&0x200)); fflush(0);
    int result=wrapper==status?0:9;
    if (!result) {printf("LSD NATIVE TRANSPORT PASS status=%u\n",status);fflush(0);}
    [pool drain];
    return result;
}
