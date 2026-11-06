/* CPU-only IOSurface sharing probe. No display swap or hardware MMIO. */
#include "sweet-foundation-api.h"
typedef unsigned int u32;
typedef struct __IOSurface *IOSurfaceRef;
extern IOSurfaceRef IOSurfaceCreate(const void *), IOSurfaceLookup(u32);
extern u32 IOSurfaceGetID(IOSurfaceRef);
extern size_t IOSurfaceGetWidth(IOSurfaceRef), IOSurfaceGetHeight(IOSurfaceRef);
extern size_t IOSurfaceGetBytesPerRow(IOSurfaceRef), IOSurfaceGetAllocSize(IOSurfaceRef);
extern void *IOSurfaceGetBaseAddress(IOSurfaceRef);
extern int IOSurfaceLock(IOSurfaceRef, u32, u32 *), IOSurfaceUnlock(IOSurfaceRef, u32, u32 *);
extern const void *kIOSurfaceWidth, *kIOSurfaceHeight, *kIOSurfaceBytesPerElement;
extern const void *kIOSurfaceBytesPerRow, *kIOSurfaceAllocSize, *kIOSurfacePixelFormat;
extern void CFRelease(const void *);
extern void *dlopen(const char *, int), *dlsym(void *, const char *);
extern const char *dlerror(void);
extern int dlclose(void *), waitpid(int, int *, int);
extern void sync(void);
extern int posix_spawn(int *, const char *, const void *, const void *, char *const [], char *const []);
extern char **environ;
#define UI_PATH "/sbin/sweet-ui-surface"
#define UI_RESULT "/private/var/tmp/ui-surface-result.txt"

static u32 pattern(size_t x, size_t y, int changed) {
    return changed ? (0xff000000u | (u32)(y * 17 + x * 31)) : (0xff660000u ^ (u32)((y << 8) | x));
}
static int pixels(IOSurfaceRef surface, int expected, int rewrite) {
    if (IOSurfaceGetWidth(surface) != 64 || IOSurfaceGetHeight(surface) != 32) return -1;
    size_t row = IOSurfaceGetBytesPerRow(surface), bytes = IOSurfaceGetAllocSize(surface);
    if (row < 256 || row > 32768 || bytes < row * 32 || bytes > 1048576) return -1;
    u32 seed = 0;
    if (IOSurfaceLock(surface, 0, &seed)) return -1;
    unsigned char *base = IOSurfaceGetBaseAddress(surface);
    if (!base) return -1;
    for (size_t y = 0; y < 32; ++y) {
        u32 *line = (u32 *)(base + row * y);
        for (size_t x = 0; x < 64; ++x) {
            if (expected >= 0 && line[x] != pattern(x, y, expected)) return -1;
            if (rewrite >= 0) line[x] = pattern(x, y, rewrite);
        }
    }
    if (IOSurfaceUnlock(surface, 0, &seed)) return -1;
    return 0;
}
static int child(const char *idtext, const char *parenttext) {
    ipc_role = "ui-child";
    ipc_trace = open("/private/var/tmp/ipc-ui-child.log", 0x601, 0600);
    char *end = 0, path[1024] = {0};
    long identifier = strtol(idtext, &end, 10);
    if (ipc_trace < 0 || !end || *end || identifier <= 0 || (unsigned long)identifier > 0xfffffffful) return ipc_fail("child ID");
    long parent = strtol(parenttext, &end, 10);
    if (!end || *end || parent <= 1 || getppid() != parent || getuid() || geteuid() ||
        proc_pidpath((int)parent, path, sizeof(path)) <= 0 || strcmp(path, UI_PATH)) return ipc_fail("child identity");
    ipc_note("UI CHILD EXEC pid=%d ppid=%d surface=%u", getpid(), getppid(), (u32)identifier);
    IOSurfaceRef surface = IOSurfaceLookup((u32)identifier);
    if (!surface || IOSurfaceGetID(surface) != (u32)identifier || pixels(surface, 0, 1)) return ipc_fail("child lookup/read/write");
    ipc_note("UI CHILD SHARED PIXELS VERIFIED width=64 height=32 pixels=2048");
    CFRelease(surface);
    ipc_note("UI CHILD EXIT status=0");
    if (fsync(ipc_trace) || close(ipc_trace)) return 1;
    return 0;
}
static int exercise(void) {
    void *mobile = dlopen("/System/Library/PrivateFrameworks/IOMobileFramebuffer.framework/IOMobileFramebuffer", 2);
    void *mini = dlopen("/System/Library/PrivateFrameworks/MiniDisplay.framework/MiniDisplay", 2);
    if (!mobile || !mini || !dlsym(mobile, "IOMobileFramebufferGetMainDisplay")) {
        ipc_note("UI DLOPEN ERROR %s", dlerror()); return ipc_fail("framework load");
    }
    ipc_note("UI FRAMEWORKS LOADED IOSurface IOMobileFramebuffer MiniDisplay");
    id keys[] = {(id)kIOSurfaceWidth, (id)kIOSurfaceHeight, (id)kIOSurfaceBytesPerElement,
                 (id)kIOSurfaceBytesPerRow, (id)kIOSurfaceAllocSize, (id)kIOSurfacePixelFormat};
    id values[] = {[NSNumber numberWithInt:64], [NSNumber numberWithInt:32], [NSNumber numberWithInt:4],
                   [NSNumber numberWithInt:256], [NSNumber numberWithInt:8192], [NSNumber numberWithInt:0x42475241]};
    NSDictionary *props = [NSDictionary dictionaryWithObjects:values forKeys:keys count:6];
    IOSurfaceRef surface = IOSurfaceCreate((const void *)props);
    if (!surface || !IOSurfaceGetID(surface) || pixels(surface, -1, 0)) return ipc_fail("surface create/write");
    u32 identifier = IOSurfaceGetID(surface);
    ipc_note("UI SURFACE CREATED id=%u width=64 height=32 row=%lu allocation=%lu", identifier,
             IOSurfaceGetBytesPerRow(surface), IOSurfaceGetAllocSize(surface));
    IOSurfaceRef same = IOSurfaceLookup(identifier);
    if (!same || IOSurfaceGetID(same) != identifier || pixels(same, 0, -1)) return ipc_fail("same-process lookup");
    CFRelease(same);
    ipc_note("UI SAME PROCESS LOOKUP VERIFIED");
    char idtext[32], parenttext[32];
    snprintf(idtext, sizeof(idtext), "%u", identifier);
    snprintf(parenttext, sizeof(parenttext), "%d", getpid());
    char *args[] = {UI_PATH, "--lookup", idtext, parenttext, 0};
    int pid = -1, status = -1, reaped = 0;
    int error = posix_spawn(&pid, UI_PATH, 0, 0, args, environ);
    if (error || pid <= 1) return ipc_fail("child spawn");
    ipc_note("UI CHILD SPAWNED pid=%d", pid);
    for (int attempt = 0; attempt < 120; ++attempt) {
        int got = waitpid(pid, &status, 1);
        if (got == pid) { reaped = 1; break; }
        if (got < 0) return ipc_fail("child wait");
        sleep(1);
    }
    if (!reaped || status) return ipc_fail("child exit/timeout");
    if (pixels(surface, 1, -1)) return ipc_fail("parent shared writeback");
    ipc_note("UI PARENT SHARED WRITEBACK VERIFIED pixels=2048 child_status=0");
    CFRelease(surface);
    if (dlclose(mini) || dlclose(mobile)) return ipc_fail("framework close");
    int fd = open(UI_RESULT, 0x601, 0600);
    const char result[] = "IOSurface CPU sharing PASS: 64x32 BGRA, 2048 pixels, exec child read+write, parent verified\n";
    if (fd < 0 || ipc_write_all(fd, result, sizeof(result) - 1) || fsync(fd) || close(fd)) return ipc_fail("result file");
    return 0;
}
int main(int argc, char **argv) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    if (!pool) return 1;
    if (argc == 4 && !strcmp(argv[1], "--lookup")) {
        int status = child(argv[2], argv[3]); [pool drain]; return status;
    }
    if (argc != 1 || ipc_identity("ui-parent")) return 1;
    ipc_note("UI PROBE ENTERED");
    @try { if (exercise()) return 1; }
    @catch (id exception) { (void)exception; return ipc_fail("Objective-C exception"); }
    [pool drain];
    ipc_note("UI SURFACE CPU SHARING PASS");
    /* Leave enough time for two sampled heartbeats and saved RAM evidence. */
    for (int tick = 1; tick <= 300; ++tick) {
        char line[64];
        int length = snprintf(line, sizeof(line), "UI PROBE HEARTBEAT=%d\n", tick);
        if (length <= 0 || (size_t)length >= sizeof(line) ||
            ipc_write_all(ipc_trace, line, (size_t)length) || fsync(ipc_trace)) return 1;
        /* Publish the stop marker only after HFS catalog/data are flushed. */
        sync();
        printf("SWEET ipc ui-parent: %s", line); fflush(0); sleep(1);
    }
    return 0;
}
