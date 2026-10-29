/* A bounded two-client, two-generation QEMU fixture; no hardware access. */
#ifndef SWEET_XPC_BATCH_H
#define SWEET_XPC_BATCH_H
#include "sweet-xpc.h"
extern sweet_xpc_t xpc_dictionary_get_value(sweet_xpc_t, const char *);
extern void xpc_dictionary_set_string(sweet_xpc_t, const char *, const char *);
extern const char _xpc_type_uint64, _xpc_type_data;
static inline void batch_path(char *path, int generation, int client, const char *kind) {
    snprintf(path, 160, "/private/var/tmp/batch-g%d-c%d-%s", generation, client, kind);
}
static inline int batch_write(int generation, int client, const char *kind, const char *text) {
    char path[160]; batch_path(path, generation, client, kind);
    int fd = open(path, 0x601, 0600);
    if (fd < 0) return -1;
    int error = ipc_write_all(fd, text, strlen(text)) || fsync(fd);
    if (close(fd)) error = 1;
    return error ? -1 : 0;
}
static inline int batch_publish(int generation, int client, const char *kind, int pid) {
    char text[32]; snprintf(text, sizeof(text), "%d\n", pid);
    return batch_write(generation, client, kind, text);
}
static inline int batch_pid(int generation, int client, const char *kind) {
    char path[160]; batch_path(path, generation, client, kind);
    return ipc_read_pid(path);
}
static inline int batch_token(int generation, int client, const char *kind, const char *token) {
    char path[160]; batch_path(path, generation, client, kind);
    return sweet_xpc_token(path, token);
}
static inline int batch_wait(int generation, int client, const char *kind, const char *token) {
    for (int i = 0; i < 300; ++i) {
        if (!batch_token(generation, client, kind, token)) return 0;
        sleep(1);
    }
    return -1;
}
static inline unsigned long long batch_get(sweet_xpc_t d, const char *key) {
    sweet_xpc_t value = xpc_dictionary_get_value(d, key);
    return value && xpc_get_type(value) == &_xpc_type_uint64 ?
        xpc_dictionary_get_uint64(d, key) : ~0ULL;
}
static inline void batch_meta(sweet_xpc_t d, int generation, int id, int op, int status) {
    xpc_dictionary_set_uint64(d, "generation", (unsigned int)generation);
    xpc_dictionary_set_uint64(d, "id", (unsigned int)id);
    xpc_dictionary_set_uint64(d, "op", (unsigned int)op);
    xpc_dictionary_set_uint64(d, "status", (unsigned int)status);
}
static inline int batch_envelope(sweet_xpc_t d, const struct ipc_message *expected) {
    if (!d || xpc_get_type(d) != &_xpc_type_dictionary) return 0;
    const char *keys[] = {"magic", "version", "kind", "seq", "client", "server", "value", "check"};
    for (int i = 0; i < 8; ++i) {
        sweet_xpc_t value = xpc_dictionary_get_value(d, keys[i]);
        if (!value || xpc_get_type(value) != &_xpc_type_uint64) return 0;
    }
    return sweet_xpc_valid(d, expected);
}
static inline ipc_u32 batch_seq(int generation, int id, int step) {
    return (ipc_u32)(generation * 100 + id * 10 + step);
}
/* Errors: JSON syntax, XPC type, missing data, size, JSON schema, envelope. */
static inline int batch_expected(int step) {
    const int statuses[] = {0, 0, 1, 0, 2, 3, 4, 5, 6, 0};
    return step >= 1 && step <= 9 ? statuses[step] : -1;
}
#endif
