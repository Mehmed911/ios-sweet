#include "sweet-xpc-batch.h"
#include "sweet-foundation-xpc.h"
static _Atomic int closing[2], failed;
static int client_id;
static int one_round(int generation, int previous_server) {
    if (batch_wait(generation, 0, "begin", "begin\n")) return ipc_fail("round gate timeout");
    sweet_xpc_t connection = xpc_connection_create_mach_service(XPC_SERVICE, 0, 0);
    if (!connection) return ipc_fail("connection");
    xpc_connection_set_event_handler(connection, ^(sweet_xpc_t event) {
        (void)event;
        if (!closing[generation - 1]) { ipc_fail("unexpected connection event"); failed = 1; }
    });
    xpc_connection_resume(connection);
    struct ipc_message hello = ipc_message(1, 0, getpid(), 0);
    sweet_xpc_t message = xpc_dictionary_create(0, 0, 0);
    if (!message) return ipc_fail("hello allocation");
    sweet_xpc_fill(message, &hello); batch_meta(message, generation, client_id, 1, 0);
    sweet_xpc_t reply = xpc_connection_send_message_with_reply_sync(connection, message);
    xpc_release(message);
    int server = xpc_connection_get_pid(connection);
    struct ipc_message hello_reply = ipc_message(2, 0, getpid(), server);
    if (failed || server == previous_server || !ipc_path_matches(server, IPC_SERVER_PATH) ||
        !batch_envelope(reply, &hello_reply) || batch_get(reply, "generation") != (unsigned int)generation ||
        batch_get(reply, "id") != (unsigned int)client_id || batch_get(reply, "op") != 1 || batch_get(reply, "status") != 0)
        return ipc_fail("hello reply/peer");
    xpc_release(reply);
    ipc_note("BATCH CONNECTED generation=%d id=%d client=%d server=%d", generation, client_id, getpid(), server);
    if (batch_publish(generation, client_id, "connected", server)) return ipc_fail("connected token");
    int together = 0;
    for (int i = 0; i < 300; ++i) {
        if (batch_pid(generation, 3 - client_id, "connected") == server) { together = 1; break; }
        sleep(1);
    }
    if (!together) return ipc_fail("other client barrier");
    for (int step = 1; step <= 9; ++step) {
        ipc_u32 seq = batch_seq(generation, client_id, step);
        struct ipc_message request = ipc_message(1, seq, getpid(), 0);
        if (step == 8) { request.client++; request.check = ipc_sum(&request); }
        message = xpc_dictionary_create(0, 0, 0);
        if (!message) return ipc_fail("request allocation");
        sweet_xpc_fill(message, &request); batch_meta(message, generation, client_id, 2, 0);
        if (!batch_expected(step)) {
            if (fnd_request(message, seq, request.value)) return ipc_fail("Foundation encode");
        } else if (step == 2) {
            xpc_dictionary_set_data(message, "foundation-json", "{bad", 4);
        } else if (step == 4) {
            xpc_dictionary_set_string(message, "foundation-json", "wrong XPC type");
        } else if (step == 6) {
            char large[4097] = {0}; xpc_dictionary_set_data(message, "foundation-json", large, sizeof(large));
        } else if (step == 7) {
            char text[128]; int n = snprintf(text, sizeof(text), "{\"device\":42,\"seq\":%u,\"value\":%u}", seq, request.value);
            xpc_dictionary_set_data(message, "foundation-json", text, (size_t)n);
        }
        /* step 5 omits data; step 8 deliberately spoofs the envelope PID. */
        reply = xpc_connection_send_message_with_reply_sync(connection, message); xpc_release(message);
        struct ipc_message expected = ipc_message(2, seq, getpid(), server);
        int status = batch_expected(step);
        if (failed || xpc_connection_get_pid(connection) != server || !ipc_path_matches(server, IPC_SERVER_PATH) ||
            !batch_envelope(reply, &expected) || batch_get(reply, "generation") != (unsigned int)generation ||
            batch_get(reply, "id") != (unsigned int)client_id || batch_get(reply, "op") != 2 ||
            batch_get(reply, "status") != (unsigned int)status || batch_get(reply, "active") != 2)
            return ipc_fail("batch response");
        if (!status && fnd_client(reply, seq, expected.value)) return ipc_fail("Foundation response");
        if (status && xpc_dictionary_get_value(reply, "foundation-json")) return ipc_fail("error reply contains payload");
        xpc_release(reply);
        ipc_note("BATCH REPLY generation=%d id=%d client=%d step=%d seq=%u status=%d server=%d active=2",
                 generation, client_id, getpid(), step, seq, status, server);
    }
    if (batch_publish(generation, client_id, "done", server) ||
        batch_wait(generation, 0, "close", "close\n")) return ipc_fail("close gate");
    closing[generation - 1] = 1;
    xpc_connection_cancel(connection); xpc_release(connection);
    ipc_note("BATCH ROUND DONE generation=%d id=%d client=%d server=%d valid=3 rejected=6", generation, client_id, getpid(), server);
    return server;
}
int main(int argc, char **argv) {
    if (argc != 2 || (strcmp(argv[1], "1") && strcmp(argv[1], "2"))) return 1;
    client_id = argv[1][0] - '0';
    static char role[32]; snprintf(role, sizeof(role), "batch-client%d", client_id);
    if (ipc_identity(role) || batch_publish(0, client_id, "pid", getpid())) return ipc_fail("identity/pid");
    int previous = -1;
    for (int generation = 1; generation <= 2; ++generation) {
        int server = one_round(generation, previous);
        if (server <= 1) return 1;
        previous = server;
    }
    ipc_note("BATCH CLIENT EXIT id=%d client=%d status=0 rounds=2 valid=6 rejected=12", client_id, getpid());
    int error = fsync(ipc_trace); if (close(ipc_trace)) error = 1;
    return error ? 1 : 0;
}
