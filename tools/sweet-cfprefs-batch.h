/* Control files carry only a PID, a step number or -1 (stop), never values. */
#ifndef SWEET_CFPREFS_BATCH_H
#define SWEET_CFPREFS_BATCH_H
#include "sweet-ipc.h"
#define PB_NAME "org.sweet.qemu.preferences.batch.changed"
#define PB_SUITE "org.sweet.qemu.preferences.batch"
extern long lseek(int, long, int);
extern int ftruncate(int, long);
static inline void pb_path(char *path, const char *kind, int id) {
    snprintf(path, 160, "/private/var/tmp/prefs-batch-%s-%d", kind, id);
}
static inline int pb_open(const char *kind, int id, int truncate) {
    char path[160]; pb_path(path, kind, id);
    return open(path, truncate ? 0x602 : 0x202, 0600);
}
static inline int pb_put_fd(int fd, int value) {
    char data[32]; int n = snprintf(data, sizeof(data), "%d\n", value);
    if (fd < 0 || n < 1 || n >= (int)sizeof(data) || lseek(fd, 0, 0) < 0 || ftruncate(fd, 0))
        return -1;
    return ipc_write_all(fd, data, (size_t)n) || fsync(fd) ? -1 : 0;
}
static inline int pb_get_fd(int fd) {
    char data[32] = {0}, *end;
    if (fd < 0 || lseek(fd, 0, 0) < 0) return -100;
    ssize_t n = read(fd, data, sizeof(data) - 1);
    if (n < 0) return -100;
    if (!n || data[n - 1] != '\n') return 0; /* writer may be between truncate/write */
    long value = strtol(data, &end, 10);
    return end != data && *end == '\n' && !end[1] && value >= -1 && value <= 2147483647L ? (int)value : -100;
}
static inline int pb_load(const char *kind, int id) {
    char path[160]; pb_path(path, kind, id);
    int fd = open(path, 0);
    if (fd < 0) return 0;
    int value = pb_get_fd(fd); close(fd); return value;
}
static inline int pb_store(const char *kind, int id, int value) {
    int fd = pb_open(kind, id, 0);
    if (fd < 0) return -1;
    int result = pb_put_fd(fd, value);
    if (close(fd)) result = -1;
    return result;
}
#endif
