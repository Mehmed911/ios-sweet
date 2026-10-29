#include "sweet-xpc.h"
static volatile int stop_requested;
static _Atomic int failed, messages, peer_closed, closing;
static _Atomic(sweet_xpc_t) peer_connection;
static void terminate(int signal) { if (signal == 15) stop_requested = 1; }
static void reject(const char *step) { ipc_fail(step); failed = 1; }
int main(void) {
    if (ipc_identity("server")) return ipc_fail("identity");
    struct ipc_action action = {terminate, 0, 0}, current = {0};
    unsigned int empty = 0, mask = 0;
    if (sigaction(15, &action, 0) || sigprocmask(3, &empty, 0) ||
        sigaction(15, 0, &current) || sigprocmask(3, 0, &mask) ||
        current.handler != terminate || mask) return ipc_fail("TERM handler readback");
    ipc_note("TERM handler installed mask=0x00000000");
    /* Listener bit 0 is also verified in this runtime's create_mach_service. */
    sweet_xpc_t listener = xpc_connection_create_mach_service(XPC_SERVICE, 0, 1);
    if (!listener) return ipc_fail("XPC listener create");
    xpc_connection_set_event_handler(listener, ^(sweet_xpc_t peer) {
        if (closing) return;
        if (xpc_get_type(peer) != &_xpc_type_connection || peer_connection) {
            reject("XPC listener event"); return;
        }
        peer_connection = xpc_retain(peer);
        xpc_connection_set_event_handler(peer, ^(sweet_xpc_t event) {
            if (closing) return;
            if (event == (sweet_xpc_t)&_xpc_error_connection_invalid && messages == 3) {
                ipc_note("XPC PEER CLOSED messages=3"); peer_closed = 1; return;
            }
            int client = xpc_connection_get_pid(peer);
            ipc_u32 seq = (ipc_u32)messages + 1;
            struct ipc_message request = ipc_message(1, seq, client, 0);
            if (seq > 3 || !ipc_path_matches(client, IPC_CLIENT_PATH) || !sweet_xpc_valid(event, &request)) {
                reject("XPC request/peer"); return;
            }
            if (seq == 1) ipc_note("XPC PEER client=%d server=%d verified=xpc_connection_get_pid", client, getpid());
            sweet_xpc_t reply = xpc_dictionary_create_reply(event);
            if (!reply) { reject("XPC reply context"); return; }
            struct ipc_message response = ipc_message(2, seq, client, getpid());
            sweet_xpc_fill(reply, &response);
            xpc_connection_send_message(peer, reply); xpc_release(reply);
            ipc_note("XPC EXCHANGE seq=%u request=0x%08x response=0x%08x server=%d client=%d",
                     seq, request.value, response.value, getpid(), client);
            messages = (int)seq;
        });
        xpc_connection_resume(peer);
    });
    xpc_connection_resume(listener);
    if (ipc_publish_pid(IPC_SERVER_PID)) return ipc_fail("XPC readiness");
    ipc_note("XPC LISTEN pid=%d name=%s", getpid(), XPC_SERVICE);
    while (!stop_requested && !failed) sleep(1);
    if (failed || messages != 3 || !peer_closed) return ipc_fail("XPC graceful prerequisites");
    closing = 1;
    sweet_xpc_t peer = peer_connection;
    if (peer) { xpc_connection_cancel(peer); xpc_release(peer); }
    xpc_connection_cancel(listener); xpc_release(listener);
    ipc_note("XPC GRACEFUL EXIT status=0 signal=15 messages=3 peer_closed=1 connections_cancelled=1");
    if (fsync(ipc_trace) || close(ipc_trace)) return 1;
    return 0;
}
