/* Execute pinned Procursus launchctl; inspect output and actual process state. */
#include <stdarg.h>
typedef unsigned long size_t;
typedef long ssize_t;
extern int printf(const char *, ...), fflush(void *);
extern int vsnprintf(char *, size_t, const char *, va_list);
extern int snprintf(char *, size_t, const char *, ...);
extern int open(const char *, int, ...), close(int), fsync(int);
extern ssize_t read(int, void *, size_t), write(int, const void *, size_t);
extern long lseek(int, long, int), strtol(const char *, char **, int);
extern int strcmp(const char *, const char *), strncmp(const char *, const char *, size_t);
extern char *strstr(const char *, const char *), *strchr(const char *, int);
extern size_t strlen(const char *);
extern int fork(void), waitpid(int, int *, int), execve(const char *, char *const *, char *const *);
extern int dup2(int, int), kill(int, int), getpid(void), getppid(void);
extern unsigned int getuid(void), geteuid(void), sleep(unsigned int);
extern int *__error(void), proc_pidpath(int, void *, unsigned int);
extern char ***_NSGetEnviron(void);
extern void _exit(int) __attribute__((noreturn));
extern void sync(void);
static int trace = -1;
static char output[65536];
static const char target[] = "system/org.sweet.qemu.c-service";

static int write_all(int fd, const char *data, size_t count) {
    while (count) {
        ssize_t n = write(fd, data, count);
        if (n < 0 && *__error() == 4) continue;
        if (n <= 0) return -1;
        data += n; count -= (size_t)n;
    }
    return 0;
}
static void note(const char *format, ...) {
    char text[512];
    va_list args;
    va_start(args, format);
    int n = vsnprintf(text, sizeof(text), format, args);
    va_end(args);
    if (n < 0 || (size_t)n >= sizeof(text)) return;
    printf("SWEET launchctl: %s\n", text);
    fflush(0);
    if (trace >= 0) {
        write_all(trace, text, (size_t)n);
        write_all(trace, "\n", 1);
        fsync(trace);
    }
}
static int fail(const char *step) {
    note("FAIL %s errno=%d", step, *__error());
    sync();
    return 1;
}
static void pause_seconds(unsigned int seconds) {
    while (seconds) seconds = sleep(seconds);
}
static int path_matches(int pid, const char *path) {
    char value[1024] = {0};
    return pid > 1 && proc_pidpath(pid, value, sizeof(value)) > 0 &&
           strcmp(value, path) == 0 && kill(pid, 0) == 0;
}
static int decimal(const char *text) {
    char *end;
    long value = strtol(text, &end, 10);
    if (end == text || value <= 1 || value > 2147483647L) return -1;
    while (*end == ' ' || *end == '\t' || *end == '\r' || *end == '\n') ++end;
    return *end ? -1 : (int)value;
}
static int ready_pid(void) {
    char value[32] = {0};
    int fd = open("/private/var/tmp/sweet-service.pid", 0);
    if (fd < 0) return -1;
    ssize_t n = read(fd, value, sizeof(value) - 1);
    close(fd);
    return n > 0 ? decimal(value) : -1;
}
static int property_pid(const char *text) {
    while (*text) {
        const char *start = text;
        while (*start == ' ' || *start == '\t') ++start;
        if (strncmp(start, "pid = ", 6) == 0) {
            char value[32] = {0};
            const char *end = strchr(start, '\n');
            size_t n = end ? (size_t)(end - start - 6) : strlen(start + 6);
            if (n >= sizeof(value)) return -1;
            for (size_t i = 0; i < n; ++i) value[i] = start[6 + i];
            return decimal(value);
        }
        text = strchr(text, '\n');
        if (!text) break;
        ++text;
    }
    return 0;
}
static int command(const char *tag, char *const *argv) {
    char path[160];
    snprintf(path, sizeof(path), "/private/var/tmp/launchctl-%s.txt", tag);
    int fd = open(path, 0x602, 0600);
    if (fd < 0) return -1;
    note("BEGIN %s", tag);
    int child = fork();
    if (child < 0) { close(fd); return -1; }
    if (!child) {
        if (dup2(fd, 1) < 0 || dup2(fd, 2) < 0) _exit(126);
        if (fd > 2) close(fd);
        if (trace > 2) close(trace);
        execve("/bin/launchctl", argv, *_NSGetEnviron());
        _exit(127);
    }
    int status = 0, reaped = 0;
    for (int poll = 0; poll < 120; ++poll) {
        int result = waitpid(child, &status, 1);
        if (result == child) { reaped = 1; break; }
        if (result < 0 && *__error() != 4) break;
        pause_seconds(1);
    }
    if (!reaped) {
        /* A successful WNOHANG query returning 0 proves it is still our
         * unreaped child. Its PID cannot be reused before our wait. */
        int state;
        do { state = waitpid(child, &status, 1); } while (state < 0 && *__error() == 4);
        if (state == 0) {
            kill(child, 9);
            while (waitpid(child, &status, 0) < 0 && *__error() == 4) {}
        }
        close(fd);
        note("TIMEOUT %s", tag);
        return -1;
    }
    note("CLI %s status=0x%08x", tag, status);
    if (fsync(fd) || lseek(fd, 0, 0) < 0) { close(fd); return -1; }
    size_t at = 0;
    while (at < sizeof(output) - 1) {
        ssize_t n = read(fd, output + at, sizeof(output) - 1 - at);
        if (n < 0 && *__error() == 4) continue;
        if (n < 0) { close(fd); return -1; }
        if (!n) break;
        at += (size_t)n;
    }
    output[at] = 0;
    close(fd);
    if (status != 0) note("CLI %s output: %.160s", tag, output);
    return status == 0 && at < sizeof(output) - 1 ? 0 : -1;
}
int main(void) {
    trace = open("/private/var/tmp/launchctl-control.log", 0x601, 0600);
    if (trace < 0) return fail("trace open");
    char parent[1024] = {0};
    if (getppid() != 1 || getuid() != 0 || geteuid() != 0 ||
        proc_pidpath(1, parent, sizeof(parent)) <= 0 || strcmp(parent, "/sbin/launchd"))
        return fail("controller identity");
    note("controller pid=%d ppid=1 uid=0 parent=/sbin/launchd", getpid());
    int old = -1;
    for (int i = 0; i < 120; ++i) {
        old = ready_pid();
        if (path_matches(old, "/sbin/sweet-launchd-service")) break;
        old = -1;
        pause_seconds(1);
    }
    if (old <= 1) return fail("initial service readiness");
    char *before[] = {"launchctl", "print", (char *)target, 0};
    if (command("print-before", before) || property_pid(output) != old ||
        !strstr(output, "state = running")) return fail("print before");
    note("BEFORE pid=%d state=running", old);
    char *stop[] = {"launchctl", "kill", "SIGTERM", (char *)target, 0};
    if (command("stop", stop)) return fail("launchctl kill");
    int gone = 0;
    for (int i = 0; i < 60; ++i) {
        if (kill(old, 0) < 0 && *__error() == 3) { gone = 1; break; }
        pause_seconds(1);
    }
    if (!gone) return fail("old pid not reaped");
    note("STOPPED pid=%d ESRCH", old);
    pause_seconds(5);
    char *stopped[] = {"launchctl", "print", (char *)target, 0};
    if (command("print-stopped", stopped) || property_pid(output) != 0 ||
        !strstr(output, "org.sweet.qemu.c-service")) return fail("print stopped");
    note("STOP GAP verified no pid after 5 seconds");
    char *restart[] = {"launchctl", "kickstart", "-p", (char *)target, 0};
    if (command("restart", restart)) return fail("launchctl kickstart");
    int next = decimal(output);
    if (next <= 1 || next == old) return fail("new pid");
    int ready = 0;
    for (int i = 0; i < 120; ++i) {
        if (ready_pid() == next && path_matches(next, "/sbin/sweet-launchd-service")) {
            ready = 1; break;
        }
        pause_seconds(1);
    }
    if (!ready) return fail("restarted service readiness");
    char *after[] = {"launchctl", "print", (char *)target, 0};
    if (command("print-after", after) || property_pid(output) != next ||
        !strstr(output, "state = running")) return fail("print after");
    note("AFTER pid=%d state=running old=%d", next, old);
    note("CONTROL PASS old=%d new=%d", old, next);
    sync();
    for (unsigned int count = 1;; ++count) {
        pause_seconds(10);
        if (!path_matches(next, "/sbin/sweet-launchd-service")) return fail("final service lost");
        note("heartbeat=%u new_pid=%d", count, next);
    }
}
