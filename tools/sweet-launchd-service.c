/* One persistent C service; require launchd to be its direct parent. */
typedef unsigned long size_t;
typedef long ssize_t;
extern int getpid(void);
extern int getppid(void);
extern unsigned int getuid(void);
extern unsigned int geteuid(void);
extern int open(const char *, int, ...);
extern int close(int);
extern ssize_t read(int, void *, size_t);
extern ssize_t write(int, const void *, size_t);
extern int printf(const char *, ...);
extern int fflush(void *);
extern unsigned int sleep(unsigned int);
extern int memcmp(const void *, const void *, size_t);
extern int strcmp(const char *, const char *);
extern int proc_pidpath(int, void *, unsigned int);
extern int snprintf(char *, size_t, const char *, ...);
extern int fsync(int);
struct action {
    void (*handler)(int);
    unsigned int mask;
    int flags;
};
_Static_assert(sizeof(struct action) == 16, "Darwin arm64 sigaction ABI");
extern int sigaction(int, const struct action *, struct action *);
extern int sigprocmask(int, const unsigned int *, unsigned int *);

int main(void) {
    int pid = getpid(), parent = getppid();
    printf("SWEET launchd service: main pid=%d ppid=%d\n", pid, parent);
    fflush(0);
    if (pid <= 1 || parent != 1) return 1;
    printf("SWEET launchd service: uid=%u euid=%u\n", getuid(), geteuid());
    fflush(0);
    if (getuid() != 0 || geteuid() != 0) return 10;
    char parent_path[1024] = {0};
    if (proc_pidpath(parent, parent_path, sizeof(parent_path)) <= 0 ||
        strcmp(parent_path, "/sbin/launchd") != 0) return 9;
    printf("SWEET launchd service: parent_path=%s\n", parent_path);
    fflush(0);
    struct action previous = {0}, defaults = {0}, current = {0};
    unsigned int inherited = 0, empty = 0, mask = 0;
    if (sigaction(15, 0, &previous) || sigprocmask(3, 0, &inherited)) return 14;
    const char *disposition = previous.handler == 0 ? "default" :
        previous.handler == (void (*)(int))1 ? "ignored" : "custom";
    printf("SWEET launchd service: TERM inherited=%s mask=0x%08x pid=%d\n",
           disposition, inherited, pid);
    if (sigaction(15, &defaults, 0) || sigprocmask(3, &empty, 0)) return 15;
    if (sigaction(15, 0, &current) || sigprocmask(3, 0, &mask) ||
        current.handler != 0 || mask != 0) return 16;
    printf("SWEET launchd service: TERM default mask=0x00000000 pid=%d\n", pid);
    fflush(0);
    const char data[] = "service launched by original PID 1\n";
    char buffer[sizeof(data)], extra;
    int fd = open("/private/var/tmp/sweet-launchd-service.data", 0x601, 0600);
    if (fd < 0) return 2;
    size_t at = 0;
    while (at < sizeof(data)) {
        ssize_t n = write(fd, data + at, sizeof(data) - at);
        if (n <= 0) return 3;
        at += (size_t)n;
    }
    if (close(fd)) return 4;
    fd = open("/private/var/tmp/sweet-launchd-service.data", 0);
    if (fd < 0) return 5;
    at = 0;
    while (at < sizeof(data)) {
        ssize_t n = read(fd, buffer + at, sizeof(data) - at);
        if (n <= 0) return 6;
        at += (size_t)n;
    }
    if (memcmp(buffer, data, sizeof(data)) || read(fd, &extra, 1) != 0) return 7;
    if (close(fd)) return 8;
    printf("SWEET launchd service: RAM file verified\n");
    fflush(0);
    char ready[32];
    int length = snprintf(ready, sizeof(ready), "%d\n", pid);
    fd = open("/private/var/tmp/sweet-service.pid", 0x601, 0600);
    if (fd < 0 || length <= 0 || (size_t)length >= sizeof(ready)) return 11;
    at = 0;
    while (at < (size_t)length) {
        ssize_t n = write(fd, ready + at, (size_t)length - at);
        if (n <= 0) return 12;
        at += (size_t)n;
    }
    if (fsync(fd) || close(fd)) return 13;
    unsigned int count = 0;
    for (;;) {
        printf("SWEET launchd service: heartbeat=%u pid=%d ppid=%d\n",
               ++count, getpid(), getppid());
        fflush(0);
        unsigned int remaining = 5;
        while (remaining) remaining = sleep(remaining);
    }
}
