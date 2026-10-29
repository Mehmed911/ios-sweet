/* Minimal Darwin arm64 ABI, checked against XNU bsd/sys/{un,socket,poll,signal}.h. */
#ifndef SWEET_IPC_H
#define SWEET_IPC_H
#include <stdarg.h>
typedef unsigned long size_t;
typedef long ssize_t;
typedef unsigned int ipc_u32;
extern int getpid(void), getppid(void), proc_pidpath(int, void *, unsigned int);
extern unsigned int getuid(void), geteuid(void), sleep(unsigned int);
extern int open(const char *, int, ...), close(int), fsync(int), unlink(const char *);
extern int access(const char *, int), kill(int, int), *__error(void);
extern ssize_t read(int, void *, size_t), write(int, const void *, size_t);
extern int strcmp(const char *, const char *), memcmp(const void *, const void *, size_t);
extern size_t strlen(const char *);
extern long strtol(const char *, char **, int);
extern int printf(const char *, ...), fflush(void *), snprintf(char *, size_t, const char *, ...);
extern int vsnprintf(char *, size_t, const char *, va_list);
extern int socket(int, int, int), bind(int, const void *, unsigned int), listen(int, int);
extern int connect(int, const void *, unsigned int), accept(int, void *, unsigned int *);
extern int setsockopt(int, int, int, const void *, unsigned int);
extern int getsockopt(int, int, int, void *, unsigned int *);
struct ipc_pollfd { int fd; short events, revents; };
struct ipc_timeval { long seconds; int micros; };
struct ipc_address { unsigned char length, family; char path[104]; };
struct ipc_action { void (*handler)(int); unsigned int mask; int flags; };
extern int poll(struct ipc_pollfd *, unsigned int, int);
extern int sigaction(int, const struct ipc_action *, struct ipc_action *);
extern int sigprocmask(int, const unsigned int *, unsigned int *);
_Static_assert(sizeof(struct ipc_pollfd) == 8, "Darwin pollfd");
_Static_assert(sizeof(struct ipc_timeval) == 16, "Darwin timeval");
_Static_assert(sizeof(struct ipc_address) == 106, "Darwin sockaddr_un");
_Static_assert(sizeof(struct ipc_action) == 16, "Darwin sigaction");
#define IPC_SOCKET "/private/var/tmp/sweet-ipc.sock"
#define IPC_SERVER_PID "/private/var/tmp/ipc-server.pid"
#define IPC_CLIENT_PID "/private/var/tmp/ipc-client.pid"
#define IPC_RELEASE "/private/var/tmp/ipc-client.exit"
#define IPC_SERVER_PATH "/sbin/sweet-launchd-service"
#define IPC_CLIENT_PATH "/sbin/sweet-ipc-client"
static int ipc_trace = -1;
static const char *ipc_role;
static inline int ipc_write_all(int fd, const void *data, size_t count) {
    const char *p = data;
    while (count) {
        ssize_t n = write(fd, p, count);
        if (n < 0 && *__error() == 4) continue;
        if (n <= 0) return -1;
        p += n; count -= (size_t)n;
    }
    return 0;
}
static inline int ipc_read_all(int fd, void *data, size_t count) {
    char *p = data;
    while (count) {
        ssize_t n = read(fd, p, count);
        if (n < 0 && *__error() == 4) continue;
        if (n <= 0) return -1;
        p += n; count -= (size_t)n;
    }
    return 0;
}
static inline void ipc_note(const char *format, ...) {
    char line[384]; va_list args;
    va_start(args, format);
    int n = vsnprintf(line, sizeof(line), format, args);
    va_end(args);
    if (n < 0 || (size_t)n >= sizeof(line)) return;
    printf("SWEET ipc %s: %s\n", ipc_role, line); fflush(0);
    if (ipc_trace >= 0) {
        ipc_write_all(ipc_trace, line, (size_t)n);
        ipc_write_all(ipc_trace, "\n", 1); fsync(ipc_trace);
    }
}
static inline int ipc_fail(const char *step) {
    ipc_note("FAIL %s errno=%d", step, *__error()); return 1;
}
static inline int ipc_identity(const char *role) {
    ipc_role = role;
    char path[128], parent[1024] = {0};
    snprintf(path, sizeof(path), "/private/var/tmp/ipc-%s.log", role);
    ipc_trace = open(path, 0x601, 0600);
    if (ipc_trace < 0 || getpid() <= 1 || getppid() != 1 || getuid() || geteuid() ||
        proc_pidpath(1, parent, sizeof(parent)) <= 0 || strcmp(parent, "/sbin/launchd")) return -1;
    ipc_note("IDENTITY pid=%d ppid=1 uid=0 parent=/sbin/launchd", getpid());
    return 0;
}
static inline int ipc_path_matches(int pid, const char *path) {
    char name[1024] = {0};
    return pid > 1 && proc_pidpath(pid, name, sizeof(name)) > 0 && !strcmp(name, path) && !kill(pid, 0);
}
static inline int ipc_read_pid(const char *path) {
    char data[32] = {0}, *end;
    int fd = open(path, 0);
    if (fd < 0) return -1;
    ssize_t n = read(fd, data, sizeof(data) - 1); close(fd);
    if (n <= 0) return -1;
    long pid = strtol(data, &end, 10);
    if (end == data || pid <= 1 || pid > 2147483647L) return -1;
    while (*end == '\n' || *end == '\r' || *end == ' ') ++end;
    return *end ? -1 : (int)pid;
}
static inline int ipc_publish_pid(const char *path) {
    char data[32]; int n = snprintf(data, sizeof(data), "%d\n", getpid());
    int fd = open(path, 0x601, 0600);
    if (fd < 0 || n <= 0 || (size_t)n >= sizeof(data)) return -1;
    int error = ipc_write_all(fd, data, (size_t)n) || fsync(fd);
    if (close(fd)) error = 1;
    return error ? -1 : 0;
}
static inline struct ipc_address ipc_addr(void) {
    struct ipc_address address = {0};
    address.family = 1;
    size_t n = strlen(IPC_SOCKET);
    for (size_t i = 0; i <= n; ++i) address.path[i] = IPC_SOCKET[i];
    address.length = (unsigned char)(2 + n + 1);
    return address;
}
static inline int ipc_options(int fd) {
    int one = 1;
    struct ipc_timeval timeout = {30, 0};
    return setsockopt(fd, 0xffff, 0x1022, &one, sizeof(one)) ||
        setsockopt(fd, 0xffff, 0x1005, &timeout, sizeof(timeout)) ||
        setsockopt(fd, 0xffff, 0x1006, &timeout, sizeof(timeout));
}
static inline int ipc_peer(int fd, const char *path) {
    int pid = -1; unsigned int length = sizeof(pid);
    if (getsockopt(fd, 0, 2, &pid, &length) || length != sizeof(pid) || !ipc_path_matches(pid, path)) return -1;
    return pid;
}
struct ipc_message { ipc_u32 magic, version, kind, seq, client, server, value, check; };
_Static_assert(sizeof(struct ipc_message) == 32, "fixed local IPC frame");
static inline ipc_u32 ipc_sum(const struct ipc_message *m) {
    return m->magic ^ m->version ^ m->kind ^ m->seq ^ m->client ^ m->server ^ m->value;
}
static inline struct ipc_message ipc_message(ipc_u32 kind, ipc_u32 seq, int client, int server) {
    struct ipc_message m = {0x53574950, 1, kind, seq, (ipc_u32)client, (ipc_u32)server, 0x10203000 + seq, 0};
    if (kind == 2) m.value ^= 0x5a5a5a5a;
    m.check = ipc_sum(&m); return m;
}
static inline int ipc_valid(const struct ipc_message *m, ipc_u32 kind, ipc_u32 seq, int client, int server) {
    struct ipc_message expected = ipc_message(kind, seq, client, server);
    return !memcmp(m, &expected, sizeof(expected));
}
#endif
