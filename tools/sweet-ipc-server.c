#include "sweet-ipc.h"
static volatile int stop_requested;
static void terminate(int signal) { if (signal == 15) stop_requested = 1; }
int main(void) {
    if (ipc_identity("server")) return ipc_fail("identity");
    struct ipc_action action = {terminate, 0, 0}, current = {0};
    unsigned int empty = 0, mask = 0;
    if (sigaction(15, &action, 0) || sigprocmask(3, &empty, 0) ||
        sigaction(15, 0, &current) || sigprocmask(3, 0, &mask) ||
        current.handler != terminate || mask) return ipc_fail("TERM handler readback");
    ipc_note("TERM handler installed mask=0x00000000");
    if (!access(IPC_SOCKET, 0) || *__error() != 2) return ipc_fail("stale socket");
    int listener = socket(1, 1, 0);
    struct ipc_address address = ipc_addr();
    if (listener < 0 || ipc_options(listener) || bind(listener, &address, address.length) ||
        listen(listener, 1) || ipc_publish_pid(IPC_SERVER_PID)) return ipc_fail("listen");
    ipc_note("LISTEN pid=%d path=%s", getpid(), IPC_SOCKET);
    int messages = 0, eof = 0, client = -1;
    while (!stop_requested) {
        struct ipc_pollfd ready = {listener, 1, 0};
        int events = poll(&ready, 1, 1000);
        if (events < 0 && *__error() == 4) continue;
        if (events < 0 || (events > 0 && !(ready.revents & 1))) return ipc_fail("listen poll");
        if (!events || stop_requested) continue;
        if (messages) return ipc_fail("unexpected second connection");
        int fd = accept(listener, 0, 0);
        if (fd < 0 || ipc_options(fd) || (client = ipc_peer(fd, IPC_CLIENT_PATH)) <= 1)
            return ipc_fail("accept peer");
        ipc_note("PEER client=%d server=%d verified=LOCAL_PEERPID", client, getpid());
        for (ipc_u32 seq = 1; seq <= 3; ++seq) {
            struct ipc_message request, response = ipc_message(2, seq, client, getpid());
            if (ipc_read_all(fd, &request, sizeof(request)) || !ipc_valid(&request, 1, seq, client, getpid()) ||
                ipc_write_all(fd, &response, sizeof(response))) return ipc_fail("request/reply");
            ++messages;
            ipc_note("EXCHANGE seq=%u request=0x%08x response=0x%08x server=%d client=%d",
                     seq, request.value, response.value, getpid(), client);
        }
        char extra; ssize_t n;
        do { n = read(fd, &extra, 1); } while (n < 0 && *__error() == 4);
        if (n != 0 || close(fd)) return ipc_fail("peer EOF");
        eof = 1; ipc_note("PEER EOF client=%d messages=3", client);
    }
    if (messages != 3 || !eof || close(listener) || unlink(IPC_SOCKET) ||
        !access(IPC_SOCKET, 0) || *__error() != 2) return ipc_fail("graceful cleanup");
    ipc_note("GRACEFUL EXIT status=0 signal=15 messages=3 peer_closed=1 socket_removed=1");
    if (fsync(ipc_trace) || close(ipc_trace)) return 1;
    return 0;
}
