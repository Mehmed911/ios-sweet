/* Public C libxpc ABI; the pinned Apple runtime exports these entry points. */
#ifndef SWEET_XPC_H
#define SWEET_XPC_H
#include "sweet-ipc.h"
#define XPC_SERVICE "org.sweet.qemu.mach-service"
#define XPC_BEGIN "/private/var/tmp/xpc-client.begin"
#define XPC_DONE "/private/var/tmp/xpc-client.done"
typedef void *sweet_xpc_t;
extern sweet_xpc_t xpc_connection_create_mach_service(const char *, void *, unsigned long long);
extern void xpc_connection_set_event_handler(sweet_xpc_t, void (^)(sweet_xpc_t));
extern void xpc_connection_resume(sweet_xpc_t), xpc_connection_cancel(sweet_xpc_t);
extern int xpc_connection_get_pid(sweet_xpc_t);
extern sweet_xpc_t xpc_connection_send_message_with_reply_sync(sweet_xpc_t, sweet_xpc_t);
extern void xpc_connection_send_message(sweet_xpc_t, sweet_xpc_t);
extern sweet_xpc_t xpc_dictionary_create(const char *const *, const sweet_xpc_t *, size_t);
extern sweet_xpc_t xpc_dictionary_create_reply(sweet_xpc_t);
extern void xpc_dictionary_set_uint64(sweet_xpc_t, const char *, unsigned long long);
extern unsigned long long xpc_dictionary_get_uint64(sweet_xpc_t, const char *);
extern const void *xpc_get_type(sweet_xpc_t);
extern sweet_xpc_t xpc_retain(sweet_xpc_t);
extern void xpc_release(sweet_xpc_t);
extern const char _xpc_type_dictionary, _xpc_type_connection, _xpc_error_connection_invalid;
static inline void sweet_xpc_fill(sweet_xpc_t d, const struct ipc_message *m) {
    const char *keys[] = {"magic", "version", "kind", "seq", "client", "server", "value", "check"};
    ipc_u32 values[] = {m->magic, m->version, m->kind, m->seq, m->client, m->server, m->value, m->check};
    for (int i = 0; i < 8; ++i) xpc_dictionary_set_uint64(d, keys[i], values[i]);
}
static inline int sweet_xpc_valid(sweet_xpc_t d, const struct ipc_message *m) {
    if (!d || xpc_get_type(d) != &_xpc_type_dictionary) return 0;
    const char *keys[] = {"magic", "version", "kind", "seq", "client", "server", "value", "check"};
    ipc_u32 values[] = {m->magic, m->version, m->kind, m->seq, m->client, m->server, m->value, m->check};
    for (int i = 0; i < 8; ++i) if (xpc_dictionary_get_uint64(d, keys[i]) != values[i]) return 0;
    return 1;
}
static inline int sweet_xpc_token(const char *path, const char *token) {
    char data[16] = {0}; int fd = open(path, 0);
    if (fd < 0) return -1;
    ssize_t n = read(fd, data, sizeof(data)); int error = close(fd);
    return !error && n == (ssize_t)strlen(token) && !memcmp(data, token, (size_t)n) ? 0 : -1;
}
#endif
