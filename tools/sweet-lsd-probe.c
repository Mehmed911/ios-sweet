/* LaunchServices daemon start/identity/endpoint witness, confined to QEMU RAM. */
#include "sweet-ipc.h"
extern int fork(void), dup2(int, int), waitpid(int, int *, int);
extern int execve(const char *, char *const [], char *const []);
extern char ***_NSGetEnviron(void);
extern void _exit(int) __attribute__((noreturn));
extern void sync(void);
extern char *strstr(const char *, const char *);
extern int mkdir(const char *, unsigned short), chown(const char *, unsigned int, unsigned int);
extern unsigned int bootstrap_port, mach_task_self_;
/* Apple liblaunch/bootstrap_priv.h; this job is relocated into user/501. */
extern int bootstrap_look_up_per_user(unsigned int, const char *, unsigned int, unsigned int *);
extern int mach_port_deallocate(unsigned int, unsigned int);
extern int proc_pidinfo(int, int, unsigned long long, void *, int);
/* XNU bsd/sys/proc_info.h: PROC_PIDTBSDINFO=3, MAXCOMLEN=16. */
struct bsd_info {
    unsigned int flags, status, xstatus, pid, ppid, uid, gid, ruid, rgid, svuid, svgid, reserved;
    char comm[16], name[32];
    unsigned int nfiles, pgid, jobc, device, foreground;
    int nice;
    unsigned long long start_seconds, start_micros;
};
_Static_assert(sizeof(struct bsd_info) == 136, "XNU proc_bsdinfo ABI");
static char output[65536];

static int publish(const char *text) {
    if (ipc_write_all(ipc_trace, text, strlen(text)) || ipc_write_all(ipc_trace, "\n", 1) || fsync(ipc_trace)) return 1;
    sync();
    printf("SWEET ipc lsd-control: %s\n", text); fflush(0);
    return 0;
}
static int failed(const char *step) {
    char line[256];
    snprintf(line, sizeof(line), "LSD PROBE FAIL step=%s errno=%d", step, *__error());
    publish(line); publish("LSD PROBE DONE status=1"); return 1;
}
static int cli(const char *tag, char *const args[]) {
    char path[192];
    snprintf(path, sizeof(path), "/private/var/tmp/lsd-cli-%s.txt", tag);
    int fd = open(path, 0x601, 0600);
    if (fd < 0) return -1;
    int pid = fork();
    if (pid < 0) { close(fd); return -1; }
    if (!pid) {
        if (dup2(fd, 1) < 0 || dup2(fd, 2) < 0) _exit(126);
        if (fd > 2) close(fd);
        if (ipc_trace > 2) close(ipc_trace);
        execve("/bin/launchctl", args, *_NSGetEnviron()); _exit(127);
    }
    int status = -1, reaped = 0;
    for (int attempt = 0; attempt < 45; ++attempt) {
        int got = waitpid(pid, &status, 1);
        if (got == pid) { reaped = 1; break; }
        if (got < 0 && *__error() != 4) break;
        sleep(1);
    }
    if (!reaped) {
        int got;
        do { got = waitpid(pid, &status, 1); } while (got < 0 && *__error() == 4);
        if (!got) {
            kill(pid, 9);
            while (waitpid(pid, &status, 0) < 0 && *__error() == 4) {}
        }
        close(fd); return -1;
    }
    if (fsync(fd) || close(fd)) return -1;
    ipc_note("LSD CLI %s status=0x%08x", tag, status);
    if (status) return -1;
    fd = open(path, 0);
    if (fd < 0) return -1;
    size_t used = 0;
    while (used < sizeof(output) - 1) {
        ssize_t count = read(fd, output + used, sizeof(output) - 1 - used);
        if (count < 0 && *__error() == 4) continue;
        if (count < 0) { close(fd); return -1; }
        if (!count) break;
        used += (size_t)count;
    }
    output[used] = 0;
    if (close(fd) || used == sizeof(output) - 1) return -1;
    return 0;
}
static int identity(int pid) {
    struct bsd_info info = {0};
    if (proc_pidinfo(pid, 3, 0, &info, sizeof(info)) != (int)sizeof(info) ||
        info.pid != (unsigned int)pid || info.ppid != 1 || info.uid != 501 || info.gid != 501 ||
        !ipc_path_matches(pid, "/usr/libexec/lsd")) return -1;
    ipc_note("LSD NATIVE IDENTITY pid=%d ppid=1 uid=501 gid=501 path=/usr/libexec/lsd", pid);
    return 0;
}
int main(void) {
    if (ipc_identity("lsd-control")) return 1;
    ipc_note("LSD PROBE ENTERED");
    const char *directories[] = {"/private/var/mobile", "/private/var/mobile/Library",
        "/private/var/mobile/Library/Caches", "/private/var/mobile/Library/Preferences",
        "/private/var/mobile/Library/Logs"};
    for (unsigned int i = 0; i < sizeof(directories) / sizeof(*directories); ++i) {
        if (mkdir(directories[i], 0755) && *__error() != 17) return failed("mobile directory");
        if (chown(directories[i], 501, 501)) return failed("mobile ownership");
    }
    char *start[] = {"launchctl", "kickstart", "-p", "system/com.apple.lsd", 0};
    if (cli("start", start)) return failed("launchctl kickstart");
    int pid = -1;
    for (int attempt = 0; attempt < 20; ++attempt) {
        char tag[40]; snprintf(tag, sizeof(tag), "startup-%d", attempt);
        char *print[] = {"launchctl", "print", "system/com.apple.lsd", 0};
        if (cli(tag, print)) return failed("launchctl print");
        char *position = strstr(output, "pid = ");
        if (position) pid = (int)strtol(position + 6, 0, 10);
        if (pid > 1 && !identity(pid)) break;
        pid = -1; sleep(1);
    }
    if (pid <= 1) return failed("native startup/identity timeout");
    const char *services[] = {"icons", "rebuild", "diagnostics", "plugin", "extensions", "openurl", "xpc",
        "modifydb", "mapdb", "personaobserver", "installation", "advertisingidentifiers", "open"};
    for (unsigned int i = 0; i < sizeof(services) / sizeof(*services); ++i) {
        char name[96]; unsigned int port = 0;
        snprintf(name, sizeof(name), "com.apple.lsd.%s", services[i]);
        int result = bootstrap_look_up_per_user(bootstrap_port, name, 501, &port);
        if (result || !port) return failed("native endpoint lookup");
        ipc_note("LSD ENDPOINT PUBLISHED name=%s lookup=0 user=501", name);
        if (mach_port_deallocate(mach_task_self_, port)) return failed("port release");
    }
    for (int check = 1; check <= 3; ++check) {
        sleep(2);
        if (identity(pid)) return failed("stable mobile identity");
        ipc_note("LSD HEALTH check=%d pid=%d stable=1", check, pid);
    }
    if (publish("LSD STARTUP PORTS PASS endpoints=13 uid=501 gid=501 stable_checks=3")) return 1;
    if (publish("LSD PROBE DONE status=0")) return 1;
    for (;;) sleep(60);
}
