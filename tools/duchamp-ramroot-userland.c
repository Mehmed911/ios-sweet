/* SPDX-License-Identifier: 0BSD */
/* Small arm64 Darwin ABI subset. This file builds without an Apple SDK. */
typedef unsigned long size_t;
typedef long ssize_t;
typedef long off_t;
typedef struct darwin_dir DIR;
struct dirent {
    unsigned long ino, seekoff;
    unsigned short reclen, namlen;
    unsigned char type;
    char name[1024];
};
_Static_assert(__builtin_offsetof(struct dirent, name) == 21, "Darwin ARM64 dirent layout");

extern DIR *opendir(const char *);
extern struct dirent *readdir(DIR *);
extern int closedir(DIR *);
extern int getpid(void), getppid(void);
struct statfs {
    unsigned int block_size;
    int io_size;
    unsigned long blocks, bfree, bavail, files, ffree;
    int fsid[2];
    unsigned int owner, type, flags, subtype;
    char filesystem[16], mounted_on[1024], mounted_from[1024];
    unsigned int extended_flags, reserved[7];
};
_Static_assert(sizeof(struct statfs) == 2168, "Darwin ARM64 statfs layout");
extern int statfs(const char *, struct statfs *);
extern int open(const char *, int, ...), close(int), *__error(void);
extern ssize_t read(int, void *, size_t);
extern int printf(const char *, ...), fflush(void *);
extern int strcmp(const char *, const char *), memcmp(const void *, const void *, size_t);
extern void *mmap(void *, size_t, int, int, int, off_t);
extern int mprotect(void *, size_t, int), munmap(void *, size_t);
extern int execve(const char *, char *const [], char *const []);
extern int fork(void), waitpid(int, int *, int);
extern void _exit(int) __attribute__((noreturn));
extern unsigned int _dyld_image_count(void);
extern const char *_dyld_get_image_name(unsigned int);

typedef unsigned int mach_port_t;
struct mach_header {
    unsigned int bits, size;
    mach_port_t remote, local, voucher;
    int id;
};
_Static_assert(sizeof(struct mach_header) == 24, "Darwin ARM64 Mach header layout");
extern mach_port_t mach_task_self_;
extern int mach_port_allocate(mach_port_t, int, mach_port_t *);
extern int mach_port_insert_right(mach_port_t, mach_port_t, mach_port_t, int);
extern int mach_port_destroy(mach_port_t, mach_port_t);
extern int mach_msg(struct mach_header *, int, unsigned int, unsigned int,
                    mach_port_t, unsigned int, mach_port_t);

enum {
    DARWIN_ENOENT = 2, DARWIN_EINTR = 4, DARWIN_ENOTDIR = 20, DARWIN_EINVAL = 22,
    DARWIN_EROFS = 30, WRITE_CREATE = 0x201, PROT_READ = 1, PROT_WRITE = 2,
    MAP_PRIVATE = 2, RECEIVE_RIGHT = 1, COPY_SEND = 19, MAKE_SEND = 20,
    SEND_MSG = 1, RCV_MSG = 2, RCV_TIMEOUT = 0x100,
    MNT_RDONLY = 1, MNT_ROOTFS = 0x4000,
};

static const char fixture[] = "/sbin/ramroot-fixture.txt";
static const char expected[] = "Duchamp Darwin HFS+ read-only fixture\n";
static const char static_program[] = "/sbin/ramroot-static";

static int fail(const char *step, int code)
{
    printf("RAMROOT USER: FAIL %s code=%d\n", step, code);
    fflush(0);
    return 1;
}

static int check_directory(void)
{
    struct statfs root;
    if (statfs("/", &root))
        return fail("root statfs", *__error());
    if (strcmp(root.filesystem, "hfs") || (root.flags & (MNT_ROOTFS | MNT_RDONLY)) !=
        (MNT_ROOTFS | MNT_RDONLY))
        return fail("root mount type or flags", (int)root.flags);
    printf("RAMROOT USER: HFS root readonly source=%s flags=%08x\n",
           root.mounted_from, root.flags);

    DIR *dir = opendir("/sbin");
    if (!dir)
        return fail("opendir", *__error());

    struct dirent *entry;
    int sample = 0, child = 0, init = 0;
    *__error() = 0;
    while ((entry = readdir(dir)) != 0) {
        sample |= strcmp(entry->name, "ramroot-fixture.txt") == 0;
        child |= strcmp(entry->name, "ramroot-static") == 0;
        init |= strcmp(entry->name, "launchd") == 0;
    }
    int error = *__error();
    int closed = closedir(dir);
    if (error || closed || !sample || !child || !init)
        return fail("readdir", error);
    printf("RAMROOT USER: HFS directory fixture static and init present\n");
    return 0;
}

static int require_open_error(const char *path, int flags, int wanted)
{
    int fd = open(path, flags, 0600);
    int error = *__error();
    if (fd >= 0) {
        close(fd);
        return fail(path, 0);
    }
    return error == wanted ? 0 : fail(path, error);
}

static int check_files_and_vm(void)
{
    const size_t bytes = sizeof(expected) - 1;
    int fd = open(fixture, 0);
    if (fd < 0)
        return fail("fixture open", *__error());

    unsigned char *map = mmap(0, bytes, PROT_READ, MAP_PRIVATE, fd, 0);
    if (map == (void *)-1 || memcmp(map, expected, bytes))
        return fail("file mmap", *__error());
    if (mprotect(map, bytes, PROT_READ | PROT_WRITE))
        return fail("mprotect private", *__error());
    map[0] = 'X';
    if (map[0] != 'X' || munmap(map, bytes))
        return fail("private mapping", *__error());
    void *invalid = mmap(0, bytes, PROT_READ, MAP_PRIVATE, fd, -1);
    if (invalid != (void *)-1 || *__error() != DARWIN_EINVAL)
        return fail("mmap invalid offset", *__error());

    char content[sizeof(expected)];
    size_t offset = 0;
    while (offset < bytes) {
        ssize_t count = read(fd, content + offset, bytes - offset);
        if (count < 0 && *__error() == DARWIN_EINTR)
            continue;
        if (count <= 0)
            return fail("fixture read", *__error());
        offset += (size_t)count;
    }
    if (memcmp(content, expected, bytes) || read(fd, content, 1) != 0 || close(fd))
        return fail("fixture bytes and EOF", *__error());
    printf("RAMROOT USER: HFS bytes=%lu EOF private VM and EINVAL verified\n", bytes);
    if (require_open_error("/sbin/ramroot-fixture.txt/not-dir", 0, DARWIN_ENOTDIR) ||
        require_open_error("/sbin/ramroot-no-such-file", 0, DARWIN_ENOENT) ||
        require_open_error("/sbin/ramroot-no-such-file", WRITE_CREATE, DARWIN_EROFS))
        return 1;
    printf("RAMROOT USER: ENOTDIR=%d ENOENT=%d EROFS=%d verified\n",
           DARWIN_ENOTDIR, DARWIN_ENOENT, DARWIN_EROFS);
    return 0;
}

static int check_mach_message(void)
{
    mach_port_t task = mach_task_self_, port = 0;
    int result = mach_port_allocate(task, RECEIVE_RIGHT, &port);
    if (result)
        return fail("mach_port_allocate", result);
    result = mach_port_insert_right(task, port, port, MAKE_SEND);
    if (result)
        return fail("mach_port_insert_right", result);

    struct {
        struct mach_header header;
        unsigned int value;
        unsigned char trailer[128];
    } packet = {{COPY_SEND, 28, port, 0, 0, 391}, 0x44554348, {0}};
    result = mach_msg(&packet.header, SEND_MSG, packet.header.size, 0, 0, 0, 0);
    if (result)
        return fail("mach_msg send", result);
    packet.value = 0;
    result = mach_msg(&packet.header, RCV_MSG | RCV_TIMEOUT, 0, sizeof(packet), port, 1000, 0);
    if (result || packet.header.size != 28 || packet.header.id != 391 ||
        packet.header.local != port || packet.value != 0x44554348)
        return fail("mach_msg receive", result);
    result = mach_port_destroy(task, port);
    if (result)
        return fail("mach_port_destroy", result);
    printf("RAMROOT USER: Mach loopback id=%d payload=%08x\n", packet.header.id, packet.value);
    return 0;
}

static int check_static_exec(void)
{
    fflush(0);
    int child = fork();
    if (child < 0)
        return fail("fork", *__error());
    if (!child) {
        char *const argv[] = {(char *)static_program, 0};
        char *const env[] = {0};
        execve(static_program, argv, env);
        _exit(127);
    }
    int status = 0, result;
    do {
        result = waitpid(child, &status, 0);
    } while (result < 0 && *__error() == DARWIN_EINTR);
    if (result != child || status != (42 << 8))
        return fail("static exec wait status", status);
    printf("RAMROOT USER: static child pid=%d exit=42 wait=%04x\n", child, (unsigned int)status);
    return 0;
}

int main(void)
{
    int pid = getpid(), parent = getppid(), libsystem = 0;
    unsigned int images = _dyld_image_count();
    for (unsigned int i = 0; i < images; i++) {
        const char *name = _dyld_get_image_name(i);
        if (name && strcmp(name, "/usr/lib/libSystem.B.dylib") == 0)
            libsystem = 1;
    }
    printf("RAMROOT USER: dynamic pid=%d ppid=%d images=%u libSystem=%d\n",
           pid, parent, images, libsystem);
    if (pid <= 1 || parent != 1 || images < 2 || !libsystem)
        return fail("dyld or process identity", 0);
    if (check_directory() || check_files_and_vm() || check_mach_message() || check_static_exec())
        return 1;
    printf("RAMROOT USER: PASS dynamic pid=%d\n", pid);
    return fflush(0) ? 1 : 0;
}
