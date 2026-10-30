/* Two distinct NSUserDefaults programs; only the writer sets the test values. */
#include "sweet-foundation-api.h"
typedef long NSInteger;
@interface NSUserDefaults : NSObject
- (id)initWithSuiteName:(NSString *)name;
- (void)setObject:(id)value forKey:(NSString *)key;
- (void)setInteger:(NSInteger)value forKey:(NSString *)key;
- (void)setBool:(BOOL)value forKey:(NSString *)key;
- (NSString *)stringForKey:(NSString *)key;
- (NSInteger)integerForKey:(NSString *)key;
- (BOOL)boolForKey:(NSString *)key;
- (BOOL)synchronize;
@end
extern int chroot(const char *), chdir(const char *);
extern void *dlopen(const char *, int), *dlsym(void *, const char *);
extern long lseek(int, long, int);
extern void sync(void);
static int bad(const char *step) {
    ipc_note("PREFERENCES ERROR step=%s", step); sync(); return ipc_fail(step);
}
static int exercise(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    void *mobile = dlopen("/System/Library/Frameworks/MobileCoreServices.framework/MobileCoreServices", 1);
    if (!mobile || !dlsym(mobile, "FSEventStreamCreate")) return bad("prepare dynamic file-watcher library");
    if (![NSUserDefaults class]) return bad("prepare NSUserDefaults class");
    /* Initialize the runtime using a DIFFERENT, unset domain. Never access
     * org.sweet.qemu.preferences or any of its keys before isolation. */
    NSUserDefaults *warm = [[NSUserDefaults alloc] initWithSuiteName:@"org.sweet.qemu.runtime-warmup"];
    if (!warm || [warm stringForKey:@"unused"] || ![warm synchronize])
        return bad("prepare preferences runtime on independent empty domain");
    ipc_note("PREFERENCES RUNTIME WARMUP domain=org.sweet.qemu.runtime-warmup unused=nil no_writes=1");
    ipc_note("PREFERENCES LIBRARIES PREPARED MobileCoreServices FSEventStreamCreate=present");
    /* Libraries are already mapped. Both absolute preferences paths are absent
     * in this empty root; no directory descriptor or cwd outside it is retained.
     * The only outside filesystem handles are console/log/PID/release files.
     * Native bootstrap Mach ports continue to address the real daemon. */
    if (chroot("/private/var/tmp/preferences-empty-root") || chdir("/"))
        return bad("enter empty filesystem root");
    const char *paths[] = {
        "/private/var/root/Library/Preferences/org.sweet.qemu.preferences.plist",
        "/var/root/Library/Preferences/org.sweet.qemu.preferences.plist",
        "/Library/Preferences/org.sweet.qemu.preferences.plist"
    };
    for (int i = 0; i < 3; ++i) {
        int fd = open(paths[i], 0x601, 0600);
        if (fd >= 0) { close(fd); return bad("direct preference create unexpectedly possible"); }
        if (*__error() != 2) return bad("unexpected direct-file error");
    }
    ipc_note("PREFERENCES ISOLATED chroot=empty cwd=/ direct_create=ENOENT paths=3");
    NSUserDefaults *prefs = [[NSUserDefaults alloc] initWithSuiteName:@"org.sweet.qemu.preferences"];
    if (!pool || !prefs) return bad("create NSUserDefaults");
#if defined(SWEET_PREFS_WRITER)
    [prefs setObject:@"DUCHAMP" forKey:@"device"];
    [prefs setInteger:6897 forKey:@"soc"];
    [prefs setBool:1 forKey:@"enabled"];
    ipc_note("PREFERENCES SET string=DUCHAMP integer=6897 bool=1");
#endif
    if (![prefs synchronize]) return bad("NSUserDefaults synchronize");
    NSString *device = [prefs stringForKey:@"device"];
    if (!device || strcmp([device UTF8String], "DUCHAMP") ||
        [prefs integerForKey:@"soc"] != 6897 || ![prefs boolForKey:@"enabled"])
        return bad("NSUserDefaults exact readback");
    ipc_note("PREFERENCES READ string=DUCHAMP integer=6897 bool=1");
    for (int i = 0; i < 3; ++i) {
        int fd = open(paths[i], 0);
        if (fd >= 0) { close(fd); return bad("direct preference read unexpectedly possible"); }
        if (*__error() != 2) return bad("unexpected direct-read error");
    }
    ipc_note("PREFERENCES ISOLATION VERIFIED direct_read=ENOENT paths=3");
    [pool drain];
    return 0;
}
int main(void) {
#if defined(SWEET_PREFS_WRITER)
    const char *role = "prefs-writer";
#else
    char role[48]; snprintf(role, sizeof(role), "prefs-reader-%d", getpid());
#endif
    if (ipc_identity(role)) return bad("identity");
#if defined(SWEET_PREFS_WRITER)
    int pid_file = open("/private/var/tmp/sweet-service.pid", 0x601, 0600);
    int release = open(IPC_RELEASE, 0x602, 0600);
    if (pid_file < 0 || release < 0) return bad("open outside regular readiness files");
#endif
    ipc_note("PREFERENCES ENTERED");
    @try { if (exercise()) return 1; }
    @catch (id exception) { (void)exception; return bad("Objective-C exception"); }
#if defined(SWEET_PREFS_WRITER)
    char identity[32]; int length = snprintf(identity, sizeof(identity), "%d\n", getpid());
    if (length < 1 || ipc_write_all(pid_file, identity, (size_t)length) ||
        fsync(pid_file) || close(pid_file)) return bad("writer readiness");
    int released = 0;
    for (int i = 0; i < 600; ++i) {
        char token[6] = {0};
        if (lseek(release, 0, 0) < 0) return bad("release seek");
        ssize_t n = read(release, token, sizeof(token));
        if (n == 5 && !memcmp(token, "exit\n", 5)) { released = 1; break; }
        if (n < 0 || n > 0) return bad("release contents");
        sleep(1);
    }
    if (!released) return bad("writer release timeout");
    if (close(release)) return bad("close release");
#endif
    ipc_note("PREFERENCES NORMAL EXIT status=0");
    sync();
    return close(ipc_trace) ? 1 : 0;
}
