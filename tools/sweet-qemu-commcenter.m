/* QEMU-only 20F66 CommCenter read-only fixture and native client. */
#include "sweet-foundation-api.h"

#define nil ((id)0)
#define LAB_SERVICE @"com.apple.commcenter.coretelephony.xpc"

typedef struct dispatch_queue_s *dispatch_queue_t;
extern dispatch_queue_t dispatch_queue_create(const char *, void *);
extern void dispatch_async(dispatch_queue_t, void (^)(void));
extern void dispatch_main(void) __attribute__((noreturn));
extern const char *getenv(const char *), *getprogname(void);
extern unsigned int alarm(unsigned int);

@interface NSObject (SweetLifetime)
- (oneway void)release;
@end

@interface NSString (SweetComparison)
- (BOOL)isEqualToString:(NSString *)string;
@end

@interface NSArray : NSObject
+ (id)arrayWithObject:(id)object;
+ (id)arrayWithObjects:(const id *)objects count:(NSUInteger)count;
- (id)firstObject;
- (NSUInteger)count;
@end

@interface NSSet : NSObject
+ (id)setWithArray:(NSArray *)array;
@end

@interface NSUUID : NSObject
- (id)initWithUUIDString:(NSString *)text;
@end

@interface NSXPCInterface : NSObject
+ (id)interfaceWithProtocol:(Protocol *)protocol;
- (void)setClasses:(NSSet *)classes forSelector:(SEL)selector argumentIndex:(NSUInteger)index ofReply:(BOOL)reply;
@end

@interface NSXPCConnection : NSObject
- (int)processIdentifier;
- (void)setExportedInterface:(NSXPCInterface *)interface;
- (void)setExportedObject:(id)object;
- (void)resume;
@end

@interface NSXPCListener : NSObject
- (id)initWithMachServiceName:(NSString *)name;
- (void)setDelegate:(id)delegate;
- (void)resume;
@end

@interface CTXPCServiceSubscriptionContext : NSObject
- (id)initWithUUID:(NSUUID *)uuid andSlot:(long long)slot;
- (long long)slotID;
- (void)setIsSimPresent:(BOOL)present;
- (void)setIsSimGood:(BOOL)good;
@end

@interface CTXPCServiceSubscriptionInfo : NSObject
- (void)setSubscriptions:(NSArray *)subscriptions;
- (void)setSubscriptionsInUse:(NSArray *)subscriptions;
- (void)setSubscriptionsValid:(NSArray *)subscriptions;
@end

@interface CTDataConnectionAvailabilityStatus : NSObject
- (void)setAvailable:(BOOL)available;
@end

@interface CTXPCContextInfo : NSObject
- (id)initWithUUID:(NSUUID *)uuid andAccountID:(NSString *)account andSlot:(long long)slot;
- (CTXPCServiceSubscriptionContext *)context;
@end

@interface CTXPCContexts : NSObject
- (void)setSubscriptions:(NSArray *)subscriptions;
- (void)setDataPreferred:(NSUUID *)uuid;
- (void)setVoicePreferred:(NSUUID *)uuid;
- (NSArray *)subscriptions;
@end

@interface CoreTelephonyClient : NSObject
- (id)initWithQueue:(dispatch_queue_t)queue;
- (CTXPCContexts *)getActiveContexts:(NSError **)error;
- (NSString *)getSIMStatus:(CTXPCServiceSubscriptionContext *)context error:(NSError **)error;
- (NSString *)copyRegistrationStatus:(CTXPCServiceSubscriptionContext *)context error:(NSError **)error;
@end

extern NSString *const kCTSIMSupportSIMStatusReady;
extern NSString *const kCTRegistrationStatusNotRegistered;

static int probe(void) {
    @autoreleasepool {
        const char *log = strcmp(getprogname(), "Setup") == 0 ? "/private/var/tmp/duchamp-cellular-setup.log" : "/private/var/tmp/duchamp-cellular-probe.log";
        int fd = open(log, 0x0209, 0666);
        char line[440];
        NSError *contextError = nil, *simError = nil, *registrationError = nil;
        dispatch_queue_t queue = dispatch_queue_create("org.sweet.cellular.reply", 0);
        CoreTelephonyClient *client = [[CoreTelephonyClient alloc] initWithQueue:queue];
        CTXPCContexts *contexts = [client getActiveContexts:&contextError];
        CTXPCContextInfo *info = [[contexts subscriptions] firstObject];
        CTXPCServiceSubscriptionContext *context = [info context];
        NSString *sim = context ? [client getSIMStatus:context error:&simError] : nil;
        NSString *registration = context ? [client copyRegistrationStatus:context error:&registrationError] : nil;
        const char *simText = [sim UTF8String], *registrationText = [registration UTF8String];
        BOOL pass = [context slotID] == 1 &&
            !contextError && !simError && !registrationError &&
            [sim isEqualToString:kCTSIMSupportSIMStatusReady] &&
            [registration isEqualToString:kCTRegistrationStatusNotRegistered];
        int count = snprintf(line, sizeof(line),
            "CELLULAR_PROBE %s process=%s pid=%d slot=%lld sim=%s registration=%s errors=%d,%d,%d\n",
            pass ? "PASS" : "FAIL", getprogname(), getpid(), [context slotID],
            simText ? simText : "-", registrationText ? registrationText : "-",
            !!contextError, !!simError, !!registrationError);
        if (count > 0 && (size_t)count < sizeof(line)) {
            if (fd >= 0) {
                ipc_write_all(fd, line, (size_t)count);
                fsync(fd);
            }
            printf("%s", line);
            fflush(0);
        }
        if (fd >= 0) close(fd);
        [client release];
        [registration release];
        return pass ? 0 : 1;
    }
}

#ifdef SWEET_CELLULAR_SETUP_PROBE
/* Only loaded explicitly by the QEMU debugger into the real Setup process. */
__attribute__((constructor))
static void setup_probe(void) {
    if (strcmp(getprogname(), "Setup") != 0) return;
    dispatch_async(dispatch_queue_create("org.sweet.cellular.setup", 0), ^{ (void)probe(); });
}
#else
@protocol SweetCommCenterReadOnly
- (void)ping:(void (^)(NSError *))reply;
- (void)getActiveContexts:(void (^)(CTXPCContexts *, NSError *))reply;
- (void)getSubscriptionInfo:(void (^)(CTXPCServiceSubscriptionInfo *, NSError *))reply;
- (void)registerForNotifications:(NSArray *)names completion:(void (^)(NSError *))reply;
- (void)getConnectionAvailability:(CTXPCServiceSubscriptionContext *)context
                   connectionType:(int)type completion:(void (^)(CTDataConnectionAvailabilityStatus *, NSError *))reply;
- (void)usingBootstrapDataServiceWithCompletion:(void (^)(BOOL))reply;
- (void)isAnySimReadyWithCompletion:(void (^)(BOOL, NSError *))reply;
- (void)getSIMStatus:(CTXPCServiceSubscriptionContext *)context completion:(void (^)(NSString *, NSError *))reply;
- (void)copyRegistrationStatus:(CTXPCServiceSubscriptionContext *)context completion:(void (^)(NSString *, NSError *))reply;
@end

/* Allocate the exported class at runtime. The guest's Foundation retain path
 * faults on the static class's ISA with this stripped 20F66 cache. */
typedef struct objc_ivar *Ivar;
typedef void (*Implementation)(void);
extern Class objc_allocateClassPair(Class, const char *, size_t);
extern void objc_registerClassPair(Class);
extern BOOL class_addIvar(Class, const char *, size_t, unsigned char, const char *);
extern BOOL class_addMethod(Class, SEL, Implementation, const char *);
extern Ivar class_getInstanceVariable(Class, const char *);
extern long ivar_getOffset(Ivar);
extern id class_createInstance(Class, size_t);
extern SEL sel_registerName(const char *);

static Class handler_class;
static long peer_offset;

static int *peer_slot(id object) {
    return (int *)((char *)object + peer_offset);
}

static void service_trace(const char *selector, int peer, const char *value) {
    printf("CELLULAR_SERVICE peer=%d selector=%s result=%s\n", peer, selector, value);
    fflush(0);
    fsync(1);
}

static BOOL accept_connection(id self, SEL command, NSXPCListener *listener, NSXPCConnection *connection) {
    (void)self; (void)command; (void)listener;
    id handler = class_createInstance(handler_class, 0);
    if (!handler) return 0;
    *peer_slot(handler) = [connection processIdentifier];
    NSXPCInterface *interface = [NSXPCInterface interfaceWithProtocol:@protocol(SweetCommCenterReadOnly)];
    NSSet *contexts = [NSSet setWithArray:[NSArray arrayWithObject:[CTXPCServiceSubscriptionContext class]]];
    [interface setClasses:contexts forSelector:@selector(getSIMStatus:completion:) argumentIndex:0 ofReply:0];
    [interface setClasses:contexts forSelector:@selector(copyRegistrationStatus:completion:) argumentIndex:0 ofReply:0];
    [interface setClasses:contexts forSelector:@selector(getConnectionAvailability:connectionType:completion:)
             argumentIndex:0 ofReply:0];
    [connection setExportedInterface:interface];
    [connection setExportedObject:handler];
    [handler release];
    service_trace("accept", [connection processIdentifier], "mach");
    [connection resume];
    return 1;
}

static void ping(id self, SEL command, void (^reply)(NSError *)) {
    (void)command;
    int peer = *peer_slot(self);
    service_trace("ping", peer, "ready");
    reply(nil);
}

static void register_notifications(id self, SEL command, NSArray *names, void (^reply)(NSError *)) {
    (void)command;
    int peer = *peer_slot(self);
    (void)names;
    service_trace("registerForNotifications", peer, "fixture-no-events");
    reply(nil);
}

static void get_contexts(id self, SEL command, void (^reply)(CTXPCContexts *, NSError *)) {
    (void)command;
    int peer = *peer_slot(self);
    NSUUID *uuid = [[NSUUID alloc] initWithUUIDString:@"44554348-414D-4000-8000-000000000001"];
    CTXPCContextInfo *info = [[CTXPCContextInfo alloc] initWithUUID:uuid andAccountID:@"duchamp-qemu-lab" andSlot:1];
    CTXPCContexts *contexts = [[CTXPCContexts alloc] init];
    [contexts setSubscriptions:[NSArray arrayWithObject:info]];
    [contexts setDataPreferred:uuid];
    [contexts setVoicePreferred:uuid];
    service_trace("getActiveContexts", peer, "synthetic-slot-1");
    reply(contexts, nil);
    [contexts release];
    [info release];
    [uuid release];
}

static void get_subscription_info(id self, SEL command, void (^reply)(CTXPCServiceSubscriptionInfo *, NSError *)) {
    (void)command;
    NSUUID *uuid = [[NSUUID alloc] initWithUUIDString:@"44554348-414D-4000-8000-000000000001"];
    CTXPCServiceSubscriptionContext *context = [[CTXPCServiceSubscriptionContext alloc] initWithUUID:uuid andSlot:1];
    [context setIsSimPresent:1];
    [context setIsSimGood:1];
    NSArray *subscriptions = [NSArray arrayWithObject:context];
    CTXPCServiceSubscriptionInfo *info = [[CTXPCServiceSubscriptionInfo alloc] init];
    [info setSubscriptions:subscriptions];
    [info setSubscriptionsInUse:subscriptions];
    [info setSubscriptionsValid:subscriptions];
    service_trace("getSubscriptionInfo", *peer_slot(self), "synthetic-slot-1-present-good");
    reply(info, nil);
    [info release];
    [context release];
    [uuid release];
}

static void get_connection_availability(id self, SEL command, CTXPCServiceSubscriptionContext *context,
                                        int type, void (^reply)(CTDataConnectionAvailabilityStatus *, NSError *)) {
    (void)command; (void)context; (void)type;
    CTDataConnectionAvailabilityStatus *status = [[CTDataConnectionAvailabilityStatus alloc] init];
    [status setAvailable:0];
    service_trace("getConnectionAvailability", *peer_slot(self), "synthetic-unavailable");
    reply(status, nil);
    [status release];
}

static void using_bootstrap_data(id self, SEL command, void (^reply)(BOOL)) {
    (void)command;
    service_trace("usingBootstrapDataService", *peer_slot(self), "synthetic-no");
    reply(0);
}

static void sim_ready(id self, SEL command, void (^reply)(BOOL, NSError *)) {
    (void)command;
    int peer = *peer_slot(self);
    service_trace("isAnySimReady", peer, "synthetic-yes");
    reply(1, nil);
}

static void get_sim(id self, SEL command, CTXPCServiceSubscriptionContext *context, void (^reply)(NSString *, NSError *)) {
    (void)command;
    int peer = *peer_slot(self);
    if ([context slotID] != 1) {
        service_trace("getSIMStatus", peer, "invalid-slot");
        reply(nil, nil);
        return;
    }
    service_trace("getSIMStatus", peer, [kCTSIMSupportSIMStatusReady UTF8String]);
    reply(kCTSIMSupportSIMStatusReady, nil);
}

static void get_registration(id self, SEL command, CTXPCServiceSubscriptionContext *context, void (^reply)(NSString *, NSError *)) {
    (void)command;
    int peer = *peer_slot(self);
    if ([context slotID] != 1) {
        service_trace("copyRegistrationStatus", peer, "invalid-slot");
        reply(nil, nil);
        return;
    }
    service_trace("copyRegistrationStatus", peer, [kCTRegistrationStatusNotRegistered UTF8String]);
    reply(kCTRegistrationStatusNotRegistered, nil);
}
static BOOL add_method(const char *name, Implementation function, const char *types) {
    return class_addMethod(handler_class, sel_registerName(name), function, types);
}

static BOOL make_handler_class(void) {
    handler_class = objc_allocateClassPair([NSObject class], "SweetQemuCellularHandler", 0);
    if (!handler_class || !class_addIvar(handler_class, "_peer", sizeof(int), 2, "i")) return 0;
    if (!add_method("listener:shouldAcceptNewConnection:", (Implementation)accept_connection, "B@:@@") ||
        !add_method("ping:", (Implementation)ping, "v@:@?") ||
        !add_method("getActiveContexts:", (Implementation)get_contexts, "v@:@?") ||
        !add_method("getSubscriptionInfo:", (Implementation)get_subscription_info, "v@:@?") ||
        !add_method("registerForNotifications:completion:", (Implementation)register_notifications, "v@:@@?") ||
        !add_method("getConnectionAvailability:connectionType:completion:", (Implementation)get_connection_availability, "v@:@i@?") ||
        !add_method("usingBootstrapDataServiceWithCompletion:", (Implementation)using_bootstrap_data, "v@:@?") ||
        !add_method("isAnySimReadyWithCompletion:", (Implementation)sim_ready, "v@:@?") ||
        !add_method("getSIMStatus:completion:", (Implementation)get_sim, "v@:@@?") ||
        !add_method("copyRegistrationStatus:completion:", (Implementation)get_registration, "v@:@@?")) return 0;
    objc_registerClassPair(handler_class);
    Ivar peer = class_getInstanceVariable(handler_class, "_peer");
    if (!peer) return 0;
    peer_offset = ivar_getOffset(peer);
    return peer_offset >= (long)sizeof(void *);
}

int main(int argc, char **argv) {
    const char *guard = getenv("SWEET_QEMU_CELLULAR_FIXTURE");
    if (!guard || strcmp(guard, "1") != 0) return 64;
    if (argc == 2 && strcmp(argv[1], "--probe") == 0) {
        alarm(90);
        return probe();
    }
    if (argc != 1) return 64;
    @autoreleasepool {
        NSXPCListener *listener = [[NSXPCListener alloc] initWithMachServiceName:LAB_SERVICE];
        if (!listener || !make_handler_class()) return 70;
        id delegate = class_createInstance(handler_class, 0);
        if (!delegate) return 70;
        [listener setDelegate:delegate];
        [listener resume];
        service_trace("listen", 0, "qemu-only");
        dispatch_main();
    }
}
#endif
