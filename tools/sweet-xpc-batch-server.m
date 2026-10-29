#include "sweet-xpc-batch.h"
#include "sweet-foundation-xpc.h"
extern void *dispatch_queue_create(const char *, void *);
extern void dispatch_sync(void *, void (^)(void)), dispatch_release(void *);
extern void xpc_connection_set_target_queue(sweet_xpc_t, void *);
struct session { sweet_xpc_t peer; int id, pid, step, hello, closed; };
static struct session sessions[2];
static _Atomic int failed, closing, accepted, closed_peers, active, valid, rejected;
static volatile int stop_requested;
static int generation;
static void terminate(int signal) { if (signal == 15) stop_requested = 1; }
static void fatal(const char *step) { ipc_fail(step); failed = 1; }
static int payload_status(sweet_xpc_t event, ipc_u32 seq) {
    sweet_xpc_t value = xpc_dictionary_get_value(event, "foundation-json");
    if (!value) return 3;
    if (xpc_get_type(value) != &_xpc_type_data) return 2;
    size_t size = 0;
    if (!xpc_dictionary_get_data(event, "foundation-json", &size) || !size || size > 4096) return 4;
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    if (!pool) { fatal("pool allocation"); return 99; }
    int status = 1;
    @try {
        NSData *data = 0;
        NSDictionary *dict = fnd_decode(event, &data);
        if (dict) status = [dict count] == 3 && fnd_device(dict, "duchamp") &&
            fnd_number(dict, "seq", (int)seq) && fnd_number(dict, "value", (int)(0x10203000 + seq)) ? 0 : 5;
    } @catch (id exception) { (void)exception; fatal("unexpected Foundation exception"); status = 99; }
    [pool drain];
    return status;
}
static void receive(struct session *s, sweet_xpc_t event) {
    if (closing) return;
    if (event == (sweet_xpc_t)&_xpc_error_connection_invalid) {
        if (s->closed || !s->hello || s->step != 9) { fatal("premature peer close"); return; }
        s->closed = 1; active--; closed_peers++;
        ipc_note("BATCH CLOSED generation=%d id=%d client=%d steps=9 active=%d",
                 generation, s->id, s->pid, (int)active);
        if (closed_peers == 2 && batch_write(generation, 0, "closed", "closed\n")) fatal("closed token");
        return;
    }
    if (!event || xpc_get_type(event) != &_xpc_type_dictionary) { fatal("unexpected non-dictionary event"); return; }
    int client = xpc_connection_get_pid(s->peer);
    int id = (int)batch_get(event, "id"), op = (int)batch_get(event, "op");
    ipc_u32 seq = (ipc_u32)batch_get(event, "seq");
    if (!s->hello) {
        struct ipc_message hello = ipc_message(1, 0, client, 0);
        if (id < 1 || id > 2 || op != 1 || batch_get(event, "generation") != (unsigned int)generation ||
            batch_get(event, "status") != 0 || !batch_envelope(event, &hello) ||
            batch_pid(0, id, "pid") != client || !ipc_path_matches(client, IPC_CLIENT_PATH)) {
            fatal("hello credentials"); return;
        }
        for (int i = 0; i < 2; ++i) if (&sessions[i] != s && sessions[i].hello && sessions[i].id == id) {
            fatal("duplicate client"); return;
        }
        s->id = id; s->pid = client; s->hello = 1;
        ipc_note("BATCH HELLO generation=%d id=%d client=%d server=%d active=%d",
                 generation, id, client, getpid(), (int)active);
    }
    int status = 0;
    if (op == 2) {
        int step = s->step + 1;
        struct ipc_message expected = ipc_message(1, batch_seq(generation, s->id, step), client, 0);
        if (step > 9 || seq != expected.seq || id != s->id || client != s->pid ||
            batch_get(event, "generation") != (unsigned int)generation ||
            batch_get(event, "status") != 0 || !batch_envelope(event, &expected)) status = 6;
        else status = payload_status(event, seq);
        s->step = step;
        if (active != 2 || step > 9) { fatal("two-live-client invariant"); return; }
    } else if (op != 1 || s->step) { fatal("invalid operation"); return; }
    sweet_xpc_t reply = xpc_dictionary_create_reply(event);
    if (!reply) { fatal("reply context"); return; }
    struct ipc_message response = ipc_message(2, seq, client, getpid());
    sweet_xpc_fill(reply, &response);
    batch_meta(reply, generation, s->id, op, status);
    xpc_dictionary_set_uint64(reply, "active", (unsigned int)active);
    if (op == 2 && !status && fnd_server(event, reply, seq, 0x10203000 + seq, response.value)) {
        xpc_release(reply); fatal("valid Foundation request"); return;
    }
    xpc_connection_send_message(s->peer, reply); xpc_release(reply);
    if (op == 2) {
        if (status) rejected++; else valid++;
        ipc_note("BATCH REQUEST generation=%d id=%d client=%d step=%d seq=%u status=%d server=%d active=%d",
                 generation, s->id, client, s->step, seq, status, getpid(), (int)active);
    }
}
int main(void) {
    generation = batch_pid(1, 0, "pid") > 1 ? 2 : 1;
    if (batch_pid(2, 0, "pid") > 1) return 1;
    static char role[32]; snprintf(role, sizeof(role), "batch-server%d", generation);
    if (ipc_identity(role)) return ipc_fail("identity");
    struct ipc_action action = {terminate, 0, 0};
    unsigned int empty = 0;
    if (sigaction(15, &action, 0) || sigprocmask(3, &empty, 0)) return ipc_fail("TERM setup");
    void *queue = dispatch_queue_create("org.sweet.qemu.batch.serial", 0);
    if (!queue) return ipc_fail("serial queue");
    sweet_xpc_t listener = xpc_connection_create_mach_service(XPC_SERVICE, queue, 1);
    if (!listener) return ipc_fail("listener");
    xpc_connection_set_event_handler(listener, ^(sweet_xpc_t peer) {
        if (closing) return;
        if (xpc_get_type(peer) != &_xpc_type_connection || accepted >= 2) { fatal("listener capacity/event"); return; }
        struct session *s = &sessions[(int)accepted++];
        s->peer = xpc_retain(peer); active++;
        xpc_connection_set_target_queue(peer, queue);
        xpc_connection_set_event_handler(peer, ^(sweet_xpc_t event) { receive(s, event); });
        xpc_connection_resume(peer);
    });
    xpc_connection_resume(listener);
    if (batch_publish(generation, 0, "pid", getpid())) return ipc_fail("server pid");
    /* Startup is logged before traffic is released by the clients' barrier. */
    while (!stop_requested && !failed) sleep(1);
    if (failed || accepted != 2 || closed_peers != 2 || active || valid != 6 || rejected != 12)
        return ipc_fail("batch graceful prerequisites");
    dispatch_sync(queue, ^{
        closing = 1;
        for (int i = 0; i < 2; ++i) {
            xpc_connection_cancel(sessions[i].peer); xpc_release(sessions[i].peer);
        }
        xpc_connection_cancel(listener); xpc_release(listener);
    });
    dispatch_release(queue);
    ipc_note("BATCH SERVER EXIT generation=%d server=%d status=0 accepted=2 closed=2 valid=6 rejected=12", generation, getpid());
    int error = fsync(ipc_trace); if (close(ipc_trace)) error = 1;
    return error ? 1 : 0;
}
