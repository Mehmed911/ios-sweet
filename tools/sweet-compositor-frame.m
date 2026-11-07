/* Synthetic QEMU-only frame submitted through the SweetFramebuffer ABI. */
#include "sweet-foundation-api.h"

typedef unsigned int u32;
typedef unsigned long long u64;
typedef struct __IOSurface *IOSurfaceRef;
extern IOSurfaceRef IOSurfaceCreate(const void *);
extern u32 IOSurfaceGetID(IOSurfaceRef);
extern size_t IOSurfaceGetBytesPerRow(IOSurfaceRef), IOSurfaceGetAllocSize(IOSurfaceRef);
extern void *IOSurfaceGetBaseAddress(IOSurfaceRef);
extern int IOSurfaceLock(IOSurfaceRef, u32, u32 *), IOSurfaceUnlock(IOSurfaceRef, u32, u32 *);
extern const void *kIOSurfaceWidth, *kIOSurfaceHeight, *kIOSurfaceBytesPerElement;
extern const void *kIOSurfaceBytesPerRow, *kIOSurfaceAllocSize, *kIOSurfacePixelFormat;
extern u32 mach_task_self_;
extern void *IOServiceMatching(const char *);
extern u32 IOServiceGetMatchingService(u32, void *);
extern int IOServiceOpen(u32, u32, u32, u32 *), IOObjectRelease(u32);
extern int IOConnectCallScalarMethod(u32, u32, const u64 *, u32, u64 *, u32 *);
extern int IOConnectCallStructMethod(u32, u32, const void *, size_t, void *, size_t *);
extern void sync(void);

enum { WIDTH = 64, HEIGHT = 32, X = 521, Y = 1801 };
struct swap_record {
    unsigned char prefix[0x50];
    u32 swap_id, surfaces[4];
    int source[4][4];
    unsigned char gap[0x20];
    int destination[4][4];
    u32 mask;
    unsigned char suffix[0x364];
};
_Static_assert(sizeof(struct swap_record) == 0x46c, "SwapEnd size");
_Static_assert(__builtin_offsetof(struct swap_record, destination) == 0xc4, "destination");
_Static_assert(__builtin_offsetof(struct swap_record, mask) == 0x104, "layer mask");

int main(void) {
    if (ipc_identity("frame-probe")) return 1;
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    if (!pool) return ipc_fail("pool");
    void *match = IOServiceMatching("AppleCLCD");
    u32 service = match ? IOServiceGetMatchingService(0, match) : 0;
    u32 connection = 0;
    int status = service ? IOServiceOpen(service, mach_task_self_, 0, &connection) : -1;
    if (service) IOObjectRelease(service);
    if (status || !connection) {
        ipc_note("IOServiceOpen status=0x%x", status);
        return ipc_fail("AppleCLCD open");
    }

    id keys[] = {(id)kIOSurfaceWidth, (id)kIOSurfaceHeight, (id)kIOSurfaceBytesPerElement,
                 (id)kIOSurfaceBytesPerRow, (id)kIOSurfaceAllocSize, (id)kIOSurfacePixelFormat};
    id values[] = {[NSNumber numberWithInt:WIDTH], [NSNumber numberWithInt:HEIGHT], [NSNumber numberWithInt:4],
                   [NSNumber numberWithInt:WIDTH * 4], [NSNumber numberWithInt:WIDTH * HEIGHT * 4],
                   [NSNumber numberWithInt:0x42475241]};
    NSDictionary *props = [NSDictionary dictionaryWithObjects:values forKeys:keys count:6];
    IOSurfaceRef surface = IOSurfaceCreate((const void *)props);
    u32 id = surface ? IOSurfaceGetID(surface) : 0, seed = 0;
    if (!id || IOSurfaceGetBytesPerRow(surface) != WIDTH * 4 ||
        IOSurfaceGetAllocSize(surface) < WIDTH * HEIGHT * 4 || IOSurfaceLock(surface, 0, &seed))
        return ipc_fail("create and lock IOSurface");
    u32 *pixels = IOSurfaceGetBaseAddress(surface);
    if (!pixels) return ipc_fail("surface address");
    for (u32 y = 0; y < HEIGHT; ++y) {
        for (u32 x = 0; x < WIDTH; ++x) {
            pixels[y * WIDTH + x] = 0xff000000u | ((x * 4) << 16) | ((y * 8) << 8) | ((x * 13 + y * 7) & 255);
        }
    }
    if (IOSurfaceUnlock(surface, 0, &seed)) return ipc_fail("unlock IOSurface");

    u64 on = 1, swap_id = 0;
    u32 count = 1;
    if (IOConnectCallScalarMethod(connection, 12, &on, 1, 0, 0) ||
        IOConnectCallScalarMethod(connection, 4, 0, 0, &swap_id, &count) || count != 1 || !swap_id)
        return ipc_fail("power on or SwapBegin");
    struct swap_record rec = {
        .swap_id = (u32)swap_id, .surfaces = {id}, .source = {{0, 0, WIDTH, HEIGHT}},
        .destination = {{X, Y, WIDTH, HEIGHT}}, .mask = 1,
    };
    status = IOConnectCallStructMethod(connection, 5, &rec, sizeof(rec), 0, 0);
    if (status) {
        ipc_note("SwapEnd status=0x%x", status);
        return ipc_fail("SwapEnd");
    }
    ipc_note("FRAME SUBMITTED swap=%u surface=%u rectangle=%d,%d,%d,%d", rec.swap_id, id, X, Y, WIDTH, HEIGHT);
    sync();
    [pool drain];
    /* Keep the surface reference and user client alive until the host samples scanout. */
    for (;;) sleep(30);
}
