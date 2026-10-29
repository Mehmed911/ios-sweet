/* Included after the launchctl capture helpers; the observer starts no service. */
#include "sweet-ipc.h"
#if defined(SWEET_XPC_TEST)
#include "sweet-xpc.h"
#endif
static int ipc_wait_gone(int pid) {
    for (int i = 0; i < 60; ++i) {
        if (kill(pid, 0) < 0 && *__error() == 3) return 0;
        pause_seconds(1);
    }
    return -1;
}
static int ipc_stopped(const char *tag, const char *service) {
    char *argv[] = {"launchctl", "print", (char *)service, 0};
    return command(tag, argv) || property_pid(output) != 0 ||
        !strstr(output, "last exit code = 0") ? -1 : 0;
}
static int ipc_lifecycle(void) {
    const char *client_target = "system/org.sweet.qemu.ipc-client";
#if defined(SWEET_XPC_TEST)
    note("SCENARIO xpc");
    int waiting = -1;
    for (int i = 0; i < 180; ++i) {
        waiting = ipc_read_pid(IPC_CLIENT_PID);
        if (ipc_path_matches(waiting, IPC_CLIENT_PATH)) break;
        waiting = -1; pause_seconds(1);
    }
    if (waiting <= 1 || ipc_read_pid(IPC_SERVER_PID) > 1) return fail("XPC initial client/server state");
    char *dormant[] = {"launchctl", "print", (char *)target, 0};
    if (command("print-server-dormant", dormant) || property_pid(output) != 0 ||
        !strstr(output, "runs = 0") || !strstr(output, XPC_SERVICE)) return fail("XPC dormant registration");
    note("XPC DORMANT verified runs=0 no pid client=%d", waiting);
    int begin = open(XPC_BEGIN, 0x601, 0600);
    if (begin < 0 || write_all(begin, "begin\n", 6) || fsync(begin) || close(begin)) return fail("XPC begin release");
    note("XPC BEGIN RELEASED client=%d", waiting);
#else
    note("SCENARIO ipc");
#endif
    int server = -1, client = -1;
    for (int i = 0; i < 180; ++i) {
        server = ipc_read_pid(IPC_SERVER_PID); client = ipc_read_pid(IPC_CLIENT_PID);
#if defined(SWEET_XPC_TEST)
        if (sweet_xpc_token(XPC_DONE, "done\n")) { pause_seconds(1); continue; }
#endif
        if (server != client && ipc_path_matches(server, IPC_SERVER_PATH) &&
            ipc_path_matches(client, IPC_CLIENT_PATH)) break;
        server = client = -1; pause_seconds(1);
    }
    if (server <= 1 || client <= 1) return fail("IPC service readiness");
    note("IPC READY server=%d client=%d", server, client);
    char *server_print[] = {"launchctl", "print", (char *)target, 0};
    if (command("print-server", server_print) || property_pid(output) != server ||
        !strstr(output, "state = running")) return fail("IPC server print");
    char *client_print[] = {"launchctl", "print", (char *)client_target, 0};
    if (command("print-client", client_print) || property_pid(output) != client ||
        !strstr(output, "state = running")) return fail("IPC client print");
    int release = open(IPC_RELEASE, 0x601, 0600);
    if (release < 0 || write_all(release, "exit\n", 5) || fsync(release) || close(release))
        return fail("IPC client release");
    note("IPC CLIENT RELEASED pid=%d", client);
    if (ipc_wait_gone(client)) return fail("IPC client not reaped");
    note("IPC CLIENT REAPED pid=%d ESRCH", client);
    pause_seconds(5);
    if (ipc_stopped("print-client-exited", client_target)) return fail("IPC client normal exit");
    char *stop[] = {"launchctl", "kill", "SIGTERM", (char *)target, 0};
    if (command("stop-server", stop) || ipc_wait_gone(server)) return fail("IPC server stop");
    note("IPC SERVER REAPED pid=%d ESRCH", server);
    pause_seconds(5);
    if (ipc_stopped("print-server-exited", target) || !access(IPC_SOCKET, 0) || *__error() != 2)
        return fail("IPC server graceful exit/socket cleanup");
    note("IPC CONTROL PASS server=%d client=%d", server, client);
    sync();
    for (unsigned int beat = 1;; ++beat) {
        pause_seconds(10);
        if (kill(server, 0) == 0 || *__error() != 3 || kill(client, 0) == 0 || *__error() != 3 ||
            !access(IPC_SOCKET, 0) || *__error() != 2) return fail("IPC stopped state lost");
        note("heartbeat=%u ipc_stopped=1 server=%d client=%d", beat, server, client);
    }
}
