#include "sweet-xpc-batch.h"
static int batch_gone(int pid) {
    for (int i = 0; i < 120; ++i) {
        if (kill(pid, 0) < 0 && *__error() == 3) return 0;
        pause_seconds(1);
    }
    return -1;
}
static int batch_print(const char *tag, const char *service, int pid, int runs) {
    char *args[] = {"launchctl", "print", (char *)service, 0};
    if (command(tag, args) || property_pid(output) != pid) return -1;
    char count[32]; snprintf(count, sizeof(count), "runs = %d\n", runs);
    if (!strstr(output, count)) return -1;
    if (pid) return strstr(output, "state = running") ? 0 : -1;
    return strstr(output, "state = not running") && (!runs || strstr(output, "last exit code = 0")) ? 0 : -1;
}
static int batch_lifecycle(void) {
    note("SCENARIO foundation-xpc-batch");
    int clients[2] = {-1, -1}, servers[2] = {-1, -1};
    for (int i = 0; i < 300; ++i) {
        clients[0] = batch_pid(0, 1, "pid"); clients[1] = batch_pid(0, 2, "pid");
        if (clients[0] != clients[1] && ipc_path_matches(clients[0], IPC_CLIENT_PATH) &&
            ipc_path_matches(clients[1], IPC_CLIENT_PATH)) break;
        clients[0] = clients[1] = -1; pause_seconds(1);
    }
    if (clients[0] <= 1 || clients[1] <= 1 ||
        batch_print("batch-dormant-1", target, 0, 0) || !strstr(output, XPC_SERVICE))
        return fail("batch initial dormant state");
    note("BATCH DORMANT generation=1 runs=0 clients=%d,%d", clients[0], clients[1]);
    for (int generation = 1; generation <= 2; ++generation) {
        if (batch_write(generation, 0, "begin", "begin\n")) return fail("batch begin");
        int server = -1;
        for (int i = 0; i < 300; ++i) {
            server = batch_pid(generation, 0, "pid");
            if (server > 1 && (generation == 1 || server != servers[0]) &&
                batch_pid(generation, 1, "connected") == server && batch_pid(generation, 2, "connected") == server &&
                ipc_path_matches(server, IPC_SERVER_PATH)) break;
            server = -1; pause_seconds(1);
        }
        if (server <= 1) return fail("batch two connected clients");
        servers[generation - 1] = server;
        note("BATCH ACTIVE generation=%d server=%d clients=%d,%d", generation, server, clients[0], clients[1]);
        char tag[48]; snprintf(tag, sizeof(tag), "batch-running-%d", generation);
        if (batch_print(tag, target, server, generation)) return fail("batch running print");
        int done = 0;
        for (int i = 0; i < 300; ++i) {
            if (batch_pid(generation, 1, "done") == server && batch_pid(generation, 2, "done") == server) {
                done = 1; break;
            }
            pause_seconds(1);
        }
        if (!done || !ipc_path_matches(clients[0], IPC_CLIENT_PATH) || !ipc_path_matches(clients[1], IPC_CLIENT_PATH))
            return fail("batch request completion");
        note("BATCH EXCHANGES generation=%d server=%d valid=6 rejected=12", generation, server);
        if (batch_write(generation, 0, "close", "close\n") ||
            batch_wait(generation, 0, "closed", "closed\n")) return fail("batch peer close");
        snprintf(tag, sizeof(tag), "batch-stop-%d", generation);
        char *stop[] = {"launchctl", "kill", "SIGTERM", (char *)target, 0};
        if (command(tag, stop) || batch_gone(server)) return fail("batch server stop");
        note("BATCH SERVER REAPED generation=%d server=%d ESRCH", generation, server);
        pause_seconds(5);
        snprintf(tag, sizeof(tag), "batch-dormant-%d", generation + 1);
        if (batch_print(tag, target, 0, generation) || !strstr(output, XPC_SERVICE))
            return fail("batch dormant after exit");
        if (generation == 1 && (!ipc_path_matches(clients[0], IPC_CLIENT_PATH) ||
                               !ipc_path_matches(clients[1], IPC_CLIENT_PATH))) return fail("clients lost between rounds");
    }
    for (int id = 1; id <= 2; ++id) {
        if (batch_gone(clients[id - 1])) return fail("batch client not reaped");
        char tag[48], service[96];
        snprintf(tag, sizeof(tag), "batch-client-%d-exited", id);
        snprintf(service, sizeof(service), "system/org.sweet.qemu.ipc-client%d", id);
        if (batch_print(tag, service, 0, 1)) return fail("batch client exit print");
    }
    note("BATCH CONTROL PASS servers=%d,%d clients=%d,%d valid=12 rejected=24",
         servers[0], servers[1], clients[0], clients[1]);
    sync();
    for (unsigned int beat = 1;; ++beat) {
        pause_seconds(10);
        for (int i = 0; i < 2; ++i)
            if (!kill(servers[i], 0) || *__error() != 3 || !kill(clients[i], 0) || *__error() != 3)
                return fail("batch stopped state lost");
        note("heartbeat=%u batch_stopped=1", beat);
    }
}
