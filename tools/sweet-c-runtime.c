/* A dynamically linked Darwin C test. No SDK is needed for this small ABI
 * surface: these declarations match the arm64 Darwin C interfaces used here.
 * All calls resolve through the supplied real libSystem and its reexports. */
typedef unsigned long size_t;
typedef long ssize_t;
extern int printf(const char *, ...);
extern int fflush(void *);
extern int open(const char *, int, ...);
extern ssize_t read(int, void *, size_t);
extern ssize_t write(int, const void *, size_t);
extern int close(int);
extern int memcmp(const void *, const void *, size_t);
extern int strcmp(const char *, const char *);
extern int fork(void);
extern int getpid(void);
extern int waitpid(int, int *, int);
extern void _exit(int) __attribute__((noreturn));
extern int *__error(void);
extern unsigned int _dyld_image_count(void);
extern const char *_dyld_get_image_name(unsigned int);

static int fail(const char *step) {
    printf("SWEET C: FAIL %s errno=%d\n", step, *__error());
    fflush(0);
    return 1;
}

int main(void) {
    unsigned int count = _dyld_image_count();
    int system = 0;
    printf("SWEET C: entered main pid=%d images=%u\n", getpid(), count);
    for (unsigned int i = 0; i < count; ++i) {
        const char *name = _dyld_get_image_name(i);
        if (name && strcmp(name, "/usr/lib/libSystem.B.dylib") == 0)
            system = 1;
    }
    if (!system || count < 2) return fail("dyld image list");
    printf("SWEET C: real libSystem loaded by dyld\n");
    const char expected[] = "C library RAM file roundtrip\n";
    char buffer[sizeof(expected)];
    int fd = open("/sbin/c-runtime-data", 0x601, 0600);
    if (fd < 0) return fail("open write");
    size_t at = 0;
    while (at < sizeof(expected)) {
        ssize_t n = write(fd, expected + at, sizeof(expected) - at);
        if (n <= 0) return fail("write");
        at += (size_t)n;
    }
    if (close(fd)) return fail("close write");
    fd = open("/sbin/c-runtime-data", 0);
    if (fd < 0) return fail("open read");
    at = 0;
    while (at < sizeof(expected)) {
        ssize_t n = read(fd, buffer + at, sizeof(expected) - at);
        if (n <= 0) return fail("read");
        at += (size_t)n;
    }
    char extra;
    if (memcmp(buffer, expected, sizeof(expected)) || read(fd, &extra, 1) != 0)
        return fail("file bytes/EOF");
    if (close(fd)) return fail("close read");
    printf("SWEET C: libc file bytes and EOF verified\n");
    fflush(0);  /* Do not duplicate buffered stdio output across fork. */
    int child = fork();
    if (child < 0) return fail("fork");
    if (!child) {
        printf("SWEET C: libc fork child running pid=%d\n", getpid());
        fflush(0);
        _exit(42);
    }
    int status = 0, result;
    do { result = waitpid(child, &status, 0); }
    while (result < 0 && *__error() == 4);
    if (result != child || status != 0x2a00) return fail("waitpid status");
    printf("SWEET C: libc fork and waitpid status 42 verified\n");
    printf("SWEET C: DYNAMIC RUNTIME PASS\n");
    fflush(0);
    return 0;
}
