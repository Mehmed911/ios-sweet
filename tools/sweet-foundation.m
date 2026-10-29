#include "sweet-foundation-api.h"

static int exercise(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    if (!pool) return ipc_fail("Foundation pool");
    ipc_note("FOUNDATION POOL ready");
    NSString *text = [NSString stringWithUTF8String:"duchamp"];
    NSString *upper = [text uppercaseString];
    const char arabic[] = "\xd9\x85\xd8\xb1\xd8\xad\xd8\xa8\xd8\xa7";
    NSString *unicode = [NSString stringWithUTF8String:arabic];
    if (!upper || [upper length] != 7 || strcmp([upper UTF8String], "DUCHAMP") ||
        !unicode || [unicode length] != 5 || strcmp([unicode UTF8String], arabic))
        return ipc_fail("Foundation strings");
    ipc_note("FOUNDATION STRING uppercase=DUCHAMP length=7 unicode_units=5");
    NSString *device = [NSString stringWithUTF8String:"device"], *soc = [NSString stringWithUTF8String:"soc"];
    id keys[] = {device, soc}, values[] = {upper, [NSNumber numberWithInt:6897]};
    NSDictionary *dict = [NSDictionary dictionaryWithObjects:values forKeys:keys count:2];
    if (!dict || [dict count] != 2 || [(NSNumber *)[dict objectForKey:soc] intValue] != 6897)
        return ipc_fail("Foundation dictionary");
    ipc_note("FOUNDATION DICTIONARY count=2 soc=6897");
    NSError *error = 0;
    NSData *json = [NSJSONSerialization dataWithJSONObject:dict options:0 error:&error];
    if (!json || error || ![json length]) return ipc_fail("Foundation JSON encode");
    NSDictionary *parsed = [NSJSONSerialization JSONObjectWithData:json options:0 error:&error];
    if (!parsed || error || [parsed count] != 2 ||
        strcmp([(NSString *)[parsed objectForKey:device] UTF8String], "DUCHAMP") ||
        [(NSNumber *)[parsed objectForKey:soc] intValue] != 6897) return ipc_fail("Foundation JSON decode");
    ipc_note("FOUNDATION JSON roundtrip bytes=%lu", [json length]);
    NSString *path = [NSString stringWithUTF8String:"/private/var/tmp/foundation-result.json"];
    if (![json writeToFile:path atomically:1]) return ipc_fail("Foundation file write");
    NSData *loaded = [NSData dataWithContentsOfFile:path];
    if (!loaded || ![json isEqualToData:loaded]) return ipc_fail("Foundation file readback");
    ipc_note("FOUNDATION FILE roundtrip bytes=%lu", [loaded length]);
    int caught = 0;
    @try {
        @throw [NSException exceptionWithName:[NSString stringWithUTF8String:"SweetProbe"]
                                      reason:[NSString stringWithUTF8String:"diagnostic"] userInfo:0];
    } @catch (NSException *exception) {
        if (!strcmp([[exception name] UTF8String], "SweetProbe")) caught = 1;
    }
    if (!caught) return ipc_fail("Foundation exception");
    ipc_note("FOUNDATION EXCEPTION caught=SweetProbe");
    [pool drain];
    ipc_note("FOUNDATION POOL drained");
    return 0;
}
int main(void) {
    if (ipc_identity("foundation")) return ipc_fail("identity");
    ipc_note("FOUNDATION ENTERED");
    @try {
        if (exercise()) return 1;
    } @catch (id exception) {
        (void)exception; return ipc_fail("unexpected Objective-C exception");
    }
    if (ipc_publish_pid("/private/var/tmp/sweet-service.pid")) return ipc_fail("readiness");
    ipc_note("FOUNDATION READY pid=%d", getpid());
    int released = 0;
    for (int i = 0; i < 240; ++i) {
        int fd = open(IPC_RELEASE, 0);
        if (fd >= 0) {
            char token[6] = {0}; ssize_t n = read(fd, token, sizeof(token));
            if (close(fd) || n != 5 || memcmp(token, "exit\n", 5)) return ipc_fail("exit release");
            released = 1; break;
        }
        if (*__error() != 2) return ipc_fail("release open");
        sleep(1);
    }
    if (!released) return ipc_fail("release timeout");
    ipc_note("FOUNDATION NORMAL EXIT status=0");
    if (fsync(ipc_trace) || close(ipc_trace)) return 1;
    return 0;
}
