/* Pinned iOS libnotify C ABI; first integration uses notifyd's IPC check path. */
#ifndef SWEET_NOTIFY_H
#define SWEET_NOTIFY_H
#include "sweet-ipc.h"
extern unsigned int notify_register_check(const char *, int *), notify_register_plain(const char *, int *);
extern unsigned int notify_check(int, int *), notify_cancel(int), notify_post(const char *);
extern unsigned int notify_set_state(int, unsigned long long), notify_get_state(int, unsigned long long *);
extern _Bool notify_is_valid_token(int);
#define NFY_NAME "org.sweet.qemu.notify.integration"
#define NFY_ONE 0x1020304050607001ULL
#define NFY_TWO 0x1020304050607002ULL
static inline void nfy_path(char *path, const char *kind, int id) {
    snprintf(path, 160, "/private/var/tmp/notify-%s-%d", kind, id);
}
static inline int nfy_mark(const char *kind, int id) {
    char path[160]; nfy_path(path, kind, id);
    int fd = open(path, 0x601, 0600);
    if (fd < 0) return -1;
    int error = ipc_write_all(fd, "done\n", 5) || fsync(fd);
    if (close(fd)) error = 1;
    return error ? -1 : 0;
}
static inline int nfy_exists(const char *kind, int id) {
    char path[160], data[8] = {0}; nfy_path(path, kind, id);
    int fd = open(path, 0); if (fd < 0) return 0;
    ssize_t n = read(fd, data, sizeof(data)); close(fd);
    return n == 5 && !memcmp(data, "done\n", 5);
}
static inline int nfy_wait(const char *kind, int id) {
    for (int i = 0; i < 300; ++i) { if (nfy_exists(kind, id)) return 0; sleep(1); }
    return -1;
}
#endif
