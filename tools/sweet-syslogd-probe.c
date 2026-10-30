/* Legacy ASL transport against the pinned original iOS syslogd, not os_log. */
#include "sweet-ipc.h"
typedef void *asl_object_t;
extern asl_object_t asl_open(const char *, const char *, unsigned int), asl_new(unsigned int);
extern int asl_set(asl_object_t, const char *, const char *), asl_send(asl_object_t, asl_object_t);
extern void asl_close(asl_object_t), asl_release(asl_object_t);
extern unsigned int _asl_evaluate_send(asl_object_t, asl_object_t, int), asl_core_get_service_port(int);
static int token(const char *path, const char *expected) {
    char text[32] = {0}; int fd = open(path, 0);
    if (fd < 0) return -1;
    ssize_t count = read(fd, text, sizeof(text)); close(fd);
    return count == (ssize_t)strlen(expected) && !memcmp(text, expected, (size_t)count) ? 0 : -1;
}
static int wait_token(const char *path, const char *expected) {
    for (int i = 0; i < 300; ++i) { if (!token(path, expected)) return 0; sleep(1); }
    return -1;
}
int main(int argc, char **argv) {
    if (argc != 2 || (strcmp(argv[1], "1") && strcmp(argv[1], "2"))) return 1;
    int id = argv[1][0] - '0';
    char role[24], path[128], sender[32];
    snprintf(role, sizeof(role), "asl%d", id);
    snprintf(sender, sizeof(sender), "sweet-asl%d", id);
    if (ipc_identity(role)) return ipc_fail("identity");
    snprintf(path, sizeof(path), "/private/var/tmp/asl-probe%d.pid", id);
    if (ipc_publish_pid(path) || wait_token("/private/var/tmp/asl-probes.begin", "begin\n")) return ipc_fail("begin gate");
    /* Apple ASL private flags: NO_REMOTE | SHIM_NO_TRACE. No local file output. */
    asl_object_t client = asl_open(sender, "local0", 0x20000004);
    unsigned int port = asl_core_get_service_port(0);
    if (!client || !port) return ipc_fail("ASL client/service port");
    ipc_note("ASL CONNECTED id=%d pid=%d port=0x%x options=0x20000004", id, getpid(), port);
    for (int seq = 1; seq <= 3; ++seq) {
        asl_object_t message = asl_new(0);
        char text[128], number[16];
        snprintf(text, sizeof(text), "SWEET_SYSLOGD_C%d_S%d_20F66", id, seq);
        snprintf(number, sizeof(number), "%d", seq);
        if (!message || asl_set(message, "Level", "5") || asl_set(message, "Message", text) ||
            asl_set(message, "SweetFixture", "syslogd-qemu") || asl_set(message, "SweetClient", argv[1]) ||
            asl_set(message, "SweetSequence", number)) return ipc_fail("ASL fields");
        unsigned int eval = _asl_evaluate_send(client, message, -1);
        if (!(eval & 0x20000) || (eval & (0x40000 | 0x80000 | 0x100000))) return ipc_fail("ASL transport evaluation");
        int status = asl_send(client, message);
        asl_release(message);
        if (status) return ipc_fail("ASL send");
        ipc_note("ASL SENT id=%d seq=%d pid=%d status=0 eval=0x%08x", id, seq, getpid(), eval);
    }
    asl_close(client);
    snprintf(path, sizeof(path), "/private/var/tmp/asl-probe%d.done", id);
    if (ipc_publish_pid(path) || wait_token("/private/var/tmp/asl-probes.exit", "exit\n")) return ipc_fail("exit gate");
    ipc_note("ASL PROBE EXIT id=%d pid=%d status=0 messages=3", id, getpid());
    int error = fsync(ipc_trace); if (close(ipc_trace)) error = 1;
    return error ? 1 : 0;
}
