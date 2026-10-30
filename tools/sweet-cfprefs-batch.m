/* Live Foundation clients, native notifyd wakeups and daemon-restart recovery. */
#include "sweet-foundation-api.h"
#include "sweet-notify.h"
#include "sweet-cfprefs-batch.h"
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
extern void sync(void);
static int pb_bad(const char *step) {
    ipc_note("PREFERENCES BATCH ERROR %s", step); sync(); return ipc_fail(step);
}
static int generation(int step) { return step == 1 ? 1 : (step == 4 ? 3 : 2); }
static const char *device(int gen) {
    return gen == 1 ? "DUCHAMP" : (gen == 2 ? "DUCHAMP-LIVE" : "DUCHAMP-RECOVERED");
}
static int soc(int gen) { return gen == 2 ? 8300 : 6897; }
static int direct_blocked(int write_test) {
    const char *paths[] = {
        "/private/var/root/Library/Preferences/" PB_SUITE ".plist",
        "/var/root/Library/Preferences/" PB_SUITE ".plist",
        "/Library/Preferences/" PB_SUITE ".plist"
    };
    for (int i = 0; i < 3; ++i) {
        int fd = open(paths[i], write_test ? 0x601 : 0, 0600);
        if (fd >= 0) { close(fd); return -1; }
        if (*__error() != 2) return -1;
    }
    return 0;
}
static NSUserDefaults *prepare(void) {
    void *mobile = dlopen("/System/Library/Frameworks/MobileCoreServices.framework/MobileCoreServices", 1);
    if (!mobile || !dlsym(mobile, "FSEventStreamCreate")) return 0;
    NSUserDefaults *warm = [[NSUserDefaults alloc] initWithSuiteName:@"org.sweet.qemu.runtime-warmup"];
    if (!warm || [warm stringForKey:@"unused"] || ![warm synchronize]) return 0;
    ipc_note("BATCH WARMUP independent_domain=1 no_fixture_access=1");
    if (chroot("/private/var/tmp/preferences-empty-root") || chdir("/") || direct_blocked(1)) return 0;
    ipc_note("BATCH ISOLATED chroot=empty cwd=/ direct_create=ENOENT paths=3");
    return [[NSUserDefaults alloc] initWithSuiteName:@PB_SUITE];
}
static int read_values(NSUserDefaults *prefs, int step) {
    int gen = generation(step);
    for (int attempt = 0; attempt < 120; ++attempt) {
        BOOL refreshed = [prefs synchronize];
        NSString *text = [prefs stringForKey:@"device"];
        long number = [prefs integerForKey:@"soc"], actual_gen = [prefs integerForKey:@"generation"];
        BOOL enabled = [prefs boolForKey:@"enabled"];
        if (refreshed && text && !strcmp([text UTF8String], device(gen)) &&
            number == soc(gen) && actual_gen == gen && enabled == (gen != 2)) {
            if (direct_blocked(0)) return pb_bad("direct preference access became possible");
            ipc_note("BATCH VALUES step=%d generation=%d device=%s soc=%ld enabled=%d refresh=synchronize direct_read=ENOENT",
                     step, gen, [text UTF8String], number, enabled);
            return 0;
        }
        if (!attempt) ipc_note("BATCH REFRESH WAIT step=%d sync=%d generation=%ld", step, refreshed, actual_gen);
        sleep(1);
    }
    return pb_bad("bounded preference refresh/readback timeout");
}
static int cancel_token(int token) {
    int changed = 0;
    if (notify_cancel(token) || notify_is_valid_token(token) || notify_check(token, &changed) != 2)
        return pb_bad("notification token cleanup");
    ipc_note("BATCH TOKEN CANCELLED valid=0 check_status=2");
    return 0;
}
static int exercise(int id, int pidfd, int control, int ack1, int ack2, int completed) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    NSUserDefaults *prefs = prepare();
    if (!pool || !prefs) return pb_bad("warmup/isolation/preferences init");
    int token = -1, changed = 0; unsigned long long initial = ~0ULL;
    if (notify_register_plain(PB_NAME, &token) || !notify_is_valid_token(token) ||
        notify_get_state(token, &initial)) return pb_bad("notify registration/state");
    if ((!id && initial != 0) || (id == 2 && initial != 0) || (id == 1 && initial != 0 && initial != 2))
        return pb_bad("unexpected initial notification state");
    if (notify_check(token, &changed) || changed != 1 || notify_check(token, &changed) || changed != 0)
        return pb_bad("initial notification check/quiet");
    ipc_note("BATCH READY id=%d pid=%d initial_step=%llu", id, getpid(), initial);
    if (pb_put_fd(pidfd, getpid()) || close(pidfd)) return pb_bad("readiness PID file");
    int last = (int)initial;
    for (int turns = 0; turns < 1200; ++turns) {
        int requested = pb_get_fd(control);
        if (requested == -100) return pb_bad("control read");
        if (id && requested == -1) {
            if (id != 1 || last != 2) return pb_bad("unexpected reader stop");
            ipc_note("BATCH ORDERLY STOP id=1 after_step=2");
            if (cancel_token(token)) return 1;
            [pool drain]; return 0;
        }
        int step = 0;
        if (!id) {
            if (requested == last + 1 && requested <= 4) step = requested;
            else if (requested < 0 || requested > last + 1) return pb_bad("writer command order");
        } else {
            if (notify_check(token, &changed)) return pb_bad("notify polling");
            if (changed) {
                unsigned long long state = 0;
                if (notify_get_state(token, &state) || state != (unsigned long long)(last + 1) || state > 4)
                    return pb_bad("notification sequence/state");
                step = (int)state;
                ipc_note("BATCH NOTIFY RECEIVED step=%d state=%llu", step, state);
            }
        }
        if (!step) { sleep(1); continue; }
        if (!id && step != 3) {
            int gen = generation(step);
            [prefs setObject:[NSString stringWithUTF8String:device(gen)] forKey:@"device"];
            [prefs setInteger:soc(gen) forKey:@"soc"];
            [prefs setBool:(gen != 2) forKey:@"enabled"];
            [prefs setInteger:gen forKey:@"generation"];
            ipc_note("BATCH SET step=%d generation=%d", step, gen);
        }
        if (read_values(prefs, step)) return 1;
        if (!id) {
            if (step == 3) ipc_note("BATCH RECOVERY READ ONLY generation=2 no_setters=1");
            /* Explicit application-level signal AFTER the successful save.
             * State contains only the step number, never preference values. */
            if (notify_set_state(token, (unsigned long long)step) || notify_post(PB_NAME))
                return pb_bad("notification publish");
            ipc_note("BATCH NOTIFY POSTED step=%d state=%d explicit_after_save=1", step, step);
            int acknowledged = 0;
            for (int i = 0; i < 600; ++i) {
                if (pb_get_fd(ack1) == step && pb_get_fd(ack2) == step) { acknowledged = 1; break; }
                sleep(1);
            }
            if (!acknowledged) return pb_bad("reader acknowledgement timeout");
            if (pb_put_fd(completed, step)) return pb_bad("writer completion acknowledgement");
            ipc_note("BATCH BOTH READERS ACK step=%d", step);
        } else {
            if (pb_put_fd(ack1, step)) return pb_bad("reader acknowledgement");
            ipc_note("BATCH ACK id=%d step=%d", id, step);
        }
        last = step;
        if (last == 4) {
            if (cancel_token(token)) return 1;
            [pool drain]; return 0;
        }
    }
    return pb_bad("batch bounded overall wait timeout");
}
int main(int argc, char **argv) {
#if defined(SWEET_PREFS_WRITER)
    (void)argc; (void)argv;
    int client_id = 0;
#else
    int client_id = argc == 2 && !strcmp(argv[1], "1") ? 1 : (argc == 2 && !strcmp(argv[1], "2") ? 2 : -1);
    if (client_id < 0) return 2;
#endif
    char role[64]; snprintf(role, sizeof(role), "prefs-batch-%d-%d", client_id, getpid());
    if (ipc_identity(role)) return pb_bad("probe identity");
    int pidfd = pb_open("pid", client_id, 1), control = pb_open("control", client_id, 1);
    int ack1 = pb_open("ack", client_id ? client_id : 1, client_id != 0);
    int ack2 = client_id ? -1 : pb_open("ack", 2, 0);
    int completed = client_id ? -1 : pb_open("completed", 0, 1);
    if (pidfd < 0 || control < 0 || ack1 < 0 || (!client_id && (ack2 < 0 || completed < 0)))
        return pb_bad("regular coordination files");
    ipc_note("BATCH ENTERED id=%d", client_id);
    @try { if (exercise(client_id, pidfd, control, ack1, ack2, completed)) return 1; }
    @catch (id exception) { (void)exception; return pb_bad("Objective-C exception"); }
    ipc_note("BATCH NORMAL EXIT id=%d status=0", client_id);
    sync();
    if (close(control) || close(ack1) || (!client_id && (close(ack2) || close(completed))) || close(ipc_trace)) return 1;
    return 0;
}
