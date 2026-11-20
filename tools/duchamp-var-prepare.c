/* SPDX-License-Identifier: 0BSD */
/* Darwin ARM64 mount arguments and stat ABI used by the QEMU bootstrap. */
typedef unsigned long size_t;
typedef long ssize_t;

struct hfs_args {
    const char *device;
    unsigned int uid, gid;
    unsigned short mask;
    unsigned int encoding;
    int minuteswest, dst, flags, journal_size, journal_flags, journal_disable;
};
struct stat {
    int dev;
    unsigned short mode, nlink;
    unsigned long ino;
    unsigned int uid, gid;
    int rdev;
    long times[8];
    long size, blocks;
    int blksize;
    unsigned int flags, gen;
    int spare;
    long reserved[2];
};
struct statfs {
    unsigned int block_size;
    int io_size;
    unsigned long blocks, bfree, bavail, files, ffree;
    int fsid[2];
    unsigned int owner, type, flags, subtype;
    char filesystem[16], mounted_on[1024], mounted_from[1024];
    unsigned int extended_flags, reserved[7];
};
_Static_assert(sizeof(struct hfs_args) == 48, "Darwin ARM64 HFS mount args");
_Static_assert(sizeof(struct stat) == 144, "Darwin ARM64 stat");
_Static_assert(sizeof(struct statfs) == 2168, "Darwin ARM64 statfs");

extern int mount(const char *, const char *, int, void *);
extern int statfs(const char *, struct statfs *);
extern int lstat(const char *, struct stat *), stat(const char *, struct stat *);
extern ssize_t readlink(const char *, char *, size_t);
extern int open(const char *, int, ...), close(int), fsync(int), unlink(const char *);
extern ssize_t read(int, void *, size_t), write(int, const void *, size_t);
extern int printf(const char *, ...), fflush(void *), strcmp(const char *, const char *);
extern int snprintf(char *, size_t, const char *, ...);
extern int *__error(void);

enum {
    EROFS = 30, ENOSPC = 28, EINTR = 4, EACCES = 13, RDONLY = 1, ROOTFS = 0x4000,
    NOSUID = 8, NODEV = 16, NOATIME = 0x10000000, CREATE_EXCLUSIVE = 0xa01,
};
static const char mountpoint[] = "/private/var";
static int fail(const char *step, int error)
{
    printf("VAR PREFLIGHT FAIL %s errno=%d\n", step, error);
    fflush(0);
    return 1;
}

static int check_capacity(unsigned long *filled)
{
    static char block[65536];
    const char *path = "/private/var/tmp/.duchamp-capacity";
    struct statfs before, after;
    if (statfs(mountpoint, &before))
        return fail("capacity statfs", *__error());
    int fd = open(path, CREATE_EXCLUSIVE, 0600);
    if (fd < 0)
        return fail("capacity open", *__error());
    unsigned long written = 0;
    int error = 0;
    /* This scratch file is bounded by the complete 32 MiB md1 reservation. */
    while (written <= 32UL * 1024 * 1024) {
        ssize_t count = write(fd, block, sizeof(block));
        if (count < 0 && *__error() == EINTR)
            continue;
        if (count <= 0) {
            error = count < 0 ? *__error() : 0;
            break;
        }
        written += (size_t)count;
    }
    int closed = close(fd);
    int removed = unlink(path);
    if (error != ENOSPC || closed || removed || statfs(mountpoint, &after) ||
        after.bavail < before.bavail / 2)
        return fail("capacity or recovery", error);
    *filled = written;
    printf("VAR CAPACITY PASS errno=%d bytes=%lu\n", error, written);
    return 0;
}

int main(void)
{
    struct statfs root, data;
    struct stat point, alias, actual, tmp;
    if (statfs("/", &root) || strcmp(root.filesystem, "hfs") ||
        (root.flags & (RDONLY | ROOTFS)) != (RDONLY | ROOTFS))
        return fail("root filesystem", *__error());
    int console = open("/dev/console", 2);
    if (console < 0 || close(console))
        return fail("devfs console", *__error());
    int raw = open("/dev/rmd0", 0);
    if (raw < 0 || close(raw))
        return fail("open raw md0 read-only", *__error());
    raw = open("/dev/rmd0", 1);
    int raw_error = *__error();
    if (raw >= 0) {
        close(raw);
        return fail("raw md0 opened for writing", 0);
    }
    if (raw_error != EACCES && raw_error != EROFS)
        return fail("raw md0 write-open error", raw_error);
    if (lstat(mountpoint, &point))
        return fail("missing /private/var", *__error());
    if (point.mode != 0040755 || point.uid || point.gid)
        return fail("mountpoint permissions", 0);
    char target[64] = {0};
    if (readlink("/var", target, sizeof(target) - 1) != sizeof(mountpoint) - 1 ||
        strcmp(target, mountpoint))
        return fail("/var resolution", 0);
    struct hfs_args args = {.device = "/dev/md1", .mask = 0755};
    if (mount("hfs", mountpoint, NOSUID | NODEV | NOATIME, &args))
        return fail("mount /dev/md1", *__error());
    if (statfs(mountpoint, &data) || strcmp(data.filesystem, "hfs") ||
        strcmp(data.mounted_from, "/dev/md1") || (data.flags & (RDONLY | ROOTFS)) ||
        (root.fsid[0] == data.fsid[0] && root.fsid[1] == data.fsid[1]))
        return fail("separate writable mount", 0);
    if (stat("/var", &alias) || stat(mountpoint, &actual) ||
        alias.dev != actual.dev || alias.ino != actual.ino)
        return fail("/var mounted identity", 0);
    if (lstat("/private/var/tmp", &tmp) || tmp.mode != 0041777 || tmp.uid || tmp.gid)
        return fail("tmp permissions", 0);

    int fd = open("/.duchamp-var-write-test", CREATE_EXCLUSIVE, 0600);
    int error = *__error();
    if (fd >= 0) {
        close(fd);
        return fail("root write unexpectedly succeeded", 0);
    }
    if (error != EROFS)
        return fail("root did not return EROFS", error);
    printf("VAR ROOT PASS EROFS=%d\n", error);
    unsigned long filled;
    if (check_capacity(&filled))
        return 1;
    char witness[256], got[256] = {0};
    int bytes = snprintf(witness, sizeof(witness),
                         "console=/dev/console\nsource=%s\nalias=%s\n"
                         "root_errno=%d\nraw_root_errno=%d\ncapacity_errno=%d\nfilled_bytes=%lu\n",
                         data.mounted_from, target, error, raw_error, ENOSPC, filled);
    if (bytes < 1 || (size_t)bytes >= sizeof(witness))
        return fail("format preflight witness", 0);
    fd = open("/var/tmp/duchamp-var-witness", CREATE_EXCLUSIVE, 0600);
    if (fd < 0 || write(fd, witness, (size_t)bytes) != bytes ||
        fsync(fd) || close(fd))
        return fail("write fresh var witness", *__error());
    fd = open("/private/var/tmp/duchamp-var-witness", 0);
    if (fd < 0 || read(fd, got, sizeof(got)) != bytes ||
        strcmp(got, witness) || close(fd))
        return fail("read var witness through canonical path", *__error());
    printf("VAR PREFLIGHT PASS source=%s /var=/private/var\n", data.mounted_from);
    return fflush(0) ? 1 : 0;
}
