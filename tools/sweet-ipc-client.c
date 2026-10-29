#include "sweet-ipc.h"
int main(void) {
    if (ipc_identity("client")) return ipc_fail("identity");
    int server = -1;
    for (int i = 0; i < 120; ++i) {
        server = ipc_read_pid(IPC_SERVER_PID);
        if (ipc_path_matches(server, IPC_SERVER_PATH)) break;
        server = -1; sleep(1);
    }
    if (server <= 1) return ipc_fail("server readiness");
    int fd = socket(1, 1, 0);
    struct ipc_address address = ipc_addr();
    if (fd < 0 || ipc_options(fd) || connect(fd, &address, address.length) ||
        ipc_peer(fd, IPC_SERVER_PATH) != server) return ipc_fail("connect peer");
    ipc_note("PEER client=%d server=%d verified=LOCAL_PEERPID", getpid(), server);
    for (ipc_u32 seq = 1; seq <= 3; ++seq) {
        struct ipc_message request = ipc_message(1, seq, getpid(), server), response;
        if (ipc_write_all(fd, &request, sizeof(request)) || ipc_read_all(fd, &response, sizeof(response)) ||
            !ipc_valid(&response, 2, seq, getpid(), server)) return ipc_fail("request/reply");
        ipc_note("EXCHANGE seq=%u request=0x%08x response=0x%08x server=%d client=%d",
                 seq, request.value, response.value, server, getpid());
    }
    if (close(fd) || ipc_publish_pid(IPC_CLIENT_PID)) return ipc_fail("close/readiness");
    ipc_note("READY client=%d server=%d messages=3 waiting_for_release=1", getpid(), server);
    int released = 0;
    for (int i = 0; i < 240; ++i) {
        int release = open(IPC_RELEASE, 0);
        if (release >= 0) {
            char command[6] = {0}; ssize_t n = read(release, command, sizeof(command));
            if (close(release) || n != 5 || memcmp(command, "exit\n", 5)) return ipc_fail("release contents");
            released = 1; break;
        }
        if (*__error() != 2) return ipc_fail("release open");
        sleep(1);
    }
    if (!released) return ipc_fail("release timeout");
    ipc_note("NORMAL EXIT status=0 messages=3 socket_closed=1");
    if (fsync(ipc_trace) || close(ipc_trace)) return 1;
    return 0;
}
