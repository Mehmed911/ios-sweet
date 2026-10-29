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
    unsigned int count = 0;
    for (;;) {
        printf("SWEET launchd service: heartbeat=%u pid=%d ppid=%d\n",
               ++count, getpid(), getppid());
        fflush(0);
        unsigned int remaining = 5;
        while (remaining) remaining = sleep(remaining);
    }
}
