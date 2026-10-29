#include "sweet-xpc.h"
static _Atomic int closing, failed;
int main(void) {
    if (ipc_identity("client")) return ipc_fail("identity");
    if (ipc_publish_pid(IPC_CLIENT_PID)) return ipc_fail("XPC initial readiness");
    ipc_note("XPC WAITING FOR BEGIN client=%d", getpid());
    int begun = 0;
    for (int i = 0; i < 180; ++i) {
        if (!sweet_xpc_token(XPC_BEGIN, "begin\n")) { begun = 1; break; }
        sleep(1);
    }
    if (!begun) return ipc_fail("XPC begin timeout");
    sweet_xpc_t connection = xpc_connection_create_mach_service(XPC_SERVICE, 0, 0);
    if (!connection) return ipc_fail("XPC connection create");
    xpc_connection_set_event_handler(connection, ^(sweet_xpc_t event) {
        (void)event;
        if (!closing) { ipc_fail("XPC client unexpected event"); failed = 1; }
    });
    xpc_connection_resume(connection);
    int server = -1;
    for (ipc_u32 seq = 1; seq <= 3; ++seq) {
        struct ipc_message request = ipc_message(1, seq, getpid(), 0);
        sweet_xpc_t message = xpc_dictionary_create(0, 0, 0);
        if (!message) return ipc_fail("XPC request allocation");
        sweet_xpc_fill(message, &request);
        /* Main is outside the event-handler queue. The VM bounds this sync wait. */
        sweet_xpc_t reply = xpc_connection_send_message_with_reply_sync(connection, message);
        xpc_release(message);
        int peer = xpc_connection_get_pid(connection);
        if (seq == 1) server = peer;
        struct ipc_message response = ipc_message(2, seq, getpid(), server);
        if (failed || peer != server || !ipc_path_matches(server, IPC_SERVER_PATH) ||
            !sweet_xpc_valid(reply, &response)) return ipc_fail("XPC reply/peer");
        xpc_release(reply);
        if (seq == 1) ipc_note("XPC PEER client=%d server=%d verified=xpc_connection_get_pid", getpid(), server);
        ipc_note("XPC EXCHANGE seq=%u request=0x%08x response=0x%08x server=%d client=%d",
                 seq, request.value, response.value, server, getpid());
    }
    int done = open(XPC_DONE, 0x601, 0600);
    if (done < 0 || ipc_write_all(done, "done\n", 5) || fsync(done) || close(done)) return ipc_fail("XPC done");
    ipc_note("XPC READY client=%d server=%d messages=3 waiting_for_release=1", getpid(), server);
    int released = 0;
    for (int i = 0; i < 240; ++i) {
        if (!sweet_xpc_token(IPC_RELEASE, "exit\n")) { released = 1; break; }
        if (failed) return ipc_fail("XPC while waiting");
        sleep(1);
    }
    if (!released) return ipc_fail("XPC release timeout");
    closing = 1;
    xpc_connection_cancel(connection); xpc_release(connection);
    ipc_note("XPC NORMAL EXIT status=0 messages=3 connection_cancelled=1");
    if (fsync(ipc_trace) || close(ipc_trace)) return 1;
    return 0;
}
